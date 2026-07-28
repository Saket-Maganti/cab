#!/usr/bin/env python3
"""Validate real Compact-20 reviews and derive the C10 gate fail-closed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.safety.human_review_gate import (
    DEFAULT_CANDIDATE_MANIFEST,
    DEFAULT_REVIEW_DIR,
    HumanReviewPolicy,
    validate_compact20_human_reviews,
    write_human_review_gate_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", default=str(DEFAULT_REVIEW_DIR))
    parser.add_argument("--candidate-manifest", default=str(DEFAULT_CANDIDATE_MANIFEST))
    parser.add_argument(
        "--output",
        default="reports/CAB_HUMAN_REVIEW_AND_C10_GATE.json",
    )
    parser.add_argument("--min-reviewers", type=int, default=2)
    parser.add_argument("--min-agreement", type=float, default=0.80)
    args = parser.parse_args(argv)
    if args.min_reviewers < 2:
        parser.error("--min-reviewers must be at least 2")
    if not 0.0 <= args.min_agreement <= 1.0:
        parser.error("--min-agreement must be between 0 and 1")

    payload = validate_compact20_human_reviews(
        ROOT,
        review_dir=args.review_dir,
        candidate_manifest=args.candidate_manifest,
        policy=HumanReviewPolicy(
            min_independent_reviewers=args.min_reviewers,
            min_raw_agreement=args.min_agreement,
        ),
    )
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    write_human_review_gate_report(payload, output)
    print(
        json.dumps(
            {
                "human_review_state": payload["human_review_state"],
                "c10_state": payload["c10_state"],
                "contract_evaluation_state": payload[
                    "contract_evaluation_state"
                ],
                "genuine_human_row_count": payload["genuine_human_row_count"],
                "complete_review_groups": payload["complete_review_groups"],
                "expected_review_groups": payload["expected_review_groups"],
                "c10_blockers": payload["c10_blockers"],
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0 if payload["c10_state"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
