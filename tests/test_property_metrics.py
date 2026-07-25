"""Property-based invariants for the core causal-robustness metrics.

`success_rate`, `acrs` (Agent Causal Robustness Score), and `degradation` are THE
benchmark metrics, so their mathematical guarantees are worth pinning across a wide
range of generated inputs rather than a few fixed examples:

* a success rate is always a fraction in [0, 1] and equals the mean outcome;
* ACRS is a non-negative ratio, exactly 1 at parity, 0 when intervention always
  fails, and undefined (None) when the clean rate is 0 or missing;
* absolute degradation is the clean-minus-intervention difference, bounded [-1, 1].
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from causal_agent_bench.metrics.causal_robustness import acrs, degradation, success_rate

_rate = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
_positive_rate = st.floats(min_value=1e-6, max_value=1.0, allow_nan=False, allow_infinity=False)
_TOL = 1e-6


def _rows(binaries: list[int]) -> list[dict]:
    return [{"metrics": {"final_success_binary": value}} for value in binaries]


# --- success_rate ------------------------------------------------------------


@given(st.lists(st.sampled_from([0, 1]), min_size=1, max_size=50))
def test_success_rate_is_a_fraction(binaries: list[int]) -> None:
    rate = success_rate(_rows(binaries))
    assert rate is not None
    assert 0.0 <= rate <= 1.0
    assert abs(rate - sum(binaries) / len(binaries)) < _TOL


def test_success_rate_of_empty_is_none() -> None:
    assert success_rate([]) is None


# --- acrs --------------------------------------------------------------------


@given(_rate, _positive_rate)
def test_acrs_is_a_nonnegative_ratio(intervention_rate: float, clean_rate: float) -> None:
    score = acrs(intervention_rate, clean_rate)
    assert score is not None
    assert score >= 0.0
    assert score == round(intervention_rate / clean_rate, 6)


@given(_positive_rate)
def test_acrs_is_one_at_parity(clean_rate: float) -> None:
    # Identical intervention and clean rate => no robustness loss => ACRS == 1.
    assert acrs(clean_rate, clean_rate) == 1.0


@given(_positive_rate)
def test_acrs_is_zero_when_intervention_always_fails(clean_rate: float) -> None:
    assert acrs(0.0, clean_rate) == 0.0


@given(_rate)
def test_acrs_is_undefined_when_clean_is_zero_or_missing(intervention_rate: float) -> None:
    assert acrs(intervention_rate, 0.0) is None
    assert acrs(intervention_rate, None) is None
    assert acrs(None, 1.0) is None


# --- degradation -------------------------------------------------------------


@given(_rate, _rate)
def test_absolute_degradation_is_the_signed_difference(
    clean_rate: float, intervention_rate: float
) -> None:
    result = degradation(clean_rate, intervention_rate)
    absolute = result["absolute_degradation"]
    assert absolute is not None
    assert absolute == round(clean_rate - intervention_rate, 6)
    assert -1.0 <= absolute <= 1.0


@given(_rate, _positive_rate)
def test_relative_degradation_complements_acrs(
    intervention_rate: float, clean_rate: float
) -> None:
    result = degradation(clean_rate, intervention_rate)
    score = acrs(intervention_rate, clean_rate)
    assert result["relative_degradation"] == round(1 - score, 6)
