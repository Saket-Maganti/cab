"""Static clean↔intervention pair-link consistency validator.

Catches real dataset bugs without running models or providers:

- ``orphaned_intervention`` — intervention instance with no matching clean instance.
- ``orphaned_clean`` — clean instance without any intervention variant.
- ``mismatched_base_task_id`` — intervention's declared ``base_task_id`` does not
  match the prefix of its ``instance_id``.
- ``pair_crosses_task_family`` — clean and intervention have different
  ``task_family`` (a likely benchmark bug).
- ``pair_crosses_protected_split`` — clean is in one split (e.g., heldout) and
  intervention is in another (e.g., pilot). This is real leakage potential
  unless the splits belong to the same declared subset family.
- ``duplicate_intervention_variants`` — two interventions claim the same
  intervention family for the same base task.
- ``intervention_missing_clean_base_task`` — intervention references a
  ``base_task_id`` that does not appear in ``base_tasks.jsonl``.

This module is read-only. It never modifies the dataset, run metadata,
results, or any claim/paper artifact.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.benchmark_quality import discover_benchmark_dirs
from causal_agent_bench.safety.common import section_markdown, write_dual_report

MAIN_OR_HELDOUT_SPLITS = frozenset({"main", "heldout", "heldout_templates", "test"})
PILOT_SPLITS = frozenset({"pilot", "pilot_20", "pilot_100", "provider_pilot", "dev", "development"})
DEFAULT_SUBSET_FAMILIES: tuple[frozenset[str], ...] = (
    frozenset({"pilot", "pilot_20", "pilot_100", "dev", "development"}),
)


def build_pair_link_report(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    output_dir: str | Path = "reports/pair_link_validator",
) -> dict[str, Any]:
    """Walk each benchmark dir and validate clean↔intervention pair linkage."""

    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    dataset_dirs = [Path(benchmark_dir)] if benchmark_dir else discover_benchmark_dirs(root)
    datasets = [validate_dataset_pair_links(path, repo_root=root) for path in dataset_dirs]
    issues = [issue for dataset in datasets for issue in dataset["issues"]]
    blockers = sum(1 for issue in issues if issue["severity"] == "blocker")
    warnings = sum(1 for issue in issues if issue["severity"] == "warning")
    root_causes = _cluster_pair_issues(issues)
    classification_counts: dict[str, int] = {}
    for row in root_causes:
        classification_counts[row["cluster_classification"]] = (
            classification_counts.get(row["cluster_classification"], 0) + 1
        )
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static clean↔intervention pair-link consistency check only. "
            "No agents, providers, models, or benchmark runs are invoked."
        ),
        "summary": {
            "dataset_count": len(datasets),
            "raw_issue_count": len(issues),
            "cluster_count": len(root_causes),
            "suppressed_symptom_count": max(0, len(issues) - len(root_causes)),
            "blockers": blockers,
            "warnings": warnings,
            "informational": sum(1 for issue in issues if issue["severity"] == "informational"),
            "classification_counts": classification_counts,
            "datasets_with_issues": sum(1 for d in datasets if d["issue_count"] > 0),
        },
        "verdicts": {
            "pair_link_consistent": blockers == 0,
            "ready_for_provider_pilot": blockers == 0,
            "needs_review": bool(blockers or warnings),
        },
        "datasets": datasets,
        "root_causes": root_causes,
        "root_cause_summary": root_causes,
        "top_clusters": root_causes[:20],
        "classification_counts": classification_counts,
        "issues": issues,
        "raw_finding_count": len(issues),
    }
    md = pair_link_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="pair_link_validation",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_dataset_pair_links(dataset_dir: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    path = Path(dataset_dir)
    if not path.is_absolute():
        path = root / path
    rel = _rel(path, root)
    base_tasks = _read_jsonl(path / "base_tasks.jsonl")
    instances = _read_jsonl(path / "instances.jsonl")
    splits = _load_splits(path)
    subset_families = _load_subset_families(path)
    base_task_ids = {str(task.get("task_id") or task.get("id") or "") for task in base_tasks}
    base_task_ids.discard("")

    pairs: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"clean": [], "intervention": []})
    for row in instances:
        base_id = _base_task_id(row)
        if not base_id:
            continue
        bucket = "clean" if _condition(row) == "clean" else "intervention"
        pairs[base_id][bucket].append(row)

    issues: list[dict[str, Any]] = []

    # 1. Orphaned interventions / cleans
    for base_id, buckets in pairs.items():
        cleans = buckets["clean"]
        interventions = buckets["intervention"]
        if interventions and not cleans:
            for inter in interventions:
                issues.append(
                    _issue(
                        rel,
                        "blocker",
                        "orphaned_intervention",
                        _instance_id(inter),
                        f"Intervention `{_instance_id(inter)}` has no matching clean baseline for base_task `{base_id}`.",
                        task_id=base_id,
                    )
                )
        elif cleans and not interventions:
            issues.append(
                _issue(
                    rel,
                    "warning",
                    "orphaned_clean",
                    _instance_id(cleans[0]),
                    f"Clean instance `{_instance_id(cleans[0])}` has no intervention variants for base_task `{base_id}`.",
                    task_id=base_id,
                )
            )

    # 2. Mismatched base_task_id (declared base_task_id does not match instance_id prefix)
    for row in instances:
        instance_id = _instance_id(row) or ""
        declared = _declared_base_task_id(row)
        if not declared:
            continue
        if not instance_id.startswith(declared):
            issues.append(
                _issue(
                    rel,
                    "blocker",
                    "mismatched_base_task_id",
                    instance_id,
                    f"instance_id `{instance_id}` does not start with declared base_task_id `{declared}`.",
                    task_id=declared,
                )
            )

    # 3. Intervention references missing base task
    for row in instances:
        condition = _condition(row)
        if condition == "clean":
            continue
        declared = _declared_base_task_id(row) or _base_task_id(row)
        if declared and base_task_ids and declared not in base_task_ids:
            issues.append(
                _issue(
                    rel,
                    "blocker",
                    "intervention_missing_clean_base_task",
                    _instance_id(row),
                    f"Intervention `{_instance_id(row)}` references base_task_id `{declared}` which is not in base_tasks.jsonl.",
                    task_id=declared,
                )
            )

    # 4. Pair crosses task_family
    for base_id, buckets in pairs.items():
        cleans = buckets["clean"]
        interventions = buckets["intervention"]
        if not cleans or not interventions:
            continue
        clean_family = _task_family(cleans[0])
        for inter in interventions:
            if _task_family(inter) != clean_family:
                issues.append(
                    _issue(
                        rel,
                        "blocker",
                        "pair_crosses_task_family",
                        _instance_id(inter),
                        f"Intervention `{_instance_id(inter)}` task_family `{_task_family(inter)}` differs from clean baseline task_family `{clean_family}`.",
                        task_id=base_id,
                    )
                )

    # 5. Pair crosses protected split boundary
    if splits:
        instance_to_splits = _instance_to_splits(splits)
        for base_id, buckets in pairs.items():
            cleans = buckets["clean"]
            interventions = buckets["intervention"]
            if not cleans or not interventions:
                continue
            clean_splits = instance_to_splits.get(_instance_id(cleans[0]) or "", set())
            for inter in interventions:
                inter_splits = instance_to_splits.get(_instance_id(inter) or "", set())
                if not clean_splits or not inter_splits:
                    continue
                # If clean and intervention live in different splits AND those splits are not
                # in the same declared subset family, it's a protected-split crossing.
                if clean_splits == inter_splits:
                    continue
                combined = sorted(clean_splits | inter_splits)
                if _splits_in_one_subset_family(combined, subset_families):
                    continue
                # If any side is in MAIN_OR_HELDOUT_SPLITS and the other is not in the same family,
                # the pair crosses a protected boundary.
                if _crosses_protected(combined):
                    issues.append(
                        _issue(
                            rel,
                            "blocker",
                            "pair_crosses_protected_split",
                            _instance_id(inter),
                            (
                                f"Clean/intervention pair `{base_id}` spans protected split boundary: "
                                f"clean in {sorted(clean_splits)}, intervention in {sorted(inter_splits)}."
                            ),
                            task_id=base_id,
                        )
                    )

    # 6. Duplicate intervention variants
    for base_id, buckets in pairs.items():
        seen_keys: dict[tuple[str, str], list[str]] = defaultdict(list)
        for inter in buckets["intervention"]:
            family = _intervention_family(inter)
            iid = _instance_id(inter) or ""
            seen_keys[(family, base_id)].append(iid)
        for (family, base), ids in seen_keys.items():
            if len(ids) > 1:
                issues.append(
                    _issue(
                        rel,
                        "warning",
                        "duplicate_intervention_variants",
                        ",".join(ids[:4]),
                        f"Base task `{base}` has multiple intervention instances for family `{family}`: {sorted(ids)}.",
                        task_id=base,
                    )
                )

    return {
        "dataset": rel,
        "task_count": len(base_tasks),
        "instance_count": len(instances),
        "pair_count": len(pairs),
        "issue_count": len(issues),
        "blockers": sum(1 for issue in issues if issue["severity"] == "blocker"),
        "warnings": sum(1 for issue in issues if issue["severity"] == "warning"),
        "issues": issues,
    }


def pair_link_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Pair-Link Consistency Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Datasets scanned: {summary['dataset_count']}",
                f"- Raw issues: {summary['raw_issue_count']}",
                f"- Root-cause clusters: {summary['cluster_count']}",
                f"- Suppressed/deduplicated symptoms: {summary['suppressed_symptom_count']}",
                f"- Blockers: {summary['blockers']}",
                f"- Warnings: {summary['warnings']}",
                f"- Informational: {summary['informational']}",
                f"- Datasets with issues: {summary['datasets_with_issues']}",
            ],
        ),
        section_markdown(
            "Verdicts",
            [
                f"- Pair-link consistent: `{payload['verdicts']['pair_link_consistent']}`",
                f"- Ready for provider pilot: `{payload['verdicts']['ready_for_provider_pilot']}`",
                f"- Needs review: `{payload['verdicts']['needs_review']}`",
            ],
        ),
        "## Top Root Causes",
        "",
    ]
    top = payload.get("top_clusters") or []
    if not top:
        lines.append("- (none)")
    for row in top[:15]:
        lines.append(
            f"- rank {row['rank']} `{row['root_cause_id']}` [{row['severity']}] "
            f"{row['root_cause_title']} ({row['symptom_count']} symptoms)"
        )
    lines.extend(["", "## Datasets", ""])
    for dataset in payload["datasets"]:
        lines.append(
            f"### `{dataset['dataset']}`  tasks={dataset['task_count']} instances={dataset['instance_count']} "
            f"pairs={dataset['pair_count']} blockers={dataset['blockers']} warnings={dataset['warnings']}"
        )
        if not dataset["issues"]:
            lines.append("- (no issues)")
            lines.append("")
            continue
        for issue in dataset["issues"][:30]:
            lines.append(f"- `{issue['severity']}` `{issue['issue_type']}` `{issue['entity_id']}`: {issue['message']}")
        if len(dataset["issues"]) > 30:
            lines.append(f"- ... {len(dataset['issues']) - 30} more (see JSON)")
        lines.append("")
    return "\n".join(lines)


def _cluster_pair_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not issues:
        return []
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    severity_rank = {"blocker": 0, "warning": 1, "informational": 2, "needs_review": 3}
    for issue in issues:
        key = (
            str(issue.get("issue_type", "unknown")),
            str(issue.get("dataset", "")),
            str(issue.get("severity", "informational")),
        )
        groups[key].append(issue)
    rows: list[dict[str, Any]] = []
    for (issue_type, dataset, severity), members in groups.items():
        rows.append(
            {
                "root_cause_id": f"pair_root_{issue_type}__{hashlib.sha1(dataset.encode()).hexdigest()[:6]}__{severity}",
                "root_cause_title": f"{issue_type} in {dataset or '(root)'}",
                "cluster_classification": issue_type,
                "severity": severity,
                "dataset": dataset,
                "symptom_count": len(members),
                "representative_messages": [str(m.get("message")) for m in members[:3] if m.get("message")],
                "readiness_gate": (
                    "must_fix_before_provider_pilot" if severity == "blocker"
                    else "must_fix_before_main_benchmark" if severity == "warning"
                    else "nice_to_have"
                ),
            }
        )
    rows.sort(key=lambda r: (severity_rank.get(r["severity"], 99), -r["symptom_count"], r["root_cause_id"]))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


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


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _load_splits(path: Path) -> dict[str, dict[str, set[str]]]:
    payload = _read_json(path / "splits.json") or {}
    raw = payload.get("splits") if isinstance(payload.get("splits"), dict) else payload
    out: dict[str, dict[str, set[str]]] = {}
    if not isinstance(raw, dict):
        return out
    for name, value in raw.items():
        if not isinstance(value, dict):
            continue
        out[str(name)] = {
            "task_ids": set(map(str, value.get("base_task_ids") or value.get("task_ids") or [])),
            "instance_ids": set(map(str, value.get("instance_ids") or [])),
        }
    return out


def _load_subset_families(path: Path) -> tuple[frozenset[str], ...]:
    payload = _read_json(path / "splits.json") or {}
    raw = payload.get("subset_families") if isinstance(payload, dict) else None
    if isinstance(raw, list):
        families = [frozenset(str(name) for name in fam if name) for fam in raw if isinstance(fam, list)]
        if families:
            return tuple(families)
    return DEFAULT_SUBSET_FAMILIES


def _instance_to_splits(splits: dict[str, dict[str, set[str]]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for split, ids in splits.items():
        for iid in ids.get("instance_ids", set()):
            out[str(iid)].add(split)
    return out


def _splits_in_one_subset_family(splits: list[str], families: tuple[frozenset[str], ...]) -> bool:
    names = set(splits)
    return any(names.issubset(family) for family in families)


def _crosses_protected(splits: list[str]) -> bool:
    names = set(splits)
    return bool(names & MAIN_OR_HELDOUT_SPLITS) and bool(names - MAIN_OR_HELDOUT_SPLITS)


def _instance_id(row: dict[str, Any]) -> str | None:
    value = row.get("instance_id") or row.get("id")
    return str(value) if value else None


def _base_task_id(row: dict[str, Any]) -> str:
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    task = row.get("base_task") if isinstance(row.get("base_task"), dict) else row
    value = intervention.get("base_task_id") or row.get("base_task_id") or task.get("task_id")
    if value:
        return str(value)
    iid = _instance_id(row) or ""
    return iid.split(".", 1)[0] if "." in iid else iid


def _declared_base_task_id(row: dict[str, Any]) -> str | None:
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    value = intervention.get("base_task_id") or row.get("base_task_id")
    return str(value) if value else None


def _condition(row: dict[str, Any]) -> str:
    value = row.get("condition")
    if value:
        return str(value)
    return "intervention" if isinstance(row.get("intervention"), dict) else "clean"


def _task_family(row: dict[str, Any]) -> str:
    task = row.get("base_task") if isinstance(row.get("base_task"), dict) else row
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    return str(
        task.get("task_family")
        or task.get("family")
        or task.get("domain")
        or task.get("category")
        or intervention.get("task_family")
        or "unknown"
    )


def _intervention_family(row: dict[str, Any]) -> str:
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    return str(
        intervention.get("family")
        or intervention.get("intervention_type")
        or row.get("intervention_type")
        or row.get("condition")
        or "unknown"
    )


def _issue(
    dataset: str,
    severity: str,
    issue_type: str,
    entity_id: str | None,
    message: str,
    *,
    task_id: str | None = None,
) -> dict[str, Any]:
    stable = hashlib.sha1(f"{dataset}|{issue_type}|{entity_id}|{message}".encode()).hexdigest()[:12]
    return {
        "issue_id": f"pair_{stable}",
        "severity": severity,
        "issue_type": issue_type,
        "dataset": dataset,
        "entity_id": entity_id or "",
        "task_id": task_id,
        "message": message,
    }


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
