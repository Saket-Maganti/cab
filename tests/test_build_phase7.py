"""Build Mode Phase 7 — consolidation and quality gate tests."""

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
def test_audit_repo_consistency_runs():
    proc = _run("audit_repo_consistency.py")
    assert proc.returncode in (0, 1)
    assert (ROOT / "audits/repo_consistency/REPO_CONSISTENCY_AUDIT.md").exists()
    data = json.loads((ROOT / "audits/repo_consistency/repo_consistency_audit.json").read_text())
    assert "passed" in data
    assert "issues" in data


@pytest.mark.build_phase
def test_audit_configs_runs():
    proc = _run("audit_configs.py")
    assert proc.returncode in (0, 1)
    assert (ROOT / "audits/config_consistency/CONFIG_AUDIT.md").exists()
    data = json.loads((ROOT / "audits/config_consistency/config_audit.json").read_text())
    assert data["configs_scanned"] >= 40


@pytest.mark.build_phase
def test_generate_project_status():
    proc = _run("generate_project_status.py")
    assert proc.returncode == 0
    assert (ROOT / "PROJECT_STATUS.md").exists()
    data = json.loads((ROOT / "PROJECT_STATUS.json").read_text())
    assert data["classification"]
    assert "C1" in data["evidence_status"]["claims"]


@pytest.mark.build_phase
def test_makefile_targets_exist():
    makefile = (ROOT / "Makefile").read_text()
    for target in [
        "doctor:",
        "plan-micro:",
        "audit-configs:",
        "audit-repo:",
        "check-readiness:",
        "status:",
        "clean-pycache:",
    ]:
        assert target in makefile


@pytest.mark.build_phase
def test_phase7_docs_exist():
    paths = [
        "docs/CLI_REFERENCE.md",
        "docs/GENERATED_FILES_POLICY.md",
        "docs/DOC_STATUS_BOARD.md",
        "docs/TECH_DEBT_REGISTER.md",
        "handoff/PROFESSOR_READY_CHECKLIST.md",
        "audits/build_phase_7/PHASE_7_START_SNAPSHOT.md",
    ]
    for rel in paths:
        assert (ROOT / rel).exists(), rel


@pytest.mark.build_phase
def test_evidence_policy_has_canonical_vocabulary():
    text = (ROOT / "docs/EVIDENCE_LEVEL_POLICY.md").read_text()
    assert "Canonical vocabulary" in text
    assert "preliminary_or_engineering" in text
    assert "submission_ready" in text
