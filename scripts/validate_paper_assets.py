#!/usr/bin/env python3
"""Validate paper assets, placeholders, and evidence linkage."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = REPO_ROOT / "paper" / "latexpaper"

PLACEHOLDER_MARKERS = (
    re.compile(r"\[(?:N|M|K|X|rho|domains|agents/models|main finding placeholder)\]"),
    re.compile(r"TODO:\s*Add", re.IGNORECASE),
    re.compile(r"not yet run", re.IGNORECASE),
)


def _run_check(script: str, *args: str) -> int:
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / script), *args]
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode


def _placeholder_figure_status(repo_root: Path) -> list[str]:
    """Verify placeholder figures are properly labeled."""
    issues: list[str] = []
    fig_dir = repo_root / "paper" / "latexpaper" / "figures"
    if not fig_dir.exists():
        return issues
    for png in sorted(fig_dir.glob("*_placeholder.png")):
        meta_path = png.with_suffix(".meta.json")
        if not meta_path.exists():
            issues.append(f"WARNING: {png.relative_to(repo_root)} missing .meta.json")
            continue
        import json

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if not meta.get("placeholder"):
            issues.append(f"WARNING: {meta_path.relative_to(repo_root)} must set placeholder=true")
        if meta.get("empirical_result"):
            issues.append(f"ERROR: {meta_path.relative_to(repo_root)} must not set empirical_result=true")
    return issues


def _placeholder_issues(mode: str) -> list[str]:
    issues: list[str] = []
    for path in sorted(PAPER_ROOT.rglob("*.tex")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern in PLACEHOLDER_MARKERS:
                if pattern.search(line):
                    rel = path.relative_to(REPO_ROOT)
                    msg = f"{rel}:{line_no}: placeholder marker in paper"
                    if mode == "submission":
                        issues.append(msg)
                    else:
                        issues.append(f"WARNING: {msg}")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["draft", "submission"], default="draft")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    args = parser.parse_args(argv)

    issues: list[str] = []
    asset_rc = _run_check("check_paper_assets.py", "--mode", args.mode)
    if asset_rc != 0:
        issues.append("check_paper_assets.py failed")
    placeholder_rc = _run_check("check_paper_placeholders.py", "--mode", args.mode)
    if placeholder_rc != 0:
        issues.append("check_paper_placeholders.py failed")
    issues.extend(_placeholder_issues(args.mode))
    issues.extend(_placeholder_figure_status(Path(args.repo_root)))

    hard = [issue for issue in issues if not issue.startswith("WARNING:")]
    warnings = [issue for issue in issues if issue.startswith("WARNING:")]
    for warning in warnings:
        print(f"- {warning}")
    if hard:
        print(f"Paper asset validation failed ({len(hard)} issue(s)):")
        for issue in hard:
            print(f"- {issue}")
        return 1
    print("Paper asset validation passed" + (f" with {len(warnings)} warning(s)" if warnings else "."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
