from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.utils.io import load_yaml


class ExperimentConfig(BaseModel):
    """Validated configuration for schema-native benchmark runs."""

    model_config = ConfigDict(extra="forbid")

    seed: int = 0
    run_name: str = Field(min_length=1)
    benchmark_path: str | None = None
    benchmark_dir: str | None = None
    agents: list[str] = Field(min_length=1)
    max_steps: int = Field(default=8, ge=1)
    num_repeats: int = Field(default=1, ge=1)
    output_dir: str = "results"
    save_observations: bool = True
    save_agent_thoughts: bool = True
    fail_fast: bool = False
    auto_score: bool = True

    @model_validator(mode="after")
    def check_benchmark_location(self) -> ExperimentConfig:
        if self.benchmark_path is None and self.benchmark_dir is None:
            raise ValueError("one of benchmark_path or benchmark_dir is required")
        if self.benchmark_path is not None and self.benchmark_dir is not None:
            raise ValueError("benchmark_path and benchmark_dir are mutually exclusive")
        return self

    def resolved_benchmark_path(self, base_dir: str | Path | None = None) -> Path:
        root = Path(base_dir or Path.cwd())
        if self.benchmark_path is not None:
            path = Path(self.benchmark_path)
        else:
            assert self.benchmark_dir is not None
            path = Path(self.benchmark_dir) / "instances.jsonl"
        return path if path.is_absolute() else root / path

    def resolved_output_dir(self, base_dir: str | Path | None = None) -> Path:
        root = Path(base_dir or Path.cwd())
        path = Path(self.output_dir)
        return path if path.is_absolute() else root / path


def is_experiment_config(raw: dict[str, Any]) -> bool:
    """Return whether a YAML mapping should use the schema-native experiment runner."""

    return "benchmark_path" in raw or "benchmark_dir" in raw


def load_experiment_config(path: str | Path) -> tuple[ExperimentConfig, dict[str, Any]]:
    raw = load_yaml(path)
    return ExperimentConfig.model_validate(raw), raw
