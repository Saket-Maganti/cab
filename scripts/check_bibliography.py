#!/usr/bin/env python3
"""Verify that paper citation keys resolve to bibliography entries."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = REPO_ROOT / "paper" / "latexpaper"
DEFAULT_BIB = PAPER_ROOT / "references.bib"

CITE_COMMAND_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyearpar)\*?"
    r"(?:\[[^\]]*\]){0,2}\{([^}]+)\}"
)
BIB_KEY_RE = re.compile(r"@\w+\{([^,\s]+),")
TODO_KEY_RE = re.compile(r"todo_", re.IGNORECASE)


def extract_cite_keys(tex: str) -> set[str]:
    keys: set[str] = set()
    for match in CITE_COMMAND_RE.finditer(tex):
        for key in match.group(1).split(","):
            key = key.strip()
            if key:
                keys.add(key)
    return keys


def extract_bib_keys(bib: str) -> set[str]:
    return {match.group(1) for match in BIB_KEY_RE.finditer(bib)}


def find_missing_citations(
    paper_root: Path = PAPER_ROOT,
    bib_path: Path = DEFAULT_BIB,
    *,
    sections: tuple[str, ...] = ("sections/02_related_work.tex",),
) -> list[str]:
    bib_text = bib_path.read_text(encoding="utf-8")
    bib_keys = extract_bib_keys(bib_text)
    missing: list[str] = []
    for rel in sections:
        tex_path = paper_root / rel
        if not tex_path.exists():
            missing.append(f"MISSING_FILE:{rel}")
            continue
        cite_keys = extract_cite_keys(tex_path.read_text(encoding="utf-8"))
        for key in sorted(cite_keys):
            if TODO_KEY_RE.search(key):
                missing.append(f"TODO_KEY:{key}")
            elif key not in bib_keys:
                missing.append(key)
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paper bibliography coverage.")
    parser.add_argument("--paper-root", default=str(PAPER_ROOT))
    parser.add_argument("--bib", default=str(DEFAULT_BIB))
    parser.add_argument(
        "--all-sections",
        action="store_true",
        help="Check every .tex file under paper/ (default: related work only).",
    )
    args = parser.parse_args(argv)

    paper_root = Path(args.paper_root).resolve()
    bib_path = Path(args.bib).resolve()
    if args.all_sections:
        sections = tuple(
            str(p.relative_to(paper_root))
            for p in sorted(paper_root.rglob("*.tex"))
        )
    else:
        sections = ("sections/02_related_work.tex",)

    missing = find_missing_citations(paper_root, bib_path, sections=sections)
    if missing:
        print(f"Bibliography check failed ({len(missing)} issue(s)):")
        for item in missing:
            print(f"- {item}")
        return 1

    print(
        f"Bibliography check passed for {len(sections)} file(s) "
        f"against {bib_path.relative_to(REPO_ROOT)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
