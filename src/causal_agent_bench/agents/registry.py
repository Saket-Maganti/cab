from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.base import BaseAgent
from causal_agent_bench.agents.greedy_tool_agent import GreedyToolAgent
from causal_agent_bench.agents.llm_adapters import (
    AnthropicAgent,
    GeminiAgent,
    LocalHFChatAgent,
    OpenAIChatAgent,
)
from causal_agent_bench.agents.planner_executor_stub_agent import PlannerExecutorStubAgent
from causal_agent_bench.agents.random_tool_agent import RandomToolAgent
from causal_agent_bench.agents.react_stub_agent import ReActStyleStubAgent
from causal_agent_bench.agents.scripted_oracle_agent import ScriptedOracleAgent

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    agent.name: agent
    for agent in [
        RandomToolAgent,
        ScriptedOracleAgent,
        GreedyToolAgent,
        ReActStyleStubAgent,
        PlannerExecutorStubAgent,
        OpenAIChatAgent,
        AnthropicAgent,
        GeminiAgent,
        LocalHFChatAgent,
    ]
}

ALIASES = {
    "RandomToolAgent": "random_tool_agent",
    "ScriptedOracleAgent": "scripted_oracle_agent",
    "GreedyToolAgent": "greedy_tool_agent",
    "ReActStyleStubAgent": "react_stub_agent",
    "ReactStyleStubAgent": "react_stub_agent",
    "PlannerExecutorStubAgent": "planner_executor_stub_agent",
    "OpenAIChatAgent": "openai_chat_agent",
    "AnthropicAgent": "anthropic_agent",
    "GeminiAgent": "gemini_agent",
    "LocalHFChatAgent": "local_hf_chat_agent",
}


def get_agent(name: str, **kwargs: Any) -> BaseAgent:
    canonical = ALIASES.get(name, name)
    if canonical not in AGENT_REGISTRY:
        available = ", ".join(list_agents())
        raise ValueError(f"unknown agent {name!r}; available agents: {available}")
    return AGENT_REGISTRY[canonical](**kwargs)


def make_agent(name: str, **kwargs: Any) -> BaseAgent:
    return get_agent(name, **kwargs)


def list_agents() -> list[str]:
    return sorted(AGENT_REGISTRY)
