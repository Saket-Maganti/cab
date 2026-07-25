from __future__ import annotations

import csv
import json
from pathlib import Path

import nbformat
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_compact20_and_human_review_are_non_evidence():
    readiness = json.loads((ROOT / "data/compact20_reviewed/compact20_readiness.json").read_text())
    assert readiness["paper_eligibility"] is False
    assert readiness["c10_supported"] is False
    for name in ["task_clarity_review.csv", "gold_policy_review.csv", "intervention_isolation_review.csv", "adjudication_template.csv"]:
        rows = list(csv.DictReader((ROOT / "data/human_validation/compact20_real_review" / name).open()))
        assert rows == []


def test_provider_configs_are_not_live_and_have_no_secrets():
    for raw in ["configs/compact20_3model_APPROVAL_REQUIRED.yaml", "configs/5model_100task_TEMPLATE_NOT_APPROVED.yaml", "configs/main_500_multi_provider_TEMPLATE_NOT_APPROVED.yaml", "configs/naturalistic_ministudy_TEMPLATE_NOT_APPROVED.yaml"]:
        data = yaml.safe_load((ROOT / raw).read_text())
        assert data["allow_paid_calls"] is False
        assert data["approved_for_live_run"] is False
        assert data["scientific_claims_allowed"] is False
        assert data["paper_asset_eligibility"] is False
        assert "sk-" not in (ROOT / raw).read_text()


def test_provider_runbooks_are_gated_notebooks():
    for path in (ROOT / "notebooks/provider_pilot").glob("*.ipynb"):
        nb = nbformat.read(path, as_version=4)
        text = "\n".join(cell["source"] for cell in nb["cells"])
        assert nb["nbformat"] == 4
        assert "BLOCKED: live provider execution requires explicit approval" in text
        assert "/Users/" not in text
        assert "Provider credentials via environment variables only" in text


def test_final_gate_and_release_do_not_claim_results():
    gate = (ROOT / "reports/FINAL_SUBMISSION_GATE.md").read_text()
    assert "NOT_SUBMITTABLE_AS_MAIN_PAPER" in gate
    manifest = json.loads((ROOT / "release/MANIFEST.json").read_text())
    assert manifest["paper_evidence"] is False
    assert manifest["default_live_providers"] is False
    classification = (ROOT / "reports/COMPACT20_3MODEL_EVIDENCE_CLASSIFICATION.md").read_text()
    assert "NO_PROVIDER_BACKED_EVIDENCE" in classification
