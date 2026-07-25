"""Canonical paths for paper coordination docs and LaTeX sources."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = REPO_ROOT / "paper"
PAPER_LATEX_DIR = PAPER_DIR / "latexpaper"
PAPER_GENERATED_DIR = PAPER_LATEX_DIR / "generated"
PAPER_FIGURES_DIR = PAPER_LATEX_DIR / "figures"
PAPER_MAIN_TEX = PAPER_LATEX_DIR / "main.tex"


def generated_rel(filename: str) -> str:
    """Repo-relative path to a generated LaTeX fragment."""
    return str(PAPER_GENERATED_DIR.relative_to(REPO_ROOT) / filename)
