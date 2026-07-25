from causal_agent_bench.metrics.acrs_v2 import (
    abstention_correctness,
    acrs_ratio,
    degradation_metrics,
    family_acrs,
    rank_shift,
    rank_with_ties,
    scorer_adjusted_success,
)


def test_acrs_edge_cases_fixture_only_not_evidence():
    assert acrs_ratio(0.5, 1.0) == 0.5
    assert acrs_ratio(0.5, 0.0) is None
    assert degradation_metrics(1.0, 0.25)["absolute_degradation"] == 0.75


def test_family_acrs_macro_micro_worst_fixture_only_not_evidence():
    rows = [
        {"condition": "clean", "success": 1, "family": None},
        {"condition": "clean", "success": 1, "family": None},
        {"condition": "intervention", "success": 1, "family": "tool_failure"},
        {"condition": "intervention", "success": 0, "family": "memory_corruption"},
    ]
    result = family_acrs(rows)
    assert result["fixture_only_not_evidence"] is True
    assert result["acrs"] == 0.5
    assert result["macro_family_acrs"] == 0.5
    assert result["worst_family_robustness"] == 0.0


def test_rank_shift_handles_ties_fixture_only_not_evidence():
    ranks = rank_with_ties({"a": 1.0, "b": 1.0, "c": 0.5})
    assert ranks["a"] == 1.5
    assert ranks["b"] == 1.5
    shift = rank_shift({"a": 1.0, "b": 0.8}, {"a": 0.2, "b": 0.9})
    assert shift["rank_delta"]["a"] == 1.0


def test_abstention_and_manual_adjustment_require_real_review_fixture_only_not_evidence():
    rows = [
        {"abstention_required": True, "abstained": True, "success": 1},
        {"abstention_required": True, "abstained": False, "success": 0},
    ]
    assert abstention_correctness(rows) == 0.5
    assert scorer_adjusted_success(rows) is None
    reviewed = [{"manual_review_status": "complete", "manual_success": 1}]
    assert scorer_adjusted_success(reviewed) == 1.0
