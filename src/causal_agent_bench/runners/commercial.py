from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.runners.config import (
    PAID_PROVIDERS,
    AgentRunConfig,
    ExperimentConfig,
    is_free_tier_agent_run,
    is_zero_cost_config,
)
from causal_agent_bench.runners.costing import estimate_experiment_cost
from causal_agent_bench.schemas import Trajectory
from causal_agent_bench.utils.io import read_json, read_jsonl, write_json


class PaidCallsNotAllowedError(RuntimeError):
    """Raised when a config uses commercial providers without allow_paid_calls."""


class BudgetPreflightExceededError(RuntimeError):
    """Raised when the conservative cost estimate exceeds the configured budget cap."""


class PaidRunGateError(RuntimeError):
    """Raised when a paid provider run fails one or more safety gates."""


def uses_paid_providers(config: ExperimentConfig) -> bool:
    return any(
        agent_run.provider in PAID_PROVIDERS
        for agent_run in config.iter_agent_runs()
        if agent_run.provider
    )


def check_paid_run_gates(
    config: ExperimentConfig,
    *,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate whether a paid provider run is allowed without making API calls."""

    estimate = estimate_experiment_cost(config, config_path=config_path)
    return {
        "uses_paid_providers": uses_paid_providers(config),
        "allow_paid_calls": config.allow_paid_calls,
        "run_allowed": estimate.get("run_allowed"),
        "run_blocked_reasons": list(estimate.get("run_blocked_reasons") or []),
        "warnings": list(estimate.get("warnings") or []),
        "cost_estimate": estimate,
    }


def enforce_paid_run_gates(
    config: ExperimentConfig,
    *,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    report = check_paid_run_gates(config, config_path=config_path)
    if uses_paid_providers(config) and not report["run_allowed"]:
        raise PaidRunGateError("; ".join(report["run_blocked_reasons"]))
    return report


def enforce_paid_call_policy(config: ExperimentConfig) -> None:
    if is_zero_cost_config(config):
        return
    if uses_paid_providers(config) and not config.allow_paid_calls:
        providers = sorted(
            {
                agent_run.provider
                for agent_run in config.iter_agent_runs()
                if agent_run.provider in PAID_PROVIDERS
                and not is_free_tier_agent_run(agent_run)
            }
        )
        if not providers:
            return
        raise PaidCallsNotAllowedError(
            "Commercial API providers are configured but allow_paid_calls is false. "
            f"Set allow_paid_calls: true in the run config to enable paid providers: {providers}"
        )


def enforce_budget_preflight(config: ExperimentConfig) -> dict[str, Any]:
    estimate = estimate_experiment_cost(config)
    effective = config.effective_budget()
    cap = effective.max_total_usd if effective else config.budget_cap_usd
    upper = estimate.get("known_cost_upper_bound_usd")
    if cap is not None and upper is not None and upper > cap:
        raise BudgetPreflightExceededError(
            "Estimated run cost exceeds budget cap: "
            f"estimate=${upper:.8f}, cap=${cap:.8f}"
        )
    if uses_paid_providers(config) and effective and effective.strict_pricing and not estimate.get("pricing_known"):
        raise PaidRunGateError("pricing unknown for one or more paid provider agent runs")
    return estimate


def provider_run_metadata(agent_run: AgentRunConfig, *, run_date: str | None = None) -> dict[str, Any]:
    extra = dict(agent_run.extra)
    api_version = extra.get("api_version") or extra.get("anthropic_version")
    return {
        "agent_run": agent_run.run_id(),
        "agent": agent_run.agent,
        "provider": agent_run.provider,
        "model_id": agent_run.model,
        "api_version": api_version,
        "run_date": run_date or datetime.now(UTC).date().isoformat(),
        "sampling_parameters": {
            "temperature": agent_run.temperature,
            "max_tokens": agent_run.max_tokens,
            "retry_count": agent_run.retry_count,
        },
        "timeout_s": agent_run.timeout,
        "base_url": agent_run.base_url,
        "api_key_env": agent_run.api_key_env,
        "pricing": dict(agent_run.pricing),
        "extra": extra,
    }


def build_commercial_run_metadata(
    config: ExperimentConfig,
    *,
    cost_estimate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_date = datetime.now(UTC).date().isoformat()
    estimate = cost_estimate or estimate_experiment_cost(config)
    effective_budget = config.effective_budget()
    return {
        "allow_paid_calls": config.allow_paid_calls,
        "uses_paid_providers": uses_paid_providers(config),
        "cost_estimate_preflight_usd": estimate.get("known_cost_upper_bound_usd"),
        "cost_estimate_preflight": estimate,
        "budget_cap_usd": effective_budget.max_total_usd if effective_budget else config.budget_cap_usd,
        "budget": effective_budget.model_dump(mode="json") if effective_budget else None,
        "budget_preflight_status": estimate.get("budget_status"),
        "run_allowed_preflight": estimate.get("run_allowed"),
        "run_blocked_reasons_preflight": estimate.get("run_blocked_reasons"),
        "provider_runs": [
            provider_run_metadata(agent_run, run_date=run_date)
            for agent_run in config.iter_agent_runs()
            if agent_run.provider
        ],
        "redaction": {
            "api_keys_persisted": False,
            "environment_dump_persisted": False,
        },
    }


def collect_prompt_hashes(trajectories: list[Trajectory]) -> list[str]:
    hashes: set[str] = set()
    for trajectory in trajectories:
        prompt_hash = trajectory.metadata.get("prompt_version_hash") or trajectory.metadata.get(
            "prompt_hash"
        )
        if prompt_hash:
            hashes.add(str(prompt_hash))
        llm_calls = trajectory.metadata.get("llm_calls")
        if not isinstance(llm_calls, list):
            continue
        for call in llm_calls:
            if not isinstance(call, dict):
                continue
            for key in ("prompt_hash", "prompt_version_hash"):
                if call.get(key):
                    hashes.add(str(call[key]))
    return sorted(hashes)


def summarize_actual_costs(trajectories: list[Trajectory]) -> dict[str, Any]:
    total = 0.0
    known = True
    per_agent: dict[str, float] = {}
    for trajectory in trajectories:
        value = trajectory.metadata.get("estimated_cost_usd")
        if value is None:
            known = False
            continue
        cost = float(value)
        total = round(total + cost, 8)
        agent = trajectory.agent_name
        per_agent[agent] = round(per_agent.get(agent, 0.0) + cost, 8)
    return {
        "actual_estimated_cost_usd": round(total, 8) if known else None,
        "actual_cost_known": known,
        "actual_estimated_cost_by_agent_usd": per_agent if known else {},
    }


def finalize_commercial_run_metadata(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir)
    metadata_path = root / "run_metadata.json"
    metadata = read_json(metadata_path) if metadata_path.exists() else {}
    trajectories = read_jsonl(root / "trajectories.jsonl", Trajectory) if (root / "trajectories.jsonl").exists() else []
    cost_summary = summarize_actual_costs(trajectories)
    metadata.update(
        {
            "prompt_hashes": collect_prompt_hashes(trajectories),
            **cost_summary,
        }
    )
    write_json(metadata_path, metadata)
    write_json(root / "metadata.json", metadata)
    return metadata
