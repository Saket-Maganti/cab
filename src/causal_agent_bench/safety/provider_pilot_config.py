"""Static validation for provider-pilot vs oracle-sanity config templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.runners.config import ExperimentConfig

FORBIDDEN_EVIDENCE_AGENTS = frozenset(
    {
        "scripted_oracle_agent",
        "mock_behavior_agent",
        "greedy_tool_agent",
        "react_stub_agent",
    }
)

FORBIDDEN_EVIDENCE_PROVIDERS = frozenset(
    {
        "",
        "none",
        "null",
        "default",
        "placeholder",
        "provider",
        "local",
        "mock",
        "stub",
        "local_stub",
        "local_openai",
        "oracle",
        "scripted_oracle",
        "synthetic",
        "deterministic",
        "fake",
        "test",
        "debug",
        "offline",
        "dry_run",
    }
)
FORBIDDEN_PROVIDER_MARKERS = frozenset(
    {
        "local",
        "mock",
        "stub",
        "oracle",
        "synthetic",
        "deterministic",
        "fake",
        "debug",
        "offline",
        "dry",
    }
)
PROVIDER_BACKED_PREFIXES = (
    "openai",
    "anthropic",
    "gemini",
    "google",
    "openrouter",
    "mistral",
    "cohere",
    "together",
    "fireworks",
    "azure_openai",
    "azure-openai",
)
INVALID_MODEL_VALUES = frozenset(
    {
        "",
        "none",
        "null",
        "default",
        "placeholder",
        "provider",
        "model",
        "test",
        "debug",
        "offline",
    }
)
MODEL_ENV_PLACEHOLDER_ALLOWLIST = frozenset({"PROVIDER_BACKED_MODEL_ID"})

REQUIRED_PROVIDER_PILOT_SCOPES = frozenset(
    {
        "provider_pilot_pending_verification",
        "commercial_api_pilot_unvalidated",
    }
)

ORACLE_SANITY_SCOPES = frozenset(
    {
        "oracle_sanity_only",
        "pilot_stub_engineering_only",
        "mock_diagnostic_only",
        "deterministic_baseline_engineering",
    }
)


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"config root must be a mapping: {path}")
    return ExperimentConfig.model_validate(payload)


def _normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def _provider_is_provider_backed(provider: str) -> bool:
    return any(
        provider == prefix or provider.startswith((f"{prefix}_", f"{prefix}-"))
        for prefix in PROVIDER_BACKED_PREFIXES
    )


def _provider_issue(provider_value: Any) -> str | None:
    provider = _normalized(provider_value)
    if not provider:
        return "missing provider"
    if provider in FORBIDDEN_EVIDENCE_PROVIDERS:
        return f"forbidden evidence provider: {provider_value!r}"
    if any(marker in provider for marker in FORBIDDEN_PROVIDER_MARKERS):
        return f"provider is not provider-backed evidence: {provider_value!r}"
    if not _provider_is_provider_backed(provider):
        return f"provider must name a real provider-backed family: {provider_value!r}"
    return None


def _model_issue(model_value: Any, provider_value: Any) -> str | None:
    raw = str(model_value or "").strip()
    model = raw.lower()
    provider = _normalized(provider_value)
    if not raw:
        return "missing model for provider-backed pilot"
    if model.startswith("${"):
        upper = raw.upper()
        provider_token = provider.replace("-", "_").upper()
        if provider_token and provider_token in upper:
            return None
        if any(marker in upper for marker in MODEL_ENV_PLACEHOLDER_ALLOWLIST):
            return None
        return f"model placeholder must name a provider-backed model env var: {model_value!r}"
    if model in INVALID_MODEL_VALUES or "placeholder" in model:
        return f"model is not a provider-backed model id: {model_value!r}"
    return None


def validate_provider_pilot_evidence_config(config: ExperimentConfig) -> list[str]:
    """Return issues if config is unsuitable for provider-backed scientific evidence."""

    issues: list[str] = []
    agent_runs = list(config.iter_agent_runs())
    if not agent_runs:
        issues.append("agent_runs is empty")
        return issues

    for run in agent_runs:
        if run.agent in FORBIDDEN_EVIDENCE_AGENTS or "oracle" in run.agent.lower():
            issues.append(f"forbidden evidence agent: {run.agent}")
        provider_issue = _provider_issue(run.provider)
        if provider_issue:
            issues.append(provider_issue)
        model_issue = _model_issue(run.model, run.provider)
        if model_issue:
            issues.append(model_issue)

    if config.allow_paid_calls:
        issues.append("allow_paid_calls must be false in unapproved templates")

    scope = str(config.evidence_scope or "").lower()
    if scope and scope not in REQUIRED_PROVIDER_PILOT_SCOPES:
        if scope in ORACLE_SANITY_SCOPES or "oracle" in scope or "mock" in scope:
            issues.append(f"evidence_scope {config.evidence_scope!r} is engineering/oracle-only")

    if config.scientific_evidence_level == "main_supported":
        issues.append("scientific_evidence_level must not be main_supported before verification")

    return issues


def validate_oracle_sanity_config(config: ExperimentConfig) -> list[str]:
    """Return issues if config is not clearly engineering-only oracle sanity."""

    issues: list[str] = []
    agents = [run.agent for run in config.iter_agent_runs()]
    if not agents or not all("oracle" in agent.lower() for agent in agents):
        issues.append("oracle sanity config must use oracle agent only")

    non_oracle = [run for run in config.iter_agent_runs() if "oracle" not in run.agent.lower()]
    if non_oracle:
        issues.append("oracle sanity config must not include provider LLM agents")

    if config.allow_paid_calls:
        issues.append("allow_paid_calls must be false for oracle sanity template")

    scope = str(config.evidence_scope or "").lower()
    if scope != "oracle_sanity_only":
        issues.append(f"evidence_scope must be oracle_sanity_only, got {config.evidence_scope!r}")

    paid_providers = [
        run.provider
        for run in config.iter_agent_runs()
        if run.provider and run.provider not in {"", "local", "local_stub"}
    ]
    if paid_providers:
        issues.append(f"oracle sanity must not use paid providers: {paid_providers}")

    return issues


def template_metadata_defaults(path: str | Path) -> dict[str, Any]:
    """Conservative metadata defaults documented for templates (not from a run)."""

    config = load_experiment_config(path)
    return {
        "scientific_evidence": False,
        "allow_paid_calls": config.allow_paid_calls,
        "evidence_scope": config.evidence_scope,
        "scientific_evidence_level": config.scientific_evidence_level,
        "agents": [run.agent for run in config.iter_agent_runs()],
        "providers": [run.provider for run in config.iter_agent_runs() if run.provider],
    }
