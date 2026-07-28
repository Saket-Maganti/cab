from __future__ import annotations

import json
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
        "table2_oracle_sanity_check": oracle_sanity_check_table(data),
        "table3_intervention_family_performance": intervention_family_performance_table(data),
        "table4_ablation_results": ablation_results_table(data),
        "table4_ablation_placeholder_or_results": ablation_results_table(data),
        "table5_human_validation_agreement": human_validation_agreement_table(data),
        "table6_performance_vs_cost": performance_vs_cost_table(data),
        "table7_robustness_vs_cost": robustness_vs_cost_table(data),
        "paired_clean_vs_intervention": paired_clean_vs_intervention_table(data),
        "table_ranking_instability": ranking_instability_table(data),
    }
    for name, frame in tables.items():
        frame = with_asset_metadata(frame, data)
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
        ("evidence_scope", _evidence_scope(data)),
        ("base_tasks", int(clean["base_task_id"].nunique())),
        ("clean_instances", len(clean)),
        ("intervention_instances", len(intervention)),
        ("domains", domains or "not yet run"),
        ("difficulty_levels", difficulties or "not yet run"),
        ("avg_tools_required", _round(clean["gold_tool_count"].mean())),
        ("avg_available_tools", _round(instances["available_tool_count"].mean())),
        ("avg_max_steps", _round(clean["max_steps"].mean())),
    ]
    return pd.DataFrame(rows, columns=["statistic", "value"])


def main_agent_performance_table(data: RunResults, *, include_oracle: bool = False) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scores = data.scores_df
    trajectories = data.trajectories_df
    for agent, row in sorted(data.aggregate.get("by_agent", {}).items()):
        if not include_oracle and _is_oracle_agent(agent):
            continue
        agent_scores = scores[scores["agent_name"] == agent]
        clean_scores = agent_scores[agent_scores["diagnostic_condition"] == "clean"]
        intervention_scores = agent_scores[agent_scores["diagnostic_condition"] == "intervention"]
        clean_mean, clean_low, clean_high = bootstrap_mean_ci(
            clean_scores.get("final_success_binary", pd.Series(dtype=float)), seed=11
        )
        int_mean, int_low, int_high = bootstrap_mean_ci(
            intervention_scores.get("final_success_binary", pd.Series(dtype=float)), seed=13
        )
        absolute_degradation = (
            clean_mean - int_mean if clean_mean is not None and int_mean is not None else None
        )
        agent_trajectories = trajectories[trajectories["agent_name"] == agent]
        rows.append(
            {
                "agent": agent,
                "evidence_scope": _evidence_scope(data),
                "clean_success": row.get("clean_success_rate"),
                "clean_success_ci95": _ci_text(clean_low, clean_high),
                "intervention_success": row.get("intervention_success_rate"),
                "intervention_success_ci95": _ci_text(int_low, int_high),
                "absolute_degradation": _round(absolute_degradation),
                "relative_degradation": row.get("relative_degradation"),
                "acrs": row.get("acrs"),
                "acrs_ci95": _ratio_ci(
                    clean_scores.get("final_success_binary", pd.Series(dtype=float)),
                    intervention_scores.get("final_success_binary", pd.Series(dtype=float)),
                    seed=17,
                ),
                "tool_precision": row.get("tool_precision"),
                "required_tool_recall": row.get("required_tool_recall"),
                "invalid_tool_call_rate": _rate_from_count(
                    agent_scores.get("invalid_tool_call_count", pd.Series(dtype=float))
                ),
                "unnecessary_tool_call_rate": row.get("unnecessary_tool_call_rate"),
                "recovery_rate": row.get("tool_error_recovery_binary"),
                "contradiction_resolution": row.get("contradiction_resolved_binary"),
                "memory_verification": row.get("memory_verified_binary"),
                "premature_stop_rate": row.get("premature_stop_binary"),
                "avg_steps": _round(agent_trajectories.get("n_steps", pd.Series(dtype=float)).mean()),
                "avg_latency_s": _round(
                    agent_trajectories.get("latency_s", pd.Series(dtype=float)).dropna().mean()
                ),
                "avg_cost_per_task_usd": row.get("avg_cost_per_task_usd"),
                "avg_model_calls_per_task": row.get("avg_model_calls_per_task"),
                "avg_tool_calls_per_task": row.get("avg_tool_calls_per_task"),
                "cost_normalized_success": row.get("cost_normalized_success"),
                "cost_normalized_acrs": row.get("cost_normalized_acrs"),
                "latency_normalized_success": row.get("latency_normalized_success"),
                "latency_normalized_acrs": row.get("latency_normalized_acrs"),
                "estimated_cost_usd": _round(
                    agent_trajectories.get("estimated_cost_usd", pd.Series(dtype=float))
                    .dropna()
                    .sum()
                ),
            }
        )
    if not rows:
        return placeholder_table(
            "Main agent performance",
            "not yet run",
            "No non-oracle agent rows were found. Oracle rows are reported separately.",
        )
    return pd.DataFrame(rows)


def performance_vs_cost_table(data: RunResults, *, include_oracle: bool = False) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for agent, aggregate_row in sorted(data.aggregate.get("by_agent", {}).items()):
        if not include_oracle and _is_oracle_agent(agent):
            continue
        trajectories = data.trajectories_df[data.trajectories_df["agent_name"] == agent]
        scores = data.scores_df[data.scores_df["agent_name"] == agent]
        rows.append(
            {
                "agent": agent,
                "evidence_scope": _evidence_scope(data),
                "n": len(scores),
                "overall_success": _round(
                    scores.get("final_success_binary", pd.Series(dtype=float)).dropna().mean()
                ),
                "clean_success": aggregate_row.get("clean_success_rate"),
                "intervention_success": aggregate_row.get("intervention_success_rate"),
                "avg_cost_per_task_usd": aggregate_row.get("avg_cost_per_task_usd"),
                "total_cost_usd": _round(
                    trajectories.get("estimated_cost_usd", pd.Series(dtype=float)).dropna().sum()
                ),
                "avg_latency_per_task_s": aggregate_row.get("avg_latency_per_task_s"),
                "avg_model_calls_per_task": aggregate_row.get("avg_model_calls_per_task"),
                "avg_tool_calls_per_task": aggregate_row.get("avg_tool_calls_per_task"),
                "avg_prompt_tokens": _round(
                    trajectories.get("prompt_tokens", pd.Series(dtype=float)).dropna().mean()
                ),
                "avg_completion_tokens": _round(
                    trajectories.get("completion_tokens", pd.Series(dtype=float)).dropna().mean()
                ),
                "cost_normalized_success": aggregate_row.get("cost_normalized_success"),
                "latency_normalized_success": aggregate_row.get("latency_normalized_success"),
            }
        )
    if not rows:
        return placeholder_table(
            "Performance vs cost",
            "not yet run",
            "No non-oracle rows were found for cost/performance export.",
        )
    return pd.DataFrame(rows)


def robustness_vs_cost_table(data: RunResults, *, include_oracle: bool = False) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for agent, aggregate_row in sorted(data.aggregate.get("by_agent", {}).items()):
        if not include_oracle and _is_oracle_agent(agent):
            continue
        rows.append(
            {
                "agent": agent,
                "evidence_scope": _evidence_scope(data),
                "clean_success": aggregate_row.get("clean_success_rate"),
                "intervention_success": aggregate_row.get("intervention_success_rate"),
                "acrs": aggregate_row.get("acrs"),
                "absolute_degradation": aggregate_row.get("absolute_degradation"),
                "relative_degradation": aggregate_row.get("relative_degradation"),
                "avg_cost_per_task_usd": aggregate_row.get("avg_cost_per_task_usd"),
                "avg_latency_per_task_s": aggregate_row.get("avg_latency_per_task_s"),
                "cost_normalized_acrs": aggregate_row.get("cost_normalized_acrs"),
                "latency_normalized_acrs": aggregate_row.get("latency_normalized_acrs"),
                "avg_model_calls_per_task": aggregate_row.get("avg_model_calls_per_task"),
                "avg_tool_calls_per_task": aggregate_row.get("avg_tool_calls_per_task"),
            }
        )
    if not rows:
        return placeholder_table(
            "Robustness vs cost",
            "not yet run",
            "No non-oracle rows were found for cost/robustness export.",
        )
    return pd.DataFrame(rows)


def oracle_sanity_check_table(data: RunResults) -> pd.DataFrame:
    frame = main_agent_performance_table(data, include_oracle=True)
    if "agent" not in frame.columns:
        return placeholder_table(
            "Oracle sanity check",
            "not yet run",
            "No oracle sanity-check rows were found.",
        )
    oracle = frame[frame["agent"].map(_is_oracle_agent)].copy()
    if oracle.empty:
        return placeholder_table(
            "Oracle sanity check",
            "not yet run",
            "No oracle sanity-check rows were found.",
        )
    oracle["leaderboard_scope"] = "sanity_check_upper_bound_not_realistic_agent"
    return oracle


def intervention_family_performance_table(data: RunResults, *, include_oracle: bool = False) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for agent, agent_row in sorted(data.aggregate.get("by_agent", {}).items()):
        if not include_oracle and _is_oracle_agent(agent):
            continue
        clean_rate = agent_row.get("clean_success_rate")
        for family, family_row in sorted(agent_row.get("families", {}).items()):
            rows.append(
                {
                    "agent": agent,
                    "evidence_scope": _evidence_scope(data),
                    "intervention_family": family,
                    "n": family_row.get("n"),
                    "success_rate": family_row.get("success_rate"),
                    "acrs_family": family_row.get("acrs_family"),
                    "absolute_degradation": family_row.get("absolute_degradation"),
                    "relative_degradation": family_row.get("relative_degradation"),
                    "clean_success_reference": clean_rate,
                    "degradation_ci95": _family_degradation_ci(data, agent, family),
                }
            )
    if not rows:
        return placeholder_table(
            "Intervention family performance",
            "not yet run",
            "No intervention rows were found.",
        )
    return pd.DataFrame(rows)


def ranking_instability_table(data: RunResults, *, include_oracle: bool = False) -> pd.DataFrame:
    ranking = data.aggregate.get("ranking_instability", {})
    clean = ranking.get("clean_success_ranking", {})
    acrs = ranking.get("acrs_ranking", {})
    delta = ranking.get("rank_delta", {})
    rows = []
    for agent in sorted(set(clean) | set(acrs)):
        if not include_oracle and _is_oracle_agent(agent):
            continue
        agent_row = data.aggregate.get("by_agent", {}).get(agent, {})
        rows.append(
            {
                "agent": agent,
                "evidence_scope": _evidence_scope(data),
                "clean_rank": clean.get(agent),
                "acrs_rank": acrs.get(agent),
                "rank_delta": delta.get(agent),
                "clean_success": agent_row.get("clean_success_rate"),
                "intervention_success": agent_row.get("intervention_success_rate"),
                "acrs": agent_row.get("acrs"),
                "spearman_clean_vs_acrs": ranking.get("spearman_clean_vs_acrs"),
                "kendall_tau_clean_vs_acrs": ranking.get("kendall_tau_clean_vs_acrs"),
            }
        )
    if not rows:
        return placeholder_table("Ranking instability", "not yet run", "No ranking data found.")
    return pd.DataFrame(rows)


def paired_clean_vs_intervention_table(data: RunResults, *, include_oracle: bool = False) -> pd.DataFrame:
    scores = data.scores_df.copy()
    if scores.empty:
        return placeholder_table("Paired comparison", "not yet run", "No score rows were found.")
    scores["base_task_id"] = scores["diagnostic_base_task_id"]
    rows: list[dict[str, Any]] = []
    for agent, agent_scores in scores.groupby("agent_name"):
        if not include_oracle and _is_oracle_agent(agent):
            continue
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
                "n_pairs": len(joined),
                "mean_clean": _round(joined["clean"].mean()),
                "mean_intervention": _round(joined["intervention"].mean()),
                "mean_difference": _round(diff.mean()),
                "cohen_dz": _round(diff.mean() / diff.std(ddof=1)) if len(diff) > 1 and diff.std(ddof=1) > 0 else None,
                "paired_t_p_value": _round(p_value),
            }
        )
    if not rows:
        return placeholder_table(
            "Paired comparison",
            "not yet run",
            "No non-oracle paired rows were found.",
        )
    return pd.DataFrame(rows)


def ablation_results_table(data: RunResults) -> pd.DataFrame:
    """Build the paper Table 4 scaffold/prompt ablation export.

    Rows are filled only for trajectories whose metadata includes an `ablation`
    mapping with at least `pair_id`, `factor`, `level`, and `comparison_role`.
    """

    ablation_meta = _ablation_metadata_by_agent(data)
    if not ablation_meta:
        return placeholder_table(
            "Ablation results",
            "not yet run",
            "Run scaffold or prompt ablation experiments before filling this table.",
        )

    rows: list[dict[str, Any]] = []
    for agent, meta in sorted(ablation_meta.items()):
        agent_scores = data.scores_df[data.scores_df["agent_name"] == agent]
        agent_trajectories = data.trajectories_df[data.trajectories_df["agent_name"] == agent]
        aggregate_row = data.aggregate.get("by_agent", {}).get(agent, {})
        rows.append(
            _ablation_row(
                data,
                agent=agent,
                meta=meta,
                scores=agent_scores,
                trajectories=agent_trajectories,
                aggregate=aggregate_row,
                family="overall",
                success_rate=aggregate_row.get("intervention_success_rate"),
                acrs_value=aggregate_row.get("acrs"),
                family_n=len(agent_scores),
            )
        )
        for family, family_row in sorted(aggregate_row.get("families", {}).items()):
            family_scores = agent_scores[agent_scores["diagnostic_intervention_family"].eq(family)]
            family_trajectories = _trajectories_for_score_rows(agent_trajectories, family_scores)
            rows.append(
                _ablation_row(
                    data,
                    agent=agent,
                    meta=meta,
                    scores=family_scores,
                    trajectories=family_trajectories,
                    aggregate=aggregate_row,
                    family=family,
                    success_rate=family_row.get("success_rate"),
                    acrs_value=family_row.get("acrs_family"),
                    family_n=family_row.get("n"),
                    absolute_degradation=family_row.get("absolute_degradation"),
                    relative_degradation=family_row.get("relative_degradation"),
                )
            )

    frame = pd.DataFrame(rows)
    return _attach_ablation_deltas(frame)


def statistical_summary(data: RunResults) -> dict[str, Any]:
    paired = paired_clean_vs_intervention_table(data)
    return {
        "bootstrap": {
            row["agent"]: {
                "clean_success_ci95": row.get("clean_success_ci95"),
                "intervention_success_ci95": row.get("intervention_success_ci95"),
            }
            for row in main_agent_performance_table(data).to_dict(orient="records")
            if "agent" in row
        },
        "paired_clean_vs_intervention": paired.to_dict(orient="records"),
        "per_family_degradation": intervention_family_performance_table(data).to_dict(
            orient="records"
        ),
        "spearman_clean_vs_acrs": data.aggregate.get("ranking_instability", {}).get(
            "spearman_clean_vs_acrs"
        ),
        "kendall_tau_clean_vs_acrs": data.aggregate.get("ranking_instability", {}).get(
            "kendall_tau_clean_vs_acrs"
        ),
    }


def human_validation_agreement_table(data: RunResults) -> pd.DataFrame:
    candidates = [
        data.run_dir / "human_validation" / "summary" / "table5_human_validation_agreement.csv",
        data.run_dir / "human_validation" / "table5_human_validation_agreement.csv",
    ]
    for path in candidates:
        if path.exists():
            frame = pd.read_csv(path)
            return with_asset_metadata(frame, data)
    return placeholder_table(
        "Human validation agreement",
        "not yet run",
        "Run export-human-validation and summarize-human-validation before filling this table.",
    )


def placeholder_table(title: str, status: str, note: str) -> pd.DataFrame:
    return pd.DataFrame([{"table": title, "status": status, "note": note}])


def write_table_bundle(frame: pd.DataFrame, stem: Path) -> list[Path]:
    paths = [stem.with_suffix(".csv"), stem.with_suffix(".md"), stem.with_suffix(".tex")]
    frame.to_csv(paths[0], index=False)
    paths[1].write_text(dataframe_to_markdown(frame), encoding="utf-8")
    paths[2].write_text(frame.to_latex(index=False, escape=True), encoding="utf-8")
    return paths


def asset_metadata(data: RunResults) -> dict[str, str]:
    metadata = data.run_metadata
    model_ids = metadata.get("model_ids")
    if not model_ids and not data.trajectories_df.empty:
        model_ids = sorted(
            {
                str(value)
                for value in data.trajectories_df.get("model", pd.Series(dtype=object)).dropna()
                if str(value) not in {"", "None"}
            }
        )
    return {
        "run_dir": str(data.run_dir),
        "config_hash": _metadata_text(metadata.get("config_hash")),
        "seed": _metadata_text(metadata.get("seed")),
        "dataset_version": _metadata_text(metadata.get("dataset_version")),
        "model_ids": ", ".join(model_ids or []) or "none",
        "scorer_versions": _scorer_versions(data),
        "git_commit": _metadata_text(metadata.get("git_commit")),
        "timestamp": _metadata_text(metadata.get("timestamp")),
    }


def with_asset_metadata(frame: pd.DataFrame, data: RunResults) -> pd.DataFrame:
    annotated = frame.copy()
    for key, value in asset_metadata(data).items():
        if key not in annotated.columns:
            annotated[key] = value
    return annotated


def _is_oracle_agent(agent: str) -> bool:
    return agent == "scripted_oracle_agent"


def _ablation_metadata_by_agent(data: RunResults) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for trajectory in data.trajectories:
        ablation = trajectory.metadata.get("ablation")
        if not isinstance(ablation, dict) or not ablation:
            continue
        metadata.setdefault(
            trajectory.agent_name,
            {
                "ablation": ablation,
                "prompt_version_hash": trajectory.metadata.get("prompt_version_hash"),
                "prompt_template_hash": trajectory.metadata.get("prompt_template_hash"),
                "prompt_files": trajectory.metadata.get("prompt_files"),
                "action_protocol": trajectory.metadata.get("action_protocol"),
                "tool_description_mode": trajectory.metadata.get("tool_description_mode"),
                "step_budget_reminder": trajectory.metadata.get("step_budget_reminder"),
                "agent_type": trajectory.metadata.get("agent_type"),
                "model_id": trajectory.metadata.get("model") or trajectory.model_name,
            },
        )
    return metadata


def _ablation_row(
    data: RunResults,
    *,
    agent: str,
    meta: dict[str, Any],
    scores: pd.DataFrame,
    trajectories: pd.DataFrame,
    aggregate: dict[str, Any],
    family: str,
    success_rate: Any,
    acrs_value: Any,
    family_n: Any,
    absolute_degradation: Any = None,
    relative_degradation: Any = None,
) -> dict[str, Any]:
    ablation = meta["ablation"]
    return {
        "pair_id": ablation.get("pair_id"),
        "factor": ablation.get("factor"),
        "level": ablation.get("level"),
        "comparison_role": ablation.get("comparison_role"),
        "agent": agent,
        "agent_type": meta.get("agent_type"),
        "model_id": meta.get("model_id"),
        "intervention_family": family,
        "n": family_n,
        "success_rate": _round(success_rate),
        "clean_success_rate": _round(aggregate.get("clean_success_rate")),
        "intervention_success_rate": _round(aggregate.get("intervention_success_rate")),
        "acrs": _round(acrs_value),
        "absolute_degradation": _round(
            aggregate.get("absolute_degradation") if family == "overall" else absolute_degradation
        ),
        "relative_degradation": _round(
            aggregate.get("relative_degradation") if family == "overall" else relative_degradation
        ),
        "estimated_cost_usd": _round(
            trajectories.get("estimated_cost_usd", pd.Series(dtype=float)).dropna().sum()
        ),
        "avg_latency_s": _round(
            trajectories.get("latency_s", pd.Series(dtype=float)).dropna().mean()
        ),
        "avg_model_calls": _round(
            trajectories.get("model_call_count", pd.Series(dtype=float)).dropna().mean()
        ),
        "avg_tool_calls": _round(
            trajectories.get("n_tool_calls", pd.Series(dtype=float)).dropna().mean()
        ),
        "avg_total_tokens": _round(
            trajectories.get("total_tokens", pd.Series(dtype=float)).dropna().mean()
        ),
        "tool_overuse": _round(
            scores.get("unnecessary_tool_call_rate", pd.Series(dtype=float)).dropna().mean()
        ),
        "required_tool_recall": _round(
            scores.get("required_tool_recall", pd.Series(dtype=float)).dropna().mean()
        ),
        "trajectory_faithfulness": _round(
            scores.get("trajectory_faithfulness", pd.Series(dtype=float)).dropna().mean()
        ),
        "prompt_version_hash": meta.get("prompt_version_hash"),
        "prompt_template_hash": meta.get("prompt_template_hash"),
        "prompt_files": _json_for_cell(meta.get("prompt_files")),
        "action_protocol": meta.get("action_protocol"),
        "tool_description_mode": meta.get("tool_description_mode"),
        "step_budget_reminder": meta.get("step_budget_reminder"),
        "evidence_scope": _evidence_scope(data),
    }


def _attach_ablation_deltas(frame: pd.DataFrame) -> pd.DataFrame:
    annotated = frame.copy()
    annotated["delta_success_vs_reference"] = None
    annotated["delta_acrs_vs_reference"] = None
    group_cols = ["pair_id", "intervention_family"]
    for _, group in annotated.groupby(group_cols, dropna=False):
        references = group[group["comparison_role"].eq("reference")]
        if references.empty:
            continue
        reference = references.iloc[0]
        for index in group.index:
            annotated.at[index, "delta_success_vs_reference"] = _delta(
                annotated.at[index, "success_rate"],
                reference.get("success_rate"),
            )
            annotated.at[index, "delta_acrs_vs_reference"] = _delta(
                annotated.at[index, "acrs"],
                reference.get("acrs"),
            )
    return annotated


def _trajectories_for_score_rows(trajectories: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    if (
        trajectories.empty
        or scores.empty
        or "instance_id" not in scores
        or "instance_id" not in trajectories
    ):
        return trajectories.iloc[0:0]
    instance_ids = set(scores["instance_id"].dropna().astype(str))
    if not instance_ids:
        return trajectories.iloc[0:0]
    return trajectories[trajectories["instance_id"].astype(str).isin(instance_ids)]


def _delta(value: Any, reference: Any) -> float | None:
    if value is None or reference is None or pd.isna(value) or pd.isna(reference):
        return None
    return round(float(value) - float(reference), 6)


def _json_for_cell(value: Any) -> str:
    if value is None:
        return ""
    return json.dumps(value, sort_keys=True, default=str)


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


def _ratio_ci(
    clean_values: pd.Series,
    intervention_values: pd.Series,
    *,
    seed: int,
    n_boot: int = 1000,
) -> str | None:
    clean = np.asarray([float(value) for value in clean_values if pd.notna(value)], dtype=float)
    intervention = np.asarray(
        [float(value) for value in intervention_values if pd.notna(value)], dtype=float
    )
    if clean.size == 0 or intervention.size == 0 or clean.mean() == 0:
        return None
    rng = np.random.default_rng(seed)
    ratios = []
    for _ in range(n_boot):
        clean_mean = rng.choice(clean, size=clean.size, replace=True).mean()
        int_mean = rng.choice(intervention, size=intervention.size, replace=True).mean()
        if clean_mean:
            ratios.append(int_mean / clean_mean)
    if not ratios:
        return None
    return _ci_text(
        round(float(np.quantile(ratios, 0.025)), 6),
        round(float(np.quantile(ratios, 0.975)), 6),
    )


def _family_degradation_ci(data: RunResults, agent: str, family: str) -> str | None:
    scores = data.scores_df
    agent_scores = scores[scores["agent_name"] == agent]
    clean = agent_scores[agent_scores["diagnostic_condition"] == "clean"].get(
        "final_success_binary", pd.Series(dtype=float)
    )
    family_scores = agent_scores[
        agent_scores["diagnostic_intervention_family"].eq(family)
    ].get("final_success_binary", pd.Series(dtype=float))
    clean_arr = np.asarray([float(value) for value in clean if pd.notna(value)], dtype=float)
    family_arr = np.asarray([float(value) for value in family_scores if pd.notna(value)], dtype=float)
    if clean_arr.size == 0 or family_arr.size == 0:
        return None
    rng = np.random.default_rng(abs(hash((agent, family))) % (2**32))
    diffs = []
    for _ in range(1000):
        diffs.append(
            rng.choice(clean_arr, size=clean_arr.size, replace=True).mean()
            - rng.choice(family_arr, size=family_arr.size, replace=True).mean()
        )
    return _ci_text(
        round(float(np.quantile(diffs, 0.025)), 6),
        round(float(np.quantile(diffs, 0.975)), 6),
    )


def _rate_from_count(values: pd.Series) -> float | None:
    numeric = [float(value) for value in values if pd.notna(value)]
    if not numeric:
        return None
    return round(sum(1 for value in numeric if value > 0) / len(numeric), 6)


def _scorer_versions(data: RunResults) -> str:
    if not data.scores_df.empty and "metadata_scorer" in data.scores_df:
        versions = sorted(
            {
                str(value)
                for value in data.scores_df["metadata_scorer"].dropna()
                if str(value) not in {"", "None"}
            }
        )
        if versions:
            return ", ".join(versions)
    return "unknown"


def _metadata_text(value: Any) -> str:
    if value is None or value == "":
        return "unknown"
    return str(value)


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


def _evidence_scope(data: RunResults) -> str:
    cached = data.run_metadata.get("evidence_scope")
    if cached:
        return str(cached)
    providers = set()
    if not data.trajectories_df.empty and "provider" in data.trajectories_df:
        providers = {
            str(value)
            for value in data.trajectories_df["provider"].dropna().unique()
            if str(value) not in {"", "None"}
        }
    run_name = str(data.run_metadata.get("run_name") or data.run_dir.name)
    from causal_agent_bench.runners.evidence_scope import classify_evidence_scope

    return classify_evidence_scope(providers, run_name=run_name)
