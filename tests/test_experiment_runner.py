from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment, run_experiment_from_config
from causal_agent_bench.schemas import Trajectory
from causal_agent_bench.utils.io import read_json, read_jsonl


def _config(tmp_path: Path, **overrides) -> ExperimentConfig:
    data = {
        "seed": 7,
        "run_name": "pytest_smoke",
        "benchmark_path": "data/sample/instances.jsonl",
        "agents": ["random_tool_agent"],
        "max_steps": 8,
        "num_repeats": 1,
        "output_dir": str(tmp_path),
        "save_observations": True,
        "save_agent_thoughts": True,
        "fail_fast": False,
        "auto_score": True,
    }
    data.update(overrides)
    return ExperimentConfig.model_validate(data)


def test_experiment_smoke_run_creates_expected_files(tmp_path):
    result = run_experiment(_config(tmp_path))
    run_dir = result["run_dir"]
    expected = {
        "config.yaml",
        "config_hash.txt",
        "run_metadata.json",
        "instances.jsonl",
        "trajectories.jsonl",
        "errors.jsonl",
        "scores.jsonl",
        "aggregate_scores.json",
        "aggregate_scores.csv",
        "score_report.md",
    }
    assert expected.issubset({path.name for path in run_dir.iterdir()})
    assert len(read_jsonl(run_dir / "trajectories.jsonl", Trajectory)) == 9


def test_run_metadata_contains_required_fields(tmp_path):
    run_dir = run_experiment(_config(tmp_path))["run_dir"]
    metadata = read_json(run_dir / "run_metadata.json")
    for key in [
        "timestamp",
        "git_commit",
        "python_version",
        "package_version",
        "seed",
        "config_hash",
        "number_of_instances",
        "agents",
        "machine",
    ]:
        assert key in metadata


def test_resume_skips_completed_pairs(tmp_path):
    result = run_experiment(_config(tmp_path, auto_score=False))
    run_dir = result["run_dir"]
    first_count = len(read_jsonl(run_dir / "trajectories.jsonl", Trajectory))
    resumed = run_experiment(_config(tmp_path, auto_score=False), resume_dir=run_dir)
    second_count = len(read_jsonl(run_dir / "trajectories.jsonl", Trajectory))
    assert first_count == second_count
    assert resumed["trajectories"] == []


def test_resume_rejects_config_hash_mismatch(tmp_path):
    result = run_experiment(_config(tmp_path, auto_score=False))
    run_dir = result["run_dir"]
    with pytest.raises(ValueError, match="config hash mismatch"):
        run_experiment(_config(tmp_path, seed=999, auto_score=False), resume_dir=run_dir)


def test_errors_are_logged_for_bad_agent(tmp_path):
    run_dir = run_experiment(
        _config(tmp_path, agents=["not_an_agent"], auto_score=False)
    )["run_dir"]
    errors = read_jsonl(run_dir / "errors.jsonl")
    assert len(errors) == 9
    assert errors[0]["error_type"] == "ValueError"
    assert errors[0]["skipped"] is True


def test_auto_scoring_is_triggered(tmp_path):
    run_dir = run_experiment(_config(tmp_path, agents=["scripted_oracle_agent"]))["run_dir"]
    aggregate = read_json(run_dir / "aggregate_scores.json")
    assert aggregate["n_agents"] == 1
    assert "scripted_oracle_agent" in aggregate["by_agent"]


def test_config_validation_catches_missing_benchmark_location():
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(
            {
                "seed": 1,
                "run_name": "bad",
                "agents": ["random_tool_agent"],
            }
        )


def test_deterministic_run_has_stable_agent_summary(tmp_path):
    first = run_experiment(_config(tmp_path / "a", agents=["scripted_oracle_agent"]))["run_dir"]
    second = run_experiment(_config(tmp_path / "b", agents=["scripted_oracle_agent"]))["run_dir"]
    first_summary = read_json(first / "aggregate_scores.json")["by_agent"]
    second_summary = read_json(second / "aggregate_scores.json")["by_agent"]
    assert first_summary == second_summary


def test_run_from_config_supports_benchmark_dir(tmp_path):
    config_path = tmp_path / "run.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "seed": 7,
                "run_name": "from_config",
                "benchmark_dir": "data/processed/dev_20",
                "agents": ["random_tool_agent"],
                "max_steps": 8,
                "num_repeats": 1,
                "output_dir": str(tmp_path / "runs"),
                "auto_score": False,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    result = run_experiment_from_config(config_path)
    assert len(result["trajectories"]) == 80
    assert result["run_dir"].parent == tmp_path / "runs"
