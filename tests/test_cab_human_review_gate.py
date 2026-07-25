from __future__ import annotations

import csv
import json
from pathlib import Path

from causal_agent_bench.safety.human_review_gate import (
    HumanReviewPolicy,
    validate_compact20_human_reviews,
)


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _fixture(tmp_path: Path, *, disagree: bool = False) -> tuple[Path, Path]:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"candidates": [{"candidate_id": "c1"}]}),
        encoding="utf-8",
    )
    review = tmp_path / "reviews"
    common = [
        ["c1", "yes", "clear evidence", "human-a", "2026-01-01T00:00:00Z"],
        [
            "c1",
            "no" if disagree else "yes",
            "independent evidence",
            "human-b",
            "2026-01-01T00:01:00Z",
        ],
    ]
    _write_csv(
        review / "task_clarity_review.csv",
        ["candidate_id", "clear_task", "notes", "reviewer_id", "timestamp"],
        common,
    )
    _write_csv(
        review / "gold_policy_review.csv",
        ["candidate_id", "gold_policy_valid", "notes", "reviewer_id", "timestamp"],
        common,
    )
    isolation = [
        ["c1", row[1], row[1], row[2], row[3], row[4]]
        for row in common
    ]
    _write_csv(
        review / "intervention_isolation_review.csv",
        [
            "candidate_id",
            "isolation_valid",
            "goal_preserved",
            "notes",
            "reviewer_id",
            "timestamp",
        ],
        isolation,
    )
    _write_csv(
        review / "adjudication_template.csv",
        ["candidate_id", "final_decision", "adjudicator_id", "notes", "timestamp"],
        [],
    )
    return review, manifest


def test_header_only_repository_packet_fails_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = validate_compact20_human_reviews(root)
    assert payload["genuine_human_row_count"] == 0
    assert payload["human_review_state"] == "HUMAN_REVIEW_INCOMPLETE"
    assert payload["c10_state"] == "C10_PENDING"
    assert payload["slice_lock_allowed"] is False
    assert payload["paper_eligibility_allowed"] is False


def test_two_independent_agreeing_reviewers_can_pass_fixture(tmp_path: Path) -> None:
    review, manifest = _fixture(tmp_path)
    payload = validate_compact20_human_reviews(
        tmp_path,
        review_dir=review,
        candidate_manifest=manifest,
        policy=HumanReviewPolicy(min_independent_reviewers=2, min_raw_agreement=0.8),
    )
    assert payload["genuine_human_row_count"] == 6
    assert payload["raw_agreement"] == 1.0
    assert payload["human_review_state"] == "HUMAN_REVIEW_COMPLETE"
    assert payload["c10_state"] == "PASS"


def test_disagreement_requires_real_adjudication(tmp_path: Path) -> None:
    review, manifest = _fixture(tmp_path, disagree=True)
    payload = validate_compact20_human_reviews(
        tmp_path,
        review_dir=review,
        candidate_manifest=manifest,
    )
    assert payload["human_review_state"] == "ADJUDICATION_PENDING"
    assert payload["c10_state"] == "C10_PENDING"
    assert payload["unresolved_disagreements"]


def test_proxy_identity_never_counts_as_human(tmp_path: Path) -> None:
    review, manifest = _fixture(tmp_path)
    path = review / "task_clarity_review.csv"
    text = path.read_text(encoding="utf-8").replace("human-a", "ai_proxy")
    path.write_text(text, encoding="utf-8")
    payload = validate_compact20_human_reviews(
        tmp_path,
        review_dir=review,
        candidate_manifest=manifest,
    )
    assert payload["c10_state"] == "C10_PENDING"
    assert payload["proxy_rows_counted"] == 0

