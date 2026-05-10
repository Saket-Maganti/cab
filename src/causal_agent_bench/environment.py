from __future__ import annotations

from copy import deepcopy
from typing import Any

from causal_agent_bench.metrics.components import final_answer_correctness
from causal_agent_bench.schemas import (
    AgentAction,
    BenchmarkInstance,
    BenchmarkTask,
    ToolObservation,
    Trajectory,
    TrajectoryStep,
)
from causal_agent_bench.tools import ToolRegistry


class BenchmarkEnvironment:
    """Deterministic environment for Prompt 04 BenchmarkInstance records."""

    def __init__(
        self,
        instance: BenchmarkInstance,
        run_id: str = "adhoc",
        agent_name: str = "unknown_agent",
        model_name: str | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.instance = instance
        self.run_id = run_id
        self.agent_name = agent_name
        self.model_name = model_name
        self.registry = registry or ToolRegistry()
        self.max_steps = instance.base_task.max_steps
        self.steps: list[dict[str, Any]] = []
        self.done = False
        self.final_answer: str | None = None
        self.terminated_reason = "running"
        self.state = self._initial_state()

    @property
    def available_tools(self) -> list[str]:
        return list(self.state["available_tools"])

    def step(self, action: AgentAction) -> dict[str, Any]:
        if self.done:
            raise RuntimeError("environment is already terminated")
        if len(self.steps) >= self.max_steps:
            self.done = True
            self.terminated_reason = "max_steps"
            return self._max_step_record()

        index = len(self.steps)
        self.state["step_index"] = index
        observation: ToolObservation | None = None
        if action.tool_call is not None:
            call = action.tool_call
            call_id = call.call_id or f"{self.instance.instance_id}:{index}"
            self.state["current_call_id"] = call_id
            observation = self.registry.call(call.tool_name, call.arguments, self.state, call_id=call_id)
        if action.final_answer is not None or action.stop:
            self.done = True
            self.final_answer = action.final_answer
            self.terminated_reason = "final_answer" if action.final_answer is not None else "agent_stop"

        step_record = {
            "index": index,
            "action": action.model_dump(mode="json"),
            "observation": observation.model_dump(mode="json") if observation is not None else None,
            "state": self._public_state_snapshot(),
        }
        self.steps.append(step_record)
        if len(self.steps) >= self.max_steps and not self.done:
            self.done = True
            self.terminated_reason = "max_steps"
        return step_record

    def trajectory(self) -> Trajectory:
        return Trajectory(
            run_id=self.run_id,
            instance_id=self.instance.instance_id,
            agent_name=self.agent_name,
            model_name=self.model_name,
            steps=self.steps,
            final_answer=self.final_answer,
            terminated_reason=self.terminated_reason,
            metadata={
                "condition": self.instance.condition,
                "base_task_id": self.instance.base_task.task_id,
                "environment_seed": self.instance.environment_seed,
                "intervention_id": self.instance.intervention.intervention_id
                if self.instance.intervention
                else None,
            },
        )

    def _initial_state(self) -> dict[str, Any]:
        available_tools = list(self.instance.available_tools)
        memory = deepcopy(self.instance.initial_memory)
        tool_output_patch: dict[str, Any] = {}
        state = {
            "instance_id": self.instance.instance_id,
            "base_task_id": self.instance.base_task.task_id,
            "condition": self.instance.condition,
            "available_tools": available_tools,
            "initial_memory": memory,
            "environment_seed": self.instance.environment_seed,
            "knowledge_base": deepcopy(self.registry.knowledge_base),
            "tool_output_patch": tool_output_patch,
            "step_index": 0,
        }
        intervention = self.instance.intervention
        if intervention is None:
            return state

        for removed in intervention.tool_availability_patch.get("removed_tools", []):
            state["available_tools"] = [tool for tool in state["available_tools"] if tool != removed]
        for added in intervention.tool_availability_patch.get("added_tools", []):
            if added not in state["available_tools"]:
                state["available_tools"].append(added)
        if intervention.memory_patch:
            state["initial_memory"].update(deepcopy(intervention.memory_patch))
        if intervention.tool_output_patch:
            state["tool_output_patch"] = deepcopy(intervention.tool_output_patch)
        if intervention.family == "observation_conflict":
            state["conflicting_observation_tools"] = list(self.instance.base_task.gold_tool_sequence or [])[:1]
            state["conflicting_observation"] = intervention.tool_output_patch.get(
                "conflicting_observation",
                {"source_a": "approved", "source_b": "denied"},
            )
        if intervention.family == "premature_success_signal":
            state["premature_success_signal"] = intervention.tool_output_patch.get(
                "premature_completion_message",
                "Looks complete before all required evidence has been gathered.",
            )
        if intervention.instruction_patch:
            state["instruction_patch"] = intervention.instruction_patch
        return state

    def _public_state_snapshot(self) -> dict[str, Any]:
        snapshot = {
            "available_tools": list(self.state["available_tools"]),
            "step_index": self.state.get("step_index"),
            "done": self.done,
        }
        for key in ["premature_success_signal", "instruction_patch"]:
            if key in self.state:
                snapshot[key] = self.state[key]
        return snapshot

    def _max_step_record(self) -> dict[str, Any]:
        record = {
            "index": len(self.steps),
            "action": None,
            "observation": None,
            "state": self._public_state_snapshot() | {"done": True, "terminated_reason": "max_steps"},
        }
        self.steps.append(record)
        return record


class SimulatedEnvironment:
    """Compatibility environment for the earlier BenchmarkTask smoke prototype."""

    def __init__(self, task: BenchmarkTask, seed: int = 0, max_steps: int = 8) -> None:
        self.task = task
        self.seed = seed
        self.max_steps = max_steps
        self.registry = ToolRegistry()
        self.steps: list[TrajectoryStep] = []
        self.done = False
        self.final_answer: str | None = None
        self.success: bool | None = None

    def step(self, action: AgentAction) -> TrajectoryStep:
        if self.done:
            raise RuntimeError("environment is already done")
        index = len(self.steps)
        if index >= self.max_steps:
            self.done = True
            self.success = False
            raise RuntimeError("maximum steps exceeded")

        observation: ToolObservation | None = None
        state = {
            "available_tools": list(self.task.available_tools),
            "done": False,
        }
        if action.kind == "tool_call":
            call = action.tool_call
            assert call is not None
            call_id = call.call_id or f"{self.task.task_id}:{index}"
            observation = self.registry.call(call.tool_name, call.arguments, self.task, call_id=call_id)
            state["last_tool_ok"] = observation.ok
            if (
                self.task.intervention is not None
                and self.task.intervention.family == "premature_success_signal"
                and index == 0
            ):
                state["environment_signal"] = self.task.mock_data.get("environment_signals", {}).get(
                    "premature_completion_message"
                )
        else:
            self.final_answer = action.final_answer
            self.done = True
            self.success = bool(final_answer_correctness(self.task, action.final_answer or ""))
            state["done"] = True
            state["success"] = self.success

        step = TrajectoryStep(index=index, action=action, observation=observation, state=state)
        self.steps.append(step)
        if len(self.steps) >= self.max_steps and not self.done:
            self.done = True
            self.success = False
        return step
