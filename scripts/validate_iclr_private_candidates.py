#!/usr/bin/env python3
"""Leak-safe validation for the ignored Scale-100 and naturalistic v2 packs.

The validator reads private payloads but emits aggregate counts and issue codes
only. It never serializes task identifiers, instructions, answers, artifact
facts, intervention payloads, or evaluator-only fields.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.analysis.assignment_balance import (
    ASSIGNMENT_DESIGN_VERSION,
    assignment_balance_diagnostics,
)
from causal_agent_bench.generation.transfer_artifacts import (
    STUDY_NAME as TRANSFER_STUDY_NAME,
)
from causal_agent_bench.generation.transfer_artifacts import (
    parse_transfer_bundle,
)
from causal_agent_bench.safety.iclr_dataset_audit import (
    CANONICAL_ANSWER_CONTRACTS,
    diversity_audit,
    naturalistic_safety_audit,
    public_manifest_payload_issues,
    read_jsonl_objects,
)
from scripts.materialize_iclr_private_candidates import REVIEW_DIMENSIONS


@dataclass(frozen=True)
class CandidateSpec:
    key: str
    dataset_id: str
    expected_count: int
    minimum_domain_count: int
    private_relative: str
    public_manifest_relative: str


CANDIDATES = (
    CandidateSpec(
        key="scale100",
        dataset_id="scale100_confirmatory_v2",
        expected_count=100,
        minimum_domain_count=8,
        private_relative="private_data/scale100_confirmatory_v2",
        public_manifest_relative=(
            "data/manifests/scale100_confirmatory_v2_public_manifest.json"
        ),
    ),
    CandidateSpec(
        key="naturalistic",
        dataset_id="naturalistic_transfer_v2",
        expected_count=60,
        minimum_domain_count=8,
        private_relative="private_data/naturalistic_transfer_v2",
        public_manifest_relative=(
            "data/manifests/naturalistic_transfer_v2_public_manifest.json"
        ),
    ),
)

PRIVATE_FILE_ROLES = (
    "candidate_tasks.jsonl",
    "human_review_items.jsonl",
    "human_review_judgments.csv",
    "assignment_balance.json",
    "artifact_inventory.json",
    "private_manifest.json",
)


def audit_public_commitments(repo_root: Path) -> dict[str, Any]:
    """Validate CI-safe v2 commitments without requiring ignored private bodies."""

    issues: list[str] = []
    datasets: dict[str, Any] = {}
    for spec in CANDIDATES:
        path = repo_root / spec.public_manifest_relative
        manifest = _read_json_object(
            path,
            issues,
            f"{spec.key}:public_manifest_missing",
        )
        payload_issues = public_manifest_payload_issues(manifest)
        issues.extend(f"{spec.key}:{issue}" for issue in payload_issues)
        counts = manifest.get("aggregate_counts", {})
        assignment = manifest.get("assignment_design", {})
        checks = assignment.get("checks", {}) if isinstance(assignment, dict) else {}
        threshold = float(assignment.get("association_threshold", 0.0) or 0.0)
        family_difficulty = (
            assignment.get("family_by_difficulty", {})
            if isinstance(assignment, dict)
            else {}
        )
        family_domain = (
            assignment.get("family_by_domain", {})
            if isinstance(assignment, dict)
            else {}
        )
        conditions = {
            "expected_task_count": counts.get("base_task_count") == spec.expected_count,
            "assignment_passed": assignment.get("passed") is True,
            "assignment_checks_passed": bool(checks) and all(checks.values()),
            "family_difficulty_below_threshold": (
                float(family_difficulty.get("cramers_v", 1.0)) <= threshold
            ),
            "family_domain_below_threshold": (
                float(family_domain.get("cramers_v", 1.0)) <= threshold
            ),
            "deterministic_receipt_present": bool(
                assignment.get("deterministic_receipt")
            ),
            "scientific_execution_blocked": (
                manifest.get("scientific_execution_allowed") is False
                and manifest.get("confirmatory_eligible") is False
                and manifest.get("paper_eligible") is False
            ),
        }
        if spec.key == "naturalistic":
            artifacts = manifest.get("artifact_materialization", {})
            conditions.update(
                {
                    "artifact_scope_named": (
                        manifest.get("canonical_study_name")
                        == "artifact_rich_synthetic_transfer"
                        and artifacts.get("artifact_class")
                        == "artifact_rich_synthetic"
                    ),
                    "artifact_commitments_present": (
                        artifacts.get("bundle_count") == spec.expected_count
                        and int(artifacts.get("artifact_file_count", 0)) > 0
                        and bool(artifacts.get("bundle_root_commitment_sha256"))
                    ),
                    "real_world_origin_not_claimed": (
                        artifacts.get("real_world_origin_claimed") is False
                    ),
                }
            )
        for name, passed in conditions.items():
            if not passed:
                issues.append(f"{spec.key}:public_commitment:{name}")
        datasets[spec.key] = {
            "task_count": int(counts.get("base_task_count", 0) or 0),
            "assignment_design": assignment,
            "checks": conditions,
            "passed": all(conditions.values()) and not payload_issues,
        }
    return {
        "schema_version": "cab_iclr_public_commitment_validation_v1",
        "status": (
            "PUBLIC_V2_COMMITMENTS_PASS_HUMAN_REVIEW_REQUIRED"
            if not issues
            else "PUBLIC_V2_COMMITMENTS_FAILED"
        ),
        "static_passed": not issues,
        "datasets": datasets,
        "issue_codes": sorted(set(issues)),
        "human_validation_complete": False,
        "scientific_execution_performed": False,
    }


def audit_repository(repo_root: Path) -> dict[str, Any]:
    """Return a public-safe aggregate audit for both protected candidates."""

    repo_root = repo_root.resolve()
    comparison_roles = _load_comparison_roles(repo_root)
    private_rows_by_key: dict[str, list[dict[str, Any]]] = {}
    dataset_reports: dict[str, dict[str, Any]] = {}
    all_issues: list[str] = []

    for spec in CANDIDATES:
        private_root = repo_root / spec.private_relative
        candidate_path = private_root / "candidate_tasks.jsonl"
        public_path = repo_root / spec.public_manifest_relative
        issues: list[str] = []
        if not candidate_path.is_file():
            issues.append("private_candidate_file_missing")
            rows: list[dict[str, Any]] = []
        else:
            rows = read_jsonl_objects(candidate_path)
        private_rows_by_key[spec.key] = rows
        manifest = _read_json_object(public_path, issues, "public_manifest_missing")
        private_manifest = _read_json_object(
            private_root / "private_manifest.json",
            issues,
            "private_manifest_missing",
        )
        diversity = diversity_audit(
            rows,
            comparison_roles=comparison_roles,
        )
        safety = naturalistic_safety_audit(rows)
        review = _review_packet_audit(private_root, rows)
        issues.extend(review.pop("issues"))
        assignment = _assignment_audit(rows, manifest)
        issues.extend(assignment.pop("issues"))
        artifacts = _artifact_audit(spec, private_root, rows, manifest)
        issues.extend(artifacts.pop("issues"))
        issues.extend(public_manifest_payload_issues(manifest, private_rows=rows))
        issues.extend(
            _candidate_contract_issues(
                spec,
                rows=rows,
                diversity=diversity,
                safety=safety,
                manifest=manifest,
            )
        )
        issues.extend(
            _commitment_issues(
                private_root,
                manifest=manifest,
                private_manifest=private_manifest,
            )
        )
        dataset_reports[spec.key] = {
            "dataset_id": spec.dataset_id,
            "task_count": len(rows),
            "diversity": _public_diversity_summary(diversity),
            "safety": {
                "static_passed": safety["static_passed"],
                "blocker_counts": safety["blocker_counts"],
                "provenance_source_class_count": len(
                    safety["provenance_counts"]
                ),
                "licence_class_count": len(safety["licence_counts"]),
                "artifact_type_count": safety["artifact_type_count"],
            },
            "review": review,
            "assignment_design": assignment,
            "artifacts": artifacts,
            "manifest": {
                "schema_version": manifest.get("schema_version"),
                "candidate_materialized": manifest.get("candidate_materialized"),
                "review_packet_materialized": manifest.get(
                    "review_packet_materialized"
                ),
                "human_validation_state": manifest.get("human_validation_state"),
                "confirmatory_eligible": manifest.get("confirmatory_eligible"),
                "paper_eligible": manifest.get("paper_eligible"),
                "scientific_execution_allowed": manifest.get(
                    "scientific_execution_allowed"
                ),
                "payload_denials_passed": not public_manifest_payload_issues(
                    manifest,
                    private_rows=rows,
                ),
            },
            "issue_codes": sorted(set(issues)),
            "static_passed": not issues,
        }
        all_issues.extend(f"{spec.key}:{issue}" for issue in issues)

    cross = _cross_candidate_audit(
        private_rows_by_key.get("scale100", []),
        private_rows_by_key.get("naturalistic", []),
    )
    if any(cross.values()):
        all_issues.append("cross_candidate:overlap_signal")

    repository_safety = _repository_safety_audit(
        repo_root,
        private_rows_by_key,
    )
    all_issues.extend(repository_safety.pop("issues"))
    contamination = _contamination_policy_audit(repo_root)
    all_issues.extend(contamination.pop("issues"))

    human_blockers = [
        "two independent qualified human reviews per task remain incomplete",
        "disagreements have not been adjudicated",
        "answer-contract/scorer compatibility needs task-level human confirmation",
        "privacy, PII, prompt-injection, realism, and manipulation checks need human confirmation",
        "the candidate split is not frozen or confirmatory-ready",
    ]
    return {
        "schema_version": "cab_iclr_private_candidate_validation_v1",
        "status": (
            "STATIC_PREVALIDATION_PASS_HUMAN_REVIEW_REQUIRED"
            if not all_issues
            else "STATIC_PREVALIDATION_FAILED"
        ),
        "static_passed": not all_issues,
        "datasets": dataset_reports,
        "cross_candidate_overlap": cross,
        "repository_safety": repository_safety,
        "public_v1_contamination_policy": contamination,
        "issue_codes": sorted(set(all_issues)),
        "human_blockers": human_blockers,
        "human_validation_complete": False,
        "confirmatory_ready": False,
        "paper_eligible": False,
        "scientific_execution_performed": False,
        "evidence_class": "HUMAN_INPUT_REQUIRED",
    }


def _candidate_contract_issues(
    spec: CandidateSpec,
    *,
    rows: list[dict[str, Any]],
    diversity: dict[str, Any],
    safety: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    if len(rows) != spec.expected_count:
        issues.append("unexpected_task_count")
    if diversity["unique_task_id_count"] != spec.expected_count:
        issues.append("task_ids_not_unique")
    if diversity["unique_content_hash_count"] != spec.expected_count:
        issues.append("content_hashes_missing_or_not_unique")
    if diversity["normalized_instruction_pattern_count"] != spec.expected_count:
        issues.append("normalized_instruction_reuse")
    if diversity["exact_duplicate_group_count"]:
        issues.append("exact_duplicate_groups_present")
    if diversity["normalized_duplicate_group_count"]:
        issues.append("normalized_duplicate_groups_present")
    if diversity["lexical_near_duplicate_pair_count"]:
        issues.append("lexical_near_duplicates_present")
    if diversity["answer_overlap_group_count"]:
        issues.append("answer_overlap_groups_present")
    if diversity["role_overlap_signal_count"]:
        issues.append("public_role_overlap_present")
    if len(diversity["domain_counts"]) < spec.minimum_domain_count:
        issues.append("insufficient_domain_coverage")
    if diversity["tool_combination_count"] < 2:
        issues.append("insufficient_tool_combination_coverage")
    if diversity["canonical_answer_contract_count"] < 2:
        issues.append("insufficient_answer_contract_coverage")
    if diversity["noncanonical_answer_contract_task_count"]:
        issues.append("noncanonical_answer_contract_present")
    if set(diversity["answer_contract_counts"]) - CANONICAL_ANSWER_CONTRACTS:
        issues.append("unknown_answer_contract_present")
    if set(diversity["intervention_family_counts"]) != {
        "tool_removal",
        "tool_failure",
        "tool_corruption",
        "irrelevant_tools",
        "memory_corruption",
        "observation_conflict",
        "ambiguous_instruction",
        "long_horizon_dependency",
        "premature_success_signal",
        "distractor_evidence",
    }:
        issues.append("intervention_family_coverage_incomplete")
    if diversity["missing_manipulation_check_count"]:
        issues.append("manipulation_check_missing")
    if not safety["static_passed"]:
        issues.append("privacy_injection_static_scan_failed")
    if manifest.get("dataset_id") != spec.dataset_id:
        issues.append("public_manifest_dataset_mismatch")
    if manifest.get("schema_version") != "cab_public_safe_candidate_manifest_v1":
        issues.append("public_manifest_schema_mismatch")
    if manifest.get("candidate_materialized") is not True:
        issues.append("candidate_not_materialized")
    if manifest.get("review_packet_materialized") is not True:
        issues.append("review_packet_not_materialized")
    if manifest.get("private_payload_root") != spec.private_relative:
        issues.append("private_payload_root_mismatch")
    expected_interventions = sum(
        len(row.get("intervention_mapping", [])) for row in rows
    )
    if manifest.get("aggregate_counts") != {
        "base_task_count": len(rows),
        "intervention_count": expected_interventions,
        "instance_count": len(rows) + expected_interventions,
    }:
        issues.append("aggregate_counts_mismatch")
    public_diversity = manifest.get("aggregate_diversity")
    if not isinstance(public_diversity, dict):
        issues.append("public_diversity_missing")
    else:
        for key in (
            "raw_task_count",
            "unique_task_id_count",
            "normalized_instruction_pattern_count",
            "canonical_answer_contract_count",
            "noncanonical_answer_contract_task_count",
            "role_overlap_signal_count",
        ):
            if public_diversity.get(key) != diversity.get(key):
                issues.append(f"public_diversity_mismatch:{key}")
    public_safety = manifest.get("aggregate_safety")
    if not isinstance(public_safety, dict) or public_safety.get(
        "blocker_counts"
    ) != safety["blocker_counts"]:
        issues.append("public_safety_mismatch")
    return issues


def _assignment_audit(
    rows: list[dict[str, Any]],
    public_manifest: dict[str, Any],
) -> dict[str, Any]:
    issues: list[str] = []
    families = [
        "tool_removal",
        "tool_failure",
        "tool_corruption",
        "irrelevant_tools",
        "memory_corruption",
        "observation_conflict",
        "ambiguous_instruction",
        "long_horizon_dependency",
        "premature_success_signal",
        "distractor_evidence",
    ]
    assignments = [
        [
            str(mapping.get("family"))
            for mapping in row.get("intervention_mapping", [])
            if isinstance(mapping, dict)
        ]
        for row in rows
    ]
    tasks = [
        {
            "domain": row.get("domain"),
            "difficulty": row.get("difficulty"),
        }
        for row in rows
    ]
    try:
        diagnostics = assignment_balance_diagnostics(
            tasks,
            assignments,
            families=families,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "design_version": None,
            "passed": False,
            "issues": [f"assignment_diagnostics_failed:{type(exc).__name__}"],
        }
    if not diagnostics["passed"]:
        issues.extend(
            f"assignment_check_failed:{key}"
            for key, value in diagnostics["checks"].items()
            if not value
        )
    for row, assignment in zip(rows, assignments, strict=True):
        mappings = row.get("intervention_mapping", [])
        if len(assignment) != 5:
            issues.append("assignment_block_size_mismatch")
        for position, mapping in enumerate(mappings):
            metadata = mapping.get("assignment") if isinstance(mapping, dict) else None
            if not isinstance(metadata, dict):
                issues.append("assignment_metadata_missing")
                continue
            if metadata.get("design_version") != ASSIGNMENT_DESIGN_VERSION:
                issues.append("assignment_design_version_mismatch")
            if metadata.get("within_block_position") != position:
                issues.append("assignment_position_mismatch")
            if metadata.get("repeated_intervention_explicit") is not True:
                issues.append("assignment_repetition_not_explicit")
    if public_manifest.get("assignment_design") != diagnostics:
        issues.append("public_assignment_diagnostics_mismatch")
    return {
        "design_version": diagnostics["design_version"],
        "association_threshold": diagnostics["association_threshold"],
        "family_difficulty_cramers_v": diagnostics["family_by_difficulty"][
            "cramers_v"
        ],
        "family_domain_cramers_v": diagnostics["family_by_domain"][
            "cramers_v"
        ],
        "mutual_information_family_difficulty": diagnostics[
            "family_by_difficulty"
        ]["mutual_information_nats"],
        "deterministic_receipt": diagnostics["deterministic_receipt"],
        "checks": diagnostics["checks"],
        "passed": diagnostics["passed"] and not issues,
        "issues": sorted(set(issues)),
    }


def _artifact_audit(
    spec: CandidateSpec,
    private_root: Path,
    rows: list[dict[str, Any]],
    public_manifest: dict[str, Any],
) -> dict[str, Any]:
    issues: list[str] = []
    inventory_path = private_root / "artifact_inventory.json"
    inventory = _read_json_object(
        inventory_path,
        issues,
        "artifact_inventory_missing",
    )
    public_inventory = public_manifest.get("artifact_materialization")
    if spec.key != "naturalistic":
        if inventory.get("bundle_count") != 0:
            issues.append("scale_artifact_inventory_must_be_not_applicable")
        return {
            "applicable": False,
            "bundle_count": int(inventory.get("bundle_count") or 0),
            "passed": not issues,
            "issues": sorted(set(issues)),
        }

    bundles = inventory.get("bundles")
    if not isinstance(bundles, list) or len(bundles) != len(rows):
        issues.append("artifact_bundle_inventory_count_mismatch")
        bundles = []
    by_task = {
        str(bundle.get("task_id")): bundle
        for bundle in bundles
        if isinstance(bundle, dict)
    }
    format_counts: Counter[str] = Counter()
    artifact_file_count = 0
    for row in rows:
        task_id = str(row.get("task_id") or "")
        bundle = by_task.get(task_id)
        if bundle is None:
            issues.append("artifact_bundle_missing_for_task")
            continue
        bundle_root = private_root / str(bundle.get("bundle_path") or "")
        manifest_path = bundle_root / "artifact_manifest.json"
        manifest = _read_json_object(
            manifest_path,
            issues,
            "artifact_manifest_missing",
        )
        if bundle.get("manifest_sha256") != (
            _sha256_file(manifest_path) if manifest_path.is_file() else None
        ):
            issues.append("artifact_manifest_hash_mismatch")
        if manifest.get("bundle_root_sha256") != bundle.get(
            "bundle_root_sha256"
        ):
            issues.append("artifact_bundle_root_mismatch")
        if manifest.get("study_name") != TRANSFER_STUDY_NAME:
            issues.append("artifact_study_name_mismatch")
        if manifest.get("provenance", {}).get("real_world_origin_claimed") is not False:
            issues.append("artifact_real_world_origin_claimed")
        try:
            derived = parse_transfer_bundle(bundle_root)
        except (OSError, ValueError):
            issues.append("artifact_parser_failed")
        else:
            if derived != row.get("hidden_answer_key"):
                issues.append("artifact_gold_derivation_mismatch")
        clean_files = manifest.get("clean_files")
        intervention_files = manifest.get("intervention_files")
        for file_row in [
            *(clean_files if isinstance(clean_files, list) else []),
            *(intervention_files if isinstance(intervention_files, list) else []),
        ]:
            if not isinstance(file_row, dict):
                issues.append("artifact_file_record_invalid")
                continue
            path = bundle_root / str(file_row.get("path") or "")
            artifact_file_count += 1
            format_counts[str(file_row.get("format") or "unknown")] += 1
            if not path.is_file() or file_row.get("sha256") != (
                _sha256_file(path) if path.is_file() else None
            ):
                issues.append("artifact_file_hash_mismatch")
        mapping_families = {
            str(mapping.get("family"))
            for mapping in row.get("intervention_mapping", [])
            if isinstance(mapping, dict)
        }
        patch_families = {
            path.parent.name
            for path in (bundle_root / "interventions").glob("*/patch.json")
        }
        if mapping_families != patch_families:
            issues.append("artifact_intervention_patch_coverage_mismatch")
        artifact_spec = row.get("artifact_spec")
        if not isinstance(artifact_spec, dict) or not artifact_spec.get("files"):
            issues.append("task_artifact_file_routes_missing")

    public_aggregate = {
        key: value
        for key, value in inventory.items()
        if key not in {"applicable", "bundles"}
    }
    if public_inventory != public_aggregate:
        issues.append("public_artifact_inventory_mismatch")
    if public_manifest.get("canonical_study_name") != TRANSFER_STUDY_NAME:
        issues.append("canonical_transfer_study_name_mismatch")
    if inventory.get("all_gold_derivations_match") is not True:
        issues.append("artifact_inventory_gold_derivation_failed")
    return {
        "applicable": True,
        "study_name": TRANSFER_STUDY_NAME,
        "bundle_count": len(bundles),
        "artifact_file_count": artifact_file_count,
        "format_counts": dict(sorted(format_counts.items())),
        "all_gold_derivations_match": not any(
            issue in {"artifact_parser_failed", "artifact_gold_derivation_mismatch"}
            for issue in issues
        ),
        "real_world_origin_claimed": False,
        "human_review_state": "HUMAN_INPUT_REQUIRED_AFTER_MATERIALIZATION",
        "passed": not issues,
        "issues": sorted(set(issues)),
    }


def _review_packet_audit(
    private_root: Path,
    tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    issues: list[str] = []
    review_path = private_root / "human_review_items.jsonl"
    csv_path = private_root / "human_review_judgments.csv"
    review_rows = read_jsonl_objects(review_path) if review_path.is_file() else []
    if not review_path.is_file():
        issues.append("review_items_missing")
    task_ids = {str(row.get("task_id")) for row in tasks}
    task_hashes = {
        str(row.get("task_id")): str(row.get("metadata", {}).get("content_hash"))
        for row in tasks
    }
    review_ids = {str(row.get("task_id")) for row in review_rows}
    if len(review_rows) != len(tasks) or review_ids != task_ids:
        issues.append("review_item_membership_mismatch")
    for row in review_rows:
        task_id = str(row.get("task_id"))
        if row.get("task_content_hash") != task_hashes.get(task_id):
            issues.append("review_item_hash_mismatch")
        if row.get("required_independent_reviewers") != 2:
            issues.append("reviewer_count_commitment_mismatch")
        if row.get("dimensions") != list(REVIEW_DIMENSIONS):
            issues.append("review_dimensions_mismatch")
        for field in (
            "model_output_blinded",
            "model_identity_blinded",
            "adjudication_required_on_disagreement",
        ):
            if row.get(field) is not True:
                issues.append(f"review_commitment_missing:{field}")

    judgment_rows: list[dict[str, str]] = []
    if csv_path.is_file():
        with csv_path.open(newline="", encoding="utf-8") as handle:
            judgment_rows = list(csv.DictReader(handle))
    else:
        issues.append("review_judgments_missing")
    if len(judgment_rows) != len(tasks) * len(REVIEW_DIMENSIONS):
        issues.append("review_judgment_row_count_mismatch")
    permitted_prefill = {"task_id", "task_content_hash", "dimension"}
    completed_rows = 0
    for row in judgment_rows:
        task_id = str(row.get("task_id") or "")
        if task_id not in task_ids:
            issues.append("review_judgment_unknown_task")
        if row.get("task_content_hash") != task_hashes.get(task_id):
            issues.append("review_judgment_hash_mismatch")
        if row.get("dimension") not in REVIEW_DIMENSIONS:
            issues.append("review_judgment_unknown_dimension")
        populated_human_fields = [
            field
            for field, value in row.items()
            if field not in permitted_prefill and str(value or "").strip()
        ]
        if populated_human_fields:
            completed_rows += 1
    if completed_rows:
        issues.append("unexpected_prefilled_human_judgments")
    return {
        "review_item_count": len(review_rows),
        "review_dimension_count": len(REVIEW_DIMENSIONS),
        "blank_judgment_row_count": len(judgment_rows) - completed_rows,
        "completed_human_judgment_row_count": completed_rows,
        "required_independent_reviewers_per_task": 2,
        "adjudication_required": True,
        "state": "HUMAN_INPUT_REQUIRED",
        "issues": sorted(set(issues)),
    }


def _commitment_issues(
    private_root: Path,
    *,
    manifest: dict[str, Any],
    private_manifest: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    commitments = manifest.get("private_file_commitments")
    if not isinstance(commitments, list):
        return ["public_file_commitments_missing"]
    by_role = {
        str(value.get("role")): value
        for value in commitments
        if isinstance(value, dict) and value.get("role")
    }
    if set(by_role) != set(PRIVATE_FILE_ROLES):
        issues.append("public_file_commitment_roles_mismatch")
    for role in PRIVATE_FILE_ROLES:
        path = private_root / role
        commitment = by_role.get(role)
        if not path.is_file():
            issues.append(f"committed_private_file_missing:{role}")
            continue
        if not isinstance(commitment, dict):
            continue
        if commitment.get("sha256") != _sha256_file(path):
            issues.append(f"private_file_hash_mismatch:{role}")
        if commitment.get("bytes") != path.stat().st_size:
            issues.append(f"private_file_size_mismatch:{role}")
    private_hash_fields = {
        "candidate_tasks.jsonl": "candidate_sha256",
        "human_review_items.jsonl": "review_items_sha256",
        "human_review_judgments.csv": "review_csv_sha256",
        "assignment_balance.json": "assignment_balance_sha256",
        "artifact_inventory.json": "artifact_inventory_sha256",
    }
    for role, field in private_hash_fields.items():
        path = private_root / role
        if path.is_file() and private_manifest.get(field) != _sha256_file(path):
            issues.append(f"private_manifest_hash_mismatch:{role}")
    if private_manifest.get("human_validation_state") != "HUMAN_INPUT_REQUIRED":
        issues.append("private_manifest_human_state_mismatch")
    if private_manifest.get("scientific_execution_allowed") is not False:
        issues.append("private_manifest_execution_not_blocked")
    if private_manifest.get("paper_eligible") is not False:
        issues.append("private_manifest_paper_eligibility_not_blocked")
    return issues


def _cross_candidate_audit(
    scale_rows: list[dict[str, Any]],
    naturalistic_rows: list[dict[str, Any]],
) -> dict[str, int]:
    report = diversity_audit(
        scale_rows,
        comparison_roles={"naturalistic_v2": naturalistic_rows},
    )
    overlap = report["role_overlap"].get("naturalistic_v2", {})
    return {
        "task_id_overlap": int(overlap.get("task_id_overlap", 0)),
        "content_hash_overlap": int(overlap.get("content_hash_overlap", 0)),
        "exact_instruction_overlap": int(
            overlap.get("exact_instruction_overlap", 0)
        ),
        "normalized_instruction_overlap": int(
            overlap.get("normalized_instruction_overlap", 0)
        ),
        "answer_hash_overlap": int(overlap.get("answer_hash_overlap", 0)),
        "lexical_near_duplicate_pair_count": int(
            overlap.get("lexical_near_duplicate_pair_count", 0)
        ),
    }


def _repository_safety_audit(
    repo_root: Path,
    rows_by_key: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    issues: list[str] = []
    tracked_private = _git_lines(repo_root, ["ls-files", "private_data"])
    if tracked_private:
        issues.append("repository:private_payload_tracked")
    ignored_roots = 0
    for spec in CANDIDATES:
        candidate = repo_root / spec.private_relative / "candidate_tasks.jsonl"
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(candidate.relative_to(repo_root))],
            cwd=repo_root,
            check=False,
        )
        if result.returncode == 0:
            ignored_roots += 1
        else:
            issues.append(f"repository:{spec.key}_private_root_not_ignored")
    public_files = _public_surface_files(repo_root)
    leak_count = 0
    for rows in rows_by_key.values():
        forbidden: list[bytes] = []
        for row in rows:
            task_id = str(row.get("task_id") or "")
            instruction = str(row.get("user_instruction") or "")
            answer = row.get("hidden_answer_key")
            if task_id:
                forbidden.append(task_id.encode("utf-8"))
            if instruction:
                forbidden.append(instruction.encode("utf-8"))
            if answer is not None:
                forbidden.append(
                    json.dumps(
                        answer,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                )
        for path in public_files:
            try:
                payload = path.read_bytes()
            except OSError:
                continue
            leak_count += sum(value in payload for value in forbidden if value)
    if leak_count:
        issues.append("repository:private_payload_fragment_on_public_surface")
    return {
        "tracked_private_file_count": len(tracked_private),
        "ignored_candidate_root_count": ignored_roots,
        "expected_ignored_candidate_root_count": len(CANDIDATES),
        "public_surface_file_count_scanned": len(public_files),
        "private_payload_fragment_match_count": leak_count,
        "issues": issues,
    }


def _contamination_policy_audit(repo_root: Path) -> dict[str, Any]:
    issues: list[str] = []
    path = repo_root / "data/manifests/CAB_PUBLIC_CONTAMINATION_REGISTRY.json"
    registry = _read_json_object(
        path,
        issues,
        "contamination_registry_missing",
    )
    records = registry.get("records")
    if not isinstance(records, list):
        records = []
        issues.append("contamination_registry_records_missing")
    required_prefixes = {
        "data/processed/scale100_confirmatory_v1_candidate/",
        "data/processed/naturalistic_transfer_v1_candidate/",
    }
    covered: set[str] = set()
    contaminated_records = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        prefixes = record.get("path_prefixes")
        if isinstance(prefixes, list):
            covered.update(str(value) for value in prefixes)
        if record.get("scientific_disposition") == "CONTAMINATED_NOT_CONFIRMATORY":
            contaminated_records += 1
        if isinstance(prefixes, list) and any(
            str(prefix) in required_prefixes for prefix in prefixes
        ):
            for field in (
                "confirmatory_eligible",
                "paper_eligible",
                "external_validity_eligible",
            ):
                if record.get(field) is not False:
                    issues.append(f"public_v1_not_invalidated:{field}")
    if not required_prefixes <= covered:
        issues.append("public_v1_contamination_records_incomplete")
    policy = registry.get("policy")
    if not isinstance(policy, dict) or any(
        policy.get(field) is not expected
        for field, expected in (
            ("deletion_restores_secrecy", False),
            ("history_rewrite_restores_scientific_eligibility", False),
            ("paper_eligible_evidence_allowed", False),
            ("public_exposure_is_permanent", True),
        )
    ):
        issues.append("permanent_contamination_policy_incomplete")
    return {
        "registry_present": path.is_file(),
        "record_count": len(records),
        "contaminated_not_confirmatory_record_count": contaminated_records,
        "scale100_v1_permanently_invalidated": (
            "data/processed/scale100_confirmatory_v1_candidate/" in covered
        ),
        "naturalistic_v1_permanently_invalidated": (
            "data/processed/naturalistic_transfer_v1_candidate/" in covered
        ),
        "deletion_does_not_restore_eligibility": True,
        "issues": issues,
    }


def _load_comparison_roles(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    role_paths = {
        "public_development": (
            "data/sample/base_tasks.jsonl",
            "data/processed/dev_20/base_tasks.jsonl",
        ),
        "contaminated_scale100_v1": (
            "data/processed/scale100_confirmatory_v1_candidate/base_tasks.jsonl",
        ),
        "contaminated_naturalistic_v1": (
            "data/processed/naturalistic_transfer_v1_candidate/base_tasks.jsonl",
        ),
        "contaminated_main500_v1": (
            "data/processed/main500_confirmatory_v1_candidate/base_tasks.jsonl",
        ),
    }
    comparison: dict[str, list[dict[str, Any]]] = {}
    for role, relative_paths in role_paths.items():
        rows: list[dict[str, Any]] = []
        for relative in relative_paths:
            path = repo_root / relative
            if path.is_file():
                rows.extend(read_jsonl_objects(path))
        comparison[role] = rows
    compact_path = (
        repo_root / "data/compact20_reviewed/compact20_reviewed_manifest.json"
    )
    compact = _read_json_object(compact_path, [], "compact_manifest_missing")
    candidates = compact.get("candidates")
    comparison["compact20_pilot"] = [
        {"task_id": value.get("base_task_id")}
        for value in candidates
        if isinstance(candidates, list)
        and isinstance(value, dict)
        and value.get("base_task_id")
    ] if isinstance(candidates, list) else []
    return comparison


def _public_diversity_summary(diversity: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "raw_task_count",
        "unique_task_id_count",
        "unique_template_id_count",
        "unique_scenario_id_count",
        "unique_workflow_class_count",
        "normalized_instruction_pattern_count",
        "genuinely_distinct_lower_bound",
        "domain_counts",
        "difficulty_counts",
        "tool_combination_count",
        "answer_contract_counts",
        "canonical_answer_contract_count",
        "noncanonical_answer_contract_task_count",
        "intervention_family_counts",
        "manipulation_check_count",
        "missing_manipulation_check_count",
        "exact_duplicate_group_count",
        "normalized_duplicate_group_count",
        "structural_duplicate_group_count",
        "coarse_structural_archetype_count",
        "coarse_structural_duplicate_group_count",
        "coarse_structural_duplicate_task_count",
        "lexical_similarity_summary",
        "answer_overlap_group_count",
        "role_overlap",
        "role_overlap_signal_count",
        "template_variant_risk",
    )
    return {key: diversity.get(key) for key in keys}


def _public_surface_files(repo_root: Path) -> list[Path]:
    tracked = {
        repo_root / value
        for value in _git_lines(repo_root, ["ls-files"])
        if value and not value.startswith("private_data/")
    }
    for relative in (
        "data/manifests",
        "docs",
        "experiments",
        "reports",
        "scripts",
        "src",
        "tests",
    ):
        root = repo_root / relative
        if root.is_dir():
            tracked.update(
                path
                for path in root.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.stat().st_size <= 10 * 1024 * 1024
            )
    return sorted(tracked)


def _git_lines(repo_root: Path, arguments: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _read_json_object(
    path: Path,
    issues: list[str],
    missing_issue: str,
) -> dict[str, Any]:
    if not path.is_file():
        issues.append(missing_issue)
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        issues.append(f"{missing_issue}:invalid_json")
        return {}
    if not isinstance(value, dict):
        issues.append(f"{missing_issue}:not_object")
        return {}
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
    )
    parser.add_argument(
        "--write-json",
        type=Path,
        help="Optional public-safe aggregate JSON report path.",
    )
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Validate committed public v2 metadata without ignored private bodies.",
    )
    args = parser.parse_args(argv)
    report = (
        audit_public_commitments(args.repo_root)
        if args.public_only
        else audit_repository(args.repo_root)
    )
    if args.write_json:
        output = args.write_json
        if not output.is_absolute():
            output = args.repo_root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    summary = {
        "status": report["status"],
        "static_passed": report["static_passed"],
        "scale100_task_count": report["datasets"]["scale100"]["task_count"],
        "naturalistic_task_count": report["datasets"]["naturalistic"][
            "task_count"
        ],
        "issue_count": len(report["issue_codes"]),
        "human_validation_complete": False,
        "scientific_execution_performed": False,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if report["static_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
