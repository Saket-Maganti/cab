#!/usr/bin/env python3
"""Build deterministic prospective Compact-20 and Scale-100 power reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.analysis.power_precision import build_power_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/pre_run/power_assumptions.json",
    )
    parser.add_argument("--output-dir", default="reports/pre_run_hardening")
    args = parser.parse_args(argv)
    result = build_power_reports(
        ROOT,
        config_path=args.config,
        output_dir=args.output_dir,
    )
    print(
        json.dumps(
            {
                "paths": result["paths"],
                "recommendation": result["recommendation"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
