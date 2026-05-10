from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.base import BaseAgent, final_action, tool_action
from causal_agent_bench.agents.greedy_tool_agent import _keyword_plan
from causal_agent_bench.schemas import AgentAction, ToolSpec


class PlannerExecutorStubAgent(BaseAgent):
    name = "planner_executor_stub_agent"

    def __init__(self, seed: int = 0, **kwargs: Any) -> None:
        super().__init__(seed=seed, **kwargs)
        self.plan: list[str] = []

    def reset(self, instance, seed: int | None = None) -> None:
        super().reset(instance, seed=seed)
        if self.legacy_task is not None:
            self.plan = self.gold_tool_sequence() or _keyword_plan(
                self.user_instruction().lower(),
                self.domain(),
            )
            return
        self.plan = _keyword_plan(self.user_instruction().lower(), self.domain())

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        called = self.called_tools(observation_history)
        if self.has_error(observation_history):
            revised = [tool for tool in ["verify_fact", "search_database"] if tool not in called]
            self.plan = revised + [tool for tool in self.plan if tool not in revised]
        for tool_name in self.plan:
            tool_spec = self.tool_by_name(available_tools, tool_name)
            if tool_spec is not None and tool_name not in called:
                return tool_action(
                    tool_name,
                    self.tool_arguments(tool_name, tool_spec),
                    thought=f"Planner step {len(called) + 1}: execute {tool_name}.",
                )
        return final_action(
            "Plan complete; final answer should be synthesized from the collected observations.",
            thought="Executor completed the current plan.",
        )
