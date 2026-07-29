from __future__ import annotations

from pathlib import Path

import pytest

from causal_agent_bench.safety.max_ceiling_gate import (
    CANONICAL_EVIDENCE_CLASSES,
    REQUIRED_FINAL_ARTIFACTS,
    REQUIRED_NOTEBOOKS,
    _large_file_inventory,
    derive_current_state,
    evaluate_max_ceiling_gate,
)
from causal_agent_bench.safety.workflow_state import (
    WorkflowState,
    parse_workflow_state,
    workflow_state_allows_live_execution,
    workflow_state_allows_paper_evidence,
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
    state = parse_workflow_state(gate["current_state"])
    assert (
        parse_workflow_state("METHODOLOGY_READY")
        is WorkflowState.METHODOLOGY_READY
    )
    if not gate["build_complete"]:
        assert state is WorkflowState.METHODOLOGY_READY
    assert workflow_state_allows_live_execution(state) is False
    assert workflow_state_allows_paper_evidence(state) is False
    assert gate["paper_eligible"] is False
    assert (
        gate["state_snapshot"]["human_validation"]["human_review_state"]
        == "HUMAN_REVIEW_INCOMPLETE"
    )
    assert gate["state_snapshot"]["human_validation"]["c10_state"] == "C10_PENDING"
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
    if gate["build_complete"]:
        assert gate["exact_next_allowed_action"].endswith("do not run models.")
    else:
        assert gate["exact_next_allowed_action"].startswith("Repair build check")


def test_unknown_workflow_state_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_workflow_state("UNKNOWN_FUTURE_STATE")


def test_required_inventory_is_exact() -> None:
    assert len(REQUIRED_NOTEBOOKS) == 9
    assert len(REQUIRED_FINAL_ARTIFACTS) == 15
    assert len(set(REQUIRED_NOTEBOOKS)) == 9
    assert len(set(REQUIRED_FINAL_ARTIFACTS)) == 15


def test_large_file_inventory_tolerates_disappearing_temp_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stable = tmp_path / "stable.bin"
    stable.write_bytes(b"stable")
    disappeared = tmp_path / ".coverage.transient"

    monkeypatch.setattr(
        "causal_agent_bench.safety.max_ceiling_gate._iter_files",
        lambda _root: iter([disappeared, stable]),
    )

    assert _large_file_inventory(tmp_path, threshold_bytes=1) == [
        {"path": "stable.bin", "bytes": 6}
    ]
