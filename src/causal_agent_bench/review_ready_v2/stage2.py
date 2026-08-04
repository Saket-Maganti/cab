"""Substantive Stage-2 review: a completed form is not an approval.

Stage 2 asks the reviewer to accept or reject the withheld material — gold,
accepted variants, answer contracts, scorer compatibility, intervention policy,
route defensibility, and the recovery / abstention / clarification policies.

Four values are allowed.  Only two of them accept:

``YES``              the reviewer accepts this dimension.
``NOT_APPLICABLE``   the dimension does not exist for this item, and the frozen
                     applicability map agrees that it does not.
``NO``               a substantive objection.  Blocks acceptance.
``UNSURE``           unresolved.  Blocks acceptance just as firmly as ``NO``.

``NO`` and ``UNSURE`` require notes, and neither can be cleared by completing the
form: they are cleared only by an adjudicator's final value.  Nothing here reads
as approval merely because every cell is filled in.
"""

from __future__ import annotations

from typing import Any

YES = "YES"
NO = "NO"
UNSURE = "UNSURE"
NOT_APPLICABLE = "NOT_APPLICABLE"

STAGE2_VALUES: tuple[str, ...] = (YES, NO, UNSURE, NOT_APPLICABLE)
ACCEPTING_VALUES: frozenset[str] = frozenset({YES, NOT_APPLICABLE})
BLOCKING_VALUES: tuple[str, ...] = (NO, UNSURE)

STAGE2_ACCEPTANCE_POLICY_VERSION = "cab_stage2_acceptance_policy_v1"
STAGE2_FORM_SCHEMA_VERSION = "cab_stage2_review_form_v2"

#: Dimensions that always apply to every pair.
STAGE2_CORE_DIMENSIONS: tuple[str, ...] = (
    "gold_correct",
    "accepted_variants_complete",
    "answer_contract_valid",
    "scorer_compatible",
    "intervention_policy_valid",
    "route_policy_defensible",
)

#: Dimensions that may legitimately be ``NOT_APPLICABLE`` — but only when the
#: frozen applicability map, derived from the private Stage-2 record, agrees.
STAGE2_CONDITIONAL_DIMENSIONS: tuple[str, ...] = (
    "recovery_authorization_valid_or_not_applicable",
    "abstention_policy_valid_or_not_applicable",
    "clarification_policy_valid_or_not_applicable",
)

STAGE2_SUBSTANTIVE_DIMENSIONS: tuple[str, ...] = (
    *STAGE2_CORE_DIMENSIONS,
    *STAGE2_CONDITIONAL_DIMENSIONS,
)

STAGE2_FORM_COLUMNS: tuple[str, ...] = (
    "reviewer_item_id",
    *STAGE2_SUBSTANTIVE_DIMENSIONS,
    "exclude_item",
    "reviewer_confidence",
    "notes",
)

EXCLUDE_VALUES: tuple[str, ...] = (YES, NO)
CONFIDENCE_VALUES: tuple[str, ...] = ("1", "2", "3", "4", "5")

#: Below this, the row goes to adjudication even when every value accepts.
MIN_REVIEWER_CONFIDENCE = 3

#: Which private Stage-2 field decides whether a conditional dimension applies.
_APPLICABILITY_SOURCE: dict[str, str] = {
    "recovery_authorization_valid_or_not_applicable": "recovery_authorization",
    "abstention_policy_valid_or_not_applicable": "abstention_opportunity",
    "clarification_policy_valid_or_not_applicable": "clarification_requirement",
}


class Stage2Error(ValueError):
    """A Stage-2 submission or policy check refused."""


def acceptance_policy() -> dict[str, Any]:
    """The machine-readable acceptance rule, frozen before genuine review."""

    return {
        "schema_version": STAGE2_ACCEPTANCE_POLICY_VERSION,
        "form_schema_version": STAGE2_FORM_SCHEMA_VERSION,
        "allowed_values": list(STAGE2_VALUES),
        "accepting_values": sorted(ACCEPTING_VALUES),
        "blocking_values": list(BLOCKING_VALUES),
        "core_dimensions": list(STAGE2_CORE_DIMENSIONS),
        "conditional_dimensions": list(STAGE2_CONDITIONAL_DIMENSIONS),
        "not_applicable_allowed_dimensions": list(STAGE2_CONDITIONAL_DIMENSIONS),
        "notes_required_for_values": list(BLOCKING_VALUES),
        "min_reviewer_confidence": MIN_REVIEWER_CONFIDENCE,
        "rules": [
            "NO is a substantive objection and blocks acceptance of that dimension.",
            "UNSURE is unresolved and blocks acceptance exactly as NO does.",
            (
                "NOT_APPLICABLE is accepted only for a conditional dimension whose frozen "
                "applicability map marks it structurally inapplicable for that item."
            ),
            "Notes are mandatory for every NO and every UNSURE.",
            (
                "reviewer_confidence below the minimum sends the item to adjudication even when "
                "every value would otherwise accept."
            ),
            "A complete Stage-2 form is not an approval; completion and acceptance are separate.",
            (
                "A dimension is accepted only when the final adjudicated value is YES, or is "
                "NOT_APPLICABLE and the applicability map agrees."
            ),
            (
                "No item carrying an unresolved NO or UNSURE may enter a C10 pass or a reviewed "
                "slice lock."
            ),
        ],
        "form_completion_is_not_approval": True,
        "frozen_before_genuine_review": True,
    }


def applicability_for(stage2_record: dict[str, Any]) -> dict[str, bool]:
    """Which conditional dimensions genuinely apply to one pair."""

    applicability: dict[str, bool] = dict.fromkeys(STAGE2_CORE_DIMENSIONS, True)
    for dimension, field in _APPLICABILITY_SOURCE.items():
        value = stage2_record.get(field)
        applicable = bool(value) and value not in ("", None, "none", "not_applicable")
        applicability[dimension] = applicable
    return applicability


def stage2_form_template(item_ids: list[str]) -> bytes:
    rows = [",".join(STAGE2_FORM_COLUMNS)]
    rows.extend(item_id + "," * (len(STAGE2_FORM_COLUMNS) - 1) for item_id in item_ids)
    return ("\n".join(rows) + "\n").encode()


def normalize_value(raw: str) -> str:
    return str(raw or "").strip().upper()


def validate_stage2_submission(
    rows: dict[str, dict[str, str]],
    expected_item_ids: list[str],
    applicability: dict[str, dict[str, bool]],
) -> dict[str, Any]:
    """Validate form *and* substance, and report what still blocks acceptance."""

    problems: list[dict[str, str]] = []
    missing = sorted(set(expected_item_ids) - set(rows))
    unexpected = sorted(set(rows) - set(expected_item_ids))
    blocking: list[dict[str, str]] = []

    for item_id, row in sorted(rows.items()):
        item_applicability = applicability.get(item_id, {})
        notes = str(row.get("notes", "")).strip()
        for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS:
            value = normalize_value(row.get(dimension, ""))
            if value not in STAGE2_VALUES:
                problems.append(
                    {"reviewer_item_id": item_id, "column": dimension, "issue": "invalid_value"}
                )
                continue
            if value == NOT_APPLICABLE:
                if dimension not in STAGE2_CONDITIONAL_DIMENSIONS:
                    problems.append(
                        {
                            "reviewer_item_id": item_id,
                            "column": dimension,
                            "issue": "not_applicable_forbidden_for_core_dimension",
                        }
                    )
                elif item_applicability.get(dimension, True):
                    problems.append(
                        {
                            "reviewer_item_id": item_id,
                            "column": dimension,
                            "issue": "not_applicable_contradicts_applicability_map",
                        }
                    )
                continue
            if value in BLOCKING_VALUES:
                blocking.append(
                    {"reviewer_item_id": item_id, "dimension": dimension, "value": value}
                )
                if not notes:
                    problems.append(
                        {"reviewer_item_id": item_id, "column": "notes", "issue": "required"}
                    )
            if value == YES and dimension in STAGE2_CONDITIONAL_DIMENSIONS:
                if not item_applicability.get(dimension, True):
                    problems.append(
                        {
                            "reviewer_item_id": item_id,
                            "column": dimension,
                            "issue": "accepted_a_structurally_inapplicable_dimension",
                        }
                    )

        exclude = normalize_value(row.get("exclude_item", ""))
        if exclude not in EXCLUDE_VALUES:
            problems.append(
                {"reviewer_item_id": item_id, "column": "exclude_item", "issue": "invalid_value"}
            )
        elif exclude == YES and not notes:
            problems.append({"reviewer_item_id": item_id, "column": "notes", "issue": "required"})

        confidence = str(row.get("reviewer_confidence", "")).strip()
        if confidence not in CONFIDENCE_VALUES:
            problems.append(
                {
                    "reviewer_item_id": item_id,
                    "column": "reviewer_confidence",
                    "issue": "invalid_value",
                }
            )
        elif int(confidence) < MIN_REVIEWER_CONFIDENCE:
            blocking.append(
                {
                    "reviewer_item_id": item_id,
                    "dimension": "reviewer_confidence",
                    "value": f"below_{MIN_REVIEWER_CONFIDENCE}",
                }
            )

    form_checks = {
        "no_missing_rows": not missing,
        "no_unexpected_rows": not unexpected,
        "no_malformed_cells": not problems,
    }
    return {
        "schema_version": "cab_stage2_submission_validation_v2",
        "form_schema_version": STAGE2_FORM_SCHEMA_VERSION,
        "acceptance_policy_version": STAGE2_ACCEPTANCE_POLICY_VERSION,
        "row_count": len(rows),
        "missing_rows": missing,
        "unexpected_rows": unexpected,
        "malformed": problems,
        "checks": form_checks,
        # "form_complete" is deliberately NOT called "passed": a complete form is
        # not an approval, and nothing downstream may treat it as one.
        "form_complete": all(form_checks.values()),
        "blocking_values": blocking,
        "blocking_value_count": len(blocking),
        "substantively_accepted_without_adjudication": all(form_checks.values()) and not blocking,
    }


def dimension_accepted(value: str, *, dimension: str, applicable: bool) -> bool:
    """Whether one final value accepts, under the frozen acceptance rule."""

    normalized = normalize_value(value)
    if normalized == YES:
        return dimension not in STAGE2_CONDITIONAL_DIMENSIONS or applicable
    if normalized == NOT_APPLICABLE:
        return dimension in STAGE2_CONDITIONAL_DIMENSIONS and not applicable
    return False


STAGE2_REVIEWER_INSTRUCTIONS = """# CAB Stage-2 reviewer instructions

Stage 2 shows you the material that was withheld in Stage 1: the expected result,
the accepted variants, the answer contract, the scorer contract, the intervention
policy and the route requirement.

You are judging whether that material is *correct and defensible*, not whether it
is present. Use four values:

* `YES` — you accept this dimension.
* `NO` — you object. Say why in `notes`.
* `UNSURE` — you cannot tell. Say what would settle it in `notes`.
* `NOT_APPLICABLE` — only for the three `*_or_not_applicable` dimensions, and
  only when the item genuinely has no recovery route, no abstention opportunity,
  or no clarification requirement. Each item's `applicability.json` tells you
  which of the three exist; contradicting it is an error, not a judgement.

`NO` and `UNSURE` both require notes, and both send the item to an independent
adjudicator. Neither counts against you. Filling every cell does not approve
anything — an item is accepted only when the final adjudicated value for every
dimension accepts.

Set `reviewer_confidence` honestly. Below 3 sends the item to adjudication even
when you answered `YES` everywhere, which is the correct outcome for a judgement
you do not trust.
"""


__all__ = [
    "ACCEPTING_VALUES",
    "BLOCKING_VALUES",
    "CONFIDENCE_VALUES",
    "EXCLUDE_VALUES",
    "MIN_REVIEWER_CONFIDENCE",
    "NO",
    "NOT_APPLICABLE",
    "STAGE2_ACCEPTANCE_POLICY_VERSION",
    "STAGE2_CONDITIONAL_DIMENSIONS",
    "STAGE2_CORE_DIMENSIONS",
    "STAGE2_FORM_COLUMNS",
    "STAGE2_FORM_SCHEMA_VERSION",
    "STAGE2_REVIEWER_INSTRUCTIONS",
    "STAGE2_SUBSTANTIVE_DIMENSIONS",
    "STAGE2_VALUES",
    "UNSURE",
    "YES",
    "Stage2Error",
    "acceptance_policy",
    "applicability_for",
    "dimension_accepted",
    "normalize_value",
    "stage2_form_template",
    "validate_stage2_submission",
]
