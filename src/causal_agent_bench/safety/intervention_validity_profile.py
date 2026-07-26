"""Fail-closed validity profiles for controlled benchmark interventions.

The profile is deliberately independent of model outcomes. It records whether
an intervention is a valid member of the evaluation design; it must never be
inferred from the size or direction of an observed performance effect.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

VALIDITY_JUDGMENTS = {
    "pass",
    "fail",
    "uncertain",
    "not_reviewed",
}
EVIDENCE_CLASSES = {
    "DESIGN_ONLY",
    "ENGINEERING_ONLY",
    "FIXTURE_ONLY",
    "HUMAN_INPUT_REQUIRED",
    "EXECUTION_PENDING",
    "PRELIMINARY_REAL_EVIDENCE",
    "AUDITED_REAL_EVIDENCE",
    "PAPER_ELIGIBLE_EVIDENCE",
}

# These dimensions determine whether the clean/intervention contrast has the
# interpretation claimed by the benchmark.
PRIMARY_VALIDITY_DIMENSIONS = (
    "manipulation_success",
    "goal_preservation",
    "invariance_preservation",
    "solvability",
    "answer_contract_validity",
    "scorer_compatibility",
    "ambiguity",
)
ALL_VALIDITY_DIMENSIONS = (*PRIMARY_VALIDITY_DIMENSIONS, "realism")


@dataclass(frozen=True)
class ValidityAssessment:
    """One auditable judgment in an intervention-validity profile."""

    judgment: str
    rationale: str
    source: str

    def __post_init__(self) -> None:
        if self.judgment not in VALIDITY_JUDGMENTS:
            raise ValueError(
                f"unknown judgment {self.judgment!r}; expected one of "
                f"{sorted(VALIDITY_JUDGMENTS)}"
            )
        if not self.rationale.strip():
            raise ValueError("assessment rationale must be non-empty")
        if not self.source.strip():
            raise ValueError("assessment source must be non-empty")


@dataclass(frozen=True)
class InterventionValidityProfile:
    """Validity record for one frozen clean/intervention pair.

    ``reviewer_agreement`` is a proportion in ``[0, 1]`` and remains ``None``
    until at least two independent human reviews have been reconciled. Static
    checks may populate assessments, but they do not count as human reviewers.
    """

    profile_id: str
    base_task_id: str
    intervention_id: str
    intervention_family: str
    manipulation_success: ValidityAssessment
    goal_preservation: ValidityAssessment
    invariance_preservation: ValidityAssessment
    solvability: ValidityAssessment
    answer_contract_validity: ValidityAssessment
    scorer_compatibility: ValidityAssessment
    realism: ValidityAssessment
    ambiguity: ValidityAssessment
    reviewer_agreement: float | None
    reviewer_count: int
    exclusion_reason: str | None = None
    evidence_class: str = "HUMAN_INPUT_REQUIRED"

    def __post_init__(self) -> None:
        for field_name in (
            "profile_id",
            "base_task_id",
            "intervention_id",
            "intervention_family",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must be non-empty")
        if self.reviewer_count < 0:
            raise ValueError("reviewer_count must be non-negative")
        if self.reviewer_agreement is not None and not (
            0.0 <= self.reviewer_agreement <= 1.0
        ):
            raise ValueError("reviewer_agreement must be in [0, 1]")
        if self.reviewer_count < 2 and self.reviewer_agreement is not None:
            raise ValueError(
                "reviewer_agreement requires at least two human reviewers"
            )
        if self.evidence_class not in EVIDENCE_CLASSES:
            raise ValueError(
                f"unknown evidence_class {self.evidence_class!r}; "
                f"expected one of {sorted(EVIDENCE_CLASSES)}"
            )


def evaluate_intervention_validity(
    profile: InterventionValidityProfile,
    *,
    minimum_reviewer_agreement: float = 0.8,
) -> dict[str, Any]:
    """Evaluate a profile without silently filling missing human judgments.

    Low realism does not invalidate a controlled contrast. It blocks realism
    and transfer claims and is reported separately. Every primary validity
    dimension, including acceptable ambiguity, must pass for inclusion.
    """

    if not 0.0 <= minimum_reviewer_agreement <= 1.0:
        raise ValueError("minimum_reviewer_agreement must be in [0, 1]")

    assessments = {
        dimension: getattr(profile, dimension)
        for dimension in ALL_VALIDITY_DIMENSIONS
    }
    failed = sorted(
        dimension
        for dimension in PRIMARY_VALIDITY_DIMENSIONS
        if assessments[dimension].judgment == "fail"
    )
    unresolved = sorted(
        dimension
        for dimension in PRIMARY_VALIDITY_DIMENSIONS
        if assessments[dimension].judgment
        in {"uncertain", "not_reviewed"}
    )
    agreement_missing = (
        profile.reviewer_count < 2
        or profile.reviewer_agreement is None
    )
    agreement_low = (
        profile.reviewer_agreement is not None
        and profile.reviewer_agreement < minimum_reviewer_agreement
    )

    reasons: list[str] = []
    if failed:
        reasons.append("failed_dimensions:" + ",".join(failed))
    if unresolved:
        reasons.append("unresolved_dimensions:" + ",".join(unresolved))
    if agreement_missing:
        reasons.append("independent_human_review_incomplete")
    elif agreement_low:
        reasons.append("reviewer_agreement_below_threshold")
    if profile.exclusion_reason:
        reasons.append(f"recorded_exclusion:{profile.exclusion_reason}")

    if failed or profile.exclusion_reason:
        state = "excluded"
    elif unresolved or agreement_missing:
        state = "human_input_required"
    elif agreement_low:
        state = "adjudication_required"
    else:
        state = "valid"

    audited_evidence = profile.evidence_class in {
        "AUDITED_REAL_EVIDENCE",
        "PAPER_ELIGIBLE_EVIDENCE",
    }
    controlled_analysis_eligible = state == "valid" and audited_evidence
    realism_claim_eligible = (
        controlled_analysis_eligible
        and profile.realism.judgment == "pass"
    )
    return {
        "profile": asdict(profile),
        "profile_state": state,
        "failed_dimensions": failed,
        "unresolved_dimensions": unresolved,
        "reviewer_agreement_threshold": minimum_reviewer_agreement,
        "reviewer_agreement_gate_passed": (
            not agreement_missing and not agreement_low
        ),
        "include_in_primary_paired_analysis": (
            controlled_analysis_eligible
        ),
        "supports_controlled_intervention_claim": (
            controlled_analysis_eligible
        ),
        "supports_realism_or_transfer_claim": realism_claim_eligible,
        "exclusion_reasons": reasons,
        "evidence_class": profile.evidence_class,
        "scientific_evidence": profile.evidence_class
        in {
            "PRELIMINARY_REAL_EVIDENCE",
            "AUDITED_REAL_EVIDENCE",
            "PAPER_ELIGIBLE_EVIDENCE",
        },
    }
