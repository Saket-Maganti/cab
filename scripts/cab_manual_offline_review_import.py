#!/usr/bin/env python3
"""Discover, import, seal and gate the completed offline Compact-20 review.

This is the deliberately separate entry point for evidence that did not travel
through the production issue-declare-submit sequence.  It cannot be reached from
the normal commands, it requires two literal opt-in flags, and everything it
seals carries the ``MANUAL_OFFLINE_REVIEW_IMPORT_V1`` origin so that no gate
expecting production evidence can ever consume it by accident.

Subcommands::

    discover      classify candidate files by content and report what was found
    import        seal the discovered evidence into write-once snapshots
    verify        re-verify the whole immutable graph from disk
    gates         run C10, the exclusion register, the slice lock, authorization
    report        write the public counts-and-hashes reports
    status        summarise where the chain currently stands

Private evidence and sealed receipts stay outside Git.  Public reports carry
counts and hashes only, and never quote a reviewer's note.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.review_ready_v2.adjudication import STAGE1, STAGE2
from causal_agent_bench.review_ready_v2.common import (
    read_json,
    sha256_json,
    write_json,
)
from causal_agent_bench.review_ready_v2.manual_import import (
    STAGE1_ADJUDICATION,
    STAGE1_REVIEW_FORM,
    STAGE2_ADJUDICATION,
    STAGE2_REVIEW_FORM,
    ManualImportError,
    default_search_roots,
    discover_completed_review,
    discovery_report,
    select_evidence_set,
)
from causal_agent_bench.review_ready_v2.manual_import_chain import (
    REQUIRED_OPT_IN_FLAGS,
    ImportChainError,
    ImportWorkspace,
    build_disagreement_queue,
    build_final_adjudicated_records,
    compute_agreement,
    import_adjudication,
    import_review_submissions,
    record_coordinator_waiver,
    verify_imported_snapshot,
)
from causal_agent_bench.review_ready_v2.manual_import_gates import (
    authorize_model_execution,
    build_exclusion_register,
    lock_reviewed_slice,
    run_c10,
)
from causal_agent_bench.review_ready_v2.roles import (
    REVIEW_ROLES,
    REVIEWER_A,
    REVIEWER_B,
)
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_FORM_SCHEMA_VERSION
from causal_agent_bench.review_ready_v2.vault import load_key, unseal

REPORT_DIR = REPO_ROOT / "reports" / "post_human_review"
REVIEWER_REPORTS = REPO_ROOT / "reports" / "reviewer_ready_v2"
CONTRACT_PATH = REPO_ROOT / "configs" / "human_validation" / "c10_contract_v2.json"


class Blocker(RuntimeError):
    """An exact, actionable blocker.  Never a silently weakened gate."""


# --------------------------------------------------------------------------
# frozen identity
# --------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def _registry() -> dict[str, Any]:
    return read_json(REVIEWER_REPORTS / "ACTIVE_PATH_REGISTRY.json")


def _private_root() -> Path:
    return REPO_ROOT / _registry()["active_private_root"]


def _frozen_identity() -> tuple[str, str, str]:
    commitment = read_json(REVIEWER_REPORTS / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = read_json(REVIEWER_REPORTS / "SCIENTIFIC_FREEZE_V2.json")
    return commitment["commitment_sha256"], freeze["freeze_sha256"], _git("rev-parse", "HEAD")


def _mappings(private_root: Path) -> dict[str, dict[str, str]]:
    mappings: dict[str, dict[str, str]] = {}
    for role, basename in ((REVIEWER_A, "stage1_reviewer_a"), (REVIEWER_B, "stage1_reviewer_b")):
        path = private_root / "mappings" / f"{basename}_mapping.json"
        if not path.is_file():
            raise Blocker(f"the active reviewer mapping is missing: {path}")
        mappings[role] = read_json(path)["reviewer_item_to_pair"]
    return mappings


def _stage2_records(private_root: Path) -> dict[str, dict[str, Any]]:
    try:
        _, key = load_key(REPO_ROOT)
    except Exception as error:
        raise Blocker(
            f"the Stage-2 vault key is unavailable, so the frozen applicability map cannot be "
            f"read: {error}"
        ) from error
    vault = (private_root / "stage2" / "stage2_vault.enc").read_bytes()
    return {str(row["pair_id"]): row for row in unseal(vault, key)}


def _applicability(private_root: Path) -> dict[str, dict[str, bool]]:
    return {
        pair_id: dict(record["stage2_dimension_applicability"])
        for pair_id, record in _stage2_records(private_root).items()
    }


def _pair_content_hashes(private_root: Path) -> dict[str, str]:
    """Content hash per pair, taken from the frozen private pair bodies."""

    pairs = read_json(private_root / "coordinator" / "private_pairs.json")
    rows = pairs["pairs"] if isinstance(pairs, dict) and "pairs" in pairs else pairs
    if isinstance(rows, dict):
        rows = list(rows.values())
    return {str(row["pair_id"]): sha256_json(row) for row in rows}


def _workspace() -> ImportWorkspace:
    return ImportWorkspace.open(
        _private_root(), REPO_ROOT, packet_version=_registry()["active_private_packet_version"]
    )


def _require_opt_in(args: argparse.Namespace) -> None:
    if not (args.manual_offline_import and args.coordinator_declaration_waiver):
        raise Blocker(
            "this path imports evidence that never passed through the production workflow and "
            "must be requested explicitly: pass " + " and ".join(REQUIRED_OPT_IN_FLAGS)
        )


# --------------------------------------------------------------------------
# subcommands
# --------------------------------------------------------------------------


def _discover(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    roots = [Path(root).expanduser() for root in (args.search_root or [])]
    roots = [root for root in roots if root.is_dir()] or default_search_roots(REPO_ROOT)
    if not roots:
        raise Blocker(
            "no search root exists. Set CAB_HUMAN_REVIEW_INPUT_DIR or pass --search-root."
        )
    result = discover_completed_review(roots)
    try:
        chosen = select_evidence_set(result, require_qualification=args.require_qualification)
    except ManualImportError as error:
        raise Blocker(str(error)) from error
    return discovery_report(result, chosen), chosen


def cmd_discover(args: argparse.Namespace) -> dict[str, Any]:
    report, _ = _discover(args)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "HUMAN_EVIDENCE_DISCOVERY.json", report)
    return report


def cmd_import(args: argparse.Namespace) -> dict[str, Any]:
    _require_opt_in(args)
    report, chosen = _discover(args)
    workspace = _workspace()
    private_root = _private_root()
    packet_commitment, freeze_sha, exact_commit = _frozen_identity()
    mappings = _mappings(private_root)
    applicability_by_pair = _applicability(private_root)

    expected_item_ids = {role: sorted(mappings[role]) for role in REVIEW_ROLES}
    # Stage-2 applicability is keyed by reviewer item id, per reviewer.
    applicability_by_item: dict[str, dict[str, bool]] = {}
    for role in REVIEW_ROLES:
        for item_id, pair_id in mappings[role].items():
            if pair_id not in applicability_by_pair:
                raise Blocker(f"no frozen applicability record for {pair_id}")
            applicability_by_item[item_id] = applicability_by_pair[pair_id]

    waiver = (
        workspace.read("coordinator_waiver")
        if workspace.has("coordinator_waiver")
        else record_coordinator_waiver(
            workspace,
            evidence_inventory_sha256=sha256_json(report["selected"]),
            qualification_discovered=bool(report["qualification_discovered"]),
            exact_commit=exact_commit,
            scientific_freeze_sha256=freeze_sha,
            packet_commitment=packet_commitment,
        )
    )

    steps: dict[str, Any] = {"coordinator_waiver_sha256": waiver["receipt_sha256"]}

    for stage, kind in ((STAGE1, STAGE1_REVIEW_FORM), (STAGE2, STAGE2_REVIEW_FORM)):
        if workspace.has(f"{stage}_commitment"):
            steps[f"{stage}_import"] = "already_committed"
            continue
        import_review_submissions(
            workspace,
            stage=stage,
            candidates={role: chosen[f"{kind}:{role}"] for role in REVIEW_ROLES},
            expected_item_ids=expected_item_ids,
            applicability=applicability_by_item if stage == STAGE2 else None,
            waiver=waiver,
            packet_commitment=packet_commitment,
            scientific_freeze_sha256=freeze_sha,
            exact_commit=exact_commit,
            review_schema_version=REVIEW_FORM_SCHEMA_VERSION,
        )
        steps[f"{stage}_import"] = "committed"

    for stage, kind in ((STAGE1, STAGE1_ADJUDICATION), (STAGE2, STAGE2_ADJUDICATION)):
        if not workspace.has(f"{stage}_disagreement_queue"):
            build_disagreement_queue(
                workspace,
                stage=stage,
                mappings=mappings,
                applicability=applicability_by_pair if stage == STAGE2 else None,
            )
        queue = workspace.read(f"{stage}_disagreement_queue")
        steps[f"{stage}_disputed_dimensions"] = len(queue.get("disputes") or [])
        if not workspace.has(f"{stage}_adjudication"):
            import_adjudication(workspace, stage=stage, candidate=chosen[kind])
        steps[f"{stage}_adjudication"] = "sealed"

    if not workspace.has("agreement"):
        compute_agreement(workspace, mappings=mappings)
    if not workspace.has("final_adjudicated_records"):
        build_final_adjudicated_records(
            workspace,
            mappings=mappings,
            applicability=applicability_by_pair,
            expected_pair_count=int(read_json(CONTRACT_PATH)["expected_pair_count"]),
        )
    agreement = workspace.read("agreement")
    final = workspace.read("final_adjudicated_records")
    steps.update(
        {
            "stage1_overall_raw_agreement": agreement["stage1"]["overall_raw_agreement"],
            "stage2_overall_raw_agreement": agreement["stage2"]["overall_raw_agreement"],
            "included_pair_count": final["included_count"],
            "excluded_pair_count": final["excluded_count"],
            "unresolved_count": len(final["unresolved"]),
            "final_records_passed": final["passed"],
        }
    )
    return steps


def cmd_verify(args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace()
    packet_commitment, freeze_sha, exact_commit = _frozen_identity()
    verified = {}
    for stage in (STAGE1, STAGE2):
        result = verify_imported_snapshot(
            workspace,
            stage=stage,
            expected_packet_commitment=packet_commitment,
            expected_scientific_freeze_sha256=freeze_sha,
            expected_frozen_source_commit=exact_commit,
        )
        verified[stage] = {
            "commitment_sha256": result["commitment_sha256"],
            "snapshot_manifest_sha256": result["snapshot_manifest_sha256"],
            "canonical_judgement_hashes": result["canonical_judgement_hashes"],
            "check_count": len(result["checks"]),
            "all_checks_passed": all(result["checks"].values()),
        }
    return {"status": "IMMUTABLE_IMPORTED_EVIDENCE_VERIFIED", "stages": verified}


def cmd_gates(args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace()
    private_root = _private_root()
    packet_commitment, freeze_sha, exact_commit = _frozen_identity()
    contract = read_json(CONTRACT_PATH)
    mappings = _mappings(private_root)
    applicability = _applicability(private_root)

    c10 = (
        workspace.read("c10_report")
        if workspace.has("c10_report") and workspace.has("slice_lock")
        else run_c10(
            workspace,
            contract=contract,
            mappings=mappings,
            applicability=applicability,
            packet_commitment=packet_commitment,
            scientific_freeze_sha256=freeze_sha,
            exact_commit=exact_commit,
        )
    )
    if c10["c10_state"] != "PASS":
        return {
            "status": c10["status"],
            "c10_state": c10["c10_state"],
            "failed_checks": c10["failed_checks"],
            "blocker": "C10 did not pass; no slice may be locked and no execution authorized",
        }

    register = (
        workspace.read("exclusion_register")
        if workspace.has("exclusion_register")
        else build_exclusion_register(workspace)
    )
    lock = (
        workspace.read("slice_lock")
        if workspace.has("slice_lock")
        else lock_reviewed_slice(
            workspace,
            pair_content_hashes=_pair_content_hashes(private_root),
            scorer_version=str(contract["stage2_acceptance_policy_version"]),
            split_version=str(contract["packet_version"]),
            exact_commit=exact_commit,
        )
    )
    authorization = (
        workspace.read("execution_authorization")
        if workspace.has("execution_authorization")
        else authorize_model_execution(workspace, exact_commit=exact_commit)
    )
    return {
        "status": c10["status"],
        "c10_state": c10["c10_state"],
        "declaration_mode": c10["declaration_mode"],
        "qualification_mode": c10["qualification_mode"],
        "waiver_statuses": c10["waiver_statuses"],
        "included_pair_count": c10["included_pair_count"],
        "excluded_pair_count": c10["excluded_pair_count"],
        "exclusion_register_sha256": register["receipt_sha256"],
        "slice_lock_sha256": lock["receipt_sha256"],
        "pair_content_digest": lock["pair_content_digest"],
        "execution_authorization_sha256": authorization["receipt_sha256"],
        "authorized_study": authorization["authorized_study"],
        "withheld_studies": authorization["withheld_studies"],
    }


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    try:
        workspace = _workspace()
    except ImportChainError as error:
        return {"status": "MANUAL_IMPORT_UNAVAILABLE", "reason": str(error)}
    present = {
        name: workspace.has(name)
        for name in (
            "coordinator_waiver",
            "stage1_commitment",
            "stage2_commitment",
            "stage1_adjudication",
            "stage2_adjudication",
            "agreement",
            "final_adjudicated_records",
            "c10_report",
            "exclusion_register",
            "slice_lock",
            "execution_authorization",
        )
    }
    state = "MANUAL_IMPORT_NOT_STARTED"
    if present["execution_authorization"]:
        state = "COMPACT20_EXECUTION_AUTHORIZED"
    elif present["c10_report"]:
        state = "C10_COMPUTED"
    elif present["stage2_commitment"]:
        state = "EVIDENCE_IMPORTED"
    elif present["coordinator_waiver"]:
        state = "WAIVER_RECORDED"
    return {
        "status": state,
        "artifact_origin": workspace.authority.origin,
        "receipts_present": present,
        "genuine_model_trajectories": 0,
    }


# --------------------------------------------------------------------------
# public reports
# --------------------------------------------------------------------------


def cmd_report(args: argparse.Namespace) -> dict[str, Any]:
    """Write the public reports.  Counts and hashes only; no note text."""

    workspace = _workspace()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def emit(name: str, payload: dict[str, Any]) -> None:
        write_json(REPORT_DIR / name, payload)
        written.append(name)

    waiver = workspace.read("coordinator_waiver")
    emit(
        "COORDINATOR_DECLARATION_WAIVER.json",
        {
            key: value
            for key, value in waiver.items()
            if key not in ("receipt_mac",)
        },
    )

    stage1 = verify_imported_snapshot(workspace, stage=STAGE1)
    stage2 = verify_imported_snapshot(workspace, stage=STAGE2)
    emit(
        "MANUAL_IMPORT_PROVENANCE.json",
        {
            "schema_version": "cab_manual_import_provenance_v1",
            "artifact_origin": workspace.authority.origin,
            "evidence_origin": waiver["evidence_origin"],
            "original_issue_receipt_available": waiver["original_issue_receipt_available"],
            "declaration_files_collected": waiver["declaration_files_collected"],
            "qualification_evidence_imported": waiver["qualification_evidence_imported"],
            "receipt_semantics": "import receipt, not retroactive issue receipt",
            "coordinator_waiver_sha256": waiver["receipt_sha256"],
            "stage1_commitment_sha256": stage1["commitment_sha256"],
            "stage2_commitment_sha256": stage2["commitment_sha256"],
            "stage1_submission_payload_hashes": stage1["payload_hashes"],
            "stage2_submission_payload_hashes": stage2["payload_hashes"],
            "stage1_submission_canonical_hashes": stage1["canonical_content_hashes"],
            "stage2_submission_canonical_hashes": stage2["canonical_content_hashes"],
        },
    )
    emit(
        "IMMUTABLE_IMPORTED_EVIDENCE_GRAPH.json",
        {
            "schema_version": "cab_immutable_imported_evidence_graph_v1",
            "stage1_snapshot_manifest_sha256": stage1["snapshot_manifest_sha256"],
            "stage2_snapshot_manifest_sha256": stage2["snapshot_manifest_sha256"],
            "stage1_canonical_judgement_hashes": stage1["canonical_judgement_hashes"],
            "stage2_canonical_judgement_hashes": stage2["canonical_judgement_hashes"],
            "stage1_snapshot_receipt_file_hashes": stage1["snapshot_receipt_file_hashes"],
            "stage2_snapshot_receipt_file_hashes": stage2["snapshot_receipt_file_hashes"],
            "adjudication_receipt_hashes": {
                stage: workspace.read(f"{stage}_adjudication")["receipt_sha256"]
                for stage in (STAGE1, STAGE2)
            },
            "disagreement_queue_hashes": {
                stage: workspace.read(f"{stage}_disagreement_queue")["receipt_sha256"]
                for stage in (STAGE1, STAGE2)
            },
            "all_checks_passed": all(stage1["checks"].values()) and all(stage2["checks"].values()),
        },
    )

    agreement = workspace.read("agreement")
    emit(
        "AGREEMENT_FINAL.json",
        {
            "schema_version": "cab_manual_import_agreement_v1",
            "computed_from": agreement["computed_from"],
            "adjudicated_values_used": agreement["adjudicated_values_used"],
            "stage1": agreement["stage1"],
            "stage2": agreement["stage2"],
            "agreement_receipt_sha256": agreement["receipt_sha256"],
        },
    )

    final = workspace.read("final_adjudicated_records")
    emit(
        "HUMAN_EVIDENCE_VALIDATION.json",
        {
            "schema_version": "cab_human_evidence_validation_v1",
            "stage1_rows_per_reviewer": {
                role: len(stage1["receipts"][role]["judgements"]) for role in REVIEW_ROLES
            },
            "stage2_rows_per_reviewer": {
                role: len(stage2["receipts"][role]["judgements"]) for role in REVIEW_ROLES
            },
            "stage1_disputed_dimensions": len(
                workspace.read("stage1_disagreement_queue").get("disputes") or []
            ),
            "stage2_disputed_dimensions": len(
                workspace.read("stage2_disagreement_queue").get("disputes") or []
            ),
            "stage1_overall_raw_agreement": agreement["stage1"]["overall_raw_agreement"],
            "stage2_overall_raw_agreement": agreement["stage2"]["overall_raw_agreement"],
            "included_pair_count": final["included_count"],
            "excluded_pair_count": final["excluded_count"],
            "unresolved_count": len(final["unresolved"]),
            "final_records_passed": final["passed"],
            "provenance_counts": final["provenance_counts"],
            "qualification_scored_in_this_chain": False,
            "qualification_note": (
                "No qualification submission was imported. No qualification rate is claimed, "
                "re-derived, or implied anywhere in this chain."
            ),
            "private_notes_quoted": False,
        },
    )

    for name, receipt_name in (
        ("C10_FINAL.json", "c10_report"),
        ("EXCLUSION_REGISTER_FINAL.json", "exclusion_register"),
        ("REVIEWED_SLICE_LOCK_FINAL.json", "slice_lock"),
        ("EXECUTION_AUTHORIZATION_FINAL.json", "execution_authorization"),
    ):
        if workspace.has(receipt_name):
            emit(name, {k: v for k, v in workspace.read(receipt_name).items() if k != "receipt_mac"})

    return {"written": sorted(written), "output_dir": str(REPORT_DIR)}


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


COMMANDS = {
    "discover": cmd_discover,
    "import": cmd_import,
    "verify": cmd_verify,
    "gates": cmd_gates,
    "report": cmd_report,
    "status": cmd_status,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument(
        "--search-root",
        action="append",
        help="a directory to search for completed review files (repeatable)",
    )
    parser.add_argument(
        "--manual-offline-import",
        action="store_true",
        help="required opt-in: import evidence that bypassed the production workflow",
    )
    parser.add_argument(
        "--coordinator-declaration-waiver",
        action="store_true",
        help="required opt-in: proceed without separate reviewer declaration files",
    )
    parser.add_argument(
        "--require-qualification",
        action="store_true",
        help="refuse to proceed unless completed qualification submissions are discovered",
    )
    args = parser.parse_args(argv)

    try:
        payload = COMMANDS[args.command](args)
    except (Blocker, ImportChainError, ManualImportError) as error:
        print(json.dumps({"status": "BLOCKED", "blocker": str(error)}, indent=2))
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
