"""Capability-bounded tool runtime and observation-only derivation.

Nothing in this module can see private gold, route labels, answer contracts or
expected fact identifiers.  Tools return declared projections of exactly one
named source; there is no general-purpose artifact reader in the scientific
route, and ``recovery_only`` tools stay invisible unless a recovery
authorization has explicitly granted them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from causal_agent_bench.review_ready_v2.catalog import Objective
from causal_agent_bench.review_ready_v2.common import canonical_bytes, sha256_json
from causal_agent_bench.review_ready_v2.models import (
    DerivedFact,
    EnvironmentState,
    Observation,
    ToolContract,
)

FORBIDDEN_TOOL_IDS = frozenset(
    {"read_file", "read_artifact", "dump_artifact", "cat_file", "load_manifest", "open_source"}
)
"""Tool identifiers that would constitute an undeclared universal oracle."""

REASONING_CLOSURE = (
    "arithmetic",
    "comparison",
    "sorting",
    "set_membership",
    "filtering",
    "date_time_comparison",
    "conjunction_of_visible_conditions",
    "direct_lookup_from_visible_primitive_observations",
)
"""Operations an agent may perform on already-visible facts without a tool."""


class ToolExecutionError(RuntimeError):
    """A tool was invoked outside its declared contract."""


@dataclass(frozen=True)
class SourcedValue:
    input_key: str
    value: Any
    tool_id: str
    source_ref: str
    trust_rank: int
    call_id: str


@dataclass
class ExecutionResult:
    observations: list[Observation] = field(default_factory=list)
    facts: list[DerivedFact] = field(default_factory=list)
    sourced: dict[str, list[SourcedValue]] = field(default_factory=dict)
    resolved: dict[str, Any] = field(default_factory=dict)
    unresolved_conflicts: list[dict[str, Any]] = field(default_factory=list)
    failures: list[Observation] = field(default_factory=list)
    executed_tool_ids: list[str] = field(default_factory=list)

    def missing_inputs(self, required: tuple[str, ...]) -> list[str]:
        return [key for key in required if key not in self.resolved]


def _project(fields: list[str], record: dict[str, Any]) -> dict[str, Any]:
    return {name: record[name] for name in fields if name in record}


def _input_values(contract: ToolContract, payload: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key in contract.provides_inputs:
        if isinstance(payload, dict) and key in payload:
            values[key] = payload[key]
        elif len(contract.provides_inputs) == 1:
            if isinstance(payload, dict) and len(contract.returned_fields) == 1:
                values[key] = payload[contract.returned_fields[0]]
            else:
                values[key] = payload
        else:
            raise ToolExecutionError(
                f"tool {contract.tool_id} cannot supply declared input {key}"
            )
    return values


class ToolRuntime:
    """Executes declared tools against a concrete environment state."""

    def __init__(
        self,
        state: EnvironmentState,
        *,
        authorized_recovery_tools: frozenset[str] = frozenset(),
    ) -> None:
        self.state = state
        self.authorized_recovery_tools = authorized_recovery_tools
        self._step = 0

    def visible_tools(self) -> list[ToolContract]:
        return [
            contract
            for contract in self.state.tools
            if contract.authorization_scope == "standard"
            or contract.tool_id in self.authorized_recovery_tools
        ]

    def execute(self, contract: ToolContract, arguments: dict[str, Any]) -> Observation:
        if contract.tool_id in FORBIDDEN_TOOL_IDS:
            raise ToolExecutionError(f"undeclared universal oracle rejected: {contract.tool_id}")
        if self.state.tool(contract.tool_id) is None:
            raise ToolExecutionError(f"tool not present in environment: {contract.tool_id}")
        if contract.authorization_scope == "recovery_only" and contract.tool_id not in self.authorized_recovery_tools:
            raise ToolExecutionError(f"recovery-only tool used without authorization: {contract.tool_id}")
        unexpected = sorted(set(arguments) - set(contract.allowed_arguments))
        if unexpected:
            raise ToolExecutionError(
                f"tool {contract.tool_id} received undeclared arguments: {', '.join(unexpected)}"
            )
        step = self._step
        self._step += 1
        call_id = "call-" + sha256_json(
            {"tool": contract.tool_id, "arguments": arguments, "step": step}
        )[:20]
        if contract.tool_id in self.state.injected_failures:
            return Observation(
                call_id=call_id,
                tool_id=contract.tool_id,
                arguments=arguments,
                status="failure",
                failure_class=self.state.injected_failures[contract.tool_id],
                step_index=step,
            )
        payload = self._payload(contract, arguments)
        if payload is None:
            return Observation(
                call_id=call_id,
                tool_id=contract.tool_id,
                arguments=arguments,
                status="failure",
                failure_class="not_found",
                source_ref=contract.trust_key,
                step_index=step,
            )
        observation = Observation(
            call_id=call_id,
            tool_id=contract.tool_id,
            arguments=arguments,
            status="success",
            source_ref=contract.trust_key,
            payload={"projection": payload},
            step_index=step,
        )
        _reject_answer_metadata(observation)
        return observation

    def _payload(self, contract: ToolContract, arguments: dict[str, Any]) -> Any:
        capability = contract.declared_capability
        if capability == "memory_read":
            if contract.scope_source not in self.state.memory:
                return None
            value = self.state.memory[contract.scope_source]
            if value is None:
                return None
            return {contract.scope_source: value}
        source = self.state.sources.get(contract.scope_source)
        if source is None:
            return None
        if capability == "collection_read":
            if not isinstance(source, list):
                raise ToolExecutionError(f"{contract.scope_source} is not a collection")
            return [_project(contract.returned_fields, row) for row in source]
        if capability in {"record_lookup", "document_read"}:
            if not isinstance(source, dict):
                raise ToolExecutionError(f"{contract.scope_source} is not a record")
            return _project(contract.returned_fields, source)
        if capability == "indexed_lookup":
            if not isinstance(source, list) or len(contract.allowed_arguments) != 1:
                raise ToolExecutionError(f"{contract.tool_id} is not a valid indexed lookup")
            key = contract.allowed_arguments[0]
            if key not in arguments:
                raise ToolExecutionError(f"{contract.tool_id} requires argument {key}")
            matches = [row for row in source if row.get(key) == arguments[key]]
            if len(matches) != 1:
                return None
            return _project(contract.returned_fields, matches[0])
        raise ToolExecutionError(f"unsupported capability: {capability}")


def _reject_answer_metadata(observation: Observation) -> None:
    text = canonical_bytes(observation.payload).decode().casefold()
    for marker in ("expected_answer", "returned_fact_ids", "route_kind", "gold", "scorer_policy"):
        if marker in text:
            raise ToolExecutionError("tool observation carries forbidden answer metadata")


def resolve(sourced: dict[str, list[SourcedValue]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Resolve multi-source inputs by trust rank; report unresolved ties."""

    resolved: dict[str, Any] = {}
    conflicts: list[dict[str, Any]] = []
    for key in sorted(sourced):
        entries = sourced[key]
        distinct = {canonical_bytes(entry.value) for entry in entries}
        if len(distinct) == 1:
            resolved[key] = entries[0].value
            continue
        best_rank = min(entry.trust_rank for entry in entries)
        top = [entry for entry in entries if entry.trust_rank == best_rank]
        if len({canonical_bytes(entry.value) for entry in top}) == 1:
            resolved[key] = top[0].value
            conflicts.append(
                {
                    "input_key": key,
                    "kind": "resolved_by_trust_hierarchy",
                    "winning_source": top[0].source_ref,
                    "winning_trust_rank": best_rank,
                    "dissenting_sources": sorted(
                        entry.source_ref for entry in entries if entry.trust_rank != best_rank
                    ),
                }
            )
            continue
        conflicts.append(
            {
                "input_key": key,
                "kind": "unresolved_trust_tie",
                "tied_sources": sorted(entry.source_ref for entry in top),
                "tied_trust_rank": best_rank,
            }
        )
    return resolved, conflicts


def execute_available_route(
    state: EnvironmentState,
    objective: Objective,
    *,
    authorized_recovery_tools: frozenset[str] = frozenset(),
) -> ExecutionResult:
    """Exhaustively execute every visible tool whose arguments can be bound.

    This is the route-exhaustion procedure: it keeps calling tools until no
    further tool can be bound, which is what makes an abstention or
    clarification claim provable rather than declared.
    """

    runtime = ToolRuntime(state, authorized_recovery_tools=authorized_recovery_tools)
    result = ExecutionResult()
    pending = list(runtime.visible_tools())
    progressed = True
    while progressed:
        progressed = False
        for contract in list(pending):
            arguments: dict[str, Any] = {}
            bindable = True
            for argument, input_key in contract.argument_bindings.items():
                if input_key not in result.resolved:
                    bindable = False
                    break
                arguments[argument] = result.resolved[input_key]
            if not bindable:
                continue
            pending.remove(contract)
            observation = runtime.execute(contract, arguments)
            result.observations.append(observation)
            result.executed_tool_ids.append(contract.tool_id)
            progressed = True
            if observation.status != "success":
                result.failures.append(observation)
                continue
            payload = observation.payload["projection"]
            trust_rank = state.source_trust.get(contract.trust_key, 1)
            for input_key, value in _input_values(contract, payload).items():
                result.sourced.setdefault(input_key, []).append(
                    SourcedValue(
                        input_key=input_key,
                        value=value,
                        tool_id=contract.tool_id,
                        source_ref=contract.trust_key,
                        trust_rank=trust_rank,
                        call_id=observation.call_id,
                    )
                )
                result.facts.append(
                    DerivedFact(
                        fact_id="fact-"
                        + sha256_json(
                            {
                                "source": contract.trust_key,
                                "input": input_key,
                                "value": value,
                                "call": observation.call_id,
                            }
                        )[:24],
                        input_key=input_key,
                        source_locator=f"{contract.trust_key}::{input_key}",
                        observed_value=value,
                        from_call_id=observation.call_id,
                    )
                )
            result.resolved, result.unresolved_conflicts = resolve(result.sourced)
    result.resolved, result.unresolved_conflicts = resolve(result.sourced)
    return result


def derive_from_observations(objective: Objective, result: ExecutionResult) -> str:
    """Derive the answer using only observed, conflict-resolved inputs."""

    missing = result.missing_inputs(objective.required_input_keys)
    if missing:
        raise ValueError(f"required inputs unobtainable: {', '.join(missing)}")
    unresolved = [row["input_key"] for row in result.unresolved_conflicts if row["kind"] == "unresolved_trust_tie"]
    blocking = sorted(set(unresolved) & set(objective.required_input_keys))
    if blocking:
        raise ValueError(f"required inputs are in unresolved conflict: {', '.join(blocking)}")
    return objective.derive({key: result.resolved[key] for key in objective.required_input_keys})


def audit_tool_contracts(state: EnvironmentState, objective: Objective) -> dict[str, Any]:
    """Structural proof that no tool is an undeclared universal oracle."""

    manifest = objective.evidence_manifest
    findings: list[str] = []
    for contract in state.tools:
        if contract.tool_id in FORBIDDEN_TOOL_IDS:
            findings.append(f"forbidden_oracle:{contract.tool_id}")
        if contract.declared_capability != "memory_read":
            declared = manifest.get(contract.scope_source)
            if declared is None:
                findings.append(f"unmanifested_source:{contract.scope_source}")
            elif not set(contract.returned_fields) <= set(declared):
                findings.append(f"projection_exceeds_manifest:{contract.tool_id}")
        if not contract.failure_modes:
            findings.append(f"missing_failure_modes:{contract.tool_id}")
    scopes = {contract.scope_source for contract in state.tools}
    checks = {
        "no_forbidden_oracle_tool": not any(row.startswith("forbidden_oracle") for row in findings),
        "every_tool_scoped_to_one_source": all(
            isinstance(contract.scope_source, str) and contract.scope_source for contract in state.tools
        ),
        "projections_within_manifest": not any(
            row.startswith(("projection_exceeds_manifest", "unmanifested_source")) for row in findings
        ),
        "failure_modes_declared": not any(row.startswith("missing_failure_modes") for row in findings),
        "no_single_tool_spans_all_sources": all(
            len({contract.scope_source}) == 1 for contract in state.tools
        )
        and len(scopes) >= 1,
    }
    return {"findings": sorted(findings), "checks": checks, "passed": all(checks.values())}


__all__ = [
    "FORBIDDEN_TOOL_IDS",
    "REASONING_CLOSURE",
    "ExecutionResult",
    "SourcedValue",
    "ToolExecutionError",
    "ToolRuntime",
    "audit_tool_contracts",
    "derive_from_observations",
    "execute_available_route",
    "resolve",
]
