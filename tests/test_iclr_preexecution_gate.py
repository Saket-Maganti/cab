from __future__ import annotations

from causal_agent_bench.safety.iclr_preexecution_gate import (
    derive_iclr_state,
    evaluate_iclr_preexecution_readiness,
    exit_code_for_state,
)
from causal_agent_bench.safety.workflow_state import WorkflowState


def _maximum(*, build_complete: bool, human_state: str) -> dict:
    return {
        "build_complete": build_complete,
        "build_blockers": [] if build_complete else [{"check_id": "release"}],
        "state_snapshot": {
            "notebooks": {
                "present_count": 9,
                "required_count": 9,
                "live_default": False,
            },
            "human_validation": {
                "human_review_state": human_state,
                "c10_state": "C10_PENDING",
                "slice_lock_allowed": False,
            },
            "evidence": {
                "genuine_human_rows": 0,
                "real_provider_trajectories": 0,
                "real_open_model_trajectories": 0,
                "audited_real_runs": 0,
                "paper_eligible_assets": 0,
                "supported_empirical_claims": 0,
            },
        },
    }


def _registry() -> dict:
    roles = []
    for role, base, interventions, instances in (
        ("scale100_confirmatory_v2_protected", 100, 500, 600),
        ("naturalistic_transfer_v2_protected", 60, 300, 360),
        ("heldout_challenge_v2_protected", 50, 250, 300),
    ):
        roles.append(
            {
                "role": role,
                "unique_base_task_count": base,
                "intervention_count": interventions,
                "instance_count": instances,
                "membership_visibility": "PRIVATE_COMMITMENT_ONLY",
                "confirmatory_eligible": False,
                "paper_eligible": False,
                "scientific_execution_allowed": False,
            }
        )
    return {
        "passed": True,
        "cross_role_overlap_count": 0,
        "roles": roles,
    }


def test_expected_preexecution_state_is_human_validation_required(tmp_path) -> None:
    report = evaluate_iclr_preexecution_readiness(
        tmp_path,
        max_ceiling_report=_maximum(
            build_complete=True,
            human_state="HUMAN_REVIEW_INCOMPLETE",
        ),
        protected_report={"passed": True, "issues": []},
        registry_report=_registry(),
        required_files=(),
    )
    assert report["current_state"] == "HUMAN_VALIDATION_REQUIRED"
    assert report["exit_code"] == 2
    assert report["build_complete"] is True
    assert report["evidence_counts"] == {
        "genuine_human_rows": 0,
        "real_trajectories": 0,
        "audited_real_runs": 0,
        "paper_eligible_assets": 0,
        "supported_empirical_claims": 0,
    }
    assert report["scientific_execution_allowed"] is False


def test_build_failure_uses_exit_one(tmp_path) -> None:
    report = evaluate_iclr_preexecution_readiness(
        tmp_path,
        max_ceiling_report=_maximum(
            build_complete=False,
            human_state="HUMAN_REVIEW_INCOMPLETE",
        ),
        protected_report={"passed": True, "issues": []},
        registry_report=_registry(),
        required_files=(),
    )
    assert report["current_state"] == "ICLR_BUILD_INCOMPLETE"
    assert report["exit_code"] == 1


def test_canonical_state_progression_and_exit_codes() -> None:
    evidence = {
        "audited_real_runs": 0,
        "paper_eligible_assets": 0,
        "supported_empirical_claims": 0,
    }
    state = derive_iclr_state(
        build_complete=True,
        human_state="HUMAN_REVIEW_COMPLETE",
        c10_state="PASS",
        slice_lock_allowed=True,
        evidence_counts=evidence,
    )
    assert state is WorkflowState.COMPACT20_READY
    assert exit_code_for_state(state) == 0
    assert exit_code_for_state(WorkflowState.C10_PENDING) == 2
    assert exit_code_for_state(WorkflowState.ICLR_BUILD_INCOMPLETE) == 1
