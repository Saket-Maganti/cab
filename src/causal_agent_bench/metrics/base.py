from __future__ import annotations

from typing import Any

from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, BenchmarkTask, Trajectory


def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    return {}


def step_action(step: Any) -> dict[str, Any]:
    return as_dict(as_dict(step).get("action"))


def step_observation(step: Any) -> dict[str, Any] | None:
    obs = as_dict(step).get("observation")
    return as_dict(obs) if obs is not None else None


def tool_call_from_step(step: Any) -> dict[str, Any] | None:
    action = step_action(step)
    call = action.get("tool_call")
    return as_dict(call) if call is not None else None


def final_action_text(step: Any) -> str | None:
    action = step_action(step)
    answer = action.get("final_answer")
    return str(answer) if answer is not None else None


def thought_texts(trajectory: Trajectory) -> list[str]:
    texts = []
    for step in trajectory.steps:
        action = step_action(step)
        if action.get("thought"):
            texts.append(str(action["thought"]))
    if trajectory.final_answer:
        texts.append(trajectory.final_answer)
    return texts


def called_tools(trajectory: Trajectory) -> list[str]:
    calls = []
    for step in trajectory.steps:
        call = tool_call_from_step(step)
        if call is not None:
            calls.append(str(call["tool_name"]))
    return calls


def observations(trajectory: Trajectory) -> list[dict[str, Any]]:
    return [obs for step in trajectory.steps if (obs := step_observation(step)) is not None]


def obtained_text(trajectory: Trajectory) -> str:
    chunks = []
    for obs in observations(trajectory):
        chunks.append(str(obs.get("output", "")))
        chunks.append(str(obs.get("metadata", "")))
    chunks.extend(thought_texts(trajectory))
    return " ".join(chunks).lower()


def is_legacy_task(task: Any) -> bool:
    return isinstance(task, BenchmarkTask) or hasattr(task, "expected_behavior")


def base_task_from_context(context: Any) -> BaseTask | BenchmarkTask:
    if isinstance(context, BenchmarkInstance):
        return context.base_task
    return context


def condition_from_context(context: Any) -> str:
    if isinstance(context, BenchmarkInstance):
        return context.condition
    return "intervention" if getattr(context, "intervention", None) is not None else "clean"


def intervention_family_from_context(context: Any) -> str | None:
    intervention = getattr(context, "intervention", None)
    if isinstance(context, BenchmarkInstance):
        intervention = context.intervention
    if intervention is None:
        return None
    return getattr(intervention, "family", getattr(intervention, "type", None))


def required_tools(context: Any) -> list[str]:
    task = base_task_from_context(context)
    if is_legacy_task(task):
        expected = task.expected_behavior
        return list(expected.tool_sequence or expected.required_tools)
    return list(task.gold_tool_sequence or [])


def available_tools(context: Any) -> list[str]:
    if isinstance(context, BenchmarkInstance):
        return list(context.available_tools)
    task = base_task_from_context(context)
    return list(getattr(task, "available_tools", []))


def expected_answer_fragments(context: Any) -> list[str]:
    task = base_task_from_context(context)
    if is_legacy_task(task):
        expected = task.expected_behavior
        if expected.final_answer_contains:
            return [str(item) for item in expected.final_answer_contains]
        if expected.acceptable_final_answers:
            return [str(expected.acceptable_final_answers[0])]
        return []
    expected = task.goal.expected_final_answer
    if isinstance(expected, dict):
        return [str(value) for value in expected.values()]
    return [str(expected)] if expected is not None else []


def success_criteria(context: Any) -> list[str]:
    task = base_task_from_context(context)
    if is_legacy_task(task):
        return expected_answer_fragments(task)
    return list(task.goal.success_criteria)


def intervention_metadata(context: Any) -> dict[str, Any]:
    intervention = getattr(context, "intervention", None)
    if isinstance(context, BenchmarkInstance):
        intervention = context.intervention
    if intervention is None:
        return {}
    return getattr(intervention, "metadata", {}) or {}
