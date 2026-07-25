"""Split-metadata repair preview and pilot subset worksheets (no-run)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.benchmark_quality import discover_benchmark_dirs
from causal_agent_bench.safety.common import section_markdown, write_dual_report
from causal_agent_bench.safety.pair_link_validator import build_pair_link_report

PILOT_SUBSET_SPLITS = frozenset({"pilot", "pilot_20", "pilot_100", "dev", "development", "provider_pilot"})


def build_split_metadata_repair_preview(
    repo_root: str | Path,
    *,
    leakage_report_path: str | Path | None = None,
    output_dir: str | Path = "reports/split_metadata_repair",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    leakage_path = _resolve_report(root, leakage_report_path, "static_leakage_report.json")
    leakage = _read_json(leakage_path) or {}
    clusters = [
        row
        for row in leakage.get("root_causes") or []
        if row.get("cluster_classification") == "split_metadata_issue"
        or (
            row.get("readiness_gate") == "must_fix_before_provider_pilot"
            and "split" in str(row.get("root_cause_title") or "").lower()
        )
    ][:50]
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    scratch = out / "_pair_link_scratch"
    if out.resolve() == (root / "reports").resolve():
        scratch = out / "split_metadata_repair" / "_pair_link_scratch"
    pair_link = build_pair_link_report(root, output_dir=scratch)
    pair_issues = [
        issue
        for issue in pair_link.get("issues") or []
        if issue.get("issue_type") in {"pair_crosses_protected_split", "mismatched_base_task_id"}
    ][:30]
    subset_notes = _pilot_subset_notes(root)
    worksheets = [_cluster_worksheet(row) for row in clusters]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Split-metadata manual repair preview only. Does not move split assignments or "
            "edit splits.json automatically."
        ),
        "summary": {
            "split_metadata_clusters": len(clusters),
            "pair_link_warnings": len(pair_issues),
            "pilot_subset_datasets": len(subset_notes),
        },
        "pilot_subset_logic": {
            "subset_splits": sorted(PILOT_SUBSET_SPLITS),
            "note": (
                "Duplicates across pilot_20 ⊂ pilot_100 ⊂ pilot are expected_subset_overlap, "
                "not provider-pilot blockers."
            ),
        },
        "protected_split_warning": (
            "Never move heldout/main instances into pilot without advisor review."
        ),
        "worksheets": worksheets,
        "pair_link_samples": pair_issues,
        "pilot_subset_notes": subset_notes,
        "manual_correction_worksheet": _manual_worksheet_steps(),
        "verdicts": {
            "auto_apply_splits": False,
            "manual_review_required": True,
        },
    }
    md = split_metadata_repair_markdown(report)
    md_path, json_path = write_dual_report(
        stem="split_metadata_repair_preview",
        payload=report,
        markdown=md,
        output_dir=out,
    )
    report["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def split_metadata_repair_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Split Metadata Repair Preview",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Split-metadata clusters: {payload['summary']['split_metadata_clusters']}",
                f"- Pair-link cross-split samples: {payload['summary']['pair_link_warnings']}",
                f"- Pilot subset datasets: {payload['summary']['pilot_subset_datasets']}",
            ],
        ),
        "## Manual Correction Worksheet",
        "",
    ]
    for step in payload["manual_correction_worksheet"]:
        lines.append(f"- [ ] {step}")
    lines.extend(["", "## Pilot Subset Notes", ""])
    for note in payload.get("pilot_subset_notes") or []:
        lines.append(f"- `{note['dataset']}`: {note['message']}")
    lines.extend(["", "## Cluster Worksheets", ""])
    if not payload["worksheets"]:
        lines.append("- (none)")
    for sheet in payload["worksheets"][:20]:
        lines.append(
            f"- `{sheet['cluster_id']}` gate=`{sheet['readiness_gate']}` "
            f"action: {sheet['recommended_action']}"
        )
    lines.append("")
    return "\n".join(lines)


def _cluster_worksheet(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "cluster_id": row.get("root_cause_id"),
        "readiness_gate": row.get("readiness_gate"),
        "classification": row.get("cluster_classification"),
        "affected_splits": row.get("affected_splits") or [],
        "recommended_action": row.get("recommended_action") or row.get("suggested_fix"),
        "manual_review_required": True,
        "representative_examples": (row.get("representative_examples") or [])[:3],
    }


def _pilot_subset_notes(root: Path) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    for path in discover_benchmark_dirs(root):
        splits_path = path / "splits.json"
        if not splits_path.exists():
            continue
        try:
            payload = json.loads(splits_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        splits = payload.get("splits") if isinstance(payload.get("splits"), dict) else payload
        if not isinstance(splits, dict):
            continue
        names = set(splits.keys())
        if names & PILOT_SUBSET_SPLITS:
            rel = str(path.relative_to(root))
            notes.append(
                {
                    "dataset": rel,
                    "message": f"Pilot-family splits present: {sorted(names & PILOT_SUBSET_SPLITS)}",
                }
            )
    return notes


def _manual_worksheet_steps() -> list[str]:
    return [
        "Open splits.json and instances.jsonl for the affected dataset under data/processed/.",
        "Confirm whether the issue is missing metadata vs true cross-split leakage.",
        "For pilot_20 vs pilot_100 vs pilot, prefer documenting subset_families — do not dedupe IDs.",
        "Re-run pair-link-validation and static-leakage-check after manual edits.",
        "Never auto-move heldout instances into pilot splits.",
    ]


def _resolve_report(root: Path, path: str | Path | None, filename: str) -> Path:
    if path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else root / candidate
    direct = root / "reports" / "static_leakage" / filename
    if direct.exists():
        return direct
    matches = sorted(root.glob(f"**/{filename}"))
    return matches[0] if matches else direct


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None
