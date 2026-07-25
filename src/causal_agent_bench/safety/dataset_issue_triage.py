"""Aggregate static dataset issues into actionable no-run repair tasks."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.benchmark_quality import (
    audit_benchmark_dataset,
    discover_benchmark_dirs,
)
from causal_agent_bench.safety.common import section_markdown, write_dual_report
from causal_agent_bench.safety.intervention_isolation import audit_intervention_isolation_instances

GROUPS = (
    "must_fix_before_provider_pilot",
    "must_fix_before_main_benchmark",
    "must_fix_before_public_release",
    "manual_review_needed",
    "nice_to_have",
)


def build_dataset_issue_triage(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    output_dir: str | Path = "reports/dataset_triage",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    dataset_dirs = [Path(benchmark_dir)] if benchmark_dir else discover_benchmark_dirs(root)
    items: list[dict[str, Any]] = []
    for dataset in dataset_dirs:
        dataset_path = dataset if dataset.is_absolute() else root / dataset
        quality = audit_benchmark_dataset(dataset_path, repo_root=root)
        items.extend(_quality_items(quality))
        instances_path = dataset_path / "instances.jsonl"
        if instances_path.exists():
            isolation = audit_intervention_isolation_instances(instances_path, repo_root=root)
            items.extend(_isolation_items(isolation, quality["dataset_relpath"]))
    items = _dedupe_items(items)
    items = sorted(items, key=lambda row: (_group_rank(row["group"]), _severity_rank(row["severity"]), row["issue_id"]))
    grouped = {group: [item for item in items if item["group"] == group] for group in GROUPS}
    family_groups = _family_groups(items)
    leakage_root_causes = _load_static_leakage_clusters(root, out)
    leakage_repair_plan = _load_leakage_repair_plan(root, out)
    root_causes = _load_repair_root_causes(root, out) or _root_cause_groups(items)
    actionable_leakage_root_causes = [row for row in leakage_root_causes if not _is_false_positive_root(row)]
    combined_root_causes = _merge_root_causes(root_causes, actionable_leakage_root_causes)
    leakage_families = _leakage_family_counts(leakage_root_causes)
    severity_counts: dict[str, int] = {}
    for item in items:
        severity_counts[item.get("severity", "informational")] = severity_counts.get(item.get("severity", "informational"), 0) + 1
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static triage aggregation only; no benchmark run or provider call.",
        "summary": {
            "total_issues": len(items),
            "blockers": severity_counts.get("blocker", 0),
            "warnings": severity_counts.get("warning", 0),
            "informational": severity_counts.get("informational", 0),
            "issue_family_count": len(family_groups),
            "root_cause_count": len(root_causes) if isinstance(root_causes, list) else 0,
        },
        "verdicts": {
            "triage_passed": severity_counts.get("blocker", 0) == 0,
            "needs_review": severity_counts.get("blocker", 0) > 0 or severity_counts.get("warning", 0) > 0,
        },
        "total_issues": len(items),
        "groups": grouped,
        "issue_families": family_groups,
        "leakage_families": leakage_families,
        "blocker_counts_by_leakage_family": {
            family: count["blockers"] for family, count in leakage_families.items()
        },
        "blocker_counts_by_family": {
            family: sum(1 for item in rows if item["severity"] == "blocker")
            for family, rows in family_groups.items()
        },
        "root_cause_groups": combined_root_causes,
        "leakage_root_causes": leakage_root_causes,
        "leakage_repair_plan_summary": leakage_repair_plan.get("summary", {}),
        "top_leakage_repairs": leakage_repair_plan.get("top_10_must_fix_before_provider_pilot", [])[:10],
        "leakage_patch_manifest_status": leakage_repair_plan.get("patch_manifest_paths", {}),
        "top_leakage_root_causes": actionable_leakage_root_causes[:20],
        "top_true_leakage_blockers": [
            row for row in leakage_root_causes if row.get("leakage_risk") == "blocker"
        ][:20],
        "top_false_positive_leakage_candidates": [
            row for row in leakage_root_causes if _is_false_positive_root(row)
        ][:20],
        "top_needs_manual_review_leakage": [
            row for row in leakage_root_causes if row.get("leakage_risk") == "needs_review"
        ][:20],
        "provider_pilot_leakage_blockers": [
            row
            for row in actionable_leakage_root_causes
            if row.get("readiness_gate") == "must_fix_before_provider_pilot"
            and row.get("leakage_risk") in {"blocker", "needs_review"}
        ][:10],
        "main_benchmark_leakage_blockers": [
            row
            for row in actionable_leakage_root_causes
            if row.get("readiness_gate") == "must_fix_before_main_benchmark"
            and row.get("leakage_risk") in {"blocker", "warning", "needs_review"}
        ][:10],
        "top_provider_pilot_blockers": [
            row
            for row in combined_root_causes
            if _root_gate(row) == "must_fix_before_provider_pilot"
            and not _is_false_positive_root(row)
        ][:10],
        "top_dataset_fixes": [row for row in combined_root_causes if row.get("suggested_owner") in {None, "dataset"}][:20],
        "manual_review_queue": _manual_review_queue(items),
        "manual_review_leakage_queue": [
            row for row in leakage_root_causes if row.get("leakage_risk") == "needs_review"
        ][:20],
        "manual_review_leakage_repair_queue": leakage_repair_plan.get("manual_review_queue", [])[:20],
        "false_positive_candidates": _false_positive_candidates(items),
        "false_positive_leakage_candidates": [
            row for row in leakage_root_causes if _is_false_positive_root(row)
        ][:50],
        "issues": items,
    }
    md = dataset_issue_triage_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="dataset_issue_triage",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def dataset_issue_triage_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Dataset Issue Triage",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Total triage items: {payload['total_issues']}",
                f"- Root-cause groups: {len(payload['root_cause_groups'])}",
                f"- Blocker counts by family: {payload['blocker_counts_by_family']}",
        f"- Leakage root causes: {len(payload['leakage_root_causes'])}",
        f"- Blocker counts by leakage family: {payload['blocker_counts_by_leakage_family']}",
        f"- Leakage repair plan: {payload.get('leakage_repair_plan_summary', {})}",
            ],
        ),
        "## Top Provider-Pilot Blockers",
        "",
    ]
    if not payload["top_provider_pilot_blockers"]:
        lines.append("- (none)")
    for row in payload["top_provider_pilot_blockers"]:
        lines.append(
            f"- `{row['root_cause_id']}` [{row['severity']}] {row['root_cause_title']} "
            f"({row['symptom_count']} symptoms) -> {_root_fix_text(row)}"
        )
    lines.extend(["", "## Top Leakage Root Causes", ""])
    if not payload["top_leakage_root_causes"]:
        lines.append("- (none)")
    for row in payload["top_leakage_root_causes"][:20]:
        lines.append(
            f"- `{row['root_cause_id']}` [{row.get('leakage_risk') or row['severity']}] "
            f"{row['root_cause_title']} ({row['symptom_count']} symptoms; "
            f"class={row.get('cluster_classification', 'needs_manual_review')}) -> {_root_fix_text(row)}"
        )
    lines.extend(["", "## Provider-Pilot Leakage Blockers", ""])
    if not payload["provider_pilot_leakage_blockers"]:
        lines.append("- (none)")
    for row in payload["provider_pilot_leakage_blockers"]:
        lines.append(f"- `{row['root_cause_id']}` {row['root_cause_title']}")
    lines.extend(["", "## Top Leakage Repair Plan Items", ""])
    if not payload.get("top_leakage_repairs"):
        lines.append("- (none)")
    for row in payload.get("top_leakage_repairs", [])[:10]:
        lines.append(
            f"- `{row.get('cluster_id')}` [{row.get('classification')}/{row.get('leakage_risk')}] "
            f"{row.get('repair_strategy')}"
        )
    lines.extend(["", "## False-Positive Leakage Candidates", ""])
    if not payload.get("false_positive_leakage_candidates"):
        lines.append("- (none)")
    for row in payload.get("false_positive_leakage_candidates", [])[:20]:
        lines.append(
            f"- `{row['root_cause_id']}` {row.get('cluster_classification')} "
            f"({row.get('symptom_count', 1)} symptoms)"
        )
    lines.extend(["", "## Leakage Manual Review Queue", ""])
    if not payload.get("manual_review_leakage_queue"):
        lines.append("- (none)")
    for row in payload.get("manual_review_leakage_queue", [])[:20]:
        lines.append(f"- `{row['root_cause_id']}` {row['root_cause_title']} -> {_root_fix_text(row)}")
    lines.extend(["", "## Manual Review Queue", ""])
    if not payload["manual_review_queue"]:
        lines.append("- (none)")
    for item in payload["manual_review_queue"][:20]:
        lines.append(f"- `{item['issue_id']}` {item['reason']} ({item['issue_family']})")
    lines.append("")
    for group in GROUPS:
        rows = payload["groups"].get(group, [])
        lines.extend([f"## {group}", ""])
        if not rows:
            lines.extend(["- (none)", ""])
            continue
        for item in rows:
            lines.append(
                f"- `{item['issue_id']}` [{item['severity']}] {item['reason']} "
                f"-> {item['suggested_fix']} (`{item['affected_readiness_gate']}`)"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _quality_items(report: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for issue in report["issues"]:
        group, gate = _quality_group(issue["id"], issue["severity"])
        out.append(
            _item(
                source="benchmark_quality",
                raw_id=issue["id"],
                severity=issue["severity"],
                dataset=issue.get("dataset") or report["dataset_relpath"],
                entity_id=_extract_entity(issue["message"]),
                reason=issue["message"],
                suggested_fix=_suggested_fix(issue["id"]),
                group=group,
                gate=gate,
            )
        )
    return out


def _isolation_items(report: dict[str, Any], dataset: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for pair in report["pairs"]:
        if pair["severity"] == "informational" and pair["isolation_status"] in {"isolated", "likely_isolated"}:
            continue
        group = "manual_review_needed"
        gate = "main_benchmark"
        if pair["severity"] == "blocker" or pair["isolation_status"] == "missing_clean_pair":
            group = "must_fix_before_provider_pilot"
            gate = "provider_pilot"
        elif pair["isolation_status"] == "multi_factor_change":
            group = "must_fix_before_main_benchmark"
        out.append(
            _item(
                source="intervention_isolation",
                raw_id=pair["isolation_status"],
                severity=pair["severity"],
                dataset=dataset,
                entity_id=pair["pair_id"],
                reason=pair["explanation"],
                suggested_fix=_isolation_fix(pair),
                group=group,
                gate=gate,
            )
        )
    return out


def _item(
    *,
    source: str,
    raw_id: str,
    severity: str,
    dataset: str,
    entity_id: str | None,
    reason: str,
    suggested_fix: str,
    group: str,
    gate: str,
) -> dict[str, Any]:
    stable = hashlib.sha1(f"{source}|{raw_id}|{dataset}|{entity_id}|{reason}".encode()).hexdigest()[:12]
    return {
        "issue_id": f"triage_{stable}",
        "source": source,
        "raw_issue_id": raw_id,
        "severity": severity,
        "dataset_or_file": dataset,
        "task_instance_or_pair_id": entity_id,
        "reason": reason,
        "suggested_fix": suggested_fix,
        "affected_readiness_gate": gate,
        "group": group,
        "issue_family": _issue_family(source, raw_id, reason, suggested_fix),
    }


def _quality_group(issue_id: str, severity: str) -> tuple[str, str]:
    if severity == "blocker" and issue_id in {
        "duplicate_task_id",
        "duplicate_instance_id",
        "missing_expected_output",
        "missing_tool_specs",
        "missing_clean_pair",
        "invalid_pair_reference",
        "missing_instances",
        "missing_base_tasks",
    }:
        return "must_fix_before_provider_pilot", "provider_pilot"
    if issue_id in {"missing_heldout_split", "missing_split_metadata", "split_leakage_risk", "main_candidate_not_ready"}:
        return "must_fix_before_main_benchmark", "main_benchmark"
    if issue_id in {"high_risk_intervention", "quality_report_warning", "missing_changed_factor"}:
        return "manual_review_needed", "main_benchmark"
    if severity == "warning":
        return "must_fix_before_public_release", "public_release"
    return "nice_to_have", "release_quality"


def _suggested_fix(issue_id: str) -> str:
    fixes = {
        "duplicate_task_id": "Assign unique task IDs and regenerate dependent instances.",
        "duplicate_instance_id": "Assign unique instance IDs before any run planning.",
        "missing_expected_output": "Add expected outputs or gold labels to the affected task.",
        "missing_tool_specs": "Add explicit tool specs or schemas.",
        "missing_clean_pair": "Add a clean pair for the intervention instance.",
        "missing_intervention_pair": "Add an intervention variant or document why it is excluded.",
        "missing_heldout_split": "Add a non-empty heldout/test split.",
        "split_leakage_risk": "Remove overlapping IDs across development and heldout/test splits.",
        "high_risk_intervention": "Queue for manual intervention-isolation review.",
        "quality_report_warning": "Resolve or explicitly document generation quality warnings.",
    }
    return fixes.get(issue_id, "Review and repair the static metadata before advancing readiness gates.")


def _isolation_fix(pair: dict[str, Any]) -> str:
    if pair["isolation_status"] == "multi_factor_change":
        return "Reduce the variant to the intended causal factor or document it as multi-factor and exclude from causal claims."
    if pair["isolation_status"] == "missing_clean_pair":
        return "Add the linked clean instance for this intervention."
    if pair["isolation_status"] == "missing_intervention_pair":
        return "Add an intervention instance or remove the clean-only task from paired analyses."
    return "Manually review field changes and update the intervention whitelist or metadata."


def _extract_entity(message: str) -> str | None:
    tokens = [token.strip("`:,") for token in message.split()]
    for token in tokens:
        if "." in token or "_" in token:
            return token
    return None


def _group_rank(group: str) -> int:
    return GROUPS.index(group) if group in GROUPS else len(GROUPS)


def _severity_rank(severity: str) -> int:
    return {"blocker": 0, "warning": 1, "informational": 2}.get(severity, 3)


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (
            item.get("source"),
            item.get("raw_issue_id"),
            item.get("dataset_or_file"),
            item.get("task_instance_or_pair_id"),
            item.get("reason"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _family_groups(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(item.get("issue_family", "validation"), []).append(item)
    return {key: grouped[key] for key in sorted(grouped)}


def _root_cause_groups(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for item in items:
        key = (
            item.get("issue_family", "validation"),
            item.get("raw_issue_id", "issue"),
            _entity_intervention_type(str(item.get("task_instance_or_pair_id") or "")) or "any",
        )
        grouped.setdefault(key, []).append(item)
    rows = []
    for key, group_items in grouped.items():
        stable = hashlib.sha1("|".join(key).encode("utf-8")).hexdigest()[:12]
        gates = sorted({item["group"] for item in group_items})
        examples = [str(item.get("task_instance_or_pair_id") or item.get("dataset_or_file")) for item in group_items[:5]]
        rows.append(
            {
                "root_cause_id": f"triage_root_{stable}",
                "root_cause_title": " / ".join(part for part in key if part != "any"),
                "severity": "blocker" if any(item["severity"] == "blocker" for item in group_items) else "warning",
                "symptom_count": len(group_items),
                "representative_examples": examples,
                "affected_readiness_gates": gates,
                "recommended_root_fix": _mode([item.get("suggested_fix") for item in group_items]) or "Review grouped dataset issue.",
                "suggested_owner": "dataset",
            }
        )
    return sorted(rows, key=lambda row: (_group_rank(row["affected_readiness_gates"][0]), _severity_rank(row["severity"]), -row["symptom_count"], row["root_cause_id"]))


def _load_repair_root_causes(root: Path, output_dir: Path) -> list[dict[str, Any]]:
    candidates = [
        output_dir / "repair_plan" / "repair_plan.json",
        output_dir.parent / "repair_plan" / "repair_plan.json",
        root / "reports" / "repair_plan" / "repair_plan.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rows = payload.get("root_causes") or payload.get("root_cause_summary") or []
        if isinstance(rows, list):
            return rows
    return []


def _load_static_leakage_clusters(root: Path, output_dir: Path) -> list[dict[str, Any]]:
    candidates = [
        output_dir / "static_leakage" / "static_leakage_report.json",
        output_dir.parent / "static_leakage" / "static_leakage_report.json",
        root / "reports" / "static_leakage" / "static_leakage_report.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rows = payload.get("root_causes") or payload.get("root_cause_summary") or payload.get("top_clusters") or []
        if isinstance(rows, list):
            return [_triage_leakage_root(row) for row in rows if isinstance(row, dict)]
    return []


def _load_leakage_repair_plan(root: Path, output_dir: Path) -> dict[str, Any]:
    candidates = [
        output_dir / "leakage_repair_plan" / "leakage_repair_plan.json",
        output_dir.parent / "leakage_repair_plan" / "leakage_repair_plan.json",
        root / "reports" / "leakage_repair_plan" / "leakage_repair_plan.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _triage_leakage_root(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "root_cause_id": row.get("root_cause_id"),
        "root_cause_title": row.get("root_cause_title") or row.get("finding_type", "leakage"),
        "symptom_count": row.get("symptom_count", 1),
        "severity": row.get("severity", "warning"),
        "affected_readiness_gates": [row.get("readiness_gate", "must_fix_before_main_benchmark")],
        "recommended_root_fix": row.get("recommended_action") or row.get("suggested_fix") or "Review static leakage cluster.",
        "suggested_owner": "dataset",
        "issue_family": _leakage_issue_family(str(row.get("finding_type") or "")),
    }


def _merge_root_causes(primary: list[dict[str, Any]], leakage: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [*primary, *leakage]
    return sorted(
        rows,
        key=lambda row: (
            _group_rank(_root_gate(row)),
            _root_priority(row),
            -int(row.get("symptom_count", 1) or 1),
            str(row.get("root_cause_id") or ""),
        ),
    )


def _root_gate(row: dict[str, Any]) -> str:
    if row.get("readiness_gate"):
        return str(row["readiness_gate"])
    gates = row.get("affected_readiness_gates") or []
    if isinstance(gates, list) and gates:
        return str(gates[0])
    return "must_fix_before_main_benchmark"


def _root_fix_text(row: dict[str, Any]) -> str:
    return str(row.get("recommended_root_fix") or row.get("recommended_action") or row.get("suggested_fix") or "Review grouped issue.")


def _leakage_family_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        family = _leakage_issue_family(str(row.get("finding_type") or "unknown_needs_review"))
        counts.setdefault(family, {"clusters": 0, "blockers": 0, "symptoms": 0})
        counts[family]["clusters"] += 1
        counts[family]["symptoms"] += int(row.get("symptom_count", 1) or 1)
        if row.get("leakage_risk") == "blocker" or row.get("severity") == "blocker":
            counts[family]["blockers"] += 1
    return {key: counts[key] for key in sorted(counts)}


def _is_false_positive_root(row: dict[str, Any]) -> bool:
    return row.get("leakage_risk") == "false_positive_candidate" or row.get("cluster_classification") in {
        "likely_template_reuse",
        "clean_intervention_pair_similarity",
        "task_family_boilerplate",
        "shared_tool_description",
        "shared_system_instruction",
    }


def _root_priority(row: dict[str, Any]) -> int:
    if _is_false_positive_root(row):
        return 9
    if row.get("leakage_risk") == "blocker":
        return 0
    if row.get("leakage_risk") == "needs_review":
        return 1
    return _severity_rank(str(row.get("severity", "warning")))


def _leakage_issue_family(finding_type: str) -> str:
    if finding_type in {"duplicate_task_id", "duplicate_instance_id"}:
        return "duplicate_ids"
    if finding_type in {"clean_intervention_split_leakage", "provider_pilot_overlap"}:
        return "split_leakage"
    if finding_type == "answer_text_leakage":
        return "answer_leakage"
    if finding_type == "near_duplicate_prompt":
        return "near_duplicates"
    if finding_type == "hidden_metadata_visible":
        return "hidden_metadata_exposure"
    if "leak" in finding_type:
        return "leakage"
    return "unknown_needs_review"


def _manual_review_queue(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = [
        item
        for item in items
        if item["group"] == "manual_review_needed"
        or (item["severity"] == "warning"
        and item.get("issue_family") in {"intervention_isolation", "gold_output"})
    ]
    return sorted(queue, key=lambda item: (item.get("issue_family", ""), item["issue_id"]))


def _false_positive_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in items
        if item["severity"] == "warning"
        and any(marker in item.get("reason", "").lower() for marker in ("metadata", "provenance", "formatting"))
    ][:50]


def _issue_family(source: str, raw_id: str, reason: str, fix: str) -> str:
    text = " ".join([source, raw_id, reason, fix]).lower()
    if "pair" in text:
        return "pairing"
    if "intervention" in text or "multi_factor" in text:
        return "intervention_isolation"
    if "gold" in text or "expected" in text or "answer" in text:
        return "gold_output"
    if "tool" in text:
        return "tool_schema"
    if "leak" in text or "duplicate" in text or "split" in text:
        return "leakage"
    if "config" in text or "approval" in text or "budget" in text:
        return "config"
    if "release" in text:
        return "release"
    if "paper" in text or "claim" in text:
        return "paper"
    return "intervention_isolation" if source == "intervention_isolation" else "validation"


def _entity_intervention_type(entity: str) -> str | None:
    if not entity or "." not in entity:
        return None
    return entity.split("::")[-1].rsplit(".", 1)[-1]


def _mode(values: list[Any]) -> Any:
    counts: dict[Any, int] = {}
    for value in values:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return None
    return sorted(counts.items(), key=lambda row: (-row[1], str(row[0])))[0][0]
