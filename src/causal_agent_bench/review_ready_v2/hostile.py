"""Hostile attacks that the route, operator and evidence validators must reject.

Each case constructs a concretely invalid situation and records whether the
validator refused it.  A case that is *not* rejected is a gate failure, so this
module fails closed rather than reporting a passing summary.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.evidence import primitive_evidence_report
from causal_agent_bench.review_ready_v2.models import PairSpec, ToolContract
from causal_agent_bench.review_ready_v2.operators import (
    OperatorError,
    corrupt_memory_field,
    inject_conflicting_observation,
    isolation_audit,
    remove_tool,
)
from causal_agent_bench.review_ready_v2.routes import objective_for, validate_intervention_route
from causal_agent_bench.review_ready_v2.runtime import (
    ToolExecutionError,
    ToolRuntime,
    audit_tool_contracts,
    execute_available_route,
)


def _copy(pair: PairSpec) -> PairSpec:
    return PairSpec.model_validate(pair.model_dump(mode="json"))


def _rejected(pair: PairSpec) -> bool:
    return not validate_intervention_route(pair).passed


def _case(name: str, rejected: bool, detail: str) -> dict[str, Any]:
    return {"attack": name, "rejected": bool(rejected), "detail": detail}


def _recovery_attacks(pair: PairSpec) -> list[dict[str, Any]]:
    authorization = dict(pair.recovery_authorization_private or {})
    cases: list[dict[str, Any]] = []

    wrong_tool = _copy(pair)
    other = next(
        (
            contract.tool_id
            for contract in pair.declared_tool_contracts
            if contract.tool_id != authorization.get("tool_id")
        ),
        "",
    )
    wrong_tool.recovery_authorization_private = {**authorization, "tool_id": other}
    cases.append(_case("recovery_with_wrong_tool", _rejected(wrong_tool), f"tool_id={other}"))

    wrong_arguments = _copy(pair)
    wrong_arguments.recovery_authorization_private = {
        **authorization,
        "arguments": {"unauthorized_scope": "all"},
    }
    cases.append(
        _case("recovery_with_wrong_arguments", _rejected(wrong_arguments), "arguments mismatch")
    )

    no_failure = _copy(pair)
    no_failure.intervention_environment = pair.clean_environment
    cases.append(
        _case(
            "recovery_before_any_failure",
            _rejected(no_failure),
            "recovery claimed against an unmutated environment",
        )
    )

    stale = _copy(pair)
    stale.recovery_authorization_private = {
        **authorization,
        "granted_after_loss_of": "tool_from_another_pair",
    }
    cases.append(_case("stale_or_foreign_authorization", _rejected(stale), "loss target unbound"))

    inherited = _copy(pair)
    standard = next(
        (
            contract.tool_id
            for contract in pair.declared_tool_contracts
            if contract.authorization_scope == "standard"
        ),
        "",
    )
    inherited.recovery_authorization_private = {**authorization, "tool_id": standard}
    cases.append(
        _case(
            "undeclared_fallback_or_inherited_authorization",
            _rejected(inherited),
            f"standard tool {standard} claimed as authorized fallback",
        )
    )

    unauthorized_call = False
    recovery_tool = next(
        (
            contract
            for contract in pair.intervention_environment.tools
            if contract.authorization_scope == "recovery_only"
        ),
        None,
    )
    if recovery_tool is not None:
        try:
            ToolRuntime(pair.intervention_environment).execute(recovery_tool, {})
        except ToolExecutionError:
            unauthorized_call = True
    cases.append(
        _case(
            "recovery_only_tool_called_without_authorization",
            unauthorized_call,
            "runtime refused an unauthorized recovery-only call",
        )
    )
    return cases


def _clarification_attacks(pair: PairSpec) -> list[dict[str, Any]]:
    requirement = dict(pair.clarification_requirement_private or {})
    generic = _copy(pair)
    generic.clarification_requirement_private = {
        **requirement,
        "required_question_reference": "Please clarify.",
    }
    misdirected = _copy(pair)
    misdirected.clarification_requirement_private = {
        **requirement,
        "missing_input_key": "unrelated_input_key",
    }
    return [
        _case("generic_clarification_request", _rejected(generic), "no input key referenced"),
        _case(
            "clarification_for_an_unblocked_field",
            _rejected(misdirected),
            "clarification target is not the blocked input",
        ),
    ]


def _abstention_attacks(pair: PairSpec) -> list[dict[str, Any]]:
    objective = objective_for(pair)
    restored = _copy(pair)
    restored.intervention_environment = pair.clean_environment
    solvable_rejected = _rejected(restored)

    result = execute_available_route(pair.clean_environment, objective)
    still_solvable = not result.missing_inputs(tuple(pair.required_input_keys))

    resolvable = _copy(pair)
    resolvable.counterparty_resolvable_inputs = list(
        (pair.abstention_opportunity_private or {}).get("unavailable_required_inputs", [])
    )
    return [
        _case(
            "abstention_claimed_while_task_remains_solvable",
            solvable_rejected and still_solvable,
            "clean environment still yields every required input",
        ),
        _case(
            "abstention_claimed_despite_a_targeted_clarification",
            _rejected(resolvable),
            "blocked input declared counterparty-resolvable",
        ),
    ]


def _evidence_attacks(pair: PairSpec) -> list[dict[str, Any]]:
    objective = objective_for(pair)
    manifest = pair.primitive_evidence_manifest

    oracle_state = pair.clean_environment.model_copy(deep=True)
    oracle_state.tools = [
        *oracle_state.tools,
        ToolContract(
            tool_id="read_file",
            declared_capability="record_lookup",
            scope_source=next(iter(oracle_state.sources)),
            returned_fields=["*"],
            failure_modes=["timeout"],
            provides_inputs=["everything"],
        ),
    ]
    oracle_rejected = not audit_tool_contracts(oracle_state, objective)["passed"]
    runtime_rejected = False
    try:
        ToolRuntime(oracle_state).execute(oracle_state.tools[-1], {})
    except ToolExecutionError:
        runtime_rejected = True

    gold_state = pair.clean_environment.model_copy(deep=True)
    first_source = next(iter(gold_state.sources))
    gold_leaked = dict(gold_state.sources)
    gold_leaked["leaked_reference"] = {"note": pair.clean_gold_private}
    gold_report = primitive_evidence_report(
        gold_leaked, gold=pair.clean_gold_private, manifest=manifest
    )

    answer_field = dict(pair.clean_environment.sources)
    answer_field["decision_hint"] = {"final_answer": "anything"}
    answer_report = primitive_evidence_report(
        answer_field, gold=pair.clean_gold_private, manifest=manifest
    )

    injected_state = pair.clean_environment.model_copy(deep=True)
    injected = injected_state.sources[first_source]
    if isinstance(injected, list) and injected:
        injected[0]["returned_fact_ids"] = ["fact-planted"]
    elif isinstance(injected, dict):
        injected["returned_fact_ids"] = ["fact-planted"]
    # Layer 1: the scoped projection must drop the planted field entirely.
    planted = execute_available_route(injected_state, objective)
    injection_invisible = not any(
        "fact-planted" in str(observation.payload) for observation in planted.observations
    ) and not any("fact-planted" in str(fact.observed_value) for fact in planted.facts)
    # Layer 2: even a mis-specified contract that declares the field must be refused.
    leaky_state = injected_state.model_copy(deep=True)
    leaky_state.tools = [
        contract.model_copy(update={"returned_fields": [*contract.returned_fields, "returned_fact_ids"]})
        if contract.scope_source == first_source
        else contract
        for contract in leaky_state.tools
    ]
    contract_refused = False
    try:
        execute_available_route(leaky_state, objective)
    except ToolExecutionError:
        contract_refused = True
    if not contract_refused:
        contract_refused = not audit_tool_contracts(leaky_state, objective)["passed"]
    injection_rejected = injection_invisible and contract_refused

    return [
        _case("undeclared_universal_artifact_oracle", oracle_rejected and runtime_rejected, "read_file"),
        _case("private_gold_planted_in_evidence", not gold_report["passed"], "verbatim gold leaf"),
        _case("answer_bearing_field_planted", not answer_report["passed"], "final_answer field"),
        _case("expected_fact_identifier_injection", injection_rejected, "returned_fact_ids"),
    ]


def _operator_attacks(pair: PairSpec) -> list[dict[str, Any]]:
    clean = pair.clean_environment
    patch = pair.intervention_patch
    cases: list[dict[str, Any]] = []

    double_removal = clean.model_copy(deep=True)
    removable = [contract.tool_id for contract in clean.tools][:2]
    if len(removable) == 2:
        double_removal.tools = [
            contract for contract in double_removal.tools if contract.tool_id not in removable
        ]
        audit = isolation_audit(clean, double_removal, remove_tool(clean, removable[0])[1])
        cases.append(_case("removal_of_more_than_one_capability", not audit["passed"], "two tools removed"))

    goal_changed = pair.intervention_environment.model_copy(deep=True)
    goal_changed.goal = clean.goal + " Also summarise the records."
    cases.append(
        _case(
            "intervention_patch_changes_the_goal",
            not isolation_audit(clean, goal_changed, patch)["passed"],
            "goal text mutated",
        )
    )

    evidence_changed = pair.intervention_environment.model_copy(deep=True)
    for name, value in evidence_changed.sources.items():
        if name in str(patch.target_locators):
            continue
        if isinstance(value, list) and value and isinstance(value[0], dict):
            key = sorted(value[0])[0]
            value[0][key] = f"mutated-{value[0][key]}"
            break
        if isinstance(value, dict) and value:
            key = sorted(value)[0]
            value[key] = f"mutated-{value[key]}"
            break
    cases.append(
        _case(
            "intervention_patch_changes_unrelated_evidence",
            not isolation_audit(clean, evidence_changed, patch)["passed"],
            "non-target source mutated",
        )
    )

    no_op_conflict = False
    try:
        source_name, source_value = next(
            (name, value) for name, value in clean.sources.items() if isinstance(value, dict) and value
        )
        field_name = sorted(source_value)[0]
        inject_conflicting_observation(
            clean, source_name, field_name, source_value[field_name]
        )
    except OperatorError:
        no_op_conflict = True
    except StopIteration:
        no_op_conflict = True
    cases.append(
        _case(
            "conflict_declared_without_a_conflicting_observation",
            no_op_conflict,
            "identical value injection refused",
        )
    )

    no_predecessor = False
    try:
        corrupt_memory_field(clean, "field_that_never_existed", "anything")
    except OperatorError:
        no_predecessor = True
    cases.append(
        _case(
            "memory_corruption_without_a_clean_predecessor",
            no_predecessor,
            "absent memory field refused",
        )
    )
    return cases


def hostile_pair_report(pair: PairSpec) -> dict[str, Any]:
    cases = _evidence_attacks(pair) + _operator_attacks(pair)
    route = pair.route_requirement_intervention
    if route == "recovery":
        cases += _recovery_attacks(pair)
    elif route == "clarification":
        cases += _clarification_attacks(pair)
    elif route == "abstention":
        cases += _abstention_attacks(pair)
    return {
        "pair_id": pair.pair_id,
        "route_kind": route,
        "attack_count": len(cases),
        "attacks": cases,
        "passed": all(case["rejected"] for case in cases),
    }


def hostile_route_audit(pairs: list[PairSpec]) -> dict[str, Any]:
    rows = [hostile_pair_report(pair) for pair in pairs]
    survivors = [
        {"pair_id": row["pair_id"], "attack": case["attack"]}
        for row in rows
        for case in row["attacks"]
        if not case["rejected"]
    ]
    return {
        "schema_version": "cab_review_ready_v2_hostile_route_audit_v1",
        "status": "CAB_ROUTE_HOSTILE_AUDIT_PASSED" if not survivors else "CAB_ROUTE_HOSTILE_AUDIT_FAILED",
        "pair_count": len(rows),
        "attack_count": sum(row["attack_count"] for row in rows),
        "surviving_attacks": survivors,
        "rows": rows,
        "passed": not survivors,
    }


__all__ = ["hostile_pair_report", "hostile_route_audit"]
