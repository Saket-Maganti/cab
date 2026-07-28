"""Fail-closed typed state machine used by every RAAC policy."""

from __future__ import annotations

from pydantic import Field, model_validator

from causal_agent_bench.raac.types import RAACState, StrictModel

LEGAL_TRANSITIONS: dict[RAACState, frozenset[RAACState]] = {
    RAACState.PLAN: frozenset({RAACState.ACT, RAACState.TERMINATE}),
    RAACState.ACT: frozenset(
        {
            RAACState.VALIDATE_OBSERVATION,
            RAACState.FINAL_VERIFY,
            RAACState.ANSWER,
            RAACState.TERMINATE,
        }
    ),
    RAACState.VALIDATE_OBSERVATION: frozenset(
        {RAACState.DETECT_ANOMALY, RAACState.TERMINATE}
    ),
    RAACState.DETECT_ANOMALY: frozenset(
        {
            RAACState.ACT,
            RAACState.RETRY,
            RAACState.ALTERNATE_ROUTE,
            RAACState.CROSS_CHECK,
            RAACState.CLARIFY,
            RAACState.ABSTAIN,
            RAACState.FINAL_VERIFY,
            RAACState.ANSWER,
            RAACState.TERMINATE,
        }
    ),
    RAACState.RETRY: frozenset({RAACState.ACT, RAACState.ABSTAIN, RAACState.TERMINATE}),
    RAACState.ALTERNATE_ROUTE: frozenset(
        {RAACState.ACT, RAACState.CROSS_CHECK, RAACState.ABSTAIN, RAACState.TERMINATE}
    ),
    RAACState.CROSS_CHECK: frozenset(
        {RAACState.ACT, RAACState.ABSTAIN, RAACState.FINAL_VERIFY, RAACState.TERMINATE}
    ),
    RAACState.CLARIFY: frozenset(
        {RAACState.ACT, RAACState.ABSTAIN, RAACState.ANSWER, RAACState.TERMINATE}
    ),
    RAACState.ABSTAIN: frozenset({RAACState.TERMINATE}),
    RAACState.FINAL_VERIFY: frozenset(
        {
            RAACState.VALIDATE_OBSERVATION,
            RAACState.CROSS_CHECK,
            RAACState.ABSTAIN,
            RAACState.ANSWER,
            RAACState.TERMINATE,
        }
    ),
    RAACState.ANSWER: frozenset({RAACState.TERMINATE}),
    RAACState.TERMINATE: frozenset(),
}


class StateMachineCheckpoint(StrictModel):
    schema_version: str = "raac_state_machine_v1"
    current_state: RAACState
    history: list[RAACState] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_history(self) -> StateMachineCheckpoint:
        if self.history[0] != RAACState.PLAN:
            raise ValueError("RAAC state history must begin at PLAN")
        if self.history[-1] != self.current_state:
            raise ValueError("RAAC checkpoint current_state must match the history tail")
        for source, target in zip(self.history, self.history[1:], strict=False):
            if target not in LEGAL_TRANSITIONS[source]:
                raise ValueError(f"invalid RAAC checkpoint transition: {source} -> {target}")
        return self


class RAACStateMachine:
    def __init__(self) -> None:
        self._state = RAACState.PLAN
        self._history = [RAACState.PLAN]

    @property
    def state(self) -> RAACState:
        return self._state

    @property
    def history(self) -> tuple[RAACState, ...]:
        return tuple(self._history)

    @property
    def terminated(self) -> bool:
        return self._state == RAACState.TERMINATE

    def transition(self, target: RAACState) -> RAACState:
        if target not in LEGAL_TRANSITIONS[self._state]:
            raise ValueError(f"invalid RAAC transition: {self._state} -> {target}")
        self._state = target
        self._history.append(target)
        return target

    def checkpoint(self) -> StateMachineCheckpoint:
        return StateMachineCheckpoint(current_state=self._state, history=list(self._history))

    @classmethod
    def restore(cls, checkpoint: StateMachineCheckpoint | dict[str, object]) -> RAACStateMachine:
        record = StateMachineCheckpoint.model_validate(checkpoint)
        machine = cls()
        for target in record.history[1:]:
            machine.transition(target)
        return machine
