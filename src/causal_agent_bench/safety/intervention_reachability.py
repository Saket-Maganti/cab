"""Deterministic evidence-route and intervention-solvability auditing."""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.answer_contracts import (
    AnswerContract,
    BehaviorRequirement,
    PermittedResponseType,
)
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.schemas import BenchmarkInstance

RouteKind = Literal["substantive_answer", "recovery", "clarification", "abstention"]


class EvidenceRoute(BaseModel):
    """Auditable fact-to-response path for one benchmark instance."""

    model_config = ConfigDict(extra="forbid")

    route_id: str = Field(min_length=1)
    kind: RouteKind
    required_facts: list[str] = Field(min_length=1)
    source_artifacts: list[str] = Field(min_length=1)
    accessible_tools: list[str]
    permitted_actions: list[str] = Field(min_length=1)
    intermediate_evidence: list[str] = Field(min_length=1)
    valid_final_response: str = Field(min_length=1)


class ReachabilityAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cab_intervention_reachability_v1"] = (
        "cab_intervention_reachability_v1"
    )
    instance_id: str
    base_task_id: str
    intervention_family: str
    routes: list[EvidenceRoute]
    failure_codes: list[str]
    warning_codes: list[str]
    passed: bool
    audit_hash: str


def audit_intervention_reachability(instance: BenchmarkInstance) -> ReachabilityAudit:
    """Return a stable, fail-closed reachability audit for one intervention."""

    if instance.condition != "intervention" or instance.intervention is None:
        raise ValueError("reachability audit requires an intervention instance")
    task = instance.base_task
    intervention = instance.intervention
    scorer = intervention.scorer_policy or task.scorer_policy
    gold = intervention.gold_answer_policy or task.gold_answer_policy
    if scorer is None or gold is None:
        return _finalize(
            instance,
            routes=[],
            failures=["SCORER_OR_GOLD_POLICY_MISSING"],
            warnings=[],
        )

    facts = list(
        task.goal.required_information
        or task.expected_evidence
        or task.goal.success_criteria
    )
    artifacts = _source_artifacts(instance)
    available = set(instance.available_tools)
    required = set(scorer.required_tools)
    removed = {
        str(value)
        for value in intervention.tool_availability_patch.get("removed_tools", [])
    }
    routes: list[EvidenceRoute] = []
    failures: list[str] = []
    warnings: list[str] = []
    opportunity = scorer.abstention_opportunity
    completion_evidence_blocked = bool(
        opportunity is not None
        and opportunity.completion_impossible_or_unsafe
        and not opportunity.another_route_exists
    )

    missing_required = sorted(required - available)
    if missing_required:
        failures.append("REQUIRED_TOOL_AVAILABLE_TOOL_MISMATCH")
    if required & removed:
        failures.append("SURVIVING_ROUTE_REQUIRES_REMOVED_TOOL")

    behavior_only = gold.answer_contract in {
        AnswerContract.ABSTENTION_REQUIRED,
        AnswerContract.CLARIFICATION_REQUIRED,
    }
    if (
        required.issubset(available)
        and required
        and not behavior_only
        and not completion_evidence_blocked
    ):
        routes.append(
            EvidenceRoute(
                route_id=f"{instance.instance_id}.substantive",
                kind="substantive_answer",
                required_facts=facts,
                source_artifacts=artifacts,
                accessible_tools=sorted(required),
                permitted_actions=[f"call:{tool}" for tool in sorted(required)],
                intermediate_evidence=[f"verified:{fact}" for fact in facts],
                valid_final_response="typed substantive answer matching the frozen gold policy",
            )
        )
    elif (
        not behavior_only
        and facts
        and not required
        and not completion_evidence_blocked
    ):
        failures.append("COMPLETION_PERMITTED_WITHOUT_EVIDENCE_ROUTE")

    recovery_actions = list(scorer.required_recovery_actions)
    if gold.answer_contract == AnswerContract.RECOVERY_ROUTE_REQUIRED:
        usable_recovery = [action for action in recovery_actions if action in available]
        if not recovery_actions or not usable_recovery:
            failures.append("REQUIRED_RECOVERY_IMPOSSIBLE")
        else:
            routes.append(
                EvidenceRoute(
                    route_id=f"{instance.instance_id}.recovery",
                    kind="recovery",
                    required_facts=facts,
                    source_artifacts=artifacts,
                    accessible_tools=sorted(usable_recovery),
                    permitted_actions=[f"recover:{tool}" for tool in sorted(usable_recovery)],
                    intermediate_evidence=["post-failure successful recovery observation"],
                    valid_final_response="typed substantive answer after executed recovery",
                )
            )

    if scorer.clarification in {BehaviorRequirement.ACCEPTED, BehaviorRequirement.REQUIRED}:
        if (
            opportunity is not None
            and opportunity.clarification_possible
            and PermittedResponseType.CLARIFICATION
            in opportunity.permitted_response_types
        ):
            routes.append(
                EvidenceRoute(
                    route_id=f"{instance.instance_id}.clarification",
                    kind="clarification",
                    required_facts=facts,
                    source_artifacts=artifacts,
                    accessible_tools=[],
                    permitted_actions=["request_material_clarification"],
                    intermediate_evidence=["typed ambiguity opportunity"],
                    valid_final_response="specific clarification request",
                )
            )
        else:
            failures.append("CLARIFICATION_POLICY_WITHOUT_TYPED_OPPORTUNITY")

    abstention_permitted = scorer.abstention in {
        BehaviorRequirement.ACCEPTED,
        BehaviorRequirement.REQUIRED,
    }
    if abstention_permitted:
        permitted = set(opportunity.permitted_response_types if opportunity else [])
        if (
            opportunity is not None
            and opportunity.completion_impossible_or_unsafe
            and permitted
            & {
                PermittedResponseType.ABSTENTION,
                PermittedResponseType.QUALIFIED_UNCERTAINTY,
            }
        ):
            routes.append(
                EvidenceRoute(
                    route_id=f"{instance.instance_id}.abstention",
                    kind="abstention",
                    required_facts=facts,
                    source_artifacts=artifacts,
                    accessible_tools=sorted(required & available),
                    permitted_actions=["inspect_surviving_evidence", "state_verified_blocker"],
                    intermediate_evidence=[opportunity.reason],
                    valid_final_response="qualified uncertainty or abstention authorized by opportunity",
                )
            )
        else:
            failures.append("ABSTENTION_POLICY_WITHOUT_TYPED_OPPORTUNITY")

    if not routes:
        failures.append("NO_VALID_FINAL_RESPONSE_ROUTE")
    if not intervention.metadata.get("goal_preserved", False):
        failures.append("GOAL_PRESERVATION_NOT_ATTESTED")
    if intervention.metadata.get("ground_truth_policy") not in {
        "unchanged",
        "behavioral_override_required",
        "unchanged_or_behavioral_override",
    }:
        failures.append("HIDDEN_GROUND_TRUTH_POLICY_INVALID")
    if not intervention.non_target_factors:
        failures.append("NON_TARGET_FACTORS_UNDECLARED")
    if scorer.abstention == BehaviorRequirement.FORBIDDEN and not any(
        route.kind in {"substantive_answer", "recovery", "clarification"}
        for route in routes
    ):
        failures.append("FACTS_UNREACHABLE_AND_ABSTENTION_FORBIDDEN")
    if opportunity is not None and opportunity.another_route_exists:
        warnings.append("ABSTENTION_OPPORTUNITY_DECLARES_SURVIVING_ROUTE")

    return _finalize(instance, routes, failures, warnings)


def audit_intervention_collection(
    instances: list[BenchmarkInstance],
) -> dict[str, Any]:
    audits = [audit_intervention_reachability(instance) for instance in instances]
    failure_counts = Counter(
        code for audit in audits for code in audit.failure_codes
    )
    payload: dict[str, Any] = {
        "schema_version": "cab_intervention_reachability_collection_v1",
        "instance_count": len(audits),
        "passed_count": sum(audit.passed for audit in audits),
        "failed_count": sum(not audit.passed for audit in audits),
        "failure_code_counts": dict(sorted(failure_counts.items())),
        "audits": [audit.model_dump(mode="json") for audit in audits],
    }
    payload["collection_hash"] = stable_hash(payload, length=64)
    payload["passed"] = payload["failed_count"] == 0
    return payload


def _source_artifacts(instance: BenchmarkInstance) -> list[str]:
    spec = instance.base_task.metadata.get("artifact_spec")
    if isinstance(spec, dict):
        files = spec.get("files")
        if isinstance(files, list) and files:
            return sorted(str(item) for item in files)
    return ["controlled_synthetic_environment"]


def _finalize(
    instance: BenchmarkInstance,
    routes: list[EvidenceRoute],
    failures: list[str],
    warnings: list[str],
) -> ReachabilityAudit:
    assert instance.intervention is not None
    payload = {
        "schema_version": "cab_intervention_reachability_v1",
        "instance_id": instance.instance_id,
        "base_task_id": instance.base_task.task_id,
        "intervention_family": instance.intervention.family,
        "routes": [route.model_dump(mode="json") for route in routes],
        "failure_codes": sorted(set(failures)),
        "warning_codes": sorted(set(warnings)),
        "passed": not failures,
    }
    return ReachabilityAudit(
        instance_id=instance.instance_id,
        base_task_id=instance.base_task.task_id,
        intervention_family=instance.intervention.family,
        routes=routes,
        failure_codes=sorted(set(failures)),
        warning_codes=sorted(set(warnings)),
        passed=not failures,
        audit_hash=stable_hash(payload, length=64),
    )


__all__ = [
    "EvidenceRoute",
    "ReachabilityAudit",
    "audit_intervention_collection",
    "audit_intervention_reachability",
]
