from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.schemas import ToolSpec

MessageRole = Literal["system", "user", "assistant", "tool"]
_UNSET = object()


@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_openai(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name:
            payload["name"] = self.name
        if self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        return payload


@dataclass(frozen=True)
class LLMToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str | None = None


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def as_dict(self) -> dict[str, int | None]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout: float = 60.0
    retry_count: int = 2
    seed: int | None = None
    json_mode: bool = True
    pricing: dict[str, float] = field(default_factory=dict)
    base_url: str | None = None
    api_key_env: str | tuple[str, ...] | None = None
    cache_dir: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    content: str | None = None
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    model_name: str | None = None
    provider_name: str | None = None
    latency_s: float | None = None
    estimated_cost_usd: float | None = None
    retries: int = 0
    response_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMClient(Protocol):
    provider_name: str

    def complete(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        config: ModelConfig,
    ) -> LLMResponse:
        ...

    def is_configured(self) -> bool:
        ...


@dataclass(frozen=True)
class ProviderSpec:
    """Provider metadata that is safe to log.

    API key values are deliberately not represented here; only environment
    variable names and endpoint hints are exposed.
    """

    name: str
    api_key_env: tuple[str, ...] = ()
    default_base_url: str | None = None
    base_url_env: str | None = None
    requires_api_key: bool = True
    openai_compatible: bool = False


class ProviderError(RuntimeError):
    """Base class for provider failures that can be logged without secrets."""


class ProviderConfigurationError(ProviderError):
    """Raised when an LLM provider cannot run because local configuration is missing."""


class ProviderRequestError(ProviderError):
    """Raised when an LLM provider request fails after retries."""


class ProviderRateLimitError(ProviderRequestError):
    """Raised when a provider reports rate limiting."""


class ProviderContextLengthError(ProviderRequestError):
    """Raised when a request is too large for the provider context window."""


class ProviderMalformedResponseError(ProviderRequestError):
    """Raised when a provider response cannot be parsed into the expected shape."""


class LocalStubLLMClient:
    """Deterministic fake client for tests and dry-run plumbing checks.

    This client is not a model baseline and must not be treated as scientific
    evidence. It simply returns scripted responses or a tiny deterministic
    fallback so the tool loop can be tested without API keys.
    """

    provider_name = "local_stub"

    def __init__(
        self,
        responses: Sequence[LLMResponse | dict[str, Any]] | None = None,
        *,
        repeat_last: bool = False,
    ) -> None:
        self._responses = [self._coerce_response(response) for response in responses or []]
        self._repeat_last = repeat_last
        self._index = 0

    def is_configured(self) -> bool:
        return True

    def complete(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        config: ModelConfig,
    ) -> LLMResponse:
        start = time.perf_counter()
        if self._responses:
            if self._index < len(self._responses):
                response = self._responses[self._index]
                self._index += 1
            elif self._repeat_last:
                response = self._responses[-1]
            else:
                response = LLMResponse(content='{"final_answer": "Stub completed.", "stop": true}')
        else:
            response = _default_stub_response(messages, tools)
        usage = response.usage
        if usage.total_tokens is None:
            usage = TokenUsage(
                input_tokens=0 if usage.input_tokens is None else usage.input_tokens,
                output_tokens=0 if usage.output_tokens is None else usage.output_tokens,
                total_tokens=0,
            )
        return LLMResponse(
            content=response.content,
            tool_calls=response.tool_calls,
            usage=usage,
            model_name=config.model,
            provider_name=self.provider_name,
            latency_s=round(time.perf_counter() - start, 6),
            estimated_cost_usd=0.0,
            retries=0,
            response_id=response.response_id,
            metadata={**response.metadata, "stub": True},
        )

    def _coerce_response(self, response: LLMResponse | dict[str, Any]) -> LLMResponse:
        if isinstance(response, LLMResponse):
            return response
        tool_calls = [
            LLMToolCall(
                name=tool_call["name"],
                arguments=dict(tool_call.get("arguments", {})),
                call_id=tool_call.get("call_id"),
            )
            for tool_call in response.get("tool_calls", [])
        ]
        usage_payload = response.get("usage", {})
        return LLMResponse(
            content=response.get("content"),
            tool_calls=tool_calls,
            usage=TokenUsage(
                input_tokens=usage_payload.get("input_tokens"),
                output_tokens=usage_payload.get("output_tokens"),
                total_tokens=usage_payload.get("total_tokens"),
            ),
            metadata=dict(response.get("metadata", {})),
        )


class _HTTPClientBase:
    provider_name = "http"
    api_key_env: str | tuple[str, ...] = ""
    endpoint: str = ""
    base_url_env: str | None = None
    requires_api_key = True

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def is_configured(self) -> bool:
        has_endpoint = bool(self.endpoint or self._configured_base_url(None))
        has_key = bool(self._api_key(None))
        return has_endpoint and (has_key or not self.requires_api_key)

    def complete(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        config: ModelConfig,
    ) -> LLMResponse:
        api_key = self._api_key(config)
        endpoint = self.endpoint_for(config)
        if not endpoint:
            raise ProviderConfigurationError(
                f"{self.provider_name} is not configured; set base_url or "
                f"{self.base_url_env or 'the provider base URL'}"
            )
        if self.requires_api_key and not api_key:
            env_names = ", ".join(_env_names(config.api_key_env or self.api_key_env))
            raise ProviderConfigurationError(
                f"{self.provider_name} is not configured; set {env_names}"
            )
        payload = self._payload(messages, tools, config)
        headers = self._headers(api_key or "", config)
        start = time.perf_counter()
        retries = 0
        last_error: Exception | None = None
        for attempt in range(config.retry_count + 1):
            retries = attempt
            try:
                raw = _post_json(endpoint, payload, headers, config.timeout)
                try:
                    response = self._parse_response(raw, config)
                except Exception as exc:
                    raise ProviderMalformedResponseError(
                        f"{self.provider_name} returned an unsupported response shape: {exc}"
                    ) from exc
                usage = response.usage
                cost = estimate_cost_usd(usage, config.pricing)
                return LLMResponse(
                    content=response.content,
                    tool_calls=response.tool_calls,
                    usage=usage,
                    model_name=response.model_name or config.model,
                    provider_name=self.provider_name,
                    latency_s=round(time.perf_counter() - start, 6),
                    estimated_cost_usd=cost,
                    retries=retries,
                    response_id=response.response_id,
                    metadata={
                        **response.metadata,
                        "provider_error_class": None,
                        "endpoint_host": _endpoint_host(endpoint),
                    },
                )
            except Exception as exc:
                last_error = exc
                if attempt >= config.retry_count:
                    break
                time.sleep(min(2.0, 0.25 * (2**attempt)))
        raise ProviderRequestError(
            f"{self.provider_name} request failed after {retries + 1} attempt(s): {last_error}"
        ) from last_error

    def endpoint_for(self, config: ModelConfig) -> str:
        configured = self._configured_base_url(config)
        if configured:
            return _normalize_chat_completions_endpoint(configured)
        return self.endpoint

    def _api_key(self, config: ModelConfig | None) -> str | None:
        if self.api_key:
            return self.api_key
        env_spec = config.api_key_env if config is not None and config.api_key_env else self.api_key_env
        for name in _env_names(env_spec):
            value = os.getenv(name)
            if value:
                return value
        return None

    def _configured_base_url(self, config: ModelConfig | None) -> str | None:
        if config is not None and config.base_url:
            return config.base_url
        if self.base_url_env:
            return os.getenv(self.base_url_env) or None
        return None

    def _payload(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        config: ModelConfig,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def _headers(self, api_key: str, config: ModelConfig) -> dict[str, str]:
        raise NotImplementedError

    def _parse_response(self, payload: dict[str, Any], config: ModelConfig) -> LLMResponse:
        raise NotImplementedError


class OpenAIClient(_HTTPClientBase):
    provider_name = "openai"
    api_key_env = "OPENAI_API_KEY"
    endpoint = "https://api.openai.com/v1/chat/completions"

    def _payload(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        config: ModelConfig,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": [message.as_openai() for message in messages],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if config.seed is not None:
            payload["seed"] = config.seed
        if config.json_mode:
            payload["response_format"] = {"type": "json_object"}
        if tools:
            payload["tools"] = [_openai_tool(tool) for tool in tools if tool.is_available]
            payload["tool_choice"] = "auto"
        payload.update(config.extra)
        return payload

    def _headers(self, api_key: str, config: ModelConfig) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _parse_response(self, payload: dict[str, Any], config: ModelConfig) -> LLMResponse:
        choice = payload.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = []
        for tool_call in message.get("tool_calls", []) or []:
            function = tool_call.get("function", {})
            tool_calls.append(
                LLMToolCall(
                    name=function.get("name", ""),
                    arguments=_parse_json_object(function.get("arguments")),
                    call_id=tool_call.get("id"),
                )
            )
        usage = payload.get("usage", {})
        return LLMResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            usage=TokenUsage(
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
            model_name=payload.get("model"),
            response_id=payload.get("id"),
            metadata={"finish_reason": choice.get("finish_reason")},
        )


class OpenRouterClient(OpenAIClient):
    provider_name = "openrouter"
    api_key_env = "OPENROUTER_API_KEY"
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def _headers(self, api_key: str, config: ModelConfig) -> dict[str, str]:
        headers = super()._headers(api_key, config)
        headers["HTTP-Referer"] = config.extra.get("http_referer", "https://github.com")
        headers["X-Title"] = config.extra.get("x_title", "CausalAgentBench")
        return headers


class OpenAICompatibleClient(OpenAIClient):
    """Generic OpenAI-compatible chat/completions adapter."""

    provider_name = "openai_compatible"
    api_key_env = "OPENAI_COMPATIBLE_API_KEY"
    endpoint = ""
    base_url_env = "OPENAI_COMPATIBLE_BASE_URL"


class LocalOpenAICompatibleClient(OpenAICompatibleClient):
    """Local open-weight server through an OpenAI-compatible API.

    Many local servers do not require API keys; if one does, set
    `LOCAL_OPENAI_API_KEY` or pass `api_key_env` in the model config.
    """

    provider_name = "local_openai"
    api_key_env = "LOCAL_OPENAI_API_KEY"
    endpoint = "http://localhost:8000/v1/chat/completions"
    base_url_env = "LOCAL_OPENAI_BASE_URL"
    requires_api_key = False


class AnthropicClient(_HTTPClientBase):
    provider_name = "anthropic"
    api_key_env = "ANTHROPIC_API_KEY"
    endpoint = "https://api.anthropic.com/v1/messages"

    def _payload(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        config: ModelConfig,
    ) -> dict[str, Any]:
        system_parts = [message.content for message in messages if message.role == "system"]
        chat_messages = [
            {"role": message.role if message.role != "tool" else "user", "content": message.content}
            for message in messages
            if message.role != "system"
        ]
        payload: dict[str, Any] = {
            "model": config.model,
            "system": "\n\n".join(system_parts),
            "messages": chat_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if tools:
            payload["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in tools
                if tool.is_available
            ]
        payload.update(config.extra)
        return payload

    def _headers(self, api_key: str, config: ModelConfig) -> dict[str, str]:
        return {
            "x-api-key": api_key,
            "anthropic-version": config.extra.get("anthropic_version", "2023-06-01"),
            "Content-Type": "application/json",
        }

    def _parse_response(self, payload: dict[str, Any], config: ModelConfig) -> LLMResponse:
        content_parts: list[str] = []
        tool_calls: list[LLMToolCall] = []
        for block in payload.get("content", []) or []:
            if block.get("type") == "text":
                content_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    LLMToolCall(
                        name=block.get("name", ""),
                        arguments=dict(block.get("input", {})),
                        call_id=block.get("id"),
                    )
                )
        usage = payload.get("usage", {})
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total = None
        if input_tokens is not None or output_tokens is not None:
            total = int(input_tokens or 0) + int(output_tokens or 0)
        return LLMResponse(
            content="\n".join(part for part in content_parts if part),
            tool_calls=tool_calls,
            usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total),
            model_name=payload.get("model"),
            response_id=payload.get("id"),
            metadata={"stop_reason": payload.get("stop_reason")},
        )


class GeminiClient(_HTTPClientBase):
    provider_name = "gemini"
    api_key_env = ("GOOGLE_API_KEY", "GEMINI_API_KEY")

    def endpoint_for(self, config: ModelConfig) -> str:
        configured = self._configured_base_url(config)
        if configured:
            return _normalize_gemini_endpoint(configured, config.model, self._api_key(config))
        return (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{config.model}:generateContent?key={self._api_key(config)}"
        )

    def _payload(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        config: ModelConfig,
    ) -> dict[str, Any]:
        system_parts = [message.content for message in messages if message.role == "system"]
        contents = [
            {
                "role": "model" if message.role == "assistant" else "user",
                "parts": [{"text": message.content}],
            }
            for message in messages
            if message.role != "system"
        ]
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens,
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
        if tools:
            payload["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.input_schema,
                        }
                        for tool in tools
                        if tool.is_available
                    ]
                }
            ]
        payload.update(config.extra)
        return payload

    def _headers(self, api_key: str, config: ModelConfig) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def _parse_response(self, payload: dict[str, Any], config: ModelConfig) -> LLMResponse:
        candidate = payload.get("candidates", [{}])[0]
        parts = candidate.get("content", {}).get("parts", []) or []
        content_parts: list[str] = []
        tool_calls: list[LLMToolCall] = []
        for part in parts:
            if "text" in part:
                content_parts.append(part["text"])
            if "functionCall" in part:
                call = part["functionCall"]
                tool_calls.append(
                    LLMToolCall(
                        name=call.get("name", ""),
                        arguments=dict(call.get("args", {})),
                    )
                )
        usage = payload.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount")
        output_tokens = usage.get("candidatesTokenCount")
        total = usage.get("totalTokenCount")
        return LLMResponse(
            content="\n".join(part for part in content_parts if part),
            tool_calls=tool_calls,
            usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total),
            model_name=config.model,
            metadata={"finish_reason": candidate.get("finishReason")},
        )


PROVIDER_SPECS: dict[str, ProviderSpec] = {
    "local_stub": ProviderSpec(name="local_stub", requires_api_key=False),
    "openai": ProviderSpec(
        name="openai",
        api_key_env=("OPENAI_API_KEY",),
        default_base_url=OpenAIClient.endpoint,
        openai_compatible=True,
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        api_key_env=("ANTHROPIC_API_KEY",),
        default_base_url=AnthropicClient.endpoint,
    ),
    "gemini": ProviderSpec(
        name="gemini",
        api_key_env=("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        default_base_url="https://generativelanguage.googleapis.com/v1beta",
    ),
    "openrouter": ProviderSpec(
        name="openrouter",
        api_key_env=("OPENROUTER_API_KEY",),
        default_base_url=OpenRouterClient.endpoint,
        openai_compatible=True,
    ),
    "openai_compatible": ProviderSpec(
        name="openai_compatible",
        api_key_env=("OPENAI_COMPATIBLE_API_KEY",),
        base_url_env="OPENAI_COMPATIBLE_BASE_URL",
        openai_compatible=True,
    ),
    "local_openai": ProviderSpec(
        name="local_openai",
        api_key_env=("LOCAL_OPENAI_API_KEY",),
        default_base_url=LocalOpenAICompatibleClient.endpoint,
        base_url_env="LOCAL_OPENAI_BASE_URL",
        requires_api_key=False,
        openai_compatible=True,
    ),
}


PROVIDER_CLIENTS: dict[str, type[LLMClient]] = {
    "local_stub": LocalStubLLMClient,
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "gemini": GeminiClient,
    "openrouter": OpenRouterClient,
    "openai_compatible": OpenAICompatibleClient,
    "local_openai": LocalOpenAICompatibleClient,
}


def get_llm_client(provider: str) -> LLMClient:
    if provider not in PROVIDER_CLIENTS:
        available = ", ".join(sorted(PROVIDER_CLIENTS))
        raise ValueError(f"unknown LLM provider {provider!r}; available providers: {available}")
    return PROVIDER_CLIENTS[provider]()


def list_provider_status() -> list[dict[str, Any]]:
    rows = []
    for name in sorted(PROVIDER_CLIENTS):
        client = get_llm_client(name)
        spec = PROVIDER_SPECS.get(name)
        env_vars = spec.api_key_env if spec else getattr(client, "api_key_env", ())
        base_url_env = spec.base_url_env if spec else getattr(client, "base_url_env", None)
        rows.append(
            {
                "provider": name,
                "configured": client.is_configured(),
                "env_vars": list(_env_names(env_vars)),
                "base_url_env": base_url_env,
                "base_url_configured": bool(os.getenv(base_url_env)) if base_url_env else None,
                "requires_api_key": spec.requires_api_key if spec else True,
                "openai_compatible": spec.openai_compatible if spec else False,
            }
        )
    return rows


def estimate_cost_usd(usage: TokenUsage, pricing: dict[str, float]) -> float | None:
    if not pricing:
        return None
    input_rate = pricing.get("input_per_1m_tokens")
    output_rate = pricing.get("output_per_1m_tokens")
    if input_rate is None and output_rate is None:
        return None
    input_cost = ((usage.input_tokens or 0) / 1_000_000) * float(input_rate or 0.0)
    output_cost = ((usage.output_tokens or 0) / 1_000_000) * float(output_rate or 0.0)
    return round(input_cost + output_cost, 8)


class DiskLLMCache:
    """Small JSON cache for provider responses.

    Cache entries intentionally contain hashes and responses only. They never
    include API keys.
    """

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> LLMResponse | None:
        path = self._path(key)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _response_from_payload(payload["response"])

    def set(self, key: str, response: LLMResponse, metadata: dict[str, Any]) -> None:
        payload = {
            "cache_key": key,
            "metadata": metadata,
            "response": _response_to_payload(response),
        }
        self._path(key).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"


class CachingLLMClient:
    """Wrap an LLM client with deterministic disk caching."""

    def __init__(self, wrapped: LLMClient, cache_dir: str | Path) -> None:
        self.wrapped = wrapped
        self.cache = DiskLLMCache(cache_dir)
        self.provider_name = wrapped.provider_name

    def is_configured(self) -> bool:
        return self.wrapped.is_configured()

    def complete(
        self,
        messages: list[Message],
        tools: list[ToolSpec],
        config: ModelConfig,
    ) -> LLMResponse:
        parts = cache_key_parts(messages, tools, config)
        cached = self.cache.get(parts["cache_key"])
        if cached is not None:
            return _with_response_metadata(
                cached,
                {
                    **parts,
                    "cache_hit": True,
                    "cached_original_estimated_cost_usd": cached.estimated_cost_usd,
                },
                estimated_cost_usd=0.0,
                latency_s=0.0,
            )
        response = self.wrapped.complete(messages, tools, config)
        response = _with_response_metadata(response, {**parts, "cache_hit": False})
        self.cache.set(parts["cache_key"], response, parts)
        return response


def cache_key_parts(
    messages: list[Message],
    tools: list[ToolSpec],
    config: ModelConfig,
) -> dict[str, Any]:
    prompt_hash = stable_hash([_message_payload(message) for message in messages])
    tool_state_hash = stable_hash(
        [tool.model_dump(mode="json", exclude_none=True) for tool in tools if tool.is_available]
    )
    config_hash = stable_hash(_public_model_config(config))
    cache_key = stable_hash(
        {
            "provider": config.provider,
            "model": config.model,
            "prompt_hash": prompt_hash,
            "tool_state_hash": tool_state_hash,
            "config_hash": config_hash,
            "seed": config.seed,
        }
    )
    return {
        "cache_key": cache_key,
        "prompt_hash": prompt_hash,
        "tool_state_hash": tool_state_hash,
        "config_hash": config_hash,
        "seed": config.seed,
    }


def response_hash(response: LLMResponse) -> str:
    return stable_hash(_response_to_payload(response))


def _post_json(
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = f"HTTP {exc.code}: {body[:1000]}"
        lowered = body.lower()
        if exc.code == 429:
            raise ProviderRateLimitError(message) from exc
        if exc.code in {400, 413} and (
            "context" in lowered or "maximum context" in lowered or "token" in lowered
        ):
            raise ProviderContextLengthError(message) from exc
        raise ProviderRequestError(message) from exc


def _openai_tool(tool: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


def _parse_json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _default_stub_response(messages: list[Message], tools: list[ToolSpec]) -> LLMResponse:
    if _history_is_nonempty(messages):
        return LLMResponse(content='{"final_answer": "Stub final answer based on local observations.", "stop": true}')
    available = [tool for tool in tools if tool.is_available]
    if available:
        return LLMResponse(
            tool_calls=[
                LLMToolCall(
                    name=available[0].name,
                    arguments=_minimal_arguments(available[0]),
                    call_id="local_stub_call",
                )
            ],
            content='{"thought": "Call one available tool."}',
        )
    return LLMResponse(content='{"final_answer": "No available tools; unable to proceed confidently.", "stop": true}')


def _history_is_nonempty(messages: list[Message]) -> bool:
    for message in reversed(messages):
        if message.role != "user":
            continue
        try:
            payload = json.loads(message.content)
        except json.JSONDecodeError:
            return "observation_history" in message.content and '"index"' in message.content
        history = payload.get("observation_history")
        return isinstance(history, list) and len(history) > 0
    return False


def _minimal_arguments(tool: ToolSpec) -> dict[str, Any]:
    args: dict[str, Any] = {}
    properties = tool.input_schema.get("properties", {})
    for field_name in tool.input_schema.get("required", []):
        field_schema = properties.get(field_name, {})
        schema_type = field_schema.get("type")
        if schema_type == "array":
            args[field_name] = []
        elif schema_type == "object":
            args[field_name] = {}
        elif schema_type == "number" or schema_type == "integer":
            args[field_name] = 0
        elif schema_type == "boolean":
            args[field_name] = False
        else:
            args[field_name] = "stub"
    return args


def _env_names(value: str | tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, tuple):
        return value
    if not value:
        return ()
    return (value,)


def _normalize_chat_completions_endpoint(base_url: str) -> str:
    value = base_url.rstrip("/")
    if value.endswith("/chat/completions"):
        return value
    if value.endswith("/v1"):
        return f"{value}/chat/completions"
    return f"{value}/v1/chat/completions"


def _normalize_gemini_endpoint(base_url: str, model: str, api_key: str | None) -> str:
    value = base_url.rstrip("/")
    endpoint = value if ":generateContent" in value else f"{value}/models/{model}:generateContent"
    if "key=" in endpoint:
        return endpoint
    separator = "&" if "?" in endpoint else "?"
    return f"{endpoint}{separator}key={api_key or ''}"


def _endpoint_host(endpoint: str) -> str:
    without_scheme = endpoint.split("://", 1)[-1]
    return without_scheme.split("/", 1)[0]


def _message_payload(message: Message) -> dict[str, Any]:
    return {
        "role": message.role,
        "content": message.content,
        "name": message.name,
        "tool_call_id": message.tool_call_id,
        "metadata": message.metadata,
    }


def _public_model_config(config: ModelConfig) -> dict[str, Any]:
    return {
        "provider": config.provider,
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "timeout": config.timeout,
        "retry_count": config.retry_count,
        "seed": config.seed,
        "json_mode": config.json_mode,
        "pricing": config.pricing,
        "base_url": config.base_url,
        "api_key_env": list(_env_names(config.api_key_env or ())),
        "extra": _redact_secret_like(config.extra),
    }


def _redact_secret_like(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in ("api_key", "secret", "password", "token")):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = _redact_secret_like(item)
        return redacted
    if isinstance(value, list):
        return [_redact_secret_like(item) for item in value]
    return value


def _response_to_payload(response: LLMResponse) -> dict[str, Any]:
    return {
        "content": response.content,
        "tool_calls": [
            {
                "name": tool_call.name,
                "arguments": tool_call.arguments,
                "call_id": tool_call.call_id,
            }
            for tool_call in response.tool_calls
        ],
        "usage": response.usage.as_dict(),
        "model_name": response.model_name,
        "provider_name": response.provider_name,
        "latency_s": response.latency_s,
        "estimated_cost_usd": response.estimated_cost_usd,
        "retries": response.retries,
        "response_id": response.response_id,
        "metadata": _redact_secret_like(response.metadata),
    }


def _response_from_payload(payload: dict[str, Any]) -> LLMResponse:
    usage = payload.get("usage", {})
    return LLMResponse(
        content=payload.get("content"),
        tool_calls=[
            LLMToolCall(
                name=tool_call["name"],
                arguments=dict(tool_call.get("arguments", {})),
                call_id=tool_call.get("call_id"),
            )
            for tool_call in payload.get("tool_calls", [])
        ],
        usage=TokenUsage(
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
        ),
        model_name=payload.get("model_name"),
        provider_name=payload.get("provider_name"),
        latency_s=payload.get("latency_s"),
        estimated_cost_usd=payload.get("estimated_cost_usd"),
        retries=payload.get("retries", 0),
        response_id=payload.get("response_id"),
        metadata=dict(payload.get("metadata", {})),
    )


def _with_response_metadata(
    response: LLMResponse,
    metadata: dict[str, Any],
    *,
    estimated_cost_usd: float | object | None = _UNSET,
    latency_s: float | object | None = _UNSET,
) -> LLMResponse:
    cost = response.estimated_cost_usd if estimated_cost_usd is _UNSET else cast("float | None", estimated_cost_usd)
    latency = response.latency_s if latency_s is _UNSET else cast("float | None", latency_s)
    return LLMResponse(
        content=response.content,
        tool_calls=response.tool_calls,
        usage=response.usage,
        model_name=response.model_name,
        provider_name=response.provider_name,
        latency_s=latency,
        estimated_cost_usd=cost,
        retries=response.retries,
        response_id=response.response_id,
        metadata={**response.metadata, **metadata},
    )
