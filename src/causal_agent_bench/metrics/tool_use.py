from __future__ import annotations

from typing import Any

from causal_agent_bench.metrics.base import (
    available_tools,
    called_tools,
    observations,
    required_tools,
)
from causal_agent_bench.schemas import Trajectory


def score_tool_use(context: Any, trajectory: Trajectory) -> dict[str, float | int]:
    required = required_tools(context)
    required_set = set(required)
    available = set(available_tools(context))
    calls = called_tools(trajectory)
    call_set = set(calls)
    total_calls = len(calls)
    useful_calls = sum(1 for call in calls if call in required_set)
    unnecessary_calls = total_calls - useful_calls
    invalid_tool_calls = sum(1 for call in calls if call not in available)
    invalid_tool_calls += sum(
        1
        for obs in observations(trajectory)
        if obs.get("error") in {"unknown_tool", "tool_unavailable"}
    )
    missing_required = len(required_set - call_set)
    required_recall = len(required_set & call_set) / len(required_set) if required_set else 1.0
    precision = useful_calls / total_calls if total_calls else (1.0 if not required_set else 0.0)
    unnecessary_rate = unnecessary_calls / total_calls if total_calls else 0.0
    return {
        "required_tool_recall": round(required_recall, 6),
        "tool_precision": round(precision, 6),
        "unnecessary_tool_call_rate": round(unnecessary_rate, 6),
        "missing_required_tool_count": missing_required,
        "invalid_tool_call_count": invalid_tool_calls,
        "argument_validity_rate": score_argument_validity(trajectory)["argument_validity_rate"],
        "argument_error_count": score_argument_validity(trajectory)["argument_error_count"],
    }


def score_argument_validity(trajectory: Trajectory) -> dict[str, float | int]:
    calls = called_tools(trajectory)
    arg_errors = sum(1 for obs in observations(trajectory) if obs.get("error") == "invalid_arguments")
    validity = (len(calls) - arg_errors) / len(calls) if calls else 1.0
    return {
        "argument_validity_rate": round(validity, 6),
        "argument_error_count": arg_errors,
    }
