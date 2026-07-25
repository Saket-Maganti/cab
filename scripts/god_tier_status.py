#!/usr/bin/env python3
"""Print god-tier status banner (no-run, evidence-honest)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.safety.god_tier_status import build_god_tier_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="reports/god_tier_status")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_god_tier_status(ROOT, output_dir=args.output_dir, reports_dir=args.reports_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
