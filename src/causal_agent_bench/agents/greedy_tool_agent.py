from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.base import BaseAgent, final_action, tool_action
from causal_agent_bench.schemas import AgentAction, ToolSpec


class GreedyToolAgent(BaseAgent):
    name = "greedy_tool_agent"

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        called = set(self.called_tools(observation_history))
        instruction = self.user_instruction().lower()
        if self.has_error(observation_history) and "verify_fact" not in called:
            verifier = self.tool_by_name(available_tools, "verify_fact")
            if verifier is not None:
                return tool_action(
                    "verify_fact",
                    self.tool_arguments("verify_fact", verifier),
                    thought="Greedy heuristic switches to verification after a tool error.",
                )
        priority = _keyword_plan(instruction, self.domain())
        for tool_name in priority:
            tool_spec = self.tool_by_name(available_tools, tool_name)
            if tool_spec is not None and tool_name not in called:
                return tool_action(
                    tool_name,
                    self.tool_arguments(tool_name, tool_spec),
                    thought=f"Greedy heuristic selected {tool_name}.",
                )
        return final_action(
            "I used the available tools and provide the best answer supported by the observations.",
            thought="No remaining heuristic tool appears necessary.",
        )


def _keyword_plan(instruction: str, domain: str) -> list[str]:
    if "calendar" in instruction or "email" in instruction or "calendar" in domain:
        return ["check_calendar", "send_email_draft"]
    if "policy" in instruction or "approval" in instruction or "compliance" in domain:
        return ["lookup_policy", "verify_fact"]
    if "hotel" in instruction or "travel" in domain:
        return ["search_database", "compare_options", "calculate_price"]
    if "spreadsheet" in instruction or "revenue" in instruction:
        return ["read_file", "query_spreadsheet"]
    if "price" in instruction or "compare" in instruction:
        return ["compare_options", "calculate_price"]
    return ["search_database"]
