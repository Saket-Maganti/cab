#!/usr/bin/env python3
"""Check whether paper placeholders are still present.

Draft mode is intentionally permissive: it lists placeholders so authors know
what remains unresolved. Submission mode is strict and fails if any submission
blocking placeholder is found.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = REPO_ROOT / "paper" / "latexpaper"


PLACEHOLDER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "result_placeholder",
        re.compile(
            r"\[(?:N|M|K|X|rho|domains|agents/models|main finding placeholder)\]"
        ),
    ),
    ("todo_add_citation", re.compile(r"TODO:\s*Add")),
    ("todo_citation_key", re.compile(r"(?:@\w+\{todo_|\\cite\w*\{[^}]*todo_)")),
    ("fake_citation_marker", re.compile(r"fake citation", re.IGNORECASE)),
)

FINAL_RESULT_RELATIVE_FILES = {
    Path("sections/07_results.tex"),
    Path("sections/08_human_validation.tex"),
    Path("sections/09_ablations.tex"),
}


@dataclass(frozen=True)
class PlaceholderFinding:
    kind: str
    path: Path
    line_number: int
    line: str

    def format(self, root: Path) -> str:
        rel_path = self.path.relative_to(root)
        return f"{rel_path}:{self.line_number}: {self.kind}: {self.line.strip()}"


def find_placeholders(paper_root: str | Path = PAPER_ROOT) -> list[PlaceholderFinding]:
    root = Path(paper_root).resolve()
    findings: list[PlaceholderFinding] = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in {".tex", ".bib", ".md"}:
            continue
        relative_path = path.relative_to(root)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for kind, pattern in PLACEHOLDER_PATTERNS:
                if pattern.search(line):
                    findings.append(PlaceholderFinding(kind, path, line_number, line))
            if relative_path in FINAL_RESULT_RELATIVE_FILES and re.search(
                r"not yet run", line, re.IGNORECASE
            ):
                findings.append(
                    PlaceholderFinding("not_yet_run_in_result_section", path, line_number, line)
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paper placeholders.")
    parser.add_argument(
        "--mode",
        choices=["draft", "submission"],
        default="draft",
        help="draft lists placeholders; submission fails on placeholders.",
    )
    parser.add_argument("--paper-root", default=str(PAPER_ROOT), help="Paper directory to scan.")
    args = parser.parse_args(argv)

    paper_root = Path(args.paper_root).resolve()
    findings = find_placeholders(paper_root)
    if findings:
        print(f"Found {len(findings)} unresolved paper placeholder(s):")
        for finding in findings:
            print(f"- {finding.format(paper_root)}")
    else:
        print("No paper placeholders detected.")

    if args.mode == "submission" and findings:
        print("Submission mode failed: unresolved placeholders remain.")
        return 1
    if args.mode == "draft" and findings:
        print("Draft mode passed: placeholders are allowed but must remain visible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
