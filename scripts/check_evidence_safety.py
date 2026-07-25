#!/usr/bin/env python3
"""Claim-safe evidence checks for run directories and configs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.claim_ledger import SCIENTIFIC_CLAIMS_NO_MOCK_SUPPORT
from causal_agent_bench.runners.index_runs import index_runs
from causal_agent_bench.runners.run_completion import infer_completion_state
from causal_agent_bench.safety.common import compute_run_index_freshness

NON_SCIENTIFIC_SCOPES = frozenset(
    {
        "pilot_stub_engineering_only",
        "deterministic_baseline_engineering",
        "mock_diagnostic_only",
        "dry_run",
    }
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check run dirs for evidence overclaim risks.")
    parser.add_argument("--mode", choices=["draft", "submission"], default="draft")
    args = parser.parse_args(argv)

    issues: list[str] = []
    runs = index_runs(ROOT / "results")

    # Inventory freshness: the persisted RUN_INDEX may lag the live tree. The scan
    # above already covers every live run directory, so a stale index never hides a
    # run from this gate — but an un-indexed run that *would* classify paper-eligible
    # is a real escalation.
    freshness = compute_run_index_freshness(ROOT, results_root="results")
    if freshness["unindexed_paper_eligible_count"]:
        ids = ", ".join(freshness["unindexed_paper_eligible_run_ids"])
        issues.append(f"un-indexed run(s) would classify paper-eligible: {ids}")

    for entry in runs:
        run_dir = Path(entry["path"])
        state = infer_completion_state(run_dir)
        scope = str(entry.get("evidence_level") or state.get("evidence_level") or "").lower()

        if state["run_status"] in {"interrupted", "incomplete", "dry_run"} and state.get("scientific_evidence"):
            issues.append(f"{run_dir.name}: incomplete/dry run marked scientific_evidence=true")

        incomplete = run_dir / "INCOMPLETE_RUN.json"
        if incomplete.exists() and (run_dir / "aggregate_scores.json").exists():
            agg = json.loads((run_dir / "aggregate_scores.json").read_text(encoding="utf-8"))
            if agg.get("scientific_evidence") is True:
                issues.append(f"{run_dir.name}: incomplete run has scientific_evidence in scores")

        if state["run_status"] == "interrupted" and (run_dir / "paper_assets").exists():
            manifest = run_dir / "paper_assets" / "paper_assets_manifest.json"
            if manifest.exists():
                data = json.loads(manifest.read_text(encoding="utf-8"))
                if data.get("assessment", {}).get("eligible_for_paper_claims"):
                    issues.append(f"{run_dir.name}: interrupted run exported as paper-eligible")

        meta_path = run_dir / "run_metadata.json"
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            evidence_scope = str(metadata.get("evidence_scope", scope)).lower()
            if evidence_scope in NON_SCIENTIFIC_SCOPES or "mock" in evidence_scope:
                if metadata.get("scientific_evidence") is True:
                    issues.append(
                        f"{run_dir.name}: mock/stub/dry scope {evidence_scope} has scientific_evidence=true"
                    )
                agg_path = run_dir / "aggregate_scores.json"
                if agg_path.exists():
                    agg = json.loads(agg_path.read_text(encoding="utf-8"))
                    if agg.get("scientific_evidence") is True:
                        issues.append(
                            f"{run_dir.name}: mock/stub run scored as scientific evidence"
                        )

    if issues:
        prefix = "Evidence safety issues" if args.mode == "submission" else "Evidence safety warnings"
        print(f"{prefix}:")
        for issue in issues:
            print(f"  - {issue}")
        return 1 if args.mode == "submission" else 0

    print(f"Evidence safety OK ({len(runs)} live run dirs scanned)")
    if freshness["index_stale"]:
        print(
            f"  NOTE: persisted run index is stale "
            f"({freshness['indexed_run_count']} indexed vs {freshness['live_run_count']} on disk); "
            f"run `{freshness['refresh_command']}` to refresh inventory (no evidence change)."
        )
    if args.mode == "draft":
        print(
            f"  (C1–C8/C10 mock support blocked; claims guarded: {sorted(SCIENTIFIC_CLAIMS_NO_MOCK_SUPPORT)})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
