#!/usr/bin/env python3
"""Initialize private held-out v2 IDs and write a payload-free public manifest.

This command creates cryptographic material and opaque IDs only.  It does not
author task text, answers, interventions, or evaluator metadata, and it never
prints private values.  Human-authored private payloads remain a separate,
review-gated step under the ignored private root.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "private_data/heldout_challenge_v2"
PRIVATE_LOCK = PRIVATE_ROOT / "private_lock.json"
PUBLIC_MANIFEST = ROOT / "data/manifests/heldout_challenge_v2_public_manifest.json"
BASE_TASK_COUNT = 50
INSTANCES_PER_TASK = 6


def _hmac_hex(key: bytes, value: str) -> str:
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()


def _membership_commitment(key: bytes, values: list[str]) -> str:
    return _hmac_hex(key, "\n".join(sorted(values)))


def _new_lock() -> dict[str, Any]:
    seed = secrets.token_bytes(32)
    commitment_key = secrets.token_bytes(32)
    namespace = f"cab_h2_{_hmac_hex(commitment_key, seed.hex())[:16]}"
    base_ids = [
        f"{namespace}__{_hmac_hex(commitment_key, f'base:{seed.hex()}:{index}')[:24]}"
        for index in range(BASE_TASK_COUNT)
    ]
    instance_ids = [
        f"{base_id}.{_hmac_hex(commitment_key, f'instance:{base_id}:{variant}')[:16]}"
        for base_id in base_ids
        for variant in range(INSTANCES_PER_TASK)
    ]
    return {
        "schema_version": "cab_private_heldout_lock_v2",
        "created_at": datetime.now(UTC).isoformat(),
        "materialization_state": "PRIVATE_IDS_LOCKED_PAYLOAD_AUTHORING_PENDING",
        "seed_hex": seed.hex(),
        "commitment_key_hex": commitment_key.hex(),
        "id_namespace": namespace,
        "base_task_ids": base_ids,
        "instance_ids": instance_ids,
        "selection_uses_model_outputs": False,
        "paper_eligible": False,
        "scientific_execution_allowed": False,
    }


def _load_or_create_lock() -> dict[str, Any]:
    if PRIVATE_LOCK.is_file():
        value = json.loads(PRIVATE_LOCK.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("private lock must be a JSON object")
        return value
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True)
    lock = _new_lock()
    PRIVATE_LOCK.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return lock


def _build_public_manifest(lock: dict[str, Any]) -> dict[str, Any]:
    key = bytes.fromhex(str(lock["commitment_key_hex"]))
    seed_hex = str(lock["seed_hex"])
    namespace = str(lock["id_namespace"])
    base_ids = [str(value) for value in lock["base_task_ids"]]
    instance_ids = [str(value) for value in lock["instance_ids"]]
    design = {
        "split_version": "heldout_challenge_v2",
        "target_base_task_count": BASE_TASK_COUNT,
        "target_instance_count": BASE_TASK_COUNT * INSTANCES_PER_TASK,
        "selection_uses_model_outputs": False,
        "requires_private_human_authoring": True,
        "forbids_public_v1_text_reuse": True,
        "forbids_trivial_parameter_replacement": True,
    }
    design_hash = hashlib.sha256(
        json.dumps(
            design,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "cab_protected_heldout_public_manifest_v2",
        "manifest_version": 2,
        "split_version": "heldout_challenge_v2",
        "canonical_role": "heldout_challenge_v2_protected",
        "generated_at": lock["created_at"],
        "public_metadata_only": True,
        "private_materialization_state": lock["materialization_state"],
        "private_storage": {
            "root": "private_data/heldout_challenge_v2/",
            "gitignored": True,
            "files_tracked_in_public_git": False,
        },
        "aggregate_counts": {
            "target_base_task_count": BASE_TASK_COUNT,
            "target_intervention_count": BASE_TASK_COUNT
            * (INSTANCES_PER_TASK - 1),
            "target_instance_count": BASE_TASK_COUNT * INSTANCES_PER_TASK,
            "publicly_disclosed_base_task_count": 0,
            "publicly_disclosed_instance_count": 0,
        },
        "distribution_summary": {
            "target_domain_count_minimum": 8,
            "target_intervention_family_count_minimum": 10,
            "target_difficulty_levels": 4,
            "selection_basis": "design coverage and private human review only",
        },
        "commitments": {
            "algorithm": "HMAC-SHA256_WITH_PRIVATE_KEY",
            "generation_design_sha256": design_hash,
            "seed_hmac_sha256": _hmac_hex(key, f"seed:{seed_hex}"),
            "id_namespace_hmac_sha256": _hmac_hex(
                key,
                f"namespace:{namespace}",
            ),
            "base_task_membership_hmac_sha256": _membership_commitment(
                key,
                base_ids,
            ),
            "instance_membership_hmac_sha256": _membership_commitment(
                key,
                instance_ids,
            ),
        },
        "generation_constraints": {
            "new_private_seed": True,
            "new_private_identifier_namespace": True,
            "public_v1_identifier_reuse_forbidden": True,
            "public_v1_text_reuse_forbidden": True,
            "trivial_parameter_replacement_forbidden": True,
            "answer_overlap_avoided_where_feasible": True,
            "model_output_based_selection_forbidden": True,
            "exact_and_near_duplicate_scan_required": True,
            "human_review_and_c10_required": True,
        },
        "provenance_summary": (
            "Repository-authored private candidate; payload authoring, review, "
            "and lock remain pending outside public Git."
        ),
        "license_summary": (
            "CAB-authored synthetic material under DATA_LICENSE.md; third-party "
            "private material is forbidden without separate provenance review."
        ),
        "scientific_execution_allowed": False,
        "paper_eligible": False,
        "full_release_unlocked": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that the current private lock reproduces the public manifest.",
    )
    args = parser.parse_args(argv)

    if args.check and not PRIVATE_LOCK.is_file():
        print("private held-out lock is absent")
        return 1
    lock = _load_or_create_lock()
    expected = _build_public_manifest(lock)
    if args.check:
        if not PUBLIC_MANIFEST.is_file():
            print("public held-out manifest is absent")
            return 1
        actual = json.loads(PUBLIC_MANIFEST.read_text(encoding="utf-8"))
        if actual != expected:
            print("public held-out manifest does not match private commitments")
            return 1
        print(
            "private held-out v2 commitments verified "
            f"(base_tasks={BASE_TASK_COUNT}, instances={BASE_TASK_COUNT * INSTANCES_PER_TASK})"
        )
        return 0

    PUBLIC_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_MANIFEST.write_text(
        json.dumps(expected, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("initialized private held-out v2 commitments; no task payload was written to public Git")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
