from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from causal_agent_bench.generation.base_tasks import generate_base_tasks
from causal_agent_bench.generation.interventions import generate_interventions_for_task
from causal_agent_bench.generation.quality_checks import (
    quality_report_markdown,
    run_quality_checks,
)
from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, InterventionSpec
from causal_agent_bench.utils.io import load_yaml, stable_hash, write_json, write_jsonl


class BenchmarkGenerationConfig(BaseModel):
    seed: int = 0
    num_base_tasks: int = Field(gt=0)
    domains: list[str] = Field(min_length=1)
    difficulty_mix: dict[str, float] = Field(default_factory=lambda: {"medium": 1.0})
    interventions_per_task: int = Field(default=3, ge=0)
    output_dir: str
    intervention_families: list[str] | None = None


def generate_benchmark(config: BenchmarkGenerationConfig) -> dict[str, Any]:
    base_tasks = generate_base_tasks(
        seed=config.seed,
        num_base_tasks=config.num_base_tasks,
        domains=config.domains,
        difficulty_mix=config.difficulty_mix,
    )
    interventions: list[InterventionSpec] = []
    instances: list[BenchmarkInstance] = []
    for task_index, base_task in enumerate(base_tasks):
        instances.append(_clean_instance(base_task, config.seed + task_index))
        task_interventions = generate_interventions_for_task(
            base_task,
            seed=config.seed,
            count=config.interventions_per_task,
            families=config.intervention_families,  # type: ignore[arg-type]
        )
        interventions.extend(task_interventions)
        for intervention_index, intervention in enumerate(task_interventions):
            instances.append(
                _intervention_instance(
                    base_task,
                    intervention,
                    seed=config.seed + task_index * 100 + intervention_index,
                )
            )

    quality_report = run_quality_checks(base_tasks, interventions, instances)
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "base_tasks.jsonl", base_tasks)
    write_jsonl(output_dir / "interventions.jsonl", interventions)
    write_jsonl(output_dir / "instances.jsonl", instances)
    generation_report = {
        "config": config.model_dump(mode="json"),
        "config_hash": stable_hash(config.model_dump(mode="json")),
        "counts": {
            "base_tasks": len(base_tasks),
            "interventions": len(interventions),
            "instances": len(instances),
        },
        "quality_passed": quality_report["passed"],
    }
    write_json(output_dir / "generation_report.json", generation_report)
    (output_dir / "quality_report.md").write_text(
        quality_report_markdown(quality_report),
        encoding="utf-8",
    )
    return {
        "base_tasks": base_tasks,
        "interventions": interventions,
        "instances": instances,
        "generation_report": generation_report,
        "quality_report": quality_report,
        "output_dir": str(output_dir),
    }


def generate_benchmark_from_config(config_path: str | Path) -> dict[str, Any]:
    raw = load_yaml(config_path)
    config = BenchmarkGenerationConfig.model_validate(raw)
    return generate_benchmark(config)


def _clean_instance(base_task: BaseTask, seed: int) -> BenchmarkInstance:
    return BenchmarkInstance(
        instance_id=f"{base_task.task_id}.clean",
        base_task=base_task,
        condition="clean",
        intervention=None,
        available_tools=list(base_task.available_tools),
        initial_memory={},
        environment_seed=seed,
        metadata={"synthetic": True},
    )


def _intervention_instance(
    base_task: BaseTask,
    intervention: InterventionSpec,
    seed: int,
) -> BenchmarkInstance:
    available_tools = _patched_tools(base_task.available_tools, intervention)
    initial_memory = dict(intervention.memory_patch)
    return BenchmarkInstance(
        instance_id=f"{base_task.task_id}.{intervention.family}",
        base_task=base_task,
        condition="intervention",
        intervention=intervention,
        available_tools=available_tools,
        initial_memory=initial_memory,
        environment_seed=seed,
        metadata={
            "synthetic": True,
            "final_answer_should_change": intervention.metadata.get("final_answer_should_change", False),
            "designed_failure_mode": intervention.metadata.get("designed_failure_mode"),
        },
    )


def _patched_tools(base_tools: list[str], intervention: InterventionSpec) -> list[str]:
    tools = list(base_tools)
    for removed in intervention.tool_availability_patch.get("removed_tools", []):
        tools = [tool for tool in tools if tool != removed]
    for added in intervention.tool_availability_patch.get("added_tools", []):
        if added not in tools:
            tools.append(added)
    return tools
