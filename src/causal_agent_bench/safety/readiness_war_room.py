"""No-run readiness war-room report.

This module turns the existing static reports into a compact strategic cockpit:
what is blocking provider spend, what would unlock next, which reviewer attacks
are predictable, and which commands remain forbidden. It never runs benchmarks
or mutates dataset/result artifacts.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

REPORT_NAMES = {
    "dashboard": "index.json",
    "repair_plan": "repair_plan.json",
    "leakage_repair_plan": "leakage_repair_plan.json",
    "provider_preflight": "provider_pilot_preflight.json",
    "static_leakage": "static_leakage_report.json",
    "report_quality": "report_quality_check.json",
    "claim_evidence": "claim_evidence_matrix.json",
    "paper_readiness": "paper_readiness_map.json",
    "benchmark_manifest": "benchmark_manifest.json",
}

FORBIDDEN_COMMANDS = [
    "python3 -m causal_agent_bench run --config ...",
    "make smoke",
    "make test",
    "python3 -m causal_agent_bench run-llm-judge ...",
    "python3 -m causal_agent_bench fill-paper-from-run --promote-to-supported ...",
    "python3 -m causal_agent_bench update-claim-ledger --promote-to-supported ...",
]


def build_readiness_war_room(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports",
    output_dir: str | Path = "reports/readiness_war_room",
) -> dict[str, Any]:
    """Build a static readiness war-room packet from existing no-run reports."""

    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)

    payloads = {name: _read_named_report(reports, filename) for name, filename in REPORT_NAMES.items()}
    evidence = _evidence_state(payloads)
    provider_gate = _provider_gate(payloads)
    leakage = _leakage_state(payloads)
    quality = _report_quality_state(payloads)
    paper = _paper_state(payloads)
    top_actions = _top_actions(payloads, leakage, provider_gate, quality)
    unlock_ladder = _unlock_ladder(leakage, provider_gate, quality, paper)
    risk_radar = _risk_radar(evidence, leakage, provider_gate, quality, paper)
    gauntlet = _reviewer_gauntlet(evidence, leakage, provider_gate, quality, paper)
    what_if = _what_if_scenarios(evidence, leakage, provider_gate, quality, paper)
    graph = _graph_mermaid(leakage, provider_gate, quality, paper)

    graph_path = out / "readiness_graph.mmd"
    gauntlet_path = out / "reviewer_gauntlet.md"
    what_if_path = out / "what_if_unlock_plan.json"
    manifest_path = out / "war_room_manifest.json"
    graph_path.write_text(graph, encoding="utf-8")
    gauntlet_path.write_text(_reviewer_gauntlet_markdown(gauntlet), encoding="utf-8")
    what_if_path.write_text(json.dumps(what_if, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    packet = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static no-run war-room report only; no benchmarks, providers, model calls, patches, or claim promotion.",
        "reports_dir": str(reports),
        "mission_status": _mission_status(evidence, leakage, provider_gate, quality, paper),
        "current_evidence_state": evidence,
        "provider_gate": provider_gate,
        "leakage_state": leakage,
        "report_quality_state": quality,
        "paper_state": paper,
        "risk_radar": risk_radar,
        "unlock_ladder": unlock_ladder,
        "what_if_scenarios": what_if,
        "reviewer_gauntlet": gauntlet,
        "top_actions": top_actions,
        "kill_switches": FORBIDDEN_COMMANDS,
        "generated_files": {
            "readiness_graph": str(graph_path),
            "reviewer_gauntlet": str(gauntlet_path),
            "what_if_unlock_plan": str(what_if_path),
            "war_room_manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(
        json.dumps(
            {
                "generated_at": packet["generated_at"],
                "scope": packet["scope"],
                "files": packet["generated_files"],
                "mission_status": packet["mission_status"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    md = readiness_war_room_markdown(packet)
    md_path, json_path = write_dual_report(
        stem="readiness_war_room",
        payload=packet,
        markdown=md,
        output_dir=out,
    )
    packet["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def readiness_war_room_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Readiness War Room",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Mission Status",
            [
                f"- Status: `{payload['mission_status']['status']}`",
                f"- Exact next move: {payload['mission_status']['exact_next_move']}",
                f"- Provider pilot blocked: `{payload['provider_gate']['blocked']}`",
                "- Claims promoted by this report: `False`",
            ],
        ),
        section_markdown(
            "Evidence State",
            [
                f"- Paper-eligible runs: {payload['current_evidence_state']['paper_eligible_runs']}",
                f"- Eligible paper assets: {payload['current_evidence_state']['eligible_paper_assets']}",
                f"- C1-C8: {payload['current_evidence_state']['C1_C8_status']}",
                f"- C9: {payload['current_evidence_state']['C9_status']}",
                f"- C10: {payload['current_evidence_state']['C10_status']}",
            ],
        ),
        "## Risk Radar",
        "",
    ]
    for item in payload["risk_radar"]:
        lines.append(f"- `{item['risk_id']}` [{item['level']}] {item['title']} -> {item['next_action']}")
    lines.extend(["", "## Unlock Ladder", ""])
    for step in payload["unlock_ladder"]:
        lines.append(
            f"{step['step']}. `{step['gate']}` [{step['status']}] {step['objective']} -> {step['next_action']}"
        )
    lines.extend(["", "## Top Actions", ""])
    for action in payload["top_actions"]:
        lines.append(f"- {action}")
    lines.extend(["", "## Reviewer Gauntlet", ""])
    for row in payload["reviewer_gauntlet"][:8]:
        lines.append(f"- **{row['attack']}**")
        lines.append(f"  - Safe answer: {row['safe_answer']}")
        lines.append(f"  - Evidence needed: {row['evidence_needed']}")
    lines.extend(["", "## What-If Unlock Scenarios", ""])
    for scenario in payload["what_if_scenarios"]:
        lines.append(
            f"- `{scenario['scenario_id']}`: {scenario['description']} -> "
            f"{scenario['predicted_status']} ({scenario['claim_boundary']})"
        )
    lines.extend(["", "## Kill Switches", ""])
    for command in payload["kill_switches"]:
        lines.append(f"- `{command}`")
    lines.extend(
        [
            "",
            "## Generated Files",
            "",
        ]
    )
    for name, path in payload["generated_files"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.append("")
    return "\n".join(lines)


def _reviewer_gauntlet_markdown(rows: list[dict[str, str]]) -> str:
    lines = ["# Reviewer Gauntlet", "", "Static reviewer-pressure questions generated from current no-run blockers.", ""]
    for row in rows:
        lines.append(f"## {row['attack']}")
        lines.append("")
        lines.append(f"- Safe answer: {row['safe_answer']}")
        lines.append(f"- Evidence needed: {row['evidence_needed']}")
        lines.append(f"- Do not say: {row['forbidden_wording']}")
        lines.append("")
    return "\n".join(lines)


def _read_named_report(reports_dir: Path, filename: str) -> dict[str, Any]:
    path = _find_report(reports_dir, filename)
    if not path:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _find_report(reports_dir: Path, filename: str) -> Path | None:
    direct = reports_dir / filename
    if direct.exists():
        return direct
    matches = sorted(reports_dir.glob(f"**/{filename}")) if reports_dir.exists() else []
    return matches[0] if matches else None


def _evidence_state(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    dashboard = payloads.get("dashboard", {})
    state = dashboard.get("current_evidence_state") if isinstance(dashboard.get("current_evidence_state"), dict) else {}
    claim_payload = payloads.get("claim_evidence", {})
    statuses = {row.get("claim_id"): row.get("status") for row in claim_payload.get("claims", []) if isinstance(row, dict)}
    if not statuses:
        statuses = {f"C{i}": "planned" for i in range(1, 9)}
        statuses["C9"] = "engineering_only"
        statuses["C10"] = "planned"
    return {
        "paper_eligible_runs": int(state.get("paper_eligible_runs") or 0),
        "eligible_paper_assets": int(state.get("eligible_paper_assets") or 0),
        "C1_C8_status": {f"C{i}": statuses.get(f"C{i}", "planned") for i in range(1, 9)},
        "C9_status": statuses.get("C9", "engineering_only"),
        "C10_status": statuses.get("C10", "planned"),
        "claims_promoted_by_war_room": False,
    }


def _provider_gate(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    dashboard_gate = payloads.get("dashboard", {}).get("provider_pilot_gate")
    if isinstance(dashboard_gate, dict) and dashboard_gate:
        return {
            "gate_status": str(dashboard_gate.get("gate_status") or "blocked"),
            "blocked": bool(dashboard_gate.get("blocked", True)),
            "exact_next_action": str(dashboard_gate.get("exact_next_action") or "Resolve provider-pilot gate blockers."),
            "blocker_count": len(dashboard_gate.get("blockers") or []),
        }
    preflight = payloads.get("provider_preflight", {})
    gate = preflight.get("gate_summary") if isinstance(preflight.get("gate_summary"), dict) else {}
    status = gate.get("gate_status") or preflight.get("gate_status") or "blocked"
    return {
        "gate_status": str(status),
        "blocked": status == "blocked" or bool(preflight.get("verdicts", {}).get("blocked", True)),
        "exact_next_action": str(gate.get("exact_next_action") or "Complete provider-pilot preflight and approval."),
        "blocker_count": len(gate.get("blockers") or preflight.get("blockers") or []),
    }


def _leakage_state(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    repair = payloads.get("leakage_repair_plan", {})
    static = payloads.get("static_leakage", {})
    repair_summary = repair.get("summary") if isinstance(repair.get("summary"), dict) else {}
    static_summary = static.get("summary") if isinstance(static.get("summary"), dict) else {}
    return {
        "repair_clusters": int(repair_summary.get("cluster_count") or 0),
        "must_fix_before_provider_pilot": int(repair_summary.get("must_fix_before_provider_pilot_count") or 0),
        "manual_review_count": int(repair_summary.get("manual_review_count") or 0),
        "candidate_auto_patch_count": int(repair_summary.get("candidate_auto_patch_count") or 0),
        "raw_finding_count": int(static_summary.get("raw_finding_count") or static.get("raw_finding_count") or 0),
        "classification_counts": static_summary.get("classification_counts") or static.get("classification_counts") or {},
    }


def _report_quality_state(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    quality = payloads.get("report_quality", {})
    summary = quality.get("summary") if isinstance(quality.get("summary"), dict) else {}
    return {
        "blockers": int(summary.get("blockers") or 0),
        "warnings": int(summary.get("warnings") or 0),
        "noisy_raw_reports": int(summary.get("noisy_raw_reports") or 0),
    }


def _paper_state(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    paper = payloads.get("paper_readiness", {})
    summary = paper.get("summary") if isinstance(paper.get("summary"), dict) else {}
    return {
        "blocked_sections": int(summary.get("blocked") or 0),
        "needs_evidence_sections": int(summary.get("needs_evidence") or 0),
        "ready_method_only_sections": int(summary.get("ready_method_only") or 0),
    }


def _risk_radar(
    evidence: dict[str, Any],
    leakage: dict[str, Any],
    provider_gate: dict[str, Any],
    quality: dict[str, Any],
    paper: dict[str, Any],
) -> list[dict[str, str]]:
    risks = []
    if leakage["must_fix_before_provider_pilot"]:
        risks.append(_risk("dataset_leakage", "critical", "Leakage blockers remain", "Review leakage repair plan before provider pilot."))
    if provider_gate["blocked"]:
        risks.append(_risk("provider_gate", "critical", "Provider gate is blocked", provider_gate["exact_next_action"]))
    if quality["blockers"]:
        risks.append(_risk("report_quality", "high", "Report quality has blockers", "Fix noisy or missing static report surfaces."))
    if evidence["paper_eligible_runs"] == 0:
        risks.append(_risk("evidence", "critical", "No paper-eligible runs", "Keep empirical claims blocked."))
    if paper["blocked_sections"]:
        risks.append(_risk("paper", "high", "Paper sections are blocked", "Keep results/human validation/ablations as placeholders."))
    return risks or [_risk("static_review", "low", "No high-risk static blockers detected", "Continue no-run review.")]


def _risk(risk_id: str, level: str, title: str, next_action: str) -> dict[str, str]:
    return {"risk_id": risk_id, "level": level, "title": title, "next_action": next_action}


def _unlock_ladder(
    leakage: dict[str, Any],
    provider_gate: dict[str, Any],
    quality: dict[str, Any],
    paper: dict[str, Any],
) -> list[dict[str, Any]]:
    steps = [
        (
            "leakage_repair",
            "Review and repair leakage blockers",
            leakage["must_fix_before_provider_pilot"] == 0,
            "Review leakage_repair_plan.md and proposed_patch_manifest.md.",
        ),
        (
            "provider_preflight",
            "Clear provider-pilot config and approval gate",
            not provider_gate["blocked"],
            provider_gate["exact_next_action"],
        ),
        (
            "report_quality",
            "Remove report-quality blockers",
            quality["blockers"] == 0,
            "Resolve report-quality blockers before public release.",
        ),
        (
            "paper_readiness",
            "Keep paper sections honest",
            paper["blocked_sections"] == 0,
            "Do not fill empirical sections until eligible evidence exists.",
        ),
    ]
    return [
        {
            "step": index,
            "gate": gate,
            "objective": objective,
            "status": "clear" if clear else "blocked",
            "next_action": next_action,
        }
        for index, (gate, objective, clear, next_action) in enumerate(steps, start=1)
    ]


def _reviewer_gauntlet(
    evidence: dict[str, Any],
    leakage: dict[str, Any],
    provider_gate: dict[str, Any],
    quality: dict[str, Any],
    paper: dict[str, Any],
) -> list[dict[str, str]]:
    rows = [
        {
            "attack": "Are your provider-pilot splits contaminated?",
            "safe_answer": f"Not cleared yet: {leakage['must_fix_before_provider_pilot']} leakage repair clusters remain before provider pilot.",
            "evidence_needed": "Clean static leakage report plus reviewed patch manifest after dataset fixes.",
            "forbidden_wording": "The benchmark is leakage-free.",
        },
        {
            "attack": "Are any empirical claims supported?",
            "safe_answer": f"No. Paper-eligible runs remain {evidence['paper_eligible_runs']} and eligible assets remain {evidence['eligible_paper_assets']}.",
            "evidence_needed": "Verified provider-backed runs, eligible paper assets, and claim-ledger review.",
            "forbidden_wording": "The benchmark demonstrates model robustness.",
        },
        {
            "attack": "Can you run the provider pilot now?",
            "safe_answer": f"No. Provider gate is `{provider_gate['gate_status']}`.",
            "evidence_needed": "Advisor-approved config, leakage repairs reviewed, budget caps, and preflight clearance.",
            "forbidden_wording": "The provider pilot is approved.",
        },
    ]
    if quality["blockers"]:
        rows.append(
            {
                "attack": "Are the no-run reports themselves reviewable?",
                "safe_answer": f"Not fully. Report-quality blockers: {quality['blockers']}.",
                "evidence_needed": "Report-quality pass with clustering and verdict surfaces.",
                "forbidden_wording": "All static reports are clean.",
            }
        )
    if paper["blocked_sections"]:
        rows.append(
            {
                "attack": "Can the paper results section be written?",
                "safe_answer": f"No. Paper readiness has {paper['blocked_sections']} blocked sections.",
                "evidence_needed": "Eligible provider evidence and human-validation artifacts.",
                "forbidden_wording": "Results are ready for submission.",
            }
        )
    return rows


def _what_if_scenarios(
    evidence: dict[str, Any],
    leakage: dict[str, Any],
    provider_gate: dict[str, Any],
    quality: dict[str, Any],
    paper: dict[str, Any],
) -> list[dict[str, str]]:
    scenarios = [
        {
            "scenario_id": "fix_leakage_blockers",
            "description": "All leakage repair plan must-fix clusters are resolved and static leakage is rerun.",
            "predicted_status": "Provider gate still requires advisor approval/config clearance." if provider_gate["blocked"] else "Provider dry-run gate may become reviewable.",
            "claim_boundary": "Still no empirical claims; this is static readiness only.",
        },
        {
            "scenario_id": "approve_provider_config",
            "description": "Advisor approves a copied provider-pilot config with budget and stop caps.",
            "predicted_status": "Still blocked if leakage or report-quality blockers remain." if leakage["must_fix_before_provider_pilot"] or quality["blockers"] else "Ready for dry-run review, not live empirical claims.",
            "claim_boundary": "Config approval is not provider evidence.",
        },
        {
            "scenario_id": "fix_report_quality",
            "description": "Report-quality blockers are resolved.",
            "predicted_status": "Release review improves; provider pilot remains gated by leakage/preflight." if leakage["must_fix_before_provider_pilot"] or provider_gate["blocked"] else "Static review surface becomes cleaner.",
            "claim_boundary": "Cleaner reports do not support C1-C8/C10.",
        },
    ]
    if evidence["paper_eligible_runs"] == 0:
        scenarios.append(
            {
                "scenario_id": "write_method_only_paper",
                "description": "Draft method/design sections using no-run evidence boundaries.",
                "predicted_status": "Method-only text can be prepared; results/human validation remain blocked.",
                "claim_boundary": "No performance, robustness, or human-validation claims.",
            }
        )
    return scenarios


def _graph_mermaid(
    leakage: dict[str, Any],
    provider_gate: dict[str, Any],
    quality: dict[str, Any],
    paper: dict[str, Any],
) -> str:
    leakage_label = f"Leakage repairs ({leakage['must_fix_before_provider_pilot']} provider blockers)"
    provider_label = f"Provider gate ({provider_gate['gate_status']})"
    quality_label = f"Report quality ({quality['blockers']} blockers)"
    paper_label = f"Paper readiness ({paper['blocked_sections']} blocked)"
    return "\n".join(
        [
            "flowchart TD",
            f'  A["{leakage_label}"] --> B["{provider_label}"]',
            '  B --> C["Advisor approval"]',
            '  C --> D["Dry-run review"]',
            '  D --> E["Future provider pilot"]',
            f'  F["{quality_label}"] --> B',
            f'  G["{paper_label}"] --> H["Method-only wording"]',
            '  E -. future evidence only .-> I["Claim ledger review"]',
            '  I -. no auto-promotion .-> J["Paper assets eligibility"]',
            "",
        ]
    )


def _mission_status(
    evidence: dict[str, Any],
    leakage: dict[str, Any],
    provider_gate: dict[str, Any],
    quality: dict[str, Any],
    paper: dict[str, Any],
) -> dict[str, str]:
    if leakage["must_fix_before_provider_pilot"]:
        return {
            "status": "blocked_by_leakage_repair",
            "exact_next_move": "Review leakage_repair_plan.md and proposed_patch_manifest.md.",
        }
    if provider_gate["blocked"]:
        return {"status": "blocked_by_provider_gate", "exact_next_move": provider_gate["exact_next_action"]}
    if quality["blockers"]:
        return {"status": "blocked_by_report_quality", "exact_next_move": "Resolve report-quality blockers."}
    if evidence["paper_eligible_runs"] == 0 or paper["blocked_sections"]:
        return {"status": "method_only_ready", "exact_next_move": "Prepare method-only materials; keep empirical claims blocked."}
    return {"status": "static_review_clear", "exact_next_move": "Proceed only with explicitly approved next validation step."}


def _top_actions(
    payloads: dict[str, dict[str, Any]],
    leakage: dict[str, Any],
    provider_gate: dict[str, Any],
    quality: dict[str, Any],
) -> list[str]:
    actions = []
    if leakage["must_fix_before_provider_pilot"]:
        actions.append("Review leakage repair plan and proposed patch manifest before provider pilot.")
    if provider_gate["blocked"]:
        actions.append(provider_gate["exact_next_action"])
    dashboard_actions = payloads.get("dashboard", {}).get("top_10_actions") or []
    for action in dashboard_actions:
        if isinstance(action, str):
            actions.append(action)
    if quality["blockers"]:
        actions.append("Resolve report-quality blockers so reviewers see clustered, parseable reports.")
    actions.append("Keep C1-C8/C10 blocked until eligible evidence exists.")
    return list(dict.fromkeys(actions))[:10]
