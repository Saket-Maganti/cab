#!/usr/bin/env python3
"""Verify the package imports from a clean interpreter path."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

REQUIRED_MODULES = (
    "causal_agent_bench",
    "causal_agent_bench.cli",
    "causal_agent_bench.schemas",
    "causal_agent_bench.scoring",
    "causal_agent_bench.runners.experiment",
    "causal_agent_bench.analysis.report",
    "causal_agent_bench.analysis.paper_fill",
)


def _ensure_src_on_path() -> None:
    src = str(SRC_ROOT.resolve())
    if src not in sys.path:
        sys.path.insert(0, src)


def run_package_import_check() -> list[str]:
    _ensure_src_on_path()
    errors: list[str] = []
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            errors.append(f"{module_name}: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check causal_agent_bench imports.")
    args = parser.parse_args(argv)
    _ = args

    errors = run_package_import_check()
    if errors:
        print(f"Package import check failed ({len(errors)} issue(s)):")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Package import check passed ({len(REQUIRED_MODULES)} modules).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
