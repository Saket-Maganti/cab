from __future__ import annotations

from typing import Any

from causal_agent_bench.metrics.typed_final_answer import (
    SCORER_NAME,
    SCORER_VERSION,
    TypedScoreResult,
    score_typed_final_answer,
    typed_scorer_fixture_self_check,
)
from causal_agent_bench.schemas import Trajectory


def score_final_success(
    context: Any,
    trajectory: Trajectory,
) -> dict[str, float | int | bool | str | None]:
    """Backward-compatible metric mapping from the canonical typed scorer."""

    return score_final_success_result(context, trajectory).metrics()


def score_final_success_result(
    context: Any,
    trajectory: Trajectory,
) -> TypedScoreResult:
    """Return the typed result, diagnostics, and scorer/gold provenance."""

    return score_typed_final_answer(context, trajectory)


__all__ = [
    "SCORER_NAME",
    "SCORER_VERSION",
    "score_final_success",
    "score_final_success_result",
    "typed_scorer_fixture_self_check",
]
