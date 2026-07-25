"""Static hardener for candidate provider-pilot configs.

This validator is intentionally **stricter** than provider_pilot_preflight: it
operates on *candidate* approved-copy configs before they reach preflight. It
verifies all the structural safety fields a candidate must have, regardless of
approval state, and writes a report that lists every missing field.

It never calls a provider, never creates an approved config, and never sets
``allow_paid_calls=true``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.safety.common import section_markdown, write_dual_report
from causal_agent_bench.safety.provider_pilot_preflight import (
    PENDING_SCOPES,
    _agent_runs,
    _approval_state,
    _stop_conditions_present,
    _trajectory_cap_present,
)

REQUIRED_SAFETY_FIELDS = (
    "run_name",
    "output_dir",
    "evidence_scope",
)
FORBIDDEN_TRUE_FIELDS = (
    "scientific_evidence",
    "paper_eligible",
    "promote_to_supported",
)
APPROVAL_FIELDS = (
    "advisor_approved",
    "advisor_approval_id",
    "budget_approved",
    "approved_for_dry_run",
)


def build_provider_pilot_config_hardening_report(
    repo_root: str | Path,
    *,
    config_path: str | Path,
    output_dir: str | Path = "reports/provider_pilot_config_hardening",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    config = Path(config_path)
    if not config.is_absolute():
        config = root / config
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    checks: list[dict[str, Any]] = []
    raw: dict[str, Any] = {}
    if not config.exists():
        _add(checks, "blocker", "config_missing", "Candidate config file does not exist.")
    else:
        try:
            parsed = yaml.safe_load(config.read_text(encoding="utf-8"))
            raw = parsed if isinstance(parsed, dict) else {}
        except yaml.YAMLError as exc:
            _add(checks, "blocker", "config_not_parseable", f"YAML parse error: {exc}")

    is_template = "template" in config.name.lower() or "template" in str(raw.get("run_name", "")).lower()
    if is_template:
        _add(checks, "blocker", "template_used_as_candidate", "Template configs are not allowed as approved candidates. Create a copy first.")

    for field in REQUIRED_SAFETY_FIELDS:
        if not raw.get(field):
            _add(checks, "blocker", f"missing_required_field:{field}", f"Required field `{field}` missing.")

    for field in FORBIDDEN_TRUE_FIELDS:
        if raw.get(field) is True:
            _add(checks, "blocker", f"forbidden_field_true:{field}", f"Forbidden field `{field}` must not be true.")

    allow_paid = bool(raw.get("allow_paid_calls", False))
    approved_copy = "approved" in config.name.lower() or "approved" in str(raw.get("run_name", "")).lower()
    if allow_paid and not approved_copy:
        _add(checks, "blocker", "paid_calls_not_in_approved_copy", "allow_paid_calls=true requires an approved config copy.")

    budget = raw.get("budget") if isinstance(raw.get("budget"), dict) else {}
    if not (raw.get("budget_cap_usd") is not None or budget.get("max_total_usd") is not None):
        _add(checks, "blocker", "missing_budget_cap", "Budget cap is missing. Add `budget_cap_usd` or `budget.max_total_usd`.")

    if not _trajectory_cap_present(raw):
        _add(checks, "blocker", "missing_trajectory_cap", "Trajectory cap missing. Add `limits.max_instances` or `limits.max_trajectories`.")

    if not _stop_conditions_present(raw):
        _add(checks, "blocker", "missing_stop_conditions", "Stop conditions missing. Add `limits.stop_after_trajectories` or `limits.max_runtime_minutes`.")

    scope = str(raw.get("evidence_scope") or "")
    if scope and scope not in PENDING_SCOPES:
        _add(
            checks,
            "warning",
            "evidence_scope_not_pending",
            f"evidence_scope `{scope}` is not in {sorted(PENDING_SCOPES)}.",
        )

    approval = raw.get("approval") if isinstance(raw.get("approval"), dict) else {}
    approval_state = _approval_state(approval)
    for field in APPROVAL_FIELDS:
        if field not in approval and not _approval_state(approval).get(field, False):
            _add(checks, "warning", f"approval_field_missing:{field}", f"Approval field `{field}` missing.")

    for agent_run in _agent_runs(raw):
        agent = str(agent_run.get("agent") or "")
        provider = str(agent_run.get("provider") or raw.get("provider") or "")
        model = str(agent_run.get("model") or raw.get("model") or "")
        if any(marker in agent.lower() for marker in ("oracle", "mock", "stub")):
            _add(checks, "blocker", "non_evidence_agent", f"Agent `{agent}` is oracle/mock/stub-like.")
        if not provider:
            _add(checks, "blocker", "missing_provider", "agent_run is missing `provider`.")
        if not model:
            _add(checks, "blocker", "missing_model", f"agent_run for `{agent}` is missing `model`.")

    blockers = [c for c in checks if c["severity"] == "blocker"]
    warnings = [c for c in checks if c["severity"] == "warning"]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static candidate provider-pilot config hardening only; no provider/preflight execution.",
        "config_path": str(config),
        "summary": {
            "blockers": len(blockers),
            "warnings": len(warnings),
            "informational": sum(1 for c in checks if c["severity"] == "informational"),
            "check_count": len(checks),
            "is_template": is_template,
            "allow_paid_calls": allow_paid,
            "approved_copy_name": approved_copy,
            "approval_state": approval_state,
        },
        "verdicts": {
            "candidate_safe_to_send_to_preflight": len(blockers) == 0,
            "blocked": bool(blockers),
            "needs_review": bool(blockers or warnings),
            "any_forbidden_true": any(c["id"].startswith("forbidden_field_true") for c in blockers),
        },
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
    }
    md = config_hardening_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="provider_pilot_config_hardening",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def config_hardening_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Provider-Pilot Config Hardening",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        f"Config: `{payload['config_path']}`",
        "",
        section_markdown(
            "Summary",
            [
                f"- Blockers: {summary['blockers']}",
                f"- Warnings: {summary['warnings']}",
                f"- Informational: {summary['informational']}",
                f"- Is template: `{summary['is_template']}`",
                f"- allow_paid_calls: `{summary['allow_paid_calls']}`",
                f"- Approved-copy name: `{summary['approved_copy_name']}`",
            ],
        ),
        section_markdown(
            "Verdicts",
            [
                f"- Candidate safe to send to preflight: `{payload['verdicts']['candidate_safe_to_send_to_preflight']}`",
                f"- Blocked: `{payload['verdicts']['blocked']}`",
                f"- Any forbidden field set true: `{payload['verdicts']['any_forbidden_true']}`",
            ],
        ),
        "## Checks",
        "",
    ]
    if not payload["checks"]:
        lines.append("- (none)")
    for check in payload["checks"]:
        lines.append(f"- `{check['severity']}` `{check['id']}`: {check['message']}")
    lines.append("")
    return "\n".join(lines)


def _add(checks: list[dict[str, Any]], severity: str, check_id: str, message: str) -> None:
    checks.append({"severity": severity, "id": check_id, "message": message})
