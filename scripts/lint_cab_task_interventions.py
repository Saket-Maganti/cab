#!/usr/bin/env python3
"""Lint a canonical CAB task/intervention pack without running models."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from causal_agent_bench.safety.task_intervention_lint import (
    lint_task_intervention_dataset,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = lint_task_intervention_dataset(
        args.dataset_dir,
        repo_root=args.repo_root,
        role=args.role,
        strict_explicit_policies=True,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "PASS" if result["passed"] else "BLOCKED"
        print(f"task-intervention-lint: {status}")
        print(f"dataset: {result['dataset']}")
        print(f"role: {result['role']}")
        for key, value in result["counts"].items():
            print(f"{key}: {value}")
        for issue in result["issues"][:25]:
            print(
                f"{issue['severity'].upper()}: {issue['code']} "
                f"{issue['file']}:{issue.get('line', '-')} "
                f"{issue.get('task_id') or '-'} {issue['detail']}"
            )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
