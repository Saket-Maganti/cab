"""Fixture-only tests for NeurIPS artifact upgrade docs and evidence firewall."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from causal_agent_bench.safety.claim_evidence_matrix import build_claim_evidence_matrix
from causal_agent_bench.safety.paper_readiness_map import build_paper_readiness_map

REPO = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


# --- NeurIPS checklist: blocked empirical state ---


@pytest.mark.parametrize(
    "path",
    [
        "docs/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md",
        "reports/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md",
    ],
)
def test_neurips_checklist_states_blocked_empirical(path: str) -> None:
    text = _read(path)
    assert "0" in text and "paper-eligible" in text.lower()
    assert "blocked" in text.lower()
    assert "C1" in text and "C10" in text
    assert "planned" in text.lower() or "unsupported" in text.lower()
    assert "engineering_only" in text or "engineering_only" in text.replace("-", "_")
    assert "template_safe_but_not_runnable" in text or "not runnable" in text.lower()


def test_neurips_checklist_covers_required_sections() -> None:
    text = _read("docs/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md")
    for heading in (
        "Benchmark motivation",
        "Dataset construction",
        "Intervention taxonomy",
        "Data leakage controls",
        "Metric definitions",
        "Human validation",
        "Provider-run requirements",
        "Reproducibility commands",
        "What is currently ready",
        "What is currently blocked",
    ):
        assert heading in text


# --- Reviewer quickstart: forbids provider run without approval ---


def test_reviewer_quickstart_forbids_provider_without_approval() -> None:
    text = _read("docs/REVIEWER_QUICKSTART_NEURIPS.md")
    assert "NOT runnable" in text or "not runnable" in text.lower()
    assert "BLOCKED" in text or "blocked" in text.lower()
    assert "allow_paid_calls: false" in text or "allow_paid_calls: false" in text.replace(" ", "")
    assert "APPROVED" in text
    assert "template_safe_but_not_runnable" in text
    # Must warn against inferring results from planning commands
    assert "Do not infer" in text or "do not infer" in text.lower()


def test_reviewer_quickstart_has_timeboxed_paths() -> None:
    text = _read("docs/REVIEWER_QUICKSTART_NEURIPS.md")
    assert "5-minute" in text or "5 minute" in text
    assert "15-minute" in text or "15 minute" in text
    assert "30-minute" in text or "30 minute" in text
    assert "all-no-run-reports" in text


# --- Artifact manifest: 0 eligible runs/assets ---


def test_artifact_manifest_json_zero_eligible() -> None:
    payload = json.loads(_read("release/benchmark_artifact_manifest.json"))
    evidence = payload["evidence_state"]
    assert evidence["paper_eligible_runs"] == 0
    assert evidence["eligible_empirical_assets"] == 0
    assert evidence["provider_backed_scientific_evidence"] is False
    assert evidence["approved_provider_config_present"] is False


def test_benchmark_artifact_manifest_md_zero_eligible() -> None:
    text = _read("docs/BENCHMARK_ARTIFACT_MANIFEST.md")
    assert "paper_eligible_runs:          0" in text or "paper_eligible_runs: 0" in text.replace(" ", "")
    assert "eligible_empirical_assets:    0" in text or "eligible_empirical_assets: 0" in text.replace(" ", "")


def test_god_tier_manifest_links_neurips_bundle() -> None:
    text = _read("GOD_TIER_MANIFEST.md")
    assert "NEURIPS_ARTIFACT_READINESS_CHECKLIST" in text
    assert "REVIEWER_QUICKSTART_NEURIPS" in text
    assert "infrastructure_artifact_candidate" in text


# --- Reproducibility tiers: provider runs approval-required ---


def test_reproducibility_tiers_provider_approval_required() -> None:
    text = _read("docs/REPRODUCIBILITY_TIERS.md")
    assert "Tier 3" in text
    assert "Approval required" in text or "approval" in text.lower()
    assert "Blocked" in text or "blocked" in text
    assert "APPROVED" in text
    assert "allow_paid_calls" in text
    tier3 = text.split("## Tier 3")[1].split("## Tier 4")[0]
    assert "Blocked" in tier3 or "blocked" in tier3


# --- Self-review rubric: does not overclaim ---


def test_self_review_rubric_conservative_scores() -> None:
    text = _read("docs/NEURIPS_SELF_REVIEW_RUBRIC.md")
    assert "Empirical completeness" in text
    assert "1 / 5" in text or "1/5" in text
    assert "0 paper-eligible" in text.lower() or "0 paper-eligible runs" in text.lower()
    assert "not" in text.lower() and "empirical" in text.lower()
    # Must not claim venue acceptance
    assert not re.search(r"\b(accepted|camera-ready results)\b", text, re.I)


def test_contribution_map_blocks_empirical() -> None:
    text = _read("docs/NEURIPS_CONTRIBUTION_MAP.md")
    assert "currently blocked" in text.lower()
    assert "Do not write" in text or "do not" in text.lower()
    assert "0 paper-eligible" in text.lower() or "0 paper-eligible runs" in text.lower()


# --- Dataset release: frozen vs processed ---


def test_dataset_release_distinguishes_frozen_vs_processed() -> None:
    text = _read("docs/DATASET_RELEASE_READINESS.md")
    assert "Frozen" in text or "frozen" in text
    assert "processed" in text.lower()
    assert "data/frozen" in text
    assert "data/processed" in text
    frozen_section = text.lower()
    assert "release authority" in frozen_section or "not release authority" in frozen_section


# --- Paper firewall: blocks unsupported claims (code + docs) ---


def test_claim_evidence_matrix_firewall_section(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "run_health_report.json").write_text(
        json.dumps({"summary": {"paper_eligible_count": 0}}), encoding="utf-8"
    )
    ledger = REPO / "docs/claim_ledger.json"
    build_claim_evidence_matrix(
        REPO,
        ledger_path=ledger,
        results_root=REPO / "results",
        output_dir=reports,
        write_tex=False,
    )
    md = (reports / "claim_evidence_matrix.md").read_text(encoding="utf-8")
    assert "Evidence-to-paper firewall" in md
    assert "Eligible scientific runs in index: 0" in md
    assert "C9 only" in md or "engineering_only" in md


def test_paper_readiness_map_blocks_abstract_claims(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    claims = [{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)]
    claims.append({"claim_id": "C9", "status": "engineering_only"})
    claims.append({"claim_id": "C10", "status": "planned"})
    (reports / "run_health_report.json").write_text(
        json.dumps({"summary": {"paper_eligible_count": 0}}), encoding="utf-8"
    )
    (reports / "paper_asset_eligibility.json").write_text(
        json.dumps({"eligible_count": 0}), encoding="utf-8"
    )
    (reports / "claim_evidence_matrix.json").write_text(
        json.dumps({"claims": claims}), encoding="utf-8"
    )
    report = build_paper_readiness_map(REPO, reports_dir=reports, output_dir=tmp_path / "out")
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "NeurIPS paper firewall summary" in md
    assert "blocked" in md.lower()
    abstract = next(s for s in report["sections"] if s["section"] == "abstract")
    assert abstract["readiness_status"] == "needs_evidence"
    assert "unsupported" in abstract["forbidden_wording"].lower()


def test_abstract_tex_guard_no_false_results() -> None:
    abstract = _read("paper/latexpaper/generated/00_abstract.tex")
    assert "not yet reported" in abstract.lower() or "not yet" in abstract.lower()


def test_do_not_overclaim_neurips_firewall() -> None:
    text = _read("docs/DO_NOT_OVERCLAIM.md")
    assert "NeurIPS artifact firewall" in text
    assert "Abstract" in text
    assert "Conclusion" in text
