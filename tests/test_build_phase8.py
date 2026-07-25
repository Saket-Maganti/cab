"""Build Mode Phase 8 — pre-experiment freeze and master status tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


@pytest.mark.build_phase
def test_generate_master_status():
    proc = _run("generate_master_status.py")
    assert proc.returncode == 0
    data = json.loads((ROOT / "MASTER_STATUS.json").read_text())
    assert data["executive_status"]["classification"] == "build_infrastructure_ready"
    assert data["claims"]["C9"] == "engineering_only"
    assert all(data["claims"].get(f"C{i}") == "planned" for i in range(1, 9))


@pytest.mark.build_phase
def test_final_build_phase_audit():
    proc = _run("final_build_phase_audit.py")
    assert proc.returncode in (0, 1)
    assert (ROOT / "audits/final_build_phase/FINAL_BUILD_PHASE_AUDIT.md").exists()
    data = json.loads((ROOT / "audits/final_build_phase/final_build_phase_audit.json").read_text())
    assert data["no_model_runs_executed_by_audit"] is True


@pytest.mark.build_phase
def test_phase8_docs_exist():
    paths = [
        "MASTER_STATUS.md",
        "PROJECT_HEALTH.md",
        "BLOCKED_ITEMS.md",
        "docs/COMMAND_MAP.md",
        "docs/DO_NOT_OVERCLAIM.md",
        "experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md",
        "experiments/SAFE_NEXT_RUN_DECISION_TREE.md",
        "handoff/ADVISOR_REVIEW_BUNDLE_INDEX.md",
        "audits/build_phase_8/PHASE_8_START_SNAPSHOT.md",
    ]
    for rel in paths:
        assert (ROOT / rel).exists(), rel


@pytest.mark.build_phase
def test_makefile_phase8_targets():
    makefile = (ROOT / "Makefile").read_text()
    assert "master-status:" in makefile
    assert "final-audit:" in makefile


@pytest.mark.build_phase
def test_do_not_overclaim_forbidden_phrases():
    text = (ROOT / "docs/DO_NOT_OVERCLAIM.md").read_text()
    assert "NeurIPS-ready" in text
    assert "we prove" in text.lower() or "we prove" in text
    assert "Safer alternatives" in text
