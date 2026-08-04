"""Materialise the twenty clean/intervention pairs from the frozen design matrix.

Generation is fail-closed: a pair is only emitted if the clean derivation
reproduces the objective's independently hand-written expected answer, the
isolation audit proves exactly one changed factor, and the required intervention
route is provable against the real environment.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.catalog import (
    DESIGN_MATRIX,
    OBJECTIVES,
    Nuisance,
    Objective,
    PairPlan,
    nuisance_for,
    plan_for_index,
)
from causal_agent_bench.review_ready_v2.common import derive_token
from causal_agent_bench.review_ready_v2.evidence import primitive_evidence_report
from causal_agent_bench.review_ready_v2.models import (
    AnchorSpec,
    EnvironmentState,
    PairSpec,
)
from causal_agent_bench.review_ready_v2.operators import (
    BASE_INVARIANTS,
    apply_operator,
    isolation_audit,
)
from causal_agent_bench.review_ready_v2.routes import (
    validate_clean_route,
    validate_intervention_route,
)
from causal_agent_bench.review_ready_v2.runtime import (
    derive_from_observations,
    execute_available_route,
)

FAMILY_OPERATOR = {
    "tool_removal": "remove_tool",
    "tool_failure": "inject_tool_failure",
    "memory_corruption": "corrupt_memory_field",
    "observation_conflict": "inject_conflicting_observation",
}

ALLOWED_NUISANCE_DIFFERENCES = ("record_order", "identifier_labels")
FORBIDDEN_SEMANTIC_DIFFERENCES = (
    "semantic_objective",
    "task_archetype",
    "answer_derivation_logic",
    "difficulty",
    "intervention_family",
    "route_requirement",
    "required_input_keys",
    "decision_relevant_numeric_values",
)

SCORER_EXACT = {
    "scorer_id": "cab_review_ready_v2_normalized_exact_v1",
    "match": "normalized_exact",
    "normalization": ["strip", "casefold", "collapse_whitespace"],
    "partial_credit": False,
}


class PairGenerationError(ValueError):
    """A designed pair failed one of its own generation-time invariants."""


def _instance_ids(seed: bytes, index: int) -> tuple[str, str, str, str]:
    return (
        f"pair-{derive_token(seed, f'pair:{index}', 20)}",
        f"base-{derive_token(seed, f'base:{index}', 20)}",
        f"clean-{derive_token(seed, f'clean:{index}', 20)}",
        f"intv-{derive_token(seed, f'intervention:{index}', 20)}",
    )


def _answer_contract(gold: str) -> dict[str, Any]:
    return {
        "response_kind": "final_answer",
        "field_separator": "|",
        "field_count": len(gold.split("|")),
        "normalization": ["strip", "casefold", "collapse_whitespace"],
        "must_not_include_reasoning_trace": True,
    }


def _clean_state(objective: Objective, nuisance: Nuisance) -> EnvironmentState:
    sources, memory, trust = objective.build_environment(nuisance)
    return EnvironmentState(
        goal=objective.goal,
        sources=sources,
        memory=memory,
        source_trust=trust,
        tools=objective.tools(nuisance),
        injected_failures={},
    )


def _derive(objective: Objective, state: EnvironmentState, authorized: frozenset[str]) -> str:
    result = execute_available_route(state, objective, authorized_recovery_tools=authorized)
    return derive_from_observations(objective, result)


def _blocked(objective: Objective, state: EnvironmentState, authorized: frozenset[str]) -> list[str]:
    result = execute_available_route(state, objective, authorized_recovery_tools=authorized)
    missing = set(result.missing_inputs(objective.required_input_keys))
    unresolved = {
        str(row["input_key"])
        for row in result.unresolved_conflicts
        if row["kind"] == "unresolved_trust_tie"
    }
    return sorted(missing | (unresolved & set(objective.required_input_keys)))


def _recovery_authorization(seed: bytes, plan: PairPlan, *, sufficient: bool) -> dict[str, Any]:
    fallback = str(plan.operator_detail["authorized_fallback"])
    return {
        "authorized_action_id": f"recover-{derive_token(seed, f'recovery:{plan.pair_index}', 16)}",
        "tool_id": fallback,
        "arguments": {},
        "granted_after_loss_of": plan.operator_target,
        "budget": 1,
        "single_use": True,
        "sufficient_for_completion": sufficient,
        "authorization_note": (
            "This fallback is authorized only after the declared loss of "
            f"{plan.operator_target} has been observed, and only for this pair."
        ),
    }


def _clarification_requirement(
    plan: PairPlan, objective: Objective, blocked: list[str]
) -> dict[str, Any]:
    target = str(plan.operator_detail.get("clarification_target") or (blocked[0] if blocked else ""))
    questions = {
        "overtime_threshold_hours": (
            "What is your contracted weekly overtime_threshold_hours? The timesheet totals are "
            "available but the contracted threshold is no longer readable."
        ),
        "max_acceptable_lead_days": (
            "What is the max_acceptable_lead_days limit for this order? The archived requirements "
            "record supplies the required unit count but not the lead-time limit."
        ),
        "target_publication_year": (
            "Which listing is authoritative for target_publication_year on this entry — the "
            "bibliography listing or the publisher listing? They disagree and neither takes "
            "precedence."
        ),
    }
    return {
        "missing_input_key": target,
        "counterparty": objective.counterparty,
        "required_question_reference": questions[target],
        "why_not_completion": (
            f"No declared tool, and no arithmetic or comparison over the visible facts, yields "
            f"{target} in the intervention environment."
        ),
        "why_not_abstention": (
            f"{target} is a value the {objective.counterparty} holds, so a single targeted question "
            "resolves the task."
        ),
        "generic_clarification_is_not_credited": True,
    }


def _abstention_opportunity(
    plan: PairPlan, objective: Objective, blocked: list[str], inventory_note: str
) -> dict[str, Any]:
    keys = ", ".join(blocked)
    return {
        "unavailable_required_inputs": blocked,
        "eliminated_routes": inventory_note,
        "counterparty": objective.counterparty,
        "counterparty_cannot_supply": True,
        "abstention_explanation": (
            f"Every declared route was executed or eliminated and {keys} remains unobtainable; "
            f"{inventory_note}. No recovery is authorized, and the {objective.counterparty} cannot "
            f"supply {keys}, so no targeted clarification resolves it. Report the blocker instead "
            "of guessing."
        ),
        "why_not_clarification": (
            f"{keys} is external system state rather than a value the {objective.counterparty} "
            "holds, so no single question they can answer resolves it."
        ),
        "why_not_completion": (
            f"Arithmetic, comparison, sorting, filtering and date reasoning over the remaining "
            f"visible facts cannot reconstruct {keys}."
        ),
    }


def build_pair(seed: bytes, plan: PairPlan) -> PairSpec:
    objective = OBJECTIVES[plan.objective_id]
    nuisance = nuisance_for(plan)
    pair_id, base_task_id, clean_id, intervention_id = _instance_ids(seed, plan.pair_index)

    clean_state = _clean_state(objective, nuisance)
    clean_gold = _derive(objective, clean_state, frozenset())
    expected = objective.expected_answer(nuisance)
    if clean_gold != expected:
        raise PairGenerationError(
            f"pair {plan.pair_index}: executable derivation {clean_gold!r} does not reproduce the "
            f"independently specified expected answer {expected!r}"
        )

    operator = FAMILY_OPERATOR[plan.family]
    intervention_state, patch = apply_operator(
        clean_state, operator, plan.operator_target, plan.operator_detail
    )
    isolation = isolation_audit(clean_state, intervention_state, patch)
    if not isolation["passed"]:
        failed = sorted(name for name, value in isolation["checks"].items() if not value)
        raise PairGenerationError(f"pair {plan.pair_index}: isolation audit failed: {failed}")

    route = plan.route_intervention
    recovery: dict[str, Any] | None = None
    clarification: dict[str, Any] | None = None
    abstention: dict[str, Any] | None = None
    authorized: frozenset[str] = frozenset()

    if route == "recovery":
        recovery = _recovery_authorization(seed, plan, sufficient=True)
        authorized = frozenset({str(recovery["tool_id"])})
        intervention_gold = _derive(objective, intervention_state, authorized)
        intervention_contract = _answer_contract(intervention_gold)
    elif route == "completion":
        intervention_gold = _derive(objective, intervention_state, frozenset())
        intervention_contract = _answer_contract(intervention_gold)
    elif route == "clarification":
        if "authorized_fallback" in plan.operator_detail:
            recovery = _recovery_authorization(seed, plan, sufficient=False)
            authorized = frozenset({str(recovery["tool_id"])})
        blocked = _blocked(objective, intervention_state, authorized)
        clarification = _clarification_requirement(plan, objective, blocked)
        target = str(clarification["missing_input_key"])
        if blocked != [target]:
            raise PairGenerationError(
                f"pair {plan.pair_index}: expected exactly {target!r} to be unresolved, got {blocked}"
            )
        intervention_gold = f"CLARIFY:{target}"
        intervention_contract = {
            "response_kind": "clarification_request",
            "must_reference_input_key": target,
            "must_not_return_a_final_answer": True,
            "generic_request_rejected": True,
        }
    else:
        blocked = _blocked(objective, intervention_state, frozenset())
        if not blocked:
            raise PairGenerationError(
                f"pair {plan.pair_index}: abstention was designed but the task remains solvable"
            )
        note = _elimination_note(plan)
        abstention = _abstention_opportunity(plan, objective, blocked, note)
        intervention_gold = "ABSTAIN:" + ",".join(blocked)
        intervention_contract = {
            "response_kind": "abstention",
            "must_name_unavailable_inputs": blocked,
            "must_not_return_a_final_answer": True,
            "must_not_fabricate_a_value": True,
        }

    manifest = objective.evidence_manifest
    evidence = primitive_evidence_report(clean_state.sources, gold=clean_gold, manifest=manifest)
    if not evidence["passed"]:
        raise PairGenerationError(
            f"pair {plan.pair_index}: primitive-evidence scan failed: {evidence['checks']}"
        )

    anchor = None
    if plan.anchor_group_id and plan.anchor_source_index:
        source_pair_id, _, _, _ = _instance_ids(seed, plan.anchor_source_index)
        anchor = AnchorSpec(
            anchor_group_id=plan.anchor_group_id,
            anchor_source_pair_id=source_pair_id,
            allowed_nuisance_differences=list(ALLOWED_NUISANCE_DIFFERENCES),
            forbidden_semantic_differences=list(FORBIDDEN_SEMANTIC_DIFFERENCES),
        )

    pair = PairSpec(
        pair_id=pair_id,
        base_task_id=base_task_id,
        semantic_objective_id=objective.objective_id,
        task_archetype=objective.archetype,
        domain=objective.domain,
        difficulty=plan.difficulty,
        intervention_family=plan.family,
        route_requirement_clean=plan.route_clean,
        route_requirement_intervention=route,
        anchor=anchor,
        clean_instance_id=clean_id,
        intervention_instance_id=intervention_id,
        shared_goal=objective.goal,
        clean_prompt=objective.prompt,
        intervention_prompt=objective.prompt,
        clean_environment=clean_state,
        intervention_environment=intervention_state,
        primitive_evidence_manifest=manifest,
        declared_tool_contracts=list(clean_state.tools),
        intervention_operator=operator,
        intervention_patch=patch,
        intended_changed_factor=patch.intended_changed_factor,
        preserved_invariants=list(BASE_INVARIANTS),
        required_input_keys=list(objective.required_input_keys),
        counterparty=objective.counterparty,
        counterparty_resolvable_inputs=list(objective.counterparty_resolvable_inputs),
        clean_gold_private=clean_gold,
        intervention_gold_or_policy_private=intervention_gold,
        clean_answer_contract_private=_answer_contract(clean_gold),
        intervention_answer_contract_private=intervention_contract,
        clean_scorer_contract_private=dict(SCORER_EXACT),
        intervention_scorer_contract_private=dict(SCORER_EXACT)
        if route in {"completion", "recovery"}
        else {
            "scorer_id": f"cab_review_ready_v2_{route}_v1",
            "match": "structured_policy",
            "partial_credit": False,
        },
        recovery_authorization_private=recovery,
        abstention_opportunity_private=abstention,
        clarification_requirement_private=clarification,
    )

    clean_proof = validate_clean_route(pair)
    if not clean_proof.passed:
        failed = sorted(name for name, value in clean_proof.checks.items() if not value)
        raise PairGenerationError(f"pair {plan.pair_index}: clean route proof failed: {failed}")
    intervention_proof = validate_intervention_route(pair)
    if not intervention_proof.passed:
        failed = sorted(name for name, value in intervention_proof.checks.items() if not value)
        raise PairGenerationError(
            f"pair {plan.pair_index}: {route} route proof failed: {failed}"
        )
    return pair


def _elimination_note(plan: PairPlan) -> str:
    if plan.family == "tool_removal":
        return f"the {plan.operator_target} capability was revoked and nothing else exposes it"
    if plan.family == "memory_corruption":
        return (
            f"the corrupted {plan.operator_target} no longer resolves to a declared record, so the "
            "dependent lookup returns nothing"
        )
    return (
        f"two equally trusted sources disagree on {plan.operator_detail.get('field')} and no "
        "declared precedence rule breaks the tie"
    )


def build_all_pairs(seed: bytes) -> list[PairSpec]:
    if len(seed) < 32:
        raise PairGenerationError("the private generation seed must contain at least 32 bytes")
    return [build_pair(seed, plan) for plan in DESIGN_MATRIX]


def anchor_groups(pairs: list[PairSpec]) -> dict[str, list[PairSpec]]:
    groups: dict[str, list[PairSpec]] = {}
    index = {pair.pair_id: pair for pair in pairs}
    for pair in pairs:
        if pair.anchor is None:
            continue
        source = index[pair.anchor.anchor_source_pair_id]
        groups.setdefault(pair.anchor.anchor_group_id, [source, pair])
    return groups


__all__ = [
    "ALLOWED_NUISANCE_DIFFERENCES",
    "FAMILY_OPERATOR",
    "FORBIDDEN_SEMANTIC_DIFFERENCES",
    "PairGenerationError",
    "anchor_groups",
    "build_all_pairs",
    "build_pair",
    "plan_for_index",
]
