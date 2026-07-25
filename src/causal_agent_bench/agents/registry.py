from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.base import BaseAgent
from causal_agent_bench.agents.greedy_tool_agent import GreedyToolAgent
from causal_agent_bench.agents.llm_adapters import (
    AnthropicAgent,
    GeminiAgent,
    LocalHFChatAgent,
    OpenAIChatAgent,
    OpenRouterAgent,
)
from causal_agent_bench.agents.llm_agents import (
    DirectLLMToolAgent,
    DirectToolAgent,
    MemoryVerifyingLLMAgent,
    PlannerExecutorAgent,
    PlannerExecutorLLMAgent,
    ReActStyleLLMAgent,
    RecoveryPromptLLMAgent,
    SelfCheckAgent,
    SelfCheckingLLMAgent,
    ToolConservativeLLMAgent,
)
from causal_agent_bench.agents.mock_behavior_agent import MockBehaviorAgent
from causal_agent_bench.agents.planner_executor_stub_agent import PlannerExecutorStubAgent
from causal_agent_bench.agents.random_tool_agent import RandomToolAgent
from causal_agent_bench.agents.react_stub_agent import ReActStyleStubAgent
from causal_agent_bench.agents.scripted_oracle_agent import ScriptedOracleAgent

_AGENT_CLASSES: list[type[BaseAgent]] = [
    RandomToolAgent,
    ScriptedOracleAgent,
    GreedyToolAgent,
    ReActStyleStubAgent,
    PlannerExecutorStubAgent,
    OpenAIChatAgent,
    AnthropicAgent,
    GeminiAgent,
    OpenRouterAgent,
    LocalHFChatAgent,
    DirectToolAgent,
    DirectLLMToolAgent,
    ReActStyleLLMAgent,
    PlannerExecutorAgent,
    PlannerExecutorLLMAgent,
    SelfCheckAgent,
    SelfCheckingLLMAgent,
    MemoryVerifyingLLMAgent,
    RecoveryPromptLLMAgent,
    ToolConservativeLLMAgent,
    MockBehaviorAgent,
]

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {agent.name: agent for agent in _AGENT_CLASSES}

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
    "OpenRouterAgent": "openrouter_agent",
    "LocalHFChatAgent": "local_hf_chat_agent",
    "DirectToolAgent": "direct_tool_agent",
    "DirectLLMToolAgent": "direct_llm_tool_agent",
    "ReActStyleLLMAgent": "react_style_llm_agent",
    "ReactStyleLLMAgent": "react_style_llm_agent",
    "PlannerExecutorAgent": "planner_executor_agent",
    "PlannerExecutorLLMAgent": "planner_executor_llm_agent",
    "SelfCheckAgent": "self_check_agent",
    "SelfCheckingLLMAgent": "self_checking_llm_agent",
    "MemoryVerifyingLLMAgent": "memory_verifying_llm_agent",
    "RecoveryPromptLLMAgent": "recovery_prompt_llm_agent",
    "ToolConservativeLLMAgent": "tool_conservative_llm_agent",
    "MockBehaviorAgent": "mock_behavior_agent",
    "react_llm_agent": "react_style_llm_agent",
    "self_check_llm_agent": "self_checking_llm_agent",
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
