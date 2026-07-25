from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from causal_agent_bench.utils.io import load_yaml

DEFAULT_PROVIDER_REGISTRY = Path("configs/providers.yaml")
DEFAULT_MODEL_PRICING_REGISTRY = Path("configs/model_pricing.yaml")


class ProviderRegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    paid: bool = True
    enabled: bool = False
    api_key_env: str | list[str] = Field(default_factory=list)
    model_id_env: str | list[str] | None = None
    base_url_env: str | None = None
    default_base_url: str | None = None
    openai_compatible: bool = False
    requires_api_key: bool = True

    def api_key_env_names(self) -> tuple[str, ...]:
        if isinstance(self.api_key_env, str):
            return (self.api_key_env,)
        return tuple(self.api_key_env)

    def model_id_env_names(self) -> tuple[str, ...]:
        if self.model_id_env is None:
            return ()
        if isinstance(self.model_id_env, str):
            return (self.model_id_env,)
        return tuple(self.model_id_env)


class ProviderRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registry_version: str
    note: str | None = None
    providers: dict[str, ProviderRegistryEntry] = Field(default_factory=dict)


class ModelPricingEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model_id: str
    input_per_1m_tokens: float | None = None
    output_per_1m_tokens: float | None = None
    currency: str = "USD"
    source: str = "unknown"
    as_of: str | None = None
    comment: str | None = None
    pricing_known: bool = False

    @field_validator("input_per_1m_tokens", "output_per_1m_tokens", mode="before")
    @classmethod
    def empty_to_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value

    def rates(self) -> dict[str, float]:
        if not self.pricing_known:
            return {}
        rates: dict[str, float] = {}
        if self.input_per_1m_tokens is not None:
            rates["input_per_1m_tokens"] = float(self.input_per_1m_tokens)
        if self.output_per_1m_tokens is not None:
            rates["output_per_1m_tokens"] = float(self.output_per_1m_tokens)
        return rates


class ModelPricingRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registry_version: str
    currency_default: str = "USD"
    defaults_note: str | None = None
    models: list[ModelPricingEntry] = Field(default_factory=list)


@dataclass(frozen=True)
class ResolvedPricing:
    rates: dict[str, float] = field(default_factory=dict)
    pricing_known: bool = False
    source: str = "none"
    registry_entry: ModelPricingEntry | None = None
    warning: str | None = None


def load_provider_registry(path: str | Path | None = None) -> ProviderRegistry:
    registry_path = Path(path or DEFAULT_PROVIDER_REGISTRY)
    raw = load_yaml(registry_path)
    return ProviderRegistry.model_validate(raw)


def load_model_pricing_registry(path: str | Path | None = None) -> ModelPricingRegistry:
    registry_path = Path(path or DEFAULT_MODEL_PRICING_REGISTRY)
    raw = load_yaml(registry_path)
    return ModelPricingRegistry.model_validate(raw)


def provider_entry(registry: ProviderRegistry, provider: str) -> ProviderRegistryEntry | None:
    return registry.providers.get(provider)


def provider_is_enabled(registry: ProviderRegistry, provider: str) -> bool:
    entry = provider_entry(registry, provider)
    if entry is None:
        return False
    if not entry.requires_api_key:
        return True
    return any(os.getenv(name) for name in entry.api_key_env_names())


def provider_api_key_configured(
    registry: ProviderRegistry,
    provider: str,
    *,
    override_env: str | None = None,
) -> bool:
    if override_env:
        return bool(os.getenv(override_env))
    entry = provider_entry(registry, provider)
    if entry is None or not entry.requires_api_key:
        return True
    return any(os.getenv(name) for name in entry.api_key_env_names())


def provider_model_id_configured(
    registry: ProviderRegistry,
    provider: str,
    model: str | None,
) -> bool:
    if model:
        return True
    entry = provider_entry(registry, provider)
    if entry is None:
        return False
    return any(os.getenv(name) for name in entry.model_id_env_names())


def lookup_model_pricing(
    registry: ModelPricingRegistry,
    *,
    provider: str,
    model: str | None,
) -> ModelPricingEntry | None:
    if not provider:
        return None
    candidates = [entry for entry in registry.models if entry.provider == provider]
    if not candidates:
        return None
    lookup_keys = [model, "default"] if model else ["default"]
    for key in lookup_keys:
        if not key:
            continue
        for entry in candidates:
            if entry.model_id == key:
                return entry
    return None


def resolve_pricing_from_registry(
    registry: ModelPricingRegistry,
    *,
    provider: str | None,
    model: str | None,
) -> ResolvedPricing:
    if not provider:
        return ResolvedPricing(source="none")
    entry = lookup_model_pricing(registry, provider=provider, model=model)
    if entry is None:
        return ResolvedPricing(
            pricing_known=False,
            source="registry:none",
            warning=(
                f"No pricing registry entry for provider={provider!r}, model={model!r}. "
                "Cost estimate will be unknown unless run config supplies pricing."
            ),
        )
    rates = entry.rates()
    if entry.pricing_known and rates:
        return ResolvedPricing(
            rates=rates,
            pricing_known=True,
            source=f"registry:{provider}:{entry.model_id}",
            registry_entry=entry,
        )
    return ResolvedPricing(
        pricing_known=False,
        source=f"registry:{provider}:{entry.model_id}:unknown",
        registry_entry=entry,
        warning=(
            f"Pricing marked unknown for provider={provider!r}, model={entry.model_id!r}. "
            "estimate-cost will not assume zero cost."
        ),
    )
