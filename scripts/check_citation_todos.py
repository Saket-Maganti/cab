#!/usr/bin/env python3
"""Check bibliography coverage and citation TODO markers across the paper."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_bibliography import find_missing_citations

PAPER_ROOT = REPO_ROOT / "paper"
DEFAULT_BIB = PAPER_ROOT / "references.bib"

CITATION_TODO_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("todo_add_citation", re.compile(r"TODO:\s*Add", re.IGNORECASE)),
    ("todo_citation_key", re.compile(r"(?:@\w+\{todo_|\\cite\w*\{[^}]*todo_)", re.IGNORECASE)),
    ("fake_citation_marker", re.compile(r"fake citation", re.IGNORECASE)),
)


def find_citation_todo_markers(
    paper_root: Path = PAPER_ROOT,
    *,
    bib_path: Path = DEFAULT_BIB,
) -> list[str]:
    issues: list[str] = []
    for path in sorted(paper_root.rglob("*")):
        if path.suffix not in {".tex", ".bib"}:
            continue
        rel = path.relative_to(paper_root)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for kind, pattern in CITATION_TODO_PATTERNS:
                if pattern.search(line):
                    issues.append(f"{rel}:{line_number}: {kind}: {line.strip()}")
    if bib_path.exists():
        for line_number, line in enumerate(bib_path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"@\w+\{todo_", line, re.IGNORECASE):
                issues.append(
                    f"references.bib:{line_number}: todo_bib_entry: {line.strip()}"
                )
    return issues


def run_citation_todo_check(
    paper_root: Path = PAPER_ROOT,
    bib_path: Path = DEFAULT_BIB,
    *,
    all_sections: bool = True,
) -> list[str]:
    issues: list[str] = []
    if all_sections:
        sections = tuple(
            str(p.relative_to(paper_root)) for p in sorted(paper_root.rglob("*.tex"))
        )
    else:
        sections = ("sections/02_related_work.tex",)
    issues.extend(find_missing_citations(paper_root, bib_path, sections=sections))
    issues.extend(find_citation_todo_markers(paper_root, bib_path=bib_path))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paper citations and citation TODOs.")
    parser.add_argument("--paper-root", default=str(PAPER_ROOT))
    parser.add_argument("--bib", default=str(DEFAULT_BIB))
    args = parser.parse_args(argv)

    issues = run_citation_todo_check(Path(args.paper_root).resolve(), Path(args.bib).resolve())
    if issues:
        print(f"Citation TODO check failed ({len(issues)} issue(s)):")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Citation TODO check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
