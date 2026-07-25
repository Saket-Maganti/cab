import os
import subprocess
import sys
from pathlib import Path

from causal_agent_bench.environment import BenchmarkEnvironment
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment
from causal_agent_bench.schemas import AgentAction, BenchmarkInstance, ToolCall, ToolCallParseResult
from causal_agent_bench.trajectory import migrate_trajectory_v2, trajectory_to_markdown
from causal_agent_bench.utils.io import read_jsonl
from causal_agent_bench.validation import validate_jsonl_file

REPO_ROOT = Path(__file__).resolve().parents[1]


def _sample_instance() -> BenchmarkInstance:
    return read_jsonl(REPO_ROOT / "data/sample/instances.jsonl", BenchmarkInstance)[0]


def test_trajectory_v2_migrates_current_environment_record():
    instance = _sample_instance()
    env = BenchmarkEnvironment(instance, run_id="schema-test", agent_name="direct_stub")
    parse_result = ToolCallParseResult(
        raw_output='{"action":"tool_call","tool_name":"search_database","arguments":{"query":"hotel"}}',
        repaired_json={
            "action": "tool_call",
            "tool_name": "search_database",
            "arguments": {"query": "hotel"},
        },
        action_type="tool_call",
        outcome="valid_tool_call",
        is_valid=True,
        tool_name="search_database",
        arguments={"query": "hotel"},
    )
    action = AgentAction(
        thought="Need evidence.",
        tool_call=ToolCall(tool_name="search_database", arguments={"query": "hotel"}),
        metadata={
            "raw_model_output": parse_result.raw_output,
            "parsed_action": parse_result.model_dump(mode="json"),
            "parser_outcome": parse_result.outcome,
        },
    )

    env.step(action)
    trajectory = migrate_trajectory_v2(env.trajectory())

    assert trajectory.schema_version == "trajectory_v2"
    assert trajectory.base_task_id == instance.base_task.task_id
    assert trajectory.agent_id == "direct_stub"
    assert trajectory.steps[0].step_index == 0
    assert trajectory.steps[0].parser_status == "valid_tool_call"
    assert trajectory.steps[0].tool_call is not None
    assert trajectory.steps[0].tool_arguments == {"query": "hotel"}


def test_trajectory_v2_validation_accepts_experiment_output(tmp_path):
    config = ExperimentConfig.model_validate(
        {
            "seed": 7,
            "run_name": "trajectory_v2",
            "benchmark_path": "data/sample/instances.jsonl",
            "agents": ["random_tool_agent"],
            "max_steps": 2,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": False,
        }
    )
    run_dir = run_experiment(config)["run_dir"]

    summary = validate_jsonl_file(run_dir / "trajectories.jsonl", "trajectories_v2")

    assert summary["total"] == 9
    assert summary["invalid"] == 0


def test_cli_validates_trajectories_v2(tmp_path):
    config = ExperimentConfig.model_validate(
        {
            "seed": 7,
            "run_name": "trajectory_v2_cli",
            "benchmark_path": "data/sample/instances.jsonl",
            "agents": ["random_tool_agent"],
            "max_steps": 1,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": False,
        }
    )
    run_dir = run_experiment(config)["run_dir"]
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "validate",
            str(run_dir / "trajectories.jsonl"),
            "--schema",
            "trajectories_v2",
        ],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "validated" in result.stdout
    assert "trajectories_v2" in result.stdout


def test_trajectory_markdown_export_is_readable():
    instance = _sample_instance()
    env = BenchmarkEnvironment(instance, run_id="schema-test", agent_name="random_tool_agent")
    env.step(
        AgentAction(
            final_answer="Unable to answer confidently.",
            stop=True,
            metadata={"parser_outcome": "valid_final_answer"},
        )
    )

    markdown = trajectory_to_markdown(env.trajectory())

    assert "# Trajectory schema-test" in markdown
    assert "Parser status" in markdown
    assert "Final answer" in markdown
