#!/usr/bin/env python3
"""Regenerate the deterministic Compact-20 v2 pre-review slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.safety.compact20_v2 import build_compact20_v2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-instances",
        default="data/processed/pilot_v0_1/instances.jsonl",
    )
    parser.add_argument("--output-dir", default="data/compact20_reviewed")
    args = parser.parse_args(argv)
    result = build_compact20_v2(
        ROOT,
        source_instances=args.source_instances,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
