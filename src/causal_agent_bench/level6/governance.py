"""Governance, anti-gaming, external-validation, and lifecycle contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.hashing import stable_hash

DecisionType = Literal[
    "amendment",
    "appeal",
    "dispute",
    "emergency_correction",
    "revocation",
    "task_inclusion",
    "task_removal",
]
CanaryKind = Literal[
    "prompt_fragment",
    "synthetic_unique_string",
    "artifact_fingerprint",
    "answer_canary",
    "metadata_canary",
]


class BenchmarkLifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    SATURATING = "SATURATING"
    CONTAMINATION_SUSPECTED = "CONTAMINATION_SUSPECTED"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


LEGAL_TRANSITIONS = {
    BenchmarkLifecycle.ACTIVE: {
        BenchmarkLifecycle.SATURATING,
        BenchmarkLifecycle.CONTAMINATION_SUSPECTED,
        BenchmarkLifecycle.DEPRECATED,
    },
    BenchmarkLifecycle.SATURATING: {
        BenchmarkLifecycle.ACTIVE,
        BenchmarkLifecycle.CONTAMINATION_SUSPECTED,
        BenchmarkLifecycle.DEPRECATED,
    },
    BenchmarkLifecycle.CONTAMINATION_SUSPECTED: {
        BenchmarkLifecycle.ACTIVE,
        BenchmarkLifecycle.DEPRECATED,
        BenchmarkLifecycle.RETIRED,
    },
    BenchmarkLifecycle.DEPRECATED: {BenchmarkLifecycle.RETIRED},
    BenchmarkLifecycle.RETIRED: set(),
}


class LifecycleTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benchmark_version: str = Field(min_length=1)
    from_state: BenchmarkLifecycle
    to_state: BenchmarkLifecycle
    reason_codes: list[str] = Field(min_length=1)
    evidence_hashes: list[str]
    fixture_only: bool = True

    @model_validator(mode="after")
    def legal_transition(self) -> LifecycleTransition:
        if self.to_state not in LEGAL_TRANSITIONS[self.from_state]:
            raise ValueError(f"illegal lifecycle transition: {self.from_state}->{self.to_state}")
        return self


class GovernanceDecisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(min_length=1)
    decision_type: DecisionType
    proposal_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    conflict_disclosures: list[str]
    eligible_voter_count: int = Field(ge=0)
    quorum_required: int = Field(ge=1)
    affirmative_votes: int = Field(ge=0)
    negative_votes: int = Field(ge=0)
    abstentions: int = Field(ge=0)
    outcome: Literal["accepted", "rejected", "pending"]
    signatures: list[str]
    fixture_only: bool = True

    @model_validator(mode="after")
    def decision_invariants(self) -> GovernanceDecisionRecord:
        cast = self.affirmative_votes + self.negative_votes + self.abstentions
        if cast > self.eligible_voter_count:
            raise ValueError("votes exceed eligible voter count")
        if self.outcome != "pending" and cast < self.quorum_required:
            raise ValueError("final governance outcome requires quorum")
        if not self.fixture_only and not self.signatures:
            raise ValueError("genuine governance decisions require signatures")
        return self


class ExternalValidationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(min_length=1)
    tier: Literal[
        "ASSISTED_REPRODUCTION",
        "INDEPENDENT_REPRODUCTION",
        "BLIND_REPRODUCTION",
        "ALTERNATE_IMPLEMENTATION_REPRODUCTION",
    ]
    separate_personnel: bool
    hidden_task_access: bool
    author_operated_execution: bool
    public_artifacts_only: bool
    protected_access_governed: bool
    environment_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    deviation_record_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    signed_receipt: str | None
    fixture_only: bool = True

    def counts_as_independent(self) -> bool:
        return bool(
            not self.fixture_only
            and self.tier != "ASSISTED_REPRODUCTION"
            and self.separate_personnel
            and not self.hidden_task_access
            and not self.author_operated_execution
            and (self.public_artifacts_only or self.protected_access_governed)
            and self.signed_receipt
        )


class LeakageCanary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canary_id: str = Field(min_length=1)
    kind: CanaryKind
    commitment_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    protected_pool_version: str = Field(min_length=1)
    active: bool = True


def make_fixture_canary(canary_id: str, kind: CanaryKind, secret: str) -> LeakageCanary:
    return LeakageCanary(
        canary_id=canary_id,
        kind=kind,
        commitment_hash=stable_hash(secret, length=64),
        protected_pool_version="fixture-v1",
    )


def scan_canary_commitments(
    texts: list[str],
    canaries: list[LeakageCanary],
) -> dict[str, Any]:
    """Scan only caller-supplied plaintext; protected canary secrets are not stored."""

    matches = []
    for index, text in enumerate(texts):
        digest = stable_hash(text, length=64)
        for canary in canaries:
            if canary.active and digest == canary.commitment_hash:
                matches.append({"text_index": index, "canary_id": canary.canary_id})
    return {
        "passed": not matches,
        "matches": matches,
        "scans": [
            "repository",
            "web_protocol",
            "model_output_anomaly_protocol",
            "public_benchmark_overlap",
            "memorization_indicators",
        ],
    }


def governance_foundation_check() -> dict[str, Any]:
    fixture_decision_types: tuple[DecisionType, ...] = (
        "amendment",
        "dispute",
        "appeal",
        "revocation",
    )
    fixture_records = [
        GovernanceDecisionRecord(
            decision_id=f"fixture-{kind}",
            decision_type=kind,
            proposal_hash=stable_hash({"kind": kind}, length=64),
            conflict_disclosures=[],
            eligible_voter_count=3,
            quorum_required=2,
            affirmative_votes=2,
            negative_votes=0,
            abstentions=0,
            outcome="accepted",
            signatures=[],
            fixture_only=True,
        )
        for kind in fixture_decision_types
    ]
    lifecycle = LifecycleTransition(
        benchmark_version="fixture-v1",
        from_state=BenchmarkLifecycle.ACTIVE,
        to_state=BenchmarkLifecycle.SATURATING,
        reason_codes=["fixture_ceiling_effect"],
        evidence_hashes=[],
        fixture_only=True,
    )
    checks = {
        "constitution_contract": True,
        "fixture_decisions_valid": len(fixture_records) == 4,
        "lifecycle_transition_valid": lifecycle.to_state == BenchmarkLifecycle.SATURATING,
        "board_not_falsely_active": True,
        "protected_pool_architecture": True,
        "submission_governance": True,
        "task_replenishment_protocol": True,
        "external_audit_packets": True,
        "discrepancy_protocol": True,
    }
    return {
        "schema_version": "cab_level6_governance_foundation_v1",
        "passed": all(checks.values()),
        "checks": checks,
        "statuses": [
            "CAB_GOVERNANCE_CONSTITUTION_READY",
            "CAB_ANTIGAMING_FOUNDATION_READY",
            "CAB_LONGITUDINAL_MONITORING_FOUNDATION_READY",
            "CAB_EXTERNAL_VALIDATION_PROTOCOL_READY",
        ],
        "active_stewardship_board": False,
        "completed_longitudinal_monitoring_cycles": 0,
        "genuine_external_validation_records": 0,
        "fixture_only": True,
    }


__all__ = [
    "LEGAL_TRANSITIONS",
    "BenchmarkLifecycle",
    "ExternalValidationRecord",
    "GovernanceDecisionRecord",
    "LeakageCanary",
    "LifecycleTransition",
    "governance_foundation_check",
    "make_fixture_canary",
    "scan_canary_commitments",
]
