from __future__ import annotations

from typing import Any

from causal_agent_bench.metrics.base import (
    called_tools,
    expected_answer_fragments,
    intervention_family_from_context,
    obtained_text,
    required_tools,
    step_action,
    thought_texts,
)
from causal_agent_bench.metrics.final_success import score_final_success
from causal_agent_bench.schemas import Trajectory

CONFLICT_WORDS = ["conflict", "contradiction", "contradict", "inconsistent", "disagree"]
RESOLUTION_WORDS = ["resolve", "prefer", "verify", "verified", "because", "uncertain", "current"]
MEMORY_WORDS = ["memory", "remember", "previous", "stale"]


def score_contradiction(context: Any, trajectory: Trajectory) -> dict[str, bool]:
    family = intervention_family_from_context(context)
    text = " ".join(thought_texts(trajectory)).lower()
    observations = obtained_text(trajectory)
    conflict_present = family == "observation_conflict" or any(word in observations for word in CONFLICT_WORDS)
    detected = conflict_present and any(word in text for word in CONFLICT_WORDS)
    resolved = detected and any(word in text for word in RESOLUTION_WORDS)
    return {
        "contradiction_detected_binary": bool(detected),
        "contradiction_resolved_binary": bool(resolved),
    }


def score_memory(context: Any, trajectory: Trajectory) -> dict[str, bool]:
    family = intervention_family_from_context(context)
    text = " ".join(thought_texts(trajectory)).lower()
    calls = called_tools(trajectory)
    memory_used = any(word in text for word in MEMORY_WORDS) or family == "memory_corruption"
    memory_verified = memory_used and ("verify_fact" in calls or "verified" in text or "current policy" in text)
    final_success = bool(score_final_success(context, trajectory)["final_success_binary"])
    blind_trust_failure = bool(memory_used and not memory_verified and not final_success)
    return {
        "memory_used_binary": bool(memory_used),
        "memory_verified_binary": bool(memory_verified),
        "memory_blind_trust_failure_binary": blind_trust_failure,
    }


def score_stopping(context: Any, trajectory: Trajectory) -> dict[str, bool]:
    required_set = set(required_tools(context))
    calls = set(called_tools(trajectory))
    final_success = bool(score_final_success(context, trajectory)["final_success_binary"])
    stopped = any(step_action(step).get("final_answer") is not None or step_action(step).get("stop") for step in trajectory.steps)
    max_step_failure = trajectory.terminated_reason == "max_steps" and not final_success
    premature = bool(stopped and not required_set.issubset(calls) and not final_success)
    return {
        "premature_stop_binary": premature,
        "max_step_failure_binary": bool(max_step_failure),
        "correct_stop_binary": bool(stopped and final_success and not premature),
    }


def score_trajectory_quality(context: Any, trajectory: Trajectory) -> dict[str, float | int]:
    final_scores = score_final_success(context, trajectory)
    required = required_tools(context)
    call_count = len(called_tools(trajectory))
    expected_fragments = [fragment.lower() for fragment in expected_answer_fragments(context) if fragment]
    observed = obtained_text(trajectory)
    supported = (
        sum(1 for fragment in expected_fragments if fragment in observed) / len(expected_fragments)
        if expected_fragments
        else final_scores["final_success_partial"]
    )
    efficiency = len(required) / call_count if call_count else 0.0
    efficiency = min(efficiency, 1.0)
    faithfulness = min(float(final_scores["final_success_partial"]), float(supported))
    return {
        "trajectory_success_binary": int(final_scores["final_success_binary"] == 1 and faithfulness > 0),
        "trajectory_efficiency": round(efficiency, 6),
        "trajectory_faithfulness": round(faithfulness, 6),
    }
