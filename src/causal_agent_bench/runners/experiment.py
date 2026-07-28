from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.commercial import (
    enforce_budget_preflight,
    enforce_paid_call_policy,
    finalize_commercial_run_metadata,
)
from causal_agent_bench.runners.config import (
    AgentRunConfig,
    ExperimentConfig,
    load_experiment_config,
)
from causal_agent_bench.runners.errors import runner_error_record
from causal_agent_bench.runners.execution import execute_agent_on_instance
from causal_agent_bench.runners.limits import RunLimiter
from causal_agent_bench.runners.metadata import (
    build_run_metadata,
    persist_run_setup,
    prepare_run_directory,
)
from causal_agent_bench.runners.redaction import sanitize_metadata
from causal_agent_bench.runners.resume import (
    completed_run_keys,
    failed_run_keys,
    run_key,
    write_checkpoint,
)
from causal_agent_bench.runners.run_completion import write_incomplete_run_record
from causal_agent_bench.schemas import BenchmarkInstance, Trajectory
from causal_agent_bench.scoring import score_run
from causal_agent_bench.trajectory import write_trajectory_markdown
from causal_agent_bench.utils.io import read_jsonl, write_json, write_jsonl


def run_experiment_from_config(
    config_path: str | Path,
    *,
    resume_dir: str | Path | None = None,
    retry_failed: bool = False,
    checkpoint_every: int = 1,
    force_resume: bool = False,
    limiter_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config, raw_config = load_experiment_config(config_path)
    return run_experiment(
        config,
        raw_config=raw_config,
        resume_dir=resume_dir,
        retry_failed=retry_failed,
        checkpoint_every=checkpoint_every,
        force_resume=force_resume,
        limiter_overrides=limiter_overrides,
    )


def run_experiment(
    config: ExperimentConfig,
    *,
    raw_config: dict[str, Any] | None = None,
    resume_dir: str | Path | None = None,
    retry_failed: bool = False,
    checkpoint_every: int = 1,
    force_resume: bool = False,
    limiter_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = raw_config or config.model_dump(mode="json")
    enforce_paid_call_policy(config)
    cost_estimate = enforce_budget_preflight(config)
    benchmark_path = config.resolved_benchmark_path()
    instances = read_jsonl(benchmark_path, BenchmarkInstance)
    if config.max_instances is not None:
        instances = instances[: config.max_instances]
    limiter = RunLimiter.from_config(config, cli_overrides=limiter_overrides)
    if limiter.max_instances is not None:
        instances = instances[: limiter.max_instances]
    if config.instance_metadata_filter:
        instances = [
            instance
            for instance in instances
            if all(
                instance.base_task.metadata.get(key) == value
                for key, value in config.instance_metadata_filter.items()
            )
        ]
    run_dir = prepare_run_directory(config, resume_dir=resume_dir)
    config_digest = stable_hash(raw)
    if resume_dir is not None:
        _check_resume_config_hash(run_dir, config_digest, force_resume=force_resume)
        _record_resume_event(run_dir, config_digest)
    if resume_dir is None:
        persist_run_setup(
            run_dir,
            config,
            raw,
            len(instances),
            config_hash=config_digest,
            cost_estimate=cost_estimate,
        )
    else:
        metadata = sanitize_metadata(
            build_run_metadata(
                config,
                config_digest,
                len(instances),
                cost_estimate=cost_estimate,
            )
        )
        write_json(run_dir / "run_metadata.json", metadata)
        write_json(run_dir / "metadata.json", metadata)
    write_jsonl(run_dir / "instances.jsonl", instances)

    trajectories_path = run_dir / "trajectories.jsonl"
    errors_path = run_dir / "errors.jsonl"
    if resume_dir is None:
        trajectories_path.write_text("", encoding="utf-8")
        errors_path.write_text("", encoding="utf-8")
    else:
        trajectories_path.touch(exist_ok=True)
        errors_path.touch(exist_ok=True)

    completed = completed_run_keys(run_dir) if resume_dir is not None else set()
    if resume_dir is not None and retry_failed:
        completed -= failed_run_keys(run_dir, retriable_only=False, exclude_skipped=True)
    trajectories: list[Trajectory] = []
    errors: list[dict[str, Any]] = []
    agent_runs = config.iter_agent_runs()
    if limiter.max_agents is not None:
        agent_runs = agent_runs[: limiter.max_agents]
    total = len(instances) * len(agent_runs) * config.num_repeats
    if limiter.max_trajectories is not None:
        total = min(total, limiter.max_trajectories)
    attempted = 0
    run_cost_usd = 0.0
    agent_costs_usd: dict[str, float] = {}

    limiter_stopped = False
    for repeat in range(config.num_repeats):
        if limiter_stopped:
            break
        for agent_index, agent_run in enumerate(agent_runs):
            if limiter_stopped:
                break
            agent_run_id = agent_run.run_id()
            agent_costs_usd.setdefault(agent_run_id, 0.0)
            for instance_index, instance in enumerate(instances):
                key = run_key(agent_run_id, instance.instance_id, repeat)
                if key in completed:
                    continue
                stop_reason = limiter.should_stop_before_trajectory(len(completed))
                if stop_reason is not None:
                    limiter.write_stop_checkpoint(
                        run_dir,
                        completed=len(completed),
                        total=total,
                        errors=len(errors),
                        reason=stop_reason,
                    )
                    write_incomplete_run_record(
                        run_dir,
                        reason=f"limiter stop: {stop_reason}",
                    )
                    limiter_stopped = True
                    break
                budget_error = _preflight_budget_error(
                    config=config,
                    agent_run=agent_run,
                    agent_run_id=agent_run_id,
                    instance_id=instance.instance_id,
                    repeat=repeat,
                    run_cost_usd=run_cost_usd,
                    agent_cost_usd=agent_costs_usd[agent_run_id],
                )
                if budget_error is not None:
                    _append_jsonl(errors_path, budget_error)
                    errors.append(budget_error)
                    continue
                attempted += 1
                seed = _derived_seed(config.seed, repeat, agent_index, instance_index)
                try:
                    trajectory = execute_agent_on_instance(
                        agent_name=agent_run.agent,
                        instance=instance,
                        run_id=run_dir.name,
                        seed=seed,
                        repeat=repeat,
                        max_steps=limiter.effective_max_steps(config.max_steps),
                        save_observations=config.save_observations,
                        save_agent_thoughts=config.save_agent_thoughts,
                        agent_run_id=agent_run_id,
                        agent_kwargs=_agent_kwargs(agent_run, config, limiter=limiter),
                        raac_config=config.resolved_raac(agent_run),
                    )
                except Exception as exc:
                    record = runner_error_record(
                        agent_name=agent_run_id,
                        instance_id=instance.instance_id,
                        repeat=repeat,
                        exc=exc,
                        skipped=True,
                    )
                    _append_jsonl(errors_path, record)
                    errors.append(record)
                    if config.fail_fast:
                        raise
                    continue
                trajectory_cost = _trajectory_cost(trajectory)
                if trajectory_cost is not None:
                    run_cost_usd = round(run_cost_usd + trajectory_cost, 8)
                    agent_costs_usd[agent_run_id] = round(
                        agent_costs_usd[agent_run_id] + trajectory_cost,
                        8,
                    )
                    trajectory.metadata["run_cost_so_far_usd"] = run_cost_usd
                    trajectory.metadata["agent_cost_so_far_usd"] = agent_costs_usd[agent_run_id]
                task_budget_error = _postflight_task_budget_error(
                    config=config,
                    agent_run=agent_run,
                    agent_run_id=agent_run_id,
                    trajectory=trajectory,
                    trajectory_cost=trajectory_cost,
                    repeat=repeat,
                )
                if task_budget_error is not None:
                    _append_jsonl(errors_path, task_budget_error)
                    errors.append(task_budget_error)
                _append_jsonl(trajectories_path, trajectory)
                if config.write_markdown_trajectories:
                    write_trajectory_markdown(trajectory, run_dir / "trajectories_md")
                trajectories.append(trajectory)
                completed.add(key)
                limiter.note_trajectory_completed()
                if checkpoint_every > 0 and (len(completed) % checkpoint_every == 0 or len(completed) == total):
                    write_checkpoint(
                        run_dir,
                        completed=len(completed),
                        total=total,
                        errors=len(errors),
                    )
                if attempted % 25 == 0 or attempted == total:
                    print(f"completed {len(completed)}/{total} trajectories in {run_dir}")

    if config.auto_score and len(completed) >= total:
        score_run(run_dir)

    finalize_commercial_run_metadata(run_dir)

    return {
        "run_dir": run_dir,
        "trajectories": trajectories,
        "errors": errors,
        "completed_keys": completed,
    }


def _derived_seed(base_seed: int, repeat: int, agent_index: int, instance_index: int) -> int:
    return base_seed + repeat * 1_000_000 + agent_index * 10_000 + instance_index


def _agent_kwargs(
    agent_run: Any,
    config: ExperimentConfig,
    *,
    limiter: RunLimiter | None = None,
) -> dict[str, Any]:
    pricing_registry = _optional_pricing_registry(config)
    max_tokens = agent_run.max_tokens
    if limiter is not None:
        max_tokens = limiter.effective_max_tokens(max_tokens)
    return {
        "provider": agent_run.provider,
        "model": agent_run.model,
        "temperature": agent_run.temperature,
        "max_tokens": max_tokens,
        "retry_count": agent_run.retry_count,
        "timeout": agent_run.timeout,
        "pricing": config.resolved_pricing(agent_run, pricing_registry=pricing_registry),
        "base_url": agent_run.base_url,
        "api_key_env": agent_run.api_key_env,
        "cache_dir": agent_run.cache_dir,
        "max_cost_per_task_usd": (
            agent_run.task_budget_cap_usd
            if agent_run.task_budget_cap_usd is not None
            else config.task_budget_cap_usd
        ),
        **agent_run.extra,
    }


def _optional_pricing_registry(config: ExperimentConfig) -> Any | None:
    path = config.resolved_pricing_registry_path()
    if path is None or not path.exists():
        return None
    from causal_agent_bench.runners.registries import load_model_pricing_registry

    return load_model_pricing_registry(path)


def _preflight_budget_error(
    *,
    config: ExperimentConfig,
    agent_run: AgentRunConfig,
    agent_run_id: str,
    instance_id: str,
    repeat: int,
    run_cost_usd: float,
    agent_cost_usd: float,
) -> dict[str, Any] | None:
    run_cap = config.budget_cap_usd
    if run_cap is not None and run_cost_usd >= run_cap and _may_spend_money(agent_run):
        return _budget_error_record(
            agent_name=agent_run_id,
            instance_id=instance_id,
            repeat=repeat,
            scope="run",
            cap_usd=run_cap,
            spent_usd=run_cost_usd,
            skipped=True,
        )
    agent_cap = agent_run.budget_cap_usd
    if agent_cap is not None and agent_cost_usd >= agent_cap and _may_spend_money(agent_run):
        return _budget_error_record(
            agent_name=agent_run_id,
            instance_id=instance_id,
            repeat=repeat,
            scope="agent",
            cap_usd=agent_cap,
            spent_usd=agent_cost_usd,
            skipped=True,
        )
    return None


def _postflight_task_budget_error(
    *,
    config: ExperimentConfig,
    agent_run: AgentRunConfig,
    agent_run_id: str,
    trajectory: Trajectory,
    trajectory_cost: float | None,
    repeat: int,
) -> dict[str, Any] | None:
    cap = (
        agent_run.task_budget_cap_usd
        if agent_run.task_budget_cap_usd is not None
        else config.task_budget_cap_usd
    )
    if cap is None or trajectory_cost is None or trajectory_cost <= cap:
        return None
    return _budget_error_record(
        agent_name=agent_run_id,
        instance_id=trajectory.instance_id,
        repeat=repeat,
        scope="task",
        cap_usd=cap,
        spent_usd=trajectory_cost,
        skipped=False,
    )


def _budget_error_record(
    *,
    agent_name: str,
    instance_id: str,
    repeat: int,
    scope: str,
    cap_usd: float,
    spent_usd: float,
    skipped: bool,
) -> dict[str, Any]:
    return {
        "agent": agent_name,
        "instance": instance_id,
        "repeat": repeat,
        "error_type": "BudgetExceededError",
        "message": (
            f"{scope} budget cap reached: spent ${spent_usd:.8f}, cap ${cap_usd:.8f}"
        ),
        "budget_scope": scope,
        "budget_cap_usd": cap_usd,
        "spent_usd": round(spent_usd, 8),
        "skipped": skipped,
    }


def _trajectory_cost(trajectory: Trajectory) -> float | None:
    value = trajectory.metadata.get("estimated_cost_usd")
    if value is None:
        value = trajectory.token_cost_metadata.get("estimated_cost_usd")
    return float(value) if value is not None else None


def _may_spend_money(agent_run: AgentRunConfig, *, config: ExperimentConfig | None = None) -> bool:
    from causal_agent_bench.runners.config import is_free_tier_agent_run

    if agent_run.provider in {None, "local_stub", "local_openai"}:
        return False
    if is_free_tier_agent_run(agent_run):
        return False
    return not (config is not None and config.cost_mode == "zero_cost")


def _check_resume_config_hash(run_dir: Path, config_digest: str, *, force_resume: bool = False) -> None:
    hash_path = run_dir / "config_hash.txt"
    if not hash_path.exists():
        return
    previous = hash_path.read_text(encoding="utf-8").strip()
    if previous and previous != config_digest and not force_resume:
        raise ValueError(
            f"resume config hash mismatch for {run_dir}: existing {previous}, new {config_digest}. "
            "Pass --force-resume to override."
        )


def _record_resume_event(run_dir: Path, config_digest: str) -> None:
    event_path = run_dir / "resume_events.jsonl"
    payload = {
        "event": "resume",
        "config_hash": config_digest,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _append_jsonl(path: Path, row: BaseModel | dict[str, Any]) -> None:
    payload = row.model_dump(mode="json") if isinstance(row, BaseModel) else row
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
