"""Local-first human review contracts, assignment, agreement, and C10 gating."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.level5.core import content_hash, utc_now


class ReviewerRole(StrEnum):
    REVIEWER = "REVIEWER"
    ADJUDICATOR = "ADJUDICATOR"


class Reviewer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_id: str
    role: ReviewerRole
    qualified: bool
    consented: bool
    human_attestation: bool
    proxy_or_ai_assistance: bool = False
    conflicts: list[str] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    compensation_disclosed: bool = False

    @model_validator(mode="after")
    def validate_human(self) -> Reviewer:
        if not self.human_attestation or self.proxy_or_ai_assistance:
            raise ValueError("review evidence requires direct human attestation without AI/proxy")
        if not self.consented:
            raise ValueError("reviewer consent is required")
        return self


class Assignment(BaseModel):
    assignment_id: str
    item_id: str
    reviewer_id: str
    role: ReviewerRole
    assignment_order: int
    receipt_hash: str


class Judgment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    judgment_id: str
    assignment_id: str
    item_id: str
    reviewer_id: str
    valid: bool
    manipulation_passed: bool
    invariant: bool
    solvable: bool
    confidence: float = Field(ge=0, le=1)
    time_seconds: float = Field(gt=0)
    notes: str = ""
    submitted_at: str
    evidence_scope: str = Field(pattern=r"^(GENUINE_HUMAN|FIXTURE_ONLY)$")
    supersedes: str | None = None


class Adjudication(BaseModel):
    adjudication_id: str
    item_id: str
    adjudicator_id: str
    decision: bool
    rationale: str = Field(min_length=1)
    submitted_at: str
    evidence_scope: str = Field(pattern=r"^(GENUINE_HUMAN|FIXTURE_ONLY)$")


def assign_reviews(
    items: list[str],
    reviewers: list[Reviewer],
    *,
    reviews_per_item: int = 2,
) -> list[Assignment]:
    eligible = sorted(
        [
            reviewer
            for reviewer in reviewers
            if reviewer.role is ReviewerRole.REVIEWER and reviewer.qualified
        ],
        key=lambda reviewer: reviewer.reviewer_id,
    )
    if len(eligible) < reviews_per_item:
        raise ValueError("insufficient independent qualified reviewers")
    workload: Counter[str] = Counter()
    assignments: list[Assignment] = []
    for item in sorted(items, key=lambda value: content_hash(value)):
        available = [reviewer for reviewer in eligible if item not in reviewer.conflicts]
        available.sort(key=lambda reviewer: (workload[reviewer.reviewer_id], reviewer.reviewer_id))
        selected = available[:reviews_per_item]
        if len(selected) < reviews_per_item:
            raise ValueError(f"insufficient conflict-free coverage for {item}")
        for order, reviewer in enumerate(selected):
            payload = {
                "item_id": item,
                "reviewer_id": reviewer.reviewer_id,
                "order": order,
            }
            receipt = content_hash(payload)
            assignments.append(
                Assignment(
                    assignment_id=f"assignment.{receipt[:24]}",
                    item_id=item,
                    reviewer_id=reviewer.reviewer_id,
                    role=reviewer.role,
                    assignment_order=order,
                    receipt_hash=receipt,
                )
            )
            workload[reviewer.reviewer_id] += 1
    return assignments


class ReviewStore:
    """In-memory immutable submission ledger used by the local service and tests."""

    def __init__(self) -> None:
        self._judgments: dict[str, Judgment] = {}
        self._amendments: list[dict[str, Any]] = []

    def submit(self, judgment: Judgment) -> Judgment:
        if judgment.judgment_id in self._judgments:
            existing = self._judgments[judgment.judgment_id]
            if existing != judgment:
                raise ValueError("submitted judgments are immutable")
            return existing
        self._judgments[judgment.judgment_id] = judgment
        return judgment

    def amend(self, original_id: str, replacement: Judgment, *, reason: str) -> Judgment:
        if original_id not in self._judgments:
            raise KeyError(original_id)
        if replacement.supersedes != original_id:
            raise ValueError("amendment must name the superseded judgment")
        self.submit(replacement)
        self._amendments.append(
            {
                "original_id": original_id,
                "replacement_id": replacement.judgment_id,
                "reason": reason,
                "created_at": utc_now(),
            }
        )
        return replacement

    @property
    def judgments(self) -> list[Judgment]:
        superseded = {row["original_id"] for row in self._amendments}
        return [
            judgment
            for judgment_id, judgment in self._judgments.items()
            if judgment_id not in superseded
        ]

    @property
    def amendments(self) -> list[dict[str, Any]]:
        return list(self._amendments)


def _wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def agreement_report(judgments: list[Judgment]) -> dict[str, Any]:
    by_item: dict[str, list[Judgment]] = defaultdict(list)
    for judgment in judgments:
        by_item[judgment.item_id].append(judgment)
    paired = [rows[:2] for rows in by_item.values() if len(rows) >= 2]
    agreements = sum(rows[0].valid == rows[1].valid for rows in paired)
    total = len(paired)
    raw = agreements / total if total else 0.0
    labels_a = [rows[0].valid for rows in paired]
    labels_b = [rows[1].valid for rows in paired]
    p_yes_a = sum(labels_a) / total if total else 0.0
    p_yes_b = sum(labels_b) / total if total else 0.0
    expected = p_yes_a * p_yes_b + (1 - p_yes_a) * (1 - p_yes_b)
    kappa = (raw - expected) / (1 - expected) if total and expected < 1 else 0.0
    observed_disagreement = 1 - raw
    all_labels = labels_a + labels_b
    prevalence = sum(all_labels) / len(all_labels) if all_labels else 0.0
    expected_disagreement = 2 * prevalence * (1 - prevalence)
    alpha = (
        1 - observed_disagreement / expected_disagreement
        if expected_disagreement
        else 0.0
    )
    interval = _wilson(agreements, total)
    times = [judgment.time_seconds for judgment in judgments]
    median_time = sorted(times)[len(times) // 2] if times else 0.0
    return {
        "paired_items": total,
        "raw_agreement": raw,
        "wilson_95": list(interval),
        "cohen_kappa": kappa,
        "krippendorff_alpha_nominal": alpha,
        "positive_prevalence": prevalence,
        "median_time_seconds": median_time,
        "time_anomaly_count": sum(
            value < max(1.0, median_time * 0.1) for value in times
        ),
        "straight_line_reviewers": sorted(
            reviewer_id
            for reviewer_id, rows in _by_reviewer(judgments).items()
            if len(rows) >= 5 and len({row.valid for row in rows}) == 1
        ),
    }


def _by_reviewer(judgments: list[Judgment]) -> dict[str, list[Judgment]]:
    grouped: dict[str, list[Judgment]] = defaultdict(list)
    for judgment in judgments:
        grouped[judgment.reviewer_id].append(judgment)
    return grouped


def evaluate_c10(
    item_ids: list[str],
    judgments: list[Judgment],
    adjudications: list[Adjudication],
) -> dict[str, Any]:
    """Fail-closed C10 readiness; fixtures can never pass."""

    blockers: list[str] = []
    if not judgments:
        blockers.append("no genuine human judgments")
    if any(row.evidence_scope != "GENUINE_HUMAN" for row in judgments):
        blockers.append("fixture or non-genuine judgment present")
    if any(row.evidence_scope != "GENUINE_HUMAN" for row in adjudications):
        blockers.append("fixture or non-genuine adjudication present")
    by_item: dict[str, list[Judgment]] = defaultdict(list)
    for judgment in judgments:
        by_item[judgment.item_id].append(judgment)
    for item_id in item_ids:
        reviewers = {row.reviewer_id for row in by_item[item_id]}
        if len(reviewers) < 2:
            blockers.append(f"{item_id}: fewer than two independent judgments")
            continue
        decisions = {row.valid for row in by_item[item_id]}
        if len(decisions) > 1 and not any(row.item_id == item_id for row in adjudications):
            blockers.append(f"{item_id}: unresolved adjudication")
        for row in by_item[item_id]:
            if not (row.manipulation_passed and row.invariant and row.solvable):
                blockers.append(f"{item_id}: validity contract failed")
                break
    passed = not blockers
    return {
        "passed": passed,
        "state": "C10_PASSED" if passed else "HUMAN_VALIDATION_REQUIRED",
        "blockers": sorted(set(blockers)),
        "item_count": len(item_ids),
        "judgment_count": len(judgments),
        "adjudication_count": len(adjudications),
        "certificate_hash": (
            content_hash(
                {
                    "items": sorted(item_ids),
                    "judgments": [
                        judgment.model_dump(mode="json") for judgment in judgments
                    ],
                    "adjudications": [
                        row.model_dump(mode="json") for row in adjudications
                    ],
                }
            )
            if passed
            else None
        ),
    }


__all__ = [
    "Adjudication",
    "Assignment",
    "Judgment",
    "ReviewStore",
    "Reviewer",
    "ReviewerRole",
    "agreement_report",
    "assign_reviews",
    "evaluate_c10",
]
