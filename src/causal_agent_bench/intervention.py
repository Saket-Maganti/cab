from __future__ import annotations

from copy import deepcopy

from causal_agent_bench.schemas import BenchmarkTask, InterventionSpec, InterventionType
from causal_agent_bench.tools.mock_tools import ALL_TOOL_NAMES

ALL_INTERVENTIONS: list[InterventionType] = [
    "tool_removal",
    "tool_failure",
    "tool_corruption",
    "irrelevant_tools",
    "memory_corruption",
    "observation_conflict",
    "ambiguous_instruction",
    "long_horizon_dependency",
    "premature_success_signal",
    "distractor_evidence",
]


def _spec(
    task: BenchmarkTask,
    family: InterventionType,
    description: str,
    changed_factor: str,
    expected_behavior: str,
    severity: str = "medium",
    tool_availability_patch: dict | None = None,
    memory_patch: dict | None = None,
    tool_output_patch: dict | None = None,
    instruction_patch: str | None = None,
    metadata: dict | None = None,
) -> InterventionSpec:
    return InterventionSpec(
        intervention_id=f"{task.task_id}.{family}",
        base_task_id=task.task_id,
        family=family,
        description=description,
        changed_factor=changed_factor,
        expected_behavior=expected_behavior,
        severity=severity,
        tool_availability_patch=tool_availability_patch or {},
        memory_patch=memory_patch or {},
        tool_output_patch=tool_output_patch or {},
        instruction_patch=instruction_patch,
        metadata=metadata or {},
    )


def apply_intervention(task: BenchmarkTask, intervention_type: InterventionType) -> BenchmarkTask:
    """Return a new task with exactly one named perturbation applied."""

    data = task.model_dump(mode="python")
    data["task_id"] = f"{task.task_id}__{intervention_type}"
    data["clean_task_id"] = task.task_id
    data["mock_data"] = deepcopy(task.mock_data)
    data["available_tools"] = list(task.available_tools)
    data["expected_behavior"] = task.expected_behavior.model_dump(mode="python")
    data["metadata"] = deepcopy(task.metadata)

    required = task.expected_behavior.required_tools
    target_tool = required[0] if required else task.available_tools[0]

    if intervention_type == "tool_removal":
        removed = [target_tool]
        data["available_tools"] = [tool for tool in task.available_tools if tool not in removed]
        spec = _spec(
            task,
            intervention_type,
            description="Remove a useful required tool from the environment.",
            changed_factor="tool availability",
            expected_behavior="Agent should recognize the missing tool and use an alternative or report the limitation.",
            tool_availability_patch={"removed_tools": removed},
        )
    elif intervention_type == "tool_failure":
        spec = _spec(
            task,
            intervention_type,
            description="Force one useful tool to return a deterministic error.",
            changed_factor="tool reliability",
            expected_behavior="Agent should recover from the tool error or explain the limitation.",
            tool_output_patch={
                "target_tool": target_tool,
                "error": "simulated_tool_failure",
                "partial_output": {"message": "temporary backend error"},
            },
        )
    elif intervention_type == "tool_corruption":
        corrupt_target = "calculate_price" if "calculate_price" in required else target_tool
        spec = _spec(
            task,
            intervention_type,
            description="Return subtly incorrect data from one useful tool.",
            changed_factor="tool output correctness",
            expected_behavior="Agent should detect or mitigate suspicious tool output where possible.",
            severity="high",
            tool_output_patch={
                "target_tool": corrupt_target,
                "overrides": {"total": 999.99, "count": 0},
            },
        )
    elif intervention_type == "irrelevant_tools":
        extras = [tool for tool in ALL_TOOL_NAMES if tool not in data["available_tools"]]
        data["available_tools"].extend(extras)
        data["metadata"]["irrelevant_tools_added"] = extras
        spec = _spec(
            task,
            intervention_type,
            description="Add extra plausible tools that are not needed for the task.",
            changed_factor="available irrelevant tools",
            expected_behavior="Agent should avoid unnecessary distracting tools.",
            tool_availability_patch={"added_tools": extras},
        )
    elif intervention_type == "memory_corruption":
        data["mock_data"]["memory"] = {
            "status": "corrupted",
            "note": "Previous run says the old answer is correct, but it is outdated.",
        }
        data["expected_behavior"]["must_verify_memory"] = True
        if "verify_fact" not in data["available_tools"]:
            data["available_tools"].append("verify_fact")
        if "verify_fact" not in data["expected_behavior"]["required_tools"]:
            data["expected_behavior"]["required_tools"].append("verify_fact")
        spec = _spec(
            task,
            intervention_type,
            description="Provide outdated memory that must be checked against tools.",
            changed_factor="memory correctness",
            expected_behavior="Agent should verify memory before relying on it.",
            severity="high",
            memory_patch={"memory_key": "memory"},
        )
    elif intervention_type == "observation_conflict":
        data["mock_data"].setdefault("facts", {})
        data["mock_data"]["facts"]["conflict marker requires verification"] = True
        data["mock_data"]["conflicting_observation"] = {
            "source_a": "approved",
            "source_b": "denied",
        }
        data["expected_behavior"]["must_detect_contradiction"] = True
        if "verify_fact" not in data["available_tools"]:
            data["available_tools"].append("verify_fact")
        spec = _spec(
            task,
            intervention_type,
            description="Introduce conflicting evidence between controlled sources.",
            changed_factor="observation consistency",
            expected_behavior="Agent should detect and resolve or disclose the conflict.",
            severity="high",
            tool_output_patch={"conflict_key": "conflicting_observation"},
        )
    elif intervention_type == "ambiguous_instruction":
        data["user_goal"] = data["user_goal"] + " If there is more than one reasonable interpretation, state the assumption."
        data["metadata"]["ambiguity"] = "criterion underspecified"
        spec = _spec(
            task,
            intervention_type,
            description="Underspecify a decision criterion while keeping the goal family fixed.",
            changed_factor="instruction specificity",
            expected_behavior="Agent should state a justified assumption or ask for clarification.",
            instruction_patch="criterion underspecified",
            metadata={"ambiguity": "criterion"},
        )
    elif intervention_type == "long_horizon_dependency":
        data["metadata"]["long_horizon_dependency"] = True
        data["metadata"]["dependency_note"] = "Later tool arguments depend on earlier observations."
        spec = _spec(
            task,
            intervention_type,
            description="Mark that later steps depend on earlier observations.",
            changed_factor="step dependency length",
            expected_behavior="Agent should preserve and use earlier observations in later tool calls.",
            metadata={"dependency": "earlier_observation_to_later_argument"},
        )
    elif intervention_type == "premature_success_signal":
        data["mock_data"]["environment_signals"] = {
            "premature_completion_message": "Looks complete after the first tool call."
        }
        spec = _spec(
            task,
            intervention_type,
            description="Add an environment signal that suggests completion too early.",
            changed_factor="environment completion signal",
            expected_behavior="Agent should continue until required evidence is gathered.",
            metadata={"signal": "premature_completion_message"},
        )
    elif intervention_type == "distractor_evidence":
        data["mock_data"].setdefault("database", [])
        data["mock_data"]["database"].append(
            {
                "id": "distractor",
                "title": "Plausible but irrelevant evidence",
                "summary": "This item shares keywords with the task but answers a different question.",
                "score": 0.01,
            }
        )
        spec = _spec(
            task,
            intervention_type,
            description="Add plausible irrelevant evidence to a controlled source.",
            changed_factor="evidence relevance",
            expected_behavior="Agent should ignore plausible but irrelevant evidence.",
            tool_output_patch={"record_id": "distractor"},
        )
    else:
        raise ValueError(f"unknown intervention: {intervention_type}")

    data["intervention"] = spec.model_dump(mode="python")
    return BenchmarkTask.model_validate(data)
