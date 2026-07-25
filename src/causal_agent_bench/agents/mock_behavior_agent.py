from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.base import BaseAgent, final_action, tool_action
from causal_agent_bench.agents.greedy_tool_agent import _keyword_plan
from causal_agent_bench.schemas import AgentAction, ToolSpec

MOCK_BEHAVIOR_MODES = frozenset(
    {
        "helpful",
        "brittle",
        "tool_overuser",
        "memory_blind",
        "contradiction_blind",
        "premature_stop",
        "premature_stopper",
        "recovery_weak",
        "argument_sloppy",
        "final_answer_hallucinator",
        "retry_loop_agent",
    }
)

EXPECTED_FAILURE_CATEGORY: dict[str, str] = {
    "premature_stop": "premature_stop",
    "premature_stopper": "premature_stop",
    "contradiction_blind": "contradiction_blind",
    "memory_blind": "memory_blind",
    "argument_sloppy": "argument_sloppy",
    "recovery_weak": "recovery_weak",
    "tool_overuser": "tool_overuser",
    "final_answer_hallucinator": "final_answer_hallucination",
    "retry_loop_agent": "retry_loop",
    "brittle": "brittle_stop",
    "helpful": "none",
}


class MockBehaviorAgent(BaseAgent):
    """Deterministic engineering-only agent with configurable failure modes.

    No LLM, API, or Ollama calls. Useful for fast trajectory/scoring/analysis tests.
    """

    name = "mock_behavior_agent"

    def __init__(self, *, mock_behavior: str = "helpful", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        mode = mock_behavior or "helpful"
        if mode not in MOCK_BEHAVIOR_MODES:
            allowed = ", ".join(sorted(MOCK_BEHAVIOR_MODES))
            raise ValueError(f"unknown mock_behavior {mode!r}; expected one of: {allowed}")
        self.mock_behavior = mode

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        called = self.called_tools(observation_history)
        mode = self.mock_behavior
        if mode == "premature_stopper":
            mode = "premature_stop"

        if mode == "final_answer_hallucinator":
            return final_action(
                "The benchmark answer is definitely 42 with full causal certainty.",
                thought="Mock: hallucinated final answer without evidence.",
            )

        if mode == "retry_loop_agent":
            if available_tools:
                tool_spec = available_tools[0]
                return tool_action(
                    tool_spec.name,
                    self.tool_arguments(tool_spec.name, tool_spec),
                    thought=f"Mock: retry loop on {tool_spec.name}.",
                )
            return final_action("Retry loop with no tools.", thought="Mock: retry_loop_agent.")

        if mode == "premature_stop":
            return final_action(
                "Premature final answer without enough evidence.",
                thought="Mock: stopping early.",
            )

        if mode == "memory_blind" and called:
            return final_action(
                "Final answer ignoring prior tool observations.",
                thought="Mock: memory-blind stop.",
            )

        if mode == "contradiction_blind":
            if self.has_error(observation_history):
                return final_action(
                    "Everything is consistent despite tool errors.",
                    thought="Mock: contradiction-blind.",
                )

        if mode == "tool_overuser":
            for tool_spec in available_tools:
                if tool_spec.name not in called:
                    return tool_action(
                        tool_spec.name,
                        self.tool_arguments(tool_spec.name, tool_spec),
                        thought=f"Mock: overusing {tool_spec.name}.",
                    )
            return final_action("Used all tools.", thought="Mock: tool overuser done.")

        if mode == "brittle":
            if self.has_error(observation_history):
                return final_action(
                    "Failed because a tool errored.",
                    thought="Mock: brittle stop on first error.",
                )

        if mode == "recovery_weak":
            if self.has_error(observation_history):
                return final_action(
                    "Giving up after tool error without recovery.",
                    thought="Mock: weak recovery — no alternate tool or verification.",
                )
            plan = _keyword_plan(self.user_instruction().lower(), self.domain())
            for tool_name in plan:
                tool_spec = self.tool_by_name(available_tools, tool_name)
                if tool_spec is not None and tool_name not in called:
                    return tool_action(
                        tool_name,
                        self.tool_arguments(tool_name, tool_spec),
                        thought=f"Mock recovery_weak: call {tool_name}.",
                    )
            return final_action("Done without verifying errors.", thought="Mock: recovery_weak.")

        if mode == "argument_sloppy":
            for tool_spec in available_tools:
                if tool_spec.name not in called:
                    return tool_action(
                        tool_spec.name,
                        {"__invalid__": True, "query": ""},
                        thought=f"Mock: sloppy arguments for {tool_spec.name}.",
                    )
            return final_action("Used tools with bad args.", thought="Mock: argument_sloppy done.")

        if self.has_error(observation_history) and "verify_fact" not in called:
            tool_spec = self.tool_by_name(available_tools, "verify_fact")
            if tool_spec is not None:
                return tool_action(
                    "verify_fact",
                    self.tool_arguments("verify_fact", tool_spec),
                    thought="Mock helpful: verify after error.",
                )

        plan = _keyword_plan(self.user_instruction().lower(), self.domain())
        for tool_name in plan:
            tool_spec = self.tool_by_name(available_tools, tool_name)
            if tool_spec is not None and tool_name not in called:
                return tool_action(
                    tool_name,
                    self.tool_arguments(tool_name, tool_spec),
                    thought=f"Mock helpful: call {tool_name}.",
                )

        return final_action(
            "Mock helpful final answer based on observations.",
            thought="Mock helpful: enough evidence.",
        )
