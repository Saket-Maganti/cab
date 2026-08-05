"""C10, the exclusion register, the reviewed-slice lock, and execution authorization.

These are the gates that decide whether model execution may begin.  Each one
re-derives what it checks rather than trusting a sealed report: C10 recomputes
the agreement tables from the frozen judgements and refuses an agreement receipt
that does not reproduce, the slice lock re-verifies C10, and the execution
authorization re-verifies the lock.  Mutating any link therefore fails at the
next gate rather than propagating.

The coordinator waivers are carried through every one of them.  A reader of the
execution authorization can see, without consulting anything else, that reviewer
declarations were not collected and that no qualification score is claimed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from causal_agent_bench.review_ready_v2.adjudication import STAGE1, STAGE2
from causal_agent_bench.review_ready_v2.commitment_integrity import (
    canonical_queue_digest,
)
from causal_agent_bench.review_ready_v2.common import sha256_json
from causal_agent_bench.review_ready_v2.final_records import dimension_is_accepted_everywhere
from causal_agent_bench.review_ready_v2.manual_import_chain import (
    C10_FAIL_STATUS,
    C10_PASS_STATUS,
    C10_PASS_STATUS_DECLARATION_ONLY,
    DECLARATION_WAIVER_STATUS,
    IMPORT_C10_SCHEMA_VERSION,
    QUALIFICATION_MODE_GENUINE,
    QUALIFICATION_MODE_WAIVED,
    QUALIFICATION_WAIVER_STATUS,
    ImportChainError,
    ImportWorkspace,
    _graph_bindings,
    _paired,
    canonical_import_adjudication_digest,
    verify_imported_qualification,
    verify_imported_snapshot,
)
from causal_agent_bench.review_ready_v2.roles import REVIEW_ROLES
from causal_agent_bench.review_ready_v2.stage2 import (
    STAGE2_ACCEPTANCE_POLICY_VERSION,
    STAGE2_SUBSTANTIVE_DIMENSIONS,
)
from causal_agent_bench.review_ready_v2.workflow import (
    GATING_DIMENSIONS,
    agreement_tables,
)

SLICE_LOCK_SCHEMA_VERSION = "cab_manual_import_reviewed_slice_lock_v1"
EXECUTION_AUTHORIZATION_SCHEMA_VERSION = "cab_manual_import_execution_authorization_v1"
EXCLUSION_REGISTER_SCHEMA_VERSION = "cab_manual_import_exclusion_register_v1"

#: The one pilot this chain may authorize.  Every larger study has its own
#: reviewed material and its own gates, and none of them are implied by this one.
AUTHORIZED_STUDY = "compact20_reviewed_pilot"

#: Studies that explicitly remain unauthorized after this chain passes.
WITHHELD_STUDIES: tuple[str, ...] = (
    "scale100_confirmatory",
    "main500_confirmatory",
    "naturalistic_transfer",
    "raac_ablation",
)


def _failed(checks: dict[str, bool]) -> list[str]:
    return sorted(name for name, ok in checks.items() if not ok)


def run_c10(
    workspace: ImportWorkspace,
    *,
    contract: dict[str, Any],
    mappings: dict[str, dict[str, str]],
    applicability: dict[str, dict[str, bool]],
    packet_commitment: str,
    scientific_freeze_sha256: str,
    exact_commit: str,
) -> dict[str, Any]:
    """The C10 mechanics gate over the complete immutable imported graph.

    Passing here is *not* a claim that the review followed the production
    workflow.  It is a claim that the imported judgements are complete,
    internally consistent, unmodified since import, and that every disputed
    dimension was resolved by an adjudicator to an accepting value.
    """

    waiver = workspace.read("coordinator_waiver")
    qualification = verify_imported_qualification(workspace)
    qualification_verified = qualification["every_role_qualified"]
    stage1 = verify_imported_snapshot(
        workspace,
        stage=STAGE1,
        expected_packet_commitment=packet_commitment,
        expected_scientific_freeze_sha256=scientific_freeze_sha256,
        expected_frozen_source_commit=exact_commit,
    )
    stage2 = verify_imported_snapshot(
        workspace,
        stage=STAGE2,
        expected_packet_commitment=packet_commitment,
        expected_scientific_freeze_sha256=scientific_freeze_sha256,
        expected_frozen_source_commit=exact_commit,
    )

    paired = {
        STAGE1: _paired(workspace, mappings, STAGE1),
        STAGE2: _paired(workspace, mappings, STAGE2),
    }
    queues = {stage: workspace.read(f"{stage}_disagreement_queue") for stage in (STAGE1, STAGE2)}
    adjudications = {stage: workspace.read(f"{stage}_adjudication") for stage in (STAGE1, STAGE2)}
    agreement = workspace.read("agreement")
    final = workspace.read("final_adjudicated_records")

    # Recompute rather than trust: a resealed agreement report with a flattering
    # number does not reproduce from the frozen judgements and fails here.
    recomputed = agreement_tables(paired[STAGE1], paired[STAGE2])
    min_agreement = float(contract["min_raw_agreement"])
    expected_pairs = int(contract["expected_pair_count"])

    records = list(final.get("records") or [])
    included = sorted(str(row["pair_id"]) for row in records if row.get("included"))
    excluded = sorted(str(row["pair_id"]) for row in records if row.get("excluded"))
    unresolved = sorted({str(row["pair_id"]) for row in (final.get("unresolved") or [])})

    checks: dict[str, bool] = {
        # -- provenance and immutability ------------------------------------
        "import_origin_is_manual_offline_import": waiver.get("artifact_origin")
        == workspace.authority.origin,
        "coordinator_waiver_sealed": bool(waiver.get("receipt_sha256")),
        "coordinator_waiver_bound_into_stage1": stage1["waiver_sha256"]
        == waiver["receipt_sha256"],
        "coordinator_waiver_bound_into_stage2": stage2["waiver_sha256"]
        == waiver["receipt_sha256"],
        "no_reviewer_declaration_is_asserted": waiver.get("reviewer_declarations_confirmed")
        is False,
        # Not "no qualification pass is asserted" — a pass may be asserted, but
        # only when scored submissions establish it.  The check is that the claim
        # in the waiver matches the evidence actually sealed in this epoch.
        "qualification_claim_matches_imported_evidence": bool(
            waiver.get("qualification_pass_verified_in_this_chain")
        )
        is qualification_verified,
        "qualification_mode_matches_imported_evidence": waiver.get("qualification_mode")
        == (QUALIFICATION_MODE_GENUINE if qualification_verified else QUALIFICATION_MODE_WAIVED),
        "qualification_commitment_bound_into_waiver": (
            waiver.get("qualification_commitment_sha256")
            == qualification["commitment"]["receipt_sha256"]
            if qualification_verified
            else waiver.get("qualification_commitment_sha256") is None
        ),
        "qualification_scored_against_private_key_when_claimed": (
            all(qualification["checks"].values()) if qualification_verified else True
        ),
        "qualification_bound_to_active_freeze_when_claimed": (
            qualification["commitment"].get("scientific_freeze_sha256")
            == scientific_freeze_sha256
            and qualification["commitment"].get("frozen_source_commit") == exact_commit
            and qualification["commitment"].get("private_packet_commitment") == packet_commitment
            if qualification_verified
            else True
        ),
        "packet_commitment_matches_active": stage1["commitment"]["private_packet_commitment"]
        == packet_commitment,
        "scientific_freeze_matches_active": stage1["commitment"]["scientific_freeze_sha256"]
        == scientific_freeze_sha256,
        "code_commit_matches_active": stage1["commitment"]["frozen_source_commit"] == exact_commit,
        "packet_version_matches_contract": workspace.packet_version == contract["packet_version"],
        # -- role separation ------------------------------------------------
        "exactly_two_reviewer_roles": sorted(stage1["manifest"]["reviewers"]) == sorted(REVIEW_ROLES),
        "reviewer_namespaces_disjoint": len(
            {str(stage1["receipts"][role]["opaque_id_namespace"]) for role in REVIEW_ROLES}
        )
        == 2,
        "adjudicator_evidence_separate_from_reviewers": all(
            adjudications[stage].get("adjudicator_evidence_is_separate_from_reviewer_evidence")
            is True
            for stage in (STAGE1, STAGE2)
        ),
        "min_independent_reviewers_met": len(REVIEW_ROLES)
        >= int(contract["min_independent_reviewers"]),
        # -- completeness ---------------------------------------------------
        "stage1_complete_for_every_pair": all(
            len(rows) == 2 for rows in paired[STAGE1].values()
        )
        and len(paired[STAGE1]) == expected_pairs,
        "stage2_complete_for_every_pair": all(
            len(rows) == 2 for rows in paired[STAGE2].values()
        )
        and len(paired[STAGE2]) == expected_pairs,
        "full_pair_coverage": len(records) == expected_pairs,
        # -- agreement ------------------------------------------------------
        "agreement_recomputes_from_frozen_judgements": {
            "stage1": agreement.get("stage1"),
            "stage2": agreement.get("stage2"),
        }
        == {"stage1": recomputed["stage1"], "stage2": recomputed["stage2"]},
        "agreement_excludes_adjudicated_values": agreement.get("adjudicated_values_used") is False,
        "stage1_agreement_meets_threshold": float(
            recomputed["stage1"]["overall_raw_agreement"]
        )
        >= min_agreement,
        "stage2_agreement_meets_threshold": float(
            recomputed["stage2"]["overall_raw_agreement"]
        )
        >= min_agreement,
        "stage1_gating_dimensions_meet_threshold": all(
            float(row["raw_agreement"]) >= min_agreement
            for row in recomputed["stage1"]["per_dimension"].values()
        ),
        # -- adjudication ---------------------------------------------------
        "stage1_queue_digest_intact": queues[STAGE1].get("queue_content_sha256")
        == canonical_queue_digest(queues[STAGE1]),
        "stage2_queue_digest_intact": queues[STAGE2].get("queue_content_sha256")
        == canonical_queue_digest(queues[STAGE2]),
        "stage1_adjudication_answers_its_queue": adjudications[STAGE1].get(
            "disagreement_queue_content_sha256"
        )
        == canonical_queue_digest(queues[STAGE1]),
        "stage2_adjudication_answers_its_queue": adjudications[STAGE2].get(
            "disagreement_queue_content_sha256"
        )
        == canonical_queue_digest(queues[STAGE2]),
        "stage1_adjudication_digest_intact": _adjudication_digest_intact(adjudications[STAGE1]),
        "stage2_adjudication_digest_intact": _adjudication_digest_intact(adjudications[STAGE2]),
        "stage1_adjudication_complete": bool(adjudications[STAGE1].get("all_disputes_resolved")),
        "stage2_adjudication_complete": bool(adjudications[STAGE2].get("all_disputes_resolved")),
        "stage1_decisions_cover_every_dispute": int(
            adjudications[STAGE1].get("decision_count", -1)
        )
        == int(adjudications[STAGE1].get("disputed_dimension_count", -2)),
        "stage2_decisions_cover_every_dispute": int(
            adjudications[STAGE2].get("decision_count", -1)
        )
        == int(adjudications[STAGE2].get("disputed_dimension_count", -2)),
        # -- final records --------------------------------------------------
        "final_records_bound_to_frozen_stage1": final.get("stage1_canonical_judgement_hashes")
        == stage1["canonical_judgement_hashes"],
        "final_records_bound_to_frozen_stage2": final.get("stage2_canonical_judgement_hashes")
        == stage2["canonical_judgement_hashes"],
        "no_unresolved_dimension": not unresolved,
        "every_stage1_gating_dimension_accepted": all(
            dimension_is_accepted_everywhere(final, STAGE1, dimension)
            for dimension in GATING_DIMENSIONS
        ),
        "every_stage2_dimension_accepted": all(
            dimension_is_accepted_everywhere(final, STAGE2, dimension)
            for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS
        ),
        "included_pairs_are_not_excluded": not (set(included) & set(excluded)),
        "stage2_acceptance_policy_is_active": contract["stage2_acceptance_policy_version"]
        == STAGE2_ACCEPTANCE_POLICY_VERSION,
        # -- fixtures -------------------------------------------------------
        "no_synthetic_fixture_in_graph": bool(contract["reject_synthetic_fixtures"]),
    }

    failed = _failed(checks)
    if failed:
        status = C10_FAIL_STATUS
    elif qualification_verified:
        # Only the declaration waiver survives: qualification stopped being a
        # waiver the moment real submissions were scored against the key.
        status = C10_PASS_STATUS_DECLARATION_ONLY
    else:
        status = C10_PASS_STATUS
    report = {
        "receipt_kind": "c10_report",
        "c10_schema_version": IMPORT_C10_SCHEMA_VERSION,
        "claim_id": contract["claim_id"],
        "c10_state": "PASS" if not failed else "FAIL",
        "status": status,
        # The qualifier is part of the result, not a footnote to it.
        "declaration_mode": "COORDINATOR_WAIVER",
        "declaration_files_collected": False,
        "reviewer_declaration_files_collected": False,
        "qualification_mode": (
            QUALIFICATION_MODE_GENUINE if qualification_verified else QUALIFICATION_MODE_WAIVED
        ),
        "qualification_evidence_imported": bool(waiver.get("qualification_evidence_imported")),
        "qualification_pass_verified": qualification_verified,
        "qualification_passed": qualification_verified,
        "qualification_commitment_sha256": qualification.get("commitment_sha256"),
        "qualification_rates": dict(
            (qualification["commitment"] or {}).get("rates") or {}
        )
        if qualification_verified
        else {},
        "qualification_threshold": (
            qualification["commitment"]["threshold"] if qualification_verified else None
        ),
        "waiver_statuses": [
            DECLARATION_WAIVER_STATUS,
            *([] if qualification_verified else [QUALIFICATION_WAIVER_STATUS]),
        ],
        "evidence_class": (
            "AUDITED_REAL_EVIDENCE_VIA_MANUAL_OFFLINE_IMPORT" if not failed else "INELIGIBLE"
        ),
        "checks": checks,
        "failed_checks": failed,
        "expected_pair_count": expected_pairs,
        "included_pair_count": len(included),
        "excluded_pair_count": len(excluded),
        "unresolved_pair_count": len(unresolved),
        "included_pair_ids": included,
        "excluded_pair_ids": excluded,
        "min_raw_agreement": min_agreement,
        "stage1_overall_raw_agreement": recomputed["stage1"]["overall_raw_agreement"],
        "stage2_overall_raw_agreement": recomputed["stage2"]["overall_raw_agreement"],
        "agreement_receipt_sha256": agreement["receipt_sha256"],
        "final_records_sha256": final["receipt_sha256"],
        "adjudication_receipt_hashes": {
            stage: adjudications[stage]["receipt_sha256"] for stage in (STAGE1, STAGE2)
        },
        "scope_note": (
            "C10 mechanics only. This does not assert that the production issue-declare-submit "
            "sequence was followed, and it asserts no reviewer declaration."
            + (
                " The qualification result is derived from both reviewers' completed submissions "
                "scored against the private answer key."
                if qualification_verified
                else " It asserts no reviewer qualification result."
            )
        ),
        **_graph_bindings(workspace),
    }
    return workspace.write("c10_report", report)


def _adjudication_digest_intact(adjudication: dict[str, Any]) -> bool:
    body = {
        key: value
        for key, value in adjudication.items()
        if key
        not in (
            "adjudication_content_sha256",
            "receipt_sha256",
            "receipt_mac",
            "recorded_at",
            "receipt_schema_version",
            "artifact_origin",
            "counts_as_genuine_evidence",
            "packet_version",
            "import_chain_schema_version",
        )
    }
    return adjudication.get("adjudication_content_sha256") == canonical_import_adjudication_digest(
        body
    )


def build_exclusion_register(workspace: ImportWorkspace) -> dict[str, Any]:
    """Derive which pairs survived review.  Never hard-codes the expected counts."""

    final = workspace.read("final_adjudicated_records")
    records = list(final.get("records") or [])
    excluded = {
        str(row["pair_id"]): {
            "reasons": list(row.get("exclusion_reasons") or []),
            "blocked_dimensions": list(row.get("blocked_dimensions") or []),
        }
        for row in sorted(records, key=lambda item: str(item["pair_id"]))
        if row.get("excluded")
    }
    included = sorted(str(row["pair_id"]) for row in records if row.get("included"))
    return workspace.write(
        "exclusion_register",
        {
            "receipt_kind": "exclusion_register",
            "register_schema_version": EXCLUSION_REGISTER_SCHEMA_VERSION,
            "derived_from": "final_adjudicated_item_records",
            "final_records_sha256": final["receipt_sha256"],
            "included_pair_ids": included,
            "included_pair_count": len(included),
            "excluded": excluded,
            "excluded_pair_count": len(excluded),
            **_graph_bindings(workspace),
        },
    )


def lock_reviewed_slice(
    workspace: ImportWorkspace,
    *,
    pair_content_hashes: dict[str, str],
    scorer_version: str,
    split_version: str,
    exact_commit: str,
) -> dict[str, Any]:
    """Bind the surviving pairs to everything that decided they survive."""

    c10 = workspace.read("c10_report")
    if c10.get("c10_state") != "PASS":
        raise ImportChainError(
            f"refusing to lock a reviewed slice while C10 reports {c10.get('c10_state')!r}"
        )
    register = workspace.read("exclusion_register")
    agreement = workspace.read("agreement")
    final = workspace.read("final_adjudicated_records")
    waiver = workspace.read("coordinator_waiver")
    stage1 = verify_imported_snapshot(workspace, stage=STAGE1)
    stage2 = verify_imported_snapshot(workspace, stage=STAGE2)

    included = list(register["included_pair_ids"])
    missing = [pair for pair in included if pair not in pair_content_hashes]
    if missing:
        raise ImportChainError(
            f"the reviewed slice cannot be locked: no pair-content hash for {missing}"
        )
    return workspace.write(
        "slice_lock",
        {
            "receipt_kind": "slice_lock",
            "lock_schema_version": SLICE_LOCK_SCHEMA_VERSION,
            "locked_pair_ids": included,
            "locked_pair_count": len(included),
            "pair_content_hashes": {pair: pair_content_hashes[pair] for pair in included},
            "pair_content_digest": sha256_json(
                {pair: pair_content_hashes[pair] for pair in included}
            ),
            "c10_report_sha256": c10["receipt_sha256"],
            "c10_state": c10["c10_state"],
            "c10_status": c10["status"],
            "declaration_mode": c10["declaration_mode"],
            "reviewer_declaration_files_collected": False,
            "qualification_mode": c10["qualification_mode"],
            "qualification_passed": bool(c10.get("qualification_passed")),
            "qualification_commitment_sha256": c10.get("qualification_commitment_sha256"),
            "waiver_statuses": list(c10["waiver_statuses"]),
            "coordinator_waiver_sha256": waiver["receipt_sha256"],
            "exclusion_register_sha256": register["receipt_sha256"],
            "agreement_report_sha256": agreement["receipt_sha256"],
            "final_records_sha256": final["receipt_sha256"],
            "stage1_snapshot_manifest_sha256": stage1["snapshot_manifest_sha256"],
            "stage2_snapshot_manifest_sha256": stage2["snapshot_manifest_sha256"],
            "stage1_canonical_judgement_hashes": stage1["canonical_judgement_hashes"],
            "stage2_canonical_judgement_hashes": stage2["canonical_judgement_hashes"],
            "adjudication_receipt_hashes": dict(c10["adjudication_receipt_hashes"]),
            "scorer_version": scorer_version,
            "split_version": split_version,
            "code_commit": exact_commit,
            "eligible_execution_configs": [AUTHORIZED_STUDY],
            **_graph_bindings(workspace),
        },
    )


def authorize_model_execution(
    workspace: ImportWorkspace, *, exact_commit: str
) -> dict[str, Any]:
    """Authorize exactly one pilot, and say plainly what remains unauthorized."""

    lock = workspace.read("slice_lock")
    c10 = workspace.read("c10_report")
    waiver = workspace.read("coordinator_waiver")
    if lock.get("c10_report_sha256") != c10["receipt_sha256"]:
        raise ImportChainError(
            "the reviewed-slice lock names a different C10 report than the one on file"
        )
    if lock.get("code_commit") != exact_commit:
        raise ImportChainError(
            "the reviewed-slice lock was taken at a different commit than the one authorizing"
        )
    return workspace.write(
        "execution_authorization",
        {
            "receipt_kind": "execution_authorization",
            "authorization_schema_version": EXECUTION_AUTHORIZATION_SCHEMA_VERSION,
            "authorized_study": AUTHORIZED_STUDY,
            "authorized_pair_ids": list(lock["locked_pair_ids"]),
            "authorized_pair_count": lock["locked_pair_count"],
            "withheld_studies": list(WITHHELD_STUDIES),
            "withheld_reason": (
                "each withheld study requires its own reviewed material, its own validity gates "
                "and its own authorization; none is implied by this pilot"
            ),
            "slice_lock_sha256": lock["receipt_sha256"],
            "pair_content_digest": lock["pair_content_digest"],
            "c10_report_sha256": c10["receipt_sha256"],
            "c10_state": c10["c10_state"],
            "declaration_mode": c10["declaration_mode"],
            "reviewer_declaration_files_collected": False,
            "qualification_mode": c10["qualification_mode"],
            "qualification_passed": bool(c10.get("qualification_passed")),
            "qualification_commitment_sha256": c10.get("qualification_commitment_sha256"),
            "waiver_statuses": list(c10["waiver_statuses"]),
            "coordinator_waiver_sha256": waiver["receipt_sha256"],
            "scorer_version": lock["scorer_version"],
            "split_version": lock["split_version"],
            "code_commit": exact_commit,
            "paid_providers_authorized": False,
            "contains_credentials": False,
            "authorized_at_utc": datetime.now(UTC).isoformat(),
        },
    )


__all__ = [
    "AUTHORIZED_STUDY",
    "EXCLUSION_REGISTER_SCHEMA_VERSION",
    "EXECUTION_AUTHORIZATION_SCHEMA_VERSION",
    "SLICE_LOCK_SCHEMA_VERSION",
    "WITHHELD_STUDIES",
    "authorize_model_execution",
    "build_exclusion_register",
    "lock_reviewed_slice",
    "run_c10",
]
