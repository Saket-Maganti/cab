"""No-run leakage repair planning and patch-manifest validation."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

TARGET_CLASSIFICATIONS = {
    "duplicate_id_leakage",
    "true_split_leakage",
    "answer_leakage",
    "split_metadata_issue",
    "needs_manual_review",
    "same_family_protected_split_overlap",
}
FALSE_POSITIVE_CLASSIFICATIONS = {
    "likely_template_reuse",
    "clean_intervention_pair_similarity",
    "task_family_boilerplate",
    "shared_tool_description",
    "shared_system_instruction",
    "expected_subset_overlap",
}
PILOT_SPLITS = {"pilot", "pilot_20", "pilot_100", "provider_pilot"}
MAIN_OR_HELDOUT_SPLITS = {"main", "heldout", "heldout_templates", "test"}
PATCH_TYPES_REQUIRING_MANUAL_REVIEW = {
    "remove_prompt_answer_leakage",
    "update_split_assignment",
    "correct_split_metadata",
}


def build_leakage_repair_plan(
    repo_root: str | Path,
    *,
    input_dir: str | Path,
    output_dir: str | Path = "reports/leakage_repair_plan",
) -> dict[str, Any]:
    """Build a no-run repair plan from clustered static leakage reports."""

    root = Path(repo_root).resolve()
    reports_dir = Path(input_dir)
    if not reports_dir.is_absolute():
        reports_dir = root / reports_dir
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    static_payload = _read_named_report(reports_dir, "static_leakage_report.json") or {}
    triage_payload = _read_named_report(reports_dir, "dataset_issue_triage.json") or {}
    repair_payload = _read_named_report(reports_dir, "repair_plan.json") or {}
    manifest_payload = _read_named_report(reports_dir, "benchmark_manifest.json") or {}

    clusters = _cluster_rows(static_payload)
    repair_items = [_repair_item(row) for row in clusters]
    repair_items = sorted(repair_items, key=_repair_sort_key)
    for rank, item in enumerate(repair_items, start=1):
        item["rank"] = rank
    _enrich_repair_items_with_locations(root, repair_items)

    patch_manifest = _build_patch_manifest(root, out, repair_items)
    patch_md = patch_manifest_markdown(patch_manifest)
    out.mkdir(parents=True, exist_ok=True)
    patch_json_path = out / "proposed_patch_manifest.json"
    patch_md_path = out / "proposed_patch_manifest.md"
    patch_json_path.write_text(json.dumps(patch_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    patch_md_path.write_text(patch_md, encoding="utf-8")

    summary = {
        "cluster_count": len(repair_items),
        "must_fix_before_provider_pilot_count": sum(
            1 for item in repair_items if item["readiness_gate"] == "must_fix_before_provider_pilot"
        ),
        "candidate_auto_patch_count": patch_manifest["summary"]["candidate_auto_patch_count"],
        "manual_review_count": patch_manifest["summary"]["manual_review_count"],
        "false_positive_candidate_count": sum(
            1 for item in repair_items if item["classification"] in FALSE_POSITIVE_CLASSIFICATIONS
        ),
        "unsafe_operation_count": patch_manifest["summary"]["unsafe_operation_count"],
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "No-run leakage repair planning only; proposed patches are not applied.",
        "input_dir": str(reports_dir),
        "source_reports": {
            "static_leakage_report": bool(static_payload),
            "dataset_issue_triage": bool(triage_payload),
            "repair_plan": bool(repair_payload),
            "benchmark_manifest": bool(manifest_payload),
        },
        "summary": summary,
        "top_10_must_fix_before_provider_pilot": [
            item for item in repair_items if item["readiness_gate"] == "must_fix_before_provider_pilot"
        ][:10],
        "top_10_must_fix_before_main_benchmark": [
            item for item in repair_items if item["readiness_gate"] == "must_fix_before_main_benchmark"
        ][:10],
        "top_answer_leakage_repairs": [
            item for item in repair_items if item["classification"] == "answer_leakage"
        ][:10],
        "top_duplicate_id_repairs": [
            item for item in repair_items if item["classification"] == "duplicate_id_leakage"
        ][:10],
        "top_split_metadata_repairs": [
            item for item in repair_items if item["classification"] == "split_metadata_issue"
        ][:10],
        "manual_review_queue": [
            item for item in repair_items if item["requires_manual_review"]
        ][:50],
        "false_positive_suppression_candidates": [
            item for item in repair_items if item["classification"] in FALSE_POSITIVE_CLASSIFICATIONS
        ][:50],
        "repair_items": repair_items,
        "patch_manifest_paths": {
            "json": str(patch_json_path),
            "markdown": str(patch_md_path),
        },
    }
    md = leakage_repair_plan_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="leakage_repair_plan",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def validate_leakage_patch_manifest(
    repo_root: str | Path,
    *,
    manifest_path: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a proposed leakage patch manifest without applying it."""

    root = Path(repo_root).resolve()
    manifest = Path(manifest_path)
    if not manifest.is_absolute():
        manifest = root / manifest
    out = Path(output_dir) if output_dir else manifest.parent
    if not out.is_absolute():
        out = root / out

    checks: list[dict[str, Any]] = []
    payload = _read_json(manifest)
    if not isinstance(payload, dict):
        _add_check(checks, "blocker", "manifest_not_parseable", str(manifest), "Manifest JSON is missing or not parseable.")
        payload = {}
    operations = payload.get("operations") if isinstance(payload.get("operations"), list) else []
    if not operations:
        _add_check(checks, "warning", "no_operations", str(manifest), "Manifest contains no operations.")

    new_ids: dict[str, str] = {}
    for op in operations:
        if not isinstance(op, dict):
            _add_check(checks, "blocker", "operation_not_object", str(manifest), "Patch operation is not an object.")
            continue
        op_id = str(op.get("operation_id") or op.get("type") or "operation")
        op_type = str(op.get("type") or "")
        details = op.get("details") if isinstance(op.get("details"), dict) else {}
        new_id = details.get("new_id")
        if op_type == "rename_instance_id" and new_id:
            if str(new_id) in new_ids:
                _add_check(checks, "blocker", "duplicate_proposed_new_id", op_id, f"New ID `{new_id}` is proposed more than once.")
            new_ids[str(new_id)] = op_id
        for affected in op.get("affected_files") or []:
            affected_path = Path(str(affected))
            display = str(affected_path)
            if _touches_results(display):
                _add_check(checks, "blocker", "touches_results", op_id, f"Operation touches forbidden results path: {display}")
            if _touches_paper_claims(display):
                _add_check(checks, "blocker", "touches_paper_claims", op_id, f"Operation touches paper/claim evidence path: {display}")
            full_path = affected_path if affected_path.is_absolute() else root / affected_path
            if not full_path.exists():
                _add_check(checks, "warning", "affected_file_missing", op_id, f"Affected file does not exist: {display}")
        if _contains_true_marker(op, "allow_paid_calls"):
            _add_check(checks, "blocker", "enables_paid_calls", op_id, "Operation would set allow_paid_calls=true.")
        if _contains_true_marker(op, "scientific_evidence"):
            _add_check(checks, "blocker", "promotes_scientific_evidence", op_id, "Operation would set scientific_evidence=true.")
        if op_type in PATCH_TYPES_REQUIRING_MANUAL_REVIEW and not op.get("requires_manual_review", True):
            _add_check(checks, "blocker", "manual_review_required", op_id, f"{op_type} must require manual review.")
        if op_type == "remove_prompt_answer_leakage" and op.get("safe_to_auto_patch") is True:
            _add_check(checks, "blocker", "content_patch_auto_enabled", op_id, "Prompt/content edits must not be auto-patchable.")
        if op_type in {"update_split_assignment", "correct_split_metadata"} and op.get("safe_to_auto_patch") is True:
            _add_check(checks, "blocker", "split_patch_auto_enabled", op_id, "Split repairs must not be auto-patchable in this phase.")

    blockers = [check for check in checks if check["severity"] == "blocker"]
    warnings = [check for check in checks if check["severity"] == "warning"]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "No-run patch-manifest validation only; no patches are applied.",
        "manifest_path": str(manifest),
        "summary": {
            "operation_count": len(operations),
            "blockers": len(blockers),
            "warnings": len(warnings),
            "candidate_auto_patch_count": sum(1 for op in operations if isinstance(op, dict) and op.get("candidate_auto_patch")),
            "manual_review_count": sum(1 for op in operations if isinstance(op, dict) and op.get("requires_manual_review")),
        },
        "verdicts": {
            "manifest_valid": not blockers,
            "patches_applied": False,
        },
        "checks": checks,
    }
    md = leakage_patch_validation_markdown(report)
    md_path, json_path = write_dual_report(
        stem="leakage_patch_validation",
        payload=report,
        markdown=md,
        output_dir=out,
    )
    report["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def leakage_repair_plan_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Leakage Repair Plan",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Repair clusters: {summary['cluster_count']}",
                f"- Must fix before provider pilot: {summary['must_fix_before_provider_pilot_count']}",
                f"- Candidate auto-patch operations: {summary['candidate_auto_patch_count']}",
                f"- Manual-review operations: {summary['manual_review_count']}",
                f"- False-positive candidates: {summary['false_positive_candidate_count']}",
                f"- Unsafe operations: {summary['unsafe_operation_count']}",
            ],
        ),
    ]
    for title, key in (
        ("Top 10 Must-Fix Before Provider Pilot", "top_10_must_fix_before_provider_pilot"),
        ("Top 10 Must-Fix Before Main Benchmark", "top_10_must_fix_before_main_benchmark"),
        ("Top Answer-Leakage Repairs", "top_answer_leakage_repairs"),
        ("Top Duplicate-ID Repairs", "top_duplicate_id_repairs"),
        ("Top Split-Metadata Repairs", "top_split_metadata_repairs"),
        ("Manual Review Queue", "manual_review_queue"),
        ("False-Positive Suppression Candidates", "false_positive_suppression_candidates"),
    ):
        lines.extend(["", f"## {title}", ""])
        rows = payload.get(key) or []
        if not rows:
            lines.append("- (none)")
            continue
        for item in rows[:10]:
            lines.append(
                f"- rank {item['rank']} `{item['cluster_id']}` [{item['classification']}/{item['leakage_risk']}] "
                f"{item['likely_root_cause']} ({item['symptom_count']} symptoms) -> {item['repair_strategy']}"
            )
            lines.append(f"  - Affected IDs: {', '.join(item['exact_affected_ids'][:8]) or '(none)'}")
            lines.append(f"  - Rerun: `{item['rerun_report_after_repair']}`")
    lines.extend(
        [
            "",
            "## Patch Manifest",
            "",
            f"- JSON: `{payload['patch_manifest_paths']['json']}`",
            f"- Markdown: `{payload['patch_manifest_paths']['markdown']}`",
            "",
            "Proposed operations are not applied by this report.",
            "",
        ]
    )
    return "\n".join(lines)


def patch_manifest_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Proposed Leakage Patch Manifest",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Operations: {summary['operation_count']}",
                f"- Candidate auto-patch operations: {summary['candidate_auto_patch_count']}",
                f"- Manual-review operations: {summary['manual_review_count']}",
                f"- Unsafe operations: {summary['unsafe_operation_count']}",
            ],
        ),
        "## Operations",
        "",
    ]
    if not payload.get("operations"):
        lines.append("- (none)")
    for op in payload.get("operations", [])[:100]:
        lines.append(
            f"- `{op['operation_id']}` `{op['type']}` "
            f"manual_review={op['requires_manual_review']} candidate_auto_patch={op['candidate_auto_patch']}: {op['reason']}"
        )
    lines.append("")
    return "\n".join(lines)


def leakage_patch_validation_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Leakage Patch Manifest Validation",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Operations: {summary['operation_count']}",
                f"- Blockers: {summary['blockers']}",
                f"- Warnings: {summary['warnings']}",
                f"- Manifest valid: `{payload['verdicts']['manifest_valid']}`",
                "- Patches applied: `False`",
            ],
        ),
        "## Checks",
        "",
    ]
    if not payload.get("checks"):
        lines.append("- (none)")
    for check in payload.get("checks", []):
        lines.append(f"- `{check['severity']}` `{check['id']}` `{check['target']}`: {check['message']}")
    lines.append("")
    return "\n".join(lines)


def _cluster_rows(static_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = static_payload.get("root_causes") or static_payload.get("root_cause_summary") or static_payload.get("top_clusters") or []
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        classification = str(row.get("cluster_classification") or "needs_manual_review")
        if classification in TARGET_CLASSIFICATIONS or classification in FALSE_POSITIVE_CLASSIFICATIONS:
            out.append(row)
    return out


def _repair_item(row: dict[str, Any]) -> dict[str, Any]:
    classification = str(row.get("cluster_classification") or "needs_manual_review")
    leakage_risk = str(row.get("leakage_risk") or row.get("severity") or "needs_review")
    patch_type = _patch_type(classification)
    affected_ids = _affected_ids(row)
    requires_manual = patch_type != "rename_duplicate_ids"
    safe_auto = patch_type == "rename_duplicate_ids" and bool(affected_ids)
    gate = _readiness_gate(row, classification, leakage_risk)
    return {
        "cluster_id": str(row.get("root_cause_id") or row.get("cluster_id") or _stable_id(row)),
        "classification": classification,
        "leakage_risk": leakage_risk,
        "symptom_count": int(row.get("symptom_count") or 1),
        "affected_task_ids": list(row.get("affected_task_ids") or [])[:50],
        "affected_instance_ids": list(row.get("affected_instance_ids") or [])[:50],
        "affected_splits": list(row.get("affected_splits") or [])[:20],
        "representative_examples": list(row.get("representative_examples") or [])[:5],
        "likely_root_cause": _likely_root_cause(row, classification),
        "repair_strategy": _repair_strategy(row, classification),
        "confidence": str(row.get("confidence") or "medium"),
        "requires_manual_review": requires_manual or leakage_risk in {"needs_review", "warning"},
        "safe_to_auto_patch": safe_auto and leakage_risk == "blocker",
        "proposed_patch_type": patch_type,
        "readiness_gate": gate,
        "why_it_matters": _why_it_matters(classification),
        "exact_affected_ids": affected_ids[:25],
        "suggested_safe_repair": _repair_strategy(row, classification),
        "rerun_report_after_repair": "python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_leakage_repair_rerun",
        "raw_finding_ids": list(row.get("raw_finding_ids") or [])[:100],
    }


def _build_patch_manifest(root: Path, out: Path, repair_items: list[dict[str, Any]]) -> dict[str, Any]:
    operations = []
    proposed_new_ids: set[str] = set()
    for item in repair_items:
        operations.extend(_operations_for_item(root, item, proposed_new_ids))
    summary = {
        "operation_count": len(operations),
        "candidate_auto_patch_count": sum(1 for op in operations if op["candidate_auto_patch"]),
        "manual_review_count": sum(1 for op in operations if op["requires_manual_review"]),
        "unsafe_operation_count": sum(1 for op in operations if op.get("unsafe")),
    }
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Proposed patch manifest only; no dataset files are modified automatically.",
        "manifest_version": 1,
        "output_dir": str(out),
        "summary": summary,
        "operations": operations,
    }


def _operations_for_item(root: Path, item: dict[str, Any], proposed_new_ids: set[str]) -> list[dict[str, Any]]:
    cluster_id = item["cluster_id"]
    patch_type = item["proposed_patch_type"]
    if patch_type == "rename_duplicate_ids":
        out = []
        for old_id in item["exact_affected_ids"][:10]:
            new_id = _dedupe_id(old_id)
            conflict_free = new_id not in proposed_new_ids and new_id not in item["exact_affected_ids"]
            proposed_new_ids.add(new_id)
            out.append(
                _operation(
                    cluster_id,
                    "rename_instance_id",
                    item,
                    reason="Duplicate ID leakage should be repaired with deterministic, reviewed ID changes.",
                    affected_files=_dataset_files_for_id(root, old_id),
                    details={"old_id": old_id, "new_id": new_id},
                    candidate_auto_patch=conflict_free,
                    requires_manual_review=not conflict_free,
                    safe_to_auto_patch=conflict_free,
                )
            )
        return out or [_manual_operation(cluster_id, item, "No affected ID was available for deterministic rename planning.")]
    if patch_type == "remove_answer_from_prompt":
        snippet = _first_snippet(item)
        return [
            _operation(
                cluster_id,
                "remove_prompt_answer_leakage",
                item,
                reason="Prompt/context appears to contain answer text; rewrite requires human review.",
                affected_files=list(item.get("dataset_files") or []),
                details={
                    "instance_id": _first_id(item),
                    "field": "prompt",
                    "leaked_text_hash": _hash_text(snippet),
                    "leak_description": item.get("representative_leak_snippet"),
                    "rewrite_recommendation": (
                        "Rewrite the prompt/context so the gold answer text no longer appears, "
                        "then re-run static-leakage-check to confirm the cluster clears. "
                        "Do not change hidden_ground_truth or success_criteria."
                    ),
                    "verify_after": "remove_prompt_answer_leakage",
                },
                requires_manual_review=True,
            )
        ]
    if patch_type in {"move_split_assignment", "correct_split_metadata"}:
        return [
            _operation(
                cluster_id,
                "update_split_assignment" if patch_type == "move_split_assignment" else "correct_split_metadata",
                item,
                reason="Split assignment/metadata repairs require human review before data movement.",
                affected_files=list(item.get("dataset_files") or []),
                details={
                    "instance_id": _first_id(item),
                    "from_split": item["affected_splits"][0] if item["affected_splits"] else None,
                    "to_split": "manual_review_target_split",
                },
                requires_manual_review=True,
            )
        ]
    if patch_type == "suppress_false_positive":
        return [
            _operation(
                cluster_id,
                "mark_false_positive",
                item,
                reason="Cluster appears to be template/tool/pair similarity and should be considered for suppression.",
                affected_files=[],
                details={"cluster_id": cluster_id, "classification": item["classification"]},
                requires_manual_review=True,
            )
        ]
    if patch_type == "review_family_overlap_or_suppress":
        return [
            _operation(
                cluster_id,
                "review_family_overlap",
                item,
                reason=(
                    "Same-task-family overlap across a protected split. Inspect representatives and either "
                    "document via suppression registry or rewrite one side before the main benchmark."
                ),
                affected_files=[],
                details={"cluster_id": cluster_id, "classification": item["classification"]},
                requires_manual_review=True,
            )
        ]
    return [_manual_operation(cluster_id, item, "Manual review is required before choosing a repair operation.")]


def _operation(
    cluster_id: str,
    op_type: str,
    item: dict[str, Any],
    *,
    reason: str,
    affected_files: list[str],
    details: dict[str, Any],
    candidate_auto_patch: bool = False,
    requires_manual_review: bool = True,
    safe_to_auto_patch: bool = False,
) -> dict[str, Any]:
    stable = hashlib.sha1(f"{cluster_id}|{op_type}|{json.dumps(details, sort_keys=True)}".encode()).hexdigest()[:12]
    return {
        "operation_id": f"leak_patch_{stable}",
        "cluster_id": cluster_id,
        "type": op_type,
        "reason": reason,
        "classification": item["classification"],
        "leakage_risk": item["leakage_risk"],
        "affected_files": affected_files,
        "details": details,
        "candidate_auto_patch": bool(candidate_auto_patch),
        "requires_manual_review": bool(requires_manual_review),
        "safe_to_auto_patch": bool(safe_to_auto_patch),
        "unsafe": False,
    }


def _manual_operation(cluster_id: str, item: dict[str, Any], reason: str) -> dict[str, Any]:
    return _operation(
        cluster_id,
        "manual_review_required",
        item,
        reason=reason,
        affected_files=[],
        details={"cluster_id": cluster_id},
        requires_manual_review=True,
    )


def _repair_sort_key(item: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        _classification_priority(item),
        0 if item["readiness_gate"] == "must_fix_before_provider_pilot" else 1,
        -int(item.get("symptom_count") or 1),
        item["cluster_id"],
    )


def _classification_priority(item: dict[str, Any]) -> int:
    classification = item["classification"]
    splits = {str(split) for split in item.get("affected_splits") or []}
    if classification == "duplicate_id_leakage":
        return 0
    if classification == "answer_leakage":
        return 1
    if classification == "true_split_leakage" and splits & PILOT_SPLITS:
        return 2
    if classification == "true_split_leakage":
        return 3
    if classification == "split_metadata_issue":
        return 4
    if classification == "needs_manual_review":
        return 5
    if classification in FALSE_POSITIVE_CLASSIFICATIONS:
        return 6
    return 7


def _readiness_gate(row: dict[str, Any], classification: str, leakage_risk: str) -> str:
    if classification in FALSE_POSITIVE_CLASSIFICATIONS:
        return "nice_to_have"
    gate = str(row.get("readiness_gate") or "")
    if gate:
        return gate
    if leakage_risk == "blocker":
        return "must_fix_before_provider_pilot"
    return "manual_review_needed"


def _patch_type(classification: str) -> str:
    mapping = {
        "duplicate_id_leakage": "rename_duplicate_ids",
        "answer_leakage": "remove_answer_from_prompt",
        "true_split_leakage": "move_split_assignment",
        "split_metadata_issue": "correct_split_metadata",
        "needs_manual_review": "manual_review_only",
        "same_family_protected_split_overlap": "review_family_overlap_or_suppress",
    }
    if classification in FALSE_POSITIVE_CLASSIFICATIONS:
        return "suppress_false_positive"
    return mapping.get(classification, "unknown")


def _likely_root_cause(row: dict[str, Any], classification: str) -> str:
    if classification == "duplicate_id_leakage":
        return "The same task or instance ID appears in multiple split manifests."
    if classification == "answer_leakage":
        return "Expected answer text appears in a visible prompt or context field."
    if classification == "true_split_leakage":
        return "Unrelated task families share high task-specific content across protected split boundaries."
    if classification == "split_metadata_issue":
        return "Split metadata is missing, ambiguous, or inconsistent with pair linkage."
    if classification == "same_family_protected_split_overlap":
        return (
            "Different tasks in the same task family share scaffolding across a protected split. "
            "Likely template overlap, but a reviewer must confirm."
        )
    if classification in FALSE_POSITIVE_CLASSIFICATIONS:
        return "Similarity is likely caused by expected template, tool, system, or pair-level reuse."
    return str(row.get("reason") or "Static leakage cluster needs manual review.")


def _repair_strategy(row: dict[str, Any], classification: str) -> str:
    if classification == "duplicate_id_leakage":
        return "Plan deterministic ID renames and update all dataset references after review."
    if classification == "answer_leakage":
        return "Manually rewrite prompt/context so the answer is not visible, then rerun leakage checks."
    if classification == "true_split_leakage":
        return "Manually move, rewrite, or remove one side of the protected split overlap."
    if classification == "split_metadata_issue":
        return "Correct split metadata or pair linkage before treating near-duplicate clusters as real leakage."
    if classification == "same_family_protected_split_overlap":
        return (
            "Inspect representative pairs. If overlap is shared family scaffolding, document via the suppression "
            "registry; otherwise treat as true leakage and move/rewrite one side before main benchmark planning."
        )
    if classification in FALSE_POSITIVE_CLASSIFICATIONS:
        return "Consider suppressing this cluster class after reviewing representative examples."
    return "Manually inspect representative examples and choose a repair."


def _why_it_matters(classification: str) -> str:
    if classification == "duplicate_id_leakage":
        return "Duplicate IDs make split boundaries and run attribution ambiguous."
    if classification == "answer_leakage":
        return "Visible answers can invalidate provider-pilot task behavior."
    if classification == "true_split_leakage":
        return "Protected split overlap can leak evaluation content into pilot or heldout analyses."
    if classification == "split_metadata_issue":
        return "Ambiguous split metadata prevents reliable leakage gating."
    if classification == "same_family_protected_split_overlap":
        return (
            "Same-family overlap is usually scaffolding, but if a heldout task is too close to a pilot task "
            "in the same family, evaluation results may not generalize."
        )
    if classification in FALSE_POSITIVE_CLASSIFICATIONS:
        return "False positives should be documented so reviewers focus on real blockers."
    return "Manual review is needed before provider spend."


def _affected_ids(row: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in ("affected_instance_ids", "affected_task_ids"):
        values = row.get(key) or []
        if isinstance(values, list):
            ids.extend(str(value) for value in values if value)
    for example in row.get("representative_examples") or []:
        if isinstance(example, dict):
            entity = example.get("entity_id")
            if entity:
                ids.extend(str(part) for part in str(entity).split("::") if part)
    return list(dict.fromkeys(ids))


def _first_id(item: dict[str, Any]) -> str | None:
    ids = item.get("exact_affected_ids") or item.get("affected_instance_ids") or item.get("affected_task_ids") or []
    return str(ids[0]) if ids else None


def _first_snippet(item: dict[str, Any]) -> str:
    for example in item.get("representative_examples") or []:
        if isinstance(example, dict) and example.get("representative_snippet"):
            return str(example["representative_snippet"])
    return item["cluster_id"]


def _dedupe_id(old_id: str) -> str:
    return f"{old_id}__dedupe_candidate"


def _dataset_files_for_id(root: Path, old_id: str) -> list[str]:
    files = []
    for path in sorted((root / "data").glob("**/*.json*")) if (root / "data").exists() else []:
        try:
            if old_id in path.read_text(encoding="utf-8"):
                files.append(_rel(path, root))
        except UnicodeDecodeError:
            continue
        if len(files) >= 10:
            break
    return files


# Locator classifications that benefit from a concrete "edit this file" pointer.
_LOCATABLE_CLASSIFICATIONS = frozenset(
    {
        "answer_leakage",
        "duplicate_id_leakage",
        "split_metadata_issue",
        "same_family_protected_split_overlap",
    }
)


def _locate_instances(root: Path, wanted_ids: set[str]) -> dict[str, list[str]]:
    """Map each wanted instance/base id to the dataset files that declare it.

    Single read-only pass over ``data/**/*.jsonl`` with a precise quoted-token
    match (``"id"``), preferring ``instances.jsonl``/``base_tasks.jsonl`` so the
    answer-leakage worksheet points a reviewer at the file to edit. Never
    modifies dataset files.
    """
    located: dict[str, list[str]] = {wid: [] for wid in wanted_ids}
    data = root / "data"
    if not wanted_ids or not data.exists():
        return located
    tokens = {wid: f'"{wid}"' for wid in wanted_ids}
    for path in sorted(data.glob("**/*.jsonl")):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = _rel(path, root)
        for wid, token in tokens.items():
            if token in text:
                located[wid].append(rel)
    for wid, files in located.items():
        preferred = [f for f in files if f.endswith(("instances.jsonl", "base_tasks.jsonl"))]
        located[wid] = (preferred or files)[:8]
    return located


def _representative_leak_snippet(item: dict[str, Any]) -> str | None:
    """Return a short, human-readable description of the leak for the worksheet.

    Uses the static-leakage example message (which already redacts to a short
    window such as "Expected answer text `2026-06-03` appears in ..."), capped
    so no large dataset content is reproduced in the report.
    """
    for example in item.get("representative_examples") or []:
        if isinstance(example, dict):
            message = example.get("message") or example.get("representative_snippet")
            if message:
                return str(message)[:240]
    return None


def _enrich_repair_items_with_locations(root: Path, repair_items: list[dict[str, Any]]) -> None:
    """Attach a dataset-file locator and a leak snippet to repair items.

    This makes the manual worksheet self-contained (which file to open, what the
    leak looks like) without applying any change. Only the first affected id per
    locatable cluster is resolved, so the single data pass stays cheap.
    """
    wanted: dict[str, str] = {}
    for item in repair_items:
        if item["classification"] not in _LOCATABLE_CLASSIFICATIONS:
            continue
        first = _first_id(item)
        if first:
            wanted[item["cluster_id"]] = first
    located = _locate_instances(root, set(wanted.values()))
    for item in repair_items:
        first = wanted.get(item["cluster_id"])
        item["dataset_files"] = located.get(first, []) if first else []
        snippet = _representative_leak_snippet(item)
        if snippet:
            item["representative_leak_snippet"] = snippet


def _read_named_report(reports_dir: Path, filename: str) -> dict[str, Any] | None:
    path = _find_report(reports_dir, filename)
    return _read_json(path) if path else None


def _find_report(reports_dir: Path, filename: str) -> Path | None:
    direct = reports_dir / filename
    if direct.exists():
        return direct
    matches = sorted(reports_dir.glob(f"**/{filename}")) if reports_dir.exists() else []
    return matches[0] if matches else None


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _hash_text(text: str) -> str:
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:12]


def _stable_id(row: dict[str, Any]) -> str:
    return "leak_cluster_" + _hash_text(json.dumps(row, sort_keys=True, default=str))


def _add_check(checks: list[dict[str, Any]], severity: str, check_id: str, target: str, message: str) -> None:
    checks.append({"severity": severity, "id": check_id, "target": target, "message": message})


def _touches_results(path: str) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    return normalized == "results" or normalized.startswith("results/") or "/results/" in normalized


def _touches_paper_claims(path: str) -> bool:
    normalized = path.replace("\\", "/").strip("/").lower()
    return normalized in {"docs/claim_ledger.json", "docs/claim_ledger_schema.json"} or "claim_evidence" in normalized


def _contains_true_marker(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if str(current_key) == key and current_value is True:
                return True
            if _contains_true_marker(current_value, key):
                return True
    if isinstance(value, list):
        return any(_contains_true_marker(item, key) for item in value)
    return False


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
