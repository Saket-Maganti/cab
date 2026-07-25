"""Tests for artifact reproduction scripts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from scripts.reproduce_artifact import (
    DETERMINISTIC_STEPS,
    check_prerequisites,
    find_latest_run,
    resolve_run_dir,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_prerequisites_pass_in_repo() -> None:
    issues = check_prerequisites(REPO_ROOT)
    assert issues == [], issues


def test_deterministic_steps_cover_quickstart() -> None:
    names = {step.name for step in DETERMINISTIC_STEPS}
    assert names >= {"install", "smoke", "pilot-stub", "table2", "figure2"}


def test_reproduce_cli_check() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/reproduce_artifact.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "passed" in proc.stdout.lower()


def test_reproduce_cli_list_steps() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/reproduce_artifact.py", "--list-steps"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "pilot-stub" in proc.stdout


def test_reproduce_dry_run_all_deterministic() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/reproduce_artifact.py",
            "--all-deterministic",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "pilot-stub" in proc.stdout


def test_find_latest_run_on_existing_stub_dir() -> None:
    results = REPO_ROOT / "results"
    if not results.exists():
        return
    latest = find_latest_run(results, "pilot_20_multi_agent_stub")
    if latest is not None:
        assert "pilot_20_multi_agent_stub" in latest.name


def test_resolve_run_dir_requires_existing_path(tmp_path: Path) -> None:
    run = tmp_path / "results" / "20260101_demo"
    run.mkdir(parents=True)
    (run / "run_metadata.json").write_text("{}", encoding="utf-8")
    resolved = resolve_run_dir(tmp_path, "results/20260101_demo")
    assert resolved == run


def test_smoke_step_runs() -> None:
    if os.environ.get("SKIP_ARTIFACT_SMOKE") == "1":
        return
    env = {**os.environ, "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"}
    proc = subprocess.run(
        [sys.executable, "scripts/reproduce_artifact.py", "--step", "smoke"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
