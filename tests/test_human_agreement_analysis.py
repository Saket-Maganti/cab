from __future__ import annotations

from causal_agent_bench.analysis.human_validation import compute_agreement


def test_agreement_reports_raw_kappa_alpha_prevalence_and_intervals() -> None:
    rows = []
    labels = [
        ("yes", "yes"),
        ("yes", "yes"),
        ("yes", "yes"),
        ("yes", "yes"),
        ("no", "no"),
        ("no", "no"),
        ("no", "no"),
        ("yes", "no"),
    ]
    for index, (first, second) in enumerate(labels):
        rows.extend(
            [
                {
                    "item_id": f"item-{index}",
                    "annotator_id": "rvw-a",
                    "valid": first,
                },
                {
                    "item_id": f"item-{index}",
                    "annotator_id": "rvw-b",
                    "valid": second,
                },
            ]
        )
    result = compute_agreement(
        rows,
        dimensions=["valid"],
        bootstrap_repetitions=300,
    )["valid"]
    assert result["analysis_state"] == "READY"
    assert result["raw_agreement"] == 0.875
    assert result["cohens_kappa"] is not None
    assert result["krippendorffs_alpha"] is not None
    assert result["raw_agreement_ci"]["state"] == "READY"
    assert result["cohens_kappa_ci"]["state"] == "READY"
    assert result["krippendorffs_alpha_ci"]["state"] == "READY"
    assert result["prevalence"]["majority_label"] == "yes"
    assert result["prevalence"]["majority_prevalence"] == 0.5625


def test_degenerate_prevalence_is_diagnosed_not_misreported_as_perfect_kappa() -> None:
    rows = [
        {
            "item_id": f"item-{item}",
            "annotator_id": reviewer,
            "valid": "yes",
        }
        for item in range(5)
        for reviewer in ("rvw-a", "rvw-b")
    ]
    result = compute_agreement(
        rows,
        dimensions=["valid"],
        bootstrap_repetitions=100,
    )["valid"]
    assert result["raw_agreement"] == 1.0
    assert result["cohens_kappa"] is None
    assert result["cohens_kappa_state"] == (
        "BLOCKED_DEGENERATE_PREVALENCE"
    )
    assert result["krippendorffs_alpha"] is None
    assert result["prevalence"]["warning"] == "HIGH_PREVALENCE"


def test_small_samples_return_explicit_blocked_interval_states() -> None:
    rows = [
        {
            "item_id": f"item-{item}",
            "annotator_id": reviewer,
            "valid": "yes" if item == 0 else "no",
        }
        for item in range(2)
        for reviewer in ("rvw-a", "rvw-b")
    ]
    result = compute_agreement(
        rows,
        dimensions=["valid"],
    )["valid"]
    assert result["analysis_state"] == "BLOCKED_INSUFFICIENT_SAMPLE"
    assert result["raw_agreement_ci"]["state"] == (
        "BLOCKED_INSUFFICIENT_SAMPLE"
    )
    assert result["raw_agreement_ci"]["low"] is None
    assert result["cohens_kappa_ci"]["low"] is None


def test_duplicate_reviewer_for_same_item_is_not_treated_as_independent() -> None:
    rows = [
        {
            "item_id": "item-1",
            "annotator_id": "rvw-a",
            "valid": "yes",
        },
        {
            "item_id": "item-1",
            "annotator_id": "rvw-a",
            "valid": "yes",
        },
    ]
    result = compute_agreement(
        rows,
        dimensions=["valid"],
    )["valid"]
    assert result["items_with_two_or_more_annotations"] == 0
    assert result["duplicate_reviewer_units_rejected"] == ["item-1"]
