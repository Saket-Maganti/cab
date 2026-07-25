#!/usr/bin/env python3
"""Generate the canonical hashed CAB study-role registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.safety.split_registry import (
    CANONICAL_SPLIT_REGISTRY_PATH,
    validate_canonical_split_registry,
    write_canonical_split_registry,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(CANONICAL_SPLIT_REGISTRY_PATH))
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the recorded registry against live sources without rewriting it.",
    )
    args = parser.parse_args(argv)
    if args.check:
        issues = validate_canonical_split_registry(
            ROOT,
            registry_path=args.output,
        )
        print(
            json.dumps(
                {
                    "output": args.output,
                    "mode": "check",
                    "issue_count": len(issues),
                    "issues": issues,
                    "passed": not issues,
                },
                sort_keys=True,
            )
        )
        return 0 if not issues else 1

    path, payload = write_canonical_split_registry(ROOT, output_path=args.output)
    print(
        json.dumps(
            {
                "output": str(path),
                "role_count": payload["role_count"],
                "cross_role_overlap_count": payload["cross_role_overlap_count"],
                "passed": payload["passed"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
