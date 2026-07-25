"""Intervention isolation audit: single-factor-change discipline checks."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.generation.quality_checks import run_quality_checks
from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, InterventionSpec
from causal_agent_bench.utils.io import git_commit, read_jsonl, write_json

ISOLATION_FLAG_RULES: list[tuple[str, str]] = [
    ("intervention changes the user goal", "goal_changed"),
    ("answer expected to change but scoring criteria unchanged", "answer_change_without_metadata"),
    ("intervention changes too many factors", "multiple_factors_changed"),
    ("intervention without expected robust behavior", "missing_expected_robust_behavior"),
    ("changed_factor does not match", "missing_or_wrong_changed_factor"),
    ("intervention family lacks audit guide", "missing_intervention_family"),
    ("no valid solution remains when one should remain", "tool_removal_impossible"),
    ("memory", "memory_corruption_unverifiable"),
    ("observation conflict", "observation_conflict_no_resolution"),
    ("distractor", "distractor_evidence_relevant"),
    ("ambiguous", "ambiguous_instruction_unscorable"),
    ("instruction clarity risk", "ambiguous_instruction_unscorable"),
]


def _isolation_flags(issue_text: str) -> list[str]:
    lowered = issue_text.lower()
    flags: list[str] = []
    for needle, flag in ISOLATION_FLAG_RULES:
        if needle.lower() in lowered and flag not in flags:
            flags.append(flag)
    if "memory" in lowered and "verification" in lowered and "memory_corruption_unverifiable" not in flags:
        flags.append("memory_corruption_unverifiable")
    if "contradiction" in lowered and "resolution" in lowered:
        flags.append("observation_conflict_no_resolution")
    if "scoring notes do not describe" in lowered:
        flags.append("answer_change_without_metadata")
    return flags


def _family_specific_isolation(
    base_task: BaseTask,
    intervention: InterventionSpec,
) -> list[str]:
    issues: list[str] = []
    if intervention.family == "memory_corruption":
        patch = intervention.memory_patch or {}
        if not any(
            patch.get(key)
            for key in ("corrupted_keys", "entries", "stale_memory", "is_corrupted")
        ):
            issues.append("memory corruption cannot be verified: no corrupted memory patch documented")
    if intervention.family == "observation_conflict":
        notes = (intervention.scoring_notes or "").lower()
        if not any(token in notes for token in ["resolve", "conflict", "contradiction", "verify"]):
            issues.append("observation conflict has no documented resolution path")
    if intervention.family == "distractor_evidence":
        patch = intervention.tool_output_patch or {}
        if patch.get("distractor_is_decisive") is True:
            issues.append("distractor evidence is actually relevant/decisive")
    if intervention.family == "ambiguous_instruction":
        instruction = (intervention.instruction_patch or "").strip()
        if len(instruction) < 20:
            issues.append("ambiguous instruction is too underspecified to score")
    if intervention.family == "tool_removal":
        removed = set(intervention.tool_availability_patch.get("removed_tools", []))
        required = set(base_task.required_tools or base_task.gold_tool_sequence or [])
        if removed & required and intervention.expected_final_answer_change == "no":
            issues.append("tool removal makes task impossible without marking answer change")
    if not intervention.changed_factor.strip():
        issues.append("missing changed_factor metadata")
    if not intervention.family.strip():
        issues.append("missing intervention family")
    return issues


def audit_intervention_isolation(
    *,
    instances_path: str | Path,
    base_tasks_path: str | Path | None = None,
    interventions_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Audit intervention isolation for a dataset directory or instances file."""

    instances_path = Path(instances_path)
    dataset_root = instances_path.parent
    base_tasks_path = Path(base_tasks_path or dataset_root / "base_tasks.jsonl")
    interventions_path = Path(interventions_path or dataset_root / "interventions.jsonl")
    dataset_version = dataset_root.name

    base_tasks = read_jsonl(base_tasks_path, BaseTask)
    interventions = read_jsonl(interventions_path, InterventionSpec)
    instances = read_jsonl(instances_path, BenchmarkInstance)
    base_by_id = {task.task_id: task for task in base_tasks}

    quality = run_quality_checks(base_tasks, interventions, instances)
    per_intervention: dict[str, dict[str, Any]] = {}
    flag_counts: Counter[str] = Counter()

    for intervention in interventions:
        base_task = base_by_id.get(intervention.base_task_id)
        if base_task is None:
            continue
        issues = list(quality["intervention_issues"].get(intervention.intervention_id, []))
        issues.extend(_family_specific_isolation(base_task, intervention))
        flags: list[str] = []
        for issue in issues:
            flags.extend(_isolation_flags(issue))
        flags = sorted(set(flags))
        for flag in flags:
            flag_counts[flag] += 1
        per_intervention[intervention.intervention_id] = {
            "intervention_id": intervention.intervention_id,
            "base_task_id": intervention.base_task_id,
            "family": intervention.family,
            "changed_factor": intervention.changed_factor,
            "issues": issues,
            "isolation_flags": flags,
            "passed": not issues,
        }

    passed = sum(1 for row in per_intervention.values() if row["passed"])
    report: dict[str, Any] = {
        "dataset_version": dataset_version,
        "instances_path": str(instances_path),
        "base_tasks_path": str(base_tasks_path),
        "interventions_path": str(interventions_path),
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(Path.cwd()),
        "scope": "Intervention isolation audit only; engineering QA, not scientific evidence.",
        "summary": {
            "interventions_audited": len(per_intervention),
            "passed": passed,
            "failed": len(per_intervention) - passed,
            "flag_counts": dict(sorted(flag_counts.items())),
        },
        "quality_report_passed": quality["passed"],
        "interventions": per_intervention,
    }
    report["passed"] = passed == len(per_intervention) and not quality["intervention_issues"]

    out_dir = Path(output_dir or Path("audits/intervention_isolation") / dataset_version)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "intervention_isolation_report.json", report)
    (out_dir / "intervention_isolation_report.md").write_text(
        _isolation_report_markdown(report),
        encoding="utf-8",
    )
    return report


def _isolation_report_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Intervention Isolation Report",
        "",
        f"Dataset: `{report['dataset_version']}`",
        f"Generated: `{report['generated_at']}`",
        f"Passed: `{report['passed']}`",
        "",
        "## Summary",
        "",
        f"- Interventions audited: {summary['interventions_audited']}",
        f"- Passed isolation checks: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "",
        "## Isolation flag counts",
        "",
    ]
    if summary["flag_counts"]:
        for flag, count in summary["flag_counts"].items():
            lines.append(f"- `{flag}`: {count}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Failed interventions", ""])
    failed = [row for row in report["interventions"].values() if not row["passed"]]
    if not failed:
        lines.append("None.")
    else:
        for row in failed[:30]:
            flags = ", ".join(row["isolation_flags"]) or "see issues"
            issue_text = "; ".join(row["issues"][:3])
            lines.append(
                f"- `{row['intervention_id']}` ({row['family']}): flags=[{flags}] — {issue_text}"
            )
        if len(failed) > 30:
            lines.append(f"- ... {len(failed) - 30} additional failures omitted.")
    lines.append("")
    return "\n".join(lines)
