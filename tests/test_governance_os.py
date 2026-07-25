from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.evidence_dashboard import build_evidence_dashboard
from causal_agent_bench.safety.governance_os import build_governance_os


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _reports(root: Path) -> Path:
    reports = root / "reports"
    _write(
        reports / "claim_evidence_matrix.json",
        {
            "claims": [
                *[{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)],
                {"claim_id": "C9", "status": "engineering_only"},
                {"claim_id": "C10", "status": "planned"},
            ]
        },
    )
    _write(
        reports / "leakage_repair_plan/leakage_repair_plan.json",
        {"summary": {"must_fix_before_provider_pilot_count": 4, "manual_review_count": 9, "candidate_auto_patch_count": 2}},
    )
    _write(
        reports / "leakage_repair_plan/leakage_patch_validation.json",
        {"verdicts": {"manifest_valid": True}, "summary": {"blockers": 0}},
    )
    _write(
        reports / "provider_pilot_preflight.json",
        {
            "verdicts": {"blocked": True},
            "gate_summary": {"gate_status": "template_safe_but_not_runnable", "exact_next_action": "Create approved copy later."},
        },
    )
    _write(reports / "report_quality/report_quality_check.json", {"summary": {"blockers": 2, "warnings": 3}})
    _write(reports / "release_blockers/release_blocker_report.json", {"summary": {"blocker_count": 1}})
    _write(reports / "paper_readiness/paper_readiness_map.json", {"summary": {"blocked": 3, "needs_evidence": 4}})
    return reports


def test_governance_os_generates_major_packet(tmp_path: Path) -> None:
    report = build_governance_os(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "gov")
    assert report["summary"]["no_go_count"] >= 3
    assert report["summary"]["sprint_ticket_count"] >= 5
    assert report["claims_promoted_by_governance_os"] is False
    assert report["patches_applied_by_governance_os"] is False
    for key in (
        "critical_path_graph",
        "go_no_go_matrix_json",
        "go_no_go_matrix_csv",
        "blocker_burndown_md",
        "sprint_board_md",
        "reviewer_red_team_dossier",
        "command_firewall_md",
        "claim_safe_wording_bank_md",
        "decision_log_template",
        "artifact_router_md",
    ):
        assert key in report["generated_files"]
        assert Path(report["generated_files"][key]).exists()


def test_governance_os_keeps_provider_and_paper_no_go(tmp_path: Path) -> None:
    report = build_governance_os(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "gov")
    verdicts = {row["decision"]: row["verdict"] for row in report["go_no_go_matrix"]}
    assert verdicts["provider_dry_run"] == "NO-GO"
    assert verdicts["live_provider_pilot"] == "NO-GO"
    assert verdicts["empirical_paper_submission"] == "NO-GO"
    assert "C9 is engineering-only." in report["claim_safe_wording_bank"]["allowed"]


def test_governance_os_command_firewall_contains_forbidden_run(tmp_path: Path) -> None:
    report = build_governance_os(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "gov")
    commands = [row["command"] for row in report["command_firewall"]["forbidden_commands"]]
    assert "python3 -m causal_agent_bench run --config ..." in commands


def test_governance_os_missing_reports_does_not_crash(tmp_path: Path) -> None:
    report = build_governance_os(tmp_path, reports_dir=tmp_path / "missing", output_dir=tmp_path / "gov")
    assert report["go_no_go_matrix"]
    assert report["critical_path"]
    assert report["current_state"]["paper_eligible_runs"] == 0


def test_dashboard_indexes_governance_os(tmp_path: Path) -> None:
    reports = _reports(tmp_path)
    gov = build_governance_os(tmp_path, reports_dir=reports, output_dir=reports / "governance_os")
    _write(reports / "run_health_report.json", {"summary": {"paper_eligible_count": 0}})
    _write(reports / "paper_asset_eligibility.json", {"eligible_count": 0})
    dash = build_evidence_dashboard(tmp_path, reports_dir=reports, output_dir=tmp_path / "dash")
    assert dash["reports"]["governance_os"]["present"] is True
    assert dash["reports"]["governance_os"]["payload"]["summary"] == gov["summary"]
