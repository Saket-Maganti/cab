"""Fixture-only tests for NeurIPS empirical plan + paper skeleton."""

from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.neurips_submission_gate import build_neurips_submission_gate

REPO = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_paper_blueprint_marks_results_blocked() -> None:
    text = _read("paper/NEURIPS_PAPER_BLUEPRINT.md")
    assert "BLOCKED" in text or "blocked" in text.lower()
    assert "Results" in text or "results" in text
    assert "not yet reported" in text.lower() or "placeholder" in text.lower()
    assert "NeurIPS-ready" not in text or "not" in text.lower()


def test_experiment_matrix_tiny_pilot_cannot_support_final_claims() -> None:
    text = _read("experiments/NEURIPS_EXPERIMENT_MATRIX.md")
    assert "Stage B" in text or "tiny" in text.lower()
    assert "cannot" in text.lower() or "not sufficient" in text.lower()
    assert "5" in text


def test_claim_evidence_map_keeps_c1_c10_unsupported() -> None:
    text = _read("docs/NEURIPS_CLAIM_EVIDENCE_UPGRADE_MAP.md")
    for claim in ("C1", "C8", "C10"):
        assert claim in text
    assert "planned" in text.lower() or "unsupported" in text.lower()
    assert "engineering_only" in text or "C9" in text
    assert "forbidden" in text.lower()


def test_result_skeletons_mark_empirical_tables_blocked() -> None:
    text = _read("paper/RESULT_TABLES_AND_FIGURES_PLAN.md")
    assert "BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST" in text
    assert "table2" in text.lower() or "main model" in text.lower()


def test_statistical_plan_warns_tiny_pilot_limits() -> None:
    text = _read("docs/STATISTICAL_ANALYSIS_PLAN.md")
    assert "tiny pilot" in text.lower() or "≤5" in text or "5 trajectory" in text.lower()
    assert "cannot" in text.lower() or "not sufficient" in text.lower()


def test_submission_gate_not_ready(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "run_health_report.json").write_text(
        json.dumps({"summary": {"paper_eligible_count": 0}}), encoding="utf-8"
    )
    (reports / "paper_asset_eligibility.json").write_text(
        json.dumps({"eligible_count": 0}), encoding="utf-8"
    )
    report = build_neurips_submission_gate(REPO, reports_dir=reports, output_dir=tmp_path / "gate")
    assert report["verdict"] == "NOT_READY"
    assert report["submission_ready"] is False
    assert report["neurips_ready"] is False
    assert report["gates_passed"] < report["gates_total"]


def test_submission_gate_blocks_assets_without_provider_runs(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "run_health_report.json").write_text(
        json.dumps({"summary": {"paper_eligible_count": 0}}), encoding="utf-8"
    )
    (reports / "paper_asset_eligibility.json").write_text(
        json.dumps({"eligible_count": 2}), encoding="utf-8"
    )
    report = build_neurips_submission_gate(REPO, reports_dir=reports, output_dir=tmp_path / "gate")
    asset_gate = next(gate for gate in report["gates"] if gate["gate_id"] == "paper_assets_eligible")
    assert asset_gate["status"] == "fail"
    assert "paper_eligible_runs=0" in asset_gate["detail"]


def test_submission_gate_doc_not_ready() -> None:
    text = _read("docs/NEURIPS_SUBMISSION_GATE.md")
    assert "NOT READY" in text or "NOT_READY" in text
    assert "not ready" in text.lower() or "NOT READY" in text
