from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.config import ExperimentConfig, load_experiment_config
from causal_agent_bench.runners.errors import runner_error_record
from causal_agent_bench.runners.execution import execute_agent_on_instance
from causal_agent_bench.runners.metadata import persist_run_setup, prepare_run_directory
from causal_agent_bench.runners.resume import completed_run_keys
from causal_agent_bench.schemas import BenchmarkInstance, Trajectory
from causal_agent_bench.scoring import score_run
from causal_agent_bench.utils.io import read_jsonl, write_jsonl


def run_experiment_from_config(
    config_path: str | Path,
    *,
    resume_dir: str | Path | None = None,
) -> dict[str, Any]:
    config, raw_config = load_experiment_config(config_path)
    return run_experiment(config, raw_config=raw_config, resume_dir=resume_dir)


def run_experiment(
    config: ExperimentConfig,
    *,
    raw_config: dict[str, Any] | None = None,
    resume_dir: str | Path | None = None,
) -> dict[str, Any]:
    raw = raw_config or config.model_dump(mode="json")
    benchmark_path = config.resolved_benchmark_path()
    instances = read_jsonl(benchmark_path, BenchmarkInstance)
    run_dir = prepare_run_directory(config, resume_dir=resume_dir)
    config_digest = stable_hash(raw)
    if resume_dir is not None:
        _check_resume_config_hash(run_dir, config_digest)
    persist_run_setup(run_dir, config, raw, len(instances), config_hash=config_digest)
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
    trajectories: list[Trajectory] = []
    errors: list[dict[str, Any]] = []
    total = len(instances) * len(config.agents) * config.num_repeats
    attempted = 0

    for repeat in range(config.num_repeats):
        for agent_index, agent_name in enumerate(config.agents):
            for instance_index, instance in enumerate(instances):
                key = (agent_name, instance.instance_id, repeat)
                if key in completed:
                    continue
                attempted += 1
                seed = _derived_seed(config.seed, repeat, agent_index, instance_index)
                try:
                    trajectory = execute_agent_on_instance(
                        agent_name=agent_name,
                        instance=instance,
                        run_id=run_dir.name,
                        seed=seed,
                        repeat=repeat,
                        max_steps=config.max_steps,
                        save_observations=config.save_observations,
                        save_agent_thoughts=config.save_agent_thoughts,
                    )
                except Exception as exc:
                    record = runner_error_record(
                        agent_name=agent_name,
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
                _append_jsonl(trajectories_path, trajectory)
                trajectories.append(trajectory)
                completed.add(key)
                if attempted % 25 == 0 or attempted == total:
                    print(f"completed {len(completed)}/{total} trajectories in {run_dir}")

    if config.auto_score:
        score_run(run_dir)

    return {
        "run_dir": run_dir,
        "trajectories": trajectories,
        "errors": errors,
        "completed_keys": completed,
    }


def _derived_seed(base_seed: int, repeat: int, agent_index: int, instance_index: int) -> int:
    return base_seed + repeat * 1_000_000 + agent_index * 10_000 + instance_index


def _check_resume_config_hash(run_dir: Path, config_digest: str) -> None:
    hash_path = run_dir / "config_hash.txt"
    if not hash_path.exists():
        return
    previous = hash_path.read_text(encoding="utf-8").strip()
    if previous and previous != config_digest:
        raise ValueError(
            f"resume config hash mismatch for {run_dir}: existing {previous}, new {config_digest}"
        )


def _append_jsonl(path: Path, row: BaseModel | dict[str, Any]) -> None:
    payload = row.model_dump(mode="json") if isinstance(row, BaseModel) else row
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
