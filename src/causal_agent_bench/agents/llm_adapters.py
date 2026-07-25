from __future__ import annotations

from typing import Any

from causal_agent_bench.agents.llm_agents import DirectToolAgent


class OpenAIChatAgent(DirectToolAgent):
    name = "openai_chat_agent"
    provider_default = "openai"
    model_default = "set-via-config-or-env"


class AnthropicAgent(DirectToolAgent):
    name = "anthropic_agent"
    provider_default = "anthropic"
    model_default = "set-via-config-or-env"


class GeminiAgent(DirectToolAgent):
    name = "gemini_agent"
    provider_default = "gemini"
    model_default = "set-via-config-or-env"


class OpenRouterAgent(DirectToolAgent):
    name = "openrouter_agent"
    provider_default = "openrouter"
    model_default = "set-via-config-or-env"


class LocalHFChatAgent(DirectToolAgent):
    """Placeholder-compatible local chat adapter.

    This keeps the earlier public name available. It intentionally does not
    load a Hugging Face model by default because the smoke/test path must remain
    lightweight and deterministic.
    """

    name = "local_hf_chat_agent"
    provider_default = "local_stub"
    model_default = "local-hf-placeholder"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
