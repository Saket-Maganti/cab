"""Fail-closed static linter for canonical CAB task/intervention packs."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from causal_agent_bench.agent_payload import (
    build_agent_task_context,
    validate_agent_task_context,
)
from causal_agent_bench.answer_contracts import FallbackMode
from causal_agent_bench.generation.answer_policies import (
    content_hash,
    intervention_answer_contract,
)
from causal_agent_bench.schemas import (
    BaseTask,
    BenchmarkInstance,
    InterventionSpec,
)
from causal_agent_bench.validation import (
    validate_instance,
    validate_intervention,
    validate_task,
)

BASE_METADATA_FIELDS = frozenset(
    {
        "schema_version",
        "task_version",
        "source",
        "license",
        "provenance",
        "template_id",
        "split_role",
        "content_hash",
        "human_validation_state",
    }
)
INTERVENTION_METADATA_FIELDS = frozenset(
    {
        "schema_version",
        "intervention_version",
        "source",
        "license",
        "provenance",
        "goal_preservation_statement",
        "required_invariances",
        "changed_fields",
        "unchanged_fields",
        "environment_mutation",
        "tool_mutation",
        "observation_mutation",
        "memory_mutation",
        "answer_policy_change",
        "scorer_policy_change",
        "manipulation_check",
        "human_validation_state",
        "content_hash",
    }
)


def lint_task_intervention_dataset(
    dataset_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    role: str,
    selected_instance_ids: Iterable[str] | None = None,
    strict_explicit_policies: bool = True,
) -> dict[str, Any]:
    """Lint one materialized dataset without running an agent or provider."""

    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    dataset = Path(dataset_dir)
    if not dataset.is_absolute():
        dataset = root / dataset
    selected = set(selected_instance_ids or [])
    issues: list[dict[str, Any]] = []

    base_rows = _read_jsonl(dataset / "base_tasks.jsonl", issues)
    intervention_rows = _read_jsonl(dataset / "interventions.jsonl", issues)
    instance_rows = _read_jsonl(dataset / "instances.jsonl", issues)
    if selected:
        instance_rows = [
            row
            for row in instance_rows
            if str(row.get("instance_id", "")) in selected
        ]
        selected_base_ids = {
            _base_id_from_instance_row(row) for row in instance_rows
        }
        selected_intervention_ids = {
            str((row.get("intervention") or {}).get("intervention_id", ""))
            for row in instance_rows
            if isinstance(row.get("intervention"), dict)
        }
        base_rows = [
            row
            for row in base_rows
            if str(row.get("task_id", "")) in selected_base_ids
        ]
        intervention_rows = [
            row
            for row in intervention_rows
            if str(row.get("intervention_id", "")) in selected_intervention_ids
        ]

    base_tasks: dict[str, BaseTask] = {}
    interventions: dict[str, InterventionSpec] = {}
    instances: dict[str, BenchmarkInstance] = {}

    _lint_base_tasks(
        base_rows,
        base_tasks,
        issues,
        dataset=dataset,
        root=root,
        role=role,
        strict_explicit_policies=strict_explicit_policies,
    )
    _lint_interventions(
        intervention_rows,
        interventions,
        base_tasks,
        issues,
        dataset=dataset,
        root=root,
        strict_explicit_policies=strict_explicit_policies,
    )
    _lint_instances(
        instance_rows,
        instances,
        base_tasks,
        interventions,
        issues,
        dataset=dataset,
        root=root,
    )
    _lint_coverage(
        base_tasks,
        interventions,
        instances,
        issues,
        dataset=dataset,
        root=root,
    )

    severity_counts = Counter(issue["severity"] for issue in issues)
    blockers = [
        issue for issue in issues if issue["severity"] in {"blocker", "error"}
    ]
    warnings = [issue for issue in issues if issue["severity"] == "warning"]
    contract_records: list[BaseTask | InterventionSpec] = [
        *base_tasks.values(),
        *interventions.values(),
    ]
    valid_content_hash_count = len(
        [
            value
            for value in contract_records
            if value.metadata.get("content_hash") == content_hash(value)
        ]
    )
    return {
        "scope": (
            "Provider-free schema, linkage, policy, invariance, payload, and "
            "content-hash lint only."
        ),
        "evidence_class": "ENGINEERING_ONLY",
        "dataset": _relative(dataset, root),
        "role": role,
        "selected_instance_count": len(selected),
        "counts": {
            "base_tasks": len(base_tasks),
            "interventions": len(interventions),
            "instances": len(instances),
            "issues": len(issues),
            "blockers": len(blockers),
            "warnings": len(warnings),
            "by_severity": dict(sorted(severity_counts.items())),
        },
        "coverage": {
            "explicit_base_policy_count": sum(
                1
                for task in base_tasks.values()
                if task.answer_contract
                and task.gold_answer_policy
                and task.scorer_policy
            ),
            "explicit_intervention_policy_count": sum(
                1
                for intervention in interventions.values()
                if intervention.answer_contract
                and intervention.gold_answer_policy
                and intervention.scorer_policy
            ),
            "valid_content_hash_count": valid_content_hash_count,
        },
        "passed": not blockers,
        "issues": issues,
    }


def _lint_base_tasks(
    rows: list[dict[str, Any]],
    output: dict[str, BaseTask],
    issues: list[dict[str, Any]],
    *,
    dataset: Path,
    root: Path,
    role: str,
    strict_explicit_policies: bool,
) -> None:
    seen: set[str] = set()
    for line_no, row in enumerate(rows, start=1):
        task_id = str(row.get("task_id", ""))
        if task_id in seen:
            issues.append(
                _issue(
                    dataset / "base_tasks.jsonl",
                    root,
                    task_id,
                    "task_id",
                    "blocker",
                    "duplicate_task_id",
                    "Make every base-task ID unique within the pack.",
                    line=line_no,
                )
            )
            continue
        seen.add(task_id)
        try:
            task = BaseTask.model_validate(row)
        except ValidationError as exc:
            issues.append(
                _issue(
                    dataset / "base_tasks.jsonl",
                    root,
                    task_id,
                    "schema",
                    "blocker",
                    "base_task_schema_invalid",
                    "Repair the record to satisfy the BaseTask schema.",
                    detail=str(exc),
                    line=line_no,
                )
            )
            continue
        output[task.task_id] = task
        for detail in validate_task(task):
            issues.append(
                _issue(
                    dataset / "base_tasks.jsonl",
                    root,
                    task.task_id,
                    "task",
                    "blocker",
                    "base_task_contract_invalid",
                    "Repair the task-level contract field.",
                    detail=detail,
                    line=line_no,
                )
            )

        missing_metadata = sorted(BASE_METADATA_FIELDS - set(task.metadata))
        if missing_metadata:
            issues.append(
                _issue(
                    dataset / "base_tasks.jsonl",
                    root,
                    task.task_id,
                    "metadata",
                    "blocker",
                    "base_task_canonical_metadata_missing",
                    "Regenerate the pack with canonical task metadata.",
                    detail=f"missing={missing_metadata}",
                    line=line_no,
                )
            )
        if task.metadata.get("split_role") != role:
            issues.append(
                _issue(
                    dataset / "base_tasks.jsonl",
                    root,
                    task.task_id,
                    "metadata.split_role",
                    "blocker",
                    "canonical_split_role_mismatch",
                    "Regenerate the task with its exact canonical study role.",
                    detail=(
                        f"expected={role!r} "
                        f"actual={task.metadata.get('split_role')!r}"
                    ),
                    line=line_no,
                )
            )
        _check_source_license(
            task.metadata,
            dataset / "base_tasks.jsonl",
            task.task_id,
            line_no,
            issues,
            root,
        )
        if not task.expected_output_schema:
            issues.append(
                _issue(
                    dataset / "base_tasks.jsonl",
                    root,
                    task.task_id,
                    "expected_output_schema",
                    "blocker",
                    "expected_output_schema_missing",
                    "Define a machine-readable expected-output schema.",
                    line=line_no,
                )
            )
        if not task.ambiguity_policy or not task.abstention_policy:
            issues.append(
                _issue(
                    dataset / "base_tasks.jsonl",
                    root,
                    task.task_id,
                    "ambiguity_policy/abstention_policy",
                    "blocker",
                    "task_behavior_policy_missing",
                    "Define ambiguity and abstention policies before execution.",
                    line=line_no,
                )
            )
        if strict_explicit_policies:
            _check_explicit_task_policy(
                task,
                dataset / "base_tasks.jsonl",
                line_no,
                issues,
                root,
            )
        _check_content_hash(
            task,
            dataset / "base_tasks.jsonl",
            task.task_id,
            line_no,
            issues,
            root,
        )


def _lint_interventions(
    rows: list[dict[str, Any]],
    output: dict[str, InterventionSpec],
    base_tasks: dict[str, BaseTask],
    issues: list[dict[str, Any]],
    *,
    dataset: Path,
    root: Path,
    strict_explicit_policies: bool,
) -> None:
    seen: set[str] = set()
    for line_no, row in enumerate(rows, start=1):
        intervention_id = str(row.get("intervention_id", ""))
        base_task_id = str(row.get("base_task_id", ""))
        if intervention_id in seen:
            issues.append(
                _issue(
                    dataset / "interventions.jsonl",
                    root,
                    base_task_id,
                    "intervention_id",
                    "blocker",
                    "duplicate_intervention_id",
                    "Make every intervention ID unique within the pack.",
                    detail=intervention_id,
                    line=line_no,
                )
            )
            continue
        seen.add(intervention_id)
        try:
            intervention = InterventionSpec.model_validate(row)
        except ValidationError as exc:
            issues.append(
                _issue(
                    dataset / "interventions.jsonl",
                    root,
                    base_task_id,
                    "schema",
                    "blocker",
                    "intervention_schema_invalid",
                    "Repair the record to satisfy InterventionSpec.",
                    detail=str(exc),
                    line=line_no,
                )
            )
            continue
        output[intervention.intervention_id] = intervention
        task = base_tasks.get(intervention.base_task_id)
        if task is None:
            issues.append(
                _issue(
                    dataset / "interventions.jsonl",
                    root,
                    intervention.base_task_id,
                    "base_task_id",
                    "blocker",
                    "intervention_base_task_missing",
                    "Point the intervention to a base task in the same pack.",
                    detail=intervention.intervention_id,
                    line=line_no,
                )
            )
            continue
        for detail in validate_intervention(task, intervention):
            issues.append(
                _issue(
                    dataset / "interventions.jsonl",
                    root,
                    task.task_id,
                    "intervention",
                    "blocker",
                    "intervention_contract_invalid",
                    "Repair the intervention linkage or single-factor patch.",
                    detail=detail,
                    line=line_no,
                )
            )
        missing_metadata = sorted(
            INTERVENTION_METADATA_FIELDS - set(intervention.metadata)
        )
        if missing_metadata:
            issues.append(
                _issue(
                    dataset / "interventions.jsonl",
                    root,
                    task.task_id,
                    "metadata",
                    "blocker",
                    "intervention_canonical_metadata_missing",
                    "Regenerate the pack with canonical intervention metadata.",
                    detail=f"missing={missing_metadata}",
                    line=line_no,
                )
            )
        _check_source_license(
            intervention.metadata,
            dataset / "interventions.jsonl",
            task.task_id,
            line_no,
            issues,
            root,
        )
        if (
            not intervention.target_factor
            or not intervention.non_target_factors
            or not intervention.expected_robust_behavior
            or not intervention.scoring_notes.strip()
        ):
            issues.append(
                _issue(
                    dataset / "interventions.jsonl",
                    root,
                    task.task_id,
                    "validity_contract",
                    "blocker",
                    "intervention_validity_contract_incomplete",
                    "Define the target factor, invariances, adaptation, and scoring notes.",
                    detail=intervention.intervention_id,
                    line=line_no,
                )
            )
        if strict_explicit_policies:
            _check_explicit_intervention_policy(
                task,
                intervention,
                dataset / "interventions.jsonl",
                line_no,
                issues,
                root,
            )
        _check_content_hash(
            intervention,
            dataset / "interventions.jsonl",
            task.task_id,
            line_no,
            issues,
            root,
        )


def _lint_instances(
    rows: list[dict[str, Any]],
    output: dict[str, BenchmarkInstance],
    base_tasks: dict[str, BaseTask],
    interventions: dict[str, InterventionSpec],
    issues: list[dict[str, Any]],
    *,
    dataset: Path,
    root: Path,
) -> None:
    for line_no, row in enumerate(rows, start=1):
        instance_id = str(row.get("instance_id", ""))
        if instance_id in output:
            issues.append(
                _issue(
                    dataset / "instances.jsonl",
                    root,
                    _base_id_from_instance_row(row),
                    "instance_id",
                    "blocker",
                    "duplicate_instance_id",
                    "Make every instance ID unique within the pack.",
                    detail=instance_id,
                    line=line_no,
                )
            )
            continue
        try:
            instance = BenchmarkInstance.model_validate(row)
        except ValidationError as exc:
            issues.append(
                _issue(
                    dataset / "instances.jsonl",
                    root,
                    _base_id_from_instance_row(row),
                    "schema",
                    "blocker",
                    "instance_schema_invalid",
                    "Repair the record to satisfy BenchmarkInstance.",
                    detail=str(exc),
                    line=line_no,
                )
            )
            continue
        output[instance.instance_id] = instance
        for detail in validate_instance(instance):
            issues.append(
                _issue(
                    dataset / "instances.jsonl",
                    root,
                    instance.base_task.task_id,
                    "instance",
                    "blocker",
                    "instance_contract_invalid",
                    "Repair condition linkage or patched tool availability.",
                    detail=detail,
                    line=line_no,
                )
            )
        canonical_task = base_tasks.get(instance.base_task.task_id)
        if canonical_task is None:
            issues.append(
                _issue(
                    dataset / "instances.jsonl",
                    root,
                    instance.base_task.task_id,
                    "base_task",
                    "blocker",
                    "instance_embedded_base_missing",
                    "Include the referenced base task in base_tasks.jsonl.",
                    line=line_no,
                )
            )
        elif canonical_task.model_dump(mode="json") != instance.base_task.model_dump(
            mode="json"
        ):
            issues.append(
                _issue(
                    dataset / "instances.jsonl",
                    root,
                    instance.base_task.task_id,
                    "base_task",
                    "blocker",
                    "instance_embedded_base_mismatch",
                    "Regenerate instances from the canonical base-task record.",
                    line=line_no,
                )
            )
        if instance.intervention is not None:
            canonical_intervention = interventions.get(
                instance.intervention.intervention_id
            )
            if canonical_intervention is None:
                issues.append(
                    _issue(
                        dataset / "instances.jsonl",
                        root,
                        instance.base_task.task_id,
                        "intervention",
                        "blocker",
                        "instance_embedded_intervention_missing",
                        "Include the intervention in interventions.jsonl.",
                        detail=instance.intervention.intervention_id,
                        line=line_no,
                    )
                )
            elif canonical_intervention.model_dump(
                mode="json"
            ) != instance.intervention.model_dump(mode="json"):
                issues.append(
                    _issue(
                        dataset / "instances.jsonl",
                        root,
                        instance.base_task.task_id,
                        "intervention",
                        "blocker",
                        "instance_embedded_intervention_mismatch",
                        "Regenerate instances from the canonical intervention record.",
                        line=line_no,
                    )
                )
        payload_issues = validate_agent_task_context(
            build_agent_task_context(instance)
        )
        for detail in payload_issues:
            issues.append(
                _issue(
                    dataset / "instances.jsonl",
                    root,
                    instance.base_task.task_id,
                    "agent_visible_payload",
                    "blocker",
                    "agent_payload_allowlist_violation",
                    "Expose only the canonical evaluator-blind task allowlist.",
                    detail=detail,
                    line=line_no,
                )
            )


def _lint_coverage(
    base_tasks: dict[str, BaseTask],
    interventions: dict[str, InterventionSpec],
    instances: dict[str, BenchmarkInstance],
    issues: list[dict[str, Any]],
    *,
    dataset: Path,
    root: Path,
) -> None:
    clean_by_base: Counter[str] = Counter()
    intervention_instances: Counter[str] = Counter()
    family_by_base: dict[str, set[str]] = defaultdict(set)
    for instance in instances.values():
        if instance.condition == "clean":
            clean_by_base[instance.base_task.task_id] += 1
        elif instance.intervention is not None:
            intervention_instances[instance.intervention.intervention_id] += 1
            family_by_base[instance.base_task.task_id].add(
                instance.intervention.family
            )
    for task_id in {
        instance.base_task.task_id for instance in instances.values()
    }:
        if clean_by_base[task_id] != 1:
            issues.append(
                _issue(
                    dataset / "instances.jsonl",
                    root,
                    task_id,
                    "condition",
                    "blocker",
                    "clean_pair_coverage_invalid",
                    "Include exactly one clean baseline for every selected base task.",
                    detail=f"clean_count={clean_by_base[task_id]}",
                )
            )
    selected_intervention_ids = {
        instance.intervention.intervention_id
        for instance in instances.values()
        if instance.intervention is not None
    }
    for intervention_id in selected_intervention_ids:
        if intervention_instances[intervention_id] != 1:
            intervention = interventions.get(intervention_id)
            issues.append(
                _issue(
                    dataset / "instances.jsonl",
                    root,
                    intervention.base_task_id if intervention else "",
                    "intervention_id",
                    "blocker",
                    "intervention_instance_coverage_invalid",
                    "Include exactly one instance for every selected intervention.",
                    detail=(
                        f"{intervention_id}: "
                        f"count={intervention_instances[intervention_id]}"
                    ),
                )
            )


def _check_explicit_task_policy(
    task: BaseTask,
    path: Path,
    line_no: int,
    issues: list[dict[str, Any]],
    root: Path,
) -> None:
    if (
        task.answer_contract is None
        or task.gold_answer_policy is None
        or task.scorer_policy is None
    ):
        issues.append(
            _issue(
                path,
                root,
                task.task_id,
                "answer_contract/gold_answer_policy/scorer_policy",
                "blocker",
                "explicit_task_policy_missing",
                "Attach preregistered typed task policies; derived legacy policy is not run-eligible.",
                line=line_no,
            )
        )
        return
    if task.answer_contract != task.gold_answer_policy.answer_contract:
        issues.append(
            _issue(
                path,
                root,
                task.task_id,
                "answer_contract",
                "blocker",
                "task_policy_contract_mismatch",
                "Use the same answer contract in the task and gold policy.",
                line=line_no,
            )
        )
    if task.scorer_policy.fallback_mode != FallbackMode.DISABLED:
        issues.append(
            _issue(
                path,
                root,
                task.task_id,
                "scorer_policy.fallback_mode",
                "blocker",
                "scientific_task_uses_legacy_fallback",
                "Disable substring fallback for scientific packs.",
                line=line_no,
            )
        )


def _check_explicit_intervention_policy(
    task: BaseTask,
    intervention: InterventionSpec,
    path: Path,
    line_no: int,
    issues: list[dict[str, Any]],
    root: Path,
) -> None:
    if (
        intervention.answer_contract is None
        or intervention.gold_answer_policy is None
        or intervention.scorer_policy is None
    ):
        issues.append(
            _issue(
                path,
                root,
                task.task_id,
                "answer_contract/gold_answer_policy/scorer_policy",
                "blocker",
                "explicit_intervention_policy_missing",
                "Attach an intervention-specific typed policy before execution.",
                detail=intervention.intervention_id,
                line=line_no,
            )
        )
        return
    expected_contract = intervention_answer_contract(intervention)
    contracts = {
        intervention.answer_contract,
        intervention.gold_answer_policy.answer_contract,
    }
    if contracts != {expected_contract}:
        issues.append(
            _issue(
                path,
                root,
                task.task_id,
                "answer_contract",
                "blocker",
                "intervention_policy_incompatible",
                "Use the preregistered family-compatible answer contract.",
                detail=(
                    f"expected={expected_contract.value}; "
                    f"actual={sorted(value.value for value in contracts)}"
                ),
                line=line_no,
            )
        )
    if intervention.scorer_policy.fallback_mode != FallbackMode.DISABLED:
        issues.append(
            _issue(
                path,
                root,
                task.task_id,
                "scorer_policy.fallback_mode",
                "blocker",
                "scientific_intervention_uses_legacy_fallback",
                "Disable substring fallback for scientific packs.",
                detail=intervention.intervention_id,
                line=line_no,
            )
        )


def _check_source_license(
    metadata: dict[str, Any],
    path: Path,
    task_id: str,
    line_no: int,
    issues: list[dict[str, Any]],
    root: Path,
) -> None:
    if not str(metadata.get("source", "")).strip():
        issues.append(
            _issue(
                path,
                root,
                task_id,
                "metadata.source",
                "blocker",
                "source_missing",
                "Record a concrete source/provenance value.",
                line=line_no,
            )
        )
    license_value = str(metadata.get("license", "")).strip()
    if not license_value:
        issues.append(
            _issue(
                path,
                root,
                task_id,
                "metadata.license",
                "blocker",
                "license_missing",
                "Record the applicable dataset license.",
                line=line_no,
            )
        )
    elif license_value.endswith(".md") and not (root / license_value).exists():
        issues.append(
            _issue(
                path,
                root,
                task_id,
                "metadata.license",
                "blocker",
                "license_reference_missing",
                "Point the record to an existing license file.",
                detail=license_value,
                line=line_no,
            )
        )


def _check_content_hash(
    value: BaseTask | InterventionSpec,
    path: Path,
    task_id: str,
    line_no: int,
    issues: list[dict[str, Any]],
    root: Path,
) -> None:
    recorded = str(value.metadata.get("content_hash", ""))
    actual = content_hash(value)
    if len(recorded) != 64 or recorded != actual:
        issues.append(
            _issue(
                path,
                root,
                task_id,
                "metadata.content_hash",
                "blocker",
                "content_hash_invalid",
                "Regenerate the canonical content hash after all policy fields are fixed.",
                detail=f"recorded={recorded or 'missing'} actual={actual}",
                line=line_no,
            )
        )


def _read_jsonl(
    path: Path,
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not path.exists():
        issues.append(
            {
                "file": str(path),
                "task_id": None,
                "field": "file",
                "severity": "blocker",
                "code": "canonical_file_missing",
                "detail": "required JSONL file is missing",
                "suggested_repair": "Materialize the canonical dataset pack.",
                "automatic_repair_status": "not_attempted",
                "unresolved_human_review_state": False,
            }
        )
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append(
                    {
                        "file": str(path),
                        "line": line_no,
                        "task_id": None,
                        "field": "json",
                        "severity": "blocker",
                        "code": "jsonl_decode_error",
                        "detail": str(exc),
                        "suggested_repair": "Repair the malformed JSONL row.",
                        "automatic_repair_status": "not_attempted",
                        "unresolved_human_review_state": False,
                    }
                )
                continue
            if not isinstance(value, dict):
                issues.append(
                    {
                        "file": str(path),
                        "line": line_no,
                        "task_id": None,
                        "field": "json",
                        "severity": "blocker",
                        "code": "jsonl_row_not_object",
                        "detail": "JSONL row must be an object",
                        "suggested_repair": "Replace the row with an object.",
                        "automatic_repair_status": "not_attempted",
                        "unresolved_human_review_state": False,
                    }
                )
                continue
            rows.append(value)
    return rows


def _base_id_from_instance_row(row: dict[str, Any]) -> str:
    base = row.get("base_task")
    if isinstance(base, dict) and base.get("task_id"):
        return str(base["task_id"])
    intervention = row.get("intervention")
    if isinstance(intervention, dict) and intervention.get("base_task_id"):
        return str(intervention["base_task_id"])
    instance_id = str(row.get("instance_id", ""))
    return instance_id.rsplit(".", 1)[0] if "." in instance_id else instance_id


def _issue(
    path: Path,
    root: Path,
    task_id: str | None,
    field: str,
    severity: str,
    code: str,
    suggested_repair: str,
    *,
    detail: str | None = None,
    line: int | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "file": _relative(path, root),
        "task_id": task_id or None,
        "field": field,
        "severity": severity,
        "code": code,
        "detail": detail or code,
        "suggested_repair": suggested_repair,
        "automatic_repair_status": "not_attempted",
        "unresolved_human_review_state": False,
    }
    if line is not None:
        value["line"] = line
    return value


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "BASE_METADATA_FIELDS",
    "INTERVENTION_METADATA_FIELDS",
    "lint_task_intervention_dataset",
]
