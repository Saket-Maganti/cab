"""The immutable reviewer assignment registry: one source of truth for who is who.

Every later artifact — declaration, qualification receipt, Stage-1 submission,
Stage-1 commitment, Stage-2 package, Stage-2 submission, adjudication, C10 —
resolves through this registry.  An assignment binds, once and for good:

``reviewer pseudonym → canonical role → package role → package hash →
qualification package hash → opaque id namespaces``

Assignments are write-once.  Re-registering a role, reusing a pseudonym across
roles, or presenting a package whose hash does not match the recorded binding is
refused, so a package swap is a hash error rather than a silent re-assignment.
The file is private; it never enters Git.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2.common import read_json, sha256_json, write_json
from causal_agent_bench.review_ready_v2.roles import (
    ADJUDICATOR,
    CANONICAL_ROLES,
    REVIEW_ROLES,
    namespace_for,
    normalize_role,
    package_basename,
)

ASSIGNMENT_REGISTRY_SCHEMA = "cab_reviewer_assignment_registry_v1"
ASSIGNMENT_STATUS_ACTIVE = "ACTIVE"
ASSIGNMENT_STATUS_REVOKED = "REVOKED"

REGISTRY_FILENAME = "reviewer_assignments.json"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class AssignmentError(ValueError):
    """The reviewer assignment registry refused an operation or a binding."""


def registry_path(private_root: Path) -> Path:
    return private_root / "coordinator" / REGISTRY_FILENAME


def _digest(registry: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in registry.items() if key != "registry_sha256"})


def empty_registry(packet_version: str) -> dict[str, Any]:
    registry = {
        "schema_version": ASSIGNMENT_REGISTRY_SCHEMA,
        "packet_version": packet_version,
        "assignments": {},
    }
    registry["registry_sha256"] = _digest(registry)
    return registry


def load_assignments(private_root: Path, *, packet_version: str) -> dict[str, Any]:
    """Load and integrity-check the registry, creating an empty one if absent."""

    path = registry_path(private_root)
    if not path.is_file():
        return empty_registry(packet_version)
    registry = read_json(path)
    if registry.get("schema_version") != ASSIGNMENT_REGISTRY_SCHEMA:
        raise AssignmentError(
            f"assignment registry schema {registry.get('schema_version')!r} is not "
            f"{ASSIGNMENT_REGISTRY_SCHEMA!r}"
        )
    if registry.get("packet_version") != packet_version:
        raise AssignmentError(
            f"assignment registry belongs to packet {registry.get('packet_version')!r}, "
            f"not the active packet {packet_version!r}"
        )
    if registry.get("registry_sha256") != _digest(registry):
        raise AssignmentError(
            "the assignment registry has been edited outside the workflow; its integrity "
            "digest does not match its content"
        )
    return registry


def _save(private_root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    registry["registry_sha256"] = _digest(registry)
    path = registry_path(private_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    write_json(path, registry)
    path.chmod(0o600)
    return registry


def create_assignment(
    private_root: Path,
    *,
    packet_version: str,
    reviewer_pseudonym: str,
    role: str,
    stage1_package_hash: str | None = None,
    qualification_package_hash: str | None = None,
) -> dict[str, Any]:
    """Register one write-once assignment.  Refuses every form of overlap."""

    canonical = normalize_role(role)
    pseudonym = str(reviewer_pseudonym).strip()
    if not pseudonym:
        raise AssignmentError("a reviewer pseudonym is required")

    registry = load_assignments(private_root, packet_version=packet_version)
    assignments: dict[str, Any] = registry["assignments"]

    if canonical in assignments:
        raise AssignmentError(
            f"{canonical} is already assigned; assignments are immutable. Revoke and issue a new "
            "packet version rather than reassigning a role."
        )
    for existing_role, existing in assignments.items():
        if str(existing["reviewer_pseudonym"]) == pseudonym:
            raise AssignmentError(
                f"pseudonym {pseudonym!r} already holds {existing_role}; one person cannot hold "
                "two roles, and a reviewer cannot also adjudicate"
            )

    if canonical in REVIEW_ROLES:
        for label, value in (
            ("stage1_package_hash", stage1_package_hash),
            ("qualification_package_hash", qualification_package_hash),
        ):
            if value is None or not _HEX64.match(str(value).strip().casefold()):
                raise AssignmentError(f"{label} must be a 64-character sha256 hex digest for {canonical}")
        stage1_role = package_basename(canonical)
        namespace = namespace_for(canonical)
    else:
        stage1_role = None
        namespace = None

    for other_role, other in assignments.items():
        if (
            stage1_package_hash
            and other.get("stage1_package_hash") == str(stage1_package_hash).strip().casefold()
        ):
            raise AssignmentError(
                f"the Stage-1 package bound to {other_role} cannot also be bound to {canonical}; "
                "the two reviewers must receive independently ordered packages"
            )

    assignment = {
        "reviewer_pseudonym": pseudonym,
        "reviewer_role": canonical,
        "stage1_package_role": stage1_role,
        "stage1_package_hash": str(stage1_package_hash).strip().casefold()
        if stage1_package_hash
        else None,
        "qualification_package_role": f"qualification_{canonical.casefold()}"
        if canonical in REVIEW_ROLES
        else None,
        "qualification_package_hash": str(qualification_package_hash).strip().casefold()
        if qualification_package_hash
        else None,
        "stage1_opaque_id_namespace": namespace,
        "stage2_opaque_id_namespace": namespace,
        "assignment_created_at": datetime.now(UTC).isoformat(),
        "assignment_status": ASSIGNMENT_STATUS_ACTIVE,
    }
    assignment["assignment_sha256"] = sha256_json(assignment)
    assignments[canonical] = assignment
    _save(private_root, registry)
    return assignment


def assignment_for_role(registry: dict[str, Any], role: str) -> dict[str, Any]:
    canonical = normalize_role(role)
    assignment = registry.get("assignments", {}).get(canonical)
    if assignment is None:
        raise AssignmentError(f"no assignment is registered for {canonical}")
    if assignment.get("assignment_status") != ASSIGNMENT_STATUS_ACTIVE:
        raise AssignmentError(f"the assignment for {canonical} is {assignment.get('assignment_status')}")
    if assignment.get("assignment_sha256") != sha256_json(
        {key: value for key, value in assignment.items() if key != "assignment_sha256"}
    ):
        raise AssignmentError(f"the assignment for {canonical} has been tampered with")
    return assignment


def assignment_for_pseudonym(registry: dict[str, Any], pseudonym: str) -> dict[str, Any]:
    for role in registry.get("assignments", {}):
        assignment = registry["assignments"][role]
        if str(assignment["reviewer_pseudonym"]) == str(pseudonym).strip():
            return assignment_for_role(registry, role)
    raise AssignmentError(f"no assignment is registered for pseudonym {pseudonym!r}")


def verify_assignment(
    registry: dict[str, Any],
    *,
    role: str,
    reviewer_pseudonym: str,
    stage1_package_hash: str | None = None,
    qualification_package_hash: str | None = None,
    item_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Fail closed unless every offered binding matches the recorded assignment."""

    canonical = normalize_role(role)
    assignment = assignment_for_role(registry, canonical)
    pseudonym = str(reviewer_pseudonym).strip()
    if str(assignment["reviewer_pseudonym"]) != pseudonym:
        raise AssignmentError(
            f"{pseudonym!r} is not the reviewer assigned to {canonical}; refusing the submission"
        )
    if stage1_package_hash is not None:
        offered = str(stage1_package_hash).strip().casefold()
        if assignment["stage1_package_hash"] != offered:
            raise AssignmentError(
                f"the Stage-1 package offered for {canonical} does not match the package bound to "
                "that assignment (renamed, swapped, or regenerated package)"
            )
    if qualification_package_hash is not None:
        offered = str(qualification_package_hash).strip().casefold()
        if assignment["qualification_package_hash"] != offered:
            raise AssignmentError(
                f"the qualification package offered for {canonical} does not match the package "
                "bound to that assignment"
            )
    if item_ids:
        namespace = assignment["stage1_opaque_id_namespace"]
        foreign = sorted({item for item in item_ids if not str(item).startswith(f"{namespace}-")})
        if foreign:
            raise AssignmentError(
                f"{canonical} submitted {len(foreign)} row(s) outside its own "
                f"{namespace!r} item namespace; this is another reviewer's package"
            )
    return assignment


def verify_registry_complete(registry: dict[str, Any]) -> dict[str, Any]:
    """Check that two distinct reviewers and one distinct adjudicator exist."""

    assignments = registry.get("assignments", {})
    pseudonyms = {
        role: str(row["reviewer_pseudonym"]) for role, row in assignments.items()
    }
    distinct = len(set(pseudonyms.values())) == len(pseudonyms)
    checks = {
        "both_reviewers_assigned": all(role in assignments for role in REVIEW_ROLES),
        "adjudicator_assigned": ADJUDICATOR in assignments,
        "all_roles_held_by_distinct_people": distinct,
        "no_unknown_roles": set(assignments) <= set(CANONICAL_ROLES),
        "all_assignments_active": all(
            row.get("assignment_status") == ASSIGNMENT_STATUS_ACTIVE for row in assignments.values()
        ),
        "reviewer_namespaces_distinct": len(
            {
                row.get("stage1_opaque_id_namespace")
                for role, row in assignments.items()
                if role in REVIEW_ROLES
            }
        )
        == len([role for role in assignments if role in REVIEW_ROLES]),
        "registry_digest_intact": registry.get("registry_sha256") == _digest(registry),
    }
    return {
        "schema_version": "cab_reviewer_assignment_check_v1",
        "assigned_roles": sorted(assignments),
        "checks": checks,
        "passed": all(checks.values()),
    }


def public_assignment_summary(registry: dict[str, Any]) -> dict[str, Any]:
    """Publishable summary: roles and binding hashes only, never a pseudonym."""

    assignments = registry.get("assignments", {})
    return {
        "schema_version": "cab_reviewer_assignment_public_summary_v1",
        "assignment_registry_schema": ASSIGNMENT_REGISTRY_SCHEMA,
        "assigned_role_count": len(assignments),
        "assigned_roles": sorted(assignments),
        "roles": {
            role: {
                "stage1_package_role": row.get("stage1_package_role"),
                "stage1_package_hash": row.get("stage1_package_hash"),
                "qualification_package_hash": row.get("qualification_package_hash"),
                "opaque_id_namespace": row.get("stage1_opaque_id_namespace"),
                "assignment_status": row.get("assignment_status"),
                "assignment_sha256": row.get("assignment_sha256"),
            }
            for role, row in sorted(assignments.items())
        },
        "reviewer_pseudonyms_published": False,
    }


__all__ = [
    "ASSIGNMENT_REGISTRY_SCHEMA",
    "ASSIGNMENT_STATUS_ACTIVE",
    "ASSIGNMENT_STATUS_REVOKED",
    "AssignmentError",
    "assignment_for_pseudonym",
    "assignment_for_role",
    "create_assignment",
    "empty_registry",
    "load_assignments",
    "public_assignment_summary",
    "registry_path",
    "verify_assignment",
    "verify_registry_complete",
]
