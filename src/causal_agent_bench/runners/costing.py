from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from causal_agent_bench.agents.llm_clients import TokenUsage, estimate_cost_usd
from causal_agent_bench.runners.config import (
    PAID_PROVIDERS,
    ExperimentConfig,
    is_zero_cost_config,
    load_experiment_config,
)
from causal_agent_bench.runners.registries import (
    load_model_pricing_registry,
    load_provider_registry,
)
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.utils.io import read_jsonl


def estimate_config_cost(config_path: str | Path) -> dict[str, Any]:
    config, _ = load_experiment_config(config_path)
    return estimate_experiment_cost(config, config_path=config_path)


def estimate_experiment_cost(
    config: ExperimentConfig,
    *,
    config_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root or Path.cwd())
    pricing_registry = _load_pricing_registry(config, root)
    provider_registry = _load_provider_registry(config, root)
    benchmark_path = config.resolved_benchmark_path(root)
    instances = read_jsonl(benchmark_path, BenchmarkInstance)
    if config.max_instances is not None:
        instances = instances[: config.max_instances]

    agent_runs = config.iter_agent_runs()
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    total_known_upper_bound = 0.0
    all_known = True
    total_input_tokens = 0
    total_output_tokens = 0
    total_calls = 0
    per_provider: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "estimated_cost_upper_bound_usd": 0.0,
            "estimated_input_tokens": 0,
            "estimated_output_tokens": 0,
            "expected_max_calls": 0,
            "pricing_known": True,
        }
    )

    effective_budget = config.effective_budget()
    run_budget_cap = effective_budget.max_total_usd if effective_budget else config.budget_cap_usd

    for agent_run in agent_runs:
        llm_backed = agent_run.provider is not None
        from causal_agent_bench.runners.config import is_free_tier_agent_run

        no_paid_provider = (
            agent_run.provider is None
            or agent_run.provider not in PAID_PROVIDERS
            or is_free_tier_agent_run(agent_run)
        )
        pricing_details = config.resolved_pricing_details(
            agent_run,
            pricing_registry=pricing_registry,
        )
        pricing = pricing_details["rates"]
        pricing_known = bool(pricing_details["pricing_known"] and pricing)
        if pricing_details.get("warning"):
            warnings.append(str(pricing_details["warning"]))
        llm_calls_upper_bound = (
            len(instances) * config.num_repeats * config.max_steps if llm_backed else 0
        )
        input_tokens_upper_bound = _input_tokens_upper_bound(agent_run, llm_calls_upper_bound)
        output_tokens_upper_bound = llm_calls_upper_bound * agent_run.max_tokens
        total_tokens_upper_bound = input_tokens_upper_bound + output_tokens_upper_bound
        cost = (
            0.0
            if no_paid_provider
            else estimate_cost_usd(
                usage=TokenUsage(
                    input_tokens=input_tokens_upper_bound,
                    output_tokens=output_tokens_upper_bound,
                    total_tokens=total_tokens_upper_bound,
                ),
                pricing=pricing,
            )
        )
        known = cost is not None
        if cost is not None:
            total_known_upper_bound += float(cost)
        else:
            all_known = False
            if not no_paid_provider:
                warnings.append(
                    f"Unknown pricing for provider={agent_run.provider!r}, "
                    f"model={agent_run.model!r}; cost not assumed zero."
                )

        total_input_tokens += input_tokens_upper_bound
        total_output_tokens += output_tokens_upper_bound
        total_calls += llm_calls_upper_bound

        provider_name = agent_run.provider or "none"
        bucket = per_provider[provider_name]
        bucket["expected_max_calls"] += llm_calls_upper_bound
        bucket["estimated_input_tokens"] += input_tokens_upper_bound
        bucket["estimated_output_tokens"] += output_tokens_upper_bound
        if known and cost is not None:
            bucket["estimated_cost_upper_bound_usd"] = round(
                bucket["estimated_cost_upper_bound_usd"] + float(cost),
                8,
            )
        else:
            bucket["pricing_known"] = False

        rows.append(
            {
                "agent_run": agent_run.run_id(),
                "provider": agent_run.provider,
                "model": agent_run.model,
                "instances": len(instances),
                "num_repeats": config.num_repeats,
                "max_steps": config.max_steps,
                "llm_calls_upper_bound": llm_calls_upper_bound,
                "input_tokens_upper_bound": input_tokens_upper_bound,
                "output_tokens_upper_bound": output_tokens_upper_bound,
                "total_tokens_upper_bound": total_tokens_upper_bound,
                "known_output_cost_upper_bound_usd": cost,
                "known_cost_upper_bound_usd": cost,
                "budget_cap_usd": agent_run.budget_cap_usd,
                "task_budget_cap_usd": agent_run.task_budget_cap_usd,
                "pricing_configured": pricing_known,
                "pricing_known": pricing_known,
                "pricing_source": pricing_details["source"],
            }
        )

    per_provider_out = {
        provider: {
            **values,
            "estimated_cost_upper_bound_usd": round(values["estimated_cost_upper_bound_usd"], 8)
            if values["pricing_known"]
            else None,
        }
        for provider, values in per_provider.items()
    }

    budget_status = _budget_status(total_known_upper_bound, run_budget_cap, all_known)
    gate_report = _build_run_permission_report(
        config,
        estimate={
            "known_cost_upper_bound_usd": round(total_known_upper_bound, 8) if all_known else None,
            "budget_status": budget_status,
            "estimated_input_tokens": total_input_tokens,
            "estimated_output_tokens": total_output_tokens,
            "expected_max_calls": total_calls,
            "pricing_known": all_known,
        },
        provider_registry=provider_registry,
        pricing_registry=pricing_registry,
    )

    return {
        "config_path": str(config_path) if config_path else None,
        "dataset_path": str(benchmark_path),
        "config_run_name": config.run_name,
        "number_of_agents": len(agent_runs),
        "number_of_instances": len(instances),
        "expected_max_calls": total_calls,
        "estimated_input_tokens": total_input_tokens,
        "estimated_output_tokens": total_output_tokens,
        "per_provider": per_provider_out,
        "agent_runs": rows,
        "instances": len(instances),
        "run_budget_cap_usd": run_budget_cap,
        "budget": effective_budget.model_dump(mode="json") if effective_budget else None,
        "known_output_cost_upper_bound_usd": round(total_known_upper_bound, 8)
        if all_known
        else None,
        "known_cost_upper_bound_usd": round(total_known_upper_bound, 8) if all_known else None,
        "total_cost_estimate_usd": round(total_known_upper_bound, 8) if all_known else None,
        "pricing_known": all_known,
        "budget_status": budget_status,
        "run_allowed": gate_report["run_allowed"],
        "run_blocked_reasons": gate_report["run_blocked_reasons"],
        "warnings": _dedupe(warnings + gate_report.get("warnings", [])),
        "note": (
            "Conservative upper-bound estimate. Unknown pricing is never treated as zero cost. "
            "Verify registry defaults against provider dashboards before paid runs."
        ),
    }


def _build_run_permission_report(
    config: ExperimentConfig,
    *,
    estimate: dict[str, Any],
    provider_registry: Any | None,
    pricing_registry: Any | None,
) -> dict[str, Any]:
    from causal_agent_bench.runners.registries import (
        provider_api_key_configured,
        provider_is_enabled,
        provider_model_id_configured,
    )

    blocked: list[str] = []
    warnings: list[str] = []
    if is_zero_cost_config(config):
        return _build_zero_cost_run_permission_report(config, estimate=estimate)
    uses_paid = any(
        run.provider in PAID_PROVIDERS for run in config.iter_agent_runs() if run.provider
    )
    if not uses_paid:
        return {"run_allowed": True, "run_blocked_reasons": [], "warnings": warnings}

    effective_budget = config.effective_budget()
    if config.budget is None and uses_paid:
        blocked.append("structured budget block missing for paid provider pilot config")
    elif effective_budget is None:
        blocked.append("budget cap missing")
    elif config.budget is not None:
        if estimate.get("expected_max_calls", 0) > effective_budget.max_calls:
            blocked.append(
                "expected max calls exceed budget.max_calls: "
                f"{estimate['expected_max_calls']} > {effective_budget.max_calls}"
            )
        if effective_budget.max_input_tokens is not None:
            if estimate.get("estimated_input_tokens", 0) > effective_budget.max_input_tokens:
                blocked.append("estimated input tokens exceed budget.max_input_tokens")
        if effective_budget.max_output_tokens is not None:
            if estimate.get("estimated_output_tokens", 0) > effective_budget.max_output_tokens:
                blocked.append("estimated output tokens exceed budget.max_output_tokens")

    cap = effective_budget.max_total_usd if effective_budget else config.budget_cap_usd
    upper = estimate.get("known_cost_upper_bound_usd")
    if cap is None:
        blocked.append("budget cap missing")
    elif upper is not None and upper > cap:
        blocked.append(f"estimated cost ${upper:.8f} exceeds budget cap ${cap:.8f}")

    if effective_budget and effective_budget.require_explicit_paid_approval and not config.allow_paid_calls:
        blocked.append("allow_paid_calls is false while budget.require_explicit_paid_approval is true")

    if not estimate.get("pricing_known") and (
        effective_budget is None or effective_budget.strict_pricing
    ):
        blocked.append("pricing unknown for one or more paid provider agent runs")

    if provider_registry is not None:
        for agent_run in config.iter_agent_runs():
            provider = agent_run.provider
            if provider not in PAID_PROVIDERS:
                continue
            entry = provider_registry.providers.get(provider)
            if entry is not None and entry.enabled is False and not provider_is_enabled(provider_registry, provider):
                warnings.append(
                    f"Provider {provider!r} is disabled in registry and no API key is configured."
                )
            if not provider_model_id_configured(provider_registry, provider, agent_run.model):
                blocked.append(
                    f"model ID missing for provider {provider!r}; set model in config or model env var"
                )
            if not provider_api_key_configured(
                provider_registry,
                provider,
                override_env=agent_run.api_key_env,
            ):
                blocked.append(f"provider key missing for {provider!r}")

    return {
        "run_allowed": not blocked,
        "run_blocked_reasons": blocked,
        "warnings": warnings,
    }


def _build_zero_cost_run_permission_report(
    config: ExperimentConfig,
    *,
    estimate: dict[str, Any],
) -> dict[str, Any]:
    from causal_agent_bench.runners.config import is_free_tier_agent_run

    blocked: list[str] = []
    warnings: list[str] = []
    upper = estimate.get("known_cost_upper_bound_usd")
    if upper not in (0, 0.0):
        blocked.append(f"zero_cost config has non-zero estimated cost ${upper}")
    if config.allow_paid_calls:
        blocked.append("allow_paid_calls must be false in zero_cost mode")
    effective_budget = config.effective_budget()
    cap = effective_budget.max_total_usd if effective_budget else config.budget_cap_usd
    if cap not in (None, 0.0):
        blocked.append(f"zero_cost config budget cap must be 0; got ${cap}")
    for agent_run in config.iter_agent_runs():
        provider = agent_run.provider
        if provider in {"openai", "anthropic"}:
            blocked.append(f"zero_cost mode blocks provider {provider!r}")
        elif provider in PAID_PROVIDERS and not is_free_tier_agent_run(agent_run):
            blocked.append(
                f"agent run {agent_run.run_id()!r} uses paid provider {provider!r} "
                "without free_tier zero pricing"
            )
    return {
        "run_allowed": not blocked,
        "run_blocked_reasons": blocked,
        "warnings": warnings,
    }


def _load_pricing_registry(config: ExperimentConfig, root: Path) -> Any | None:
    path = config.resolved_pricing_registry_path(root)
    if path is None or not path.exists():
        return None
    return load_model_pricing_registry(path)


def _load_provider_registry(config: ExperimentConfig, root: Path) -> Any | None:
    path = config.resolved_provider_registry_path(root)
    if path is None or not path.exists():
        return None
    return load_provider_registry(path)


def _input_tokens_upper_bound(agent_run: Any, llm_calls_upper_bound: int) -> int:
    estimate = agent_run.extra.get("input_tokens_per_call_estimate", 0)
    try:
        per_call = int(estimate)
    except (TypeError, ValueError):
        per_call = 0
    return max(0, per_call) * llm_calls_upper_bound


def _budget_status(cost: float, cap: float | None, known: bool) -> str:
    if cap is None:
        return "no_run_cap"
    if not known:
        return "unknown_cost"
    return "within_budget" if cost <= cap else "exceeds_budget"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
