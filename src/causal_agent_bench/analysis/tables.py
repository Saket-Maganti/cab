from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from causal_agent_bench.analysis.load_results import RunResults


def bootstrap_mean_ci(
    values: list[float] | pd.Series | np.ndarray,
    *,
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int = 0,
) -> tuple[float | None, float | None, float | None]:
    array = np.asarray([float(value) for value in values if pd.notna(value)], dtype=float)
    if array.size == 0:
        return None, None, None
    if array.size == 1:
        value = round(float(array[0]), 6)
        return value, value, value
    rng = np.random.default_rng(seed)
    sample_means = rng.choice(array, size=(n_boot, array.size), replace=True).mean(axis=1)
    alpha = (1 - ci) / 2
    return (
        round(float(array.mean()), 6),
        round(float(np.quantile(sample_means, alpha)), 6),
        round(float(np.quantile(sample_means, 1 - alpha)), 6),
    )


def build_all_tables(data: RunResults, output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    tables = {
        "table1_benchmark_statistics": benchmark_statistics_table(data),
        "table2_main_agent_performance": main_agent_performance_table(data),
        "table3_intervention_family_performance": intervention_family_performance_table(data),
        "table4_ablation_results": placeholder_table(
            "Ablation results",
            "not yet run",
            "Run scaffold or prompt ablation experiments before filling this table.",
        ),
        "table5_human_validation_agreement": placeholder_table(
            "Human validation agreement",
            "not yet run",
            "Run the human validation sample before filling this table.",
        ),
        "paired_clean_vs_intervention": paired_clean_vs_intervention_table(data),
    }
    for name, frame in tables.items():
        paths.extend(write_table_bundle(frame, out / name))
    return paths


def benchmark_statistics_table(data: RunResults) -> pd.DataFrame:
    instances = data.instances_df
    clean = instances[instances["condition"] == "clean"]
    intervention = instances[instances["condition"] == "intervention"]
    domains = ", ".join(
        f"{domain} ({count})" for domain, count in clean["domain"].value_counts().sort_index().items()
    )
    difficulties = ", ".join(
        f"{difficulty} ({count})"
        for difficulty, count in clean["difficulty"].value_counts().sort_index().items()
    )
    rows = [
        ("base_tasks", int(clean["base_task_id"].nunique())),
        ("clean_instances", int(len(clean))),
        ("intervention_instances", int(len(intervention))),
        ("domains", domains or "not yet run"),
        ("difficulty_levels", difficulties or "not yet run"),
        ("avg_tools_required", _round(clean["gold_tool_count"].mean())),
        ("avg_available_tools", _round(instances["available_tool_count"].mean())),
        ("avg_max_steps", _round(clean["max_steps"].mean())),
    ]
    return pd.DataFrame(rows, columns=["statistic", "value"])


def main_agent_performance_table(data: RunResults) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scores = data.scores_df
    for agent, row in sorted(data.aggregate.get("by_agent", {}).items()):
        agent_scores = scores[scores["agent_name"] == agent]
        clean_scores = agent_scores[agent_scores["diagnostic_condition"] == "clean"]
        intervention_scores = agent_scores[agent_scores["diagnostic_condition"] == "intervention"]
        _, clean_low, clean_high = bootstrap_mean_ci(
            clean_scores.get("final_success_binary", pd.Series(dtype=float)), seed=11
        )
        _, int_low, int_high = bootstrap_mean_ci(
            intervention_scores.get("final_success_binary", pd.Series(dtype=float)), seed=13
        )
        rows.append(
            {
                "agent": agent,
                "clean_success": row.get("clean_success_rate"),
                "clean_success_ci95": _ci_text(clean_low, clean_high),
                "intervention_success": row.get("intervention_success_rate"),
                "intervention_success_ci95": _ci_text(int_low, int_high),
                "acrs": row.get("acrs"),
                "tool_precision": row.get("tool_precision"),
                "required_tool_recall": row.get("required_tool_recall"),
                "recovery_rate": row.get("tool_error_recovery_binary"),
                "contradiction_resolution": row.get("contradiction_resolved_binary"),
            }
        )
    return pd.DataFrame(rows)


def intervention_family_performance_table(data: RunResults) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family, row in sorted(data.aggregate.get("by_intervention_family", {}).items()):
        if family == "clean":
            continue
        rows.append(
            {
                "intervention_family": family,
                "n": row.get("n"),
                "final_success_rate": row.get("final_success_rate"),
                "trajectory_faithfulness": row.get("trajectory_faithfulness"),
            }
        )
    if not rows:
        return placeholder_table(
            "Intervention family performance",
            "not yet run",
            "No intervention rows were found.",
        )
    return pd.DataFrame(rows)


def paired_clean_vs_intervention_table(data: RunResults) -> pd.DataFrame:
    scores = data.scores_df.copy()
    if scores.empty:
        return placeholder_table("Paired comparison", "not yet run", "No score rows were found.")
    scores["base_task_id"] = scores["diagnostic_base_task_id"]
    rows: list[dict[str, Any]] = []
    for agent, agent_scores in scores.groupby("agent_name"):
        clean = (
            agent_scores[agent_scores["diagnostic_condition"] == "clean"]
            .groupby("base_task_id")["final_success_binary"]
            .mean()
        )
        intervention = (
            agent_scores[agent_scores["diagnostic_condition"] == "intervention"]
            .groupby("base_task_id")["final_success_binary"]
            .mean()
        )
        joined = pd.concat([clean.rename("clean"), intervention.rename("intervention")], axis=1).dropna()
        if joined.empty:
            rows.append(
                {
                    "agent": agent,
                    "n_pairs": 0,
                    "mean_clean": None,
                    "mean_intervention": None,
                    "mean_difference": None,
                    "cohen_dz": None,
                    "paired_t_p_value": None,
                }
            )
            continue
        diff = joined["clean"] - joined["intervention"]
        p_value = None
        if len(joined) > 1 and diff.std(ddof=1) > 0:
            p_value = float(stats.ttest_rel(joined["clean"], joined["intervention"]).pvalue)
        rows.append(
            {
                "agent": agent,
                "n_pairs": int(len(joined)),
                "mean_clean": _round(joined["clean"].mean()),
                "mean_intervention": _round(joined["intervention"].mean()),
                "mean_difference": _round(diff.mean()),
                "cohen_dz": _round(diff.mean() / diff.std(ddof=1)) if len(diff) > 1 and diff.std(ddof=1) > 0 else None,
                "paired_t_p_value": _round(p_value),
            }
        )
    return pd.DataFrame(rows)


def statistical_summary(data: RunResults) -> dict[str, Any]:
    paired = paired_clean_vs_intervention_table(data)
    return {
        "bootstrap": {
            row["agent"]: {
                "clean_success_ci95": row.get("clean_success_ci95"),
                "intervention_success_ci95": row.get("intervention_success_ci95"),
            }
            for row in main_agent_performance_table(data).to_dict(orient="records")
        },
        "paired_clean_vs_intervention": paired.to_dict(orient="records"),
        "per_family_degradation": {
            agent: row.get("families", {})
            for agent, row in data.aggregate.get("by_agent", {}).items()
        },
        "spearman_clean_vs_acrs": data.aggregate.get("ranking_instability", {}).get(
            "spearman_clean_vs_acrs"
        ),
    }


def placeholder_table(title: str, status: str, note: str) -> pd.DataFrame:
    return pd.DataFrame([{"table": title, "status": status, "note": note}])


def write_table_bundle(frame: pd.DataFrame, stem: Path) -> list[Path]:
    paths = [stem.with_suffix(".csv"), stem.with_suffix(".md"), stem.with_suffix(".tex")]
    frame.to_csv(paths[0], index=False)
    paths[1].write_text(dataframe_to_markdown(frame), encoding="utf-8")
    paths[2].write_text(frame.to_latex(index=False, escape=True), encoding="utf-8")
    return paths


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._\n"
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(_fmt_cell(value) for value in row) + " |")
    return "\n".join(lines) + "\n"


def _ci_text(low: float | None, high: float | None) -> str | None:
    if low is None or high is None:
        return None
    return f"[{low:.3f}, {high:.3f}]"


def _round(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)


def _fmt_cell(value: Any) -> str:
    if value is None or pd.isna(value):
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value).replace("|", "\\|")
