from __future__ import annotations

from pathlib import Path

from causal_agent_bench.schemas import Trajectory
from causal_agent_bench.utils.io import read_jsonl

RunKey = tuple[str, str, int]


def completed_run_keys(run_dir: str | Path) -> set[RunKey]:
    path = Path(run_dir) / "trajectories.jsonl"
    if not path.exists():
        return set()
    completed: set[RunKey] = set()
    for trajectory in read_jsonl(path, Trajectory):
        repeat = int(trajectory.metadata.get("repeat", 0))
        completed.add((trajectory.agent_name, trajectory.instance_id, repeat))
    return completed
