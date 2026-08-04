"""Reviewer declarations: submitted by the reviewer, never written by the code.

Every field below has to arrive in the reviewer's own submitted declaration
file.  Ingestion parses and validates; it never supplies, defaults, or infers a
value.  A missing confirmation is a refusal, not a ``False``.

A disclosed conflict of interest does not silently pass: it produces a
declaration that is valid but *not accepted*, and the coordinator has to record
an explicit decision before the reviewer can be qualified.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from causal_agent_bench.review_ready_v2.common import FIXTURE_MARKER, canonical_bytes, sha256_json
from causal_agent_bench.review_ready_v2.roles import RoleError, normalize_role

DECLARATION_VERSION = "cab_reviewer_declaration_v1"

#: Statements the reviewer must affirmatively confirm.  Each must be a literal
#: ``true`` in the submitted file; absent, null, "yes" and false are all refusals.
REQUIRED_CONFIRMATIONS: tuple[str, ...] = (
    "independence_confirmed",
    "not_author_or_coauthor_confirmed",
    "no_ai_assistance_confirmed",
    "confidentiality_confirmed",
    "worked_independently_confirmed",
)

REQUIRED_FIELDS: tuple[str, ...] = (
    "declaration_version",
    "reviewer_pseudonym",
    "package_role",
    "qualification_package_hash",
    "stage1_package_hash",
    *REQUIRED_CONFIRMATIONS,
    "conflict_of_interest_disclosed",
    "conflict_of_interest_details",
    "signed_name_or_approved_signature_field",
    "signed_at",
)

OPTIONAL_FIELDS: tuple[str, ...] = (
    "conflict_of_interest_details_are_encrypted",
    "notes",
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class DeclarationError(ValueError):
    """A reviewer declaration was missing, malformed, or unaffirmed."""


def declaration_template() -> dict[str, Any]:
    """An empty template.  Safe to ship: it contains no answers and no values."""

    return {
        "declaration_version": DECLARATION_VERSION,
        "reviewer_pseudonym": "",
        "package_role": "",
        "qualification_package_hash": "",
        "stage1_package_hash": "",
        "independence_confirmed": None,
        "not_author_or_coauthor_confirmed": None,
        "no_ai_assistance_confirmed": None,
        "confidentiality_confirmed": None,
        "worked_independently_confirmed": None,
        "conflict_of_interest_disclosed": None,
        "conflict_of_interest_details": "",
        "conflict_of_interest_details_are_encrypted": False,
        "signed_name_or_approved_signature_field": "",
        "signed_at": "",
    }


DECLARATION_INSTRUCTIONS = """# Reviewer declaration

Fill in `reviewer_declaration.json` and return it with your qualification
answers. The coordinator cannot qualify you without it, and cannot fill any of
it in on your behalf.

Every `*_confirmed` field must be a literal JSON `true`. If any statement is not
true for you, say so — write `false` and tell the coordinator. A `false` stops
the process; it does not fail you.

* `independence_confirmed` — you are independent of the benchmark authors.
* `not_author_or_coauthor_confirmed` — you are not an author or co-author.
* `no_ai_assistance_confirmed` — you used no AI assistant or language model for
  any part of this review, including the qualification items.
* `confidentiality_confirmed` — you will not copy, publish, post, or upload any
  part of the package, and will delete your copy when the coordinator confirms
  receipt.
* `worked_independently_confirmed` — you discussed no item with the other
  reviewer or anyone else.
* `conflict_of_interest_disclosed` — `true` if you have any financial,
  professional or personal interest in the outcome. Disclosing a conflict does
  not automatically disqualify you; concealing one invalidates the review.
* `conflict_of_interest_details` — required when you disclose one. If it is
  sensitive, encrypt it, paste the ciphertext, and set
  `conflict_of_interest_details_are_encrypted` to `true`.
* `signed_name_or_approved_signature_field` — your name, or the signature form
  the coordinator agreed with you.
* `signed_at` — an ISO-8601 timestamp.

This is a content-bound, tamper-evident record. It is not a cryptographic proof
of identity, and the project does not claim it is.
"""


def _as_bool(payload: dict[str, Any], field: str) -> bool:
    value = payload[field]
    if not isinstance(value, bool):
        raise DeclarationError(
            f"declaration field {field!r} must be a literal true or false, got {value!r}; "
            "ingestion never supplies a default"
        )
    return value


def parse_declaration(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a submitted declaration.  Every value comes from ``payload``."""

    if not isinstance(payload, dict):
        raise DeclarationError("the reviewer declaration must be a JSON object")
    missing = sorted(field for field in REQUIRED_FIELDS if field not in payload)
    if missing:
        raise DeclarationError(f"the reviewer declaration is missing required fields: {missing}")
    unknown = sorted(set(payload) - set(REQUIRED_FIELDS) - set(OPTIONAL_FIELDS))
    if unknown:
        raise DeclarationError(f"the reviewer declaration carries unknown fields: {unknown}")

    if str(payload["declaration_version"]) != DECLARATION_VERSION:
        raise DeclarationError(
            f"declaration_version must be {DECLARATION_VERSION!r}, got "
            f"{payload['declaration_version']!r}"
        )

    pseudonym = str(payload["reviewer_pseudonym"]).strip()
    if not pseudonym:
        raise DeclarationError("reviewer_pseudonym must not be empty")
    try:
        role = normalize_role(payload["package_role"])
    except RoleError as error:
        raise DeclarationError(str(error)) from error

    for field in ("qualification_package_hash", "stage1_package_hash"):
        value = str(payload[field]).strip().casefold()
        if not _HEX64.match(value):
            raise DeclarationError(f"{field} must be a 64-character sha256 hex digest")

    unaffirmed = sorted(field for field in REQUIRED_CONFIRMATIONS if not _as_bool(payload, field))
    if unaffirmed:
        raise DeclarationError(
            f"the reviewer did not affirm required declarations: {unaffirmed}; "
            "the review cannot proceed"
        )

    coi = _as_bool(payload, "conflict_of_interest_disclosed")
    details = str(payload["conflict_of_interest_details"]).strip()
    if coi and not details:
        raise DeclarationError(
            "conflict_of_interest_disclosed is true but conflict_of_interest_details is empty"
        )
    if not coi and details:
        raise DeclarationError(
            "conflict_of_interest_details were supplied without disclosing a conflict"
        )

    signature = str(payload["signed_name_or_approved_signature_field"]).strip()
    if not signature:
        raise DeclarationError("signed_name_or_approved_signature_field must not be empty")
    signed_at = str(payload["signed_at"]).strip()
    try:
        datetime.fromisoformat(signed_at)
    except ValueError as error:
        raise DeclarationError(f"signed_at must be an ISO-8601 timestamp, got {signed_at!r}") from error

    synthetic = FIXTURE_MARKER in canonical_bytes(payload).decode()

    normalized: dict[str, Any] = {
        "declaration_version": DECLARATION_VERSION,
        "reviewer_pseudonym": pseudonym,
        "package_role": role,
        "qualification_package_hash": str(payload["qualification_package_hash"]).strip().casefold(),
        "stage1_package_hash": str(payload["stage1_package_hash"]).strip().casefold(),
        **dict.fromkeys(REQUIRED_CONFIRMATIONS, True),
        "conflict_of_interest_disclosed": coi,
        "conflict_of_interest_details_present": bool(details),
        "conflict_of_interest_details_are_encrypted": bool(
            payload.get("conflict_of_interest_details_are_encrypted", False)
        ),
        # The details themselves are never copied into the receipt; only a
        # binding hash, so a receipt can be published without the disclosure.
        "conflict_of_interest_details_sha256": sha256_json(details) if details else None,
        "signed_name_sha256": sha256_json(signature),
        "signed_at": signed_at,
        "declaration_is_synthetic": synthetic,
        "requires_coordinator_review": bool(coi),
    }
    normalized["declaration_sha256"] = sha256_json(normalized)
    return normalized


def declaration_blocks_qualification(declaration: dict[str, Any]) -> list[str]:
    """Reasons this declaration cannot yet support a production qualification."""

    blockers: list[str] = []
    if declaration.get("declaration_is_synthetic"):
        blockers.append("declaration_is_synthetic")
    if declaration.get("requires_coordinator_review") and not declaration.get(
        "coordinator_review_decision"
    ):
        blockers.append("disclosed_conflict_awaiting_coordinator_decision")
    if declaration.get("coordinator_review_decision") == "REJECTED":
        blockers.append("coordinator_rejected_declaration")
    return blockers


__all__ = [
    "DECLARATION_INSTRUCTIONS",
    "DECLARATION_VERSION",
    "OPTIONAL_FIELDS",
    "REQUIRED_CONFIRMATIONS",
    "REQUIRED_FIELDS",
    "DeclarationError",
    "declaration_blocks_qualification",
    "declaration_template",
    "parse_declaration",
]
