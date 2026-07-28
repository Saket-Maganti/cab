"""Observable-only anomaly extraction.

The controller never accepts benchmark condition, intervention, gold-answer, or
evaluator fields. ``ObservationEnvelope.from_payload`` selects a public
allow-list and recursively removes hidden metadata from observation values.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import Field, field_validator, model_validator

from causal_agent_bench.raac.types import AnomalySignal, BudgetSnapshot, StrictModel

FORBIDDEN_POLICY_KEYS = frozenset(
    {
        "answer_key",
        "condition",
        "condition_label",
        "evaluator_metadata",
        "expected_behavior",
        "gold",
        "gold_answer",
        "hidden_expected_behavior",
        "hidden_ground_truth",
        "intervention",
        "intervention_family",
        "intervention_id",
        "intervention_type",
        "scorer_metadata",
        "target_factor",
    }
)

_PUBLIC_FIELDS = frozenset(
    {
        "tool_name",
        "error",
        "timed_out",
        "raw_output",
        "parsed_output",
        "required_fields",
        "schema_valid",
        "contradicts_previous",
        "repeated_result_consistent",
        "partial",
        "impossible_value",
        "observed_at",
        "reference_time",
        "max_staleness_seconds",
        "evidence_count",
        "minimum_evidence",
        "insufficient_evidence",
        "success_claimed",
        "success_verifiable",
        "candidate_answer",
        "clarification_possible",
        "reported_token_budget_exhausted",
        "reported_tool_budget_exhausted",
        "reported_retry_budget_exhausted",
        "infrastructure_failure",
        "elapsed_seconds",
    }
)


def _normalized_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def scrub_hidden_metadata(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): scrub_hidden_metadata(item)
            for key, item in value.items()
            if _normalized_key(key) not in FORBIDDEN_POLICY_KEYS
        }
    if isinstance(value, list):
        return [scrub_hidden_metadata(item) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub_hidden_metadata(item) for item in value)
    return value


class ObservationEnvelope(StrictModel):
    tool_name: str | None = None
    error: str | None = None
    timed_out: bool = False
    raw_output: Any = None
    parsed_output: Any = None
    required_fields: tuple[str, ...] = ()
    schema_valid: bool | None = None
    contradicts_previous: bool = False
    repeated_result_consistent: bool | None = None
    partial: bool = False
    impossible_value: bool = False
    observed_at: float | None = None
    reference_time: float | None = None
    max_staleness_seconds: float | None = Field(default=None, ge=0)
    evidence_count: int = Field(default=0, ge=0)
    minimum_evidence: int = Field(default=0, ge=0)
    insufficient_evidence: bool = False
    success_claimed: bool = False
    success_verifiable: bool = False
    candidate_answer: str | None = None
    clarification_possible: bool = False
    reported_token_budget_exhausted: bool = False
    reported_tool_budget_exhausted: bool = False
    reported_retry_budget_exhausted: bool = False
    infrastructure_failure: bool = False
    elapsed_seconds: float = Field(default=0.0, ge=0)

    @field_validator("raw_output", "parsed_output", mode="before")
    @classmethod
    def remove_hidden_metadata(cls, value: Any) -> Any:
        return scrub_hidden_metadata(value)

    @model_validator(mode="after")
    def reject_hidden_required_fields(self) -> ObservationEnvelope:
        hidden = [
            field for field in self.required_fields if _normalized_key(field) in FORBIDDEN_POLICY_KEYS
        ]
        if hidden:
            raise ValueError(f"required_fields cannot request hidden policy metadata: {hidden}")
        return self

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ObservationEnvelope:
        public = {key: payload[key] for key in _PUBLIC_FIELDS if key in payload}
        if "parsed_output" not in public and "output" in payload:
            public["parsed_output"] = payload["output"]
        if "raw_output" not in public and isinstance(payload.get("output"), str):
            public["raw_output"] = payload["output"]
        if "timed_out" not in public:
            public["timed_out"] = str(payload.get("error", "")).lower() == "timeout"
        return cls.model_validate(public)


_SIGNAL_PRIORITY = (
    AnomalySignal.INFRASTRUCTURE_FAILURE,
    AnomalySignal.EXHAUSTED_TOKEN_BUDGET,
    AnomalySignal.EXHAUSTED_TOOL_BUDGET,
    AnomalySignal.EXHAUSTED_RETRY_BUDGET,
    AnomalySignal.TIMEOUT,
    AnomalySignal.TOOL_ERROR,
    AnomalySignal.MALFORMED_OUTPUT,
    AnomalySignal.MISSING_REQUIRED_FIELD,
    AnomalySignal.SCHEMA_MISMATCH,
    AnomalySignal.CONTRADICTORY_OBSERVATION,
    AnomalySignal.INCONSISTENT_REPEATED_RESULT,
    AnomalySignal.STALE_TIMESTAMP,
    AnomalySignal.PARTIAL_OUTPUT,
    AnomalySignal.IMPOSSIBLE_VALUE,
    AnomalySignal.INSUFFICIENT_EVIDENCE,
    AnomalySignal.UNVERIFIABLE_SUCCESS_SIGNAL,
)


def detect_anomaly_signals(
    event: ObservationEnvelope,
    budgets: BudgetSnapshot | None = None,
) -> tuple[AnomalySignal, ...]:
    found: set[AnomalySignal] = set()
    if event.infrastructure_failure:
        found.add(AnomalySignal.INFRASTRUCTURE_FAILURE)
    if event.reported_token_budget_exhausted:
        found.add(AnomalySignal.EXHAUSTED_TOKEN_BUDGET)
    if event.reported_tool_budget_exhausted:
        found.add(AnomalySignal.EXHAUSTED_TOOL_BUDGET)
    if event.reported_retry_budget_exhausted:
        found.add(AnomalySignal.EXHAUSTED_RETRY_BUDGET)
    if event.timed_out:
        found.add(AnomalySignal.TIMEOUT)
    if event.error:
        found.add(AnomalySignal.TOOL_ERROR)
    if event.raw_output is not None and event.parsed_output is None and not event.error:
        found.add(AnomalySignal.MALFORMED_OUTPUT)
    if isinstance(event.parsed_output, Mapping):
        if any(field not in event.parsed_output for field in event.required_fields):
            found.add(AnomalySignal.MISSING_REQUIRED_FIELD)
    elif event.required_fields:
        found.add(AnomalySignal.MISSING_REQUIRED_FIELD)
    if event.schema_valid is False:
        found.add(AnomalySignal.SCHEMA_MISMATCH)
    if event.contradicts_previous:
        found.add(AnomalySignal.CONTRADICTORY_OBSERVATION)
    if event.repeated_result_consistent is False:
        found.add(AnomalySignal.INCONSISTENT_REPEATED_RESULT)
    if (
        event.observed_at is not None
        and event.reference_time is not None
        and event.max_staleness_seconds is not None
        and event.reference_time - event.observed_at > event.max_staleness_seconds
    ):
        found.add(AnomalySignal.STALE_TIMESTAMP)
    if event.partial:
        found.add(AnomalySignal.PARTIAL_OUTPUT)
    if event.impossible_value:
        found.add(AnomalySignal.IMPOSSIBLE_VALUE)
    if event.insufficient_evidence or event.evidence_count < event.minimum_evidence:
        found.add(AnomalySignal.INSUFFICIENT_EVIDENCE)
    if event.success_claimed and not event.success_verifiable:
        found.add(AnomalySignal.UNVERIFIABLE_SUCCESS_SIGNAL)
    if budgets is not None:
        if event.reported_token_budget_exhausted and budgets.tokens == 0:
            found.add(AnomalySignal.EXHAUSTED_TOKEN_BUDGET)
        if event.reported_tool_budget_exhausted and budgets.extra_tool_calls == 0:
            found.add(AnomalySignal.EXHAUSTED_TOOL_BUDGET)
        if event.reported_retry_budget_exhausted and budgets.retries == 0:
            found.add(AnomalySignal.EXHAUSTED_RETRY_BUDGET)
    return tuple(signal for signal in _SIGNAL_PRIORITY if signal in found)
