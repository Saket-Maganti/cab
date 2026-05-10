from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from causal_agent_bench.analysis.load_results import RunResults
from causal_agent_bench.utils.io import write_jsonl

CATEGORY_DESCRIPTIONS = {
    "high_clean_low_intervention": "Agent has high clean success but low intervention success.",
    "final_success_trajectory_failure": "Final answer succeeded but trajectory score exposed a failure.",
    "tool_corruption_not_detected": "Tool corruption condition ended without robust recovery.",
    "memory_corruption_blind_trust": "Memory corruption appears blindly trusted.",
    "contradiction_ignored": "Observation conflict was not detected.",
    "premature_stopping": "Agent stopped before required evidence was gathered.",
}


def extract_error_cases(data: RunResults, output_dir: str | Path, *, max_cases: int = 5) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    cases_by_category = mine_error_cases(data, max_cases=max_cases)
    paths: list[Path] = []
    summary_lines = ["# Error Case Index", ""]
    for category, cases in cases_by_category.items():
        jsonl_path = out / f"{category}.jsonl"
        md_path = out / f"{category}.md"
        write_jsonl(jsonl_path, cases)
        md_path.write_text(_cases_to_markdown(category, cases), encoding="utf-8")
        paths.extend([jsonl_path, md_path])
        summary_lines.append(f"- `{category}`: {len(cases)} cases")
    summary_path = out / "README.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    paths.append(summary_path)
    return paths


def mine_error_cases(data: RunResults, *, max_cases: int = 5) -> dict[str, list[dict[str, Any]]]:
    scores = data.scores_df.copy()
    if scores.empty:
        return {category: [] for category in CATEGORY_DESCRIPTIONS}
    categories = {
        "high_clean_low_intervention": _high_clean_low_intervention(data),
        "final_success_trajectory_failure": scores[
            scores["final_success_binary"].eq(1) & scores["trajectory_success_binary"].eq(0)
        ],
        "tool_corruption_not_detected": scores[
            scores["diagnostic_intervention_family"].eq("tool_corruption")
            & (scores["tool_error_recovery_binary"].eq(False) | scores["final_success_binary"].eq(0))
        ],
        "memory_corruption_blind_trust": scores[
            scores["diagnostic_intervention_family"].eq("memory_corruption")
            & scores["memory_blind_trust_failure_binary"].eq(True)
        ],
        "contradiction_ignored": scores[
            scores["diagnostic_intervention_family"].eq("observation_conflict")
            & scores["contradiction_detected_binary"].eq(False)
        ],
        "premature_stopping": scores[scores["premature_stop_binary"].eq(True)],
    }
    return {
        category: [
            _case_payload(data, row)
            for row in frame.head(max_cases).to_dict(orient="records")
        ]
        for category, frame in categories.items()
    }


def _high_clean_low_intervention(data: RunResults) -> pd.DataFrame:
    agents = [
        agent
        for agent, row in data.aggregate.get("by_agent", {}).items()
        if (row.get("clean_success_rate") or 0) >= 0.8
        and (row.get("intervention_success_rate") or 0) <= 0.5
    ]
    if not agents:
        return data.scores_df.iloc[0:0]
    return data.scores_df[
        data.scores_df["agent_name"].isin(agents)
        & data.scores_df["diagnostic_condition"].eq("intervention")
        & data.scores_df["final_success_binary"].eq(0)
    ]


def _case_payload(data: RunResults, row: dict[str, Any]) -> dict[str, Any]:
    instance_id = row["instance_id"]
    agent = row["agent_name"]
    instance = next((item for item in data.instances if item.instance_id == instance_id), None)
    legacy_task = next((item for item in data.legacy_tasks if item.task_id == instance_id), None)
    trajectory = next(
        (
            trajectory
            for trajectory in data.trajectories
            if trajectory.instance_id == instance_id and trajectory.agent_name == agent
        ),
        None,
    )
    user_instruction = (
        instance.base_task.goal.user_instruction
        if instance is not None
        else legacy_task.user_goal
        if legacy_task is not None
        else ""
    )
    return {
        "instance_id": instance_id,
        "agent": agent,
        "intervention_family": row.get("diagnostic_intervention_family"),
        "user_instruction": user_instruction,
        "tool_calls": _tool_calls(trajectory),
        "observations": _observations(trajectory),
        "final_answer": trajectory.final_answer if trajectory else None,
        "metric_diagnosis": {
            key: value
            for key, value in row.items()
            if key
            in {
                "final_success_binary",
                "trajectory_success_binary",
                "premature_stop_binary",
                "missing_required_tool_count",
                "tool_error_recovery_binary",
                "contradiction_detected_binary",
                "memory_blind_trust_failure_binary",
            }
        },
    }


def _tool_calls(trajectory) -> list[dict[str, Any]]:
    if trajectory is None:
        return []
    calls = []
    for step in trajectory.steps:
        action = step.get("action")
        if isinstance(action, dict) and isinstance(action.get("tool_call"), dict):
            calls.append(action["tool_call"])
    return calls


def _observations(trajectory) -> list[dict[str, Any]]:
    if trajectory is None:
        return []
    observations = []
    for step in trajectory.steps:
        observation = step.get("observation")
        if isinstance(observation, dict):
            observations.append(observation)
    return observations


def _cases_to_markdown(category: str, cases: list[dict[str, Any]]) -> str:
    lines = ["# " + category.replace("_", " ").title(), "", CATEGORY_DESCRIPTIONS[category], ""]
    if not cases:
        lines.append("_No matching cases in this run._")
        return "\n".join(lines) + "\n"
    for case in cases:
        lines.extend(
            [
                f"## {case['agent']} on {case['instance_id']}",
                "",
                f"- Intervention family: `{case.get('intervention_family')}`",
                f"- User instruction: {case.get('user_instruction')}",
                f"- Final answer: {case.get('final_answer')}",
                f"- Tool calls: {', '.join(call.get('tool_name', 'unknown') for call in case.get('tool_calls', [])) or 'none'}",
                f"- Metric diagnosis: `{case.get('metric_diagnosis')}`",
                "",
            ]
        )
    return "\n".join(lines)
