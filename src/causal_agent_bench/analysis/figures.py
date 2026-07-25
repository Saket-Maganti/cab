from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from causal_agent_bench.analysis.error_analysis import mine_error_taxonomy
from causal_agent_bench.analysis.load_results import RunResults
from causal_agent_bench.analysis.tables import _is_oracle_agent, asset_metadata
from causal_agent_bench.utils.io import read_json

FIGURE1_MERMAID = """# Figure 1: Benchmark Schematic

```mermaid
flowchart LR
  A["Base task"] --> B["Clean condition"]
  A --> C["Intervention conditions"]
  C --> C1["Tool failure"]
  C --> C2["Memory corruption"]
  C --> C3["Observation conflict"]
  B --> D["Agent trajectory"]
  C1 --> D
  C2 --> D
  C3 --> D
  D --> E["Trajectory-level metrics"]
  E --> F["Final success"]
  E --> G["Tool use, recovery, contradiction, memory, stopping"]
  F --> H["ACRS aggregation"]
  G --> H
```

This is a schematic template. Replace with a designed figure after the benchmark design is frozen.
"""


def build_all_figures(data: RunResults, output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    metadata = asset_metadata(data)
    paths.append(write_figure1_schematic(out, metadata))
    paths.extend(
        _save_or_placeholder(
            out / "figure2_clean_vs_intervention_success",
            lambda: figure2_clean_vs_intervention(data),
            metadata,
        )
    )
    paths.extend(
        _save_or_placeholder(
            out / "figure3_intervention_family_degradation",
            lambda: figure3_intervention_family_degradation(data),
            metadata,
        )
    )
    paths.extend(
        _save_or_placeholder(
            out / "figure3_intervention_family_breakdown",
            lambda: figure3_family_breakdown(data),
            metadata,
        )
    )
    paths.extend(
        _save_or_placeholder(
            out / "figure4_ranking_instability",
            lambda: figure4_ranking_instability(data),
            metadata,
        )
    )
    paths.extend(
        _save_or_placeholder(
            out / "figure5_cost_vs_robustness",
            lambda: figure5_cost_vs_robustness(data),
            metadata,
        )
    )
    paths.extend(
        _save_or_placeholder(
            out / "figure6_trajectory_failure_taxonomy",
            lambda: figure6_trajectory_failure_taxonomy(data),
            metadata,
        )
    )
    figure7 = figure7_human_judge_agreement(data)
    if figure7 is not None:
        paths.extend(_save_or_placeholder(out / "figure7_human_judge_agreement", lambda: figure7, metadata))
    legacy = out / "legacy"
    legacy.mkdir(exist_ok=True)
    paths.extend(
        _save_or_placeholder(
            legacy / "figure5_failure_mode_distribution",
            lambda: figure5_failure_modes(data),
            metadata,
        )
    )
    paths.extend(
        _save_or_placeholder(
            legacy / "figure6_trajectory_final_disagreement",
            lambda: figure6_trajectory_final_disagreement(data),
            metadata,
        )
    )
    paths.extend(
        _save_or_placeholder(
            legacy / "figure6_error_case_taxonomy",
            lambda: figure6_error_case_taxonomy(data),
            metadata,
        )
    )
    return paths


def write_figure1_schematic(output_dir: str | Path, metadata: dict[str, str] | None = None) -> Path:
    path = Path(output_dir) / "figure1_benchmark_schematic.md"
    text = FIGURE1_MERMAID
    if metadata:
        text += "\n## Asset Metadata\n\n"
        text += "\n".join(f"- {key}: `{value}`" for key, value in metadata.items())
        text += "\n"
    path.write_text(text, encoding="utf-8")
    return path


def figure2_clean_vs_intervention(data: RunResults) -> plt.Figure:
    rows = data.aggregate.get("by_agent", {})
    if not rows:
        return placeholder_figure("Figure 2: not yet run")
    agents = sorted(rows)
    clean = [_nan(rows[agent].get("clean_success_rate")) for agent in agents]
    intervention = [_nan(rows[agent].get("intervention_success_rate")) for agent in agents]
    x = np.arange(len(agents))
    width = 0.38
    fig, ax = plt.subplots(figsize=(max(7, len(agents) * 1.3), 4.5))
    ax.bar(x - width / 2, clean, width, label="Clean", color="#4C78A8")
    ax.bar(x + width / 2, intervention, width, label="Intervention", color="#F58518")
    ax.set_ylabel("Success rate")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x)
    ax.set_xticklabels(agents, rotation=30, ha="right")
    ax.set_title("Clean vs intervention success")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def figure3_intervention_family_degradation(data: RunResults) -> plt.Figure:
    rows = []
    for agent, agent_row in data.aggregate.get("by_agent", {}).items():
        if _is_oracle_agent(agent):
            continue
        clean = agent_row.get("clean_success_rate")
        for family, family_row in agent_row.get("families", {}).items():
            degradation = family_row.get("absolute_degradation")
            if degradation is None and clean is not None and family_row.get("success_rate") is not None:
                degradation = clean - family_row.get("success_rate")
            rows.append({"agent": agent, "family": family, "degradation": degradation})
    if not rows:
        return placeholder_figure("Figure 3: no intervention family degradation data")
    frame = pd.DataFrame(rows)
    matrix = frame.pivot(index="family", columns="agent", values="degradation").sort_index()
    values = matrix.to_numpy(dtype=float)
    vmax = np.nanmax(values) if np.any(~np.isnan(values)) else 1.0
    fig, ax = plt.subplots(figsize=(max(7, matrix.shape[1] * 1.4), max(4, matrix.shape[0] * 0.45)))
    image = ax.imshow(values, vmin=0, vmax=max(vmax, 0.01), cmap="Reds", aspect="auto")
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels(matrix.columns, rotation=30, ha="right")
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index)
    ax.set_title("Intervention-family degradation (clean minus family success)")
    for y in range(matrix.shape[0]):
        for x in range(matrix.shape[1]):
            value = values[y, x]
            if not np.isnan(value):
                ax.text(
                    x,
                    y,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    color="white" if value > vmax * 0.55 else "black",
                    fontsize=8,
                )
    fig.colorbar(image, ax=ax, label="Absolute degradation")
    fig.tight_layout()
    return fig


def figure3_family_breakdown(data: RunResults) -> plt.Figure:
    rows = []
    for agent, agent_row in data.aggregate.get("by_agent", {}).items():
        for family, family_row in agent_row.get("families", {}).items():
            rows.append(
                {
                    "agent": agent,
                    "family": family,
                    "success_rate": family_row.get("success_rate"),
                }
            )
    if not rows:
        return placeholder_figure("Figure 3: no intervention family data")
    frame = pd.DataFrame(rows)
    matrix = frame.pivot(index="family", columns="agent", values="success_rate").sort_index()
    values = matrix.to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(max(7, matrix.shape[1] * 1.4), max(4, matrix.shape[0] * 0.45)))
    image = ax.imshow(values, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels(matrix.columns, rotation=30, ha="right")
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index)
    ax.set_title("Intervention family success by agent")
    for y in range(matrix.shape[0]):
        for x in range(matrix.shape[1]):
            value = values[y, x]
            if not np.isnan(value):
                ax.text(x, y, f"{value:.2f}", ha="center", va="center", color="white" if value < 0.55 else "black", fontsize=8)
    fig.colorbar(image, ax=ax, label="Success rate")
    fig.tight_layout()
    return fig


def figure4_ranking_instability(data: RunResults) -> plt.Figure:
    ranking = data.aggregate.get("ranking_instability", {})
    clean = ranking.get("clean_success_ranking", {})
    acrs = ranking.get("acrs_ranking", {})
    agents = sorted(set(clean) & set(acrs), key=lambda agent: clean[agent])
    if not agents:
        return placeholder_figure("Figure 4: no ranking data")
    fig, ax = plt.subplots(figsize=(7, max(4, len(agents) * 0.55)))
    for agent in agents:
        ax.plot([0, 1], [clean[agent], acrs[agent]], marker="o", linewidth=1.8)
        ax.text(-0.05, clean[agent], agent, ha="right", va="center", fontsize=8)
        ax.text(1.05, acrs[agent], agent, ha="left", va="center", fontsize=8)
    ax.set_xlim(-0.25, 1.25)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Clean rank", "ACRS rank"])
    ax.set_ylabel("Rank (1 is best)")
    ax.invert_yaxis()
    ax.set_title(f"Ranking instability (Spearman={ranking.get('spearman_clean_vs_acrs', 'NA')})")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    return fig


def figure5_cost_vs_robustness(data: RunResults) -> plt.Figure:
    rows = []
    for agent, agent_row in data.aggregate.get("by_agent", {}).items():
        if _is_oracle_agent(agent):
            continue
        cost = agent_row.get("avg_cost_per_task_usd")
        acrs = agent_row.get("acrs")
        if cost is None or acrs is None:
            continue
        rows.append({"agent": agent, "cost": cost, "acrs": acrs})
    if not rows:
        return placeholder_figure("Figure 5: no cost/robustness data")
    frame = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(frame["cost"], frame["acrs"], s=80, color="#4C78A8")
    for _, row in frame.iterrows():
        ax.annotate(row["agent"], (row["cost"], row["acrs"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("Average cost per task (USD)")
    ax.set_ylabel("ACRS")
    ax.set_ylim(0, 1.05)
    ax.set_title("Cost vs robustness (ACRS)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


def figure5_failure_modes(data: RunResults) -> plt.Figure:
    scores = data.scores_df
    if scores.empty:
        return placeholder_figure("Figure 5: no score data")
    categories = {
        "invalid tool call": scores.get("invalid_tool_call_count", pd.Series(dtype=float)).fillna(0) > 0,
        "missed required tool": scores.get("missing_required_tool_count", pd.Series(dtype=float)).fillna(0) > 0,
        "blind memory trust": scores.get("memory_blind_trust_failure_binary", pd.Series(dtype=bool)).fillna(False).astype(bool),
        "failed recovery": scores.get("tool_error_recovery_binary", pd.Series(dtype=object)).eq(False),
        "contradiction miss": (
            scores.get("diagnostic_intervention_family", pd.Series(dtype=object)).eq("observation_conflict")
            & scores.get("contradiction_detected_binary", pd.Series(dtype=object)).eq(False)
        ),
        "premature stop": scores.get("premature_stop_binary", pd.Series(dtype=bool)).fillna(False).astype(bool),
    }
    names = list(categories)
    proportions = [float(mask.mean()) if len(mask) else 0.0 for mask in categories.values()]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, proportions, color="#54A24B")
    ax.set_ylabel("Proportion of scored trajectories")
    ax.set_ylim(0, 1.05)
    ax.set_title("Failure mode distribution")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def figure6_trajectory_final_disagreement(data: RunResults) -> plt.Figure:
    scores = data.scores_df
    if scores.empty:
        return placeholder_figure("Figure 6: no score data")
    disagreement = scores[
        scores.get("final_success_binary", pd.Series(dtype=float)).eq(1)
        & scores.get("trajectory_success_binary", pd.Series(dtype=float)).eq(0)
    ]
    counts = disagreement.groupby("agent_name").size().reindex(sorted(scores["agent_name"].unique()), fill_value=0)
    fig, ax = plt.subplots(figsize=(max(7, len(counts) * 1.2), 4.5))
    ax.bar(counts.index, counts.values, color="#E45756")
    ax.set_ylabel("Count")
    ax.set_title("Final-success / trajectory-failure disagreements")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def figure6_trajectory_failure_taxonomy(data: RunResults) -> plt.Figure:
    return figure6_error_case_taxonomy(data)


def figure7_human_judge_agreement(data: RunResults) -> plt.Figure | None:
    run_dir = data.run_dir
    human_summary = run_dir / "human_validation" / "summary" / "validation_agreement.json"
    judge_summary = run_dir / "llm_judge" / "calibration" / "judge_calibration_report.json"
    if not human_summary.exists() and not judge_summary.exists():
        return None
    labels: list[str] = []
    values: list[float] = []
    title = "Human / judge agreement"
    if human_summary.exists():
        payload = read_json(human_summary)
        agreement = payload.get("agreement", {})
        for dimension, stats in agreement.items():
            labels.append(f"human:{dimension}")
            values.append(float(stats.get("percent_agreement") or 0.0))
        title = "Human validation agreement by dimension"
    if judge_summary.exists():
        payload = read_json(judge_summary)
        for dimension, stats in payload.get("by_dimension", {}).items():
            labels.append(f"judge:{dimension}")
            values.append(float(stats.get("percent_agreement") or stats.get("agreement_rate") or 0.0))
        if "Human" not in title:
            title = "LLM judge vs human agreement by dimension"
    if not labels:
        return placeholder_figure("Figure 7: no agreement metrics")
    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 0.7), 4.5))
    ax.bar(labels, values, color="#72B7B2")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Agreement rate")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def figure6_error_case_taxonomy(data: RunResults) -> plt.Figure:
    cases = mine_error_taxonomy(data, max_cases=10_000)
    names = list(cases)
    counts = [len(cases[name]) for name in names]
    if not names:
        return placeholder_figure("Figure 6: no error-case data")
    fig, ax = plt.subplots(figsize=(max(9, len(names) * 0.8), 5))
    ax.bar(names, counts, color="#B279A2")
    ax.set_ylabel("Mined case count")
    ax.set_title("Pilot error-case taxonomy")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def placeholder_figure(message: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=14)
    ax.set_axis_off()
    fig.tight_layout()
    return fig


def _save_or_placeholder(stem: Path, builder, metadata: dict[str, str] | None = None) -> list[Path]:
    fig = builder()
    if metadata:
        _stamp_figure(fig, metadata)
    png = stem.with_suffix(".png")
    pdf = stem.with_suffix(".pdf")
    fig.savefig(png, dpi=180)
    fig.savefig(pdf)
    plt.close(fig)
    return [png, pdf]


def _stamp_figure(fig: plt.Figure, metadata: dict[str, str]) -> None:
    footer = (
        f"run={metadata.get('run_dir', 'unknown')} | "
        f"config={metadata.get('config_hash', 'unknown')} | "
        f"dataset={metadata.get('dataset_version', 'unknown')} | "
        f"models={metadata.get('model_ids', 'none')} | "
        f"time={metadata.get('timestamp', 'unknown')}"
    )
    fig.subplots_adjust(bottom=max(fig.subplotpars.bottom, 0.18))
    fig.text(0.01, 0.01, footer, ha="left", va="bottom", fontsize=6, color="#555555")


def _nan(value: Any) -> float:
    return float(value) if value is not None else np.nan
