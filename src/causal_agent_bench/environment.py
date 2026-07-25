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
            self._sync_web_navigation_state(call.tool_name, observation)
        if action.final_answer is not None or action.stop:
            self.done = True
            self.final_answer = action.final_answer
            self.terminated_reason = "final_answer" if action.final_answer is not None else "agent_stop"

        action_payload = action.model_dump(mode="json")
        observation_payload = observation.model_dump(mode="json") if observation is not None else None
        tool_call_payload = (
            action.tool_call.model_dump(mode="json") if action.tool_call is not None else None
        )
        parsed_action = action.metadata.get("parsed_action")
        step_record = {
            "index": index,
            "step_index": index,
            "action": action_payload,
            "observation": observation_payload,
            "state": self._public_state_snapshot(),
            "raw_model_output": action.metadata.get("raw_model_output"),
            "parsed_action": parsed_action,
            "tool_call": tool_call_payload,
            "tool_arguments": dict(action.tool_call.arguments) if action.tool_call is not None else {},
            "tool_result": observation_payload,
            "parser_status": _parser_status(action.metadata, parsed_action),
            "tool_error_status": _tool_error_status(action.metadata, observation, action.tool_call is not None),
            "recovery_marker": action.metadata.get("recovery_marker"),
            "contradiction_marker": action.metadata.get("contradiction_marker"),
            "memory_use_marker": action.metadata.get("memory_use_marker"),
            "final_answer": action.final_answer,
            "stop_reason": self.terminated_reason if self.done else None,
            "token_cost_metadata": _token_cost_metadata(action.metadata),
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
                "task_id": self.instance.base_task.task_id,
                "condition": self.instance.condition,
                "base_task_id": self.instance.base_task.task_id,
                "intervention_family": self.instance.intervention.family
                if self.instance.intervention
                else None,
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
        knowledge_base = deepcopy(self.registry.knowledge_base)
        self._merge_task_knowledge_base(knowledge_base)
        state = {
            "instance_id": self.instance.instance_id,
            "base_task_id": self.instance.base_task.task_id,
            "condition": self.instance.condition,
            "available_tools": available_tools,
            "initial_memory": memory,
            "environment_seed": self.instance.environment_seed,
            "knowledge_base": knowledge_base,
            "tool_output_patch": tool_output_patch,
            "step_index": 0,
        }
        if self.instance.base_task.metadata.get("task_style") == "web_shadow":
            navigation = self.instance.base_task.hidden_ground_truth.get("navigation", {})
            state["current_url"] = navigation.get("start_url", "/")
            state["web_visited_urls"] = set()
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
        if intervention.family.startswith("web_"):
            state["web_intervention"] = intervention.family
        return state

    def _sync_web_navigation_state(self, tool_name: str, observation: ToolObservation | None) -> None:
        if not tool_name.startswith("web_") or observation is None or not observation.output:
            return
        output = observation.output
        url = output.get("url")
        if isinstance(url, str) and url:
            self.state["current_url"] = url
            visited = self.state.get("web_visited_urls")
            if isinstance(visited, set):
                visited.add(url)
            elif isinstance(visited, list):
                if url not in visited:
                    visited.append(url)
            else:
                self.state["web_visited_urls"] = {url}

    def _merge_task_knowledge_base(self, knowledge_base: dict[str, Any]) -> None:
        hidden = self.instance.base_task.hidden_ground_truth
        if hidden.get("web_site"):
            knowledge_base["web_snapshot"] = deepcopy(hidden["web_site"])
        api_mock = hidden.get("api_mock")
        if isinstance(api_mock, dict):
            for key, value in api_mock.items():
                knowledge_base[key] = deepcopy(value)

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
        index = len(self.steps)
        record = {
            "index": index,
            "step_index": index,
            "action": None,
            "observation": None,
            "state": self._public_state_snapshot() | {"done": True, "terminated_reason": "max_steps"},
            "raw_model_output": None,
            "parsed_action": None,
            "tool_call": None,
            "tool_arguments": {},
            "tool_result": None,
            "parser_status": "not_applicable",
            "tool_error_status": "not_applicable",
            "recovery_marker": None,
            "contradiction_marker": None,
            "memory_use_marker": None,
            "final_answer": None,
            "stop_reason": "max_steps",
            "token_cost_metadata": {},
        }
        self.steps.append(record)
        return record


def _parser_status(metadata: dict[str, Any], parsed_action: Any) -> str:
    if metadata.get("parser_outcome"):
        return str(metadata["parser_outcome"])
    if isinstance(parsed_action, dict) and parsed_action.get("outcome"):
        return str(parsed_action["outcome"])
    return "not_applicable"


def _tool_error_status(
    metadata: dict[str, Any],
    observation: ToolObservation | None,
    has_tool_call: bool,
) -> str:
    if metadata.get("invalid_action"):
        return "invalid_action"
    if observation is None:
        return "not_applicable" if not has_tool_call else "missing_observation"
    if observation.error:
        return "error"
    if observation.is_corrupted:
        return "corrupted"
    return "none"


def _token_cost_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "token_usage": metadata.get("token_usage"),
            "estimated_cost_usd": metadata.get("estimated_cost_usd"),
            "latency_s": metadata.get("latency_s"),
            "llm_calls": metadata.get("llm_calls"),
        }.items()
        if value is not None
    }


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
