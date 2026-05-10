from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from causal_agent_bench.schemas import BenchmarkInstance, BenchmarkTask, ScoreRecord, Trajectory
from causal_agent_bench.scoring import score_run
from causal_agent_bench.utils.io import read_json, read_jsonl


@dataclass(frozen=True)
class RunResults:
    run_dir: Path
    aggregate: dict[str, Any]
    scores: list[ScoreRecord]
    instances: list[BenchmarkInstance]
    legacy_tasks: list[BenchmarkTask]
    trajectories: list[Trajectory]
    scores_df: pd.DataFrame
    instances_df: pd.DataFrame
    trajectories_df: pd.DataFrame


def load_run_results(run_dir: str | Path, *, ensure_scores: bool = True) -> RunResults:
    run_path = Path(run_dir)
    if ensure_scores and not (run_path / "aggregate_scores.json").exists():
        score_run(run_path)
    aggregate = read_json(run_path / "aggregate_scores.json")
    scores = read_jsonl(run_path / "scores.jsonl", ScoreRecord)
    instances: list[BenchmarkInstance] = []
    legacy_tasks: list[BenchmarkTask] = []
    if (run_path / "instances.jsonl").exists():
        instances = read_jsonl(run_path / "instances.jsonl", BenchmarkInstance)
    elif (run_path / "tasks.jsonl").exists():
        legacy_tasks = read_jsonl(run_path / "tasks.jsonl", BenchmarkTask)
    trajectories = read_jsonl(run_path / "trajectories.jsonl", Trajectory)
    return RunResults(
        run_dir=run_path,
        aggregate=aggregate,
        scores=scores,
        instances=instances,
        legacy_tasks=legacy_tasks,
        trajectories=trajectories,
        scores_df=scores_to_dataframe(scores),
        instances_df=contexts_to_dataframe(instances, legacy_tasks),
        trajectories_df=trajectories_to_dataframe(trajectories),
    )


def scores_to_dataframe(scores: list[ScoreRecord]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for score in scores:
        row = {
            "run_id": score.run_id,
            "instance_id": score.instance_id,
            "agent_name": score.agent_name,
        }
        row.update(score.metrics)
        row.update({f"diagnostic_{key}": value for key, value in score.diagnostics.items()})
        row.update({f"metadata_{key}": value for key, value in score.metadata.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def contexts_to_dataframe(
    instances: list[BenchmarkInstance],
    legacy_tasks: list[BenchmarkTask],
) -> pd.DataFrame:
    if instances:
        return instances_to_dataframe(instances)
    return legacy_tasks_to_dataframe(legacy_tasks)


def instances_to_dataframe(instances: list[BenchmarkInstance]) -> pd.DataFrame:
    rows = []
    for instance in instances:
        intervention = instance.intervention
        base_task = instance.base_task
        rows.append(
            {
                "instance_id": instance.instance_id,
                "base_task_id": base_task.task_id,
                "condition": instance.condition,
                "intervention_family": intervention.family if intervention else None,
                "domain": base_task.domain,
                "difficulty": base_task.difficulty,
                "available_tool_count": len(instance.available_tools),
                "gold_tool_count": len(base_task.gold_tool_sequence or []),
                "max_steps": base_task.max_steps,
                "user_instruction": base_task.goal.user_instruction,
            }
        )
    return pd.DataFrame(rows)


def legacy_tasks_to_dataframe(tasks: list[BenchmarkTask]) -> pd.DataFrame:
    rows = []
    for task in tasks:
        intervention = task.intervention
        tool_sequence = task.expected_behavior.tool_sequence or task.expected_behavior.required_tools
        rows.append(
            {
                "instance_id": task.task_id,
                "base_task_id": task.clean_task_id or task.task_id,
                "condition": "intervention" if intervention else "clean",
                "intervention_family": intervention.family if intervention else None,
                "domain": task.domain,
                "difficulty": task.metadata.get("difficulty", "unknown"),
                "available_tool_count": len(task.available_tools),
                "gold_tool_count": len(tool_sequence),
                "max_steps": task.metadata.get("max_steps", 8),
                "user_instruction": task.user_goal,
            }
        )
    return pd.DataFrame(rows)


def trajectories_to_dataframe(trajectories: list[Trajectory]) -> pd.DataFrame:
    rows = []
    for trajectory in trajectories:
        tool_calls = extract_tool_calls(trajectory)
        rows.append(
            {
                "run_id": trajectory.run_id,
                "instance_id": trajectory.instance_id,
                "agent_name": trajectory.agent_name,
                "repeat": trajectory.metadata.get("repeat", 0),
                "terminated_reason": trajectory.terminated_reason,
                "final_answer": trajectory.final_answer,
                "n_steps": len(trajectory.steps),
                "n_tool_calls": len(tool_calls),
                "tool_calls": tool_calls,
            }
        )
    return pd.DataFrame(rows)


def extract_tool_calls(trajectory: Trajectory) -> list[str]:
    calls: list[str] = []
    for step in trajectory.steps:
        action = step.get("action")
        if not isinstance(action, dict):
            continue
        tool_call = action.get("tool_call")
        if isinstance(tool_call, dict) and tool_call.get("tool_name"):
            calls.append(str(tool_call["tool_name"]))
    return calls
