"""Static provider-pilot preflight validator."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.safety.common import (
    is_real_provider_type,
    section_markdown,
    write_dual_report,
)
from causal_agent_bench.safety.run_cost_estimator import estimate_run_cost

FORBIDDEN_AGENT_MARKERS = ("oracle", "mock", "stub")
PENDING_SCOPES = {
    "provider_pilot_pending_verification",
    "provider_pilot_debug_or_preliminary",
    "commercial_api_pilot_unvalidated",
}


def build_provider_pilot_preflight(
    repo_root: str | Path,
    *,
    config_path: str | Path,
    output_dir: str | Path = "reports/provider_pilot_preflight",
    reports_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    config = Path(config_path)
    if not config.is_absolute():
        config = root / config
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    report = validate_provider_pilot_preflight(config, repo_root=root, reports_dir=reports_dir)
    md = provider_pilot_preflight_markdown(report)
    md_path, json_path = write_dual_report(
        stem="provider_pilot_preflight",
        payload=report,
        markdown=md,
        output_dir=out,
    )
    report["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def validate_provider_pilot_preflight(
    config_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    reports_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    reports_root = Path(reports_dir).resolve() if reports_dir else root
    path = Path(config_path)
    raw = _load_yaml(path)
    checks: list[dict[str, Any]] = []
    is_template = "template" in path.name.lower() or "template" in str(raw.get("run_name", "")).lower()
    approved_name = "approved" in path.name.lower() or "approved" in str(raw.get("run_name", "")).lower()
    approval = raw.get("approval") if isinstance(raw.get("approval"), dict) else {}
    approval_state = _approval_state(approval)

    if is_template:
        _add(checks, "warning", "template_not_runnable", "Template config is safe for static review but must not be run.")
        if approval_state["any_true"]:
            _add(checks, "blocker", "template_has_approval_true", "Template approval markers must remain false.")
    else:
        _add(checks, "informational", "config_is_not_template", "OK")
    _check(approved_name, checks, "approved_copy_name", "Config path or run_name should clearly be an APPROVED copy.", warning=True)
    if is_template:
        _add(checks, "warning", "approved_copy_required", "Create a separate APPROVED copy only after advisor approval.")
    else:
        _check(approval_state["dry_run_ready"], checks, "approval_marker_present", "Approval marker missing.")

    allow_paid = bool(raw.get("allow_paid_calls", False))
    if allow_paid and (not approved_name or is_template):
        _add(checks, "blocker", "paid_calls_only_in_approved_copy", "allow_paid_calls=true is only allowed in an approved copy.")
    else:
        _add(checks, "informational", "paid_call_gate", f"allow_paid_calls={allow_paid}.")

    budget = raw.get("budget") if isinstance(raw.get("budget"), dict) else {}
    _check(raw.get("budget_cap_usd") is not None or budget.get("max_total_usd") is not None, checks, "budget_cap_present", "Budget cap missing.")
    _check(_trajectory_cap_present(raw), checks, "trajectory_cap_present", "Tiny trajectory/stop cap missing.")
    _check(_stop_conditions_present(raw), checks, "stop_conditions_present", "Stop conditions missing.")

    for agent_run in _agent_runs(raw):
        provider = str(agent_run.get("provider") or raw.get("provider") or "")
        agent = str(agent_run.get("agent") or "")
        _check(is_real_provider_type(provider), checks, "provider_backed_family", f"Provider is not provider-backed: {provider!r}.")
        if any(marker in agent.lower() for marker in FORBIDDEN_AGENT_MARKERS):
            _add(checks, "blocker", "non_evidence_agent", f"Agent is oracle/mock/stub-like: {agent!r}.")
        model = str(agent_run.get("model") or raw.get("model") or "")
        if _model_placeholder_unresolved(model):
            severity = "warning" if is_template else "blocker"
            _add(checks, severity, "model_placeholder_unresolved", f"Model placeholder is unresolved: {model!r}.")
        elif model.startswith("${"):
            _add(checks, "warning", "model_env_based", f"Model is env-based and must be resolved before live run: {model!r}.")

    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    _check(raw.get("scientific_evidence") is not True, checks, "scientific_evidence_false_before_run", "scientific_evidence must remain false before run review.")
    level = str(raw.get("scientific_evidence_level") or "")
    if level.lower() in {"supported", "full", "paper_eligible"}:
        _add(checks, "blocker", "scientific_evidence_level_too_strong", f"scientific_evidence_level must not be {level!r} before post-run review.")
    scope = str(raw.get("evidence_scope") or "")
    _check(scope in PENDING_SCOPES, checks, "pending_evidence_scope", f"evidence_scope should be pending verification, got {scope!r}.")
    _check((root / "docs/POST_PROVIDER_PILOT_CHECKLIST.md").exists(), checks, "post_run_checklist_exists", "Post-run checklist missing.")
    _check(bool(raw.get("require_dry_run_before_live", True)), checks, "dry_run_required", "Dry run should be required before live run.", warning=True)
    if is_template and not raw.get("template_only", True):
        _add(checks, "warning", "template_only_flag_missing", "Template should set template_only: true.")
    max_inst = int(raw.get("max_instances") or limits.get("max_instances") or 999)
    if max_inst > 5:
        _add(checks, "blocker", "tiny_pilot_instance_cap", f"max_instances={max_inst} exceeds tiny pilot cap of 5.")
    if _api_key_in_yaml(path):
        _add(checks, "blocker", "api_key_in_config", "API keys must not appear in YAML; use environment variables only.")

    output_dir = Path(str(raw.get("output_dir") or "results"))
    run_name = str(raw.get("run_name") or path.stem)
    candidate = (output_dir if output_dir.is_absolute() else root / output_dir) / run_name
    if candidate.exists():
        _add(checks, "blocker", "output_dir_would_overwrite", f"Output directory already exists: {candidate}.")
    else:
        _add(checks, "informational", "output_dir_available", f"Output directory not present: {candidate}.")

    try:
        cost = estimate_run_cost(path, repo_root=root)
    except Exception as exc:  # pragma: no cover - defensive; still no provider calls
        cost = {"pricing_known": False, "warnings": [str(exc)]}
    if not cost.get("pricing_known"):
        _add(checks, "warning", "pricing_unknown", "Pricing is unknown or incomplete; do not assume zero cost.")

    leakage_gate = _leakage_gate_from_reports(root, reports_root=reports_root)
    if leakage_gate["must_fix_before_provider_pilot"] > 0:
        _add(
            checks,
            "blocker",
            "leakage_repair_must_fix",
            (
                f"{leakage_gate['must_fix_before_provider_pilot']} leakage cluster(s) must be fixed "
                "before provider pilot (see leakage_repair_plan / static_leakage reports)."
            ),
        )
    elif leakage_gate.get("answer_leakage_blockers", 0) > 0:
        _add(
            checks,
            "blocker",
            "answer_leakage_blockers",
            (
                f"{leakage_gate['answer_leakage_blockers']} true answer-leakage blocker cluster(s) remain."
            ),
        )

    blockers = [check for check in checks if check["severity"] == "blocker"]
    warnings = [check for check in checks if check["severity"] == "warning"]
    ready_for_approval_review = is_template and not blockers and _template_has_static_guards(raw)
    ready_for_dry_run = (
        not blockers
        and not is_template
        and approved_name
        and approval_state["dry_run_ready"]
        and leakage_gate["must_fix_before_provider_pilot"] == 0
        and leakage_gate.get("answer_leakage_blockers", 0) == 0
    )
    ready_for_live = (
        ready_for_dry_run
        and allow_paid
        and approval_state["live_ready"]
    )
    gate_summary = _gate_summary(
        checks=checks,
        is_template=is_template,
        ready_for_approval_review=ready_for_approval_review,
        ready_for_dry_run=ready_for_dry_run,
        ready_for_live=ready_for_live,
        approval=approval,
        approval_state=approval_state,
        allow_paid=allow_paid,
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static config preflight only; no API keys, providers, or benchmark runs are invoked.",
        "config_path": str(path),
        "checks": checks,
        "cost_summary": {
            "estimated_high_cost_usd": cost.get("estimated_high_cost_usd"),
            "pricing_known": cost.get("pricing_known"),
            "warnings": cost.get("warnings", []),
        },
        "verdicts": {
            "template_safe_but_not_runnable": gate_summary["gate_status"] == "template_safe_but_not_runnable",
            "ready_for_approval_review": gate_summary["gate_status"] == "ready_for_approval_review",
            "ready_for_dry_run": ready_for_dry_run,
            "ready_for_live_provider_run": ready_for_live,
            "blocked": gate_summary["gate_status"] == "blocked",
            "live_run_blocked": not ready_for_live,
            "paper_evidence_blocked_until_post_run_audit": True,
        },
        "leakage_gate": leakage_gate,
        "gate_summary": gate_summary,
        "gate_status": gate_summary["gate_status"],
        "blockers": blockers,
        "warnings": warnings,
    }


def provider_pilot_preflight_markdown(report: dict[str, Any]) -> str:
    verdicts = report["verdicts"]
    lines = [
        "# Provider Pilot Preflight",
        "",
        f"Generated: {report['generated_at']}",
        "",
        report["scope"],
        "",
        section_markdown(
            "Gate states",
            [
                "- `template_safe_but_not_runnable`: template has caps/safety fields; not executable.",
                "- `ready_for_approval_review`: non-template static fields ready for advisor/budget review.",
                "- `ready_for_dry_run`: approved copy + dry-run approval + leakage clear (still no live spend).",
                "- `ready_for_live_run`: approved copy + live approval + `allow_paid_calls=true` in approved copy only.",
                "- `blocked`: leakage, caps, approval, or safety check failed.",
            ],
        ),
        section_markdown(
            "Verdicts",
            [
                f"- Gate status: `{report.get('gate_status')}`",
                f"- Template safe (not runnable): `{verdicts['template_safe_but_not_runnable']}`",
                f"- Ready for approval review: `{verdicts['ready_for_approval_review']}`",
                f"- Ready for dry run: `{verdicts['ready_for_dry_run']}`",
                f"- Ready for live provider run: `{verdicts['ready_for_live_provider_run']}`",
                f"- Blocked: `{verdicts['blocked']}`",
                f"- Paper evidence blocked until post-run audit: `{verdicts.get('paper_evidence_blocked_until_post_run_audit', True)}`",
            ],
        ),
        section_markdown(
            "Exact next action before provider pilot",
            [f"- {report.get('gate_summary', {}).get('exact_next_action', 'Review provider-pilot blockers.')}"],
        ),
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        lines.append(f"- `{check['severity']}` `{check['id']}`: {check['message']}")
    lines.append("")
    return "\n".join(lines)


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _agent_runs(raw: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(raw.get("agent_runs"), list):
        return [row for row in raw["agent_runs"] if isinstance(row, dict)]
    return [{"agent": agent, "provider": raw.get("provider"), "model": raw.get("model")} for agent in raw.get("agents", [])]


def _trajectory_cap_present(raw: dict[str, Any]) -> bool:
    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    return any(raw.get(key) is not None for key in ("max_instances", "max_api_calls")) or any(
        limits.get(key) is not None for key in ("max_instances", "max_trajectories", "stop_after_trajectories")
    )


def _stop_conditions_present(raw: dict[str, Any]) -> bool:
    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    return bool(limits.get("stop_after_trajectories") or limits.get("max_runtime_minutes") or raw.get("max_steps"))


def _model_placeholder_unresolved(model: str) -> bool:
    lowered = model.lower()
    return "placeholder" in lowered or "set_before_run" in lowered or lowered in {"", "model", "default"}


def _approval_state(approval: dict[str, Any]) -> dict[str, bool]:
    advisor = bool(approval.get("advisor_approved")) or bool(approval.get("advisor_approval_id"))
    budget = bool(approval.get("budget_approved"))
    dry_run = bool(approval.get("approved_for_dry_run") and advisor and budget)
    live = bool(
        approval.get("approved_for_live_run")
        and advisor
        and budget
        and bool(approval.get("advisor_approval_id") or approval.get("approved_by"))
        and bool(approval.get("approval_date"))
    )
    approval_flags = {
        k: v
        for k, v in approval.items()
        if k
        in {
            "advisor_approved",
            "budget_approved",
            "approved_for_dry_run",
            "approved_for_live_run",
        }
    }
    return {
        "advisor_approved": advisor,
        "budget_approved": budget,
        "dry_run_ready": dry_run,
        "live_ready": live,
        "any_true": any(value is True for value in approval_flags.values()),
    }


def _template_has_static_guards(raw: dict[str, Any]) -> bool:
    return (
        raw.get("allow_paid_calls") is False
        and raw.get("scientific_evidence") is not True
        and _trajectory_cap_present(raw)
        and _stop_conditions_present(raw)
        and (
            raw.get("budget_cap_usd") is not None
            or (isinstance(raw.get("budget"), dict) and raw["budget"].get("max_total_usd") is not None)
        )
    )


def _check(condition: bool, checks: list[dict[str, Any]], check_id: str, message: str, *, warning: bool = False) -> None:
    if condition:
        _add(checks, "informational", check_id, "OK")
    else:
        _add(checks, "warning" if warning else "blocker", check_id, message)


def _add(checks: list[dict[str, Any]], severity: str, check_id: str, message: str) -> None:
    checks.append({"severity": severity, "id": check_id, "message": message})


def _api_key_in_yaml(path: Path) -> bool:
    text = path.read_text(encoding="utf-8").lower()
    markers = ("sk-", "api_key:", "apikey:", "openai_api_key", "anthropic_api_key", "gemini_api_key")
    return any(marker in text for marker in markers)


def _gate_summary(
    *,
    checks: list[dict[str, Any]],
    is_template: bool,
    ready_for_approval_review: bool,
    ready_for_dry_run: bool,
    ready_for_live: bool,
    approval: dict[str, Any],
    approval_state: dict[str, bool],
    allow_paid: bool,
) -> dict[str, Any]:
    blockers = [check for check in checks if check["severity"] == "blocker"]
    warnings = [check for check in checks if check["severity"] == "warning"]
    if blockers:
        gate_status = "blocked"
    elif ready_for_live:
        gate_status = "ready_for_live_run"
    elif ready_for_dry_run:
        gate_status = "ready_for_dry_run"
    elif is_template and ready_for_approval_review:
        gate_status = "template_safe_but_not_runnable"
    elif not is_template:
        gate_status = "ready_for_approval_review"
    else:
        gate_status = "blocked"
    return {
        "gate_status": gate_status,
        "blockers": blockers,
        "warnings": warnings,
        "required_human_actions": _human_actions(is_template, approval, approval_state, ready_for_dry_run, ready_for_live),
        "required_config_actions": _config_actions(checks, allow_paid),
        "required_validation_commands": [
            "python3 -m causal_agent_bench validate-config --config <approved_config>",
            "python3 -m causal_agent_bench provider-pilot-preflight --config <approved_config>",
        ],
        "forbidden_commands": [
            "python3 -m causal_agent_bench run --config ...",
            "make smoke",
            "make test",
            "python3 -m causal_agent_bench run-llm-judge ...",
            "python3 -m causal_agent_bench fill-paper-from-run --promote-to-supported ...",
        ],
        "exact_next_action": _exact_next_action(checks, is_template, ready_for_dry_run, ready_for_live, approval),
    }


def _leakage_gate_from_reports(root: Path, *, reports_root: Path | None = None) -> dict[str, int]:
    search_roots = []
    if reports_root is not None:
        search_roots.append(reports_root)
    search_roots.append(root)
    rel_paths = (
        "reports/leakage_repair_plan/leakage_repair_plan.json",
        "leakage_repair_plan/leakage_repair_plan.json",
        "static_leakage/static_leakage_report.json",
        "reports/static_leakage/static_leakage_report.json",
    )
    for base in search_roots:
        for rel in rel_paths:
            path = base / rel
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if "leakage_repair" in rel:
                summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
                must_fix = int(summary.get("must_fix_before_provider_pilot") or 0)
                answer_blockers = len(payload.get("top_answer_leakage_repairs") or [])
                if must_fix or answer_blockers:
                    return {
                        "must_fix_before_provider_pilot": must_fix,
                        "answer_leakage_blockers": answer_blockers,
                    }
            summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
            blocker_clusters = int(summary.get("blocker_cluster_count") or 0)
            answer_clusters = sum(
                1
                for row in payload.get("top_provider_pilot_blockers") or []
                if row.get("cluster_classification") == "answer_leakage"
            )
            if blocker_clusters or answer_clusters:
                return {
                    "must_fix_before_provider_pilot": blocker_clusters,
                    "answer_leakage_blockers": answer_clusters,
                }
    return {"must_fix_before_provider_pilot": 0, "answer_leakage_blockers": 0}


def _exact_next_action(
    checks: list[dict[str, Any]],
    is_template: bool,
    ready_for_dry_run: bool,
    ready_for_live: bool,
    approval: dict[str, Any],
) -> str:
    blockers = [check for check in checks if check["severity"] == "blocker"]
    leakage_blockers = [c for c in blockers if c["id"] in {"leakage_repair_must_fix", "answer_leakage_blockers"}]
    if leakage_blockers:
        return (
            "Fix true answer-leakage clusters (see answer_leakage_repair.md), rerun all-no-run-reports, "
            "then proceed to advisor review."
        )
    if is_template:
        return "Create an approved provider-pilot config copy only after advisor approval; keep templates non-runnable."
    if blockers:
        first = blockers[0]
        if "budget" in first["id"]:
            return "Add a tiny budget cap to the approved config candidate."
        if "trajectory" in first["id"] or "stop" in first["id"]:
            return "Add tiny trajectory/runtime stop caps to the approved config candidate."
        if "approval" in first["id"]:
            return "Complete advisor approval before treating this config as an approved provider-pilot candidate."
        return f"Fix provider preflight blocker `{first['id']}`."
    if ready_for_live:
        return "Run final human review of the approved live-run config before any provider execution."
    if ready_for_dry_run:
        return "Run validate-config on the approved config, then complete the no-run preflight review."
    if not approval.get("advisor_approval_id"):
        return "Complete advisor approval review before any provider dry-run."
    return "Review warnings and rerun provider-pilot preflight."


def _human_actions(
    is_template: bool,
    approval: dict[str, Any],
    approval_state: dict[str, bool],
    ready_for_dry_run: bool,
    ready_for_live: bool,
) -> list[str]:
    actions = []
    if is_template:
        actions.append("Advisor must approve creating a separate approved config copy.")
    if not approval_state.get("advisor_approved") and not ready_for_dry_run:
        actions.append("Record advisor approval before provider spend.")
    if ready_for_dry_run and not ready_for_live:
        actions.append("Review dry-run-only approval scope before live provider execution.")
    return actions


def _config_actions(checks: list[dict[str, Any]], allow_paid: bool) -> list[str]:
    actions = []
    for check in checks:
        if check["severity"] != "blocker":
            continue
        if check["id"] in {"budget_cap_present", "trajectory_cap_present", "stop_conditions_present", "model_placeholder_unresolved"}:
            actions.append(check["message"])
    if allow_paid:
        actions.append("Confirm allow_paid_calls is enabled only in an approved live-run copy.")
    return actions
