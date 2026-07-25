"""Build Mode Phase 9 — mock demo and advisor-ready freeze tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO_RUN = ROOT / "results/20260520T072032Z_pilot_mock_diagnostic_micro"


@pytest.mark.build_phase
def test_phase9_docs_exist():
    paths = [
        "demo/ENGINEERING_DEMO_BUNDLE.md",
        "demo/engineering_demo_bundle.json",
        "demo/RUN_CARD_EXAMPLE.md",
        "demo/AGENT_CARD_EXAMPLE.md",
        "handoff/ADVISOR_SHOW_AND_TELL_CHECKLIST.md",
        "NEXT_DECISION.md",
        "audits/build_phase_9/PHASE_9_START_SNAPSHOT.md",
    ]
    for rel in paths:
        assert (ROOT / rel).exists(), rel


@pytest.mark.build_phase
def test_demo_run_metadata():
    if not DEMO_RUN.exists():
        pytest.skip("Phase 9 demo run not present")
    meta = json.loads((DEMO_RUN / "run_metadata.json").read_text())
    assert meta.get("scientific_evidence") is False
    assert meta.get("not_real_llm_behavior") is True
    assert meta.get("evidence_scope") == "mock_diagnostic_only"
    assert meta.get("paid_calls_made") is False


@pytest.mark.build_phase
def test_demo_paper_assets_not_eligible():
    if not DEMO_RUN.exists():
        pytest.skip("Phase 9 demo run not present")
    manifest = json.loads((DEMO_RUN / "paper_assets/paper_assets_manifest.json").read_text())
    assert manifest["assessment"]["eligible_for_paper_claims"] is False
    assert manifest["assessment"]["engineering_only"] is True


@pytest.mark.build_phase
def test_next_decision_recommends_pause():
    text = (ROOT / "NEXT_DECISION.md").read_text()
    assert "prepare_advisor_review" in text
    assert "pause" in text.lower()


@pytest.mark.build_phase
def test_engineering_demo_bundle_labels():
    data = json.loads((ROOT / "demo/engineering_demo_bundle.json").read_text())
    assert data["scientific_evidence"] is False
    assert data["not_real_llm_behavior"] is True
    assert "NOT REAL LLM" in data["label"]
