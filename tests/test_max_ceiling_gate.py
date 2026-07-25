from __future__ import annotations

from pathlib import Path

from causal_agent_bench.safety.max_ceiling_gate import (
    CANONICAL_EVIDENCE_CLASSES,
    REQUIRED_FINAL_ARTIFACTS,
    REQUIRED_NOTEBOOKS,
    derive_current_state,
    evaluate_max_ceiling_gate,
)

ROOT = Path(__file__).resolve().parents[1]


def test_max_ceiling_state_is_derived_and_evidence_bounded() -> None:
    state = derive_current_state(ROOT)
    assert state["repository"]["commit"]
    assert state["datasets"]["cross_role_overlap_count"] == 0
    assert state["evidence"]["genuine_human_rows"] == 0
    assert state["evidence"]["real_provider_trajectories"] == 0
    assert state["evidence"]["real_open_model_trajectories"] == 0
    assert state["evidence"]["paper_eligible_assets"] == 0
    assert state["boundary"]["scientific_execution_performed_by_this_build"] is False
    assert tuple(CANONICAL_EVIDENCE_CLASSES)[-1] == "PAPER_ELIGIBLE_EVIDENCE"


def test_unified_gate_separates_build_and_external_blockers() -> None:
    gate = evaluate_max_ceiling_gate(ROOT)
    assert gate["scientific_execution_allowed"] is False
    assert gate["current_state"] in {
        "HUMAN_REVIEW_PENDING",
        "HUMAN_REVIEW_INCOMPLETE",
        "ADJUDICATION_PENDING",
        "C10_PENDING",
    }
    check_ids = {row["check_id"] for row in gate["checks"]}
    assert {
        "repository_consistency",
        "leakage",
        "schemas",
        "scorer",
        "metrics",
        "human_review",
        "c10",
        "slice_integrity",
        "configs",
        "secrets",
        "provider_approval",
        "notebooks",
        "provenance",
        "paper_claims",
        "paper_assets",
        "release_status",
    } <= check_ids
    assert any(row["check_id"] == "human_review" for row in gate["external_blockers"])
    assert gate["exact_next_allowed_action"].endswith("do not run models.")


def test_required_inventory_is_exact() -> None:
    assert len(REQUIRED_NOTEBOOKS) == 9
    assert len(REQUIRED_FINAL_ARTIFACTS) == 15
    assert len(set(REQUIRED_NOTEBOOKS)) == 9
    assert len(set(REQUIRED_FINAL_ARTIFACTS)) == 15
