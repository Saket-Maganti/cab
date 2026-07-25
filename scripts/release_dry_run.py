#!/usr/bin/env python3
"""Dry-run release and submission packaging checks without publishing."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Release dry-run: packaging + tests smoke.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip pytest (faster local iteration).",
    )
    parser.add_argument(
        "--submission",
        action="store_true",
        help="Run camera-ready precheck in submission mode (expected to fail until ready).",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    python = sys.executable
    steps: list[tuple[str, list[str]]] = [
        ("release_check", [python, "scripts/release_check.py"]),
        (
            "camera_ready_precheck",
            [
                python,
                "scripts/camera_ready_precheck.py",
                "--mode",
                "submission" if args.submission else "draft",
            ],
        ),
    ]
    if not args.skip_tests:
        steps.append(("pytest", [python, "-m", "pytest", "-q"]))

    failed: list[str] = []
    for name, command in steps:
        print(f"\n==> {name}")
        proc = subprocess.run(command, cwd=repo_root)
        if proc.returncode != 0:
            failed.append(name)

    if failed:
        print(f"\nrelease-dry-run: FAIL ({', '.join(failed)})")
        return 1
    print("\nrelease-dry-run: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
