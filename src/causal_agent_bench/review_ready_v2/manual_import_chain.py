"""The immutable manual offline-import chain, and its C10-equivalent gate.

The production workflow in :mod:`workflow` issues a package, collects a signed
reviewer declaration, scores a private qualification, then accepts a submission
that names all three.  The Compact-20 review did not happen that way: the
reviewers completed the substantive forms through simplified offline HTML pages,
so no declaration was collected and no issue receipt preceded the judgements.

Rather than fake the missing steps — which would make the scientific record a
lie about its own provenance — this module implements a *separate*, explicitly
versioned import path that says exactly what happened.  It reuses the production
scientific functions unchanged (queue construction, adjudication validation,
final-record derivation, agreement) so the science is identical, while sealing
everything under a distinct authority whose origin is
``MANUAL_OFFLINE_REVIEW_IMPORT_V1``.  A manual-import receipt can never
authenticate against a production gate, and the production commands are left
exactly as strict as they were.

What the coordinator waives is recorded, not hidden: a sealed waiver names each
element that was not collected, and every downstream artifact — C10, the
exclusion register, the slice lock, the execution authorization — carries the
waiver forward by hash.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2.adjudication import (
    STAGE1,
    STAGE2,
    AdjudicationError,
    build_stage1_queue,
    build_stage2_queue,
    validate_adjudication,
)
from causal_agent_bench.review_ready_v2.commitment_integrity import (
    CommitmentIntegrityError,
    assert_contained,
    assert_private_mode,
    assert_regular_file,
    canonical_queue_digest,
    create_submission_snapshot,
    manifest_sha256,
    read_snapshot_manifest,
    read_snapshot_receipts,
    receipt_content_sha256,
    snapshot_exists,
    write_private_json,
)
from causal_agent_bench.review_ready_v2.common import read_json, sha256_bytes, sha256_json
from causal_agent_bench.review_ready_v2.final_records import (
    FinalRecordError,
    build_final_records,
)
from causal_agent_bench.review_ready_v2.manual_import import (
    ADJUDICATION_COLUMNS,
    QUALIFICATION_FORM,
    STAGE1_ADJUDICATION,
    STAGE2_ADJUDICATION,
    Candidate,
    read_csv_rows,
)
from causal_agent_bench.review_ready_v2.qualification import (
    QualificationError,
    enforce_active_qualification,
    score_qualification,
)
from causal_agent_bench.review_ready_v2.receipts import (
    Authority,
    ReceiptError,
    manual_import_authority,
    receipt_is_fixture,
    seal_receipt,
    verify_receipt,
)
from causal_agent_bench.review_ready_v2.roles import REVIEW_ROLES
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_FORM_COLUMNS
from causal_agent_bench.review_ready_v2.stage2 import (
    STAGE2_FORM_COLUMNS,
    validate_stage2_submission,
)
from causal_agent_bench.review_ready_v2.workflow import (
    agreement_tables,
    parse_review_csv,
    validate_stage1_submission,
)

IMPORT_CHAIN_SCHEMA_VERSION = "cab_manual_offline_import_chain_v1"
IMPORT_COMMITMENT_SCHEMA_VERSION = "cab_manual_offline_import_commitment_v1"
IMPORT_WAIVER_SCHEMA_VERSION = "cab_coordinator_review_waiver_v1"
IMPORT_C10_SCHEMA_VERSION = "cab_manual_offline_import_c10_v1"
IMPORT_QUALIFICATION_SCHEMA_VERSION = "cab_manual_offline_import_qualification_v1"

#: The import epoch a workspace opens by default.  An epoch names one complete
#: attempt at importing a review: its receipts live in their own directory *and*
#: carry the epoch inside the sealed payload, so a receipt from an abandoned
#: epoch cannot be moved into a later one and still authenticate.  Correcting an
#: import means starting a new epoch, never editing a sealed receipt in place.
DEFAULT_IMPORT_EPOCH = "v1"

#: The literal opt-in flags a caller must pass.  Two flags, not one, so that
#: neither an accidental re-run nor a copied command line can activate this path.
REQUIRED_OPT_IN_FLAGS: tuple[str, ...] = (
    "--manual-offline-import",
    "--coordinator-declaration-waiver",
)

#: What the coordinator is waiving, named individually.  Anything not on this
#: list has not been waived and still gates normally.
WAIVED_ELEMENTS: tuple[str, ...] = (
    "reviewer_declaration_files",
    "production_issue_receipts",
    "qualification_submission_evidence",
)

#: Status strings.  The chain never emits ``REVIEWER_DECLARATIONS_CONFIRMED``,
#: because no declaration was collected.  A qualification pass is claimed only
#: when genuine submissions were scored against the private answer key.
DECLARATION_WAIVER_STATUS = "COORDINATOR_DECLARATION_WAIVER_RECORDED"
QUALIFICATION_WAIVER_STATUS = "COORDINATOR_QUALIFICATION_EVIDENCE_WAIVER_RECORDED"
C10_PASS_STATUS = "C10_MECHANICS_PASS_WITH_COORDINATOR_WAIVERS"
C10_PASS_STATUS_DECLARATION_ONLY = "C10_MECHANICS_PASS_WITH_COORDINATOR_DECLARATION_WAIVER"
C10_FAIL_STATUS = "C10_MECHANICS_FAIL"

#: How the qualification screen was established.  ``GENUINE_VERIFIED_SUBMISSIONS``
#: means both reviewers' completed submissions were scored against the private
#: answer key in this chain; ``COORDINATOR_WAIVER`` means none was imported and
#: no rate is claimed anywhere.
QUALIFICATION_MODE_GENUINE = "GENUINE_VERIFIED_SUBMISSIONS"
QUALIFICATION_MODE_WAIVED = "COORDINATOR_WAIVER"

#: Receipts that record a completed one-way transition.  Write-once, always.
_SEALED_NAMES: frozenset[str] = frozenset(
    {
        "coordinator_waiver",
        "import_manifest",
        "qualification_REVIEWER_A",
        "qualification_REVIEWER_B",
        "qualification_commitment",
        "stage1_submission_REVIEWER_A",
        "stage1_submission_REVIEWER_B",
        "stage1_commitment",
        "stage2_submission_REVIEWER_A",
        "stage2_submission_REVIEWER_B",
        "stage2_commitment",
        "stage1_disagreement_queue",
        "stage2_disagreement_queue",
        "stage1_adjudication",
        "stage2_adjudication",
        "agreement",
        "final_adjudicated_records",
        "exclusion_register",
        "slice_lock",
        "execution_authorization",
    }
)

_FORM_COLUMNS = {STAGE1: REVIEW_FORM_COLUMNS, STAGE2: STAGE2_FORM_COLUMNS}

_IMPORT_JUDGEMENTS_DIGEST = "cab_manual_import_judgements_canonical_v1"


def _canonical_import_judgements_digest(receipt: dict[str, Any], *, stage: str) -> str:
    """Deterministic digest of one reviewer's imported content for ``stage``.

    The production digest binds the declaration, qualification and issuance
    hashes a production receipt carries.  Imported evidence has none of those —
    that is the whole point of the separate origin — so this digest binds what
    imported evidence *does* have: every parsed cell, the row count, the
    validation outcome, the role, the opaque namespace, the raw payload hash, the
    canonical content hash, and the coordinator waiver that authorized the import.

    Keeping the payload hash *inside* the digest is what defeats the substitution
    attack: retaining the original ``submission_sha256`` while editing a single
    judgement still changes the digest.  Binding the canonical hash too means the
    reverse — keeping the canonical hash while changing the bytes — fails as well.
    """

    columns = _FORM_COLUMNS[stage]
    judgements = receipt.get("judgements")
    if not isinstance(judgements, dict) or not judgements:
        raise ImportChainError(f"the imported {stage} receipt carries no parsed judgements")
    rows: dict[str, dict[str, str]] = {}
    for raw_id, row in judgements.items():
        item_id = str(raw_id).strip()
        if not item_id:
            raise ImportChainError(f"the imported {stage} receipt carries an empty item id")
        if item_id in rows:
            raise ImportChainError(
                f"the imported {stage} receipt carries duplicate rows for {item_id}"
            )
        if not isinstance(row, dict):
            raise ImportChainError(f"the imported {stage} row for {item_id} is not an object")
        missing = sorted(column for column in columns if column not in row)
        unexpected = sorted(set(row) - set(columns))
        if missing or unexpected:
            raise ImportChainError(
                f"the imported {stage} row for {item_id} does not match the issued column layout "
                f"(missing={missing}, unexpected={unexpected})"
            )
        rows[item_id] = {column: str(row[column]).strip() for column in columns}

    row_count = receipt.get("row_count")
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count != len(rows):
        raise ImportChainError(
            f"the imported {stage} receipt declares a row count that does not match its rows"
        )
    validation = receipt.get("validation")
    if not isinstance(validation, dict):
        raise ImportChainError(f"the imported {stage} validation block is malformed")
    return sha256_json(
        {
            "digest_kind": _IMPORT_JUDGEMENTS_DIGEST,
            "stage": stage,
            "import_origin": str(receipt.get("import_origin", "")),
            "reviewer_role": str(receipt.get("reviewer_role", "")),
            "opaque_id_namespace": str(receipt.get("opaque_id_namespace", "")),
            "columns": list(columns),
            "payload_sha256": str(receipt.get("submission_sha256", "")),
            "canonical_content_sha256": str(receipt.get("canonical_content_sha256", "")),
            "coordinator_waiver_sha256": str(receipt.get("coordinator_waiver_sha256", "")),
            "declaration_collected": bool(receipt.get("declaration_collected")),
            "issue_receipt_available": bool(receipt.get("issue_receipt_available")),
            "row_count": row_count,
            "reviewer_item_ids": sorted(rows),
            "validation": {key: bool(value) for key, value in sorted(validation.items())},
            # Stage-2 substance, when the receipt carries it.  Absent for
            # Stage 1, which has no separate acceptance block.
            "stage2_substance": {
                key: receipt[key]
                for key in (
                    "form_schema_version",
                    "acceptance_policy_version",
                    "form_complete",
                    "blocking_value_count",
                    "substantively_accepted_without_adjudication",
                )
                if key in receipt
            },
            "judgements": rows,
        }
    )


_IMPORT_ADJUDICATION_DIGEST = "cab_manual_import_adjudication_canonical_v1"


def canonical_import_adjudication_digest(receipt: dict[str, Any]) -> str:
    """Deterministic digest of an imported adjudication's decided content.

    Covers every decision — pair, dimension, final value, rationale, evidence
    reference, confidence and exclusion flag — so a changed rationale is exactly
    as detectable as a changed verdict.  It binds the queue the decisions answer
    and the raw submission bytes, but not the adjudicator package or pseudonym
    hashes a production adjudication carries, because this evidence has neither.
    """

    stage = str(receipt.get("stage", "")).strip()
    if stage not in (STAGE1, STAGE2):
        raise ImportChainError(f"unknown adjudication stage {stage!r}")
    decisions = receipt.get("decisions")
    if not isinstance(decisions, list):
        raise ImportChainError(f"the imported {stage} adjudication decisions are malformed")
    seen: set[str] = set()
    canonical: list[dict[str, Any]] = []
    for row in decisions:
        if not isinstance(row, dict):
            raise ImportChainError(f"an imported {stage} adjudication decision is malformed")
        key = f"{row.get('pair_id')}::{row.get('dimension')}"
        if key in seen:
            raise ImportChainError(f"the imported {stage} adjudication decides {key} twice")
        seen.add(key)
        canonical.append(
            {
                "stage": stage,
                "pair_id": str(row.get("pair_id", "")).strip(),
                "dimension": str(row.get("dimension", "")).strip(),
                "final_value": str(row.get("final_value", "")).strip(),
                "rationale": str(row.get("rationale", "")).strip(),
                "evidence_reference": str(row.get("evidence_reference", "")).strip(),
                "confidence": str(row.get("confidence", "")).strip(),
                "exclude_item": str(row.get("exclude_item", "")).strip(),
                "resolves_to_accepting_value": bool(row.get("resolves_to_accepting_value")),
                "dispute_reasons": sorted(
                    str(reason).strip() for reason in row.get("dispute_reasons", [])
                ),
            }
        )
    if len(canonical) != int(receipt.get("decision_count", -1)):
        raise ImportChainError(
            f"the imported {stage} adjudication declares a decision count that does not match "
            "its decisions"
        )
    return sha256_json(
        {
            "digest_kind": _IMPORT_ADJUDICATION_DIGEST,
            "stage": stage,
            "import_origin": str(receipt.get("import_origin", "")),
            "adjudication_schema_version": str(receipt.get("schema_version", "")),
            "disagreement_queue_sha256": str(receipt.get("disagreement_queue_sha256", "")),
            "disagreement_queue_content_sha256": str(
                receipt.get("disagreement_queue_content_sha256", "")
            ),
            "submission_sha256": str(receipt.get("submission_sha256", "")),
            "submission_canonical_sha256": str(receipt.get("submission_canonical_sha256", "")),
            "coordinator_waiver_sha256": str(receipt.get("coordinator_waiver_sha256", "")),
            "adjudicator_declaration_collected": bool(
                receipt.get("adjudicator_declaration_collected")
            ),
            "disputed_dimension_count": int(receipt.get("disputed_dimension_count", -1)),
            "decision_count": int(receipt.get("decision_count", -1)),
            "excluded_pair_ids": sorted(
                str(item).strip() for item in receipt.get("excluded_pair_ids", [])
            ),
            "decisions": canonical,
        }
    )


def import_judgements_digest(stage: str) -> Any:
    """The digest function bound to ``stage``, for snapshot create and read."""

    def digest(receipt: dict[str, Any]) -> str:
        return _canonical_import_judgements_digest(receipt, stage=stage)

    return digest


_JUDGEMENT_DIGEST = {
    STAGE1: import_judgements_digest(STAGE1),
    STAGE2: import_judgements_digest(STAGE2),
}


class ImportChainError(RuntimeError):
    """A manual-import gate refused to proceed."""


# --------------------------------------------------------------------------
# sealed receipt store
# --------------------------------------------------------------------------


@dataclass
class ImportWorkspace:
    """Sealed, write-once receipt store for the manual-import chain.

    Deliberately a sibling of :class:`~causal_agent_bench.review_ready_v2.workflow.ReviewWorkspace`
    rather than a subclass: the two must not be substitutable for one another,
    because the whole point is that their evidence classes differ.
    """

    private_root: Path
    authority: Authority
    packet_version: str
    import_epoch: str = DEFAULT_IMPORT_EPOCH

    @classmethod
    def open(
        cls,
        private_root: Path,
        repo_root: Path,
        *,
        packet_version: str,
        import_epoch: str = DEFAULT_IMPORT_EPOCH,
    ) -> ImportWorkspace:
        epoch = str(import_epoch).strip()
        if not epoch or not epoch.replace("_", "").replace("-", "").isalnum():
            raise ImportChainError(
                f"an import epoch must be a non-empty alphanumeric label, not {import_epoch!r}"
            )
        try:
            authority = manual_import_authority(repo_root)
        except ReceiptError as error:
            raise ImportChainError(str(error)) from error
        return cls(private_root, authority, packet_version, epoch)

    @property
    def receipts(self) -> Path:
        name = self.authority.namespace
        if self.import_epoch != DEFAULT_IMPORT_EPOCH:
            name = f"{name}__{self.import_epoch}"
        directory = self.private_root / name
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)
        return directory

    def path_for(self, name: str) -> Path:
        return self.receipts / f"{name}.json"

    def has(self, name: str) -> bool:
        path = self.path_for(name)
        return path.is_file() and not path.is_symlink()

    def write(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = self.path_for(name)
        sealed_name = name in _SEALED_NAMES
        if sealed_name and path.exists():
            raise ImportChainError(
                f"refusing to overwrite the sealed {name} receipt: imported review evidence is "
                "write-once. A correction requires a fresh import namespace, not an edit in place."
            )
        if name == "c10_report" and self.has("slice_lock"):
            raise ImportChainError(
                "refusing to rewrite the C10 report after the reviewed slice was locked"
            )
        sealed = seal_receipt(
            self.authority,
            {
                **payload,
                "packet_version": self.packet_version,
                "import_epoch": self.import_epoch,
                "import_chain_schema_version": IMPORT_CHAIN_SCHEMA_VERSION,
            },
        )
        try:
            write_private_json(path, sealed, allow_replace=not sealed_name)
        except CommitmentIntegrityError as error:
            raise ImportChainError(f"receipt {name} could not be written: {error}") from error
        return sealed

    def read(self, name: str) -> dict[str, Any]:
        path = self.path_for(name)
        if path.is_symlink():
            raise ImportChainError(f"receipt {name} is a symbolic link and is unusable")
        if not path.is_file():
            raise ImportChainError(f"required import receipt is missing: {name}")
        try:
            assert_regular_file(path)
            assert_contained(path, root=self.private_root)
            assert_private_mode(path, require_private=True)
        except CommitmentIntegrityError as error:
            raise ImportChainError(f"required import receipt is unusable: {name}: {error}") from error
        receipt = read_json(path)
        if receipt_is_fixture(receipt):
            raise ImportChainError(
                f"receipt {name} is a synthetic test fixture and cannot be genuine evidence"
            )
        try:
            verify_receipt(self.authority, receipt)
        except ReceiptError as error:
            raise ImportChainError(f"receipt {name} failed verification: {error}") from error
        if receipt.get("packet_version") != self.packet_version:
            raise ImportChainError(
                f"receipt {name} belongs to packet {receipt.get('packet_version')!r}, not "
                f"{self.packet_version!r}"
            )
        # The epoch is inside the MAC, so a receipt from an abandoned import
        # cannot be copied into a later epoch's directory and pass as current.
        if receipt.get("import_epoch") != self.import_epoch:
            raise ImportChainError(
                f"receipt {name} belongs to import epoch {receipt.get('import_epoch')!r}, not "
                f"{self.import_epoch!r}; evidence from an abandoned import cannot be reused"
            )
        return receipt

    def live_paths(self, stage: str) -> dict[str, Path]:
        return {role: self.path_for(f"{stage}_submission_{role}") for role in REVIEW_ROLES}

    def has_snapshot(self, stage: str) -> bool:
        return snapshot_exists(self.receipts, stage)


# --------------------------------------------------------------------------
# genuine qualification evidence
# --------------------------------------------------------------------------


def import_qualification_submissions(
    workspace: ImportWorkspace,
    *,
    candidates: dict[str, Candidate],
    answer_keys: dict[str, Any],
    qualification_version: str,
    public_qualification_commitment: str,
    exact_commit: str,
    scientific_freeze_sha256: str,
    packet_commitment: str,
) -> dict[str, Any]:
    """Score both reviewers' completed qualification submissions against the key.

    This is the one place the chain may claim a qualification result, and it may
    claim it only by *deriving* it: the private answer key decides, the reviewer's
    own file supplies the answers, and a submission that misses the threshold is
    a blocker rather than a note.  A role is never taken on assertion — the caller
    attributes it from the answered item set, and this function re-checks that
    attribution against the key before scoring.

    The sealed receipt carries counts, the rate, the threshold and hashes.  It
    never carries a decisive dimension, an expected value, or per-item
    correctness, so it can be summarized publicly without leaking the key.
    """

    if workspace.has("qualification_commitment"):
        raise ImportChainError(
            "qualification evidence is already committed for this import epoch; a correction "
            "requires a fresh import epoch, not an edit in place"
        )
    if set(candidates) != set(REVIEW_ROLES):
        raise ImportChainError(
            "qualification import requires exactly one completed submission per reviewer role"
        )
    missing_keys = sorted(set(REVIEW_ROLES) - set(answer_keys))
    if missing_keys:
        raise ImportChainError(
            f"the encrypted qualification key holds no answers for {missing_keys}"
        )

    receipts: dict[str, dict[str, Any]] = {}
    for role in sorted(REVIEW_ROLES):
        candidate = candidates[role]
        if candidate.kind != QUALIFICATION_FORM:
            raise ImportChainError(
                f"the file offered as the {role} qualification submission classifies as "
                f"{candidate.kind}"
            )
        payload = candidate.path.read_bytes()
        if sha256_bytes(payload) != candidate.raw_sha256:
            raise ImportChainError(
                f"the {role} qualification file changed on disk between discovery and import"
            )
        _, rows = read_csv_rows(payload)
        submission = {str(row["reviewer_item_id"]).strip(): row for row in rows}
        if len(submission) != len(rows):
            raise ImportChainError(
                f"the {role} qualification submission answers an item twice"
            )
        # The caller attributed the role from the answered items; re-derive it
        # here so a mis-attributed file is refused rather than mis-scored.
        if set(submission) != set(answer_keys[role]):
            raise ImportChainError(
                f"the submission offered as {role}'s qualification does not answer {role}'s "
                "issued item set; roles cannot be assigned by assertion"
            )
        try:
            enforce_active_qualification(qualification_version)
            result = score_qualification(submission, answer_keys[role], reviewer_role=role)
        except QualificationError as error:
            raise ImportChainError(f"{role} qualification refused: {error}") from error
        if not result["qualified"]:
            raise ImportChainError(
                f"{role} scored {result['correct_count']}/{result['item_count']} and did not reach "
                f"the {result['threshold']:.0%} qualification threshold; their review evidence "
                "cannot be imported"
            )
        receipts[role] = workspace.write(
            f"qualification_{role}",
            {
                "receipt_kind": "reviewer_qualification",
                "import_origin": workspace.authority.origin,
                "qualification_schema_version": IMPORT_QUALIFICATION_SCHEMA_VERSION,
                "qualification_version": qualification_version,
                "reviewer_role": role,
                "submission_sha256": candidate.raw_sha256,
                "canonical_content_sha256": candidate.canonical_sha256,
                "source_filename_recorded_for_audit_only": candidate.path.name,
                "opaque_id_namespace": candidate.namespace,
                "reviewer_item_ids_sha256": sha256_json(sorted(submission)),
                "item_count": result["item_count"],
                "correct_count": result["correct_count"],
                "rate": result["rate"],
                "threshold": result["threshold"],
                "qualified": True,
                "scored_against_private_answer_key": True,
                # Deliberately absent: the graded per-item breakdown, which would
                # let a reader recover expected values from the reviewer's answers.
                "per_item_correctness_recorded": False,
                "answer_key_disclosed": False,
                "declaration_collected": False,
                "imported_at_utc": datetime.now(UTC).isoformat(),
            },
        )

    namespaces = {str(receipts[role]["opaque_id_namespace"]) for role in REVIEW_ROLES}
    item_digests = {str(receipts[role]["reviewer_item_ids_sha256"]) for role in REVIEW_ROLES}
    if len(item_digests) != len(REVIEW_ROLES):
        raise ImportChainError(
            "both qualification submissions answer the same items; they cannot be two "
            "independently issued packages"
        )
    return workspace.write(
        "qualification_commitment",
        {
            "receipt_kind": "qualification_commitment",
            "qualification_schema_version": IMPORT_QUALIFICATION_SCHEMA_VERSION,
            "import_origin": workspace.authority.origin,
            "qualification_version": qualification_version,
            "qualification_mode": QUALIFICATION_MODE_GENUINE,
            "public_qualification_commitment_sha256": public_qualification_commitment,
            "private_packet_commitment": packet_commitment,
            "scientific_freeze_sha256": scientific_freeze_sha256,
            "frozen_source_commit": exact_commit,
            "reviewer_roles": sorted(REVIEW_ROLES),
            "opaque_id_namespaces": sorted(namespaces),
            "submission_payload_hashes": {
                role: str(receipts[role]["submission_sha256"]) for role in sorted(REVIEW_ROLES)
            },
            "submission_canonical_hashes": {
                role: str(receipts[role]["canonical_content_sha256"])
                for role in sorted(REVIEW_ROLES)
            },
            "qualification_receipt_hashes": {
                role: receipt_content_sha256(receipts[role]) for role in sorted(REVIEW_ROLES)
            },
            "rates": {role: receipts[role]["rate"] for role in sorted(REVIEW_ROLES)},
            "correct_counts": {
                role: receipts[role]["correct_count"] for role in sorted(REVIEW_ROLES)
            },
            "item_counts": {role: receipts[role]["item_count"] for role in sorted(REVIEW_ROLES)},
            "threshold": min(float(receipts[role]["threshold"]) for role in REVIEW_ROLES),
            "every_role_qualified": True,
            "answer_key_disclosed": False,
        },
    )


def verify_imported_qualification(workspace: ImportWorkspace) -> dict[str, Any]:
    """Re-derive the qualification commitment from the sealed per-role receipts.

    Returns ``None`` for ``commitment`` when no qualification evidence was
    imported at all — the waived case — so the caller can distinguish "no
    qualification was claimed" from "a qualification claim does not hold up".
    """

    if not workspace.has("qualification_commitment"):
        return {"commitment": None, "receipts": {}, "checks": {}, "every_role_qualified": False}
    commitment = workspace.read("qualification_commitment")
    receipts = {role: workspace.read(f"qualification_{role}") for role in REVIEW_ROLES}
    checks = {
        "qualification_receipt_hashes_match_commitment": {
            role: receipt_content_sha256(receipts[role]) for role in REVIEW_ROLES
        }
        == dict(commitment.get("qualification_receipt_hashes") or {}),
        "qualification_payload_hashes_match_commitment": {
            role: str(receipts[role]["submission_sha256"]) for role in REVIEW_ROLES
        }
        == dict(commitment.get("submission_payload_hashes") or {}),
        "qualification_canonical_hashes_match_commitment": {
            role: str(receipts[role]["canonical_content_sha256"]) for role in REVIEW_ROLES
        }
        == dict(commitment.get("submission_canonical_hashes") or {}),
        "qualification_rates_match_commitment": {
            role: receipts[role]["rate"] for role in REVIEW_ROLES
        }
        == dict(commitment.get("rates") or {}),
        "qualification_scored_against_private_key": all(
            receipts[role].get("scored_against_private_answer_key") is True
            for role in REVIEW_ROLES
        ),
        "qualification_meets_threshold_for_every_role": all(
            float(receipts[role]["rate"]) >= float(receipts[role]["threshold"])
            and receipts[role].get("qualified") is True
            for role in REVIEW_ROLES
        ),
        "qualification_roles_answered_distinct_item_sets": len(
            {str(receipts[role]["reviewer_item_ids_sha256"]) for role in REVIEW_ROLES}
        )
        == len(REVIEW_ROLES),
        "qualification_import_origin_matches": all(
            receipts[role].get("artifact_origin") == workspace.authority.origin
            for role in REVIEW_ROLES
        )
        and commitment.get("artifact_origin") == workspace.authority.origin,
        "qualification_answer_key_not_disclosed": commitment.get("answer_key_disclosed") is False
        and all(receipts[role].get("answer_key_disclosed") is False for role in REVIEW_ROLES),
    }
    failed = sorted(name for name, ok in checks.items() if not ok)
    if failed:
        raise ImportChainError(
            f"the imported qualification evidence has changed since it was committed: {failed}"
        )
    return {
        "commitment": commitment,
        "commitment_sha256": receipt_content_sha256(commitment),
        "receipts": receipts,
        "checks": checks,
        "every_role_qualified": bool(commitment.get("every_role_qualified")),
    }


# --------------------------------------------------------------------------
# the coordinator waiver
# --------------------------------------------------------------------------


def record_coordinator_waiver(
    workspace: ImportWorkspace,
    *,
    evidence_inventory_sha256: str,
    qualification_discovered: bool,
    exact_commit: str,
    scientific_freeze_sha256: str,
    packet_commitment: str,
    qualification_commitment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal exactly what was, and was not, collected.

    The waiver is bound to *this* evidence inventory: reusing it against a
    different set of files fails, so a stale waiver cannot authorize new
    evidence it was never written about.

    When ``qualification_commitment`` is supplied, genuine qualification
    submissions were scored in this epoch and only the reviewer-declaration
    waiver remains.  Without it, nothing about qualification is claimed.
    """

    if workspace.has("coordinator_waiver"):
        raise ImportChainError("a coordinator waiver is already sealed for this import namespace")
    verified = qualification_commitment is not None
    if qualification_commitment is not None:
        if not qualification_discovered:
            raise ImportChainError(
                "a qualification commitment was supplied for evidence that discovery did not find"
            )
        if not qualification_commitment.get("every_role_qualified"):
            raise ImportChainError(
                "refusing to record a waiver that claims a qualification pass the commitment does "
                "not establish for every reviewer role"
            )
    waived = [
        element
        for element in WAIVED_ELEMENTS
        if not (element == "qualification_submission_evidence" and qualification_discovered)
    ]
    qualification_statement = (
        "Both reviewers' completed qualification submissions were imported and scored against "
        "the private answer key; every role met the threshold."
        if verified
        else (
            "Qualification submissions were not imported; no qualification score is "
            "claimed, re-derived, or implied by this chain."
        )
    )
    return workspace.write(
        "coordinator_waiver",
        {
            "receipt_kind": "coordinator_review_waiver",
            "waiver_schema_version": IMPORT_WAIVER_SCHEMA_VERSION,
            "evidence_origin": "completed offline role-separated review forms",
            "waived_elements": waived,
            "declaration_waiver_status": DECLARATION_WAIVER_STATUS,
            "qualification_waiver_status": (
                None if qualification_discovered else QUALIFICATION_WAIVER_STATUS
            ),
            "qualification_mode": (
                QUALIFICATION_MODE_GENUINE if verified else QUALIFICATION_MODE_WAIVED
            ),
            "declaration_files_collected": False,
            "qualification_evidence_imported": qualification_discovered,
            "qualification_pass_verified_in_this_chain": verified,
            "qualification_commitment_sha256": (
                str(qualification_commitment["receipt_sha256"])
                if qualification_commitment is not None
                else None
            ),
            "reviewer_declarations_confirmed": False,
            "original_issue_receipt_available": False,
            "required_opt_in_flags": list(REQUIRED_OPT_IN_FLAGS),
            "evidence_inventory_sha256": evidence_inventory_sha256,
            "exact_commit": exact_commit,
            "scientific_freeze_sha256": scientific_freeze_sha256,
            "private_packet_commitment": packet_commitment,
            "statements": [
                "Separate reviewer declaration files were not collected.",
                "The coordinator explicitly permits manual import of this completed evidence.",
                "The two reviewer roles were kept separate and answer disjoint opaque namespaces.",
                "The adjudicator evidence is separate from both reviewers' evidence.",
                "No retrospective reviewer confirmation is asserted anywhere in this chain.",
                "The imported judgements are preserved byte-for-byte and canonically.",
                "The normal strict production workflow is unchanged for any future review.",
                qualification_statement,
            ],
            "recorded_at_utc": datetime.now(UTC).isoformat(),
        },
    )


# --------------------------------------------------------------------------
# importing the submissions
# --------------------------------------------------------------------------


def _canonical_payload(candidate: Candidate) -> bytes:
    """The exact bytes the reviewer's file contained."""

    return candidate.path.read_bytes()


def import_review_submissions(
    workspace: ImportWorkspace,
    *,
    stage: str,
    candidates: dict[str, Candidate],
    expected_item_ids: dict[str, list[str]],
    applicability: dict[str, dict[str, bool]] | None,
    waiver: dict[str, Any],
    packet_commitment: str,
    scientific_freeze_sha256: str,
    exact_commit: str,
    review_schema_version: str,
) -> dict[str, Any]:
    """Import both reviewers' submissions for one stage and freeze them.

    The judgements are validated with the production validators, not with a
    relaxed import-only copy: a malformed offline form is refused exactly as a
    malformed production form would be.
    """

    if stage not in (STAGE1, STAGE2):
        raise ImportChainError(f"unknown review stage {stage!r}")
    if workspace.has(f"{stage}_commitment") or workspace.has_snapshot(stage):
        raise ImportChainError(
            f"{stage} evidence is already imported and committed; committed evidence is immutable"
        )
    orphaned = [
        role for role in REVIEW_ROLES if workspace.has(f"{stage}_submission_{role}")
    ]
    if orphaned:
        # An earlier attempt wrote submission receipts and then failed before the
        # snapshot existed.  Those receipts are sealed and cannot be rewritten,
        # so the honest recovery is to discard the whole partial namespace rather
        # than to patch around it.
        raise ImportChainError(
            f"a previous {stage} import left sealed submission receipts for {sorted(orphaned)} "
            f"without a committed snapshot. Imported evidence is write-once, so move the whole "
            f"{workspace.receipts} directory aside and re-import from the source files."
        )
    if set(candidates) != set(REVIEW_ROLES):
        raise ImportChainError(f"{stage} import requires exactly one submission per reviewer role")

    submissions: dict[str, dict[str, Any]] = {}
    bindings: dict[str, dict[str, Any]] = {}
    for role in REVIEW_ROLES:
        candidate = candidates[role]
        if candidate.role != role:
            raise ImportChainError(
                f"the file offered as the {stage} submission for {role} carries the "
                f"{candidate.role} opaque namespace; roles cannot be swapped by filename"
            )
        payload = _canonical_payload(candidate)
        if sha256_bytes(payload) != candidate.raw_sha256:
            raise ImportChainError(
                f"the {stage} file for {role} changed on disk between discovery and import"
            )
        rows = parse_review_csv(payload, _FORM_COLUMNS[stage])
        extra: dict[str, Any] = {}
        if stage == STAGE1:
            validation = validate_stage1_submission(rows, expected_item_ids[role])
            well_formed = bool(validation["passed"])
        else:
            if applicability is None:
                raise ImportChainError("a Stage-2 import requires the frozen applicability map")
            validation = validate_stage2_submission(rows, expected_item_ids[role], applicability)
            # Stage 2 deliberately never reports "passed": a complete form is not
            # an approval, and acceptance is decided later from the final records.
            well_formed = bool(validation["form_complete"])
            extra = {
                "form_schema_version": validation["form_schema_version"],
                "acceptance_policy_version": validation["acceptance_policy_version"],
                "form_complete": validation["form_complete"],
                "blocking_value_count": validation["blocking_value_count"],
                "substantively_accepted_without_adjudication": validation[
                    "substantively_accepted_without_adjudication"
                ],
            }
        if not well_formed:
            raise ImportChainError(
                f"the imported {stage} submission for {role} is malformed: {validation['checks']}"
            )
        namespace = candidate.namespace
        if any(not str(item).startswith(f"{namespace}-") for item in rows):
            raise ImportChainError(
                f"the imported {stage} submission for {role} carries rows outside its namespace"
            )
        submissions[role] = workspace.write(
            f"{stage}_submission_{role}",
            {
                "receipt_kind": f"{stage}_submission",
                "import_origin": workspace.authority.origin,
                "reviewer_role": role,
                "submission_sha256": sha256_bytes(payload),
                "canonical_content_sha256": candidate.canonical_sha256,
                "source_filename_recorded_for_audit_only": candidate.path.name,
                "opaque_id_namespace": namespace,
                "row_count": validation["row_count"],
                "judgements": rows,
                "validation": validation["checks"],
                **extra,
                "coordinator_waiver_sha256": waiver["receipt_sha256"],
                "declaration_collected": False,
                "issue_receipt_available": False,
                "imported_at_utc": datetime.now(UTC).isoformat(),
            },
        )
        bindings[role] = {
            "reviewer_role": role,
            "submission_payload_sha256": sha256_bytes(payload),
            "canonical_content_sha256": candidate.canonical_sha256,
            "opaque_id_namespace": namespace,
            "item_count": validation["row_count"],
            "reviewer_item_ids_sha256": sha256_json(sorted(rows)),
        }

    item_counts = {row["row_count"] for row in submissions.values()}
    if len(item_counts) != 1:
        raise ImportChainError(
            f"the two {stage} submissions do not cover the same number of items; they cannot "
            "describe one reviewed slice"
        )
    expected_item_count = item_counts.pop()
    namespaces = {bindings[role]["opaque_id_namespace"] for role in REVIEW_ROLES}
    if len(namespaces) != 2:
        raise ImportChainError(
            f"both {stage} submissions share one opaque namespace; the roles are not separated"
        )

    try:
        manifest = create_submission_snapshot(
            receipts_root=workspace.receipts,
            authority=workspace.authority,
            stage=stage,
            live_paths=workspace.live_paths(stage),
            receipts=submissions,
            reviewer_bindings=bindings,
            manifest_bindings={
                "packet_version": workspace.packet_version,
                "expected_item_count": expected_item_count,
                "import_origin": workspace.authority.origin,
                "coordinator_waiver_sha256": waiver["receipt_sha256"],
                "review_schema_version": review_schema_version,
                "private_packet_commitment": packet_commitment,
                "scientific_freeze_sha256": scientific_freeze_sha256,
                "frozen_source_commit": exact_commit,
                "reviewer_item_id_namespace_digest": sha256_json(
                    {role: sorted(submissions[role]["judgements"]) for role in sorted(REVIEW_ROLES)}
                ),
            },
            digest_for=_JUDGEMENT_DIGEST[stage],
        )
    except CommitmentIntegrityError as error:
        raise ImportChainError(f"{stage} import commitment refused: {error}") from error

    return workspace.write(
        f"{stage}_commitment",
        {
            "receipt_kind": f"{stage}_import_commitment",
            "commitment_schema_version": IMPORT_COMMITMENT_SCHEMA_VERSION,
            "import_origin": workspace.authority.origin,
            "coordinator_waiver_sha256": waiver["receipt_sha256"],
            "private_packet_commitment": packet_commitment,
            "scientific_freeze_sha256": scientific_freeze_sha256,
            "exact_commit": exact_commit,
            "frozen_source_commit": exact_commit,
            "review_schema_version": review_schema_version,
            "expected_item_count": expected_item_count,
            "reviewer_roles": sorted(REVIEW_ROLES),
            f"{stage}_submission_payload_hashes": {
                role: submissions[role]["submission_sha256"] for role in sorted(REVIEW_ROLES)
            },
            f"{stage}_submission_canonical_hashes": {
                role: submissions[role]["canonical_content_sha256"] for role in sorted(REVIEW_ROLES)
            },
            f"{stage}_submission_receipt_hashes": {
                role: receipt_content_sha256(submissions[role]) for role in sorted(REVIEW_ROLES)
            },
            f"{stage}_canonical_judgement_hashes": {
                role: _JUDGEMENT_DIGEST[stage](submissions[role]) for role in sorted(REVIEW_ROLES)
            },
            f"{stage}_snapshot_manifest_sha256": manifest_sha256(manifest),
            f"{stage}_snapshot_receipt_file_hashes": {
                role: manifest["reviewers"][role]["snapshot_receipt_file_sha256"]
                for role in sorted(REVIEW_ROLES)
            },
            f"{stage}_snapshot_schema_version": manifest["manifest_schema_version"],
            f"{stage}_final": True,
        },
    )


def verify_imported_snapshot(
    workspace: ImportWorkspace,
    *,
    stage: str,
    expected_packet_commitment: str | None = None,
    expected_scientific_freeze_sha256: str | None = None,
    expected_frozen_source_commit: str | None = None,
) -> dict[str, Any]:
    """Return the immutable imported evidence for ``stage``, or refuse to return any.

    Every digest the commitment binds is recomputed from what is on disk.  A live
    receipt that no longer matches the frozen snapshot is a conflict rather than
    an update, and is reported even though nothing downstream reads it.
    """

    commitment = workspace.read(f"{stage}_commitment")
    if commitment.get("commitment_schema_version") != IMPORT_COMMITMENT_SCHEMA_VERSION:
        raise ImportChainError(
            f"the {stage} import commitment declares "
            f"{commitment.get('commitment_schema_version')!r}, not "
            f"{IMPORT_COMMITMENT_SCHEMA_VERSION!r}"
        )
    waiver = workspace.read("coordinator_waiver")
    try:
        manifest = read_snapshot_manifest(
            workspace.receipts, authority=workspace.authority, stage=stage, require_private=True
        )
        receipts, checks = read_snapshot_receipts(
            workspace.receipts,
            authority=workspace.authority,
            stage=stage,
            manifest=manifest,
            live_paths=workspace.live_paths(stage),
            require_private=True,
            digest_for=_JUDGEMENT_DIGEST[stage],
        )
    except CommitmentIntegrityError as error:
        raise ImportChainError(f"the imported {stage} snapshot is invalid: {error}") from error

    file_hashes = {
        role: manifest["reviewers"][role]["snapshot_receipt_file_sha256"] for role in REVIEW_ROLES
    }
    judgement_hashes = {role: _JUDGEMENT_DIGEST[stage](receipts[role]) for role in REVIEW_ROLES}
    payload_hashes = {role: str(receipts[role]["submission_sha256"]) for role in REVIEW_ROLES}
    canonical_hashes = {role: str(receipts[role]["canonical_content_sha256"]) for role in REVIEW_ROLES}
    namespaces = {str(receipts[role]["opaque_id_namespace"]) for role in REVIEW_ROLES}

    checks.update(
        {
            f"{stage}_snapshot_manifest_matches_commitment": manifest_sha256(manifest)
            == commitment.get(f"{stage}_snapshot_manifest_sha256"),
            f"{stage}_snapshot_file_hashes_match_commitment": file_hashes
            == dict(commitment.get(f"{stage}_snapshot_receipt_file_hashes") or {}),
            f"{stage}_receipt_hashes_match_commitment": {
                role: receipt_content_sha256(receipts[role]) for role in REVIEW_ROLES
            }
            == dict(commitment.get(f"{stage}_submission_receipt_hashes") or {}),
            f"{stage}_judgement_hashes_match_commitment": judgement_hashes
            == dict(commitment.get(f"{stage}_canonical_judgement_hashes") or {}),
            f"{stage}_payload_hashes_match_commitment": payload_hashes
            == dict(commitment.get(f"{stage}_submission_payload_hashes") or {}),
            # The canonical hash is bound separately from the payload hash on
            # purpose: keeping one while changing the other is exactly the
            # substitution this chain exists to detect.
            f"{stage}_canonical_hashes_match_commitment": canonical_hashes
            == dict(commitment.get(f"{stage}_submission_canonical_hashes") or {}),
            f"{stage}_roles_use_disjoint_namespaces": len(namespaces) == 2,
            f"{stage}_import_origin_matches": manifest.get("import_origin")
            == workspace.authority.origin
            and all(
                receipts[role].get("artifact_origin") == workspace.authority.origin
                for role in REVIEW_ROLES
            ),
            f"{stage}_waiver_bound_into_snapshot": manifest.get("coordinator_waiver_sha256")
            == waiver["receipt_sha256"],
            f"{stage}_waiver_bound_into_commitment": commitment.get("coordinator_waiver_sha256")
            == waiver["receipt_sha256"],
            f"{stage}_waiver_bound_into_receipts": all(
                receipts[role].get("coordinator_waiver_sha256") == waiver["receipt_sha256"]
                for role in REVIEW_ROLES
            ),
            f"{stage}_snapshot_binds_committed_packet": manifest.get("private_packet_commitment")
            == commitment.get("private_packet_commitment"),
            f"{stage}_snapshot_binds_committed_freeze": manifest.get("scientific_freeze_sha256")
            == commitment.get("scientific_freeze_sha256"),
            f"{stage}_snapshot_binds_committed_commit": manifest.get("frozen_source_commit")
            == commitment.get("frozen_source_commit"),
            f"{stage}_item_coverage_matches_commitment": all(
                len(receipts[role]["judgements"]) == int(commitment.get("expected_item_count", -1))
                for role in REVIEW_ROLES
            ),
            f"{stage}_no_declaration_is_asserted": all(
                receipts[role].get("declaration_collected") is False for role in REVIEW_ROLES
            ),
        }
    )
    if expected_packet_commitment is not None:
        checks[f"{stage}_packet_commitment_matches_expected"] = (
            commitment.get("private_packet_commitment") == expected_packet_commitment
        )
    if expected_scientific_freeze_sha256 is not None:
        checks[f"{stage}_freeze_matches_expected"] = (
            commitment.get("scientific_freeze_sha256") == expected_scientific_freeze_sha256
        )
    if expected_frozen_source_commit is not None:
        checks[f"{stage}_source_commit_matches_expected"] = (
            commitment.get("frozen_source_commit") == expected_frozen_source_commit
        )

    failed = sorted(name for name, ok in checks.items() if not ok)
    if failed:
        raise ImportChainError(
            f"the imported {stage} evidence has changed since it was committed: {failed}"
        )
    return {
        "stage": stage,
        "commitment": commitment,
        "commitment_sha256": receipt_content_sha256(commitment),
        "manifest": manifest,
        "snapshot_manifest_sha256": manifest_sha256(manifest),
        "receipts": receipts,
        "canonical_judgement_hashes": judgement_hashes,
        "snapshot_receipt_file_hashes": file_hashes,
        "payload_hashes": payload_hashes,
        "canonical_content_hashes": canonical_hashes,
        "waiver_sha256": waiver["receipt_sha256"],
        "checks": checks,
    }


# --------------------------------------------------------------------------
# derived chain: queues, adjudication, agreement, final records
# --------------------------------------------------------------------------


def _paired(
    workspace: ImportWorkspace, mappings: dict[str, dict[str, str]], stage: str
) -> dict[str, dict[str, dict[str, str]]]:
    """Pair the two reviewers' rows by pair id, reading only frozen snapshots."""

    receipts = verify_imported_snapshot(workspace, stage=stage)["receipts"]
    by_pair: dict[str, dict[str, dict[str, str]]] = {}
    for role in REVIEW_ROLES:
        mapping = mappings[role]
        for item_id, row in receipts[role]["judgements"].items():
            pair_id = mapping.get(item_id)
            if pair_id is None:
                raise ImportChainError(f"unmapped reviewer item {item_id}")
            by_pair.setdefault(pair_id, {})[role] = row
    return by_pair


def _graph_bindings(workspace: ImportWorkspace) -> dict[str, Any]:
    """The immutable inputs every derived artifact is permanently bound to."""

    stage1 = verify_imported_snapshot(workspace, stage=STAGE1)
    qualification = verify_imported_qualification(workspace)
    bindings: dict[str, Any] = {
        "import_origin": workspace.authority.origin,
        "import_epoch": workspace.import_epoch,
        "coordinator_waiver_sha256": stage1["waiver_sha256"],
        "qualification_commitment_sha256": qualification.get("commitment_sha256"),
        "qualification_mode": (
            QUALIFICATION_MODE_GENUINE
            if qualification["every_role_qualified"]
            else QUALIFICATION_MODE_WAIVED
        ),
        "stage1_commitment_sha256": stage1["commitment_sha256"],
        "stage1_snapshot_manifest_sha256": stage1["snapshot_manifest_sha256"],
        "stage1_snapshot_receipt_hashes": stage1["snapshot_receipt_file_hashes"],
        "stage1_canonical_judgement_hashes": stage1["canonical_judgement_hashes"],
        "private_packet_commitment": str(stage1["commitment"]["private_packet_commitment"]),
        "scientific_freeze_sha256": str(stage1["commitment"]["scientific_freeze_sha256"]),
        "frozen_source_commit": str(stage1["commitment"]["frozen_source_commit"]),
    }
    if workspace.has_snapshot(STAGE2):
        stage2 = verify_imported_snapshot(workspace, stage=STAGE2)
        bindings.update(
            {
                "stage2_commitment_sha256": stage2["commitment_sha256"],
                "stage2_snapshot_manifest_sha256": stage2["snapshot_manifest_sha256"],
                "stage2_snapshot_receipt_hashes": stage2["snapshot_receipt_file_hashes"],
                "stage2_canonical_judgement_hashes": stage2["canonical_judgement_hashes"],
            }
        )
    return bindings


def build_disagreement_queue(
    workspace: ImportWorkspace,
    *,
    stage: str,
    mappings: dict[str, dict[str, str]],
    applicability: dict[str, dict[str, bool]] | None = None,
) -> dict[str, Any]:
    """Derive the disagreement queue from the frozen independent judgements."""

    if workspace.has(f"{stage}_adjudication"):
        raise ImportChainError(
            f"the {stage} disagreement queue cannot be rebuilt after it was adjudicated; a "
            "different queue would leave the adjudication answering nothing"
        )
    paired = _paired(workspace, mappings, stage)
    try:
        if stage == STAGE1:
            queue = build_stage1_queue(paired)
        else:
            if applicability is None:
                raise ImportChainError("a Stage-2 queue requires the frozen applicability map")
            queue = build_stage2_queue(paired, applicability)
    except AdjudicationError as error:
        raise ImportChainError(str(error)) from error
    return workspace.write(
        f"{stage}_disagreement_queue",
        {
            "receipt_kind": f"{stage}_disagreement_queue",
            **_graph_bindings(workspace),
            **queue,
            "queue_content_sha256": canonical_queue_digest(queue),
        },
    )


def import_adjudication(
    workspace: ImportWorkspace, *, stage: str, candidate: Candidate
) -> dict[str, Any]:
    """Import an adjudicator's completed decisions against the sealed queue."""

    if workspace.has(f"{stage}_adjudication"):
        raise ImportChainError(
            f"the {stage} adjudication is already sealed; replacing it would rewrite settled "
            "review evidence"
        )
    if workspace.has("final_adjudicated_records"):
        raise ImportChainError(
            f"the {stage} adjudication cannot be accepted after the final records were built"
        )
    expected_kind = {STAGE1: STAGE1_ADJUDICATION, STAGE2: STAGE2_ADJUDICATION}[stage]
    if candidate.kind != expected_kind:
        raise ImportChainError(
            f"the file offered as the {stage} adjudication classifies as {candidate.kind}; "
            "the decision dimensions belong to another stage"
        )
    payload = candidate.path.read_bytes()
    if sha256_bytes(payload) != candidate.raw_sha256:
        raise ImportChainError(
            f"the {stage} adjudication file changed on disk between discovery and import"
        )
    header, rows = read_csv_rows(payload)
    missing = [column for column in ADJUDICATION_COLUMNS if column not in header]
    if missing:
        raise ImportChainError(f"the {stage} adjudication is missing columns: {missing}")
    decisions = [{column: row.get(column, "") for column in ADJUDICATION_COLUMNS} for row in rows]

    queue = workspace.read(f"{stage}_disagreement_queue")
    if queue.get("queue_content_sha256") != canonical_queue_digest(queue):
        raise ImportChainError(
            f"the {stage} disagreement queue content no longer matches the digest it was sealed with"
        )
    try:
        validated = validate_adjudication(stage=stage, queue=queue, decisions=decisions)
    except AdjudicationError as error:
        raise ImportChainError(f"{stage} adjudication refused: {error}") from error

    payload_receipt = {
        "receipt_kind": f"{stage}_adjudication",
        "import_origin": workspace.authority.origin,
        "adjudicator_declaration_collected": False,
        "adjudicator_evidence_is_separate_from_reviewer_evidence": True,
        "disagreement_queue_sha256": queue["receipt_sha256"],
        "disagreement_queue_content_sha256": canonical_queue_digest(queue),
        "submission_sha256": sha256_bytes(payload),
        "submission_canonical_sha256": candidate.canonical_sha256,
        "source_filename_recorded_for_audit_only": candidate.path.name,
        **_graph_bindings(workspace),
        **validated,
    }
    return workspace.write(
        f"{stage}_adjudication",
        {
            **payload_receipt,
            "adjudication_content_sha256": canonical_import_adjudication_digest(payload_receipt),
        },
    )


def compute_agreement(
    workspace: ImportWorkspace, *, mappings: dict[str, dict[str, str]]
) -> dict[str, Any]:
    """Raw agreement between the two independent submissions.

    Adjudicated values are deliberately not consulted: resolving a dispute must
    never make the reviewers look as though they had agreed in the first place.
    """

    stage1 = _paired(workspace, mappings, STAGE1)
    stage2 = _paired(workspace, mappings, STAGE2) if workspace.has_snapshot(STAGE2) else {}
    tables = agreement_tables(stage1, stage2)
    return workspace.write(
        "agreement",
        {
            "receipt_kind": "agreement",
            "computed_from": "immutable_imported_raw_pre_adjudication_judgements",
            "adjudicated_values_used": False,
            **_graph_bindings(workspace),
            **tables,
            "combined_rule": "both_stages_must_meet_the_threshold_independently",
        },
    )


def build_final_adjudicated_records(
    workspace: ImportWorkspace,
    *,
    mappings: dict[str, dict[str, str]],
    applicability: dict[str, dict[str, bool]],
    expected_pair_count: int,
) -> dict[str, Any]:
    """Derive the final per-pair records from frozen judgements plus adjudications."""

    stage1 = _paired(workspace, mappings, STAGE1)
    stage2 = _paired(workspace, mappings, STAGE2) if workspace.has_snapshot(STAGE2) else {}
    adjudications = {
        stage: (workspace.read(f"{stage}_adjudication") if workspace.has(f"{stage}_adjudication") else None)
        for stage in (STAGE1, STAGE2)
    }
    try:
        final = build_final_records(
            stage1_paired=stage1,
            stage2_paired=stage2,
            stage1_adjudication=adjudications[STAGE1],
            stage2_adjudication=adjudications[STAGE2],
            applicability=applicability,
            expected_pair_count=expected_pair_count,
        )
    except FinalRecordError as error:
        raise ImportChainError(f"final adjudicated records refused: {error}") from error
    return workspace.write(
        "final_adjudicated_records",
        {
            "receipt_kind": "final_adjudicated_records",
            **_graph_bindings(workspace),
            **final,
        },
    )


__all__ = [
    "C10_FAIL_STATUS",
    "C10_PASS_STATUS",
    "C10_PASS_STATUS_DECLARATION_ONLY",
    "DECLARATION_WAIVER_STATUS",
    "DEFAULT_IMPORT_EPOCH",
    "IMPORT_C10_SCHEMA_VERSION",
    "IMPORT_CHAIN_SCHEMA_VERSION",
    "IMPORT_COMMITMENT_SCHEMA_VERSION",
    "IMPORT_QUALIFICATION_SCHEMA_VERSION",
    "IMPORT_WAIVER_SCHEMA_VERSION",
    "QUALIFICATION_MODE_GENUINE",
    "QUALIFICATION_MODE_WAIVED",
    "QUALIFICATION_WAIVER_STATUS",
    "REQUIRED_OPT_IN_FLAGS",
    "WAIVED_ELEMENTS",
    "ImportChainError",
    "ImportWorkspace",
    "build_disagreement_queue",
    "build_final_adjudicated_records",
    "compute_agreement",
    "import_adjudication",
    "import_qualification_submissions",
    "import_review_submissions",
    "record_coordinator_waiver",
    "verify_imported_qualification",
    "verify_imported_snapshot",
]
