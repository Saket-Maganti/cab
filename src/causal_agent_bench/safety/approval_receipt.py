"""Cryptographically verifiable, content-bound CAB execution approvals."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.hashing import stable_hash


class ApprovalArtifactBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CryptographicApprovalReceipt(BaseModel):
    """Immutable approval over the exact scientific execution inputs."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cab_cryptographic_approval_receipt_v1"]
    receipt_id: str = Field(min_length=1)
    approval_scope: Literal["fixture", "scientific"]
    issuer_id: str = Field(min_length=1)
    public_key_id: str = Field(min_length=1)
    issued_at: datetime
    expires_at: datetime
    evidence_completed_at: datetime
    nonce: str = Field(min_length=16)
    candidate_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage1_commitment_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage2_packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    c10_receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    c10_status: Literal["FIXTURE_ACCEPTED", "GENUINE_C10_PASSED"]
    c10_candidate_count: int = Field(ge=1)
    c10_included_count: int = Field(ge=0)
    excluded_candidate_ids: list[str]
    executable_reachability_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    gold_reconstruction_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    intervention_isolation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scorer_name: str = Field(min_length=1)
    scorer_version: str = Field(min_length=1)
    scorer_policy_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    system_identity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    code_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    task_pack_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    intervention_pack_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    revocation_registry_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_bindings: dict[str, ApprovalArtifactBinding]
    signature_algorithm: Literal["Ed25519"]
    signature_or_log: dict[str, str]

    @model_validator(mode="after")
    def validate_receipt_invariants(self) -> CryptographicApprovalReceipt:
        if self.issued_at <= self.evidence_completed_at:
            raise ValueError("approval must be issued after evidence completion")
        if self.expires_at <= self.issued_at:
            raise ValueError("approval expiry must be after issuance")
        if self.c10_included_count + len(self.excluded_candidate_ids) != self.c10_candidate_count:
            raise ValueError("C10 included and excluded counts must cover every candidate")
        if self.approval_scope == "scientific" and self.c10_status != "GENUINE_C10_PASSED":
            raise ValueError("scientific approval requires genuine C10")
        if self.signature_or_log.get("kind") != "ed25519_signature":
            raise ValueError("signature_or_log must contain an Ed25519 signature")
        if not self.signature_or_log.get("signature_base64"):
            raise ValueError("signature_or_log is missing signature_base64")
        return self


def approval_signature_payload(receipt: CryptographicApprovalReceipt) -> bytes:
    payload = receipt.model_dump(mode="json", exclude={"signature_or_log"})
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def verify_approval_receipt(
    receipt_path: str | Path,
    *,
    repo_root: str | Path,
    allowed_scope: Literal["fixture", "scientific"],
    trusted_issuers_path: str | Path = "configs/approval/trusted_issuers.json",
    revocation_registry_path: str | Path = "configs/approval/revocations.json",
    expected_bindings: dict[str, str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify signature, freshness, scope, references, C10, and substitutions."""

    root = Path(repo_root).resolve()
    path = _resolve(root, receipt_path)
    trusted_path = _resolve(root, trusted_issuers_path)
    revocations_path = _resolve(root, revocation_registry_path)
    errors: list[str] = []
    try:
        receipt = CryptographicApprovalReceipt.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "schema_version": "cab_approval_verification_v1",
            "passed": False,
            "errors": [f"INVALID_RECEIPT:{type(exc).__name__}:{exc}"],
            "receipt_path": str(path),
        }
    trusted = _read_json(trusted_path)
    issuers = trusted.get("issuers", {})
    issuer = issuers.get(receipt.issuer_id) if isinstance(issuers, dict) else None
    if not isinstance(issuer, dict):
        errors.append("UNTRUSTED_ISSUER")
    elif issuer.get("public_key_id") != receipt.public_key_id:
        errors.append("PUBLIC_KEY_ID_MISMATCH")
    else:
        if receipt.approval_scope not in set(issuer.get("allowed_scopes", [])):
            errors.append("ISSUER_SCOPE_NOT_TRUSTED")
        try:
            public_key = Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(str(issuer["public_key_hex"]))
            )
            signature = base64.b64decode(
                receipt.signature_or_log["signature_base64"],
                validate=True,
            )
            public_key.verify(signature, approval_signature_payload(receipt))
        except (KeyError, ValueError, InvalidSignature):
            errors.append("SIGNATURE_INVALID")

    current = now or datetime.now(UTC)
    issued = receipt.issued_at
    expires = receipt.expires_at
    if issued.tzinfo is None or expires.tzinfo is None:
        errors.append("TIMESTAMP_NOT_TIMEZONE_AWARE")
    else:
        if current < issued:
            errors.append("RECEIPT_NOT_YET_VALID")
        if current >= expires:
            errors.append("RECEIPT_EXPIRED")
    if receipt.approval_scope != allowed_scope:
        errors.append("APPROVAL_SCOPE_MISMATCH")
    if allowed_scope == "scientific" and receipt.c10_status != "GENUINE_C10_PASSED":
        errors.append("GENUINE_C10_REQUIRED")

    if _sha256_file(revocations_path) != receipt.revocation_registry_sha256:
        errors.append("REVOCATION_REGISTRY_HASH_MISMATCH")
    revocations = _read_json(revocations_path)
    if receipt.receipt_id in set(revocations.get("revoked_receipt_ids", [])):
        errors.append("RECEIPT_REVOKED")
    if receipt.nonce in set(revocations.get("revoked_nonces", [])):
        errors.append("NONCE_REVOKED")

    verified_bindings: dict[str, str] = {}
    for name, binding in receipt.artifact_bindings.items():
        artifact = _resolve(root, binding.path)
        if not artifact.is_file():
            errors.append(f"BOUND_ARTIFACT_MISSING:{name}")
            continue
        observed = _sha256_file(artifact)
        verified_bindings[name] = observed
        if observed != binding.sha256:
            errors.append(f"BOUND_ARTIFACT_HASH_MISMATCH:{name}")
    direct_hashes = {
        "candidate_manifest": receipt.candidate_manifest_sha256,
        "stage1_commitment": receipt.stage1_commitment_sha256,
        "stage2_packet": receipt.stage2_packet_sha256,
        "c10_receipt": receipt.c10_receipt_sha256,
        "executable_reachability": receipt.executable_reachability_sha256,
        "gold_reconstruction": receipt.gold_reconstruction_sha256,
        "intervention_isolation": receipt.intervention_isolation_sha256,
        "task_pack": receipt.task_pack_sha256,
        "intervention_pack": receipt.intervention_pack_sha256,
    }
    for name, expected in direct_hashes.items():
        bound_hash = verified_bindings.get(name)
        if bound_hash is None:
            errors.append(f"REQUIRED_BINDING_MISSING:{name}")
        elif bound_hash != expected:
            errors.append(f"DIRECT_HASH_BINDING_MISMATCH:{name}")

    for name, expected in sorted((expected_bindings or {}).items()):
        expected_hash = direct_hashes.get(name) or verified_bindings.get(name)
        if expected_hash != expected:
            errors.append(f"EXPECTED_BINDING_SUBSTITUTION:{name}")

    result: dict[str, Any] = {
        "schema_version": "cab_approval_verification_v1",
        "passed": not errors,
        "receipt_id": receipt.receipt_id,
        "approval_scope": receipt.approval_scope,
        "issuer_id": receipt.issuer_id,
        "signature_verified": "SIGNATURE_INVALID" not in errors
        and "UNTRUSTED_ISSUER" not in errors,
        "verified_binding_count": len(verified_bindings),
        "excluded_candidate_count": len(receipt.excluded_candidate_ids),
        "errors": sorted(set(errors)),
        "receipt_sha256": _sha256_file(path),
    }
    result["verification_hash"] = stable_hash(result, length=64)
    return result


def verify_fixture_approval(repo_root: str | Path) -> dict[str, Any]:
    return verify_approval_receipt(
        "tests/fixtures/approval/fixture_approval_receipt.json",
        repo_root=repo_root,
        allowed_scope="fixture",
    )


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "ApprovalArtifactBinding",
    "CryptographicApprovalReceipt",
    "approval_signature_payload",
    "verify_approval_receipt",
    "verify_fixture_approval",
]
