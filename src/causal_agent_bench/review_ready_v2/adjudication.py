"""Separate Stage-1 and Stage-2 disagreement queues, and their adjudication.

Stage 1 and Stage 2 dispute different things, so they get different queues.  A
Stage-1 dispute is about whether the *pair* is a valid controlled comparison; a
Stage-2 dispute is about whether the withheld gold, contracts and policies are
correct.  Mixing them would let a resolved Stage-1 disagreement stand in for an
unexamined Stage-2 objection, which is exactly the defect this module closes.

An adjudicator has two ways to resolve a disputed dimension and no third: give a
final value that accepts under the frozen rule, or exclude the item.  There is no
path on which an unresolved ``NO`` or ``UNSURE`` survives into C10.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.stage2 import (
    NOT_APPLICABLE,
    STAGE2_CONDITIONAL_DIMENSIONS,
    STAGE2_SUBSTANTIVE_DIMENSIONS,
    STAGE2_VALUES,
    dimension_accepted,
    normalize_value,
)

STAGE1 = "stage1"
STAGE2 = "stage2"

STAGE1_QUEUE_SCHEMA = "cab_stage1_disagreement_queue_v1"
STAGE2_QUEUE_SCHEMA = "cab_stage2_disagreement_queue_v1"
ADJUDICATION_SCHEMA = "cab_adjudication_v2"

#: Stage-1 dimensions whose disagreement blocks the pair.
STAGE1_GATING_DIMENSIONS: tuple[str, ...] = (
    "clean_solvable",
    "clean_evidence_sufficient",
    "goal_preserved",
    "single_factor_isolation",
    "preserved_invariants_hold",
    "primitive_evidence_adequate",
    "response_space_structurally_valid",
    "exclude_item",
)

#: The Stage-1 values that accept.  Anything else needs adjudication.
STAGE1_ACCEPTING_VALUES: dict[str, frozenset[str]] = {
    "clean_solvable": frozenset({"yes"}),
    "clean_evidence_sufficient": frozenset({"yes"}),
    "goal_preserved": frozenset({"yes"}),
    "single_factor_isolation": frozenset({"yes"}),
    "preserved_invariants_hold": frozenset({"yes", "partial"}),
    "primitive_evidence_adequate": frozenset({"yes"}),
    "response_space_structurally_valid": frozenset({"yes"}),
    "exclude_item": frozenset({"no"}),
}

MIN_STAGE1_CONFIDENCE = 3

REQUIRED_DECISION_FIELDS: tuple[str, ...] = (
    "pair_id",
    "dimension",
    "final_value",
    "rationale",
    "evidence_reference",
    "confidence",
    "exclude_item",
)


class AdjudicationError(ValueError):
    """A disagreement queue or an adjudication submission refused."""


def _key(pair_id: str, dimension: str) -> str:
    return f"{pair_id}::{dimension}"


# --------------------------------------------------------------------------
# Stage-1 queue
# --------------------------------------------------------------------------


def build_stage1_queue(paired: dict[str, dict[str, dict[str, str]]]) -> dict[str, Any]:
    """Every Stage-1 dimension that two reviewers did not jointly accept."""

    disputes: list[dict[str, Any]] = []
    for pair_id, rows in sorted(paired.items()):
        if len(rows) != 2:
            raise AdjudicationError(f"pair {pair_id} lacks two independent Stage-1 judgements")
        roles = sorted(rows)
        for dimension in STAGE1_GATING_DIMENSIONS:
            values = {role: str(rows[role].get(dimension, "")).strip().casefold() for role in roles}
            accepting = STAGE1_ACCEPTING_VALUES[dimension]
            reasons: list[str] = []
            if len(set(values.values())) > 1:
                reasons.append("reviewer_disagreement")
            if any(value not in accepting for value in values.values()):
                reasons.append("non_accepting_value")
            if reasons:
                disputes.append(
                    {
                        "stage": STAGE1,
                        "pair_id": pair_id,
                        "dimension": dimension,
                        "reasons": sorted(set(reasons)),
                        "reviewer_values": values,
                    }
                )
        for dimension, blocking in (
            ("ambiguity_present", {"material"}),
            ("response_space_structurally_valid", {"unsure"}),
        ):
            values = {role: str(rows[role].get(dimension, "")).strip().casefold() for role in roles}
            if any(value in blocking for value in values.values()):
                disputes.append(
                    {
                        "stage": STAGE1,
                        "pair_id": pair_id,
                        "dimension": dimension,
                        "reasons": ["substantive_reviewer_concern"],
                        "reviewer_values": values,
                    }
                )
        confidences = {
            role: str(rows[role].get("reviewer_confidence", "")).strip() for role in roles
        }
        if any(
            value.isdigit() and int(value) < MIN_STAGE1_CONFIDENCE for value in confidences.values()
        ):
            disputes.append(
                {
                    "stage": STAGE1,
                    "pair_id": pair_id,
                    "dimension": "reviewer_confidence",
                    "reasons": ["confidence_below_threshold"],
                    "reviewer_values": confidences,
                }
            )
    deduped = {_key(str(row["pair_id"]), str(row["dimension"])): row for row in disputes}
    return {
        "schema_version": STAGE1_QUEUE_SCHEMA,
        "stage": STAGE1,
        "pair_count": len(paired),
        "disputed_pair_count": len({str(row["pair_id"]) for row in deduped.values()}),
        "disputed_dimension_count": len(deduped),
        "disputes": [deduped[key] for key in sorted(deduped)],
    }


# --------------------------------------------------------------------------
# Stage-2 queue
# --------------------------------------------------------------------------


def build_stage2_queue(
    paired: dict[str, dict[str, dict[str, str]]],
    applicability: dict[str, dict[str, bool]],
) -> dict[str, Any]:
    """Every Stage-2 dimension that two reviewers did not jointly accept."""

    disputes: list[dict[str, Any]] = []
    for pair_id, rows in sorted(paired.items()):
        if len(rows) != 2:
            raise AdjudicationError(f"pair {pair_id} lacks two independent Stage-2 judgements")
        roles = sorted(rows)
        pair_applicability = applicability.get(pair_id, {})
        for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS:
            applicable = bool(pair_applicability.get(dimension, True))
            values = {role: normalize_value(rows[role].get(dimension, "")) for role in roles}
            reasons: list[str] = []
            if len(set(values.values())) > 1:
                reasons.append("reviewer_disagreement")
            for value in values.values():
                if value == "NO":
                    reasons.append("substantive_objection")
                elif value == "UNSURE":
                    reasons.append("unresolved_uncertainty")
                elif value not in STAGE2_VALUES:
                    reasons.append("invalid_value")
                elif value == NOT_APPLICABLE and (
                    dimension not in STAGE2_CONDITIONAL_DIMENSIONS or applicable
                ):
                    reasons.append("invalid_not_applicable")
            if any(
                value == NOT_APPLICABLE for value in values.values()
            ) and not all(value == NOT_APPLICABLE for value in values.values()):
                reasons.append("applicability_policy_mismatch")
            if reasons:
                disputes.append(
                    {
                        "stage": STAGE2,
                        "pair_id": pair_id,
                        "dimension": dimension,
                        "applicable": applicable,
                        "reasons": sorted(set(reasons)),
                        "reviewer_values": values,
                    }
                )
        confidences = {
            role: str(rows[role].get("reviewer_confidence", "")).strip() for role in roles
        }
        if any(value.isdigit() and int(value) < 3 for value in confidences.values()):
            disputes.append(
                {
                    "stage": STAGE2,
                    "pair_id": pair_id,
                    "dimension": "reviewer_confidence",
                    "applicable": True,
                    "reasons": ["confidence_below_threshold"],
                    "reviewer_values": confidences,
                }
            )
        excludes = {role: normalize_value(rows[role].get("exclude_item", "")) for role in roles}
        if len(set(excludes.values())) > 1 or "YES" in set(excludes.values()):
            disputes.append(
                {
                    "stage": STAGE2,
                    "pair_id": pair_id,
                    "dimension": "exclude_item",
                    "applicable": True,
                    "reasons": ["exclusion_requested_or_disputed"],
                    "reviewer_values": excludes,
                }
            )
        notes = {role: str(rows[role].get("notes", "")).strip() for role in roles}
        objected = {
            role
            for role in roles
            if any(
                normalize_value(rows[role].get(dimension, "")) in {"NO", "UNSURE"}
                for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS
            )
        }
        noted = {role for role in roles if notes[role]}
        if noted - objected and not (objected or len(noted) == 2):
            disputes.append(
                {
                    "stage": STAGE2,
                    "pair_id": pair_id,
                    "dimension": "notes",
                    "applicable": True,
                    "reasons": ["unmatched_substantive_note"],
                    "reviewer_values": {role: bool(notes[role]) for role in roles},
                }
            )
    deduped = {_key(str(row["pair_id"]), str(row["dimension"])): row for row in disputes}
    return {
        "schema_version": STAGE2_QUEUE_SCHEMA,
        "stage": STAGE2,
        "pair_count": len(paired),
        "disputed_pair_count": len({str(row["pair_id"]) for row in deduped.values()}),
        "disputed_dimension_count": len(deduped),
        "disputes": [deduped[key] for key in sorted(deduped)],
    }


# --------------------------------------------------------------------------
# adjudication
# --------------------------------------------------------------------------


def _final_value_accepts(stage: str, dimension: str, value: str, *, applicable: bool) -> bool:
    if stage == STAGE1:
        accepting = STAGE1_ACCEPTING_VALUES.get(dimension)
        if accepting is None:
            # Non-gating Stage-1 concerns (ambiguity, confidence) are resolved by
            # the adjudicator recording any value plus a rationale.
            return bool(str(value).strip())
        return str(value).strip().casefold() in accepting
    if dimension in ("reviewer_confidence", "notes"):
        return bool(str(value).strip())
    if dimension == "exclude_item":
        return normalize_value(value) == "NO"
    return dimension_accepted(value, dimension=dimension, applicable=applicable)


def validate_adjudication(
    *,
    stage: str,
    queue: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check that the adjudicator decided exactly the disputes, and resolved them."""

    if stage not in (STAGE1, STAGE2):
        raise AdjudicationError(f"unknown adjudication stage {stage!r}")
    if queue.get("stage") != stage:
        raise AdjudicationError(
            f"the {stage} adjudication was offered a {queue.get('stage')!r} disagreement queue"
        )

    disputed = {
        _key(str(row["pair_id"]), str(row["dimension"])): row for row in queue.get("disputes", [])
    }
    decided: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        missing = sorted(field for field in REQUIRED_DECISION_FIELDS if field not in decision)
        if missing:
            raise AdjudicationError(f"an adjudication decision is missing fields: {missing}")
        key = _key(str(decision["pair_id"]), str(decision["dimension"]))
        if key in decided:
            raise AdjudicationError(f"duplicate adjudication decision for {key}")
        if not str(decision["rationale"]).strip():
            raise AdjudicationError(f"the adjudication for {key} lacks a rationale")
        if not str(decision["evidence_reference"]).strip():
            raise AdjudicationError(f"the adjudication for {key} lacks an evidence reference")
        confidence = str(decision["confidence"]).strip()
        if confidence not in {"1", "2", "3", "4", "5"}:
            raise AdjudicationError(f"the adjudication for {key} lacks a 1-5 confidence")
        decided[key] = decision

    undecided = sorted(set(disputed) - set(decided))
    extraneous = sorted(set(decided) - set(disputed))
    if undecided:
        raise AdjudicationError(
            f"{len(undecided)} disputed {stage} dimension(s) were left undecided"
        )
    if extraneous:
        raise AdjudicationError(
            f"{len(extraneous)} adjudication decision(s) do not correspond to a {stage} dispute"
        )

    resolved: list[dict[str, Any]] = []
    for key in sorted(decided):
        decision = decided[key]
        dispute = disputed[key]
        dimension = str(decision["dimension"])
        excluded = normalize_value(decision["exclude_item"]) == "YES"
        accepts = _final_value_accepts(
            stage,
            dimension,
            str(decision["final_value"]),
            applicable=bool(dispute.get("applicable", True)),
        )
        if not accepts and not excluded:
            raise AdjudicationError(
                f"the adjudication for {key} neither resolves the dimension to an accepting value "
                f"({decision['final_value']!r}) nor excludes the item; an unresolved objection "
                "cannot proceed"
            )
        resolved.append(
            {
                "stage": stage,
                "pair_id": str(decision["pair_id"]),
                "dimension": dimension,
                "final_value": str(decision["final_value"]).strip(),
                "rationale": str(decision["rationale"]).strip(),
                "evidence_reference": str(decision["evidence_reference"]).strip(),
                "confidence": str(decision["confidence"]).strip(),
                "exclude_item": "YES" if excluded else "NO",
                "resolves_to_accepting_value": accepts,
                "dispute_reasons": list(dispute.get("reasons", [])),
                "reviewer_values": dispute.get("reviewer_values", {}),
            }
        )
    return {
        "schema_version": ADJUDICATION_SCHEMA,
        "stage": stage,
        "queue_schema_version": queue.get("schema_version"),
        "disputed_dimension_count": len(disputed),
        "decision_count": len(resolved),
        "excluded_pair_ids": sorted(
            {row["pair_id"] for row in resolved if row["exclude_item"] == "YES"}
        ),
        "decisions": resolved,
        "all_disputes_resolved": True,
    }


def adjudication_package(queue: dict[str, Any]) -> dict[str, Any]:
    """The adjudicator's package: disputed items only, and nothing else."""

    return {
        "schema_version": f"cab_{queue['stage']}_adjudication_package_v1",
        "stage": queue["stage"],
        "acceptance_rule": (
            "For each disputed dimension give a final value that accepts under the frozen rule, "
            "or set exclude_item=YES. There is no third option: an unresolved objection cannot "
            "enter the benchmark."
        ),
        "required_fields": list(REQUIRED_DECISION_FIELDS),
        "disputed_dimension_count": queue["disputed_dimension_count"],
        "disputes": [
            {
                "pair_id": row["pair_id"],
                "dimension": row["dimension"],
                "applicable": row.get("applicable", True),
                "reasons": row["reasons"],
                "reviewer_values": row["reviewer_values"],
            }
            for row in queue["disputes"]
        ],
    }


__all__ = [
    "ADJUDICATION_SCHEMA",
    "MIN_STAGE1_CONFIDENCE",
    "REQUIRED_DECISION_FIELDS",
    "STAGE1",
    "STAGE1_ACCEPTING_VALUES",
    "STAGE1_GATING_DIMENSIONS",
    "STAGE1_QUEUE_SCHEMA",
    "STAGE2",
    "STAGE2_QUEUE_SCHEMA",
    "AdjudicationError",
    "adjudication_package",
    "build_stage1_queue",
    "build_stage2_queue",
    "validate_adjudication",
]
