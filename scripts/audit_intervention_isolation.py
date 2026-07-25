#!/usr/bin/env python3
"""Audit intervention isolation for a processed dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.audit.intervention_isolation import (
    audit_intervention_isolation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit intervention single-factor isolation.")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to instances.jsonl or benchmark directory.",
    )
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)

    dataset = Path(args.dataset)
    instances_path = dataset / "instances.jsonl" if dataset.is_dir() else dataset

    report = audit_intervention_isolation(
        instances_path=instances_path,
        output_dir=args.output_dir,
    )
    out = args.output_dir or Path("audits/intervention_isolation") / report["dataset_version"]
    print(f"Intervention isolation audit: passed={report['passed']} -> {out}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
