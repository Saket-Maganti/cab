#!/usr/bin/env python3
"""Export a versioned leaderboard bundle (JSON, CSV, Markdown) from a run directory."""

from __future__ import annotations

import argparse

from causal_agent_bench.analysis.leaderboard import export_leaderboard


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Scored experiment run directory.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Defaults to <run-dir>/leaderboard.",
    )
    parser.add_argument(
        "--eval-split",
        default="unfiltered",
        help="Split filter: unfiltered, public_dev, dev, pilot, validation, test, heldout_templates.",
    )
    parser.add_argument(
        "--splits-path",
        default=None,
        help="Path to splits.json (defaults from dataset_version or pilot_v0.1 frozen bundle).",
    )
    args = parser.parse_args()
    paths = export_leaderboard(
        args.run_dir,
        args.output_dir,
        eval_split=args.eval_split,
        splits_path=args.splits_path,
    )
    for path in paths:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
