from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from causal_agent_bench.generation.interventions import INTERVENTION_FAMILY_AUDIT_GUIDE
from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, InterventionSpec
from causal_agent_bench.validation import validate_instance, validate_intervention, validate_task


def check_base_task(task: BaseTask) -> list[str]:
    issues = validate_task(task)
    instruction = task.goal.user_instruction.strip()
    if len(instruction) < 40:
        issues.append("instruction clarity risk: instruction is too short")
    if task.goal.expected_final_answer in (None, "", {}):
        issues.append("missing expected answer")
    required_tools = task.required_tools or list(task.gold_tool_sequence or [])
    if not required_tools:
        issues.append("no required tools")
    if not task.goal.success_criteria or any(len(item.strip()) < 8 for item in task.goal.success_criteria):
        issues.append("ambiguous success criteria")
    if not _success_criteria_machine_checkable(task):
        issues.append("success criteria are not machine-checkable enough for deterministic scoring")
    if task.gold_tool_sequence:
        missing = [tool for tool in task.gold_tool_sequence if tool not in task.available_tools]
        if missing:
            issues.append(f"mismatch between gold tool sequence and available tools: {missing}")
    missing_required = [tool for tool in required_tools if tool not in task.available_tools]
    if missing_required:
        issues.append(f"required tool is missing in clean task: {missing_required}")
    if not task.hidden_ground_truth:
        issues.append("hidden ground truth incomplete")
    if not task.expected_evidence:
        issues.append("missing expected evidence metadata")
    if not task.partial_credit_criteria:
        issues.append("missing partial credit criteria")
    if task.max_steps < len(task.gold_tool_sequence or []):
        issues.append("impossible task: max_steps shorter than gold tool sequence")
    issues.extend(_synthetic_data_issues(task))
    issues.extend(_live_action_issues(task))
    return issues


def check_intervention(base_task: BaseTask, intervention: InterventionSpec) -> list[str]:
    issues = validate_intervention(base_task, intervention)
    guide = INTERVENTION_FAMILY_AUDIT_GUIDE.get(intervention.family)
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
    if intervention.metadata.get("goal_preserved") is False:
        issues.append("intervention changes the user goal")
    if not intervention.expected_behavior.strip():
        issues.append("intervention without expected behavior")
    if not (intervention.expected_robust_behavior or "").strip():
        issues.append("intervention without expected robust behavior")
    if not intervention.patch_details:
        issues.append("intervention missing patch details")
    if intervention.expected_final_answer_change in {"yes", "unclear"} and not intervention.scoring_notes:
        issues.append("answer expected to change but scoring criteria unchanged")
    if "designed_failure_mode" not in intervention.metadata:
        issues.append("intervention missing designed failure mode metadata")
    if intervention.expected_final_answer_change == "no" and intervention.family == "tool_removal":
        removed = set(intervention.tool_availability_patch.get("removed_tools", []))
        if removed.intersection(base_task.required_tools or base_task.gold_tool_sequence or []):
            issues.append("no valid solution remains when one should remain")
    if guide is None:
        issues.append(f"intervention family lacks audit guide: {intervention.family}")
    else:
        issues.extend(_family_audit_issues(base_task, intervention, guide))
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
        "warnings": [],
        "examples": {},
        "counts": {
            "base_tasks": len(base_tasks),
            "interventions": len(interventions),
            "instances": len(instances),
        },
        "distributions": _distribution_summary(base_tasks, interventions),
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
    task_counts = Counter(task.task_id for task in base_tasks)
    duplicate_tasks = sorted(task_id for task_id, count in task_counts.items() if count > 1)
    report["duplicate_tasks"] = duplicate_tasks
    if duplicate_tasks:
        report["warnings"].append(f"duplicate tasks/templates detected: {duplicate_tasks[:5]}")
    report["warnings"].extend(_balance_warnings(base_tasks, interventions))
    report["statistics"] = _quality_statistics(base_tasks, interventions)
    report["examples"] = _warning_examples(base_tasks, interventions, instances)
    report["instance_validity_scores"] = _instance_validity_scores(
        instances=instances,
        base_task_issues=report["base_task_issues"],
        intervention_issues=report["intervention_issues"],
        instance_issues=report["instance_issues"],
        duplicate_instances=report["duplicate_instances"],
    )
    report["validity_score_counts"] = dict(
        sorted(
            Counter(row["score"] for row in report["instance_validity_scores"].values()).items()
        )
    )
    report["passed"] = not (
        report["base_task_issues"]
        or report["intervention_issues"]
        or report["instance_issues"]
        or report["duplicate_instances"]
        or duplicate_tasks
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
        "## Distributions",
        "",
        "### Domains",
        "",
        *_counter_lines(report["distributions"]["domains"]),
        "",
        "### Difficulties",
        "",
        *_counter_lines(report["distributions"]["difficulties"]),
        "",
        "### Intervention Families",
        "",
        *_counter_lines(report["distributions"]["intervention_families"]),
        "",
        "## Statistics",
        "",
        f"- Average max steps: {report.get('statistics', {}).get('average_max_steps')}",
        f"- Average required tools: {report.get('statistics', {}).get('average_required_tools')}",
        f"- Duplicate task IDs: {len(report.get('duplicate_tasks', []))}",
        f"- Duplicate instance IDs: {len(report.get('duplicate_instances', []))}",
        "",
        "## Intervention Validity Scores",
        "",
        *_counter_lines(report.get("validity_score_counts", {})),
        "",
        "| Instance | Score | Family | Notes |",
        "|---|---:|---|---|",
        *_instance_score_lines(report.get("instance_validity_scores", {})),
        "",
        "### Tool Patterns",
        "",
        *_counter_lines(report["distributions"]["tool_patterns"], limit=12),
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
    lines.extend(["", "### duplicate_tasks"])
    if report.get("duplicate_tasks"):
        for task_id in report["duplicate_tasks"]:
            lines.append(f"- `{task_id}`")
    else:
        lines.append("")
        lines.append("None.")
    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("None.")
    lines.extend(["", "## Warning Examples", ""])
    for key, examples in report.get("examples", {}).items():
        lines.append(f"### {key}")
        if not examples:
            lines.append("None.")
            continue
        for example in examples[:5]:
            lines.append(f"- `{example}`")
    return "\n".join(lines) + "\n"


def _distribution_summary(
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


def _family_audit_issues(
    base_task: BaseTask,
    intervention: InterventionSpec,
    guide: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    target_factor = str(guide["target_factor"])
    if intervention.target_factor != target_factor:
        issues.append(
            f"target factor audit metadata mismatch: expected {target_factor!r}, got {intervention.target_factor!r}"
        )
    if intervention.changed_factor != target_factor:
        issues.append(
            f"changed_factor does not match family target factor: expected {target_factor!r}, got {intervention.changed_factor!r}"
        )
    expected_non_targets = set(guide["non_target_factors"])
    if not intervention.non_target_factors:
        issues.append("intervention missing non-target factor stability metadata")
    elif not expected_non_targets.issubset(set(intervention.non_target_factors)):
        issues.append("intervention non-target factors do not cover the family audit guide")
    if not intervention.invalid_examples:
        issues.append("intervention missing invalid examples for audit reviewers")
    expected_answer_change = str(guide["expected_final_answer_change"])
    if intervention.expected_final_answer_change != expected_answer_change:
        issues.append(
            "expected final-answer change does not match family audit guide: "
            f"expected {expected_answer_change}, got {intervention.expected_final_answer_change}"
        )
    severity_range = set(guide["acceptable_severity_range"])
    if intervention.severity not in severity_range:
        issues.append(
            f"severity {intervention.severity!r} outside acceptable range {sorted(severity_range)}"
        )
    expected_patch_group = str(guide["patch_group"])
    active_groups = _active_patch_groups(intervention)
    if active_groups != [expected_patch_group]:
        issues.append(
            f"intervention patch must isolate {expected_patch_group}; active groups are {active_groups}"
        )
    patch_field_count = _patch_field_count(intervention, expected_patch_group)
    if patch_field_count > int(guide["max_patch_fields"]):
        issues.append(
            f"intervention patch changes too many fields for {intervention.family}: "
            f"{patch_field_count} > {guide['max_patch_fields']}"
        )
    if intervention.metadata.get("goal_preserved") is not True:
        issues.append("intervention must explicitly mark the user goal as preserved")
    issues.extend(_required_tool_stability_issues(base_task, intervention))
    issues.extend(_ground_truth_validity_issues(base_task, intervention))
    issues.extend(_scoring_alignment_issues(intervention))
    return issues


def _active_patch_groups(intervention: InterventionSpec) -> list[str]:
    groups = []
    if intervention.tool_availability_patch:
        groups.append("tool_availability_patch")
    if intervention.memory_patch:
        groups.append("memory_patch")
    if intervention.tool_output_patch:
        groups.append("tool_output_patch")
    if intervention.instruction_patch is not None:
        groups.append("instruction_patch")
    return groups


def _patch_field_count(intervention: InterventionSpec, patch_group: str) -> int:
    if patch_group == "instruction_patch":
        return 1 if intervention.instruction_patch is not None else 0
    patch = getattr(intervention, patch_group)
    return len([key for key, value in patch.items() if value not in (None, "", [], {})])


def _required_tool_stability_issues(
    base_task: BaseTask,
    intervention: InterventionSpec,
) -> list[str]:
    issues: list[str] = []
    required_tools = set(base_task.required_tools or base_task.gold_tool_sequence or [])
    removed_tools = set(intervention.tool_availability_patch.get("removed_tools", []))
    if intervention.family != "tool_removal":
        missing = sorted(required_tools.intersection(removed_tools))
        if missing:
            issues.append(f"required tools removed outside tool_removal family: {missing}")
    else:
        still_required = sorted(required_tools - removed_tools)
        unavailable_non_removed = [tool for tool in still_required if tool not in base_task.available_tools]
        if unavailable_non_removed:
            issues.append(f"non-target required tools are unavailable: {unavailable_non_removed}")

    target_tool = intervention.tool_output_patch.get("target_tool")
    if target_tool is not None:
        if target_tool not in base_task.available_tools:
            issues.append(f"target tool is not available in the base task: {target_tool}")
        if target_tool in removed_tools:
            issues.append(f"target tool is also removed, changing availability and output: {target_tool}")
    return issues


def _ground_truth_validity_issues(
    base_task: BaseTask,
    intervention: InterventionSpec,
) -> list[str]:
    issues: list[str] = []
    policy = intervention.metadata.get("ground_truth_policy")
    expected_change = intervention.expected_final_answer_change
    if expected_change == "no":
        if policy not in {"unchanged", None}:
            issues.append(f"ground truth policy should be unchanged, got {policy!r}")
        if intervention.metadata.get("final_answer_should_change") is True:
            issues.append("metadata says final answer should change but family guide says it should not")
        if base_task.goal.expected_final_answer in (None, "", {}) or not base_task.hidden_ground_truth:
            issues.append("ground truth cannot be audited as unchanged because labels are incomplete")
        return issues

    if policy not in {
        "updated",
        "behavioral_override_required",
        "unchanged_or_behavioral_override",
    }:
        issues.append("ground truth must be explicitly updated or documented with a scoring override")
    if expected_change == "yes" and intervention.metadata.get("final_answer_should_change") is not True:
        issues.append("metadata must mark final_answer_should_change for answer-changing interventions")
    return issues


def _scoring_alignment_issues(intervention: InterventionSpec) -> list[str]:
    notes = intervention.scoring_notes.strip()
    if not notes:
        return ["intervention missing scoring notes"]
    lower_notes = notes.lower()
    if intervention.expected_final_answer_change == "no":
        if not any(token in lower_notes for token in ["unchanged", "ground-truth", "ground truth", "same"]):
            return ["scoring notes do not state that the ground-truth answer is unchanged"]
    else:
        if not any(
            token in lower_notes
            for token in ["limitation", "uncertainty", "assumption", "recover", "conflict", "alternative", "alternate"]
        ):
            return ["scoring notes do not describe the expected changed-answer behavior"]
    return []


def _instance_validity_scores(
    *,
    instances: list[BenchmarkInstance],
    base_task_issues: dict[str, list[str]],
    intervention_issues: dict[str, list[str]],
    instance_issues: dict[str, list[str]],
    duplicate_instances: list[str],
) -> dict[str, dict[str, Any]]:
    duplicate_set = set(duplicate_instances)
    scores: dict[str, dict[str, Any]] = {}
    for instance in instances:
        issues = list(instance_issues.get(instance.instance_id, []))
        warnings: list[str] = []
        if instance.instance_id in duplicate_set:
            issues.append("duplicate instance id")
        for issue in base_task_issues.get(instance.base_task.task_id, []):
            issues.append(f"base task issue: {issue}")
        family = None
        intervention_id = None
        expected_final_answer_change = None
        if instance.intervention is not None:
            family = instance.intervention.family
            intervention_id = instance.intervention.intervention_id
            expected_final_answer_change = instance.intervention.expected_final_answer_change
            for issue in intervention_issues.get(instance.intervention.intervention_id, []):
                issues.append(f"intervention issue: {issue}")
            if instance.intervention.intervention_validity_risk == "high":
                warnings.append("intervention validity risk is marked high")
            if instance.intervention.expected_final_answer_change in {"yes", "unclear"}:
                warnings.append("final-answer scoring requires explicit audit attention")
        score = "fail" if issues else "warning" if warnings else "pass"
        scores[instance.instance_id] = {
            "score": score,
            "issues": issues,
            "warnings": warnings,
            "base_task_id": instance.base_task.task_id,
            "intervention_id": intervention_id,
            "intervention_family": family,
            "expected_final_answer_change": expected_final_answer_change,
        }
    return dict(sorted(scores.items()))


def _instance_score_lines(scores: dict[str, dict[str, Any]], limit: int = 20) -> list[str]:
    if not scores:
        return ["| None | NA | NA | NA |"]
    lines = []
    for instance_id, row in list(scores.items())[:limit]:
        notes = row.get("issues") or row.get("warnings") or []
        note_text = "; ".join(str(note) for note in notes[:3]) if notes else "None."
        lines.append(
            f"| `{instance_id}` | `{row.get('score')}` | `{row.get('intervention_family') or 'clean'}` | {note_text} |"
        )
    remaining = len(scores) - limit
    if remaining > 0:
        lines.append(f"| ... | ... | ... | {remaining} additional instances omitted. |")
    return lines


def _balance_warnings(
    base_tasks: list[BaseTask],
    interventions: list[InterventionSpec],
) -> list[str]:
    warnings = []
    counters: list[tuple[str, Counter[Any]]] = [
        ("domain imbalance", Counter(task.domain for task in base_tasks)),
        ("difficulty imbalance", Counter(task.difficulty for task in base_tasks)),
        ("intervention family imbalance", Counter(intervention.family for intervention in interventions)),
    ]
    for label, counter in counters:
        values = list(counter.values())
        if len(values) <= 1:
            warnings.append(f"{label}: only one category present")
            continue
        avg = mean(values)
        if avg and max(values) - min(values) > max(2, avg * 0.25):
            warnings.append(f"{label}: distribution is uneven: {dict(sorted(counter.items()))}")

    pattern_counts = Counter(" -> ".join(task.gold_tool_sequence or []) for task in base_tasks)
    if base_tasks:
        dominant_pattern, dominant_count = pattern_counts.most_common(1)[0]
        if dominant_count / len(base_tasks) > 0.2:
            warnings.append(
                f"too many tasks requiring the same tool pattern: {dominant_pattern} ({dominant_count})"
            )
    for intervention in interventions:
        if intervention.intervention_validity_risk == "high":
            warnings.append(
                f"intervention validity risk high for {intervention.intervention_id}: {intervention.family}"
            )
            break
    return warnings


def _quality_statistics(
    base_tasks: list[BaseTask],
    interventions: list[InterventionSpec],
) -> dict[str, float | int | dict[str, int]]:
    required_counts = [len(task.required_tools or task.gold_tool_sequence or []) for task in base_tasks]
    max_steps = [task.max_steps for task in base_tasks]
    return {
        "average_max_steps": round(mean(max_steps), 3) if max_steps else 0.0,
        "average_required_tools": round(mean(required_counts), 3) if required_counts else 0.0,
        "max_required_tools": max(required_counts) if required_counts else 0,
        "high_validity_risk_interventions": sum(
            1 for intervention in interventions if intervention.intervention_validity_risk == "high"
        ),
    }


def _warning_examples(
    base_tasks: list[BaseTask],
    interventions: list[InterventionSpec],
    instances: list[BenchmarkInstance],
) -> dict[str, list[str]]:
    return {
        "high_validity_risk_interventions": [
            intervention.intervention_id
            for intervention in interventions
            if intervention.intervention_validity_risk == "high"
        ][:5],
        "expected_answer_change_interventions": [
            intervention.intervention_id
            for intervention in interventions
            if intervention.expected_final_answer_change in {"yes", "unclear"}
        ][:5],
        "long_tool_sequences": [
            task.task_id for task in base_tasks if len(task.gold_tool_sequence or []) >= 5
        ][:5],
        "intervention_instances": [
            instance.instance_id for instance in instances if instance.condition == "intervention"
        ][:5],
    }


def _counter_lines(counter: dict[str, int], limit: int | None = None) -> list[str]:
    items = list(counter.items())
    if limit is not None:
        items = items[:limit]
    return [f"- `{key}`: {value}" for key, value in items] or ["None."]


def _success_criteria_machine_checkable(task: BaseTask) -> bool:
    expected = task.goal.expected_final_answer
    if isinstance(expected, dict):
        return bool(expected) and bool(task.hidden_ground_truth)
    if isinstance(expected, str):
        return len(expected.strip()) >= 8 and bool(task.hidden_ground_truth)
    return False


def _synthetic_data_issues(task: BaseTask) -> list[str]:
    issues: list[str] = []
    haystack = " ".join(
        [
            task.goal.user_instruction,
            " ".join(task.goal.forbidden_assumptions),
            str(task.hidden_ground_truth),
        ]
    ).lower()
    if "ssn" in haystack or "social security" in haystack:
        issues.append("possible private data reference")
    if "@" in haystack:
        suspicious_fragments = [
            fragment
            for fragment in haystack.replace("{", " ").replace("}", " ").split()
            if "@" in fragment and "example.com" not in fragment
        ]
        if suspicious_fragments:
            issues.append("email-like data must use example.com synthetic addresses")
    return issues


def _live_action_issues(task: BaseTask) -> list[str]:
    issues: list[str] = []
    forbidden = " ".join(task.goal.forbidden_assumptions).lower()
    instruction = task.goal.user_instruction.lower()
    if "send_email_draft" in task.available_tools and "do not send" not in forbidden:
        issues.append("email workflow must explicitly forbid real sending")
    if "book_stub" in task.available_tools and "do not book" not in forbidden:
        issues.append("booking workflow must explicitly forbid real booking")
    if "send an email" in instruction and "draft" not in instruction:
        issues.append("instruction may imply live email sending instead of drafting")
    if "book " in instruction and "stub" not in instruction and "do not book" not in forbidden:
        issues.append("instruction may imply live booking")
    return issues
