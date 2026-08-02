"""Per-attempt, fail-closed recovery authorization state machine."""

from __future__ import annotations

from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.answer_contracts import RecoveryActionContract
from causal_agent_bench.hashing import stable_hash


class RecoveryAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_id: str = Field(min_length=1)
    failure_event_id: str = Field(min_length=1)
    authorized_action_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    validated_arguments: dict[str, Any]
    start_step: int = Field(ge=0)
    end_step: int = Field(ge=0)
    attempt_number: int = Field(ge=1)
    budget_remaining: int = Field(ge=0)
    observation_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    returned_fact_ids: list[str]
    success_predicate_results: dict[str, bool]
    authorized: bool
    succeeded: bool


def evaluate_recovery_attempts(
    steps: list[Any],
    authorizations: list[RecoveryActionContract],
    *,
    final_answer_correct: bool = False,
) -> dict[str, Any]:
    """Evaluate every attempt independently; no authorization state is carried."""

    contracts = {contract.action_id: contract for contract in authorizations}
    failure_events: list[dict[str, Any]] = []
    attempts: list[RecoveryAttempt] = []
    counts: Counter[str] = Counter()
    seen_attempt_ids: set[str] = set()
    for step_index, raw in enumerate(steps):
        payload = raw.model_dump(mode="python") if hasattr(raw, "model_dump") else raw
        if not isinstance(payload, dict):
            continue
        action = payload.get("action")
        action = action if isinstance(action, dict) else {}
        call = action.get("tool_call")
        call = call if isinstance(call, dict) else payload.get("tool_call")
        call = call if isinstance(call, dict) else {}
        metadata = action.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        observation = payload.get("observation") or payload.get("tool_result")
        observation = observation if isinstance(observation, dict) else {}
        tool_name = str(call.get("tool_name") or observation.get("tool_name") or "")
        if _observation_failed(observation):
            failure_class = str(observation.get("error") or "corrupt_or_partial_observation")
            failure_event_id = str(
                observation.get("failure_event_id")
                or stable_hash(
                    {
                        "step": step_index,
                        "tool": tool_name,
                        "failure_class": failure_class,
                    },
                    length=32,
                )
            )
            failure_events.append(
                {
                    "failure_event_id": failure_event_id,
                    "failure_class": failure_class,
                    "tool_name": tool_name,
                    "step": step_index,
                }
            )
            continue
        action_id = str(metadata.get("recovery_action") or "")
        marker = bool(metadata.get("recovery_marker") or payload.get("recovery_marker"))
        if not action_id and not marker:
            continue
        latest_failure = failure_events[-1] if failure_events else None
        contract = contracts.get(action_id)
        counts[action_id] += 1
        attempt_number = counts[action_id]
        derived_attempt_id = stable_hash(
            {"step": step_index, "action_id": action_id, "attempt": attempt_number},
            length=32,
        )
        attempt_id = str(metadata.get("attempt_id") or derived_attempt_id)
        declared_failure_id = str(
            metadata.get("failure_event_id")
            or (latest_failure or {}).get("failure_event_id")
            or "missing-failure-event"
        )
        returned_fact_ids = _returned_fact_ids(observation)
        arguments = call.get("arguments")
        arguments = arguments if isinstance(arguments, dict) else {}
        expected_failure_tool = _expected_failed_tool(contract)
        checks = {
            "failure_occurred": latest_failure is not None,
            "failure_id_current": bool(
                latest_failure
                and declared_failure_id == latest_failure["failure_event_id"]
            ),
            "failure_class_permitted": bool(
                contract
                and latest_failure
                and _failure_class_allowed(
                    str(latest_failure["failure_class"]),
                    contract.failure_types,
                )
            ),
            "failed_tool_matches_precondition": bool(
                contract
                and latest_failure
                and (not expected_failure_tool or latest_failure["tool_name"] == expected_failure_tool)
            ),
            "action_id_exact": contract is not None,
            "tool_exact": bool(contract and tool_name in contract.allowed_tool_names),
            "arguments_valid": bool(
                contract and _arguments_match_schema(arguments, contract.argument_schema)
            ),
            "temporal_order_valid": bool(latest_failure and latest_failure["step"] < step_index),
            "attempt_budget_valid": bool(contract and attempt_number <= contract.max_attempts),
            "attempt_not_replayed": attempt_id not in seen_attempt_ids,
            "observation_owned_by_attempt": str(observation.get("attempt_id") or attempt_id)
            == attempt_id,
            "observation_error_free": not _observation_failed(observation),
            "success_predicate_satisfied": bool(
                contract and _useful_observation(observation, contract.success_predicate)
            ),
            # Fact IDs are content-derived from this observation.  The contract is
            # consulted only after extraction to verify its declared output schema;
            # expected IDs are never copied into the observation.
            "returned_facts_exact": bool(
                contract
                and returned_fact_ids
                and not _declares_fact_ids(observation)
                and _useful_observation(observation, contract.success_predicate)
            ),
        }
        authorization_checks = (
            "failure_occurred",
            "failure_id_current",
            "failure_class_permitted",
            "failed_tool_matches_precondition",
            "action_id_exact",
            "tool_exact",
            "arguments_valid",
            "temporal_order_valid",
            "attempt_budget_valid",
            "attempt_not_replayed",
        )
        authorized = all(checks[name] for name in authorization_checks)
        succeeded = bool(
            authorized
            and checks["observation_owned_by_attempt"]
            and checks["observation_error_free"]
            and checks["success_predicate_satisfied"]
            and checks["returned_facts_exact"]
        )
        budget_remaining = max((contract.max_attempts if contract else 0) - attempt_number, 0)
        attempts.append(
            RecoveryAttempt(
                attempt_id=attempt_id,
                failure_event_id=declared_failure_id,
                authorized_action_id=action_id or "missing-action-id",
                tool_name=tool_name or "missing-tool",
                validated_arguments=arguments,
                start_step=step_index,
                end_step=step_index,
                attempt_number=attempt_number,
                budget_remaining=budget_remaining,
                observation_hash=stable_hash(observation, length=64),
                returned_fact_ids=returned_fact_ids,
                success_predicate_results=checks,
                authorized=authorized,
                succeeded=succeeded,
            )
        )
        seen_attempt_ids.add(attempt_id)
    successful_attempts = [row for row in attempts if row.succeeded]
    replay_or_budget_violation = any(
        not row.success_predicate_results["attempt_budget_valid"]
        or not row.success_predicate_results["attempt_not_replayed"]
        for row in attempts
    )
    recovery_succeeded = bool(successful_attempts and not replay_or_budget_violation)
    return {
        "schema_version": "cab_recovery_authorization_v5_result_v1",
        "status": "CAB_RECOVERY_AUTHORIZATION_V5_READY",
        "failure_events": failure_events,
        "attempts": [row.model_dump(mode="json") for row in attempts],
        "attempted": bool(attempts),
        "authorized": any(row.authorized for row in attempts),
        "succeeded": recovery_succeeded,
        "task_recovered": bool(recovery_succeeded and final_answer_correct),
        "causal_attempt_id": successful_attempts[0].attempt_id if recovery_succeeded else None,
    }


def _returned_fact_ids(observation: dict[str, Any]) -> list[str]:
    """Hash actual observation leaves; never trust caller-declared fact IDs."""

    output = observation.get("output")
    if output in (None, {}, [], "") or _declares_fact_ids(observation):
        return []
    return [
        "obsfact." + stable_hash({"locator": locator, "value": value}, length=24)
        for locator, value in _flatten_observation(output)
    ]


def _declares_fact_ids(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() == "returned_fact_ids" or _declares_fact_ids(child)
            for key, child in value.items()
        )
    return isinstance(value, list) and any(_declares_fact_ids(child) for child in value)


def _flatten_observation(value: Any, locator: str = "$.output") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        return [
            item
            for key in sorted(value)
            for item in _flatten_observation(value[key], f"{locator}.{key}")
        ]
    if isinstance(value, list):
        return [
            item
            for index, child in enumerate(value)
            for item in _flatten_observation(child, f"{locator}[{index}]")
        ]
    return [(locator, value)]


def _expected_failed_tool(contract: RecoveryActionContract | None) -> str:
    if contract is None:
        return ""
    marker = next((value for value in contract.preconditions if value.startswith("failed_tool:")), "")
    return marker.split(":", 1)[1] if marker else ""


def _failure_class_allowed(observed: str, allowed: list[str]) -> bool:
    normalized = observed.casefold()
    return any(value.casefold() in normalized or normalized in value.casefold() for value in allowed)


def _arguments_match_schema(arguments: dict[str, Any], schema: dict[str, Any]) -> bool:
    if schema.get("type") != "object":
        return False
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if not isinstance(required, list) or not isinstance(properties, dict):
        return False
    if any(key not in arguments for key in required):
        return False
    if schema.get("additionalProperties") is False and any(
        key not in properties for key in arguments
    ):
        return False
    return all(
        _value_matches_schema(value, properties.get(key, {}))
        for key, value in arguments.items()
        if key in properties
    )


def _value_matches_schema(value: Any, schema: dict[str, Any]) -> bool:
    expected = schema.get("type")
    allowed = set(expected if isinstance(expected, list) else [expected])
    if value is None:
        return "null" in allowed
    return bool(
        ("string" in allowed and isinstance(value, str))
        or ("array" in allowed and isinstance(value, list))
        or ("object" in allowed and isinstance(value, dict))
        or ("boolean" in allowed and isinstance(value, bool))
        or (
            "integer" in allowed
            and isinstance(value, int)
            and not isinstance(value, bool)
        )
        or (
            "number" in allowed
            and isinstance(value, int | float)
            and not isinstance(value, bool)
        )
    )


def _useful_observation(observation: dict[str, Any], predicate: dict[str, Any]) -> bool:
    if _observation_failed(observation):
        return False
    output = observation.get("output")
    if output in (None, {}, [], ""):
        return observation.get("ok") is True or observation.get("status") in {
            "ok",
            "success",
            "succeeded",
        }
    required = predicate.get("required_output_keys", [])
    return not required or bool(
        isinstance(output, dict) and all(key in output for key in required)
    )


def _observation_failed(observation: dict[str, Any]) -> bool:
    metadata = observation.get("metadata")
    output = observation.get("output")
    return bool(
        observation.get("error")
        or observation.get("is_corrupted")
        or (isinstance(metadata, dict) and metadata.get("intervention") == "partial_output")
        or (isinstance(output, dict) and output.get("partial") is True)
    )


__all__ = ["RecoveryAttempt", "evaluate_recovery_attempts"]
