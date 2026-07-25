"""Tests for the no-run paper section evidence contract."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.check_paper_section_contract import check_paper_section_contract

REPO = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_repo_paper_section_contract_draft_passes() -> None:
    issues = check_paper_section_contract(
        contract_path=REPO / "paper" / "paper_section_contract.json",
        ledger_path=REPO / "docs" / "claim_ledger.json",
        repo_root=REPO,
        mode="draft",
    )
    assert issues == [], [issue.format() for issue in issues]


def test_contract_flags_unsupported_result_language(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "docs" / "claim_ledger.json",
        {
            "schema_version": 2,
            "claims": [
                {
                    "claim_id": "C1",
                    "status": "planned",
                }
            ],
        },
    )
    paper_file = tmp_path / "paper" / "result.tex"
    paper_file.parent.mkdir(parents=True)
    paper_file.write_text("We show agents fail under intervention.\n", encoding="utf-8")
    _write_json(
        tmp_path / "paper" / "paper_section_contract.json",
        {
            "schema_version": 1,
            "sections": [
                {
                    "section_id": "results",
                    "paper_files": ["paper/result.tex"],
                    "claim_ids": ["C1"],
                    "minimum_claim_status_for_submission": "supported",
                    "required_markers_when_any_claim_unsupported": ["placeholder"],
                    "forbidden_when_any_claim_unsupported": ["we show", "agents fail"],
                    "must_clear_markers_for_submission": True,
                }
            ],
        },
    )

    issues = check_paper_section_contract(
        contract_path=tmp_path / "paper" / "paper_section_contract.json",
        ledger_path=tmp_path / "docs" / "claim_ledger.json",
        repo_root=tmp_path,
        mode="draft",
    )
    messages = "\n".join(issue.format() for issue in issues)
    assert "unsupported dependent claims lack required" in messages
    assert "forbidden result wording" in messages


def test_contract_submission_requires_supported_claims(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "docs" / "claim_ledger.json",
        {
            "schema_version": 2,
            "claims": [
                {
                    "claim_id": "C1",
                    "status": "planned",
                }
            ],
        },
    )
    paper_file = tmp_path / "paper" / "abstract.tex"
    paper_file.parent.mkdir(parents=True)
    paper_file.write_text("Planned final study; results not yet reported.\n", encoding="utf-8")
    _write_json(
        tmp_path / "paper" / "paper_section_contract.json",
        {
            "schema_version": 1,
            "sections": [
                {
                    "section_id": "abstract",
                    "paper_files": ["paper/abstract.tex"],
                    "claim_ids": ["C1"],
                    "minimum_claim_status_for_submission": "supported",
                    "required_markers_when_any_claim_unsupported": ["not yet reported"],
                    "must_clear_markers_for_submission": True,
                }
            ],
        },
    )

    issues = check_paper_section_contract(
        contract_path=tmp_path / "paper" / "paper_section_contract.json",
        ledger_path=tmp_path / "docs" / "claim_ledger.json",
        repo_root=tmp_path,
        mode="submission",
    )
    messages = "\n".join(issue.format() for issue in issues)
    assert "submission requires supported" in messages
    assert "submission text still contains" in messages
