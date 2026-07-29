#!/usr/bin/env python3
"""Enforce the CAB Level-5 line-coverage contract from coverage JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CRITICAL_MODULES = (
    "registry.py",
    "execution.py",
    "evaluator.py",
    "review.py",
    "evidence.py",
)


def _line_percent(summary: dict[str, Any]) -> float:
    statements = int(summary["num_statements"])
    covered = int(summary["covered_lines"])
    return 100.0 if statements == 0 else covered * 100.0 / statements


def check_coverage(
    path: str | Path,
    *,
    overall_minimum: float = 85.0,
    critical_minimum: float = 90.0,
) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    files = {
        name: row
        for name, row in payload["files"].items()
        if "/level5/" in name.replace("\\", "/")
    }
    overall_summary = {
        "num_statements": sum(int(row["summary"]["num_statements"]) for row in files.values()),
        "covered_lines": sum(int(row["summary"]["covered_lines"]) for row in files.values()),
    }
    overall = _line_percent(overall_summary)
    critical: dict[str, float] = {}
    missing: list[str] = []
    for module in CRITICAL_MODULES:
        matches = [
            row
            for name, row in files.items()
            if name.replace("\\", "/").endswith(f"/level5/{module}")
        ]
        if len(matches) != 1:
            missing.append(module)
            continue
        critical[module] = _line_percent(matches[0]["summary"])
    failures = [
        f"overall line coverage {overall:.2f}% < {overall_minimum:.2f}%"
        for _ in [None]
        if overall < overall_minimum
    ]
    failures.extend(
        f"{module} line coverage {percent:.2f}% < {critical_minimum:.2f}%"
        for module, percent in critical.items()
        if percent < critical_minimum
    )
    failures.extend(f"critical module missing from coverage JSON: {module}" for module in missing)
    return {
        "passed": not failures,
        "overall_line_coverage": round(overall, 2),
        "overall_minimum": overall_minimum,
        "critical_line_coverage": {
            key: round(value, 2) for key, value in sorted(critical.items())
        },
        "critical_minimum": critical_minimum,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage_json")
    parser.add_argument("--overall-minimum", type=float, default=85.0)
    parser.add_argument("--critical-minimum", type=float, default=90.0)
    args = parser.parse_args()
    result = check_coverage(
        args.coverage_json,
        overall_minimum=args.overall_minimum,
        critical_minimum=args.critical_minimum,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
