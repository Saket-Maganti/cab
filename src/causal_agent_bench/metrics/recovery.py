from __future__ import annotations

from typing import Any

from causal_agent_bench.metrics.base import step_observation, tool_call_from_step
from causal_agent_bench.schemas import Trajectory

UNCERTAINTY_WORDS = ["uncertain", "unable", "cannot", "can't", "limitation", "error", "failed", "clarify"]


def score_recovery(trajectory: Trajectory) -> dict[str, bool | int | None]:
    failure_indices = []
    failed_tools = []
    for index, step in enumerate(trajectory.steps):
        obs = step_observation(step)
        if obs is None:
            continue
        if obs.get("error") or obs.get("is_corrupted") or _is_partial(obs):
            failure_indices.append(index)
            failed_tools.append(obs.get("tool_name"))
    if not failure_indices:
        return {
            "tool_error_recovery_binary": None,
            "recovery_action_attempted_binary": None,
            "correct_abstention_uncertainty_binary": None,
            "steps_to_recovery": None,
            "repeated_failed_call_count": 0,
        }

    first_failure = failure_indices[0]
    first_tool = failed_tools[0]
    recovery_index = None
    recovery_succeeded = False
    for index in range(first_failure + 1, len(trajectory.steps)):
        step = trajectory.steps[index]
        call = tool_call_from_step(step)
        if call is not None and call.get("tool_name") != first_tool:
            recovery_index = index
            observation = step_observation(step)
            recovery_succeeded = bool(
                observation
                and not observation.get("error")
                and not observation.get("is_corrupted")
                and not _is_partial(observation)
                and (
                    observation.get("output") is not None
                    or observation.get("ok") is True
                    or observation.get("status") in {"ok", "success", "succeeded"}
                )
            )
            break
    uncertainty_answer = any(
        word in str(trajectory.final_answer or "").lower() for word in UNCERTAINTY_WORDS
    )
    repeated = 0
    seen_failed = set()
    for step in trajectory.steps:
        call = tool_call_from_step(step)
        obs = step_observation(step)
        if call is None:
            continue
        tool = call.get("tool_name")
        if tool in seen_failed:
            repeated += 1
        if obs and (obs.get("error") or obs.get("is_corrupted")):
            seen_failed.add(tool)
    return {
        "tool_error_recovery_binary": recovery_succeeded,
        "recovery_action_attempted_binary": recovery_index is not None,
        "correct_abstention_uncertainty_binary": uncertainty_answer,
        "steps_to_recovery": None if recovery_index is None else recovery_index - first_failure,
        "repeated_failed_call_count": repeated,
    }


def _is_partial(obs: dict[str, Any]) -> bool:
    metadata = obs.get("metadata", {})
    output = obs.get("output")
    return metadata.get("intervention") == "partial_output" or (
        isinstance(output, dict) and output.get("partial") is True
    )
