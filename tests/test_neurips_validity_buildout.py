"""Fixture-only tests for NeurIPS dataset validity + human validation buildout."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from causal_agent_bench.safety.gold_output_validation import build_gold_output_validation
from causal_agent_bench.safety.high_risk_intervention_queue import (
    build_high_risk_intervention_queue,
)
from causal_agent_bench.safety.human_validation_packet import (
    ANNOTATION_COLUMNS,
    build_human_validation_packet,
)
from causal_agent_bench.safety.validity_scorecard import build_validity_scorecard

REPO = Path(__file__).resolve().parents[1]

REQUIRED_DOSSIER_FIELDS = (
    "Intended causal factor",
    "Expected invariant",
    "Answer policy",
    "Human validation required",
    "Claim dependency",
    "Current readiness",
)


def _read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_intervention_validity_dossier_required_fields() -> None:
    text = _read("docs/INTERVENTION_VALIDITY_DOSSIER.md")
    assert "tool_removal" in text
    assert "long_horizon_dependency" in text
    assert "memory_corruption" in text
    for field in REQUIRED_DOSSIER_FIELDS:
        assert field in text
    assert "empirical_blocked" in text.lower() or "human_review_pending" in text


def test_human_master_protocol_blocks_c3_c10_without_annotations() -> None:
    text = _read("docs/HUMAN_VALIDATION_MASTER_PROTOCOL.md")
    assert "C3" in text and "blocked" in text.lower()
    assert "C10" in text and "blocked" in text.lower()
    assert "0" in text or "no completed annotations" in text.lower()
    assert "do not fabricate" in text.lower() or "not fabricate" in text.lower()


def test_annotation_schema_required_columns(tmp_path: Path) -> None:
    report = build_human_validation_packet(tmp_path, output_dir=tmp_path / "out")
    schema = json.loads(Path(report["templates"]["schema"]).read_text(encoding="utf-8"))
    for col in (
        "task_understandable_yes_no",
        "intervention_isolation_valid_yes_no",
        "gold_answer_correct_yes_no",
        "trajectory_label_valid_yes_no",
        "invalid_sample_flag",
    ):
        assert col in schema["properties"]
        assert col in schema["required"]
    with Path(report["templates"]["csv"]).open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    assert "task_understandable_yes_no" in header
    assert set(ANNOTATION_COLUMNS).issubset(set(header))


def test_validity_scorecard_conservative(tmp_path: Path) -> None:
    report = build_validity_scorecard(REPO, output_dir=tmp_path / "scorecard")
    assert report["verdicts"]["empirical_claims_allowed"] is False
    assert report["verdicts"]["valid_for_main_benchmark"] is False
    assert report["verdicts"]["valid_for_public_release"] is False
    assert report["evidence_state"]["paper_eligible_runs"] == 0
    assert report["evidence_state"]["claims_supported"] is False
    for dim in report["dimensions"]:
        assert dim["supports_empirical_claims"] is False
        assert 0 <= dim["score"] <= 100


def test_high_risk_queue_separates_pilot_vs_main_blockers(tmp_path: Path) -> None:
    report = build_high_risk_intervention_queue(REPO, output_dir=tmp_path / "hr")
    assert "pilot_blocker" in report["manual_review_queue"][0]
    assert "main_benchmark_blocker" in report["manual_review_queue"][0]
    assert report["verdicts"]["auto_approval_forbidden"] is True
    families = {row["canonical_family"] for row in report["manual_review_queue"]}
    assert "long_horizon_dependency" in families or any(
        row["intervention_type"] == "long_horizon_dependency" for row in report["manual_review_queue"]
    )


def test_gold_output_triage_manual_review_queue(tmp_path: Path) -> None:
    report = build_gold_output_validation(REPO, output_dir=tmp_path / "gold")
    assert report["verdicts"]["auto_fix_forbidden"] is True
    assert "manual_review_queue" in report
    assert "warnings_by_intervention_type" in report
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "Do not auto-fix" in md
    csv_path = Path(report["report_paths"]["manual_review_csv"])
    assert csv_path.exists()


def test_main_benchmark_readiness_not_marked_ready() -> None:
    text = _read("docs/MAIN_BENCHMARK_READINESS_PLAN.md")
    assert "not ready" in text.lower() or "main_candidate_not_ready" in text
    assert "main_200" in text
    assert "main_v0_1_500" in text or "main_500" in text
    assert "not ready" in text.lower()
    assert "not now" in text.lower() or "not ready" in text.lower()


def test_human_validation_templates_include_readmes(tmp_path: Path) -> None:
    report = build_human_validation_packet(tmp_path, output_dir=tmp_path / "out")
    assert Path(report["templates"]["annotator_readme"]).exists()
    assert Path(report["templates"]["adjudicator_readme"]).exists()
    assert Path(report["templates"]["codebook"]).exists()
    assert Path(report["templates"]["adjudication_csv"]).exists()
