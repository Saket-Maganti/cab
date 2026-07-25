from __future__ import annotations

from pathlib import Path

from causal_agent_bench.safety.max_ceiling_gate import REQUIRED_FINAL_ARTIFACTS

ROOT = Path(__file__).resolve().parents[1]


def test_exact_required_max_ceiling_artifacts_exist_and_are_nonempty() -> None:
    assert len(REQUIRED_FINAL_ARTIFACTS) == 15
    for relative in REQUIRED_FINAL_ARTIFACTS:
        path = ROOT / relative
        assert path.is_file(), relative
        assert path.stat().st_size > 200, relative


def test_handbook_has_all_categories_fields_and_estimate_labels() -> None:
    text = (ROOT / "CAB_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md").read_text(
        encoding="utf-8"
    )
    for category in "ABCDEFGHI":
        assert f"## Category {category} " in text
    for field in (
        "Run ID",
        "Study stage",
        "Evidence role",
        "Prerequisite gates",
        "Clean/intervention counts",
        "Expected trajectories",
        "Compute class",
        "T4×2 compatibility",
        "Expected runtime range",
        "Expected monetary cost",
        "Completion validator",
        "Failure recovery",
        "Paper eligibility",
    ):
        assert field in text
    assert "ESTIMATE_NOT_MEASURED" in text


def test_handoff_keeps_empirical_evidence_at_zero() -> None:
    text = (ROOT / "cabv2.md").read_text(encoding="utf-8")
    assert "Genuine human rows: 0" in text
    assert "Real provider trajectories: 0" in text
    assert "Real open-model trajectories: 0" in text
    assert "Paper-eligible assets: 0" in text
    assert "do not run models" in text.lower()
