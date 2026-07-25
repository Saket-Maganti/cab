from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.base import (
    BaseAgent,
    default_tool_arguments,
    final_action,
    tool_action,
)
from causal_agent_bench.schemas import AgentAction, ToolSpec


class RandomToolAgent(BaseAgent):
    name = "random_tool_agent"

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        usable_tools = [tool for tool in available_tools if tool.is_available]
        if not usable_tools or (observation_history and self.rng.random() < 0.35):
            return final_action(
                "Unable to determine from the available evidence.",
                thought="Random lower-bound agent stops.",
            )
        tool = self.rng.choice(usable_tools)
        arguments = default_tool_arguments(tool.name, self.user_instruction(), self.domain(), self)
        return tool_action(tool.name, arguments, thought="Randomly selected an available tool.")
