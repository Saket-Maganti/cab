from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.release_blocker_analyzer import build_release_blocker_report


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_missing_license_is_release_blocker(tmp_path: Path) -> None:
    report = build_release_blocker_report(tmp_path, reports_dir=tmp_path / "reports", output_dir=tmp_path / "out")
    assert any(b["id"].endswith("license_missing") and b["severity"] == "blocker" for b in report["blockers"])
    assert report["verdicts"]["ready_for_public_release"] is False
    assert report["verdicts"]["any_license_blockers"] is True


def test_supported_claim_is_evidence_blocker(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("MIT", encoding="utf-8")
    reports = tmp_path / "reports"
    _write(reports / "claim_evidence_matrix.json", {"claims": [{"claim_id": "C1", "status": "supported"}]})
    report = build_release_blocker_report(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    assert report["verdicts"]["any_evidence_blockers"] is True


def test_leakage_blockers_propagated(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("MIT", encoding="utf-8")
    reports = tmp_path / "reports"
    _write(
        reports / "leakage_repair_plan/leakage_repair_plan.json",
        {"summary": {"must_fix_before_provider_pilot_count": 5}},
    )
    report = build_release_blocker_report(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    assert report["verdicts"]["any_leakage_blockers"] is True
    leakage = [b for b in report["blockers"] if b["category"] == "leakage"]
    assert leakage[0]["impact_count"] == 5


def test_pair_link_blockers_propagated(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("MIT", encoding="utf-8")
    reports = tmp_path / "reports"
    _write(reports / "pair_link_validator/pair_link_validation.json", {"summary": {"blockers": 2}})
    report = build_release_blocker_report(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    pair = [b for b in report["blockers"] if b["category"] == "pair_link"]
    assert pair and pair[0]["severity"] == "blocker"


def test_clean_state_is_ready_for_release(tmp_path: Path) -> None:
    # Set up a clean state with LICENSE, DATA_LICENSE, CITATION, and a no-claim matrix.
    (tmp_path / "LICENSE").write_text("MIT", encoding="utf-8")
    (tmp_path / "DATA_LICENSE.md").write_text("data license", encoding="utf-8")
    (tmp_path / "CITATION.cff").write_text("cff", encoding="utf-8")
    reports = tmp_path / "reports"
    _write(reports / "claim_evidence_matrix.json", {"claims": [{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)]})
    _write(reports / "leakage_repair_plan/leakage_repair_plan.json", {"summary": {"must_fix_before_provider_pilot_count": 0}})
    _write(reports / "pair_link_validator/pair_link_validation.json", {"summary": {"blockers": 0}})
    _write(reports / "benchmark_quality_report.json", {"verdicts": {"benchmark_quality_ready_for_release": True}})
    _write(
        reports / "reproducibility_manifest/reproducibility_manifest.json",
        {"verdicts": {"dependency_locked": True, "all_datasets_frozen": True, "license_complete": True}},
    )
    report = build_release_blocker_report(tmp_path, reports_dir=reports, output_dir=tmp_path / "out")
    assert report["verdicts"]["ready_for_public_release"] is True
