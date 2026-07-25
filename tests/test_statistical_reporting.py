import pandas as pd
import pytest

from causal_agent_bench.analysis.load_results import scores_to_dataframe
from causal_agent_bench.analysis.statistics import (
    agent_level_bootstrap,
    intervention_family_bootstrap,
    multiple_comparison_correction,
    paired_clean_intervention_tests,
    statistical_report,
    statistical_report_markdown,
    statistical_warnings,
)
from causal_agent_bench.schemas import ScoreRecord


def _score(agent, base_task, condition, success, family=None):
    return ScoreRecord(
        run_id="toy",
        instance_id=f"{base_task}.{condition}.{family or 'clean'}",
        agent_name=agent,
        metrics={"final_success_binary": success},
        diagnostics={
            "condition": condition,
            "base_task_id": base_task,
            "intervention_family": family,
        },
        metadata={},
    )


def _scores_df():
    records = [
        _score("agent_a", "t1", "clean", 1),
        _score("agent_a", "t2", "clean", 1),
        _score("agent_a", "t3", "clean", 0),
        _score("agent_a", "t1", "intervention", 0, "tool_failure"),
        _score("agent_a", "t2", "intervention", 1, "tool_failure"),
        _score("agent_a", "t3", "intervention", 0, "memory_corruption"),
        _score("agent_b", "t1", "clean", 1),
        _score("agent_b", "t2", "clean", 0),
        _score("agent_b", "t1", "intervention", 1, "tool_failure"),
        _score("agent_b", "t2", "intervention", 0, "tool_failure"),
    ]
    return scores_to_dataframe(records)


def test_paired_clean_intervention_tests_use_base_task_pairing():
    rows = paired_clean_intervention_tests(_scores_df(), seed=1, n_boot=100)
    agent_a = next(row for row in rows if row["agent"] == "agent_a")

    assert agent_a["n_pairs"] == 3
    assert agent_a["mean_clean"] == 0.666667
    assert agent_a["mean_intervention"] == 0.333333
    assert agent_a["absolute_degradation"] == 0.333333
    assert agent_a["acrs"] == pytest.approx(0.5, abs=1e-5)
    assert agent_a["bootstrap_ci"]["absolute_degradation"][0] is not None


def test_family_and_agent_bootstrap_outputs_effect_sizes():
    scores = _scores_df()
    family = intervention_family_bootstrap(scores, seed=2, n_boot=100)
    agent = agent_level_bootstrap(scores, seed=3, n_boot=100)

    tool_failure = next(
        row
        for row in family
        if row["agent"] == "agent_a" and row["intervention_family"] == "tool_failure"
    )
    agent_a = next(row for row in agent if row["agent"] == "agent_a")

    assert tool_failure["n"] == 2
    # Family clean denominators use exactly t1/t2, not global t1/t2/t3.
    assert tool_failure["clean_success"] == 1.0
    assert tool_failure["absolute_degradation"] == 0.5
    assert tool_failure["success_ci"][0] is not None
    assert agent_a["clean_success"] == 0.666667
    assert agent_a["acrs"] == pytest.approx(0.5, abs=1e-5)


def test_statistical_warnings_flag_small_samples_and_many_families():
    rows = []
    for index in range(6):
        family = f"family_{index}"
        rows.append(
            {
                "agent_name": "agent_a",
                "diagnostic_condition": "intervention",
                "diagnostic_base_task_id": f"t{index}",
                "diagnostic_intervention_family": family,
                "final_success_binary": 1,
            }
        )
    scores = pd.DataFrame(rows)
    warnings = statistical_warnings(
        scores,
        [{"agent": "agent_a", "n_pairs": 3}],
        [{"agent": "agent_a", "intervention_family": "family_0", "n": 1}],
    )

    assert any("multiple comparisons" in warning for warning in warnings)
    assert any("minimum sample-size" in warning for warning in warnings)
    assert any("minimum family-size" in warning for warning in warnings)


def test_statistical_report_handles_empty_scores():
    class EmptyRun:
        scores_df = pd.DataFrame()
        aggregate = {}

    report = statistical_report(EmptyRun())  # type: ignore[arg-type]

    assert report["paired_clean_vs_intervention"] == []
    assert "no score records available" in report["warnings"]


def test_paired_rows_include_cliffs_delta_and_bca_ci():
    rows = paired_clean_intervention_tests(_scores_df())
    agent_a = next(row for row in rows if row["agent"] == "agent_a")
    assert agent_a["cliffs_delta"] is not None
    assert -1.0 <= agent_a["cliffs_delta"] <= 1.0
    bca = agent_a["bootstrap_ci_bca"]["absolute_degradation"]
    assert bca[0] is not None and bca[1] is not None
    assert bca[0] <= bca[1]
    # BCa is an independent stream and must not perturb the percentile CI.
    assert agent_a["bootstrap_ci"]["absolute_degradation"][0] is not None


def test_multiple_comparison_correction_adjusts_upward_and_is_in_report():
    rows = paired_clean_intervention_tests(_scores_df())
    correction = multiple_comparison_correction(rows)
    assert correction["methods"] == ["holm", "benjamini_hochberg"]
    for test in correction["tests"]:
        if test["p_value"] is not None:
            # Holm adjustment never reduces a p-value.
            assert test["holm_adjusted_p_value"] >= test["p_value"] - 1e-9
            assert isinstance(test["significant_holm"], bool)

    report = statistical_report(_DfRun(_scores_df()))
    assert "multiple_comparison_correction" in report
    assert "Multiple-comparison correction" in statistical_report_markdown(report)


class _DfRun:
    def __init__(self, scores_df):
        self.scores_df = scores_df
        self.aggregate = {}
