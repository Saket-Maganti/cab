"""Typed public contracts for Recovery-Aware Agent Control (RAAC)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EvidenceClass = Literal[
    "DESIGN_ONLY",
    "ENGINEERING_ONLY",
    "FIXTURE_ONLY",
    "HUMAN_INPUT_REQUIRED",
    "EXECUTION_PENDING",
    "PRELIMINARY_REAL_EVIDENCE",
    "AUDITED_REAL_EVIDENCE",
    "PAPER_ELIGIBLE_EVIDENCE",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RAACState(StrEnum):
    PLAN = "PLAN"
    ACT = "ACT"
    VALIDATE_OBSERVATION = "VALIDATE_OBSERVATION"
    DETECT_ANOMALY = "DETECT_ANOMALY"
    RETRY = "RETRY"
    ALTERNATE_ROUTE = "ALTERNATE_ROUTE"
    CROSS_CHECK = "CROSS_CHECK"
    CLARIFY = "CLARIFY"
    ABSTAIN = "ABSTAIN"
    FINAL_VERIFY = "FINAL_VERIFY"
    ANSWER = "ANSWER"
    TERMINATE = "TERMINATE"


class AnomalySignal(StrEnum):
    TOOL_ERROR = "tool_error"
    TIMEOUT = "timeout"
    MALFORMED_OUTPUT = "malformed_output"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    SCHEMA_MISMATCH = "schema_mismatch"
    CONTRADICTORY_OBSERVATION = "contradictory_observation"
    STALE_TIMESTAMP = "stale_timestamp"
    INCONSISTENT_REPEATED_RESULT = "inconsistent_repeated_result"
    PARTIAL_OUTPUT = "partial_output"
    IMPOSSIBLE_VALUE = "impossible_value"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNVERIFIABLE_SUCCESS_SIGNAL = "unverifiable_success_signal"
    EXHAUSTED_TOKEN_BUDGET = "exhausted_token_budget"
    EXHAUSTED_TOOL_BUDGET = "exhausted_tool_budget"
    EXHAUSTED_RETRY_BUDGET = "exhausted_retry_budget"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"


class DecisionKind(StrEnum):
    CONTINUE = "continue"
    RETRY_SAME_TOOL = "retry_same_tool"
    USE_ALTERNATE_TOOL = "use_alternate_tool"
    CROSS_CHECK_SOURCE = "cross_check_source"
    VERIFY_CURRENT_EVIDENCE = "verify_current_evidence"
    REQUEST_CLARIFICATION = "request_clarification"
    QUALIFIED_ANSWER = "qualified_answer"
    ABSTAIN = "abstain"
    FINAL_VERIFICATION = "final_verification"
    ANSWER = "answer"
    TERMINATE_INFRASTRUCTURE_FAILURE = "terminate_infrastructure_failure"


class ReasonCode(StrEnum):
    NO_ANOMALY = "no_anomaly"
    OBSERVABLE_SUCCESS = "observable_success"
    TRANSIENT_FAILURE = "transient_failure"
    RETRY_EXHAUSTED = "retry_exhausted"
    ALTERNATE_ROUTE_AVAILABLE = "alternate_route_available"
    CONTRADICTION_REQUIRES_CROSS_CHECK = "contradiction_requires_cross_check"
    EVIDENCE_REQUIRES_VERIFICATION = "evidence_requires_verification"
    CLARIFICATION_CAN_RESOLVE = "clarification_can_resolve"
    INSUFFICIENT_SUPPORT = "insufficient_support"
    SAFE_ABSTENTION = "safe_abstention"
    PREMATURE_SUCCESS_REQUIRES_VERIFICATION = "premature_success_requires_verification"
    BUDGET_EXHAUSTED = "budget_exhausted"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    POLICY_ABLATION = "policy_ablation"
    TERMINAL_STATE = "terminal_state"


class PolicyVariant(StrEnum):
    RAAC_LIGHT = "RAAC_LIGHT"
    RAAC_FULL = "RAAC_FULL"
    VERIFY_ONLY = "VERIFY_ONLY"
    RETRY_ONLY = "RETRY_ONLY"
    ABSTAIN_ONLY = "ABSTAIN_ONLY"
    NO_CROSS_CHECK = "NO_CROSS_CHECK"
    NO_ALTERNATE_ROUTE = "NO_ALTERNATE_ROUTE"
    NO_FINAL_VERIFY = "NO_FINAL_VERIFY"
    DIRECT_ANSWER = "DIRECT_ANSWER"
    STANDARD_TOOL_USE = "STANDARD_TOOL_USE"
    REACT_STYLE = "REACT_STYLE"
    SELF_CHECK = "SELF_CHECK"
    ORACLE_ENGINEERING_ONLY = "ORACLE_ENGINEERING_ONLY"


class ComparisonMode(StrEnum):
    EQUAL_BUDGET = "equal_budget"
    PRACTICAL_BUDGET = "practical_budget"


class BudgetSnapshot(StrictModel):
    extra_model_calls: int = Field(ge=0)
    extra_tool_calls: int = Field(ge=0)
    retries: int = Field(ge=0)
    alternate_routes: int = Field(ge=0)
    verification_steps: int = Field(ge=0)
    clarification_steps: int = Field(ge=0)
    tokens: int = Field(ge=0)
    wall_clock_seconds: float = Field(ge=0)


class ControlAction(StrictModel):
    kind: DecisionKind
    instruction: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class RAACDecision(StrictModel):
    decision: DecisionKind
    reason_code: ReasonCode
    current_state: RAACState
    next_state: RAACState
    trigger_signal: AnomalySignal | None = None
    remaining_budgets: BudgetSnapshot
    action: ControlAction
    trace_index: int = Field(ge=0)
    evidence_class: EvidenceClass
