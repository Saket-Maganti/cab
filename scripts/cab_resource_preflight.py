#!/usr/bin/env python3
"""Read-only M4 resource report and transparent experiment estimator."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.resources import (
    WorkerMode,
    bootstrap_execution_plan,
    choose_worker_limit,
    estimate_trajectory_resources,
    repository_disk_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument(
        "--worker-mode",
        choices=[mode.value for mode in WorkerMode],
        default=WorkerMode.LOW_MEMORY.value,
    )
    parser.add_argument("--memory-gib", type=float, default=16.0)
    parser.add_argument("--tasks", type=int, default=20)
    parser.add_argument("--conditions", type=int, default=6)
    parser.add_argument("--models", type=int, default=4)
    parser.add_argument("--policies", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seconds-per-trajectory", type=float, default=45.0)
    parser.add_argument("--kib-per-trajectory", type=float, default=64.0)
    parser.add_argument("--bootstrap-mode", choices=["pilot", "final"], default="pilot")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    workers = choose_worker_limit(
        args.worker_mode,
        cpu_count=os.cpu_count(),
        memory_gib=args.memory_gib,
    )
    payload = {
        "schema_version": "cab_resource_preflight_v1",
        "scope": "READ_ONLY_ESTIMATE_NOT_MEASURED",
        "worker_policy": workers,
        "disk": repository_disk_report(args.repo_root),
        "trajectory_estimate": estimate_trajectory_resources(
            tasks=args.tasks,
            conditions_per_task=args.conditions,
            models=args.models,
            policies=args.policies,
            repeats=args.repeats,
            mean_seconds_per_trajectory=args.seconds_per_trajectory,
            mean_kib_per_trajectory=args.kib_per_trajectory,
            workers=int(workers["workers"]),
        ),
        "bootstrap": bootstrap_execution_plan(mode=args.bootstrap_mode),
        "scientific_execution_performed": False,
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
