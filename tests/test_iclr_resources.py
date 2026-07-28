from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from causal_agent_bench.resources import (
    bootstrap_execution_plan,
    cache_cleanup_plan,
    choose_worker_limit,
    compress_jsonl,
    duplicate_artifact_report,
    estimate_trajectory_resources,
    stream_jsonl,
)


def test_worker_modes_are_bounded() -> None:
    assert choose_worker_limit("serial", cpu_count=12, memory_gib=16)["workers"] == 1
    assert choose_worker_limit("low_memory", cpu_count=12, memory_gib=16)["workers"] == 2
    assert choose_worker_limit("four_worker", cpu_count=2, memory_gib=16)["workers"] == 2
    assert choose_worker_limit("adaptive", cpu_count=12, memory_gib=7)["workers"] == 2
    assert choose_worker_limit("adaptive", cpu_count=12, memory_gib=16)["workers"] == 4


def test_streaming_and_reproducible_compression(tmp_path: Path) -> None:
    source = tmp_path / "rows.jsonl"
    source.write_text(
        "\n".join(json.dumps({"index": index}) for index in range(5)) + "\n",
        encoding="utf-8",
    )
    assert [len(chunk) for chunk in stream_jsonl(source, chunk_size=2)] == [2, 2, 1]
    first = tmp_path / "first.jsonl.gz"
    second = tmp_path / "second.jsonl.gz"
    first_report = compress_jsonl(source, first, chunk_size=2)
    second_report = compress_jsonl(source, second, chunk_size=3)
    assert first_report["sha256"] == second_report["sha256"]
    with gzip.open(first, "rt", encoding="utf-8") as handle:
        assert len(handle.readlines()) == 5


def test_stream_jsonl_rejects_non_objects(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("[1,2,3]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected JSON object"):
        list(stream_jsonl(path))


def test_duplicate_report_does_not_delete(tmp_path: Path) -> None:
    left = tmp_path / "left.bin"
    right = tmp_path / "right.bin"
    left.write_bytes(b"duplicate")
    right.write_bytes(b"duplicate")
    report = duplicate_artifact_report([tmp_path], minimum_bytes=0)
    assert report["duplicate_group_count"] == 1
    assert report["automatic_deletion_performed"] is False
    assert left.exists() and right.exists()


def test_cleanup_plan_rejects_broad_targets() -> None:
    report = cache_cleanup_plan(["/", str(Path.home())])
    assert report["state"] == "no_safe_candidates"
    assert len(report["rejected_broad_targets"]) == 2
    assert report["automatic_cleanup_performed"] is False


def test_resource_estimator_is_explicitly_unmeasured() -> None:
    report = estimate_trajectory_resources(
        tasks=20,
        conditions_per_task=6,
        models=4,
        policies=2,
        repeats=1,
        mean_seconds_per_trajectory=10,
        mean_kib_per_trajectory=32,
        workers=4,
    )
    assert report["trajectory_count"] == 960
    assert report["runtime_seconds"]["base"] == 2400
    assert report["label"] == "ESTIMATE_NOT_MEASURED"
    assert report["scientific_evidence"] is False


def test_bootstrap_plans_are_complete_and_disjoint() -> None:
    pilot = bootstrap_execution_plan(mode="pilot", shard_size=300)
    assert pilot["replicates"] == 1000
    assert pilot["shards"][0] == {"replicate_start": 0, "replicate_stop": 300}
    assert pilot["shards"][-1]["replicate_stop"] == 1000
    final = bootstrap_execution_plan(mode="final", shard_size=250)
    assert len(final["shards"]) == 40
