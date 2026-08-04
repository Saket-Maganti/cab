"""One final adjudicated record per pair — the only thing C10 is allowed to read.

Agreement statistics and eligibility decisions answer different questions and
must not share an input.  Agreement is a property of what two reviewers
independently wrote, so it is computed from the raw submissions and never
improves when an adjudicator resolves a dispute.  Eligibility is a property of
the *settled* judgement, so it is computed here, from adjudicated values.

Every dimension in a final record carries its provenance: ``agreed_by_reviewers``,
``resolved_by_adjudicator``, or ``excluded``.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.adjudication import (
    STAGE1,
    STAGE1_ACCEPTING_VALUES,
    STAGE1_GATING_DIMENSIONS,
    STAGE2,
)
from causal_agent_bench.review_ready_v2.stage2 import (
    STAGE2_SUBSTANTIVE_DIMENSIONS,
    dimension_accepted,
    normalize_value,
)

FINAL_RECORD_SCHEMA = "cab_final_adjudicated_item_record_v1"

AGREED = "agreed_by_reviewers"
RESOLVED = "resolved_by_adjudicator"
EXCLUDED = "excluded"


class FinalRecordError(ValueError):
    """A final adjudicated record could not be built."""


def _decisions_by_key(adjudication: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not adjudication:
        return {}
    return {
        f"{row['pair_id']}::{row['dimension']}": row for row in adjudication.get("decisions", [])
    }


def _stage1_accepts(dimension: str, value: str) -> bool:
    accepting = STAGE1_ACCEPTING_VALUES.get(dimension)
    if accepting is None:
        return True
    return str(value).strip().casefold() in accepting


def _resolve(
    *,
    stage: str,
    pair_id: str,
    dimension: str,
    reviewer_values: dict[str, str],
    decisions: dict[str, dict[str, Any]],
    applicable: bool,
) -> dict[str, Any]:
    decision = decisions.get(f"{pair_id}::{dimension}")
    if decision is not None:
        final_value = str(decision["final_value"]).strip()
        excluded = normalize_value(decision["exclude_item"]) == "YES"
        accepted = (
            _stage1_accepts(dimension, final_value)
            if stage == STAGE1
            else dimension_accepted(final_value, dimension=dimension, applicable=applicable)
        )
        return {
            "final_value": final_value,
            "provenance": EXCLUDED if excluded else RESOLVED,
            "accepted": bool(accepted and not excluded),
            "excluded": excluded,
            "reviewer_values": dict(reviewer_values),
            "adjudicator_rationale_present": bool(str(decision.get("rationale", "")).strip()),
        }

    values = {
        role: (value.strip().casefold() if stage == STAGE1 else normalize_value(value))
        for role, value in reviewer_values.items()
    }
    distinct = set(values.values())
    if len(distinct) != 1:
        raise FinalRecordError(
            f"{stage} dimension {dimension!r} on {pair_id} is disputed but not adjudicated"
        )
    settled = next(iter(distinct))
    accepted = (
        _stage1_accepts(dimension, settled)
        if stage == STAGE1
        else dimension_accepted(settled, dimension=dimension, applicable=applicable)
    )
    if not accepted:
        raise FinalRecordError(
            f"{stage} dimension {dimension!r} on {pair_id} does not accept and was not adjudicated"
        )
    return {
        "final_value": settled,
        "provenance": AGREED,
        "accepted": True,
        "excluded": False,
        "reviewer_values": dict(reviewer_values),
        "adjudicator_rationale_present": False,
    }


def build_final_records(
    *,
    stage1_paired: dict[str, dict[str, dict[str, str]]],
    stage2_paired: dict[str, dict[str, dict[str, str]]],
    stage1_adjudication: dict[str, Any] | None,
    stage2_adjudication: dict[str, Any] | None,
    applicability: dict[str, dict[str, bool]],
    expected_pair_count: int,
) -> dict[str, Any]:
    """Combine both stages and both adjudications into one record per pair."""

    stage1_decisions = _decisions_by_key(stage1_adjudication)
    stage2_decisions = _decisions_by_key(stage2_adjudication)

    records: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    for pair_id in sorted(stage1_paired):
        stage1_rows = stage1_paired[pair_id]
        stage2_rows = stage2_paired.get(pair_id, {})
        pair_applicability = applicability.get(pair_id, {})

        stage1_final: dict[str, Any] = {}
        for dimension in STAGE1_GATING_DIMENSIONS:
            values = {role: str(row.get(dimension, "")) for role, row in stage1_rows.items()}
            try:
                stage1_final[dimension] = _resolve(
                    stage=STAGE1,
                    pair_id=pair_id,
                    dimension=dimension,
                    reviewer_values=values,
                    decisions=stage1_decisions,
                    applicable=True,
                )
            except FinalRecordError as error:
                unresolved.append({"pair_id": pair_id, "stage": STAGE1, "detail": str(error)})
                stage1_final[dimension] = {
                    "final_value": None,
                    "provenance": None,
                    "accepted": False,
                    "excluded": False,
                    "reviewer_values": values,
                    "adjudicator_rationale_present": False,
                }

        stage2_final: dict[str, Any] = {}
        stage2_complete = len(stage2_rows) == 2
        if stage2_complete:
            for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS:
                values = {role: str(row.get(dimension, "")) for role, row in stage2_rows.items()}
                try:
                    stage2_final[dimension] = _resolve(
                        stage=STAGE2,
                        pair_id=pair_id,
                        dimension=dimension,
                        reviewer_values=values,
                        decisions=stage2_decisions,
                        applicable=bool(pair_applicability.get(dimension, True)),
                    )
                except FinalRecordError as error:
                    unresolved.append({"pair_id": pair_id, "stage": STAGE2, "detail": str(error)})
                    stage2_final[dimension] = {
                        "final_value": None,
                        "provenance": None,
                        "accepted": False,
                        "excluded": False,
                        "reviewer_values": values,
                        "adjudicator_rationale_present": False,
                    }

        excluded_here = [
            dimension
            for stage_final in (stage1_final, stage2_final)
            for dimension, row in stage_final.items()
            if row.get("excluded")
        ]
        blocked_here = [
            f"{stage}:{dimension}"
            for stage, stage_final in ((STAGE1, stage1_final), (STAGE2, stage2_final))
            for dimension, row in stage_final.items()
            if not row.get("accepted") and not row.get("excluded")
        ]
        excluded = bool(excluded_here) or bool(blocked_here) or not stage2_complete
        reasons: list[str] = []
        if excluded_here:
            reasons.append("adjudicator_excluded")
        if blocked_here:
            reasons.append("unresolved_objection")
        if not stage2_complete:
            reasons.append("stage2_incomplete")

        records.append(
            {
                "schema_version": FINAL_RECORD_SCHEMA,
                "pair_id": pair_id,
                "stage1": stage1_final,
                "stage2": stage2_final,
                "stage2_complete": stage2_complete,
                "included": not excluded,
                "excluded": excluded,
                "exclusion_reasons": sorted(set(reasons)),
                "blocked_dimensions": sorted(blocked_here),
            }
        )

    included = [row["pair_id"] for row in records if row["included"]]
    excluded_pairs = [
        {"pair_id": row["pair_id"], "reasons": row["exclusion_reasons"]}
        for row in records
        if row["excluded"]
    ]
    provenance_counts: dict[str, int] = {AGREED: 0, RESOLVED: 0, EXCLUDED: 0}
    for record in records:
        for stage_final in (record["stage1"], record["stage2"]):
            for row in stage_final.values():
                provenance = row.get("provenance")
                if provenance in provenance_counts:
                    provenance_counts[provenance] += 1

    checks = {
        "every_expected_pair_has_a_final_record": len(records) == expected_pair_count,
        "every_pair_has_two_stage1_judgements": all(
            len(rows) == 2 for rows in stage1_paired.values()
        ),
        "every_pair_has_two_stage2_judgements": bool(stage2_paired)
        and all(len(rows) == 2 for rows in stage2_paired.values())
        and set(stage2_paired) == set(stage1_paired),
        "no_unresolved_dimensions": not unresolved,
        "at_least_one_included_pair": bool(included),
    }
    return {
        "schema_version": "cab_final_adjudicated_records_v1",
        "record_count": len(records),
        "expected_pair_count": expected_pair_count,
        "included_pair_ids": included,
        "included_count": len(included),
        "excluded_pairs": excluded_pairs,
        "excluded_count": len(excluded_pairs),
        "unresolved": unresolved,
        "provenance_counts": provenance_counts,
        "records": records,
        "checks": checks,
        "passed": all(checks.values()),
    }


def dimension_is_accepted_everywhere(final: dict[str, Any], stage: str, dimension: str) -> bool:
    """True when every *included* pair accepts ``dimension`` in ``stage``."""

    included = [row for row in final["records"] if row["included"]]
    if not included:
        return False
    return all(row[stage].get(dimension, {}).get("accepted") is True for row in included)


__all__ = [
    "AGREED",
    "EXCLUDED",
    "FINAL_RECORD_SCHEMA",
    "RESOLVED",
    "FinalRecordError",
    "build_final_records",
    "dimension_is_accepted_everywhere",
]
