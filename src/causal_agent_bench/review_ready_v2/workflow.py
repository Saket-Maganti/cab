"""The complete two-stage human-review workflow, end to end.

Every step is a gate.  Stage 2 stays sealed until a validated Stage-1 commitment
exists, C10 stays ``C10_PENDING_GENUINE_REVIEW`` until genuine validated review
data exists, the reviewed slice cannot be locked before C10 passes, and model
execution cannot be authorized before the slice is locked.

Authenticity is not a flag.  A workspace does not decide whether its artifacts
are genuine — the *authority* that sealed each receipt does, and the production
authority requires an external coordinator key that no synthetic run possesses.
Fixture receipts are sealed by a deliberately public authority, stamped
``SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE``, and fail production verification
on origin, on schema, and on MAC.  There is no boolean anywhere that converts one
into the other.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.adjudication import (
    STAGE1,
    STAGE2,
    AdjudicationError,
    build_stage1_queue,
    build_stage2_queue,
    validate_adjudication,
)
from causal_agent_bench.review_ready_v2.adjudication_packages import (
    AdjudicationPackageError,
    verify_package_binding,
)
from causal_agent_bench.review_ready_v2.assignments import (
    AssignmentError,
    assignment_for_role,
    load_assignments,
    verify_assignment,
    verify_registry_complete,
)
from causal_agent_bench.review_ready_v2.commitment_integrity import (
    RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS,
    REVIEW_INPUT_GRAPH_SCHEMA_VERSION,
    STAGE1_COMMITMENT_SCHEMA_VERSION,
    CommitmentIntegrityError,
    assert_contained,
    assert_private_mode,
    assert_regular_file,
    canonical_adjudication_digest,
    canonical_assignment_registry_digest,
    canonical_declaration_digest,
    canonical_qualification_digest,
    canonical_queue_digest,
    canonical_stage1_judgements_digest,
    canonical_stage2_judgements_digest,
    create_submission_snapshot,
    manifest_sha256,
    read_snapshot_manifest,
    read_snapshot_receipts,
    receipt_content_sha256,
    snapshot_directory,
    snapshot_exists,
    write_private_json,
)
from causal_agent_bench.review_ready_v2.common import (
    read_json,
    sha256_bytes,
    sha256_json,
)
from causal_agent_bench.review_ready_v2.declarations import (
    DECLARATION_VERSION,
    DeclarationError,
    declaration_blocks_qualification,
    parse_declaration,
)
from causal_agent_bench.review_ready_v2.final_records import build_final_records
from causal_agent_bench.review_ready_v2.qualification import (
    MIN_QUALIFICATION_RATE,
    QUALIFICATION_SCHEMA_VERSION,
    QualificationError,
    enforce_active_qualification,
    score_qualification,
)
from causal_agent_bench.review_ready_v2.receipts import (
    Authority,
    ReceiptError,
    coordinator_authority,
    fixture_authority,
    receipt_is_fixture,
    seal_receipt,
    verify_receipt,
)
from causal_agent_bench.review_ready_v2.registry import enforce_active_packet
from causal_agent_bench.review_ready_v2.roles import (
    ADJUDICATOR,
    REVIEW_ROLES,
    REVIEWER_A,
    REVIEWER_B,
    RoleError,
    normalize_role,
)
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_DIMENSIONS, REVIEW_FORM_COLUMNS
from causal_agent_bench.review_ready_v2.stage2 import (
    STAGE2_ACCEPTANCE_POLICY_VERSION,
    STAGE2_FORM_COLUMNS,
    STAGE2_FORM_SCHEMA_VERSION,
    STAGE2_SUBSTANTIVE_DIMENSIONS,
    validate_stage2_submission,
)
from causal_agent_bench.review_ready_v2.stage2_issuance import (
    STAGE2_ISSUANCE_SCHEMA_VERSION,
    Stage2IssuanceError,
    build_stage2_issuance,
    verify_stage2_issuance,
)

WORKFLOW_SCHEMA_VERSION = "cab_review_ready_v2_two_stage_workflow_v3"

#: Workflow schemas whose review evidence the active gates refuse.  ``v2`` bound
#: only the reviewer's CSV payload hash at Stage-1 commitment, so a resealed
#: receipt could change the parsed judgements without invalidating anything
#: downstream.  Evidence recorded under it is development-only and cannot be
#: migrated; genuine review starts under ``v3`` or not at all.
RETIRED_WORKFLOW_SCHEMA_VERSIONS: tuple[str, ...] = (
    "cab_review_ready_v2_two_stage_workflow_v1",
    "cab_review_ready_v2_two_stage_workflow_v2",
)

#: Receipts that seal a completed one-way state transition.  Once written they
#: are never rewritten in place; a correction requires a fresh workspace under a
#: superseding workflow version.  ``c10_report`` is deliberately absent: it is a
#: derived report a coordinator may recompute to see what is still failing, and
#: it becomes immutable the moment a slice lock binds it.
_SEALED_RECEIPT_PREFIXES: tuple[str, ...] = (
    "declaration_",
    "qualification_",
    "stage1_submission_",
    "stage2_issuance_",
    "stage2_submission_",
)

_SEALED_RECEIPT_NAMES: frozenset[str] = frozenset(
    {
        "stage1_commitment",
        "stage2_unlock",
        "stage1_disagreement_queue",
        "stage2_disagreement_queue",
        "stage1_adjudicator_package",
        "stage2_adjudicator_package",
        "stage1_adjudication",
        "stage2_adjudication",
        "agreement",
        "final_adjudicated_records",
        "exclusion_register",
        "slice_lock",
        "execution_authorization",
    }
)

#: Stage-1 dimensions whose agreement is gated.
GATING_DIMENSIONS = (
    "clean_solvable",
    "clean_evidence_sufficient",
    "goal_preserved",
    "single_factor_isolation",
    "preserved_invariants_hold",
    "primitive_evidence_adequate",
    "response_space_structurally_valid",
    "exclude_item",
)

ENUMS = {name: set(values) for name, values, _ in REVIEW_DIMENSIONS if values}

#: The bindings a review artifact must carry before it can count as genuine.
REQUIRED_EVIDENCE_BINDINGS: tuple[str, ...] = (
    "active_non_retired_packet",
    "valid_reviewer_assignment",
    "valid_declaration_receipt",
    "valid_private_qualification_receipt",
    "correct_package_hash",
    "correct_reviewer_namespace",
    "sealed_stage2_issuance_receipt",
    "complete_submission",
    "non_fixture_artifact_origin",
    "production_schema_version",
    "content_hash_intact",
    "coordinator_acceptance_receipt",
)


class WorkflowError(RuntimeError):
    """A workflow gate refused to proceed."""


def parse_review_csv(payload: bytes, columns: tuple[str, ...]) -> dict[str, dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode()))
    if tuple(reader.fieldnames or ()) != columns:
        raise WorkflowError("the submitted form does not match the issued column layout")
    rows: dict[str, dict[str, str]] = {}
    for row in reader:
        item_id = str(row["reviewer_item_id"]).strip()
        if not item_id:
            continue
        if item_id in rows:
            raise WorkflowError(f"duplicate row for {item_id}")
        rows[item_id] = {key: str(value or "").strip() for key, value in row.items()}
    return rows


def validate_stage1_submission(
    rows: dict[str, dict[str, str]], expected_item_ids: list[str]
) -> dict[str, Any]:
    problems: list[dict[str, str]] = []
    missing = sorted(set(expected_item_ids) - set(rows))
    unexpected = sorted(set(rows) - set(expected_item_ids))
    for item_id, row in sorted(rows.items()):
        for name, allowed in ENUMS.items():
            value = row.get(name, "").casefold()
            if value not in allowed:
                problems.append({"reviewer_item_id": item_id, "column": name, "issue": "invalid_value"})
        if row.get("exclude_item", "").casefold() == "yes" and not row.get("notes"):
            problems.append({"reviewer_item_id": item_id, "column": "notes", "issue": "required"})
        if row.get("ambiguity_present", "").casefold() == "material" and not row.get("notes"):
            problems.append({"reviewer_item_id": item_id, "column": "notes", "issue": "required"})
        if row.get("response_space_structurally_valid", "").casefold() == "unsure" and not row.get(
            "notes"
        ):
            problems.append({"reviewer_item_id": item_id, "column": "notes", "issue": "required"})
    checks = {
        "no_missing_rows": not missing,
        "no_unexpected_rows": not unexpected,
        "no_malformed_cells": not problems,
    }
    return {
        "row_count": len(rows),
        "missing_rows": missing,
        "unexpected_rows": unexpected,
        "malformed": problems,
        "checks": checks,
        # A complete Stage-1 form is not an approval either; it is only well-formed.
        "form_complete": all(checks.values()),
        "passed": all(checks.values()),
    }


@dataclass
class ReviewWorkspace:
    """Coordinator-side workflow state under the private packet root.

    Construct through :meth:`production` or :meth:`fixture`.  ``authority``
    carries the sealing key and the artifact origin; nothing else in the class
    can change whether a receipt counts as evidence.
    """

    private_root: Path
    authority: Authority
    packet_version: str = PACKET_VERSION

    @classmethod
    def production(cls, private_root: Path, repo_root: Path) -> ReviewWorkspace:
        """Fails closed unless the external coordinator acceptance key is present."""

        return cls(private_root, coordinator_authority(repo_root))

    @classmethod
    def fixture(cls, private_root: Path) -> ReviewWorkspace:
        """A synthetic namespace whose receipts can never be genuine evidence."""

        return cls(private_root, fixture_authority())

    # -- receipt plumbing --------------------------------------------------

    @property
    def is_production(self) -> bool:
        return self.authority.is_production

    @property
    def evidence_class(self) -> str:
        return self.authority.origin

    @property
    def receipts(self) -> Path:
        directory = self.private_root / self.authority.namespace
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)
        return directory

    @staticmethod
    def _is_sealed(name: str) -> bool:
        """True when ``name`` records a completed, one-way state transition."""

        return name in _SEALED_RECEIPT_NAMES or name.startswith(_SEALED_RECEIPT_PREFIXES)

    def write(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = self.receipts / f"{name}.json"
        if self._is_sealed(name) and path.exists():
            raise WorkflowError(
                f"refusing to overwrite the sealed {name} receipt: a completed review state is "
                "write-once. Correcting it requires a fresh workspace under a superseding "
                "workflow version, not an edit in place."
            )
        if name == "c10_report" and self.has("slice_lock"):
            # C10 stays recomputable while a coordinator is still working out why
            # it fails; the moment a lock binds it, it is settled evidence.
            raise WorkflowError(
                "refusing to rewrite the C10 report after the reviewed slice was locked"
            )
        sealed = seal_receipt(self.authority, {**payload, "packet_version": self.packet_version})
        try:
            write_private_json(path, sealed, allow_replace=not self._is_sealed(name))
        except CommitmentIntegrityError as error:
            raise WorkflowError(f"receipt {name} could not be written: {error}") from error
        return sealed

    def read(self, name: str) -> dict[str, Any]:
        path = self.receipts / f"{name}.json"
        if path.is_symlink():
            raise WorkflowError(
                f"required receipt is unusable: {name}: a private review artifact must not be a "
                "symbolic link"
            )
        if not path.is_file():
            raise WorkflowError(f"required receipt is missing: {name}")
        try:
            assert_regular_file(path)
            assert_contained(path, root=self.private_root)
            assert_private_mode(path, require_private=self.is_production)
        except CommitmentIntegrityError as error:
            raise WorkflowError(f"required receipt is unusable: {name}: {error}") from error
        receipt = read_json(path)
        if self.is_production and receipt_is_fixture(receipt):
            raise WorkflowError(
                f"receipt {name} is a synthetic test fixture and cannot be used as genuine evidence"
            )
        try:
            verify_receipt(self.authority, receipt)
        except ReceiptError as error:
            raise WorkflowError(f"receipt {name} failed verification: {error}") from error
        if receipt.get("packet_version") != self.packet_version:
            raise WorkflowError(
                f"receipt {name} belongs to packet {receipt.get('packet_version')!r}, not "
                f"{self.packet_version!r}"
            )
        return receipt

    def has(self, name: str) -> bool:
        path = self.receipts / f"{name}.json"
        return path.is_file() and not path.is_symlink()

    # -- committed, immutable review evidence ------------------------------

    def snapshot_path(self, stage: str) -> Path:
        """Where this workspace's committed ``stage`` snapshot lives."""

        return snapshot_directory(self.receipts, stage)

    def has_committed_snapshot(self, stage: str) -> bool:
        return snapshot_exists(self.receipts, stage)

    def _live_submission_paths(self, stage: str) -> dict[str, Path]:
        return {
            role: self.receipts / f"{stage}_submission_{role}.json" for role in REVIEW_ROLES
        }

    # -- assignment registry ----------------------------------------------

    def assignments(self) -> dict[str, Any]:
        try:
            return load_assignments(self.private_root, packet_version=self.packet_version)
        except AssignmentError as error:
            raise WorkflowError(str(error)) from error

    def _role(self, role: str) -> str:
        try:
            return normalize_role(role)
        except RoleError as error:
            raise WorkflowError(str(error)) from error

    # -- declarations ------------------------------------------------------

    def ingest_declaration(self, role: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Record a reviewer's own declaration.  No field is supplied by us."""

        canonical = self._role(role)
        try:
            declaration = parse_declaration(payload)
        except DeclarationError as error:
            raise WorkflowError(f"reviewer declaration refused: {error}") from error
        if declaration["package_role"] != canonical:
            raise WorkflowError(
                f"the declaration was signed for {declaration['package_role']}, not {canonical}"
            )
        registry = self.assignments()
        try:
            verify_assignment(
                registry,
                role=canonical,
                reviewer_pseudonym=declaration["reviewer_pseudonym"],
                stage1_package_hash=declaration["stage1_package_hash"],
                qualification_package_hash=declaration["qualification_package_hash"],
            )
        except AssignmentError as error:
            raise WorkflowError(f"reviewer declaration refused: {error}") from error
        if self.is_production and declaration["declaration_is_synthetic"]:
            raise WorkflowError(
                "a synthetic declaration cannot be recorded in a production workspace"
            )
        return self.write(
            f"declaration_{canonical}",
            {
                "receipt_kind": "reviewer_declaration",
                "reviewer_role": canonical,
                "declaration_version": DECLARATION_VERSION,
                **declaration,
            },
        )

    def accept_declaration(
        self, role: str, *, decision: str, rationale: str
    ) -> dict[str, Any]:
        """Coordinator decision on a declaration that disclosed a conflict."""

        canonical = self._role(role)
        declaration = self.read(f"declaration_{canonical}")
        if decision not in ("ACCEPTED", "REJECTED"):
            raise WorkflowError("a coordinator declaration decision must be ACCEPTED or REJECTED")
        if not str(rationale).strip():
            raise WorkflowError("a coordinator declaration decision requires a rationale")
        return self.write(
            f"declaration_decision_{canonical}",
            {
                "receipt_kind": "coordinator_declaration_decision",
                "reviewer_role": canonical,
                "declaration_sha256": declaration["declaration_sha256"],
                "coordinator_review_decision": decision,
                "rationale": str(rationale).strip(),
            },
        )

    def _declaration_for(self, role: str) -> dict[str, Any]:
        canonical = self._role(role)
        declaration = dict(self.read(f"declaration_{canonical}"))
        if self.has(f"declaration_decision_{canonical}"):
            decision = self.read(f"declaration_decision_{canonical}")
            if decision["declaration_sha256"] != declaration["declaration_sha256"]:
                raise WorkflowError(
                    f"the coordinator decision for {canonical} was made against a different "
                    "declaration than the one on file"
                )
            declaration["coordinator_review_decision"] = decision["coordinator_review_decision"]
        blockers = declaration_blocks_qualification(declaration)
        if blockers:
            raise WorkflowError(
                f"the declaration for {canonical} cannot support qualification: {blockers}"
            )
        return declaration

    # -- qualification -----------------------------------------------------

    def ingest_qualification(
        self,
        role: str,
        submission: dict[str, dict[str, str]],
        answer_key: dict[str, Any],
        *,
        qualification_version: str = QUALIFICATION_SCHEMA_VERSION,
    ) -> dict[str, Any]:
        """Score a reviewer against their own private key.  Never logs the key."""

        canonical = self._role(role)
        try:
            enforce_active_qualification(qualification_version)
        except QualificationError as error:
            raise WorkflowError(str(error)) from error
        declaration = self._declaration_for(canonical)
        already = {
            other
            for other in REVIEW_ROLES
            if other != canonical and self.has(f"qualification_{other}")
        }
        reused = {
            other
            for other in already
            if self.read(f"qualification_{other}")["reviewer_pseudonym_sha256"]
            == sha256_json(declaration["reviewer_pseudonym"])
        }
        if reused:
            raise WorkflowError(
                f"this reviewer already holds the qualification receipt for {sorted(reused)}; "
                "one person cannot qualify as two reviewers"
            )
        try:
            result = score_qualification(
                submission, answer_key, reviewer_role=canonical, already_qualified_roles=set()
            )
        except QualificationError as error:
            raise WorkflowError(f"qualification refused: {error}") from error
        if not result["qualified"]:
            raise WorkflowError(
                f"{canonical} did not reach the {MIN_QUALIFICATION_RATE:.0%} qualification "
                "threshold; they cannot be assigned a review package"
            )
        return self.write(
            f"qualification_{canonical}",
            {
                "receipt_kind": "reviewer_qualification",
                "reviewer_role": canonical,
                "qualification_version": qualification_version,
                # The pseudonym itself stays in the private registry; the receipt
                # binds it by hash so receipts can be shown without naming anyone.
                "reviewer_pseudonym_sha256": sha256_json(declaration["reviewer_pseudonym"]),
                "declaration_sha256": declaration["declaration_sha256"],
                "qualification_package_hash": declaration["qualification_package_hash"],
                "rate": result["rate"],
                "threshold": MIN_QUALIFICATION_RATE,
                "qualified": True,
                "item_count": result["item_count"],
                "correct_count": result["correct_count"],
                "answer_key_disclosed": False,
            },
        )

    # -- Stage 1 -----------------------------------------------------------

    def ingest_stage1(
        self,
        role: str,
        payload: bytes,
        *,
        expected_item_ids: list[str],
        package_sha256: str,
    ) -> dict[str, Any]:
        canonical = self._role(role)
        if self.has("stage1_commitment") or self.has_committed_snapshot(STAGE1):
            raise WorkflowError(
                "Stage-1 is already committed; a further Stage-1 submission cannot be accepted. "
                "Committed review evidence is immutable."
            )
        if not self.has(f"qualification_{canonical}"):
            raise WorkflowError(f"{canonical} is not qualified; Stage-1 ingestion refused")
        qualification = self.read(f"qualification_{canonical}")
        declaration = self._declaration_for(canonical)
        registry = self.assignments()
        rows = parse_review_csv(payload, REVIEW_FORM_COLUMNS)
        try:
            verify_assignment(
                registry,
                role=canonical,
                reviewer_pseudonym=declaration["reviewer_pseudonym"],
                stage1_package_hash=package_sha256,
                item_ids=sorted(rows),
            )
        except AssignmentError as error:
            raise WorkflowError(f"Stage-1 submission refused: {error}") from error
        if declaration["stage1_package_hash"] != str(package_sha256).strip().casefold():
            raise WorkflowError(
                f"{canonical} declared a different Stage-1 package than the one submitted against"
            )
        validation = validate_stage1_submission(rows, expected_item_ids)
        if not validation["passed"]:
            raise WorkflowError(f"Stage-1 submission from {canonical} is malformed")
        return self.write(
            f"stage1_submission_{canonical}",
            {
                "receipt_kind": "stage1_submission",
                "reviewer_role": canonical,
                "package_sha256": str(package_sha256).strip().casefold(),
                "submission_sha256": sha256_bytes(payload),
                "qualification_receipt_sha256": qualification["receipt_sha256"],
                "declaration_sha256": declaration["declaration_sha256"],
                "row_count": validation["row_count"],
                "judgements": rows,
                "validation": validation["checks"],
            },
        )

    def commit_stage1(
        self,
        *,
        packet_commitment: str,
        package_hashes: dict[str, str],
        review_schema_version: str,
        scientific_freeze_sha256: str,
        exact_commit: str,
        expected_item_ids: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        """Freeze Stage-1 evidence into a write-once snapshot, then seal it.

        The commitment binds three different things per reviewer, because they
        answer three different questions: the uploaded payload bytes, the exact
        sealed receipt file, and the canonical parsed judgement content.  Binding
        only the first — which is what the retired ``v2`` commitment did — left a
        coordinator free to edit the parsed judgements, keep the payload hash,
        re-seal, and leave every downstream gate satisfied.
        """

        if self.has("stage1_commitment") or self.has_committed_snapshot(STAGE1):
            raise WorkflowError(
                "Stage-1 has already been committed for this workspace; committing twice would "
                "replace immutable review evidence"
            )
        enforce_active_packet(
            packet_version=self.packet_version,
            commitment=packet_commitment,
            action="stage1_commitment",
            package_hashes=package_hashes,
        )
        registry = self.assignments()
        registry_check = verify_registry_complete(registry)
        if not registry_check["passed"]:
            raise WorkflowError(
                f"the reviewer assignment registry is incomplete: {registry_check['checks']}"
            )
        declarations = {role: self._declaration_for(role) for role in REVIEW_ROLES}
        qualifications = {role: self.read(f"qualification_{role}") for role in REVIEW_ROLES}
        submissions = {role: self.read(f"stage1_submission_{role}") for role in REVIEW_ROLES}
        if not all(row["qualified"] for row in qualifications.values()):
            raise WorkflowError("both reviewers must be qualified before Stage-1 can be committed")

        reviewer_bindings: dict[str, dict[str, Any]] = {}
        for role in REVIEW_ROLES:
            assignment = assignment_for_role(registry, role)
            submission = submissions[role]
            declaration = declarations[role]
            qualification = qualifications[role]
            if submission["package_sha256"] != assignment["stage1_package_hash"]:
                raise WorkflowError(
                    f"the Stage-1 submission for {role} is bound to a package that is not the one "
                    "recorded in the assignment registry"
                )
            if submission["package_sha256"] != str(package_hashes.get(role, "")).strip().casefold():
                raise WorkflowError(
                    f"the Stage-1 submission for {role} is bound to a package that is not the one "
                    "being committed"
                )
            if submission["declaration_sha256"] != declaration["declaration_sha256"]:
                raise WorkflowError(
                    f"the Stage-1 submission for {role} names a declaration other than the one on "
                    "file"
                )
            if submission["qualification_receipt_sha256"] != qualification["receipt_sha256"]:
                raise WorkflowError(
                    f"the Stage-1 submission for {role} names a qualification receipt other than "
                    "the one on file"
                )
            item_ids = sorted(submission["judgements"])
            if expected_item_ids is not None and item_ids != sorted(expected_item_ids[role]):
                raise WorkflowError(
                    f"the Stage-1 submission for {role} does not cover exactly the issued items"
                )
            namespace = assignment["stage1_opaque_id_namespace"]
            if any(not str(item).startswith(f"{namespace}-") for item in item_ids):
                raise WorkflowError(
                    f"the Stage-1 submission for {role} carries rows outside its own item namespace"
                )
            reviewer_bindings[role] = {
                "reviewer_pseudonym_sha256": sha256_json(declaration["reviewer_pseudonym"]),
                "stage1_package_sha256": submission["package_sha256"],
                "submission_payload_sha256": submission["submission_sha256"],
                "declaration_sha256": declaration["declaration_sha256"],
                "qualification_receipt_sha256": qualification["receipt_sha256"],
                "assignment_sha256": assignment["assignment_sha256"],
                "item_count": len(item_ids),
                "reviewer_item_ids_sha256": sha256_json(item_ids),
            }

        item_counts = {len(row["judgements"]) for row in submissions.values()}
        if len(item_counts) != 1:
            raise WorkflowError(
                "the two Stage-1 submissions do not cover the same number of items; they cannot "
                "describe one reviewed slice"
            )
        expected_item_count = item_counts.pop()

        try:
            manifest = create_submission_snapshot(
                receipts_root=self.receipts,
                authority=self.authority,
                stage=STAGE1,
                live_paths=self._live_submission_paths(STAGE1),
                receipts=submissions,
                reviewer_bindings=reviewer_bindings,
                manifest_bindings={
                    "packet_version": self.packet_version,
                    "expected_item_count": expected_item_count,
                    "reviewer_item_id_namespace_digest": sha256_json(
                        {role: sorted(submissions[role]["judgements"]) for role in sorted(REVIEW_ROLES)}
                    ),
                    "assignment_registry_sha256": registry["registry_sha256"],
                    "assignment_registry_canonical_sha256": canonical_assignment_registry_digest(
                        registry
                    ),
                    "review_schema_version": review_schema_version,
                    "private_packet_commitment": packet_commitment,
                    "scientific_freeze_sha256": scientific_freeze_sha256,
                    "frozen_source_commit": exact_commit,
                    "stage1_package_hashes": dict(sorted(package_hashes.items())),
                },
            )
        except CommitmentIntegrityError as error:
            raise WorkflowError(f"Stage-1 commitment refused: {error}") from error

        return self.write(
            "stage1_commitment",
            {
                "receipt_kind": "stage1_commitment",
                "commitment_schema_version": STAGE1_COMMITMENT_SCHEMA_VERSION,
                "workflow_schema_version": WORKFLOW_SCHEMA_VERSION,
                "private_packet_commitment": packet_commitment,
                "stage1_package_hashes": package_hashes,
                "assignment_registry_sha256": registry["registry_sha256"],
                "assignment_registry_canonical_sha256": canonical_assignment_registry_digest(
                    registry
                ),
                "declaration_hashes": {
                    role: row["declaration_sha256"] for role, row in sorted(declarations.items())
                },
                "declaration_receipt_hashes": {
                    role: row["receipt_sha256"] for role, row in sorted(declarations.items())
                },
                "declaration_canonical_hashes": {
                    role: canonical_declaration_digest(self.read(f"declaration_{role}"))
                    for role in sorted(REVIEW_ROLES)
                },
                "qualification_receipt_hashes": {
                    role: row["receipt_sha256"] for role, row in sorted(qualifications.items())
                },
                "qualification_canonical_hashes": {
                    role: canonical_qualification_digest(qualifications[role])
                    for role in sorted(REVIEW_ROLES)
                },
                # Three distinct digests per reviewer.  They are not
                # interchangeable and the active workflow verifies all three.
                "stage1_submission_payload_hashes": {
                    role: row["submission_sha256"] for role, row in sorted(submissions.items())
                },
                "stage1_submission_receipt_hashes": {
                    role: receipt_content_sha256(submissions[role])
                    for role in sorted(REVIEW_ROLES)
                },
                "stage1_canonical_judgement_hashes": {
                    role: canonical_stage1_judgements_digest(submissions[role])
                    for role in sorted(REVIEW_ROLES)
                },
                "stage1_snapshot_manifest_sha256": manifest_sha256(manifest),
                "stage1_snapshot_receipt_file_hashes": {
                    role: manifest["reviewers"][role]["snapshot_receipt_file_sha256"]
                    for role in sorted(REVIEW_ROLES)
                },
                "stage1_snapshot_schema_version": manifest["manifest_schema_version"],
                "expected_item_count": expected_item_count,
                "reviewer_roles": sorted(REVIEW_ROLES),
                "review_schema_version": review_schema_version,
                "scientific_freeze_sha256": scientific_freeze_sha256,
                "exact_commit": exact_commit,
                "frozen_source_commit": exact_commit,
                "stage1_final": True,
            },
        )

    # -- Stage 2 -----------------------------------------------------------

    def unlock_stage2(
        self,
        *,
        packet_commitment: str,
        scientific_freeze_sha256: str,
        exact_commit: str,
        key_available: bool,
    ) -> dict[str, Any]:
        """Open Stage 2 only against Stage-1 evidence that is still what was committed.

        Every failure mode named in the integrity closure is checked here rather
        than assumed: a missing snapshot, a replaced snapshot file, a changed
        manifest, a changed judgement digest, a changed payload digest, a changed
        registry, declaration, qualification or package hash, and a live Stage-1
        receipt that now conflicts with the frozen one.
        """

        verified = verify_committed_stage1_snapshot(
            self,
            expected_packet_commitment=packet_commitment,
            expected_scientific_freeze_sha256=scientific_freeze_sha256,
            expected_frozen_source_commit=exact_commit,
        )
        commitment = verified["commitment"]
        checks = {
            "stage1_commitment_valid": bool(commitment.get("stage1_final")),
            "stage1_commitment_schema_is_active": commitment.get("commitment_schema_version")
            == STAGE1_COMMITMENT_SCHEMA_VERSION,
            "packet_commitment_matches": commitment["private_packet_commitment"] == packet_commitment,
            "freeze_hash_matches": commitment["scientific_freeze_sha256"] == scientific_freeze_sha256,
            "code_commit_matches": commitment["exact_commit"] == exact_commit,
            "both_reviewers_declared": len(commitment["declaration_hashes"]) == 2,
            "both_reviewers_qualified": len(commitment["qualification_receipt_hashes"]) == 2,
            "both_submissions_present": len(commitment["stage1_submission_payload_hashes"]) == 2,
            "assignment_registry_unchanged": commitment["assignment_registry_sha256"]
            == self.assignments()["registry_sha256"],
            "external_key_available": key_available,
            **verified["checks"],
        }
        if not all(checks.values()):
            raise WorkflowError(f"Stage-2 unlock refused: {_failed(checks)}")
        return self.write(
            "stage2_unlock",
            {
                "receipt_kind": "stage2_unlock",
                "checks": checks,
                "stage1_commitment_sha256": verified["stage1_commitment_sha256"],
                "stage1_snapshot_manifest_sha256": verified["stage1_snapshot_manifest_sha256"],
                "stage1_canonical_judgement_hashes": verified["canonical_judgement_hashes"],
                "unlocked": True,
            },
        )

    def issue_stage2_package(
        self,
        role: str,
        *,
        package_sha256: str,
        packet_commitment: str,
        scientific_freeze_sha256: str,
        exact_commit: str,
    ) -> dict[str, Any]:
        """Seal the receipt that permanently binds one reviewer's Stage-2 archive."""

        canonical = self._role(role)
        self.read("stage2_unlock")
        verified = verify_committed_stage1_snapshot(
            self,
            expected_packet_commitment=packet_commitment,
            expected_scientific_freeze_sha256=scientific_freeze_sha256,
            expected_frozen_source_commit=exact_commit,
        )
        commitment = verified["commitment"]
        if commitment["private_packet_commitment"] != packet_commitment:
            raise WorkflowError(
                "refusing to issue a Stage-2 package against a packet the Stage-1 commitment "
                "does not name"
            )
        declaration = self._declaration_for(canonical)
        qualification = self.read(f"qualification_{canonical}")
        try:
            assignment = assignment_for_role(self.assignments(), canonical)
        except AssignmentError as error:
            raise WorkflowError(str(error)) from error
        try:
            payload = build_stage2_issuance(
                reviewer_role=canonical,
                reviewer_pseudonym_sha256=sha256_json(declaration["reviewer_pseudonym"]),
                stage1_commitment_sha256=verified["stage1_commitment_sha256"],
                stage1_snapshot_manifest_sha256=verified["stage1_snapshot_manifest_sha256"],
                stage1_canonical_judgements_sha256=verified["canonical_judgement_hashes"][canonical],
                stage1_snapshot_receipt_sha256=verified["snapshot_receipt_file_hashes"][canonical],
                stage2_package_sha256=package_sha256,
                stage2_opaque_id_namespace=assignment["stage2_opaque_id_namespace"],
                private_packet_commitment=packet_commitment,
                qualification_receipt_sha256=qualification["receipt_sha256"],
                reviewer_declaration_sha256=declaration["declaration_sha256"],
                scientific_freeze_sha256=scientific_freeze_sha256,
                exact_commit=exact_commit,
            )
        except Stage2IssuanceError as error:
            raise WorkflowError(f"Stage-2 issuance refused: {error}") from error
        return self.write(f"stage2_issuance_{canonical}", payload)

    def _stage2_issuance_hashes(self) -> dict[str, str]:
        return {
            role: str(self.read(f"stage2_issuance_{role}")["receipt_sha256"])
            for role in REVIEW_ROLES
            if self.has(f"stage2_issuance_{role}")
        }

    def ingest_stage2(
        self,
        role: str,
        payload: bytes,
        *,
        expected_item_ids: list[str],
        applicability: dict[str, dict[str, bool]],
        package_sha256: str,
        packet_commitment: str,
        scientific_freeze_sha256: str,
        exact_commit: str,
    ) -> dict[str, Any]:
        canonical = self._role(role)
        if self.has_committed_snapshot(STAGE2):
            raise WorkflowError(
                "Stage-2 is already committed; a further Stage-2 submission cannot be accepted. "
                "Committed review evidence is immutable."
            )
        self.read("stage2_unlock")
        verified = verify_committed_stage1_snapshot(
            self,
            expected_packet_commitment=packet_commitment,
            expected_scientific_freeze_sha256=scientific_freeze_sha256,
            expected_frozen_source_commit=exact_commit,
        )
        declaration = self._declaration_for(canonical)
        qualification = self.read(f"qualification_{canonical}")
        registry = self.assignments()
        rows = parse_review_csv(payload, STAGE2_FORM_COLUMNS)
        try:
            assignment = verify_assignment(
                registry,
                role=canonical,
                reviewer_pseudonym=declaration["reviewer_pseudonym"],
                item_ids=sorted(rows),
            )
        except AssignmentError as error:
            raise WorkflowError(f"Stage-2 submission refused: {error}") from error
        if not self.has(f"stage2_issuance_{canonical}"):
            raise WorkflowError(
                f"Stage-2 submission refused: no sealed issuance receipt exists for {canonical}; "
                "generate the Stage-2 packages before accepting a Stage-2 submission"
            )
        issuance = self.read(f"stage2_issuance_{canonical}")
        try:
            issuance_checks = verify_stage2_issuance(
                issuance,
                reviewer_role=canonical,
                reviewer_pseudonym_sha256=sha256_json(declaration["reviewer_pseudonym"]),
                stage1_commitment_sha256=verified["stage1_commitment_sha256"],
                stage1_snapshot_manifest_sha256=verified["stage1_snapshot_manifest_sha256"],
                stage1_canonical_judgements_sha256=verified["canonical_judgement_hashes"][canonical],
                stage1_snapshot_receipt_sha256=verified["snapshot_receipt_file_hashes"][canonical],
                stage2_package_sha256=package_sha256,
                stage2_opaque_id_namespace=assignment["stage2_opaque_id_namespace"],
                private_packet_commitment=packet_commitment,
                qualification_receipt_sha256=qualification["receipt_sha256"],
                reviewer_declaration_sha256=declaration["declaration_sha256"],
                scientific_freeze_sha256=scientific_freeze_sha256,
                exact_commit=exact_commit,
                submitted_item_ids=sorted(rows),
            )
        except Stage2IssuanceError as error:
            raise WorkflowError(f"Stage-2 submission refused: {error}") from error
        validation = validate_stage2_submission(rows, expected_item_ids, applicability)
        if not validation["form_complete"]:
            raise WorkflowError(f"Stage-2 submission from {canonical} is malformed")
        receipt = self.write(
            f"stage2_submission_{canonical}",
            {
                "receipt_kind": "stage2_submission",
                "reviewer_role": canonical,
                "form_schema_version": STAGE2_FORM_SCHEMA_VERSION,
                "acceptance_policy_version": STAGE2_ACCEPTANCE_POLICY_VERSION,
                "declaration_sha256": declaration["declaration_sha256"],
                "submission_sha256": sha256_bytes(payload),
                "stage2_issuance_sha256": issuance["receipt_sha256"],
                "stage2_issuance_schema_version": STAGE2_ISSUANCE_SCHEMA_VERSION,
                "stage2_package_sha256": str(package_sha256).strip().casefold(),
                "issuance_checks": issuance_checks,
                "judgements": rows,
                "validation": validation["checks"],
                # Recorded so that nothing downstream can mistake a complete form
                # for an approval.
                "form_complete": validation["form_complete"],
                "blocking_value_count": validation["blocking_value_count"],
                "substantively_accepted_without_adjudication": validation[
                    "substantively_accepted_without_adjudication"
                ],
            },
        )
        if all(self.has(f"stage2_submission_{other}") for other in REVIEW_ROLES):
            self._commit_stage2(verified)
        return receipt

    def _commit_stage2(self, stage1: dict[str, Any]) -> dict[str, Any]:
        """Freeze both Stage-2 submissions the moment the second one lands.

        Stage 2 gets the same treatment as Stage 1 for the same reason: the
        disagreement queue, the adjudicator package, the final records and C10
        all read Stage-2 judgements, so a Stage-2 receipt that stayed mutable
        after acceptance would reopen the identical hole one stage later.
        """

        submissions = {role: self.read(f"stage2_submission_{role}") for role in REVIEW_ROLES}
        issuance = {role: self.read(f"stage2_issuance_{role}") for role in REVIEW_ROLES}
        reviewer_bindings = {
            role: {
                "reviewer_pseudonym_sha256": str(issuance[role]["reviewer_pseudonym_sha256"]),
                "submission_payload_sha256": str(submissions[role]["submission_sha256"]),
                "stage2_package_sha256": str(submissions[role]["stage2_package_sha256"]),
                "stage2_issuance_sha256": str(issuance[role]["receipt_sha256"]),
                "declaration_sha256": str(submissions[role]["declaration_sha256"]),
                "stage1_canonical_judgements_sha256": stage1["canonical_judgement_hashes"][role],
                "item_count": len(submissions[role]["judgements"]),
                "reviewer_item_ids_sha256": sha256_json(sorted(submissions[role]["judgements"])),
            }
            for role in REVIEW_ROLES
        }
        try:
            return create_submission_snapshot(
                receipts_root=self.receipts,
                authority=self.authority,
                stage=STAGE2,
                live_paths=self._live_submission_paths(STAGE2),
                receipts=submissions,
                reviewer_bindings=reviewer_bindings,
                manifest_bindings={
                    "packet_version": self.packet_version,
                    "stage1_commitment_sha256": stage1["stage1_commitment_sha256"],
                    "stage1_snapshot_manifest_sha256": stage1["stage1_snapshot_manifest_sha256"],
                    "stage1_canonical_judgement_hashes": stage1["canonical_judgement_hashes"],
                    "stage2_issuance_hashes": {
                        role: str(issuance[role]["receipt_sha256"]) for role in sorted(REVIEW_ROLES)
                    },
                    "private_packet_commitment": str(
                        stage1["commitment"]["private_packet_commitment"]
                    ),
                    "scientific_freeze_sha256": str(
                        stage1["commitment"]["scientific_freeze_sha256"]
                    ),
                    "frozen_source_commit": str(stage1["commitment"]["frozen_source_commit"]),
                    "expected_item_count": len(submissions[REVIEWER_A]["judgements"]),
                },
            )
        except CommitmentIntegrityError as error:
            raise WorkflowError(f"Stage-2 commitment refused: {error}") from error

    # -- pairing, queues, adjudication -------------------------------------

    def _paired(
        self, mappings: dict[str, dict[str, str]], stage: str
    ) -> dict[str, dict[str, dict[str, str]]]:
        """Pair reviewer rows, reading only committed evidence.

        After commitment there is no legitimate reader of
        ``<stage>_submission_<role>.json``.  This function is the single place
        every pairing consumer goes through, so routing it at the snapshot
        removes the mutable path from the whole downstream graph at once.
        """

        if stage == STAGE1:
            receipts = verify_committed_stage1_snapshot(self)["receipts"]
        elif stage == STAGE2:
            receipts = verify_committed_stage2_snapshot(self)["receipts"]
        else:
            raise WorkflowError(f"unknown review stage {stage!r}")
        by_pair: dict[str, dict[str, dict[str, str]]] = {}
        for role in REVIEW_ROLES:
            mapping = mappings[role]
            for item_id, row in receipts[role]["judgements"].items():
                pair_id = mapping.get(item_id)
                if pair_id is None:
                    raise WorkflowError(f"unmapped reviewer item {item_id}")
                by_pair.setdefault(pair_id, {})[role] = row
        return by_pair

    def _queue_bindings(self, stage: str) -> dict[str, Any]:
        """What a disagreement queue is permanently bound to."""

        stage1 = verify_committed_stage1_snapshot(self)
        bindings: dict[str, Any] = {
            "stage1_commitment_sha256": stage1["stage1_commitment_sha256"],
            "stage1_snapshot_manifest_sha256": stage1["stage1_snapshot_manifest_sha256"],
            "stage1_snapshot_receipt_hashes": stage1["snapshot_receipt_file_hashes"],
            "stage1_canonical_judgement_hashes": stage1["canonical_judgement_hashes"],
        }
        if stage == STAGE2:
            stage2 = verify_committed_stage2_snapshot(self)
            bindings.update(
                {
                    "stage2_snapshot_manifest_sha256": stage2["stage2_snapshot_manifest_sha256"],
                    "stage2_snapshot_receipt_hashes": stage2["snapshot_receipt_file_hashes"],
                    "stage2_canonical_judgement_hashes": stage2["canonical_judgement_hashes"],
                }
            )
        return bindings

    def build_stage1_disagreements(
        self, *, mappings: dict[str, dict[str, str]]
    ) -> dict[str, Any]:
        if self.has("stage1_adjudication"):
            raise WorkflowError(
                "the Stage-1 disagreement queue cannot be regenerated after it has been "
                "adjudicated; a different queue would leave the adjudication answering nothing"
            )
        try:
            queue = build_stage1_queue(self._paired(mappings, STAGE1))
        except AdjudicationError as error:
            raise WorkflowError(str(error)) from error
        return self.write(
            "stage1_disagreement_queue",
            {
                "receipt_kind": "stage1_disagreement_queue",
                "stage2_issuance_hashes": self._stage2_issuance_hashes(),
                **self._queue_bindings(STAGE1),
                **queue,
                "queue_content_sha256": canonical_queue_digest(queue),
            },
        )

    def build_stage2_disagreements(
        self, *, mappings: dict[str, dict[str, str]], applicability: dict[str, dict[str, bool]]
    ) -> dict[str, Any]:
        if self.has("stage2_adjudication"):
            raise WorkflowError(
                "the Stage-2 disagreement queue cannot be regenerated after it has been "
                "adjudicated; a different queue would leave the adjudication answering nothing"
            )
        issuance = self._stage2_issuance_hashes()
        if set(issuance) != set(REVIEW_ROLES):
            raise WorkflowError(
                "a Stage-2 disagreement queue requires a sealed Stage-2 issuance receipt for both "
                "reviewers; the queue would otherwise describe unissued packages"
            )
        try:
            queue = build_stage2_queue(self._paired(mappings, STAGE2), applicability)
        except AdjudicationError as error:
            raise WorkflowError(str(error)) from error
        return self.write(
            "stage2_disagreement_queue",
            {
                "receipt_kind": "stage2_disagreement_queue",
                "stage2_issuance_hashes": issuance,
                **self._queue_bindings(STAGE2),
                **queue,
                "queue_content_sha256": canonical_queue_digest(queue),
            },
        )

    def _check_adjudicator(self, adjudicator_pseudonym: str) -> dict[str, Any]:
        registry = self.assignments()
        try:
            adjudicator = assignment_for_role(registry, ADJUDICATOR)
        except AssignmentError as error:
            raise WorkflowError(str(error)) from error
        if str(adjudicator["reviewer_pseudonym"]) != str(adjudicator_pseudonym).strip():
            raise WorkflowError("the submitted adjudication is not from the assigned adjudicator")
        reviewers = {
            str(assignment_for_role(registry, role)["reviewer_pseudonym"]) for role in REVIEW_ROLES
        }
        if str(adjudicator["reviewer_pseudonym"]) in reviewers:
            raise WorkflowError("the adjudicator must be independent of both reviewers")
        return adjudicator

    def record_adjudicator_package(self, *, stage: str, package: dict[str, Any]) -> dict[str, Any]:
        """Seal what was issued, so a later adjudication can be matched to it."""

        if stage not in (STAGE1, STAGE2):
            raise WorkflowError(f"unknown adjudication stage {stage!r}")
        binding = dict(package["binding"])
        binding.pop("schema_version", None)
        return self.write(
            f"{stage}_adjudicator_package",
            {
                "receipt_kind": f"{stage}_adjudicator_package",
                "package_schema_version": package["schema_version"],
                "package_filename": package["filename"],
                "package_sha256": package["package_sha256"],
                **binding,
            },
        )

    def ingest_adjudication(
        self,
        *,
        stage: str,
        adjudicator_pseudonym: str,
        decisions: list[dict[str, Any]],
        package_sha256: str,
    ) -> dict[str, Any]:
        if stage not in (STAGE1, STAGE2):
            raise WorkflowError(f"unknown adjudication stage {stage!r}")
        if self.has(f"{stage}_adjudication"):
            raise WorkflowError(
                f"the {stage} adjudication is already sealed; replacing it would rewrite settled "
                "review evidence"
            )
        if self.has("final_adjudicated_records"):
            raise WorkflowError(
                f"the {stage} adjudication cannot be accepted after the final adjudicated records "
                "were built; the records would no longer describe the decisions behind them"
            )
        adjudicator = self._check_adjudicator(adjudicator_pseudonym)
        queue = self.read(f"{stage}_disagreement_queue")
        if queue.get("queue_content_sha256") != canonical_queue_digest(queue):
            raise WorkflowError(
                f"the {stage} disagreement queue content no longer matches the digest it was "
                "sealed with"
            )
        if not self.has(f"{stage}_adjudicator_package"):
            raise WorkflowError(
                f"{stage} adjudication refused: no adjudicator package was issued, so there is "
                "nothing this decision could have been made against"
            )
        issued = self.read(f"{stage}_adjudicator_package")
        try:
            package_checks = verify_package_binding(
                issued,
                stage=stage,
                queue=queue,
                package_sha256=package_sha256,
                adjudicator_assignment_sha256=adjudicator["assignment_sha256"],
            )
        except AdjudicationPackageError as error:
            raise WorkflowError(f"{stage} adjudication refused: {error}") from error
        try:
            validated = validate_adjudication(stage=stage, queue=queue, decisions=decisions)
        except AdjudicationError as error:
            raise WorkflowError(f"{stage} adjudication refused: {error}") from error
        payload = {
            "receipt_kind": f"{stage}_adjudication",
            "adjudicator_assignment_sha256": adjudicator["assignment_sha256"],
            "adjudicator_pseudonym_sha256": sha256_json(adjudicator["reviewer_pseudonym"]),
            "disagreement_queue_sha256": queue["receipt_sha256"],
            "disagreement_queue_content_sha256": canonical_queue_digest(queue),
            "adjudicator_package_sha256": issued["package_sha256"],
            "adjudicator_package_receipt_sha256": issued["receipt_sha256"],
            "adjudicator_package_checks": package_checks,
            "stage2_issuance_hashes": self._stage2_issuance_hashes(),
            "submission_sha256": sha256_json(decisions),
            **self._queue_bindings(stage),
            **validated,
        }
        return self.write(
            f"{stage}_adjudication",
            {**payload, "adjudication_content_sha256": canonical_adjudication_digest(payload)},
        )

    # -- agreement (raw, pre-adjudication) ---------------------------------

    def compute_agreement(self, *, mappings: dict[str, dict[str, str]]) -> dict[str, Any]:
        """Raw agreement between the two independent submissions.

        Adjudicated values are deliberately not consulted: resolving a dispute
        must never make the reviewers look as though they had agreed.
        """

        graph = self._input_graph_bindings()
        stage1 = self._paired(mappings, STAGE1)
        stage2 = self._paired(mappings, STAGE2) if self.has_committed_snapshot(STAGE2) else {}
        tables = agreement_tables(stage1, stage2)

        return self.write(
            "agreement",
            {
                "receipt_kind": "agreement",
                "computed_from": "immutable_committed_raw_pre_adjudication_judgements",
                "adjudicated_values_used": False,
                **graph,
                **tables,
                "combined_rule": "both_stages_must_meet_the_threshold_independently",
                "prevalence_note": (
                    "Chance-corrected coefficients are reported alongside prevalence diagnostics "
                    "but are not pass thresholds, because degenerate prevalence can make them "
                    "undefined on a twenty-pair pilot."
                ),
            },
        )

    # -- final adjudicated records ----------------------------------------

    def build_final_adjudicated_records(
        self,
        *,
        mappings: dict[str, dict[str, str]],
        applicability: dict[str, dict[str, bool]],
        expected_pair_count: int,
    ) -> dict[str, Any]:
        self._require_valid_input_graph("the final adjudicated records")
        graph = self._input_graph_bindings()
        stage1 = self._paired(mappings, STAGE1)
        stage2 = self._paired(mappings, STAGE2) if self.has_committed_snapshot(STAGE2) else {}
        adjudications = {
            stage: (self.read(f"{stage}_adjudication") if self.has(f"{stage}_adjudication") else None)
            for stage in (STAGE1, STAGE2)
        }
        final = build_final_records(
            stage1_paired=stage1,
            stage2_paired=stage2,
            stage1_adjudication=adjudications[STAGE1],
            stage2_adjudication=adjudications[STAGE2],
            applicability=applicability,
            expected_pair_count=expected_pair_count,
        )
        return self.write(
            "final_adjudicated_records",
            {
                "receipt_kind": "final_adjudicated_records",
                "stage2_issuance_hashes": self._stage2_issuance_hashes(),
                **graph,
                **final,
            },
        )

    def _require_valid_input_graph(self, what: str) -> dict[str, Any]:
        """Refuse to derive ``what`` from a chain that has changed under us."""

        graph = review_input_graph(self)
        if not graph["complete_input_graph_valid"]:
            raise WorkflowError(
                f"refusing to build {what} over a changed input graph: {graph['failed_checks']}"
            )
        return graph

    def _input_graph_bindings(self) -> dict[str, Any]:
        """The immutable inputs a derived artifact is permanently bound to.

        Carried into the agreement report, the final records, the exclusion
        register and the slice lock, so that each of them can be re-checked
        against what is on disk rather than trusted.
        """

        stage1 = verify_committed_stage1_snapshot(self)
        bindings: dict[str, Any] = {
            "stage1_commitment_sha256": stage1["stage1_commitment_sha256"],
            "stage1_snapshot_manifest_sha256": stage1["stage1_snapshot_manifest_sha256"],
            "stage1_snapshot_receipt_hashes": stage1["snapshot_receipt_file_hashes"],
            "stage1_canonical_judgement_hashes": stage1["canonical_judgement_hashes"],
            "assignment_registry_sha256": str(
                stage1["commitment"]["assignment_registry_sha256"]
            ),
            "declaration_receipt_hashes": dict(
                stage1["commitment"]["declaration_receipt_hashes"]
            ),
            "qualification_receipt_hashes": dict(
                stage1["commitment"]["qualification_receipt_hashes"]
            ),
            "private_packet_commitment": str(
                stage1["commitment"]["private_packet_commitment"]
            ),
            "scientific_freeze_sha256": str(stage1["commitment"]["scientific_freeze_sha256"]),
            "frozen_source_commit": str(stage1["commitment"]["frozen_source_commit"]),
        }
        if self.has_committed_snapshot(STAGE2):
            stage2 = verify_committed_stage2_snapshot(self)
            bindings.update(
                {
                    "stage2_snapshot_manifest_sha256": stage2["stage2_snapshot_manifest_sha256"],
                    "stage2_snapshot_receipt_hashes": stage2["snapshot_receipt_file_hashes"],
                    "stage2_canonical_judgement_hashes": stage2["canonical_judgement_hashes"],
                }
            )
        bindings["queue_content_hashes"] = {
            stage: (
                canonical_queue_digest(self.read(f"{stage}_disagreement_queue"))
                if self.has(f"{stage}_disagreement_queue")
                else None
            )
            for stage in (STAGE1, STAGE2)
        }
        bindings["adjudication_content_hashes"] = {
            stage: (
                canonical_adjudication_digest(self.read(f"{stage}_adjudication"))
                if self.has(f"{stage}_adjudication")
                else None
            )
            for stage in (STAGE1, STAGE2)
        }
        return bindings

    # -- evidence eligibility ---------------------------------------------

    def evidence_eligibility(self) -> dict[str, Any]:
        """Derive, from provenance alone, whether this workspace holds evidence.

        Nothing here consults a mode flag.  Every binding is either present and
        verifiable on disk, or it is not.
        """

        bindings: dict[str, bool] = dict.fromkeys(REQUIRED_EVIDENCE_BINDINGS, False)
        try:
            enforce_active_packet(packet_version=self.packet_version, action="evidence_eligibility")
            bindings["active_non_retired_packet"] = True
        except Exception:
            pass
        try:
            registry = self.assignments()
            bindings["valid_reviewer_assignment"] = verify_registry_complete(registry)["passed"]
        except WorkflowError:
            registry = {}
        try:
            declarations = [self._declaration_for(role) for role in REVIEW_ROLES]
            bindings["valid_declaration_receipt"] = len(declarations) == 2 and not any(
                row["declaration_is_synthetic"] for row in declarations
            )
        except WorkflowError:
            declarations = []
        try:
            qualifications = [self.read(f"qualification_{role}") for role in REVIEW_ROLES]
            bindings["valid_private_qualification_receipt"] = len(qualifications) == 2 and all(
                row.get("qualification_version") == QUALIFICATION_SCHEMA_VERSION
                and row.get("qualified") is True
                for row in qualifications
            )
        except WorkflowError:
            pass
        try:
            # After commitment the committed snapshot is the only legitimate
            # source; before it there is nothing to be eligible yet.
            submissions = verify_committed_stage1_snapshot(self)["receipts"]
            stage2 = verify_committed_stage2_snapshot(self)["receipts"]
            issuance = self._stage2_issuance_hashes()
            bindings["complete_submission"] = bool(submissions) and bool(stage2)
            bindings["sealed_stage2_issuance_receipt"] = set(issuance) == set(REVIEW_ROLES) and all(
                stage2[role].get("stage2_issuance_sha256") == issuance[role]
                for role in REVIEW_ROLES
            )
            if registry:
                bindings["correct_package_hash"] = all(
                    submissions[role]["package_sha256"]
                    == assignment_for_role(registry, role)["stage1_package_hash"]
                    for role in REVIEW_ROLES
                )
                bindings["correct_reviewer_namespace"] = all(
                    all(
                        str(item).startswith(
                            f"{assignment_for_role(registry, role)['stage1_opaque_id_namespace']}-"
                        )
                        for item in submissions[role]["judgements"]
                    )
                    for role in REVIEW_ROLES
                )
        except (WorkflowError, AssignmentError):
            pass

        # ``rglob`` so the committed snapshot files and manifests are audited
        # alongside the live receipts rather than sitting in an unchecked subtree.
        receipts = sorted(self.receipts.rglob("*.json"))
        loaded: list[dict[str, Any]] = []
        for path in receipts:
            if path.is_symlink():
                loaded.append({})
                continue
            try:
                loaded.append(read_json(path))
            except ValueError:
                loaded.append({})
        bindings["non_fixture_artifact_origin"] = bool(loaded) and not any(
            receipt_is_fixture(receipt) for receipt in loaded
        )
        bindings["production_schema_version"] = bool(loaded) and all(
            receipt.get("receipt_schema_version") == self.authority.schema_version
            for receipt in loaded
        )
        content_intact = bool(loaded)
        for receipt in loaded:
            try:
                verify_receipt(self.authority, receipt)
            except ReceiptError:
                content_intact = False
                break
        bindings["content_hash_intact"] = content_intact
        bindings["coordinator_acceptance_receipt"] = self.is_production and content_intact

        return {
            "schema_version": "cab_review_ready_v2_evidence_eligibility_v1",
            "artifact_origin": self.authority.origin,
            "required_bindings": list(REQUIRED_EVIDENCE_BINDINGS),
            "bindings": bindings,
            "missing_bindings": sorted(name for name, value in bindings.items() if not value),
            "counts_as_genuine_evidence": all(bindings.values())
            and self.authority.counts_as_genuine_evidence,
        }


# --------------------------------------------------------------------------
# committed-evidence verification
#
# One function per stage, and nothing downstream reimplements a subset of it.
# Each is fail-closed: it returns the committed receipts only after every
# binding re-derives, and raises otherwise.
# --------------------------------------------------------------------------


def _failed(checks: dict[str, bool]) -> list[str]:
    return sorted(name for name, value in checks.items() if not value)


def _content_digests(
    artifacts: dict[str, dict[str, Any] | None],
    digest: Callable[[dict[str, Any]], str],
) -> dict[str, str | None]:
    """Per-stage content digest, or ``None`` where the stage produced nothing.

    A stage with no disputes has no adjudication, and ``None`` is the honest
    record of that — distinguishable from a stage whose adjudication went
    missing, which would be a hash mismatch instead.
    """

    return {
        stage: (digest(artifact) if artifact is not None else None)
        for stage, artifact in sorted(artifacts.items())
    }


def agreement_tables(
    stage1: dict[str, dict[str, dict[str, str]]],
    stage2: dict[str, dict[str, dict[str, str]]],
) -> dict[str, Any]:
    """Raw per-dimension agreement, as a pure function of the paired judgements.

    Pure on purpose: ``compute_agreement`` seals the result and C10 recomputes it
    from the committed judgements and refuses to score a sealed agreement report
    that does not reproduce.  A resealed report with a flattering number is
    therefore detectable without anyone having to trust the report.
    """

    def per_dimension(
        paired: dict[str, dict[str, dict[str, str]]], dimensions: tuple[str, ...]
    ) -> dict[str, dict[str, Any]]:
        table: dict[str, dict[str, Any]] = {}
        for dimension in dimensions:
            agree = 0
            total = 0
            for rows in paired.values():
                values = [
                    str(rows[role].get(dimension, "")).strip().casefold() for role in sorted(rows)
                ]
                total += 1
                agree += len(set(values)) == 1
            table[dimension] = {
                "agreed": agree,
                "total": total,
                "raw_agreement": round(agree / total, 4) if total else 0.0,
            }
        return table

    def overall(table: dict[str, dict[str, Any]]) -> float:
        agreed = sum(row["agreed"] for row in table.values())
        total = sum(row["total"] for row in table.values())
        return round(agreed / total, 4) if total else 0.0

    stage1_table = per_dimension(stage1, GATING_DIMENSIONS)
    stage2_table = per_dimension(stage2, STAGE2_SUBSTANTIVE_DIMENSIONS) if stage2 else {}
    return {
        "stage1": {
            "per_dimension": stage1_table,
            "overall_raw_agreement": overall(stage1_table),
            "pair_count": len(stage1),
        },
        "stage2": {
            "per_dimension": stage2_table,
            "overall_raw_agreement": overall(stage2_table),
            "pair_count": len(stage2),
        },
    }


def verify_committed_stage1_snapshot(
    workspace: ReviewWorkspace,
    *,
    expected_packet_commitment: str | None = None,
    expected_scientific_freeze_sha256: str | None = None,
    expected_frozen_source_commit: str | None = None,
) -> dict[str, Any]:
    """Return the immutable Stage-1 evidence, or refuse to return anything.

    Reads only the committed snapshot.  A live ``stage1_submission_*.json`` that
    no longer matches the snapshot is a *conflict*, not an update: it fails here
    even though nothing downstream would otherwise have read it, because making
    tampering visible is the point.
    """

    commitment = workspace.read("stage1_commitment")
    schema = commitment.get("commitment_schema_version")
    if schema in RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS:
        raise WorkflowError(
            f"the Stage-1 commitment declares the retired schema {schema!r}; evidence recorded "
            f"under it bound only the payload hash and cannot be migrated. Genuine review must "
            f"start under {STAGE1_COMMITMENT_SCHEMA_VERSION!r}."
        )
    if schema != STAGE1_COMMITMENT_SCHEMA_VERSION:
        raise WorkflowError(
            f"the Stage-1 commitment declares {schema!r}, not {STAGE1_COMMITMENT_SCHEMA_VERSION!r}"
        )

    try:
        manifest = read_snapshot_manifest(
            workspace.receipts,
            authority=workspace.authority,
            stage=STAGE1,
            require_private=workspace.is_production,
        )
        receipts, checks = read_snapshot_receipts(
            workspace.receipts,
            authority=workspace.authority,
            stage=STAGE1,
            manifest=manifest,
            live_paths=workspace._live_submission_paths(STAGE1),
            require_private=workspace.is_production,
        )
    except CommitmentIntegrityError as error:
        raise WorkflowError(f"the committed Stage-1 snapshot is invalid: {error}") from error

    registry = workspace.assignments()
    declarations = {role: workspace.read(f"declaration_{role}") for role in REVIEW_ROLES}
    qualifications = {role: workspace.read(f"qualification_{role}") for role in REVIEW_ROLES}

    file_hashes = {
        role: manifest["reviewers"][role]["snapshot_receipt_file_sha256"] for role in REVIEW_ROLES
    }
    judgement_hashes = {
        role: canonical_stage1_judgements_digest(receipts[role]) for role in REVIEW_ROLES
    }
    payload_hashes = {role: str(receipts[role]["submission_sha256"]) for role in REVIEW_ROLES}
    pseudonym_hashes = {
        role: sha256_json(declarations[role]["reviewer_pseudonym"]) for role in REVIEW_ROLES
    }

    checks.update(
        {
            "stage1_snapshot_manifest_valid": manifest_sha256(manifest)
            == commitment.get("stage1_snapshot_manifest_sha256"),
            "stage1_snapshot_file_hashes_match_commitment": file_hashes
            == dict(commitment.get("stage1_snapshot_receipt_file_hashes") or {}),
            "stage1_receipt_hashes_match_commitment": {
                role: receipt_content_sha256(receipts[role]) for role in REVIEW_ROLES
            }
            == dict(commitment.get("stage1_submission_receipt_hashes") or {}),
            "stage1_judgement_hashes_match_commitment": judgement_hashes
            == dict(commitment.get("stage1_canonical_judgement_hashes") or {}),
            "stage1_payload_hashes_match_commitment": payload_hashes
            == dict(commitment.get("stage1_submission_payload_hashes") or {}),
            "stage1_declarations_match_commitment": {
                role: declarations[role]["declaration_sha256"] for role in REVIEW_ROLES
            }
            == dict(commitment.get("declaration_hashes") or {}),
            "stage1_declaration_content_unchanged": {
                role: canonical_declaration_digest(declarations[role]) for role in REVIEW_ROLES
            }
            == dict(commitment.get("declaration_canonical_hashes") or {}),
            "stage1_qualifications_match_commitment": {
                role: qualifications[role]["receipt_sha256"] for role in REVIEW_ROLES
            }
            == dict(commitment.get("qualification_receipt_hashes") or {}),
            "stage1_qualification_content_unchanged": {
                role: canonical_qualification_digest(qualifications[role]) for role in REVIEW_ROLES
            }
            == dict(commitment.get("qualification_canonical_hashes") or {}),
            "stage1_package_hashes_match_commitment": {
                role: str(receipts[role]["package_sha256"]) for role in REVIEW_ROLES
            }
            == {
                role: str(assignment_for_role(registry, role)["stage1_package_hash"])
                for role in REVIEW_ROLES
            },
            "assignment_registry_unchanged_since_commitment": registry["registry_sha256"]
            == commitment.get("assignment_registry_sha256"),
            "assignment_registry_content_unchanged": canonical_assignment_registry_digest(registry)
            == commitment.get("assignment_registry_canonical_sha256"),
            "stage1_reviewer_pseudonyms_bound": pseudonym_hashes
            == {
                role: manifest["reviewers"][role]["reviewer_pseudonym_sha256"]
                for role in REVIEW_ROLES
            },
            "stage1_reviewers_are_distinct": len(set(pseudonym_hashes.values())) == 2,
            "stage1_exactly_two_reviewer_roles": sorted(manifest["reviewers"]) == sorted(REVIEW_ROLES),
            "stage1_item_coverage_matches_commitment": all(
                len(receipts[role]["judgements"]) == int(commitment.get("expected_item_count", -1))
                for role in REVIEW_ROLES
            ),
            "stage1_snapshot_artifact_origin_matches": manifest.get("artifact_origin")
            == workspace.authority.origin
            and all(
                receipts[role].get("artifact_origin") == workspace.authority.origin
                for role in REVIEW_ROLES
            ),
            "stage1_snapshot_packet_matches": manifest.get("packet_version")
            == workspace.packet_version
            and all(
                receipts[role].get("packet_version") == workspace.packet_version
                for role in REVIEW_ROLES
            ),
            "stage1_snapshot_binds_the_committed_packet": manifest.get("private_packet_commitment")
            == commitment.get("private_packet_commitment"),
            "stage1_snapshot_binds_the_committed_freeze": manifest.get("scientific_freeze_sha256")
            == commitment.get("scientific_freeze_sha256"),
            "stage1_snapshot_binds_the_committed_source_commit": manifest.get("frozen_source_commit")
            == commitment.get("frozen_source_commit"),
        }
    )
    if expected_packet_commitment is not None:
        checks["stage1_packet_commitment_matches_expected"] = (
            commitment.get("private_packet_commitment") == expected_packet_commitment
        )
    if expected_scientific_freeze_sha256 is not None:
        checks["stage1_freeze_matches_expected"] = (
            commitment.get("scientific_freeze_sha256") == expected_scientific_freeze_sha256
        )
    if expected_frozen_source_commit is not None:
        checks["stage1_source_commit_matches_expected"] = (
            commitment.get("frozen_source_commit") == expected_frozen_source_commit
        )

    failed = _failed(checks)
    if failed:
        raise WorkflowError(
            f"the committed Stage-1 evidence has changed since it was committed: {failed}"
        )
    return {
        "schema_version": REVIEW_INPUT_GRAPH_SCHEMA_VERSION,
        "stage": STAGE1,
        "commitment": commitment,
        "stage1_commitment_sha256": receipt_content_sha256(commitment),
        "manifest": manifest,
        "stage1_snapshot_manifest_sha256": manifest_sha256(manifest),
        "receipts": receipts,
        "canonical_judgement_hashes": judgement_hashes,
        "snapshot_receipt_file_hashes": file_hashes,
        "payload_hashes": payload_hashes,
        "checks": checks,
    }


def verify_committed_stage2_snapshot(
    workspace: ReviewWorkspace,
    *,
    expected_packet_commitment: str | None = None,
    expected_scientific_freeze_sha256: str | None = None,
    expected_frozen_source_commit: str | None = None,
) -> dict[str, Any]:
    """Return the immutable Stage-2 evidence, bound to the Stage-1 snapshot."""

    stage1 = verify_committed_stage1_snapshot(
        workspace,
        expected_packet_commitment=expected_packet_commitment,
        expected_scientific_freeze_sha256=expected_scientific_freeze_sha256,
        expected_frozen_source_commit=expected_frozen_source_commit,
    )
    try:
        manifest = read_snapshot_manifest(
            workspace.receipts,
            authority=workspace.authority,
            stage=STAGE2,
            require_private=workspace.is_production,
        )
        receipts, checks = read_snapshot_receipts(
            workspace.receipts,
            authority=workspace.authority,
            stage=STAGE2,
            manifest=manifest,
            live_paths=workspace._live_submission_paths(STAGE2),
            require_private=workspace.is_production,
        )
    except CommitmentIntegrityError as error:
        raise WorkflowError(f"the committed Stage-2 snapshot is invalid: {error}") from error

    issuance = {role: workspace.read(f"stage2_issuance_{role}") for role in REVIEW_ROLES}
    judgement_hashes = {
        role: canonical_stage2_judgements_digest(receipts[role]) for role in REVIEW_ROLES
    }
    checks.update(
        {
            "stage2_snapshot_binds_the_stage1_commitment": manifest.get("stage1_commitment_sha256")
            == stage1["stage1_commitment_sha256"],
            "stage2_snapshot_binds_the_stage1_snapshot": manifest.get(
                "stage1_snapshot_manifest_sha256"
            )
            == stage1["stage1_snapshot_manifest_sha256"],
            "stage2_snapshot_binds_the_stage1_judgements": dict(
                manifest.get("stage1_canonical_judgement_hashes") or {}
            )
            == stage1["canonical_judgement_hashes"],
            "stage2_issuance_receipts_unchanged_since_snapshot": {
                role: str(issuance[role]["receipt_sha256"]) for role in REVIEW_ROLES
            }
            == dict(manifest.get("stage2_issuance_hashes") or {}),
            "stage2_submissions_bound_to_their_issuance": all(
                str(receipts[role].get("stage2_issuance_sha256"))
                == str(issuance[role]["receipt_sha256"])
                for role in REVIEW_ROLES
            ),
            "stage2_issuance_bound_to_the_stage1_commitment": all(
                str(issuance[role]["stage1_commitment_sha256"])
                == stage1["stage1_commitment_sha256"]
                for role in REVIEW_ROLES
            ),
            "stage2_issuance_bound_to_the_stage1_snapshot": all(
                str(issuance[role].get("stage1_snapshot_manifest_sha256"))
                == stage1["stage1_snapshot_manifest_sha256"]
                for role in REVIEW_ROLES
            ),
            "stage2_issuance_bound_to_each_reviewers_stage1_judgements": all(
                str(issuance[role].get("stage1_canonical_judgements_sha256"))
                == stage1["canonical_judgement_hashes"][role]
                for role in REVIEW_ROLES
            ),
            "stage2_snapshot_artifact_origin_matches": manifest.get("artifact_origin")
            == workspace.authority.origin
            and all(
                receipts[role].get("artifact_origin") == workspace.authority.origin
                for role in REVIEW_ROLES
            ),
            "stage2_snapshot_packet_matches": manifest.get("packet_version")
            == workspace.packet_version,
            "stage2_exactly_two_reviewer_roles": sorted(manifest["reviewers"]) == sorted(REVIEW_ROLES),
            "stage2_item_coverage_matches_stage1": all(
                len(receipts[role]["judgements"])
                == len(stage1["receipts"][role]["judgements"])
                for role in REVIEW_ROLES
            ),
        }
    )
    failed = _failed(checks)
    if failed:
        raise WorkflowError(
            f"the committed Stage-2 evidence has changed since it was committed: {failed}"
        )
    return {
        "schema_version": REVIEW_INPUT_GRAPH_SCHEMA_VERSION,
        "stage": STAGE2,
        "stage1": stage1,
        "manifest": manifest,
        "stage2_snapshot_manifest_sha256": manifest_sha256(manifest),
        "receipts": receipts,
        "canonical_judgement_hashes": judgement_hashes,
        "snapshot_receipt_file_hashes": {
            role: manifest["reviewers"][role]["snapshot_receipt_file_sha256"]
            for role in REVIEW_ROLES
        },
        "stage2_issuance_hashes": {
            role: str(issuance[role]["receipt_sha256"]) for role in REVIEW_ROLES
        },
        "checks": checks,
    }


def review_input_graph(
    workspace: ReviewWorkspace,
    *,
    packet_commitment: str | None = None,
    scientific_freeze_sha256: str | None = None,
    exact_commit: str | None = None,
) -> dict[str, Any]:
    """The complete immutable input graph every late gate has to revalidate.

    Stage-1 and Stage-2 snapshots, both queues, both adjudications and the final
    records, each re-derived from what is on disk right now and compared against
    what the artifact that consumed it bound at the time.
    """

    stage2 = verify_committed_stage2_snapshot(
        workspace,
        expected_packet_commitment=packet_commitment,
        expected_scientific_freeze_sha256=scientific_freeze_sha256,
        expected_frozen_source_commit=exact_commit,
    )
    stage1 = stage2["stage1"]
    checks: dict[str, bool] = {}

    queues: dict[str, dict[str, Any] | None] = {}
    adjudications: dict[str, dict[str, Any] | None] = {}
    for stage in (STAGE1, STAGE2):
        queue = (
            workspace.read(f"{stage}_disagreement_queue")
            if workspace.has(f"{stage}_disagreement_queue")
            else None
        )
        queues[stage] = queue
        adjudication = (
            workspace.read(f"{stage}_adjudication")
            if workspace.has(f"{stage}_adjudication")
            else None
        )
        adjudications[stage] = adjudication
        source = stage1 if stage == STAGE1 else stage2
        checks[f"{stage}_queue_present"] = queue is not None or stage == STAGE2
        if queue is not None:
            checks[f"{stage}_queue_bound_to_committed_inputs"] = (
                queue.get("stage1_snapshot_manifest_sha256")
                == stage1["stage1_snapshot_manifest_sha256"]
                and queue.get("stage1_commitment_sha256") == stage1["stage1_commitment_sha256"]
                and dict(queue.get(f"{stage}_canonical_judgement_hashes") or {})
                == source["canonical_judgement_hashes"]
            )
            checks[f"{stage}_queue_content_unchanged"] = (
                queue.get("queue_content_sha256") == canonical_queue_digest(queue)
            )
        if adjudication is not None:
            if queue is None:
                checks[f"{stage}_adjudication_has_a_queue"] = False
            else:
                checks[f"{stage}_adjudication_answers_its_queue"] = (
                    str(adjudication.get("disagreement_queue_sha256"))
                    == str(queue.get("receipt_sha256"))
                    and str(adjudication.get("disagreement_queue_content_sha256"))
                    == canonical_queue_digest(queue)
                )
            checks[f"{stage}_adjudication_content_unchanged"] = (
                adjudication.get("adjudication_content_sha256")
                == canonical_adjudication_digest(adjudication)
            )

    final = (
        workspace.read("final_adjudicated_records")
        if workspace.has("final_adjudicated_records")
        else None
    )
    if final is not None:
        checks["final_records_bind_the_stage1_snapshot"] = (
            final.get("stage1_snapshot_manifest_sha256")
            == stage1["stage1_snapshot_manifest_sha256"]
        )
        checks["final_records_bind_the_stage2_snapshot"] = (
            final.get("stage2_snapshot_manifest_sha256")
            == stage2["stage2_snapshot_manifest_sha256"]
        )
        checks["final_records_match_adjudications"] = _content_digests(
            adjudications, canonical_adjudication_digest
        ) == dict(final.get("adjudication_content_hashes") or {})
        checks["final_records_match_queues"] = _content_digests(
            queues, canonical_queue_digest
        ) == dict(final.get("queue_content_hashes") or {})

    failed = _failed(checks)
    return {
        "schema_version": REVIEW_INPUT_GRAPH_SCHEMA_VERSION,
        "stage1": stage1,
        "stage2": stage2,
        "queues": queues,
        "adjudications": adjudications,
        "final": final,
        "checks": checks,
        "failed_checks": failed,
        "complete_input_graph_valid": not failed,
    }


# --------------------------------------------------------------------------
# C10
# --------------------------------------------------------------------------


def _raw_dimension_all(
    paired: dict[str, dict[str, dict[str, str]]], dimension: str, accepting: set[str]
) -> bool:
    if not paired:
        return False
    return all(
        all(str(row.get(dimension, "")).strip().casefold() in accepting for row in rows.values())
        for rows in paired.values()
    )


def _raw_scale_at_least(
    paired: dict[str, dict[str, dict[str, str]]], dimension: str, minimum: int
) -> bool:
    if not paired:
        return False
    for rows in paired.values():
        for row in rows.values():
            value = str(row.get(dimension, "")).strip()
            if not value.isdigit() or int(value) < minimum:
                return False
    return True


def _adjudicator_packages_bound(
    workspace: ReviewWorkspace,
    stage1_queue: dict[str, Any] | None,
    stage2_queue: dict[str, Any] | None,
    stage1_adj: dict[str, Any] | None,
    stage2_adj: dict[str, Any] | None,
) -> bool:
    """Every adjudicated stage decided the package that was actually issued."""

    for stage, queue, adjudication in (
        (STAGE1, stage1_queue, stage1_adj),
        (STAGE2, stage2_queue, stage2_adj),
    ):
        if queue is None or not queue["disputes"]:
            continue
        if adjudication is None or not workspace.has(f"{stage}_adjudicator_package"):
            return False
        issued = workspace.read(f"{stage}_adjudicator_package")
        if issued["disagreement_queue_sha256"] != queue["receipt_sha256"]:
            return False
        if adjudication.get("adjudicator_package_sha256") != issued["package_sha256"]:
            return False
        disputed = sorted({str(row["pair_id"]) for row in queue["disputes"]})
        if list(issued.get("disputed_pair_ids", [])) != disputed:
            return False
    return True


def run_c10(
    workspace: ReviewWorkspace,
    *,
    contract: dict[str, Any],
    mappings: dict[str, dict[str, str]],
    applicability: dict[str, dict[str, bool]],
    prerequisites: dict[str, bool],
    packet_commitment: str,
    scientific_freeze_sha256: str,
) -> dict[str, Any]:
    """Evaluate C10 from final adjudicated records and raw agreement only.

    The complete immutable input graph is verified *before* any check is
    computed.  If any committed receipt, snapshot, queue, adjudication or final
    record differs from what the artifact consuming it bound, C10 reports
    ``C10_MECHANICS_FAIL`` rather than scoring a mutated chain.
    """

    enforce_active_packet(
        packet_version=workspace.packet_version,
        commitment=packet_commitment,
        action="c10_evaluation",
    )
    expected_pairs = int(contract.get("expected_pair_count", 20))
    min_agreement = float(contract["min_raw_agreement"])
    min_clarity = int(contract.get("min_task_clarity", 3))

    try:
        graph = review_input_graph(
            workspace,
            packet_commitment=packet_commitment,
            scientific_freeze_sha256=scientific_freeze_sha256,
        )
    except (WorkflowError, CommitmentIntegrityError) as error:
        return _c10_input_graph_failure(workspace, contract, str(error))
    if not graph["complete_input_graph_valid"]:
        return _c10_input_graph_failure(
            workspace,
            contract,
            f"the committed review input graph is inconsistent: {graph['failed_checks']}",
        )

    eligibility = workspace.evidence_eligibility()
    commitment = graph["stage1"]["commitment"]
    agreement = workspace.read("agreement")
    final = workspace.read("final_adjudicated_records")
    registry_check = verify_registry_complete(workspace.assignments())

    stage1_raw = workspace._paired(mappings, STAGE1)
    stage2_present = workspace.has_committed_snapshot(STAGE2)
    stage2_raw = workspace._paired(mappings, STAGE2) if stage2_present else {}

    stage1_queue = workspace.read("stage1_disagreement_queue")
    stage2_queue = (
        workspace.read("stage2_disagreement_queue")
        if workspace.has("stage2_disagreement_queue")
        else None
    )
    stage1_adj = (
        workspace.read("stage1_adjudication") if workspace.has("stage1_adjudication") else None
    )
    stage2_adj = (
        workspace.read("stage2_adjudication") if workspace.has("stage2_adjudication") else None
    )

    def resolved(queue: dict[str, Any] | None, adjudication: dict[str, Any] | None) -> bool:
        if queue is None:
            return False
        if not queue["disputes"]:
            return True
        if adjudication is None:
            return False
        disputed = {f"{row['pair_id']}::{row['dimension']}" for row in queue["disputes"]}
        decided = {f"{row['pair_id']}::{row['dimension']}" for row in adjudication["decisions"]}
        return disputed <= decided

    def accepted_everywhere(stage: str, dimension: str) -> bool:
        included = [row for row in final["records"] if row["included"]]
        if not included:
            return False
        return all(row[stage].get(dimension, {}).get("accepted") is True for row in included)

    stage1_agreement = agreement["stage1"]
    stage2_agreement = agreement["stage2"]

    # Neither derived artifact is trusted: both are recomputed here from the
    # committed judgements, so a resealed report carrying a flattering number or
    # an extra included pair fails to reproduce and cannot be scored.
    recomputed_agreement = agreement_tables(stage1_raw, stage2_raw)
    recomputed_final = build_final_records(
        stage1_paired=stage1_raw,
        stage2_paired=stage2_raw,
        stage1_adjudication=stage1_adj,
        stage2_adjudication=stage2_adj,
        applicability=applicability,
        expected_pair_count=expected_pairs,
    )
    final_fields = (
        "records",
        "included_pair_ids",
        "included_count",
        "excluded_pairs",
        "excluded_count",
        "record_count",
        "unresolved",
        "provenance_counts",
        "checks",
    )

    issuance = workspace._stage2_issuance_hashes()
    stage2_submissions = dict(graph["stage2"]["receipts"]) if stage2_present else {}

    def issuance_bound_into(receipt: dict[str, Any] | None) -> bool:
        if receipt is None:
            return False
        return dict(receipt.get("stage2_issuance_hashes") or {}) == issuance

    checks: dict[str, bool] = {
        # -- the immutable input graph, verified before anything is scored
        "stage1_snapshot_manifest_valid": graph["stage1"]["checks"][
            "stage1_snapshot_manifest_valid"
        ],
        "stage1_receipt_hashes_match_commitment": graph["stage1"]["checks"][
            "stage1_receipt_hashes_match_commitment"
        ],
        "stage1_judgement_hashes_match_commitment": graph["stage1"]["checks"][
            "stage1_judgement_hashes_match_commitment"
        ],
        "stage1_payload_hashes_match_commitment": graph["stage1"]["checks"][
            "stage1_payload_hashes_match_commitment"
        ],
        "stage1_live_receipts_not_conflicting": graph["stage1"]["checks"][
            "stage1_live_receipts_not_conflicting"
        ],
        "stage1_commitment_schema_is_active": commitment.get("commitment_schema_version")
        == STAGE1_COMMITMENT_SCHEMA_VERSION,
        "stage2_issuance_bound_to_stage1_snapshot": graph["stage2"]["checks"][
            "stage2_issuance_bound_to_the_stage1_snapshot"
        ],
        "stage2_submission_receipts_immutable": graph["stage2"]["checks"][
            "stage2_snapshot_receipt_hashes_match_manifest"
        ]
        and graph["stage2"]["checks"]["stage2_judgement_hashes_match_manifest"]
        and graph["stage2"]["checks"]["stage2_live_receipts_not_conflicting"],
        "adjudication_inputs_match_queues": all(
            value
            for name, value in graph["checks"].items()
            if name.endswith(
                (
                    "_adjudication_answers_its_queue",
                    "_queue_bound_to_committed_inputs",
                    "_queue_content_unchanged",
                    "_adjudication_content_unchanged",
                )
            )
        ),
        "final_records_match_adjudications": bool(
            graph["checks"].get("final_records_match_adjudications")
        ),
        "final_records_reproduce_from_committed_inputs": all(
            final.get(name) == recomputed_final[name] for name in final_fields
        ),
        "agreement_reproduces_from_committed_judgements": all(
            agreement.get(stage) == recomputed_agreement[stage] for stage in ("stage1", "stage2")
        ),
        "complete_input_graph_valid": graph["complete_input_graph_valid"],
        # -- reviewer prerequisites
        "two_distinct_reviewers_assigned": registry_check["checks"]["both_reviewers_assigned"],
        "separate_adjudicator_assigned": registry_check["checks"]["adjudicator_assigned"],
        "no_role_overlap": registry_check["checks"]["all_roles_held_by_distinct_people"],
        "assignment_registry_valid": registry_check["passed"],
        "assignment_registry_unchanged_since_commitment": commitment[
            "assignment_registry_sha256"
        ]
        == workspace.assignments()["registry_sha256"],
        "both_declarations_valid": len(commitment["declaration_hashes"]) == 2,
        "both_reviewers_qualified_privately": len(commitment["qualification_receipt_hashes"]) == 2,
        "qualification_version_is_active": all(
            workspace.read(f"qualification_{role}").get("qualification_version")
            == QUALIFICATION_SCHEMA_VERSION
            for role in REVIEW_ROLES
        ),
        "stage1_submissions_complete": len(commitment["stage1_submission_payload_hashes"]) == 2,
        "stage2_submissions_complete": stage2_present,
        "package_hashes_bound_to_assignments": eligibility["bindings"]["correct_package_hash"],
        "reviewer_namespaces_correct": eligibility["bindings"]["correct_reviewer_namespace"],
        # -- Stage-2 issuance, bound end to end
        "stage2_issuance_receipts_issued": set(issuance) == set(REVIEW_ROLES),
        "stage2_issuance_bound_to_submissions": bool(stage2_submissions)
        and all(
            stage2_submissions[role].get("stage2_issuance_sha256") == issuance.get(role)
            for role in REVIEW_ROLES
            if role in stage2_submissions
        )
        and set(stage2_submissions) == set(REVIEW_ROLES),
        "stage2_issuance_matches_stage1_commitment": bool(issuance)
        and all(
            workspace.read(f"stage2_issuance_{role}")["stage1_commitment_sha256"]
            == graph["stage1"]["stage1_commitment_sha256"]
            for role in issuance
        ),
        "stage2_issuance_bound_into_queue": issuance_bound_into(stage2_queue),
        "stage2_issuance_bound_into_final_records": issuance_bound_into(final),
        "stage2_issuance_bound_into_adjudication": (
            stage2_queue is not None and not stage2_queue["disputes"]
        )
        or issuance_bound_into(stage2_adj),
        "adjudicator_packages_bound_to_their_queues": _adjudicator_packages_bound(
            workspace, stage1_queue, stage2_queue, stage1_adj, stage2_adj
        ),
        # -- Stage 1
        "full_pair_coverage": len(stage1_raw) == expected_pairs,
        "stage2_covers_every_stage1_pair": set(stage2_raw) == set(stage1_raw)
        and len(stage2_raw) == expected_pairs,
        "task_clarity_meets_threshold": _raw_scale_at_least(stage1_raw, "task_clarity", min_clarity),
        "intervention_comprehensible": _raw_dimension_all(
            stage1_raw, "intervention_understandable", {"yes"}
        ),
        "clean_solvability_accepted": accepted_everywhere(STAGE1, "clean_solvable"),
        "evidence_sufficiency_accepted": accepted_everywhere(STAGE1, "clean_evidence_sufficient"),
        "goal_preservation_accepted": accepted_everywhere(STAGE1, "goal_preserved"),
        "single_factor_isolation_accepted": accepted_everywhere(STAGE1, "single_factor_isolation"),
        "preserved_invariants_accepted": accepted_everywhere(STAGE1, "preserved_invariants_hold"),
        "primitive_evidence_accepted": accepted_everywhere(STAGE1, "primitive_evidence_adequate"),
        "stage1_disagreements_resolved": resolved(stage1_queue, stage1_adj),
        # -- Stage 2
        "gold_correctness_accepted": accepted_everywhere(STAGE2, "gold_correct"),
        "accepted_variants_complete": accepted_everywhere(STAGE2, "accepted_variants_complete"),
        "answer_contracts_accepted": accepted_everywhere(STAGE2, "answer_contract_valid"),
        "scorer_compatibility_accepted": accepted_everywhere(STAGE2, "scorer_compatible"),
        "intervention_policy_accepted": accepted_everywhere(STAGE2, "intervention_policy_valid"),
        "route_policy_accepted": accepted_everywhere(STAGE2, "route_policy_defensible"),
        "recovery_policy_accepted_where_applicable": accepted_everywhere(
            STAGE2, "recovery_authorization_valid_or_not_applicable"
        ),
        "abstention_policy_accepted_where_applicable": accepted_everywhere(
            STAGE2, "abstention_policy_valid_or_not_applicable"
        ),
        "clarification_policy_accepted_where_applicable": accepted_everywhere(
            STAGE2, "clarification_policy_valid_or_not_applicable"
        ),
        "stage2_applicability_map_covers_every_pair": bool(applicability)
        and all(str(row["pair_id"]) in applicability for row in final["records"]),
        "no_unresolved_stage2_objection": bool(final["records"])
        and not any(row["blocked_dimensions"] for row in final["records"]),
        "stage2_disagreements_resolved": resolved(stage2_queue, stage2_adj),
        # -- final records and exclusions
        "final_records_built_for_every_pair": final["checks"][
            "every_expected_pair_has_a_final_record"
        ],
        "final_records_have_no_unresolved_dimension": final["checks"]["no_unresolved_dimensions"],
        "exclusions_applied": final["included_count"] + final["excluded_count"] == expected_pairs,
        "included_slice_non_empty": final["included_count"] > 0,
        # -- agreement, from raw independent judgements only
        "agreement_computed_from_raw_judgements": agreement["adjudicated_values_used"] is False,
        "stage1_agreement_meets_threshold": stage1_agreement["overall_raw_agreement"]
        >= min_agreement,
        "stage2_agreement_meets_threshold": bool(stage2_agreement["per_dimension"])
        and stage2_agreement["overall_raw_agreement"] >= min_agreement,
        "every_stage1_dimension_meets_threshold": bool(stage1_agreement["per_dimension"])
        and all(
            row["raw_agreement"] >= min_agreement
            for row in stage1_agreement["per_dimension"].values()
        ),
        "every_stage2_dimension_meets_threshold": bool(stage2_agreement["per_dimension"])
        and all(
            row["raw_agreement"] >= min_agreement
            for row in stage2_agreement["per_dimension"].values()
        ),
        # -- authenticity, derived from provenance rather than from a mode flag
        "artifact_origin_is_production": workspace.is_production,
        "every_required_evidence_binding_present": not eligibility["missing_bindings"],
        "evidence_counts_as_genuine": eligibility["counts_as_genuine_evidence"],
        # -- binding to the frozen packet and code
        "packet_commitment_matches": commitment["private_packet_commitment"] == packet_commitment,
        "freeze_hash_matches": commitment["scientific_freeze_sha256"] == scientific_freeze_sha256,
        "prerequisites_satisfied": bool(prerequisites) and all(prerequisites.values()),
    }

    passed = all(checks.values())
    # Mechanics status lets the fixture end-to-end test prove the pipeline works
    # without ever producing a genuine C10 pass.  It excludes exactly the checks
    # that a fixture cannot satisfy by construction, and nothing else.
    fixture_exempt = {
        "artifact_origin_is_production",
        "every_required_evidence_binding_present",
        "evidence_counts_as_genuine",
    }
    mechanics = all(value for name, value in checks.items() if name not in fixture_exempt)
    return {
        "schema_version": "cab_review_ready_v2_c10_report_v2",
        "workflow_schema_version": WORKFLOW_SCHEMA_VERSION,
        "claim_id": "C10",
        "status": "C10_PASS" if passed else "C10_PENDING_GENUINE_REVIEW",
        "mechanics_status": "C10_MECHANICS_PASS" if mechanics else "C10_MECHANICS_FAIL",
        "evidence_class": contract["evidence_class_on_pass"] if passed else "NO_GENUINE_EVIDENCE",
        "counts_as_genuine_evidence": passed and eligibility["counts_as_genuine_evidence"],
        "artifact_origin": workspace.authority.origin,
        "checks": checks,
        "failed_checks": sorted(name for name, value in checks.items() if not value),
        "evidence_eligibility": eligibility,
        "stage1_agreement": stage1_agreement["per_dimension"],
        "stage2_agreement": stage2_agreement["per_dimension"],
        "included_count": final["included_count"],
        "excluded_count": final["excluded_count"],
        "passed": passed,
    }


def _c10_input_graph_failure(
    workspace: ReviewWorkspace, contract: dict[str, Any], detail: str
) -> dict[str, Any]:
    """A C10 report for a chain that no longer matches what was committed.

    Deliberately a report and not an exception: a mutated chain must produce a
    visible, recorded ``C10_MECHANICS_FAIL`` rather than a traceback a caller
    could catch and interpret as "not applicable".
    """

    checks = {"complete_input_graph_valid": False}
    return {
        "schema_version": "cab_review_ready_v2_c10_report_v2",
        "workflow_schema_version": WORKFLOW_SCHEMA_VERSION,
        "claim_id": "C10",
        "status": "C10_PENDING_GENUINE_REVIEW",
        "mechanics_status": "C10_MECHANICS_FAIL",
        "evidence_class": "NO_GENUINE_EVIDENCE",
        "counts_as_genuine_evidence": False,
        "artifact_origin": workspace.authority.origin,
        "checks": checks,
        "failed_checks": ["complete_input_graph_valid"],
        "input_graph_failure": detail,
        "evidence_eligibility": {
            "schema_version": "cab_review_ready_v2_evidence_eligibility_v1",
            "artifact_origin": workspace.authority.origin,
            "required_bindings": list(REQUIRED_EVIDENCE_BINDINGS),
            "bindings": dict.fromkeys(REQUIRED_EVIDENCE_BINDINGS, False),
            "missing_bindings": sorted(REQUIRED_EVIDENCE_BINDINGS),
            "counts_as_genuine_evidence": False,
        },
        "stage1_agreement": {},
        "stage2_agreement": {},
        "included_count": 0,
        "excluded_count": 0,
        "passed": False,
    }


def build_exclusion_register(workspace: ReviewWorkspace) -> dict[str, Any]:
    """Read exclusions off the final adjudicated records, not off raw rows."""

    workspace._require_valid_input_graph("the exclusion register")
    final = workspace.read("final_adjudicated_records")
    graph = workspace._input_graph_bindings()
    return workspace.write(
        "exclusion_register",
        {
            "receipt_kind": "exclusion_register",
            "derived_from": "final_adjudicated_records",
            "final_records_sha256": final["receipt_sha256"],
            "final_records_content_sha256": receipt_content_sha256(final),
            **graph,
            "included_pair_ids": final["included_pair_ids"],
            "excluded_pairs": final["excluded_pairs"],
            "included_count": final["included_count"],
            "excluded_count": final["excluded_count"],
        },
    )


def lock_reviewed_slice(
    workspace: ReviewWorkspace,
    *,
    c10_report: dict[str, Any],
    packet_commitment: str,
    scorer_sha256: str,
    endpoints_sha256: str,
    analysis_plan_sha256: str,
    system_identity_sha256: str,
    scientific_freeze_sha256: str,
    exact_commit: str,
) -> dict[str, Any]:
    genuine_pass = c10_report.get("status") == "C10_PASS"
    fixture_mechanics = (
        not workspace.is_production and c10_report.get("mechanics_status") == "C10_MECHANICS_PASS"
    )
    if not (genuine_pass or fixture_mechanics):
        raise WorkflowError("the reviewed slice cannot be locked before C10 passes")
    if genuine_pass and not workspace.is_production:
        raise WorkflowError("a fixture workspace can never produce a genuine C10 pass")
    if genuine_pass and not c10_report.get("counts_as_genuine_evidence"):
        raise WorkflowError("a C10 pass that does not count as genuine evidence cannot lock a slice")
    enforce_active_packet(
        packet_version=workspace.packet_version, commitment=packet_commitment, action="slice_lock"
    )
    # Everything the C10 report was computed from is re-verified here, from disk,
    # before a single hash is copied into the lock.
    graph = review_input_graph(
        workspace,
        packet_commitment=packet_commitment,
        scientific_freeze_sha256=scientific_freeze_sha256,
        exact_commit=exact_commit,
    )
    if not graph["complete_input_graph_valid"]:
        raise WorkflowError(
            f"the reviewed slice cannot be locked over a changed input graph: {graph['failed_checks']}"
        )
    register = workspace.read("exclusion_register")
    commitment = graph["stage1"]["commitment"]
    final = graph["final"]
    if final is None:
        raise WorkflowError("the reviewed slice cannot be locked before the final records exist")
    registry = workspace.assignments()
    stage2 = graph["stage2"]
    stage2_submissions = {
        role: str(stage2["receipts"][role]["submission_sha256"]) for role in REVIEW_ROLES
    }
    stage2_issuance = workspace._stage2_issuance_hashes()
    if set(stage2_issuance) != set(REVIEW_ROLES):
        raise WorkflowError(
            "the reviewed slice cannot be locked without a sealed Stage-2 issuance receipt for "
            "both reviewers"
        )
    if register.get("final_records_content_sha256") != receipt_content_sha256(final):
        raise WorkflowError(
            "the exclusion register was derived from a different set of final adjudicated records"
        )
    return workspace.write(
        "slice_lock",
        {
            "receipt_kind": "reviewed_slice_lock",
            "stage2_issuance_hashes": stage2_issuance,
            "stage2_package_hashes": {
                role: workspace.read(f"stage2_issuance_{role}")["stage2_package_sha256"]
                for role in REVIEW_ROLES
            },
            "stage1_adjudicator_package_sha256": workspace.read("stage1_adjudicator_package")[
                "package_sha256"
            ]
            if workspace.has("stage1_adjudicator_package")
            else None,
            "stage2_adjudicator_package_sha256": workspace.read("stage2_adjudicator_package")[
                "package_sha256"
            ]
            if workspace.has("stage2_adjudicator_package")
            else None,
            "included_pair_ids": register["included_pair_ids"],
            "excluded_pairs": register["excluded_pairs"],
            "private_packet_commitment": packet_commitment,
            "assignment_registry_sha256": registry["registry_sha256"],
            "declaration_hashes": commitment["declaration_hashes"],
            "qualification_receipt_hashes": commitment["qualification_receipt_hashes"],
            "stage1_submission_payload_hashes": commitment["stage1_submission_payload_hashes"],
            "stage1_submission_receipt_hashes": commitment["stage1_submission_receipt_hashes"],
            "stage1_canonical_judgement_hashes": graph["stage1"]["canonical_judgement_hashes"],
            "stage1_snapshot_manifest_sha256": graph["stage1"]["stage1_snapshot_manifest_sha256"],
            "stage1_snapshot_receipt_hashes": graph["stage1"]["snapshot_receipt_file_hashes"],
            "stage1_commitment_sha256": graph["stage1"]["stage1_commitment_sha256"],
            "stage2_snapshot_manifest_sha256": stage2["stage2_snapshot_manifest_sha256"],
            "stage2_snapshot_receipt_hashes": stage2["snapshot_receipt_file_hashes"],
            "stage2_canonical_judgement_hashes": stage2["canonical_judgement_hashes"],
            "stage2_submission_hashes": stage2_submissions,
            "queue_content_hashes": _content_digests(graph["queues"], canonical_queue_digest),
            "adjudication_content_hashes": _content_digests(
                graph["adjudications"], canonical_adjudication_digest
            ),
            "final_adjudicated_records_content_sha256": receipt_content_sha256(final),
            "exclusion_register_content_sha256": receipt_content_sha256(register),
            "stage1_adjudication_sha256": workspace.read("stage1_adjudication")["receipt_sha256"]
            if workspace.has("stage1_adjudication")
            else None,
            "stage2_adjudication_sha256": workspace.read("stage2_adjudication")["receipt_sha256"]
            if workspace.has("stage2_adjudication")
            else None,
            "final_adjudicated_records_sha256": final["receipt_sha256"],
            "exclusion_register_sha256": register["receipt_sha256"],
            "c10_report_sha256": sha256_json(c10_report),
            "c10_schema_version": c10_report["schema_version"],
            "scorer_sha256": scorer_sha256,
            "endpoints_sha256": endpoints_sha256,
            "analysis_plan_sha256": analysis_plan_sha256,
            "system_identity_schema_sha256": system_identity_sha256,
            "scientific_freeze_sha256": scientific_freeze_sha256,
            "exact_commit": exact_commit,
            "locked": True,
        },
    )


def authorize_model_execution(
    workspace: ReviewWorkspace,
    *,
    exact_commit: str,
    scientific_freeze_sha256: str,
    c10_report: dict[str, Any] | None = None,
    external_attestation_present: bool = False,
) -> dict[str, Any]:
    if not workspace.has("slice_lock"):
        raise WorkflowError("model execution is blocked: no reviewed-slice lock receipt exists")
    lock = workspace.read("slice_lock")
    report = c10_report or workspace.read("c10_report")
    # ``locked: true`` is a claim, not a proof.  The whole chain is re-derived
    # from disk and compared against what the lock bound, so a change to any
    # upstream artifact after the lock — including a reviewer note that gates
    # nothing — refuses execution.
    graph = review_input_graph(
        workspace,
        packet_commitment=str(lock.get("private_packet_commitment") or ""),
        scientific_freeze_sha256=scientific_freeze_sha256,
        exact_commit=exact_commit,
    )
    final = graph["final"]
    register = workspace.read("exclusion_register")
    locked_hashes = {
        "stage1_snapshot_manifest_sha256": graph["stage1"]["stage1_snapshot_manifest_sha256"],
        "stage1_snapshot_receipt_hashes": graph["stage1"]["snapshot_receipt_file_hashes"],
        "stage1_canonical_judgement_hashes": graph["stage1"]["canonical_judgement_hashes"],
        "stage1_commitment_sha256": graph["stage1"]["stage1_commitment_sha256"],
        "stage2_snapshot_manifest_sha256": graph["stage2"]["stage2_snapshot_manifest_sha256"],
        "stage2_snapshot_receipt_hashes": graph["stage2"]["snapshot_receipt_file_hashes"],
        "stage2_canonical_judgement_hashes": graph["stage2"]["canonical_judgement_hashes"],
        "queue_content_hashes": _content_digests(graph["queues"], canonical_queue_digest),
        "adjudication_content_hashes": _content_digests(
            graph["adjudications"], canonical_adjudication_digest
        ),
    }
    checks = {
        "complete_input_graph_valid": graph["complete_input_graph_valid"],
        "immutable_chain_unchanged_since_lock": all(
            lock.get(name) == value for name, value in locked_hashes.items()
        ),
        "final_records_unchanged_since_lock": final is not None
        and lock.get("final_adjudicated_records_content_sha256") == receipt_content_sha256(final),
        "exclusion_register_unchanged_since_lock": lock.get("exclusion_register_content_sha256")
        == receipt_content_sha256(register),
        "assignment_registry_unchanged_since_lock": lock.get("assignment_registry_sha256")
        == workspace.assignments()["registry_sha256"],
        "declarations_unchanged_since_lock": dict(lock.get("declaration_hashes") or {})
        == dict(graph["stage1"]["commitment"]["declaration_hashes"]),
        "qualifications_unchanged_since_lock": dict(
            lock.get("qualification_receipt_hashes") or {}
        )
        == dict(graph["stage1"]["commitment"]["qualification_receipt_hashes"]),
        "slice_locked": bool(lock.get("locked")),
        "commit_matches_lock": lock.get("exact_commit") == exact_commit,
        "freeze_matches_lock": lock.get("scientific_freeze_sha256") == scientific_freeze_sha256,
        "artifact_origin_matches_workspace": lock.get("artifact_origin") == workspace.authority.origin,
        "c10_report_matches_lock": lock.get("c10_report_sha256") == sha256_json(report),
        "c10_is_not_stale": report.get("schema_version") == lock.get("c10_schema_version"),
        "c10_belongs_to_this_packet": report.get("packet_version", workspace.packet_version)
        == workspace.packet_version,
        "stage2_complete": bool(lock.get("stage2_submission_hashes")),
        "stage2_issuance_bound_into_lock": set(lock.get("stage2_issuance_hashes") or {})
        == set(REVIEW_ROLES),
        "stage2_issuance_unchanged_since_lock": dict(lock.get("stage2_issuance_hashes") or {})
        == workspace._stage2_issuance_hashes(),
        "no_unresolved_objection": bool(lock.get("included_pair_ids")),
        "genuine_evidence_required_in_production": (not workspace.is_production)
        or lock.get("counts_as_genuine_evidence") is True,
        "external_attestation_present": (not workspace.is_production) or external_attestation_present,
        "included_slice_non_empty": bool(lock.get("included_pair_ids")),
    }
    if not all(checks.values()):
        raise WorkflowError(
            f"model execution refused: {sorted(name for name, value in checks.items() if not value)}"
        )
    return workspace.write(
        "execution_authorization",
        {"receipt_kind": "model_execution_authorization", "checks": checks, "authorized": True},
    )


def workflow_status(workspace: ReviewWorkspace) -> dict[str, Any]:
    """Public-safe status. Reports stage completion only, never review content."""

    stages = {
        "reviewer_assignments": len(workspace.assignments().get("assignments", {})),
        "declaration_receipts": sum(1 for _ in workspace.receipts.glob("declaration_REVIEWER_*.json")),
        "qualification_receipts": sum(1 for _ in workspace.receipts.glob("qualification_*.json")),
        "stage1_submissions": sum(1 for _ in workspace.receipts.glob("stage1_submission_*.json")),
        "stage1_committed": workspace.has("stage1_commitment"),
        "stage1_snapshot_frozen": workspace.has_committed_snapshot(STAGE1),
        "stage2_unlocked": workspace.has("stage2_unlock"),
        "stage2_snapshot_frozen": workspace.has_committed_snapshot(STAGE2),
        "stage2_issuance_receipts": sum(
            1 for _ in workspace.receipts.glob("stage2_issuance_REVIEWER_*.json")
        ),
        "stage2_submissions": sum(1 for _ in workspace.receipts.glob("stage2_submission_*.json")),
        "stage1_disagreement_queue_built": workspace.has("stage1_disagreement_queue"),
        "stage2_disagreement_queue_built": workspace.has("stage2_disagreement_queue"),
        "stage1_adjudicator_package_issued": workspace.has("stage1_adjudicator_package"),
        "stage2_adjudicator_package_issued": workspace.has("stage2_adjudicator_package"),
        "stage1_adjudicated": workspace.has("stage1_adjudication"),
        "stage2_adjudicated": workspace.has("stage2_adjudication"),
        "agreement_computed": workspace.has("agreement"),
        "final_records_built": workspace.has("final_adjudicated_records"),
        "exclusion_register_built": workspace.has("exclusion_register"),
        "slice_locked": workspace.has("slice_lock"),
        "execution_authorized": workspace.has("execution_authorization"),
    }
    c10_status = "C10_PENDING_GENUINE_REVIEW"
    if workspace.has("c10_report"):
        try:
            c10_status = str(workspace.read("c10_report").get("status", c10_status))
        except WorkflowError:
            c10_status = "C10_PENDING_GENUINE_REVIEW"
    return {
        "schema_version": "cab_review_ready_v2_workflow_status_v2",
        "workflow_schema_version": WORKFLOW_SCHEMA_VERSION,
        "artifact_origin": workspace.authority.origin,
        "stages": stages,
        "c10_status": c10_status,
        "model_execution": "MODEL_EXECUTION_AUTHORIZED"
        if stages["execution_authorized"]
        else "MODEL_EXECUTION_BLOCKED",
        "private_content_disclosed": False,
    }


__all__ = [
    "GATING_DIMENSIONS",
    "REQUIRED_EVIDENCE_BINDINGS",
    "RETIRED_WORKFLOW_SCHEMA_VERSIONS",
    "REVIEWER_A",
    "REVIEWER_B",
    "STAGE1_COMMITMENT_SCHEMA_VERSION",
    "STAGE2_FORM_COLUMNS",
    "WORKFLOW_SCHEMA_VERSION",
    "ReviewWorkspace",
    "WorkflowError",
    "authorize_model_execution",
    "build_exclusion_register",
    "lock_reviewed_slice",
    "parse_review_csv",
    "review_input_graph",
    "run_c10",
    "validate_stage1_submission",
    "validate_stage2_submission",
    "verify_committed_stage1_snapshot",
    "verify_committed_stage2_snapshot",
    "workflow_status",
]
