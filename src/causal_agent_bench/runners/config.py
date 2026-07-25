from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from causal_agent_bench.utils.io import load_yaml

KNOWN_PROVIDERS = {
    "local_stub",
    "openai",
    "anthropic",
    "gemini",
    "openrouter",
    "openai_compatible",
    "local_openai",
}
PAID_PROVIDERS = KNOWN_PROVIDERS - {"local_stub", "local_openai"}
ZERO_COST_LOCAL_PROVIDERS = frozenset({"local_stub", "local_openai"})
ZERO_COST_BLOCKED_PROVIDERS = frozenset({"openai", "anthropic"})
COST_MODES = frozenset({"default", "zero_cost"})
SCIENTIFIC_EVIDENCE_LEVELS = frozenset(
    {"default", "preliminary_or_engineering", "pilot_supported", "main_supported"}
)
PROVIDER_TYPES = frozenset({"default", "local", "free_tier", "mixed_zero_cost"})
ORACLE_AGENT_NAMES = frozenset({"scripted_oracle_agent"})
PRICING_KEYS = {"input_per_1m_tokens", "output_per_1m_tokens"}
PROVIDER_MODEL_ENV_VARS = {
    "openai": ("OPENAI_MODEL_ID",),
    "anthropic": ("ANTHROPIC_MODEL_ID",),
    "gemini": ("GEMINI_MODEL_ID",),
    "openrouter": ("OPENROUTER_MODEL_ID",),
    "openai_compatible": ("OPENAI_COMPATIBLE_MODEL_ID",),
    "local_openai": ("LOCAL_OPENAI_MODEL_ID",),
}


class AgentRunConfig(BaseModel):
    """One concrete agent/provider/model run entry."""

    model_config = ConfigDict(extra="forbid")

    agent: str
    name: str | None = None
    provider: str | None = None
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = Field(default=1024, ge=1)
    retry_count: int = Field(default=2, ge=0)
    timeout: float = Field(default=60.0, gt=0)
    budget_cap_usd: float | None = Field(default=None, ge=0)
    task_budget_cap_usd: float | None = Field(default=None, ge=0)
    max_api_calls: int | None = Field(default=None, ge=1)
    pricing: dict[str, float] = Field(default_factory=dict)
    base_url: str | None = None
    api_key_env: str | None = None
    cache_dir: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in KNOWN_PROVIDERS:
            available = ", ".join(sorted(KNOWN_PROVIDERS))
            raise ValueError(f"unknown provider {value!r}; expected one of: {available}")
        return value

    @field_validator("pricing")
    @classmethod
    def validate_pricing(cls, value: dict[str, float]) -> dict[str, float]:
        unknown = sorted(set(value) - PRICING_KEYS)
        if unknown:
            allowed = ", ".join(sorted(PRICING_KEYS))
            raise ValueError(f"unknown pricing key(s) {unknown}; expected keys: {allowed}")
        negative = [key for key, price in value.items() if price < 0]
        if negative:
            raise ValueError(f"pricing values must be non-negative; got negative value(s) for {negative}")
        return value

    @model_validator(mode="after")
    def reject_oracle_in_provider_runs(self) -> AgentRunConfig:
        if self.provider in PAID_PROVIDERS and self.agent in ORACLE_AGENT_NAMES:
            raise ValueError(
                f"oracle agent {self.agent!r} cannot be used with paid provider {self.provider!r}"
            )
        return self

    def run_id(self) -> str:
        if self.name:
            return self.name
        if self.provider and self.model:
            model_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", self.model).strip("_")
            return f"{self.agent}_{self.provider}_{model_slug}"
        if self.provider:
            return f"{self.agent}_{self.provider}"
        return self.agent


CostModelConfig = dict[str, dict[str, dict[str, float]]]


class BudgetConfig(BaseModel):
    """Structured budget gate for provider pilot runs."""

    model_config = ConfigDict(extra="forbid")

    # Caps may be omitted in the structured block and inherited from the
    # top-level ``budget_cap_usd`` / ``max_api_calls`` fields (see
    # ``ExperimentConfig.reconcile_budget``). When neither source supplies them,
    # they default to a zero-spend / single-call floor.
    max_total_usd: float | None = Field(default=None, ge=0)
    max_calls: int | None = Field(default=None, ge=1)
    max_input_tokens: int | None = Field(default=None, ge=0)
    max_output_tokens: int | None = Field(default=None, ge=0)
    require_explicit_paid_approval: bool = True
    strict_pricing: bool = True


class ApprovalConfig(BaseModel):
    """Static approval markers for provider-pilot config copies."""

    model_config = ConfigDict(extra="forbid")

    advisor_approved: bool = False
    budget_approved: bool = False
    approved_for_dry_run: bool = False
    approved_for_live_run: bool = False
    approved_by: str | None = None
    approval_date: str | None = None
    advisor_approval_id: str | None = None
    max_budget_usd: float | None = Field(default=None, ge=0)
    notes: str | None = None


class RunLimitsConfig(BaseModel):
    """Optional runtime guardrails for micro/debug/local runs."""

    model_config = ConfigDict(extra="forbid")

    max_instances: int | None = Field(default=None, ge=1)
    max_agents: int | None = Field(default=None, ge=1)
    max_trajectories: int | None = Field(default=None, ge=1)
    max_runtime_minutes: float | None = Field(default=None, gt=0)
    stop_after_trajectories: int | None = Field(default=None, ge=1)
    max_steps_per_instance: int | None = Field(default=None, ge=1)
    max_output_tokens: int | None = Field(default=None, ge=1)
    max_api_calls: int | None = Field(default=None, ge=1)


class ExperimentConfig(BaseModel):
    """Validated configuration for schema-native benchmark runs."""

    model_config = ConfigDict(extra="forbid")

    seed: int = 0
    run_name: str = Field(min_length=1)
    benchmark_path: str | None = None
    benchmark_dir: str | None = None
    agents: list[str] = Field(default_factory=list)
    agent_runs: list[AgentRunConfig] = Field(default_factory=list)
    max_steps: int = Field(default=8, ge=1)
    num_repeats: int = Field(default=1, ge=1)
    output_dir: str = "results"
    save_observations: bool = True
    save_agent_thoughts: bool = True
    write_markdown_trajectories: bool = False
    fail_fast: bool = False
    auto_score: bool = True
    allow_paid_calls: bool = False
    cost_mode: str = "default"
    scientific_evidence_level: str = "default"
    scientific_evidence: bool = False
    template_only: bool = False
    require_dry_run_before_live: bool = True
    provider_type: str = "default"
    provider: str | None = None
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = Field(default=1024, ge=1)
    retry_count: int = Field(default=2, ge=0)
    timeout: float = Field(default=60.0, gt=0)
    budget_cap_usd: float | None = Field(default=None, ge=0)
    task_budget_cap_usd: float | None = Field(default=None, ge=0)
    max_instances: int | None = Field(default=None, ge=1)
    max_api_calls: int | None = Field(default=None, ge=1)
    budget: BudgetConfig | None = None
    approval: ApprovalConfig | None = None
    pricing: dict[str, float] = Field(default_factory=dict)
    cost_models: CostModelConfig = Field(default_factory=dict)
    provider_registry_path: str | None = "configs/providers.yaml"
    pricing_registry_path: str | None = "configs/model_pricing.yaml"
    base_url: str | None = None
    api_key_env: str | None = None
    cache_dir: str | None = None
    evidence_scope: str | None = None
    instance_metadata_filter: dict[str, Any] = Field(default_factory=dict)
    limits: RunLimitsConfig | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str | None) -> str | None:
        return AgentRunConfig.validate_provider(value)

    @field_validator("cost_mode")
    @classmethod
    def validate_cost_mode(cls, value: str) -> str:
        if value not in COST_MODES:
            allowed = ", ".join(sorted(COST_MODES))
            raise ValueError(f"unknown cost_mode {value!r}; expected one of: {allowed}")
        return value

    @field_validator("scientific_evidence_level")
    @classmethod
    def validate_scientific_evidence_level(cls, value: str) -> str:
        if value not in SCIENTIFIC_EVIDENCE_LEVELS:
            allowed = ", ".join(sorted(SCIENTIFIC_EVIDENCE_LEVELS))
            raise ValueError(
                f"unknown scientific_evidence_level {value!r}; expected one of: {allowed}"
            )
        return value

    @field_validator("provider_type")
    @classmethod
    def validate_provider_type(cls, value: str) -> str:
        if value not in PROVIDER_TYPES:
            allowed = ", ".join(sorted(PROVIDER_TYPES))
            raise ValueError(f"unknown provider_type {value!r}; expected one of: {allowed}")
        return value

    @field_validator("pricing")
    @classmethod
    def validate_pricing(cls, value: dict[str, float]) -> dict[str, float]:
        return AgentRunConfig.validate_pricing(value)

    @field_validator("cost_models")
    @classmethod
    def validate_cost_models(cls, value: CostModelConfig) -> CostModelConfig:
        for provider, models in value.items():
            if provider not in KNOWN_PROVIDERS:
                available = ", ".join(sorted(KNOWN_PROVIDERS))
                raise ValueError(f"unknown cost model provider {provider!r}; expected one of: {available}")
            for model, pricing in models.items():
                try:
                    AgentRunConfig.validate_pricing(pricing)
                except ValueError as exc:
                    raise ValueError(f"invalid pricing for cost_models.{provider}.{model}: {exc}") from exc
        return value

    @model_validator(mode="after")
    def check_benchmark_location(self) -> ExperimentConfig:
        if self.benchmark_path is None and self.benchmark_dir is None:
            raise ValueError("one of benchmark_path or benchmark_dir is required")
        if self.benchmark_path is not None and self.benchmark_dir is not None:
            raise ValueError("benchmark_path and benchmark_dir are mutually exclusive")
        if not self.agents and not self.agent_runs:
            raise ValueError("one of agents or agent_runs is required")
        for agent_run in self.iter_agent_runs():
            if agent_run.provider in PAID_PROVIDERS and agent_run.agent in ORACLE_AGENT_NAMES:
                raise ValueError(
                    f"oracle agent {agent_run.agent!r} cannot be used with paid provider "
                    f"{agent_run.provider!r} in run {self.run_name!r}"
                )
        if self.budget is not None:
            # The structured ``budget`` block may omit the numeric caps and rely
            # on the top-level fields (as the commercial-API configs do), or vice
            # versa. Reconcile both directions so downstream code always sees a
            # populated, consistent budget.
            if self.budget.max_total_usd is None:
                self.budget.max_total_usd = (
                    self.budget_cap_usd if self.budget_cap_usd is not None else 0.0
                )
            if self.budget.max_calls is None:
                self.budget.max_calls = (
                    self.max_api_calls if self.max_api_calls is not None else 1
                )
            self.budget_cap_usd = self.budget.max_total_usd
            self.max_api_calls = self.budget.max_calls
        if self.cost_mode == "zero_cost":
            if self.allow_paid_calls:
                raise ValueError("zero_cost mode requires allow_paid_calls: false")
            cap = self.budget_cap_usd
            if cap not in (None, 0.0):
                raise ValueError("zero_cost mode requires budget cap of 0 USD")
            if self.scientific_evidence_level == "default":
                self.scientific_evidence_level = "preliminary_or_engineering"
            for agent_run in self.iter_agent_runs():
                provider = agent_run.provider
                if provider in ZERO_COST_BLOCKED_PROVIDERS:
                    raise ValueError(
                        f"zero_cost mode does not allow provider {provider!r} "
                        f"in agent run {agent_run.run_id()!r}"
                    )
                if provider in PAID_PROVIDERS and not _agent_run_is_zero_cost_free_tier(agent_run):
                    raise ValueError(
                        f"zero_cost paid provider {provider!r} in {agent_run.run_id()!r} "
                        "must set extra.free_tier: true and zero pricing"
                    )
        return self

    def effective_budget(self) -> BudgetConfig | None:
        if self.budget is not None:
            return self.budget
        if self.budget_cap_usd is None and self.max_api_calls is None:
            return None
        return BudgetConfig(
            max_total_usd=float(self.budget_cap_usd or 0.0),
            max_calls=int(self.max_api_calls or 1),
            require_explicit_paid_approval=True,
            strict_pricing=True,
        )

    def resolved_provider_registry_path(self, base_dir: str | Path | None = None) -> Path | None:
        if not self.provider_registry_path:
            return None
        path = Path(self.provider_registry_path)
        root = Path(base_dir or Path.cwd())
        return path if path.is_absolute() else root / path

    def resolved_pricing_registry_path(self, base_dir: str | Path | None = None) -> Path | None:
        if not self.pricing_registry_path:
            return None
        path = Path(self.pricing_registry_path)
        root = Path(base_dir or Path.cwd())
        return path if path.is_absolute() else root / path

    def resolved_benchmark_path(self, base_dir: str | Path | None = None) -> Path:
        root = Path(base_dir or Path.cwd())
        if self.benchmark_path is not None:
            path = Path(self.benchmark_path)
        else:
            assert self.benchmark_dir is not None
            path = Path(self.benchmark_dir) / "instances.jsonl"
        return path if path.is_absolute() else root / path

    def resolved_output_dir(self, base_dir: str | Path | None = None) -> Path:
        root = Path(base_dir or Path.cwd())
        path = Path(self.output_dir)
        return path if path.is_absolute() else root / path

    def iter_agent_runs(self) -> list[AgentRunConfig]:
        if self.agent_runs:
            return self.agent_runs
        return [
            AgentRunConfig(
                agent=agent,
                provider=self.provider,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                retry_count=self.retry_count,
                timeout=self.timeout,
                budget_cap_usd=self.budget_cap_usd,
                task_budget_cap_usd=self.task_budget_cap_usd,
                max_api_calls=self.max_api_calls,
                pricing=dict(self.pricing),
                base_url=self.base_url,
                api_key_env=self.api_key_env,
                cache_dir=self.cache_dir,
            )
            for agent in self.agents
        ]

    def resolved_pricing(
        self,
        agent_run: AgentRunConfig,
        *,
        pricing_registry: Any | None = None,
    ) -> dict[str, float]:
        if agent_run.pricing:
            return dict(agent_run.pricing)
        provider = agent_run.provider or self.provider
        model = agent_run.model or self.model
        if provider:
            provider_models = self.cost_models.get(provider, {})
            lookup_keys = [model, "*", "default"] if model else ["*", "default"]
            for key in lookup_keys:
                if key in provider_models:
                    return dict(provider_models[key])
        if self.pricing:
            return dict(self.pricing)
        if pricing_registry is not None and provider:
            from causal_agent_bench.runners.registries import resolve_pricing_from_registry

            resolved = resolve_pricing_from_registry(
                pricing_registry,
                provider=provider,
                model=model,
            )
            if resolved.rates:
                return dict(resolved.rates)
        return {}

    def resolved_pricing_details(
        self,
        agent_run: AgentRunConfig,
        *,
        pricing_registry: Any | None = None,
    ) -> dict[str, Any]:
        from causal_agent_bench.runners.registries import resolve_pricing_from_registry

        if agent_run.pricing:
            return {
                "rates": dict(agent_run.pricing),
                "pricing_known": True,
                "source": "agent_run.pricing",
                "warning": None,
            }
        provider = agent_run.provider or self.provider
        model = agent_run.model or self.model
        if provider:
            provider_models = self.cost_models.get(provider, {})
            lookup_keys = [model, "*", "default"] if model else ["*", "default"]
            for key in lookup_keys:
                if key in provider_models:
                    return {
                        "rates": dict(provider_models[key]),
                        "pricing_known": True,
                        "source": f"cost_models.{provider}.{key}",
                        "warning": None,
                    }
        if self.pricing:
            return {
                "rates": dict(self.pricing),
                "pricing_known": True,
                "source": "pricing",
                "warning": None,
            }
        if pricing_registry is not None and provider:
            resolved = resolve_pricing_from_registry(
                pricing_registry,
                provider=provider,
                model=model,
            )
            return {
                "rates": dict(resolved.rates),
                "pricing_known": resolved.pricing_known,
                "source": resolved.source,
                "warning": resolved.warning,
            }
        return {
            "rates": {},
            "pricing_known": False,
            "source": "none",
            "warning": "No pricing configured in run config or registry.",
        }


def _agent_run_is_zero_cost_free_tier(agent_run: AgentRunConfig) -> bool:
    if agent_run.provider not in PAID_PROVIDERS:
        return False
    if not agent_run.extra.get("free_tier"):
        return False
    pricing = agent_run.pricing
    return (
        pricing.get("input_per_1m_tokens") == 0.0
        and pricing.get("output_per_1m_tokens") == 0.0
    )


def is_zero_cost_config(config: ExperimentConfig) -> bool:
    return config.cost_mode == "zero_cost"


def is_free_tier_agent_run(agent_run: AgentRunConfig) -> bool:
    return _agent_run_is_zero_cost_free_tier(agent_run)


def is_experiment_config(raw: dict[str, Any]) -> bool:
    """Return whether a YAML mapping should use the schema-native experiment runner."""

    return "benchmark_path" in raw or "benchmark_dir" in raw


class ProviderConfig(BaseModel):
    """Reusable provider block for future config families."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = Field(default=1024, ge=1)
    retry_count: int = Field(default=2, ge=0)
    timeout: float = Field(default=60.0, gt=0)
    budget_cap_usd: float | None = Field(default=None, ge=0)
    pricing: dict[str, float] = Field(default_factory=dict)
    base_url: str | None = None
    api_key_env: str | None = None
    cache_dir: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        checked = AgentRunConfig.validate_provider(value)
        assert checked is not None
        return checked

    @field_validator("pricing")
    @classmethod
    def validate_pricing(cls, value: dict[str, float]) -> dict[str, float]:
        return AgentRunConfig.validate_pricing(value)


class DatasetValidationConfig(BaseModel):
    """Config used to validate a generated benchmark artifact bundle."""

    model_config = ConfigDict(extra="forbid")

    benchmark_version: str
    base_tasks_path: str
    interventions_path: str
    instances_path: str
    splits_path: str | None = None
    expected: dict[str, Any] = Field(default_factory=dict)


class ScoringConfig(BaseModel):
    """Minimal score-command config schema for scripted runs."""

    model_config = ConfigDict(extra="forbid")

    run_dir: str


class AnalysisConfig(BaseModel):
    """Minimal analysis-command config schema for scripted runs."""

    model_config = ConfigDict(extra="forbid")

    run_dir: str
    export_paper_assets: bool = False


class CostEstimationConfig(BaseModel):
    """Config that points at a run config for cost-estimation automation."""

    model_config = ConfigDict(extra="forbid")

    config: str


class LegacyTaskGenerationConfig(BaseModel):
    """Older synthetic-task config kept validating during the transition."""

    model_config = ConfigDict(extra="allow")

    seed: int = 0
    output_path: str
    n_tasks: int = Field(gt=0)
    include_clean: bool = True
    domains: list[str] = Field(min_length=1)
    interventions: list[str] = Field(default_factory=list)


def load_experiment_config(path: str | Path) -> tuple[ExperimentConfig, dict[str, Any]]:
    raw = _expand_env_values(load_yaml(path))
    return ExperimentConfig.model_validate(raw), raw


_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")


def _expand_env_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env_values(item) for item in value]
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), match.group(2) or ""), value)
    return value
