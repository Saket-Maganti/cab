from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from causal_agent_bench.generation.quality_checks import (
    check_base_task,
    check_instance,
    check_intervention,
)
from causal_agent_bench.runners.config import load_experiment_config
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.utils.io import read_jsonl
from causal_agent_bench.validation import validate_jsonl_file


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def _instruction_tokens(text: str) -> set[str]:
    return {token for token in text.lower().split() if len(token) > 3}


def resolve_dataset_path(*, dataset: str | Path | None = None, config: str | Path | None = None) -> Path:
    if dataset is not None:
        return Path(dataset)
    if config is None:
        raise ValueError("one of --dataset or --config is required")
    cfg, _ = load_experiment_config(config)
    return cfg.resolved_benchmark_path()


def audit_dataset(
    dataset_path: str | Path,
    *,
    near_duplicate_threshold: float = 0.85,
) -> dict[str, Any]:
    path = Path(dataset_path)
    schema = validate_jsonl_file(path, schema_type="instances")
    instances = read_jsonl(path, BenchmarkInstance)
    base_tasks = {instance.base_task.task_id: instance.base_task for instance in instances}
    domains = Counter(instance.base_task.domain for instance in instances)
    families = Counter(
        instance.intervention.family if instance.intervention else "clean"
        for instance in instances
    )
    difficulties = Counter(instance.base_task.metadata.get("difficulty", "unknown") for instance in instances)
    clean_count = sum(1 for i in instances if i.intervention is None)
    intervention_count = len(instances) - clean_count
    answer_changes = Counter(
        (instance.intervention.metadata or {}).get("expected_answer_change", "unknown")
        if instance.intervention
        else "clean"
        for instance in instances
    )
    required_tools = [len(instance.base_task.required_tools or []) for instance in instances]
    max_steps = [instance.base_task.max_steps for instance in instances]

    warnings: list[str] = []
    missing_metadata = 0
    quality_issues: list[dict[str, Any]] = []
    for instance in instances:
        issues = check_instance(instance)
        if instance.intervention is not None:
            issues.extend(check_intervention(instance.base_task, instance.intervention))
        issues.extend(check_base_task(instance.base_task))
        if issues:
            quality_issues.append({"instance_id": instance.instance_id, "issues": issues})
        meta = instance.base_task.metadata or {}
        if not meta.get("difficulty") or not meta.get("domain"):
            missing_metadata += 1

    near_duplicates: list[dict[str, Any]] = []
    ids = [instance.instance_id for instance in instances]
    instr_map = {
        instance.instance_id: _instruction_tokens(instance.base_task.goal.user_instruction)
        for instance in instances
    }
    for i, id_a in enumerate(ids):
        for id_b in ids[i + 1 :]:
            score = _jaccard(instr_map[id_a], instr_map[id_b])
            if score >= near_duplicate_threshold:
                near_duplicates.append({"a": id_a, "b": id_b, "jaccard": round(score, 3)})

    hidden_gt_risk = sum(
        1
        for instance in instances
        if not instance.base_task.hidden_ground_truth
        or "answer" in json.dumps(instance.base_task.model_dump(mode="json")).lower()
    )
    tool_mismatch = sum(
        1 for issue in quality_issues if any("tool" in item.lower() for item in issue["issues"])
    )
    impossible = sum(
        1 for issue in quality_issues if any("impossible" in item.lower() for item in issue["issues"])
    )

    if near_duplicates:
        warnings.append(f"{len(near_duplicates)} near-duplicate instruction pair(s) detected.")
    if missing_metadata:
        warnings.append(f"{missing_metadata} instance(s) missing difficulty/domain metadata.")
    if hidden_gt_risk:
        warnings.append(f"{hidden_gt_risk} instance(s) with hidden-ground-truth exposure risk.")
    if impossible:
        warnings.append(f"{impossible} instance(s) flagged as potentially impossible.")
    if schema.get("invalid", 0) > 0:
        warnings.append(f"Schema validation: {schema['invalid']} invalid row(s).")

    return {
        "dataset_path": str(path),
        "n_instances": len(instances),
        "n_base_tasks": len(base_tasks),
        "clean_instances": clean_count,
        "intervention_instances": intervention_count,
        "domain_distribution": dict(domains),
        "intervention_family_distribution": dict(families),
        "difficulty_distribution": dict(difficulties),
        "expected_answer_change_distribution": dict(answer_changes),
        "average_required_tools": round(statistics.mean(required_tools), 3) if required_tools else 0.0,
        "average_max_steps": round(statistics.mean(max_steps), 3) if max_steps else 0.0,
        "schema_validation": schema,
        "near_duplicate_pairs": near_duplicates[:20],
        "missing_metadata_count": missing_metadata,
        "hidden_ground_truth_risk_count": hidden_gt_risk,
        "impossible_task_warnings": impossible,
        "tool_mismatch_warnings": tool_mismatch,
        "quality_issue_count": len(quality_issues),
        "sample_quality_issues": quality_issues[:10],
        "warnings": warnings,
    }


def format_dataset_audit(report: dict[str, Any]) -> str:
    lines = [
        "# Dataset quality audit",
        "",
        f"- **Dataset:** `{report['dataset_path']}`",
        f"- **Instances:** {report['n_instances']}",
        f"- **Base tasks:** {report['n_base_tasks']}",
        f"- **Clean / intervention:** {report['clean_instances']} / {report['intervention_instances']}",
        f"- **Avg required tools:** {report['average_required_tools']}",
        f"- **Avg max steps:** {report['average_max_steps']}",
        "",
        "## Domain distribution",
    ]
    for key, count in sorted(report["domain_distribution"].items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Intervention families"])
    for key, count in sorted(report["intervention_family_distribution"].items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Warnings"])
    lines.extend(f"- {w}" for w in report["warnings"])
    lines.append("- none")
    return "\n".join(lines) + "\n"


def write_dataset_audit(
    dataset_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    report = audit_dataset(dataset_path)
    path = Path(dataset_path)
    if output_dir is None:
        out = Path("audits/dataset_quality") / path.parent.name
    else:
        out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    md_path = out / f"{stem}_dataset_audit.md"
    json_path = out / f"{stem}_dataset_audit.json"
    md_path.write_text(format_dataset_audit(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"markdown": md_path, "json": json_path}
