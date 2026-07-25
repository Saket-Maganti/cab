"""Deterministic static leakage and near-duplicate checks."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.benchmark_quality import discover_benchmark_dirs
from causal_agent_bench.safety.common import section_markdown, write_dual_report

MAIN_OR_HELDOUT_SPLITS = {"main", "heldout", "heldout_templates", "test"}
PILOT_SPLITS = {"pilot", "pilot_20", "pilot_100", "provider_pilot"}
# Default subset family: pilot, pilot_100, pilot_20, and dev/development are
# intentionally nested. A duplicate ID across these splits is an *expected*
# subset relationship, not split leakage. Explicit `subset_families` declared
# in splits.json take precedence.
DEFAULT_SUBSET_FAMILIES: tuple[frozenset[str], ...] = (
    frozenset({"pilot", "pilot_20", "pilot_100", "dev", "development"}),
)
TOKEN_RE = re.compile(r"[a-z0-9_]+")
BENIGN_NEAR_DUPLICATE_FIELDS = {"expected_final_answer", "gold_answer", "gold_label"}
MAX_RAW_FINDINGS_IN_MARKDOWN = 100
MAX_EXAMPLES_PER_CLUSTER = 5
TRUE_LEAKAGE_CLASSES = {
    "true_split_leakage",
    "answer_leakage",
    "intervention_label_leakage",
    "hidden_metadata_visible",
    "duplicate_id_leakage",
    "split_metadata_issue",
}
FALSE_POSITIVE_CLASSES = {
    "likely_template_reuse",
    "clean_intervention_pair_similarity",
    "task_family_boilerplate",
    "shared_tool_description",
    "shared_system_instruction",
    "expected_subset_overlap",
    "instruction_parameter_overlap",
}
ANSWER_SPOILER_MARKERS = (
    "final answer",
    "expected answer",
    "gold answer",
    "correct answer",
    "answer is",
    "respond with",
    "output must be",
)
DATE_LEAF_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_LEAF_RE = re.compile(r"^\d{1,2}:\d{2}$")
BOILERPLATE_TOKENS = {
    "answer",
    "available",
    "call",
    "check",
    "concise",
    "context",
    "database",
    "determine",
    "final",
    "find",
    "given",
    "instruction",
    "lookup",
    "policy",
    "provide",
    "report",
    "return",
    "table",
    "task",
    "threshold",
    "tool",
    "use",
    "using",
}
TOOL_DESCRIPTION_TOKENS = {"tool", "lookup", "database", "api", "search", "query", "record", "records", "table"}
SYSTEM_INSTRUCTION_TOKENS = {"answer", "final", "concise", "respond", "report", "provide", "return", "only", "format"}


def build_static_leakage_report(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    output_dir: str | Path = "reports/static_leakage",
    near_duplicate_threshold: float = 0.88,
    max_raw_findings_in_markdown: int = MAX_RAW_FINDINGS_IN_MARKDOWN,
    max_examples_per_cluster: int = MAX_EXAMPLES_PER_CLUSTER,
    suppression_path: str | Path | None = None,
) -> dict[str, Any]:
    from causal_agent_bench.safety.leakage_suppressions import (
        apply_suppressions,
        load_suppression_registry,
    )

    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    dataset_dirs = [Path(benchmark_dir)] if benchmark_dir else discover_benchmark_dirs(root)
    dataset_reports = [
        check_static_leakage_for_dataset(
            path if path.is_absolute() else root / path,
            repo_root=root,
            near_duplicate_threshold=near_duplicate_threshold,
        )
        for path in dataset_dirs
    ]
    raw_findings = [issue for report in dataset_reports for issue in report.get("raw_findings", report["issues"])]
    issues = _dedupe_findings(raw_findings)
    root_causes = _cluster_findings(issues, max_examples=max_examples_per_cluster)
    registry = load_suppression_registry(root, path=suppression_path)
    suppression_result = apply_suppressions(root_causes, registry=registry)
    root_causes = suppression_result["annotated_root_causes"]
    active_root_causes = [row for row in root_causes if not row.get("suppressed")]
    top_provider = [
        row
        for row in active_root_causes
        if row["readiness_gate"] == "must_fix_before_provider_pilot"
        and row["leakage_risk"] in {"blocker", "needs_review"}
    ][:20]
    top_main = [
        row
        for row in active_root_causes
        if row["readiness_gate"] == "must_fix_before_main_benchmark"
    ][:20]
    classification_counts = _classification_counts(root_causes)
    summary = {
        "dataset_count": len(dataset_reports),
        "issue_count": len(issues),
        "raw_finding_count": len(raw_findings),
        "cluster_count": len(root_causes),
        "active_cluster_count": len(active_root_causes),
        "suppressed_cluster_count": sum(1 for row in root_causes if row.get("suppressed")),
        "suppressed_symptom_count": max(0, len(raw_findings) - len(root_causes)),
        "blockers": sum(1 for issue in issues if issue["severity"] == "blocker"),
        "warnings": sum(1 for issue in issues if issue["severity"] == "warning"),
        "classification_counts": classification_counts,
        "blocker_cluster_count": sum(1 for row in active_root_causes if row["leakage_risk"] == "blocker"),
        "warning_cluster_count": sum(1 for row in active_root_causes if row["leakage_risk"] == "warning"),
        "false_positive_candidate_count": sum(
            1 for row in active_root_causes if row["leakage_risk"] == "false_positive_candidate"
        ),
        "needs_review_count": sum(1 for row in active_root_causes if row["leakage_risk"] == "needs_review"),
        "registry_active_suppressions": registry.get("active_count", 0),
        "registry_expired_suppressions": registry.get("expired_count", 0),
        "registry_malformed_entries": registry.get("malformed_count", 0),
        "refused_suppression_attempts": len(suppression_result["refused_attempts"]),
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static leakage heuristics only; no embeddings, models, providers, or benchmark runs.",
        "near_duplicate_threshold": near_duplicate_threshold,
        "summary": summary,
        "datasets": dataset_reports,
        "raw_finding_count": len(raw_findings),
        "cluster_count": len(root_causes),
        "suppressed_symptom_count": max(0, len(raw_findings) - len(root_causes)),
        "root_causes": root_causes,
        "root_cause_summary": root_causes,
        "active_root_causes": active_root_causes,
        "top_clusters": active_root_causes[:20],
        "classification_counts": classification_counts,
        "blocker_cluster_count": summary["blocker_cluster_count"],
        "warning_cluster_count": summary["warning_cluster_count"],
        "false_positive_candidate_count": summary["false_positive_candidate_count"],
        "needs_review_count": summary["needs_review_count"],
        "top_true_leakage_clusters": _top_true_leakage_clusters(active_root_causes),
        "top_false_positive_candidates": _false_positive_candidates(active_root_causes),
        "top_needs_manual_review": _manual_review_queue(active_root_causes),
        "top_provider_pilot_blockers": top_provider,
        "top_main_benchmark_blockers": top_main,
        "manual_review_queue": _manual_review_queue(active_root_causes),
        "false_positive_candidates": _false_positive_candidates(active_root_causes),
        "suppression_registry_path": registry.get("registry_path"),
        "active_suppressions": suppression_result["active_entries"],
        "expired_suppressions": suppression_result["expired_entries"],
        "refused_suppression_attempts": suppression_result["refused_attempts"],
        "suppression_usage_counts": suppression_result["usage_counts"],
        "suppression_issues": registry.get("issues", []),
        "raw_findings": raw_findings,
        "issues": sorted(issues, key=lambda row: (row["severity"], row["dataset"], row["issue_id"])),
    }
    md = static_leakage_markdown(payload, max_raw_findings=max_raw_findings_in_markdown)
    md_path, json_path = write_dual_report(
        stem="static_leakage_report",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def check_static_leakage_for_dataset(
    dataset_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    near_duplicate_threshold: float = 0.88,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    path = Path(dataset_dir)
    if not path.is_absolute():
        path = root / path
    base_tasks = _read_jsonl(path / "base_tasks.jsonl")
    instances = _read_jsonl(path / "instances.jsonl")
    rows = instances or [{"instance_id": _task_id(task), "condition": "base_task", "base_task": task} for task in base_tasks]
    raw_findings: list[dict[str, Any]] = []
    splits = _load_splits(path)
    subset_families = _load_subset_families(path)
    split_lookup = _split_lookup(splits)

    _check_split_duplicates(path, root, splits, raw_findings, subset_families=subset_families)
    _check_variant_split_overlap(path, root, splits, raw_findings, subset_families=subset_families)
    _check_near_duplicate_prompts(path, root, rows, split_lookup, raw_findings, near_duplicate_threshold)
    _check_identical_expected_outputs(path, root, rows, raw_findings)
    _check_prompt_leakage(path, root, rows, raw_findings)
    _check_visible_metadata_leakage(path, root, rows, raw_findings)

    issues = _dedupe_findings(raw_findings)
    root_causes = _cluster_findings(issues)
    blockers = sum(1 for issue in issues if issue["severity"] == "blocker")
    classification_counts = _classification_counts(root_causes)
    return {
        "dataset": _rel(path, root),
        "task_count": len(base_tasks),
        "instance_count": len(instances),
        "split_count": len(splits),
        "issue_count": len(issues),
        "raw_finding_count": len(raw_findings),
        "cluster_count": len(root_causes),
        "suppressed_symptom_count": max(0, len(raw_findings) - len(root_causes)),
        "classification_counts": classification_counts,
        "blocker_cluster_count": sum(1 for row in root_causes if row["leakage_risk"] == "blocker"),
        "warning_cluster_count": sum(1 for row in root_causes if row["leakage_risk"] == "warning"),
        "false_positive_candidate_count": sum(1 for row in root_causes if row["leakage_risk"] == "false_positive_candidate"),
        "needs_review_count": sum(1 for row in root_causes if row["leakage_risk"] == "needs_review"),
        "blockers": blockers,
        "warnings": sum(1 for issue in issues if issue["severity"] == "warning"),
        "passed": blockers == 0,
        "raw_findings": raw_findings,
        "root_causes": root_causes,
        "root_cause_summary": root_causes,
        "top_clusters": root_causes[:20],
        "top_true_leakage_clusters": _top_true_leakage_clusters(root_causes),
        "top_false_positive_candidates": _false_positive_candidates(root_causes),
        "top_needs_manual_review": _manual_review_queue(root_causes),
        "issues": issues,
    }


def static_leakage_markdown(payload: dict[str, Any], *, max_raw_findings: int = MAX_RAW_FINDINGS_IN_MARKDOWN) -> str:
    summary = payload["summary"]
    lines = [
        "# Static Leakage Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        "This is a static heuristic report, not empirical model evidence.",
        "",
        section_markdown(
            "Executive Summary",
            [
                f"- Datasets scanned: {summary['dataset_count']}",
                f"- Raw findings: {summary['raw_finding_count']}",
                f"- Deduplicated findings: {summary['issue_count']}",
                f"- Root-cause clusters: {summary['cluster_count']}",
                f"- Active clusters (post-suppression): {summary.get('active_cluster_count', summary['cluster_count'])}",
                f"- Suppressed clusters (reviewed registry): {summary.get('suppressed_cluster_count', 0)}",
                f"- Suppressed/deduplicated symptoms: {summary['suppressed_symptom_count']}",
                f"- Blockers: {summary['blockers']}",
                f"- Warnings: {summary['warnings']}",
                f"- Blocker clusters: {summary['blocker_cluster_count']}",
                f"- False-positive candidate clusters: {summary['false_positive_candidate_count']}",
                f"- Needs-review clusters: {summary['needs_review_count']}",
                f"- Active suppression entries: {summary.get('registry_active_suppressions', 0)}",
                f"- Expired suppression entries: {summary.get('registry_expired_suppressions', 0)}",
                f"- Refused suppression attempts (blocker classes): {summary.get('refused_suppression_attempts', 0)}",
            ],
        ),
        "## Classification Counts",
        "",
    ]
    for name, count in sorted(payload.get("classification_counts", {}).items()):
        lines.append(f"- `{name}`: {count}")
    lines.extend(
        [
            "",
            "## Top True Leakage Blockers",
            "",
        ]
    )
    if not payload.get("top_true_leakage_clusters"):
        lines.append("- (none)")
    for row in payload.get("top_true_leakage_clusters", [])[:10]:
        lines.append(
            f"- rank {row['rank']} `{row['root_cause_id']}` [{row['leakage_risk']}] "
            f"{row['root_cause_title']} ({row['symptom_count']} symptoms) -> {row['recommended_action']}"
        )
    lines.extend(
        [
            "",
            "## Top Provider-Pilot Leakage Blockers",
            "",
        ]
    )
    if not payload.get("top_provider_pilot_blockers"):
        lines.append("- (none)")
    for row in payload.get("top_provider_pilot_blockers", [])[:10]:
        lines.append(f"- `{row['root_cause_id']}` {row['root_cause_title']} -> {row['recommended_action']}")
    lines.extend(
        [
            "",
            "## Top Likely False Positives / Boilerplate Clusters",
            "",
        ]
    )
    if not payload.get("top_false_positive_candidates"):
        lines.append("- (none)")
    for row in payload.get("top_false_positive_candidates", [])[:20]:
        lines.append(
            f"- `{row['root_cause_id']}` {row['cluster_classification']} "
            f"({row['symptom_count']} symptoms, basis={row.get('classification_basis', 'n/a')})"
        )
    lines.extend(
        [
            "",
            "## Top Manual-Review Clusters",
            "",
        ]
    )
    if not payload.get("top_needs_manual_review"):
        lines.append("- (none)")
    for row in payload.get("top_needs_manual_review", [])[:20]:
        lines.append(f"- `{row['root_cause_id']}` {row['root_cause_title']} -> {row['recommended_action']}")
    lines.extend(
        [
            "",
            "## Root-Cause Summary",
            "",
        ]
    )
    if not payload.get("top_clusters"):
        lines.append("- (none)")
    for row in payload.get("top_clusters", [])[:20]:
        lines.append(
            f"- rank {row['rank']} `{row['root_cause_id']}` [{row['leakage_risk']}] "
            f"{row['root_cause_title']} ({row['symptom_count']} symptoms) -> {row['recommended_action']}"
        )
    lines.extend(["", "## Top Main-Benchmark Leakage Blockers", ""])
    if not payload.get("top_main_benchmark_blockers"):
        lines.append("- (none)")
    for row in payload.get("top_main_benchmark_blockers", [])[:10]:
        lines.append(
            f"- `{row['root_cause_id']}` {row['root_cause_title']} -> "
            f"{row.get('recommended_action') or row.get('suggested_fix')}"
        )
    lines.extend(["", "## Manual Review Queue", ""])
    if not payload.get("manual_review_queue"):
        lines.append("- (none)")
    for row in payload.get("manual_review_queue", [])[:20]:
        lines.append(f"- `{row['root_cause_id']}` {row['root_cause_title']}")
    lines.extend(["", "## False-Positive Candidates", ""])
    if not payload.get("false_positive_candidates"):
        lines.append("- (none)")
    for row in payload.get("false_positive_candidates", [])[:20]:
        lines.append(f"- `{row['root_cause_id']}` {row['root_cause_title']}")
    lines.extend(["", "## Active Suppressions", ""])
    active_suppressions = payload.get("active_suppressions") or []
    if not active_suppressions:
        lines.append("- (none)")
    for entry in active_suppressions[:20]:
        lines.append(
            f"- `{entry['id']}` reviewer={entry['reviewer']} scope={entry['scope']} "
            f"date={entry['date']} -> reason: {entry['reason']}"
        )
    expired = payload.get("expired_suppressions") or []
    if expired:
        lines.extend(["", "## Expired Suppressions (reappear as active)", ""])
        for entry in expired[:20]:
            lines.append(
                f"- `{entry['id']}` expired={entry.get('review_after')} reviewer={entry['reviewer']} "
                f"-> reason: {entry['reason']}"
            )
    refused = payload.get("refused_suppression_attempts") or []
    if refused:
        lines.extend(["", "## Refused Suppression Attempts (always-blocking classes)", ""])
        for refusal in refused[:20]:
            lines.append(
                f"- `{refusal.get('suppression_id')}` cluster=`{refusal.get('cluster_id')}` "
                f"class=`{refusal.get('classification')}` risk=`{refusal.get('leakage_risk')}` "
                f"-> {refusal.get('reason')}"
            )
    lines.extend(
        [
            "",
            "## Next Actions",
            "",
            "- Fix provider-pilot split, answer leakage, and visible hidden-metadata blockers first.",
            "- Review near-duplicate clusters before editing large batches.",
            "- Use raw findings in JSON for traceability; do not manually triage the raw flood first.",
            "- Suppressions are advisory metadata only; never use them to hide blocker-risk findings.",
            "",
            "## Capped Raw Finding Examples",
            "",
        ]
    )
    raw_examples = payload.get("issues", [])[:max_raw_findings]
    if not raw_examples:
        lines.append("- (none)")
    for issue in raw_examples:
        lines.append(
            f"- `{issue['severity']}` `{issue['dataset']}` `{issue['entity_id']}` "
            f"`{issue['finding_type']}`: {issue['message']}"
        )
    if len(payload.get("issues", [])) > max_raw_findings:
        lines.append(f"- Raw finding examples capped at {max_raw_findings}; full raw findings are in JSON only.")
    lines.append("")
    return "\n".join(lines)


def _check_split_duplicates(
    path: Path,
    root: Path,
    splits: dict[str, dict[str, set[str]]],
    issues: list[dict[str, Any]],
    *,
    subset_families: tuple[frozenset[str], ...] = DEFAULT_SUBSET_FAMILIES,
) -> None:
    for id_kind in ("task_ids", "instance_ids"):
        owners: dict[str, list[str]] = defaultdict(list)
        for split, ids in splits.items():
            for value in ids.get(id_kind, set()):
                owners[value].append(split)
        for value, split_names in owners.items():
            if len(split_names) <= 1:
                continue
            sorted_splits = sorted(split_names)
            is_expected_subset = _is_expected_subset_overlap(sorted_splits, subset_families)
            finding_type = "duplicate_task_id" if id_kind == "task_ids" else "duplicate_instance_id"
            if is_expected_subset:
                # Intentional pilot-family subset overlap: e.g., pilot_20 ⊂ pilot.
                # Surface as informational/false_positive_candidate only.
                issues.append(
                    _issue(
                        path,
                        root,
                        "informational",
                        finding_type,
                        value,
                        f"{value} appears in multiple splits inside a declared subset family: {', '.join(sorted_splits)}.",
                        source_split=sorted_splits[0],
                        target_split=sorted_splits[1] if len(sorted_splits) > 1 else None,
                        task_id=value if id_kind == "task_ids" else None,
                        instance_id=value if id_kind == "instance_ids" else None,
                        affected_field=id_kind,
                        cluster_classification="expected_subset_overlap",
                        leakage_risk="false_positive_candidate",
                        readiness_gate="nice_to_have",
                        classification_basis="subset_family_overlap",
                        reason="Splits are part of a declared subset family (e.g. pilot_20 ⊂ pilot_100 ⊂ pilot, dev ⊂ pilot). No protected split was crossed.",
                        recommended_action="No dataset edit needed. Update the subset_families list in splits.json if this is unexpected.",
                    )
                )
                continue
            issues.append(
                _issue(
                    path,
                    root,
                    "blocker",
                    finding_type,
                    value,
                    f"{value} appears in multiple splits: {', '.join(sorted_splits)}.",
                    source_split=sorted_splits[0],
                    target_split=sorted_splits[1] if len(sorted_splits) > 1 else None,
                    task_id=value if id_kind == "task_ids" else None,
                    instance_id=value if id_kind == "instance_ids" else None,
                    affected_field=id_kind,
                )
            )
    pilot_ids = set().union(*(splits[name]["instance_ids"] for name in splits if name in PILOT_SPLITS)) if splits else set()
    main_ids = set().union(*(splits[name]["instance_ids"] for name in splits if name in MAIN_OR_HELDOUT_SPLITS)) if splits else set()
    overlap = sorted(pilot_ids & main_ids)
    for value in overlap[:20]:
        issues.append(
            _issue(
                path,
                root,
                "blocker",
                "provider_pilot_overlap",
                value,
                "Provider-pilot split overlaps with main/heldout split.",
                instance_id=value,
                affected_field="split.instance_ids",
                readiness_gate="must_fix_before_provider_pilot",
            )
        )


def _check_variant_split_overlap(
    path: Path,
    root: Path,
    splits: dict[str, dict[str, set[str]]],
    issues: list[dict[str, Any]],
    *,
    subset_families: tuple[frozenset[str], ...] = DEFAULT_SUBSET_FAMILIES,
) -> None:
    base_to_splits: dict[str, set[str]] = defaultdict(set)
    for split, ids in splits.items():
        for instance_id in ids.get("instance_ids", set()):
            base_to_splits[_base_from_instance_id(instance_id)].add(split)
    for base_id, split_names in base_to_splits.items():
        if not base_id or len(split_names) <= 1:
            continue
        sorted_splits = sorted(split_names)
        if _is_expected_subset_overlap(sorted_splits, subset_families):
            # Subset family is allowed to share clean/intervention pairs.
            continue
        if any(name in MAIN_OR_HELDOUT_SPLITS for name in split_names) and any(name not in MAIN_OR_HELDOUT_SPLITS for name in split_names):
            severity = "blocker" if any(name in PILOT_SPLITS for name in split_names) else "warning"
            issues.append(
                _issue(
                    path,
                    root,
                    severity,
                    "clean_intervention_split_leakage",
                    base_id,
                    f"Clean/intervention variants for {base_id} cross split boundaries: {', '.join(sorted_splits)}.",
                    source_split=sorted_splits[0],
                    target_split=sorted_splits[1] if len(sorted_splits) > 1 else None,
                    task_id=base_id,
                    pair_id=base_id,
                    affected_field="split.instance_ids",
                )
            )


def _check_near_duplicate_prompts(
    path: Path,
    root: Path,
    rows: list[dict[str, Any]],
    split_lookup: dict[str, str],
    issues: list[dict[str, Any]],
    threshold: float,
) -> None:
    prompts: list[dict[str, Any]] = []
    for row in rows:
        prompt = _visible_prompt(row)
        tokens = _tokens(prompt)
        if tokens:
            prompts.append(
                {
                    "row": row,
                    "entity_id": _instance_id(row) or _base_task_id(row),
                    "base_id": _base_task_id(row),
                    "tokens": tokens,
                    "task_family": _task_family(row),
                    "intervention_type": _intervention_type(row),
                    "condition": _condition(row),
                }
            )
    boilerplate_tokens = _dataset_boilerplate_tokens([item["tokens"] for item in prompts])
    task_threshold = max(0.60, threshold - 0.10)
    for index, left in enumerate(prompts):
        for right in prompts[index + 1 :]:
            left_tokens = left["tokens"]
            right_tokens = right["tokens"]
            raw_score = _jaccard(left_tokens, right_tokens)
            left_specific = _task_specific_tokens(left_tokens, boilerplate_tokens)
            right_specific = _task_specific_tokens(right_tokens, boilerplate_tokens)
            task_specific_score = _jaccard(left_specific, right_specific)
            if raw_score < threshold and task_specific_score < task_threshold:
                continue

            left_id = str(left["entity_id"])
            right_id = str(right["entity_id"])
            left_base = str(left["base_id"])
            right_base = str(right["base_id"])
            left_split = split_lookup.get(left_id) or split_lookup.get(left_base)
            right_split = split_lookup.get(right_id) or split_lookup.get(right_base)
            classification = _classify_near_duplicate(
                left=left,
                right=right,
                source_split=left_split,
                target_split=right_split,
                raw_score=raw_score,
                task_specific_score=task_specific_score,
                boilerplate_fraction=_boilerplate_fraction(left_tokens, right_tokens, boilerplate_tokens),
                common_tokens=left_tokens & right_tokens,
                boilerplate_tokens=boilerplate_tokens,
            )
            if classification["leakage_risk"] == "informational" and raw_score < threshold:
                continue

            common_specific = left_specific & right_specific
            common_tokens = common_specific or (left_tokens & right_tokens)
            issues.append(
                _issue(
                    path,
                    root,
                    classification["severity"],
                    "near_duplicate_prompt",
                    f"{left_id}::{right_id}",
                    (
                        f"Prompt token overlap is {raw_score:.2f}; "
                        f"task-specific overlap is {task_specific_score:.2f}."
                    ),
                    source_split=left_split,
                    target_split=right_split,
                    task_id=left_base if left_base == right_base else f"{left_base}::{right_base}",
                    pair_id=f"{left_id}::{right_id}",
                    affected_field="prompt",
                    overlap_score=raw_score,
                    raw_overlap_score=raw_score,
                    boilerplate_adjusted_overlap_score=task_specific_score,
                    boilerplate_fraction=classification["boilerplate_fraction"],
                    task_specific_overlap_score=task_specific_score,
                    classification_basis=classification["classification_basis"],
                    cluster_classification=classification["cluster_classification"],
                    confidence=classification["confidence"],
                    leakage_risk=classification["leakage_risk"],
                    reason=classification["reason"],
                    recommended_action=classification["recommended_action"],
                    representative_snippet=" ".join(sorted(common_tokens)[:12]),
                    readiness_gate=classification["readiness_gate"],
                )
            )


def _check_identical_expected_outputs(path: Path, root: Path, rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    by_answer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        expected = _expected_output(_task_from_row(row))
        if expected is not None:
            by_answer[json.dumps(expected, sort_keys=True, default=str)].append(row)
    for answer, matching in by_answer.items():
        if len(matching) < 2:
            continue
        bases = {_base_task_id(row) for row in matching}
        domains = {_domain(_task_from_row(row)) for row in matching}
        if len(bases) > 1 and len(domains) > 1:
            digest = hashlib.sha1(answer.encode("utf-8")).hexdigest()[:8]
            issues.append(
                _issue(
                    path,
                    root,
                    "warning",
                    "identical_expected_output_unrelated_task",
                    ",".join(sorted(bases)[:4]),
                    f"Identical expected output hash {digest} appears across unrelated task domains.",
                    task_id=",".join(sorted(bases)[:4]),
                    affected_field="expected_output",
                    representative_snippet=digest,
                    readiness_gate="must_fix_before_main_benchmark",
                )
            )


def _check_prompt_leakage(path: Path, root: Path, rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    for row in rows:
        task = _task_from_row(row)
        entity = _instance_id(row) or _base_task_id(row)
        prompt_lower = _visible_prompt(row).lower()
        instruction_lower = _user_instruction_text(row).lower()
        non_instruction_lower = _visible_non_instruction_text(row).lower()
        expected = _expected_output(task)
        for leaf in _answer_leaves(expected):
            if len(leaf) < 4:
                continue
            leaf_lower = leaf.lower()
            if leaf_lower not in prompt_lower:
                continue
            issue_type, severity, classification, risk, gate = _classify_answer_leaf_overlap(
                leaf,
                instruction_lower=instruction_lower,
                non_instruction_lower=non_instruction_lower,
            )
            issues.append(
                _issue(
                    path,
                    root,
                    severity,
                    issue_type,
                    entity,
                    _answer_leaf_message(leaf, issue_type),
                    task_id=_base_task_id(row),
                    instance_id=_instance_id(row),
                    affected_field="prompt",
                    representative_snippet=_safe_snippet(leaf),
                    readiness_gate=gate,
                    cluster_classification=classification,
                    leakage_risk=risk,
                    classification_basis=issue_type,
                    reason=_answer_leaf_reason(issue_type),
                    recommended_action=_fix(issue_type),
                )
            )
            break
        intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
        label = str(intervention.get("family") or intervention.get("intervention_type") or "")
        if label and (label.lower() in prompt_lower or "intervention" in prompt_lower):
            issues.append(
                _issue(
                    path,
                    root,
                    "blocker",
                    "intervention_label_leakage",
                    entity,
                    "Intervention label appears in user-facing prompt/context.",
                    task_id=_base_task_id(row),
                    instance_id=_instance_id(row),
                    affected_field="prompt",
                    representative_snippet=_safe_snippet(label),
                    readiness_gate="must_fix_before_provider_pilot",
                )
            )
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        metadata_text = json.dumps(metadata, sort_keys=True, default=str).lower()
        if label and label.lower() in metadata_text:
            issues.append(
                _issue(
                    path,
                    root,
                    "warning",
                    "intervention_label_leakage",
                    entity,
                    "Intervention label appears in metadata notes; confirm it is hidden from users.",
                    task_id=_base_task_id(row),
                    instance_id=_instance_id(row),
                    affected_field="metadata",
                    representative_snippet=_safe_snippet(label),
                    readiness_gate="must_fix_before_main_benchmark",
                )
            )


def _check_visible_metadata_leakage(path: Path, root: Path, rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    for row in rows:
        entity = _instance_id(row) or _base_task_id(row)
        visible = json.dumps(
            {
                "observations": row.get("observations") or row.get("initial_observations"),
                "context": row.get("context"),
                "visible_context": row.get("visible_context"),
            },
            sort_keys=True,
            default=str,
        ).lower()
        if any(marker in visible for marker in ("intervention_id", "expected_final_answer_change", "hidden_ground_truth", "changed_factor")):
            issues.append(
                _issue(
                    path,
                    root,
                    "blocker",
                    "hidden_metadata_visible",
                    entity,
                    "Hidden metadata marker appears in visible observation/context.",
                    task_id=_base_task_id(row),
                    instance_id=_instance_id(row),
                    affected_field="visible_observation",
                    readiness_gate="must_fix_before_provider_pilot",
                )
            )


def _load_splits(path: Path) -> dict[str, dict[str, set[str]]]:
    payload = _read_json(path / "splits.json") or {}
    raw_splits = payload.get("splits") if isinstance(payload.get("splits"), dict) else payload
    out: dict[str, dict[str, set[str]]] = {}
    if not isinstance(raw_splits, dict):
        return out
    for name, value in raw_splits.items():
        if isinstance(value, dict):
            task_ids = set(map(str, value.get("base_task_ids") or value.get("task_ids") or []))
            instance_ids = set(map(str, value.get("instance_ids") or []))
        elif isinstance(value, list):
            task_ids = set(map(str, value))
            instance_ids = set()
        else:
            continue
        out[str(name)] = {"task_ids": task_ids, "instance_ids": instance_ids}
    return out


def _load_subset_families(path: Path) -> tuple[frozenset[str], ...]:
    """Return declared subset-family groupings from splits.json (or defaults)."""

    payload = _read_json(path / "splits.json") or {}
    raw = payload.get("subset_families") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        return DEFAULT_SUBSET_FAMILIES
    families: list[frozenset[str]] = []
    for family in raw:
        if isinstance(family, list):
            families.append(frozenset(str(name) for name in family if name))
    return tuple(families) if families else DEFAULT_SUBSET_FAMILIES


def _is_expected_subset_overlap(
    split_names: list[str],
    subset_families: tuple[frozenset[str], ...],
) -> bool:
    """Return True if the duplicate spans only one declared subset family.

    A duplicate ID across splits {dev, pilot} or {pilot, pilot_100} is expected
    when both names belong to the same declared subset family and no protected
    split (heldout/main/test/train) is involved.
    """

    names = set(split_names)
    if names & MAIN_OR_HELDOUT_SPLITS:
        return False
    if names & {"train"}:
        return False
    return any(names.issubset(family) for family in subset_families)


def _split_lookup(splits: dict[str, dict[str, set[str]]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for split, ids in splits.items():
        for task_id in ids.get("task_ids", set()):
            lookup.setdefault(task_id, split)
        for instance_id in ids.get("instance_ids", set()):
            lookup.setdefault(instance_id, split)
            lookup.setdefault(_base_from_instance_id(instance_id), split)
    return lookup


def _protected_split_pair(source_split: str | None, target_split: str | None) -> bool:
    if not source_split or not target_split or source_split == target_split:
        return False
    names = {source_split, target_split}
    return bool(names & MAIN_OR_HELDOUT_SPLITS) and bool(names & (PILOT_SPLITS | {"dev", "train", "development"}))


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


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


def _user_instruction_text(row: dict[str, Any]) -> str:
    task = _task_from_row(row)
    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    return str(goal.get("user_instruction") or task.get("user_instruction") or row.get("prompt") or "")


def _visible_non_instruction_text(row: dict[str, Any]) -> str:
    parts = [
        row.get("context"),
        row.get("visible_context"),
        row.get("observations"),
        row.get("initial_observations"),
    ]
    return " ".join(
        json.dumps(part, sort_keys=True, default=str) if isinstance(part, (dict, list)) else str(part or "")
        for part in parts
    )


def _visible_prompt(row: dict[str, Any]) -> str:
    return " ".join(part for part in (_user_instruction_text(row), _visible_non_instruction_text(row)) if part)


def _classify_answer_leaf_overlap(
    leaf: str,
    *,
    instruction_lower: str,
    non_instruction_lower: str,
) -> tuple[str, str, str, str, str]:
    """Classify expected-output substring overlap with visible agent context.

    Returns ``(issue_type, severity, cluster_classification, leakage_risk, readiness_gate)``.
    True answer spoilers outside task parameters remain provider-pilot blockers.
    Dates/times and short tokens embedded only in ``user_instruction`` are calibrated
    as instruction-parameter overlap (not duplicate-ID blockers).
    """
    leaf_lower = leaf.lower()
    if leaf_lower not in instruction_lower and leaf_lower not in non_instruction_lower:
        return (
            "no_visible_overlap",
            "informational",
            "likely_template_reuse",
            "informational",
            "nice_to_have",
        )
    if leaf_lower in non_instruction_lower:
        return (
            "answer_text_leakage",
            "blocker",
            "answer_leakage",
            "blocker",
            "must_fix_before_provider_pilot",
        )
    if leaf_lower not in instruction_lower:
        return (
            "answer_text_leakage",
            "blocker",
            "answer_leakage",
            "blocker",
            "must_fix_before_provider_pilot",
        )
    if _looks_like_answer_spoiler(instruction_lower, leaf_lower):
        return (
            "answer_text_leakage",
            "blocker",
            "answer_leakage",
            "blocker",
            "must_fix_before_provider_pilot",
        )
    if _looks_like_instruction_parameter(leaf, instruction_lower):
        return (
            "instruction_parameter_overlap",
            "informational",
            "instruction_parameter_overlap",
            "false_positive_candidate",
            "nice_to_have",
        )
    return (
        "answer_text_leakage",
        "blocker",
        "answer_leakage",
        "blocker",
        "must_fix_before_provider_pilot",
    )


def _looks_like_answer_spoiler(instruction_lower: str, leaf_lower: str) -> bool:
    for marker in ANSWER_SPOILER_MARKERS:
        idx = instruction_lower.find(marker)
        if idx >= 0 and leaf_lower in instruction_lower[idx : idx + 120]:
            return True
    return False


def _looks_like_instruction_parameter(leaf: str, instruction_lower: str) -> bool:
    if DATE_LEAF_RE.fullmatch(leaf.strip()) or TIME_LEAF_RE.fullmatch(leaf.strip()):
        return True
    leaf_lower = leaf.lower()
    if leaf_lower not in instruction_lower:
        return False
    return len(leaf_lower) <= 12


def _answer_leaf_message(leaf: str, issue_type: str) -> str:
    if issue_type == "instruction_parameter_overlap":
        return (
            f"Expected output token `{leaf}` also appears in the task instruction as a "
            "declared parameter (not treated as a provider-pilot leakage blocker)."
        )
    return f"Expected answer text `{leaf}` appears in visible prompt/context."


def _answer_leaf_reason(issue_type: str) -> str:
    if issue_type == "instruction_parameter_overlap":
        return (
            "Gold-output token overlaps the user instruction because the task states the "
            "same date/time/entity explicitly; review only if the overlap is unintended."
        )
    return "Expected answer text is visible in the prompt/context."


def _expected_output(task: dict[str, Any]) -> Any:
    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    for container in (goal, task):
        for key in ("expected_final_answer", "expected_output", "gold_answer", "gold_label"):
            if key in container:
                return container[key]
    return None


def _answer_leaves(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()]
    if isinstance(value, int | float):
        return [str(value)]
    if isinstance(value, list):
        return [leaf for item in value for leaf in _answer_leaves(item)]
    if isinstance(value, dict):
        return [leaf for item in value.values() for leaf in _answer_leaves(item)]
    return []


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _dataset_boilerplate_tokens(token_sets: list[set[str]]) -> set[str]:
    counts: dict[str, int] = defaultdict(int)
    for tokens in token_sets:
        for token in tokens:
            counts[token] += 1
    threshold = max(3, int(len(token_sets) * 0.60 + 0.999))
    repeated = {token for token, count in counts.items() if count >= threshold}
    return BOILERPLATE_TOKENS | repeated


def _task_specific_tokens(tokens: set[str], boilerplate_tokens: set[str]) -> set[str]:
    return tokens - boilerplate_tokens


def _boilerplate_fraction(left: set[str], right: set[str], boilerplate_tokens: set[str]) -> float:
    shared = left & right
    if not shared:
        return 0.0
    return len(shared & boilerplate_tokens) / len(shared)


def _classify_near_duplicate(
    *,
    left: dict[str, Any],
    right: dict[str, Any],
    source_split: str | None,
    target_split: str | None,
    raw_score: float,
    task_specific_score: float,
    boilerplate_fraction: float,
    common_tokens: set[str],
    boilerplate_tokens: set[str],
) -> dict[str, Any]:
    same_base = left["base_id"] == right["base_id"]
    same_family = left.get("task_family") == right.get("task_family")
    protected = _protected_split_pair(source_split, target_split)
    has_split_metadata = bool(source_split and target_split)
    boilerplate_class = _boilerplate_classification(common_tokens, boilerplate_tokens, same_family=same_family)

    if same_base and not protected:
        return _classification(
            "clean_intervention_pair_similarity",
            "high",
            "false_positive_candidate",
            "informational",
            "nice_to_have",
            "linked_clean_intervention_pair",
            boilerplate_fraction,
            "Clean/intervention variants for the same task are expected to share prompt surface.",
            "No dataset edit needed unless the pair is split across protected boundaries.",
        )
    if same_base and protected:
        return _classification(
            "split_metadata_issue",
            "high",
            "blocker",
            "blocker",
            "must_fix_before_provider_pilot",
            "linked_pair_crosses_protected_split",
            boilerplate_fraction,
            "A clean/intervention pair appears across protected split boundaries.",
            "Keep linked clean/intervention variants inside one approved split family.",
        )
    if not has_split_metadata:
        return _classification(
            "split_metadata_issue",
            "medium",
            "needs_review",
            "warning",
            "manual_review_needed",
            "missing_split_metadata",
            boilerplate_fraction,
            "Split metadata is missing or ambiguous, so near-duplicate risk cannot be gated reliably.",
            "Add or repair split metadata before treating this as true leakage.",
        )
    if boilerplate_fraction >= 0.65 and task_specific_score < 0.60:
        return _classification(
            boilerplate_class,
            "high" if raw_score >= 0.85 else "medium",
            "false_positive_candidate",
            "informational",
            "nice_to_have",
            "boilerplate_high_raw_low_task_specific",
            boilerplate_fraction,
            "Raw overlap is dominated by shared instructions, task templates, or tool descriptions.",
            "Review one representative cluster and tune boilerplate rules if needed; do not bulk-delete tasks from this alone.",
        )
    if protected and same_family:
        # Same task family across protected split: scaffolding overlap is expected.
        # Surface as needs_review/warning at main-benchmark gate, not provider-pilot blocker.
        if task_specific_score >= 0.70:
            return _classification(
                "same_family_protected_split_overlap",
                "medium",
                "needs_review",
                "warning",
                "must_fix_before_main_benchmark",
                "same_family_protected_split_high_task_specific_overlap",
                boilerplate_fraction,
                "Different tasks in the same task family share high task-specific prompt content across a protected split. "
                "Likely shared scaffolding rather than cross-family leakage.",
                "Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. "
                "If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.",
            )
        return _classification(
            "same_family_protected_split_overlap",
            "low",
            "false_positive_candidate",
            "informational",
            "nice_to_have",
            "same_family_protected_split_moderate_overlap",
            boilerplate_fraction,
            "Different tasks in the same task family with moderate overlap across a protected split.",
            "Likely shared scaffolding; document or ignore unless reviewer disagrees.",
        )
    if protected and task_specific_score >= 0.70:
        return _classification(
            "true_split_leakage",
            "high",
            "blocker",
            "blocker",
            "must_fix_before_provider_pilot",
            "protected_split_high_task_specific_overlap_cross_family",
            boilerplate_fraction,
            "Unrelated task families share high task-specific prompt content across protected split boundaries.",
            "Move, rewrite, or remove one side of the protected split overlap before provider-pilot planning.",
        )
    if protected:
        return _classification(
            "needs_manual_review",
            "medium",
            "needs_review",
            "warning",
            "must_fix_before_provider_pilot",
            "protected_split_moderate_task_specific_overlap",
            boilerplate_fraction,
            "Protected split overlap remains after boilerplate removal, but task-specific overlap is not decisive.",
            "Manually inspect representative examples before editing tasks or approving provider-pilot splits.",
        )
    if task_specific_score >= 0.70:
        return _classification(
            "needs_manual_review",
            "medium",
            "warning",
            "warning",
            "must_fix_before_main_benchmark",
            "unprotected_high_task_specific_overlap",
            boilerplate_fraction,
            "Unrelated examples have high task-specific prompt overlap.",
            "Review whether this is intentional task-family reuse or a duplicate task.",
        )
    return _classification(
        boilerplate_class,
        "medium",
        "false_positive_candidate",
        "informational",
        "nice_to_have",
        "template_or_family_similarity",
        boilerplate_fraction,
        "Prompt similarity appears consistent with shared template or task-family boilerplate.",
        "Keep as a low-priority review item; prioritize answer leakage, duplicate IDs, and protected split leakage first.",
    )


def _classification(
    cluster_classification: str,
    confidence: str,
    leakage_risk: str,
    severity: str,
    readiness_gate: str,
    basis: str,
    boilerplate_fraction: float,
    reason: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "cluster_classification": cluster_classification,
        "confidence": confidence,
        "leakage_risk": leakage_risk,
        "severity": severity,
        "readiness_gate": readiness_gate,
        "classification_basis": basis,
        "boilerplate_fraction": round(boilerplate_fraction, 4),
        "reason": reason,
        "recommended_action": recommended_action,
    }


def _boilerplate_classification(common_tokens: set[str], boilerplate_tokens: set[str], *, same_family: bool) -> str:
    shared_boilerplate = common_tokens & boilerplate_tokens
    if len(shared_boilerplate & TOOL_DESCRIPTION_TOKENS) >= 3:
        return "shared_tool_description"
    if len(shared_boilerplate & SYSTEM_INSTRUCTION_TOKENS) >= 3:
        return "shared_system_instruction"
    if same_family:
        return "task_family_boilerplate"
    return "likely_template_reuse"


def _task_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("base_task") if isinstance(row.get("base_task"), dict) else row


def _base_task_id(row: dict[str, Any]) -> str:
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    task = _task_from_row(row)
    value = intervention.get("base_task_id") or row.get("base_task_id") or task.get("task_id")
    if value:
        return str(value)
    instance_id = _instance_id(row)
    return _base_from_instance_id(instance_id) if instance_id else "unknown"


def _base_from_instance_id(instance_id: str | None) -> str:
    if not instance_id:
        return "unknown"
    return instance_id.split(".", 1)[0] if "." in instance_id else instance_id


def _task_id(task: dict[str, Any]) -> str | None:
    value = task.get("task_id") or task.get("id")
    return str(value) if value else None


def _instance_id(row: dict[str, Any]) -> str | None:
    value = row.get("instance_id") or row.get("id")
    return str(value) if value else None


def _domain(task: dict[str, Any]) -> str:
    return str(task.get("domain") or task.get("category") or "unknown")


def _task_family(row: dict[str, Any]) -> str:
    task = _task_from_row(row)
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    return str(
        task.get("task_family")
        or task.get("family")
        or task.get("domain")
        or task.get("category")
        or intervention.get("task_family")
        or "unknown"
    )


def _intervention_type(row: dict[str, Any]) -> str:
    intervention = row.get("intervention") if isinstance(row.get("intervention"), dict) else {}
    return str(
        intervention.get("intervention_type")
        or intervention.get("family")
        or row.get("intervention_type")
        or row.get("condition")
        or "clean"
    )


def _condition(row: dict[str, Any]) -> str:
    value = row.get("condition")
    if value:
        return str(value)
    return "intervention" if isinstance(row.get("intervention"), dict) else "clean"


def _issue(
    path: Path,
    root: Path,
    severity: str,
    issue_type: str,
    entity_id: str,
    message: str,
    *,
    source_split: str | None = None,
    target_split: str | None = None,
    task_id: str | None = None,
    instance_id: str | None = None,
    pair_id: str | None = None,
    affected_field: str | None = None,
    overlap_score: float | None = None,
    raw_overlap_score: float | None = None,
    boilerplate_adjusted_overlap_score: float | None = None,
    boilerplate_fraction: float | None = None,
    task_specific_overlap_score: float | None = None,
    classification_basis: str | None = None,
    cluster_classification: str | None = None,
    confidence: str | None = None,
    leakage_risk: str | None = None,
    reason: str | None = None,
    recommended_action: str | None = None,
    representative_snippet: str | None = None,
    readiness_gate: str | None = None,
) -> dict[str, Any]:
    dataset = _rel(path, root)
    stable = hashlib.sha1(f"{dataset}|{issue_type}|{entity_id}|{message}".encode()).hexdigest()[:12]
    defaults = _default_classification(issue_type, severity, affected_field, source_split, target_split)
    risk = leakage_risk or defaults["leakage_risk"]
    final_severity = _severity_from_risk(risk, severity)
    gate = readiness_gate or defaults["readiness_gate"] or _readiness_gate(issue_type, final_severity, source_split, target_split)
    action = recommended_action or defaults["recommended_action"] or _fix(issue_type)
    return {
        "issue_id": f"leak_{stable}",
        "finding_id": f"leak_{stable}",
        "severity": final_severity,
        "issue_type": issue_type,
        "finding_type": issue_type,
        "dataset": dataset,
        "entity_id": entity_id,
        "source_split": source_split,
        "target_split": target_split,
        "task_id": task_id,
        "instance_id": instance_id,
        "pair_id": pair_id,
        "affected_field": affected_field,
        "overlap_score": overlap_score,
        "raw_overlap_score": raw_overlap_score if raw_overlap_score is not None else overlap_score,
        "boilerplate_adjusted_overlap_score": boilerplate_adjusted_overlap_score,
        "boilerplate_fraction": boilerplate_fraction,
        "task_specific_overlap_score": task_specific_overlap_score,
        "cluster_classification": cluster_classification or defaults["cluster_classification"],
        "confidence": confidence or defaults["confidence"],
        "leakage_risk": risk,
        "classification_basis": classification_basis or defaults["classification_basis"],
        "reason": reason or defaults["reason"],
        "representative_snippet": representative_snippet,
        "readiness_gate": gate,
        "message": message,
        "recommended_fix": _fix(issue_type),
        "recommended_action": action,
    }


def _default_classification(
    issue_type: str,
    severity: str,
    affected_field: str | None,
    source_split: str | None,
    target_split: str | None,
) -> dict[str, str]:
    if issue_type in {"duplicate_task_id", "duplicate_instance_id"}:
        return {
            "cluster_classification": "duplicate_id_leakage",
            "confidence": "high",
            "leakage_risk": "blocker",
            "classification_basis": "duplicate_id_across_splits",
            "readiness_gate": "must_fix_before_provider_pilot",
            "reason": "The same task or instance ID appears in more than one split.",
            "recommended_action": "Move duplicate IDs to one split or repair split manifests before any provider planning.",
        }
    if issue_type in {"provider_pilot_overlap", "clean_intervention_split_leakage"}:
        risk = "blocker" if issue_type == "provider_pilot_overlap" or _protected_split_pair(source_split, target_split) else "needs_review"
        return {
            "cluster_classification": "true_split_leakage" if risk == "blocker" else "split_metadata_issue",
            "confidence": "high" if risk == "blocker" else "medium",
            "leakage_risk": risk,
            "classification_basis": issue_type,
            "readiness_gate": "must_fix_before_provider_pilot" if risk == "blocker" else "manual_review_needed",
            "reason": "Split metadata links protected or paired examples in a way that may leak evaluation content.",
            "recommended_action": _fix(issue_type),
        }
    if issue_type == "answer_text_leakage":
        return {
            "cluster_classification": "answer_leakage",
            "confidence": "high",
            "leakage_risk": "blocker",
            "classification_basis": "expected_answer_visible",
            "readiness_gate": "must_fix_before_provider_pilot",
            "reason": "Expected answer text is visible in the prompt/context.",
            "recommended_action": _fix(issue_type),
        }
    if issue_type == "instruction_parameter_overlap":
        return {
            "cluster_classification": "instruction_parameter_overlap",
            "confidence": "medium",
            "leakage_risk": "false_positive_candidate",
            "classification_basis": "instruction_declared_parameter",
            "readiness_gate": "nice_to_have",
            "reason": _answer_leaf_reason(issue_type),
            "recommended_action": "No provider-pilot blocker: confirm the overlap is intentional task wording.",
        }
    if issue_type == "intervention_label_leakage":
        visible = affected_field in {"prompt", "visible_observation", "context"}
        return {
            "cluster_classification": "intervention_label_leakage",
            "confidence": "high" if visible else "medium",
            "leakage_risk": "blocker" if visible else "warning",
            "classification_basis": "intervention_label_visible" if visible else "intervention_label_metadata",
            "readiness_gate": "must_fix_before_provider_pilot" if visible else "must_fix_before_main_benchmark",
            "reason": "Intervention labels should not appear in user-facing fields.",
            "recommended_action": _fix(issue_type),
        }
    if issue_type == "hidden_metadata_visible":
        return {
            "cluster_classification": "hidden_metadata_visible",
            "confidence": "high",
            "leakage_risk": "blocker",
            "classification_basis": "hidden_marker_visible",
            "readiness_gate": "must_fix_before_provider_pilot",
            "reason": "Hidden metadata markers are visible to the agent.",
            "recommended_action": _fix(issue_type),
        }
    if issue_type == "identical_expected_output_unrelated_task":
        return {
            "cluster_classification": "needs_manual_review",
            "confidence": "medium",
            "leakage_risk": "warning",
            "classification_basis": "identical_expected_output",
            "readiness_gate": "must_fix_before_main_benchmark",
            "reason": "Unrelated tasks share an expected output; this may be valid but needs review.",
            "recommended_action": _fix(issue_type),
        }
    return {
        "cluster_classification": "needs_manual_review",
        "confidence": "low",
        "leakage_risk": "needs_review" if severity != "blocker" else "blocker",
        "classification_basis": "default_static_rule",
        "readiness_gate": _readiness_gate(issue_type, severity, source_split, target_split),
        "reason": "Static leakage heuristic requires manual review.",
        "recommended_action": _fix(issue_type),
    }


def _severity_from_risk(risk: str, fallback: str) -> str:
    if risk == "blocker":
        return "blocker"
    if risk in {"warning", "needs_review"}:
        return "warning"
    if risk in {"false_positive_candidate", "informational"}:
        return "informational"
    return fallback


def _fix(issue_type: str) -> str:
    fixes = {
        "duplicate_task_id": "Move duplicate task IDs to one split or revise split metadata.",
        "duplicate_instance_id": "Move duplicate instance IDs to one split or revise split metadata.",
        "clean_intervention_split_leakage": "Keep clean/intervention variants within the same approved split family.",
        "provider_pilot_overlap": "Remove provider-pilot instances from main/heldout split manifests.",
        "near_duplicate_prompt": "Rewrite or remove near-duplicate prompts across unrelated tasks.",
        "intervention_label_leakage": "Remove intervention labels from user-facing prompts/context.",
        "answer_text_leakage": "Remove direct answer leakage from the visible prompt/context.",
        "instruction_parameter_overlap": "Confirm task instruction overlap is intentional; no provider-pilot blocker.",
        "identical_expected_output_unrelated_task": "Review shared expected outputs and document whether they are intentional.",
        "hidden_metadata_visible": "Remove hidden metadata markers from user-facing observations/context.",
    }
    return fixes.get(issue_type, "Review static leakage finding.")


def _readiness_gate(issue_type: str, severity: str, source_split: str | None, target_split: str | None) -> str:
    if issue_type == "instruction_parameter_overlap":
        return "nice_to_have"
    if issue_type in {"answer_text_leakage", "intervention_label_leakage", "hidden_metadata_visible", "provider_pilot_overlap"}:
        return "must_fix_before_provider_pilot"
    if issue_type in {"duplicate_task_id", "duplicate_instance_id", "clean_intervention_split_leakage"}:
        return "must_fix_before_provider_pilot" if _protected_split_pair(source_split, target_split) else "must_fix_before_main_benchmark"
    if issue_type == "near_duplicate_prompt":
        return "must_fix_before_provider_pilot" if severity == "blocker" else "must_fix_before_main_benchmark"
    if severity == "blocker":
        return "must_fix_before_provider_pilot"
    return "must_fix_before_main_benchmark"


def _dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for item in findings:
        key = (
            item.get("finding_type") or item.get("issue_type"),
            item.get("dataset"),
            item.get("source_split"),
            item.get("target_split"),
            item.get("task_id") or item.get("instance_id") or item.get("entity_id"),
            item.get("pair_id"),
            item.get("affected_field"),
            _pattern_key(item),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _cluster_findings(findings: list[dict[str, Any]], *, max_examples: int = MAX_EXAMPLES_PER_CLUSTER) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in findings:
        key = (
            item.get("finding_type") or item.get("issue_type") or "unknown_needs_review",
            item.get("source_split") or "split_any",
            item.get("target_split") or "split_any",
            item.get("affected_field") or "field_any",
            item.get("cluster_classification") or "classification_any",
            _pattern_key(item),
            item.get("readiness_gate") or "must_fix_before_main_benchmark",
            item.get("recommended_fix") or "",
        )
        grouped[key].append(item)
    rows = [_root_cause(key, values, max_examples=max_examples) for key, values in grouped.items()]
    rows = sorted(
        rows,
        key=lambda row: (
            _gate_rank(row["readiness_gate"]),
            _risk_rank(row.get("leakage_risk")),
            _severity_rank(row["severity"]),
            -row["symptom_count"],
            row["root_cause_id"],
        ),
    )
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def _root_cause(key: tuple[Any, ...], findings: list[dict[str, Any]], *, max_examples: int) -> dict[str, Any]:
    finding_type = str(key[0])
    leakage_risk = _max_risk(findings)
    severity = _severity_from_risk(leakage_risk, _max_severity(findings))
    splits = sorted({split for item in findings for split in (item.get("source_split"), item.get("target_split")) if split})
    task_ids = sorted({item.get("task_id") for item in findings if item.get("task_id")})
    instance_ids = sorted({item.get("instance_id") for item in findings if item.get("instance_id")})
    fields = sorted({item.get("affected_field") for item in findings if item.get("affected_field")})
    gates = sorted({item.get("readiness_gate") for item in findings if item.get("readiness_gate")}, key=_gate_rank)
    cluster_classification = _mode([item.get("cluster_classification") for item in findings]) or "needs_manual_review"
    confidence = _max_confidence(findings)
    reason = _mode([item.get("reason") for item in findings]) or "Static leakage cluster requires review."
    recommended_action = _mode([item.get("recommended_action") for item in findings]) or _fix(finding_type)
    classification_basis = _mode([item.get("classification_basis") for item in findings]) or "clustered_static_heuristic"
    stable = hashlib.sha1("|".join(map(str, key)).encode("utf-8")).hexdigest()[:12]
    examples = [
        {
            "finding_id": item.get("finding_id") or item.get("issue_id"),
            "entity_id": item.get("entity_id"),
            "message": item.get("message"),
            "overlap_score": item.get("overlap_score"),
            "raw_overlap_score": item.get("raw_overlap_score"),
            "boilerplate_adjusted_overlap_score": item.get("boilerplate_adjusted_overlap_score"),
            "boilerplate_fraction": item.get("boilerplate_fraction"),
            "task_specific_overlap_score": item.get("task_specific_overlap_score"),
            "cluster_classification": item.get("cluster_classification"),
            "leakage_risk": item.get("leakage_risk"),
            "representative_snippet": item.get("representative_snippet"),
        }
        for item in findings[:max_examples]
    ]
    raw_scores = [item.get("raw_overlap_score") for item in findings if isinstance(item.get("raw_overlap_score"), (int, float))]
    adjusted_scores = [
        item.get("boilerplate_adjusted_overlap_score")
        for item in findings
        if isinstance(item.get("boilerplate_adjusted_overlap_score"), (int, float))
    ]
    boilerplate_fractions = [
        item.get("boilerplate_fraction") for item in findings if isinstance(item.get("boilerplate_fraction"), (int, float))
    ]
    return {
        "root_cause_id": f"leak_root_{stable}",
        "root_cause_title": _root_title(finding_type, splits, fields),
        "finding_type": finding_type,
        "symptom_count": len(findings),
        "severity": severity,
        "cluster_classification": cluster_classification,
        "confidence": confidence,
        "leakage_risk": leakage_risk,
        "reason": reason,
        "recommended_action": recommended_action,
        "classification_basis": classification_basis,
        "raw_overlap_score": max(raw_scores) if raw_scores else None,
        "boilerplate_adjusted_overlap_score": max(adjusted_scores) if adjusted_scores else None,
        "boilerplate_fraction": round(sum(boilerplate_fractions) / len(boilerplate_fractions), 4) if boilerplate_fractions else None,
        "representative_examples": examples,
        "affected_splits": splits,
        "affected_task_ids": task_ids[:50],
        "affected_instance_ids": instance_ids[:50],
        "affected_fields": fields,
        "suggested_fix": _fix(finding_type),
        "readiness_gate": gates[0] if gates else "must_fix_before_main_benchmark",
        "rank": 0,
        "raw_finding_ids": [item.get("finding_id") or item.get("issue_id") for item in findings],
    }


def _root_title(finding_type: str, splits: list[str], fields: list[str]) -> str:
    title = finding_type.replace("_", " ")
    if splits:
        title += " across " + " / ".join(splits[:3])
    if fields:
        title += " in " + ", ".join(fields[:3])
    return title


def _pattern_key(item: dict[str, Any]) -> str:
    finding_type = str(item.get("finding_type") or item.get("issue_type") or "")
    if finding_type == "near_duplicate_prompt":
        if item.get("leakage_risk") == "false_positive_candidate":
            pattern = "|".join(
                [
                    str(item.get("cluster_classification") or ""),
                    str(item.get("classification_basis") or ""),
                    str(item.get("source_split") or ""),
                    str(item.get("target_split") or ""),
                ]
            )
        elif item.get("leakage_risk") == "needs_review":
            pattern = "|".join(
                [
                    str(item.get("cluster_classification") or ""),
                    str(item.get("classification_basis") or ""),
                    str(item.get("source_split") or ""),
                    str(item.get("target_split") or ""),
                    str(item.get("representative_snippet") or ""),
                ]
            )
        else:
            pattern = str(item.get("representative_snippet") or item.get("message") or item.get("pair_id") or "")
        return hashlib.sha1(_normalize_text(pattern).encode("utf-8")).hexdigest()[:12]
    if finding_type == "answer_text_leakage":
        return hashlib.sha1(str(item.get("representative_snippet") or item.get("message") or "").lower().encode("utf-8")).hexdigest()[:12]
    if finding_type == "intervention_label_leakage":
        return str(item.get("representative_snippet") or "intervention_label").lower()
    if "duplicate" in finding_type or "split" in finding_type or "overlap" in finding_type:
        return finding_type
    return hashlib.sha1(str(item.get("message") or "").encode("utf-8")).hexdigest()[:12]


def _normalize_pair(pair: str) -> str:
    parts = sorted(part for part in pair.split("::") if part)
    return "::".join(parts)


def _normalize_text(text: str) -> str:
    return " ".join(TOKEN_RE.findall(str(text).lower()))


def _manual_review_queue(root_causes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in root_causes
        if row.get("leakage_risk") == "needs_review"
        or row.get("cluster_classification") in {"needs_manual_review", "split_metadata_issue"}
    ][:50]


def _false_positive_candidates(root_causes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in root_causes
        if row.get("leakage_risk") == "false_positive_candidate"
        or row.get("cluster_classification") in FALSE_POSITIVE_CLASSES
    ][:50]


def _top_true_leakage_clusters(root_causes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in root_causes
        if row.get("leakage_risk") == "blocker"
        and row.get("cluster_classification") in TRUE_LEAKAGE_CLASSES
    ][:50]


def _classification_counts(root_causes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in root_causes:
        name = str(row.get("cluster_classification") or "needs_manual_review")
        counts[name] = counts.get(name, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _max_severity(findings: list[dict[str, Any]]) -> str:
    return min((item.get("severity", "warning") for item in findings), key=_severity_rank)


def _max_risk(findings: list[dict[str, Any]]) -> str:
    return min((str(item.get("leakage_risk") or "warning") for item in findings), key=_risk_rank)


def _max_confidence(findings: list[dict[str, Any]]) -> str:
    return min((str(item.get("confidence") or "low") for item in findings), key=_confidence_rank)


def _mode(values: list[Any]) -> Any:
    counts: dict[Any, int] = {}
    for value in values:
        if value is None:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return None
    return sorted(counts.items(), key=lambda row: (-row[1], str(row[0])))[0][0]


def _severity_rank(severity: str) -> int:
    return {"blocker": 0, "warning": 1, "needs_review": 2, "informational": 3}.get(str(severity), 4)


def _risk_rank(risk: str | None) -> int:
    return {
        "blocker": 0,
        "needs_review": 1,
        "warning": 2,
        "false_positive_candidate": 3,
        "informational": 4,
    }.get(str(risk), 5)


def _confidence_rank(confidence: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(str(confidence), 3)


def _gate_rank(gate: str) -> int:
    ranks = {
        "must_fix_before_provider_pilot": 0,
        "must_fix_before_main_benchmark": 1,
        "must_fix_before_public_release": 2,
        "manual_review_needed": 3,
        "nice_to_have": 4,
    }
    return ranks.get(str(gate), 5)


def _safe_snippet(text: str) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= 60:
        return cleaned
    return cleaned[:57] + "..."


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
