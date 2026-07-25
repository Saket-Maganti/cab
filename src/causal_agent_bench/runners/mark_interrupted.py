from __future__ import annotations

from pathlib import Path

from causal_agent_bench.runners.resume import write_checkpoint
from causal_agent_bench.runners.run_completion import (
    expected_trajectory_total,
    infer_completion_state,
    write_incomplete_run_record,
)
from causal_agent_bench.utils.io import read_json, write_json


def mark_run_interrupted(
    run_dir: str | Path,
    *,
    reason: str = "user stopped long local run",
) -> dict:
    run_dir = Path(run_dir)
    if not run_dir.exists():
        raise FileNotFoundError(f"run directory not found: {run_dir}")

    state = infer_completion_state(run_dir)
    completed = state["completed_trajectories"]
    expected = state["expected_trajectories"] or expected_trajectory_total(run_dir)
    errors = state["errors"]

    write_incomplete_run_record(run_dir, reason=reason)
    write_checkpoint(
        run_dir,
        completed=completed,
        total=expected or completed,
        errors=errors,
        extra={
            "status": "incomplete",
            "interruption_reason": "local_interrupted",
            "scientific_evidence": False,
        },
    )

    status_md = run_dir / "RUN_STATUS.md"
    status_md.write_text(
        "\n".join(
            [
                "# Run status",
                "",
                "- **status:** incomplete / local_interrupted",
                f"- **reason:** {reason}",
                f"- **completed_trajectories:** {completed} / {expected or '?'}",
                "- **scientific_evidence:** false",
                "- **paid_calls_made:** false (or unchanged; verify run_metadata.json)",
                "",
                "Do not score, analyze, or export as final scientific evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    for meta_name in ("run_metadata.json", "metadata.json"):
        meta_path = run_dir / meta_name
        if not meta_path.exists():
            continue
        metadata = read_json(meta_path)
        metadata["completion_state"] = "incomplete"
        metadata["run_status"] = "interrupted"
        metadata["scientific_evidence"] = False
        metadata["interruption_reason"] = reason
        write_json(meta_path, metadata)

    return infer_completion_state(run_dir)
