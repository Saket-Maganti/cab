"""Scientific freeze V2: hash-bind every surface the review depends on.

The freeze binds the generator source *and* its commit provenance, so a reviewer
can verify that the committed generator at the recorded commit is byte-identical
to the source that produced the private packet.  The external Stage-2 key value
is never bound, recorded, or hashed.

Provenance is recorded as *the last commit that touched the generator*, resolved
with ``git rev-list -1 <ref> -- <paths>``.  That commit is by construction
reachable from the branch being frozen, so the freeze verifies inside a
``--single-branch`` clone with no reflog and no dangling objects.  Recording the
current ``HEAD`` instead would be self-referential (the freeze cannot live inside
the commit it names), and recording a sibling or amended-away commit produces a
freeze that only verifies on the machine that built it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.adjudication_packages import (
    BINDING_FIELDS,
    BINDING_SCHEMA_VERSION,
    STAGE1_PACKAGE_SCHEMA_VERSION,
    STAGE2_PACKAGE_SCHEMA_VERSION,
)
from causal_agent_bench.review_ready_v2.commitment_integrity import (
    RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS,
    REVIEW_INPUT_GRAPH_SCHEMA_VERSION,
    STAGE1_COMMITMENT_SCHEMA_VERSION,
    STAGE1_SNAPSHOT_SCHEMA_VERSION,
    STAGE2_SNAPSHOT_SCHEMA_VERSION,
)
from causal_agent_bench.review_ready_v2.common import (
    canonical_bytes,
    read_json,
    sha256_bytes,
    sha256_file,
)
from causal_agent_bench.review_ready_v2.qualification import RETIRED_QUALIFICATION_VERSIONS
from causal_agent_bench.review_ready_v2.stage2_issuance import (
    REQUIRED_ISSUANCE_FIELDS,
    STAGE2_ISSUANCE_SCHEMA_VERSION,
)
from causal_agent_bench.review_ready_v2.workflow import RETIRED_WORKFLOW_SCHEMA_VERSIONS

FREEZE_SCHEMA = "cab_review_ready_v2_scientific_freeze_v1"

FROZEN_SOURCES = (
    "src/causal_agent_bench/review_ready_v2/models.py",
    "src/causal_agent_bench/review_ready_v2/catalog.py",
    "src/causal_agent_bench/review_ready_v2/pairs.py",
    "src/causal_agent_bench/review_ready_v2/operators.py",
    "src/causal_agent_bench/review_ready_v2/runtime.py",
    "src/causal_agent_bench/review_ready_v2/routes.py",
    "src/causal_agent_bench/review_ready_v2/evidence.py",
    "src/causal_agent_bench/review_ready_v2/design.py",
    "src/causal_agent_bench/review_ready_v2/stage1.py",
    "src/causal_agent_bench/review_ready_v2/stage2.py",
    "src/causal_agent_bench/review_ready_v2/stage2_issuance.py",
    "src/causal_agent_bench/review_ready_v2/qualification.py",
    "src/causal_agent_bench/review_ready_v2/leakage.py",
    "src/causal_agent_bench/review_ready_v2/vault.py",
    "src/causal_agent_bench/review_ready_v2/keys.py",
    "src/causal_agent_bench/review_ready_v2/receipts.py",
    "src/causal_agent_bench/review_ready_v2/roles.py",
    "src/causal_agent_bench/review_ready_v2/declarations.py",
    "src/causal_agent_bench/review_ready_v2/assignments.py",
    "src/causal_agent_bench/review_ready_v2/adjudication.py",
    "src/causal_agent_bench/review_ready_v2/adjudication_packages.py",
    "src/causal_agent_bench/review_ready_v2/commitment_integrity.py",
    "src/causal_agent_bench/review_ready_v2/final_records.py",
    "src/causal_agent_bench/review_ready_v2/packet.py",
    "src/causal_agent_bench/review_ready_v2/workflow.py",
    "src/causal_agent_bench/review_ready_v2/registry.py",
    "src/causal_agent_bench/review_ready_v2/power.py",
    # The manual offline-import path decides what evidence exists, whether C10
    # passes over it, and which slice may be executed.  A reviewer who verifies
    # the freeze should be verifying that code too, not only the production
    # path it sits beside.
    "src/causal_agent_bench/review_ready_v2/manual_import.py",
    "src/causal_agent_bench/review_ready_v2/manual_import_chain.py",
    "src/causal_agent_bench/review_ready_v2/manual_import_gates.py",
)

#: The sources that actually materialise the twenty pairs.  Provenance is
#: resolved against these, not against the whole package.
GENERATOR_SOURCES = (
    "src/causal_agent_bench/review_ready_v2/pairs.py",
    "src/causal_agent_bench/review_ready_v2/catalog.py",
)

FROZEN_CONFIGS = {
    "scorer": "configs/reviewer_ready_v2/scorer_v2.json",
    "endpoints": "configs/reviewer_ready_v2/frozen_endpoints_v2.json",
    "analysis_plan": "configs/reviewer_ready_v2/analysis_plan_v2.json",
    "power_plan": "configs/reviewer_ready_v2/power_plan_v2.json",
    "c10_contract": "configs/human_validation/c10_contract_v2.json",
    "stage2_acceptance_policy": "configs/reviewer_ready_v2/stage2_acceptance_policy_v1.json",
    "system_identity_schema": "configs/pre_run/evaluated_system_identity.schema.json",
    "packet_config": "configs/human_review/compact20_review_ready_v2.yaml",
}

FROZEN_REPORTS = {
    "public_packet_commitment": "reports/reviewer_ready_v2/PUBLIC_PACKET_COMMITMENT.json",
    "retired_packet_registry": "reports/reviewer_ready_v2/RETIRED_PACKET_REGISTRY.json",
    "retired_qualification_registry": (
        "reports/reviewer_ready_v2/RETIRED_QUALIFICATION_REGISTRY.json"
    ),
    "active_path_registry": "reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json",
    "reviewer_distribution_schemas": (
        "reports/reviewer_ready_v2/REVIEWER_DISTRIBUTION_SCHEMAS.json"
    ),
}

FROZEN_DOCS = {
    "review_runbook": "docs/HUMAN_REVIEW_READY_V2_RUNBOOK.md",
    "reviewer_instructions": "docs/STAGE1_REVIEWER_INSTRUCTIONS_V2.md",
    "coordinator_runbook": "docs/STAGE2_COORDINATOR_RUNBOOK_V2.md",
    "scientific_design": "docs/COMPACT20_V2_SCIENTIFIC_DESIGN.md",
    "security_policy": "docs/PRIVATE_PACKET_SECURITY_POLICY.md",
}

WORKFLOW_VERSION = "cab_review_ready_v2_two_stage_workflow_v3"


def current_head(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _committed_blob(repo_root: Path, commit: str, relative: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=repo_root, check=False, capture_output=True
    )
    return result.stdout if result.returncode == 0 else None


def _git(repo_root: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args], cwd=repo_root, check=False, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip()


def last_commit_touching(repo_root: Path, paths: tuple[str, ...], ref: str = "HEAD") -> str | None:
    """The most recent commit reachable from ``ref`` that changed ``paths``.

    This is the only provenance anchor that survives a branch-only clone: it is
    an ancestor of the branch by definition, so it needs no reflog, no sibling
    commit, and no unreachable object.
    """

    code, out = _git(repo_root, "rev-list", "-1", ref, "--", *paths)
    return out or None if code == 0 else None


def commit_is_ancestor(repo_root: Path, commit: str, ref: str = "HEAD") -> bool:
    code, _ = _git(repo_root, "merge-base", "--is-ancestor", commit, ref)
    return code == 0


def _blob_sha1(repo_root: Path, commit: str, relative: str) -> str | None:
    code, out = _git(repo_root, "rev-parse", f"{commit}:{relative}")
    return out if code == 0 and out else None


def _blob_exists(repo_root: Path, blob: str) -> bool:
    code, _ = _git(repo_root, "cat-file", "-e", f"{blob}^{{blob}}")
    return code == 0


def generator_provenance(repo_root: Path, *, generator_commit: str | None = None) -> dict[str, Any]:
    """Bind the generator to a commit that is reachable from the branch."""

    commit = generator_commit or last_commit_touching(repo_root, GENERATOR_SOURCES)
    sources: list[dict[str, Any]] = []
    content_matches = True
    blobs_present = True
    for relative in GENERATOR_SOURCES:
        working = sha256_file(repo_root / relative)
        blob = _committed_blob(repo_root, commit, relative) if commit else None
        blob_sha1 = _blob_sha1(repo_root, commit, relative) if commit else None
        matches = blob is not None and sha256_bytes(blob) == working
        content_matches = content_matches and matches
        blobs_present = blobs_present and bool(blob_sha1)
        sources.append(
            {
                "path": relative,
                "source_sha256": working,
                "git_blob_sha1": blob_sha1,
                "commit_content_matches": matches,
            }
        )
    return {
        "resolution": "git rev-list -1 <branch> -- " + " ".join(GENERATOR_SOURCES),
        "source_commit": commit,
        "commit_resolves": bool(commit)
        and _git(repo_root, "cat-file", "-t", str(commit))[1] == "commit",
        "commit_is_ancestor_of_head": bool(commit) and commit_is_ancestor(repo_root, str(commit)),
        "commit_content_matches": content_matches,
        "generator_blobs_present": blobs_present,
        "sources": sources,
        "requires_unreachable_objects": False,
        "verifiable_from_single_branch_clone": True,
    }


def build_freeze(repo_root: Path, *, generator_commit: str | None = None) -> dict[str, Any]:
    commitment_path = repo_root / FROZEN_REPORTS["public_packet_commitment"]
    commitment = read_json(commitment_path)
    manifest: dict[str, Any] = {
        "schema_version": FREEZE_SCHEMA,
        "status": "CAB_SCIENTIFIC_FREEZE_V2_VALID",
        "benchmark_version": PACKET_VERSION,
        "two_stage_workflow_version": WORKFLOW_VERSION,
        "packet_commitment_sha256": commitment["commitment_sha256"],
        "stage1_package_hashes": commitment["stage1_package_hashes"],
        "qualification_version": commitment["qualification_version"],
        "qualification_package_hashes": commitment["qualification_package_hashes"],
        "qualification_commitment_sha256": commitment["qualification_commitment"][
            "commitment_sha256"
        ],
        "qualification_source_schema_version": commitment["qualification_source_schema_version"],
        "qualification_key_environment_variable": commitment[
            "qualification_key_environment_variable"
        ],
        "qualification_key_value_bound": False,
        "qualification_source_value_bound": False,
        "retired_qualification_versions": sorted(RETIRED_QUALIFICATION_VERSIONS),
        "stage2_encrypted_vault_sha256": commitment["stage2_vault_sha256"],
        "stage2_key_environment_variable": commitment["stage2_key_environment_variable"],
        "stage2_key_value_bound": False,
        # The reviewer-distribution contracts: what a Stage-2 issuance receipt and
        # an adjudicator package must be, frozen alongside the science they gate.
        "stage2_issuance_schema_version": STAGE2_ISSUANCE_SCHEMA_VERSION,
        "stage2_issuance_required_fields": list(REQUIRED_ISSUANCE_FIELDS),
        "stage1_adjudicator_package_schema_version": STAGE1_PACKAGE_SCHEMA_VERSION,
        "stage2_adjudicator_package_schema_version": STAGE2_PACKAGE_SCHEMA_VERSION,
        "adjudicator_package_binding_schema_version": BINDING_SCHEMA_VERSION,
        "adjudicator_package_binding_fields": list(BINDING_FIELDS),
        # The immutable-evidence contract: which commitment and snapshot schemas
        # the active gates accept, and which they refuse outright.
        "stage1_commitment_schema_version": STAGE1_COMMITMENT_SCHEMA_VERSION,
        "committed_stage1_snapshot_schema_version": STAGE1_SNAPSHOT_SCHEMA_VERSION,
        "committed_stage2_snapshot_schema_version": STAGE2_SNAPSHOT_SCHEMA_VERSION,
        "review_input_graph_schema_version": REVIEW_INPUT_GRAPH_SCHEMA_VERSION,
        "retired_stage1_commitment_schema_versions": [
            version
            for version in RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS
            if version is not None
        ],
        "retired_two_stage_workflow_versions": list(RETIRED_WORKFLOW_SCHEMA_VERSIONS),
        "frozen_sources": {
            path: sha256_file(repo_root / path) for path in FROZEN_SOURCES
        },
        "frozen_configs": {
            name: {"path": path, "sha256": sha256_file(repo_root / path)}
            for name, path in FROZEN_CONFIGS.items()
        },
        "frozen_reports": {
            name: {"path": path, "sha256": sha256_file(repo_root / path)}
            for name, path in FROZEN_REPORTS.items()
        },
        "frozen_docs": {
            name: {"path": path, "sha256": sha256_file(repo_root / path)}
            for name, path in FROZEN_DOCS.items()
        },
        "invalidation_rules": {
            "pair_change": "NEW_BENCHMARK_VERSION_AND_FRESH_REVIEW_REQUIRED",
            "operator_change": "NEW_BENCHMARK_VERSION_AND_FRESH_REVIEW_REQUIRED",
            "scorer_change": "NEW_SCORER_VERSION_AND_FRESH_REVIEW_REQUIRED",
            "endpoint_change": "NEW_ENDPOINT_VERSION_AND_FRESH_REVIEW_REQUIRED",
            "packet_regeneration": "PRIOR_REVIEW_INVALID",
            "run_hash_mismatch": "EXECUTION_REFUSED",
        },
    }
    provenance = generator_provenance(repo_root, generator_commit=generator_commit)
    if not provenance["commit_is_ancestor_of_head"]:
        raise ValueError(
            "refusing to write a freeze whose generator commit "
            f"{provenance['source_commit']!r} is not an ancestor of HEAD; such a freeze verifies "
            "only in the object database that built it, never in a fresh clone"
        )
    if not provenance["commit_content_matches"]:
        raise ValueError(
            "refusing to write a freeze whose recorded generator commit does not carry the "
            "generator source currently on disk; commit the generator first"
        )
    manifest["generator"] = provenance
    manifest["freeze_sha256"] = sha256_bytes(canonical_bytes(manifest))
    return manifest


def verify_freeze(repo_root: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    path = manifest_path or repo_root / "reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json"
    if not path.is_file():
        return {"status": "SCIENTIFIC_FREEZE_V2_MISSING", "checks": {}, "passed": False}
    manifest = read_json(path)
    checks: dict[str, bool] = {}
    mismatched: list[str] = []
    for relative, digest in manifest["frozen_sources"].items():
        target = repo_root / relative
        if not target.is_file() or sha256_file(target) != digest:
            mismatched.append(relative)
    checks["frozen_sources_match"] = not mismatched
    for group in ("frozen_configs", "frozen_reports", "frozen_docs"):
        group_ok = True
        for binding in manifest[group].values():
            target = repo_root / binding["path"]
            if not target.is_file() or sha256_file(target) != binding["sha256"]:
                group_ok = False
                mismatched.append(str(binding["path"]))
        checks[f"{group}_match"] = group_ok

    generator = manifest["generator"]
    commit = str(generator["source_commit"])
    working_matches = True
    committed_matches = True
    blobs_present = True
    for source in generator["sources"]:
        target = repo_root / source["path"]
        working_matches = working_matches and target.is_file() and sha256_file(target) == source[
            "source_sha256"
        ]
        blob = _committed_blob(repo_root, commit, source["path"])
        committed_matches = committed_matches and bool(
            blob is not None and sha256_bytes(blob) == source["source_sha256"]
        )
        blobs_present = blobs_present and bool(
            source.get("git_blob_sha1") and _blob_exists(repo_root, str(source["git_blob_sha1"]))
        )
    checks["generator_source_matches"] = working_matches
    checks["generator_commit_resolves"] = (
        _git(repo_root, "cat-file", "-t", commit)[1] == "commit"
    )
    # The check that makes the freeze portable: the recorded commit must be
    # reachable from HEAD, not merely present in this machine's object store.
    checks["generator_commit_is_ancestor_of_head"] = commit_is_ancestor(repo_root, commit)
    checks["generator_commit_content_matches"] = committed_matches
    checks["generator_blobs_resolve"] = blobs_present
    checks["provenance_needs_no_unreachable_objects"] = (
        generator.get("requires_unreachable_objects") is False
    )

    without_hash = dict(manifest)
    declared = without_hash.pop("freeze_sha256")
    checks["manifest_self_hash_matches"] = sha256_bytes(canonical_bytes(without_hash)) == declared

    commitment = read_json(repo_root / manifest["frozen_reports"]["public_packet_commitment"]["path"])
    checks["stage1_hashes_match_commitment"] = (
        manifest["stage1_package_hashes"] == commitment["stage1_package_hashes"]
    )
    checks["stage2_hash_matches_commitment"] = (
        manifest["stage2_encrypted_vault_sha256"] == commitment["stage2_vault_sha256"]
    )
    checks["stage2_key_value_not_bound"] = manifest["stage2_key_value_bound"] is False
    checks["qualification_hashes_match_commitment"] = (
        manifest["qualification_package_hashes"] == commitment["qualification_package_hashes"]
    )
    checks["qualification_key_value_not_bound"] = (
        manifest["qualification_key_value_bound"] is False
    )
    checks["qualification_source_value_not_bound"] = (
        manifest.get("qualification_source_value_bound") is False
    )
    checks["qualification_version_is_active_and_not_retired"] = (
        manifest["qualification_version"] not in RETIRED_QUALIFICATION_VERSIONS
        and manifest["qualification_version"] == commitment["qualification_version"]
    )
    checks["retired_qualification_versions_recorded"] = sorted(
        manifest.get("retired_qualification_versions", [])
    ) == sorted(RETIRED_QUALIFICATION_VERSIONS)
    checks["stage2_issuance_schema_matches_code"] = (
        manifest.get("stage2_issuance_schema_version") == STAGE2_ISSUANCE_SCHEMA_VERSION
        and list(manifest.get("stage2_issuance_required_fields", []))
        == list(REQUIRED_ISSUANCE_FIELDS)
    )
    checks["adjudicator_package_schemas_match_code"] = (
        manifest.get("stage1_adjudicator_package_schema_version") == STAGE1_PACKAGE_SCHEMA_VERSION
        and manifest.get("stage2_adjudicator_package_schema_version")
        == STAGE2_PACKAGE_SCHEMA_VERSION
        and manifest.get("adjudicator_package_binding_schema_version") == BINDING_SCHEMA_VERSION
        and list(manifest.get("adjudicator_package_binding_fields", [])) == list(BINDING_FIELDS)
    )
    return {
        "schema_version": "cab_review_ready_v2_freeze_check_v1",
        "status": "CAB_SCIENTIFIC_FREEZE_V2_VALID"
        if all(checks.values())
        else "SCIENTIFIC_FREEZE_V2_MISMATCH",
        "mismatched_paths": sorted(set(mismatched)),
        "freeze_sha256": manifest["freeze_sha256"],
        "checks": checks,
        "passed": all(checks.values()),
    }


def attestation_policy() -> dict[str, Any]:
    """The tracked pointer to the external exact-commit attestation."""

    return {
        "schema_version": "cab_review_ready_v2_attestation_policy_v1",
        "attestation_model": "EXTERNAL_EXACT_COMMIT",
        "why_external": (
            "An exact-commit attestation cannot be committed inside the commit it attests, so it "
            "is written outside the repository after the final tracked commit."
        ),
        "location_template": "~/.cab/attestations/cab-review-ready-v2-<commit>.json",
        "environment_override": "CAB_ATTESTATION_DIR",
        "required_fields": [
            "exact_commit",
            "branch",
            "scientific_freeze_hash",
            "public_packet_commitment",
            "stage1_reviewer_a_hash",
            "stage1_reviewer_b_hash",
            "encrypted_stage2_vault_hash",
            "wheel_hash",
            "normalized_sdist_hash",
            "test_summary",
            "build_environment",
            "timestamp",
        ],
        "permissions": "0700 directories, 0600 files",
        "required_before": "any distribution of this repository as a release artifact",
    }


def verify_attestation(repo_root: Path, attestation_path: Path | None) -> dict[str, Any]:
    head = current_head(repo_root)
    if attestation_path is None or not attestation_path.is_file():
        return {
            "head": head,
            "attestation_present": False,
            "status": "EXTERNAL_EXACT_COMMIT_ATTESTATION_PENDING",
            "passed": False,
        }
    attestation = read_json(attestation_path)
    checks = {
        "attestation_model_external": attestation.get("attestation_model") == "EXTERNAL_EXACT_COMMIT",
        "commit_is_exact_head": attestation.get("exact_commit") == head,
        "freeze_hash_present": len(str(attestation.get("scientific_freeze_hash", ""))) == 64,
        "wheel_hash_present": len(str(attestation.get("wheel_hash", ""))) == 64,
        "sdist_hash_present": len(str(attestation.get("normalized_sdist_hash", ""))) == 64,
        "builds_reproducible": attestation.get("builds_reproducible") is True,
    }
    return {
        "head": head,
        "attestation_present": True,
        "status": "CAB_EXACT_COMMIT_ATTESTATION_CREATED"
        if all(checks.values())
        else "STALE_OR_INVALID_ATTESTATION",
        "checks": checks,
        "passed": all(checks.values()),
    }


__all__ = [
    "FREEZE_SCHEMA",
    "FROZEN_CONFIGS",
    "FROZEN_DOCS",
    "FROZEN_REPORTS",
    "FROZEN_SOURCES",
    "GENERATOR_SOURCES",
    "WORKFLOW_VERSION",
    "attestation_policy",
    "build_freeze",
    "commit_is_ancestor",
    "current_head",
    "generator_provenance",
    "last_commit_touching",
    "verify_attestation",
    "verify_freeze",
]
