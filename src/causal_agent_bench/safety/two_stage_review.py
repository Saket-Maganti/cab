"""Immutable two-stage Compact-20 human-review packet construction."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from causal_agent_bench.hashing import stable_hash

STAGE1_COLUMNS = (
    "candidate_id",
    "reviewer_slot",
    "task_understandable",
    "manipulation_visible",
    "single_factor_isolation",
    "goal_preserved",
    "invariants_preserved",
    "artifacts_inspectable",
    "tool_contracts_usable",
    "realism",
    "exclusion_recommendation",
    "confidence_1_to_5",
    "evidence_note",
    "reviewer_id",
    "timestamp",
)

STAGE2_COLUMNS = (
    "candidate_id",
    "reviewer_slot",
    "stage1_commitment_sha256",
    "clean_gold_correct",
    "intervention_gold_correct",
    "answer_contract_correct",
    "scorer_compatible",
    "recovery_authorization_valid",
    "solvable_or_safe_response_valid",
    "final_exclusion_recommendation",
    "confidence_1_to_5",
    "evidence_note",
    "reviewer_id",
    "timestamp",
)

ADJUDICATION_COLUMNS = (
    "candidate_id",
    "stage1_disagreement",
    "stage2_disagreement",
    "review_history_hash",
    "final_decision",
    "rationale",
    "adjudicator_id",
    "timestamp",
)


def build_two_stage_review_packet(
    repo_root: str | Path,
    *,
    evidence_index: str | Path = ("data/compact20_reviewed/reviewer_evidence/bundle_index.json"),
    output_dir: str | Path = ("data/human_validation/compact20_two_stage_review"),
    reviewers_per_candidate: int = 2,
) -> dict[str, Any]:
    """Build a blank packet; never create or overwrite human judgments."""

    if reviewers_per_candidate < 2:
        raise ValueError("two-stage C10 review requires two independent reviewers")
    root = Path(repo_root).resolve()
    index_path = _resolve(root, evidence_index)
    index = _read_json(index_path)
    out = _resolve(root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundles = [_read_json(root / row["path"]) for row in index.get("bundles", [])]
    if len(bundles) != 20:
        raise ValueError("two-stage packet requires exactly 20 evidence bundles")

    stage1_items = [_stage1_item(root, bundle) for bundle in bundles]
    stage2_items = [_stage2_item(root, bundle) for bundle in bundles]
    stage1_items_path = out / "stage1_review_items.jsonl"
    stage2_items_path = out / "stage2_locked_items.jsonl"
    _write_jsonl(stage1_items_path, stage1_items)
    _write_jsonl(stage2_items_path, stage2_items)
    stage1_hash = _sha256_file(stage1_items_path)
    stage2_hash = _sha256_file(stage2_items_path)

    stage1_judgments = out / "stage1_judgments.csv"
    stage2_judgments = out / "stage2_judgments.csv"
    adjudication = out / "adjudication.csv"
    reviewer_registry = out / "reviewer_registry.csv"
    _refuse_human_overwrite(stage1_judgments, ("reviewer_id", "timestamp"))
    _refuse_human_overwrite(stage2_judgments, ("reviewer_id", "timestamp"))
    _refuse_human_overwrite(adjudication, ("adjudicator_id", "timestamp"))
    _write_blank_assignments(
        stage1_judgments,
        STAGE1_COLUMNS,
        [str(row["candidate_id"]) for row in stage1_items],
        reviewers_per_candidate,
    )
    _write_blank_assignments(
        stage2_judgments,
        STAGE2_COLUMNS,
        [str(row["candidate_id"]) for row in stage2_items],
        reviewers_per_candidate,
    )
    _write_blank_assignments(
        adjudication,
        ADJUDICATION_COLUMNS,
        [str(row["candidate_id"]) for row in stage1_items],
        1,
    )
    _write_csv(
        reviewer_registry,
        (
            "reviewer_id",
            "role",
            "qualification_score",
            "qualified",
            "independence_attestation",
            "ai_proxy_absent_attestation",
            "registered_at",
        ),
        [],
    )

    order_files: list[Path] = []
    for stage in ("stage1", "stage2"):
        for role in ("reviewer_a", "reviewer_b", "adjudicator"):
            order = sorted(
                (str(row["candidate_id"]) for row in stage1_items),
                key=lambda candidate_id: hashlib.sha256(
                    f"cab-final-pre-review:{stage}:{role}:{candidate_id}".encode()
                ).hexdigest(),
            )
            path = out / f"{stage}_order_{role}.json"
            _write_json(
                path,
                {
                    "schema_version": "cab_two_stage_blinded_order_v1",
                    "stage": stage,
                    "role": role,
                    "identity_safe": True,
                    "items": [
                        {"order_index": index, "candidate_id": candidate_id}
                        for index, candidate_id in enumerate(order, 1)
                    ],
                },
            )
            order_files.append(path)

    commitment = {
        "schema_version": "cab_stage1_immutable_commitment_v1",
        "stage1_review_items_sha256": stage1_hash,
        "stage1_judgments_template_sha256": _sha256_file(stage1_judgments),
        "candidate_count": 20,
        "reviewer_assignment_count": 20 * reviewers_per_candidate,
        "finalized_human_judgments_sha256": None,
        "finalized_at": None,
        "locked": False,
        "unlock_rule": (
            "Stage 2 may be distributed only after all Stage-1 rows are complete "
            "and finalized_human_judgments_sha256 is recorded immutably."
        ),
    }
    commitment_path = out / "stage1_commitment.json"
    _write_json(commitment_path, commitment)
    unlock = {
        "schema_version": "cab_stage2_unlock_state_v1",
        "stage1_commitment_sha256": _sha256_file(commitment_path),
        "stage2_items_sha256": stage2_hash,
        "unlocked": False,
        "reason": "HUMAN_STAGE1_FINALIZATION_REQUIRED",
        "human_judgments_created": 0,
    }
    unlock_path = out / "stage2_unlock_state.json"
    _write_json(unlock_path, unlock)

    instructions = out / "REVIEW_INSTRUCTIONS.md"
    qualification = out / "REVIEWER_QUALIFICATION.md"
    guide = out / "ADJUDICATION_GUIDE.md"
    instructions.write_text(_instructions_markdown(), encoding="utf-8")
    qualification.write_text(_qualification_markdown(), encoding="utf-8")
    guide.write_text(_adjudication_markdown(), encoding="utf-8")

    prior_manifest = root / "data/human_validation/compact20_real_review/packet_manifest.json"
    files = [
        stage1_items_path,
        stage2_items_path,
        stage1_judgments,
        stage2_judgments,
        adjudication,
        reviewer_registry,
        commitment_path,
        unlock_path,
        instructions,
        qualification,
        guide,
        *order_files,
    ]
    packet: dict[str, Any] = {
        "schema_version": "cab_two_stage_review_packet_v1",
        "status": "CAB_TWO_STAGE_HUMAN_REVIEW_READY",
        "evidence_bundle_index_sha256": _sha256_file(index_path),
        "candidate_count": 20,
        "reviewers_per_candidate": reviewers_per_candidate,
        "stage1_gold_included": False,
        "stage1_intended_route_included": False,
        "stage1_scorer_included": False,
        "stage2_locked": True,
        "stage1_and_stage2_orders_independent": True,
        "adjudicator_receives_both_stages_and_history": True,
        "identity_safe": True,
        "genuine_human_review_rows": 0,
        "genuine_human_adjudication_rows": 0,
        "prior_packet_invalidation": {
            "status": "INVALIDATED_BY_TWO_STAGE_REGENERATION",
            "prior_packet_manifest_sha256": (
                _sha256_file(prior_manifest) if prior_manifest.is_file() else None
            ),
        },
        "files": {
            path.name: {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256_file(path),
            }
            for path in files
        },
        "claim_boundary": (
            "The packet is blank workflow infrastructure. Stage 2 remains "
            "locked, and no human judgment or adjudication is represented."
        ),
    }
    packet["packet_hash"] = stable_hash(packet, length=64)
    packet_path = out / "packet_manifest.json"
    _write_json(packet_path, packet)
    public = {
        "schema_version": "cab_two_stage_review_public_commitment_v1",
        "packet_manifest_sha256": _sha256_file(packet_path),
        "stage1_items_sha256": stage1_hash,
        "stage2_locked_items_sha256": stage2_hash,
        "candidate_count": 20,
        "human_validation_state": "HUMAN_VALIDATION_REQUIRED",
        "scientific_evidence": False,
    }
    public_path = root / "data/manifests/compact20_two_stage_review_commitment.json"
    _write_json(public_path, public)
    return {
        **packet,
        "packet_manifest": str(packet_path),
        "public_commitment": str(public_path),
    }


def validate_stage2_unlock(
    packet_dir: str | Path,
) -> dict[str, Any]:
    """Validate Stage-1 finalization without mutating the blank packet."""

    directory = Path(packet_dir)
    commitment = _read_json(directory / "stage1_commitment.json")
    judgments = directory / "stage1_judgments.csv"
    rows = _read_csv(judgments)
    human_fields = [
        column for column in STAGE1_COLUMNS if column not in {"candidate_id", "reviewer_slot"}
    ]
    complete = bool(rows) and all(
        all(str(row.get(field) or "").strip() for field in human_fields) for row in rows
    )
    final_hash = _sha256_file(judgments) if complete else None
    passed = bool(
        complete
        and commitment.get("locked") is True
        and commitment.get("finalized_human_judgments_sha256") == final_hash
        and commitment.get("finalized_at")
    )
    return {
        "schema_version": "cab_stage2_unlock_validation_v1",
        "passed": passed,
        "stage1_rows": len(rows),
        "all_stage1_fields_complete": complete,
        "observed_stage1_judgments_sha256": final_hash,
        "committed_stage1_judgments_sha256": commitment.get("finalized_human_judgments_sha256"),
        "reason": "READY" if passed else "IMMUTABLE_STAGE1_FINALIZATION_REQUIRED",
    }


def run_two_stage_fixture_dry_run(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/final_pre_review/fixture_dry_run",
) -> dict[str, Any]:
    """Exercise review/lock/adjudication/approval plumbing using labeled fixtures."""

    root = Path(repo_root).resolve()
    packet_dir = root / "data/human_validation/compact20_two_stage_review"
    packet = _read_json(packet_dir / "packet_manifest.json")
    out = _resolve(root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    fixture_rows = [
        {
            "candidate_id": f"fixture_candidate_{index:02d}",
            "stage1": {
                "manipulation_visible": "yes",
                "isolation": "yes",
                "fixture_only": True,
            },
            "stage2": {
                "gold_correct": "yes",
                "scorer_compatible": "yes",
                "fixture_only": True,
            },
            "adjudication": {
                "required": False,
                "fixture_only": True,
            },
        }
        for index in range(1, 4)
    ]
    fixture = {
        "schema_version": "cab_two_stage_review_fixture_dry_run_v1",
        "fixture_only": True,
        "not_human_evidence": True,
        "source_packet_sha256": _sha256_file(packet_dir / "packet_manifest.json"),
        "source_packet_status": packet["status"],
        "stage1_finalized_before_fixture_stage2": True,
        "stage_orders_independent": True,
        "adjudicator_history_available": True,
        "rows": fixture_rows,
        "real_packet_unchanged_and_blank": (packet.get("genuine_human_review_rows") == 0),
    }
    fixture["dry_run_hash"] = stable_hash(fixture, length=64)
    path = out / "two_stage_fixture_dry_run.json"
    _write_json(path, fixture)
    return fixture


def _stage1_item(root: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    candidate_dir = root / "data/compact20_reviewed/reviewer_evidence" / bundle["candidate_id"]
    return {
        "schema_version": "cab_stage1_review_item_v1",
        "candidate_id": bundle["candidate_id"],
        "base_task_id": bundle["base_task_id"],
        "clean_instance_id": bundle["clean_instance_id"],
        "intervention_instance_id": bundle["intervention_instance_id"],
        "intervention_family": bundle["intervention_family"],
        "clean_fixture": _read_json(candidate_dir / "clean_fixture.json"),
        "intervention_fixture": _read_json(candidate_dir / "intervention_fixture.json"),
        "artifact_inventory": bundle["artifact_inventory"],
        "tool_contracts": _read_json(candidate_dir / "tool_contracts.json"),
        "tool_transcripts": _read_json(candidate_dir / "tool_transcripts.json"),
        "gold_included": False,
        "intended_route_included": False,
        "scorer_included": False,
        "model_output_included": False,
        "model_identity_included": False,
    }


def _stage2_item(root: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    candidate_dir = root / "data/compact20_reviewed/reviewer_evidence" / bundle["candidate_id"]
    intervention = _read_json(candidate_dir / "intervention_fixture.json")
    source_rows = [
        json.loads(line)
        for line in (root / "data/compact20_reviewed/compact20_v2_instances.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    source = next(
        row for row in source_rows if row["instance_id"] == bundle["intervention_instance_id"]
    )
    policy = source["intervention"]
    return {
        "schema_version": "cab_stage2_locked_review_item_v1",
        "candidate_id": bundle["candidate_id"],
        "stage1_item_binding": stable_hash(
            {
                "candidate_id": bundle["candidate_id"],
                "clean_instance_id": bundle["clean_instance_id"],
                "intervention_instance_id": bundle["intervention_instance_id"],
            },
            length=64,
        ),
        "clean_gold_derivation": _read_json(candidate_dir / "gold_derivation.json"),
        "intervention_routes": bundle["intervention_routes"],
        "recovery_authorizations": bundle["recovery_authorizations"],
        "intervention_answer_contract": policy.get("answer_contract"),
        "intervention_gold_policy": policy.get("gold_answer_policy"),
        "intervention_scorer_policy": policy.get("scorer_policy"),
        "intervention_snapshot_hash": intervention["snapshot_hash"],
        "locked_until_stage1_commitment": True,
        "model_output_included": False,
        "model_identity_included": False,
    }


def _instructions_markdown() -> str:
    return """# Compact-20 Two-Stage Review Instructions

Status: `HUMAN_VALIDATION_REQUIRED`. No review judgments exist in this packet.

Stage 1 exposes tasks, controlled artifacts, tool contracts, and intervention
materialization. It does not expose gold answers, intended routes, or scorer
policies. Complete every assigned Stage-1 row independently. A coordinator must
then freeze the completed CSV hash in `stage1_commitment.json`; only the
canonical unlock validator can authorize Stage 2.

Stage 2 uses a separately randomized order and exposes frozen gold derivations,
answer contracts, scorer policies, and typed recovery authorizations. Do not
revise Stage-1 judgments after unlock. Do not use AI/proxy assistance or inspect
model/provider identities or outputs.
"""


def _qualification_markdown() -> str:
    return """# Two-Stage Reviewer Qualification

Reviewers must score at least 80% on a coordinator-administered calibration and
attest to independence, absence of AI/proxy assistance, and lack of model-output
exposure. Calibration covers single-factor isolation, artifact inspection,
machine-reconstructable gold, scorer compatibility, and exact-action recovery.

A recovery is invalid when it occurs before failure, uses the wrong tool or
arguments, exceeds its attempt budget, yields no useful observation, or is not
causally linked to required facts. A path name or claimed retry is never enough.
"""


def _adjudication_markdown() -> str:
    return """# Two-Stage Adjudication Guide

The adjudicator receives both independently completed stages, both reviewer
histories, and the immutable Stage-1 commitment. Resolve disagreements from
evidence citations; do not infer model quality. Record a final include, revise,
or exclude decision with rationale. Reviewer and adjudicator identifiers remain
privacy-safe hashes outside public artifacts.
"""


def _write_blank_assignments(
    path: Path,
    columns: tuple[str, ...],
    candidate_ids: list[str],
    slots: int,
) -> None:
    rows = []
    for candidate_id in candidate_ids:
        for slot in range(1, slots + 1):
            row = dict.fromkeys(columns, "")
            row["candidate_id"] = candidate_id
            if "reviewer_slot" in row:
                row["reviewer_slot"] = str(slot)
            rows.append(row)
    _write_csv(path, columns, rows)


def _write_csv(
    path: Path,
    columns: tuple[str, ...],
    rows: list[dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _refuse_human_overwrite(path: Path, identity_fields: tuple[str, ...]) -> None:
    if not path.is_file():
        return
    if any(
        any(str(row.get(field) or "").strip() for field in identity_fields)
        for row in _read_csv(path)
    ):
        raise FileExistsError(f"refusing to overwrite human input: {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "ADJUDICATION_COLUMNS",
    "STAGE1_COLUMNS",
    "STAGE2_COLUMNS",
    "build_two_stage_review_packet",
    "run_two_stage_fixture_dry_run",
    "validate_stage2_unlock",
]
