from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.runners.resume import completed_run_keys
from causal_agent_bench.utils.io import read_json


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return read_json(path)


def trajectory_count(run_dir: Path) -> int:
    path = run_dir / "trajectories.jsonl"
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def error_count(run_dir: Path) -> int:
    path = run_dir / "errors.jsonl"
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def load_checkpoint(run_dir: Path) -> dict[str, Any] | None:
    return _read_json_if_exists(run_dir / "checkpoint.json")


def load_run_metadata(run_dir: Path) -> dict[str, Any]:
    for name in ("run_metadata.json", "metadata.json"):
        payload = _read_json_if_exists(run_dir / name)
        if payload:
            return payload
    return {}


def _strict_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, int | float):
        return value == 1
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no", ""}:
        return False
    return False


def expected_trajectory_total(run_dir: Path, metadata: dict[str, Any] | None = None) -> int | None:
    checkpoint = load_checkpoint(run_dir)
    if checkpoint and checkpoint.get("total") is not None:
        return int(checkpoint["total"])
    meta = metadata or load_run_metadata(run_dir)
    n_instances = meta.get("n_instances")
    agents = meta.get("agents") or meta.get("agent_runs") or []
    num_repeats = int(meta.get("num_repeats", 1))
    if n_instances is not None and agents:
        return int(n_instances) * len(agents) * num_repeats
    return None


def infer_completion_state(run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    metadata = load_run_metadata(run_dir)
    checkpoint = load_checkpoint(run_dir) or {}
    incomplete_doc = _read_json_if_exists(run_dir / "INCOMPLETE_RUN.json")
    status_md = (run_dir / "RUN_STATUS.md").exists()
    dry_run_meta = _read_json_if_exists(run_dir / "dry_run_metadata.json")

    completed = int(checkpoint.get("completed", trajectory_count(run_dir)))
    expected = expected_trajectory_total(run_dir, metadata)
    errors = int(checkpoint.get("errors", error_count(run_dir)))
    status = str(checkpoint.get("status") or "").lower()
    interruption = checkpoint.get("interruption_reason")

    if dry_run_meta is not None:
        run_status = "dry_run"
    elif status in {"incomplete", "interrupted"} or interruption or incomplete_doc or status_md:
        run_status = "interrupted"
    elif expected is not None and completed >= expected:
        run_status = "complete"
    elif expected is not None and completed < expected:
        run_status = "interrupted" if (incomplete_doc or status_md or interruption) else "incomplete"
    elif expected is None and completed > 0 and not (incomplete_doc or status_md or interruption):
        run_status = "complete"
    else:
        run_status = "unknown"

    limiter_stop = checkpoint.get("limiter_stop_reason")
    if limiter_stop:
        run_status = "interrupted"

    scientific_evidence = _strict_bool(metadata.get("scientific_evidence", False))
    evidence_level = metadata.get("scientific_evidence_level") or metadata.get("evidence_scope") or "unknown"
    allow_paid = _strict_bool(metadata.get("allow_paid_calls", False))
    paid_calls_made = metadata.get("paid_calls_made")

    oracle_agents = [
        name
        for name in (metadata.get("agents") or [])
        if "oracle" in str(name).lower()
    ]
    for agent_run in metadata.get("agent_runs") or []:
        agent_name = agent_run.get("agent") or agent_run.get("name") or ""
        if "oracle" in str(agent_name).lower():
            label = agent_run.get("name") or agent_name
            if label not in oracle_agents:
                oracle_agents.append(label)

    percent = round(100.0 * completed / expected, 2) if expected else None
    return {
        "run_dir": str(run_dir),
        "run_status": run_status,
        "completion_state": "complete" if run_status == "complete" else "incomplete",
        "completed_trajectories": completed,
        "expected_trajectories": expected,
        "progress_percent": percent,
        "errors": errors,
        "scientific_evidence": scientific_evidence,
        "evidence_level": evidence_level,
        "allow_paid_calls": allow_paid,
        "paid_calls_made": paid_calls_made,
        "oracle_agents": oracle_agents,
        "limiter_stop_reason": limiter_stop,
        "interruption_reason": interruption or (incomplete_doc or {}).get("reason"),
        "score_allowed": run_status == "complete",
        "analyze_allowed": run_status == "complete",
        "export_allowed": run_status == "complete",
    }


def assert_complete_for_pipeline(
    run_dir: str | Path,
    *,
    operation: str,
    allow_incomplete: bool = False,
) -> dict[str, Any]:
    state = infer_completion_state(run_dir)
    if state["completion_state"] == "complete":
        return state
    if allow_incomplete:
        return state
    completed = state["completed_trajectories"]
    expected = state["expected_trajectories"]
    raise ValueError(
        f"refusing {operation} on incomplete run {state['run_dir']}: "
        f"{completed}/{expected or '?'} trajectories; "
        f"status={state['run_status']!r}. "
        f"Pass --allow-incomplete to proceed with preliminary/incomplete labeling."
    )


def write_incomplete_run_record(
    run_dir: str | Path,
    *,
    reason: str,
    timestamp: str | None = None,
) -> Path:
    run_dir = Path(run_dir)
    state = infer_completion_state(run_dir)
    payload = {
        "status": "interrupted",
        "completion_state": "incomplete",
        "scientific_evidence": False,
        "paid_calls_made": state.get("paid_calls_made", False),
        "allow_paid_calls": state.get("allow_paid_calls", False),
        "completed_trajectories": state["completed_trajectories"],
        "expected_trajectories": state["expected_trajectories"],
        "reason": reason,
        "timestamp": timestamp or datetime.now(UTC).isoformat(),
    }
    path = run_dir / "INCOMPLETE_RUN.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = run_dir / "INCOMPLETE_RUN.md"
    md_path.write_text(
        "\n".join(
            [
                "# Incomplete / interrupted run",
                "",
                "- **status:** interrupted / incomplete",
                "- **scientific_evidence:** false",
                f"- **paid_calls_made:** {payload['paid_calls_made']}",
                f"- **completed_trajectories:** {payload['completed_trajectories']}",
                f"- **expected_trajectories:** {payload['expected_trajectories']}",
                f"- **reason:** {reason}",
                f"- **timestamp:** {payload['timestamp']}",
                "",
                "Do not score, analyze, or export this run as final scientific evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def latest_trajectory_info(run_dir: Path) -> dict[str, str | None]:
    path = run_dir / "trajectories.jsonl"
    if not path.exists():
        return {"instance_id": None, "agent_name": None}
    last_line = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            last_line = line
    if not last_line:
        return {"instance_id": None, "agent_name": None}
    row = json.loads(last_line)
    return {
        "instance_id": row.get("instance_id"),
        "agent_name": row.get("agent_name"),
    }


def duplicate_trajectory_keys(run_dir: Path) -> int:
    keys = completed_run_keys(run_dir)
    return trajectory_count(run_dir) - len(keys)
