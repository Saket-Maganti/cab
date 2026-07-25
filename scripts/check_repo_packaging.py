#!/usr/bin/env python3
"""Check repository packaging prerequisites for camera-ready submission."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
LICENSE = REPO_ROOT / "LICENSE"
ETHICS = REPO_ROOT / "docs" / "ETHICS_AND_LIMITATIONS.md"
RELEASE_MANIFEST = REPO_ROOT / "release" / "release_manifest.json"

README_QUICKSTART_MARKERS = (
    "## Installation",
    "## Smoke Run",
)


def run_repo_packaging_check(repo_root: Path = REPO_ROOT) -> list[str]:
    issues: list[str] = []

    if not LICENSE.exists():
        issues.append("missing LICENSE file")
    if not README.exists():
        issues.append("missing README.md")
    else:
        readme_text = README.read_text(encoding="utf-8")
        for marker in README_QUICKSTART_MARKERS:
            if marker not in readme_text:
                issues.append(f"README missing quickstart section: {marker}")
        if "pip install" not in readme_text and "pip install -e" not in readme_text:
            issues.append("README missing install instructions")

    if not ETHICS.exists():
        issues.append("missing docs/ETHICS_AND_LIMITATIONS.md")

    if not RELEASE_MANIFEST.exists():
        issues.append("missing release/release_manifest.json")
        return issues

    manifest = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
    frozen_manifest = manifest.get("default_frozen_manifest")
    if not frozen_manifest:
        issues.append("release manifest missing default_frozen_manifest")
    else:
        frozen_path = repo_root / frozen_manifest
        if not frozen_path.exists():
            issues.append(f"dataset freeze manifest missing: {frozen_manifest}")
        else:
            payload = json.loads(frozen_path.read_text(encoding="utf-8"))
            for field in ("dataset_version", "dataset_hash", "files"):
                if field not in payload:
                    issues.append(f"{frozen_manifest}: missing field {field!r}")

    paper_main = repo_root / "paper" / "latexpaper" / "main.tex"
    if not paper_main.exists():
        issues.append("missing paper/latexpaper/main.tex")
    elif not re.search(r"\\begin\{document\}", paper_main.read_text(encoding="utf-8")):
        issues.append("paper/latexpaper/main.tex does not look like a complete LaTeX document")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check repo packaging prerequisites.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    args = parser.parse_args(argv)

    issues = run_repo_packaging_check(Path(args.repo_root).resolve())
    if issues:
        print(f"Repo packaging check failed ({len(issues)} issue(s)):")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Repo packaging check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
