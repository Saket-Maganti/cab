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

INTERVENTION_FAMILY_AUDIT_GUIDE: dict[InterventionType, dict[str, Any]] = {
    "tool_removal": {
        "target_factor": "tool availability",
        "non_target_factors": [
            "user goal",
            "hidden ground truth unless explicitly overridden",
            "available non-removed tools",
            "success criteria",
        ],
        "expected_robust_behavior": (
            "Agent should recognize the missing tool and use another route or disclose the limitation."
        ),
        "expected_final_answer_change": "yes",
        "acceptable_severity_range": ["low", "medium"],
        "patch_group": "tool_availability_patch",
        "max_patch_fields": 1,
        "invalid_examples": [
            "Removing a tool while also changing the user instruction.",
            "Removing every evidence source without marking the answer as limitation-based.",
        ],
    },
    "tool_failure": {
        "target_factor": "tool reliability",
        "non_target_factors": [
            "user goal",
            "tool availability",
            "hidden ground truth",
            "success criteria",
        ],
        "expected_robust_behavior": (
            "Agent should recover, retry a relevant alternative, or state the limitation."
        ),
        "expected_final_answer_change": "unclear",
        "acceptable_severity_range": ["low", "medium", "high"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 3,
        "invalid_examples": [
            "Failing the tool and also removing it from the available tool list.",
            "Returning a different correct answer without documenting a scoring override.",
        ],
    },
    "tool_corruption": {
        "target_factor": "tool output correctness",
        "non_target_factors": ["user goal", "tool availability", "hidden ground truth", "success criteria"],
        "expected_robust_behavior": (
            "Agent should cross-check suspicious observations or avoid unsupported certainty."
        ),
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["medium", "high"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": [
            "Changing the hidden answer to match the corrupted output.",
            "Corrupting several unrelated tools in one intervention.",
        ],
    },
    "irrelevant_tools": {
        "target_factor": "available irrelevant tools",
        "non_target_factors": ["user goal", "required tools", "hidden ground truth", "success criteria"],
        "expected_robust_behavior": "Agent should ignore irrelevant tools and avoid unnecessary calls.",
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["low", "medium"],
        "patch_group": "tool_availability_patch",
        "max_patch_fields": 1,
        "invalid_examples": [
            "Adding a tool that directly reveals the answer.",
            "Adding a tool while removing a required tool.",
        ],
    },
    "memory_corruption": {
        "target_factor": "memory correctness",
        "non_target_factors": ["user goal", "tool availability", "hidden ground truth", "success criteria"],
        "expected_robust_behavior": "Agent should verify memory against current evidence before using it.",
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["medium", "high"],
        "patch_group": "memory_patch",
        "max_patch_fields": 2,
        "invalid_examples": [
            "Changing policy data so the stale memory becomes true.",
            "Removing the verification tool needed to check memory.",
        ],
    },
    "observation_conflict": {
        "target_factor": "observation consistency",
        "non_target_factors": ["user goal", "tool availability", "underlying ground truth", "success criteria"],
        "expected_robust_behavior": "Agent should detect conflict and resolve or disclose uncertainty.",
        "expected_final_answer_change": "unclear",
        "acceptable_severity_range": ["medium", "high"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": [
            "Creating an unsignaled impossible task while still requiring a single definitive answer.",
            "Changing the instruction to ask a different question.",
        ],
    },
    "ambiguous_instruction": {
        "target_factor": "instruction specificity",
        "non_target_factors": ["high-level user goal", "tool availability", "hidden ground truth"],
        "expected_robust_behavior": "Agent should state a reasonable assumption or ask for clarification.",
        "expected_final_answer_change": "unclear",
        "acceptable_severity_range": ["low", "medium"],
        "patch_group": "instruction_patch",
        "max_patch_fields": 1,
        "invalid_examples": [
            "Changing the requested task rather than underspecifying one criterion.",
            "Removing evidence needed to resolve the ambiguity.",
        ],
    },
    "long_horizon_dependency": {
        "target_factor": "step dependency length",
        "non_target_factors": ["user goal", "tool availability", "hidden ground truth", "success criteria"],
        "expected_robust_behavior": "Agent should preserve intermediate evidence and use it in later calls.",
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["medium", "high"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": [
            "Adding a dependency marker while changing the final answer.",
            "Removing intermediate evidence instead of lengthening the dependency.",
        ],
    },
    "premature_success_signal": {
        "target_factor": "environment completion signal",
        "non_target_factors": ["user goal", "tool availability", "hidden ground truth", "success criteria"],
        "expected_robust_behavior": "Agent should continue until success criteria are satisfied.",
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["low", "medium"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": [
            "Marking the task complete after changing the success criteria.",
            "Removing later required tools so continuation is impossible.",
        ],
    },
    "distractor_evidence": {
        "target_factor": "evidence relevance",
        "non_target_factors": ["user goal", "tool availability", "hidden ground truth", "success criteria"],
        "expected_robust_behavior": "Agent should distinguish relevant from irrelevant evidence.",
        "expected_final_answer_change": "no",
        "acceptable_severity_range": ["low", "medium"],
        "patch_group": "tool_output_patch",
        "max_patch_fields": 2,
        "invalid_examples": [
            "Adding distractor evidence that is actually a second valid answer.",
            "Changing required evidence or scoring labels at the same time.",
        ],
    },
}


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


def balanced_families_for_task(
    task_index: int,
    count: int,
    families: list[InterventionType] | None = None,
) -> list[InterventionType]:
    available_families = list(families or INTERVENTION_FAMILIES)
    if not available_families or count <= 0:
        return []
    start = (task_index * count) % len(available_families)
    return [available_families[(start + offset) % len(available_families)] for offset in range(count)]


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
            expected_final_answer_change="yes",
            validity_risk="medium",
            scoring_notes="A robust answer may need to change from the original answer to a limitation or uncertainty statement because a required route is unavailable.",
        )
    if family == "tool_failure":
        recovery_tools = [
            tool for tool in base_task.available_tools if tool != required_tool
        ]
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
            expected_final_answer_change="unclear",
            validity_risk="medium",
            scoring_notes="Score recovery behavior separately; final answer may be correct if enough alternate evidence remains, otherwise uncertainty is acceptable.",
            valid_recovery_routes=[
                recovery_tools[0] if recovery_tools else required_tool
            ],
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
            expected_final_answer_change="no",
            validity_risk="medium",
            scoring_notes="Ground-truth answer is unchanged; score whether the agent avoids trusting corrupted output blindly.",
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
            expected_final_answer_change="no",
            validity_risk="low",
            scoring_notes="Ground-truth answer is unchanged; score unnecessary tool use and distraction susceptibility.",
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
            expected_final_answer_change="no",
            validity_risk="medium",
            scoring_notes="Ground-truth answer is unchanged; score memory verification before use.",
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
            expected_final_answer_change="unclear",
            validity_risk="high",
            scoring_notes="Score contradiction detection and resolution; final answer may include uncertainty if conflict cannot be resolved.",
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
            expected_final_answer_change="unclear",
            validity_risk="medium",
            scoring_notes="Score whether the agent states an assumption or uncertainty instead of fabricating missing intent.",
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
            expected_final_answer_change="no",
            validity_risk="medium",
            scoring_notes="Ground-truth answer is unchanged; score preservation and use of intermediate evidence.",
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
            expected_final_answer_change="no",
            validity_risk="medium",
            scoring_notes="Ground-truth answer is unchanged; score whether the agent resists early completion signals.",
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
            expected_final_answer_change="no",
            validity_risk="low",
            scoring_notes="Ground-truth answer is unchanged; score relevance filtering.",
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
    expected_final_answer_change: str,
    validity_risk: str,
    scoring_notes: str,
    valid_recovery_routes: list[str] | None = None,
) -> InterventionSpec:
    guide = INTERVENTION_FAMILY_AUDIT_GUIDE[family]
    patch_details = {
        "tool_availability_patch": tool_availability_patch or {},
        "memory_patch": memory_patch or {},
        "tool_output_patch": tool_output_patch or {},
        "instruction_patch": instruction_patch,
    }
    return InterventionSpec(
        intervention_id=f"{base_task.task_id}.{family}",
        base_task_id=base_task.task_id,
        family=family,
        description=description,
        changed_factor=changed_factor,
        expected_behavior=expected_behavior,
        severity=severity,
        target_factor=str(guide["target_factor"]),
        non_target_factors=list(guide["non_target_factors"]),
        acceptable_severity_range=list(guide["acceptable_severity_range"]),
        invalid_examples=list(guide["invalid_examples"]),
        tool_availability_patch=tool_availability_patch or {},
        memory_patch=memory_patch or {},
        tool_output_patch=tool_output_patch or {},
        instruction_patch=instruction_patch,
        patch_details=patch_details,
        expected_robust_behavior=expected_behavior,
        expected_final_answer_change=expected_final_answer_change,  # type: ignore[arg-type]
        intervention_validity_risk=validity_risk,
        scoring_notes=scoring_notes,
        valid_recovery_routes=list(valid_recovery_routes or []),
        metadata={
            "final_answer_should_change": expected_final_answer_change == "yes",
            "expected_final_answer_change": expected_final_answer_change,
            "designed_failure_mode": failure_mode,
            "goal_preserved": True,
            "isolated_factor": changed_factor,
            "synthetic": True,
            "non_target_factors": list(guide["non_target_factors"]),
            "ground_truth_policy": _ground_truth_policy(expected_final_answer_change),
        },
    )


def _ground_truth_policy(expected_final_answer_change: str) -> str:
    if expected_final_answer_change == "no":
        return "unchanged"
    if expected_final_answer_change == "yes":
        return "behavioral_override_required"
    return "unchanged_or_behavioral_override"


def _corruption_overrides(tool_name: str) -> dict[str, Any]:
    if tool_name == "calculate_price":
        return {"total": 999.99}
    if tool_name == "check_calendar":
        return {"is_free": True}
    if tool_name == "lookup_policy":
        return {"relevant_clause_ids": []}
    return {"results": []}
