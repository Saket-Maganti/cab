#!/usr/bin/env python3
"""Run the provider-free CAB Phase 2/3 leakage eligibility gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from causal_agent_bench.safety.leakage_gate import run_cab_leakage_gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument(
        "--output",
        default="audits/max_ceiling/leakage_gate/CAB_PHASE2_PHASE3_GATE.json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete machine-readable gate result.",
    )
    args = parser.parse_args(argv)
    result = run_cab_leakage_gate(
        args.repo_root,
        output_path=args.output,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(
            "run_eligible_under_phase2_phase3: "
            f"{str(result['run_eligible_under_phase2_phase3']).lower()}"
        )
        print(f"internal_blocker_count: {result['internal_blocker_count']}")
        print(f"output: {result.get('output_path', args.output)}")
        for blocker in result["internal_blockers"]:
            print(
                "BLOCKER: "
                f"{blocker['gate']} / {blocker.get('role') or 'repository'}: "
                f"{blocker['detail']}"
            )
    return 0 if result["run_eligible_under_phase2_phase3"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
