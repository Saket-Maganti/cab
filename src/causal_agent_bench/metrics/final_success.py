from __future__ import annotations

from typing import Any

from causal_agent_bench.metrics.base import expected_answer_fragments, success_criteria
from causal_agent_bench.schemas import Trajectory


def score_final_success(context: Any, trajectory: Trajectory) -> dict[str, float | int]:
    answer = (trajectory.final_answer or "").lower()
    fragments = [fragment.lower() for fragment in expected_answer_fragments(context) if fragment]
    if fragments:
        matches = sum(1 for fragment in fragments if fragment in answer)
        partial = matches / len(fragments)
        binary = float(matches == len(fragments))
    else:
        criteria = success_criteria(context)
        matches = sum(1 for criterion in criteria if _criterion_hint(criterion) in answer)
        partial = matches / len(criteria) if criteria else 0.0
        binary = float(partial == 1.0 and bool(criteria))
    return {
        "final_success_binary": int(binary),
        "final_success_partial": round(partial, 6),
    }


def _criterion_hint(criterion: str) -> str:
    words = [word.strip(".,;:!?").lower() for word in criterion.split()]
    useful = [word for word in words if len(word) > 4]
    return useful[0] if useful else criterion.lower()
