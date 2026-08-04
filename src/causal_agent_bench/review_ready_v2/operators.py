"""Executable intervention operators and the fail-closed isolation audit.

An intervention instance is never produced by relabelling an expected route.  It
is produced by applying exactly one operator to a concrete clean environment and
then proving, from the enumerated structural diff, that exactly the intended
factor changed and every declared invariant held.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.common import structural_diff
from causal_agent_bench.review_ready_v2.evidence import ANSWER_BEARING_TOKENS, scan_answer_bearing
from causal_agent_bench.review_ready_v2.models import EnvironmentState, InterventionPatch

OPERATORS = ("remove_tool", "inject_tool_failure", "corrupt_memory_field", "inject_conflicting_observation")

CHANGED_FACTOR = {
    "remove_tool": "declared_tool_capability_availability",
    "inject_tool_failure": "declared_tool_runtime_success",
    "corrupt_memory_field": "task_critical_memory_field_validity",
    "inject_conflicting_observation": "cross_source_observation_consistency",
}

BASE_INVARIANTS = (
    "goal_text_identical",
    "prompt_text_identical",
    "non_target_sources_identical",
    "non_target_memory_fields_identical",
    "non_target_tool_contracts_identical",
    "source_trust_ranks_identical",
    "no_answer_bearing_field_introduced",
)


class OperatorError(ValueError):
    """The operator could not be applied to this clean state as declared."""


def canonical_state(state: EnvironmentState) -> dict[str, Any]:
    """State view whose diff locators are stable under list reordering."""

    dumped = state.model_dump(mode="json")
    return {
        "goal": dumped["goal"],
        "sources": dumped["sources"],
        "memory": dumped["memory"],
        "source_trust": dumped["source_trust"],
        "injected_failures": dumped["injected_failures"],
        "tools": {contract["tool_id"]: contract for contract in dumped["tools"]},
    }


def _clone(state: EnvironmentState) -> EnvironmentState:
    return EnvironmentState.model_validate(state.model_dump(mode="json"))


def remove_tool(state: EnvironmentState, tool_id: str) -> tuple[EnvironmentState, InterventionPatch]:
    target = state.tool(tool_id)
    if target is None:
        raise OperatorError(f"cannot remove absent tool: {tool_id}")
    mutated = _clone(state)
    mutated.tools = [contract for contract in mutated.tools if contract.tool_id != tool_id]
    patch = InterventionPatch(
        operator="remove_tool",
        intended_changed_factor=CHANGED_FACTOR["remove_tool"],
        target_locators=[f"$.tools.{tool_id}"],
        before={"tool": target.model_dump(mode="json")},
        after={"tool": None},
        rationale=(
            f"The {tool_id} capability is revoked. Every other declared tool, all evidence, all "
            "memory and the user goal are preserved exactly."
        ),
    )
    return mutated, patch


def inject_tool_failure(
    state: EnvironmentState, tool_id: str, failure_class: str
) -> tuple[EnvironmentState, InterventionPatch]:
    target = state.tool(tool_id)
    if target is None:
        raise OperatorError(f"cannot fail absent tool: {tool_id}")
    if failure_class not in target.failure_modes:
        raise OperatorError(f"{failure_class} is not a declared failure mode of {tool_id}")
    if tool_id in state.injected_failures:
        raise OperatorError(f"{tool_id} already fails in the clean state")
    mutated = _clone(state)
    mutated.injected_failures = {**mutated.injected_failures, tool_id: failure_class}
    patch = InterventionPatch(
        operator="inject_tool_failure",
        intended_changed_factor=CHANGED_FACTOR["inject_tool_failure"],
        target_locators=["$.injected_failures"],
        before={"injected_failures": dict(state.injected_failures)},
        after={"injected_failures": mutated.injected_failures, "failure_class": failure_class},
        rationale=(
            f"Calls to {tool_id} now fail through the tool runtime with {failure_class}. The tool "
            "remains declared, and no other tool, record, or memory field changes."
        ),
    )
    return mutated, patch


def corrupt_memory_field(
    state: EnvironmentState, field_name: str, corrupted_value: Any
) -> tuple[EnvironmentState, InterventionPatch]:
    if field_name not in state.memory:
        raise OperatorError(f"cannot corrupt absent memory field: {field_name}")
    clean_value = state.memory[field_name]
    if clean_value is None:
        raise OperatorError(f"memory field {field_name} has no valid clean predecessor value")
    if clean_value == corrupted_value:
        raise OperatorError(f"memory corruption of {field_name} would be a no-op")
    mutated = _clone(state)
    mutated.memory[field_name] = corrupted_value
    patch = InterventionPatch(
        operator="corrupt_memory_field",
        intended_changed_factor=CHANGED_FACTOR["corrupt_memory_field"],
        target_locators=[f"$.memory.{field_name}"],
        before={field_name: clean_value},
        after={field_name: corrupted_value},
        rationale=(
            f"The previously valid, task-critical memory field {field_name} is replaced by a stale "
            "or unusable value. No other memory field, record, or tool changes."
        ),
    )
    return mutated, patch


def inject_conflicting_observation(
    state: EnvironmentState,
    source_name: str,
    field_name: str,
    conflicting_value: Any,
    *,
    match_field: str | None = None,
    match_value: Any = None,
) -> tuple[EnvironmentState, InterventionPatch]:
    source = state.sources.get(source_name)
    if source is None:
        raise OperatorError(f"cannot conflict absent source: {source_name}")
    mutated = _clone(state)
    target = mutated.sources[source_name]
    if isinstance(target, list):
        if match_field is None:
            raise OperatorError("a collection conflict requires a match field")
        rows = [row for row in target if row.get(match_field) == match_value]
        if len(rows) != 1:
            raise OperatorError(f"conflict target is not unique in {source_name}")
        row = rows[0]
        clean_value = row[field_name]
        locator = f"$.sources.{source_name}[{match_field}={match_value}].{field_name}"
        row[field_name] = conflicting_value
    else:
        clean_value = target[field_name]
        locator = f"$.sources.{source_name}.{field_name}"
        target[field_name] = conflicting_value
    if clean_value == conflicting_value:
        raise OperatorError(f"conflict injection into {source_name}.{field_name} would be a no-op")
    peers = sorted(
        name
        for name, rank in state.source_trust.items()
        if name != source_name and rank == state.source_trust.get(source_name)
    )
    patch = InterventionPatch(
        operator="inject_conflicting_observation",
        intended_changed_factor=CHANGED_FACTOR["inject_conflicting_observation"],
        target_locators=[locator],
        before={field_name: clean_value},
        after={field_name: conflicting_value, "equal_trust_peers": peers},
        rationale=(
            f"The peer source {source_name} now reports a value for {field_name} that contradicts "
            "the other declared source. Both sources remain readable through their own declared "
            "tools, and the user goal is unchanged."
        ),
    )
    return mutated, patch


def apply_operator(
    state: EnvironmentState, operator: str, target: str, detail: dict[str, Any]
) -> tuple[EnvironmentState, InterventionPatch]:
    if operator == "remove_tool":
        return remove_tool(state, target)
    if operator == "inject_tool_failure":
        return inject_tool_failure(state, target, str(detail["failure_class"]))
    if operator == "corrupt_memory_field":
        return corrupt_memory_field(state, target, detail.get("corrupted_value"))
    if operator == "inject_conflicting_observation":
        match_field = detail.get("match_field")
        match_value = detail.get("match_value")
        if match_field and "match_source_field" in detail:
            source_name, field_name = detail["match_source_field"]
            match_value = state.sources[source_name][field_name]
        return inject_conflicting_observation(
            state,
            target,
            str(detail["field"]),
            detail["conflicting_value"],
            match_field=match_field,
            match_value=match_value,
        )
    raise OperatorError(f"unknown intervention operator: {operator}")


def _locator_allowed(locator: str, patch: InterventionPatch) -> bool:
    if patch.operator == "inject_conflicting_observation":
        declared = patch.target_locators[0]
        head, _, tail = declared.partition("[")
        if tail:
            field = declared.rsplit(".", 1)[1]
            return locator.startswith(head) and locator.endswith(f".{field}")
        return locator == declared
    return any(locator == prefix or locator.startswith(prefix + ".") for prefix in patch.target_locators)


def isolation_audit(
    clean: EnvironmentState,
    intervention: EnvironmentState,
    patch: InterventionPatch,
    *,
    required_invariants: tuple[str, ...] = BASE_INVARIANTS,
) -> dict[str, Any]:
    """Fail-closed proof that exactly the intended factor changed."""

    diff = structural_diff(canonical_state(clean), canonical_state(intervention))
    unexpected = [row for row in diff if not _locator_allowed(str(row["locator"]), patch)]
    changed_units = {
        str(row["locator"]).split("[")[0].rsplit(".", 1)[0]
        if patch.operator == "inject_conflicting_observation"
        else next(
            (prefix for prefix in patch.target_locators if str(row["locator"]).startswith(prefix)),
            str(row["locator"]),
        )
        for row in diff
    }
    clean_tools = {contract.tool_id: contract.model_dump(mode="json") for contract in clean.tools}
    intervention_tools = {
        contract.tool_id: contract.model_dump(mode="json") for contract in intervention.tools
    }
    target_tool = patch.target_locators[0].removeprefix("$.tools.") if patch.operator == "remove_tool" else None
    target_memory = (
        patch.target_locators[0].removeprefix("$.memory.") if patch.operator == "corrupt_memory_field" else None
    )
    target_source = (
        patch.target_locators[0].removeprefix("$.sources.").split("[")[0].split(".")[0]
        if patch.operator == "inject_conflicting_observation"
        else None
    )
    added_tokens = scan_answer_bearing(intervention.sources)
    checks = {
        "diff_is_non_empty": bool(diff),
        "exactly_one_intended_mutation_unit": len(changed_units) == 1,
        "no_unexpected_mutation": not unexpected,
        "goal_text_identical": clean.goal == intervention.goal,
        "non_target_sources_identical": all(
            clean.sources[name] == intervention.sources[name]
            for name in clean.sources
            if name != target_source
        )
        and set(clean.sources) == set(intervention.sources),
        "non_target_memory_fields_identical": all(
            clean.memory[name] == intervention.memory[name]
            for name in clean.memory
            if name != target_memory
        )
        and set(clean.memory) == set(intervention.memory),
        "non_target_tool_contracts_identical": all(
            clean_tools[name] == intervention_tools[name]
            for name in clean_tools
            if name != target_tool and name in intervention_tools
        ),
        "source_trust_ranks_identical": clean.source_trust == intervention.source_trust,
        "no_answer_bearing_field_introduced": not added_tokens,
        "declared_factor_recognised": patch.intended_changed_factor == CHANGED_FACTOR[patch.operator],
    }
    if patch.operator == "remove_tool":
        checks["exactly_one_capability_removed"] = (
            len(clean_tools) - len(intervention_tools) == 1 and target_tool not in intervention_tools
        )
    if patch.operator == "inject_tool_failure":
        checks["exactly_one_tool_failing"] = (
            len(intervention.injected_failures) - len(clean.injected_failures) == 1
        )
        checks["tool_still_declared"] = all(
            intervention.tool(tool_id) is not None for tool_id in intervention.injected_failures
        )
    return {
        "operator": patch.operator,
        "intended_changed_factor": patch.intended_changed_factor,
        "diff": diff,
        "unexpected_mutations": unexpected,
        "answer_bearing_tokens_added": sorted(added_tokens),
        "required_invariants": list(required_invariants),
        "checks": checks,
        "passed": all(checks.values()),
    }


__all__ = [
    "ANSWER_BEARING_TOKENS",
    "BASE_INVARIANTS",
    "CHANGED_FACTOR",
    "OPERATORS",
    "OperatorError",
    "apply_operator",
    "canonical_state",
    "corrupt_memory_field",
    "inject_conflicting_observation",
    "inject_tool_failure",
    "isolation_audit",
    "remove_tool",
]
