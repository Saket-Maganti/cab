"""Canonical fail-closed human-validation and C10 contract.

The validator never creates judgments or identities. It accepts only the
canonical comprehensive review sheet, a privacy-safe reviewer registry, a
separate adjudication sheet, and independently checkable prerequisite
artifacts. Proxy, AI-assisted, synthetic, fixture, partial, and header-only
inputs cannot promote C10.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.analysis.human_validation import compute_agreement
from causal_agent_bench.hashing import stable_hash

DEFAULT_REVIEW_DIR = Path("data/human_validation/compact20_real_review")
DEFAULT_CANDIDATE_MANIFEST = Path(
    "data/compact20_reviewed/compact20_reviewed_manifest.json"
)
DEFAULT_CONTRACT_PATH = Path("configs/human_validation/c10_contract_v1.json")

REVIEW_FILE = "review_judgments.csv"
REVIEWER_REGISTRY_FILE = "reviewer_registry.csv"
ADJUDICATION_FILE = "adjudication.csv"
SESSION_FILE = "review_session.json"
PREREQUISITES_FILE = "c10_prerequisites.json"
MANIPULATION_CHECK_FILE = "manipulation_checks.json"

REVIEW_DIMENSIONS = (
    "task_clarity",
    "clean_gold_correctness",
    "manipulation_success",
    "goal_preservation",
    "invariance_preservation",
    "solvability",
    "answer_contract_correctness",
    "scorer_compatibility",
    "realism",
    "ambiguity",
    "exclusion_recommendation",
)

REVIEW_COLUMNS = (
    "candidate_id",
    "reviewer_slot",
    "reviewer_id",
    "review_source",
    "ai_assistance_used",
    "model_output_visible",
    "model_identity_visible",
    *REVIEW_DIMENSIONS,
    "confidence_1_to_5",
    "notes",
    "timestamp",
)

REVIEWER_REGISTRY_COLUMNS = (
    "reviewer_id",
    "role",
    "privacy_safe_id_confirmed",
    "qualification_status",
    "qualification_score",
    "qualification_total",
    "expertise_disclosure",
    "conflict_of_interest",
    "consent_confirmed",
    "human_only_attestation",
    "is_study_author",
    "compensation_disclosure_ack",
    "registered_at",
)

ADJUDICATION_COLUMNS = (
    "candidate_id",
    "dimension",
    "reviewer_ids",
    "reviewer_labels",
    "final_label",
    "adjudicator_id",
    "review_source",
    "ai_assistance_used",
    "rationale",
    "timestamp",
)

YES_NO_UNCLEAR_DIMENSIONS = frozenset(REVIEW_DIMENSIONS[:9])
ALLOWED_LABELS: dict[str, frozenset[str]] = {
    **{
        dimension: frozenset({"yes", "no", "unclear"})
        for dimension in YES_NO_UNCLEAR_DIMENSIONS
    },
    "ambiguity": frozenset({"acceptable", "problematic", "unclear"}),
    "exclusion_recommendation": frozenset({"include", "revise", "exclude"}),
}
PASS_LABELS = {
    **dict.fromkeys(YES_NO_UNCLEAR_DIMENSIONS, "yes"),
    "ambiguity": "acceptable",
    "exclusion_recommendation": "include",
}

REAL_REVIEWER_ID = re.compile(r"^rvw_[0-9a-f]{12,64}$")
REAL_ADJUDICATOR_ID = re.compile(r"^adj_[0-9a-f]{12,64}$")
PLACEHOLDER_TOKENS = frozenset(
    {
        "",
        "tbd",
        "todo",
        "unknown",
        "placeholder",
        "reviewer",
        "reviewer_id",
        "annotator",
        "anonymous",
        "human-a",
        "human-b",
        "ai",
        "proxy",
        "synthetic",
        "fixture",
        "test",
        "fake",
    }
)
FORBIDDEN_PROVENANCE_TOKENS = (
    "ai_proxy",
    "ai review",
    "ai_review",
    "model_generated",
    "not_human",
    "synthetic_review",
    "fixture_only",
    "proxy_review",
)


@dataclass(frozen=True)
class HumanReviewPolicy:
    """Preregistered C10 thresholds; callers may strengthen but not weaken."""

    min_independent_reviewers: int = 2
    min_raw_agreement: float = 0.80
    min_items_for_agreement: int = 5
    min_qualification_rate: float = 0.80
    require_all_final_valid: bool = True


def validate_compact20_human_reviews(
    repo_root: str | Path,
    *,
    review_dir: str | Path = DEFAULT_REVIEW_DIR,
    candidate_manifest: str | Path = DEFAULT_CANDIDATE_MANIFEST,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
    policy: HumanReviewPolicy | None = None,
) -> dict[str, Any]:
    """Validate canonical human rows and derive C10 without model inference."""

    root = Path(repo_root).resolve()
    review_root = _resolve(root, review_dir)
    manifest_path = _resolve(root, candidate_manifest)
    contract_file = _resolve(root, contract_path)
    registered_policy = policy or HumanReviewPolicy()
    issues: list[dict[str, str]] = []

    contract = _load_contract(contract_file, issues)
    _validate_policy_strength(registered_policy, contract, issues)
    candidate_rows = _candidate_rows(manifest_path, issues)
    candidate_ids = sorted(candidate_rows)
    manifest_sha256 = _sha256_file(manifest_path)
    slice_hash = candidate_slice_hash(candidate_rows)

    session = _read_json_object(
        review_root / SESSION_FILE,
        issues=issues,
        issue_code="MISSING_OR_INVALID_REVIEW_SESSION",
    )
    session_mode, session_valid = _validate_session(
        session,
        manifest_sha256=manifest_sha256,
        issues=issues,
    )

    registry_rows = _read_csv(
        review_root / REVIEWER_REGISTRY_FILE,
        required_columns=REVIEWER_REGISTRY_COLUMNS,
        issues=issues,
    )
    registry = _validate_reviewer_registry(
        registry_rows,
        policy=registered_policy,
        session_mode=session_mode,
        issues=issues,
    )

    raw_review_rows = _read_csv(
        review_root / REVIEW_FILE,
        required_columns=REVIEW_COLUMNS,
        issues=issues,
    )
    review_rows, blank_review_rows = _validate_review_rows(
        raw_review_rows,
        candidate_ids=set(candidate_ids),
        registry=registry,
        session_mode=session_mode,
        issues=issues,
    )

    raw_adjudication_rows = _read_csv(
        review_root / ADJUDICATION_FILE,
        required_columns=ADJUDICATION_COLUMNS,
        issues=issues,
    )
    adjudication_rows, blank_adjudication_rows = _validate_adjudication_rows(
        raw_adjudication_rows,
        candidate_ids=set(candidate_ids),
        registry=registry,
        review_rows=review_rows,
        session_mode=session_mode,
        issues=issues,
    )

    coverage = _coverage(
        candidate_ids,
        review_rows,
        min_reviewers=registered_policy.min_independent_reviewers,
    )
    expected_groups = len(candidate_ids)
    complete_groups = sum(
        bool(summary["complete"]) for summary in coverage.values()
    )
    full_coverage = expected_groups > 0 and complete_groups == expected_groups

    agreement_rows = [
        {
            "item_id": row["candidate_id"],
            "annotator_id": row["reviewer_id"],
            **{dimension: row[dimension] for dimension in REVIEW_DIMENSIONS},
        }
        for row in review_rows
    ]
    agreement = compute_agreement(
        agreement_rows,
        dimensions=REVIEW_DIMENSIONS,
        confidence_level=0.95,
        min_items_for_ci=registered_policy.min_items_for_agreement,
        bootstrap_repetitions=1_000,
    )
    raw_agreement = _overall_raw_agreement(agreement_rows)
    agreement_threshold_met = (
        raw_agreement is not None
        and raw_agreement >= registered_policy.min_raw_agreement
        and all(
            stats["analysis_state"] == "READY"
            and isinstance(stats["raw_agreement"], int | float)
            and float(stats["raw_agreement"])
            >= registered_policy.min_raw_agreement
            for stats in agreement.values()
        )
    )

    disagreements = _disagreements(review_rows)
    adjudication_by_key = {
        (row["candidate_id"], row["dimension"]): row
        for row in adjudication_rows
    }
    unresolved = [
        {
            "candidate_id": candidate_id,
            "dimension": dimension,
            "labels": labels,
            "reason": "independent reviewers disagree and no valid separate adjudication exists",
        }
        for (candidate_id, dimension), labels in disagreements.items()
        if (candidate_id, dimension) not in adjudication_by_key
    ]
    adjudication_complete = not unresolved
    final_labels = _final_labels(
        candidate_ids,
        review_rows,
        adjudication_by_key,
    )
    final_validity = {
        candidate_id: (
            all(
                labels.get(dimension) == PASS_LABELS[dimension]
                for dimension in REVIEW_DIMENSIONS
            )
            if len(labels) == len(REVIEW_DIMENSIONS)
            else None
        )
        for candidate_id, labels in final_labels.items()
    }
    all_final_valid = bool(final_validity) and all(
        value is True for value in final_validity.values()
    )

    prerequisite_payload = _read_json_object(
        review_root / PREREQUISITES_FILE,
        issues=issues,
        issue_code="MISSING_OR_INVALID_C10_PREREQUISITES",
    )
    manipulation_payload = _read_json_object(
        review_root / MANIPULATION_CHECK_FILE,
        issues=issues,
        issue_code="MISSING_OR_INVALID_MANIPULATION_CHECK_REPORT",
    )
    prerequisites = _validate_prerequisites(
        root=root,
        review_root=review_root,
        payload=prerequisite_payload,
        manipulation_payload=manipulation_payload,
        manifest_sha256=manifest_sha256,
        slice_hash=slice_hash,
        candidate_count=len(candidate_ids),
    )

    review_mode_eligible = session_mode in {"real_human", "fixture"}
    structural_blockers: list[str] = []
    if not candidate_ids:
        structural_blockers.append("CANDIDATE_MANIFEST_EMPTY")
    if not session_valid:
        structural_blockers.append("REVIEW_SESSION_INVALID")
    if not full_coverage:
        structural_blockers.append("FULL_CANDIDATE_COVERAGE_MISSING")
    if not agreement_threshold_met:
        structural_blockers.append("AGREEMENT_THRESHOLD_NOT_MET")
    if not adjudication_complete:
        structural_blockers.append("ADJUDICATION_INCOMPLETE")
    if registered_policy.require_all_final_valid and not all_final_valid:
        structural_blockers.append("FINAL_VALIDITY_NOT_SATISFIED")
    structural_blockers.extend(
        check["code"]
        for check in prerequisites.values()
        if not check["passed"]
    )
    if _blocking_issues(issues):
        structural_blockers.append("INVALID_REVIEW_ARTIFACTS")
    structural_blockers = sorted(set(structural_blockers))
    structural_contract_pass = (
        review_mode_eligible and not structural_blockers
    )

    if not full_coverage:
        human_state = "HUMAN_REVIEW_INCOMPLETE"
    elif not adjudication_complete:
        human_state = "ADJUDICATION_PENDING"
    else:
        human_state = "HUMAN_REVIEW_COMPLETE"

    if session_mode == "real_human" and structural_contract_pass:
        c10_state = "PASS"
        contract_evaluation_state = "REAL_HUMAN_CONTRACT_PASS"
    elif session_mode == "fixture" and structural_contract_pass:
        c10_state = "C10_PENDING"
        contract_evaluation_state = "FIXTURE_CONTRACT_PASS"
    elif full_coverage and adjudication_complete and session_valid:
        c10_state = "C10_FAILED"
        contract_evaluation_state = "CONTRACT_FAILED"
    else:
        c10_state = "C10_PENDING"
        contract_evaluation_state = "INPUT_PENDING"

    genuine_review_rows = len(review_rows) if session_mode == "real_human" else 0
    genuine_adjudication_rows = (
        len(adjudication_rows) if session_mode == "real_human" else 0
    )
    fixture_review_rows = len(review_rows) if session_mode == "fixture" else 0
    fixture_adjudication_rows = (
        len(adjudication_rows) if session_mode == "fixture" else 0
    )

    return {
        "schema_version": "cab_c10_contract_v2",
        "generated_at": datetime.now(UTC).isoformat(),
        "evidence_class": (
            "AUDITED_REAL_EVIDENCE"
            if c10_state == "PASS"
            else "FIXTURE_ONLY"
            if session_mode == "fixture"
            else "HUMAN_INPUT_REQUIRED"
        ),
        "review_dir": _relative(review_root, root),
        "candidate_manifest": _relative(manifest_path, root),
        "candidate_manifest_sha256": manifest_sha256,
        "candidate_slice_hash": slice_hash,
        "contract_path": _relative(contract_file, root),
        "contract": contract,
        "policy": {
            "min_independent_reviewers": registered_policy.min_independent_reviewers,
            "min_raw_agreement": registered_policy.min_raw_agreement,
            "min_items_for_agreement": registered_policy.min_items_for_agreement,
            "min_qualification_rate": registered_policy.min_qualification_rate,
            "require_all_final_valid": registered_policy.require_all_final_valid,
            "policy_status": "DESIGN_ONLY_PREREGISTERED_BEFORE_REVIEW",
        },
        "review_session": {
            "mode": session_mode,
            "valid": session_valid,
            "model_output_blinded": session.get("model_output_blinded"),
            "model_identity_blinded": session.get("model_identity_blinded"),
            "human_only_attestation": session.get("human_only_attestation"),
        },
        "candidate_count": len(candidate_ids),
        "expected_review_groups": expected_groups,
        "complete_review_groups": complete_groups,
        "blank_template_review_rows": blank_review_rows,
        "blank_template_adjudication_rows": blank_adjudication_rows,
        "genuine_human_review_row_count": genuine_review_rows,
        "genuine_human_adjudication_row_count": genuine_adjudication_rows,
        "genuine_human_row_count": genuine_review_rows + genuine_adjudication_rows,
        "fixture_review_row_count": fixture_review_rows,
        "fixture_adjudication_row_count": fixture_adjudication_rows,
        "proxy_rows_counted": 0,
        "raw_agreement": raw_agreement,
        "agreement_threshold_met": agreement_threshold_met,
        "agreement": agreement,
        "prevalence_diagnostics": {
            dimension: stats["prevalence"]
            for dimension, stats in agreement.items()
        },
        "unresolved_disagreements": unresolved,
        "adjudication": {
            "disagreement_count": len(disagreements),
            "resolved_disagreement_count": len(disagreements) - len(unresolved),
            "adjudication_rate": (
                round(
                    (len(disagreements) - len(unresolved))
                    / len(disagreements),
                    6,
                )
                if disagreements
                else 0.0
            ),
            "complete": adjudication_complete,
        },
        "exclusion": _exclusion_summary(final_labels),
        "family_specific_validity": _family_validity(
            candidate_rows,
            final_labels,
        ),
        "reviewer_confidence": _confidence_summary(review_rows),
        "coverage": coverage,
        "final_labels": final_labels,
        "final_validity": final_validity,
        "prerequisites": prerequisites,
        "manipulation_checks": {
            "schema_version": manipulation_payload.get("schema_version"),
            "record_count": manipulation_payload.get("record_count"),
            "all_candidates_linked": manipulation_payload.get(
                "all_candidates_linked"
            ),
            "all_applicable_checks_passed": manipulation_payload.get(
                "all_applicable_checks_passed"
            ),
        },
        "issues": issues,
        "c10_blockers": structural_blockers,
        "human_review_state": human_state,
        "c10_state": c10_state,
        "contract_evaluation_state": contract_evaluation_state,
        "fixture_contract_passed": (
            session_mode == "fixture" and structural_contract_pass
        ),
        "slice_lock_allowed": c10_state == "PASS",
        "paper_eligibility_allowed": False,
        "scientific_execution_allowed": False,
    }


def write_human_review_gate_report(
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _load_contract(
    path: Path,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    payload = _read_json_object(
        path,
        issues=issues,
        issue_code="MISSING_OR_INVALID_C10_CONTRACT",
    )
    if not payload:
        return {
            "schema_version": "cab_c10_contract_v1",
            "required_dimensions": list(REVIEW_DIMENSIONS),
            "min_independent_reviewers": 2,
            "min_raw_agreement": 0.80,
            "min_items_for_agreement": 5,
            "min_qualification_rate": 0.80,
            "require_all_final_valid": True,
            "required_prerequisites": [
                "leakage_gate",
                "answer_contract",
                "slice_freeze",
                "manipulation_checks",
            ],
        }
    required_dimensions = payload.get("required_dimensions")
    if required_dimensions != list(REVIEW_DIMENSIONS):
        issues.append(
            _issue(
                "C10_CONTRACT_DIMENSIONS_MISMATCH",
                str(path),
                "contract dimensions do not match the canonical v1 dimensions",
            )
        )
    return payload


def _validate_policy_strength(
    policy: HumanReviewPolicy,
    contract: dict[str, Any],
    issues: list[dict[str, str]],
) -> None:
    checks = (
        (
            "min_independent_reviewers",
            policy.min_independent_reviewers,
            int(contract.get("min_independent_reviewers") or 2),
        ),
        (
            "min_raw_agreement",
            policy.min_raw_agreement,
            float(contract.get("min_raw_agreement") or 0.80),
        ),
        (
            "min_items_for_agreement",
            policy.min_items_for_agreement,
            int(contract.get("min_items_for_agreement") or 5),
        ),
        (
            "min_qualification_rate",
            policy.min_qualification_rate,
            float(contract.get("min_qualification_rate") or 0.80),
        ),
    )
    for name, actual, minimum in checks:
        if actual < minimum:
            issues.append(
                _issue(
                    "C10_POLICY_WEAKENING_REJECTED",
                    name,
                    f"{actual} is below canonical minimum {minimum}",
                )
            )
    if bool(contract.get("require_all_final_valid", True)) and not policy.require_all_final_valid:
        issues.append(
            _issue(
                "C10_POLICY_WEAKENING_REJECTED",
                "require_all_final_valid",
                "canonical contract requires all final labels to be valid",
            )
        )


def _candidate_rows(
    path: Path,
    issues: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    payload = _read_json_object(
        path,
        issues=issues,
        issue_code="MISSING_OR_INVALID_CANDIDATE_MANIFEST",
    )
    raw = payload.get("candidates")
    rows = raw if isinstance(raw, list) else []
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        candidate_id = str(row.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        if candidate_id in output:
            issues.append(
                _issue(
                    "DUPLICATE_CANDIDATE_ID",
                    str(path),
                    candidate_id,
                )
            )
        output[candidate_id] = row
    if not output:
        issues.append(
            _issue(
                "CANDIDATE_MANIFEST_EMPTY",
                str(path),
                "candidate manifest has no usable candidates",
            )
        )
    return output


def _validate_session(
    session: dict[str, Any],
    *,
    manifest_sha256: str | None,
    issues: list[dict[str, str]],
) -> tuple[str, bool]:
    mode = str(session.get("review_mode") or "pending").strip().lower()
    valid_modes = {"pending", "real_human", "fixture"}
    valid = True
    if mode not in valid_modes:
        issues.append(
            _issue(
                "INVALID_REVIEW_MODE",
                SESSION_FILE,
                f"expected one of {sorted(valid_modes)}, got {mode!r}",
            )
        )
        valid = False
    expected_evidence = {
        "pending": "HUMAN_INPUT_REQUIRED",
        "real_human": "AUDITED_REAL_EVIDENCE",
        "fixture": "FIXTURE_ONLY",
    }.get(mode)
    if session.get("evidence_class") != expected_evidence:
        issues.append(
            _issue(
                "REVIEW_SESSION_EVIDENCE_CLASS_MISMATCH",
                SESSION_FILE,
                f"{mode} requires evidence_class={expected_evidence}",
            )
        )
        valid = False
    if session.get("candidate_manifest_sha256") != manifest_sha256:
        issues.append(
            _issue(
                "REVIEW_SESSION_MANIFEST_HASH_MISMATCH",
                SESSION_FILE,
                "session is not bound to the current candidate manifest",
            )
        )
        valid = False
    for key, expected in (
        ("model_output_blinded", True),
        ("model_identity_blinded", True),
        ("ai_or_proxy_review_permitted", False),
    ):
        if session.get(key) is not expected:
            issues.append(
                _issue(
                    "REVIEW_SESSION_BLINDING_OR_PROVENANCE_INVALID",
                    SESSION_FILE,
                    f"{key} must be {expected}",
                )
            )
            valid = False
    expected_human_attestation = mode == "real_human"
    if (
        mode in {"real_human", "fixture"}
        and session.get("human_only_attestation")
        is not expected_human_attestation
    ):
        issues.append(
            _issue(
                "HUMAN_ONLY_ATTESTATION_MISSING",
                SESSION_FILE,
                "human_only_attestation must match the declared review mode",
            )
        )
        valid = False
    return mode, valid


def _validate_reviewer_registry(
    rows: list[dict[str, str]],
    *,
    policy: HumanReviewPolicy,
    session_mode: str,
    issues: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    registry: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, start=2):
        if _blank_row(row, identity_columns=("reviewer_id",)):
            continue
        reviewer_id = row.get("reviewer_id", "").strip().lower()
        role = row.get("role", "").strip().lower()
        expected_pattern = (
            REAL_REVIEWER_ID if role == "reviewer" else REAL_ADJUDICATOR_ID
            if role == "adjudicator"
            else None
        )
        valid = True
        if (
            expected_pattern is None
            or not _valid_identity(reviewer_id, expected_pattern)
        ):
            issues.append(
                _issue(
                    "FAKE_OR_INVALID_REVIEWER_ID",
                    f"{REVIEWER_REGISTRY_FILE}:{row_number}",
                    reviewer_id or "blank identity",
                )
            )
            valid = False
        if reviewer_id in registry:
            issues.append(
                _issue(
                    "DUPLICATE_REVIEWER_REGISTRY_ID",
                    f"{REVIEWER_REGISTRY_FILE}:{row_number}",
                    reviewer_id,
                )
            )
            valid = False
        if session_mode == "fixture":
            required_exact = {
                "privacy_safe_id_confirmed": "yes",
                "qualification_status": "passed",
                "conflict_of_interest": "not_applicable_fixture",
                "consent_confirmed": "not_applicable_fixture",
                "human_only_attestation": "no",
                "is_study_author": "not_applicable_fixture",
                "compensation_disclosure_ack": "not_applicable_fixture",
            }
        else:
            required_exact = {
                "privacy_safe_id_confirmed": "yes",
                "qualification_status": "passed",
                "conflict_of_interest": "none_declared",
                "consent_confirmed": "yes",
                "human_only_attestation": "yes",
                "is_study_author": "no",
                "compensation_disclosure_ack": "yes",
            }
        for column, expected in required_exact.items():
            if row.get(column, "").strip().lower() != expected:
                issues.append(
                    _issue(
                        "REVIEWER_QUALIFICATION_OR_DISCLOSURE_INVALID",
                        f"{REVIEWER_REGISTRY_FILE}:{row_number}",
                        f"{column} must be {expected}",
                    )
                )
                valid = False
        if not row.get("expertise_disclosure", "").strip():
            issues.append(
                _issue(
                    "EXPERTISE_DISCLOSURE_MISSING",
                    f"{REVIEWER_REGISTRY_FILE}:{row_number}",
                    reviewer_id,
                )
            )
            valid = False
        try:
            score = int(row.get("qualification_score", ""))
            total = int(row.get("qualification_total", ""))
            qualification_rate = score / total
        except (ValueError, ZeroDivisionError):
            qualification_rate = -1.0
        if qualification_rate < policy.min_qualification_rate:
            issues.append(
                _issue(
                    "REVIEWER_QUALIFICATION_THRESHOLD_NOT_MET",
                    f"{REVIEWER_REGISTRY_FILE}:{row_number}",
                    reviewer_id,
                )
            )
            valid = False
        if not _valid_timestamp(row.get("registered_at", "")):
            issues.append(
                _issue(
                    "INVALID_REVIEWER_REGISTRATION_TIMESTAMP",
                    f"{REVIEWER_REGISTRY_FILE}:{row_number}",
                    reviewer_id,
                )
            )
            valid = False
        if valid:
            registry[reviewer_id] = row
    return registry


def _validate_review_rows(
    rows: list[dict[str, str]],
    *,
    candidate_ids: set[str],
    registry: dict[str, dict[str, str]],
    session_mode: str,
    issues: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int]:
    accepted: list[dict[str, str]] = []
    blank_count = 0
    seen_reviewers: set[tuple[str, str]] = set()
    seen_slots: set[tuple[str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        if _blank_row(
            row,
            identity_columns=(
                "reviewer_id",
                *REVIEW_DIMENSIONS,
                "confidence_1_to_5",
                "notes",
                "timestamp",
            ),
        ):
            blank_count += 1
            continue
        valid = True
        candidate_id = row.get("candidate_id", "").strip()
        reviewer_id = row.get("reviewer_id", "").strip().lower()
        slot = row.get("reviewer_slot", "").strip()
        if candidate_id not in candidate_ids:
            issues.append(
                _issue(
                    "UNKNOWN_OR_MISSING_CANDIDATE_ID",
                    f"{REVIEW_FILE}:{row_number}",
                    candidate_id,
                )
            )
            valid = False
        reviewer = registry.get(reviewer_id)
        if reviewer is None or reviewer.get("role", "").lower() != "reviewer":
            issues.append(
                _issue(
                    "UNREGISTERED_OR_UNQUALIFIED_REVIEWER",
                    f"{REVIEW_FILE}:{row_number}",
                    reviewer_id,
                )
            )
            valid = False
        try:
            if int(slot) < 1:
                raise ValueError
        except ValueError:
            issues.append(
                _issue(
                    "INVALID_REVIEWER_SLOT",
                    f"{REVIEW_FILE}:{row_number}",
                    slot,
                )
            )
            valid = False
        duplicate_reviewer_key = (candidate_id, reviewer_id)
        duplicate_slot_key = (candidate_id, slot)
        if duplicate_reviewer_key in seen_reviewers:
            issues.append(
                _issue(
                    "DUPLICATED_REVIEWER_FOR_CANDIDATE",
                    f"{REVIEW_FILE}:{row_number}",
                    f"{candidate_id}:{reviewer_id}",
                )
            )
            valid = False
        if duplicate_slot_key in seen_slots:
            issues.append(
                _issue(
                    "DUPLICATED_REVIEWER_SLOT",
                    f"{REVIEW_FILE}:{row_number}",
                    f"{candidate_id}:{slot}",
                )
            )
            valid = False
        expected_source = "fixture" if session_mode == "fixture" else "human"
        if row.get("review_source", "").strip().lower() != expected_source:
            issues.append(
                _issue(
                    "PROXY_OR_AI_REVIEW_REJECTED",
                    f"{REVIEW_FILE}:{row_number}",
                    f"review_source must be {expected_source}",
                )
            )
            valid = False
        if row.get("ai_assistance_used", "").strip().lower() != "no":
            issues.append(
                _issue(
                    "PROXY_OR_AI_REVIEW_REJECTED",
                    f"{REVIEW_FILE}:{row_number}",
                    "ai_assistance_used must be no",
                )
            )
            valid = False
        for column in ("model_output_visible", "model_identity_visible"):
            if row.get(column, "").strip().lower() != "no":
                issues.append(
                    _issue(
                        "MODEL_BLINDING_VIOLATION",
                        f"{REVIEW_FILE}:{row_number}",
                        f"{column} must be no",
                    )
                )
                valid = False
        for dimension in REVIEW_DIMENSIONS:
            label = row.get(dimension, "").strip().lower()
            if label not in ALLOWED_LABELS[dimension]:
                issues.append(
                    _issue(
                        "INVALID_REVIEW_VALUE",
                        f"{REVIEW_FILE}:{row_number}",
                        f"{dimension}={label!r}",
                    )
                )
                valid = False
        try:
            confidence = int(row.get("confidence_1_to_5", ""))
        except ValueError:
            confidence = 0
        if not 1 <= confidence <= 5:
            issues.append(
                _issue(
                    "INVALID_REVIEWER_CONFIDENCE",
                    f"{REVIEW_FILE}:{row_number}",
                    row.get("confidence_1_to_5", ""),
                )
            )
            valid = False
        if not row.get("notes", "").strip():
            issues.append(
                _issue(
                    "REVIEW_NOTES_MISSING",
                    f"{REVIEW_FILE}:{row_number}",
                    candidate_id,
                )
            )
            valid = False
        if not _valid_timestamp(row.get("timestamp", "")):
            issues.append(
                _issue(
                    "INVALID_REVIEW_TIMESTAMP",
                    f"{REVIEW_FILE}:{row_number}",
                    candidate_id,
                )
            )
            valid = False
        if _contains_forbidden_provenance(row.values()):
            issues.append(
                _issue(
                    "PROXY_OR_AI_REVIEW_REJECTED",
                    f"{REVIEW_FILE}:{row_number}",
                    "row contains forbidden proxy/synthetic provenance marker",
                )
            )
            valid = False
        seen_reviewers.add(duplicate_reviewer_key)
        seen_slots.add(duplicate_slot_key)
        if valid:
            accepted.append(row)
    return accepted, blank_count


def _validate_adjudication_rows(
    rows: list[dict[str, str]],
    *,
    candidate_ids: set[str],
    registry: dict[str, dict[str, str]],
    review_rows: list[dict[str, str]],
    session_mode: str,
    issues: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int]:
    reviewers_by_candidate: dict[str, set[str]] = defaultdict(set)
    labels_by_candidate_dimension: dict[
        tuple[str, str], Counter[str]
    ] = defaultdict(Counter)
    for row in review_rows:
        reviewers_by_candidate[row["candidate_id"]].add(row["reviewer_id"])
        for dimension in REVIEW_DIMENSIONS:
            labels_by_candidate_dimension[
                (row["candidate_id"], dimension)
            ][row[dimension]] += 1
    accepted: list[dict[str, str]] = []
    blank_count = 0
    seen: set[tuple[str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        if _blank_row(
            row,
            identity_columns=(
                "dimension",
                "reviewer_ids",
                "reviewer_labels",
                "final_label",
                "adjudicator_id",
                "rationale",
                "timestamp",
            ),
        ):
            blank_count += 1
            continue
        candidate_id = row.get("candidate_id", "").strip()
        dimension = row.get("dimension", "").strip()
        adjudicator_id = row.get("adjudicator_id", "").strip().lower()
        valid = True
        if candidate_id not in candidate_ids:
            issues.append(
                _issue(
                    "UNKNOWN_OR_MISSING_CANDIDATE_ID",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    candidate_id,
                )
            )
            valid = False
        if dimension not in REVIEW_DIMENSIONS:
            issues.append(
                _issue(
                    "INVALID_ADJUDICATION_DIMENSION",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    dimension,
                )
            )
            valid = False
        adjudicator = registry.get(adjudicator_id)
        if (
            adjudicator is None
            or adjudicator.get("role", "").lower() != "adjudicator"
        ):
            issues.append(
                _issue(
                    "UNREGISTERED_OR_UNQUALIFIED_ADJUDICATOR",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    adjudicator_id,
                )
            )
            valid = False
        if adjudicator_id in reviewers_by_candidate.get(candidate_id, set()):
            issues.append(
                _issue(
                    "ADJUDICATOR_NOT_SEPARATE",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    adjudicator_id,
                )
            )
            valid = False
        final_label = row.get("final_label", "").strip().lower()
        if dimension in ALLOWED_LABELS and final_label not in ALLOWED_LABELS[dimension]:
            issues.append(
                _issue(
                    "INVALID_ADJUDICATION_VALUE",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    f"{dimension}={final_label!r}",
                )
            )
            valid = False
        declared_reviewers = {
            value.strip().lower()
            for value in row.get("reviewer_ids", "").split("|")
            if value.strip()
        }
        if declared_reviewers != reviewers_by_candidate.get(candidate_id, set()):
            issues.append(
                _issue(
                    "ADJUDICATION_REVIEWER_LINKAGE_MISMATCH",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    candidate_id,
                )
            )
            valid = False
        declared_labels = Counter(
            value.strip().lower()
            for value in row.get("reviewer_labels", "").split("|")
            if value.strip()
        )
        if declared_labels != labels_by_candidate_dimension.get(
            (candidate_id, dimension),
            Counter(),
        ):
            issues.append(
                _issue(
                    "ADJUDICATION_LABEL_LINKAGE_MISMATCH",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    f"{candidate_id}:{dimension}",
                )
            )
            valid = False
        expected_source = "fixture" if session_mode == "fixture" else "human"
        if row.get("review_source", "").strip().lower() != expected_source:
            issues.append(
                _issue(
                    "PROXY_OR_AI_ADJUDICATION_REJECTED",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    f"review_source must be {expected_source}",
                )
            )
            valid = False
        if row.get("ai_assistance_used", "").strip().lower() != "no":
            issues.append(
                _issue(
                    "PROXY_OR_AI_ADJUDICATION_REJECTED",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    "ai_assistance_used must be no",
                )
            )
            valid = False
        if not row.get("rationale", "").strip():
            issues.append(
                _issue(
                    "ADJUDICATION_RATIONALE_MISSING",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    candidate_id,
                )
            )
            valid = False
        if not _valid_timestamp(row.get("timestamp", "")):
            issues.append(
                _issue(
                    "INVALID_ADJUDICATION_TIMESTAMP",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    candidate_id,
                )
            )
            valid = False
        key = (candidate_id, dimension)
        if key in seen:
            issues.append(
                _issue(
                    "DUPLICATE_ADJUDICATION",
                    f"{ADJUDICATION_FILE}:{row_number}",
                    f"{candidate_id}:{dimension}",
                )
            )
            valid = False
        seen.add(key)
        if valid:
            accepted.append(row)
    return accepted, blank_count


def _coverage(
    candidate_ids: list[str],
    rows: list[dict[str, str]],
    *,
    min_reviewers: int,
) -> dict[str, dict[str, Any]]:
    by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_candidate[row["candidate_id"]].append(row)
    return {
        candidate_id: {
            "row_count": len(by_candidate[candidate_id]),
            "independent_reviewer_count": len(
                {
                    row["reviewer_id"]
                    for row in by_candidate[candidate_id]
                }
            ),
            "reviewer_slots": sorted(
                row["reviewer_slot"] for row in by_candidate[candidate_id]
            ),
            "complete": len(
                {
                    row["reviewer_id"]
                    for row in by_candidate[candidate_id]
                }
            )
            >= min_reviewers,
        }
        for candidate_id in candidate_ids
    }


def _overall_raw_agreement(
    rows: list[dict[str, Any]],
) -> float | None:
    labels_by_group: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        item_id = str(row.get("item_id") or "")
        for dimension in REVIEW_DIMENSIONS:
            label = str(row.get(dimension) or "").strip().lower()
            if item_id and label:
                labels_by_group[(item_id, dimension)].append(label)
    comparable = [
        labels for labels in labels_by_group.values() if len(labels) >= 2
    ]
    if not comparable:
        return None
    return round(
        sum(len(set(labels)) == 1 for labels in comparable)
        / len(comparable),
        6,
    )


def _disagreements(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], list[str]]:
    labels: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        for dimension in REVIEW_DIMENSIONS:
            labels[(row["candidate_id"], dimension)].add(row[dimension])
    return {
        key: sorted(values)
        for key, values in labels.items()
        if len(values) > 1
    }


def _final_labels(
    candidate_ids: list[str],
    review_rows: list[dict[str, str]],
    adjudication_by_key: dict[tuple[str, str], dict[str, str]],
) -> dict[str, dict[str, str]]:
    labels: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in review_rows:
        for dimension in REVIEW_DIMENSIONS:
            labels[(row["candidate_id"], dimension)].add(row[dimension])
    output: dict[str, dict[str, str]] = {}
    for candidate_id in candidate_ids:
        candidate: dict[str, str] = {}
        for dimension in REVIEW_DIMENSIONS:
            key = (candidate_id, dimension)
            values = labels.get(key, set())
            if len(values) == 1:
                candidate[dimension] = next(iter(values))
            elif key in adjudication_by_key:
                candidate[dimension] = adjudication_by_key[key]["final_label"]
        output[candidate_id] = candidate
    return output


def _validate_prerequisites(
    *,
    root: Path,
    review_root: Path,
    payload: dict[str, Any],
    manipulation_payload: dict[str, Any],
    manifest_sha256: str | None,
    slice_hash: str,
    candidate_count: int,
) -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}
    for name in ("leakage_gate", "answer_contract"):
        item = payload.get(name)
        mapping = item if isinstance(item, dict) else {}
        report_path = _resolve_evidence_path(
            root,
            review_root,
            str(mapping.get("report_path") or ""),
        )
        report = _read_json_object(report_path) if report_path else {}
        expected_hash = str(mapping.get("report_sha256") or "")
        actual_hash = _sha256_file(report_path) if report_path else None
        passed = (
            mapping.get("passed") is True
            and bool(report)
            and report.get("passed") is True
            and bool(expected_hash)
            and actual_hash == expected_hash
        )
        checks[name] = {
            "passed": passed,
            "code": (
                f"{name.upper()}_PASS"
                if passed
                else f"{name.upper()}_MISSING_OR_INVALID"
            ),
            "report_path": str(report_path) if report_path else None,
            "expected_sha256": expected_hash or None,
            "actual_sha256": actual_hash,
        }

    slice_freeze_raw = payload.get("slice_freeze")
    slice_freeze = (
        slice_freeze_raw if isinstance(slice_freeze_raw, dict) else {}
    )
    slice_passed = (
        slice_freeze.get("frozen") is True
        and slice_freeze.get("candidate_manifest_sha256")
        == manifest_sha256
        and slice_freeze.get("slice_hash") == slice_hash
        and int(slice_freeze.get("candidate_count") or -1) == candidate_count
    )
    checks["slice_freeze"] = {
        "passed": slice_passed,
        "code": (
            "SLICE_FREEZE_PASS"
            if slice_passed
            else "SLICE_FREEZE_MISSING_OR_MISMATCHED"
        ),
        "expected_slice_hash": slice_hash,
        "reported_slice_hash": slice_freeze.get("slice_hash"),
    }

    manipulation_item_raw = payload.get("manipulation_checks")
    manipulation_item = (
        manipulation_item_raw
        if isinstance(manipulation_item_raw, dict)
        else {}
    )
    manipulation_path = review_root / MANIPULATION_CHECK_FILE
    manipulation_hash = _sha256_file(manipulation_path)
    manipulation_passed = (
        manipulation_payload.get("evidence_class") == "ENGINEERING_ONLY"
        and manipulation_payload.get("candidate_manifest_sha256")
        == manifest_sha256
        and int(manipulation_payload.get("candidate_count") or -1)
        == candidate_count
        and int(manipulation_payload.get("record_count") or -1)
        == candidate_count
        and manipulation_payload.get("all_candidates_linked") is True
        and manipulation_payload.get("all_applicable_checks_passed") is True
        and manipulation_item.get("passed") is True
        and manipulation_item.get("report_sha256") == manipulation_hash
    )
    checks["manipulation_checks"] = {
        "passed": manipulation_passed,
        "code": (
            "MANIPULATION_CHECKS_PASS"
            if manipulation_passed
            else "MANIPULATION_CHECKS_MISSING_OR_FAILED"
        ),
        "report_path": str(manipulation_path),
        "expected_sha256": manipulation_item.get("report_sha256"),
        "actual_sha256": manipulation_hash,
    }
    return checks


def _exclusion_summary(
    final_labels: dict[str, dict[str, str]],
) -> dict[str, Any]:
    completed = [
        labels["exclusion_recommendation"]
        for labels in final_labels.values()
        if "exclusion_recommendation" in labels
    ]
    excluded = sum(label == "exclude" for label in completed)
    revised = sum(label == "revise" for label in completed)
    return {
        "items_with_final_recommendation": len(completed),
        "excluded_items": excluded,
        "revision_items": revised,
        "exclusion_rate": (
            round(excluded / len(completed), 6) if completed else None
        ),
    }


def _family_validity(
    candidate_rows: dict[str, dict[str, Any]],
    final_labels: dict[str, dict[str, str]],
) -> dict[str, Any]:
    by_family: dict[str, list[str]] = defaultdict(list)
    for candidate_id, row in candidate_rows.items():
        family = str(row.get("family") or "unknown")
        by_family[family].append(candidate_id)
    families: dict[str, Any] = {}
    for family, candidate_ids in sorted(by_family.items()):
        dimensions: dict[str, Any] = {}
        for dimension in REVIEW_DIMENSIONS:
            labels = [
                final_labels[candidate_id][dimension]
                for candidate_id in candidate_ids
                if dimension in final_labels.get(candidate_id, {})
            ]
            dimensions[dimension] = {
                "n": len(labels),
                "valid_rate": (
                    round(
                        sum(
                            label == PASS_LABELS[dimension]
                            for label in labels
                        )
                        / len(labels),
                        6,
                    )
                    if labels
                    else None
                ),
            }
        families[family] = {
            "candidate_count": len(candidate_ids),
            "dimensions": dimensions,
        }
    return {
        "state": "READY" if families else "BLOCKED_NO_FAMILIES",
        "families": families,
    }


def _confidence_summary(
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    by_reviewer: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        try:
            value = int(row["confidence_1_to_5"])
        except (KeyError, ValueError):
            continue
        by_reviewer[row["reviewer_id"]].append(value)
    values = [value for ratings in by_reviewer.values() for value in ratings]
    if not values:
        return {
            "state": "BLOCKED_NO_CONFIDENCE_LABELS",
            "n_ratings": 0,
            "overall_mean": None,
            "by_reviewer": {},
        }
    return {
        "state": "READY",
        "n_ratings": len(values),
        "overall_mean": round(sum(values) / len(values), 6),
        "distribution": dict(sorted(Counter(values).items())),
        "by_reviewer": {
            reviewer: {
                "n": len(ratings),
                "mean": round(sum(ratings) / len(ratings), 6),
            }
            for reviewer, ratings in sorted(by_reviewer.items())
        },
    }


def _read_csv(
    path: Path,
    *,
    required_columns: Iterable[str],
    issues: list[dict[str, str]],
) -> list[dict[str, str]]:
    if not path.exists():
        issues.append(
            _issue(
                "MISSING_REVIEW_FILE",
                str(path),
                "required canonical review file is missing",
            )
        )
        return []
    lowered_path = path.name.lower()
    if any(
        token in lowered_path
        for token in ("proxy", "synthetic", "fixture_only", "ai_review")
    ):
        issues.append(
            _issue(
                "PROXY_FILE_REJECTED",
                str(path),
                "proxy/synthetic review file rejected",
            )
        )
        return []
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])
            missing = sorted(set(required_columns) - fieldnames)
            if missing:
                issues.append(
                    _issue(
                        "MISSING_REVIEW_COLUMNS",
                        str(path),
                        f"missing columns: {', '.join(missing)}",
                    )
                )
                return []
            return [
                {
                    str(key): str(value or "").strip()
                    for key, value in row.items()
                }
                for row in reader
            ]
    except (OSError, csv.Error) as exc:
        issues.append(
            _issue(
                "UNREADABLE_REVIEW_CSV",
                str(path),
                type(exc).__name__,
            )
        )
        return []


def _read_json_object(
    path: Path,
    *,
    issues: list[dict[str, str]] | None = None,
    issue_code: str | None = None,
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        if issues is not None and issue_code is not None:
            issues.append(
                _issue(
                    issue_code,
                    str(path),
                    type(exc).__name__,
                )
            )
        return {}
    if not isinstance(payload, dict):
        if issues is not None and issue_code is not None:
            issues.append(
                _issue(
                    issue_code,
                    str(path),
                    "expected a JSON object",
                )
            )
        return {}
    return payload


def _valid_identity(value: str, pattern: re.Pattern[str]) -> bool:
    normalized = value.strip().lower()
    if (
        not normalized
        or normalized in PLACEHOLDER_TOKENS
        or any(token in normalized for token in PLACEHOLDER_TOKENS - {""})
    ):
        return False
    return pattern.fullmatch(normalized) is not None


def _valid_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return False
    return parsed.tzinfo is not None


def _contains_forbidden_provenance(values: Iterable[str]) -> bool:
    joined = " ".join(values).lower()
    return any(token in joined for token in FORBIDDEN_PROVENANCE_TOKENS)


def _blank_row(
    row: dict[str, str],
    *,
    identity_columns: Iterable[str],
) -> bool:
    return not any(row.get(column, "").strip() for column in identity_columns)


def candidate_slice_hash(
    rows: dict[str, dict[str, Any]],
) -> str:
    canonical = [
        {
            "candidate_id": candidate_id,
            "base_task_id": row.get("base_task_id"),
            "clean_instance_id": row.get("clean_instance_id"),
            "intervention_instance_id": row.get(
                "intervention_instance_id"
            ),
            "family": row.get("family"),
        }
        for candidate_id, row in sorted(rows.items())
    ]
    return stable_hash(canonical, length=64)


def _resolve_evidence_path(
    root: Path,
    review_root: Path,
    value: str,
) -> Path | None:
    if not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    review_candidate = review_root / candidate
    if review_candidate.exists():
        return review_candidate
    return root / candidate


def _blocking_issues(issues: list[dict[str, str]]) -> bool:
    return bool(issues)


def _issue(code: str, path: str, detail: str) -> dict[str, str]:
    return {
        "kind": code.lower(),
        "code": code,
        "path": path,
        "detail": detail,
        "severity": "BLOCKER",
    }


def _sha256_file(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
