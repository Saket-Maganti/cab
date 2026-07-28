from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from causal_agent_bench.generation.answer_policies import (
    attach_base_task_policies,
    attach_intervention_policies,
)
from causal_agent_bench.generation.base_tasks import generate_base_tasks
from causal_agent_bench.generation.interventions import (
    balanced_families_for_task,
    generate_interventions_for_task,
    make_intervention,
)
from causal_agent_bench.generation.naturalistic import generate_naturalistic_base_tasks
from causal_agent_bench.generation.quality_checks import (
    quality_report_markdown,
    run_quality_checks,
)
from causal_agent_bench.generation.web_shadow import (
    API_MIRROR_FAMILIES,
    generate_web_shadow_base_tasks,
)
from causal_agent_bench.generation.web_shadow_interventions import (
    WEB_SHADOW_INTERVENTION_FAMILIES,
    make_web_shadow_intervention,
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
    benchmark_version: str = "dev"
    balanced_intervention_families: bool = False
    dev_split_size: int = 20
    pilot_split_size: int | None = None
    heldout_split_size: int = 0
    human_audit_sample_size: int = 0
    task_style: str = "template"
    id_namespace: str | None = None
    scientific_disposition: str = "PUBLIC_DEVELOPMENT_ONLY"
    confirmatory_eligible: bool = False

    @property
    def normalized_id_namespace(self) -> str | None:
        if self.id_namespace is None:
            return None
        namespace = self.id_namespace.strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", namespace):
            raise ValueError(
                "id_namespace must use lowercase letters, digits, '.', '_' or '-'"
            )
        return namespace


def generate_benchmark(config: BenchmarkGenerationConfig) -> dict[str, Any]:
    if config.confirmatory_eligible:
        raise ValueError(
            "the public deterministic generator cannot create protected or "
            "confirmatory packs; use the private held-out authoring workflow"
        )
    if config.task_style == "naturalistic":
        base_tasks = generate_naturalistic_base_tasks(
            seed=config.seed,
            num_base_tasks=config.num_base_tasks,
            domains=config.domains,
            difficulty_mix=config.difficulty_mix,
        )
    elif config.task_style == "template":
        base_tasks = generate_base_tasks(
            seed=config.seed,
            num_base_tasks=config.num_base_tasks,
            domains=config.domains,
            difficulty_mix=config.difficulty_mix,
        )
    elif config.task_style == "web_shadow":
        base_tasks = generate_web_shadow_base_tasks(
            seed=config.seed,
            num_base_tasks=config.num_base_tasks,
        )
    else:
        raise ValueError(
            f"unknown task_style {config.task_style!r}; expected 'template', 'naturalistic', or 'web_shadow'"
        )
    namespace = config.normalized_id_namespace
    if namespace:
        base_tasks = [
            task.model_copy(
                update={
                    # A single dot separates the base-task ID from condition /
                    # intervention suffixes throughout CAB.  Keep namespaces
                    # inside the base ID so pair-link and split scanners do not
                    # collapse every namespaced task to the namespace token.
                    "task_id": f"{namespace}__{task.task_id}",
                    "metadata": {
                        **task.metadata,
                        "id_namespace": namespace,
                    },
                }
            )
            for task in base_tasks
        ]
    base_tasks = [
        task.model_copy(
            update={
                "metadata": {
                    **task.metadata,
                    "scientific_disposition": config.scientific_disposition,
                    "confirmatory_eligible": False,
                }
            }
        )
        for task in base_tasks
    ]
    base_tasks = [
        attach_base_task_policies(
            task,
            benchmark_version=config.benchmark_version,
            split_role=_canonical_split_role(config, index),
        )
        for index, task in enumerate(base_tasks)
    ]
    interventions: list[InterventionSpec] = []
    instances: list[BenchmarkInstance] = []
    for task_index, base_task in enumerate(base_tasks):
        instances.append(_clean_instance(base_task, config.seed + task_index))
        if config.task_style == "web_shadow":
            task_interventions = _web_shadow_task_interventions(base_task, config.interventions_per_task)
        elif config.balanced_intervention_families:
            families = balanced_families_for_task(
                task_index,
                config.interventions_per_task,
                config.intervention_families,  # type: ignore[arg-type]
            )
            task_interventions = [make_intervention(base_task, family) for family in families]
        else:
            task_interventions = generate_interventions_for_task(
                base_task,
                seed=config.seed,
                count=config.interventions_per_task,
                families=config.intervention_families,  # type: ignore[arg-type]
            )
        task_interventions = [
            attach_intervention_policies(
                base_task,
                intervention,
                benchmark_version=config.benchmark_version,
            )
            for intervention in task_interventions
        ]
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
    splits = _make_splits(base_tasks, instances, config)
    write_json(output_dir / "splits.json", splits)
    _write_split_jsonl(output_dir, splits, base_tasks, instances)
    if config.human_audit_sample_size:
        write_jsonl(
            output_dir / "human_audit_sample.jsonl",
            _human_audit_sample(instances, config.seed, config.human_audit_sample_size),
        )
    generation_report = {
        "config": config.model_dump(mode="json"),
        "config_hash": stable_hash(config.model_dump(mode="json")),
        "benchmark_version": config.benchmark_version,
        "counts": {
            "base_tasks": len(base_tasks),
            "interventions": len(interventions),
            "instances": len(instances),
        },
        "distributions": _distributions(base_tasks, interventions),
        "statistics": _generation_statistics(base_tasks, interventions),
        "duplicates": _duplicate_report(base_tasks, instances),
        "quality_warnings": list(quality_report["warnings"]),
        "splits": {key: len(value["base_task_ids"]) for key, value in splits["splits"].items()},
        "quality_passed": quality_report["passed"],
    }
    write_json(output_dir / "generation_report.json", generation_report)
    (output_dir / "quality_report.md").write_text(
        quality_report_markdown(quality_report),
        encoding="utf-8",
    )
    (output_dir / "dataset_card.md").write_text(
        _dataset_card_markdown(config, generation_report, quality_report),
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
            "expected_final_answer_change": intervention.expected_final_answer_change,
            "designed_failure_mode": intervention.metadata.get("designed_failure_mode"),
        },
    )


def _web_shadow_task_interventions(base_task: BaseTask, count: int) -> list[InterventionSpec]:
    interface = base_task.metadata.get("tool_interface")
    if interface == "web_snapshot":
        families = WEB_SHADOW_INTERVENTION_FAMILIES[: max(count, 0)]
        return [make_web_shadow_intervention(base_task, family) for family in families]
    families = API_MIRROR_FAMILIES[: max(count, 0)]
    return [make_intervention(base_task, family) for family in families]


def _canonical_split_role(
    config: BenchmarkGenerationConfig,
    task_index: int,
) -> str:
    version = config.benchmark_version.lower()
    if "main500" in version:
        pilot_size = config.pilot_split_size or config.num_base_tasks
        return (
            "main500_public_development_v1"
            if task_index < pilot_size
            else "heldout_challenge_v1_contaminated"
        )
    if "scale100" in version:
        return "scale100_public_development_v1"
    if "naturalistic" in version:
        return "naturalistic_public_development_v1"
    if "pilot_v0" in version:
        return "compact20_pilot"
    return "dev_fixture"


def _patched_tools(base_tools: list[str], intervention: InterventionSpec) -> list[str]:
    tools = list(base_tools)
    for removed in intervention.tool_availability_patch.get("removed_tools", []):
        tools = [tool for tool in tools if tool != removed]
    for added in intervention.tool_availability_patch.get("added_tools", []):
        if added not in tools:
            tools.append(added)
    return tools


def _make_splits(
    base_tasks: list[BaseTask],
    instances: list[BenchmarkInstance],
    config: BenchmarkGenerationConfig,
) -> dict[str, Any]:
    pilot_size = config.pilot_split_size or len(base_tasks)
    pilot_tasks = base_tasks[: min(pilot_size, len(base_tasks))]
    dev_tasks = pilot_tasks[: min(config.dev_split_size, len(pilot_tasks))]
    heldout_start = len(pilot_tasks)
    heldout_end = min(heldout_start + config.heldout_split_size, len(base_tasks))
    heldout_tasks = base_tasks[heldout_start:heldout_end]
    return {
        "benchmark_version": config.benchmark_version,
        "seed": config.seed,
        "split_policy": (
            "dev is a deterministic subset of pilot for quick iteration; "
            "heldout uses later template variants when available."
        ),
        "splits": {
            "dev": _split_payload(dev_tasks, instances),
            "pilot_20": _split_payload(dev_tasks, instances),
            "pilot_100": _split_payload(pilot_tasks[: min(100, len(pilot_tasks))], instances),
            "pilot": _split_payload(pilot_tasks, instances),
            "heldout": _split_payload(heldout_tasks, instances),
        },
    }


def _write_split_jsonl(
    output_dir: Path,
    splits: dict[str, Any],
    base_tasks: list[BaseTask],
    instances: list[BenchmarkInstance],
) -> None:
    tasks_by_id = {task.task_id: task for task in base_tasks}
    instances_by_id = {instance.instance_id: instance for instance in instances}
    for split_name, split_payload in splits["splits"].items():
        split_tasks = [
            tasks_by_id[task_id]
            for task_id in split_payload["base_task_ids"]
            if task_id in tasks_by_id
        ]
        split_instances = [
            instances_by_id[instance_id]
            for instance_id in split_payload["instance_ids"]
            if instance_id in instances_by_id
        ]
        write_jsonl(output_dir / f"{split_name}_base_tasks.jsonl", split_tasks)
        write_jsonl(output_dir / f"{split_name}_instances.jsonl", split_instances)


def _split_payload(
    tasks: list[BaseTask],
    instances: list[BenchmarkInstance],
) -> dict[str, list[str]]:
    task_ids = [task.task_id for task in tasks]
    task_id_set = set(task_ids)
    return {
        "base_task_ids": task_ids,
        "instance_ids": [
            instance.instance_id
            for instance in instances
            if instance.base_task.task_id in task_id_set
        ],
    }


def _human_audit_sample(
    instances: list[BenchmarkInstance],
    seed: int,
    sample_size: int,
) -> list[dict[str, Any]]:
    intervention_instances = [instance for instance in instances if instance.intervention is not None]
    grouped: dict[tuple[str, str, str, str], list[BenchmarkInstance]] = defaultdict(list)
    for instance in intervention_instances:
        assert instance.intervention is not None
        grouped[
            (
                instance.base_task.domain,
                instance.intervention.family,
                instance.base_task.difficulty,
                instance.intervention.expected_final_answer_change,
            )
        ].append(instance)

    selected: list[BenchmarkInstance] = []
    seen: set[str] = set()
    for key in sorted(grouped):
        instance = sorted(grouped[key], key=lambda item: item.instance_id)[0]
        selected.append(instance)
        seen.add(instance.instance_id)
        if len(selected) >= sample_size:
            break

    remaining = [instance for instance in intervention_instances if instance.instance_id not in seen]
    rng = random.Random(seed)
    rng.shuffle(remaining)
    selected.extend(remaining[: max(0, sample_size - len(selected))])
    selected = selected[:sample_size]
    return [_audit_row(instance) for instance in selected]


def _audit_row(instance: BenchmarkInstance) -> dict[str, Any]:
    intervention = instance.intervention
    assert intervention is not None
    return {
        "audit_id": f"audit.{instance.instance_id}",
        "instance_id": instance.instance_id,
        "base_task_id": instance.base_task.task_id,
        "domain": instance.base_task.domain,
        "difficulty": instance.base_task.difficulty,
        "intervention_family": intervention.family,
        "expected_final_answer_change": intervention.expected_final_answer_change,
        "user_instruction": instance.base_task.goal.user_instruction,
        "success_criteria": instance.base_task.goal.success_criteria,
        "expected_final_answer": instance.base_task.goal.expected_final_answer,
        "changed_factor": intervention.changed_factor,
        "patch_details": intervention.patch_details,
        "expected_robust_behavior": intervention.expected_robust_behavior,
        "intervention_validity_risk": intervention.intervention_validity_risk,
        "scoring_notes": intervention.scoring_notes,
        "review_questions": [
            "Is the task understandable?",
            "Is the correct answer/scoring label valid?",
            "Does the intervention preserve the high-level goal?",
            "Is the changed factor isolated?",
            "What, if anything, is ambiguous?",
        ],
        "reviewer_response_schema": {
            "task_understandable": "yes/no/unclear",
            "scoring_label_valid": "yes/no/unclear",
            "goal_preserved": "yes/no/unclear",
            "changed_factor_isolated": "yes/no/unclear",
            "ambiguity_notes": "free text",
        },
    }


def _distributions(
    base_tasks: list[BaseTask],
    interventions: list[InterventionSpec],
) -> dict[str, dict[str, int]]:
    return {
        "domains": dict(sorted(Counter(task.domain for task in base_tasks).items())),
        "difficulties": dict(sorted(Counter(task.difficulty for task in base_tasks).items())),
        "intervention_families": dict(
            sorted(Counter(intervention.family for intervention in interventions).items())
        ),
        "tool_patterns": dict(
            sorted(
                Counter(" -> ".join(task.gold_tool_sequence or []) for task in base_tasks).items()
            )
        ),
    }


def _generation_statistics(
    base_tasks: list[BaseTask],
    interventions: list[InterventionSpec],
) -> dict[str, float | int]:
    required_tool_counts = [len(task.required_tools or task.gold_tool_sequence or []) for task in base_tasks]
    max_step_counts = [task.max_steps for task in base_tasks]
    return {
        "average_max_steps": round(sum(max_step_counts) / len(max_step_counts), 3)
        if max_step_counts
        else 0.0,
        "average_required_tools": round(sum(required_tool_counts) / len(required_tool_counts), 3)
        if required_tool_counts
        else 0.0,
        "average_interventions_per_task": round(len(interventions) / len(base_tasks), 3)
        if base_tasks
        else 0.0,
    }


def _duplicate_report(
    base_tasks: list[BaseTask],
    instances: list[BenchmarkInstance],
) -> dict[str, list[str]]:
    task_counts = Counter(task.task_id for task in base_tasks)
    instance_counts = Counter(instance.instance_id for instance in instances)
    instruction_counts = Counter(task.goal.user_instruction for task in base_tasks)
    return {
        "task_ids": sorted(task_id for task_id, count in task_counts.items() if count > 1),
        "instance_ids": sorted(
            instance_id for instance_id, count in instance_counts.items() if count > 1
        ),
        "instructions": sorted(
            instruction for instruction, count in instruction_counts.items() if count > 1
        )[:20],
    }


def _dataset_card_markdown(
    config: BenchmarkGenerationConfig,
    generation_report: dict[str, Any],
    quality_report: dict[str, Any],
) -> str:
    distributions = generation_report["distributions"]
    lines = [
        f"# Dataset Card: {config.benchmark_version}",
        "",
        "This is a deterministic synthetic pilot benchmark for CausalAgentBench.",
        "It is not the final NeurIPS-scale dataset and should not be described as a completed scientific benchmark.",
        "",
        "## Intended Use",
        "",
        "- Local pilot experiments for tool-using agent robustness.",
        "- Human audit calibration of intervention validity.",
        "- Engineering validation of runner, scoring, and analysis code.",
        "",
        "## Out-of-Scope Use",
        "",
        "- Claims about real-world agent reliability without LLM runs and human validation.",
        "- Evaluation of live web, real email, real booking, or private-data workflows.",
        "",
        "## Counts",
        "",
        f"- Base tasks: {generation_report['counts']['base_tasks']}",
        f"- Interventions: {generation_report['counts']['interventions']}",
        f"- Instances: {generation_report['counts']['instances']}",
        f"- Quality passed: `{quality_report['passed']}`",
        f"- Average max steps: {generation_report['statistics']['average_max_steps']}",
        f"- Average required tools: {generation_report['statistics']['average_required_tools']}",
        f"- Average interventions per task: {generation_report['statistics']['average_interventions_per_task']}",
        "",
        "## Domain Distribution",
        "",
        *[f"- `{key}`: {value}" for key, value in distributions["domains"].items()],
        "",
        "## Intervention Distribution",
        "",
        *[
            f"- `{key}`: {value}"
            for key, value in distributions["intervention_families"].items()
        ],
        "",
        "## Known Limitations",
        "",
        "- Tasks are synthetic and template-derived.",
        "- Automated quality checks are necessary but not sufficient for causal validity.",
        "- Human audit is required before moving claims from planned to supported.",
        "- Tool and scoring behavior remain deterministic approximations of real agent environments.",
    ]
    return "\n".join(lines) + "\n"
