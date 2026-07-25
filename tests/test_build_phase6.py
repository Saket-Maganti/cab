"""Build Mode Phase 6: docs navigation, diagrams, placeholder figures, demo package."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_phase6_docs_hub_exists():
    assert (REPO / "docs/README.md").exists()
    assert (REPO / "docs/REPO_MAP.md").exists()
    assert (REPO / "docs/GLOSSARY.md").exists()
    assert (REPO / "docs/ONBOARDING.md").exists()


def test_phase6_diagrams_exist():
    diagrams = REPO / "docs/diagrams"
    for name in (
        "system_architecture.mmd",
        "benchmark_flow.mmd",
        "intervention_pairing.mmd",
        "run_lifecycle.mmd",
        "evidence_levels.mmd",
        "claim_ledger_flow.mmd",
        "human_validation_flow.mmd",
        "DIAGRAMS_README.md",
    ):
        assert (diagrams / name).exists(), name


def test_phase6_handoff_demo_files():
    for rel in (
        "handoff/ADVISOR_DEMO_SCRIPT.md",
        "handoff/DEMO_SLIDES_OUTLINE.md",
    ):
        assert (REPO / rel).exists(), rel


def test_generate_placeholder_figures():
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, "scripts/generate_placeholder_figures.py"],
        cwd=REPO,
        check=True,
        env={"MPLCONFIGDIR": "/tmp/mpl", **dict(__import__("os").environ)},
    )
    fig_dir = REPO / "paper" / "latexpaper" / "figures"
    for name in (
        "figure1_benchmark_overview_placeholder.png",
        "figure2_intervention_pairing_placeholder.png",
        "figure3_acrs_concept_placeholder.png",
        "figure4_run_lifecycle_placeholder.png",
    ):
        png = fig_dir / name
        assert png.exists(), name
        meta = json.loads(png.with_suffix(".meta.json").read_text(encoding="utf-8"))
        assert meta.get("placeholder") is True
        assert meta.get("empirical_result") is False


def test_walkthroughs_and_explainer():
    assert (REPO / "docs/EXAMPLE_WALKTHROUGHS.md").exists()
    text = (REPO / "docs/EXAMPLE_WALKTHROUGHS.md").read_text(encoding="utf-8")
    assert "tool_failure" in text
    assert (REPO / "docs/TRAJECTORY_EXPLAINER.md").exists()


def test_contributing_and_pr_template():
    assert (REPO / "CONTRIBUTING.md").exists()
    assert (REPO / ".github/pull_request_template.md").exists()
