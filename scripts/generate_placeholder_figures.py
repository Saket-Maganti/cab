#!/usr/bin/env python3
"""Generate schematic placeholder figures — NOT empirical results."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "paper" / "latexpaper" / "figures"

PLACEHOLDER_LABEL = "PLACEHOLDER — NOT EMPIRICAL RESULT"


def _ensure_mpl():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _write_meta(path: Path, *, figure_id: str, title: str, description: str) -> None:
    meta = {
        "figure_id": figure_id,
        "title": title,
        "description": description,
        "placeholder": True,
        "empirical_result": False,
        "scientific_evidence": False,
        "label": PLACEHOLDER_LABEL,
        "generated_at": datetime.now(UTC).isoformat(),
        "generator": "scripts/generate_placeholder_figures.py",
        "warning": "Do not use as final paper result figure.",
    }
    meta_path = path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def figure1_benchmark_overview(plt, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    boxes = [
        (0.5, 3.2, "Base tasks"),
        (2.5, 3.2, "Clean instances"),
        (4.5, 3.2, "Intervention instances"),
        (6.5, 3.2, "Agent trajectories"),
        (8.2, 3.2, "Metrics / ACRS"),
    ]
    for x, y, label in boxes:
        ax.add_patch(plt.Rectangle((x, y), 1.6, 0.9, fill=False, linewidth=2))
        ax.text(x + 0.8, y + 0.45, label, ha="center", va="center", fontsize=9)
    for x in [2.1, 4.1, 6.1, 7.8]:
        ax.annotate("", xy=(x + 0.4, 3.65), xytext=(x, 3.65), arrowprops={"arrowstyle": "->", "lw": 1.5})
    ax.text(5, 1.2, PLACEHOLDER_LABEL, ha="center", fontsize=11, color="red", weight="bold")
    ax.text(5, 0.5, "Schematic only — no performance data", ha="center", fontsize=9)
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    _write_meta(out, figure_id="figure1", title="Benchmark overview (schematic)", description="High-level CAB pipeline")


def figure2_intervention_pairing(plt, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0.8, 2.5), 2.2, 1.2, fill=False, lw=2))
    ax.text(1.9, 3.1, "Clean\n(same goal)", ha="center", va="center")
    ax.add_patch(plt.Rectangle((5.5, 2.5), 2.2, 1.2, fill=False, lw=2))
    ax.text(6.6, 3.1, "Intervention\n(one factor changed)", ha="center", va="center")
    ax.text(4.5, 3.1, "Base task", ha="center", fontsize=10, weight="bold")
    ax.annotate("", xy=(0.8, 3.1), xytext=(3.5, 3.8), arrowprops={"arrowstyle": "->", "lw": 1.5})
    ax.annotate("", xy=(5.5, 3.1), xytext=(3.5, 3.8), arrowprops={"arrowstyle": "->", "lw": 1.5})
    ax.text(4.5, 1.0, PLACEHOLDER_LABEL, ha="center", color="red", weight="bold")
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    _write_meta(out, figure_id="figure2", title="Intervention pairing (schematic)", description="Paired clean/intervention design")


def figure3_acrs_concept(plt, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis("off")
    ax.text(0.5, 0.75, "ACRS = f(clean success, intervention success, trajectory diagnostics)", ha="center", transform=ax.transAxes, fontsize=11)
    components = ["Final success", "Intervention robustness", "Tool efficiency", "Recovery", "Contradiction handling"]
    for i, comp in enumerate(components):
        ax.add_patch(plt.Rectangle((0.1 + i * 0.17, 0.35), 0.14, 0.25, fill=False, lw=1.5))
        ax.text(0.17 + i * 0.17, 0.47, comp, ha="center", va="center", fontsize=7, rotation=90)
    ax.text(0.5, 0.12, PLACEHOLDER_LABEL, ha="center", transform=ax.transAxes, color="red", weight="bold")
    ax.text(0.5, 0.05, "Concept diagram — weights not empirical", ha="center", transform=ax.transAxes, fontsize=9)
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    _write_meta(out, figure_id="figure3", title="ACRS concept (schematic)", description="Composite metric components")


def figure4_run_lifecycle(plt, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 3))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 3)
    ax.axis("off")
    stages = ["planned", "dry-run", "running", "complete", "scored", "audited", "claim-checked"]
    for i, stage in enumerate(stages):
        x = 0.3 + i * 1.5
        ax.add_patch(plt.Rectangle((x, 1.2), 1.2, 0.7, fill=False, lw=1.5))
        ax.text(x + 0.6, 1.55, stage, ha="center", va="center", fontsize=8)
        if i < len(stages) - 1:
            ax.annotate("", xy=(x + 1.25, 1.55), xytext=(x + 1.35, 1.55), arrowprops={"arrowstyle": "->", "lw": 1.2})
    ax.text(5.5, 0.4, PLACEHOLDER_LABEL, ha="center", color="red", weight="bold")
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    _write_meta(out, figure_id="figure4", title="Run lifecycle (schematic)", description="Experiment state flow")


FIGURES = [
    ("figure1_benchmark_overview_placeholder.png", figure1_benchmark_overview),
    ("figure2_intervention_pairing_placeholder.png", figure2_intervention_pairing),
    ("figure3_acrs_concept_placeholder.png", figure3_acrs_concept),
    ("figure4_run_lifecycle_placeholder.png", figure4_run_lifecycle),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt = _ensure_mpl()
    for filename, generator in FIGURES:
        path = OUT_DIR / filename
        generator(plt, path)
        print(f"wrote {path.relative_to(REPO_ROOT)}")
        print(f"wrote {path.with_suffix('.meta.json').relative_to(REPO_ROOT)}")
    readme_note = OUT_DIR / "GENERATED_PLACEHOLDERS.txt"
    readme_note.write_text(
        f"{PLACEHOLDER_LABEL}\nGenerated: {datetime.now(UTC).isoformat()}\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
