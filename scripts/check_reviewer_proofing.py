#!/usr/bin/env python3
"""Verify reviewer attack matrix completeness for NeurIPS ED proofing."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = REPO_ROOT / "reviews" / "reviewer_attack_response_matrix.md"

EXPECTED_ATTACK_COUNT = 20
ATTACK_HEADING_RE = re.compile(r"^###\s+\d+\.\s+", re.MULTILINE)
REQUIRED_ROW_LABELS = (
    "Why it matters",
    "Current status",
    "Required fix",
    "Paper section",
    "Evidence needed",
    "Blocking",
)
PRIORITIZED_SECTION = "## Prioritized fix list"


def validate_matrix(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"Missing matrix file: {path}"]

    text = path.read_text(encoding="utf-8")
    if PRIORITIZED_SECTION not in text:
        issues.append("Missing prioritized fix list section.")

    attack_headings = ATTACK_HEADING_RE.findall(text)
    if len(attack_headings) != EXPECTED_ATTACK_COUNT:
        issues.append(
            f"Expected {EXPECTED_ATTACK_COUNT} attack headings, found {len(attack_headings)}."
        )

    for label in REQUIRED_ROW_LABELS:
        if f"**{label}**" not in text:
            issues.append(f"Missing required row label: {label}")

    # Each attack block should include all row labels after its heading.
    blocks = re.split(r"^###\s+\d+\.\s+", text, flags=re.MULTILINE)[1:]
    if len(blocks) != EXPECTED_ATTACK_COUNT:
        issues.append(f"Expected {EXPECTED_ATTACK_COUNT} attack blocks, found {len(blocks)}.")
    else:
        for index, block in enumerate(blocks, start=1):
            for label in REQUIRED_ROW_LABELS:
                if f"**{label}**" not in block:
                    issues.append(f"Attack {index} missing row: {label}")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check reviewer proofing matrix.")
    parser.add_argument(
        "--matrix",
        default=str(DEFAULT_MATRIX),
        help="Path to reviewer_attack_response_matrix.md",
    )
    args = parser.parse_args(argv)

    issues = validate_matrix(Path(args.matrix).resolve())
    if issues:
        print(f"Reviewer proofing check failed ({len(issues)} issue(s)):")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(
        f"Reviewer proofing check passed: {EXPECTED_ATTACK_COUNT} attacks documented "
        f"in {Path(args.matrix).resolve().relative_to(REPO_ROOT)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
