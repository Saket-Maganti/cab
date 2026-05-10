from __future__ import annotations

import os
from typing import Any

from causal_agent_bench.agents.base import BaseAgent
from causal_agent_bench.schemas import AgentAction, ToolSpec


class LLMAdapterAgent(BaseAgent):
    provider_name = "generic"
    env_key_name: str | None = None

    def __init__(
        self,
        system_prompt: str = "You are a careful tool-using agent.",
        max_steps: int = 8,
        temperature: float = 0.0,
        seed: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(seed=seed, **kwargs)
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.temperature = temperature

    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        key_hint = f" Set {self.env_key_name} and install the provider SDK." if self.env_key_name else ""
        if self.env_key_name and not os.getenv(self.env_key_name):
            raise RuntimeError(f"{self.name} is an interface placeholder only.{key_hint}")
        raise RuntimeError(
            f"{self.name} is an interface placeholder for {self.provider_name}; no provider SDK call is implemented yet."
        )


class OpenAIChatAgent(LLMAdapterAgent):
    name = "openai_chat_agent"
    provider_name = "OpenAI-style chat"
    env_key_name = "OPENAI_API_KEY"


class AnthropicAgent(LLMAdapterAgent):
    name = "anthropic_agent"
    provider_name = "Anthropic-style chat"
    env_key_name = "ANTHROPIC_API_KEY"


class GeminiAgent(LLMAdapterAgent):
    name = "gemini_agent"
    provider_name = "Gemini-style chat"
    env_key_name = "GEMINI_API_KEY"


class LocalHFChatAgent(LLMAdapterAgent):
    name = "local_hf_chat_agent"
    provider_name = "local Hugging Face chat"
    env_key_name = None
