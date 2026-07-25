"""Property-based invariant tests (Hypothesis) for the statistical and hashing core.

These complement the example-based unit tests: instead of pinning specific output
values, they assert *mathematical and structural invariants* that must hold across a
wide range of generated inputs (bounds, symmetry, monotonicity, determinism,
permutation/closure properties). They therefore do not touch any pinned scientific
number — they check the relationships those numbers must obey.

If one of these fails, Hypothesis prints a minimal counterexample, which is usually a
sharper bug report than a fixed-input unit test.
"""

from __future__ import annotations

import itertools

from hypothesis import given, settings
from hypothesis import strategies as st

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.metrics.statistics import (
    adjust_pvalues,
    bca_bootstrap_ci,
    cliffs_delta,
    rank_agents,
    spearman_from_rankings,
)

# --- shared strategies -------------------------------------------------------

_finite = st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False)
_samples = st.lists(_finite, min_size=1, max_size=25)
_pvalues = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
_json_atoms = (
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text()
)
_json = st.recursive(
    _json_atoms,
    lambda children: st.lists(children, max_size=5)
    | st.dictionaries(st.text(max_size=5), children, max_size=5),
    max_leaves=12,
)

_TOL = 1e-6  # outputs are rounded to 6 decimals; compare with this slack


# --- stable_hash -------------------------------------------------------------


@given(st.dictionaries(st.text(min_size=1, max_size=6), st.integers(), min_size=2, max_size=8))
def test_stable_hash_is_key_order_independent(mapping: dict[str, int]) -> None:
    """Reordering a dict's keys must not change its stable hash (sort_keys=True)."""
    reordered = dict(reversed(list(mapping.items())))
    assert stable_hash(mapping) == stable_hash(reordered)


@given(_json, st.integers(min_value=1, max_value=64))
def test_stable_hash_length_and_alphabet(data: object, length: int) -> None:
    digest = stable_hash(data, length=length)
    assert len(digest) == length
    assert set(digest) <= set("0123456789abcdef")


@given(_json)
def test_stable_hash_is_deterministic(data: object) -> None:
    assert stable_hash(data) == stable_hash(data)


# --- cliffs_delta ------------------------------------------------------------


@given(_samples, _samples)
def test_cliffs_delta_is_bounded(a: list[float], b: list[float]) -> None:
    delta = cliffs_delta(a, b)
    assert delta is not None
    assert -1.0 <= delta <= 1.0


@given(_samples, _samples)
def test_cliffs_delta_is_antisymmetric(a: list[float], b: list[float]) -> None:
    forward = cliffs_delta(a, b)
    backward = cliffs_delta(b, a)
    assert forward is not None and backward is not None
    assert abs(forward + backward) < _TOL


@given(_samples)
def test_cliffs_delta_self_comparison_is_zero(a: list[float]) -> None:
    assert cliffs_delta(a, a) == 0.0


@given(_samples, _samples)
def test_cliffs_delta_fully_separated_is_extremal(a: list[float], b: list[float]) -> None:
    """If every element of one sample exceeds the other, |delta| == 1."""
    if max(b) < min(a):
        assert cliffs_delta(a, b) == 1.0
    if max(a) < min(b):
        assert cliffs_delta(a, b) == -1.0


# --- adjust_pvalues ----------------------------------------------------------


@given(st.lists(_pvalues, min_size=1, max_size=20), st.sampled_from(["holm", "bh"]))
def test_adjusted_pvalues_bounded_and_not_below_raw(ps: list[float], method: str) -> None:
    adjusted = adjust_pvalues(ps, method=method)
    assert len(adjusted) == len(ps)
    for raw, adj in zip(ps, adjusted, strict=True):
        assert adj is not None
        assert 0.0 <= adj <= 1.0
        # Multiplicity correction can only inflate (or keep) a p-value.
        assert adj >= raw - _TOL


@given(st.lists(_pvalues, min_size=2, max_size=20), st.sampled_from(["holm", "bh"]))
def test_adjusted_pvalues_monotone_in_raw_order(ps: list[float], method: str) -> None:
    adjusted = adjust_pvalues(ps, method=method)
    by_raw = sorted(zip(ps, adjusted, strict=True), key=lambda pair: pair[0])
    ordered = [adj for _, adj in by_raw]
    for lower, higher in itertools.pairwise(ordered):
        assert lower is not None and higher is not None
        assert lower <= higher + _TOL


@given(st.lists(st.one_of(_pvalues, st.none()), min_size=1, max_size=20))
def test_adjusted_pvalues_pass_through_none(ps: list[float | None]) -> None:
    adjusted = adjust_pvalues(ps, method="holm")
    for raw, adj in zip(ps, adjusted, strict=True):
        assert (adj is None) == (raw is None)


# --- bca_bootstrap_ci --------------------------------------------------------


@given(
    st.lists(_finite, min_size=2, max_size=20),
    st.integers(min_value=0, max_value=2**31 - 1),
)
@settings(max_examples=40, deadline=None)
def test_bca_ci_is_ordered_and_within_data_range(values: list[float], seed: int) -> None:
    lo, hi = bca_bootstrap_ci(values, seed=seed, n_boot=150)
    assert lo is not None and hi is not None
    assert lo <= hi + _TOL
    # The statistic is the mean, so every bootstrap/quantile value lies in [min, max].
    assert lo >= min(values) - _TOL
    assert hi <= max(values) + _TOL


@given(
    st.lists(_finite, min_size=2, max_size=15),
    st.integers(min_value=0, max_value=10**6),
)
@settings(max_examples=30, deadline=None)
def test_bca_ci_is_seed_deterministic(values: list[float], seed: int) -> None:
    first = bca_bootstrap_ci(values, seed=seed, n_boot=120)
    second = bca_bootstrap_ci(values, seed=seed, n_boot=120)
    assert first == second


@given(st.lists(_finite, max_size=1), st.integers(min_value=0, max_value=1000))
def test_bca_ci_degenerate_sample_returns_none(values: list[float], seed: int) -> None:
    assert bca_bootstrap_ci(values, seed=seed) == [None, None]


# --- rank_agents / spearman --------------------------------------------------


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=4),
        st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=8,
    )
)
def test_rank_agents_produces_a_permutation(scores: dict[str, float]) -> None:
    agent_scores = {agent: {"acrs": value} for agent, value in scores.items()}
    ranks = rank_agents(agent_scores, "acrs")
    assert sorted(ranks.values()) == list(range(1, len(scores) + 1))


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=4),
        st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=8,
    )
)
def test_rank_agents_orders_higher_scores_first(scores: dict[str, float]) -> None:
    agent_scores = {agent: {"acrs": value} for agent, value in scores.items()}
    ranks = rank_agents(agent_scores, "acrs")
    for x in scores:
        for y in scores:
            if scores[x] > scores[y]:
                assert ranks[x] < ranks[y]


@given(st.integers(min_value=2, max_value=12))
def test_spearman_of_identical_rankings_is_one(n: int) -> None:
    ranking = {f"agent_{i}": i + 1 for i in range(n)}
    assert spearman_from_rankings(ranking, ranking) == 1.0
