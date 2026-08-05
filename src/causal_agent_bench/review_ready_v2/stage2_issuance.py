"""Stage-2 package issuance: a coordinator-sealed receipt per reviewer.

Generating a Stage-2 ZIP used to produce a hash that nothing downstream had to
honour, so a modified archive, a swapped archive, or an archive built against a
superseded Stage-1 commitment could still be ingested.  Issuance closes that gap.

At generation time the coordinator seals one receipt per reviewer binding the
archive to the whole provenance chain: who it was built for, which Stage-1
commitment authorised it, which packet and freeze and commit it belongs to, and
which declaration and qualification receipt stand behind that reviewer.  Stage-2
ingestion then *requires* the receipt and re-derives every one of those bindings
from the current workspace.  A stale, copied, swapped or edited issuance fails on
identity rather than on a flag, and the receipt hash travels on into the
submission receipt, the disagreement queue, the adjudicator packages, the final
adjudicated records, C10, the slice lock and the execution authorization.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

STAGE2_ISSUANCE_SCHEMA_VERSION = "cab_stage2_issuance_receipt_v1"

#: Every field a Stage-2 issuance receipt must carry.  Ingestion re-derives each
#: one from the workspace and refuses on the first mismatch.
REQUIRED_ISSUANCE_FIELDS: tuple[str, ...] = (
    "reviewer_pseudonym_sha256",
    "reviewer_role",
    "stage1_commitment_sha256",
    "stage2_package_sha256",
    "stage2_opaque_id_namespace",
    "private_packet_commitment",
    "qualification_receipt_sha256",
    "reviewer_declaration_sha256",
    "scientific_freeze_sha256",
    "exact_commit",
    "issued_at",
)


class Stage2IssuanceError(ValueError):
    """A Stage-2 issuance receipt was missing, stale, copied, or contradicted."""


def build_stage2_issuance(
    *,
    reviewer_role: str,
    reviewer_pseudonym_sha256: str,
    stage1_commitment_sha256: str,
    stage2_package_sha256: str,
    stage2_opaque_id_namespace: str,
    private_packet_commitment: str,
    qualification_receipt_sha256: str,
    reviewer_declaration_sha256: str,
    scientific_freeze_sha256: str,
    exact_commit: str,
    issued_at: str | None = None,
) -> dict[str, Any]:
    """Assemble the issuance payload.  The caller seals it as a receipt."""

    payload: dict[str, Any] = {
        "schema_version": STAGE2_ISSUANCE_SCHEMA_VERSION,
        "receipt_kind": "stage2_issuance",
        "reviewer_role": str(reviewer_role),
        "reviewer_pseudonym_sha256": str(reviewer_pseudonym_sha256),
        "stage1_commitment_sha256": str(stage1_commitment_sha256),
        "stage2_package_sha256": str(stage2_package_sha256).strip().casefold(),
        "stage2_opaque_id_namespace": str(stage2_opaque_id_namespace),
        "private_packet_commitment": str(private_packet_commitment),
        "qualification_receipt_sha256": str(qualification_receipt_sha256),
        "reviewer_declaration_sha256": str(reviewer_declaration_sha256),
        "scientific_freeze_sha256": str(scientific_freeze_sha256),
        "exact_commit": str(exact_commit),
        "issued_at": issued_at or datetime.now(UTC).isoformat(),
        "reviewer_pseudonym_published": False,
    }
    missing = sorted(field for field in REQUIRED_ISSUANCE_FIELDS if not str(payload.get(field, "")).strip())
    if missing:
        raise Stage2IssuanceError(f"a Stage-2 issuance receipt is missing {missing}")
    return payload


def verify_stage2_issuance(
    issuance: dict[str, Any],
    *,
    reviewer_role: str,
    reviewer_pseudonym_sha256: str,
    stage1_commitment_sha256: str,
    stage2_package_sha256: str,
    stage2_opaque_id_namespace: str,
    private_packet_commitment: str,
    qualification_receipt_sha256: str,
    reviewer_declaration_sha256: str,
    scientific_freeze_sha256: str,
    exact_commit: str,
    submitted_item_ids: list[str] | None = None,
) -> dict[str, bool]:
    """Re-derive every binding.  Raises on the first contradiction."""

    if not isinstance(issuance, dict):
        raise Stage2IssuanceError("the Stage-2 issuance receipt is malformed")
    missing = sorted(field for field in REQUIRED_ISSUANCE_FIELDS if field not in issuance)
    if missing:
        raise Stage2IssuanceError(f"the Stage-2 issuance receipt is missing {missing}")
    if issuance.get("schema_version") != STAGE2_ISSUANCE_SCHEMA_VERSION:
        raise Stage2IssuanceError(
            f"the Stage-2 issuance receipt declares {issuance.get('schema_version')!r}, not "
            f"{STAGE2_ISSUANCE_SCHEMA_VERSION!r}"
        )

    namespace = str(issuance["stage2_opaque_id_namespace"])
    checks: dict[str, bool] = {
        "issued_to_this_reviewer": str(issuance["reviewer_role"]) == str(reviewer_role),
        "issued_to_this_person": str(issuance["reviewer_pseudonym_sha256"])
        == str(reviewer_pseudonym_sha256),
        "bound_to_the_current_stage1_commitment": str(issuance["stage1_commitment_sha256"])
        == str(stage1_commitment_sha256),
        "bound_to_the_submitted_package": str(issuance["stage2_package_sha256"])
        == str(stage2_package_sha256).strip().casefold(),
        "bound_to_this_reviewer_namespace": namespace == str(stage2_opaque_id_namespace),
        "bound_to_the_active_packet_commitment": str(issuance["private_packet_commitment"])
        == str(private_packet_commitment),
        "bound_to_the_qualification_receipt": str(issuance["qualification_receipt_sha256"])
        == str(qualification_receipt_sha256),
        "bound_to_the_reviewer_declaration": str(issuance["reviewer_declaration_sha256"])
        == str(reviewer_declaration_sha256),
        "bound_to_the_scientific_freeze": str(issuance["scientific_freeze_sha256"])
        == str(scientific_freeze_sha256),
        "bound_to_the_exact_commit": str(issuance["exact_commit"]) == str(exact_commit),
    }
    if submitted_item_ids is not None:
        checks["submitted_rows_are_in_the_issued_namespace"] = all(
            str(item).startswith(f"{namespace}-") for item in submitted_item_ids
        )
    failed = sorted(name for name, value in checks.items() if not value)
    if failed:
        raise Stage2IssuanceError(
            f"the Stage-2 issuance receipt does not authorise this submission: {failed}"
        )
    return checks


def issuance_schema() -> dict[str, Any]:
    """Publishable description of the issuance contract."""

    return {
        "schema_version": "cab_stage2_issuance_schema_v1",
        "issuance_receipt_version": STAGE2_ISSUANCE_SCHEMA_VERSION,
        "required_fields": list(REQUIRED_ISSUANCE_FIELDS),
        "sealed_by": "coordinator_acceptance_key",
        "required_for": "stage2_ingestion",
        "bound_into": [
            "stage2_submission_receipt",
            "stage2_disagreement_queue",
            "stage1_adjudicator_package",
            "stage2_adjudicator_package",
            "final_adjudicated_records",
            "c10_report",
            "reviewed_slice_lock",
            "model_execution_authorization",
        ],
        "refuses": [
            "a modified Stage-2 archive",
            "another reviewer's archive",
            "an issuance receipt copied between reviewers",
            "an issuance bound to a superseded Stage-1 commitment",
            "an issuance carrying the wrong opaque-id namespace",
            "an issuance bound to another packet, freeze, or commit",
        ],
        "reviewer_pseudonyms_published": False,
    }


__all__ = [
    "REQUIRED_ISSUANCE_FIELDS",
    "STAGE2_ISSUANCE_SCHEMA_VERSION",
    "Stage2IssuanceError",
    "build_stage2_issuance",
    "issuance_schema",
    "verify_stage2_issuance",
]
