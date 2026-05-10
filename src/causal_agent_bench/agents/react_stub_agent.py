from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.base import BaseAgent, final_action, tool_action
from causal_agent_bench.agents.greedy_tool_agent import _keyword_plan
from causal_agent_bench.schemas import AgentAction, ToolSpec


class ReActStyleStubAgent(BaseAgent):
    name = "react_stub_agent"

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        called = self.called_tools(observation_history)
        if self.has_error(observation_history) and "verify_fact" not in called:
            tool_spec = self.tool_by_name(available_tools, "verify_fact")
            if tool_spec is not None:
                return tool_action(
                    "verify_fact",
                    self.tool_arguments("verify_fact", tool_spec),
                    thought="Thought: a tool failed, so I should verify the key claim before answering.",
                )
        plan = _keyword_plan(self.user_instruction().lower(), self.domain())
        for tool_name in plan:
            tool_spec = self.tool_by_name(available_tools, tool_name)
            if tool_spec is not None and tool_name not in called:
                return tool_action(
                    tool_name,
                    self.tool_arguments(tool_name, tool_spec),
                    thought=f"Thought: I need evidence from {tool_name}. Action: call the tool.",
                )
        return final_action(
            "Based on the observations, I have enough information to answer.",
            thought="Thought: combine observations into a final answer.",
        )
