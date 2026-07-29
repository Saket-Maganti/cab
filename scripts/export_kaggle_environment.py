#!/usr/bin/env python3
"""Export a public-safe Kaggle dependency and runtime manifest."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

from causal_agent_bench.level5.core import content_hash, file_sha256, utc_now


def build_manifest(repo_root: Path) -> dict:
    constraints = repo_root / "constraints.txt"
    payload = {
        "schema_version": "1.0",
        "python_requirement": ">=3.11",
        "python_observed": platform.python_version(),
        "constraints_sha256": file_sha256(constraints),
        "gpu_expectation": "optional Kaggle T4x2; not required for fixture validation",
        "network_required_for_fixture": False,
        "persistent_storage_assumed": False,
        "evidence_class": "ENGINEERING_ONLY",
        "created_at": utc_now(),
    }
    return {**payload, "environment_id": f"kaggle.{content_hash(payload)[:24]}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="environment/kaggle_environment.json")
    args = parser.parse_args()
    report = build_manifest(Path(args.repo_root).resolve())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
