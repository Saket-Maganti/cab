"""Reproducibility guards: the same seed must produce byte-identical artifacts.

`tests/test_generation.py` already checks in-memory determinism. These tests go
further and pin the guarantees that actually matter for a released benchmark:

* the written JSONL artifact is byte-for-byte identical across separate runs;
* the deterministic dataset hash is stable across runs;
* generation is stable **across processes** even when `PYTHONHASHSEED` differs
  (i.e. dict/set iteration order can never leak into the artifact).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from causal_agent_bench.generation.instances import (
    BenchmarkGenerationConfig,
    generate_benchmark,
)
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.io import write_jsonl

_DOMAINS = ["travel", "calendar_email", "file_spreadsheet", "policy_compliance"]


def _config(out: Path) -> BenchmarkGenerationConfig:
    return BenchmarkGenerationConfig(
        seed=7,
        num_base_tasks=6,
        domains=_DOMAINS,
        difficulty_mix={"easy": 0.25, "medium": 0.5, "hard": 0.25},
        interventions_per_task=3,
        output_dir=str(out),
    )


def _instances_hash(result: dict) -> str:
    return stable_hash([item.model_dump(mode="json") for item in result["instances"]], length=32)


def test_generated_jsonl_is_byte_identical_across_runs(tmp_path: Path) -> None:
    first = generate_benchmark(_config(tmp_path / "a"))
    second = generate_benchmark(_config(tmp_path / "b"))

    path_a = tmp_path / "a_instances.jsonl"
    path_b = tmp_path / "b_instances.jsonl"
    write_jsonl(path_a, first["instances"])
    write_jsonl(path_b, second["instances"])

    assert path_a.read_bytes() == path_b.read_bytes()


def test_instance_hash_is_stable_across_runs(tmp_path: Path) -> None:
    first = generate_benchmark(_config(tmp_path / "a"))
    second = generate_benchmark(_config(tmp_path / "b"))
    assert _instances_hash(first) == _instances_hash(second)


# A snippet that builds a small benchmark and prints the deterministic instance
# hash. Run in subprocesses with different PYTHONHASHSEED values to prove that
# hash randomization can never change the artifact.
_SUBPROCESS_SNIPPET = """
from causal_agent_bench.generation.instances import BenchmarkGenerationConfig, generate_benchmark
from causal_agent_bench.hashing import stable_hash

config = BenchmarkGenerationConfig(
    seed=7,
    num_base_tasks=6,
    domains=["travel", "calendar_email", "file_spreadsheet", "policy_compliance"],
    difficulty_mix={"easy": 0.25, "medium": 0.5, "hard": 0.25},
    interventions_per_task=3,
    output_dir="/tmp/_cab_determinism_unused",
)
result = generate_benchmark(config)
print(stable_hash([i.model_dump(mode="json") for i in result["instances"]], length=32))
"""


def _hash_in_subprocess(hashseed: str) -> str:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hashseed
    result = subprocess.run(
        [sys.executable, "-c", _SUBPROCESS_SNIPPET],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return result.stdout.strip()


def test_generation_is_stable_across_process_hash_seeds() -> None:
    """Different PYTHONHASHSEED must still yield the identical dataset hash."""
    hash_a = _hash_in_subprocess("0")
    hash_b = _hash_in_subprocess("1")
    hash_c = _hash_in_subprocess("12345")
    assert hash_a == hash_b == hash_c
    assert len(hash_a) == 32
