"""Hash-bound scientific freeze, exact-HEAD release, and execution gate."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from causal_agent_bench.final_pre_run.private_packet import canonical_bytes


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_head(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_freeze_manifest(repo_root: Path, *, generator_commit: str) -> dict[str, Any]:
    commitment_path = repo_root / "data/manifests/compact20_final_private_commitment.json"
    endpoint_path = repo_root / "configs/pre_run/frozen_endpoints.json"
    analysis_path = repo_root / "configs/final_hostile_pre_run/analysis_plan.json"
    power_path = repo_root / "configs/final_hostile_pre_run/power_plan.json"
    system_path = repo_root / "configs/pre_run/evaluated_system_identity.schema.json"
    review_path = repo_root / "docs/final_hostile_pre_run/HUMAN_REVIEW_PROTOCOL.md"
    c10_path = repo_root / "configs/human_validation/c10_contract_v1.json"
    generator_path = repo_root / "src/causal_agent_bench/final_pre_run/private_packet.py"
    scorer_path = repo_root / "configs/final_hostile_pre_run/scorer.json"
    commitment = json.loads(commitment_path.read_text())
    endpoints = json.loads(endpoint_path.read_text())
    scorer = json.loads(scorer_path.read_text())
    manifest: dict[str, Any] = {
        "schema_version": "cab_scientific_freeze_manifest_v1",
        "status": "CAB_REPOSITORY_FROZEN_FOR_HUMAN_REVIEW",
        "benchmark_version": "cab-compact20-private-v1",
        "packet_commitment": {
            "path": str(commitment_path.relative_to(repo_root)),
            "sha256": file_sha256(commitment_path),
            "commitment_sha256": commitment["commitment_sha256"],
        },
        "stage1_package_hashes": commitment["stage1_package_hashes"],
        "stage2_encrypted_commitment": commitment["stage2_encrypted_sha256"],
        "scorer": {
            "path": str(scorer_path.relative_to(repo_root)),
            "name": scorer["scorer_name"],
            "version": scorer["scorer_version"],
            "sha256": file_sha256(scorer_path),
        },
        "endpoints": {
            "path": str(endpoint_path.relative_to(repo_root)),
            "version": endpoints["freeze_version"],
            "sha256": file_sha256(endpoint_path),
        },
        "analysis_plan": {
            "path": str(analysis_path.relative_to(repo_root)),
            "sha256": file_sha256(analysis_path),
        },
        "power_plan": {
            "path": str(power_path.relative_to(repo_root)),
            "sha256": file_sha256(power_path),
        },
        "system_identity_schema": {
            "path": str(system_path.relative_to(repo_root)),
            "sha256": file_sha256(system_path),
        },
        "review_protocol": {
            "path": str(review_path.relative_to(repo_root)),
            "sha256": file_sha256(review_path),
        },
        "c10_contract": {
            "path": str(c10_path.relative_to(repo_root)),
            "sha256": file_sha256(c10_path),
        },
        "generator": {
            "path": str(generator_path.relative_to(repo_root)),
            "source_sha256": file_sha256(generator_path),
            "source_commit": generator_commit,
        },
        "invalidation_rules": {
            "task_change": "NEW_BENCHMARK_VERSION_AND_REVIEW_REQUIRED",
            "scorer_change": "NEW_SCORER_VERSION_AND_REVIEW_REQUIRED",
            "endpoint_change": "NEW_ENDPOINT_VERSION_AND_REVIEW_REQUIRED",
            "packet_regeneration": "PRIOR_REVIEW_INVALID",
            "run_hash_mismatch": "EXECUTION_REFUSED",
        },
    }
    manifest["freeze_manifest_sha256"] = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
    return manifest


def verify_scientific_freeze(repo_root: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    path = manifest_path or repo_root / "reports/final_hostile_pre_run/SCIENTIFIC_FREEZE_MANIFEST.json"
    manifest = json.loads(path.read_text())
    checks: dict[str, bool] = {}
    for key in (
        "packet_commitment",
        "scorer",
        "endpoints",
        "analysis_plan",
        "power_plan",
        "system_identity_schema",
        "review_protocol",
        "c10_contract",
    ):
        binding = manifest[key]
        checks[f"{key}_hash_matches"] = file_sha256(repo_root / binding["path"]) == binding["sha256"]
    generator = manifest["generator"]
    checks["generator_hash_matches"] = file_sha256(repo_root / generator["path"]) == generator["source_sha256"]
    without_hash = dict(manifest)
    declared = without_hash.pop("freeze_manifest_sha256")
    checks["manifest_self_hash_matches"] = hashlib.sha256(canonical_bytes(without_hash)).hexdigest() == declared
    commitment = json.loads((repo_root / manifest["packet_commitment"]["path"]).read_text())
    checks["stage1_hashes_match_commitment"] = manifest["stage1_package_hashes"] == commitment["stage1_package_hashes"]
    checks["stage2_hash_matches_commitment"] = manifest["stage2_encrypted_commitment"] == commitment["stage2_encrypted_sha256"]
    return {
        "schema_version": "cab_scientific_freeze_check_v1",
        "checks": checks,
        "passed": all(checks.values()),
        "status": "CAB_REPOSITORY_FROZEN_FOR_HUMAN_REVIEW" if all(checks.values()) else "SCIENTIFIC_FREEZE_MISMATCH",
    }


def exact_head_release_check(
    repo_root: Path,
    receipt_path: Path | None,
    *,
    allow_attestation_pending: bool = False,
) -> dict[str, Any]:
    head = current_head(repo_root)
    if receipt_path is None or not receipt_path.is_file():
        passed = allow_attestation_pending
        return {
            "head": head,
            "receipt": None,
            "attestation_pending": True,
            "passed": passed,
            "status": "EXTERNAL_FINAL_COMMIT_ATTESTATION_PENDING" if passed else "EXACT_HEAD_RECEIPT_REQUIRED",
        }
    receipt = json.loads(receipt_path.read_text())
    checks = {
        "external_attestation_model": receipt.get("attestation_model") == "EXTERNAL_FINAL_COMMIT",
        "source_commit_exact_head": receipt.get("source_commit") == head,
        "wheel_reproducible": receipt.get("wheel", {}).get("reproducible") is True,
        "sdist_reproducible": receipt.get("sdist", {}).get("reproducible") is True,
        "artifact_hashes_present": all(
            len(str(receipt.get(kind, {}).get("sha256", ""))) == 64 for kind in ("wheel", "sdist")
        ),
    }
    return {
        "head": head,
        "receipt": str(receipt_path),
        "checks": checks,
        "passed": all(checks.values()),
        "status": "CAB_EXACT_HEAD_RELEASE_ATTESTED" if all(checks.values()) else "STALE_OR_INVALID_RELEASE_ATTESTATION",
    }


def verify_run_gate(repo_root: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads(
        (repo_root / "reports/final_hostile_pre_run/SCIENTIFIC_FREEZE_MANIFEST.json").read_text()
    )
    required = {
        "c10_status": "C10_PASS",
        "slice_lock_receipt": receipt.get("slice_lock_receipt"),
        "approval_receipt": receipt.get("approval_receipt"),
        "approved_packet_hash": manifest["packet_commitment"]["commitment_sha256"],
        "scorer_hash": manifest["scorer"]["sha256"],
        "endpoint_hash": manifest["endpoints"]["sha256"],
        "analysis_plan_hash": manifest["analysis_plan"]["sha256"],
        "system_identity_hash": manifest["system_identity_schema"]["sha256"],
    }
    checks = {
        key: bool(expected) and receipt.get(key) == expected
        for key, expected in required.items()
    }
    checks["freeze_intact"] = verify_scientific_freeze(repo_root)["passed"]
    return {
        "schema_version": "cab_final_run_gate_v1",
        "checks": checks,
        "passed": all(checks.values()),
        "status": "CAB_AUTHORIZED_RUN_GATE_PASS" if all(checks.values()) else "CAB_RUN_BLOCKED",
    }


__all__ = [
    "build_freeze_manifest",
    "current_head",
    "exact_head_release_check",
    "file_sha256",
    "verify_run_gate",
    "verify_scientific_freeze",
]
