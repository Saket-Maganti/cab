#!/usr/bin/env python3
"""Verify RUN_INDEX.jsonl freshness against the live results tree (inventory only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.safety.common import compute_run_index_freshness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare persisted run index to live results directories (no mutations)."
    )
    parser.add_argument("--repo-root", default=None, help="Repository root (default: cwd).")
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--json", action="store_true", help="Print JSON payload only.")
    args = parser.parse_args(argv)

    repo = Path(args.repo_root).resolve() if args.repo_root else Path.cwd().resolve()
    freshness = compute_run_index_freshness(repo, results_root=args.results_root)
    if args.json:
        print(json.dumps(freshness, indent=2, sort_keys=True))
    else:
        print(f"index_present={freshness['index_present']}")
        print(f"indexed_run_count={freshness['indexed_run_count']}")
        print(f"live_run_count={freshness['live_run_count']}")
        print(f"index_stale={freshness['index_stale']}")
        print(f"unindexed_run_count={freshness['unindexed_run_count']}")
        print(f"orphaned_index_run_count={freshness['orphaned_index_run_count']}")
        if freshness["unindexed_paper_eligible_count"]:
            print(
                "WARNING: unindexed runs would be paper-eligible: "
                + ", ".join(freshness["unindexed_paper_eligible_run_ids"])
            )
        if freshness["index_stale"]:
            print(f"Refresh (inventory only): {freshness['refresh_command']}")
    return 1 if freshness["index_stale"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
