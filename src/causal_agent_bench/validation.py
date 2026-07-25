from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from causal_agent_bench.schemas import (
    BaseTask,
    BenchmarkInstance,
    InterventionSpec,
    ScoreRecord,
    ToolSpec,
    Trajectory,
    TrajectoryV2,
)

SCHEMA_TYPES: dict[str, type[BaseModel]] = {
    "tools": ToolSpec,
    "tool_specs": ToolSpec,
    "base_tasks": BaseTask,
    "base-task": BaseTask,
    "base_task": BaseTask,
    "interventions": InterventionSpec,
    "instances": BenchmarkInstance,
    "benchmark_instances": BenchmarkInstance,
    "trajectories": Trajectory,
    "trajectories_v2": TrajectoryV2,
    "trajectory_v2": TrajectoryV2,
    "scores": ScoreRecord,
}


def validate_task(task: BaseTask) -> list[str]:
    errors: list[str] = []
    if not task.task_id.strip():
        errors.append("task_id must be non-empty")
    if not task.domain.strip():
        errors.append("domain must be non-empty")
    if not task.goal.user_instruction.strip():
        errors.append("goal.user_instruction must be non-empty")
    if not task.goal.success_criteria:
        errors.append("goal.success_criteria must contain at least one criterion")
    if task.max_steps < 1:
        errors.append("max_steps must be at least 1")
    if len(set(task.available_tools)) != len(task.available_tools):
        errors.append("available_tools must not contain duplicates")
    if task.gold_tool_sequence:
        missing = [tool for tool in task.gold_tool_sequence if tool not in task.available_tools]
        if missing:
            errors.append(f"gold_tool_sequence references unavailable tools: {missing}")
        if len(task.gold_tool_sequence) > task.max_steps:
            errors.append("gold_tool_sequence must not be longer than max_steps")
    return errors


def validate_intervention(base_task: BaseTask, intervention: InterventionSpec) -> list[str]:
    errors: list[str] = []
    if intervention.base_task_id != base_task.task_id:
        errors.append(
            f"intervention.base_task_id {intervention.base_task_id!r} does not match "
            f"base task {base_task.task_id!r}"
        )
    if not intervention.changed_factor.strip():
        errors.append("changed_factor must be non-empty")
    patch_groups = [
        bool(intervention.tool_availability_patch),
        bool(intervention.memory_patch),
        bool(intervention.tool_output_patch),
        intervention.instruction_patch is not None,
    ]
    changed_count = sum(patch_groups)
    if changed_count == 0:
        errors.append("intervention must define at least one patch")
    if changed_count > 1:
        errors.append(
            "intervention changes multiple patch groups; controlled interventions should target one factor"
        )

    removed_tools = intervention.tool_availability_patch.get("removed_tools", [])
    missing_removed = [tool for tool in removed_tools if tool not in base_task.available_tools]
    if missing_removed:
        errors.append(f"tool_removal references tools not available in base task: {missing_removed}")

    if intervention.family == "tool_removal" and not removed_tools:
        errors.append("tool_removal intervention requires tool_availability_patch.removed_tools")
    if intervention.family == "irrelevant_tools" and not intervention.tool_availability_patch.get(
        "added_tools"
    ):
        errors.append("irrelevant_tools intervention requires tool_availability_patch.added_tools")
    if intervention.family in {"tool_failure", "tool_corruption"} and not intervention.tool_output_patch:
        errors.append(f"{intervention.family} intervention requires tool_output_patch")
    if intervention.family == "memory_corruption" and not intervention.memory_patch:
        errors.append("memory_corruption intervention requires memory_patch")
    if intervention.family == "ambiguous_instruction" and not intervention.instruction_patch:
        errors.append("ambiguous_instruction intervention requires instruction_patch")
    if intervention.family.startswith("web_") and not intervention.tool_output_patch:
        errors.append(f"{intervention.family} intervention requires tool_output_patch")
    return errors


def validate_instance(instance: BenchmarkInstance) -> list[str]:
    errors = validate_task(instance.base_task)
    if instance.condition == "clean":
        if instance.intervention is not None:
            errors.append("clean instance must not include an intervention")
        if set(instance.available_tools) != set(instance.base_task.available_tools):
            errors.append("clean instance available_tools should match base_task.available_tools")
    else:
        if instance.intervention is None:
            errors.append("intervention instance must include an intervention")
        else:
            errors.extend(validate_intervention(instance.base_task, instance.intervention))
            expected_tools = _patched_tools(instance.base_task.available_tools, instance.intervention)
            if set(instance.available_tools) != set(expected_tools):
                errors.append(
                    "intervention instance available_tools do not match tool availability patch"
                )
    if not isinstance(instance.initial_memory, dict):
        errors.append("initial_memory must be a dictionary")
    return errors


def validate_jsonl_file(path: Path, schema_type: str) -> dict[str, Any]:
    schema_key = schema_type.strip().lower()
    if schema_key not in SCHEMA_TYPES:
        allowed = ", ".join(sorted(SCHEMA_TYPES))
        raise ValueError(f"unknown schema type {schema_type!r}; expected one of: {allowed}")
    model: type[BaseModel] = SCHEMA_TYPES[schema_key]
    summary: dict[str, Any] = {
        "path": str(path),
        "schema": schema_key,
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "errors": [],
    }
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            summary["total"] += 1
            try:
                payload = json.loads(stripped)
                obj = model.model_validate(payload)
                custom_errors = _custom_errors(schema_key, obj)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                summary["invalid"] += 1
                summary["errors"].append({"line": line_no, "errors": [str(exc)]})
                continue
            if custom_errors:
                summary["invalid"] += 1
                summary["errors"].append({"line": line_no, "errors": custom_errors})
            else:
                summary["valid"] += 1
    return summary


def _custom_errors(schema_key: str, obj: Any) -> list[str]:
    if schema_key in {"base_tasks", "base-task", "base_task"}:
        return validate_task(obj)
    if schema_key in {"instances", "benchmark_instances"}:
        return validate_instance(obj)
    if schema_key in {"trajectories_v2", "trajectory_v2"}:
        return validate_trajectory_v2(obj)
    return []


def validate_trajectory_v2(trajectory: TrajectoryV2) -> list[str]:
    errors: list[str] = []
    if trajectory.agent_id != trajectory.agent_name and not trajectory.agent_id.strip():
        errors.append("agent_id must be non-empty")
    expected_indices = list(range(len(trajectory.steps)))
    actual_indices = [step.step_index for step in trajectory.steps]
    if actual_indices != expected_indices:
        errors.append(
            f"step_index values must be contiguous from zero; got {actual_indices}, "
            f"expected {expected_indices}"
        )
    for step in trajectory.steps:
        if step.parser_status == "valid_tool_call" and step.tool_call is None:
            errors.append(f"step {step.step_index}: valid_tool_call requires tool_call")
        if step.tool_call is not None and step.tool_arguments != step.tool_call.arguments:
            errors.append(f"step {step.step_index}: tool_arguments must match tool_call.arguments")
        if step.tool_error_status == "error" and (
            step.tool_result is None or step.tool_result.error is None
        ):
            errors.append(f"step {step.step_index}: tool_error_status=error requires tool_result.error")
    return errors


def _patched_tools(base_tools: list[str], intervention: InterventionSpec) -> list[str]:
    tools = list(base_tools)
    for removed in intervention.tool_availability_patch.get("removed_tools", []):
        tools = [tool for tool in tools if tool != removed]
    for added in intervention.tool_availability_patch.get("added_tools", []):
        if added not in tools:
            tools.append(added)
    return tools
