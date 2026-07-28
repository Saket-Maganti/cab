#!/usr/bin/env python3
"""Build the canonical blank Compact-20 C10 review packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.safety.human_validation_packet import (
    build_c10_review_packet,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="data/human_validation/compact20_real_review",
    )
    parser.add_argument(
        "--candidate-manifest",
        default="data/compact20_reviewed/compact20_reviewed_manifest.json",
    )
    parser.add_argument(
        "--instances",
        default="data/processed/pilot_v0_1/instances.jsonl",
    )
    parser.add_argument("--reviewers-per-candidate", type=int, default=2)
    args = parser.parse_args(argv)
    payload = build_c10_review_packet(
        ROOT,
        output_dir=args.output_dir,
        candidate_manifest=args.candidate_manifest,
        instances_path=args.instances,
        reviewers_per_candidate=args.reviewers_per_candidate,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
