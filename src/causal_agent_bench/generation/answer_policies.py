"""Deterministic, explicit answer policies for generated CAB studies."""

from __future__ import annotations

from typing import Any

from causal_agent_bench.answer_contracts import (
    AbstentionOpportunity,
    AnswerContract,
    AnswerValueType,
    BehaviorRequirement,
    FallbackMode,
    GoldAnswerPolicy,
    PermittedResponseType,
    ScorerPolicy,
)
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.schemas import BaseTask, InterventionSpec

POLICY_VERSION = "cab_answer_policy_v3"

_CLARIFICATION_FAMILIES = frozenset({"ambiguous_instruction"})
_RECOVERY_FAMILIES = frozenset({"tool_failure", "web_broken_link"})
_UNCERTAINTY_FAMILIES = frozenset(
    {"tool_removal", "observation_conflict", "web_conflicting_page"}
)


def attach_base_task_policies(
    task: BaseTask,
    *,
    benchmark_version: str,
    split_role: str,
) -> BaseTask:
    """Attach preregistered typed policies and canonical contract metadata."""

    expected = task.goal.expected_final_answer
    contract = AnswerContract.ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED
    gold = GoldAnswerPolicy(
        policy_id=f"{task.task_id}.gold.v3",
        answer_contract=contract,
        expected=expected,
        metadata={"policy_version": POLICY_VERSION},
    )
    scorer = ScorerPolicy(
        policy_id=f"{task.task_id}.scorer.v3",
        answer_type=infer_answer_type(expected),
        fallback_mode=FallbackMode.DISABLED,
        required_tools=list(task.required_tools or task.gold_tool_sequence or []),
        metadata={"policy_version": POLICY_VERSION},
    )
    metadata = {
        **task.metadata,
        "schema_version": "cab_base_task_contract_v3",
        "task_version": benchmark_version,
        "source": task.metadata.get(
            "source",
            "repository-authored deterministic synthetic generator",
        ),
        "license": task.metadata.get("license", "DATA_LICENSE.md"),
        "provenance": task.metadata.get(
            "provenance",
            "repository-authored deterministic synthetic generator",
        ),
        "template_id": _template_id(task),
        "split_role": split_role,
        "visible_context_fields": [
            "user_instruction",
            "instruction_patch",
            "success_criteria",
            "required_information",
            "forbidden_assumptions",
            "initial_memory",
            "max_steps",
        ],
        "hidden_evaluator_context_fields": [
            "hidden_ground_truth",
            "gold_answer_policy",
            "scorer_policy",
        ],
        "human_validation_state": task.metadata.get(
            "human_validation_state",
            "HUMAN_INPUT_REQUIRED",
        ),
    }
    updated = task.model_copy(
        update={
            "answer_contract": contract,
            "gold_answer_policy": gold,
            "scorer_policy": scorer,
            "expected_output_schema": (
                task.expected_output_schema or infer_output_schema(expected)
            ),
            "ambiguity_policy": (
                task.ambiguity_policy
                or {
                    "mode": "clarify_or_state_assumption_when_material",
                    "policy_version": POLICY_VERSION,
                }
            ),
            "abstention_policy": (
                task.abstention_policy
                or {
                    "mode": "allowed_only_when_required_evidence_is_unavailable",
                    "must_state_limitation": True,
                    "policy_version": POLICY_VERSION,
                }
            ),
            "metadata": metadata,
        }
    )
    return updated.model_copy(
        update={
            "metadata": {
                **updated.metadata,
                "content_hash": content_hash(updated),
            }
        }
    )


def attach_intervention_policies(
    base_task: BaseTask,
    intervention: InterventionSpec,
    *,
    benchmark_version: str,
) -> InterventionSpec:
    """Attach an intervention-specific answer contract and scorer policy."""

    contract = intervention_answer_contract(intervention)
    expected = base_task.goal.expected_final_answer
    gold = GoldAnswerPolicy(
        policy_id=f"{intervention.intervention_id}.gold.v3",
        answer_contract=contract,
        expected=expected,
        metadata={
            "policy_version": POLICY_VERSION,
            "expected_final_answer_change": intervention.expected_final_answer_change,
        },
    )
    removed_tools = [
        str(value)
        for value in intervention.tool_availability_patch.get("removed_tools", [])
    ]
    required_tools = list(
        (base_task.scorer_policy.required_tools if base_task.scorer_policy else None)
        or base_task.required_tools
        or base_task.gold_tool_sequence
        or []
    )
    if contract == AnswerContract.CLARIFICATION_REQUIRED:
        required_tools = []
    elif removed_tools:
        required_tools = [
            tool for tool in required_tools if tool not in set(removed_tools)
        ]

    opportunity = _abstention_opportunity(
        base_task,
        intervention,
        contract,
        removed_tools=removed_tools,
    )
    scorer = ScorerPolicy(
        policy_id=f"{intervention.intervention_id}.scorer.v3",
        answer_type=infer_answer_type(expected),
        fallback_mode=FallbackMode.DISABLED,
        abstention=(
            BehaviorRequirement.ACCEPTED
            if contract
            in {
                AnswerContract.QUALIFIED_UNCERTAINTY_ACCEPTED,
                AnswerContract.RECOVERY_ROUTE_REQUIRED,
            }
            else BehaviorRequirement.FORBIDDEN
        ),
        clarification=(
            BehaviorRequirement.REQUIRED
            if contract == AnswerContract.CLARIFICATION_REQUIRED
            else BehaviorRequirement.FORBIDDEN
        ),
        required_tools=required_tools,
        required_recovery_actions=(
            list(intervention.valid_recovery_routes)
            if contract == AnswerContract.RECOVERY_ROUTE_REQUIRED
            else []
        ),
        unavailable_tool_disclosure=(
            BehaviorRequirement.ACCEPTED
            if removed_tools or contract == AnswerContract.RECOVERY_ROUTE_REQUIRED
            else BehaviorRequirement.FORBIDDEN
        ),
        unavailable_tools=(
            removed_tools
            or (
                [str(intervention.tool_output_patch.get("target_tool"))]
                if contract == AnswerContract.RECOVERY_ROUTE_REQUIRED
                and intervention.tool_output_patch.get("target_tool")
                else []
            )
        ),
        abstention_opportunity=opportunity,
        metadata={"policy_version": POLICY_VERSION},
    )
    acceptable_abstention_conditions = list(
        intervention.acceptable_abstention_conditions
    )
    if (
        contract == AnswerContract.QUALIFIED_UNCERTAINTY_ACCEPTED
        and not acceptable_abstention_conditions
    ):
        acceptable_abstention_conditions = [
            "Required evidence remains unavailable or contradictory after permitted checks."
        ]
    changed_fields = [
        field
        for field, value in (
            ("tool_availability", intervention.tool_availability_patch),
            ("memory", intervention.memory_patch),
            ("tool_output_or_observation", intervention.tool_output_patch),
            ("instruction", intervention.instruction_patch),
        )
        if value
    ]
    metadata = {
        **intervention.metadata,
        "schema_version": "cab_intervention_contract_v3",
        "intervention_version": benchmark_version,
        "source": intervention.metadata.get(
            "source",
            "repository-authored deterministic intervention generator",
        ),
        "license": intervention.metadata.get("license", "DATA_LICENSE.md"),
        "provenance": intervention.metadata.get(
            "provenance",
            "repository-authored deterministic intervention generator",
        ),
        "goal_preservation_statement": (
            "The high-level user goal and evaluator ground truth are preserved "
            "unless the explicit answer contract permits uncertainty or clarification."
        ),
        "required_invariances": list(intervention.non_target_factors),
        "changed_fields": changed_fields,
        "unchanged_fields": [
            "base_task.goal",
            "base_task.success_criteria",
            "base_task.hidden_ground_truth",
        ],
        "environment_mutation": bool(
            intervention.tool_availability_patch
            or intervention.tool_output_patch
            or intervention.memory_patch
            or intervention.instruction_patch
        ),
        "tool_mutation": bool(
            intervention.tool_availability_patch
            or intervention.tool_output_patch
        ),
        "observation_mutation": bool(intervention.tool_output_patch),
        "memory_mutation": bool(intervention.memory_patch),
        "answer_policy_change": (
            contract != base_task.answer_contract
            or intervention.expected_final_answer_change != "no"
        ),
        "scorer_policy_change": True,
        "manipulation_check": "HUMAN_INPUT_REQUIRED",
        "human_validation_state": "HUMAN_INPUT_REQUIRED",
    }
    updated = intervention.model_copy(
        update={
            "answer_contract": contract,
            "gold_answer_policy": gold,
            "scorer_policy": scorer,
            "acceptable_abstention_conditions": acceptable_abstention_conditions,
            "metadata": metadata,
        }
    )
    return updated.model_copy(
        update={
            "metadata": {
                **updated.metadata,
                "content_hash": content_hash(updated),
            }
        }
    )


def intervention_answer_contract(
    intervention: InterventionSpec,
) -> AnswerContract:
    family = intervention.family
    if family in _CLARIFICATION_FAMILIES:
        return AnswerContract.CLARIFICATION_REQUIRED
    if family in _RECOVERY_FAMILIES:
        return AnswerContract.RECOVERY_ROUTE_REQUIRED
    if family in _UNCERTAINTY_FAMILIES:
        return AnswerContract.QUALIFIED_UNCERTAINTY_ACCEPTED
    return AnswerContract.ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED


def _abstention_opportunity(
    base_task: BaseTask,
    intervention: InterventionSpec,
    contract: AnswerContract,
    *,
    removed_tools: list[str],
) -> AbstentionOpportunity | None:
    if contract not in {
        AnswerContract.QUALIFIED_UNCERTAINTY_ACCEPTED,
        AnswerContract.CLARIFICATION_REQUIRED,
        AnswerContract.RECOVERY_ROUTE_REQUIRED,
    }:
        return None
    target_tool = str(intervention.tool_output_patch.get("target_tool") or "")
    unavailable_tools = list(removed_tools)
    if contract == AnswerContract.RECOVERY_ROUTE_REQUIRED and target_tool:
        unavailable_tools.append(target_tool)
    required_evidence = list(
        base_task.goal.required_information
        or base_task.expected_evidence
        or base_task.goal.success_criteria
    )
    if contract == AnswerContract.CLARIFICATION_REQUIRED:
        required_evidence = ["material user decision criterion"]
    permitted: list[PermittedResponseType]
    if contract == AnswerContract.CLARIFICATION_REQUIRED:
        permitted = [PermittedResponseType.CLARIFICATION]
    else:
        permitted = [
            PermittedResponseType.ABSTENTION,
            PermittedResponseType.QUALIFIED_UNCERTAINTY,
        ]
    return AbstentionOpportunity(
        opportunity_id=f"{intervention.intervention_id}.opportunity.v3",
        completion_impossible_or_unsafe=True,
        reason=(
            "The intervention can make the preregistered evidence insufficient "
            "for a safe substantive answer."
        ),
        missing_or_contradictory_evidence=required_evidence,
        unavailable_required_tools=sorted(set(unavailable_tools)),
        unavailable_required_artifacts=[],
        another_route_exists=False,
        clarification_possible=(
            contract == AnswerContract.CLARIFICATION_REQUIRED
        ),
        recovery_possible=(contract == AnswerContract.RECOVERY_ROUTE_REQUIRED),
        permitted_response_types=permitted,
    )


def infer_answer_type(value: Any) -> AnswerValueType:
    if isinstance(value, bool):
        return AnswerValueType.BOOLEAN
    if isinstance(value, int | float):
        return AnswerValueType.NUMBER
    if isinstance(value, list):
        return AnswerValueType.ORDERED_COLLECTION
    if isinstance(value, dict):
        if {"min", "max"}.issubset(value) or {"lower", "upper"}.issubset(
            value
        ):
            return AnswerValueType.RANGE
        return AnswerValueType.JSON
    return AnswerValueType.NORMALIZED_STRING


def infer_output_schema(value: Any) -> dict[str, Any]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        item_schemas = [infer_output_schema(item) for item in value]
        unique = {
            stable_hash(schema, length=64): schema for schema in item_schemas
        }
        items: dict[str, Any]
        if not unique:
            items = {}
        elif len(unique) == 1:
            items = next(iter(unique.values()))
        else:
            items = {"anyOf": list(unique.values())}
        return {"type": "array", "items": items}
    if isinstance(value, dict):
        properties = {
            str(key): infer_output_schema(item)
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
        }
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }
    return {"type": "string"}


def content_hash(value: BaseTask | InterventionSpec) -> str:
    payload = value.model_dump(mode="json", exclude_none=False)
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        metadata = dict(metadata)
        metadata.pop("content_hash", None)
        payload["metadata"] = metadata
    return stable_hash(payload, length=64)


def _template_id(task: BaseTask) -> str:
    metadata = task.metadata
    hidden = task.hidden_ground_truth
    family = (
        metadata.get("scenario_key")
        or hidden.get("template_domain")
        or metadata.get("artifact_type")
        or task.domain
    )
    variant = metadata.get("template_variant", hidden.get("variant", 0))
    return f"{family}:{variant}"


__all__ = [
    "POLICY_VERSION",
    "attach_base_task_policies",
    "attach_intervention_policies",
    "content_hash",
    "infer_answer_type",
    "infer_output_schema",
    "intervention_answer_contract",
]
