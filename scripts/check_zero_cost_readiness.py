#!/usr/bin/env python3
"""Check whether a zero-cost experiment config is ready for dry-run or local/free execution."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for path in (REPO_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from causal_agent_bench.runners.zero_cost import (
    check_zero_cost_readiness,
    format_zero_cost_report,
)

DEFAULT_CONFIG = REPO_ROOT / "configs" / "pilot_zero_cost_matrix_20.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check zero-cost experiment config readiness.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Experiment YAML config path.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root for path resolution.")
    parser.add_argument(
        "--dry-run-output-dir",
        default="results/dry_runs",
        help="Directory for dry-run reports (gitignored).",
    )
    parser.add_argument(
        "--skip-dry-run",
        action="store_true",
        help="Skip executing dry-run (checks config and costing only).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of markdown.",
    )
    parser.add_argument(
        "--require",
        choices=["dry_run_ready", "zero_cost_ready"],
        default="dry_run_ready",
        help="Minimum verdict required for exit code 0.",
    )
    args = parser.parse_args(argv)

    report = check_zero_cost_readiness(
        args.config,
        repo_root=args.repo_root,
        dry_run_output_dir=args.dry_run_output_dir,
        run_dry_run=not args.skip_dry_run,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_zero_cost_report(report))

    order = ["not_ready", "dry_run_ready", "zero_cost_ready"]
    if order.index(report.verdict) < order.index(args.require):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
