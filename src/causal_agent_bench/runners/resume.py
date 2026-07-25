from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from causal_agent_bench.schemas import Trajectory
from causal_agent_bench.utils.io import read_jsonl, write_json

RunKey = tuple[str, str, int]


def run_key(agent: str, instance_id: str, repeat: int) -> RunKey:
    return (agent, instance_id, repeat)


def completed_run_keys(run_dir: str | Path) -> set[RunKey]:
    path = Path(run_dir) / "trajectories.jsonl"
    if not path.exists():
        return set()
    completed: set[RunKey] = set()
    for trajectory in read_jsonl(path, Trajectory):
        repeat = int(trajectory.metadata.get("repeat", 0))
        completed.add(run_key(trajectory.agent_name, trajectory.instance_id, repeat))
    return completed


def error_run_keys(
    run_dir: str | Path,
    *,
    retriable_only: bool = False,
    skipped_only: bool = False,
) -> set[RunKey]:
    path = Path(run_dir) / "errors.jsonl"
    if not path.exists():
        return set()
    keys: set[RunKey] = set()
    for row in _read_error_rows(path):
        if retriable_only and not row.get("retriable", True):
            continue
        if skipped_only and not row.get("skipped", False):
            continue
        agent = row.get("agent")
        instance = row.get("instance")
        if agent is None or instance is None:
            continue
        keys.add(run_key(str(agent), str(instance), int(row.get("repeat", 0))))
    return keys


def failed_run_keys(
    run_dir: str | Path,
    *,
    retriable_only: bool = True,
    exclude_skipped: bool = True,
) -> set[RunKey]:
    """Keys with errors and no completed trajectory (candidates for retry)."""
    completed = completed_run_keys(run_dir)
    path = Path(run_dir) / "errors.jsonl"
    if not path.exists():
        return set()
    keys: set[RunKey] = set()
    for row in _read_error_rows(path):
        if retriable_only and not row.get("retriable", True):
            continue
        if exclude_skipped and row.get("skipped"):
            continue
        agent = row.get("agent")
        instance = row.get("instance")
        if agent is None or instance is None:
            continue
        keys.add(run_key(str(agent), str(instance), int(row.get("repeat", 0))))
    return keys - completed


def pending_run_keys(expected: set[RunKey], run_dir: str | Path) -> set[RunKey]:
    completed = completed_run_keys(run_dir)
    return expected - completed


def duplicate_run_keys(run_dir: str | Path) -> list[RunKey]:
    path = Path(run_dir) / "trajectories.jsonl"
    if not path.exists():
        return []
    seen: set[RunKey] = set()
    duplicates: list[RunKey] = []
    for trajectory in read_jsonl(path, Trajectory):
        key = run_key(
            trajectory.agent_name,
            trajectory.instance_id,
            int(trajectory.metadata.get("repeat", 0)),
        )
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    return duplicates


def write_checkpoint(
    run_dir: str | Path,
    *,
    completed: int,
    total: int,
    errors: int,
    extra: dict[str, Any] | None = None,
) -> None:
    payload = {
        "completed": completed,
        "total": total,
        "errors": errors,
        "progress_fraction": round(completed / total, 6) if total else None,
    }
    if extra:
        payload.update(extra)
    write_json(Path(run_dir) / "checkpoint.json", payload)


def _read_error_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows
