#!/usr/bin/env python3
"""Find LaTeX and markdown TODO markers in paper sources."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = REPO_ROOT / "paper"

TODO_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("latex_todo_macro", re.compile(r"\\todo\{")),
    ("latex_todo_bold", re.compile(r"\\textbf\{TODO\.?", re.IGNORECASE)),
    ("line_todo_marker", re.compile(r"(?:^|\s)TODO[.:]\s", re.IGNORECASE)),
    ("html_todo_comment", re.compile(r"<!--\s*TODO", re.IGNORECASE)),
)


def find_todos(paper_root: Path = PAPER_ROOT) -> list[str]:
    issues: list[str] = []
    for path in sorted(paper_root.rglob("*")):
        if path.suffix not in {".tex", ".md", ".bib"}:
            continue
        rel = path.relative_to(paper_root)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for kind, pattern in TODO_PATTERNS:
                if pattern.search(line):
                    issues.append(f"{rel}:{line_number}: {kind}: {line.strip()}")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paper TODO markers.")
    parser.add_argument("--paper-root", default=str(PAPER_ROOT))
    args = parser.parse_args(argv)

    issues = find_todos(Path(args.paper_root).resolve())
    if issues:
        print(f"TODO check failed ({len(issues)} issue(s)):")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("TODO check passed: no TODO markers found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
