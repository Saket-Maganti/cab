from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.runners.run_completion import infer_completion_state, load_run_metadata
from causal_agent_bench.utils.io import read_json


def index_run_directory(run_dir: Path) -> dict[str, Any]:
    state = infer_completion_state(run_dir)
    metadata = load_run_metadata(run_dir)
    aggregate_path = run_dir / "aggregate_scores.json"
    key_metrics: dict[str, Any] = {}
    if aggregate_path.exists():
        aggregate = read_json(aggregate_path)
        key_metrics = {
            "n_score_records": aggregate.get("n_score_records"),
            "n_agents": aggregate.get("n_agents"),
            "n_instances": aggregate.get("n_instances"),
        }
    return {
        "run_id": run_dir.name,
        "path": str(run_dir),
        "run_name": metadata.get("run_name"),
        "config": metadata.get("run_name"),
        "dataset": metadata.get("benchmark_location") or metadata.get("benchmark_instances_path"),
        "agents": metadata.get("agents") or [],
        "provider_type": metadata.get("provider_type"),
        "status": state["run_status"],
        "completion_state": state["completion_state"],
        "evidence_level": state["evidence_level"],
        "scientific_evidence": state["scientific_evidence"],
        "completed_trajectories": state["completed_trajectories"],
        "expected_trajectories": state["expected_trajectories"],
        "paid_calls_made": state["paid_calls_made"],
        "allow_paid_calls": state["allow_paid_calls"],
        "oracle_agents": state["oracle_agents"],
        "timestamp": metadata.get("started_at") or metadata.get("timestamp"),
        "indexed_at": datetime.now(UTC).isoformat(),
        "key_metrics": key_metrics,
    }


def index_runs(results_root: str | Path = "results") -> list[dict[str, Any]]:
    root = Path(results_root)
    entries: list[dict[str, Any]] = []
    if not root.exists():
        return entries
    for path in sorted(root.iterdir()):
        if not path.is_dir() or path.name in {"cache", "dry_runs"}:
            continue
        if not (path / "run_metadata.json").exists() and not (path / "metadata.json").exists():
            continue
        entries.append(index_run_directory(path))
    return entries


def write_run_index(
    results_root: str | Path = "results",
    *,
    json_path: str | Path | None = None,
    jsonl_path: str | Path | None = None,
) -> tuple[Path, Path]:
    root = Path(results_root)
    entries = index_runs(root)
    json_out = Path(json_path or root / "run_index.json")
    jsonl_out = Path(jsonl_path or root / "RUN_INDEX.jsonl")
    json_out.write_text(json.dumps({"runs": entries, "count": len(entries)}, indent=2) + "\n", encoding="utf-8")
    with jsonl_out.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
    return json_out, jsonl_out
