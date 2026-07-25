#!/usr/bin/env python3
"""Run CAB's provider-free maximum-ceiling build or execution-entry gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.safety.max_ceiling_gate import (
    evaluate_max_ceiling_gate,
    write_current_state_reports,
    write_gate_reports,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=("build", "execution"),
        default="build",
        help=(
            "build exits zero when repository-controlled pre-execution checks pass; "
            "execution also requires human review, approval, and evidence prerequisites"
        ),
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print only; do not update canonical state/gate reports.",
    )
    args = parser.parse_args(argv)

    payload = evaluate_max_ceiling_gate(ROOT)
    if not args.no_write:
        write_gate_reports(payload, repo_root=ROOT)
        write_current_state_reports(payload["state_snapshot"], repo_root=ROOT)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print(payload["status"])
        print(f"current_state={payload['current_state']}")
        print(f"build_complete={str(payload['build_complete']).lower()}")
        print(
            "scientific_execution_allowed="
            f"{str(payload['scientific_execution_allowed']).lower()}"
        )
        print("blockers:")
        blockers = [*payload["build_blockers"], *payload["external_blockers"]]
        if not blockers:
            print("- none")
        for row in blockers:
            print(f"- {row['scope']}:{row['check_id']}: {row['detail']}")
        print(f"next_action={payload['exact_next_allowed_action']}")
        print(f"next_command={payload['exact_next_allowed_command']}")
        print("forbidden_commands:")
        for command in payload["forbidden_commands"]:
            print(f"- {command}")

    if args.scope == "build":
        return 0 if payload["build_complete"] else 1
    return 0 if payload["scientific_execution_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

