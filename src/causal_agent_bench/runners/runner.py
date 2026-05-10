from __future__ import annotations

from pathlib import Path

from causal_agent_bench.agents import make_agent
from causal_agent_bench.environment import SimulatedEnvironment
from causal_agent_bench.metrics.components import compute_trajectory_metrics
from causal_agent_bench.runners.config import is_experiment_config
from causal_agent_bench.runners.experiment import run_experiment_from_config
from causal_agent_bench.schemas import BenchmarkTask, RunConfig, RunMetadata, Trajectory
from causal_agent_bench.task import generate_tasks, generation_config_from_mapping
from causal_agent_bench.tools import ToolRegistry
from causal_agent_bench.utils.io import (
    git_commit,
    load_yaml,
    read_jsonl,
    stable_hash,
    utc_now,
    write_json,
    write_jsonl,
)


def run_agent_on_task(agent_name: str, task: BenchmarkTask, seed: int, max_steps: int) -> Trajectory:
    agent = make_agent(agent_name, seed=seed)
    agent.reset(task, seed)
    env = SimulatedEnvironment(task, seed=seed, max_steps=max_steps)
    registry = ToolRegistry()
    tool_specs = registry.specs(task.available_tools)
    trajectory = Trajectory(
        run_id="adhoc",
        instance_id=task.task_id,
        agent_name=agent_name,
        model_name=None,
        steps=[],
        final_answer=None,
        terminated_reason="running",
        metadata={"seed": seed},
    )

    for _ in range(max_steps):
        if env.done:
            break
        action = agent.act(trajectory.steps, tool_specs)
        step = env.step(action)
        trajectory.steps.append(step.model_dump(mode="json"))

    if not env.done:
        env.done = True
        env.success = False
    trajectory.final_answer = env.final_answer
    trajectory.terminated_reason = "final_answer" if env.final_answer is not None else "max_steps"
    trajectory.metadata["success"] = bool(env.success)
    trajectory.metadata["metrics"] = compute_trajectory_metrics(task, trajectory)
    return trajectory


def run_benchmark(config: RunConfig, repo_root: str | Path | None = None) -> list[Trajectory]:
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = read_jsonl(config.tasks_path, BenchmarkTask)
    trajectories: list[Trajectory] = []
    for task_index, task in enumerate(tasks):
        for agent_index, agent_name in enumerate(config.agents):
            seed = config.seed + task_index * 1000 + agent_index
            trajectory = run_agent_on_task(agent_name, task, seed, config.max_steps)
            trajectory.run_id = config.run_name
            trajectories.append(trajectory)

    write_jsonl(output_dir / "tasks.jsonl", tasks)
    write_jsonl(output_dir / "trajectories.jsonl", trajectories)
    metadata = RunMetadata(
        run_id=config.run_name,
        config_hash=stable_hash(config.model_dump(mode="json")),
        seed=config.seed,
        timestamp=utc_now(),
        git_commit=git_commit(repo_root or Path.cwd()),
        config=config.model_dump(mode="json"),
    )
    write_json(output_dir / "metadata.json", metadata.model_dump(mode="json"))
    return trajectories


def run_from_config(
    config_path: str | Path,
    repo_root: str | Path | None = None,
    resume_dir: str | Path | None = None,
) -> list[Trajectory]:
    raw = load_yaml(config_path)
    if is_experiment_config(raw):
        result = run_experiment_from_config(config_path, resume_dir=resume_dir)
        return list(result["trajectories"])
    config = run_config_from_mapping(raw)
    return run_benchmark(config, repo_root=repo_root)


def run_config_from_mapping(raw: dict) -> RunConfig:
    """Normalize either a full run config or the bootstrap smoke config shape."""

    if "tasks_path" in raw and "run_name" in raw:
        return RunConfig.model_validate(raw)

    generation_config = generation_config_from_mapping(raw)
    tasks = generate_tasks(generation_config)
    write_jsonl(generation_config.output_path, tasks)

    run_name = raw.get("run_name", "smoke")
    output_dir = Path(raw.get("output_dir", "results")) / run_name
    agents = list(raw.get("agents", ["random_tool_agent"]))
    return RunConfig.model_validate(
        {
            "run_name": run_name,
            "seed": raw.get("seed", 0),
            "tasks_path": generation_config.output_path,
            "output_dir": str(output_dir),
            "agents": agents,
            "max_steps": raw.get("max_steps", 8),
        }
    )
