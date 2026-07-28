"""Agent/provider/open-model extension points for RAAC.

The hook layer is deliberately provider-neutral.  It accepts only sanitized
observation envelopes and emits typed control directives.  Provider and
open-model adapters can translate those directives into their native request
formats without receiving benchmark labels or evaluator metadata.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from causal_agent_bench.agents.base import BaseAgent, final_action, tool_action
from causal_agent_bench.raac.config import RAACRunConfig
from causal_agent_bench.raac.controller import RAACController
from causal_agent_bench.raac.signals import ObservationEnvelope
from causal_agent_bench.raac.types import DecisionKind, RAACDecision, RAACState
from causal_agent_bench.schemas import AgentAction, BenchmarkInstance, BenchmarkTask, ToolSpec


@runtime_checkable
class RAACDirectiveConsumer(Protocol):
    """Minimal contract implemented by future provider/open-model adapters."""

    def apply_raac_directive(
        self,
        decision: RAACDecision,
        *,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction | None:
        ...


@dataclass
class RAACControlHooks:
    controller: RAACController
    adapter_kind: str

    def inspect(self, payload: dict[str, Any] | ObservationEnvelope) -> RAACDecision:
        event = (
            payload
            if isinstance(payload, ObservationEnvelope)
            else ObservationEnvelope.from_payload(payload)
        )
        return self.controller.evaluate(event)

    def annotate(self, action: AgentAction, decision: RAACDecision) -> AgentAction:
        payload = action.model_dump(mode="python")
        metadata = dict(payload.get("metadata", {}))
        metadata.update(
            {
                "raac_state": decision.next_state.value,
                "raac_decision": decision.decision.value,
                "raac_signal": (
                    decision.trigger_signal.value if decision.trigger_signal is not None else None
                ),
                "raac_trace_index": decision.trace_index,
                "raac_evidence_class": decision.evidence_class,
            }
        )
        payload["metadata"] = metadata
        return AgentAction.model_validate(payload)

    def metadata(self) -> dict[str, Any]:
        return {
            **self.controller.metadata(),
            "adapter_kind": self.adapter_kind,
        }


class ProviderRAACAdapter(RAACControlHooks):
    def __init__(self, controller: RAACController) -> None:
        super().__init__(controller=controller, adapter_kind="provider")


class OpenModelRAACAdapter(RAACControlHooks):
    def __init__(self, controller: RAACController) -> None:
        super().__init__(controller=controller, adapter_kind="open_model")


class RAACAgentWrapper(BaseAgent):
    """Opt-in wrapper around the canonical ``BaseAgent`` interface.

    Same-tool retry and safe termination are enforced directly.  More
    provider-specific directives are offered to adapters through
    ``apply_raac_directive``; otherwise the wrapped agent chooses the concrete
    next action and the directive remains attached to the auditable trace.
    """

    name = "raac_agent_wrapper"

    def __init__(self, wrapped: BaseAgent, config: RAACRunConfig) -> None:
        super().__init__(seed=wrapped.seed)
        self.wrapped = wrapped
        self.config = config
        self.name = wrapped.name
        self.controller = RAACController.from_config(config)
        self._processed_steps = 0

    @property
    def model_name(self) -> str | None:
        value = getattr(self.wrapped, "model_name", None)
        return str(value) if value is not None else None

    def reset(self, instance: BenchmarkInstance | BenchmarkTask, seed: int | None = None) -> None:
        # The wrapped base agent receives the benchmark instance as usual.  The
        # RAAC wrapper deliberately does not retain it, so gold/intervention
        # fields cannot become controller inputs through inherited helpers.
        if seed is not None:
            self.seed = seed
        self.rng = random.Random(self.seed)
        self.instance = None
        self.legacy_task = None
        self.wrapped.reset(instance, seed=seed)
        self.controller = RAACController.from_config(self.config)
        self._processed_steps = 0

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        decision = self._inspect_newest_observation(observation_history)
        if decision is not None:
            if decision.decision == DecisionKind.RETRY_SAME_TOOL:
                retry = _last_tool_action(observation_history, available_tools)
                if retry is not None:
                    return self._annotate(retry, decision, applied=True)
            if decision.decision == DecisionKind.REQUEST_CLARIFICATION:
                action = final_action(
                    "I need clarification before I can provide a supported answer.",
                    thought="RAAC requested clarification from observable evidence.",
                )
                return self._annotate(action, decision, applied=True)
            if decision.decision == DecisionKind.ABSTAIN:
                action = final_action(
                    "I cannot provide a reliable answer from the available evidence.",
                    thought="RAAC abstained within its declared compute contract.",
                )
                return self._annotate(action, decision, applied=True)
            if decision.decision == DecisionKind.QUALIFIED_ANSWER:
                action = final_action(
                    "The available evidence is incomplete; any answer would be qualified.",
                    thought="RAAC exhausted a bounded recovery route.",
                )
                return self._annotate(action, decision, applied=True)
            if decision.decision == DecisionKind.TERMINATE_INFRASTRUCTURE_FAILURE:
                action = final_action(
                    "Execution terminated because the infrastructure failed.",
                    thought="RAAC distinguished infrastructure failure from agent failure.",
                )
                return self._annotate(action, decision, applied=True)
            if isinstance(self.wrapped, RAACDirectiveConsumer):
                controlled = self.wrapped.apply_raac_directive(
                    decision,
                    observation_history=observation_history,
                    available_tools=available_tools,
                )
                if controlled is not None:
                    return self._annotate(controlled, decision, applied=True)
        action = self.wrapped.act(observation_history, available_tools)
        if not isinstance(action, AgentAction):
            action = AgentAction.model_validate(action)
        if action.final_answer is not None:
            final_decision = self.controller.evaluate(
                ObservationEnvelope(
                    success_claimed=True,
                    success_verifiable=_history_supports_answer(observation_history),
                    candidate_answer=action.final_answer,
                    evidence_count=_successful_observation_count(observation_history),
                    minimum_evidence=1,
                )
            )
            if final_decision.decision == DecisionKind.FINAL_VERIFICATION:
                verifier = next(
                    (
                        tool
                        for tool in available_tools
                        if tool.is_available and tool.name == "verify_fact"
                    ),
                    None,
                )
                if verifier is not None:
                    verification = tool_action(
                        verifier.name,
                        _verification_arguments(
                            verifier,
                            claim=action.final_answer,
                            history=observation_history,
                        ),
                        thought="RAAC bounded final verification.",
                    )
                    return self._annotate(verification, final_decision, applied=True)
                final_decision = self.controller.evaluate(
                    ObservationEnvelope(
                        reported_tool_budget_exhausted=True,
                        insufficient_evidence=True,
                        candidate_answer=action.final_answer,
                    )
                )
            if final_decision.decision == DecisionKind.ABSTAIN:
                action = final_action(
                    "I cannot provide a reliable answer from the available evidence.",
                    thought="RAAC could not perform the required final verification.",
                )
            elif final_decision.decision == DecisionKind.QUALIFIED_ANSWER:
                action = final_action(
                    f"Qualified because final verification was unavailable: {action.final_answer}",
                    thought="RAAC preserved the candidate only as a qualified answer.",
                )
            return self._annotate(action, final_decision, applied=True)
        if decision is None:
            return action
        return self._annotate(action, decision, applied=decision.decision == DecisionKind.CONTINUE)

    def run_metadata(self) -> dict[str, Any]:
        if self.controller.machine.state in {RAACState.ANSWER, RAACState.ABSTAIN}:
            self.controller.finalize()
        elif self.controller.machine.state == RAACState.CLARIFY:
            # The non-interactive benchmark runner records the clarification
            # request as the terminal response. Interactive adapters may resume
            # from CLARIFY before requesting run metadata.
            self.controller.machine.transition(RAACState.TERMINATE)
        base: dict[str, Any] = {}
        if hasattr(self.wrapped, "run_metadata"):
            candidate = self.wrapped.run_metadata()
            if isinstance(candidate, dict):
                base.update(candidate)
        base["raac"] = self.controller.metadata()
        return base

    def _inspect_newest_observation(
        self,
        observation_history: list[dict[str, Any]],
    ) -> RAACDecision | None:
        if len(observation_history) <= self._processed_steps:
            return None
        decision: RAACDecision | None = None
        for step in observation_history[self._processed_steps :]:
            payload = _observation_payload(step)
            if payload is None:
                continue
            decision = self.controller.evaluate(payload)
            if decision.next_state.value in {"ANSWER", "ABSTAIN", "TERMINATE"}:
                break
        self._processed_steps = len(observation_history)
        return decision

    def _annotate(
        self,
        action: AgentAction,
        decision: RAACDecision,
        *,
        applied: bool,
    ) -> AgentAction:
        payload = action.model_dump(mode="python")
        metadata = dict(payload.get("metadata", {}))
        metadata.update(
            {
                "raac_state": decision.next_state.value,
                "raac_decision": decision.decision.value,
                "raac_signal": (
                    decision.trigger_signal.value if decision.trigger_signal is not None else None
                ),
                "raac_trace_index": decision.trace_index,
                "raac_directive_applied": applied,
                "recovery_marker": decision.decision
                in {
                    DecisionKind.RETRY_SAME_TOOL,
                    DecisionKind.USE_ALTERNATE_TOOL,
                    DecisionKind.CROSS_CHECK_SOURCE,
                    DecisionKind.VERIFY_CURRENT_EVIDENCE,
                    DecisionKind.FINAL_VERIFICATION,
                },
            }
        )
        payload["metadata"] = metadata
        return AgentAction.model_validate(payload)


def _observation_payload(step: dict[str, Any]) -> dict[str, Any] | None:
    observation = step.get("observation")
    if isinstance(observation, BaseModel):
        observation = observation.model_dump(mode="python")
    if not isinstance(observation, dict):
        return None
    output = observation.get("output")
    payload: dict[str, Any] = {
        "tool_name": observation.get("tool_name"),
        "error": observation.get("error"),
        "parsed_output": output,
    }
    metadata = observation.get("metadata")
    if isinstance(metadata, dict):
        for key in (
            "timed_out",
            "schema_valid",
            "contradicts_previous",
            "repeated_result_consistent",
            "partial",
            "impossible_value",
            "observed_at",
            "reference_time",
            "max_staleness_seconds",
            "insufficient_evidence",
            "clarification_possible",
            "infrastructure_failure",
        ):
            if key in metadata:
                payload[key] = metadata[key]
    if isinstance(output, dict):
        payload.setdefault("partial", output.get("partial") is True)
        payload["success_claimed"] = output.get("success") is True
        payload["success_verifiable"] = (
            payload["success_claimed"] and observation.get("error") is None
        )
        payload["evidence_count"] = 1 if observation.get("error") is None else 0
        payload["minimum_evidence"] = 1
    return payload


def _last_tool_action(
    history: list[dict[str, Any]],
    available_tools: list[ToolSpec],
) -> AgentAction | None:
    available = {tool.name for tool in available_tools if tool.is_available}
    for step in reversed(history):
        action = step.get("action")
        if isinstance(action, BaseModel):
            action = action.model_dump(mode="python")
        if not isinstance(action, dict):
            continue
        tool_call = action.get("tool_call")
        if not isinstance(tool_call, dict) or tool_call.get("tool_name") not in available:
            continue
        payload = dict(action)
        payload["thought"] = "RAAC bounded same-tool retry."
        payload["stop"] = False
        payload["final_answer"] = None
        return AgentAction.model_validate(payload)
    return None


def _successful_observation_count(history: list[dict[str, Any]]) -> int:
    count = 0
    for step in history:
        payload = _observation_payload(step)
        if payload is None or payload.get("error") is not None:
            continue
        if payload.get("partial") is True:
            continue
        count += 1
    return count


def _history_supports_answer(history: list[dict[str, Any]]) -> bool:
    if _successful_observation_count(history) == 0:
        return False
    for step in history:
        payload = _observation_payload(step)
        if payload is None:
            continue
        if payload.get("error") is not None or payload.get("partial") is True:
            return False
    return True


def _verification_arguments(
    tool: ToolSpec,
    *,
    claim: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    properties = tool.input_schema.get("properties", {})
    required = tool.input_schema.get("required", [])
    evidence_ids = [
        str(payload.get("tool_name"))
        for step in history
        if (payload := _observation_payload(step)) is not None and payload.get("tool_name")
    ]
    values: dict[str, Any] = {
        "claim": claim,
        "evidence_ids": evidence_ids,
    }
    arguments: dict[str, Any] = {}
    for name in required:
        schema = properties.get(name, {}) if isinstance(properties, dict) else {}
        if name in values:
            arguments[name] = values[name]
        elif schema.get("type") == "array":
            arguments[name] = []
        elif schema.get("type") in {"integer", "number"}:
            arguments[name] = 0
        elif schema.get("type") == "boolean":
            arguments[name] = False
        elif schema.get("type") == "object":
            arguments[name] = {}
        else:
            arguments[name] = claim
    return arguments
