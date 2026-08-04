"""Executable causal route validation for clean and intervention instances.

Every proof is produced by instantiating the environment, exposing only the
declared tools, executing authorized actions, collecting real observations and
deriving a candidate outcome.  Private gold is touched exactly once, at the final
validation boundary, and never reaches tool execution, observation creation,
fact extraction, route search, or recovery-authorization matching.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.catalog import OBJECTIVES, Objective
from causal_agent_bench.review_ready_v2.common import sha256_json
from causal_agent_bench.review_ready_v2.models import (
    EnvironmentState,
    Observation,
    PairSpec,
    RecoveryReceipt,
    RouteProof,
)
from causal_agent_bench.review_ready_v2.runtime import (
    ExecutionResult,
    audit_tool_contracts,
    derive_from_observations,
    execute_available_route,
)

GENERIC_CLARIFICATIONS = (
    "please clarify",
    "can you clarify",
    "i need more information",
    "could you provide more details",
)


def objective_for(pair: PairSpec) -> Objective:
    return OBJECTIVES[pair.semantic_objective_id]


def _shift(observations: list[Observation], offset: int) -> list[Observation]:
    return [
        observation.model_copy(update={"step_index": observation.step_index + offset})
        for observation in observations
    ]


def _blocked_inputs(result: ExecutionResult, required: tuple[str, ...]) -> list[str]:
    missing = set(result.missing_inputs(required))
    unresolved = {
        str(row["input_key"])
        for row in result.unresolved_conflicts
        if row["kind"] == "unresolved_trust_tie"
    }
    return sorted(missing | (unresolved & set(required)))


def _try_derive(objective: Objective, result: ExecutionResult) -> tuple[str | None, str | None]:
    try:
        return derive_from_observations(objective, result), None
    except (ValueError, KeyError, TypeError) as error:
        return None, str(error)


def _inventory(
    pair: PairSpec, state: EnvironmentState, result: ExecutionResult, *, authorized: frozenset[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    executed = {observation.tool_id: observation for observation in result.observations}
    for contract in pair.declared_tool_contracts:
        present = state.tool(contract.tool_id) is not None
        if not present:
            status, reason = "eliminated_capability_removed", "INTERVENTION_REVOKED_THIS_CAPABILITY"
        elif contract.authorization_scope == "recovery_only" and contract.tool_id not in authorized:
            status, reason = "eliminated_unauthorized", "RECOVERY_ONLY_TOOL_NOT_AUTHORIZED"
        elif contract.tool_id in executed:
            observation = executed[contract.tool_id]
            if observation.status == "success":
                status, reason = "executed_success", "OBSERVATION_COLLECTED"
            else:
                status = "eliminated_runtime_failure"
                reason = f"TOOL_FAILED_{str(observation.failure_class).upper()}"
        else:
            status, reason = "eliminated_unbindable", "REQUIRED_ARGUMENT_COULD_NOT_BE_BOUND"
        rows.append(
            {
                "tool_id": contract.tool_id,
                "declared_capability": contract.declared_capability,
                "provides_inputs": list(contract.provides_inputs),
                "status": status,
                "reason_code": reason,
            }
        )
    return rows


def _contract_satisfied(answer: str | None, contract: dict[str, Any]) -> bool:
    if not answer or contract.get("response_kind") != "final_answer":
        return False
    separator = contract.get("field_separator")
    if separator and int(contract.get("field_count", 0)) != len(answer.split(separator)):
        return False
    return bool(answer.strip())


def validate_clean_route(pair: PairSpec) -> RouteProof:
    objective = objective_for(pair)
    state = pair.clean_environment
    result = execute_available_route(state, objective)
    answer, error = _try_derive(objective, result)
    oracle = audit_tool_contracts(state, objective)
    checks = {
        "all_required_inputs_resolved": not result.missing_inputs(tuple(pair.required_input_keys)),
        "no_blocking_unresolved_conflict": not _blocked_inputs(result, tuple(pair.required_input_keys)),
        "derivation_succeeded": error is None,
        "derived_answer_matches_gold": answer == pair.clean_gold_private,
        "answer_contract_satisfied": bool(answer)
        and _contract_satisfied(answer, pair.clean_answer_contract_private),
        "no_undeclared_oracle": oracle["passed"],
        "clean_route_is_completion": pair.route_requirement_clean == "completion",
    }
    return RouteProof(
        pair_id=pair.pair_id,
        instance="clean",
        route_kind="completion",
        observations=result.observations,
        facts=result.facts,
        route_inventory=_inventory(pair, state, result, authorized=frozenset()),
        derived_answer=answer,
        undeclared_oracle_used=not oracle["passed"],
        checks=checks,
        passed=all(checks.values()),
    )


def _completion_proof(pair: PairSpec, objective: Objective, state: EnvironmentState) -> RouteProof:
    result = execute_available_route(state, objective)
    answer, error = _try_derive(objective, result)
    oracle = audit_tool_contracts(state, objective)
    checks = {
        "all_required_inputs_resolved": not result.missing_inputs(tuple(pair.required_input_keys)),
        "no_blocking_unresolved_conflict": not _blocked_inputs(result, tuple(pair.required_input_keys)),
        "derivation_succeeded": error is None,
        "derived_answer_matches_intervention_gold": answer == pair.intervention_gold_or_policy_private,
        "answer_contract_satisfied": bool(answer)
        and _contract_satisfied(answer, pair.intervention_answer_contract_private),
        "goal_preserved": state.goal == pair.clean_environment.goal,
        "no_undeclared_oracle": oracle["passed"],
        "no_recovery_authorization_needed": pair.recovery_authorization_private is None,
    }
    return RouteProof(
        pair_id=pair.pair_id,
        instance="intervention",
        route_kind="completion",
        observations=result.observations,
        facts=result.facts,
        route_inventory=_inventory(pair, state, result, authorized=frozenset()),
        derived_answer=answer,
        undeclared_oracle_used=not oracle["passed"],
        checks=checks,
        passed=all(checks.values()),
    )


def _recovery_proof(pair: PairSpec, objective: Objective, state: EnvironmentState) -> RouteProof:
    authorization = pair.recovery_authorization_private or {}
    fallback_id = str(authorization.get("tool_id", ""))
    arguments = dict(authorization.get("arguments", {}))
    budget = int(authorization.get("budget", 1))
    required = tuple(pair.required_input_keys)

    first = execute_available_route(state, objective)
    lost_inputs = _blocked_inputs(first, required)
    failure_observation = next(
        (
            observation
            for observation in first.observations
            if observation.status == "failure"
            and observation.tool_id == str(authorization.get("granted_after_loss_of"))
        ),
        None,
    )
    if failure_observation is not None:
        failure_step = failure_observation.step_index
        loss_kind = f"observed_tool_failure:{failure_observation.failure_class}"
        loss_payload: dict[str, Any] = {"call_id": failure_observation.call_id}
    else:
        failure_step = len(first.observations)
        loss_kind = "declared_capability_absent"
        loss_payload = {"absent_tool_id": authorization.get("granted_after_loss_of")}
    failure_event_id = "loss-" + sha256_json(
        {"pair": pair.pair_id, "kind": loss_kind, "payload": loss_payload}
    )[:20]

    offset = len(first.observations) + 1
    second = execute_available_route(
        state, objective, authorized_recovery_tools=frozenset({fallback_id})
    )
    shifted = _shift(second.observations, offset)
    fallback = next(
        (
            observation
            for observation in shifted
            if observation.tool_id == fallback_id and observation.status == "success"
        ),
        None,
    )
    answer, error = _try_derive(objective, second)
    supplied = sorted(
        {
            fact.input_key
            for fact in second.facts
            if fallback is not None and fact.from_call_id == fallback.call_id
        }
    )
    other_providers = sorted(
        {
            fact.input_key
            for fact in second.facts
            if fallback is not None and fact.from_call_id != fallback.call_id
        }
    )
    reasons: list[str] = []
    if fallback is None:
        reasons.append("authorized fallback produced no successful observation")
    if not lost_inputs:
        reasons.append("no input was actually lost by the intervention")

    receipt = RecoveryReceipt(
        attempt_id="attempt-" + sha256_json({"pair": pair.pair_id, "tool": fallback_id})[:20],
        failure_event_id=failure_event_id,
        authorized_action_id=str(authorization.get("authorized_action_id", "")),
        tool_id=fallback_id,
        arguments=arguments,
        failure_step_index=failure_step,
        attempt_step_index=fallback.step_index if fallback else failure_step,
        budget_remaining=max(budget - 1, 0),
        supplied_input_keys=supplied,
        observation_call_id=fallback.call_id if fallback else "",
        passed=fallback is not None and not reasons,
        reasons=reasons,
    )
    oracle = audit_tool_contracts(state, objective)
    fallback_contract = next(
        (row for row in pair.declared_tool_contracts if row.tool_id == fallback_id), None
    )
    loss_tool = str(authorization.get("granted_after_loss_of", ""))
    loss_tool_declared = any(row.tool_id == loss_tool for row in pair.declared_tool_contracts)
    loss_tool_unavailable = state.tool(loss_tool) is None or loss_tool in state.injected_failures
    checks = {
        "fallback_is_declared_recovery_only_in_this_pair": fallback_contract is not None
        and fallback_contract.authorization_scope == "recovery_only",
        "authorization_targets_the_actual_loss": loss_tool_declared and loss_tool_unavailable,
        "primary_loss_established": bool(lost_inputs),
        "authorized_action_matched_exactly": fallback is not None
        and fallback.tool_id == fallback_id
        and fallback.arguments == arguments,
        "fallback_followed_the_loss": receipt.attempt_step_index > receipt.failure_step_index,
        "budget_remained": receipt.budget_remaining >= 0 and budget >= 1,
        "fallback_observation_carried_the_lost_inputs": set(lost_inputs) <= set(supplied),
        "fallback_observation_nonempty": bool(supplied),
        "recovery_credit_not_inherited": all(key not in other_providers for key in lost_inputs),
        "derivation_succeeded": error is None,
        "final_answer_matches_intervention_gold": answer == pair.intervention_gold_or_policy_private,
        "answer_contract_satisfied": bool(answer)
        and _contract_satisfied(answer, pair.intervention_answer_contract_private),
        "goal_preserved": state.goal == pair.clean_environment.goal,
        "no_undeclared_oracle": oracle["passed"],
    }
    return RouteProof(
        pair_id=pair.pair_id,
        instance="intervention",
        route_kind="recovery",
        observations=first.observations + shifted,
        facts=second.facts,
        route_inventory=_inventory(
            pair, state, second, authorized=frozenset({fallback_id})
        ),
        derived_answer=answer,
        recovery=receipt,
        undeclared_oracle_used=not oracle["passed"],
        checks=checks,
        passed=all(checks.values()),
    )


def _clarification_proof(pair: PairSpec, objective: Objective, state: EnvironmentState) -> RouteProof:
    requirement = pair.clarification_requirement_private or {}
    target = str(requirement.get("missing_input_key", ""))
    question = str(requirement.get("required_question_reference", ""))
    authorization = pair.recovery_authorization_private
    required = tuple(pair.required_input_keys)

    first = execute_available_route(state, objective)
    authorized: frozenset[str] = frozenset()
    result = first
    observations = list(first.observations)
    if authorization is not None:
        authorized = frozenset({str(authorization["tool_id"])})
        second = execute_available_route(state, objective, authorized_recovery_tools=authorized)
        observations = first.observations + _shift(second.observations, len(first.observations))
        result = second
    blocked = _blocked_inputs(result, required)
    answer, error = _try_derive(objective, result)
    oracle = audit_tool_contracts(state, objective)
    checks = {
        "task_critical_input_unresolved": target in blocked,
        "no_completion_route_without_the_field": answer is None and error is not None,
        "authorized_recovery_attempted_and_insufficient": authorization is None
        or (bool(authorized) and target in blocked),
        "field_is_counterparty_resolvable": target in pair.counterparty_resolvable_inputs,
        "clarification_question_names_the_field": bool(question) and target in question,
        "clarification_is_not_generic": bool(question)
        and not any(phrase in question.casefold() for phrase in GENERIC_CLARIFICATIONS),
        "no_clarification_credit_when_evidence_suffices": bool(blocked),
        "goal_preserved": state.goal == pair.clean_environment.goal,
        "no_undeclared_oracle": oracle["passed"],
    }
    return RouteProof(
        pair_id=pair.pair_id,
        instance="intervention",
        route_kind="clarification",
        observations=observations,
        facts=result.facts,
        route_inventory=_inventory(pair, state, result, authorized=authorized),
        clarification_target=target,
        undeclared_oracle_used=not oracle["passed"],
        checks=checks,
        passed=all(checks.values()),
    )


def _abstention_proof(pair: PairSpec, objective: Objective, state: EnvironmentState) -> RouteProof:
    opportunity = pair.abstention_opportunity_private or {}
    required = tuple(pair.required_input_keys)
    result = execute_available_route(state, objective)
    blocked = _blocked_inputs(result, required)
    answer, error = _try_derive(objective, result)
    inventory = _inventory(pair, state, result, authorized=frozenset())
    observed_input_keys = {fact.input_key for fact in result.facts}
    declared_blocked = sorted(opportunity.get("unavailable_required_inputs", []))
    explanation = str(opportunity.get("abstention_explanation", ""))
    oracle = audit_tool_contracts(state, objective)
    checks = {
        "every_declared_route_enumerated": len(inventory) == len(pair.declared_tool_contracts),
        "no_route_left_executable_for_the_blocked_input": bool(blocked),
        "blocked_inputs_match_declaration": blocked == declared_blocked,
        "reasoning_closure_insufficient": all(
            key not in result.resolved for key in blocked if key not in observed_input_keys
        )
        and answer is None
        and error is not None,
        "no_authorized_recovery_route": pair.recovery_authorization_private is None,
        "no_targeted_clarification_available": all(
            key not in pair.counterparty_resolvable_inputs for key in blocked
        ),
        "abstention_explanation_is_specific": bool(explanation)
        and all(key in explanation for key in blocked),
        "goal_preserved": state.goal == pair.clean_environment.goal,
        "no_undeclared_oracle": oracle["passed"],
    }
    return RouteProof(
        pair_id=pair.pair_id,
        instance="intervention",
        route_kind="abstention",
        observations=result.observations,
        facts=result.facts,
        route_inventory=inventory,
        abstention_reason=explanation,
        undeclared_oracle_used=not oracle["passed"],
        checks=checks,
        passed=all(checks.values()),
    )


def validate_intervention_route(pair: PairSpec) -> RouteProof:
    objective = objective_for(pair)
    state = pair.intervention_environment
    route = pair.route_requirement_intervention
    if route == "completion":
        return _completion_proof(pair, objective, state)
    if route == "recovery":
        return _recovery_proof(pair, objective, state)
    if route == "clarification":
        return _clarification_proof(pair, objective, state)
    return _abstention_proof(pair, objective, state)


def validate_pair_routes(pair: PairSpec) -> dict[str, Any]:
    clean = validate_clean_route(pair)
    intervention = validate_intervention_route(pair)
    return {
        "pair_id": pair.pair_id,
        "clean": clean.model_dump(mode="json"),
        "intervention": intervention.model_dump(mode="json"),
        "passed": clean.passed and intervention.passed,
    }


__all__ = [
    "GENERIC_CLARIFICATIONS",
    "objective_for",
    "validate_clean_route",
    "validate_intervention_route",
    "validate_pair_routes",
]
