"""Tests for camera-ready packaging precheck scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.camera_ready_precheck import run_camera_ready_precheck
from scripts.check_citation_todos import run_citation_todo_check
from scripts.check_package_import import run_package_import_check
from scripts.check_paper_assets import find_missing_inputs, find_unresolved_figure_table_refs
from scripts.check_repo_packaging import run_repo_packaging_check
from scripts.check_todos import find_todos

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_package_import_check_passes() -> None:
    assert run_package_import_check() == []


def test_repo_packaging_check_passes() -> None:
    assert run_repo_packaging_check(REPO_ROOT) == []


def test_citation_todo_check_passes_on_repo() -> None:
    paper_root = REPO_ROOT / "paper" / "latexpaper"
    assert run_citation_todo_check(paper_root, paper_root / "references.bib") == []


def test_draft_precheck_passes_on_scaffold() -> None:
    results = run_camera_ready_precheck(REPO_ROOT, mode="draft", skip_release=False)
    failed = [step.name for step in results if not step.passed]
    assert failed == [], f"unexpected draft failures: {failed}"


def test_submission_precheck_fails_without_filled_evidence() -> None:
    results = run_camera_ready_precheck(REPO_ROOT, mode="submission", skip_release=True)
    failed = {step.name for step in results if not step.passed}
    assert "unsupported_claims" in failed or "paper_assets" in failed or "placeholders" in failed


def test_find_todos_detects_latex_macro(tmp_path: Path) -> None:
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text(r"\todo{fill me}", encoding="utf-8")
    assert find_todos(paper)


def test_find_missing_inputs_detects_broken_input(tmp_path: Path) -> None:
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text(r"\input{missing/file}", encoding="utf-8")
    issues = find_missing_inputs(paper)
    assert any("missing input" in issue for issue in issues)


def test_submission_mode_unresolved_ref_is_hard_failure(tmp_path: Path) -> None:
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text(
        r"\ref{fig:missing}" + "\n" + r"\label{tab:ok}",
        encoding="utf-8",
    )
    draft = find_unresolved_figure_table_refs(paper, mode="draft")
    submission = find_unresolved_figure_table_refs(paper, mode="submission")
    assert any(item.startswith("WARNING:") for item in draft)
    assert any("unresolved ref" in item and not item.startswith("WARNING:") for item in submission)


def test_release_dry_run_cli() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/release_dry_run.py", "--skip-tests"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_camera_ready_precheck_cli_json() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/camera_ready_precheck.py",
            "--mode",
            "draft",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is True
