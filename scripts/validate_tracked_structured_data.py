#!/usr/bin/env python3
"""Validate syntax for every tracked structured-data file."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {".json", ".jsonl", ".yaml", ".yml", ".ipynb"}


def tracked_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        root / raw.decode()
        for raw in result.stdout.split(b"\0")
        if raw and Path(raw.decode()).suffix.lower() in SUFFIXES
    ]


def validate(path: Path) -> tuple[str, int]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        count = 0
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            json.loads(line)
            count = line_number
        return "JSONL syntax (one JSON value per nonblank line)", count
    if suffix in {".json", ".ipynb"}:
        value = json.loads(path.read_text(encoding="utf-8"))
        if suffix == ".ipynb":
            if not isinstance(value, dict) or not isinstance(value.get("cells"), list):
                raise ValueError("notebook root must contain a cells list")
            return "Jupyter notebook JSON structure", len(value["cells"])
        return "JSON syntax", 1
    yaml.safe_load(path.read_text(encoding="utf-8"))
    return "YAML safe-load syntax", 1


def build_report(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in tracked_paths(root):
        relative = path.relative_to(root).as_posix()
        try:
            schema, records = validate(path)
            rows.append(
                {
                    "path": relative,
                    "passed": True,
                    "schema": schema,
                    "records_or_cells_checked": records,
                    "error_location": None,
                    "error": None,
                    "fix_applied": False,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "path": relative,
                    "passed": False,
                    "schema": "syntax selected by file extension",
                    "records_or_cells_checked": 0,
                    "error_location": getattr(exc, "lineno", None),
                    "error": f"{type(exc).__name__}: {exc}",
                    "fix_applied": False,
                }
            )
    failures = [row for row in rows if not row["passed"]]
    return {
        "schema_version": "cab_cpu_structured_data_validation_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": "ENGINEERING_ONLY",
        "scope": "Tracked JSON, JSONL, YAML, YML, and Jupyter notebook files.",
        "files_scanned": len(rows),
        "files_passed": len(rows) - len(failures),
        "files_failed": len(failures),
        "passed": not failures,
        "files": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports/CAB_CPU_STRUCTURED_DATA_VALIDATION.json",
    )
    args = parser.parse_args()
    report = build_report(ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"structured-data: {'PASS' if report['passed'] else 'FAIL'} "
        f"({report['files_passed']}/{report['files_scanned']} files)"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
