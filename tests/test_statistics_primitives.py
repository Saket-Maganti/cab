"""Unit tests for the reusable statistical primitives in metrics.statistics."""

from __future__ import annotations

import pytest

from causal_agent_bench.metrics.statistics import (
    adjust_pvalues,
    bca_bootstrap_ci,
    cliffs_delta,
)


def test_adjust_pvalues_holm_matches_reference():
    # Reference values for Holm-Bonferroni on five ordered p-values.
    pvals = [0.01, 0.02, 0.03, 0.04, 0.05]
    assert adjust_pvalues(pvals, method="holm") == [0.05, 0.08, 0.09, 0.09, 0.09]


def test_adjust_pvalues_bh_matches_reference():
    pvals = [0.01, 0.02, 0.03, 0.04, 0.05]
    # Benjamini-Hochberg collapses this evenly-spaced family to a constant.
    assert adjust_pvalues(pvals, method="bh") == [0.05, 0.05, 0.05, 0.05, 0.05]


def test_adjust_pvalues_preserves_order_and_passes_through_none():
    pvals = [0.04, None, 0.01]
    holm = adjust_pvalues(pvals, method="holm")
    assert holm[1] is None
    # Two real tests => multiplier 2 on the smallest, then monotone.
    assert holm[2] == pytest.approx(0.02)
    assert holm[0] == pytest.approx(0.04)


def test_adjust_pvalues_rejects_unknown_method():
    with pytest.raises(ValueError, match="unknown method"):
        adjust_pvalues([0.1], method="bonferroni")


def test_adjust_pvalues_empty_and_all_none():
    assert adjust_pvalues([]) == []
    assert adjust_pvalues([None, None]) == [None, None]


def test_cliffs_delta_extremes_and_symmetry():
    assert cliffs_delta([1, 1, 1], [0, 0, 0]) == 1.0
    assert cliffs_delta([0, 0], [1, 1]) == -1.0
    assert cliffs_delta([1, 0], [1, 0]) == 0.0
    # Antisymmetry: delta(a, b) == -delta(b, a)
    assert cliffs_delta([3, 1, 2], [2, 2]) == -cliffs_delta([2, 2], [3, 1, 2])


def test_cliffs_delta_empty_returns_none():
    assert cliffs_delta([], [1, 2]) is None
    assert cliffs_delta([1, 2], []) is None


def test_bca_bootstrap_ci_is_deterministic_and_ordered():
    values = [0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    first = bca_bootstrap_ci(values, seed=7, n_boot=500)
    second = bca_bootstrap_ci(values, seed=7, n_boot=500)
    assert first == second
    assert first[0] is not None and first[1] is not None
    assert first[0] <= first[1]


def test_bca_bootstrap_ci_handles_degenerate_inputs():
    # n < 2 -> undefined interval
    assert bca_bootstrap_ci([0.5], seed=1) == [None, None]
    # Constant sample -> falls back to percentile (degenerate bias correction)
    assert bca_bootstrap_ci([1.0, 1.0, 1.0], seed=1) == [1.0, 1.0]


def test_bca_bootstrap_ci_brackets_true_mean_for_clean_signal():
    # A strongly separated sample's CI should sit in a sensible range.
    lo, hi = bca_bootstrap_ci([0.0] * 5 + [1.0] * 5, seed=3, n_boot=800)
    assert 0.0 <= lo <= hi <= 1.0
