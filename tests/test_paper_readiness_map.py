from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.paper_readiness_map import build_paper_readiness_map


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _reports(tmp_path: Path) -> Path:
    reports = tmp_path / "reports"
    _write(reports / "run_health_report.json", {"summary": {"paper_eligible_count": 0}})
    _write(reports / "paper_asset_eligibility.json", {"eligible_count": 0})
    _write(reports / "claim_evidence_matrix.json", {"claims": [{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)] + [{"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "planned"}]})
    return reports


def _section(report: dict, name: str) -> dict:
    return next(row for row in report["sections"] if row["section"] == name)


def test_results_blocked_without_eligible_runs(tmp_path: Path) -> None:
    report = build_paper_readiness_map(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "paper")
    assert _section(report, "results")["readiness_status"] == "blocked"


def test_human_validation_blocked_without_annotation_artifacts(tmp_path: Path) -> None:
    report = build_paper_readiness_map(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "paper")
    assert _section(report, "human validation")["readiness_status"] == "blocked"
    assert "protocol/templates only" in _section(report, "human validation")["allowed_wording"]


def test_method_section_ready_method_only(tmp_path: Path) -> None:
    report = build_paper_readiness_map(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "paper")
    assert _section(report, "benchmark design")["readiness_status"] == "ready_method_only"


def test_abstract_cannot_include_unsupported_claims(tmp_path: Path) -> None:
    report = build_paper_readiness_map(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "paper")
    abstract = _section(report, "abstract")
    assert abstract["readiness_status"] == "needs_evidence"
    assert "unsupported empirical" in abstract["forbidden_wording"]


def test_output_generated(tmp_path: Path) -> None:
    report = build_paper_readiness_map(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "paper")
    assert Path(report["report_paths"]["json"]).exists()
    assert Path(report["report_paths"]["markdown"]).exists()


def test_markdown_includes_wording_examples(tmp_path: Path) -> None:
    report = build_paper_readiness_map(tmp_path, reports_dir=_reports(tmp_path), output_dir=tmp_path / "paper")
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "Allowed / Forbidden Wording Examples" in md
    assert "### Abstract" in md
