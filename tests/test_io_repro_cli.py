import os
import subprocess
import sys

from causal_agent_bench.runners.runner import run_benchmark
from causal_agent_bench.schemas import GenerationConfig, RunConfig, Trajectory
from causal_agent_bench.task import generate_tasks
from causal_agent_bench.utils.io import read_jsonl, write_jsonl


def test_jsonl_round_trip(tmp_path):
    tasks = generate_tasks(GenerationConfig(output_path=str(tmp_path / "tasks.jsonl"), n_tasks=3, seed=3))
    path = tmp_path / "tasks.jsonl"
    write_jsonl(path, tasks)
    loaded = read_jsonl(path, type(tasks[0]))
    assert [task.task_id for task in loaded] == [task.task_id for task in tasks]


def test_run_reproducibility(tmp_path):
    tasks = generate_tasks(GenerationConfig(output_path=str(tmp_path / "tasks.jsonl"), n_tasks=4, seed=4))
    tasks_path = tmp_path / "tasks.jsonl"
    write_jsonl(tasks_path, tasks)
    config1 = RunConfig(
        run_name="repro",
        seed=9,
        tasks_path=str(tasks_path),
        output_dir=str(tmp_path / "run1"),
        agents=["ScriptedOracleAgent", "RandomToolAgent"],
        max_steps=8,
    )
    config2 = config1.model_copy(update={"output_dir": str(tmp_path / "run2")})
    run_benchmark(config1)
    run_benchmark(config2)
    t1 = read_jsonl(tmp_path / "run1" / "trajectories.jsonl", Trajectory)
    t2 = read_jsonl(tmp_path / "run2" / "trajectories.jsonl", Trajectory)
    assert [t.model_dump(exclude={"metadata"}) for t in t1] == [
        t.model_dump(exclude={"metadata"}) for t in t2
    ]


def test_cli_smoke_path(tmp_path):
    repo = os.getcwd()
    py_path = os.path.join(repo, "src")
    tasks_path = tmp_path / "tasks.jsonl"
    config_path = tmp_path / "gen.yaml"
    config_path.write_text(
        f"seed: 1\noutput_path: {tasks_path}\nn_tasks: 4\ninclude_clean: true\n",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": py_path}
    subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "generate", "--config", str(config_path)],
        check=True,
        env=env,
        cwd=repo,
    )
    subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "validate", str(tasks_path)],
        check=True,
        env=env,
        cwd=repo,
    )
    run_config = tmp_path / "run.yaml"
    run_config.write_text(
        "\n".join(
            [
                "run_name: cli",
                "seed: 2",
                f"tasks_path: {tasks_path}",
                f"output_dir: {tmp_path / 'run'}",
                "agents:",
                "  - ScriptedOracleAgent",
                "max_steps: 8",
            ]
        ),
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "run", "--config", str(run_config)],
        check=True,
        env=env,
        cwd=repo,
    )
    subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "score", "--run-dir", str(tmp_path / "run")],
        check=True,
        env=env,
        cwd=repo,
    )
    subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "analyze", "--run-dir", str(tmp_path / "run")],
        check=True,
        env=env,
        cwd=repo,
    )
    assert (tmp_path / "run" / "scores.json").exists()
    assert (tmp_path / "run" / "analysis_report.md").exists()
