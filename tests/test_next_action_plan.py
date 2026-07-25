from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.next_action_plan import build_next_action_plan


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_empty_reports_yield_re_run_warning(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    plan = build_next_action_plan(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    # With no reports, the plan should surface a warning to run all-no-run-reports first.
    assert plan["summary"]["action_count"] >= 1
    assert plan["verdicts"]["next_phase"] == "none_blocking"
    assert Path(plan["report_paths"]["json"]).exists()
    assert Path(plan["report_paths"]["markdown"]).exists()
    ids = [a["id"] for a in plan["actions"]]
    assert any("claim_evidence_matrix_missing" in i for i in ids)


def test_answer_leakage_drives_blocker(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(
        reports / "leakage_repair_plan/leakage_repair_plan.json",
        {
            "summary": {"must_fix_before_provider_pilot_count": 6},
            "top_answer_leakage_repairs": [{"cluster_id": f"leak_root_{i}"} for i in range(6)],
            "top_duplicate_id_repairs": [],
            "top_split_metadata_repairs": [],
            "manual_review_queue": [],
        },
    )
    plan = build_next_action_plan(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    answer_actions = [a for a in plan["actions"] if a["id"].endswith("answer_leakage_manual_rewrite")]
    assert answer_actions
    assert answer_actions[0]["severity"] == "blocker"
    assert plan["verdicts"]["next_phase"] == "leakage_repair"


def test_pair_link_blockers_added(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(
        reports / "pair_link_validator/pair_link_validation.json",
        {"summary": {"blockers": 3, "warnings": 2}},
    )
    plan = build_next_action_plan(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    pair_blocker = [a for a in plan["actions"] if a["id"].endswith("pair_link_blockers")]
    assert pair_blocker
    assert pair_blocker[0]["severity"] == "blocker"
    assert pair_blocker[0]["impact_count"] == 3


def test_promoted_claim_creates_evidence_blocker(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(
        reports / "claim_evidence_matrix.json",
        {"claims": [{"claim_id": "C1", "status": "supported"}, {"claim_id": "C9", "status": "engineering_only"}]},
    )
    plan = build_next_action_plan(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    promoted = [a for a in plan["actions"] if "claims_marked_supported" in a["id"]]
    assert promoted
    assert promoted[0]["severity"] == "blocker"
    assert plan["verdicts"]["next_phase"] == "evidence_safety"


def test_ranking_orders_by_phase_then_severity(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(
        reports / "leakage_repair_plan/leakage_repair_plan.json",
        {
            "summary": {"must_fix_before_provider_pilot_count": 1},
            "top_duplicate_id_repairs": [{"cluster_id": "a"}],
            "top_answer_leakage_repairs": [],
            "top_split_metadata_repairs": [],
            "manual_review_queue": [],
        },
    )
    _write(
        reports / "release_readiness_report.json",
        {"verdicts": {"ready_for_public_release": False}},
    )
    plan = build_next_action_plan(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    phases = [a["phase"] for a in plan["actions"]]
    # leakage_repair must come before release
    assert phases.index("leakage_repair") < phases.index("release")
