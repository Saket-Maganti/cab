from __future__ import annotations

import random
from typing import Any

from causal_agent_bench.schemas import BaseTask, InterventionSpec, InterventionType

INTERVENTION_FAMILIES: list[InterventionType] = [
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

IRRELEVANT_TOOLS = ["book_stub", "read_file", "query_spreadsheet", "verify_fact", "search_database"]


def generate_interventions_for_task(
    base_task: BaseTask,
    seed: int,
    count: int,
    families: list[InterventionType] | None = None,
) -> list[InterventionSpec]:
    rng = random.Random(f"{seed}:{base_task.task_id}")
    available_families = list(families or INTERVENTION_FAMILIES)
    rng.shuffle(available_families)
    interventions = []
    for family in available_families[:count]:
        interventions.append(make_intervention(base_task, family))
    return interventions


def make_intervention(base_task: BaseTask, family: InterventionType) -> InterventionSpec:
    required_tool = (base_task.gold_tool_sequence or base_task.available_tools)[0]
    if family == "tool_removal":
        patch = {"removed_tools": [required_tool]}
        return _spec(
            base_task,
            family,
            "Remove one useful tool from the available tool set.",
            "tool availability",
            "Agent should recognize the missing tool and use another route or disclose the limitation.",
            "medium",
            tool_availability_patch=patch,
            failure_mode="under-tooling or brittle tool dependence",
            final_answer_should_change=False,
        )
    if family == "tool_failure":
        patch = {
            "target_tool": required_tool,
            "error": "simulated_tool_failure",
            "partial_output": {"message": "deterministic simulated failure"},
        }
        return _spec(
            base_task,
            family,
            "Force a useful tool to return a deterministic error.",
            "tool reliability",
            "Agent should recover, retry a relevant alternative, or state the limitation.",
            "medium",
            tool_output_patch=patch,
            failure_mode="failure recovery",
            final_answer_should_change=False,
        )
    if family == "tool_corruption":
        target = "calculate_price" if "calculate_price" in base_task.available_tools else required_tool
        patch = {"target_tool": target, "overrides": _corruption_overrides(target)}
        return _spec(
            base_task,
            family,
            "Return subtly incorrect output from a useful tool.",
            "tool output correctness",
            "Agent should cross-check suspicious observations or avoid unsupported certainty.",
            "high",
            tool_output_patch=patch,
            failure_mode="observation interpretation",
            final_answer_should_change=False,
        )
    if family == "irrelevant_tools":
        additions = [tool for tool in IRRELEVANT_TOOLS if tool not in base_task.available_tools][:2]
        return _spec(
            base_task,
            family,
            "Add plausible but unnecessary tools.",
            "available irrelevant tools",
            "Agent should ignore irrelevant tools and avoid unnecessary calls.",
            "low",
            tool_availability_patch={"added_tools": additions},
            failure_mode="over-tooling",
            final_answer_should_change=False,
        )
    if family == "memory_corruption":
        return _spec(
            base_task,
            family,
            "Inject stale or incorrect initial memory.",
            "memory correctness",
            "Agent should verify memory against current evidence before using it.",
            "high",
            memory_patch={"stale_memory": "Previous run said the old answer was correct.", "is_corrupted": True},
            failure_mode="unverified memory reliance",
            final_answer_should_change=False,
        )
    if family == "observation_conflict":
        return _spec(
            base_task,
            family,
            "Insert a conflicting observation into a controlled tool response.",
            "observation consistency",
            "Agent should detect conflict and resolve or disclose uncertainty.",
            "high",
            tool_output_patch={
                "target_tool": required_tool,
                "conflicting_observation": {"source_a": "approved", "source_b": "denied"},
            },
            failure_mode="contradiction handling",
            final_answer_should_change=False,
        )
    if family == "ambiguous_instruction":
        return _spec(
            base_task,
            family,
            "Underspecify one decision criterion in the instruction.",
            "instruction specificity",
            "Agent should state a reasonable assumption or ask for clarification.",
            "medium",
            instruction_patch="One selection criterion is intentionally underspecified; state your assumption.",
            failure_mode="ambiguity handling",
            final_answer_should_change=False,
        )
    if family == "long_horizon_dependency":
        return _spec(
            base_task,
            family,
            "Require later tool calls to depend on earlier observations.",
            "step dependency length",
            "Agent should preserve intermediate evidence and use it in later calls.",
            "medium",
            tool_output_patch={"target_tool": required_tool, "dependency_marker": "later arguments depend on this observation"},
            failure_mode="planning and memory over long horizons",
            final_answer_should_change=False,
        )
    if family == "premature_success_signal":
        return _spec(
            base_task,
            family,
            "Insert a misleading environment signal suggesting completion too early.",
            "environment completion signal",
            "Agent should continue until success criteria are satisfied.",
            "medium",
            tool_output_patch={
                "target_tool": required_tool,
                "premature_completion_message": "Looks complete after this observation.",
            },
            failure_mode="premature stopping",
            final_answer_should_change=False,
        )
    if family == "distractor_evidence":
        return _spec(
            base_task,
            family,
            "Add plausible but irrelevant evidence to the observation stream.",
            "evidence relevance",
            "Agent should distinguish relevant from irrelevant evidence.",
            "medium",
            tool_output_patch={
                "target_tool": required_tool,
                "distractor_record": {
                    "id": "distractor",
                    "text": "Shares keywords with the task but answers a different question.",
                },
            },
            failure_mode="distractor susceptibility",
            final_answer_should_change=False,
        )
    raise ValueError(f"unknown intervention family {family}")


def _spec(
    base_task: BaseTask,
    family: InterventionType,
    description: str,
    changed_factor: str,
    expected_behavior: str,
    severity: str,
    *,
    tool_availability_patch: dict[str, Any] | None = None,
    memory_patch: dict[str, Any] | None = None,
    tool_output_patch: dict[str, Any] | None = None,
    instruction_patch: str | None = None,
    failure_mode: str,
    final_answer_should_change: bool,
) -> InterventionSpec:
    return InterventionSpec(
        intervention_id=f"{base_task.task_id}.{family}",
        base_task_id=base_task.task_id,
        family=family,
        description=description,
        changed_factor=changed_factor,
        expected_behavior=expected_behavior,
        severity=severity,
        tool_availability_patch=tool_availability_patch or {},
        memory_patch=memory_patch or {},
        tool_output_patch=tool_output_patch or {},
        instruction_patch=instruction_patch,
        metadata={
            "final_answer_should_change": final_answer_should_change,
            "designed_failure_mode": failure_mode,
            "synthetic": True,
        },
    )


def _corruption_overrides(tool_name: str) -> dict[str, Any]:
    if tool_name == "calculate_price":
        return {"total": 999.99}
    if tool_name == "check_calendar":
        return {"is_free": True}
    if tool_name == "lookup_policy":
        return {"relevant_clause_ids": []}
    return {"results": []}
