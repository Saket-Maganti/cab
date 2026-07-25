from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.advisor_review_packet import build_advisor_review_packet


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_packet_generated(tmp_path: Path) -> None:
    report = build_advisor_review_packet(tmp_path, output_dir=tmp_path / "advisor")
    assert Path(report["files"]["packet"]).exists()
    assert Path(report["files"]["checklist"]).exists()
    assert Path(report["manifest_path"]).exists()


def test_blocked_claims_listed(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "claim_evidence_matrix.json", {"claims": [{"claim_id": "C1", "status": "planned"}, {"claim_id": "C9", "status": "engineering_only"}]})
    report = build_advisor_review_packet(tmp_path, reports_dir=reports, output_dir=tmp_path / "advisor")
    text = Path(report["files"]["packet"]).read_text(encoding="utf-8")
    assert "C1: planned" in text
    assert "C9: engineering_only" in text


def test_no_empirical_claims(tmp_path: Path) -> None:
    report = build_advisor_review_packet(tmp_path, output_dir=tmp_path / "advisor")
    text = Path(report["files"]["packet"]).read_text(encoding="utf-8")
    manifest = json.loads(Path(report["manifest_path"]).read_text(encoding="utf-8"))
    assert "does not claim empirical results" in text
    assert manifest["hard_rules"]["empirical_results_claimed"] is False
    assert manifest["hard_rules"]["claims_marked_supported"] is False


def test_decision_options_and_signature_present(tmp_path: Path) -> None:
    report = build_advisor_review_packet(tmp_path, output_dir=tmp_path / "advisor")
    text = Path(report["files"]["packet"]).read_text(encoding="utf-8")
    assert "approve tiny provider dry-run" in text
    assert "request dataset fixes first" in text
    assert "defer provider spend" in text
    assert "Advisor name:" in text
    assert "Date:" in text
