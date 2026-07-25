"""Advisor review packet generator for pre-provider-pilot decisions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DECISION_OPTIONS = [
    "approve tiny provider dry-run (after leakage repair + APPROVED config)",
    "request dataset fixes first",
    "request human-validation protocol changes",
    "defer provider spend",
]

APPROVE_NOT_YET = [
    "Live provider pilot with paid calls",
    "Promoting C1–C8 or C10 to supported",
    "Filling empirical results tables/figures",
    "Public release claiming completed benchmark",
    "Main multi-provider 500-run before tiny pilot review",
]


def build_advisor_review_packet(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports",
    output_dir: str | Path = "reports/advisor_review",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    context = _context(root, reports)
    packet_path = out / "advisor_review_packet.md"
    checklist_path = out / "advisor_review_checklist.md"
    summary_path = out / "advisor_one_page_summary.md"
    packet_path.write_text(_packet_markdown(generated_at, context), encoding="utf-8")
    checklist_path.write_text(_checklist_markdown(generated_at, context), encoding="utf-8")
    summary_path.write_text(_one_page_summary(generated_at, context), encoding="utf-8")
    evidence_state = context.get("evidence_state") or {}
    summary = {
        "paper_eligible_runs": int(evidence_state.get("paper_eligible_runs", 0) or 0),
        "eligible_paper_assets": int(evidence_state.get("eligible_paper_assets", 0) or 0),
        "blocked_claim_count": len(context.get("blocked_claims") or []),
        "provider_pilot_blocked": True,
        "empirical_paper_blocked": True,
        "public_release_blocked": True,
    }
    verdicts = {
        "advisor_review_ready": summary["paper_eligible_runs"] == 0
        and summary["eligible_paper_assets"] == 0
        and summary["provider_pilot_blocked"] is True,
        "empirical_results_claimed": False,
        "provider_pilot_already_approved": False,
        "claims_marked_supported": False,
        "packet_is_no_run_only": True,
    }
    manifest = {
        "generated_at": generated_at,
        "scope": "Advisor review packet only; no provider pilot is approved by this file.",
        "files": {
            "packet": str(packet_path),
            "checklist": str(checklist_path),
            "one_page_summary": str(summary_path),
        },
        "current_project_status": context["project_status"],
        "blocked_claims": context["blocked_claims"],
        "decision_options": DECISION_OPTIONS,
        "summary": summary,
        "verdicts": verdicts,
        "hard_rules": {
            "empirical_results_claimed": False,
            "provider_pilot_already_approved": False,
            "claims_marked_supported": False,
            "no_provider_calls_in_no_run_lane": True,
            "no_paid_calls_in_no_run_lane": True,
        },
    }
    manifest_path = out / "advisor_review_manifest.json"
    manifest["report_paths"] = {**manifest["files"], "manifest": str(manifest_path)}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def _one_page_summary(generated_at: str, context: dict[str, Any]) -> str:
    ev = context["evidence_state"]
    return "\n".join(
        [
            "# Advisor One-Page Summary",
            "",
            f"Generated: {generated_at}",
            "",
            "**No empirical claims yet.** This is benchmark infrastructure, not a completed empirical paper.",
            "",
            "## What Causal Agent Bench Is",
            "",
            "A paired clean/intervention benchmark scaffold for tool-using agents, with strong no-run safety governance.",
            "",
            "## Current Evidence (honest)",
            "",
            f"- Paper-eligible runs: **{ev['paper_eligible_runs']}**",
            f"- Eligible paper assets: **{ev['eligible_paper_assets']}**",
            "- C1–C8: planned / unsupported",
            "- C9: engineering_only (CI/smoke reproducibility)",
            "- C10: planned / unsupported",
            "",
            "## What Is Validated (no-run)",
            "",
            "- Static dataset, leakage, tool-schema, and config preflight tooling",
            "- Claim ledger and export guards block overclaiming",
            "",
            "## What Is Blocked",
            "",
            f"- {context['blocked_summary']}",
            f"- Provider pilot: {context['provider_gate_summary']}",
            "",
            "## Cost / Time (tiny pilot, indicative)",
            "",
            context["cost_risk_summary"],
            "",
            "## Advisor May Approve",
            "",
            "- Method-only review and pilot scale/budget discussion",
            "- Leakage repair plan review",
            "- Creating `provider_pilot_tiny_APPROVED.yaml` **after** blockers clear",
            "",
            "## Do Not Approve Yet",
            "",
        ]
        + [f"- {item}" for item in APPROVE_NOT_YET]
        + [
            "",
            "Signature: ____________________  Date: ____________",
            "",
        ]
    )


def _packet_markdown(generated_at: str, context: dict[str, Any]) -> str:
    blocked = context["blocked_claims"]
    lines = [
        "# Advisor Review Packet",
        "",
        f"Generated: {generated_at}",
        "",
        "Status: pre-provider-pilot. **No empirical claims yet.** This packet does not claim empirical results and does not approve provider spend.",
        "",
        "See also: `advisor_one_page_summary.md` for a one-page handout.",
        "",
        "## Current Project Status",
        "",
        context["project_status"],
        "",
        "## No-Run Evidence State",
        "",
        f"- Paper-eligible runs: {context['evidence_state']['paper_eligible_runs']}",
        f"- Eligible paper assets: {context['evidence_state']['eligible_paper_assets']}",
        "- C1-C8: planned / unsupported",
        "- C9: engineering_only",
        "- C10: planned / unsupported",
        "",
        "## Validated So Far",
        "",
    ]
    lines.extend(f"- {item}" for item in context["validated"])
    lines.extend(["", "## Not Yet Validated", ""])
    lines.extend(f"- {item}" for item in context["not_validated"])
    lines.extend(
        [
            "",
            "## Provider Pilot Objective",
            "",
            "Run a tiny, explicitly approved provider-backed dry-run only after static blockers and advisor concerns are resolved.",
            "",
            "## Claims That Remain Blocked",
            "",
        ]
    )
    lines.extend(f"- `{claim}`" for claim in blocked)
    lines.extend(
        [
            "",
            "## Expected Cost and Risk Summary",
            "",
            context["cost_risk_summary"],
            "",
            "## Expected Runtime (indicative, not measured here)",
            "",
            context["runtime_summary"],
            "",
            "## Provider Pilot Risk Summary",
            "",
            context["provider_risk_summary"],
            "",
            "## What Advisor Must Approve",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in context["advisor_must_approve"])
    lines.extend(
        [
            "",
            "## What Not to Approve Yet",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in APPROVE_NOT_YET)
    lines.extend(
        [
            "",
            "## Dataset and Intervention Quality Summary",
            "",
            context["dataset_quality_summary"],
            "",
            "## Human-Validation Plan",
            "",
            "Use the existing protocol/templates for a dry-run review first; do not claim C10 until completed human-validation artifacts exist.",
            "",
            "## Risks and Mitigations",
            "",
            "- Risk: provider spend before dataset repairs. Mitigation: require repair plan and preflight checks.",
            "- Risk: unsupported paper language. Mitigation: keep claim ledger blocked and use method-only wording.",
            "- Risk: intervention leakage or multi-factor changes. Mitigation: run taxonomy-backed static validators and human review.",
            "",
            "## Decision Options",
            "",
        ]
    )
    lines.extend(f"- {option}" for option in DECISION_OPTIONS)
    lines.extend(
        [
            "",
            "## Signature",
            "",
            "- Advisor name: ______________________________",
            "- Decision: ______________________________",
            "- Date: ______________________________",
            "- Notes: ______________________________",
            "",
        ]
    )
    return "\n".join(lines)


def _checklist_markdown(generated_at: str, context: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Advisor Review Checklist",
            "",
            f"Generated: {generated_at}",
            "",
            "**Disclaimer: No empirical results exist. Checking this list does not approve paid provider spend.**",
            "",
            "## Decision checklist",
            "",
            "- [ ] I understand there are **zero** paper-eligible runs and **zero** eligible empirical assets.",
            "- [ ] I will not approve empirical claim promotion (C1–C8, C10).",
            "- [ ] Leakage repair reviewed; true answer-leakage blockers addressed.",
            "- [ ] Provider template kept non-runnable (`allow_paid_calls=false`).",
            "",
            "## Approval checklist (only after blockers clear)",
            "",
            "- [ ] Repair plan reviewed.",
            "- [ ] Dataset/intervention blockers reviewed.",
            "- [ ] Gold-output and tool-schema validators reviewed.",
            "- [ ] Static leakage report reviewed.",
            "- [ ] Provider pilot preflight reviewed.",
            "- [ ] Cost cap and stop conditions reviewed.",
            "- [ ] `allow_paid_calls` remains false in templates.",
            "- [ ] Claims C1-C8 and C10 remain blocked.",
            "- [ ] C9 remains engineering-only.",
            "- [ ] Human-validation protocol reviewed.",
            "- [ ] Decision option selected explicitly.",
            "",
            "Signature: ______________________________",
            "Date: ______________________________",
            "",
            "This checklist does not approve a live provider pilot by itself.",
            "",
        ]
    )


def _context(root: Path, reports: Path) -> dict[str, Any]:
    run_health = _find_json(reports, "run_health_report.json") or {}
    assets = _find_json(reports, "paper_asset_eligibility.json") or {}
    repair = _find_json(reports, "repair_plan.json") or {}
    claim_matrix = _find_json(reports, "claim_evidence_matrix.json") or _read_json(root / "docs/claim_ledger.json") or {}
    blocked_claims = _blocked_claims(claim_matrix)
    preflight = _find_json(reports, "provider_pilot_preflight.json") or {}
    cost = _find_json(reports, "run_cost_estimate.json") or {}
    quality = _find_json(reports, "benchmark_quality_report.json") or {}
    leakage = _find_json(reports, "static_leakage_report.json") or {}
    leakage_plan = _find_json(reports, "leakage_repair_plan.json") or _find_json(reports, "leakage_repair_plan/leakage_repair_plan.json") or {}
    preflight = _find_json(reports, "provider_pilot_preflight.json") or {}
    blocker_clusters = int((leakage.get("summary") or {}).get("blocker_cluster_count") or 0)
    must_fix = int((leakage_plan.get("summary") or {}).get("must_fix_before_provider_pilot_count") or blocker_clusters)
    evidence_state = {
        "paper_eligible_runs": int((run_health.get("summary") or {}).get("paper_eligible_count") or 0),
        "eligible_paper_assets": int(assets.get("eligible_count") or 0),
        "leakage_blocker_clusters": blocker_clusters,
    }
    validated = [
        "No-run evidence guardrails and claim ledger reviewed.",
        "Static config/preflight checks available when reports are present.",
        "Repair plan generated from available no-run reports." if repair else "Repair plan not yet generated.",
    ]
    not_validated = [
        "No provider-backed model behavior has been measured.",
        "No empirical paper results are available.",
        "Human validation is not complete.",
        "Provider pilot is not approved by this packet.",
    ]
    cost_summary = (cost.get("summary") or cost.get("cost_summary") or {})
    preflight_verdicts_raw = preflight.get("verdicts")
    preflight_verdicts = preflight_verdicts_raw if isinstance(preflight_verdicts_raw, dict) else {}
    gate_raw = preflight.get("gate_summary")
    gate = gate_raw if isinstance(gate_raw, dict) else {}
    return {
        "project_status": (
            "Benchmark infrastructure with method-only documentation. "
            "Not an empirical paper; not submission-ready for results claims."
        ),
        "evidence_state": evidence_state,
        "blocked_claims": blocked_claims,
        "validated": validated,
        "not_validated": not_validated,
        "blocked_summary": (
            f"{must_fix} leakage cluster(s) before provider pilot; no provider-backed runs; no human annotations."
        ),
        "provider_gate_summary": gate.get("exact_next_action") or "Provider pilot blocked (template + leakage + no APPROVED config).",
        "advisor_must_approve": [
            "Pilot trajectory cap and budget ceiling for tiny pilot only",
            "Separate APPROVED config copy (never run template in place)",
            "Explicit decision to spend after leakage repair",
            "Human-validation protocol scope (C3/C10 remain blocked until data exists)",
        ],
        "cost_risk_summary": (
            f"Tiny pilot (5 traj) estimated high bound: ~${cost_summary.get('estimated_high_cost_usd', 'unknown')} USD. "
            f"Live provider ready per preflight: {preflight_verdicts.get('ready_for_live_provider_run', False)}. "
            "Requires advisor sign-off and APPROVED config."
        ),
        "runtime_summary": (
            "- `all-no-run-reports`: ~1–2 min\n"
            "- `validate-config` / `plan-run` / `estimate-run-cost`: seconds\n"
            "- Tiny provider pilot (5 instances): ~5–30 min (model-dependent)\n"
            "- 20-task pilot: ~30–120 min\n"
            "- Local LLM 20-task: hours; often interrupted on laptop CPU"
        ),
        "provider_risk_summary": (
            "- Paid calls disabled in template (`allow_paid_calls=false`).\n"
            f"- True leakage blocker clusters: {blocker_clusters}.\n"
            "- No APPROVED config exists yet.\n"
            "- Post-run evidence audit required before any claim promotion."
        ),
        "dataset_quality_summary": (
            f"Static quality gate (structure): {(quality.get('verdicts') or {}).get('benchmark_quality_ready_for_provider_pilot', 'needs_review')}. "
            f"Leakage blocker clusters: {blocker_clusters}. "
            "Instruction-parameter date overlap is calibrated as non-blocking."
        ),
    }


def _blocked_claims(payload: dict[str, Any]) -> list[str]:
    claims_raw = payload.get("claims")
    claims = claims_raw if isinstance(claims_raw, list) else []
    out = []
    for row in claims:
        claim_id = str(row.get("claim_id") or "")
        status = str(row.get("status") or "planned")
        if claim_id and status != "supported":
            out.append(f"{claim_id}: {status}")
    if not out:
        out = [*(f"C{i}: planned / unsupported" for i in range(1, 9)), "C9: engineering_only", "C10: planned / unsupported"]
    return out


def _find_json(reports: Path, filename: str) -> dict[str, Any] | None:
    direct = reports / filename
    if direct.exists():
        return _read_json(direct)
    for path in sorted(reports.glob(f"**/{filename}")) if reports.exists() else []:
        return _read_json(path)
    return None


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
