#!/usr/bin/env python3
"""Run contamination and memorization audits for a benchmark bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from causal_agent_bench.contamination.audit import (
    contamination_report_markdown,
    run_contamination_audit,
)
from causal_agent_bench.utils.io import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark-dir",
        required=True,
        help="Directory containing base_tasks.jsonl, instances.jsonl, and splits.json.",
    )
    parser.add_argument(
        "--splits-path",
        default=None,
        help="Optional override for splits.json.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Defaults to <benchmark-dir>.",
    )
    parser.add_argument(
        "--near-duplicate-threshold",
        type=float,
        default=0.85,
        help="Jaccard threshold for near-duplicate instructions across splits.",
    )
    args = parser.parse_args()
    benchmark_dir = Path(args.benchmark_dir)
    output_dir = Path(args.output_dir) if args.output_dir else benchmark_dir
    report = run_contamination_audit(
        benchmark_dir,
        splits_path=args.splits_path,
        near_duplicate_threshold=args.near_duplicate_threshold,
    )
    write_json(output_dir / "contamination_audit_report.json", report)
    (output_dir / "contamination_audit_report.md").write_text(
        contamination_report_markdown(report),
        encoding="utf-8",
    )
    print(f"wrote {output_dir / 'contamination_audit_report.json'}")
    print(f"wrote {output_dir / 'contamination_audit_report.md'}")
    print(f"passed={report['passed']} errors={report['summary']['n_errors']} warnings={report['summary']['n_warnings']}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
