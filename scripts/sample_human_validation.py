#!/usr/bin/env python3
"""Export a human-validation sample from a run directory (no annotation execution)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.schemas import Trajectory
from causal_agent_bench.utils.io import read_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", default="data/human_validation/sample.jsonl")
    parser.add_argument("--max-cases", type=int, default=5)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    trajectories = list(read_jsonl(run_dir / "trajectories.jsonl", Trajectory))
    sample = trajectories[: args.max_cases]
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for trajectory in sample:
            handle.write(
                json.dumps(
                    {
                        "instance_id": trajectory.instance_id,
                        "agent_name": trajectory.agent_name,
                        "n_steps": len(trajectory.steps),
                        "labels": {},
                        "notes": "",
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    print(f"wrote {len(sample)} cases to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
