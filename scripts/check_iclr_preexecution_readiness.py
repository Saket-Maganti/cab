#!/usr/bin/env python3
"""Print the unified, provider-free ICLR pre-execution readiness state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.safety.iclr_preexecution_gate import (
    evaluate_iclr_preexecution_readiness,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-json", type=Path)
    args = parser.parse_args(argv)
    report = evaluate_iclr_preexecution_readiness(args.repo_root)
    if args.write_json:
        output = args.write_json
        if not output.is_absolute():
            output = args.repo_root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return int(report["exit_code"])


def _print_human(report: dict[str, Any]) -> None:
    print(f"current_state: {report['current_state']}")
    print(f"build_complete: {str(report['build_complete']).lower()}")
    print("blockers:")
    for blocker in report["blockers"]:
        print(
            f"- [{blocker['class']}] {blocker['code']}: {blocker['detail']}"
        )
    print(f"exact_next_allowed_action: {report['exact_next_allowed_action']}")
    print("forbidden_actions:")
    for action in report["forbidden_actions"]:
        print(f"- {action}")
    print("evidence_counts:")
    for key, value in report["evidence_counts"].items():
        print(f"- {key}: {value}")
    print("scientific_execution_performed: false")


if __name__ == "__main__":
    raise SystemExit(main())
