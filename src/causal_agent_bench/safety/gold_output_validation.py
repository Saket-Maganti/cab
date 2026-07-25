"""Static gold-answer and expected-output validation."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.benchmark_quality import discover_benchmark_dirs
from causal_agent_bench.safety.common import section_markdown, write_dual_report
from causal_agent_bench.safety.intervention_isolation import load_intervention_taxonomy

PLACEHOLDER_VALUES = {"", "todo", "tbd", "n/a", "na", "none", "placeholder", "fill_me", "fixme"}
ANSWER_PRESERVING = {"answer_preserving", "no", "false", "unchanged"}
ANSWER_CHANGING = {"answer_changing", "yes", "true", "changed"}


def build_gold_output_validation(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    taxonomy_path: str | Path | None = None,
    output_dir: str | Path = "reports/gold_outputs",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    dataset_dirs = [Path(benchmark_dir)] if benchmark_dir else discover_benchmark_dirs(root)
    taxonomy, taxonomy_meta = load_intervention_taxonomy(taxonomy_path, repo_root=root)
    dataset_reports = [
        validate_gold_outputs_for_dataset(path if path.is_absolute() else root / path, repo_root=root, taxonomy=taxonomy)
        for path in dataset_dirs
    ]
    issues = [issue for report in dataset_reports for issue in report["issues"]]
    for issue in issues:
        issue.update(_triage_metadata(issue))
    manual_queue = _manual_review_queue(issues)
    by_intervention = _group_by_intervention(issues)
    summary = {
        "dataset_count": len(dataset_reports),
        "issue_count": len(issues),
        "blockers": sum(1 for issue in issues if issue["severity"] == "blocker"),
        "warnings": sum(1 for issue in issues if issue["severity"] == "warning"),
        "informational": sum(1 for issue in issues if issue["severity"] == "informational"),
        "manual_review_queue_count": len(manual_queue),
        "pilot_blocker_count": sum(1 for issue in issues if issue.get("pilot_blocker")),
        "main_benchmark_blocker_count": sum(1 for issue in issues if issue.get("main_benchmark_blocker")),
        "answer_changing_without_gold_change_count": sum(
            1 for issue in issues if issue["issue_type"] == "answer_changing_without_gold_change"
        ),
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static gold-output validation only; no model, provider, or benchmark run is invoked. "
            "Do not auto-fix gold answers from this report."
        ),
        "taxonomy": taxonomy_meta,
        "summary": summary,
        "datasets": dataset_reports,
        "issues": sorted(issues, key=lambda row: (row["severity"], row["dataset"], row["issue_id"])),
        "warnings_by_intervention_type": by_intervention,
        "manual_review_queue": manual_queue,
        "verdicts": {
            "auto_fix_forbidden": True,
            "claims_supported": False,
            "fabricate_gold_answers_forbidden": True,
        },
    }
    md = gold_output_validation_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="gold_output_validation",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    csv_path = out / "gold_output_manual_review_queue.csv"
    _write_manual_queue_csv(csv_path, manual_queue)
    payload["report_paths"] = {
        "markdown": str(md_path),
        "json": str(json_path),
        "manual_review_csv": str(csv_path),
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_gold_outputs_for_dataset(
    dataset_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    taxonomy: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    path = Path(dataset_dir)
    if not path.is_absolute():
        path = root / path
    taxonomy = taxonomy or load_intervention_taxonomy(repo_root=root)[0]
    base_tasks = _read_jsonl(path / "base_tasks.jsonl")
    instances = _read_jsonl(path / "instances.jsonl")
    rows = instances or [{"instance_id": _task_id(task), "condition": "base_task", "base_task": task} for task in base_tasks]
    issues: list[dict[str, Any]] = []

    for row in rows:
        task = _task_from_row(row)
        entity_id = _instance_id(row) or _task_id(task) or "unknown"
        expected = _expected_output(task)
        if expected is _MISSING:
            issues.append(_issue(path, root, "blocker", "missing_gold_output", entity_id, "Expected output/gold answer is missing."))
            continue
        if _is_placeholder(expected):
            issues.append(_issue(path, root, "blocker", "placeholder_gold_output", entity_id, "Gold output is empty or placeholder text."))
        if not _expected_type_matches(task, expected):
            issues.append(_issue(path, root, "warning", "expected_output_type_mismatch", entity_id, "Expected output type does not match task metadata."))
        if _leaks_hidden_intervention_metadata(expected):
            issues.append(_issue(path, root, "blocker", "hidden_intervention_metadata_leak", entity_id, "Gold output appears to include hidden intervention metadata."))

    _check_pairs(path, root, rows, taxonomy, issues)
    _check_reused_gold_outputs(path, root, rows, issues)
    blockers = sum(1 for issue in issues if issue["severity"] == "blocker")
    return {
        "dataset": _rel(path, root),
        "task_count": len(base_tasks),
        "instance_count": len(instances),
        "issue_count": len(issues),
        "blockers": blockers,
        "warnings": sum(1 for issue in issues if issue["severity"] == "warning"),
        "passed": blockers == 0,
        "issues": issues,
    }


def gold_output_validation_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Gold Output Validation",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        "**Do not auto-fix** gold answers from this report. Ambiguous cases require manual reviewer judgment.",
        "",
        section_markdown(
            "Summary",
            [
                f"- Datasets scanned: {summary['dataset_count']}",
                f"- Issues: {summary['issue_count']}",
                f"- Blockers: {summary['blockers']}",
                f"- Warnings: {summary['warnings']}",
                f"- Manual-review queue: {summary.get('manual_review_queue_count', 0)}",
                f"- Pilot blockers: {summary.get('pilot_blocker_count', 0)}",
                f"- Main-benchmark blockers: {summary.get('main_benchmark_blocker_count', 0)}",
                f"- Answer-changing without gold change: {summary.get('answer_changing_without_gold_change_count', 0)}",
            ],
        ),
        "## Warnings by intervention type",
        "",
    ]
    grouped = payload.get("warnings_by_intervention_type") or {}
    if not grouped:
        lines.append("- (none)")
    else:
        for itype, rows in sorted(grouped.items()):
            lines.append(f"- `{itype}`: {len(rows)} issue(s)")
    lines.extend(["", "## Manual review queue (top 25)", ""])
    queue = payload.get("manual_review_queue") or []
    if not queue:
        lines.append("- (none)")
    else:
        for row in queue[:25]:
            lines.append(
                f"- `{row['severity']}` `{row['intervention_type']}` `{row['entity_id']}` "
                f"pilot={row['pilot_blocker']} main={row['main_benchmark_blocker']}: {row['suggested_reviewer_check']}"
            )
    lines.extend(["", "## Issues", ""])
    if not payload["issues"]:
        lines.append("- (none)")
    for issue in payload["issues"][:50]:
        lines.append(
            f"- `{issue['severity']}` `{issue['dataset']}` `{issue['entity_id']}` "
            f"`{issue['issue_type']}`: {issue['message']}"
        )
    if len(payload["issues"]) > 50:
        lines.append(f"- … and {len(payload['issues']) - 50} more (see JSON).")
    lines.append("")
    return "\n".join(lines)


def _check_pairs(
    path: Path,
    root: Path,
    rows: list[dict[str, Any]],
    taxonomy: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    pairs: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        base_id = _base_task_id(row)
        pairs[base_id][_condition(row)].append(row)
    for base_id, grouped in pairs.items():
        clean_items = grouped.get("clean") or []
        intervention_items = grouped.get("intervention") or []
        if not clean_items:
            continue
        clean_expected = _expected_output(_task_from_row(clean_items[0]))
        for intervention in intervention_items:
            intervention_expected = _expected_output(_task_from_row(intervention))
            intervention_obj = intervention.get("intervention") if isinstance(intervention.get("intervention"), dict) else {}
            intervention_type = _intervention_type(intervention_obj)
            policy = taxonomy.get(intervention_type, {})
            expected_change = str(
                intervention_obj.get("expected_final_answer_change")
                or (intervention.get("metadata") or {}).get("expected_final_answer_change")
                or policy.get("answer_preservation")
                or "depends"
            ).lower()
            entity_id = _instance_id(intervention) or base_id
            if expected_change in ANSWER_PRESERVING and not _same_expected(clean_expected, intervention_expected):
                issues.append(
                    _issue(
                        path,
                        root,
                        "blocker",
                        "answer_preserving_expected_answer_changed",
                        entity_id,
                        "Answer-preserving intervention changes expected output.",
                        intervention_type=intervention_type,
                    )
                )
            if expected_change in ANSWER_CHANGING and not _has_answer_change_rationale(intervention_obj):
                issues.append(
                    _issue(
                        path,
                        root,
                        "warning",
                        "answer_changing_without_rationale",
                        entity_id,
                        "Answer-changing intervention lacks rationale/scoring notes.",
                        intervention_type=intervention_type,
                    )
                )
            if _same_expected(clean_expected, intervention_expected) and expected_change in ANSWER_CHANGING:
                issues.append(
                    _issue(
                        path,
                        root,
                        "warning",
                        "answer_changing_without_gold_change",
                        entity_id,
                        "Intervention is marked answer-changing but expected output did not change.",
                        intervention_type=intervention_type,
                    )
                )


def _check_reused_gold_outputs(path: Path, root: Path, rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    by_expected: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        expected = _expected_output(_task_from_row(row))
        if expected is not _MISSING and not _is_placeholder(expected):
            by_expected[_stable_json(expected)].append(row)
    for expected_key, matching in by_expected.items():
        if len(matching) < 2:
            continue
        domains = {_domain(_task_from_row(row)) for row in matching}
        task_ids = {_base_task_id(row) for row in matching}
        if len(domains) > 1 and len(task_ids) > 1:
            entity = ",".join(sorted(task_ids)[:4])
            issues.append(
                _issue(
                    path,
                    root,
                    "warning",
                    "gold_output_reused_across_incompatible_tasks",
                    entity,
                    f"Identical expected output reused across unrelated domains for hash {hashlib.sha1(expected_key.encode('utf-8')).hexdigest()[:8]}.",
                )
            )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


class _Missing:
    pass


_MISSING = _Missing()


def _expected_output(task: dict[str, Any]) -> Any:
    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    for container in (goal, task):
        for key in ("expected_final_answer", "expected_output", "gold_answer", "gold_label", "answer"):
            if key in container:
                return container[key]
    return _MISSING


def _expected_type_matches(task: dict[str, Any], expected: Any) -> bool:
    expected_type = str(
        task.get("expected_output_type")
        or task.get("answer_type")
        or (task.get("goal") if isinstance(task.get("goal"), dict) else {}).get("expected_output_type")
        or ""
    ).lower()
    if not expected_type:
        return True
    if expected_type in {"string", "str", "text", "final_answer"}:
        return isinstance(expected, str)
    if expected_type in {"number", "numeric", "float", "int"}:
        return isinstance(expected, int | float) and not isinstance(expected, bool)
    if expected_type in {"object", "dict", "json"}:
        return isinstance(expected, dict)
    if expected_type in {"list", "array"}:
        return isinstance(expected, list)
    if expected_type in {"boolean", "bool"}:
        return isinstance(expected, bool)
    return True


def _is_placeholder(value: Any) -> bool:
    if value is _MISSING or value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in PLACEHOLDER_VALUES or "todo" in value.lower() or "tbd" in value.lower()
    if isinstance(value, list):
        return not value or any(_is_placeholder(item) for item in value)
    if isinstance(value, dict):
        return not value or any(_is_placeholder(item) for item in value.values())
    return False


def _leaks_hidden_intervention_metadata(value: Any) -> bool:
    text = _stable_json(value).lower()
    return any(marker in text for marker in ("intervention_id", "expected_final_answer_change", "changed_factor", "target_factor", "designed_failure_mode"))


def _has_answer_change_rationale(intervention: dict[str, Any]) -> bool:
    text = json.dumps(intervention, sort_keys=True, default=str).lower()
    return any(marker in text for marker in ("rationale", "scoring_notes", "ground_truth_policy", "answer_change_reason", "expected_behavior"))


def _same_expected(left: Any, right: Any) -> bool:
    return _stable_json(left) == _stable_json(right)


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _task_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("base_task") if isinstance(row.get("base_task"), dict) else row


def _condition(row: dict[str, Any]) -> str:
    return str(row.get("condition") or ("intervention" if row.get("intervention") else "clean"))


def _base_task_id(row: dict[str, Any]) -> str:
    if row.get("base_task_id"):
        return str(row["base_task_id"])
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    if intervention.get("base_task_id"):
        return str(intervention["base_task_id"])
    task = _task_from_row(row)
    if _task_id(task):
        return str(_task_id(task))
    instance_id = _instance_id(row)
    return instance_id.split(".", 1)[0] if instance_id and "." in instance_id else instance_id or "unknown"


def _task_id(task: dict[str, Any]) -> str | None:
    value = task.get("task_id") or task.get("id")
    return str(value) if value else None


def _instance_id(row: dict[str, Any]) -> str | None:
    value = row.get("instance_id") or row.get("id")
    return str(value) if value else None


def _domain(task: dict[str, Any]) -> str:
    return str(task.get("domain") or task.get("category") or "unknown")


def _intervention_type(intervention: dict[str, Any]) -> str:
    return str(intervention.get("family") or intervention.get("type") or intervention.get("intervention_type") or "unknown")


def _issue(
    path: Path,
    root: Path,
    severity: str,
    issue_type: str,
    entity_id: str,
    message: str,
    *,
    intervention_type: str = "unknown",
) -> dict[str, Any]:
    dataset = _rel(path, root)
    stable = hashlib.sha1(f"{dataset}|{issue_type}|{entity_id}|{message}".encode()).hexdigest()[:12]
    row = {
        "issue_id": f"gold_{stable}",
        "severity": severity,
        "issue_type": issue_type,
        "dataset": dataset,
        "entity_id": entity_id,
        "intervention_type": intervention_type,
        "message": message,
        "recommended_fix": _fix(issue_type),
        "do_not_auto_fix": True,
    }
    row.update(_triage_metadata(row))
    return row


def _triage_metadata(issue: dict[str, Any]) -> dict[str, Any]:
    issue_type = str(issue.get("issue_type") or "")
    severity = str(issue.get("severity") or "informational")
    pilot_types = {
        "missing_gold_output",
        "placeholder_gold_output",
        "hidden_intervention_metadata_leak",
        "answer_preserving_expected_answer_changed",
    }
    main_types = {
        "answer_changing_without_rationale",
        "answer_changing_without_gold_change",
        "gold_output_reused_across_incompatible_tasks",
        "expected_output_type_mismatch",
    }
    pilot_blocker = severity == "blocker" or issue_type in pilot_types
    main_blocker = pilot_blocker or issue_type in main_types or severity in {"blocker", "warning"}
    return {
        "pilot_blocker": pilot_blocker,
        "main_benchmark_blocker": main_blocker,
        "suggested_reviewer_check": _reviewer_check(issue_type),
        "required_action": "manual_review" if issue_type in main_types or severity == "blocker" else "optional_review",
    }


def _reviewer_check(issue_type: str) -> str:
    checks = {
        "answer_changing_without_gold_change": "Confirm whether gold should change; document rationale before editing.",
        "answer_preserving_expected_answer_changed": "Restore clean gold or reclassify intervention as answer-changing.",
        "answer_changing_without_rationale": "Add explicit answer-change rationale; do not auto-edit gold.",
        "placeholder_gold_output": "Replace placeholder manually; do not batch auto-fill.",
        "missing_gold_output": "Author gold with domain expert review.",
        "hidden_intervention_metadata_leak": "Remove leakage from expected answer text.",
        "gold_output_reused_across_incompatible_tasks": "Verify tasks are truly equivalent before reusing gold.",
        "expected_output_type_mismatch": "Align expected_output_type with gold structure.",
    }
    return checks.get(issue_type, "Expert review of gold-output policy.")


def _manual_review_queue(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = [
        {
            "issue_id": issue["issue_id"],
            "severity": issue["severity"],
            "issue_type": issue["issue_type"],
            "dataset": issue["dataset"],
            "entity_id": issue["entity_id"],
            "intervention_type": issue.get("intervention_type", "unknown"),
            "pilot_blocker": issue.get("pilot_blocker", False),
            "main_benchmark_blocker": issue.get("main_benchmark_blocker", False),
            "message": issue["message"],
            "suggested_reviewer_check": issue.get("suggested_reviewer_check", ""),
            "do_not_auto_fix": True,
            "required_action": issue.get("required_action", "manual_review"),
        }
        for issue in issues
        if issue.get("severity") in {"blocker", "warning"}
        or issue.get("issue_type") == "answer_changing_without_gold_change"
    ]
    queue.sort(
        key=lambda row: (
            0 if row["severity"] == "blocker" else 1,
            0 if row["main_benchmark_blocker"] else 1,
            row["intervention_type"],
            row["entity_id"],
        )
    )
    return queue


def _group_by_intervention(issues: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        if issue.get("severity") not in {"warning", "blocker"}:
            continue
        grouped[str(issue.get("intervention_type") or "unknown")].append(issue)
    return dict(sorted(grouped.items()))


def _write_manual_queue_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv

    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fix(issue_type: str) -> str:
    fixes = {
        "missing_gold_output": "Add expected_final_answer, expected_output, or gold_answer metadata.",
        "placeholder_gold_output": "Replace placeholder gold output with a real expected answer or remove the task.",
        "answer_preserving_expected_answer_changed": "Restore the clean answer or mark the intervention answer-changing with rationale.",
        "answer_changing_without_rationale": "Add explicit answer-change rationale and scoring notes.",
        "hidden_intervention_metadata_leak": "Remove hidden intervention metadata from the expected answer.",
    }
    return fixes.get(issue_type, "Review the gold-output metadata.")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
