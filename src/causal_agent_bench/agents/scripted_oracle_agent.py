from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.base import BaseAgent, final_action, tool_action
from causal_agent_bench.schemas import AgentAction, ToolSpec


class ScriptedOracleAgent(BaseAgent):
    name = "scripted_oracle_agent"
    uses_hidden_information = True

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        called = self.called_tools(observation_history)
        sequence = self.gold_tool_sequence()
        for tool_name in sequence:
            if tool_name not in called:
                tool_spec = self.tool_by_name(available_tools, tool_name)
                if tool_spec is None:
                    continue
                return tool_action(
                    tool_name,
                    self.tool_arguments(tool_name, tool_spec, observation_history),
                    thought=f"Oracle follows gold tool sequence and calls {tool_name}.",
                )
        return final_action(
            self.expected_answer(),
            thought="Oracle uses hidden expected-answer metadata. This is an upper-bound sanity check.",
        )
