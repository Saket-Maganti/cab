from __future__ import annotations

from dataclasses import replace

import pytest

from causal_agent_bench.safety.intervention_validity_profile import (
    InterventionValidityProfile,
    ValidityAssessment,
    evaluate_intervention_validity,
)


def _assessment(
    judgment: str = "pass",
    *,
    source: str = "blinded_human_review_packet",
) -> ValidityAssessment:
    return ValidityAssessment(
        judgment=judgment,
        rationale=f"fixture rationale for {judgment}",
        source=source,
    )


def _profile(
    **overrides: object,
) -> InterventionValidityProfile:
    values: dict[str, object] = {
        "profile_id": "profile-1",
        "base_task_id": "task-1",
        "intervention_id": "task-1.tool_failure",
        "intervention_family": "tool_failure",
        "manipulation_success": _assessment(),
        "goal_preservation": _assessment(),
        "invariance_preservation": _assessment(),
        "solvability": _assessment(),
        "answer_contract_validity": _assessment(),
        "scorer_compatibility": _assessment(),
        "realism": _assessment(),
        "ambiguity": _assessment(),
        "reviewer_agreement": 1.0,
        "reviewer_count": 2,
        "evidence_class": "AUDITED_REAL_EVIDENCE",
    }
    values.update(overrides)
    return InterventionValidityProfile(**values)  # type: ignore[arg-type]


def test_audited_all_pass_profile_is_primary_analysis_eligible() -> None:
    result = evaluate_intervention_validity(_profile())

    assert result["profile_state"] == "valid"
    assert result["include_in_primary_paired_analysis"] is True
    assert result["supports_controlled_intervention_claim"] is True
    assert result["supports_realism_or_transfer_claim"] is True
    assert result["exclusion_reasons"] == []


@pytest.mark.parametrize(
    "dimension",
    [
        "manipulation_success",
        "goal_preservation",
        "invariance_preservation",
        "solvability",
        "answer_contract_validity",
        "scorer_compatibility",
        "ambiguity",
    ],
)
def test_every_primary_dimension_fails_closed(dimension: str) -> None:
    profile = replace(_profile(), **{dimension: _assessment("fail")})
    result = evaluate_intervention_validity(profile)

    assert result["profile_state"] == "excluded"
    assert result["include_in_primary_paired_analysis"] is False
    assert result["failed_dimensions"] == [dimension]


def test_missing_human_review_cannot_be_inferred_from_static_checks() -> None:
    profile = replace(
        _profile(),
        reviewer_count=0,
        reviewer_agreement=None,
        evidence_class="ENGINEERING_ONLY",
        manipulation_success=_assessment(source="static_validator"),
    )
    result = evaluate_intervention_validity(profile)

    assert result["profile_state"] == "human_input_required"
    assert result["reviewer_agreement_gate_passed"] is False
    assert result["include_in_primary_paired_analysis"] is False
    assert "independent_human_review_incomplete" in result[
        "exclusion_reasons"
    ]


def test_low_realism_preserves_internal_contrast_but_blocks_transfer_claim() -> None:
    profile = replace(_profile(), realism=_assessment("fail"))
    result = evaluate_intervention_validity(profile)

    assert result["profile_state"] == "valid"
    assert result["supports_controlled_intervention_claim"] is True
    assert result["supports_realism_or_transfer_claim"] is False


def test_low_agreement_requires_adjudication() -> None:
    result = evaluate_intervention_validity(
        replace(_profile(), reviewer_agreement=0.5)
    )

    assert result["profile_state"] == "adjudication_required"
    assert result["include_in_primary_paired_analysis"] is False


def test_profile_rejects_impossible_agreement_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="requires at least two human reviewers",
    ):
        _profile(reviewer_count=1, reviewer_agreement=1.0)


def test_recorded_exclusion_reason_is_fail_closed() -> None:
    result = evaluate_intervention_validity(
        replace(_profile(), exclusion_reason="answer contract drift")
    )

    assert result["profile_state"] == "excluded"
    assert result["include_in_primary_paired_analysis"] is False
    assert (
        "recorded_exclusion:answer contract drift"
        in result["exclusion_reasons"]
    )
