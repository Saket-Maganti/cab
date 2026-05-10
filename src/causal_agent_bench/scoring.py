from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from causal_agent_bench.metrics.causal_robustness import agent_robustness
from causal_agent_bench.metrics.final_success import score_final_success
from causal_agent_bench.metrics.recovery import score_recovery
from causal_agent_bench.metrics.statistics import ranking_instability
from causal_agent_bench.metrics.tool_use import score_tool_use
from causal_agent_bench.metrics.trajectory import (
    score_contradiction,
    score_memory,
    score_stopping,
    score_trajectory_quality,
)
from causal_agent_bench.schemas import (
    BenchmarkInstance,
    BenchmarkTask,
    ScoreRecord,
    ScoreSummary,
    Trajectory,
)
from causal_agent_bench.utils.io import read_json, read_jsonl, write_json, write_jsonl


def score_trajectory(context: Any, trajectory: Trajectory) -> ScoreRecord:
    metrics: dict[str, float | int | bool | str | None] = {}
    metrics.update(score_final_success(context, trajectory))
    metrics.update(score_tool_use(context, trajectory))
    metrics.update(score_recovery(trajectory))
    metrics.update(score_contradiction(context, trajectory))
    metrics.update(score_memory(context, trajectory))
    metrics.update(score_stopping(context, trajectory))
    metrics.update(score_trajectory_quality(context, trajectory))
    diagnostics = {
        "condition": _condition(context),
        "intervention_family": _family(context),
        "base_task_id": _base_task_id(context),
        "terminated_reason": trajectory.terminated_reason,
        "failure_modes": _failure_modes(metrics),
    }
    return ScoreRecord(
        run_id=trajectory.run_id,
        instance_id=trajectory.instance_id,
        agent_name=trajectory.agent_name,
        metrics=metrics,
        diagnostics=diagnostics,
        metadata={
            "model_name": trajectory.model_name,
            "scorer": "deterministic_heuristic_v1",
        },
    )


def score_records(contexts: dict[str, Any], trajectories: list[Trajectory]) -> list[ScoreRecord]:
    records = []
    for trajectory in trajectories:
        context = contexts.get(trajectory.instance_id)
        if context is None:
            raise ValueError(f"no task/instance context found for trajectory {trajectory.instance_id}")
        records.append(score_trajectory(context, trajectory))
    return records


def aggregate_score_records(records: list[ScoreRecord]) -> dict[str, Any]:
    rows = [record.model_dump(mode="json") for record in records]
    agent_scores = agent_robustness(rows)
    by_agent_metrics: dict[str, dict[str, Any]] = {}
    by_agent_records: dict[str, list[ScoreRecord]] = defaultdict(list)
    by_instance_records: dict[str, list[ScoreRecord]] = defaultdict(list)
    by_family_records: dict[str, list[ScoreRecord]] = defaultdict(list)
    for record in records:
        by_agent_records[record.agent_name].append(record)
        by_instance_records[record.instance_id].append(record)
        family = record.diagnostics.get("intervention_family") or "clean"
        by_family_records[family].append(record)

    for agent, agent_records in by_agent_records.items():
        metric_means = _metric_means(agent_records)
        by_agent_metrics[agent] = {**agent_scores.get(agent, {}), **metric_means}

    by_instance = {
        instance_id: {
            "n": len(instance_records),
            "final_success_rate": _mean(
                [record.metrics.get("final_success_binary") for record in instance_records]
            ),
            "trajectory_success_rate": _mean(
                [record.metrics.get("trajectory_success_binary") for record in instance_records]
            ),
        }
        for instance_id, instance_records in sorted(by_instance_records.items())
    }
    by_family = {
        family: {
            "n": len(family_records),
            "final_success_rate": _mean(
                [record.metrics.get("final_success_binary") for record in family_records]
            ),
            "trajectory_faithfulness": _mean(
                [record.metrics.get("trajectory_faithfulness") for record in family_records]
            ),
        }
        for family, family_records in sorted(by_family_records.items())
    }
    ranking = ranking_instability(by_agent_metrics)
    return {
        "n_score_records": len(records),
        "n_instances": len(by_instance_records),
        "n_agents": len(by_agent_records),
        "by_agent": by_agent_metrics,
        "by_instance": by_instance,
        "by_intervention_family": by_family,
        "ranking_instability": ranking,
        "top_failure_modes": _top_failure_modes(records),
    }


def score_run(run_dir: str | Path) -> ScoreSummary:
    run_dir = Path(run_dir)
    contexts = _load_contexts(run_dir)
    trajectories = read_jsonl(run_dir / "trajectories.jsonl", Trajectory)
    records = score_records(contexts, trajectories)
    aggregate = aggregate_score_records(records)
    metadata = _load_metadata(run_dir)
    aggregate["metadata"] = metadata

    write_jsonl(run_dir / "scores.jsonl", records)
    write_json(run_dir / "aggregate_scores.json", aggregate)
    _write_aggregate_csv(run_dir / "aggregate_scores.csv", aggregate)
    _write_score_report(run_dir / "score_report.md", aggregate)

    compat = ScoreSummary(
        run_dir=str(run_dir),
        by_agent={
            agent: _compat_agent_row(row)
            for agent, row in aggregate["by_agent"].items()
        },
        by_task={
            instance_id: {
                "success_rate": row["final_success_rate"],
                "n_trajectories": row["n"],
            }
            for instance_id, row in aggregate["by_instance"].items()
        },
        metadata=metadata,
    )
    write_json(run_dir / "scores.json", compat.model_dump(mode="json"))
    return compat


def _load_contexts(run_dir: Path) -> dict[str, Any]:
    if (run_dir / "instances.jsonl").exists():
        instances = read_jsonl(run_dir / "instances.jsonl", BenchmarkInstance)
        return {instance.instance_id: instance for instance in instances}
    tasks = read_jsonl(run_dir / "tasks.jsonl", BenchmarkTask)
    return {task.task_id: task for task in tasks}


def _load_metadata(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "metadata.json"
    return read_json(path) if path.exists() else {}


def _condition(context: Any) -> str:
    if isinstance(context, BenchmarkInstance):
        return context.condition
    return "intervention" if getattr(context, "intervention", None) is not None else "clean"


def _family(context: Any) -> str | None:
    intervention = context.intervention if isinstance(context, BenchmarkInstance) else getattr(context, "intervention", None)
    if intervention is None:
        return None
    return getattr(intervention, "family", getattr(intervention, "type", None))


def _base_task_id(context: Any) -> str:
    if isinstance(context, BenchmarkInstance):
        return context.base_task.task_id
    return context.clean_task_id or context.task_id


def _failure_modes(metrics: dict[str, Any]) -> list[str]:
    failures = []
    if metrics.get("final_success_binary") == 0:
        failures.append("final_answer_failure")
    if metrics.get("premature_stop_binary"):
        failures.append("premature_stop")
    if metrics.get("max_step_failure_binary"):
        failures.append("max_step_failure")
    if metrics.get("missing_required_tool_count", 0) > 0:
        failures.append("missing_required_tools")
    if metrics.get("argument_error_count", 0) > 0:
        failures.append("argument_errors")
    if metrics.get("tool_error_recovery_binary") is False:
        failures.append("recovery_failure")
    if metrics.get("contradiction_detected_binary") is False and metrics.get("contradiction_resolved_binary") is False:
        # Only added for rows where a conflict was expected by diagnostics in future; harmless as a weak signal.
        pass
    if metrics.get("memory_blind_trust_failure_binary"):
        failures.append("memory_blind_trust")
    if metrics.get("trajectory_faithfulness", 0) < 1 and metrics.get("final_success_binary") == 1:
        failures.append("unfaithful_success")
    return failures


def _metric_means(records: list[ScoreRecord]) -> dict[str, Any]:
    keys = sorted({key for record in records for key in record.metrics})
    return {key: _mean([record.metrics.get(key) for record in records]) for key in keys}


def _mean(values: list[Any]) -> float | None:
    numeric = []
    for value in values:
        if value is None or isinstance(value, str):
            continue
        numeric.append(float(value))
    return round(mean(numeric), 6) if numeric else None


def _top_failure_modes(records: list[ScoreRecord]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for record in records:
        counter.update(record.diagnostics.get("failure_modes", []))
    return [{"failure_mode": name, "count": count} for name, count in counter.most_common()]


def _write_aggregate_csv(path: Path, aggregate: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "agent",
        "clean_success_rate",
        "intervention_success_rate",
        "acrs",
        "absolute_degradation",
        "relative_degradation",
        "trajectory_faithfulness",
        "required_tool_recall",
        "tool_precision",
        "n_trajectories",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for agent, row in sorted(aggregate["by_agent"].items()):
            writer.writerow({"agent": agent, **{field: row.get(field) for field in fields if field != "agent"}})


def _write_score_report(path: Path, aggregate: dict[str, Any]) -> None:
    lines = [
        "# Score Report",
        "",
        f"- Instances: {aggregate['n_instances']}",
        f"- Agents: {aggregate['n_agents']}",
        f"- Score records: {aggregate['n_score_records']}",
        "",
        "## Agent Robustness",
        "",
        "| Agent | Clean success | Intervention success | ACRS | Abs degradation | Rel degradation |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for agent, row in sorted(aggregate["by_agent"].items()):
        lines.append(
            f"| {agent} | {_fmt(row.get('clean_success_rate'))} | {_fmt(row.get('intervention_success_rate'))} | {_fmt(row.get('acrs'))} | {_fmt(row.get('absolute_degradation'))} | {_fmt(row.get('relative_degradation'))} |"
        )
    lines.extend(["", "## Intervention Family Breakdown", "", "| Family | N | Final success | Trajectory faithfulness |", "|---|---:|---:|---:|"])
    for family, row in sorted(aggregate["by_intervention_family"].items()):
        lines.append(
            f"| {family} | {row['n']} | {_fmt(row.get('final_success_rate'))} | {_fmt(row.get('trajectory_faithfulness'))} |"
        )
    lines.extend(["", "## Top Failure Modes", ""])
    if aggregate["top_failure_modes"]:
        for item in aggregate["top_failure_modes"][:10]:
            lines.append(f"- `{item['failure_mode']}`: {item['count']}")
    else:
        lines.append("No failure modes detected by deterministic heuristics.")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "Scoring is deterministic and heuristic. It is intended for auditable smoke and development runs, not as a substitute for human validation or calibrated LLM-as-judge scoring.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _compat_agent_row(row: dict[str, Any]) -> dict[str, float | int | None]:
    compat: dict[str, float | int | None] = {
        "clean_success_rate": row.get("clean_success_rate"),
        "intervention_success_rate": row.get("intervention_success_rate"),
        "acrs": row.get("acrs"),
        "n_trajectories": row.get("n_trajectories"),
    }
    for key, value in row.items():
        if isinstance(value, (int, float)) or value is None:
            compat[key] = value
    return compat
