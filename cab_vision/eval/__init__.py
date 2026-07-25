"""Evaluation metrics for CAB-Vision."""

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

__all__ = [
    "EvalResult",
    "accuracy",
    "accuracy_by_condition",
    "action_validity",
    "causal_consistency",
    "intervention_sensitivity",
    "spurious_cue_resistance",
    "summarize",
]
