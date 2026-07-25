from __future__ import annotations

from copy import deepcopy

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from causal_agent_bench.metrics.causal_robustness import (
    agent_robustness,
    matched_pair_outcomes,
    paired_metrics_fixture_self_check,
)
from causal_agent_bench.metrics.statistics import (
    clustered_paired_bootstrap,
    paired_binary_test,
    rank_bootstrap,
    scorer_error_sensitivity,
    stratified_paired_bootstrap,
)


def _row(
    base_task_id: str,
    condition: str,
    success: int,
    *,
    agent: str = "agent_a",
    model: str | None = None,
    family: str | None = None,
    intervention_id: str | None = None,
    repeat_id: int | None = 0,
    extra_metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    metrics: dict[str, object] = {"final_success_binary": success}
    metrics.update(extra_metrics or {})
    diagnostics: dict[str, object] = {
        "condition": condition,
        "base_task_id": base_task_id,
        "intervention_family": family,
        "intervention_id": intervention_id,
    }
    if repeat_id is not None:
        diagnostics["repeat_id"] = repeat_id
    return {
        "instance_id": (
            f"{base_task_id}.clean"
            if condition == "clean"
            else intervention_id or f"{base_task_id}.{family}"
        ),
        "agent_name": agent,
        "metrics": metrics,
        "diagnostics": diagnostics,
        "metadata": {"model_name": model} if model else {},
    }


def _paired_rows(
    outcomes: list[tuple[int, int]],
    *,
    agent: str = "agent_a",
    family: str = "tool_failure",
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (clean, intervention) in enumerate(outcomes):
        base = f"task_{index}"
        rows.extend(
            [
                _row(base, "clean", clean, agent=agent),
                _row(
                    base,
                    "intervention",
                    intervention,
                    agent=agent,
                    family=family,
                    intervention_id=f"{base}.{family}",
                ),
            ]
        )
    return rows


def test_family_denominators_are_exact_matched_subsets() -> None:
    rows = [
        _row("t1", "clean", 1),
        _row("t2", "clean", 0),
        _row("t3", "clean", 1),
        _row(
            "t1",
            "intervention",
            0,
            family="tool_failure",
            intervention_id="t1.tool_failure",
        ),
        _row(
            "t2",
            "intervention",
            0,
            family="tool_failure",
            intervention_id="t2.tool_failure",
        ),
        _row(
            "t3",
            "intervention",
            1,
            family="memory_corruption",
            intervention_id="t3.memory_corruption",
        ),
    ]
    result = agent_robustness(rows)["agent_a"]

    assert result["n_pairs"] == 3
    assert result["clean_success_rate"] == pytest.approx(2 / 3, abs=1e-6)
    tool = result["families"]["tool_failure"]
    memory = result["families"]["memory_corruption"]
    assert tool["clean_success_rate"] == 0.5
    assert tool["success_rate"] == 0.0
    assert tool["absolute_degradation"] == 0.5
    assert memory["clean_success_rate"] == 1.0
    assert memory["acrs_family"] == 1.0
    assert result["transition_profile"]["success_to_failure"]["count"] == 1
    assert result["transition_profile"]["failure_to_failure"]["count"] == 1
    assert result["transition_profile"]["success_to_success"]["count"] == 1


def test_lightweight_paired_metrics_fixture_self_check() -> None:
    check = paired_metrics_fixture_self_check()

    assert check["passed"] is True
    assert check["evidence_class"] == "FIXTURE_ONLY"
    assert check["scientific_evidence"] is False
    assert check["observed"]["global_clean_success_rate"] == 0.666667
    assert check["observed"]["tool_family_clean_success_rate"] == 0.5


def test_paper_eligible_class_is_accepted_as_real_without_creating_results() -> None:
    result = matched_pair_outcomes(
        _paired_rows([(1, 0)]),
        evidence_class="PAPER_ELIGIBLE_EVIDENCE",
    )
    assert result
    assert all(subject["scientific_evidence"] is True for subject in result.values())


def test_duplicate_incomplete_and_missing_identifiers_are_never_averaged() -> None:
    rows = [
        _row("duplicate_clean", "clean", 1),
        _row("duplicate_clean", "clean", 0),
        _row(
            "duplicate_clean",
            "intervention",
            0,
            family="tool_failure",
            intervention_id="duplicate_clean.tool_failure",
        ),
        _row(
            "missing_clean",
            "intervention",
            1,
            family="tool_failure",
            intervention_id="missing_clean.tool_failure",
        ),
        _row("missing_intervention", "clean", 1),
        _row("duplicate_intervention", "clean", 1),
        _row(
            "duplicate_intervention",
            "intervention",
            0,
            family="tool_failure",
            intervention_id="duplicate_intervention.tool_failure",
        ),
        _row(
            "duplicate_intervention",
            "intervention",
            1,
            family="tool_failure",
            intervention_id="duplicate_intervention.tool_failure",
        ),
        {
            "agent_name": "agent_a",
            "instance_id": "missing_base.tool_failure",
            "metrics": {"final_success_binary": 1},
            "diagnostics": {
                "condition": "intervention",
                "intervention_family": "tool_failure",
            },
        },
    ]
    result = agent_robustness(rows)["agent_a"]
    reasons = result["pairing_summary"]["invalid_pair_reason_counts"]

    assert result["n_pairs"] == 0
    assert result["clean_success_rate"] is None
    assert result["denominator_policy"]["state"] == "missing_clean_condition"
    assert reasons["duplicate_clean_run"] == 1
    assert reasons["duplicate_intervention_run"] == 1
    assert reasons["missing_clean_condition"] == 1
    assert reasons["missing_intervention_condition"] == 1
    assert reasons["missing_base_task_id"] == 1
    assert all(
        pair["completeness_state"] == "invalid"
        for pair in result["invalid_pairs"]
    )


def test_explicit_repeats_match_independently() -> None:
    rows = []
    for repeat, intervention_success in ((0, 0), (1, 1)):
        rows.extend(
            [
                _row("task", "clean", 1, repeat_id=repeat),
                _row(
                    "task",
                    "intervention",
                    intervention_success,
                    family="tool_failure",
                    intervention_id="task.tool_failure",
                    repeat_id=repeat,
                ),
            ]
        )
    result = agent_robustness(rows)["agent_a"]

    assert result["n_pairs"] == 2
    assert {pair["repeat_id"] for pair in result["pair_outcomes"]} == {
        "0",
        "1",
    }
    assert result["absolute_degradation"] == 0.5
    assert result["pairing_summary"]["invalid_pair_count"] == 0


def test_duplicate_runs_without_repeat_id_are_rejected_not_averaged() -> None:
    rows = [
        _row("task", "clean", 1, repeat_id=None),
        _row("task", "clean", 0, repeat_id=None),
        _row(
            "task",
            "intervention",
            0,
            family="tool_failure",
            intervention_id="task.tool_failure",
            repeat_id=None,
        ),
        _row(
            "task",
            "intervention",
            1,
            family="tool_failure",
            intervention_id="task.tool_failure",
            repeat_id=None,
        ),
    ]
    result = agent_robustness(rows)["agent_a"]
    reasons = result["pairing_summary"]["invalid_pair_reason_counts"]

    assert result["n_pairs"] == 0
    assert result["raw_unpaired_clean_success_rate"] == 0.5
    assert result["raw_unpaired_intervention_success_rate"] == 0.5
    assert result["clean_success_rate"] is None
    assert result["intervention_success_rate"] is None
    assert reasons == {
        "duplicate_clean_run": 1,
        "duplicate_intervention_run": 1,
    }
    assert result["pairing_summary"]["implicit_repeat_row_count"] == 4
    assert result["invalid_pairs"][0]["source_row_indices"] == [0, 1, 2, 3]


def test_model_is_part_of_the_matched_unit() -> None:
    rows = [
        _row("task", "clean", 1, model="model_a"),
        _row(
            "task",
            "intervention",
            0,
            model="model_b",
            family="tool_failure",
            intervention_id="task.tool_failure",
        ),
    ]
    result = agent_robustness(rows)

    assert set(result) == {"agent_a::model_a", "agent_a::model_b"}
    assert all(payload["n_pairs"] == 0 for payload in result.values())
    assert {
        pair["invalid_pair_reason"]
        for payload in result.values()
        for pair in payload["invalid_pairs"]
    } == {"missing_clean_condition", "missing_intervention_condition"}


def test_zero_and_near_zero_denominators_are_explicit_and_suppressed() -> None:
    zero = agent_robustness(
        _paired_rows([(0, 0), (0, 1)])
    )["agent_a"]
    assert zero["denominator_policy"]["state"] == "zero_clean_success"
    assert zero["acrs"] is None
    assert zero["absolute_degradation"] == -0.5

    near_zero_outcomes = [(1, 1)] + [(0, 0)] * 19
    near_zero = agent_robustness(
        _paired_rows(near_zero_outcomes)
    )["agent_a"]
    assert near_zero["clean_success_rate"] == 0.05
    assert (
        near_zero["denominator_policy"]["state"]
        == "near_zero_clean_success"
    )
    assert near_zero["denominator_policy"]["ratio_reportable"] is False
    assert near_zero["acrs"] is None
    assert near_zero["relative_degradation"] is None


def test_recovery_abstention_and_transition_outcomes_are_preserved() -> None:
    rows = [
        _row("task", "clean", 1),
        _row(
            "task",
            "intervention",
            0,
            family="tool_failure",
            intervention_id="task.tool_failure",
            extra_metrics={
                "tool_error_recovery_binary": 1,
                "correct_abstention_binary": 1,
                "false_abstention_binary": 0,
            },
        ),
    ]
    result = agent_robustness(rows)["agent_a"]
    pair = result["pair_outcomes"][0]

    assert pair["transition"] == "success_to_failure"
    assert pair["conditional_degradation"] == 1
    assert result["conditional_robustness_among_clean_successes"] == 0.0
    assert result["recovery_success_rate"] == 1.0
    assert result["correct_abstention_rate"] == 1.0
    assert result["false_abstention_rate"] == 0.0


def test_clustered_and_stratified_bootstraps_are_deterministic() -> None:
    rows = [
        *_paired_rows([(1, 0), (1, 1)], family="tool_failure"),
        _row(
            "task_0",
            "intervention",
            0,
            family="memory_corruption",
            intervention_id="task_0.memory_corruption",
        ),
    ]
    pairs = agent_robustness(rows)["agent_a"]["pair_outcomes"]
    first = clustered_paired_bootstrap(
        pairs,
        seed=7,
        n_boot=100,
    )
    second = clustered_paired_bootstrap(
        pairs,
        seed=7,
        n_boot=100,
    )
    stratified = stratified_paired_bootstrap(
        pairs,
        seed=8,
        n_boot=100,
    )

    assert first == second
    assert first["resampling_unit"] == "base_task_id"
    assert first["cluster_count"] == 2
    assert first["point_estimate"]["n_pairs"] == 3
    assert stratified["strata_key"] == "intervention_family"
    assert stratified["stratum_count"] == 2


def test_exact_paired_binary_test_reports_transitions() -> None:
    result = paired_binary_test(
        [1, 1, 0, 0],
        [0, 0, 1, 0],
    )

    assert result["success_to_failure"] == 2
    assert result["failure_to_success"] == 1
    assert result["failure_to_failure"] == 1
    assert result["discordant_pair_count"] == 3
    assert result["p_value"] == 1.0


def test_rank_bootstrap_probability_matrix_is_coherent() -> None:
    rows: list[dict[str, object]] = []
    rows.extend(_paired_rows([(1, 1), (1, 1), (1, 0)], agent="a"))
    rows.extend(_paired_rows([(1, 1), (1, 0), (1, 0)], agent="b"))
    rows.extend(_paired_rows([(1, 0), (1, 0), (1, 0)], agent="c"))
    ledgers = matched_pair_outcomes(rows)
    pairs = [
        pair
        for ledger in ledgers.values()
        for pair in ledger["complete_pairs"]
    ]
    first = rank_bootstrap(pairs, seed=11, n_boot=200)
    second = rank_bootstrap(pairs, seed=11, n_boot=200)

    assert first == second
    assert first["state"] == "ok"
    assert first["common_cluster_count"] == 3
    assert first["common_pair_unit_count"] == 3
    matrix = first["pairwise_rank_probability_matrix"]
    for agent in ("a", "b", "c"):
        assert matrix[agent][agent] == 0.5
    for left, right in (("a", "b"), ("a", "c"), ("b", "c")):
        assert matrix[left][right] + matrix[right][left] == pytest.approx(1.0)
    assert first["point_robustness_ranking"]["a"] == 1.0
    assert first["point_robustness_ranking"]["c"] == 3.0


def test_rank_bootstrap_excludes_heterogeneous_pair_support() -> None:
    rows: list[dict[str, object]] = []
    rows.extend(_paired_rows([(1, 1), (1, 0)], agent="a"))
    rows.extend(_paired_rows([(1, 0), (1, 0)], agent="b"))
    # Agent a has an additional family on a shared base task. It must not be
    # silently weighted into only one side of the ranking.
    rows.append(
        _row(
            "task_0",
            "intervention",
            0,
            agent="a",
            family="memory_corruption",
            intervention_id="task_0.memory_corruption",
        )
    )
    pairs = [
        pair
        for ledger in matched_pair_outcomes(rows).values()
        for pair in ledger["complete_pairs"]
    ]
    result = rank_bootstrap(pairs, seed=4, n_boot=50)

    assert result["state"] == "ok"
    assert result["common_cluster_count"] == 2
    assert result["common_pair_unit_count"] == 2
    assert result["agent_pair_unit_counts"] == {"a": 3, "b": 2}
    assert result["excluded_noncommon_pair_unit_count"] == 1


def test_scorer_error_sensitivity_requires_explicit_assumptions() -> None:
    pairs = agent_robustness(
        _paired_rows([(1, 0), (1, 1)])
    )["agent_a"]["pair_outcomes"]
    unchanged = scorer_error_sensitivity(
        pairs,
        false_positive_rate=0.0,
        false_negative_rate=0.0,
    )
    unidentified = scorer_error_sensitivity(
        pairs,
        false_positive_rate=0.6,
        false_negative_rate=0.5,
    )

    assert unchanged["state"] == "sensitivity_scenario_only"
    assert unchanged["corrected"]["acrs"] == unchanged["baseline"]["acrs"]
    assert unidentified["available"] is False
    assert (
        unidentified["state"]
        == "unidentifiable_error_rates_sum_to_one_or_more"
    )
    assert unchanged["fixture_only_not_evidence"] is True


@given(
    st.lists(
        st.tuples(st.integers(min_value=0, max_value=1), st.integers(min_value=0, max_value=1)),
        min_size=1,
        max_size=30,
    )
)
@settings(max_examples=40, deadline=None)
def test_matched_aggregate_property_matches_pairwise_arithmetic(
    outcomes: list[tuple[int, int]],
) -> None:
    rows = _paired_rows(outcomes)
    forward = agent_robustness(rows)["agent_a"]
    reversed_result = agent_robustness(
        list(reversed(deepcopy(rows)))
    )["agent_a"]

    clean_mean = sum(clean for clean, _ in outcomes) / len(outcomes)
    intervention_mean = (
        sum(intervention for _, intervention in outcomes) / len(outcomes)
    )
    assert forward["n_pairs"] == len(outcomes)
    assert forward["clean_success_rate"] == round(clean_mean, 6)
    assert forward["intervention_success_rate"] == round(
        intervention_mean,
        6,
    )
    assert forward["absolute_degradation"] == round(
        clean_mean - intervention_mean,
        6,
    )
    assert sum(
        payload["count"]
        for payload in forward["transition_profile"].values()
    ) == len(outcomes)
    # Input order and source-row offsets cannot change any reported estimate.
    for key in (
        "clean_success_rate",
        "intervention_success_rate",
        "absolute_degradation",
        "conditional_robustness_among_clean_successes",
        "transition_profile",
        "n_pairs",
    ):
        assert forward[key] == reversed_result[key]
