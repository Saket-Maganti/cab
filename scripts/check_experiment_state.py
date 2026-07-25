#!/usr/bin/env python3
"""Validate experiment run state against the state machine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.release.experiment_state import (
    infer_experiment_state,
    validate_experiment_state,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check experiment run state.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = infer_experiment_state(args.run_dir)
    issues = validate_experiment_state(args.run_dir)
    result["validation_issues"] = issues

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"state: {result['state']}")
        print(f"run_status: {result.get('run_status')}")
        print(f"evidence_scope: {result.get('evidence_scope')}")
        print(f"allowed_claims: {result.get('allowed_claims')}")
        for issue in issues:
            print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
