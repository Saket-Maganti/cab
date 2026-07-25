from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts import analyze_compact20_ai_proxy_review as proxy_review

REPO = Path(__file__).resolve().parents[1]
INPUT_DIR = REPO / "data" / "human_validation" / "no_api_task_review"
TASK_ORIGINAL = INPUT_DIR / "compact20_task_review.csv"
GOLD_ORIGINAL = INPUT_DIR / "compact20_gold_policy_review.csv"
TASK_PROXY = INPUT_DIR / "compact20_task_review_AI_PROXY_TEST_ONLY.csv"
GOLD_PROXY = INPUT_DIR / "compact20_gold_policy_review_AI_PROXY_TEST_ONLY.csv"


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _text(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def _is_blank(value: str | None) -> bool:
    return value in {"", None}


def test_original_review_csvs_are_not_modified() -> None:
    task_rows = _csv_rows(TASK_ORIGINAL)
    gold_rows = _csv_rows(GOLD_ORIGINAL)

    assert len(task_rows) == 20
    assert len(gold_rows) == 20
    assert "status" not in task_rows[0]
    assert "reviewer_notes" not in task_rows[0]
    assert "reviewer_confidence_1_to_5" not in task_rows[0]
    assert "status" not in gold_rows[0]
    assert "reviewer_notes" not in gold_rows[0]
    assert "reviewer_confidence_1_to_5" not in gold_rows[0]

    for row in task_rows:
        assert _is_blank(row["task_clear"])
        assert _is_blank(row["intervention_isolated"])
        assert _is_blank(row["gold_policy_clear"])
        assert _is_blank(row["include_in_compact20"])
        assert _is_blank(row["reviewer_id"])
        assert _is_blank(row["review_date"])
        assert _is_blank(row["notes"])

    for row in gold_rows:
        assert _is_blank(row["should_answer_change"])
        assert _is_blank(row["abstention_acceptable"])
        assert _is_blank(row["cannot_determine_acceptable"])
        assert _is_blank(row["review_decision"])
        assert _is_blank(row["reviewer_id"])
        assert _is_blank(row["review_date"])
        assert _is_blank(row["notes"])


@pytest.mark.parametrize("path", [TASK_PROXY, GOLD_PROXY])
def test_ai_proxy_files_are_clearly_labeled(path: Path) -> None:
    rows = _csv_rows(path)
    assert len(rows) == 20
    for row in rows:
        assert row["status"] == "ai_proxy_test_only"
        assert row["review_type"] == "ai_proxy_review"
        assert "synthetic_review_for_pipeline_testing" in row["review_labels"]
        assert "not_human_annotation" in row["review_labels"]
        assert row["reviewer_id"] == "AI_PROXY_TEST_ONLY"
        assert row["reviewer_confidence_1_to_5"] == "3"
        assert row["reviewer_notes"].startswith("AI_PROXY_TEST_ONLY: not human validation.")


def test_ai_proxy_files_cannot_promote_c10() -> None:
    c10_status = _text("reports/C10_STATUS_AFTER_AI_PROXY_REVIEW_TEST.md")
    assert "C10_UNSUPPORTED_AFTER_AI_PROXY_REVIEW_TEST" in c10_status
    assert "does not create C10 evidence" in c10_status
    assert "Real human annotations: `0`" in c10_status
    assert "Inter-annotator agreement computations: `0`" in c10_status
    assert "not human validation" in c10_status


def test_ai_proxy_files_cannot_count_as_human_annotations() -> None:
    status = _text("reports/COMPACT20_AI_PROXY_REVIEW_TEST_STATUS.md")
    boundary = _text("reports/AI_PROXY_REVIEW_EVIDENCE_BOUNDARY.md")
    assert "not_human_annotation" in status
    assert "Real human annotations remain `0`" in status
    assert "Real human annotations remain `0`" in boundary
    assert "must not be counted as annotations" in boundary


def test_ai_proxy_outputs_cannot_mark_paper_assets_eligible() -> None:
    subset = json.loads((INPUT_DIR / "compact20_ai_proxy_clean_candidate_subset.json").read_text(encoding="utf-8"))
    completion = _text("reports/COMPACT20_AI_PROXY_REVIEW_COMPLETION_STATUS.md")
    boundary = _text("reports/AI_PROXY_REVIEW_EVIDENCE_BOUNDARY.md")

    assert subset["paper_asset_eligibility"] is False
    assert subset["c10_support"] is False
    assert subset["human_annotation_count"] == 0
    assert all(candidate["paper_eligible"] is False for candidate in subset["candidates"])
    assert "Eligible paper assets produced: `0`" in completion
    assert "Eligible paper assets remain `0`" in boundary


def test_downstream_analysis_requires_proxy_test_mode() -> None:
    with pytest.raises(SystemExit) as exc_info:
        proxy_review.main([])
    assert exc_info.value.code == 2


def test_downstream_proxy_outputs_are_pipeline_only() -> None:
    subset = json.loads((INPUT_DIR / "compact20_ai_proxy_clean_candidate_subset.json").read_text(encoding="utf-8"))
    action_log = _text("reports/COMPACT20_AI_PROXY_REVIEW_ACTION_LOG.md")
    assert subset["status"] == "ai_proxy_test_only"
    assert subset["candidate_count"] == 5
    assert {candidate["family"] for candidate in subset["candidates"]} == {"memory_corruption"}
    assert all(candidate["use_limit"] == "pipeline_testing_only_not_human_validation" for candidate in subset["candidates"])
    assert "pipeline-testing metadata" in action_log
    assert "not human validation" in action_log


def test_provider_evidence_and_claim_support_remain_zero() -> None:
    boundary = _text("reports/AI_PROXY_REVIEW_EVIDENCE_BOUNDARY.md")
    status = _text("reports/COMPACT20_AI_PROXY_REVIEW_TEST_STATUS.md")
    assert "Provider-backed evidence remains `0`" in boundary
    assert "Eligible paper assets remain `0`" in boundary
    assert "C1-C8/C10 remain unsupported" in boundary
    assert "Provider-backed evidence remains `0`" in status
    assert "C1-C8/C10 remain unsupported" in status
