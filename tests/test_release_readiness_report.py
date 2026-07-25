from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.release_readiness import build_release_readiness_report


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_repo(tmp_path: Path, *, license_file: bool = False, no_run_doc: bool = True) -> Path:
    _write(
        tmp_path / "pyproject.toml",
        """
[project]
requires-python = ">=3.11"

[tool.pytest.ini_options]
markers = [
  "integration: integration tests",
  "local_run: starts local runs",
]
""",
    )
    _write(tmp_path / "README.md", "Setup with `python -m pip install -e .`.\n")
    docs = [
        "docs/PROVIDER_PILOT_READINESS_PACKET.md",
        "docs/REPRODUCIBILITY.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/DO_NOT_OVERCLAIM.md",
        "paper/EVIDENCE_GAP_MAP.md",
    ]
    if no_run_doc:
        docs.append("docs/NO_RUN_VALIDATION.md")
    for rel in docs:
        _write(tmp_path / rel, rel)
    claims = {
        "claims": [
            {"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)
        ]
        + [{"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "planned"}]
    }
    _write(tmp_path / "docs/claim_ledger.json", json.dumps(claims))
    _write(tmp_path / "reports/paper_asset_eligibility.json", json.dumps({"eligible_count": 0}))
    _write(tmp_path / "results/RUN_INDEX.jsonl", "")
    _write(
        tmp_path / "configs/provider_pilot_tiny_template.yaml",
        "allow_paid_calls: false\nrun_name: provider_pilot_tiny_PENDING_APPROVAL\n",
    )
    _write(tmp_path / "configs/provider_pilot_oracle_sanity_check_template.yaml", "allow_paid_calls: false\n")
    _write(tmp_path / "data/frozen/v/splits.json", "{}")
    _write(tmp_path / "CITATION.cff", "title: fixture\n")
    _write(tmp_path / "DATA_LICENSE.md", "fixture data license\n")
    if license_file:
        _write(tmp_path / "LICENSE", "MIT\n")
    return tmp_path


def _checks(report: dict) -> dict[str, dict]:
    return {check["name"]: check for check in report["checks"]}


def test_missing_lockfile_becomes_warning(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, license_file=True)
    report = build_release_readiness_report(repo, output_dir=repo / "reports_out")
    assert _checks(report)["lockfile missing"]["severity"] == "warning"


def test_no_eligible_runs_blocks_empirical_submission(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, license_file=True)
    report = build_release_readiness_report(repo, output_dir=repo / "reports_out")
    assert _checks(report)["no eligible runs"]["severity"] == "blocker_before_empirical_claims"
    assert report["verdicts"]["ready_for_empirical_paper_submission"] is False


def test_no_run_validation_docs_required(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, license_file=True, no_run_doc=False)
    report = build_release_readiness_report(repo, output_dir=repo / "reports_out")
    assert _checks(report)["no-run validation docs"]["severity"] == "warning"


def test_provider_template_allow_paid_calls_false(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, license_file=True)
    report = build_release_readiness_report(repo, output_dir=repo / "reports_out")
    assert _checks(report)["provider template safety"]["severity"] == "informational"


def test_missing_license_blocks_public_release(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, license_file=False)
    report = build_release_readiness_report(repo, output_dir=repo / "reports_out")
    assert _checks(report)["license file missing"]["severity"] == "blocker_before_public_release"
    assert report["verdicts"]["ready_for_public_release"] is False


def test_markdown_includes_reproduction_and_artifact_sections(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, license_file=True)
    report = build_release_readiness_report(repo, output_dir=repo / "reports_out")
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "Reproduction Paths" in md
    assert "Artifact Evaluation Checklist" in md
    assert "Public Release Blockers" in md
