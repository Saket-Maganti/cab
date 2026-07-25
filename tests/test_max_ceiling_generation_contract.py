from __future__ import annotations

from causal_agent_bench.generation.instances import (
    BenchmarkGenerationConfig,
    generate_benchmark,
)


def test_id_namespace_prevents_cross_study_id_overlap(tmp_path) -> None:
    common = {
        "seed": 7,
        "num_base_tasks": 2,
        "domains": ["travel_planning"],
        "interventions_per_task": 1,
        "pilot_split_size": 2,
        "output_dir": str(tmp_path / "a"),
    }
    a = generate_benchmark(
        BenchmarkGenerationConfig(**common, id_namespace="scale100_v1")
    )
    b = generate_benchmark(
        BenchmarkGenerationConfig(
            **{**common, "output_dir": str(tmp_path / "b")},
            id_namespace="main500_v1",
        )
    )
    a_ids = {row.instance_id for row in a["instances"]}
    b_ids = {row.instance_id for row in b["instances"]}
    assert a_ids.isdisjoint(b_ids)
    assert all(row.base_task.metadata["id_namespace"] == "scale100_v1" for row in a["instances"])


def test_invalid_namespace_is_rejected(tmp_path) -> None:
    config = BenchmarkGenerationConfig(
        seed=1,
        num_base_tasks=1,
        domains=["travel_planning"],
        interventions_per_task=0,
        output_dir=str(tmp_path),
        id_namespace="../unsafe",
    )
    try:
        generate_benchmark(config)
    except ValueError as exc:
        assert "id_namespace" in str(exc)
    else:
        raise AssertionError("unsafe namespace should fail")

