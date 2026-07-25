from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from causal_agent_bench.runners.batch import (
    build_failure_report,
    merge_batch_shards,
    partition_sorted,
    plan_batch_shards,
)
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment
from causal_agent_bench.runners.resume import (
    completed_run_keys,
    failed_run_keys,
)
from causal_agent_bench.schemas import Trajectory
from causal_agent_bench.utils.io import read_json, read_jsonl


def _smoke_config(tmp_path: Path, **overrides) -> ExperimentConfig:
    data = {
        "seed": 7,
        "run_name": "batch_smoke",
        "benchmark_path": "data/sample/instances.jsonl",
        "agents": ["random_tool_agent"],
        "max_steps": 4,
        "num_repeats": 1,
        "output_dir": str(tmp_path / "results"),
        "auto_score": False,
    }
    data.update(overrides)
    return ExperimentConfig.model_validate(data)


def test_partition_sorted_is_deterministic():
    items = ["c", "a", "b", "d"]
    assert partition_sorted(items, 0, 2) == ["a", "c"]
    assert partition_sorted(items, 1, 2) == ["b", "d"]


def test_plan_batch_shards_writes_manifest(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "seed": 1,
                "run_name": "plan_test",
                "benchmark_path": "data/sample/instances.jsonl",
                "agents": ["random_tool_agent", "scripted_oracle_agent"],
                "max_steps": 4,
                "num_repeats": 1,
                "output_dir": str(tmp_path / "results"),
            }
        ),
        encoding="utf-8",
    )
    manifest = plan_batch_shards(
        config_path,
        shard_by="instance",
        shard_count=3,
        output_dir=tmp_path / "batch",
    )
    assert manifest["shard_count"] == 3
    assert manifest["n_expected_total"] == 9 * 2
    assert len(manifest["shards"]) == 3
    assert (tmp_path / "batch" / "batch_manifest.json").exists()
    for shard in manifest["shards"]:
        assert Path(shard["config_path"]).exists()
        assert Path(shard["instances_path"]).exists()


def test_merge_batch_shards_combines_without_duplicates(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "seed": 1,
                "run_name": "merge_test",
                "benchmark_path": "data/sample/instances.jsonl",
                "agents": ["random_tool_agent"],
                "max_steps": 2,
                "num_repeats": 1,
                "output_dir": str(tmp_path / "results"),
            }
        ),
        encoding="utf-8",
    )
    batch_dir = tmp_path / "batch"
    manifest = plan_batch_shards(
        config_path,
        shard_by="instance",
        shard_count=2,
        output_dir=batch_dir,
    )
    for shard in manifest["shards"]:
        shard_dir = batch_dir / "shards" / shard["shard_id"]
        run_dir = shard_dir / "run" / f"test_{shard['shard_id']}"
        run_dir.mkdir(parents=True)
        trajectories = []
        for row in shard["expected_keys"]:
            trajectories.append(
                _fake_trajectory(
                    run_id=run_dir.name,
                    agent=row["agent"],
                    instance_id=row["instance_id"],
                    repeat=row["repeat"],
                )
            )
        with (run_dir / "trajectories.jsonl").open("w", encoding="utf-8") as handle:
            for trajectory in trajectories:
                handle.write(json.dumps(trajectory.model_dump(mode="json"), sort_keys=True) + "\n")
        (run_dir / "errors.jsonl").write_text("", encoding="utf-8")

    merged = merge_batch_shards(batch_dir, auto_score=False)
    merged_run = Path(merged["merged_run_dir"])
    assert merged["n_trajectories"] == manifest["n_expected_total"]
    assert len(read_jsonl(merged_run / "trajectories.jsonl", Trajectory)) == manifest["n_expected_total"]
    assert read_json(merged_run / "merge_report.json")["n_missing_keys"] == 0
    assert (merged_run / "failure_report.md").exists()


def test_merge_detects_duplicates(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "seed": 1,
                "run_name": "dup_test",
                "benchmark_path": "data/sample/instances.jsonl",
                "agents": ["random_tool_agent"],
                "max_steps": 2,
                "num_repeats": 1,
                "output_dir": str(tmp_path / "results"),
            }
        ),
        encoding="utf-8",
    )
    batch_dir = tmp_path / "batch"
    manifest = plan_batch_shards(
        config_path,
        shard_by="instance",
        shard_count=1,
        output_dir=batch_dir,
    )
    shard = manifest["shards"][0]
    shard_dir = batch_dir / "shards" / shard["shard_id"]
    run_dir = shard_dir / "run" / "test_dup"
    run_dir.mkdir(parents=True)
    row = shard["expected_keys"][0]
    trajectory = _fake_trajectory(
        run_id="test_dup",
        agent=row["agent"],
        instance_id=row["instance_id"],
        repeat=row["repeat"],
    )
    payload = json.dumps(trajectory.model_dump(mode="json"), sort_keys=True) + "\n"
    (run_dir / "trajectories.jsonl").write_text(payload + payload, encoding="utf-8")
    (run_dir / "errors.jsonl").write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate"):
        merge_batch_shards(batch_dir, auto_score=False)


def test_checkpoint_written_during_run(tmp_path):
    result = run_experiment(_smoke_config(tmp_path, auto_score=False), checkpoint_every=3)
    run_dir = result["run_dir"]
    checkpoint = read_json(run_dir / "checkpoint.json")
    assert checkpoint["completed"] == 9
    assert checkpoint["total"] == 9


def test_failed_run_keys_exclude_skipped_errors(tmp_path):
    result = run_experiment(_smoke_config(tmp_path, agents=["not_an_agent"], auto_score=False))
    run_dir = result["run_dir"]
    assert failed_run_keys(run_dir, exclude_skipped=True) == set()
    assert failed_run_keys(run_dir, exclude_skipped=False, retriable_only=False)


def test_failure_report_counts_missing_pairs(tmp_path):
    result = run_experiment(_smoke_config(tmp_path, auto_score=False))
    run_dir = result["run_dir"]
    report = build_failure_report(run_dir)
    assert report["n_completed"] == len(completed_run_keys(run_dir))
    assert report["n_expected"] >= report["n_completed"]


def test_end_to_end_shard_run_and_merge(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "seed": 3,
                "run_name": "e2e_batch",
                "benchmark_path": "data/sample/instances.jsonl",
                "agents": ["random_tool_agent"],
                "max_steps": 2,
                "num_repeats": 1,
                "output_dir": str(tmp_path / "results"),
                "auto_score": False,
            }
        ),
        encoding="utf-8",
    )
    batch_dir = tmp_path / "batch"
    manifest = plan_batch_shards(
        config_path,
        shard_by="intervention_family",
        shard_count=2,
        output_dir=batch_dir,
    )
    from causal_agent_bench.runners.batch import run_batch_shard

    for shard in manifest["shards"]:
        run_batch_shard(shard["config_path"], checkpoint_every=1)
    merged = merge_batch_shards(batch_dir, auto_score=False)
    assert merged["n_trajectories"] == manifest["n_expected_total"]


def _fake_trajectory(*, run_id: str, agent: str, instance_id: str, repeat: int) -> Trajectory:
    return Trajectory.model_validate(
        {
            "run_id": run_id,
            "instance_id": instance_id,
            "agent_name": agent,
            "steps": [],
            "final_answer": "stub",
            "terminated_reason": "completed",
            "metadata": {"repeat": repeat},
        }
    )
