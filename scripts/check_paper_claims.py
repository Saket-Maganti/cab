#!/usr/bin/env python3
"""Scan paper sources for claim IDs and cross-check the claim ledger."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from causal_agent_bench.claim_ledger import (
    check_paper_claims,
    extract_paper_claim_ids,
)

DEFAULT_LEDGER = REPO_ROOT / "docs" / "claim_ledger.json"
DEFAULT_PAPER = REPO_ROOT / "paper" / "latexpaper"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paper claim references.")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--paper-root", default=str(DEFAULT_PAPER))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument(
        "--mode",
        choices=["draft", "submission"],
        default="draft",
    )
    parser.add_argument("--list-ids", action="store_true", help="Print claim IDs found in paper.")
    args = parser.parse_args(argv)

    paper_root = Path(args.paper_root).resolve()
    if args.list_ids:
        ids = sorted(extract_paper_claim_ids(paper_root))
        print(f"Found {len(ids)} claim reference(s) in paper:")
        for claim_id in ids:
            print(f"- {claim_id}")
        return 0

    issues = check_paper_claims(
        Path(args.ledger).resolve(),
        paper_root,
        repo_root=Path(args.repo_root).resolve(),
        mode=args.mode,
    )
    hard = [issue for issue in issues if not issue.startswith("WARNING:")]
    warnings = [issue for issue in issues if issue.startswith("WARNING:")]
    for warning in warnings:
        print(f"- {warning}")
    if hard:
        print(f"Paper claim check failed ({len(hard)} issue(s)):")
        for issue in hard:
            print(f"- {issue}")
        return 1
    print("Paper claim check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
