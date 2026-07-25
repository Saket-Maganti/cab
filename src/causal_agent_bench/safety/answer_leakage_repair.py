"""Answer-leakage repair worksheets and post-repair validation (no-run, no auto-apply)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report
from causal_agent_bench.safety.static_leakage import (
    _answer_leaves,
    _classify_answer_leaf_overlap,
    _expected_output,
    _task_from_row,
    _user_instruction_text,
    _visible_non_instruction_text,
    _visible_prompt,
)

PROMPT_FIELD_CANDIDATES = ("user_instruction", "prompt", "context", "visible_context")


def build_answer_leakage_repair_packet(
    repo_root: str | Path,
    *,
    leakage_report_path: str | Path | None = None,
    output_dir: str | Path = "reports/answer_leakage_repair",
) -> dict[str, Any]:
    """Build per-cluster answer-leakage checklists with before/after previews."""

    root = Path(repo_root).resolve()
    report_path = _resolve_leakage_report(root, leakage_report_path)
    payload = _read_json(report_path) or {}
    clusters = [
        row
        for row in payload.get("root_causes") or []
        if row.get("cluster_classification") == "answer_leakage" and row.get("leakage_risk") == "blocker"
    ]
    worksheets: list[dict[str, Any]] = []
    for cluster in clusters:
        worksheets.append(_worksheet_for_cluster(root, cluster))

    summary = {
        "leakage_report": str(report_path),
        "blocker_cluster_count": len(clusters),
        "worksheet_count": len(worksheets),
        "instances_with_locator": sum(1 for w in worksheets if w.get("field_locator")),
        "manual_review_required": True,
        "auto_apply": False,
    }
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Answer-leakage repair packet only. Shows before/after previews and suggested rewrites "
            "for true answer_leakage blocker clusters. Never modifies frozen data or applies patches."
        ),
        "summary": summary,
        "checklist": _global_checklist(),
        "worksheets": worksheets,
        "verdicts": {
            "provider_pilot_blocked_by_answer_leakage": len(worksheets) > 0,
            "safe_to_auto_apply": False,
        },
    }
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    md = answer_leakage_repair_markdown(report)
    md_path, json_path = write_dual_report(
        stem="answer_leakage_repair",
        payload=report,
        markdown=md,
        output_dir=out,
    )
    report["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def validate_answer_leakage_cleared(
    repo_root: str | Path,
    dataset_file: str | Path,
    *,
    instance_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Return whether gold-answer leaves still appear outside safe instruction overlap."""

    root = Path(repo_root).resolve()
    path = Path(dataset_file)
    if not path.is_absolute():
        path = root / path
    remaining: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        iid = str(row.get("instance_id") or "")
        if instance_ids and iid not in instance_ids:
            continue
        task = _task_from_row(row)
        instruction_lower = _user_instruction_text(row).lower()
        non_instruction_lower = _visible_non_instruction_text(row).lower()
        for leaf in _answer_leaves(_expected_output(task)):
            if len(leaf) < 4:
                continue
            issue_type, *_rest = _classify_answer_leaf_overlap(
                leaf,
                instruction_lower=instruction_lower,
                non_instruction_lower=non_instruction_lower,
            )
            if issue_type == "answer_text_leakage":
                remaining.append(
                    {
                        "instance_id": iid,
                        "leaf": leaf,
                        "field": _field_with_leaf(row, leaf),
                        "leaked_text_hash": _hash_text(leaf),
                    }
                )
                break
    return {
        "dataset_file": str(path),
        "instance_ids_filter": instance_ids,
        "remaining_blockers": len(remaining),
        "passed": len(remaining) == 0,
        "remaining": remaining,
    }


def answer_leakage_repair_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Answer Leakage Repair Packet",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Source leakage report: `{summary['leakage_report']}`",
                f"- Blocker clusters: {summary['blocker_cluster_count']}",
                f"- Worksheets: {summary['worksheet_count']}",
                f"- Auto-apply: `{payload['verdicts']['safe_to_auto_apply']}`",
            ],
        ),
        "## Global Checklist",
        "",
    ]
    for step in payload["checklist"]:
        lines.append(f"- [ ] {step}")
    lines.extend(["", "## Per-Cluster Worksheets", ""])
    if not payload["worksheets"]:
        lines.append("- (no true answer-leakage blocker clusters — provider pilot not blocked on this gate)")
    for sheet in payload["worksheets"][:30]:
        lines.extend(_worksheet_markdown(sheet))
    if len(payload["worksheets"]) > 30:
        lines.append(f"- ... {len(payload['worksheets']) - 30} more (see JSON).")
    lines.append("")
    return "\n".join(lines)


def _worksheet_for_cluster(root: Path, cluster: dict[str, Any]) -> dict[str, Any]:
    instance_ids = list(cluster.get("affected_instance_ids") or [])[:8]
    located = _locate_instances(root, set(instance_ids))
    previews: list[dict[str, Any]] = []
    for iid in instance_ids[:3]:
        files = located.get(iid) or []
        if not files:
            continue
        previews.append(_preview_instance(root, iid, files[0], cluster))
    return {
        "cluster_id": cluster.get("root_cause_id"),
        "classification": cluster.get("cluster_classification"),
        "symptom_count": cluster.get("symptom_count"),
        "manual_review_required": True,
        "affected_instance_ids": instance_ids,
        "field_locator": previews[0]["field_locator"] if previews else None,
        "leaked_text_hash": previews[0].get("leaked_text_hash") if previews else None,
        "before_after_previews": previews,
        "suggested_rewrite": previews[0].get("suggested_rewrite") if previews else None,
        "checklist": [
            "Confirm leaked token equals gold output (not a coincidental substring).",
            "Edit only processed (non-frozen) dataset files unless advisor approves frozen edits.",
            "Rewrite visible field so gold answer text is not exposed outside task parameters.",
            "Run validate_answer_leakage_cleared on edited file.",
            "Re-run all-no-run-reports to confirm cluster cleared.",
        ],
    }


def _preview_instance(root: Path, instance_id: str, rel_file: str, cluster: dict[str, Any]) -> dict[str, Any]:
    path = root / rel_file
    row = _load_instance(path, instance_id)
    task = _task_from_row(row)
    leaves = _answer_leaves(_expected_output(task))
    leaf = leaves[0] if leaves else ""
    field_result = _field_with_leaf(row, leaf, with_text=True)
    field, before = field_result if isinstance(field_result, tuple) else (field_result, "")
    after = _suggest_rewrite(before, leaf) if before else None
    return {
        "instance_id": instance_id,
        "dataset_file": rel_file,
        "field_locator": f"{rel_file} :: {field}",
        "leaked_text_hash": _hash_text(leaf),
        "leak_description": cluster.get("root_cause_title") or cluster.get("reason"),
        "before_preview": _truncate(before or ""),
        "after_preview": _truncate(after or ""),
        "suggested_rewrite": after,
        "manual_review_required": True,
    }


def _suggest_rewrite(text: str, leaf: str) -> str:
    if not text or not leaf:
        return text
    lowered = text.lower()
    leaf_lower = leaf.lower()
    if leaf_lower not in lowered:
        return text
    if DATE_RE.fullmatch(leaf.strip()):
        return re.sub(re.escape(leaf), "the scheduled date", text, count=1)
    if TIME_RE.fullmatch(leaf.strip()):
        return re.sub(re.escape(leaf), "the first open slot", text, count=1)
    return re.sub(re.escape(leaf), "[redacted-gold-token]", text, count=1, flags=re.IGNORECASE)


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


def _field_with_leaf(
    row: dict[str, Any],
    leaf: str,
    *,
    with_text: bool = False,
) -> str | tuple[str, str]:
    task = _task_from_row(row)
    goal_raw = task.get("goal")
    goal = goal_raw if isinstance(goal_raw, dict) else {}
    candidates: list[tuple[str, str]] = [
        ("goal.user_instruction", str(goal.get("user_instruction") or "")),
        ("task.user_instruction", str(task.get("user_instruction") or "")),
        ("row.prompt", str(row.get("prompt") or "")),
        ("row.context", str(row.get("context") or "")),
    ]
    leaf_lower = leaf.lower()
    for name, text in candidates:
        if leaf_lower in text.lower():
            return (name, text) if with_text else name
    visible = _visible_prompt(row)
    return ("visible_prompt", visible) if with_text else "visible_prompt"


def _load_instance(path: Path, instance_id: str) -> dict[str, Any]:
    token = f'"{instance_id}"'
    for line in path.read_text(encoding="utf-8").splitlines():
        if token in line:
            return json.loads(line)
    return {}


def _locate_instances(root: Path, wanted: set[str]) -> dict[str, list[str]]:
    located: dict[str, list[str]] = {wid: [] for wid in wanted}
    data = root / "data"
    if not wanted or not data.exists():
        return located
    for path in sorted(data.glob("**/*.jsonl")):
        if "frozen" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(root))
        for wid in wanted:
            if f'"{wid}"' in text:
                located[wid].append(rel)
    for wid, files in located.items():
        preferred = [f for f in files if f.endswith("instances.jsonl")]
        located[wid] = (preferred or files)[:5]
    return located


def _worksheet_markdown(sheet: dict[str, Any]) -> list[str]:
    lines = [
        "",
        f"### `{sheet['cluster_id']}` ({sheet.get('symptom_count', '?')} symptoms)",
        "",
        f"- Manual review required: `{sheet['manual_review_required']}`",
    ]
    if sheet.get("field_locator"):
        lines.append(f"- Locator: `{sheet['field_locator']}` (hash `{sheet.get('leaked_text_hash')}`)")
    for preview in sheet.get("before_after_previews") or []:
        lines.append(f"- Instance `{preview['instance_id']}`:")
        lines.append(f"  - Before: `{preview['before_preview']}`")
        lines.append(f"  - After (suggested): `{preview['after_preview']}`")
    return lines


def _global_checklist() -> list[str]:
    return [
        "Open each worksheet locator under data/processed/ only (never auto-edit data/frozen/).",
        "Verify the leak is a true spoiler, not instruction_parameter_overlap (see static_leakage report).",
        "Apply manual rewrite or regenerate instances; do not use apply-leakage-patch for content.",
        "Run validate_answer_leakage_cleared on the edited JSONL file.",
        "Re-run all-no-run-reports and confirm answer_leakage blocker_cluster_count is 0.",
    ]


def _resolve_leakage_report(root: Path, path: str | Path | None) -> Path:
    if path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else root / candidate
    for name in (
        "reports/static_leakage/static_leakage_report.json",
        "reports/static_leakage_report.json",
    ):
        candidate = root / name
        if candidate.exists():
            return candidate
    matches = sorted(root.glob("**/static_leakage_report.json"))
    if matches:
        return matches[0]
    return root / "reports/static_leakage/static_leakage_report.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _hash_text(text: str) -> str:
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:12]


def _truncate(text: str, limit: int = 220) -> str:
    cleaned = " ".join(text.split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3] + "..."
