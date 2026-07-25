from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import (
    PAPER_ASSET_PATH_HINTS,
    classify_run_entry,
    compute_run_index_freshness,
    load_run_index_entries,
    section_markdown,
    write_dual_report,
)


def build_run_health_report(
    repo_root: str | Path,
    *,
    results_root: str | Path = "results",
    output_dir: str | Path = "reports",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    raw_entries = load_run_index_entries(root, results_root=results_root)
    runs = [classify_run_entry(entry, root) for entry in raw_entries]

    freshness = compute_run_index_freshness(root, results_root=results_root)

    warnings = _collect_warnings(runs, root)
    warnings = _freshness_warnings(freshness) + warnings
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "results_root": str(results_root),
        "total_runs": len(runs),
        "indexed_run_count": freshness["indexed_run_count"],
        "live_run_count": freshness["live_run_count"],
        "index_stale": freshness["index_stale"],
        "unindexed_run_count": freshness["unindexed_run_count"],
        "orphaned_index_run_count": freshness["orphaned_index_run_count"],
        "unindexed_paper_eligible_count": freshness["unindexed_paper_eligible_count"],
        "by_classification": dict(Counter(r["classification"] for r in runs)),
        "paper_eligible_count": sum(1 for r in runs if r["paper_eligible"]),
        "interrupted_count": sum(1 for r in runs if r["classification"] == "interrupted"),
        "incomplete_count": sum(1 for r in runs if r["classification"] == "incomplete"),
        "mock_diagnostic_count": sum(1 for r in runs if r["classification"] == "mock_diagnostic"),
        "warnings": warnings,
    }

    payload = {"summary": summary, "runs": runs, "warnings": warnings, "run_index_freshness": freshness}
    md = _format_markdown(summary, runs, warnings, freshness)
    md_path, json_path = write_dual_report(
        stem="run_health_report",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _freshness_warnings(freshness: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not freshness.get("index_present"):
        warnings.append(
            "run index missing: no RUN_INDEX.jsonl/run_index.json under results — "
            f"run `{freshness['refresh_command']}` (inventory-only) to build it"
        )
    if freshness.get("unindexed_run_count"):
        warnings.append(
            f"STALE RUN INDEX: {freshness['live_run_count']} run directories on disk but "
            f"{freshness['indexed_run_count']} indexed "
            f"({freshness['unindexed_run_count']} un-indexed) — reports undercount until you "
            f"run `{freshness['refresh_command']}` (inventory-only, no eligibility change)"
        )
    if freshness.get("orphaned_index_run_count"):
        warnings.append(
            f"STALE RUN INDEX: {freshness['orphaned_index_run_count']} indexed run(s) have no "
            f"live directory — re-run `{freshness['refresh_command']}` to drop stale entries"
        )
    if freshness.get("unindexed_paper_eligible_count"):
        warnings.append(
            "REVIEW REQUIRED: "
            f"{freshness['unindexed_paper_eligible_count']} un-indexed run(s) would classify as "
            f"paper-eligible: {', '.join(freshness.get('unindexed_paper_eligible_run_ids', []))} — "
            "do NOT promote; verify provenance and index explicitly"
        )
    return warnings


def _collect_warnings(runs: list[dict[str, Any]], repo_root: Path) -> list[str]:
    warnings: list[str] = []
    for run in runs:
        run_id = run["run_id"]
        if run["classification"] == "interrupted":
            warnings.append(f"{run_id}: interrupted run")
        if run["classification"] == "incomplete":
            warnings.append(f"{run_id}: incomplete run")
        if run["classification"] == "provider_backed_pilot" and not run["scientific_evidence"]:
            warnings.append(f"{run_id}: provider_pilot classification without scientific_evidence=true")
        if run["status"] == "complete" and not run["scientific_evidence"] and run["classification"] not in {
            "mock_diagnostic",
            "stub_engineering",
            "complete_engineering_only",
        }:
            warnings.append(f"{run_id}: complete run with scientific_evidence=false (review before paper use)")
        if run["missing_metadata"]:
            warnings.append(f"{run_id}: missing metadata fields: {', '.join(run['missing_metadata'])}")
        if (repo_root / run["run_path"].replace(str(repo_root) + "/", "")).exists():
            rel = Path(run["run_path"])
            if rel.name and (rel / "paper_assets").exists() and not run["paper_eligible"]:
                warnings.append(f"{run_id}: paper_assets present but run not paper-eligible")
    for hint in PAPER_ASSET_PATH_HINTS:
        path = repo_root / hint.split("/")[0]
        if path.exists() and any(
            r["classification"] in {"mock_diagnostic", "stub_engineering", "incomplete", "interrupted"}
            for r in runs
        ):
            warnings.append(
                f"repo contains {hint} paths while non-eligible runs exist — verify asset provenance before submission"
            )
            break
    return warnings


def _format_markdown(
    summary: dict[str, Any],
    runs: list[dict[str, Any]],
    warnings: list[str],
    freshness: dict[str, Any],
) -> str:
    stale_flag = " ⚠️ STALE" if summary.get("index_stale") else " (fresh)"
    lines = [
        "# Run health report",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "Zero-compute inspection of local run index only. Does not start runs or call providers.",
        "",
        section_markdown(
            "Summary",
            [
                f"- Runs classified from index: {summary['total_runs']}",
                f"- Run directories on disk (live scan): {summary['live_run_count']}{stale_flag}",
                f"- Paper-eligible (strict): {summary['paper_eligible_count']}",
                f"- Interrupted: {summary['interrupted_count']}",
                f"- Incomplete: {summary['incomplete_count']}",
                f"- Mock diagnostic: {summary['mock_diagnostic_count']}",
                "",
                "**By classification:**",
                *[f"  - {k}: {v}" for k, v in sorted(summary["by_classification"].items())],
            ],
        ),
        _freshness_section_markdown(freshness),
        section_markdown("Warnings", [f"- {w}" for w in warnings]),
        "## Runs\n",
    ]
    for run in runs:
        lines.extend(
            [
                f"### {run['run_id']}",
                "",
                f"- Path: `{run['run_path']}`",
                f"- Classification: `{run['classification']}`",
                f"- Status / completion: `{run['status']}` / `{run['completion_state']}`",
                f"- Trajectories: {run['completed_trajectories']}/{run['expected_trajectories']}",
                f"- Provider: `{run['provider_type']}` | evidence_level: `{run['evidence_level']}`",
                f"- scientific_evidence: `{run['scientific_evidence']}`",
                f"- Config: `{run.get('config_name')}` (hash: `{run.get('config_hash')}`)",
                f"- Paper-eligible: **{run['paper_eligible']}** — {run['paper_eligibility_reason']}",
            ]
        )
        if run["missing_metadata"]:
            lines.append(f"- Missing metadata: {', '.join(run['missing_metadata'])}")
        lines.append("")
    return "\n".join(lines)


def _freshness_section_markdown(freshness: dict[str, Any]) -> str:
    status = "STALE — index undercounts/overcounts the live tree" if freshness["index_stale"] else "fresh"
    lines = [
        f"- Index status: **{status}**",
        f"- Indexed runs: {freshness['indexed_run_count']} | Live run dirs: {freshness['live_run_count']}",
        f"- Un-indexed (on disk, not in index): {freshness['unindexed_run_count']}",
        f"- Orphaned (in index, no live dir): {freshness['orphaned_index_run_count']}",
        f"- Un-indexed runs that would be paper-eligible: "
        f"**{freshness['unindexed_paper_eligible_count']}** "
        f"({'review required' if freshness['unindexed_paper_eligible_count'] else 'none — refresh is inventory-only'})",
    ]
    if freshness["unindexed_run_ids"]:
        shown = ", ".join(freshness["unindexed_run_ids"])
        extra = freshness["unindexed_run_ids_truncated"]
        suffix = f" (+{extra} more)" if extra else ""
        lines.append(f"- Un-indexed ids: {shown}{suffix}")
    if freshness["orphaned_index_run_ids"]:
        shown = ", ".join(freshness["orphaned_index_run_ids"])
        extra = freshness["orphaned_index_run_ids_truncated"]
        suffix = f" (+{extra} more)" if extra else ""
        lines.append(f"- Orphaned ids: {shown}{suffix}")
    if freshness["index_stale"]:
        lines.append(f"- **Fix:** run `{freshness['refresh_command']}` (safe inventory op; does not change evidence state)")
    return section_markdown("Run index freshness", lines)
