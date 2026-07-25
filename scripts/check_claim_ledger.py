#!/usr/bin/env python3
"""Validate claim ledger schema, evidence links, and paper claim references."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from causal_agent_bench.claim_ledger import (
    check_paper_claims,
    validate_claim_evidence_levels,
    validate_claim_ledger,
)
from scripts.check_paper_placeholders import find_placeholders

DEFAULT_LEDGER = REPO_ROOT / "docs" / "claim_ledger.json"
DEFAULT_PAPER = REPO_ROOT / "paper"


def run_claim_ledger_check(
    ledger_path: Path,
    repo_root: Path,
    *,
    paper_root: Path | None = None,
    mode: str = "draft",
    check_placeholders: bool = True,
) -> list[str]:
    issues: list[str] = []
    issues.extend(validate_claim_ledger(ledger_path, repo_root=repo_root))
    issues.extend(validate_claim_evidence_levels(ledger_path, repo_root=repo_root, mode=mode))
    if paper_root is not None:
        issues.extend(
            check_paper_claims(
                ledger_path,
                paper_root,
                repo_root=repo_root,
                mode=mode,
            )
        )
    if check_placeholders and mode == "submission":
        findings = find_placeholders(paper_root or DEFAULT_PAPER)
        for finding in findings:
            issues.append(
                f"placeholder:{finding.path.relative_to(paper_root or DEFAULT_PAPER)}:"
                f"{finding.line_number}: {finding.kind}"
            )
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate docs/claim_ledger.json.")
    parser.add_argument("--path", default=str(DEFAULT_LEDGER))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--paper-root", default=str(DEFAULT_PAPER))
    parser.add_argument(
        "--no-paper-check",
        action="store_true",
        help="Skip LaTeX claimref cross-check.",
    )
    parser.add_argument(
        "--mode",
        choices=["draft", "submission"],
        default="draft",
        help="submission mode is stricter for paper references and placeholders.",
    )
    parser.add_argument(
        "--no-placeholder-check",
        action="store_true",
        help="Skip placeholder scan even in submission mode.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    issues = run_claim_ledger_check(
        Path(args.path).resolve(),
        repo_root,
        paper_root=None if args.no_paper_check else Path(args.paper_root).resolve(),
        mode=args.mode,
        check_placeholders=not args.no_placeholder_check,
    )

    hard_failures = [issue for issue in issues if not issue.startswith("WARNING:")]
    warnings = [issue for issue in issues if issue.startswith("WARNING:")]

    for warning in warnings:
        print(f"- {warning}")
    if hard_failures:
        print(f"Claim ledger check failed ({len(hard_failures)} issue(s)):")
        for issue in hard_failures:
            print(f"- {issue}")
        return 1

    if warnings:
        print(f"Claim ledger check passed with {len(warnings)} warning(s): {args.path}")
    else:
        print(f"Claim ledger is valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
