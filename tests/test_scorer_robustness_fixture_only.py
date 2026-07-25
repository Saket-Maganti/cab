from causal_agent_bench.metrics.scorer_robustness import (
    contains_match,
    date_match,
    exact_match,
    list_set_match,
    normalized_match,
    numeric_match,
    refusal_or_uncertainty_handled,
    safe_contains_match,
)


def test_string_and_numeric_matching_fixture_only_not_evidence():
    assert exact_match("Answer", "Answer")
    assert not exact_match("Answer", "answer")
    assert normalized_match("Answer!", "answer")
    assert numeric_match("10.001", "10", tolerance=0.01)
    assert not numeric_match("10.2", "10", tolerance=0.01)


def test_list_date_and_substring_risks_fixture_only_not_evidence():
    assert list_set_match(["B", "A"], ["a", "b"])
    assert not list_set_match(["B", "A"], ["a", "b"], order_sensitive=True)
    assert date_match("2026-07-09", "2026-07-09")
    assert contains_match("cat", "concatenate") is True
    assert safe_contains_match("cat", "concatenate") is False
    assert safe_contains_match("cat", "the cat sat") is True


def test_abstention_handling_fixture_only_not_evidence():
    assert refusal_or_uncertainty_handled(
        "I cannot determine this from the available evidence.",
        abstention_required=True,
        definitive_answer_expected=False,
    )
    assert not refusal_or_uncertainty_handled(
        "I cannot determine this from the available evidence.",
        abstention_required=False,
        definitive_answer_expected=True,
    )
