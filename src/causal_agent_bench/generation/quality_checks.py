from __future__ import annotations

from collections import Counter
from typing import Any

from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, InterventionSpec
from causal_agent_bench.validation import validate_instance, validate_intervention, validate_task


def check_base_task(task: BaseTask) -> list[str]:
    issues = validate_task(task)
    if task.goal.expected_final_answer in (None, "", {}):
        issues.append("missing expected answer")
    if not task.gold_tool_sequence:
        issues.append("no required tools")
    if not task.goal.success_criteria or any(len(item.strip()) < 8 for item in task.goal.success_criteria):
        issues.append("ambiguous success criteria")
    if task.gold_tool_sequence:
        missing = [tool for tool in task.gold_tool_sequence if tool not in task.available_tools]
        if missing:
            issues.append(f"mismatch between gold tool sequence and available tools: {missing}")
    if task.max_steps < len(task.gold_tool_sequence or []):
        issues.append("impossible task: max_steps shorter than gold tool sequence")
    return issues


def check_intervention(base_task: BaseTask, intervention: InterventionSpec) -> list[str]:
    issues = validate_intervention(base_task, intervention)
    patch_count = sum(
        [
            bool(intervention.tool_availability_patch),
            bool(intervention.memory_patch),
            bool(intervention.tool_output_patch),
            intervention.instruction_patch is not None,
        ]
    )
    if patch_count > 1:
        issues.append("intervention changes too many factors")
    if not intervention.expected_behavior.strip():
        issues.append("intervention without expected behavior")
    if "designed_failure_mode" not in intervention.metadata:
        issues.append("intervention missing designed failure mode metadata")
    return issues


def check_instance(instance: BenchmarkInstance) -> list[str]:
    issues = validate_instance(instance)
    if instance.condition == "intervention" and instance.intervention is None:
        issues.append("intervention instance lacks intervention")
    return issues


def run_quality_checks(
    base_tasks: list[BaseTask],
    interventions: list[InterventionSpec],
    instances: list[BenchmarkInstance],
) -> dict[str, Any]:
    base_by_id = {task.task_id: task for task in base_tasks}
    report: dict[str, Any] = {
        "base_task_issues": {},
        "intervention_issues": {},
        "instance_issues": {},
        "duplicate_instances": [],
        "counts": {
            "base_tasks": len(base_tasks),
            "interventions": len(interventions),
            "instances": len(instances),
        },
    }
    for task in base_tasks:
        issues = check_base_task(task)
        if issues:
            report["base_task_issues"][task.task_id] = issues
    for intervention in interventions:
        base_task = base_by_id.get(intervention.base_task_id)
        if base_task is None:
            report["intervention_issues"][intervention.intervention_id] = ["intervention links to missing base task"]
            continue
        issues = check_intervention(base_task, intervention)
        if issues:
            report["intervention_issues"][intervention.intervention_id] = issues
    for instance in instances:
        issues = check_instance(instance)
        if issues:
            report["instance_issues"][instance.instance_id] = issues

    instance_counts = Counter(instance.instance_id for instance in instances)
    report["duplicate_instances"] = sorted(
        instance_id for instance_id, count in instance_counts.items() if count > 1
    )
    report["passed"] = not (
        report["base_task_issues"]
        or report["intervention_issues"]
        or report["instance_issues"]
        or report["duplicate_instances"]
    )
    return report


def quality_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Generation Quality Report",
        "",
        f"Passed: `{report['passed']}`",
        "",
        "## Counts",
        "",
        f"- Base tasks: {report['counts']['base_tasks']}",
        f"- Interventions: {report['counts']['interventions']}",
        f"- Instances: {report['counts']['instances']}",
        "",
        "## Issues",
        "",
    ]
    for key in ["base_task_issues", "intervention_issues", "instance_issues"]:
        lines.append(f"### {key}")
        issues = report[key]
        if not issues:
            lines.append("")
            lines.append("None.")
            lines.append("")
            continue
        for item_id, item_issues in issues.items():
            lines.append(f"- `{item_id}`: {'; '.join(item_issues)}")
        lines.append("")
    lines.append("### duplicate_instances")
    if report["duplicate_instances"]:
        for instance_id in report["duplicate_instances"]:
            lines.append(f"- `{instance_id}`")
    else:
        lines.append("")
        lines.append("None.")
    return "\n".join(lines) + "\n"
