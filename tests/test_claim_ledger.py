"""Tests for claim ledger automation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from causal_agent_bench.claim_ledger import (
    check_paper_claims,
    extract_paper_claim_ids,
    normalize_claim,
    update_claim_ledger,
    update_claim_ledger_from_run,
    validate_claim_ledger,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _sample_claim(**overrides: object) -> dict:
    claim = {
        "claim_id": "C-test",
        "claim_text": "Test claim.",
        "short_name": "test_claim",
        "status": "planned",
        "required_evidence": "Need a run.",
        "linked_run_dirs": [],
        "linked_tables_figures": [],
        "linked_validation_files": [],
        "current_evidence_paths": [],
        "blocking_items": [],
        "notes": "",
        "owner": "pytest",
        "last_updated": "2026-05-12",
    }
    claim.update(overrides)
    return claim


def test_repo_claim_ledger_schema_valid() -> None:
    errors = validate_claim_ledger(REPO_ROOT / "docs" / "claim_ledger.json", REPO_ROOT)
    assert errors == [], errors


def test_normalize_claim_migrates_planned_artifacts() -> None:
    claim = normalize_claim(
        {
            "claim_id": "C1",
            "planned_artifacts": ["tables/table2_main_agent_performance.csv"],
        }
    )
    assert claim["linked_tables_figures"] == ["tables/table2_main_agent_performance.csv"]
    assert claim["claim_text"]


def test_supported_claim_requires_linked_run_dir(tmp_path: Path) -> None:
    ledger = tmp_path / "claim_ledger.json"
    evidence = tmp_path / "README.md"
    evidence.write_text("ok", encoding="utf-8")
    ledger.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "claims": [
                    _sample_claim(
                        status="supported",
                        current_evidence_paths=[evidence.name],
                        linked_run_dirs=[],
                    )
                ],
            }
        ),
        encoding="utf-8",
    )
    errors = validate_claim_ledger(ledger, repo_root=tmp_path)
    assert any("linked_run_dirs" in error for error in errors)


def test_update_claim_ledger_rejects_supported_without_evidence(tmp_path: Path) -> None:
    ledger = tmp_path / "claim_ledger.json"
    ledger.write_text(json.dumps({"schema_version": 2, "claims": [_sample_claim()]}), encoding="utf-8")
    try:
        update_claim_ledger(ledger, claim_id="C-test", status="supported")
    except ValueError as exc:
        message = str(exc)
        assert (
            "refusing manual status=supported" in message
            or "linked_run_dirs" in message
            or "current_evidence_paths" in message
        )
    else:
        raise AssertionError("expected supported promotion to fail without evidence")


def test_extract_paper_claim_ids_finds_claimref() -> None:
    paper = REPO_ROOT / "paper"
    ids = extract_paper_claim_ids(paper)
    assert "C1" in ids
    assert "C10" in ids


def test_paper_claim_check_warns_on_planned_in_submission(tmp_path: Path) -> None:
    ledger = tmp_path / "claim_ledger.json"
    ledger.write_text(
        json.dumps({"schema_version": 2, "claims": [_sample_claim(claim_id="C1")]}),
        encoding="utf-8",
    )
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "main.tex").write_text(r"Planned test \claimref{C1}.", encoding="utf-8")
    issues = check_paper_claims(ledger, paper, repo_root=tmp_path, mode="submission")
    assert any("C1" in issue and "submission mode" in issue for issue in issues)


def test_update_claim_ledger_from_run_links_run_dir(tmp_path: Path) -> None:
    repo = tmp_path
    run_dir = repo / "results" / "20260101_test"
    run_dir.mkdir(parents=True)
    (run_dir / "run_metadata.json").write_text(
        json.dumps({"evidence_scope": "pilot_stub_engineering_only"}),
        encoding="utf-8",
    )
    (run_dir / "scores.jsonl").write_text("{}\n", encoding="utf-8")
    ledger = repo / "claim_ledger.json"
    ledger.write_text(
        json.dumps({"schema_version": 2, "claims": [_sample_claim(claim_id="C1")]}),
        encoding="utf-8",
    )
    result = update_claim_ledger_from_run(
        ledger,
        run_dir,
        repo_root=repo,
        claim_ids=["C1"],
    )
    assert result["updated"] is True
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    claim = payload["claims"][0]
    assert claim["linked_run_dirs"] == ["results/20260101_test"]
    assert claim["status"] == "engineering_only"


def test_update_claim_ledger_cli_with_run_dir(tmp_path: Path) -> None:
    repo = tmp_path
    run_dir = repo / "results" / "run_a"
    run_dir.mkdir(parents=True)
    (run_dir / "run_metadata.json").write_text("{}", encoding="utf-8")
    ledger = repo / "claim_ledger.json"
    ledger.write_text(
        json.dumps({"schema_version": 2, "claims": [_sample_claim(claim_id="C1")]}),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "update-claim-ledger",
            "--ledger",
            str(ledger),
            "--run-dir",
            str(run_dir),
            "--claim-id",
            "C1",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"},
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["updated"] is True
    assert "results/run_a" in payload["run_dir"]
