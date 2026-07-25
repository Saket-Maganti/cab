"""Tests for scripts/security_check.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.security_check import (
    _should_scan,
    check_gitignore,
    check_mock_tool_safety,
    check_required_files,
    run_security_check,
    scan_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_required_release_files_exist() -> None:
    errors = [f for f in check_required_files(REPO_ROOT) if f.severity == "error"]
    assert errors == [], [e.format() for e in errors]


def test_gitignore_covers_secrets() -> None:
    errors = [f for f in check_gitignore(REPO_ROOT) if f.severity == "error"]
    assert errors == [], [e.format() for e in errors]


def test_mock_tools_are_draft_and_stub_only() -> None:
    errors = [f for f in check_mock_tool_safety(REPO_ROOT) if f.severity == "error"]
    assert errors == [], [e.format() for e in errors]


def test_repo_security_scan_passes() -> None:
    errors = [f for f in run_security_check(REPO_ROOT) if f.severity == "error"]
    assert errors == [], [e.format() for e in errors]


def test_scan_detects_hardcoded_secret(tmp_path: Path) -> None:
    bad = tmp_path / "leak.py"
    bad.write_text('API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456"\n', encoding="utf-8")
    findings = scan_file(bad, tmp_path)
    assert any(f.kind == "openai_style_key" for f in findings)


def test_scan_allowlists_test_fixtures(tmp_path: Path) -> None:
    ok = tmp_path / "tests/test_foo.py"
    ok.parent.mkdir(parents=True)
    ok.write_text('secret = "sk-test-secret-that-must-not-appear"\n', encoding="utf-8")
    findings = scan_file(ok, tmp_path)
    assert findings == []


def test_generated_results_and_audits_are_outside_source_scan(tmp_path: Path) -> None:
    audit = tmp_path / "audits" / "generated.json"
    result = tmp_path / "results" / "run" / "trajectory.jsonl"
    source = tmp_path / "src" / "module.py"
    for path in (audit, result, source):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")

    assert _should_scan(audit, tmp_path) is False
    assert _should_scan(result, tmp_path) is False
    assert _should_scan(source, tmp_path) is True


def test_security_check_cli_passes() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/security_check.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "PASS" in proc.stdout
