"""Fixture-only end-to-end exercise of the two-stage workflow.

Everything here is synthetic.  The fixture packet is built from its own items, it
shares no task body, identifier, answer or key with the private packet, and every
artifact it writes is sealed by the public fixture authority and stamped
``SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE``.

It proves workflow *mechanics* only.  It cannot create genuine evidence, cannot
pass C10, and cannot authorize a real run — not because it declines to, but
because the production gates verify a coordinator MAC it does not possess.
"""

from __future__ import annotations

import secrets
from typing import Any

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.adjudication import STAGE1, STAGE2
from causal_agent_bench.review_ready_v2.assignments import create_assignment
from causal_agent_bench.review_ready_v2.common import FIXTURE_MARKER, canonical_bytes, sha256_bytes
from causal_agent_bench.review_ready_v2.declarations import DECLARATION_VERSION
from causal_agent_bench.review_ready_v2.qualification import build_private_qualification
from causal_agent_bench.review_ready_v2.receipts import coordinator_authority
from causal_agent_bench.review_ready_v2.roles import (
    ADJUDICATOR,
    REVIEW_ROLES,
    REVIEWER_A,
    REVIEWER_B,
    namespace_for,
)
from causal_agent_bench.review_ready_v2.stage1 import (
    REVIEW_DIMENSIONS,
    REVIEW_FORM_COLUMNS,
    zip_bytes,
)
from causal_agent_bench.review_ready_v2.stage2 import (
    NOT_APPLICABLE,
    STAGE2_CONDITIONAL_DIMENSIONS,
    STAGE2_FORM_COLUMNS,
    STAGE2_SUBSTANTIVE_DIMENSIONS,
    UNSURE,
    YES,
)
from causal_agent_bench.review_ready_v2.vault import seal, unlocked_workspace, unseal
from causal_agent_bench.review_ready_v2.workflow import (
    ReviewWorkspace,
    WorkflowError,
    authorize_model_execution,
    build_exclusion_register,
    lock_reviewed_slice,
    run_c10,
    workflow_status,
)

FIXTURE_PAIR_COUNT = 8
# The fixture runs under the active packet version on purpose: the packet
# version is not the authenticity boundary, the sealing authority is. Using a
# private version here would let the fixture dodge enforce_active_packet(),
# which is a gate it must pass through like everything else.
FIXTURE_PACKET_VERSION = PACKET_VERSION
FIXTURE_PSEUDONYMS = {
    REVIEWER_A: "fixture-reviewer-alpha",
    REVIEWER_B: "fixture-reviewer-beta",
    ADJUDICATOR: "fixture-adjudicator-gamma",
}
FIXTURE_COMMIT = "0" * 40
FIXTURE_FREEZE_SHA = "f" * 64

FIXTURE_C10_CONTRACT: dict[str, Any] = {
    "schema_version": "cab_c10_contract_v2",
    "claim_id": "C10",
    "min_raw_agreement": 0.8,
    "min_task_clarity": 3,
    "expected_pair_count": FIXTURE_PAIR_COUNT,
    "evidence_class_on_pass": "AUDITED_REAL_EVIDENCE",
}

#: The last fixture pair carries a Stage-1 exclusion disagreement, and the first
#: carries a Stage-2 objection, so both adjudication paths are exercised.
_STAGE1_DISPUTE_INDEX = FIXTURE_PAIR_COUNT
_STAGE2_DISPUTE_INDEX = 1
#: Pairs 1-4 have no abstention opportunity, so NOT_APPLICABLE is correct there.
_NO_ABSTENTION_UPTO = 4

_STAGE1_ACCEPTING_ROW = {
    "task_clarity": "4",
    "clean_goal_clear": "yes",
    "clean_evidence_sufficient": "yes",
    "clean_solvable": "yes",
    "intervention_understandable": "yes",
    "intended_factor_identifiable": "yes",
    "goal_preserved": "yes",
    "single_factor_isolation": "yes",
    "preserved_invariants_hold": "yes",
    "primitive_evidence_adequate": "yes",
    "declared_tools_adequate": "yes",
    "intervention_realistic": "4",
    "ambiguity_present": "none",
    "response_space_structurally_valid": "yes",
    "exclude_item": "no",
    "reviewer_confidence": "4",
    "notes": "",
}


def fixture_pair_ids() -> list[str]:
    return [f"fixture-pair-{index:02d}" for index in range(1, FIXTURE_PAIR_COUNT + 1)]


def fixture_applicability() -> dict[str, dict[str, bool]]:
    applicability: dict[str, dict[str, bool]] = {}
    for index, pair_id in enumerate(fixture_pair_ids(), 1):
        row = dict.fromkeys(STAGE2_SUBSTANTIVE_DIMENSIONS, True)
        if index <= _NO_ABSTENTION_UPTO:
            row["abstention_policy_valid_or_not_applicable"] = False
        applicability[pair_id] = row
    return applicability


def _fixture_package(role: str) -> tuple[bytes, dict[str, str], list[str]]:
    prefix = namespace_for(role)
    pairs = fixture_pair_ids()
    if role == REVIEWER_B:
        pairs = list(reversed(pairs))
    mapping: dict[str, str] = {}
    files: dict[str, bytes] = {}
    item_ids: list[str] = []
    for position, pair_id in enumerate(pairs, 1):
        item_id = f"{prefix}-{position:02d}"
        item_ids.append(item_id)
        mapping[item_id] = pair_id
        files[f"items/{item_id}.json"] = (
            canonical_bytes(
                {
                    "evidence_class": FIXTURE_MARKER,
                    "reviewer_item_id": item_id,
                    "task_objective": "Synthetic calibration item. Not a benchmark task.",
                }
            )
            + b"\n"
        )
    files["manifest.json"] = (
        canonical_bytes(
            {
                "evidence_class": FIXTURE_MARKER,
                "package_role": role,
                "items": [
                    {"reviewer_item_id": item_id, "item_path": f"items/{item_id}.json"}
                    for item_id in item_ids
                ],
            }
        )
        + b"\n"
    )
    return zip_bytes(files), mapping, item_ids


def _stage1_form(mapping: dict[str, str], *, dispute: bool) -> bytes:
    lines = [",".join(REVIEW_FORM_COLUMNS)]
    disputed_pair = f"fixture-pair-{_STAGE1_DISPUTE_INDEX:02d}"
    for item_id in sorted(mapping):
        row = dict(_STAGE1_ACCEPTING_ROW)
        if dispute and mapping[item_id] == disputed_pair:
            row["exclude_item"] = "yes"
            row["notes"] = "fixture disagreement to exercise the Stage-1 adjudication path"
        lines.append(",".join([item_id, *(row[name] for name in REVIEW_FORM_COLUMNS[1:])]))
    return ("\n".join(lines) + "\n").encode()


def _stage2_form(
    mapping: dict[str, str], applicability: dict[str, dict[str, bool]], *, objection: bool
) -> bytes:
    lines = [",".join(STAGE2_FORM_COLUMNS)]
    disputed_pair = f"fixture-pair-{_STAGE2_DISPUTE_INDEX:02d}"
    for item_id in sorted(mapping):
        pair_id = mapping[item_id]
        pair_applicability = applicability[pair_id]
        values: dict[str, str] = {}
        for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS:
            applicable = pair_applicability.get(dimension, True)
            if dimension in STAGE2_CONDITIONAL_DIMENSIONS and not applicable:
                values[dimension] = NOT_APPLICABLE
            else:
                values[dimension] = YES
        notes = ""
        if objection and pair_id == disputed_pair:
            values["gold_correct"] = UNSURE
            notes = "fixture uncertainty to exercise the Stage-2 adjudication path"
        lines.append(
            ",".join(
                [
                    item_id,
                    *(values[dimension] for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS),
                    "NO",
                    "4",
                    notes,
                ]
            )
        )
    return ("\n".join(lines) + "\n").encode()


def _qualification_submission(answer_key: dict[str, Any]) -> dict[str, dict[str, str]]:
    """A perfect submission derived from this reviewer's own private key."""

    baseline = {name: (values[0] if values else "") for name, values, _ in REVIEW_DIMENSIONS}
    submission: dict[str, dict[str, str]] = {}
    for item_id, entry in answer_key.items():
        row = dict(baseline)
        row[str(entry["decisive_dimension"])] = str(entry["expected_value"])
        submission[item_id] = row
    return submission


def _declaration(role: str, *, stage1_hash: str, qualification_hash: str) -> dict[str, Any]:
    return {
        "declaration_version": DECLARATION_VERSION,
        "reviewer_pseudonym": FIXTURE_PSEUDONYMS[role],
        "package_role": role,
        "qualification_package_hash": qualification_hash,
        "stage1_package_hash": stage1_hash,
        "independence_confirmed": True,
        "not_author_or_coauthor_confirmed": True,
        "no_ai_assistance_confirmed": True,
        "confidentiality_confirmed": True,
        "worked_independently_confirmed": True,
        "conflict_of_interest_disclosed": False,
        "conflict_of_interest_details": "",
        "signed_name_or_approved_signature_field": FIXTURE_PSEUDONYMS[role],
        "signed_at": "2026-01-01T00:00:00+00:00",
    }


def run_fixture_e2e(*, prerequisites: dict[str, bool] | None = None) -> dict[str, Any]:
    """Run the complete workflow against synthetic fixtures under a temp path.

    ``prerequisites`` is exposed so a hostile test can prove that an empty
    prerequisite map fails C10 rather than vacuously satisfying it.
    """

    steps: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        steps.append({"step": name, "passed": bool(ok), "detail": detail})

    with unlocked_workspace(prefix="cab-fixture-e2e-") as root:
        private_root = root / "fixture_packet"
        workspace = ReviewWorkspace.fixture(private_root)
        workspace.packet_version = FIXTURE_PACKET_VERSION

        packages: dict[str, bytes] = {}
        mappings: dict[str, dict[str, str]] = {}
        item_ids: dict[str, list[str]] = {}
        qualification: dict[str, dict[str, Any]] = {}
        fixture_seed = b"cab-fixture-qualification-seed-32b"
        for role in REVIEW_ROLES:
            payload, mapping, ids = _fixture_package(role)
            packages[role] = payload
            mappings[role] = mapping
            item_ids[role] = ids
            qualification[role] = build_private_qualification(fixture_seed, role)
        record("fixture_packet_generation", len(fixture_pair_ids()) == FIXTURE_PAIR_COUNT)
        record(
            "stage1_package_generation",
            len(packages) == 2 and mappings[REVIEWER_A] != mappings[REVIEWER_B],
            "independent item order",
        )
        record(
            "private_qualification_generation",
            qualification[REVIEWER_A]["package_sha256"]
            != qualification[REVIEWER_B]["package_sha256"],
            "each reviewer receives a different qualification package",
        )

        for role in REVIEW_ROLES:
            create_assignment(
                private_root,
                packet_version=FIXTURE_PACKET_VERSION,
                reviewer_pseudonym=FIXTURE_PSEUDONYMS[role],
                role=role,
                stage1_package_hash=sha256_bytes(packages[role]),
                qualification_package_hash=qualification[role]["package_sha256"],
            )
        create_assignment(
            private_root,
            packet_version=FIXTURE_PACKET_VERSION,
            reviewer_pseudonym=FIXTURE_PSEUDONYMS[ADJUDICATOR],
            role=ADJUDICATOR,
        )
        record("reviewer_assignment_registry", len(workspace.assignments()["assignments"]) == 3)

        duplicate_rejected = False
        try:
            create_assignment(
                private_root,
                packet_version=FIXTURE_PACKET_VERSION,
                reviewer_pseudonym=FIXTURE_PSEUDONYMS[REVIEWER_A],
                role=ADJUDICATOR,
            )
        except Exception:
            duplicate_rejected = True
        record(
            "assignment_registry_refuses_role_overlap",
            duplicate_rejected,
            "a reviewer cannot also adjudicate",
        )

        for role in REVIEW_ROLES:
            workspace.ingest_declaration(
                role,
                _declaration(
                    role,
                    stage1_hash=sha256_bytes(packages[role]),
                    qualification_hash=qualification[role]["package_sha256"],
                ),
            )
        record("reviewer_declarations", True, "declarations parsed from submitted files")

        for role in REVIEW_ROLES:
            workspace.ingest_qualification(
                role, _qualification_submission(qualification[role]["answer_key"]),
                qualification[role]["answer_key"],
            )
        record("qualification_fixture", True, "both fixture reviewers qualified privately")

        for role in REVIEW_ROLES:
            workspace.ingest_stage1(
                role,
                _stage1_form(mappings[role], dispute=role == REVIEWER_B),
                expected_item_ids=item_ids[role],
                package_sha256=sha256_bytes(packages[role]),
            )
        record("stage1_fixture_ingestion", True)

        packet_commitment = sha256_bytes(b"fixture-packet-commitment")
        workspace.commit_stage1(
            packet_commitment=packet_commitment,
            package_hashes={role: sha256_bytes(payload) for role, payload in packages.items()},
            review_schema_version="cab_stage1_review_form_v2",
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
            exact_commit=FIXTURE_COMMIT,
        )
        record("stage1_commitment", workspace.has("stage1_commitment"))

        fixture_key = secrets.token_bytes(32)
        vault = seal(
            [{"pair_id": pair_id, "fixture": True} for pair_id in fixture_pair_ids()], fixture_key
        )
        roundtrip = unseal(vault, fixture_key)
        wrong_key_rejected = False
        try:
            unseal(vault, secrets.token_bytes(32))
        except Exception:
            wrong_key_rejected = True
        record(
            "stage2_fixture_vault_roundtrip",
            len(roundtrip) == FIXTURE_PAIR_COUNT and wrong_key_rejected,
            "wrong key refused",
        )

        workspace.unlock_stage2(
            packet_commitment=packet_commitment,
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
            exact_commit=FIXTURE_COMMIT,
            key_available=True,
        )
        record("stage2_fixture_unlock", workspace.has("stage2_unlock"))

        applicability_by_pair = fixture_applicability()
        for role in REVIEW_ROLES:
            per_item = {
                item_id: applicability_by_pair[mappings[role][item_id]]
                for item_id in mappings[role]
            }
            workspace.ingest_stage2(
                role,
                _stage2_form(
                    mappings[role], applicability_by_pair, objection=role == REVIEWER_A
                ),
                expected_item_ids=item_ids[role],
                applicability=per_item,
            )
        record("stage2_fixture_ingestion", True)

        stage1_queue = workspace.build_stage1_disagreements(mappings=mappings)
        stage2_queue = workspace.build_stage2_disagreements(
            mappings=mappings, applicability=applicability_by_pair
        )
        record(
            "stage1_disagreement_queue",
            stage1_queue["disputed_dimension_count"] >= 1,
            f"{stage1_queue['disputed_dimension_count']} disputed Stage-1 dimension(s)",
        )
        record(
            "stage2_disagreement_queue",
            stage2_queue["disputed_dimension_count"] >= 1,
            f"{stage2_queue['disputed_dimension_count']} disputed Stage-2 dimension(s)",
        )

        for stage, queue, final_value in (
            (STAGE1, stage1_queue, "no"),
            (STAGE2, stage2_queue, YES),
        ):
            workspace.ingest_adjudication(
                stage=stage,
                adjudicator_pseudonym=FIXTURE_PSEUDONYMS[ADJUDICATOR],
                decisions=[
                    {
                        "pair_id": row["pair_id"],
                        "dimension": row["dimension"],
                        "final_value": _fixture_final_value(stage, row, final_value),
                        "rationale": "Fixture adjudication; no genuine judgement was made.",
                        "evidence_reference": "fixture://synthetic-item",
                        "confidence": "4",
                        "exclude_item": "NO",
                    }
                    for row in queue["disputes"]
                ],
            )
        record(
            "stage1_and_stage2_adjudication",
            workspace.has("stage1_adjudication") and workspace.has("stage2_adjudication"),
        )

        agreement = workspace.compute_agreement(mappings=mappings)
        record(
            "agreement_computed_from_raw",
            agreement["adjudicated_values_used"] is False
            and agreement["stage1"]["overall_raw_agreement"] >= 0.8
            and agreement["stage2"]["overall_raw_agreement"] >= 0.8,
            f"stage1={agreement['stage1']['overall_raw_agreement']} "
            f"stage2={agreement['stage2']['overall_raw_agreement']}",
        )

        final = workspace.build_final_adjudicated_records(
            mappings=mappings,
            applicability=applicability_by_pair,
            expected_pair_count=FIXTURE_PAIR_COUNT,
        )
        record(
            "final_adjudicated_records",
            final["passed"] and final["included_count"] == FIXTURE_PAIR_COUNT,
            f"{final['included_count']} included, {final['excluded_count']} excluded",
        )

        c10 = run_c10(
            workspace,
            contract=FIXTURE_C10_CONTRACT,
            mappings=mappings,
            applicability=applicability_by_pair,
            prerequisites={"fixture_prerequisites": True}
            if prerequisites is None
            else prerequisites,
            packet_commitment=packet_commitment,
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
        )
        workspace.write("c10_report", c10)
        c10_summary = {
            "status": c10["status"],
            "mechanics_status": c10["mechanics_status"],
            "failed_checks": c10["failed_checks"],
            "counts_as_genuine_evidence": c10["counts_as_genuine_evidence"],
        }
        if prerequisites is not None:
            # A caller-supplied prerequisite map means this run exists to probe a
            # gate, not to demonstrate the happy path; stop before the lock.
            return {
                "schema_version": "cab_review_ready_v2_fixture_e2e_probe_v1",
                "status": "CAB_FIXTURE_E2E_PROBE",
                "evidence_class": FIXTURE_MARKER,
                "counts_as_genuine_evidence": False,
                "c10": c10_summary,
                "steps": steps,
                "step_count": len(steps),
                "passed": all(step["passed"] for step in steps),
            }
        record(
            "c10_fixture_evaluation",
            c10["mechanics_status"] == "C10_MECHANICS_PASS"
            and c10["status"] == "C10_PENDING_GENUINE_REVIEW"
            and c10["counts_as_genuine_evidence"] is False,
            "mechanics pass, genuine C10 still pending"
            if c10["mechanics_status"] == "C10_MECHANICS_PASS"
            else f"mechanics failed: {c10['failed_checks']}",
        )

        build_exclusion_register(workspace)
        lock_reviewed_slice(
            workspace,
            c10_report=c10,
            packet_commitment=packet_commitment,
            scorer_sha256="0" * 64,
            endpoints_sha256="1" * 64,
            analysis_plan_sha256="2" * 64,
            system_identity_sha256="3" * 64,
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
            exact_commit=FIXTURE_COMMIT,
        )
        record("fixture_slice_lock", workspace.has("slice_lock"))

        authorize_model_execution(
            workspace,
            exact_commit=FIXTURE_COMMIT,
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
            c10_report=c10,
        )
        record("fixture_execution_authorization", workspace.has("execution_authorization"))

        record(
            "fixture_evidence_is_never_genuine",
            workspace.evidence_eligibility()["counts_as_genuine_evidence"] is False,
            "no fixture artifact can satisfy the production bindings",
        )

        # A production workspace, given the very same receipt files, refuses them.
        rejected = 0
        copied = ("slice_lock", "stage1_commitment", "execution_authorization", "c10_report")
        try:
            production = ReviewWorkspace(private_root, coordinator_authority(root))
            production.packet_version = FIXTURE_PACKET_VERSION
            production.receipts.mkdir(parents=True, exist_ok=True)
            for name in copied:
                (production.receipts / f"{name}.json").write_bytes(
                    (workspace.receipts / f"{name}.json").read_bytes()
                )
            for name in copied:
                try:
                    production.read(name)
                except WorkflowError:
                    rejected += 1
            detail = "fixture receipts refused by the production authority"
        except Exception:
            rejected = len(copied)
            detail = "production receipts are unreachable without the coordinator key"
        record("production_gates_reject_fixture_receipts", rejected == len(copied), detail)

        status = workflow_status(workspace)
        record(
            "fixture_status_reports_pending",
            status["c10_status"] == "C10_PENDING_GENUINE_REVIEW",
        )

    passed = all(step["passed"] for step in steps)
    return {
        "schema_version": "cab_review_ready_v2_fixture_e2e_v2",
        "status": "CAB_TWO_STAGE_WORKFLOW_E2E_FIXTURE_VALIDATED"
        if passed
        else "CAB_FIXTURE_E2E_FAILED",
        "evidence_class": FIXTURE_MARKER,
        "counts_as_genuine_evidence": False,
        "genuine_human_judgments": 0,
        "genuine_model_trajectories": 0,
        "c10": c10_summary,
        "step_count": len(steps),
        "steps": steps,
        "passed": passed,
    }


def _fixture_final_value(stage: str, dispute: dict[str, Any], default: str) -> str:
    dimension = str(dispute["dimension"])
    if stage == STAGE1:
        if dimension == "preserved_invariants_hold":
            return "yes"
        if dimension == "exclude_item":
            return "no"
        if dimension in ("reviewer_confidence", "ambiguity_present"):
            return "resolved"
        return "yes"
    if dimension == "exclude_item":
        return "NO"
    if dimension in ("reviewer_confidence", "notes"):
        return "resolved"
    if dimension in STAGE2_CONDITIONAL_DIMENSIONS and not dispute.get("applicable", True):
        return NOT_APPLICABLE
    return default


__all__ = [
    "FIXTURE_C10_CONTRACT",
    "FIXTURE_PACKET_VERSION",
    "FIXTURE_PAIR_COUNT",
    "FIXTURE_PSEUDONYMS",
    "fixture_applicability",
    "fixture_pair_ids",
    "run_fixture_e2e",
]
