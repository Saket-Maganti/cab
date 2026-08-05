"""Immutable committed review evidence: canonical digests and sealed snapshots.

A commitment that binds only the reviewer's uploaded CSV bytes binds the wrong
thing.  The scientific record downstream is not the CSV — it is the *parsed*
judgement content inside the sealed submission receipt, together with the role,
package, declaration and qualification bindings that receipt carries.  A
coordinator who edits the parsed content, keeps the original ``submission_sha256``
field, and re-seals the receipt leaves the commitment satisfied while changing
what every later gate reads.  That is the defect this module closes.

Three digests are kept deliberately distinct and are never interchangeable:

``payload_sha256``
    The bytes the reviewer actually uploaded.  Proves the form was not edited in
    transit; proves nothing about the receipt built from it.
``sealed_receipt_file_sha256``
    The exact bytes of the sealed receipt file on disk, envelope and all.  Any
    re-seal changes it, because sealing stamps a fresh ``recorded_at``.
``canonical_scientific_content_sha256``
    A deterministic digest over the scientific content alone — every parsed
    judgement cell, every provenance binding, the validation result — with only
    the receipt's own hash and MAC excluded.  It is stable across re-serialisation
    and re-sealing, so it answers "did the *content* change?" rather than "did the
    file change?".

At commitment the verified receipt bytes are copied into a write-once snapshot
directory, a sealed manifest binds all three digests per reviewer, and the
commitment binds the manifest.  Every downstream gate reads the snapshot, never
the live receipt path — and treats a live receipt that no longer matches the
snapshot as tampering rather than as an update.
"""

from __future__ import annotations

import json
import os
import secrets
import stat
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2.common import (
    read_json,
    sha256_bytes,
    sha256_json,
)
from causal_agent_bench.review_ready_v2.receipts import (
    Authority,
    ReceiptError,
    receipt_is_fixture,
    seal_receipt,
    verify_receipt,
)
from causal_agent_bench.review_ready_v2.roles import REVIEW_ROLES, RoleError, normalize_role
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_FORM_COLUMNS
from causal_agent_bench.review_ready_v2.stage2 import STAGE2_FORM_COLUMNS

STAGE1 = "stage1"
STAGE2 = "stage2"

#: Active schema versions.  A retired version is rejected outright; there is no
#: silent in-place migration of scientific review evidence.
STAGE1_COMMITMENT_SCHEMA_VERSION = "cab_stage1_commitment_v3"
STAGE1_SNAPSHOT_SCHEMA_VERSION = "cab_committed_stage1_snapshot_v1"
STAGE2_SNAPSHOT_SCHEMA_VERSION = "cab_committed_stage2_snapshot_v1"
REVIEW_INPUT_GRAPH_SCHEMA_VERSION = "cab_review_input_graph_v1"

#: Commitment schemas the active workflow refuses.  ``None`` is the pre-repair
#: shape, which carried no schema field and bound only the CSV payload hash.
RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS: tuple[str | None, ...] = (
    None,
    "cab_stage1_commitment_v1",
    "cab_stage1_commitment_v2",
)

SNAPSHOT_SCHEMA_VERSIONS: dict[str, str] = {
    STAGE1: STAGE1_SNAPSHOT_SCHEMA_VERSION,
    STAGE2: STAGE2_SNAPSHOT_SCHEMA_VERSION,
}

SNAPSHOT_DIRNAMES: dict[str, str] = {
    STAGE1: "committed_stage1",
    STAGE2: "committed_stage2",
}

MANIFEST_FILENAME = "manifest.json"

#: Digest kinds.  Each is part of the digest input, so a Stage-1 receipt can
#: never collide with a Stage-2 receipt that happens to carry the same cells.
_STAGE1_JUDGEMENTS_DIGEST = "cab_stage1_canonical_judgements_v1"
_STAGE2_JUDGEMENTS_DIGEST = "cab_stage2_canonical_judgements_v1"
_DECLARATION_DIGEST = "cab_reviewer_declaration_canonical_v1"
_QUALIFICATION_DIGEST = "cab_reviewer_qualification_canonical_v1"
_ADJUDICATION_DIGEST = "cab_adjudication_canonical_v1"
_QUEUE_DIGEST = "cab_disagreement_queue_canonical_v1"
_REGISTRY_DIGEST = "cab_assignment_registry_canonical_v1"

#: Self-referential envelope fields.  They are the only things a canonical
#: *content* digest may exclude: a digest cannot cover itself, and a MAC is
#: computed over the digest.  Everything else — including notes, which gate
#: nothing but are still committed evidence — is inside.
_SELF_REFERENTIAL_FIELDS: tuple[str, ...] = ("receipt_sha256", "receipt_mac")

#: Fields stamped by sealing rather than by the workflow.  They belong to the
#: file digest, not to the scientific-content digest, because re-sealing an
#: unchanged receipt must not look like a content change.
_SEALING_FIELDS: tuple[str, ...] = ("recorded_at",)


class CommitmentIntegrityError(RuntimeError):
    """Committed review evidence was missing, altered, replayed, or replaced."""


# --------------------------------------------------------------------------
# canonicalisation primitives
# --------------------------------------------------------------------------


def _text(value: Any) -> str:
    return str("" if value is None else value).strip()


def _hex64(value: Any, field: str) -> str:
    text = _text(value).casefold()
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise CommitmentIntegrityError(f"{field} must be a 64-character sha256 hex digest")
    return text


def reject_non_json(value: Any, locator: str = "$") -> None:
    """Refuse NaN, Infinity and anything JSON cannot round-trip.

    ``json.dumps`` accepts NaN and Infinity by default and emits tokens no other
    parser accepts, so a digest computed over them is not reproducible.  A digest
    that is not reproducible cannot bind anything.
    """

    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise CommitmentIntegrityError(f"{locator}: mapping keys must be strings")
            reject_non_json(value[key], f"{locator}.{key}")
        return
    if isinstance(value, list | tuple):
        for index, child in enumerate(value):
            reject_non_json(child, f"{locator}[{index}]")
        return
    if isinstance(value, bool) or value is None or isinstance(value, str | int):
        return
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise CommitmentIntegrityError(f"{locator}: NaN and Infinity cannot be committed")
        return
    raise CommitmentIntegrityError(f"{locator}: {type(value).__name__} is not JSON-serialisable")


def _digest(body: dict[str, Any]) -> str:
    reject_non_json(body)
    return sha256_json(body)


def _require_kind(receipt: Any, expected: str) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise CommitmentIntegrityError(f"expected a {expected} receipt object")
    kind = _text(receipt.get("receipt_kind"))
    if kind != expected:
        raise CommitmentIntegrityError(
            f"expected a {expected!r} receipt, got {kind or '<none>'!r}"
        )
    return receipt


def _require_fields(receipt: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = sorted(field for field in fields if field not in receipt)
    if missing:
        raise CommitmentIntegrityError(f"the {label} receipt is missing {missing}")


def _canonical_role(value: Any) -> str:
    """Normalise through the canonical role system, refusing loose aliases.

    A receipt is machine-written, so its role field is expected to be the
    canonical enum already.  Accepting ``reviewer-a`` here would let two spellings
    produce two different committed identities for one person.
    """

    try:
        canonical = normalize_role(value)
    except RoleError as error:
        raise CommitmentIntegrityError(str(error)) from error
    if _text(value) != canonical:
        raise CommitmentIntegrityError(
            f"committed evidence must carry the canonical role {canonical!r}, not {value!r}"
        )
    return canonical


def _canonical_rows(
    receipt: dict[str, Any], columns: tuple[str, ...], label: str
) -> dict[str, dict[str, str]]:
    judgements = receipt.get("judgements")
    if not isinstance(judgements, dict) or not judgements:
        raise CommitmentIntegrityError(f"the {label} receipt carries no parsed judgements")
    rows: dict[str, dict[str, str]] = {}
    for raw_id, row in judgements.items():
        item_id = _text(raw_id)
        if not item_id:
            raise CommitmentIntegrityError(f"the {label} receipt carries an empty item id")
        if item_id in rows:
            raise CommitmentIntegrityError(
                f"the {label} receipt carries duplicate rows for {item_id}"
            )
        if not isinstance(row, dict):
            raise CommitmentIntegrityError(f"the {label} row for {item_id} is not an object")
        missing = sorted(column for column in columns if column not in row)
        if missing:
            raise CommitmentIntegrityError(
                f"the {label} row for {item_id} is missing columns {missing}"
            )
        unexpected = sorted(set(row) - set(columns))
        if unexpected:
            raise CommitmentIntegrityError(
                f"the {label} row for {item_id} carries unknown columns {unexpected}"
            )
        rows[item_id] = {column: _text(row[column]) for column in columns}
    return rows


def canonical_stage1_judgements_digest(receipt: dict[str, Any]) -> str:
    """Deterministic digest of one reviewer's committed Stage-1 content.

    Covers every parsed cell — notes and confidence included — plus the package,
    declaration, qualification and payload bindings the receipt asserts.  Keeping
    the payload hash *inside* this digest is what defeats the confirmed exploit:
    retaining the original ``submission_sha256`` while editing a judgement changes
    the digest anyway.
    """

    _require_kind(receipt, "stage1_submission")
    _require_fields(
        receipt,
        (
            "reviewer_role",
            "package_sha256",
            "submission_sha256",
            "qualification_receipt_sha256",
            "declaration_sha256",
            "row_count",
            "judgements",
            "validation",
        ),
        "Stage-1 submission",
    )
    rows = _canonical_rows(receipt, REVIEW_FORM_COLUMNS, "Stage-1 submission")
    row_count = receipt["row_count"]
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count != len(rows):
        raise CommitmentIntegrityError(
            "the Stage-1 submission receipt declares a row count that does not match its rows"
        )
    validation = receipt["validation"]
    if not isinstance(validation, dict):
        raise CommitmentIntegrityError("the Stage-1 submission validation block is malformed")
    return _digest(
        {
            "digest_kind": _STAGE1_JUDGEMENTS_DIGEST,
            "reviewer_role": _canonical_role(receipt["reviewer_role"]),
            "columns": list(REVIEW_FORM_COLUMNS),
            "package_sha256": _hex64(receipt["package_sha256"], "package_sha256"),
            "payload_sha256": _hex64(receipt["submission_sha256"], "submission_sha256"),
            "qualification_receipt_sha256": _hex64(
                receipt["qualification_receipt_sha256"], "qualification_receipt_sha256"
            ),
            "declaration_sha256": _hex64(receipt["declaration_sha256"], "declaration_sha256"),
            "row_count": row_count,
            "reviewer_item_ids": sorted(rows),
            "validation": {key: bool(value) for key, value in sorted(validation.items())},
            "judgements": rows,
        }
    )


def canonical_stage2_judgements_digest(receipt: dict[str, Any]) -> str:
    """Deterministic digest of one reviewer's committed Stage-2 content."""

    _require_kind(receipt, "stage2_submission")
    _require_fields(
        receipt,
        (
            "reviewer_role",
            "form_schema_version",
            "acceptance_policy_version",
            "declaration_sha256",
            "submission_sha256",
            "stage2_issuance_sha256",
            "stage2_package_sha256",
            "judgements",
            "validation",
            "form_complete",
            "blocking_value_count",
            "substantively_accepted_without_adjudication",
        ),
        "Stage-2 submission",
    )
    rows = _canonical_rows(receipt, STAGE2_FORM_COLUMNS, "Stage-2 submission")
    validation = receipt["validation"]
    if not isinstance(validation, dict):
        raise CommitmentIntegrityError("the Stage-2 submission validation block is malformed")
    return _digest(
        {
            "digest_kind": _STAGE2_JUDGEMENTS_DIGEST,
            "reviewer_role": _canonical_role(receipt["reviewer_role"]),
            "columns": list(STAGE2_FORM_COLUMNS),
            "form_schema_version": _text(receipt["form_schema_version"]),
            "acceptance_policy_version": _text(receipt["acceptance_policy_version"]),
            "declaration_sha256": _hex64(receipt["declaration_sha256"], "declaration_sha256"),
            "payload_sha256": _hex64(receipt["submission_sha256"], "submission_sha256"),
            "stage2_issuance_sha256": _hex64(
                receipt["stage2_issuance_sha256"], "stage2_issuance_sha256"
            ),
            "stage2_package_sha256": _hex64(
                receipt["stage2_package_sha256"], "stage2_package_sha256"
            ),
            "reviewer_item_ids": sorted(rows),
            "validation": {key: bool(value) for key, value in sorted(validation.items())},
            "form_complete": bool(receipt["form_complete"]),
            "blocking_value_count": int(receipt["blocking_value_count"]),
            "substantively_accepted_without_adjudication": bool(
                receipt["substantively_accepted_without_adjudication"]
            ),
            "judgements": rows,
        }
    )


def canonical_declaration_digest(receipt: dict[str, Any]) -> str:
    """Deterministic digest of a reviewer declaration receipt."""

    _require_kind(receipt, "reviewer_declaration")
    _require_fields(
        receipt,
        (
            "reviewer_role",
            "declaration_version",
            "declaration_sha256",
            "stage1_package_hash",
            "qualification_package_hash",
        ),
        "reviewer declaration",
    )
    body = {
        key: value
        for key, value in receipt.items()
        if key not in (*_SELF_REFERENTIAL_FIELDS, *_SEALING_FIELDS)
    }
    return _digest(
        {
            "digest_kind": _DECLARATION_DIGEST,
            "reviewer_role": _canonical_role(receipt["reviewer_role"]),
            "declaration_sha256": _hex64(receipt["declaration_sha256"], "declaration_sha256"),
            "content": body,
        }
    )


def canonical_qualification_digest(receipt: dict[str, Any]) -> str:
    """Deterministic digest of a private-qualification receipt."""

    _require_kind(receipt, "reviewer_qualification")
    _require_fields(
        receipt,
        (
            "reviewer_role",
            "qualification_version",
            "reviewer_pseudonym_sha256",
            "declaration_sha256",
            "qualification_package_hash",
            "rate",
            "threshold",
            "qualified",
            "item_count",
            "correct_count",
        ),
        "reviewer qualification",
    )
    body = {
        key: value
        for key, value in receipt.items()
        if key not in (*_SELF_REFERENTIAL_FIELDS, *_SEALING_FIELDS)
    }
    return _digest(
        {
            "digest_kind": _QUALIFICATION_DIGEST,
            "reviewer_role": _canonical_role(receipt["reviewer_role"]),
            "qualification_version": _text(receipt["qualification_version"]),
            "content": body,
        }
    )


def canonical_queue_digest(receipt: dict[str, Any]) -> str:
    """Deterministic digest of a disagreement queue's disputed content.

    Dispute order is scientifically meaningful — the queue is the ordered work
    list an adjudicator is handed — so it is preserved rather than sorted away.
    """

    if not isinstance(receipt, dict):
        raise CommitmentIntegrityError("expected a disagreement queue object")
    stage = _text(receipt.get("stage"))
    if stage not in (STAGE1, STAGE2):
        raise CommitmentIntegrityError(f"unknown disagreement queue stage {stage!r}")
    _require_fields(
        receipt,
        ("schema_version", "pair_count", "disputed_pair_count", "disputed_dimension_count", "disputes"),
        f"{stage} disagreement queue",
    )
    disputes = receipt["disputes"]
    if not isinstance(disputes, list):
        raise CommitmentIntegrityError(f"the {stage} disagreement queue disputes are malformed")
    seen: set[str] = set()
    canonical: list[dict[str, Any]] = []
    for row in disputes:
        if not isinstance(row, dict):
            raise CommitmentIntegrityError(f"a {stage} dispute row is malformed")
        key = f"{_text(row.get('pair_id'))}::{_text(row.get('dimension'))}"
        if key in seen:
            raise CommitmentIntegrityError(f"the {stage} queue disputes {key} twice")
        seen.add(key)
        canonical.append(
            {
                "stage": stage,
                "pair_id": _text(row.get("pair_id")),
                "dimension": _text(row.get("dimension")),
                "applicable": bool(row.get("applicable", True)),
                "reasons": sorted(_text(reason) for reason in row.get("reasons", [])),
                "reviewer_values": {
                    _canonical_role(role): _text(value)
                    for role, value in sorted(dict(row.get("reviewer_values", {})).items())
                },
            }
        )
    if len(canonical) != int(receipt["disputed_dimension_count"]):
        raise CommitmentIntegrityError(
            f"the {stage} queue declares a dispute count that does not match its disputes"
        )
    return _digest(
        {
            "digest_kind": _QUEUE_DIGEST,
            "stage": stage,
            "queue_schema_version": _text(receipt["schema_version"]),
            "pair_count": int(receipt["pair_count"]),
            "disputed_pair_count": int(receipt["disputed_pair_count"]),
            "disputed_dimension_count": int(receipt["disputed_dimension_count"]),
            "disputes": canonical,
        }
    )


def canonical_adjudication_digest(receipt: dict[str, Any]) -> str:
    """Deterministic digest of an adjudication's decided content.

    Every disputed item, its final value, its rationale and its evidence
    reference are inside, so a changed rationale is as detectable as a changed
    verdict.
    """

    if not isinstance(receipt, dict):
        raise CommitmentIntegrityError("expected an adjudication receipt object")
    stage = _text(receipt.get("stage"))
    if stage not in (STAGE1, STAGE2):
        raise CommitmentIntegrityError(f"unknown adjudication stage {stage!r}")
    _require_kind(receipt, f"{stage}_adjudication")
    _require_fields(
        receipt,
        (
            "schema_version",
            "disagreement_queue_sha256",
            "adjudicator_package_sha256",
            "adjudicator_assignment_sha256",
            "adjudicator_pseudonym_sha256",
            "decisions",
            "decision_count",
            "disputed_dimension_count",
            "excluded_pair_ids",
        ),
        f"{stage} adjudication",
    )
    decisions = receipt["decisions"]
    if not isinstance(decisions, list):
        raise CommitmentIntegrityError(f"the {stage} adjudication decisions are malformed")
    seen: set[str] = set()
    canonical: list[dict[str, Any]] = []
    for row in decisions:
        if not isinstance(row, dict):
            raise CommitmentIntegrityError(f"a {stage} adjudication decision is malformed")
        key = f"{_text(row.get('pair_id'))}::{_text(row.get('dimension'))}"
        if key in seen:
            raise CommitmentIntegrityError(f"the {stage} adjudication decides {key} twice")
        seen.add(key)
        canonical.append(
            {
                "stage": stage,
                "pair_id": _text(row.get("pair_id")),
                "dimension": _text(row.get("dimension")),
                "final_value": _text(row.get("final_value")),
                "rationale": _text(row.get("rationale")),
                "evidence_reference": _text(row.get("evidence_reference")),
                "confidence": _text(row.get("confidence")),
                "exclude_item": _text(row.get("exclude_item")),
                "resolves_to_accepting_value": bool(row.get("resolves_to_accepting_value")),
                "dispute_reasons": sorted(_text(reason) for reason in row.get("dispute_reasons", [])),
            }
        )
    if len(canonical) != int(receipt["decision_count"]):
        raise CommitmentIntegrityError(
            f"the {stage} adjudication declares a decision count that does not match its decisions"
        )
    return _digest(
        {
            "digest_kind": _ADJUDICATION_DIGEST,
            "stage": stage,
            "adjudication_schema_version": _text(receipt["schema_version"]),
            "disagreement_queue_sha256": _hex64(
                receipt["disagreement_queue_sha256"], "disagreement_queue_sha256"
            ),
            "adjudicator_package_sha256": _hex64(
                receipt["adjudicator_package_sha256"], "adjudicator_package_sha256"
            ),
            "adjudicator_assignment_sha256": _hex64(
                receipt["adjudicator_assignment_sha256"], "adjudicator_assignment_sha256"
            ),
            "adjudicator_pseudonym_sha256": _hex64(
                receipt["adjudicator_pseudonym_sha256"], "adjudicator_pseudonym_sha256"
            ),
            "disputed_dimension_count": int(receipt["disputed_dimension_count"]),
            "decision_count": int(receipt["decision_count"]),
            "excluded_pair_ids": sorted(_text(item) for item in receipt["excluded_pair_ids"]),
            "decisions": canonical,
        }
    )


def canonical_assignment_registry_digest(registry: dict[str, Any]) -> str:
    """Deterministic digest of the reviewer assignment registry's bindings.

    Pseudonyms are hashed rather than carried, so the digest can travel into a
    publishable receipt without naming anyone.
    """

    if not isinstance(registry, dict):
        raise CommitmentIntegrityError("expected an assignment registry object")
    _require_fields(registry, ("schema_version", "packet_version", "assignments"), "assignment registry")
    assignments = registry["assignments"]
    if not isinstance(assignments, dict):
        raise CommitmentIntegrityError("the assignment registry assignments are malformed")
    canonical: dict[str, Any] = {}
    for role, assignment in sorted(assignments.items()):
        if not isinstance(assignment, dict):
            raise CommitmentIntegrityError(f"the assignment for {role} is malformed")
        canonical[_canonical_role(role)] = {
            "reviewer_role": _canonical_role(assignment.get("reviewer_role")),
            "reviewer_pseudonym_sha256": sha256_json(_text(assignment.get("reviewer_pseudonym"))),
            "stage1_package_role": _text(assignment.get("stage1_package_role")) or None,
            "stage1_package_hash": _text(assignment.get("stage1_package_hash")).casefold() or None,
            "qualification_package_hash": _text(
                assignment.get("qualification_package_hash")
            ).casefold()
            or None,
            "stage1_opaque_id_namespace": _text(assignment.get("stage1_opaque_id_namespace")) or None,
            "stage2_opaque_id_namespace": _text(assignment.get("stage2_opaque_id_namespace")) or None,
            "assignment_status": _text(assignment.get("assignment_status")),
            "assignment_sha256": _text(assignment.get("assignment_sha256")),
        }
    return _digest(
        {
            "digest_kind": _REGISTRY_DIGEST,
            "registry_schema_version": _text(registry["schema_version"]),
            "packet_version": _text(registry["packet_version"]),
            "assignments": canonical,
        }
    )


def receipt_content_sha256(receipt: dict[str, Any]) -> str:
    """Recompute a receipt's own content hash rather than trusting the field."""

    if not isinstance(receipt, dict):
        raise CommitmentIntegrityError("expected a receipt object")
    body = {key: value for key, value in receipt.items() if key not in _SELF_REFERENTIAL_FIELDS}
    return sha256_json(body)


def receipt_file_sha256(path: Path) -> str:
    """Hash the exact bytes of a receipt file, refusing a symlinked path."""

    resolved = assert_regular_file(path)
    return sha256_bytes(resolved.read_bytes())


# --------------------------------------------------------------------------
# filesystem hardening
# --------------------------------------------------------------------------


def assert_regular_file(path: Path) -> Path:
    """Refuse a symlink, a directory, or anything that is not a regular file."""

    if path.is_symlink():
        raise CommitmentIntegrityError(
            f"refusing to read {path.name}: a private review artifact must not be a symbolic link"
        )
    if not path.is_file():
        raise CommitmentIntegrityError(f"required private review artifact is missing: {path.name}")
    return path


def assert_contained(path: Path, *, root: Path) -> Path:
    """Refuse a path that escapes the private root, by symlink or by ``..``."""

    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise CommitmentIntegrityError(
            f"refusing to use {path.name}: it resolves outside the private review root"
        )
    return resolved


def assert_private_mode(path: Path, *, require_private: bool) -> None:
    """Refuse group- or world-readable production private files.

    ``require_private`` is off for fixture workspaces, whose artifacts are
    worthless by construction, and off on platforms without POSIX modes.
    """

    if not require_private or os.name != "posix":
        return
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise CommitmentIntegrityError(
            f"refusing to use {path.name}: it is group- or world-accessible (mode {mode:04o})"
        )
    parent_mode = stat.S_IMODE(path.parent.stat().st_mode)
    if parent_mode & 0o002:
        raise CommitmentIntegrityError(
            f"refusing to use {path.name}: its directory is world-writable (mode {parent_mode:04o})"
        )


def read_private_json(path: Path, *, root: Path, require_private: bool = False) -> dict[str, Any]:
    """Read a private JSON artifact through every path defence."""

    assert_regular_file(path)
    assert_contained(path, root=root)
    assert_private_mode(path, require_private=require_private)
    return read_json(path)


def write_private_json(
    path: Path, value: Any, *, mode: int = 0o600, allow_replace: bool = False
) -> None:
    """Write atomically: temp file in the same directory, fsync, then rename.

    A crash therefore leaves either the previous file or the complete new one,
    never a half-written artifact that verifies as valid.  ``allow_replace`` is
    off by default because an immutable artifact is never replaced.
    """

    if path.is_symlink():
        raise CommitmentIntegrityError(
            f"refusing to write {path.name}: the target is a symbolic link"
        )
    if path.exists() and not allow_replace:
        raise CommitmentIntegrityError(
            f"refusing to overwrite {path.name}: committed review evidence is write-once"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp-{secrets.token_hex(8)}"
    try:
        payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _fsync_directory(directory: Path) -> None:
    """Best-effort directory fsync; not every platform or filesystem allows it."""

    try:
        handle = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(handle)
    except OSError:
        pass
    finally:
        os.close(handle)


# --------------------------------------------------------------------------
# immutable submission snapshots
# --------------------------------------------------------------------------


def snapshot_directory(receipts_root: Path, stage: str) -> Path:
    if stage not in SNAPSHOT_DIRNAMES:
        raise CommitmentIntegrityError(f"unknown snapshot stage {stage!r}")
    return receipts_root / SNAPSHOT_DIRNAMES[stage]


def snapshot_filename(role: str, stage: str) -> str:
    """``REVIEWER_A.stage1_submission.json`` — canonical role, never an alias."""

    return f"{_canonical_role(role)}.{stage}_submission.json"


def snapshot_exists(receipts_root: Path, stage: str) -> bool:
    return (snapshot_directory(receipts_root, stage) / MANIFEST_FILENAME).is_file()


def create_submission_snapshot(
    *,
    receipts_root: Path,
    authority: Authority,
    stage: str,
    live_paths: dict[str, Path],
    receipts: dict[str, dict[str, Any]],
    reviewer_bindings: dict[str, dict[str, Any]],
    manifest_bindings: dict[str, Any],
    digest_for: Callable[[dict[str, Any]], str] | None = None,
) -> dict[str, Any]:
    """Freeze the verified receipt bytes into a write-once sealed snapshot.

    The caller has already verified authenticity, assignment, declaration,
    qualification, package and coverage; this function is responsible only for
    making that verified state permanent and unambiguous.  It builds the whole
    snapshot in a temporary sibling directory and renames it into place, so an
    interrupted commitment leaves no partially populated snapshot behind.
    """

    if stage not in SNAPSHOT_SCHEMA_VERSIONS:
        raise CommitmentIntegrityError(f"unknown snapshot stage {stage!r}")
    if set(receipts) != set(REVIEW_ROLES) or set(live_paths) != set(REVIEW_ROLES):
        raise CommitmentIntegrityError(
            f"a committed {stage} snapshot requires exactly one receipt per reviewer role"
        )
    directory = snapshot_directory(receipts_root, stage)
    if directory.exists():
        raise CommitmentIntegrityError(
            f"a committed {stage} snapshot already exists; committed review evidence is "
            "write-once. Start a fresh workspace rather than recommitting."
        )

    # The production digests bind the declaration, qualification and issuance
    # hashes a production receipt must carry.  A caller whose evidence class does
    # not have those bindings supplies its own digest, which must cover the same
    # scientific content plus whatever provenance that class does bind.
    digest_for = digest_for or {
        STAGE1: canonical_stage1_judgements_digest,
        STAGE2: canonical_stage2_judgements_digest,
    }[stage]

    temporary = receipts_root / f".{SNAPSHOT_DIRNAMES[stage]}.tmp-{secrets.token_hex(8)}"
    temporary.mkdir(parents=True)
    temporary.chmod(0o700)
    try:
        reviewers: dict[str, Any] = {}
        for role in sorted(REVIEW_ROLES):
            canonical = _canonical_role(role)
            source = assert_regular_file(live_paths[role])
            raw = source.read_bytes()
            receipt = receipts[role]
            if _canonical_role(receipt.get("reviewer_role")) != canonical:
                raise CommitmentIntegrityError(
                    f"the {stage} receipt filed under {canonical} declares another role"
                )
            if receipt_is_fixture(receipt) and authority.is_production:
                raise CommitmentIntegrityError(
                    f"refusing to commit a synthetic {stage} receipt as production evidence"
                )
            if json.loads(raw.decode()) != receipt:
                raise CommitmentIntegrityError(
                    f"the {stage} receipt on disk no longer matches the verified receipt"
                )
            filename = snapshot_filename(canonical, stage)
            target = temporary / filename
            target.write_bytes(raw)
            target.chmod(0o600)
            reviewers[canonical] = {
                **dict(reviewer_bindings[role]),
                "reviewer_role": canonical,
                "snapshot_filename": filename,
                "snapshot_receipt_file_sha256": sha256_bytes(raw),
                "submission_receipt_sha256": receipt_content_sha256(receipt),
                "canonical_judgements_sha256": digest_for(receipt),
            }

        manifest_payload = {
            "receipt_kind": f"committed_{stage}_snapshot_manifest",
            "manifest_schema_version": SNAPSHOT_SCHEMA_VERSIONS[stage],
            "stage": stage,
            "reviewer_roles": sorted(REVIEW_ROLES),
            "authority_namespace": authority.namespace,
            "snapshot_created_at": datetime.now(UTC).isoformat(),
            "reviewers": reviewers,
            **dict(manifest_bindings),
        }
        reject_non_json(manifest_payload)
        manifest = seal_receipt(authority, manifest_payload)
        write_private_json(temporary / MANIFEST_FILENAME, manifest)
        _fsync_directory(temporary)
        if directory.exists():  # pragma: no cover - lost a race with another commit
            raise CommitmentIntegrityError(f"a committed {stage} snapshot already exists")
        os.rename(temporary, directory)
        _fsync_directory(receipts_root)
    finally:
        if temporary.exists():
            for child in temporary.iterdir():
                child.unlink()
            temporary.rmdir()
    return manifest


def read_snapshot_manifest(
    receipts_root: Path, *, authority: Authority, stage: str, require_private: bool = False
) -> dict[str, Any]:
    """Read and authenticate a snapshot manifest, or fail closed."""

    directory = snapshot_directory(receipts_root, stage)
    path = directory / MANIFEST_FILENAME
    if not path.is_file():
        raise CommitmentIntegrityError(
            f"no committed {stage} snapshot exists; the workflow cannot proceed on mutable "
            "submission receipts"
        )
    manifest = read_private_json(path, root=receipts_root, require_private=require_private)
    if manifest.get("manifest_schema_version") != SNAPSHOT_SCHEMA_VERSIONS[stage]:
        raise CommitmentIntegrityError(
            f"the committed {stage} snapshot manifest declares "
            f"{manifest.get('manifest_schema_version')!r}, not "
            f"{SNAPSHOT_SCHEMA_VERSIONS[stage]!r}"
        )
    if authority.is_production and receipt_is_fixture(manifest):
        raise CommitmentIntegrityError(
            f"the committed {stage} snapshot manifest is a synthetic test fixture"
        )
    try:
        verify_receipt(authority, manifest)
    except ReceiptError as error:
        raise CommitmentIntegrityError(
            f"the committed {stage} snapshot manifest failed authentication: {error}"
        ) from error
    if manifest.get("authority_namespace") != authority.namespace:
        raise CommitmentIntegrityError(
            f"the committed {stage} snapshot manifest belongs to another authority namespace"
        )
    if sorted(manifest.get("reviewer_roles") or ()) != sorted(REVIEW_ROLES):
        raise CommitmentIntegrityError(
            f"the committed {stage} snapshot manifest does not name exactly two reviewer roles"
        )
    if sorted(dict(manifest.get("reviewers") or {})) != sorted(REVIEW_ROLES):
        raise CommitmentIntegrityError(
            f"the committed {stage} snapshot manifest does not carry exactly two reviewer entries"
        )
    return manifest


def read_snapshot_receipts(
    receipts_root: Path,
    *,
    authority: Authority,
    stage: str,
    manifest: dict[str, Any],
    live_paths: dict[str, Path] | None = None,
    require_private: bool = False,
    digest_for: Callable[[dict[str, Any]], str] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, bool]]:
    """Read the frozen receipts and re-derive every digest the manifest binds.

    ``live_paths`` is checked but never *used*: a live receipt that no longer
    matches the snapshot is reported as a conflict rather than quietly ignored,
    because silence would let tampering look like a no-op.

    ``digest_for`` must be the same function the snapshot was created with;
    passing a different one makes every judgement digest mismatch, which is
    reported as a failed check rather than silently accepted.
    """

    directory = snapshot_directory(receipts_root, stage)
    digest_for = digest_for or {
        STAGE1: canonical_stage1_judgements_digest,
        STAGE2: canonical_stage2_judgements_digest,
    }[stage]
    receipts: dict[str, dict[str, Any]] = {}
    checks: dict[str, bool] = {}
    file_hashes_match = True
    content_hashes_match = True
    judgement_hashes_match = True
    payload_hashes_match = True
    roles_bound = True
    live_consistent = True

    for role in sorted(REVIEW_ROLES):
        binding = dict(manifest["reviewers"][role])
        path = directory / str(binding["snapshot_filename"])
        assert_regular_file(path)
        assert_contained(path, root=receipts_root)
        assert_private_mode(path, require_private=require_private)
        raw = path.read_bytes()
        if sha256_bytes(raw) != binding["snapshot_receipt_file_sha256"]:
            file_hashes_match = False
        receipt = json.loads(raw.decode())
        if not isinstance(receipt, dict):
            raise CommitmentIntegrityError(f"the committed {stage} receipt for {role} is malformed")
        if authority.is_production and receipt_is_fixture(receipt):
            raise CommitmentIntegrityError(
                f"the committed {stage} receipt for {role} is a synthetic test fixture"
            )
        try:
            verify_receipt(authority, receipt)
        except ReceiptError as error:
            raise CommitmentIntegrityError(
                f"the committed {stage} receipt for {role} failed authentication: {error}"
            ) from error
        if receipt_content_sha256(receipt) != binding["submission_receipt_sha256"]:
            content_hashes_match = False
        if digest_for(receipt) != binding["canonical_judgements_sha256"]:
            judgement_hashes_match = False
        if str(receipt.get("submission_sha256")) != str(binding["submission_payload_sha256"]):
            payload_hashes_match = False
        if _canonical_role(receipt.get("reviewer_role")) != role:
            roles_bound = False
        if live_paths and role in live_paths:
            live = live_paths[role]
            if live.is_symlink() or (live.is_file() and sha256_bytes(live.read_bytes()) != sha256_bytes(raw)):
                live_consistent = False
        receipts[role] = receipt

    checks[f"{stage}_snapshot_receipt_hashes_match_manifest"] = file_hashes_match
    checks[f"{stage}_receipt_content_hashes_match_manifest"] = content_hashes_match
    checks[f"{stage}_judgement_hashes_match_manifest"] = judgement_hashes_match
    checks[f"{stage}_payload_hashes_match_manifest"] = payload_hashes_match
    checks[f"{stage}_snapshot_roles_bound"] = roles_bound
    checks[f"{stage}_live_receipts_not_conflicting"] = live_consistent
    return receipts, checks


def manifest_sha256(manifest: dict[str, Any]) -> str:
    """The manifest's own recomputed content hash."""

    return receipt_content_sha256(manifest)


__all__ = [
    "MANIFEST_FILENAME",
    "RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS",
    "REVIEW_INPUT_GRAPH_SCHEMA_VERSION",
    "SNAPSHOT_DIRNAMES",
    "SNAPSHOT_SCHEMA_VERSIONS",
    "STAGE1",
    "STAGE1_COMMITMENT_SCHEMA_VERSION",
    "STAGE1_SNAPSHOT_SCHEMA_VERSION",
    "STAGE2",
    "STAGE2_SNAPSHOT_SCHEMA_VERSION",
    "CommitmentIntegrityError",
    "assert_contained",
    "assert_private_mode",
    "assert_regular_file",
    "canonical_adjudication_digest",
    "canonical_assignment_registry_digest",
    "canonical_declaration_digest",
    "canonical_qualification_digest",
    "canonical_queue_digest",
    "canonical_stage1_judgements_digest",
    "canonical_stage2_judgements_digest",
    "create_submission_snapshot",
    "manifest_sha256",
    "read_private_json",
    "read_snapshot_manifest",
    "read_snapshot_receipts",
    "receipt_content_sha256",
    "receipt_file_sha256",
    "reject_non_json",
    "snapshot_directory",
    "snapshot_exists",
    "snapshot_filename",
    "write_private_json",
]
