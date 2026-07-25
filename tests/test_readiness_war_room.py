from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.evidence_dashboard import build_evidence_dashboard
from causal_agent_bench.safety.readiness_war_room import build_readiness_war_room


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _fixture_reports(root: Path) -> Path:
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
        {
            "summary": {
                "cluster_count": 12,
                "must_fix_before_provider_pilot_count": 3,
                "manual_review_count": 11,
                "candidate_auto_patch_count": 1,
            },
            "top_10_must_fix_before_provider_pilot": [{"cluster_id": "leak_root_1"}],
        },
    )
    _write(
        reports / "static_leakage/static_leakage_report.json",
        {
            "summary": {
                "raw_finding_count": 2000,
                "classification_counts": {"true_split_leakage": 2, "duplicate_id_leakage": 1},
            }
        },
    )
    _write(
        reports / "provider_pilot_preflight.json",
        {
            "gate_status": "template_safe_but_not_runnable",
            "gate_summary": {
                "gate_status": "template_safe_but_not_runnable",
                "exact_next_action": "Create an approved copy after advisor approval.",
                "blockers": [],
            },
            "verdicts": {"blocked": True},
        },
    )
    _write(
        reports / "report_quality/report_quality_check.json",
        {"summary": {"blockers": 2, "warnings": 4, "noisy_raw_reports": 2}},
    )
    _write(
        reports / "paper_readiness/paper_readiness_map.json",
        {"summary": {"blocked": 3, "needs_evidence": 4, "ready_method_only": 5}},
    )
    return reports


def test_readiness_war_room_generates_packet_and_sidecars(tmp_path: Path) -> None:
    reports = _fixture_reports(tmp_path)
    packet = build_readiness_war_room(tmp_path, reports_dir=reports, output_dir=tmp_path / "war")
    assert packet["mission_status"]["status"] == "blocked_by_leakage_repair"
    assert packet["current_evidence_state"]["paper_eligible_runs"] == 0
    assert packet["current_evidence_state"]["claims_promoted_by_war_room"] is False
    assert any(row["risk_id"] == "dataset_leakage" for row in packet["risk_radar"])
    assert Path(packet["generated_files"]["readiness_graph"]).exists()
    assert Path(packet["generated_files"]["reviewer_gauntlet"]).exists()
    assert Path(packet["generated_files"]["what_if_unlock_plan"]).exists()
    assert Path(packet["report_paths"]["json"]).exists()
    assert Path(packet["report_paths"]["markdown"]).exists()


def test_war_room_missing_reports_does_not_crash(tmp_path: Path) -> None:
    packet = build_readiness_war_room(tmp_path, reports_dir=tmp_path / "missing", output_dir=tmp_path / "war")
    assert packet["mission_status"]["status"] in {"blocked_by_provider_gate", "method_only_ready", "blocked_by_report_quality"}
    assert packet["top_actions"]
    assert "python3 -m causal_agent_bench run --config ..." in packet["kill_switches"]


def test_war_room_what_if_keeps_claim_boundary(tmp_path: Path) -> None:
    reports = _fixture_reports(tmp_path)
    packet = build_readiness_war_room(tmp_path, reports_dir=reports, output_dir=tmp_path / "war")
    boundaries = " ".join(row["claim_boundary"] for row in packet["what_if_scenarios"])
    assert "no empirical claims" in boundaries.lower() or "not provider evidence" in boundaries.lower()
    assert any("Are any empirical claims supported?" in row["attack"] for row in packet["reviewer_gauntlet"])


def test_dashboard_indexes_readiness_war_room(tmp_path: Path) -> None:
    reports = _fixture_reports(tmp_path)
    packet = build_readiness_war_room(tmp_path, reports_dir=reports, output_dir=reports / "readiness_war_room")
    _write(reports / "run_health_report.json", {"summary": {"paper_eligible_count": 0}})
    _write(reports / "paper_asset_eligibility.json", {"eligible_count": 0})
    dashboard = build_evidence_dashboard(tmp_path, reports_dir=reports, output_dir=tmp_path / "dash")
    assert "readiness_war_room" in dashboard["reports"]
    assert dashboard["reports"]["readiness_war_room"]["present"] is True
    assert dashboard["reports"]["readiness_war_room"]["payload"]["mission_status"] == packet["mission_status"]
