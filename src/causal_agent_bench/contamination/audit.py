from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.agent_payload import build_agent_task_context
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, InterventionSpec
from causal_agent_bench.tools.registry import ToolRegistry
from causal_agent_bench.utils.io import git_commit, read_json, read_jsonl

CANARY_PREFIX = "CAB-CANARY"
PUBLIC_SPLITS = frozenset({"dev", "pilot", "validation"})
HIDDEN_SPLITS = frozenset({"test", "heldout_templates"})
NEAR_DUPLICATE_THRESHOLD = 0.85
NEAR_DUPLICATE_ERROR_THRESHOLD = 0.95
EXCLUDED_HIDDEN_GT_KEYS = frozenset(
    {"template_domain", "public_domain", "variant", "task_style", "generator_seed"}
)
MIN_LEAK_SUBSTRING_LEN = 20
CRITICAL_ERROR_CATEGORIES = frozenset(
    {
        "canary_leak",
        "intervention_patch_details_leak",
        "intervention_scoring_notes_leak",
        "hidden_ground_truth_leak",
    }
)

CONTAMINATION_RISKS = [
    "Public task instructions and tool schemas may appear in pretraining corpora.",
    "Models may memorize template variants seen during method development on pilot splits.",
    "Repeated submissions on the held-out test split enable adaptive overfitting.",
    "Oracle or hidden-metadata exposure inflates scores without realistic agent skill.",
    "Near-duplicate instructions across splits reduce effective held-out size.",
]

MITIGATIONS = [
    "Use disjoint release splits (`release_disjoint_v1`) and report the eval split explicitly.",
    "Assign per-task template fingerprints and audit cross-split template collisions.",
    "Embed canary strings on hidden splits and scan public splits for leakage.",
    "Run prompt-leakage checks before agent evaluation exports.",
    "Exclude oracle agents from leaderboard rows; label engineering-only runs.",
    "Version datasets with `dataset_hash` and freeze manifests before headline claims.",
]

REMAINING_LIMITATIONS = [
    "Synthetic tasks are not a proxy for live web or enterprise tool environments.",
    "Canary and near-duplicate checks are heuristic; they do not prove absence of memorization.",
    "Tool descriptions are shared across tasks and may still correlate with public documentation.",
    "Human validation is still required before strong robustness claims.",
]


def template_fingerprint(task: BaseTask) -> str:
    """Stable fingerprint for a task template (ignores per-instance numeric suffixes)."""

    instruction = _normalize_template_text(task.goal.user_instruction)
    template_domain = task.hidden_ground_truth.get("template_domain") or task.domain
    return stable_hash(
        {
            "domain": task.domain,
            "template_domain": template_domain,
            "template_variant": task.metadata.get("template_variant"),
            "instruction_skeleton": instruction,
            "available_tools": sorted(task.available_tools),
            "gold_tool_sequence": task.gold_tool_sequence,
            "tags": sorted(task.tags),
        },
        length=16,
    )


def make_canary_string(dataset_version: str, task_id: str) -> str:
    token = stable_hash({"dataset_version": dataset_version, "task_id": task_id}, length=12)
    return f"{CANARY_PREFIX}-{dataset_version}-{token}"


def assign_canary_strings(
    base_tasks: list[BaseTask],
    split_policy: dict[str, Any],
    *,
    dataset_version: str,
) -> dict[str, str]:
    """Return canary strings that should be present on hidden-split base tasks."""

    hidden_ids = _split_base_task_ids(split_policy, set(HIDDEN_SPLITS))
    return {
        task.task_id: make_canary_string(dataset_version, task.task_id)
        for task in base_tasks
        if task.task_id in hidden_ids
    }


def apply_canary_metadata(
    base_tasks: list[BaseTask],
    split_policy: dict[str, Any],
    *,
    dataset_version: str,
) -> list[BaseTask]:
    """Attach `metadata.contamination_canary` to hidden-split base tasks."""

    canaries = assign_canary_strings(
        base_tasks, split_policy, dataset_version=dataset_version
    )
    updated: list[BaseTask] = []
    for task in base_tasks:
        canary = canaries.get(task.task_id)
        if not canary:
            updated.append(task)
            continue
        metadata = dict(task.metadata)
        metadata["contamination_canary"] = canary
        updated.append(task.model_copy(update={"metadata": metadata}))
    return updated


def run_contamination_audit(
    benchmark_dir: str | Path,
    *,
    splits_path: str | Path | None = None,
    near_duplicate_threshold: float = NEAR_DUPLICATE_THRESHOLD,
) -> dict[str, Any]:
    benchmark_path = Path(benchmark_dir)
    splits_file = Path(splits_path) if splits_path else benchmark_path / "splits.json"
    base_tasks = read_jsonl(benchmark_path / "base_tasks.jsonl", BaseTask)
    interventions = read_jsonl(benchmark_path / "interventions.jsonl", InterventionSpec)
    instances = read_jsonl(benchmark_path / "instances.jsonl", BenchmarkInstance)
    split_policy = read_json(splits_file) if splits_file.exists() else {}
    dataset_version = str(
        split_policy.get("benchmark_version")
        or _read_optional_version(benchmark_path)
        or benchmark_path.name
    )
    split_map = _task_split_map(split_policy)
    findings: list[dict[str, Any]] = []

    fingerprint_section = _fingerprint_section(base_tasks, split_map)
    findings.extend(fingerprint_section["findings"])

    canary_section = _canary_section(base_tasks, split_policy, dataset_version)
    findings.extend(canary_section["findings"])

    near_duplicate_section = _near_duplicate_section(
        base_tasks, split_map, threshold=near_duplicate_threshold
    )
    findings.extend(near_duplicate_section["findings"])

    leakage_section = _prompt_leakage_section(base_tasks, interventions, instances)
    findings.extend(leakage_section["findings"])

    errors = [finding for finding in findings if finding["severity"] == "error"]
    warnings = [finding for finding in findings if finding["severity"] == "warning"]
    critical_errors = [finding for finding in errors if finding["category"] in CRITICAL_ERROR_CATEGORIES]
    return {
        "passed": not critical_errors,
        "audited_at": datetime.now(UTC).isoformat(),
        "benchmark_dir": str(benchmark_path),
        "splits_path": str(splits_file) if splits_file.exists() else None,
        "dataset_version": dataset_version,
        "git_commit": git_commit(Path.cwd()),
        "near_duplicate_threshold": near_duplicate_threshold,
        "summary": {
            "n_base_tasks": len(base_tasks),
            "n_instances": len(instances),
            "n_errors": len(errors),
            "n_warnings": len(warnings),
            "n_critical_errors": len(critical_errors),
        },
        "fingerprinting": fingerprint_section,
        "canaries": canary_section,
        "near_duplicates": near_duplicate_section,
        "prompt_leakage": leakage_section,
        "contamination_risks": list(CONTAMINATION_RISKS),
        "mitigations": list(MITIGATIONS),
        "remaining_limitations": list(REMAINING_LIMITATIONS),
        "findings": findings,
    }


def contamination_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Contamination and Memorization Audit",
        "",
        f"Passed: `{report.get('passed')}`",
        f"Dataset version: `{report.get('dataset_version')}`",
        f"Benchmark dir: `{report.get('benchmark_dir')}`",
        f"Splits path: `{report.get('splits_path')}`",
        f"Audited at: `{report.get('audited_at')}`",
        "",
        "## Summary",
        "",
        f"- Base tasks: {report.get('summary', {}).get('n_base_tasks')}",
        f"- Instances: {report.get('summary', {}).get('n_instances')}",
        f"- Errors: {report.get('summary', {}).get('n_errors')}",
        f"- Warnings: {report.get('summary', {}).get('n_warnings')}",
        "",
        "## Contamination risks",
        "",
    ]
    lines.extend(f"- {item}" for item in report.get("contamination_risks", []))
    lines.extend(["", "## Mitigations", ""])
    lines.extend(f"- {item}" for item in report.get("mitigations", []))
    lines.extend(["", "## Remaining limitations", ""])
    lines.extend(f"- {item}" for item in report.get("remaining_limitations", []))
    lines.extend(
        [
            "",
            "## Fingerprinting",
            "",
            f"- Unique template fingerprints: {report.get('fingerprinting', {}).get('unique_fingerprint_count')}",
            f"- Cross-split template collisions: {len(report.get('fingerprinting', {}).get('collisions', []))}",
            "",
            "## Canaries",
            "",
            f"- Expected hidden canaries: {report.get('canaries', {}).get('expected_count')}",
            f"- Stored on tasks: {report.get('canaries', {}).get('stored_count')}",
            f"- Missing assignments: {len(report.get('canaries', {}).get('missing', []))}",
            f"- Leaks into public splits: {len(report.get('canaries', {}).get('leaks_in_public', []))}",
            "",
            "## Near duplicates",
            "",
            f"- Threshold (Jaccard): {report.get('near_duplicate_threshold')}",
            f"- Cross-split pairs flagged: {len(report.get('near_duplicates', {}).get('pairs', []))}",
            "",
            "## Prompt leakage",
            "",
            f"- Instances checked: {report.get('prompt_leakage', {}).get('instances_checked')}",
            f"- Findings: {len(report.get('prompt_leakage', {}).get('findings', []))}",
        f"- Truncated findings: {report.get('prompt_leakage', {}).get('truncated_findings', 0)}",
            "",
            "## Findings",
            "",
            "| Severity | Category | Task / Instance | Detail |",
            "|---|---|---|---|",
        ]
    )
    for finding in report.get("findings", [])[:200]:
        lines.append(
            "| {severity} | {category} | `{subject}` | {detail} |".format(
                severity=finding.get("severity"),
                category=finding.get("category"),
                subject=finding.get("subject", ""),
                detail=str(finding.get("detail", "")).replace("|", "\\|")[:180],
            )
        )
    if len(report.get("findings", [])) > 200:
        lines.append(f"\n_... truncated {len(report['findings']) - 200} additional findings._")
    lines.append("")
    return "\n".join(lines)


def _fingerprint_section(
    base_tasks: list[BaseTask],
    split_map: dict[str, str],
) -> dict[str, Any]:
    fingerprints = {task.task_id: template_fingerprint(task) for task in base_tasks}
    by_fingerprint: dict[str, list[str]] = defaultdict(list)
    for task_id, fingerprint in fingerprints.items():
        by_fingerprint[fingerprint].append(task_id)

    collisions: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for fingerprint, task_ids in sorted(by_fingerprint.items()):
        if len(task_ids) < 2:
            continue
        splits = {split_map.get(task_id, "unknown") for task_id in task_ids}
        if len(splits) > 1:
            collisions.append(
                {
                    "fingerprint": fingerprint,
                    "task_ids": task_ids,
                    "splits": sorted(splits),
                }
            )
            findings.append(
                {
                    "severity": "warning",
                    "category": "template_fingerprint_collision",
                    "subject": fingerprint,
                    "detail": f"Same template fingerprint across splits {sorted(splits)}: {task_ids[:4]}",
                }
            )

    templates_per_split: dict[str, Counter[str]] = {}
    for task_id, fingerprint in fingerprints.items():
        split_name = split_map.get(task_id, "unknown")
        templates_per_split.setdefault(split_name, Counter())[fingerprint] += 1

    return {
        "fingerprints_by_task": fingerprints,
        "unique_fingerprint_count": len(by_fingerprint),
        "templates_per_split": {
            split: dict(counter) for split, counter in sorted(templates_per_split.items())
        },
        "collisions": collisions,
        "findings": findings,
    }


def _canary_section(
    base_tasks: list[BaseTask],
    split_policy: dict[str, Any],
    dataset_version: str,
) -> dict[str, Any]:
    split_map = _task_split_map(split_policy)
    expected = assign_canary_strings(base_tasks, split_policy, dataset_version=dataset_version)
    stored = {
        task.task_id: task.metadata.get("contamination_canary")
        for task in base_tasks
        if task.metadata.get("contamination_canary")
    }
    missing = [
        task_id for task_id, canary in expected.items() if stored.get(task_id) != canary
    ]
    public_text = _public_split_corpus(base_tasks, split_map)
    leaks: list[dict[str, str]] = []
    findings: list[dict[str, Any]] = []
    for task_id, canary in expected.items():
        if canary in public_text:
            leaks.append({"canary": canary, "hidden_task_id": task_id})
            findings.append(
                {
                    "severity": "error",
                    "category": "canary_leak",
                    "subject": task_id,
                    "detail": f"Hidden canary string appears in a public split: {canary}",
                }
            )
    if missing:
        findings.append(
            {
                "severity": "warning",
                "category": "canary_missing",
                "subject": "hidden_splits",
                "detail": f"{len(missing)} hidden tasks lack metadata.contamination_canary",
            }
        )
    return {
        "expected": expected,
        "expected_count": len(expected),
        "stored": stored,
        "stored_count": len(stored),
        "missing": missing[:50],
        "leaks_in_public": leaks,
        "findings": findings,
    }


def _near_duplicate_section(
    base_tasks: list[BaseTask],
    split_map: dict[str, str],
    *,
    threshold: float,
) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    tokenized = {
        task.task_id: _instruction_tokens(task.goal.user_instruction) for task in base_tasks
    }
    task_ids = list(tokenized)
    for left_index, left_id in enumerate(task_ids):
        left_split = split_map.get(left_id, "unknown")
        left_tokens = tokenized[left_id]
        for right_id in task_ids[left_index + 1 :]:
            right_split = split_map.get(right_id, "unknown")
            if left_split == right_split:
                continue
            score = _jaccard(left_tokens, tokenized[right_id])
            if score < threshold:
                continue
            pair = {
                "task_a": left_id,
                "task_b": right_id,
                "split_a": left_split,
                "split_b": right_split,
                "jaccard": round(score, 4),
            }
            pairs.append(pair)
            crosses_public_hidden = bool(
                {left_split, right_split} & HIDDEN_SPLITS and {left_split, right_split} & PUBLIC_SPLITS
            )
            severity = (
                "error"
                if crosses_public_hidden and score >= NEAR_DUPLICATE_ERROR_THRESHOLD
                else "warning"
            )
            findings.append(
                {
                    "severity": severity,
                    "category": "near_duplicate_instruction",
                    "subject": f"{left_id}|{right_id}",
                    "detail": (
                        f"Instruction Jaccard {score:.3f} between {left_split} and {right_split}"
                    ),
                }
            )
    pairs.sort(key=lambda row: row["jaccard"], reverse=True)
    return {"pairs": pairs[:100], "findings": findings[:100], "truncated_findings": max(0, len(findings) - 100)}


def _prompt_leakage_section(
    base_tasks: list[BaseTask],
    interventions: list[InterventionSpec],
    instances: list[BenchmarkInstance],
) -> dict[str, Any]:
    registry = ToolRegistry()
    tool_text = json.dumps(
        [tool.model_dump(mode="json") for tool in registry.specs()],
        sort_keys=True,
    )
    intervention_by_id = {item.intervention_id: item for item in interventions}
    findings: list[dict[str, Any]] = []
    for instance in instances:
        payload = _agent_visible_payload(instance)
        visible_text = json.dumps(payload, sort_keys=True, default=str).lower()
        instruction_text = instance.base_task.goal.user_instruction.lower()
        for value in _hidden_ground_truth_leaves(instance.base_task):
            lowered = value.lower()
            if lowered in instruction_text or lowered in visible_text:
                if lowered in visible_text and lowered not in instruction_text:
                    findings.append(
                        {
                            "severity": "error",
                            "category": "hidden_ground_truth_leak",
                            "subject": instance.instance_id,
                            "detail": (
                                "Hidden ground-truth value appears in agent-visible context: "
                                f"{value[:80]}"
                            ),
                        }
                    )
                continue
            if lowered in tool_text.lower():
                findings.append(
                    {
                        "severity": "warning",
                        "category": "hidden_ground_truth_in_tool_catalog",
                        "subject": instance.instance_id,
                        "detail": (
                            "Hidden ground-truth value appears in shared tool catalog: "
                            f"{value[:80]}"
                        ),
                    }
                )

        intervention = instance.intervention
        if intervention is None and instance.condition == "intervention":
            intervention = intervention_by_id.get(instance.instance_id) or next(
                (
                    item
                    for item in interventions
                    if instance.instance_id.startswith(f"{item.base_task_id}.")
                    or instance.instance_id == item.intervention_id
                ),
                None,
            )
        if intervention is not None:
            for field, category in [
                ("patch_details", "intervention_patch_details_leak"),
                ("scoring_notes", "intervention_scoring_notes_leak"),
            ]:
                if _field_visible_in_text(getattr(intervention, field, None), visible_text):
                    findings.append(
                        {
                            "severity": "error",
                            "category": category,
                            "subject": instance.instance_id,
                            "detail": f"{field} content appears in agent-visible context",
                        }
                    )
    by_category = Counter(finding["category"] for finding in findings)
    return {
        "instances_checked": len(instances),
        "findings": findings[:500],
        "truncated_findings": max(0, len(findings) - 500),
        "by_category": dict(sorted(by_category.items())),
    }


def _agent_visible_payload(instance: BenchmarkInstance) -> dict[str, Any]:
    """Mirror the fields exposed to LLM tool agents in `llm_agents._task_context`."""

    return {
        **build_agent_task_context(instance),
        "available_tools": list(instance.available_tools),
    }


def _normalize_template_text(text: str) -> str:
    normalized = re.sub(r"\b\d{3,}\b", "<num>", text.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _instruction_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _collect_string_leaves(value: Any, *, min_len: int) -> list[str]:
    leaves: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            leaves.extend(_collect_string_leaves(item, min_len=min_len))
    elif isinstance(value, list):
        for item in value:
            leaves.extend(_collect_string_leaves(item, min_len=min_len))
    elif isinstance(value, str) and len(value.strip()) >= min_len:
        leaves.append(value.strip())
    elif isinstance(value, int | float) and not isinstance(value, bool):
        leaves.append(str(value))
    return leaves


def _hidden_ground_truth_leaves(task: BaseTask) -> list[str]:
    filtered = {
        key: value
        for key, value in task.hidden_ground_truth.items()
        if key not in EXCLUDED_HIDDEN_GT_KEYS
    }
    return _collect_string_leaves(filtered, min_len=MIN_LEAK_SUBSTRING_LEN)


def _field_visible_in_text(value: Any, visible_text: str) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        snippet = value.strip().lower()
        return len(snippet) >= MIN_LEAK_SUBSTRING_LEN and snippet in visible_text
    serialized = json.dumps(value, sort_keys=True, default=str).lower()
    return len(serialized) >= MIN_LEAK_SUBSTRING_LEN and serialized in visible_text


def _split_base_task_ids(split_policy: dict[str, Any], split_names: set[str]) -> set[str]:
    task_ids: set[str] = set()
    for split_name, payload in split_policy.get("splits", {}).items():
        if split_name in split_names:
            task_ids.update(str(task_id) for task_id in payload.get("base_task_ids", []))
    return task_ids


def _task_split_map(split_policy: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for split_name, payload in split_policy.get("splits", {}).items():
        for task_id in payload.get("base_task_ids", []):
            mapping[str(task_id)] = split_name
    return mapping


def _public_split_corpus(base_tasks: list[BaseTask], split_map: dict[str, str]) -> str:
    chunks: list[str] = []
    for task in base_tasks:
        if split_map.get(task.task_id) not in PUBLIC_SPLITS:
            continue
        chunks.extend(
            [
                task.goal.user_instruction,
                json.dumps(task.goal.expected_final_answer, sort_keys=True, default=str),
                json.dumps(task.hidden_ground_truth, sort_keys=True, default=str),
                json.dumps(task.metadata, sort_keys=True, default=str),
            ]
        )
    return "\n".join(chunks)


def _read_optional_version(benchmark_path: Path) -> str | None:
    generation_report = benchmark_path / "generation_report.json"
    if not generation_report.exists():
        return None
    payload = read_json(generation_report)
    return payload.get("benchmark_version")
