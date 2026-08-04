"""Fixture-only end-to-end exercise of the two-stage workflow.

The fixture packet is built from its own synthetic items.  It shares no task
body, identifier, answer or key with the final private packet, every artifact it
writes is stamped ``SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE``, and it runs
under a temporary path.  It proves workflow mechanics only: it never creates
genuine evidence, never passes C10, and never authorizes a real run.
"""

from __future__ import annotations

import secrets
from typing import Any

from causal_agent_bench.review_ready_v2.common import FIXTURE_MARKER, canonical_bytes, sha256_bytes
from causal_agent_bench.review_ready_v2.qualification import QUALIFICATION_KEY
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_FORM_COLUMNS, zip_bytes
from causal_agent_bench.review_ready_v2.vault import seal, unlocked_workspace, unseal
from causal_agent_bench.review_ready_v2.workflow import (
    STAGE2_FORM_COLUMNS,
    ReviewWorkspace,
    WorkflowError,
    authorize_model_execution,
    build_exclusion_register,
    lock_reviewed_slice,
    run_c10,
    workflow_status,
)

FIXTURE_PAIR_COUNT = 8
FIXTURE_REVIEWERS = ("fixture-reviewer-alpha", "fixture-reviewer-beta")
FIXTURE_ADJUDICATOR = "fixture-adjudicator-gamma"
FIXTURE_COMMIT = "0" * 40
FIXTURE_FREEZE_SHA = "f" * 64

FIXTURE_C10_CONTRACT: dict[str, Any] = {
    "schema_version": "cab_c10_contract_v2",
    "claim_id": "C10",
    "min_raw_agreement": 0.8,
    "expected_pair_count": FIXTURE_PAIR_COUNT,
    "evidence_class_on_pass": "AUDITED_REAL_EVIDENCE",
}

_GATING_YES = {
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


def _fixture_package(role: str) -> tuple[bytes, dict[str, str], list[str]]:
    prefix = "FA" if role.endswith("alpha") else "FB"
    pairs = fixture_pair_ids()
    if prefix == "FB":
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


def _stage1_form(item_ids: list[str], *, flip_last: bool = False) -> bytes:
    lines = [",".join(REVIEW_FORM_COLUMNS)]
    for position, item_id in enumerate(item_ids, 1):
        row = dict(_GATING_YES)
        if flip_last and position == len(item_ids):
            row["exclude_item"] = "yes"
            row["notes"] = "fixture disagreement to exercise the adjudication path"
        lines.append(",".join([item_id, *(row[name] for name in REVIEW_FORM_COLUMNS[1:])]))
    return ("\n".join(lines) + "\n").encode()


def _stage2_form(item_ids: list[str]) -> bytes:
    lines = [",".join(STAGE2_FORM_COLUMNS)]
    for item_id in item_ids:
        lines.append(",".join([item_id, "yes", "yes", "yes", "yes", "yes", "no", ""]))
    return ("\n".join(lines) + "\n").encode()


def _qualification_submission() -> dict[str, dict[str, str]]:
    return {
        item_id: {str(entry["decisive_dimension"]): str(entry["expected_value"])}
        for item_id, entry in QUALIFICATION_KEY.items()
    }


def run_fixture_e2e() -> dict[str, Any]:
    """Run the complete workflow against synthetic fixtures under a temp path."""

    steps: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        steps.append({"step": name, "passed": bool(ok), "detail": detail})

    with unlocked_workspace(prefix="cab-fixture-e2e-") as root:
        workspace = ReviewWorkspace(root / "fixture_packet", fixture=True)
        packages: dict[str, bytes] = {}
        mappings: dict[str, dict[str, str]] = {}
        item_ids: dict[str, list[str]] = {}
        for reviewer_id in FIXTURE_REVIEWERS:
            payload, mapping, ids = _fixture_package(reviewer_id)
            packages[reviewer_id] = payload
            mappings[reviewer_id] = mapping
            item_ids[reviewer_id] = ids
        record("fixture_packet_generation", len(fixture_pair_ids()) == FIXTURE_PAIR_COUNT)
        record(
            "stage1_package_generation",
            len(packages) == 2 and mappings[FIXTURE_REVIEWERS[0]] != mappings[FIXTURE_REVIEWERS[1]],
            "independent item order",
        )

        for reviewer_id in FIXTURE_REVIEWERS:
            workspace.ingest_qualification(reviewer_id, _qualification_submission())
        record("qualification_fixture", True, "both fixture reviewers qualified")

        for index, reviewer_id in enumerate(FIXTURE_REVIEWERS):
            workspace.ingest_stage1(
                reviewer_id,
                _stage1_form(item_ids[reviewer_id], flip_last=index == 1),
                expected_item_ids=item_ids[reviewer_id],
                package_sha256=sha256_bytes(packages[reviewer_id]),
            )
        record("stage1_fixture_ingestion", True)

        packet_commitment = sha256_bytes(b"fixture-packet-commitment")
        workspace.commit_stage1(
            reviewer_ids=FIXTURE_REVIEWERS,
            packet_commitment=packet_commitment,
            package_hashes={
                reviewer_id: sha256_bytes(payload) for reviewer_id, payload in packages.items()
            },
            review_schema_version="cab_stage1_review_form_v2",
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
            exact_commit=FIXTURE_COMMIT,
        )
        record("stage1_commitment", workspace.has("stage1_commitment"))

        fixture_key = secrets.token_bytes(32)
        vault = seal([{"pair_id": pair_id, "fixture": True} for pair_id in fixture_pair_ids()], fixture_key)
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

        for reviewer_id in FIXTURE_REVIEWERS:
            workspace.ingest_stage2(
                reviewer_id, _stage2_form(item_ids[reviewer_id]), expected_item_ids=item_ids[reviewer_id]
            )
        record("stage2_fixture_ingestion", True)

        queue = workspace.build_disagreement_queue(
            reviewer_ids=FIXTURE_REVIEWERS, mappings=mappings
        )
        record(
            "disagreement_queue",
            queue["disputed_pair_count"] == 1,
            f"{queue['disputed_pair_count']} disputed pair(s)",
        )

        workspace.ingest_adjudication(
            adjudicator_id=FIXTURE_ADJUDICATOR,
            reviewer_ids=FIXTURE_REVIEWERS,
            decisions=[
                {
                    "pair_id": row["pair_id"],
                    "resolved_values": {"exclude_item": "no"},
                    "rationale": "Fixture adjudication; no genuine judgement was made.",
                }
                for row in queue["disputes"]
            ],
        )
        record("fixture_adjudication", workspace.has("adjudication"))

        agreement = workspace.compute_agreement(reviewer_ids=FIXTURE_REVIEWERS, mappings=mappings)
        record(
            "agreement_computed",
            agreement["overall_raw_agreement"] >= 0.8,
            f"raw={agreement['overall_raw_agreement']}",
        )

        c10 = run_c10(
            workspace,
            contract=FIXTURE_C10_CONTRACT,
            reviewer_ids=FIXTURE_REVIEWERS,
            mappings=mappings,
            prerequisites={"fixture_prerequisites": True},
            packet_commitment=packet_commitment,
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
        )
        record(
            "c10_fixture_evaluation",
            c10["mechanics_status"] == "C10_MECHANICS_PASS"
            and c10["status"] == "C10_PENDING_GENUINE_REVIEW"
            and c10["counts_as_genuine_evidence"] is False,
            "mechanics pass, genuine C10 still pending"
            if c10["mechanics_status"] == "C10_MECHANICS_PASS"
            else f"mechanics failed: {c10['failed_checks']}",
        )

        build_exclusion_register(workspace, reviewer_ids=FIXTURE_REVIEWERS, mappings=mappings)
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
            workspace, exact_commit=FIXTURE_COMMIT, scientific_freeze_sha256=FIXTURE_FREEZE_SHA
        )
        record("fixture_execution_authorization", workspace.has("execution_authorization"))

        production = ReviewWorkspace(root / "fixture_packet", fixture=False)
        production.receipts.mkdir(parents=True, exist_ok=True)
        for name in ("slice_lock", "stage1_commitment", "execution_authorization"):
            source = workspace.receipts / f"{name}.json"
            (production.receipts / f"{name}.json").write_bytes(source.read_bytes())
        rejected = 0
        for name in ("slice_lock", "stage1_commitment", "execution_authorization"):
            try:
                production.read(name)
            except WorkflowError:
                rejected += 1
        record(
            "production_gates_reject_fixture_receipts",
            rejected == 3,
            "fixture receipts refused as genuine evidence",
        )

        status = workflow_status(workspace)
        record(
            "fixture_status_reports_pending",
            status["c10_status"] == "C10_PENDING_GENUINE_REVIEW"
            and status["model_execution"] == "MODEL_EXECUTION_BLOCKED",
        )

    passed = all(step["passed"] for step in steps)
    return {
        "schema_version": "cab_review_ready_v2_fixture_e2e_v1",
        "status": "CAB_TWO_STAGE_WORKFLOW_E2E_FIXTURE_VALIDATED" if passed else "CAB_FIXTURE_E2E_FAILED",
        "evidence_class": FIXTURE_MARKER,
        "counts_as_genuine_evidence": False,
        "genuine_human_judgments": 0,
        "genuine_model_trajectories": 0,
        "step_count": len(steps),
        "steps": steps,
        "passed": passed,
    }


__all__ = [
    "FIXTURE_ADJUDICATOR",
    "FIXTURE_C10_CONTRACT",
    "FIXTURE_PAIR_COUNT",
    "FIXTURE_REVIEWERS",
    "fixture_pair_ids",
    "run_fixture_e2e",
]
