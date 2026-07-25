"""Fixture-only tests for god-tier paper/advisor/release readiness (no runs)."""

from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.advisor_review_packet import build_advisor_review_packet
from causal_agent_bench.safety.benchmark_cards import build_benchmark_cards
from causal_agent_bench.safety.paper_readiness_map import build_paper_readiness_map
from causal_agent_bench.safety.publication_readiness import build_publication_readiness_report
from causal_agent_bench.safety.release_readiness import build_release_readiness_report


def _write(path: Path, payload: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, dict):
        path.write_text(json.dumps(payload), encoding="utf-8")
    else:
        path.write_text(payload, encoding="utf-8")


def _reports(tmp_path: Path) -> Path:
    reports = tmp_path / "reports"
    _write(
        reports / "run_health_report.json",
        {"summary": {"paper_eligible_count": 0}},
    )
    _write(reports / "paper_asset_eligibility.json", {"eligible_count": 0})
    claims = [{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)]
    claims.append({"claim_id": "C9", "status": "engineering_only"})
    claims.append({"claim_id": "C10", "status": "planned"})
    _write(reports / "claim_evidence_matrix.json", {"claims": claims})
    _write(
        reports / "static_leakage_report.json",
        {"summary": {"blocker_cluster_count": 1}},
    )
    return reports


def test_paper_readiness_blocks_unsupported_claim_wording(tmp_path: Path) -> None:
    report = build_paper_readiness_map(
        tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "paper"
    )
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "Allowed / Forbidden Wording Examples" in md
    assert "Forbidden:" in md
    assert "C1-C8 and C10 remain planned" in md


def test_advisor_packet_has_decision_checklist_and_no_claims_disclaimer(tmp_path: Path) -> None:
    report = build_advisor_review_packet(
        tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "advisor"
    )
    packet = Path(report["files"]["packet"]).read_text(encoding="utf-8")
    checklist = Path(report["files"]["checklist"]).read_text(encoding="utf-8")
    summary = Path(report["files"]["one_page_summary"]).read_text(encoding="utf-8")
    assert "No empirical claims yet" in packet
    assert "Decision checklist" in checklist
    assert "Approval checklist" in checklist
    assert "Do Not Approve Yet" in packet or "What Not to Approve Yet" in packet
    assert "No empirical claims yet" in summary


def test_dossier_audit_has_required_sections() -> None:
    root = Path(__file__).resolve().parents[1]
    dossier = (root / "PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md").read_text(encoding="utf-8")
    for heading in (
        "## 1. Executive Summary",
        "## 2. Current Verdict",
        "## 22. What Can Be Run Now",
        "## 23. What Must Not Be Run Yet",
        "## 27. Top Critical Blockers",
        "## 30. Final Recommendation",
    ):
        assert heading in dossier


def test_release_readiness_does_not_claim_public_release_ready(tmp_path: Path) -> None:
    repo = tmp_path
    _write(repo / "pyproject.toml", "[project]\nrequires-python = '>=3.11'\n")
    _write(repo / "README.md", "install\n")
    for rel in (
        "docs/PROVIDER_PILOT_READINESS_PACKET.md",
        "docs/REPRODUCIBILITY.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/DO_NOT_OVERCLAIM.md",
        "docs/NO_RUN_VALIDATION.md",
        "paper/EVIDENCE_GAP_MAP.md",
    ):
        _write(repo / rel, rel)
    _write(repo / "docs/claim_ledger.json", {"claims": []})
    _write(repo / "reports/paper_asset_eligibility.json", {"eligible_count": 0})
    _write(repo / "results/RUN_INDEX.jsonl", "")
    _write(
        repo / "configs/provider_pilot_tiny_template.yaml",
        "allow_paid_calls: false\nrun_name: provider_pilot_tiny_PENDING_APPROVAL\n",
    )
    _write(
        repo / "configs/provider_pilot_oracle_sanity_check_template.yaml",
        "allow_paid_calls: false\n",
    )
    _write(repo / "data/frozen/v/splits.json", "{}")
    _write(repo / "CITATION.cff", "title: x\n")
    _write(repo / "DATA_LICENSE.md", "data\n")
    _write(repo / "LICENSE", "MIT\n")
    report = build_release_readiness_report(repo, output_dir=repo / "out")
    assert report["verdicts"]["ready_for_public_release"] is False
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "Public Release Blockers" in md
    assert "Static-only" in md


def test_human_validation_docs_block_c3_c10(tmp_path: Path) -> None:
    from causal_agent_bench.safety.human_validation_packet import build_human_validation_packet

    report = build_human_validation_packet(tmp_path, output_dir=tmp_path / "hv")
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "C3 remains blocked" in md
    assert "C10 remains blocked" in md
    assert "placeholder" in md.lower()
    assert report["verdicts"]["claims_supported_by_packet"] is False


def test_command_runtime_guide_marks_provider_unsafe_before_approval() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/COMMAND_AND_RUNTIME_GUIDE.md").read_text(encoding="utf-8")
    assert "unsafe before approval" in text.lower() or "Unsafe commands" in text
    assert "allow_paid_calls: true" in text or "allow_paid_calls=true" in text
    assert "APPROVED" in text


def test_publication_readiness_honest_tiers(tmp_path: Path) -> None:
    report = build_publication_readiness_report(
        tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "pub"
    )
    assert report["summary"]["empirical_paper_ready"] is False
    assert report["summary"]["any_main_venue_ready"] is False
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "No empirical claims" in md or "C1" in md


def test_benchmark_cards_include_leakage_disclaimer(tmp_path: Path) -> None:
    reports = _reports(tmp_path)
    report = build_benchmark_cards(
        tmp_path, output_dir=tmp_path / "cards", reports_dir=reports
    )
    md = Path(report["files"]["benchmark_card"]).read_text(encoding="utf-8")
    assert "Leakage Status" in md
    assert "No Empirical Results Disclaimer" in md or "zero" in md.lower()
