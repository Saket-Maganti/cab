"""Artifact origin and tamper-evident, content-bound coordinator receipts.

This module exists so that no caller-selected boolean can decide whether an
artifact is genuine evidence.  Authenticity is a property of the *authority* that
sealed a receipt:

* A **production** receipt is sealed under the coordinator's external acceptance
  key (``CAB_COORDINATOR_KEY_PATH``) with the production HMAC domain.  Without
  that key no production receipt can be produced at all, so a synthetic run
  cannot mint one.
* A **fixture** receipt is sealed under a well-known constant key with a
  different HMAC domain, and carries
  ``SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE`` as its recorded origin.  Because
  the fixture key is public by construction, a fixture MAC proves nothing about
  authenticity — which is exactly the point.  Rewriting the origin field of a
  fixture receipt invalidates its MAC, and re-sealing it as production requires
  the coordinator key.

What this is: tamper-evident, content-bound receipts plus explicit coordinator
acceptance.  What this is *not*: cryptographic proof of a human reviewer's
identity.  No claim of identity verification is made anywhere in this package.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2.common import FIXTURE_MARKER, canonical_bytes, sha256_json
from causal_agent_bench.review_ready_v2.keys import ExternalKeyError, load_external_key

COORDINATOR_KEY_ENV = "CAB_COORDINATOR_KEY_PATH"

PRODUCTION_ORIGIN = "PRODUCTION_COORDINATOR_ACCEPTED"
FIXTURE_ORIGIN = FIXTURE_MARKER

#: Evidence that reached us through the manual offline-import path rather than
#: through the normal issue-declare-submit sequence.  It is genuine human
#: judgement, sealed under the coordinator's own key, but it is *not* production
#: evidence: no declaration was collected and no issue receipt preceded it.  The
#: separate origin and HMAC domain mean a manual-import receipt can never
#: authenticate against a production gate, and a production receipt can never
#: authenticate against an import gate, in either direction.
MANUAL_IMPORT_ORIGIN = "MANUAL_OFFLINE_REVIEW_IMPORT_V1"

PRODUCTION_RECEIPT_SCHEMA = "cab_review_ready_v2_production_receipt_v1"
FIXTURE_RECEIPT_SCHEMA = "cab_review_ready_v2_fixture_receipt_v1"
MANUAL_IMPORT_RECEIPT_SCHEMA = "cab_review_ready_v2_manual_offline_import_receipt_v1"

_PRODUCTION_DOMAIN = b"cab-review-ready-v2/production-coordinator-receipt/v1"
_FIXTURE_DOMAIN = b"cab-review-ready-v2/synthetic-test-fixture-receipt/v1"
_MANUAL_IMPORT_DOMAIN = b"cab-review-ready-v2/manual-offline-review-import/v1"

#: Deliberately public.  Fixture receipts are sealed with it so that they are
#: reproducible in tests and worthless as evidence.
_FIXTURE_KEY = sha256(b"cab-review-ready-v2/fixture-authority/not-a-secret").digest()

#: Fields that are excluded from the MAC input because they are the MAC itself.
_UNSEALED_FIELDS = ("receipt_mac",)


class ReceiptError(RuntimeError):
    """A receipt could not be sealed or failed verification."""


@dataclass(frozen=True)
class Authority:
    """Who sealed a receipt, and whether receipts it seals can be evidence."""

    origin: str
    schema_version: str
    namespace: str
    counts_as_genuine_evidence: bool
    _domain: bytes
    _key: bytes

    @property
    def is_production(self) -> bool:
        return self.origin == PRODUCTION_ORIGIN


def fixture_authority() -> Authority:
    """The synthetic-test authority.  Its receipts are never genuine evidence."""

    return Authority(
        origin=FIXTURE_ORIGIN,
        schema_version=FIXTURE_RECEIPT_SCHEMA,
        namespace="fixture_receipts",
        counts_as_genuine_evidence=False,
        _domain=_FIXTURE_DOMAIN,
        _key=_FIXTURE_KEY,
    )


def coordinator_authority(repo_root: Path) -> Authority:
    """The production authority.  Fails closed without the external key."""

    try:
        key = load_external_key(COORDINATOR_KEY_ENV, repo_root)
    except ExternalKeyError as error:
        raise ReceiptError(
            f"production receipts require the coordinator acceptance key: {error}"
        ) from error
    return Authority(
        origin=PRODUCTION_ORIGIN,
        schema_version=PRODUCTION_RECEIPT_SCHEMA,
        namespace="receipts",
        counts_as_genuine_evidence=True,
        _domain=_PRODUCTION_DOMAIN,
        _key=key,
    )


def manual_import_authority(repo_root: Path) -> Authority:
    """The manual offline-import authority.  Fails closed without the external key.

    Its receipts count as genuine evidence — the judgements really were made by
    the reviewers — but they carry an origin that says plainly how they arrived.
    Nothing sealed here can satisfy a gate that requires the production origin.
    """

    try:
        key = load_external_key(COORDINATOR_KEY_ENV, repo_root)
    except ExternalKeyError as error:
        raise ReceiptError(
            f"manual-import receipts require the coordinator acceptance key: {error}"
        ) from error
    return Authority(
        origin=MANUAL_IMPORT_ORIGIN,
        schema_version=MANUAL_IMPORT_RECEIPT_SCHEMA,
        namespace="manual_import_receipts",
        counts_as_genuine_evidence=True,
        _domain=_MANUAL_IMPORT_DOMAIN,
        _key=key,
    )


def coordinator_key_available(repo_root: Path) -> bool:
    try:
        coordinator_authority(repo_root)
    except ReceiptError:
        return False
    return True


def _mac(authority: Authority, payload: dict[str, Any]) -> str:
    body = {key: value for key, value in payload.items() if key not in _UNSEALED_FIELDS}
    return hmac.new(authority._key, authority._domain + canonical_bytes(body), sha256).hexdigest()


def seal_receipt(authority: Authority, payload: dict[str, Any]) -> dict[str, Any]:
    """Stamp origin, content hash and MAC onto a receipt payload."""

    stamped: dict[str, Any] = {
        **payload,
        "receipt_schema_version": authority.schema_version,
        "artifact_origin": authority.origin,
        "counts_as_genuine_evidence": authority.counts_as_genuine_evidence,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    stamped["receipt_sha256"] = sha256_json(
        {key: value for key, value in stamped.items() if key not in _UNSEALED_FIELDS}
    )
    stamped["receipt_mac"] = _mac(authority, stamped)
    return stamped


def verify_receipt(authority: Authority, receipt: dict[str, Any]) -> None:
    """Fail closed unless ``receipt`` was sealed by exactly this authority."""

    if receipt.get("artifact_origin") != authority.origin:
        raise ReceiptError(
            f"receipt origin {receipt.get('artifact_origin')!r} does not match the "
            f"{authority.origin!r} authority this gate requires"
        )
    if receipt.get("receipt_schema_version") != authority.schema_version:
        raise ReceiptError(
            f"receipt schema {receipt.get('receipt_schema_version')!r} is not the "
            f"{authority.schema_version!r} schema this gate requires"
        )
    if authority.counts_as_genuine_evidence and receipt.get("counts_as_genuine_evidence") is not True:
        raise ReceiptError("a production gate cannot consume a receipt that disclaims evidence")
    declared_mac = str(receipt.get("receipt_mac", ""))
    if not declared_mac or not hmac.compare_digest(declared_mac, _mac(authority, receipt)):
        raise ReceiptError(
            "receipt authentication failed: the content was altered, or it was sealed by a "
            "different authority (a fixture receipt can never authenticate as production)"
        )
    body = {key: value for key, value in receipt.items() if key not in (*_UNSEALED_FIELDS, "receipt_sha256")}
    if receipt.get("receipt_sha256") != sha256_json(body):
        raise ReceiptError("receipt content hash does not match its content")


def receipt_is_fixture(receipt: dict[str, Any]) -> bool:
    """True when anything about the receipt marks it synthetic."""

    if receipt.get("artifact_origin") == FIXTURE_ORIGIN:
        return True
    if receipt.get("receipt_schema_version") == FIXTURE_RECEIPT_SCHEMA:
        return True
    return FIXTURE_MARKER in canonical_bytes(receipt).decode()


__all__ = [
    "COORDINATOR_KEY_ENV",
    "FIXTURE_ORIGIN",
    "FIXTURE_RECEIPT_SCHEMA",
    "MANUAL_IMPORT_ORIGIN",
    "MANUAL_IMPORT_RECEIPT_SCHEMA",
    "PRODUCTION_ORIGIN",
    "PRODUCTION_RECEIPT_SCHEMA",
    "Authority",
    "ReceiptError",
    "coordinator_authority",
    "coordinator_key_available",
    "fixture_authority",
    "manual_import_authority",
    "receipt_is_fixture",
    "seal_receipt",
    "verify_receipt",
]
