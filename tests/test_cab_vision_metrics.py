"""Tests for CAB-Vision causal metrics."""

from __future__ import annotations

from cab_vision.eval.metrics import (
    EvalResult,
    accuracy,
    accuracy_by_condition,
    action_validity,
    causal_consistency,
    intervention_sensitivity,
    spurious_cue_resistance,
    summarize,
)


def _pair(pair_id, gold_obs, gold_int, pred_obs, pred_int, expected_change):
    """Build an observational+interventional result pair."""

    return [
        EvalResult(
            task_id=f"{pair_id}_obs",
            family="intervention_consistency",
            prediction=pred_obs,
            gold_index=gold_obs,
            pair_id=pair_id,
            condition="observational",
            expected_answer_change="unclear",
        ),
        EvalResult(
            task_id=f"{pair_id}_int",
            family="intervention_consistency",
            prediction=pred_int,
            gold_index=gold_int,
            pair_id=pair_id,
            condition="interventional",
            expected_answer_change=expected_change,
        ),
    ]


# --- accuracy ----------------------------------------------------------------


def test_accuracy_basic():
    results = [
        EvalResult("a", "visual_intervention", prediction=1, gold_index=1),
        EvalResult("b", "visual_intervention", prediction=0, gold_index=1),
    ]
    assert accuracy(results) == 0.5


def test_accuracy_empty_is_none():
    assert accuracy([]) is None


def test_accuracy_by_condition():
    results = [
        EvalResult("a", "intervention_consistency", 1, 1, condition="observational"),
        EvalResult("b", "intervention_consistency", 0, 1, condition="interventional"),
    ]
    by_cond = accuracy_by_condition(results)
    assert by_cond["observational"] == 1.0
    assert by_cond["interventional"] == 0.0


# --- causal consistency ------------------------------------------------------


def test_causal_consistency_perfect():
    # pair should change (expected yes) AND model changed -> consistent
    results = _pair("p1", gold_obs=0, gold_int=1, pred_obs=0, pred_int=1, expected_change="yes")
    assert causal_consistency(results) == 1.0


def test_causal_consistency_prior_locked_model():
    # answer should change but model gave the same answer both times -> inconsistent
    results = _pair("p1", gold_obs=0, gold_int=1, pred_obs=0, pred_int=0, expected_change="yes")
    assert causal_consistency(results) == 0.0


def test_causal_consistency_over_reactive_model():
    # answer should NOT change, but model flipped it -> inconsistent
    results = _pair("p1", gold_obs=0, gold_int=0, pred_obs=0, pred_int=2, expected_change="no")
    assert causal_consistency(results) == 0.0


def test_causal_consistency_ignores_incomplete_pairs():
    # only an observational member present -> no scorable pair
    results = [
        EvalResult("solo", "intervention_consistency", 0, 0, pair_id="p9", condition="observational")
    ]
    assert causal_consistency(results) is None


# --- intervention sensitivity ------------------------------------------------


def test_intervention_sensitivity_detects_change():
    results = _pair("p1", 0, 1, pred_obs=0, pred_int=1, expected_change="yes")
    assert intervention_sensitivity(results) == 1.0


def test_intervention_sensitivity_zero_when_unchanged():
    results = _pair("p1", 0, 1, pred_obs=3, pred_int=3, expected_change="yes")
    assert intervention_sensitivity(results) == 0.0


def test_intervention_sensitivity_none_when_no_change_expected():
    results = _pair("p1", 0, 0, pred_obs=0, pred_int=0, expected_change="no")
    assert intervention_sensitivity(results) is None


# --- spurious cue resistance -------------------------------------------------


def test_spurious_resistance_avoids_trap():
    results = [
        EvalResult("s1", "spurious_cue", prediction=1, gold_index=1, spurious_index=0),
        EvalResult("s2", "spurious_cue", prediction=0, gold_index=1, spurious_index=0),
    ]
    # first avoids trap, second falls for it -> 0.5
    assert spurious_cue_resistance(results) == 0.5


def test_spurious_resistance_none_without_spurious_tasks():
    results = [EvalResult("a", "visual_intervention", 1, 1)]
    assert spurious_cue_resistance(results) is None


# --- action validity ---------------------------------------------------------


def test_action_validity():
    results = [
        EvalResult("a", "action_selection", prediction=1, gold_index=1, valid_action_indices=[1]),
        EvalResult("b", "action_selection", prediction=0, gold_index=1, valid_action_indices=[1]),
    ]
    assert action_validity(results) == 0.5


# --- summary panel -----------------------------------------------------------


def test_summarize_returns_full_panel():
    results = _pair("p1", 0, 1, pred_obs=0, pred_int=1, expected_change="yes")
    results.append(
        EvalResult("s1", "spurious_cue", prediction=1, gold_index=1, spurious_index=0)
    )
    panel = summarize(results)
    assert panel["n"] == 3
    assert panel["causal_consistency"] == 1.0
    assert panel["intervention_sensitivity"] == 1.0
    assert panel["spurious_cue_resistance"] == 1.0
    # no action tasks present
    assert panel["action_validity"] is None
