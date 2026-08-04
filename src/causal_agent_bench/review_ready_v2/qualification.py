"""Reviewer qualification packet.

Qualification items are purpose-built and share no task, domain, evidence or
identifier with the final twenty pairs.  Each item has one decisive dimension
whose correct value is known; the key stays in the private coordinator area and
is never shipped to a reviewer.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.common import canonical_bytes
from causal_agent_bench.review_ready_v2.stage1 import (
    CONFLICT_DECLARATION,
    FORM_VALIDATION_RULES,
    REVIEW_DIMENSIONS,
    REVIEW_FORM_COLUMNS,
    zip_bytes,
)

QUALIFICATION_SCHEMA_VERSION = "cab_stage1_qualification_v2"
MIN_QUALIFICATION_RATE = 0.80

QUALIFICATION_INSTRUCTIONS = """# CAB Stage-1 qualification

These five items are a calibration exercise, not part of the benchmark. They use
different tasks, different domains and different records from the review set.

Judge them exactly as you will judge the real items and fill one row per item in
`qualification_form.csv`. Each item has one dimension that decides whether the
calibration passes; every dimension is scored, so answer all of them.

You must reach at least 80% agreement with the reference judgement on the
decisive dimensions before you can be assigned a review package. Work alone and
do not use any AI assistant.
"""


def _item(
    item_id: str,
    scenario: str,
    objective: str,
    clean: dict[str, Any],
    intervention: dict[str, Any],
    difference: dict[str, Any],
    invariants: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": QUALIFICATION_SCHEMA_VERSION,
        "reviewer_item_id": item_id,
        "scenario": scenario,
        "task_objective": objective,
        "clean_instance": clean,
        "intervention_instance": intervention,
        "controlled_difference": difference,
        "claimed_preserved_invariants": invariants,
    }


QUALIFICATION_ITEMS: tuple[dict[str, Any], ...] = (
    _item(
        "Q-01",
        "library circulation",
        (
            "A member wants to know the latest date they can return a borrowed title without a "
            "fine. Use the loan record and the lending policy to give the due date."
        ),
        {
            "evidence": {
                "loan_record": {"loan_ref": "LN-4471", "checked_out_on": "2026-03-02"},
                "lending_policy": {"loan_days": 21},
            },
            "declared_tools": [
                {"tool_id": "loan_record_reader", "reads_source": "loan_record"},
                {"tool_id": "lending_policy_reader", "reads_source": "lending_policy"},
            ],
        },
        {
            "evidence": {
                "loan_record": {"loan_ref": "LN-4471", "checked_out_on": "2026-03-02"},
                "lending_policy": {"loan_days": 21},
            },
            "declared_tools": [{"tool_id": "loan_record_reader", "reads_source": "loan_record"}],
        },
        {
            "intervention_family": "tool_removal",
            "intended_changed_factor": "declared_tool_capability_availability",
            "changed_locators": ["$.tools.lending_policy_reader"],
            "author_rationale": "The lending-policy capability is revoked; nothing else changes.",
        },
        ["goal_text_identical", "non_target_sources_identical"],
    ),
    _item(
        "Q-02",
        "gym membership",
        (
            "A member asks how much they owe for this month. Use the membership record and the "
            "rate card to give the amount due."
        ),
        {
            "evidence": {
                "membership_record": {"member_ref": "GM-208", "tier": "standard", "months_due": 2},
                "rate_card": [{"tier": "standard", "monthly_fee": 34}, {"tier": "plus", "monthly_fee": 52}],
            },
            "declared_tools": [
                {"tool_id": "membership_reader", "reads_source": "membership_record"},
                {"tool_id": "rate_card_reader", "reads_source": "rate_card"},
            ],
        },
        {
            "evidence": {
                "membership_record": {"member_ref": "GM-208", "tier": "standard", "months_due": 2},
                "rate_card": [{"tier": "standard", "monthly_fee": 34}, {"tier": "plus", "monthly_fee": 52}],
            },
            "declared_tools": [
                {"tool_id": "membership_reader", "reads_source": "membership_record"},
                {"tool_id": "rate_card_reader", "reads_source": "rate_card"},
            ],
            "goal_override": "Cancel this member's subscription and confirm the cancellation date.",
        },
        {
            "intervention_family": "memory_corruption",
            "intended_changed_factor": "task_critical_memory_field_validity",
            "changed_locators": ["$.memory.billing_cycle"],
            "author_rationale": "A stale billing-cycle memory field is corrupted; the goal is unchanged.",
        },
        ["goal_text_identical", "non_target_sources_identical"],
    ),
    _item(
        "Q-03",
        "parking permits",
        (
            "A resident wants to know whether their permit covers overnight parking on their "
            "street. Use the permit record and the zone rules to answer."
        ),
        {
            "evidence": {
                "permit_record": {"permit_ref": "PK-9013", "zone": "north", "class": "resident"},
                "zone_rules": [
                    {"zone": "north", "overnight_allowed": True},
                    {"zone": "south", "overnight_allowed": False},
                ],
            },
            "declared_tools": [
                {"tool_id": "permit_reader", "reads_source": "permit_record"},
                {"tool_id": "zone_rule_reader", "reads_source": "zone_rules"},
            ],
        },
        {
            "evidence": {
                "permit_record": {"permit_ref": "PK-9013", "zone": "south", "class": "visitor"},
                "zone_rules": [
                    {"zone": "north", "overnight_allowed": True},
                    {"zone": "south", "overnight_allowed": False},
                ],
            },
            "declared_tools": [
                {"tool_id": "permit_reader", "reads_source": "permit_record"},
                {"tool_id": "zone_rule_reader", "reads_source": "zone_rules"},
            ],
        },
        {
            "intervention_family": "observation_conflict",
            "intended_changed_factor": "cross_source_observation_consistency",
            "changed_locators": ["$.sources.permit_record.zone"],
            "author_rationale": "One field of the permit record is changed to conflict with the zone rules.",
        },
        ["goal_text_identical", "non_target_sources_identical"],
    ),
    _item(
        "Q-04",
        "food truck licensing",
        (
            "An operator asks which licence class they need for a weekend market pitch. Use the "
            "pitch record and the licence schedule to answer."
        ),
        {
            "evidence": {
                "pitch_record": {
                    "pitch_ref": "FT-77",
                    "days_per_week": 2,
                    "serves_hot_food": True,
                    "licence_class_to_apply_for": "class-B",
                },
                "licence_schedule": [
                    {"class": "class-A", "max_days_per_week": 1, "hot_food": False},
                    {"class": "class-B", "max_days_per_week": 3, "hot_food": True},
                ],
            },
            "declared_tools": [
                {"tool_id": "pitch_reader", "reads_source": "pitch_record"},
                {"tool_id": "licence_schedule_reader", "reads_source": "licence_schedule"},
            ],
        },
        {
            "evidence": {
                "pitch_record": {
                    "pitch_ref": "FT-77",
                    "days_per_week": 2,
                    "serves_hot_food": True,
                    "licence_class_to_apply_for": "class-B",
                },
                "licence_schedule": [
                    {"class": "class-A", "max_days_per_week": 1, "hot_food": False},
                    {"class": "class-B", "max_days_per_week": 3, "hot_food": True},
                ],
            },
            "declared_tools": [
                {"tool_id": "pitch_reader", "reads_source": "pitch_record"},
                {"tool_id": "licence_schedule_reader", "reads_source": "licence_schedule"},
            ],
            "tools_reported_failing": ["licence_schedule_reader"],
        },
        {
            "intervention_family": "tool_failure",
            "intended_changed_factor": "declared_tool_runtime_success",
            "changed_locators": ["$.injected_failures"],
            "author_rationale": "The licence-schedule capability now fails at runtime.",
        },
        ["goal_text_identical", "non_target_sources_identical"],
    ),
    _item(
        "Q-05",
        "bike share",
        (
            "A rider asks how much their last trip cost. Use the trip record and the fare table "
            "to give the fare."
        ),
        {
            "evidence": {
                "trip_record": {"trip_ref": "BS-5512", "minutes": 27},
                "fare_table": [{"band": "0-30", "fare": 3}, {"band": "31-60", "fare": 5}],
            },
            "declared_tools": [{"tool_id": "trip_reader", "reads_source": "trip_record"}],
        },
        {
            "evidence": {
                "trip_record": {"trip_ref": "BS-5512", "minutes": 27},
                "fare_table": [{"band": "0-30", "fare": 3}, {"band": "31-60", "fare": 5}],
            },
            "declared_tools": [{"tool_id": "trip_reader", "reads_source": "trip_record"}],
            "tools_reported_failing": ["trip_reader"],
        },
        {
            "intervention_family": "tool_failure",
            "intended_changed_factor": "declared_tool_runtime_success",
            "changed_locators": ["$.injected_failures"],
            "author_rationale": "The trip-record capability now fails at runtime.",
        },
        ["goal_text_identical", "non_target_sources_identical"],
    ),
)

QUALIFICATION_KEY: dict[str, dict[str, str]] = {
    "Q-01": {
        "decisive_dimension": "single_factor_isolation",
        "expected_value": "yes",
        "why": "Exactly one declared capability is revoked and nothing else differs.",
    },
    "Q-02": {
        "decisive_dimension": "goal_preserved",
        "expected_value": "no",
        "why": "The intervention instance replaces the user's goal with a different task.",
    },
    "Q-03": {
        "decisive_dimension": "single_factor_isolation",
        "expected_value": "no",
        "why": "Two fields of the permit record change, not one.",
    },
    "Q-04": {
        "decisive_dimension": "primitive_evidence_adequate",
        "expected_value": "no",
        "why": "The pitch record carries a pre-computed licence class, which is the answer itself.",
    },
    "Q-05": {
        "decisive_dimension": "clean_evidence_sufficient",
        "expected_value": "no",
        "why": "No declared capability exposes the fare table, so even the clean instance is unsolvable.",
    },
}


def _qualification_form(item_ids: list[str]) -> bytes:
    header = ",".join(REVIEW_FORM_COLUMNS)
    rows = [header]
    rows.extend(item_id + "," * (len(REVIEW_FORM_COLUMNS) - 1) for item_id in item_ids)
    return ("\n".join(rows) + "\n").encode()


def build_qualification_package() -> bytes:
    files: dict[str, bytes] = {}
    item_ids: list[str] = []
    for item in QUALIFICATION_ITEMS:
        item_id = str(item["reviewer_item_id"])
        item_ids.append(item_id)
        files[f"items/{item_id}.json"] = canonical_bytes(item) + b"\n"
    files["manifest.json"] = (
        canonical_bytes(
            {
                "schema_version": QUALIFICATION_SCHEMA_VERSION,
                "item_count": len(item_ids),
                "items": [
                    {"reviewer_item_id": item_id, "item_path": f"items/{item_id}.json"}
                    for item_id in item_ids
                ],
                "form": "qualification_form.csv",
                "pass_threshold": MIN_QUALIFICATION_RATE,
                "reference_solutions_included": False,
                "reuses_review_set_tasks": False,
            }
        )
        + b"\n"
    )
    files["qualification_form.csv"] = _qualification_form(item_ids)
    files["QUALIFICATION_INSTRUCTIONS.md"] = QUALIFICATION_INSTRUCTIONS.encode()
    files["CONFLICT_OF_INTEREST.md"] = CONFLICT_DECLARATION.encode()
    files["review_form.schema.json"] = (
        canonical_bytes(
            {
                "columns": [
                    {"name": name, "allowed_values": list(values) if values else "free_text"}
                    for name, values, _ in REVIEW_DIMENSIONS
                ],
                "validation_rules": list(FORM_VALIDATION_RULES),
            }
        )
        + b"\n"
    )
    return zip_bytes(files)


def score_qualification(submission: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Score a genuine qualification submission against the private key."""

    graded: list[dict[str, Any]] = []
    for item_id, expected in sorted(QUALIFICATION_KEY.items()):
        dimension = expected["decisive_dimension"]
        given = str(submission.get(item_id, {}).get(dimension, "")).strip().casefold()
        graded.append(
            {
                "reviewer_item_id": item_id,
                "decisive_dimension": dimension,
                "correct": given == expected["expected_value"],
            }
        )
    correct = sum(row["correct"] for row in graded)
    rate = correct / len(graded) if graded else 0.0
    return {
        "schema_version": "cab_qualification_result_v2",
        "item_count": len(graded),
        "correct_count": correct,
        "rate": round(rate, 4),
        "threshold": MIN_QUALIFICATION_RATE,
        "graded": graded,
        "qualified": rate >= MIN_QUALIFICATION_RATE,
    }


__all__ = [
    "MIN_QUALIFICATION_RATE",
    "QUALIFICATION_ITEMS",
    "QUALIFICATION_KEY",
    "QUALIFICATION_SCHEMA_VERSION",
    "build_qualification_package",
    "score_qualification",
]
