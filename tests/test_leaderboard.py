import json
from pathlib import Path

import yaml

from causal_agent_bench.analysis.leaderboard import (
    LEADERBOARD_SCHEMA_ID,
    build_leaderboard_document,
    export_leaderboard,
    filter_scores_by_base_tasks,
    load_split_policy,
)
from causal_agent_bench.analysis.load_results import load_run_results
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment


def _analysis_run(tmp_path: Path) -> Path:
    config = ExperimentConfig.model_validate(
        {
            "seed": 17,
            "run_name": "leaderboard_smoke",
            "benchmark_path": "data/sample/instances.jsonl",
            "agents": ["random_tool_agent", "scripted_oracle_agent"],
            "max_steps": 8,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )
    return run_experiment(config)["run_dir"]


def test_leaderboard_export_excludes_oracle(tmp_path):
    run_dir = _analysis_run(tmp_path)
    paths = export_leaderboard(
        run_dir,
        tmp_path / "leaderboard_out",
        allow_engineering_only=True,
        allow_mock_stub=True,
    )
    assert len(paths) == 3
    document = json.loads(paths[0].read_text(encoding="utf-8"))
    agents = {entry["agent_run_name"] for entry in document["entries"]}
    assert "scripted_oracle_agent" not in agents
    assert "random_tool_agent" in agents
    assert document["schema_id"] == LEADERBOARD_SCHEMA_ID
    assert document["reporting_rules"]["exclude_oracle_agents"] is True
    assert "held-out test" in document["contamination_warning"].lower()
    markdown = paths[2].read_text(encoding="utf-8")
    assert "## Entries" in markdown
    assert "| random_tool_agent |" in markdown


def test_leaderboard_cli_command(tmp_path, capsys):
    run_dir = _analysis_run(tmp_path / "cli_run")
    from causal_agent_bench.cli import main as cli_main

    cli_main(
        [
            "export-leaderboard",
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(tmp_path / "cli_leaderboard"),
            "--allow-engineering-only",
            "--allow-mock-stub",
        ]
    )
    captured = capsys.readouterr().out
    assert "leaderboard_v1_unfiltered.json" in captured
    assert (tmp_path / "cli_leaderboard" / "leaderboard_v1_unfiltered.csv").exists()


def test_leaderboard_split_filter_uses_splits_json(tmp_path):
    run_dir = _analysis_run(tmp_path)
    data = load_run_results(run_dir)
    policy = load_split_policy("data/frozen/pilot_v0.1/splits.json")
    assert policy["policy_name"] == "release_disjoint_v1"
    sample_base_ids = set(data.scores_df["diagnostic_base_task_id"].dropna().astype(str))
    filtered = filter_scores_by_base_tasks(data.scores_df, sample_base_ids)
    assert len(filtered) == len(data.scores_df)

    document = build_leaderboard_document(
        data,
        eval_split="dev",
        splits_path=Path("data/frozen/pilot_v0.1/splits.json"),
    )
    assert document["split_policy_name"] == "release_disjoint_v1"
    assert document["eval_split"] == "dev"
    if document["entries"]:
        assert (
            document["entries"][0]["leaderboard_eligibility"]
            == "engineering_or_method_development_only"
        )


def test_leaderboard_records_agent_config_metadata(tmp_path):
    config = ExperimentConfig.model_validate(
        {
            "seed": 19,
            "run_name": "leaderboard_agent_runs",
            "benchmark_path": "data/sample/instances.jsonl",
            "agent_runs": [
                {
                    "name": "direct_stub",
                    "agent": "direct_tool_agent",
                    "provider": "local_stub",
                    "model": "local-stub-v2",
                    "retry_count": 2,
                }
            ],
            "max_steps": 4,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )
    run_dir = run_experiment(config)["run_dir"]
    (run_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "agent_runs": [
                    {
                        "name": "direct_stub",
                        "agent": "direct_tool_agent",
                        "provider": "local_stub",
                        "model": "local-stub-v2",
                        "retry_count": 2,
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    document = build_leaderboard_document(load_run_results(run_dir))
    entry = document["entries"][0]
    assert entry["agent_scaffold"] == "direct_tool_agent"
    assert entry["provider"] == "local_stub"
    assert entry["model"] == "local-stub-v2"
    assert entry["retry_count"] == 2
    assert entry["engineering_only"] is True
