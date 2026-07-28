"""Deterministic, bounded RAAC decision controller."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from causal_agent_bench.raac.config import RAACRunConfig
from causal_agent_bench.raac.contracts import ActionCost, ComputeContract, OverheadAccounting
from causal_agent_bench.raac.policy import comparison_contract, get_policy
from causal_agent_bench.raac.signals import ObservationEnvelope, detect_anomaly_signals
from causal_agent_bench.raac.state_machine import RAACStateMachine, StateMachineCheckpoint
from causal_agent_bench.raac.types import (
    AnomalySignal,
    BudgetSnapshot,
    ComparisonMode,
    ControlAction,
    DecisionKind,
    EvidenceClass,
    PolicyVariant,
    RAACDecision,
    RAACState,
    ReasonCode,
    StrictModel,
)

_RETRYABLE = frozenset(
    {
        AnomalySignal.TOOL_ERROR,
        AnomalySignal.TIMEOUT,
        AnomalySignal.MALFORMED_OUTPUT,
        AnomalySignal.MISSING_REQUIRED_FIELD,
        AnomalySignal.SCHEMA_MISMATCH,
        AnomalySignal.PARTIAL_OUTPUT,
        AnomalySignal.IMPOSSIBLE_VALUE,
    }
)
_CONTRADICTION = frozenset(
    {
        AnomalySignal.CONTRADICTORY_OBSERVATION,
        AnomalySignal.INCONSISTENT_REPEATED_RESULT,
    }
)
_VERIFY = frozenset(
    {
        AnomalySignal.STALE_TIMESTAMP,
        AnomalySignal.INSUFFICIENT_EVIDENCE,
        AnomalySignal.UNVERIFIABLE_SUCCESS_SIGNAL,
    }
)
_EXHAUSTED = frozenset(
    {
        AnomalySignal.EXHAUSTED_TOKEN_BUDGET,
        AnomalySignal.EXHAUSTED_TOOL_BUDGET,
        AnomalySignal.EXHAUSTED_RETRY_BUDGET,
    }
)

_ACTION_COSTS: dict[DecisionKind, ActionCost] = {
    DecisionKind.CONTINUE: ActionCost(),
    DecisionKind.RETRY_SAME_TOOL: ActionCost(extra_tool_calls=1, retries=1),
    DecisionKind.USE_ALTERNATE_TOOL: ActionCost(
        extra_model_calls=1, extra_tool_calls=1, alternate_routes=1, tokens=96
    ),
    DecisionKind.CROSS_CHECK_SOURCE: ActionCost(
        extra_model_calls=1, extra_tool_calls=1, verification_steps=1, tokens=96
    ),
    DecisionKind.VERIFY_CURRENT_EVIDENCE: ActionCost(
        extra_model_calls=1, extra_tool_calls=1, verification_steps=1, tokens=64
    ),
    DecisionKind.REQUEST_CLARIFICATION: ActionCost(
        extra_model_calls=1, clarification_steps=1, tokens=64
    ),
    DecisionKind.QUALIFIED_ANSWER: ActionCost(),
    DecisionKind.ABSTAIN: ActionCost(),
    DecisionKind.FINAL_VERIFICATION: ActionCost(
        extra_model_calls=1, extra_tool_calls=1, verification_steps=1, tokens=96
    ),
    DecisionKind.ANSWER: ActionCost(),
    DecisionKind.TERMINATE_INFRASTRUCTURE_FAILURE: ActionCost(),
}

_NEXT_STATE = {
    DecisionKind.CONTINUE: RAACState.ACT,
    DecisionKind.RETRY_SAME_TOOL: RAACState.RETRY,
    DecisionKind.USE_ALTERNATE_TOOL: RAACState.ALTERNATE_ROUTE,
    DecisionKind.CROSS_CHECK_SOURCE: RAACState.CROSS_CHECK,
    DecisionKind.VERIFY_CURRENT_EVIDENCE: RAACState.CROSS_CHECK,
    DecisionKind.REQUEST_CLARIFICATION: RAACState.CLARIFY,
    DecisionKind.QUALIFIED_ANSWER: RAACState.ANSWER,
    DecisionKind.ABSTAIN: RAACState.ABSTAIN,
    DecisionKind.FINAL_VERIFICATION: RAACState.FINAL_VERIFY,
    DecisionKind.ANSWER: RAACState.ANSWER,
    DecisionKind.TERMINATE_INFRASTRUCTURE_FAILURE: RAACState.TERMINATE,
}

_INSTRUCTIONS = {
    DecisionKind.CONTINUE: "Continue the wrapped agent without an extra RAAC action.",
    DecisionKind.RETRY_SAME_TOOL: "Retry the same observable tool call once.",
    DecisionKind.USE_ALTERNATE_TOOL: "Use an independent available route or tool.",
    DecisionKind.CROSS_CHECK_SOURCE: "Cross-check the conflicting observation with another source.",
    DecisionKind.VERIFY_CURRENT_EVIDENCE: "Verify the current evidence before relying on it.",
    DecisionKind.REQUEST_CLARIFICATION: "Request the minimum clarification needed to proceed.",
    DecisionKind.QUALIFIED_ANSWER: "Return an explicitly qualified answer limited to supported facts.",
    DecisionKind.ABSTAIN: "Abstain because observable evidence is insufficient for a safe answer.",
    DecisionKind.FINAL_VERIFICATION: "Perform one bounded final verification before answering.",
    DecisionKind.ANSWER: "Return the answer supported by the observable interaction evidence.",
    DecisionKind.TERMINATE_INFRASTRUCTURE_FAILURE: (
        "Terminate and label the trajectory as an infrastructure failure."
    ),
}


class ControllerCheckpoint(StrictModel):
    schema_version: str = "raac_controller_v1"
    variant: PolicyVariant
    comparison_mode: ComparisonMode
    policy_hash: str
    contract: ComputeContract
    state_machine: StateMachineCheckpoint
    remaining_budgets: BudgetSnapshot
    overhead: OverheadAccounting
    trace: list[RAACDecision] = Field(default_factory=list)
    evidence_class: EvidenceClass

    @model_validator(mode="after")
    def trace_indices_are_contiguous(self) -> ControllerCheckpoint:
        if [row.trace_index for row in self.trace] != list(range(len(self.trace))):
            raise ValueError("RAAC checkpoint trace indices must be contiguous")
        return self


class RAACController:
    def __init__(
        self,
        variant: PolicyVariant | str = PolicyVariant.RAAC_LIGHT,
        *,
        comparison_mode: ComparisonMode | str = ComparisonMode.PRACTICAL_BUDGET,
        equal_budget_contract: ComputeContract | None = None,
        evidence_class: EvidenceClass = "ENGINEERING_ONLY",
    ) -> None:
        self.policy = get_policy(variant)
        self.comparison_mode = ComparisonMode(comparison_mode)
        self.contract = comparison_contract(
            self.policy,
            self.comparison_mode,
            equal_budget_contract=equal_budget_contract,
        )
        self.evidence_class = evidence_class
        self.machine = RAACStateMachine()
        self._remaining = self.contract.initial_budget()
        self._overhead = OverheadAccounting()
        self._trace: list[RAACDecision] = []

    @classmethod
    def from_config(cls, config: RAACRunConfig) -> RAACController:
        return cls(
            config.variant,
            comparison_mode=config.comparison_mode,
            equal_budget_contract=config.equal_budget_contract,
            evidence_class=config.evidence_class,
        )

    @property
    def trace(self) -> tuple[RAACDecision, ...]:
        return tuple(self._trace)

    @property
    def remaining_budgets(self) -> BudgetSnapshot:
        return self._remaining.model_copy(deep=True)

    @property
    def overhead(self) -> OverheadAccounting:
        return self._overhead.model_copy(deep=True)

    @property
    def max_decisions(self) -> int:
        """Hard loop bound, including one initial decision and one terminal decision."""

        return (
            self.contract.max_retries
            + self.contract.max_alternate_routes
            + self.contract.max_verification_steps
            + self.contract.max_clarification_steps
            + 2
        )

    def evaluate(self, event: ObservationEnvelope | dict[str, Any]) -> RAACDecision:
        if self.machine.state in {RAACState.ABSTAIN, RAACState.ANSWER, RAACState.TERMINATE}:
            raise RuntimeError(f"cannot evaluate an event from terminal RAAC state {self.machine.state}")
        observation = (
            event if isinstance(event, ObservationEnvelope) else ObservationEnvelope.from_payload(event)
        )
        self._consume_elapsed(observation.elapsed_seconds)
        self._enter_detection()
        signals = detect_anomaly_signals(observation, self._remaining)
        decision, reason, trigger = self._select_decision(observation, signals)
        decision = self._fallback_if_unaffordable(decision, observation, trigger)
        if decision == DecisionKind.ABSTAIN:
            reason = ReasonCode.SAFE_ABSTENTION
        elif decision == DecisionKind.QUALIFIED_ANSWER:
            reason = ReasonCode.INSUFFICIENT_SUPPORT
        elif decision == DecisionKind.TERMINATE_INFRASTRUCTURE_FAILURE:
            reason = ReasonCode.INFRASTRUCTURE_FAILURE
        self._consume(_ACTION_COSTS[decision])
        current = self.machine.state
        target = _NEXT_STATE[decision]
        self.machine.transition(target)
        record = RAACDecision(
            decision=decision,
            reason_code=reason,
            current_state=current,
            next_state=target,
            trigger_signal=trigger,
            remaining_budgets=self.remaining_budgets,
            action=ControlAction(
                kind=decision,
                instruction=_INSTRUCTIONS[decision],
                parameters={"observable_signals": [signal.value for signal in signals]},
            ),
            trace_index=len(self._trace),
            evidence_class=self.evidence_class,
        )
        self._trace.append(record)
        return record

    def finalize(self) -> None:
        if self.machine.state == RAACState.TERMINATE:
            return
        if self.machine.state not in {RAACState.ABSTAIN, RAACState.ANSWER}:
            raise RuntimeError("RAAC can finalize only after ANSWER or ABSTAIN")
        self.machine.transition(RAACState.TERMINATE)

    def checkpoint(self) -> ControllerCheckpoint:
        return ControllerCheckpoint(
            variant=self.policy.variant,
            comparison_mode=self.comparison_mode,
            policy_hash=self.policy.policy_hash(),
            contract=self.contract,
            state_machine=self.machine.checkpoint(),
            remaining_budgets=self.remaining_budgets,
            overhead=self.overhead,
            trace=list(self._trace),
            evidence_class=self.evidence_class,
        )

    @classmethod
    def restore(
        cls,
        checkpoint: ControllerCheckpoint | dict[str, Any],
    ) -> RAACController:
        record = ControllerCheckpoint.model_validate(checkpoint)
        controller = cls(
            record.variant,
            comparison_mode=record.comparison_mode,
            equal_budget_contract=(
                record.contract if record.comparison_mode == ComparisonMode.EQUAL_BUDGET else None
            ),
            evidence_class=record.evidence_class,
        )
        if controller.policy.policy_hash() != record.policy_hash:
            raise ValueError("RAAC checkpoint policy hash mismatch")
        if controller.contract != record.contract:
            raise ValueError("RAAC checkpoint compute contract mismatch")
        controller.machine = RAACStateMachine.restore(record.state_machine)
        controller._remaining = record.remaining_budgets.model_copy(deep=True)
        controller._overhead = record.overhead.model_copy(deep=True)
        controller._trace = [row.model_copy(deep=True) for row in record.trace]
        if not controller._overhead.within(controller.contract):
            raise ValueError("RAAC checkpoint exceeds its compute contract")
        return controller

    def metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "raac_trace_v1",
            "enabled": True,
            "variant": self.policy.variant.value,
            "policy_hash": self.policy.policy_hash(),
            "comparison_mode": self.comparison_mode.value,
            "compute_contract": self.contract.model_dump(mode="json"),
            "remaining_budgets": self.remaining_budgets.model_dump(mode="json"),
            "overhead": self.overhead.model_dump(mode="json"),
            "current_state": self.machine.state.value,
            "state_history": [state.value for state in self.machine.history],
            "terminated": self.machine.terminated,
            "trace": [row.model_dump(mode="json") for row in self._trace],
            "evidence_class": self.evidence_class,
            "observable_signals_only": True,
            "hidden_metadata_access": False,
        }

    def _enter_detection(self) -> None:
        state = self.machine.state
        if state == RAACState.PLAN:
            self.machine.transition(RAACState.ACT)
            state = self.machine.state
        if state in {
            RAACState.RETRY,
            RAACState.ALTERNATE_ROUTE,
            RAACState.CROSS_CHECK,
            RAACState.CLARIFY,
        }:
            self.machine.transition(RAACState.ACT)
            state = self.machine.state
        if state == RAACState.ACT:
            self.machine.transition(RAACState.VALIDATE_OBSERVATION)
            state = self.machine.state
        if state == RAACState.FINAL_VERIFY:
            self.machine.transition(RAACState.VALIDATE_OBSERVATION)
            state = self.machine.state
        if state != RAACState.VALIDATE_OBSERVATION:
            raise RuntimeError(f"cannot validate an observation from RAAC state {state}")
        self.machine.transition(RAACState.DETECT_ANOMALY)

    def _select_decision(
        self,
        event: ObservationEnvelope,
        signals: tuple[AnomalySignal, ...],
    ) -> tuple[DecisionKind, ReasonCode, AnomalySignal | None]:
        if not signals:
            if event.success_claimed and event.success_verifiable:
                return DecisionKind.ANSWER, ReasonCode.OBSERVABLE_SUCCESS, None
            return DecisionKind.CONTINUE, ReasonCode.NO_ANOMALY, None
        trigger = signals[0]
        signal_set = set(signals)
        if len(self._trace) >= self.max_decisions - 1:
            terminal = (
                DecisionKind.ABSTAIN
                if self.policy.enable_abstention
                else DecisionKind.QUALIFIED_ANSWER
            )
            return terminal, ReasonCode.BUDGET_EXHAUSTED, trigger
        if AnomalySignal.INFRASTRUCTURE_FAILURE in signal_set:
            return (
                DecisionKind.TERMINATE_INFRASTRUCTURE_FAILURE,
                ReasonCode.INFRASTRUCTURE_FAILURE,
                AnomalySignal.INFRASTRUCTURE_FAILURE,
            )
        if signal_set & _EXHAUSTED:
            if event.candidate_answer and event.evidence_count >= event.minimum_evidence:
                return DecisionKind.QUALIFIED_ANSWER, ReasonCode.BUDGET_EXHAUSTED, trigger
            return DecisionKind.ABSTAIN, ReasonCode.BUDGET_EXHAUSTED, trigger
        if self.policy.abstain_on_any_anomaly:
            return DecisionKind.ABSTAIN, ReasonCode.POLICY_ABLATION, trigger
        if signal_set & _CONTRADICTION:
            if self.policy.enable_cross_check:
                return (
                    DecisionKind.CROSS_CHECK_SOURCE,
                    ReasonCode.CONTRADICTION_REQUIRES_CROSS_CHECK,
                    trigger,
                )
            if self.policy.enable_verification:
                return (
                    DecisionKind.VERIFY_CURRENT_EVIDENCE,
                    ReasonCode.EVIDENCE_REQUIRES_VERIFICATION,
                    trigger,
                )
            return self._terminal_for_evidence(event, trigger)
        if trigger == AnomalySignal.INSUFFICIENT_EVIDENCE:
            if self.policy.enable_clarification and event.clarification_possible:
                return (
                    DecisionKind.REQUEST_CLARIFICATION,
                    ReasonCode.CLARIFICATION_CAN_RESOLVE,
                    trigger,
                )
            if self.policy.enable_verification:
                return (
                    DecisionKind.VERIFY_CURRENT_EVIDENCE,
                    ReasonCode.EVIDENCE_REQUIRES_VERIFICATION,
                    trigger,
                )
            return self._terminal_for_evidence(event, trigger)
        if trigger == AnomalySignal.UNVERIFIABLE_SUCCESS_SIGNAL:
            if self.policy.enable_final_verify:
                return (
                    DecisionKind.FINAL_VERIFICATION,
                    ReasonCode.PREMATURE_SUCCESS_REQUIRES_VERIFICATION,
                    trigger,
                )
            if self.policy.enable_verification:
                return (
                    DecisionKind.VERIFY_CURRENT_EVIDENCE,
                    ReasonCode.EVIDENCE_REQUIRES_VERIFICATION,
                    trigger,
                )
            return self._terminal_for_evidence(event, trigger)
        if signal_set & _RETRYABLE:
            if self.policy.enable_retry:
                return DecisionKind.RETRY_SAME_TOOL, ReasonCode.TRANSIENT_FAILURE, trigger
            if self.policy.enable_alternate_route:
                return (
                    DecisionKind.USE_ALTERNATE_TOOL,
                    ReasonCode.ALTERNATE_ROUTE_AVAILABLE,
                    trigger,
                )
            if self.policy.enable_verification:
                return (
                    DecisionKind.VERIFY_CURRENT_EVIDENCE,
                    ReasonCode.EVIDENCE_REQUIRES_VERIFICATION,
                    trigger,
                )
            return self._terminal_for_evidence(event, trigger)
        if signal_set & _VERIFY and self.policy.enable_verification:
            return (
                DecisionKind.VERIFY_CURRENT_EVIDENCE,
                ReasonCode.EVIDENCE_REQUIRES_VERIFICATION,
                trigger,
            )
        return self._terminal_for_evidence(event, trigger)

    def _terminal_for_evidence(
        self,
        event: ObservationEnvelope,
        trigger: AnomalySignal,
    ) -> tuple[DecisionKind, ReasonCode, AnomalySignal]:
        if self.policy.enable_abstention:
            return DecisionKind.ABSTAIN, ReasonCode.SAFE_ABSTENTION, trigger
        if event.candidate_answer:
            return DecisionKind.QUALIFIED_ANSWER, ReasonCode.INSUFFICIENT_SUPPORT, trigger
        return DecisionKind.CONTINUE, ReasonCode.POLICY_ABLATION, trigger

    def _fallback_if_unaffordable(
        self,
        decision: DecisionKind,
        event: ObservationEnvelope,
        trigger: AnomalySignal | None,
    ) -> DecisionKind:
        if self._can_afford(_ACTION_COSTS[decision]):
            return decision
        if decision == DecisionKind.RETRY_SAME_TOOL and self.policy.enable_alternate_route:
            alternate = _ACTION_COSTS[DecisionKind.USE_ALTERNATE_TOOL]
            if self._can_afford(alternate):
                return DecisionKind.USE_ALTERNATE_TOOL
        if self.policy.enable_abstention:
            return DecisionKind.ABSTAIN
        if event.candidate_answer:
            return DecisionKind.QUALIFIED_ANSWER
        if trigger == AnomalySignal.INFRASTRUCTURE_FAILURE:
            return DecisionKind.TERMINATE_INFRASTRUCTURE_FAILURE
        return DecisionKind.CONTINUE

    def _can_afford(self, cost: ActionCost) -> bool:
        remaining = self._remaining
        requires_compute = any(getattr(cost, field) > 0 for field in ActionCost.model_fields)
        return (
            cost.extra_model_calls <= remaining.extra_model_calls
            and cost.extra_tool_calls <= remaining.extra_tool_calls
            and cost.retries <= remaining.retries
            and cost.alternate_routes <= remaining.alternate_routes
            and cost.verification_steps <= remaining.verification_steps
            and cost.clarification_steps <= remaining.clarification_steps
            and cost.tokens <= remaining.tokens
            and (not requires_compute or remaining.wall_clock_seconds > 0)
        )

    def _consume(self, cost: ActionCost) -> None:
        if not self._can_afford(cost):
            raise RuntimeError("RAAC attempted to exceed its declared compute contract")
        values = self._remaining.model_dump(mode="python")
        overhead = self._overhead.model_dump(mode="python")
        for field in ActionCost.model_fields:
            amount = getattr(cost, field)
            values[field if field != "extra_model_calls" else "extra_model_calls"] -= amount
            overhead[field] += amount
        self._remaining = BudgetSnapshot.model_validate(values)
        self._overhead = OverheadAccounting.model_validate(overhead)

    def _consume_elapsed(self, seconds: float) -> None:
        if seconds <= 0:
            return
        values = self._remaining.model_dump(mode="python")
        charged = min(seconds, values["wall_clock_seconds"])
        values["wall_clock_seconds"] = max(0.0, values["wall_clock_seconds"] - charged)
        self._remaining = BudgetSnapshot.model_validate(values)
        overhead = self._overhead.model_dump(mode="python")
        overhead["wall_clock_seconds"] += charged
        self._overhead = OverheadAccounting.model_validate(overhead)
