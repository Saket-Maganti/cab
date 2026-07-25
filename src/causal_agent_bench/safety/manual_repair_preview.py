"""Reviewer-facing manual repair preview for content/split leakage operations.

The leakage patch applier only applies deterministic ID renames. Operations
that need manual review — `remove_prompt_answer_leakage`,
`update_split_assignment`, `correct_split_metadata`, and
`mark_false_positive` — never get applied automatically. But reviewers still
need a concise, actionable preview so they can decide what to rewrite, move,
or document.

This module reads the proposed patch manifest and produces:
- A grouped Markdown checklist per repair type
- A JSON payload with the same data for downstream tooling
- A blank reviewer worksheet that the human can annotate

It does *not* run anything, modify any file, or approve any operation.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

MANUAL_TYPES = {
    "remove_prompt_answer_leakage": {
        "title": "Answer Leakage — Manual Prompt Rewrite Required",
        "summary": (
            "Each operation corresponds to a cluster where the expected answer text "
            "appears in a visible prompt/context field. Rewrite the prompt so the "
            "answer is not visible. Do not auto-apply."
        ),
        "checklist": [
            "Locate the instance file and field listed in details.",
            "Confirm the leaked text really equals the expected answer (do not paraphrase blindly).",
            "Rewrite the prompt/context to remove the leaked snippet while preserving task intent.",
            "Re-run `all-no-run-reports` to confirm the cluster disappears.",
            "Record the change with a brief reviewer note (who/why/when).",
        ],
        "gate": "must_fix_before_provider_pilot",
    },
    "update_split_assignment": {
        "title": "True Split Leakage — Manual Split Move Required",
        "summary": (
            "Each operation corresponds to a cluster where unlinked examples cross "
            "protected split boundaries with high task-specific overlap. Move, rewrite, "
            "or remove one side. Do not auto-apply."
        ),
        "checklist": [
            "Inspect the affected instance IDs on both sides of the protected boundary.",
            "Decide whether to remove one side, rewrite the prompt, or relabel the split.",
            "Update the splits.json file manually if needed.",
            "Re-run `all-no-run-reports`.",
        ],
        "gate": "must_fix_before_provider_pilot",
    },
    "correct_split_metadata": {
        "title": "Split Metadata Issue — Manual Metadata Fix Required",
        "summary": (
            "Each operation corresponds to a cluster where split metadata is missing, "
            "ambiguous, or inconsistent with pair linkage."
        ),
        "checklist": [
            "Locate the affected instance/task in instances.jsonl and splits.json.",
            "Add the missing split label or correct the pair linkage.",
            "Re-run `all-no-run-reports`.",
        ],
        "gate": "must_fix_before_provider_pilot",
    },
    "mark_false_positive": {
        "title": "False-Positive Cluster — Documented Suppression Required",
        "summary": (
            "Each operation corresponds to a cluster that looks like template/tool/system "
            "boilerplate. If reviewed and confirmed false-positive, document it in "
            "configs/static_leakage_suppressions.yaml. Never use suppressions to hide "
            "answer-leakage, duplicate-ID, hidden-metadata, or intervention-label clusters."
        ),
        "checklist": [
            "Open one representative example for the cluster.",
            "Confirm the overlap is genuinely shared scaffolding, not real leakage.",
            "Add a reviewed entry to configs/static_leakage_suppressions.yaml with reviewer/reason/scope/date.",
            "Re-run `leakage-suppression-registry` to validate the entry.",
        ],
        "gate": "nice_to_have",
    },
    "review_family_overlap": {
        "title": "Same-Family Protected-Split Overlap — Reviewer Decision Required",
        "summary": (
            "Different tasks in the same task family share scaffolding across a protected split "
            "(e.g., research_assistant_hard_003 in heldout vs research_assistant_hard_025 in pilot). "
            "Likely template overlap, but review is required before main benchmark."
        ),
        "checklist": [
            "Sample 2–3 representative pairs per family.",
            "Confirm overlap is scaffolding (greetings, tool descriptions, system instructions), not specific content.",
            "If scaffolding, document via the suppression registry with scope=static_leakage_template_reuse.",
            "If scaffolding is fine but heldout-specific content is too close to pilot content, rewrite the heldout side or remove the heldout task.",
            "Re-run `all-no-run-reports` and confirm the cluster moves to suppressed or disappears.",
        ],
        "gate": "must_fix_before_main_benchmark",
    },
    "manual_review_required": {
        "title": "Generic Manual-Review Cluster",
        "summary": "Cluster cannot be classified automatically. Inspect representative examples and decide.",
        "checklist": [
            "Read the representative_examples in the cluster.",
            "Decide whether this is leakage, boilerplate, or noise.",
            "Reclassify (rewrite/move/suppress/leave) accordingly.",
        ],
        "gate": "manual_review_needed",
    },
}


def build_manual_repair_preview(
    repo_root: str | Path,
    *,
    manifest_path: str | Path,
    output_dir: str | Path = "reports/manual_repair_preview",
) -> dict[str, Any]:
    """Generate a manual-repair preview report from a proposed patch manifest."""

    root = Path(repo_root).resolve()
    manifest = Path(manifest_path)
    if not manifest.is_absolute():
        manifest = root / manifest
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)

    payload = _read_json(manifest) or {}
    operations_raw = payload.get("operations")
    operations = operations_raw if isinstance(operations_raw, list) else []

    groups: dict[str, list[dict[str, Any]]] = {key: [] for key in MANUAL_TYPES}
    other: list[dict[str, Any]] = []
    for op in operations:
        if not isinstance(op, dict):
            continue
        op_type = str(op.get("type") or "")
        if op_type == "rename_instance_id":
            # The applier handles these; not part of the manual preview.
            continue
        if op_type in groups:
            groups[op_type].append(_simplify(op))
        else:
            other.append(_simplify(op))

    summary = {
        "manifest_path": str(manifest),
        "operation_count": sum(len(rows) for rows in groups.values()) + len(other),
        "by_type": {key: len(rows) for key, rows in groups.items()},
        "unclassified_count": len(other),
    }
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Reviewer-facing manual repair preview only. No content, splits, or metadata "
            "are modified. Apply mode is not exposed here; content/split changes remain "
            "manual."
        ),
        "summary": summary,
        "groups": {key: groups[key] for key in MANUAL_TYPES},
        "unclassified_operations": other,
        "verdicts": {
            "auto_apply_attempted": False,
            "manual_review_required": True,
            "patches_applied": False,
        },
    }
    md = manual_repair_preview_markdown(report)
    md_path, json_path = write_dual_report(
        stem="manual_repair_preview",
        payload=report,
        markdown=md,
        output_dir=out,
    )
    report["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def manual_repair_preview_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Manual Repair Preview",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Manifest: `{summary['manifest_path']}`",
                f"- Manual operations total: {summary['operation_count']}",
                *[f"- `{name}`: {count}" for name, count in sorted(summary["by_type"].items())],
                f"- Unclassified manual operations: {summary['unclassified_count']}",
            ],
        ),
    ]
    for key, definition in MANUAL_TYPES.items():
        rows = payload["groups"].get(key) or []
        lines.extend(["", f"## {definition['title']}", ""])
        lines.append(definition["summary"])
        lines.extend(["", "**Checklist:**", ""])
        for step in definition["checklist"]:
            lines.append(f"- [ ] {step}")
        lines.extend(["", f"Operations (gate: `{definition['gate']}`):", ""])
        if not rows:
            lines.append("- (none)")
        for op in rows[:30]:
            details = op.get("details") or {}
            lines.append(
                f"- `{op['operation_id']}` cluster=`{op.get('cluster_id', '?')}` "
                f"class=`{op.get('classification', '?')}` -> {op.get('reason', '')}"
            )
            if key == "remove_prompt_answer_leakage":
                lines.append(
                    f"  - Instance: `{details.get('instance_id')}` field=`{details.get('field')}` "
                    f"leaked_hash=`{details.get('leaked_text_hash')}`"
                )
            elif key in {"update_split_assignment", "correct_split_metadata"}:
                lines.append(
                    f"  - Instance: `{details.get('instance_id')}` from=`{details.get('from_split')}` "
                    f"to=`{details.get('to_split')}`"
                )
            elif key == "mark_false_positive":
                lines.append(
                    f"  - Cluster classification=`{details.get('classification')}`"
                )
        if len(rows) > 30:
            lines.append(f"- ... {len(rows) - 30} more (see JSON).")
    if payload["unclassified_operations"]:
        lines.extend(["", "## Other Manual Operations", ""])
        for op in payload["unclassified_operations"][:20]:
            lines.append(f"- `{op['operation_id']}` type=`{op.get('type')}` -> {op.get('reason', '')}")
        if len(payload["unclassified_operations"]) > 20:
            lines.append(f"- ... {len(payload['unclassified_operations']) - 20} more (see JSON).")
    lines.append("")
    return "\n".join(lines)


def _simplify(op: dict[str, Any]) -> dict[str, Any]:
    return {
        "operation_id": str(op.get("operation_id") or ""),
        "type": str(op.get("type") or ""),
        "classification": str(op.get("classification") or ""),
        "leakage_risk": str(op.get("leakage_risk") or ""),
        "cluster_id": str(op.get("cluster_id") or ""),
        "reason": str(op.get("reason") or ""),
        "affected_files": list(op.get("affected_files") or []),
        "details": op.get("details") if isinstance(op.get("details"), dict) else {},
        "requires_manual_review": bool(op.get("requires_manual_review", True)),
        "safe_to_auto_patch": bool(op.get("safe_to_auto_patch", False)),
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
