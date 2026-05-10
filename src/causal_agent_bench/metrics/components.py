from __future__ import annotations

from collections.abc import Iterable

from causal_agent_bench.schemas import BenchmarkTask, Trajectory


def _as_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    return {}


def _action(step) -> dict:
    return _as_dict(_as_dict(step).get("action"))


def _observation(step) -> dict | None:
    obs = _as_dict(step).get("observation")
    return _as_dict(obs) if obs is not None else None


def _step_index(step) -> int:
    return int(_as_dict(step).get("index", 0))


def tool_calls(trajectory: Trajectory) -> list[str]:
    calls: list[str] = []
    for step in trajectory.steps:
        action = _action(step)
        tool_call = action.get("tool_call")
        if tool_call is not None:
            calls.append(_as_dict(tool_call)["tool_name"])
    return calls


def final_answer_correctness(task: BenchmarkTask, answer: str) -> float:
    normalized = answer.lower()
    expected = task.expected_behavior
    if expected.final_answer_contains:
        return float(all(fragment.lower() in normalized for fragment in expected.final_answer_contains))
    if expected.acceptable_final_answers:
        return float(any(candidate.lower() == normalized for candidate in expected.acceptable_final_answers))
    return 0.0


def _contains_any(texts: Iterable[str], needles: Iterable[str]) -> bool:
    joined = " ".join(texts).lower()
    return any(needle in joined for needle in needles)


def compute_trajectory_metrics(task: BenchmarkTask, trajectory: Trajectory) -> dict[str, float | int | None]:
    calls = tool_calls(trajectory)
    required = list(task.expected_behavior.required_tools)
    required_set = set(required)
    call_set = set(calls)
    total_calls = len(calls)
    required_call_count = sum(1 for call in calls if call in required_set)
    non_required_call_count = total_calls - required_call_count
    failed_observations = [
        _observation(step)
        for step in trajectory.steps
        if _observation(step) is not None and _observation(step).get("error") is not None
    ]
    invalid_observations = [
        obs for obs in failed_observations if obs is not None and obs.get("error") == "invalid_arguments"
    ]

    recall = len(call_set & required_set) / len(required_set) if required_set else 1.0
    precision = required_call_count / total_calls if total_calls else 1.0 if not required_set else 0.0
    selection_accuracy = (
        len(call_set & required_set) / len(call_set | required_set)
        if (call_set or required_set)
        else 1.0
    )
    argument_validity = (
        (total_calls - len(invalid_observations)) / total_calls if total_calls else 1.0
    )
    final_correct = final_answer_correctness(task, trajectory.final_answer or "")

    final_index = None
    for step in trajectory.steps:
        action = _action(step)
        if action.get("final_answer") is not None or action.get("stop") is True:
            final_index = _step_index(step)
            break
    premature_stop = 0.0
    if final_index is not None:
        calls_before_final = [
            tool_call["tool_name"]
            for step in trajectory.steps[:final_index]
            if _action(step).get("tool_call") is not None
            for tool_call in [_as_dict(_action(step).get("tool_call"))]
        ]
        if not required_set.issubset(set(calls_before_final)):
            premature_stop = 1.0

    rationale_and_answer = [
        str(_action(step).get("thought") or "")
        for step in trajectory.steps
    ] + [trajectory.final_answer or ""]
    contradiction_detection = None
    if task.expected_behavior.must_detect_contradiction:
        contradiction_detection = float(
            _contains_any(
                rationale_and_answer,
                ["conflict", "contradiction", "contradict", "disagree", "inconsistent"],
            )
        )
    memory_verification = None
    if task.expected_behavior.must_verify_memory:
        memory_verification = float("verify_fact" in calls)

    recovery_rate = None
    if failed_observations:
        recovery_rate = float(bool(final_correct))

    unnecessary_tool_rate = non_required_call_count / total_calls if total_calls else 0.0
    trajectory_faithfulness = float(
        bool(final_correct)
        and (not task.expected_behavior.must_verify_memory or memory_verification == 1.0)
        and (not task.expected_behavior.must_detect_contradiction or contradiction_detection == 1.0)
    )

    return {
        "tool_selection_accuracy": round(selection_accuracy, 6),
        "tool_call_precision": round(precision, 6),
        "tool_call_recall": round(recall, 6),
        "argument_validity": round(argument_validity, 6),
        "recovery_rate": recovery_rate,
        "contradiction_detection_rate": contradiction_detection,
        "memory_verification_rate": memory_verification,
        "premature_stop_rate": premature_stop,
        "unnecessary_tool_call_rate": round(unnecessary_tool_rate, 6),
        "trajectory_faithfulness": trajectory_faithfulness,
        "final_answer_correctness": final_correct,
    }
