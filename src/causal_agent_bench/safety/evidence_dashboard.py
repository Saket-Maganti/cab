"""Evidence dashboard index for no-run governance reports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORT_FILES = {
    "run_health": "run_health_report.json",
    "paper_assets": "paper_asset_eligibility.json",
    "claim_evidence": "claim_evidence_matrix.json",
    "paper_todo": "paper_todo_inventory.json",
    "benchmark_quality": "benchmark_quality_report.json",
    "intervention_isolation": "intervention_isolation_report.json",
    "synthetic_fixtures": "synthetic_fixture_metric_report.json",
    "human_validation": "human_validation_dry_run_packet.json",
    "cost_estimate": "run_cost_estimate.json",
    "release_readiness": "release_readiness_report.json",
    "provider_preflight": "provider_pilot_preflight.json",
    "dataset_triage": "dataset_issue_triage.json",
    "config_lint": "config_metadata_lint.json",
    "repair_plan": "repair_plan.json",
    "benchmark_cards": "benchmark_cards_manifest.json",
    "gold_outputs": "gold_output_validation.json",
    "tool_schemas": "tool_schema_validation.json",
    "static_leakage": "static_leakage_report.json",
    "benchmark_manifest": "benchmark_manifest.json",
    "config_profiles": "config_profiles.json",
    "advisor_review": "advisor_review_manifest.json",
    "paper_readiness": "paper_readiness_map.json",
    "report_quality": "report_quality_check.json",
    "leakage_repair_plan": "leakage_repair_plan.json",
    "leakage_patch_validation": "leakage_patch_validation.json",
    "leakage_suppression_registry": "leakage_suppression_registry.json",
    "leakage_patch_apply": "leakage_patch_apply_report.json",
    "manual_repair_preview": "manual_repair_preview.json",
    "reviewed_ops_template": "reviewed_ops_template.json",
    "pair_link_validation": "pair_link_validation.json",
    "provider_pilot_config_hardening": "provider_pilot_config_hardening.json",
    "reproducibility_manifest": "reproducibility_manifest.json",
    "release_blocker_report": "release_blocker_report.json",
    "next_action_plan": "next_action_plan.json",
    "readiness_war_room": "readiness_war_room.json",
    "governance_os": "governance_os.json",
}


def build_evidence_dashboard(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports",
    output_dir: str | Path = "reports/evidence_dashboard",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    entries = {name: _entry(name, reports / filename) for name, filename in REPORT_FILES.items()}
    evidence_state = _evidence_state(entries)
    blockers = _blockers(entries, evidence_state)
    provider_gate = _provider_pilot_gate(entries)
    static_leakage_summary = _static_leakage_summary(entries)
    leakage_repair_summary = _leakage_repair_summary(entries)
    top_leakage = _top_leakage_root_causes(entries)
    top_actions = _next_10_actions(entries, provider_gate)
    readiness_state = _readiness_state(entries, provider_gate, evidence_state, blockers)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static dashboard index only; no claims are promoted and no reports are treated as empirical evidence.",
        "current_evidence_state": evidence_state,
        "provider_pilot_gate": provider_gate,
        "current_readiness_state": readiness_state,
        "static_leakage_summary": static_leakage_summary,
        "leakage_repair_plan_summary": leakage_repair_summary,
        "top_leakage_root_causes": top_leakage,
        "next_required_action": _next_action(evidence_state, blockers, provider_gate),
        "top_10_actions": top_actions,
        "next_10_actions": top_actions,
        "root_cause_blockers": _root_cause_blockers(entries),
        "do_not_run_yet": _do_not_run_yet(),
        "what_is_safe_to_do_now": _safe_to_do_now(),
        "what_is_still_not_evidence": _still_not_evidence(),
        "biggest_blockers": blockers[:12],
        "reports": entries,
    }
    json_path = out / "index.json"
    md_path = out / "index.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(evidence_dashboard_markdown(payload), encoding="utf-8")
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def evidence_dashboard_markdown(payload: dict[str, Any]) -> str:
    state = payload["current_evidence_state"]
    lines = [
        "# Evidence Dashboard",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        "## Current Evidence State",
        "",
        f"- Paper-eligible runs: {state['paper_eligible_runs']}",
        f"- Eligible paper assets: {state['eligible_paper_assets']}",
        f"- C1-C8: {state['C1_C8_status']}",
        f"- C9: {state['C9_status']}",
        f"- C10: {state['C10_status']}",
        "",
        "Current reports are static/no-run aids. They do not support empirical claims.",
        "",
        "## Provider Pilot Gate",
        "",
        f"- Gate status: `{payload['provider_pilot_gate']['gate_status']}`",
        f"- Blocked: `{payload['provider_pilot_gate']['blocked']}`",
        f"- Exact next action: {payload['provider_pilot_gate']['exact_next_action']}",
        "",
        "## Static Leakage Summary",
        "",
        f"- Raw findings: {payload['static_leakage_summary']['raw_finding_count']}",
        f"- Root-cause clusters: {payload['static_leakage_summary']['cluster_count']}",
        f"- Suppressed/deduplicated symptoms: {payload['static_leakage_summary']['suppressed_symptom_count']}",
        f"- Blockers: {payload['static_leakage_summary']['blockers']}",
        f"- Blocker clusters: {payload['static_leakage_summary']['blocker_cluster_count']}",
        f"- False-positive candidate clusters: {payload['static_leakage_summary']['false_positive_candidate_count']}",
        f"- Needs-review clusters: {payload['static_leakage_summary']['needs_review_count']}",
        f"- Classification counts: {payload['static_leakage_summary']['classification_counts']}",
        "",
        "## Leakage Repair Plan",
        "",
        f"- Repair clusters: {payload['leakage_repair_plan_summary']['cluster_count']}",
        f"- Must fix before provider pilot: {payload['leakage_repair_plan_summary']['must_fix_before_provider_pilot_count']}",
        f"- Candidate auto-patch operations: {payload['leakage_repair_plan_summary']['candidate_auto_patch_count']}",
        f"- Manual-review operations: {payload['leakage_repair_plan_summary']['manual_review_count']}",
        f"- Patch manifest valid: `{payload['leakage_repair_plan_summary']['patch_manifest_valid']}`",
        "",
        "## Top True Leakage Blockers",
        "",
    ]
    if not payload["top_leakage_root_causes"]:
        lines.append("- (none)")
    for row in payload["top_leakage_root_causes"][:10]:
        lines.append(
            f"- `{row.get('root_cause_id')}` [{row.get('leakage_risk') or row.get('severity')}] "
            f"{row.get('root_cause_title')} ({row.get('symptom_count')} symptoms; "
            f"class={row.get('cluster_classification')})"
        )
    lines.extend(
        [
            "",
        f"Next required action: {payload['next_required_action']}",
        "",
        "## Top 10 Actions",
        "",
        ]
    )
    if not payload.get("top_10_actions"):
        lines.append("- (none)")
    for action in payload.get("top_10_actions", [])[:10]:
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## Root Cause Blockers",
            "",
        ]
    )
    if not payload["root_cause_blockers"]:
        lines.append("- (none)")
    for blocker in payload["root_cause_blockers"][:10]:
        lines.append(
            f"- `{blocker.get('root_cause_id')}` [{blocker.get('severity')}] "
            f"{blocker.get('root_cause_title')} ({blocker.get('symptom_count')} symptoms)"
        )
    readiness = payload.get("current_readiness_state") or {}
    lines.extend(
        [
            "",
            "## Current Readiness State",
            "",
            f"- Advisor review: `{readiness.get('advisor_review_readiness', 'unknown')}`",
            f"- Provider dry-run: `{readiness.get('provider_dry_run_readiness', 'blocked')}`",
            f"- Provider live run: `{readiness.get('provider_live_run_readiness', 'blocked')}`",
            f"- Public release: `{readiness.get('public_release_readiness', 'blocked')}`",
            f"- Empirical paper: `{readiness.get('empirical_paper_readiness', 'blocked')}`",
            f"- Paper readiness map blocked sections: {readiness.get('paper_readiness_map_blocked_sections', 0)}",
        ]
    )
    lines.extend(["", "## Do Not Run Yet", ""])
    for item in payload["do_not_run_yet"]:
        lines.append(f"- {item}")
    lines.extend(["", "## What Is Safe To Do Now", ""])
    for item in payload["what_is_safe_to_do_now"]:
        lines.append(f"- {item}")
    lines.extend(["", "## What Is Still Not Evidence", ""])
    for item in payload["what_is_still_not_evidence"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Biggest Blockers", ""])
    if not payload["biggest_blockers"]:
        lines.append("- (none)")
    for blocker in payload["biggest_blockers"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Reports", "", "| Report | Badge | Path | Summary |", "|---|---|---|---|"])
    for name, entry in payload["reports"].items():
        lines.append(f"| `{name}` | `{entry['badge']}` | `{entry.get('path') or '(missing)'}` | {entry['summary']} |")
    lines.append("")
    return "\n".join(lines)


def _entry(name: str, path: Path) -> dict[str, Any]:
    path = _find_report(path.parent, path.name) or path
    payload = _read_json(path)
    if payload is None:
        return {"badge": "needs_review", "path": str(path), "present": False, "summary": "report missing"}
    badge, summary = _badge_and_summary(name, payload)
    return {"badge": badge, "path": str(path), "present": True, "summary": summary, "payload": _small_payload(name, payload)}


def _badge_and_summary(name: str, payload: dict[str, Any]) -> tuple[str, str]:
    if name == "run_health":
        summary = payload.get("summary", {})
        count = summary.get("paper_eligible_count", 0)
        if summary.get("index_stale"):
            indexed = summary.get("indexed_run_count", count)
            live = summary.get("live_run_count", indexed)
            return (
                "needs_review",
                f"STALE INDEX: {indexed} indexed vs {live} on disk — run `index-runs`",
            )
        return ("safe" if count else "no_evidence", f"paper_eligible_count={count}")
    if name == "paper_assets":
        count = payload.get("eligible_count", 0)
        return ("safe" if count else "no_evidence", f"eligible_count={count}")
    if name == "claim_evidence":
        statuses = {row.get("claim_id"): row.get("status") for row in payload.get("claims", [])}
        empirical_supported = any(statuses.get(f"C{i}") == "supported" for i in range(1, 9))
        return ("blocked" if not empirical_supported else "safe", f"C9={statuses.get('C9')}, empirical_supported={empirical_supported}")
    if name == "benchmark_quality":
        score = payload.get("summary", {}).get("scores", {}).get("overall_quality_score")
        ready = payload.get("verdicts", {}).get("benchmark_quality_ready_for_provider_pilot")
        return ("safe" if ready else "needs_review", f"overall_score={score}")
    if name == "intervention_isolation":
        score = payload.get("summary", {}).get("isolation_score")
        return ("needs_review" if payload.get("summary", {}).get("warnings", 0) else "safe", f"isolation_score={score}")
    if name == "synthetic_fixtures":
        failed = payload.get("summary", {}).get("failed", 0)
        return ("safe" if failed == 0 else "needs_review", f"failed={failed}")
    if name == "release_readiness":
        verdict = payload.get("verdicts", {}).get("ready_for_empirical_paper_submission")
        return ("blocked" if not verdict else "safe", f"empirical_submission={verdict}")
    if name == "provider_preflight":
        blocked = payload.get("verdicts", {}).get("blocked", True)
        return ("blocked" if blocked else "safe", f"blocked={blocked}")
    if name == "config_lint":
        issues = payload.get("issue_count", 0)
        return ("needs_review" if issues else "safe", f"issues={issues}")
    if name == "dataset_triage":
        issues = payload.get("total_issues", 0)
        return ("needs_review" if issues else "safe", f"issues={issues}")
    if name == "repair_plan":
        count = payload.get("summary", {}).get("repair_item_count", len(payload.get("items", [])))
        top = (payload.get("items") or [{}])[0].get("readiness_gate") if payload.get("items") else "none"
        return ("needs_review" if count else "safe", f"items={count}, top_gate={top}")
    if name == "benchmark_cards":
        hard_rules = payload.get("hard_rules", {})
        promoted = hard_rules.get("claims_promoted", False)
        return ("safe" if not promoted else "blocked", "pre-provider-pilot cards")
    if name == "gold_outputs":
        blockers = payload.get("summary", {}).get("blockers", 0)
        return ("blocked" if blockers else "safe", f"blockers={blockers}")
    if name == "tool_schemas":
        blockers = payload.get("summary", {}).get("blockers", 0)
        return ("blocked" if blockers else "safe", f"blockers={blockers}")
    if name == "static_leakage":
        summary = payload.get("summary", {})
        blockers = summary.get("blockers", 0)
        clusters = summary.get("cluster_count", payload.get("cluster_count", 0))
        raw = summary.get("raw_finding_count", payload.get("raw_finding_count", 0))
        return ("blocked" if blockers else "safe", f"blockers={blockers}, raw={raw}, clusters={clusters}")
    if name == "benchmark_manifest":
        blocked = payload.get("readiness", {}).get("empirical_paper_blocked", True)
        return ("blocked" if blocked else "safe", f"empirical_paper_blocked={blocked}")
    if name == "config_profiles":
        issues = payload.get("summary", {}).get("issue_count", 0)
        return ("needs_review" if issues else "safe", f"issues={issues}")
    if name == "advisor_review":
        return ("engineering_only", "advisor packet generated; approval still manual")
    if name == "paper_readiness":
        blocked = payload.get("summary", {}).get("blocked", 0)
        return ("blocked" if blocked else "safe", f"blocked_sections={blocked}")
    if name == "report_quality":
        blockers = payload.get("summary", {}).get("blockers", 0)
        warnings = payload.get("summary", {}).get("warnings", 0)
        return ("blocked" if blockers else ("needs_review" if warnings else "safe"), f"blockers={blockers}, warnings={warnings}")
    if name == "leakage_repair_plan":
        summary = payload.get("summary", {})
        must_fix = summary.get("must_fix_before_provider_pilot_count", 0)
        manual = summary.get("manual_review_count", 0)
        return ("blocked" if must_fix else ("needs_review" if manual else "safe"), f"must_fix_provider={must_fix}, manual_review={manual}")
    if name == "leakage_patch_validation":
        valid = payload.get("verdicts", {}).get("manifest_valid", False)
        blockers = payload.get("summary", {}).get("blockers", 0)
        return ("safe" if valid else "blocked", f"manifest_valid={valid}, blockers={blockers}")
    if name == "leakage_suppression_registry":
        summary = payload.get("summary", {})
        verdicts = payload.get("verdicts", {})
        active = summary.get("active_count", 0)
        malformed = summary.get("malformed_count", 0)
        valid = verdicts.get("registry_valid", malformed == 0)
        badge = "safe" if valid else "needs_review"
        return (badge, f"active={active}, malformed={malformed}, valid={valid}")
    if name == "leakage_patch_apply":
        mode = payload.get("mode", "unknown")
        verdicts = payload.get("verdicts", {})
        applied_count = payload.get("summary", {}).get("applied_count", 0)
        manifest_blocked = verdicts.get("manifest_blocked", False)
        if manifest_blocked:
            badge = "blocked"
        elif applied_count > 0:
            badge = "needs_review"
        else:
            badge = "engineering_only"
        return (badge, f"mode={mode}, applied={applied_count}")
    if name == "manual_repair_preview":
        summary = payload.get("summary", {}) or {}
        total = summary.get("operation_count", 0)
        return ("needs_review" if total else "safe", f"manual_ops={total}")
    if name == "reviewed_ops_template":
        count = payload.get("candidate_count", 0)
        return ("engineering_only", f"candidates={count}")
    if name == "pair_link_validation":
        blockers = payload.get("summary", {}).get("blockers", 0)
        clusters = payload.get("summary", {}).get("cluster_count", 0)
        return ("blocked" if blockers else "safe", f"blockers={blockers}, clusters={clusters}")
    if name == "provider_pilot_config_hardening":
        verdicts = payload.get("verdicts", {})
        blocked = verdicts.get("blocked", True)
        safe = verdicts.get("candidate_safe_to_send_to_preflight", False)
        return ("blocked" if blocked else ("safe" if safe else "needs_review"), f"blocked={blocked}, safe={safe}")
    if name == "reproducibility_manifest":
        verdicts = payload.get("verdicts", {})
        ready = verdicts.get("ready_for_public_reproducibility_packet", False)
        return ("safe" if ready else "needs_review", f"ready={ready}")
    if name == "release_blocker_report":
        verdicts = payload.get("verdicts", {})
        ready = verdicts.get("ready_for_public_release", False)
        summary = payload.get("summary", {})
        blocker_count = summary.get("blocker_count", 0)
        return ("safe" if ready else ("blocked" if blocker_count else "needs_review"), f"ready={ready}, blockers={blocker_count}")
    if name == "next_action_plan":
        summary = payload.get("summary", {})
        verdicts = payload.get("verdicts", {})
        return (
            "needs_review" if summary.get("blocker_count", 0) else "engineering_only",
            f"actions={summary.get('action_count', 0)}, next_phase={verdicts.get('next_phase', 'unknown')}",
        )
    if name == "readiness_war_room":
        mission = payload.get("mission_status") if isinstance(payload.get("mission_status"), dict) else {}
        status = str(mission.get("status") or "needs_review")
        return ("blocked" if status.startswith("blocked") else "needs_review", f"mission_status={status}")
    if name == "governance_os":
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        no_go = int(summary.get("no_go_count") or 0)
        review = int(summary.get("review_count") or 0)
        return ("blocked" if no_go else ("needs_review" if review else "safe"), f"no_go={no_go}, review={review}")
    return "engineering_only", "static report present"


def _evidence_state(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    run_payload = entries.get("run_health", {}).get("payload", {})
    asset_payload = entries.get("paper_assets", {}).get("payload", {})
    claim_payload = entries.get("claim_evidence", {}).get("payload", {})
    statuses = {row.get("claim_id"): row.get("status") for row in claim_payload.get("claims", [])}
    c1_c8 = {f"C{i}": statuses.get(f"C{i}", "planned") for i in range(1, 9)}
    return {
        "paper_eligible_runs": run_payload.get("paper_eligible_count", 0),
        "eligible_paper_assets": asset_payload.get("eligible_count", 0),
        "C1_C8_status": c1_c8,
        "C9_status": statuses.get("C9", "engineering_only"),
        "C10_status": statuses.get("C10", "planned"),
        "claims_promoted_by_dashboard": False,
    }


def _blockers(entries: dict[str, dict[str, Any]], state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if state["paper_eligible_runs"] == 0:
        blockers.append("No paper-eligible runs are available.")
    if state["eligible_paper_assets"] == 0:
        blockers.append("No eligible paper assets are available.")
    if state["C10_status"] != "supported":
        blockers.append("C10 remains blocked without real human validation artifacts.")
    for name, entry in entries.items():
        if entry["badge"] in {"blocked", "needs_review"}:
            blockers.append(f"{name}: {entry['summary']}")
    return list(dict.fromkeys(blockers))


def _next_action(state: dict[str, Any], blockers: list[str], provider_gate: dict[str, Any]) -> str:
    leakage_must_fix = int(provider_gate.get("leakage_must_fix_count") or 0)
    if leakage_must_fix > 0:
        return (
            "Review leakage_repair_plan.md and proposed_patch_manifest.md, "
            f"fix {leakage_must_fix} leakage cluster(s) (true answer-leakage first), "
            "rerun all-no-run-reports, then advisor review."
        )
    if provider_gate.get("blocked"):
        return str(provider_gate.get("exact_next_action") or "Resolve provider-pilot gate blockers.")
    if blockers:
        return "Resolve static blockers and complete provider-pilot approval before any live run."
    return (
        "Continue no-run review; rerun all-no-run-reports after dataset edits; "
        "do not promote claims without eligible evidence."
    )


def _small_payload(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if name == "run_health":
        return payload.get("summary", {})
    if name == "paper_assets":
        return {"eligible_count": payload.get("eligible_count"), "flagged_count": payload.get("flagged_count")}
    if name == "claim_evidence":
        return {"claims": [{k: row.get(k) for k in ("claim_id", "status")} for row in payload.get("claims", [])]}
    if name in {"benchmark_quality", "intervention_isolation", "synthetic_fixtures", "release_readiness"}:
        return {"summary": payload.get("summary"), "verdicts": payload.get("verdicts")}
    if name == "repair_plan":
        return {
            "summary": payload.get("summary"),
            "top_actions": [
                {
                    "repair_id": row.get("repair_id") or row.get("root_cause_id"),
                    "recommended_fix": row.get("recommended_fix") or row.get("recommended_root_fix"),
                    "readiness_gate": row.get("readiness_gate"),
                    "rank": row.get("rank"),
                }
                for row in _repair_rows(payload)[:10]
            ],
            "root_causes": _repair_rows(payload)[:25],
            "top_10_provider_pilot_blockers": payload.get("top_10_provider_pilot_blockers", [])[:10],
        }
    if name == "provider_preflight":
        return {
            "summary": payload.get("summary"),
            "verdicts": payload.get("verdicts"),
            "gate_summary": payload.get("gate_summary"),
            "gate_status": payload.get("gate_status"),
            "blockers": payload.get("blockers", [])[:10],
            "warnings": payload.get("warnings", [])[:10],
        }
    if name == "static_leakage":
        return {
            "summary": payload.get("summary"),
            "top_clusters": payload.get("top_clusters", [])[:20],
            "classification_counts": payload.get("classification_counts") or payload.get("summary", {}).get("classification_counts"),
            "top_true_leakage_clusters": payload.get("top_true_leakage_clusters", [])[:20],
            "top_false_positive_candidates": payload.get("top_false_positive_candidates", [])[:20],
            "top_needs_manual_review": payload.get("top_needs_manual_review", [])[:20],
            "top_provider_pilot_blockers": payload.get("top_provider_pilot_blockers", [])[:10],
            "top_main_benchmark_blockers": payload.get("top_main_benchmark_blockers", [])[:10],
        }
    if name == "leakage_repair_plan":
        return {
            "summary": payload.get("summary"),
            "top_10_must_fix_before_provider_pilot": payload.get("top_10_must_fix_before_provider_pilot", [])[:10],
            "manual_review_queue": payload.get("manual_review_queue", [])[:10],
            "patch_manifest_paths": payload.get("patch_manifest_paths"),
        }
    if name == "leakage_patch_validation":
        return {"summary": payload.get("summary"), "verdicts": payload.get("verdicts"), "checks": payload.get("checks", [])[:10]}
    if name == "readiness_war_room":
        return {
            "mission_status": payload.get("mission_status"),
            "risk_radar": payload.get("risk_radar", [])[:10],
            "top_actions": payload.get("top_actions", [])[:10],
        }
    if name == "governance_os":
        return {
            "summary": payload.get("summary"),
            "go_no_go_matrix": payload.get("go_no_go_matrix", [])[:10],
            "critical_path": payload.get("critical_path", [])[:10],
            "generated_files": payload.get("generated_files"),
        }
    return {"summary": payload.get("summary")}


def _next_10_actions(entries: dict[str, dict[str, Any]], provider_gate: dict[str, Any] | None = None) -> list[str]:
    repair_payload = entries.get("repair_plan", {}).get("payload", {})
    actions: list[str] = []
    leakage_plan = _leakage_repair_summary(entries)
    if leakage_plan.get("must_fix_before_provider_pilot_count", 0) > 0:
        actions.insert(0, "Review leakage_repair_plan.md and proposed_patch_manifest.md before provider pilot.")
    for row in _repair_rows(repair_payload):
        fix = row.get("recommended_root_fix") or row.get("recommended_fix")
        if fix:
            actions.append(f"{row.get('rank')}. {fix} (`{row.get('readiness_gate')}`; {row.get('symptom_count', 1)} symptoms)")
    if provider_gate and provider_gate.get("blocked") and not leakage_plan.get("must_fix_before_provider_pilot_count", 0):
        actions.insert(0, f"Provider gate: {provider_gate.get('exact_next_action')}")
    leakage_summary = _static_leakage_summary(entries)
    if leakage_summary.get("blocker_cluster_count", 0) > 0:
        actions.append("Static leakage: fix true leakage blockers before provider-pilot split approval.")
    elif leakage_summary.get("needs_review_count", 0) > 0:
        actions.append("Static leakage: manually review needs-review split/near-duplicate clusters before treating them as false positives.")
    elif leakage_summary.get("false_positive_candidate_count", 0) > 0:
        actions.append("Static leakage: review representative boilerplate false-positive clusters and tune thresholds if needed.")
    classification_counts = leakage_summary.get("classification_counts") or {}
    if classification_counts.get("split_metadata_issue"):
        actions.append("Static leakage: repair split metadata issues before any provider-pilot approval.")
    for row in _top_leakage_root_causes(entries)[:3]:
        fix = row.get("recommended_action") or row.get("suggested_fix") or "Review leakage root cause."
        actions.append(f"Leakage: {fix} (`{row.get('readiness_gate')}`; {row.get('symptom_count', 1)} symptoms)")
    if actions:
        return list(dict.fromkeys(actions))[:10]
    return _fallback_actions(entries)


def _fallback_actions(entries: dict[str, dict[str, Any]]) -> list[str]:
    actions = []
    for name, entry in entries.items():
        if entry["badge"] in {"blocked", "needs_review"}:
            actions.append(f"Review `{name}`: {entry['summary']}")
    return actions[:10]


def _repair_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = (
        payload.get("top_10_provider_pilot_blockers")
        or payload.get("top_50_actionable_repairs")
        or payload.get("root_causes")
        or payload.get("root_cause_summary")
        or payload.get("items")
        or []
    )
    return [row for row in rows if isinstance(row, dict)]


def _root_cause_blockers(entries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    repair_payload = entries.get("repair_plan", {}).get("payload", {})
    rows = (
        repair_payload.get("top_10_provider_pilot_blockers")
        or [
            row for row in _repair_rows(repair_payload)
            if "must_fix_before_provider_pilot" in row.get("affected_readiness_gates", [])
            or row.get("readiness_gate") == "must_fix_before_provider_pilot"
        ]
    )
    return [row for row in rows[:10] if isinstance(row, dict)]


def _provider_pilot_gate(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = entries.get("provider_preflight", {}).get("payload", {})
    gate = payload.get("gate_summary") if isinstance(payload.get("gate_summary"), dict) else {}
    status = gate.get("gate_status") or payload.get("gate_status") or "blocked"
    blocked = status == "blocked" or payload.get("verdicts", {}).get("blocked", True)
    exact_next = gate.get("exact_next_action") or "Complete provider-pilot preflight and approval before any provider run."
    leakage_summary = _leakage_repair_summary(entries)
    leakage_must_fix = leakage_summary.get("must_fix_before_provider_pilot_count", 0)
    blockers = list(gate.get("blockers") or payload.get("blockers", []))
    if leakage_must_fix:
        blocked = True
        status = "blocked"
        exact_next = (
            "Review leakage_repair_plan.md and proposed_patch_manifest.md, "
            f"fix {leakage_must_fix} leakage cluster(s) (true answer-leakage first), "
            "rerun all-no-run-reports, then advisor review."
        )
        blockers.append(
            {
                "id": "leakage_repair_plan_must_fix",
                "severity": "blocker",
                "message": f"{leakage_must_fix} leakage repair clusters must be reviewed before provider pilot.",
            }
        )
    return {
        "gate_status": status,
        "blocked": bool(blocked),
        "leakage_must_fix_count": leakage_must_fix,
        "exact_next_action": exact_next,
        "blockers": blockers,
        "warnings": gate.get("warnings") or payload.get("warnings", []),
    }


def _static_leakage_summary(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = entries.get("static_leakage", {}).get("payload", {})
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "raw_finding_count": int(summary.get("raw_finding_count") or payload.get("raw_finding_count") or 0),
        "cluster_count": int(summary.get("cluster_count") or payload.get("cluster_count") or 0),
        "suppressed_symptom_count": int(summary.get("suppressed_symptom_count") or payload.get("suppressed_symptom_count") or 0),
        "blockers": int(summary.get("blockers") or 0),
        "warnings": int(summary.get("warnings") or 0),
        "classification_counts": summary.get("classification_counts") or payload.get("classification_counts") or {},
        "blocker_cluster_count": int(summary.get("blocker_cluster_count") or payload.get("blocker_cluster_count") or 0),
        "warning_cluster_count": int(summary.get("warning_cluster_count") or payload.get("warning_cluster_count") or 0),
        "false_positive_candidate_count": int(
            summary.get("false_positive_candidate_count") or payload.get("false_positive_candidate_count") or 0
        ),
        "needs_review_count": int(summary.get("needs_review_count") or payload.get("needs_review_count") or 0),
    }


def _leakage_repair_summary(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = entries.get("leakage_repair_plan", {}).get("payload", {})
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    validation = entries.get("leakage_patch_validation", {}).get("payload", {})
    verdicts = validation.get("verdicts") if isinstance(validation.get("verdicts"), dict) else {}
    return {
        "cluster_count": int(summary.get("cluster_count") or 0),
        "must_fix_before_provider_pilot_count": int(summary.get("must_fix_before_provider_pilot_count") or 0),
        "candidate_auto_patch_count": int(summary.get("candidate_auto_patch_count") or 0),
        "manual_review_count": int(summary.get("manual_review_count") or 0),
        "unsafe_operation_count": int(summary.get("unsafe_operation_count") or 0),
        "patch_manifest_valid": bool(verdicts.get("manifest_valid")) if validation else False,
    }


def _top_leakage_root_causes(entries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    payload = entries.get("static_leakage", {}).get("payload", {})
    rows = (
        payload.get("top_true_leakage_clusters")
        or payload.get("top_provider_pilot_blockers")
        or payload.get("top_needs_manual_review")
        or payload.get("top_clusters")
        or payload.get("root_causes")
        or payload.get("root_cause_summary")
        or []
    )
    return [row for row in rows[:10] if isinstance(row, dict)]


def _do_not_run_yet() -> list[str]:
    return [
        "Do not run `python3 -m causal_agent_bench run --config ...`.",
        "Do not call provider APIs or use paid calls.",
        "Do not run local LLM jobs.",
        "Do not promote claims or fill empirical paper results.",
    ]


def _safe_to_do_now() -> list[str]:
    return [
        "Fix top root-cause blockers in configs, dataset metadata, schemas, and documentation.",
        "Rerun the static no-run report bundle after fixes.",
        "Review the advisor packet and provider preflight output before any spend decision.",
        "Use `apply-leakage-patch` in preview mode to validate proposed deterministic ID renames; apply only after reviewer approval.",
        "Document any false-positive clusters via `configs/static_leakage_suppressions.yaml`; never use it to hide answer-leakage or duplicate-ID blockers.",
    ]


def _still_not_evidence() -> list[str]:
    return [
        "Static report generation is not empirical model evidence.",
        "No-run validators do not support C1-C8 or C10.",
        "C9 remains engineering-only unless the claim ledger says otherwise.",
        "Provider-pilot readiness is a gate, not a provider result.",
    ]


def _readiness_state(
    entries: dict[str, dict[str, Any]],
    provider_gate: dict[str, Any],
    evidence_state: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    """Summarize readiness for downstream gates without promoting claims."""

    advisor_entry = entries.get("advisor_review", {})
    release_payload = entries.get("release_readiness", {}).get("payload", {}) or {}
    paper_readiness_payload = entries.get("paper_readiness", {}).get("payload", {}) or {}
    paper_readiness_summary = (
        paper_readiness_payload.get("summary") if isinstance(paper_readiness_payload, dict) else {}
    ) or {}
    leakage_summary = _leakage_repair_summary(entries)
    has_must_fix_leakage = leakage_summary.get("must_fix_before_provider_pilot_count", 0) > 0

    advisor_ready = advisor_entry.get("present", False) and not has_must_fix_leakage
    dry_run_ready = provider_gate.get("gate_status") == "ready_for_dry_run"
    live_ready = provider_gate.get("gate_status") == "ready_for_live_run"
    public_release_ready = bool(
        release_payload.get("verdicts", {}).get("ready_for_public_release")
        or release_payload.get("verdicts", {}).get("ready_for_release")
    )
    empirical_paper_ready = (
        evidence_state.get("paper_eligible_runs", 0) > 0
        and evidence_state.get("eligible_paper_assets", 0) > 0
        and not blockers
    )
    paper_readiness_blocked = int(paper_readiness_summary.get("blocked", 0) or 0)

    return {
        "advisor_review_readiness": "ready" if advisor_ready else "not_ready",
        "advisor_review_blockers": [] if advisor_ready else _short_blockers(blockers, 5),
        "provider_dry_run_readiness": "ready" if dry_run_ready else "blocked",
        "provider_live_run_readiness": "ready" if live_ready else "blocked",
        "public_release_readiness": "ready" if public_release_ready else "blocked",
        "empirical_paper_readiness": "ready" if empirical_paper_ready else "blocked",
        "paper_readiness_map_blocked_sections": paper_readiness_blocked,
        "blocking_summary": _short_blockers(blockers, 10),
    }


def _short_blockers(blockers: list[str], limit: int) -> list[str]:
    return [str(item)[:160] for item in blockers[:limit]]


def _find_report(reports_dir: Path, filename: str) -> Path | None:
    direct = reports_dir / filename
    if direct.exists():
        return direct
    matches = sorted(reports_dir.glob(f"**/{filename}")) if reports_dir.exists() else []
    return matches[0] if matches else None


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None
