import json
import os
import subprocess
import sys
from pathlib import Path

from causal_agent_bench.claim_ledger import validate_claim_ledger
from scripts.check_paper_placeholders import find_placeholders

REPO_ROOT = Path(__file__).resolve().parents[1]


def _env():
    return {**os.environ, "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"}


def test_paper_placeholder_check_draft_lists_placeholders():
    result = subprocess.run(
        [sys.executable, "scripts/check_paper_placeholders.py", "--mode", "draft"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=_env(),
    )
    assert "Draft mode passed" in result.stdout
    assert "[N]" in result.stdout


def test_paper_placeholder_check_submission_fails_until_results_exist():
    result = subprocess.run(
        [sys.executable, "scripts/check_paper_placeholders.py", "--mode", "submission"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
    )
    assert result.returncode == 1
    assert "Submission mode failed" in result.stdout


def test_paper_placeholder_check_detects_citep_todo_keys(tmp_path):
    paper_root = tmp_path / "paper"
    paper_root.mkdir()
    (paper_root / "main.tex").write_text(
        r"Unresolved citation \citep{todo_agent_benchmark_survey}.",
        encoding="utf-8",
    )
    (paper_root / "references.bib").write_text(
        "@article{todo_fake, title={Placeholder}}\n",
        encoding="utf-8",
    )

    findings = find_placeholders(paper_root)

    assert [finding.kind for finding in findings].count("todo_citation_key") == 2


def test_claim_ledger_check_passes_current_ledger():
    result = subprocess.run(
        [sys.executable, "scripts/check_claim_ledger.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=_env(),
    )
    assert "Claim ledger is valid" in result.stdout


def test_claim_ledger_rejects_supported_claim_without_evidence(tmp_path):
    ledger_path = tmp_path / "claim_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "C-test",
                        "short_name": "bad_supported_claim",
                        "status": "supported",
                        "required_evidence": "A real artifact.",
                        "current_evidence_paths": [],
                        "blocking_items": [],
                        "owner": "test",
                        "last_updated": "2026-05-10",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = validate_claim_ledger(ledger_path, repo_root=tmp_path)
    assert any("supported claims require" in error for error in errors)
