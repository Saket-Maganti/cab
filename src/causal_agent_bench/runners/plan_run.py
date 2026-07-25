from __future__ import annotations

from pathlib import Path
from typing import Any

from causal_agent_bench.runners.config import load_experiment_config
from causal_agent_bench.runners.costing import estimate_config_cost
from causal_agent_bench.runners.limits import estimate_runtime_category, warn_if_huge_local_run
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.utils.io import read_jsonl


def plan_run(config_path: str | Path) -> dict[str, Any]:
    config, _raw = load_experiment_config(config_path)
    benchmark_path = config.resolved_benchmark_path()
    instances = read_jsonl(benchmark_path, BenchmarkInstance)
    if config.max_instances is not None:
        instances = instances[: config.max_instances]
    if config.limits and config.limits.max_instances is not None:
        instances = instances[: config.limits.max_instances]
    agent_runs = config.iter_agent_runs()
    if config.limits and config.limits.max_agents is not None:
        agent_runs = agent_runs[: config.limits.max_agents]
    expected = len(instances) * len(agent_runs) * config.num_repeats
    if config.limits and config.limits.max_trajectories is not None:
        expected = min(expected, config.limits.max_trajectories)

    providers = sorted({run.provider or "local_stub" for run in config.iter_agent_runs()})
    provider_set = set(providers)
    category, est_seconds = estimate_runtime_category(
        expected_trajectories=expected,
        max_steps=config.max_steps,
        provider_types=provider_set,
    )
    cost = estimate_config_cost(config_path)
    warnings = warn_if_huge_local_run(config, expected)
    if config.cost_mode == "zero_cost":
        warnings.append("Zero-cost / preliminary evidence only.")
    if config.scientific_evidence_level == "preliminary_or_engineering":
        warnings.append("scientific_evidence_level=preliminary_or_engineering")

    safe_now = category in {"micro_debug", "fast_local"} and not config.allow_paid_calls
    if "local_openai" in provider_set and category != "micro_debug":
        safe_now = False

    return {
        "config": str(config_path),
        "run_name": config.run_name,
        "dataset": str(benchmark_path),
        "n_instances": len(instances),
        "n_agents": len(agent_runs),
        "agents": [run.run_id() for run in agent_runs],
        "expected_trajectories": expected,
        "max_steps": config.max_steps,
        "providers": providers,
        "provider_type": config.provider_type,
        "cost_mode": config.cost_mode,
        "allow_paid_calls": config.allow_paid_calls,
        "estimated_cost_usd_upper": cost.get("upper_bound_usd"),
        "estimated_runtime_category": category,
        "estimated_runtime_seconds": est_seconds,
        "scientific_evidence_level": config.scientific_evidence_level,
        "evidence_level": config.scientific_evidence_level,
        "warnings": warnings,
        "safe_to_run_now": safe_now,
        "limits": config.limits.model_dump(mode="json") if config.limits else None,
    }


def format_plan_report(plan: dict[str, Any]) -> str:
    lines = [
        "# Run plan",
        "",
        f"- **Config:** `{plan['config']}`",
        f"- **Run name:** {plan['run_name']}",
        f"- **Dataset:** `{plan['dataset']}`",
        f"- **Instances:** {plan['n_instances']}",
        f"- **Agents:** {', '.join(plan['agents'])}",
        f"- **Expected trajectories:** {plan['expected_trajectories']}",
        f"- **Max steps:** {plan['max_steps']}",
        f"- **Providers:** {', '.join(plan['providers'])}",
        f"- **Cost mode:** {plan['cost_mode']}",
        f"- **Allow paid calls:** {plan['allow_paid_calls']}",
        f"- **Est. cost upper bound:** ${plan['estimated_cost_usd_upper']}",
        f"- **Runtime category:** {plan['estimated_runtime_category']}",
        f"- **Est. runtime (s):** {plan['estimated_runtime_seconds']:.0f}",
        f"- **Evidence level:** {plan['evidence_level']}",
        f"- **Safe to run now:** {plan['safe_to_run_now']}",
        "",
        "## Warnings",
    ]
    if plan["warnings"]:
        lines.extend(f"- {warning}" for warning in plan["warnings"])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
