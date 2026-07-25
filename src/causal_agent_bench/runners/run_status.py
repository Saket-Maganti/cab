from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.runners.run_completion import (
    infer_completion_state,
    latest_trajectory_info,
    load_run_metadata,
)


def find_latest_run_dirs(results_root: str | Path = "results", *, count: int = 1) -> list[Path]:
    root = Path(results_root)
    if not root.exists():
        return []
    candidates = [
        path
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(("cache", "dry_runs"))
    ]
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[:count]


def find_latest_run_dir(results_root: str | Path = "results") -> Path | None:
    dirs = find_latest_run_dirs(results_root, count=1)
    return dirs[0] if dirs else None


def resolve_run_dir(run_dir: str | Path | None, *, latest: bool = False) -> Path:
    if latest:
        resolved = find_latest_run_dir()
        if resolved is None:
            raise FileNotFoundError("no run directories found under results/")
        return resolved
    if run_dir is None:
        raise ValueError("run-dir is required unless --latest is set")
    path = Path(run_dir)
    if not path.exists():
        raise FileNotFoundError(f"run directory not found: {path}")
    return path


def build_run_status(run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    state = infer_completion_state(run_dir)
    metadata = load_run_metadata(run_dir)
    latest = latest_trajectory_info(run_dir)
    traj_path = run_dir / "trajectories.jsonl"
    file_size = traj_path.stat().st_size if traj_path.exists() else 0
    started = metadata.get("started_at") or metadata.get("timestamp")
    elapsed_seconds = None
    avg_seconds = None
    eta_seconds = None
    if started:
        try:
            start_dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            elapsed_seconds = (datetime.now(UTC) - start_dt.astimezone(UTC)).total_seconds()
            completed = state["completed_trajectories"] or 0
            if completed > 0 and elapsed_seconds is not None:
                avg_seconds = elapsed_seconds / completed
                remaining = (state["expected_trajectories"] or 0) - completed
                if remaining > 0:
                    eta_seconds = avg_seconds * remaining
        except ValueError:
            pass

    return {
        **state,
        "run_name": metadata.get("run_name"),
        "config_hash": metadata.get("config_hash"),
        "latest_instance_id": latest.get("instance_id"),
        "latest_agent_name": latest.get("agent_name"),
        "trajectories_file_bytes": file_size,
        "elapsed_seconds": elapsed_seconds,
        "avg_seconds_per_trajectory": avg_seconds,
        "eta_seconds": eta_seconds,
        "score_allowed_default": state["score_allowed"],
        "analyze_allowed_default": state["analyze_allowed"],
        "export_allowed_default": state["export_allowed"],
    }


def format_run_status(status: dict[str, Any]) -> str:
    lines = [
        "# Run status",
        "",
        f"- **Run directory:** `{status['run_dir']}`",
        f"- **Status:** {status['run_status']}",
        f"- **Completion:** {status['completed_trajectories']}/{status['expected_trajectories']} "
        f"({status.get('progress_percent', '?')}%)",
        f"- **Errors:** {status['errors']}",
        f"- **Evidence level:** {status['evidence_level']}",
        f"- **Scientific evidence:** {status['scientific_evidence']}",
        f"- **Paid calls allowed:** {status['allow_paid_calls']}",
        f"- **Paid calls made:** {status['paid_calls_made']}",
        f"- **Oracle agents:** {', '.join(status['oracle_agents']) or 'none'}",
        f"- **Latest instance:** {status.get('latest_instance_id')}",
        f"- **Latest agent:** {status.get('latest_agent_name')}",
        f"- **Trajectories file size:** {status.get('trajectories_file_bytes', 0)} bytes",
    ]
    if status.get("elapsed_seconds") is not None:
        lines.append(f"- **Elapsed (s):** {status['elapsed_seconds']:.0f}")
    if status.get("avg_seconds_per_trajectory") is not None:
        lines.append(f"- **Avg s/trajectory:** {status['avg_seconds_per_trajectory']:.1f}")
    if status.get("eta_seconds") is not None:
        lines.append(f"- **Rough ETA (s):** {status['eta_seconds']:.0f}")
    lines.extend(
        [
            f"- **Score allowed (default):** {status['score_allowed_default']}",
            f"- **Analyze allowed (default):** {status['analyze_allowed_default']}",
            f"- **Export allowed (default):** {status['export_allowed_default']}",
        ]
    )
    if status.get("interruption_reason"):
        lines.append(f"- **Interruption reason:** {status['interruption_reason']}")
    if status.get("limiter_stop_reason"):
        lines.append(f"- **Limiter stop:** {status['limiter_stop_reason']}")
    return "\n".join(lines) + "\n"
