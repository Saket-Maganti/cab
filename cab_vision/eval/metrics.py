"""Causal evaluation metrics for CAB-Vision.

Metrics operate on lightweight ``EvalResult`` records so they can be unit-tested
without any model calls. Each record pairs a task's gold annotation with a single
predicted answer index. The metrics intentionally go *beyond accuracy* — the
point of the benchmark is to expose *why* a model is wrong:

  * ``accuracy`` / ``accuracy_by_condition`` — baseline correctness.
  * ``causal_consistency`` — over paired (observational/interventional or
    before/after) tasks, does the model change its answer iff the causal
    structure changed? A model that ignores the intervention OR over-reacts to
    cosmetic edits scores poorly even with high raw accuracy.
  * ``intervention_sensitivity`` — among pairs where the answer *should* change,
    how often does the model actually change it? (Detects prior-locked models.)
  * ``spurious_cue_resistance`` — on cue-conflict tasks, how often does the model
    avoid the misleading-correlation trap?
  * ``action_validity`` — on action-selection tasks, how often is the chosen
    action causally permissible?

All metrics return ``None`` when the relevant population is empty so callers can
distinguish "0.0" from "not measured".
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class EvalResult:
    """One model prediction joined with the gold annotation needed to score it.

    Built from a ``VisualCausalTask`` plus a predicted answer index. Kept as a
    plain dataclass (not pydantic) so tests can construct it trivially.
    """

    task_id: str
    family: str
    prediction: int  # predicted answer-choice index
    gold_index: int
    # paired-family fields
    pair_id: str | None = None
    condition: str | None = None  # "observational" | "interventional"
    expected_answer_change: str = "unclear"  # yes | no | unclear
    # spurious-cue field
    spurious_index: int | None = None
    # action-selection field
    valid_action_indices: list[int] = field(default_factory=list)

    @property
    def correct(self) -> bool:
        return self.prediction == self.gold_index


def _frac(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def accuracy(results: list[EvalResult]) -> float | None:
    """Fraction of predictions matching the gold answer."""

    if not results:
        return None
    return round(mean(1.0 if r.correct else 0.0 for r in results), 6)


def accuracy_by_condition(results: list[EvalResult]) -> dict[str, float | None]:
    """Accuracy split by ``condition`` (observational vs interventional)."""

    buckets: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        if r.condition is not None:
            buckets[r.condition].append(r)
    return {cond: accuracy(rows) for cond, rows in sorted(buckets.items())}


def _pairs(results: list[EvalResult]) -> dict[str, dict[str, EvalResult]]:
    """Group paired results by pair_id -> {condition: result}.

    Only pairs with both an ``observational`` and an ``interventional`` member
    are returned. For before/after counterfactual tasks, encode the "before"
    member as ``observational`` and the "after" member as ``interventional``.
    """

    grouped: dict[str, dict[str, EvalResult]] = defaultdict(dict)
    for r in results:
        if r.pair_id is None or r.condition is None:
            continue
        grouped[r.pair_id][r.condition] = r
    return {
        pid: members
        for pid, members in grouped.items()
        if "observational" in members and "interventional" in members
    }


def causal_consistency(results: list[EvalResult]) -> float | None:
    """Fraction of pairs whose answer-change behaviour matches the causal truth.

    For each complete pair, the model is *consistent* when::

        (pred_obs != pred_int)  ==  (expected_answer_change == "yes")

    i.e. it changes its answer exactly when the causal structure changed.
    Pairs whose ``expected_answer_change`` is "unclear" are excluded.
    """

    pairs = _pairs(results)
    scored = 0
    consistent = 0
    for members in pairs.values():
        obs = members["observational"]
        intv = members["interventional"]
        expected = intv.expected_answer_change or obs.expected_answer_change
        if expected not in {"yes", "no"}:
            continue
        scored += 1
        changed = obs.prediction != intv.prediction
        should_change = expected == "yes"
        if changed == should_change:
            consistent += 1
    return _frac(consistent, scored)


def intervention_sensitivity(results: list[EvalResult]) -> float | None:
    """Among pairs that *should* change, fraction where the model changed.

    Low sensitivity = the model is locked to its prior / blind to the
    intervention. Complements ``causal_consistency`` (which also penalises
    over-reaction to cosmetic edits).
    """

    pairs = _pairs(results)
    should_change = 0
    did_change = 0
    for members in pairs.values():
        obs = members["observational"]
        intv = members["interventional"]
        expected = intv.expected_answer_change or obs.expected_answer_change
        if expected != "yes":
            continue
        should_change += 1
        if obs.prediction != intv.prediction:
            did_change += 1
    return _frac(did_change, should_change)


def spurious_cue_resistance(results: list[EvalResult]) -> float | None:
    """On spurious-cue tasks, fraction where the model avoids the trap.

    A task counts as resisted when the prediction is *not* the spurious-trap
    option. When no trap index is annotated, falls back to plain correctness.
    Only ``spurious_cue`` family results are considered.
    """

    population = [r for r in results if r.family == "spurious_cue"]
    if not population:
        return None
    resisted = 0
    for r in population:
        if r.spurious_index is None:
            resisted += int(r.correct)
        else:
            resisted += int(r.prediction != r.spurious_index)
    return _frac(resisted, len(population))


def action_validity(results: list[EvalResult]) -> float | None:
    """On action-selection tasks, fraction where the chosen action is valid."""

    population = [r for r in results if r.family == "action_selection"]
    if not population:
        return None
    valid = sum(1 for r in population if r.prediction in r.valid_action_indices)
    return _frac(valid, len(population))


def summarize(results: list[EvalResult]) -> dict[str, Any]:
    """Compute the full CAB-Vision metric panel for a set of results."""

    return {
        "n": len(results),
        "accuracy": accuracy(results),
        "accuracy_by_condition": accuracy_by_condition(results),
        "causal_consistency": causal_consistency(results),
        "intervention_sensitivity": intervention_sensitivity(results),
        "spurious_cue_resistance": spurious_cue_resistance(results),
        "action_validity": action_validity(results),
    }
