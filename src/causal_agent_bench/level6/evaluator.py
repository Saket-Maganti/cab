"""Bounded protected-evaluator challenge and appeals protocol."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.hashing import stable_hash


class EvaluatorBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_tool_calls: int = Field(ge=0)
    max_model_calls: int = Field(ge=0)
    max_tokens: int = Field(ge=0)
    max_wall_seconds: float = Field(gt=0)


class ProtectedSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submission_id: str = Field(min_length=1)
    payload_ciphertext_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    signature: str = Field(min_length=1)
    system_identity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    budget: EvaluatorBudget
    confidentiality_terms_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    replay_nonce: str = Field(min_length=16)
    fixture_only: bool = True


class ImmutableRunReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt_id: str = Field(min_length=1)
    submission_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    protected_task_commitment: str = Field(pattern=r"^[0-9a-f]{64}$")
    environment_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    result_attestation_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    replay_audit_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    rate_limit_bucket: str = Field(min_length=1)
    revoked: bool = False
    fixture_only: bool = True


class ChallengeAppeal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appeal_id: str = Field(min_length=1)
    run_receipt_id: str = Field(min_length=1)
    kind: Literal["challenge", "appeal", "correction", "revocation"]
    evidence_hashes: list[str] = Field(min_length=1)
    status: Literal["submitted", "under_review", "upheld", "denied", "corrected", "revoked"]
    decision_signature: str | None = None
    fixture_only: bool = True

    @model_validator(mode="after")
    def final_status_signed(self) -> ChallengeAppeal:
        if self.status not in {"submitted", "under_review"} and not self.decision_signature:
            if not self.fixture_only:
                raise ValueError("genuine final appeal state requires a decision signature")
        return self


def protected_evaluator_fixture_demo() -> dict[str, object]:
    budget = EvaluatorBudget(
        max_tool_calls=10,
        max_model_calls=5,
        max_tokens=4_096,
        max_wall_seconds=120,
    )
    submission = ProtectedSubmission(
        submission_id="fixture-submission",
        payload_ciphertext_hash=stable_hash("fixture-ciphertext", length=64),
        signature="fixture-signature-not-production",
        system_identity_hash=stable_hash("fixture-system", length=64),
        budget=budget,
        confidentiality_terms_hash=stable_hash("fixture-terms", length=64),
        replay_nonce="fixture-replay-nonce-0001",
        fixture_only=True,
    )
    submission_hash = stable_hash(submission.model_dump(mode="json"), length=64)
    receipt = ImmutableRunReceipt(
        receipt_id="fixture-run-receipt",
        submission_hash=submission_hash,
        protected_task_commitment=stable_hash("fixture-task", length=64),
        environment_hash=stable_hash("fixture-environment", length=64),
        result_attestation_hash=stable_hash("fixture-result", length=64),
        replay_audit_hash=stable_hash("fixture-replay", length=64),
        rate_limit_bucket="fixture-only",
        fixture_only=True,
    )
    appeal = ChallengeAppeal(
        appeal_id="fixture-appeal",
        run_receipt_id=receipt.receipt_id,
        kind="appeal",
        evidence_hashes=[receipt.result_attestation_hash],
        status="submitted",
        fixture_only=True,
    )
    return {
        "schema_version": "cab_protected_evaluator_protocol_fixture_v1",
        "status": "CAB_PROTECTED_EVALUATOR_PROTOCOL_READY",
        "submission": submission.model_dump(mode="json"),
        "run_receipt": receipt.model_dump(mode="json"),
        "appeal": appeal.model_dump(mode="json"),
        "encrypted_transfer_required": True,
        "protected_execution_required": True,
        "genuine_external_pilot": False,
        "fixture_only": True,
    }


__all__ = [
    "ChallengeAppeal",
    "EvaluatorBudget",
    "ImmutableRunReceipt",
    "ProtectedSubmission",
    "protected_evaluator_fixture_demo",
]
