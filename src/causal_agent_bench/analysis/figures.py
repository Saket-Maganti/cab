from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from causal_agent_bench.analysis.load_results import RunResults

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
    paths.append(write_figure1_schematic(out))
    paths.extend(_save_or_placeholder(out / "figure2_clean_vs_intervention_success", lambda: figure2_clean_vs_intervention(data)))
    paths.extend(_save_or_placeholder(out / "figure3_intervention_family_breakdown", lambda: figure3_family_breakdown(data)))
    paths.extend(_save_or_placeholder(out / "figure4_ranking_instability", lambda: figure4_ranking_instability(data)))
    paths.extend(_save_or_placeholder(out / "figure5_failure_mode_distribution", lambda: figure5_failure_modes(data)))
    paths.extend(_save_or_placeholder(out / "figure6_trajectory_final_disagreement", lambda: figure6_trajectory_final_disagreement(data)))
    return paths


def write_figure1_schematic(output_dir: str | Path) -> Path:
    path = Path(output_dir) / "figure1_benchmark_schematic.md"
    path.write_text(FIGURE1_MERMAID, encoding="utf-8")
    return path


def figure2_clean_vs_intervention(data: RunResults) -> plt.Figure:
    rows = data.aggregate.get("by_agent", {})
    if not rows:
        return placeholder_figure("Figure 2: not yet run")
    agents = list(sorted(rows))
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


def placeholder_figure(message: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=14)
    ax.set_axis_off()
    fig.tight_layout()
    return fig


def _save_or_placeholder(stem: Path, builder) -> list[Path]:
    fig = builder()
    png = stem.with_suffix(".png")
    pdf = stem.with_suffix(".pdf")
    fig.savefig(png, dpi=180)
    fig.savefig(pdf)
    plt.close(fig)
    return [png, pdf]


def _nan(value: Any) -> float:
    return float(value) if value is not None else np.nan
