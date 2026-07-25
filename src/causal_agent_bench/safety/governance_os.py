"""No-run governance operating system.

This is a higher-level control plane over Causal Agent Bench's static reports.
It builds a multi-artifact packet for release planning, provider-pilot gating,
paper wording discipline, reviewer red-teaming, and command safety.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

REPORT_FILES = {
    "dashboard": "index.json",
    "readiness_war_room": "readiness_war_room.json",
    "leakage_repair_plan": "leakage_repair_plan.json",
    "leakage_patch_validation": "leakage_patch_validation.json",
    "repair_plan": "repair_plan.json",
    "provider_preflight": "provider_pilot_preflight.json",
    "report_quality": "report_quality_check.json",
    "release_blockers": "release_blocker_report.json",
    "paper_readiness": "paper_readiness_map.json",
    "claim_evidence": "claim_evidence_matrix.json",
    "benchmark_manifest": "benchmark_manifest.json",
    "config_profiles": "config_profiles.json",
    "next_action_plan": "next_action_plan.json",
}

FORBIDDEN_COMMANDS = [
    ("run_benchmark", "python3 -m causal_agent_bench run --config ...", "Runs agents and may call providers."),
    ("make_smoke", "make smoke", "May execute benchmark smoke paths."),
    ("make_test", "make test", "Broad lane may invoke unsafe tests."),
    ("llm_judge", "python3 -m causal_agent_bench run-llm-judge ...", "Can call model/provider APIs."),
    ("claim_promotion", "python3 -m causal_agent_bench update-claim-ledger --promote-to-supported ...", "No eligible evidence exists."),
    ("paper_fill_promotion", "python3 -m causal_agent_bench fill-paper-from-run --promote-to-supported ...", "Would risk empirical overclaiming."),
]

SAFE_COMMANDS = [
    "python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_governance_os_reports",
    "python3 -m causal_agent_bench governance-os --reports-dir /tmp/cab_governance_os_reports --output-dir /tmp/cab_governance_os_reports/governance_os",
    "python3 scripts/check_evidence_safety.py",
]


def build_governance_os(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports",
    output_dir: str | Path = "reports/governance_os",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)

    payloads = {name: _read_report(reports, filename) for name, filename in REPORT_FILES.items()}
    state = _state(payloads)
    gates = _gates(payloads, state)
    critical_path = _critical_path(gates, state)
    go_no_go = _go_no_go_matrix(gates, state)
    sprint_board = _sprint_board(payloads, gates, state)
    burndown = _burndown_plan(gates, sprint_board)
    red_team = _red_team_dossier(state, gates)
    command_firewall = _command_firewall()
    wording_bank = _wording_bank(state)
    decision_template = _decision_log_template(gates, state)
    artifact_router = _artifact_router(out)

    files = _write_sidecars(
        out=out,
        critical_path=critical_path,
        go_no_go=go_no_go,
        sprint_board=sprint_board,
        burndown=burndown,
        red_team=red_team,
        command_firewall=command_firewall,
        wording_bank=wording_bank,
        decision_template=decision_template,
        artifact_router=artifact_router,
    )
    summary = {
        "go_count": sum(1 for row in go_no_go if row["verdict"] == "GO"),
        "no_go_count": sum(1 for row in go_no_go if row["verdict"] == "NO-GO"),
        "review_count": sum(1 for row in go_no_go if row["verdict"] == "REVIEW"),
        "critical_path_blocked_count": sum(1 for row in critical_path if row["status"] == "blocked"),
        "sprint_ticket_count": len(sprint_board),
        "safe_command_count": len(command_firewall["safe_commands"]),
        "forbidden_command_count": len(command_firewall["forbidden_commands"]),
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static no-run Governance OS only; no providers, models, patches, benchmark runs, or claim promotion.",
        "reports_dir": str(reports),
        "summary": summary,
        "current_state": state,
        "gates": gates,
        "go_no_go_matrix": go_no_go,
        "critical_path": critical_path,
        "blocker_burndown_plan": burndown,
        "sprint_board": sprint_board,
        "reviewer_red_team_dossier": red_team,
        "command_firewall": command_firewall,
        "claim_safe_wording_bank": wording_bank,
        "decision_log_template": decision_template,
        "artifact_router": artifact_router,
        "generated_files": files,
        "claims_promoted_by_governance_os": False,
        "patches_applied_by_governance_os": False,
    }
    md = governance_os_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="governance_os",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def governance_os_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    state = payload["current_state"]
    lines = [
        "# Governance OS",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Control Plane Summary",
            [
                f"- GO: {summary['go_count']}",
                f"- NO-GO: {summary['no_go_count']}",
                f"- REVIEW: {summary['review_count']}",
                f"- Blocked critical-path gates: {summary['critical_path_blocked_count']}",
                f"- Sprint tickets: {summary['sprint_ticket_count']}",
                f"- Claims promoted: `{payload['claims_promoted_by_governance_os']}`",
                f"- Patches applied: `{payload['patches_applied_by_governance_os']}`",
            ],
        ),
        section_markdown(
            "Evidence Boundary",
            [
                f"- Paper-eligible runs: {state['paper_eligible_runs']}",
                f"- Eligible paper assets: {state['eligible_paper_assets']}",
                f"- C1-C8: {state['C1_C8_status']}",
                f"- C9: {state['C9_status']}",
                f"- C10: {state['C10_status']}",
            ],
        ),
        "## Go / No-Go Matrix",
        "",
    ]
    for row in payload["go_no_go_matrix"]:
        lines.append(f"- `{row['decision']}`: **{row['verdict']}** -> {row['reason']}")
    lines.extend(["", "## Critical Path", ""])
    for row in payload["critical_path"]:
        lines.append(f"{row['order']}. `{row['gate_id']}` [{row['status']}] {row['objective']} -> {row['next_action']}")
    lines.extend(["", "## First Sprint Tickets", ""])
    for ticket in payload["sprint_board"][:12]:
        lines.append(f"- `{ticket['ticket_id']}` [{ticket['priority']}] {ticket['title']} ({ticket['lane']})")
    lines.extend(["", "## Reviewer Red-Team", ""])
    for row in payload["reviewer_red_team_dossier"][:8]:
        lines.append(f"- **{row['attack']}** -> {row['safe_response']}")
    lines.extend(["", "## Command Firewall", ""])
    for row in payload["command_firewall"]["forbidden_commands"]:
        lines.append(f"- FORBIDDEN `{row['command']}`: {row['reason']}")
    lines.extend(["", "## Generated Files", ""])
    for name, path in payload["generated_files"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.append("")
    return "\n".join(lines)


def _write_sidecars(
    *,
    out: Path,
    critical_path: list[dict[str, Any]],
    go_no_go: list[dict[str, Any]],
    sprint_board: list[dict[str, Any]],
    burndown: dict[str, Any],
    red_team: list[dict[str, Any]],
    command_firewall: dict[str, Any],
    wording_bank: dict[str, Any],
    decision_template: str,
    artifact_router: dict[str, Any],
) -> dict[str, str]:
    files: dict[str, str] = {}
    graph = _critical_path_mermaid(critical_path)
    files["critical_path_graph"] = _write_text(out / "critical_path_graph.mmd", graph)
    files["go_no_go_matrix_json"] = _write_json(out / "go_no_go_matrix.json", {"decisions": go_no_go})
    files["go_no_go_matrix_md"] = _write_text(out / "go_no_go_matrix.md", _go_no_go_markdown(go_no_go))
    csv_path = out / "go_no_go_matrix.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["decision", "verdict", "reason", "next_action"])
        writer.writeheader()
        writer.writerows(go_no_go)
    files["go_no_go_matrix_csv"] = str(csv_path)
    files["blocker_burndown_json"] = _write_json(out / "blocker_burndown_plan.json", burndown)
    files["blocker_burndown_md"] = _write_text(out / "blocker_burndown_plan.md", _burndown_markdown(burndown))
    files["sprint_board_json"] = _write_json(out / "sprint_board.json", {"tickets": sprint_board})
    files["sprint_board_md"] = _write_text(out / "sprint_board.md", _sprint_board_markdown(sprint_board))
    files["reviewer_red_team_dossier"] = _write_text(out / "reviewer_red_team_dossier.md", _red_team_markdown(red_team))
    files["command_firewall_json"] = _write_json(out / "command_firewall.json", command_firewall)
    files["command_firewall_md"] = _write_text(out / "command_firewall.md", _firewall_markdown(command_firewall))
    files["claim_safe_wording_bank_json"] = _write_json(out / "claim_safe_wording_bank.json", wording_bank)
    files["claim_safe_wording_bank_md"] = _write_text(out / "claim_safe_wording_bank.md", _wording_markdown(wording_bank))
    files["decision_log_template"] = _write_text(out / "decision_log_template.md", decision_template)
    files["artifact_router_json"] = _write_json(out / "artifact_router.json", artifact_router)
    files["artifact_router_md"] = _write_text(out / "artifact_router.md", _artifact_router_markdown(artifact_router))
    files["control_plane_manifest"] = _write_json(out / "control_plane_manifest.json", {"files": files})
    return files


def _state(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    dashboard_state = payloads.get("dashboard", {}).get("current_evidence_state")
    if isinstance(dashboard_state, dict):
        statuses = dashboard_state.get("C1_C8_status") or {}
        return {
            "paper_eligible_runs": int(dashboard_state.get("paper_eligible_runs") or 0),
            "eligible_paper_assets": int(dashboard_state.get("eligible_paper_assets") or 0),
            "C1_C8_status": statuses,
            "C9_status": dashboard_state.get("C9_status", "engineering_only"),
            "C10_status": dashboard_state.get("C10_status", "planned"),
        }
    claims = payloads.get("claim_evidence", {}).get("claims") or []
    statuses = {row.get("claim_id"): row.get("status") for row in claims if isinstance(row, dict)}
    return {
        "paper_eligible_runs": 0,
        "eligible_paper_assets": 0,
        "C1_C8_status": {f"C{i}": statuses.get(f"C{i}", "planned") for i in range(1, 9)},
        "C9_status": statuses.get("C9", "engineering_only"),
        "C10_status": statuses.get("C10", "planned"),
    }


def _gates(payloads: dict[str, dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    leakage = payloads.get("leakage_repair_plan", {}).get("summary") or {}
    provider = payloads.get("provider_preflight", {})
    provider_gate = provider.get("gate_summary") if isinstance(provider.get("gate_summary"), dict) else {}
    quality = payloads.get("report_quality", {}).get("summary") or {}
    release = payloads.get("release_blockers", {}).get("summary") or {}
    paper = payloads.get("paper_readiness", {}).get("summary") or {}
    patch_validation = payloads.get("leakage_patch_validation", {}).get("verdicts") or {}
    return {
        "leakage": {
            "blocked": int(leakage.get("must_fix_before_provider_pilot_count") or 0) > 0,
            "must_fix_count": int(leakage.get("must_fix_before_provider_pilot_count") or 0),
            "manual_review_count": int(leakage.get("manual_review_count") or 0),
            "candidate_auto_patch_count": int(leakage.get("candidate_auto_patch_count") or 0),
        },
        "patch_manifest": {
            "valid": bool(patch_validation.get("manifest_valid", False)),
        },
        "provider": {
            "blocked": bool(provider.get("verdicts", {}).get("blocked", True)),
            "gate_status": provider_gate.get("gate_status") or provider.get("gate_status") or "blocked",
            "next_action": provider_gate.get("exact_next_action") or "Complete provider preflight.",
        },
        "report_quality": {
            "blockers": int(quality.get("blockers") or 0),
            "warnings": int(quality.get("warnings") or 0),
        },
        "release": {
            "blocker_count": int(release.get("blocker_count") or 0),
        },
        "paper": {
            "blocked_sections": int(paper.get("blocked") or 0),
            "needs_evidence_sections": int(paper.get("needs_evidence") or 0),
            "empirical_evidence_missing": state["paper_eligible_runs"] == 0 or state["eligible_paper_assets"] == 0,
        },
    }


def _critical_path(gates: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    steps = [
        ("leakage", "Clear leakage repair blockers", not gates["leakage"]["blocked"], "Review and repair leakage repair plan items."),
        ("patch_manifest", "Validate proposed patch manifest", gates["patch_manifest"]["valid"], "Fix manifest validation blockers."),
        ("provider_preflight", "Clear provider-pilot preflight", not gates["provider"]["blocked"], gates["provider"]["next_action"]),
        ("report_quality", "Clear report-quality blockers", gates["report_quality"]["blockers"] == 0, "Resolve noisy or missing report surfaces."),
        ("public_release", "Clear release blocker report", gates["release"]["blocker_count"] == 0, "Resolve public release blockers."),
        ("empirical_paper", "Obtain eligible evidence before empirical claims", not gates["paper"]["empirical_evidence_missing"], "Keep C1-C8/C10 blocked until eligible evidence exists."),
    ]
    rows = []
    for idx, (gate_id, objective, clear, next_action) in enumerate(steps, start=1):
        rows.append(
            {
                "order": idx,
                "gate_id": gate_id,
                "objective": objective,
                "status": "clear" if clear else "blocked",
                "next_action": next_action,
                "evidence_boundary": "static_no_run_only" if gate_id != "empirical_paper" else "requires_future_provider_evidence",
            }
        )
    return rows


def _go_no_go_matrix(gates: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    leakage_clear = not gates["leakage"]["blocked"]
    provider_clear = not gates["provider"]["blocked"]
    quality_clear = gates["report_quality"]["blockers"] == 0
    release_clear = gates["release"]["blocker_count"] == 0 and quality_clear
    evidence_exists = state["paper_eligible_runs"] > 0 and state["eligible_paper_assets"] > 0
    return [
        _decision("advisor_static_review", "REVIEW", "Static packet can be reviewed, but approval is still manual.", "Review advisor, leakage, war-room, and preflight packets."),
        _decision("provider_dry_run", "GO" if leakage_clear and provider_clear else "NO-GO", "Requires leakage and provider preflight clearance.", "Clear leakage repair and provider preflight gates."),
        _decision("live_provider_pilot", "NO-GO", "Live provider run requires explicit approval and paid-call intent outside this no-run phase.", "Do not run providers from this packet."),
        _decision("public_release", "GO" if release_clear else "NO-GO", "Public release requires release/report-quality blockers to be clear.", "Resolve release/report-quality blockers."),
        _decision("empirical_paper_submission", "GO" if evidence_exists else "NO-GO", "Empirical submission requires eligible provider evidence and paper assets.", "Keep empirical claims blocked."),
    ]


def _decision(decision: str, verdict: str, reason: str, next_action: str) -> dict[str, str]:
    return {"decision": decision, "verdict": verdict, "reason": reason, "next_action": next_action}


def _sprint_board(payloads: dict[str, dict[str, Any]], gates: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    tickets = []
    if gates["leakage"]["must_fix_count"]:
        tickets.append(_ticket("GOV-LEAK-001", "critical", "dataset", "Review leakage repair plan top blockers", "leakage", "Leakage plan must-fix count decreases or is advisor-deferred."))
    if gates["leakage"]["candidate_auto_patch_count"]:
        tickets.append(_ticket("GOV-LEAK-002", "high", "dataset", "Review deterministic duplicate-ID rename candidates", "leakage", "Reviewed ops template completed without touching results/claims."))
    if gates["provider"]["blocked"]:
        tickets.append(_ticket("GOV-PROV-001", "critical", "config", "Resolve provider preflight next action", "provider_preflight", gates["provider"]["next_action"]))
    if gates["report_quality"]["blockers"]:
        tickets.append(_ticket("GOV-QUAL-001", "high", "validation", "Resolve report-quality blockers", "report_quality", "Report quality blockers reach zero."))
    if gates["release"]["blocker_count"]:
        tickets.append(_ticket("GOV-REL-001", "high", "release", "Resolve release blockers", "release", "Release blocker report reaches zero blockers."))
    if state["paper_eligible_runs"] == 0:
        tickets.append(_ticket("GOV-PAPER-001", "critical", "paper", "Keep empirical wording blocked", "claim_evidence", "Paper sections use method-only wording until eligible evidence exists."))
    tickets.append(_ticket("GOV-REV-001", "medium", "review", "Run reviewer gauntlet before advisor meeting", "advisor_review", "Every red-team attack has a safe answer and evidence boundary."))
    return tickets


def _ticket(ticket_id: str, priority: str, lane: str, title: str, blocked_by: str, acceptance: str) -> dict[str, str]:
    return {
        "ticket_id": ticket_id,
        "priority": priority,
        "lane": lane,
        "title": title,
        "blocked_by": blocked_by,
        "acceptance_check": acceptance,
    }


def _burndown_plan(gates: dict[str, Any], tickets: list[dict[str, Any]]) -> dict[str, Any]:
    waves = [
        {
            "wave": 1,
            "name": "Leakage repair review",
            "objective": "Reduce provider-pilot leakage blockers before config approval.",
            "ticket_ids": [ticket["ticket_id"] for ticket in tickets if ticket["blocked_by"] == "leakage"],
        },
        {
            "wave": 2,
            "name": "Provider gate hardening",
            "objective": "Clear template/approval/preflight issues without enabling paid calls.",
            "ticket_ids": [ticket["ticket_id"] for ticket in tickets if ticket["blocked_by"] == "provider_preflight"],
        },
        {
            "wave": 3,
            "name": "Report and release polish",
            "objective": "Make static report surfaces clean enough for reviewers.",
            "ticket_ids": [ticket["ticket_id"] for ticket in tickets if ticket["blocked_by"] in {"report_quality", "release"}],
        },
        {
            "wave": 4,
            "name": "Paper language lockdown",
            "objective": "Preserve method-only wording until eligible evidence exists.",
            "ticket_ids": [ticket["ticket_id"] for ticket in tickets if ticket["lane"] == "paper"],
        },
    ]
    return {
        "starting_blockers": {
            "leakage": gates["leakage"]["must_fix_count"],
            "report_quality": gates["report_quality"]["blockers"],
            "release": gates["release"]["blocker_count"],
        },
        "waves": waves,
    }


def _red_team_dossier(state: dict[str, Any], gates: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "attack": "Your benchmark split is contaminated.",
            "safe_response": f"Static leakage repair is not cleared yet; must-fix count is {gates['leakage']['must_fix_count']}.",
            "evidence_needed": "Leakage repair plan rerun with zero must-fix provider-pilot clusters or advisor acceptance.",
            "forbidden_response": "The dataset is leakage-free.",
        },
        {
            "attack": "You are already making empirical claims.",
            "safe_response": f"No; paper-eligible runs are {state['paper_eligible_runs']} and eligible assets are {state['eligible_paper_assets']}.",
            "evidence_needed": "Verified provider-backed run plus eligible paper assets and claim-ledger promotion.",
            "forbidden_response": "The results demonstrate robustness.",
        },
        {
            "attack": "The provider pilot is ready to run.",
            "safe_response": f"No; provider gate is {gates['provider']['gate_status']} and this packet cannot approve paid calls.",
            "evidence_needed": "Advisor-approved copied config, budget cap, stop cap, and preflight clearance.",
            "forbidden_response": "We can run the provider now.",
        },
        {
            "attack": "Static reports are too noisy to review.",
            "safe_response": f"Report-quality blockers are {gates['report_quality']['blockers']}; those must be fixed before release claims.",
            "evidence_needed": "Report-quality check with zero blockers and clustered high-volume reports.",
            "forbidden_response": "All reports are clean.",
        },
    ]


def _command_firewall() -> dict[str, Any]:
    return {
        "safe_commands": [{"command": command, "reason": "Static no-run governance command."} for command in SAFE_COMMANDS],
        "forbidden_commands": [
            {"command_id": command_id, "command": command, "reason": reason}
            for command_id, command, reason in FORBIDDEN_COMMANDS
        ],
        "policy": "This packet is advisory. It never authorizes provider calls, paid calls, claim promotion, or benchmark execution.",
    }


def _wording_bank(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed": [
            "The current repository contains static no-run readiness checks.",
            "The benchmark design and governance machinery are under review.",
            "Current empirical claims remain blocked pending eligible provider evidence.",
            "C9 is engineering-only.",
        ],
        "forbidden": [
            "The benchmark demonstrates robustness.",
            "The provider pilot is approved.",
            "C1-C8 are supported.",
            "Human validation confirms the benchmark.",
        ],
        "evidence_state": state,
    }


def _decision_log_template(gates: dict[str, Any], state: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Decision Log Template",
            "",
            "- Date:",
            "- Reviewer/advisor:",
            "- Decision:",
            "- Scope: static/no-run, provider dry-run, live provider pilot, public release, empirical paper",
            f"- Current leakage must-fix count: {gates['leakage']['must_fix_count']}",
            f"- Provider gate: {gates['provider']['gate_status']}",
            f"- Paper-eligible runs: {state['paper_eligible_runs']}",
            "- Evidence boundary acknowledged: yes/no",
            "- Forbidden commands acknowledged: yes/no",
            "- Follow-up ticket IDs:",
            "",
        ]
    )


def _artifact_router(out: Path) -> dict[str, Any]:
    return {
        "advisor": ["go_no_go_matrix.md", "decision_log_template.md", "reviewer_red_team_dossier.md"],
        "dataset_owner": ["sprint_board.md", "blocker_burndown_plan.md"],
        "release_owner": ["go_no_go_matrix.md", "command_firewall.md"],
        "paper_owner": ["claim_safe_wording_bank.md", "reviewer_red_team_dossier.md"],
        "output_dir": str(out),
    }


def _critical_path_mermaid(rows: list[dict[str, Any]]) -> str:
    lines = ["flowchart TD"]
    for row in rows:
        status = row["status"]
        label = f"{row['order']}. {row['gate_id']} ({status})"
        lines.append(f'  N{row["order"]}["{label}"]')
        if row["order"] > 1:
            lines.append(f'  N{row["order"] - 1} --> N{row["order"]}')
    lines.append("")
    return "\n".join(lines)


def _go_no_go_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# Go / No-Go Matrix", "", "| Decision | Verdict | Reason | Next Action |", "|---|---|---|---|"]
    for row in rows:
        lines.append(f"| `{row['decision']}` | **{row['verdict']}** | {row['reason']} | {row['next_action']} |")
    lines.append("")
    return "\n".join(lines)


def _burndown_markdown(plan: dict[str, Any]) -> str:
    lines = ["# Blocker Burn-Down Plan", "", f"Starting blockers: `{plan['starting_blockers']}`", ""]
    for wave in plan["waves"]:
        lines.append(f"## Wave {wave['wave']}: {wave['name']}")
        lines.append("")
        lines.append(f"- Objective: {wave['objective']}")
        lines.append(f"- Tickets: {', '.join(wave['ticket_ids']) or '(none)'}")
        lines.append("")
    return "\n".join(lines)


def _sprint_board_markdown(tickets: list[dict[str, Any]]) -> str:
    lines = ["# Sprint Board", "", "| Ticket | Priority | Lane | Title | Acceptance |", "|---|---|---|---|---|"]
    for ticket in tickets:
        lines.append(f"| `{ticket['ticket_id']}` | {ticket['priority']} | {ticket['lane']} | {ticket['title']} | {ticket['acceptance_check']} |")
    lines.append("")
    return "\n".join(lines)


def _red_team_markdown(rows: list[dict[str, str]]) -> str:
    lines = ["# Reviewer Red-Team Dossier", ""]
    for row in rows:
        lines.append(f"## {row['attack']}")
        lines.append("")
        lines.append(f"- Safe response: {row['safe_response']}")
        lines.append(f"- Evidence needed: {row['evidence_needed']}")
        lines.append(f"- Forbidden response: {row['forbidden_response']}")
        lines.append("")
    return "\n".join(lines)


def _firewall_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Command Firewall", "", payload["policy"], "", "## Safe Commands", ""]
    for row in payload["safe_commands"]:
        lines.append(f"- `{row['command']}`: {row['reason']}")
    lines.extend(["", "## Forbidden Commands", ""])
    for row in payload["forbidden_commands"]:
        lines.append(f"- `{row['command']}`: {row['reason']}")
    lines.append("")
    return "\n".join(lines)


def _wording_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Claim-Safe Wording Bank", "", "## Allowed", ""]
    lines.extend(f"- {row}" for row in payload["allowed"])
    lines.extend(["", "## Forbidden", ""])
    lines.extend(f"- {row}" for row in payload["forbidden"])
    lines.append("")
    return "\n".join(lines)


def _artifact_router_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Artifact Router", ""]
    for owner, files in payload.items():
        if owner == "output_dir":
            continue
        lines.append(f"- `{owner}`: {', '.join(files)}")
    lines.append("")
    return "\n".join(lines)


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _write_text(path: Path, text: str) -> str:
    path.write_text(text, encoding="utf-8")
    return str(path)


def _read_report(reports: Path, filename: str) -> dict[str, Any]:
    path = _find_report(reports, filename)
    if not path:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _find_report(reports: Path, filename: str) -> Path | None:
    direct = reports / filename
    if direct.exists():
        return direct
    matches = sorted(reports.glob(f"**/{filename}")) if reports.exists() else []
    return matches[0] if matches else None
