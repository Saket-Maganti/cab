from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.evidence_dashboard import build_evidence_dashboard


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_dashboard_generated_from_fixture_reports(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "run_health_report.json", {"summary": {"paper_eligible_count": 0}})
    _write(reports / "paper_asset_eligibility.json", {"eligible_count": 0, "flagged_count": 2})
    _write(
        reports / "claim_evidence_matrix.json",
        {"claims": [{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)] + [{"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "planned"}]},
    )
    report = build_evidence_dashboard(tmp_path, reports_dir=reports, output_dir=tmp_path / "dash")
    state = report["current_evidence_state"]
    assert state["paper_eligible_runs"] == 0
    assert state["eligible_paper_assets"] == 0
    assert state["claims_promoted_by_dashboard"] is False
    assert report["reports"]["paper_todo"]["badge"] == "needs_review"
    assert "repair_plan" in report["reports"]
    assert "benchmark_cards" in report["reports"]
    assert "gold_outputs" in report["reports"]
    assert "tool_schemas" in report["reports"]
    assert "static_leakage" in report["reports"]
    assert "benchmark_manifest" in report["reports"]
    assert "config_profiles" in report["reports"]
    assert "advisor_review" in report["reports"]
    assert "paper_readiness" in report["reports"]
    assert "report_quality" in report["reports"]
    assert report["next_10_actions"]
    assert report["top_10_actions"]
    assert report["provider_pilot_gate"]["blocked"] is True
    assert "Do not run" in "\n".join(report["do_not_run_yet"])
    assert "no-run aids" in Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert Path(report["report_paths"]["json"]).exists()
    assert Path(report["report_paths"]["markdown"]).exists()


def test_dashboard_reads_repair_plan_next_actions_from_subdir(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "run_health_report.json", {"summary": {"paper_eligible_count": 0}})
    _write(reports / "paper_asset_eligibility.json", {"eligible_count": 0, "flagged_count": 0})
    _write(
        reports / "claim_evidence_matrix.json",
        {"claims": [{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)] + [{"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "planned"}]},
    )
    _write(
        reports / "repair_plan/repair_plan.json",
        {
            "summary": {"repair_item_count": 1},
            "items": [
                {
                    "repair_id": "repair_1",
                    "rank": 1,
                    "recommended_fix": "Fix provider preflight blockers.",
                    "readiness_gate": "must_fix_before_provider_pilot",
                }
            ],
        },
    )
    report = build_evidence_dashboard(tmp_path, reports_dir=reports, output_dir=tmp_path / "dash")
    assert any("Fix provider preflight blockers" in action for action in report["next_10_actions"])
    assert report["current_evidence_state"]["claims_promoted_by_dashboard"] is False


def test_dashboard_uses_root_causes_without_listing_thousands(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "run_health_report.json", {"summary": {"paper_eligible_count": 0}})
    _write(reports / "paper_asset_eligibility.json", {"eligible_count": 0})
    _write(
        reports / "claim_evidence_matrix.json",
        {"claims": [{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)] + [{"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "planned"}]},
    )
    _write(
        reports / "provider_pilot_preflight.json",
        {
            "verdicts": {"blocked": True},
            "gate_summary": {"gate_status": "blocked", "exact_next_action": "Fix top dataset blockers.", "blockers": []},
        },
    )
    _write(
        reports / "repair_plan/repair_plan.json",
        {
            "summary": {"raw_repair_item_count": 11285, "root_cause_count": 3},
            "top_10_provider_pilot_blockers": [
                {
                    "root_cause_id": "root_1",
                    "root_cause_title": "missing gold outputs",
                    "rank": 1,
                    "severity": "blocker",
                    "symptom_count": 9000,
                    "recommended_root_fix": "Repair expected-output metadata once.",
                    "readiness_gate": "must_fix_before_provider_pilot",
                    "affected_readiness_gates": ["must_fix_before_provider_pilot"],
                }
            ],
        },
    )
    _write(
        reports / "static_leakage/static_leakage_report.json",
        {
            "summary": {
                "raw_finding_count": 2500,
                "cluster_count": 2,
                "suppressed_symptom_count": 2498,
                "blockers": 1,
                "warnings": 1,
                "classification_counts": {"answer_leakage": 1, "shared_tool_description": 1},
                "blocker_cluster_count": 1,
                "false_positive_candidate_count": 1,
                "needs_review_count": 0,
            },
            "top_true_leakage_clusters": [
                {
                    "root_cause_id": "leak_root_1",
                    "root_cause_title": "answer text leakage in prompt",
                    "severity": "blocker",
                    "leakage_risk": "blocker",
                    "cluster_classification": "answer_leakage",
                    "symptom_count": 2000,
                    "readiness_gate": "must_fix_before_provider_pilot",
                    "recommended_action": "Remove answer leakage.",
                }
            ],
            "top_provider_pilot_blockers": [
                {
                    "root_cause_id": "leak_root_1",
                    "root_cause_title": "answer text leakage in prompt",
                    "severity": "blocker",
                    "symptom_count": 2000,
                    "readiness_gate": "must_fix_before_provider_pilot",
                    "suggested_fix": "Remove answer leakage.",
                }
            ],
            "top_clusters": [],
        },
    )
    report = build_evidence_dashboard(tmp_path, reports_dir=reports, output_dir=tmp_path / "dash")
    assert len(report["top_10_actions"]) <= 10
    assert report["root_cause_blockers"][0]["root_cause_id"] == "root_1"
    assert any("Repair expected-output metadata once" in action for action in report["top_10_actions"])
    assert report["static_leakage_summary"]["raw_finding_count"] == 2500
    assert report["top_leakage_root_causes"][0]["root_cause_id"] == "leak_root_1"
    assert report["static_leakage_summary"]["false_positive_candidate_count"] == 1
    assert report["static_leakage_summary"]["classification_counts"]["answer_leakage"] == 1
    assert "Static Leakage Summary" in Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
