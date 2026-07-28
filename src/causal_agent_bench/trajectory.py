from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from causal_agent_bench.schemas import Trajectory, TrajectoryV2


def migrate_trajectory_v2(trajectory: Trajectory | TrajectoryV2 | dict[str, Any]) -> TrajectoryV2:
    """Validate a current or legacy trajectory payload as Trajectory Schema v2."""

    if isinstance(trajectory, TrajectoryV2):
        return trajectory
    if isinstance(trajectory, Trajectory):
        return TrajectoryV2.model_validate(trajectory.model_dump(mode="python"))
    return TrajectoryV2.model_validate(trajectory)


def trajectory_to_markdown(trajectory: Trajectory | TrajectoryV2 | dict[str, Any]) -> str:
    """Render a compact, audit-friendly trajectory transcript."""

    record = migrate_trajectory_v2(trajectory)
    lines = [
        f"# Trajectory {record.run_id} / {record.instance_id}",
        "",
        f"- Schema version: `{record.schema_version}`",
        f"- Base task: `{record.base_task_id}`",
        f"- Intervention: `{record.intervention_id or 'clean'}`",
        f"- Agent: `{record.agent_id}`",
        f"- Stop reason: `{record.stop_reason}`",
        f"- Final answer: {record.final_answer or 'None'}",
        "",
        "## Provider / Model",
        "",
    ]
    if record.provider_model_metadata:
        for key, value in sorted(record.provider_model_metadata.items()):
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- Not recorded.")

    if record.token_cost_metadata:
        lines.extend(["", "## Token / Cost Metadata", ""])
        for key, value in sorted(record.token_cost_metadata.items()):
            lines.append(f"- `{key}`: `{value}`")

    if record.raac_metadata:
        lines.extend(["", "## RAAC", ""])
        for key in (
            "variant",
            "comparison_mode",
            "evidence_class",
            "observable_signals_only",
        ):
            if key in record.raac_metadata:
                lines.append(f"- `{key}`: `{record.raac_metadata[key]}`")
        overhead = record.raac_metadata.get("overhead")
        if isinstance(overhead, dict):
            lines.append(f"- `overhead`: `{overhead}`")

    lines.extend(["", "## Steps", ""])
    if not record.steps:
        lines.append("No steps recorded.")
        return "\n".join(lines) + "\n"

    for step in record.steps:
        lines.extend(
            [
                f"### Step {step.step_index}",
                "",
                f"- Parser status: `{step.parser_status}`",
                f"- Tool error status: `{step.tool_error_status}`",
                f"- Recovery marker: `{step.recovery_marker}`",
                f"- Contradiction marker: `{step.contradiction_marker}`",
                f"- Memory-use marker: `{step.memory_use_marker}`",
                f"- RAAC state: `{step.raac_state}`",
                f"- RAAC decision: `{step.raac_decision}`",
                f"- RAAC signals: `{step.raac_signals}`",
            ]
        )
        if step.raw_model_output is not None:
            lines.extend(["", "Raw model output:", "", "```text", step.raw_model_output, "```"])
        if step.parsed_action is not None:
            lines.append(f"- Parsed action outcome: `{step.parsed_action.outcome}`")
        if step.tool_call is not None:
            lines.append(f"- Tool call: `{step.tool_call.tool_name}`")
            lines.append(f"- Tool arguments: `{step.tool_arguments}`")
        if step.tool_result is not None:
            lines.append(f"- Tool result error: `{step.tool_result.error}`")
            lines.append(f"- Tool result corrupted: `{step.tool_result.is_corrupted}`")
        if step.final_answer is not None:
            lines.append(f"- Final answer: {step.final_answer}")
        if step.stop_reason is not None:
            lines.append(f"- Stop reason: `{step.stop_reason}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_trajectory_markdown(
    trajectory: Trajectory | TrajectoryV2 | dict[str, Any],
    output_dir: str | Path,
) -> Path:
    """Write a readable markdown transcript and return its path."""

    record = migrate_trajectory_v2(trajectory)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename(f"{record.run_id}_{record.agent_id}_{record.instance_id}.md")
    path = destination / filename
    path.write_text(trajectory_to_markdown(record), encoding="utf-8")
    return path


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "trajectory.md"
