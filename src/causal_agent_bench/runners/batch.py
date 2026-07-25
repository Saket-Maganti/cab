from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.config import ExperimentConfig, load_experiment_config
from causal_agent_bench.runners.experiment import run_experiment_from_config
from causal_agent_bench.runners.metadata import persist_run_setup
from causal_agent_bench.runners.resume import (
    RunKey,
    completed_run_keys,
    duplicate_run_keys,
    failed_run_keys,
    pending_run_keys,
    run_key,
    write_checkpoint,
)
from causal_agent_bench.schemas import BenchmarkInstance, Trajectory
from causal_agent_bench.scoring import score_run
from causal_agent_bench.utils.io import git_commit, read_json, read_jsonl, write_json, write_jsonl

ShardBy = Literal["instance", "agent", "intervention_family"]


class BatchShardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shard_by: ShardBy
    shard_index: int = Field(ge=0)
    shard_count: int = Field(ge=1)
    batch_id: str | None = None

    @model_validator(mode="after")
    def validate_index(self) -> BatchShardConfig:
        if self.shard_index >= self.shard_count:
            raise ValueError(
                f"shard_index ({self.shard_index}) must be < shard_count ({self.shard_count})"
            )
        return self


@dataclass(frozen=True)
class ShardPlan:
    shard_id: str
    shard_index: int
    shard_count: int
    shard_by: ShardBy
    config_path: Path
    expected_keys: set[RunKey]
    instance_ids: list[str]
    agent_run_ids: list[str]
    intervention_families: list[str]


def instance_intervention_family(instance: BenchmarkInstance) -> str:
    if instance.intervention is None:
        return "clean"
    return instance.intervention.family


def expected_run_keys(
    config: ExperimentConfig,
    instances: list[BenchmarkInstance],
) -> set[RunKey]:
    keys: set[RunKey] = set()
    for repeat in range(config.num_repeats):
        for agent_run in config.iter_agent_runs():
            agent_id = agent_run.run_id()
            for instance in instances:
                keys.add(run_key(agent_id, instance.instance_id, repeat))
    return keys


def partition_sorted(items: list[str], shard_index: int, shard_count: int) -> list[str]:
    return [item for index, item in enumerate(sorted(items)) if index % shard_count == shard_index]


def filter_instances_for_shard(
    instances: list[BenchmarkInstance],
    shard_by: ShardBy,
    shard_index: int,
    shard_count: int,
    agent_run_ids: list[str] | None = None,
) -> tuple[list[BenchmarkInstance], list[str], list[str]]:
    if shard_by == "instance":
        chosen = set(partition_sorted([inst.instance_id for inst in instances], shard_index, shard_count))
        filtered = [inst for inst in instances if inst.instance_id in chosen]
        return filtered, sorted(chosen), agent_run_ids or []

    if shard_by == "intervention_family":
        families_all = sorted({instance_intervention_family(inst) for inst in instances})
        chosen_families = partition_sorted(families_all, shard_index, shard_count)
        chosen = set(chosen_families)
        filtered = [inst for inst in instances if instance_intervention_family(inst) in chosen]
        return filtered, sorted({inst.instance_id for inst in filtered}), chosen_families

    return instances, sorted({inst.instance_id for inst in instances}), []


def filter_agents_for_shard(
    config: ExperimentConfig,
    shard_by: ShardBy,
    shard_index: int,
    shard_count: int,
) -> tuple[list[Any], list[str]]:
    agent_runs = config.iter_agent_runs()
    if shard_by != "agent":
        return agent_runs, [run.run_id() for run in agent_runs]
    chosen = partition_sorted([run.run_id() for run in agent_runs], shard_index, shard_count)
    chosen_set = set(chosen)
    filtered = [run for run in agent_runs if run.run_id() in chosen_set]
    return filtered, chosen


def plan_batch_shards(
    config_path: str | Path,
    *,
    shard_by: ShardBy,
    shard_count: int,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config, raw = load_experiment_config(config_path)
    benchmark_path = config.resolved_benchmark_path()
    instances = read_jsonl(benchmark_path, BenchmarkInstance)
    if config.instance_metadata_filter:
        instances = [
            instance
            for instance in instances
            if all(
                instance.base_task.metadata.get(key) == value
                for key, value in config.instance_metadata_filter.items()
            )
        ]

    batch_root = Path(output_dir) if output_dir else Path(config.output_dir) / f"{config.run_name}_batch"
    batch_root.mkdir(parents=True, exist_ok=True)
    shards_root = batch_root / "shards"
    shards_root.mkdir(parents=True, exist_ok=True)

    full_expected = expected_run_keys(config, instances)
    shard_plans: list[dict[str, Any]] = []

    for shard_index in range(shard_count):
        filtered_instances, instance_ids, families = filter_instances_for_shard(
            instances,
            shard_by,
            shard_index,
            shard_count,
        )
        filtered_agents, agent_ids = filter_agents_for_shard(config, shard_by, shard_index, shard_count)

        shard_config = config.model_copy(deep=True)
        if shard_by == "agent":
            shard_config.agent_runs = filtered_agents
            shard_config.agents = []
        shard_id = f"shard_{shard_index:03d}"
        shard_config.run_name = f"{config.run_name}__{shard_id}"
        shard_config.output_dir = str(shards_root / shard_id)

        shard_dir = shards_root / shard_id
        shard_dir.mkdir(parents=True, exist_ok=True)
        instances_path = shard_dir / "instances.jsonl"
        write_jsonl(instances_path, filtered_instances)

        raw_shard = dict(raw)
        raw_shard["run_name"] = shard_config.run_name
        raw_shard["output_dir"] = shard_config.output_dir
        raw_shard["benchmark_path"] = str(instances_path)
        raw_shard.pop("benchmark_dir", None)
        if shard_by == "agent":
            raw_shard["agent_runs"] = [run.model_dump(mode="json") for run in filtered_agents]
            raw_shard["agents"] = []
        shard_config_path = shard_dir / "config.yaml"
        shard_config_path.write_text(yaml.safe_dump(raw_shard, sort_keys=False), encoding="utf-8")

        shard_expected = expected_run_keys(shard_config, filtered_instances)
        shard_manifest = {
            "shard_id": shard_id,
            "shard_index": shard_index,
            "shard_count": shard_count,
            "shard_by": shard_by,
            "batch_id": f"{config.run_name}_batch",
            "parent_config_path": str(Path(config_path).resolve()),
            "config_path": str(shard_config_path),
            "instances_path": str(instances_path),
            "n_instances": len(filtered_instances),
            "instance_ids": instance_ids,
            "agent_run_ids": agent_ids,
            "intervention_families": families,
            "expected_keys": [_key_to_dict(key) for key in sorted(shard_expected)],
            "n_expected": len(shard_expected),
        }
        write_json(shard_dir / "shard_manifest.json", shard_manifest)
        shard_plans.append(shard_manifest)

    batch_manifest = {
        "batch_id": f"{config.run_name}_batch",
        "parent_config_path": str(Path(config_path).resolve()),
        "parent_config_hash": stable_hash(raw),
        "shard_by": shard_by,
        "shard_count": shard_count,
        "n_expected_total": len(full_expected),
        "expected_keys": [_key_to_dict(key) for key in sorted(full_expected)],
        "shards": shard_plans,
        "git_commit": git_commit(Path.cwd()),
        "scope": "Batch shard plan; merge required before treating as one experiment run.",
    }
    write_json(batch_root / "batch_manifest.json", batch_manifest)
    (batch_root / "batch_plan.md").write_text(_batch_plan_markdown(batch_manifest), encoding="utf-8")
    return batch_manifest


def run_batch_shard(
    config_path: str | Path,
    *,
    resume_dir: str | Path | None = None,
    retry_failed: bool = False,
    checkpoint_every: int = 1,
) -> dict[str, Any]:
    return run_experiment_from_config(
        config_path,
        resume_dir=resume_dir,
        retry_failed=retry_failed,
        checkpoint_every=checkpoint_every,
    )


def _find_scored_run_dir(base: Path) -> Path | None:
    if not base.exists():
        return None
    if (base / "trajectories.jsonl").exists():
        return base
    for child in sorted(base.iterdir(), reverse=True):
        if child.is_dir() and (child / "trajectories.jsonl").exists():
            return child
    return None


def find_shard_run_dir(shard_dir: Path) -> Path | None:
    run_root = shard_dir / "run"
    if run_root.exists():
        resolved = _find_scored_run_dir(run_root)
        if resolved is not None:
            return resolved
    candidates = [
        child
        for child in shard_dir.iterdir()
        if child.is_dir()
        and child.name not in {"run", "shards"}
        and (child / "trajectories.jsonl").exists()
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)[0]


def merge_batch_shards(
    batch_dir: str | Path,
    *,
    output_dir: str | Path | None = None,
    auto_score: bool = True,
    strict: bool = True,
) -> dict[str, Any]:
    batch_root = Path(batch_dir)
    manifest = read_json(batch_root / "batch_manifest.json")
    expected = {_key_from_dict(row) for row in manifest.get("expected_keys", [])}

    shard_runs: list[dict[str, Any]] = []
    merged_trajectories: list[Trajectory] = []
    merged_errors: list[dict[str, Any]] = []
    seen_keys: set[RunKey] = set()
    duplicate_keys: list[RunKey] = []

    for shard in manifest.get("shards", []):
        shard_dir = batch_root / "shards" / shard["shard_id"]
        run_dir = find_shard_run_dir(shard_dir)
        if run_dir is None:
            shard_runs.append({"shard_id": shard["shard_id"], "run_dir": None, "status": "missing"})
            continue
        trajectories = read_jsonl(run_dir / "trajectories.jsonl", Trajectory)
        errors = _read_errors(run_dir / "errors.jsonl")
        for trajectory in trajectories:
            key = run_key(
                trajectory.agent_name,
                trajectory.instance_id,
                int(trajectory.metadata.get("repeat", 0)),
            )
            if key in seen_keys:
                duplicate_keys.append(key)
            seen_keys.add(key)
            merged_trajectories.append(trajectory)
        merged_errors.extend(errors)
        shard_runs.append(
            {
                "shard_id": shard["shard_id"],
                "run_dir": str(run_dir),
                "n_trajectories": len(trajectories),
                "status": "ok",
            }
        )

    missing_keys = sorted(expected - seen_keys)
    extra_keys = sorted(seen_keys - expected)

    report = build_failure_report_from_parts(
        expected=expected,
        completed=seen_keys,
        errors=merged_errors,
        duplicate_keys=duplicate_keys,
        missing_keys=missing_keys,
        extra_keys=extra_keys,
    )

    if strict and (duplicate_keys or missing_keys or extra_keys):
        issues = []
        if duplicate_keys:
            issues.append(f"{len(duplicate_keys)} duplicate trajectory keys")
        if missing_keys:
            issues.append(f"{len(missing_keys)} missing expected keys")
        if extra_keys:
            issues.append(f"{len(extra_keys)} unexpected keys")
        raise ValueError("; ".join(issues))

    merged_root = Path(output_dir) if output_dir else batch_root / "merged"
    merged_root.mkdir(parents=True, exist_ok=True)
    merged_run = merged_root / "run"
    merged_run.mkdir(parents=True, exist_ok=True)

    parent_config = Path(manifest["parent_config_path"])
    if parent_config.exists():
        shutil.copy2(parent_config, merged_run / "config.yaml")
    (merged_run / "config_hash.txt").write_text(
        str(manifest.get("parent_config_hash", "")),
        encoding="utf-8",
    )
    write_jsonl(merged_run / "trajectories.jsonl", merged_trajectories)
    _write_errors(merged_run / "errors.jsonl", merged_errors)

    parent_config_obj, parent_raw = load_experiment_config(parent_config)
    benchmark_path = parent_config_obj.resolved_benchmark_path()
    instances = read_jsonl(benchmark_path, BenchmarkInstance)
    write_jsonl(merged_run / "instances.jsonl", instances)
    persist_run_setup(
        merged_run,
        parent_config_obj,
        parent_raw,
        len(instances),
        config_hash=manifest.get("parent_config_hash"),
    )
    write_checkpoint(
        merged_run,
        completed=len(seen_keys),
        total=len(expected),
        errors=len(merged_errors),
        extra={"merge_source": "batch_shards", "batch_dir": str(batch_root)},
    )
    write_json(merged_run / "merge_report.json", report)
    (merged_run / "failure_report.md").write_text(failure_report_markdown(report), encoding="utf-8")

    merge_manifest = {
        "batch_dir": str(batch_root),
        "merged_run_dir": str(merged_run),
        "n_trajectories": len(merged_trajectories),
        "n_errors": len(merged_errors),
        "n_duplicate_keys": len(duplicate_keys),
        "n_missing_keys": len(missing_keys),
        "shard_runs": shard_runs,
        "git_commit": git_commit(Path.cwd()),
    }
    write_json(merged_root / "merge_manifest.json", merge_manifest)

    if auto_score and merged_trajectories:
        score_run(merged_run)

    return merge_manifest


def build_failure_report(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    config_path = run_path / "config.yaml"
    expected: set[RunKey] = set()
    instances_path = run_path / "instances.jsonl"
    if config_path.exists():
        config, _ = load_experiment_config(config_path)
        if instances_path.exists():
            instances = read_jsonl(instances_path, BenchmarkInstance)
        else:
            instances = read_jsonl(config.resolved_benchmark_path(), BenchmarkInstance)
        expected = expected_run_keys(config, instances)

    completed = completed_run_keys(run_path)
    errors = _read_errors(run_path / "errors.jsonl")
    return build_failure_report_from_parts(
        expected=expected,
        completed=completed,
        errors=errors,
        duplicate_keys=duplicate_run_keys(run_path),
        missing_keys=sorted(expected - completed),
        extra_keys=[],
        failed_keys=sorted(failed_run_keys(run_path)),
        pending_keys=sorted(pending_run_keys(expected, run_path)),
    )


def build_failure_report_from_parts(
    *,
    expected: set[RunKey],
    completed: set[RunKey],
    errors: list[dict[str, Any]],
    duplicate_keys: list[RunKey],
    missing_keys: list[RunKey],
    extra_keys: list[RunKey],
    failed_keys: list[RunKey] | None = None,
    pending_keys: list[RunKey] | None = None,
) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    for row in errors:
        error_type = str(row.get("error_type", "unknown"))
        by_type[error_type] = by_type.get(error_type, 0) + 1
        agent = str(row.get("agent", "unknown"))
        by_agent[agent] = by_agent.get(agent, 0) + 1

    return {
        "n_expected": len(expected),
        "n_completed": len(completed),
        "n_errors": len(errors),
        "n_duplicate_keys": len(duplicate_keys),
        "n_missing_keys": len(missing_keys),
        "n_extra_keys": len(extra_keys),
        "duplicate_keys": [_key_to_dict(key) for key in duplicate_keys],
        "missing_keys": [_key_to_dict(key) for key in missing_keys],
        "extra_keys": [_key_to_dict(key) for key in extra_keys],
        "failed_keys": [_key_to_dict(key) for key in (failed_keys or [])],
        "pending_keys": [_key_to_dict(key) for key in (pending_keys or [])],
        "errors_by_type": dict(sorted(by_type.items())),
        "errors_by_agent": dict(sorted(by_agent.items())),
        "completion_rate": round(len(completed) / len(expected), 6) if expected else None,
    }


def failure_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Run Failure Report",
        "",
        f"- Expected pairs: `{report.get('n_expected')}`",
        f"- Completed pairs: `{report.get('n_completed')}`",
        f"- Errors logged: `{report.get('n_errors')}`",
        f"- Missing pairs: `{report.get('n_missing_keys')}`",
        f"- Duplicate keys: `{report.get('n_duplicate_keys')}`",
        f"- Completion rate: `{report.get('completion_rate')}`",
        "",
        "## Errors by type",
        "",
    ]
    for error_type, count in (report.get("errors_by_type") or {}).items():
        lines.append(f"- `{error_type}`: {count}")
    lines.extend(["", "## Errors by agent", ""])
    for agent, count in (report.get("errors_by_agent") or {}).items():
        lines.append(f"- `{agent}`: {count}")
    if report.get("missing_keys"):
        lines.extend(["", "## Missing keys (sample)", ""])
        for row in report["missing_keys"][:20]:
            lines.append(f"- `{row['agent']}` / `{row['instance_id']}` / repeat={row['repeat']}")
    return "\n".join(lines) + "\n"


def _key_to_dict(key: RunKey) -> dict[str, Any]:
    return {"agent": key[0], "instance_id": key[1], "repeat": key[2]}


def _key_from_dict(row: dict[str, Any]) -> RunKey:
    return (str(row["agent"]), str(row["instance_id"]), int(row["repeat"]))


def _read_errors(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_errors(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows),
        encoding="utf-8",
    )


def _batch_plan_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Batch Shard Plan",
        "",
        f"- Batch ID: `{manifest.get('batch_id')}`",
        f"- Shard by: `{manifest.get('shard_by')}`",
        f"- Shard count: `{manifest.get('shard_count')}`",
        f"- Expected total pairs: `{manifest.get('n_expected_total')}`",
        "",
        "| Shard | Instances | Agents | Expected pairs | Config |",
        "|---|---:|---:|---:|---|",
    ]
    for shard in manifest.get("shards", []):
        lines.append(
            f"| `{shard['shard_id']}` | {shard.get('n_instances')} | "
            f"{len(shard.get('agent_run_ids', []))} | {shard.get('n_expected')} | "
            f"`{shard.get('config_path')}` |"
        )
    lines.append("")
    return "\n".join(lines)
