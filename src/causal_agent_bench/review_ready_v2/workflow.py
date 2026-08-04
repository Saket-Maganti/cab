"""The complete two-stage human-review workflow, end to end.

Every step is a gate.  Stage 2 stays sealed until a validated Stage-1 commitment
exists, C10 stays ``C10_PENDING_GENUINE_REVIEW`` until genuine validated review
data exists, the reviewed slice cannot be locked before C10 passes, and model
execution cannot be authorized before the slice is locked.

Fixture receipts are stamped ``SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE`` and are
refused by every production gate, so the fixture end-to-end test can exercise the
mechanics without ever creating genuine evidence.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.common import (
    FIXTURE_MARKER,
    read_json,
    sha256_bytes,
    sha256_json,
    write_json,
)
from causal_agent_bench.review_ready_v2.qualification import (
    MIN_QUALIFICATION_RATE,
    score_qualification,
)
from causal_agent_bench.review_ready_v2.registry import enforce_active_packet
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_DIMENSIONS, REVIEW_FORM_COLUMNS

GENUINE_EVIDENCE_CLASS = "GENUINE_HUMAN_REVIEW"
FIXTURE_EVIDENCE_CLASS = FIXTURE_MARKER

GATING_DIMENSIONS = (
    "clean_solvable",
    "clean_evidence_sufficient",
    "goal_preserved",
    "single_factor_isolation",
    "preserved_invariants_hold",
    "primitive_evidence_adequate",
    "response_space_structurally_valid",
    "exclude_item",
)

STAGE2_DIMENSIONS = (
    "clean_gold_correct",
    "intervention_gold_or_policy_correct",
    "answer_contract_correct",
    "scorer_compatible",
    "route_policy_defensible",
    "exclude_item",
)

STAGE2_FORM_COLUMNS = ("reviewer_item_id", *STAGE2_DIMENSIONS, "notes")

ENUMS = {name: set(values) for name, values, _ in REVIEW_DIMENSIONS if values}
STAGE2_ENUMS = {name: {"yes", "no", "unsure"} for name in STAGE2_DIMENSIONS}


class WorkflowError(RuntimeError):
    """A workflow gate refused to proceed."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def parse_review_csv(payload: bytes, columns: tuple[str, ...]) -> dict[str, dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode()))
    if tuple(reader.fieldnames or ()) != columns:
        raise WorkflowError("the submitted form does not match the issued column layout")
    rows: dict[str, dict[str, str]] = {}
    for row in reader:
        item_id = str(row["reviewer_item_id"]).strip()
        if not item_id:
            continue
        if item_id in rows:
            raise WorkflowError(f"duplicate row for {item_id}")
        rows[item_id] = {key: str(value or "").strip() for key, value in row.items()}
    return rows


def validate_stage1_submission(
    rows: dict[str, dict[str, str]], expected_item_ids: list[str]
) -> dict[str, Any]:
    problems: list[dict[str, str]] = []
    missing = sorted(set(expected_item_ids) - set(rows))
    unexpected = sorted(set(rows) - set(expected_item_ids))
    for item_id, row in sorted(rows.items()):
        for name, allowed in ENUMS.items():
            value = row.get(name, "").casefold()
            if value not in allowed:
                problems.append({"reviewer_item_id": item_id, "column": name, "issue": "invalid_value"})
        if row.get("exclude_item", "").casefold() == "yes" and not row.get("notes"):
            problems.append({"reviewer_item_id": item_id, "column": "notes", "issue": "required"})
        if row.get("ambiguity_present", "").casefold() == "material" and not row.get("notes"):
            problems.append({"reviewer_item_id": item_id, "column": "notes", "issue": "required"})
    checks = {
        "no_missing_rows": not missing,
        "no_unexpected_rows": not unexpected,
        "no_malformed_cells": not problems,
    }
    return {
        "row_count": len(rows),
        "missing_rows": missing,
        "unexpected_rows": unexpected,
        "malformed": problems,
        "checks": checks,
        "passed": all(checks.values()),
    }


def validate_stage2_submission(
    rows: dict[str, dict[str, str]], expected_item_ids: list[str]
) -> dict[str, Any]:
    problems: list[dict[str, str]] = []
    missing = sorted(set(expected_item_ids) - set(rows))
    for item_id, row in sorted(rows.items()):
        for name, allowed in STAGE2_ENUMS.items():
            if row.get(name, "").casefold() not in allowed:
                problems.append({"reviewer_item_id": item_id, "column": name, "issue": "invalid_value"})
    checks = {"no_missing_rows": not missing, "no_malformed_cells": not problems}
    return {
        "row_count": len(rows),
        "missing_rows": missing,
        "malformed": problems,
        "checks": checks,
        "passed": all(checks.values()),
    }


@dataclass
class ReviewWorkspace:
    """Coordinator-side workflow state under the private packet root."""

    private_root: Path
    fixture: bool = False

    @property
    def receipts(self) -> Path:
        directory = self.private_root / ("fixture_receipts" if self.fixture else "receipts")
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)
        return directory

    @property
    def evidence_class(self) -> str:
        return FIXTURE_EVIDENCE_CLASS if self.fixture else GENUINE_EVIDENCE_CLASS

    def _stamp(self, payload: dict[str, Any]) -> dict[str, Any]:
        stamped = {
            **payload,
            "packet_version": PACKET_VERSION,
            "evidence_class": self.evidence_class,
            "counts_as_genuine_evidence": not self.fixture,
            "recorded_at": _now(),
        }
        stamped["receipt_sha256"] = sha256_json(stamped)
        return stamped

    def write(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        stamped = self._stamp(payload)
        path = self.receipts / f"{name}.json"
        write_json(path, stamped)
        path.chmod(0o600)
        return stamped

    def read(self, name: str) -> dict[str, Any]:
        path = self.receipts / f"{name}.json"
        if not path.is_file():
            raise WorkflowError(f"required receipt is missing: {name}")
        receipt = read_json(path)
        if not self.fixture and receipt.get("evidence_class") == FIXTURE_EVIDENCE_CLASS:
            raise WorkflowError(
                f"receipt {name} is a synthetic test fixture and cannot be used as genuine evidence"
            )
        return receipt

    def has(self, name: str) -> bool:
        return (self.receipts / f"{name}.json").is_file()

    # -- Stage 1 ----------------------------------------------------------

    def ingest_qualification(
        self, reviewer_id: str, submission: dict[str, dict[str, str]]
    ) -> dict[str, Any]:
        result = score_qualification(submission)
        if not result["qualified"]:
            raise WorkflowError(
                f"reviewer {reviewer_id} did not reach the {MIN_QUALIFICATION_RATE:.0%} "
                "qualification threshold; they cannot be assigned a review package"
            )
        return self.write(
            f"qualification_{reviewer_id}",
            {
                "receipt_kind": "reviewer_qualification",
                "reviewer_pseudonymous_id": reviewer_id,
                "rate": result["rate"],
                "threshold": MIN_QUALIFICATION_RATE,
                "qualified": True,
                "ai_assistance_declared": False,
                "conflict_of_interest_declared": False,
            },
        )

    def ingest_stage1(
        self,
        reviewer_id: str,
        payload: bytes,
        *,
        expected_item_ids: list[str],
        package_sha256: str,
    ) -> dict[str, Any]:
        if not self.has(f"qualification_{reviewer_id}"):
            raise WorkflowError(f"reviewer {reviewer_id} is not qualified; Stage-1 ingestion refused")
        rows = parse_review_csv(payload, REVIEW_FORM_COLUMNS)
        validation = validate_stage1_submission(rows, expected_item_ids)
        if not validation["passed"]:
            raise WorkflowError(f"Stage-1 submission from {reviewer_id} is malformed")
        return self.write(
            f"stage1_submission_{reviewer_id}",
            {
                "receipt_kind": "stage1_submission",
                "reviewer_pseudonymous_id": reviewer_id,
                "package_sha256": package_sha256,
                "submission_sha256": sha256_bytes(payload),
                "row_count": validation["row_count"],
                "judgements": rows,
                "validation": validation["checks"],
            },
        )

    def commit_stage1(
        self,
        *,
        reviewer_ids: tuple[str, str],
        packet_commitment: str,
        package_hashes: dict[str, str],
        review_schema_version: str,
        scientific_freeze_sha256: str,
        exact_commit: str,
    ) -> dict[str, Any]:
        enforce_active_packet(
            packet_version=PACKET_VERSION,
            commitment=packet_commitment,
            action="stage1_commitment",
            package_hashes=package_hashes,
        )
        qualifications = {rid: self.read(f"qualification_{rid}") for rid in reviewer_ids}
        submissions = {rid: self.read(f"stage1_submission_{rid}") for rid in reviewer_ids}
        if not all(row["qualified"] for row in qualifications.values()):
            raise WorkflowError("both reviewers must be qualified before Stage-1 can be committed")
        return self.write(
            "stage1_commitment",
            {
                "receipt_kind": "stage1_commitment",
                "private_packet_commitment": packet_commitment,
                "stage1_package_hashes": package_hashes,
                "qualification_receipt_hashes": {
                    rid: row["receipt_sha256"] for rid, row in sorted(qualifications.items())
                },
                "submission_hashes": {
                    rid: row["submission_sha256"] for rid, row in sorted(submissions.items())
                },
                "reviewer_pseudonymous_ids": sorted(reviewer_ids),
                "review_schema_version": review_schema_version,
                "scientific_freeze_sha256": scientific_freeze_sha256,
                "exact_commit": exact_commit,
                "stage1_final": True,
            },
        )

    # -- Stage 2 ----------------------------------------------------------

    def unlock_stage2(
        self,
        *,
        packet_commitment: str,
        scientific_freeze_sha256: str,
        exact_commit: str,
        key_available: bool,
    ) -> dict[str, Any]:
        commitment = self.read("stage1_commitment")
        checks = {
            "stage1_commitment_valid": bool(commitment.get("stage1_final")),
            "packet_commitment_matches": commitment["private_packet_commitment"] == packet_commitment,
            "freeze_hash_matches": commitment["scientific_freeze_sha256"] == scientific_freeze_sha256,
            "code_commit_matches": commitment["exact_commit"] == exact_commit,
            "both_reviewers_qualified": len(commitment["qualification_receipt_hashes"]) == 2,
            "both_submissions_present": len(commitment["submission_hashes"]) == 2,
            "external_key_available": key_available,
        }
        if not all(checks.values()):
            failed = sorted(name for name, value in checks.items() if not value)
            raise WorkflowError(f"Stage-2 unlock refused: {failed}")
        return self.write(
            "stage2_unlock", {"receipt_kind": "stage2_unlock", "checks": checks, "unlocked": True}
        )

    def ingest_stage2(
        self, reviewer_id: str, payload: bytes, *, expected_item_ids: list[str]
    ) -> dict[str, Any]:
        self.read("stage2_unlock")
        rows = parse_review_csv(payload, STAGE2_FORM_COLUMNS)
        validation = validate_stage2_submission(rows, expected_item_ids)
        if not validation["passed"]:
            raise WorkflowError(f"Stage-2 submission from {reviewer_id} is malformed")
        return self.write(
            f"stage2_submission_{reviewer_id}",
            {
                "receipt_kind": "stage2_submission",
                "reviewer_pseudonymous_id": reviewer_id,
                "submission_sha256": sha256_bytes(payload),
                "judgements": rows,
                "validation": validation["checks"],
            },
        )

    # -- adjudication and agreement ---------------------------------------

    def _paired(
        self, reviewer_ids: tuple[str, str], mappings: dict[str, dict[str, str]], stage: str
    ) -> dict[str, dict[str, dict[str, str]]]:
        by_pair: dict[str, dict[str, dict[str, str]]] = {}
        for reviewer_id in reviewer_ids:
            receipt = self.read(f"{stage}_submission_{reviewer_id}")
            mapping = mappings[reviewer_id]
            for item_id, row in receipt["judgements"].items():
                pair_id = mapping.get(item_id)
                if pair_id is None:
                    raise WorkflowError(f"unmapped reviewer item {item_id}")
                by_pair.setdefault(pair_id, {})[reviewer_id] = row
        return by_pair

    def build_disagreement_queue(
        self, *, reviewer_ids: tuple[str, str], mappings: dict[str, dict[str, str]]
    ) -> dict[str, Any]:
        paired = self._paired(reviewer_ids, mappings, "stage1")
        disputes: list[dict[str, Any]] = []
        for pair_id, rows in sorted(paired.items()):
            if len(rows) != 2:
                raise WorkflowError(f"pair {pair_id} lacks two independent judgements")
            left, right = (rows[reviewer_id] for reviewer_id in reviewer_ids)
            differing = sorted(
                dimension
                for dimension in GATING_DIMENSIONS
                if left.get(dimension, "").casefold() != right.get(dimension, "").casefold()
            )
            if differing:
                disputes.append(
                    {
                        "pair_id": pair_id,
                        "disputed_dimensions": differing,
                        "reviewer_values": {
                            reviewer_id: {
                                dimension: rows[reviewer_id].get(dimension, "")
                                for dimension in differing
                            }
                            for reviewer_id in reviewer_ids
                        },
                    }
                )
        return self.write(
            "disagreement_queue",
            {
                "receipt_kind": "disagreement_queue",
                "pair_count": len(paired),
                "disputed_pair_count": len(disputes),
                "disputes": disputes,
            },
        )

    def ingest_adjudication(
        self, *, adjudicator_id: str, decisions: list[dict[str, Any]], reviewer_ids: tuple[str, str]
    ) -> dict[str, Any]:
        queue = self.read("disagreement_queue")
        if adjudicator_id in reviewer_ids:
            raise WorkflowError("the adjudicator must be independent of both reviewers")
        disputed = {str(row["pair_id"]) for row in queue["disputes"]}
        decided = {str(row["pair_id"]) for row in decisions}
        if disputed != decided:
            raise WorkflowError("adjudication must decide exactly the disputed pairs")
        for decision in decisions:
            if not decision.get("rationale"):
                raise WorkflowError(f"adjudication for {decision['pair_id']} lacks a rationale")
        return self.write(
            "adjudication",
            {
                "receipt_kind": "adjudication",
                "adjudicator_pseudonymous_id": adjudicator_id,
                "decision_count": len(decisions),
                "decisions": [
                    {
                        **decision,
                        "reviewer_judgements": next(
                            row["reviewer_values"]
                            for row in queue["disputes"]
                            if str(row["pair_id"]) == str(decision["pair_id"])
                        ),
                    }
                    for decision in decisions
                ],
                "submission_sha256": sha256_json(decisions),
            },
        )

    def compute_agreement(
        self, *, reviewer_ids: tuple[str, str], mappings: dict[str, dict[str, str]]
    ) -> dict[str, Any]:
        paired = self._paired(reviewer_ids, mappings, "stage1")
        per_dimension: dict[str, dict[str, Any]] = {}
        for dimension in GATING_DIMENSIONS:
            agree = 0
            total = 0
            for rows in paired.values():
                left, right = (rows[reviewer_id] for reviewer_id in reviewer_ids)
                total += 1
                agree += left.get(dimension, "").casefold() == right.get(dimension, "").casefold()
            per_dimension[dimension] = {
                "agreed": agree,
                "total": total,
                "raw_agreement": round(agree / total, 4) if total else 0.0,
            }
        overall = sum(row["agreed"] for row in per_dimension.values())
        total = sum(row["total"] for row in per_dimension.values())
        return self.write(
            "agreement",
            {
                "receipt_kind": "agreement",
                "per_dimension": per_dimension,
                "overall_raw_agreement": round(overall / total, 4) if total else 0.0,
                "pair_count": len(paired),
                "prevalence_note": (
                    "Chance-corrected coefficients are reported alongside prevalence diagnostics "
                    "but are not pass thresholds, because degenerate prevalence can make them "
                    "undefined on a twenty-pair pilot."
                ),
            },
        )


def _majority(values: list[str]) -> str:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return max(sorted(counts), key=lambda key: counts[key])


def run_c10(
    workspace: ReviewWorkspace,
    *,
    contract: dict[str, Any],
    reviewer_ids: tuple[str, str],
    mappings: dict[str, dict[str, str]],
    prerequisites: dict[str, bool],
    packet_commitment: str,
    scientific_freeze_sha256: str,
) -> dict[str, Any]:
    """Evaluate C10 from genuine validated review data only."""

    enforce_active_packet(
        packet_version=PACKET_VERSION, commitment=packet_commitment, action="c10_evaluation"
    )
    commitment = workspace.read("stage1_commitment")
    agreement = workspace.read("agreement")
    adjudication = workspace.read("adjudication")
    stage1 = workspace._paired(reviewer_ids, mappings, "stage1")
    stage2_available = all(
        workspace.has(f"stage2_submission_{reviewer_id}") for reviewer_id in reviewer_ids
    )
    stage2 = (
        workspace._paired(reviewer_ids, mappings, "stage2") if stage2_available else {}
    )
    resolved = {str(row["pair_id"]) for row in adjudication["decisions"]}
    queued = {str(row["pair_id"]) for row in workspace.read("disagreement_queue")["disputes"]}

    checks = {
        "reviewer_identities_present": len(commitment["reviewer_pseudonymous_ids"]) == 2,
        "reviewers_qualified": len(commitment["qualification_receipt_hashes"]) == 2,
        "no_synthetic_fixture_evidence": not workspace.fixture,
        "full_pair_coverage": len(stage1) == int(contract.get("expected_pair_count", 20)),
        "agreement_meets_threshold": agreement["overall_raw_agreement"]
        >= float(contract["min_raw_agreement"]),
        "every_gating_dimension_meets_threshold": all(
            row["raw_agreement"] >= float(contract["min_raw_agreement"])
            for row in agreement["per_dimension"].values()
        ),
        "adjudication_resolved": queued <= resolved,
        "separate_adjudicator": adjudication["adjudicator_pseudonymous_id"] not in reviewer_ids,
        "intervention_isolation_confirmed": _dimension_pass(stage1, "single_factor_isolation"),
        "goal_preservation_confirmed": _dimension_pass(stage1, "goal_preserved"),
        "gold_and_scorer_review_complete": stage2_available
        and len(stage2) == int(contract.get("expected_pair_count", 20)),
        "packet_commitment_matches": commitment["private_packet_commitment"] == packet_commitment,
        "freeze_hash_matches": commitment["scientific_freeze_sha256"] == scientific_freeze_sha256,
        "prerequisites_satisfied": all(prerequisites.values()),
    }
    passed = all(checks.values())
    # Mechanics status exists so the fixture-only end-to-end test can prove the
    # pipeline works without ever producing a genuine C10 pass.
    mechanics = all(value for name, value in checks.items() if name != "no_synthetic_fixture_evidence")
    return {
        "schema_version": "cab_review_ready_v2_c10_report_v1",
        "claim_id": "C10",
        "status": "C10_PASS" if passed else "C10_PENDING_GENUINE_REVIEW",
        "mechanics_status": "C10_MECHANICS_PASS" if mechanics else "C10_MECHANICS_FAIL",
        "evidence_class": contract["evidence_class_on_pass"] if passed else "NO_GENUINE_EVIDENCE",
        "counts_as_genuine_evidence": passed and not workspace.fixture,
        "checks": checks,
        "failed_checks": sorted(name for name, value in checks.items() if not value),
        "agreement": agreement["per_dimension"],
        "passed": passed,
    }


def _dimension_pass(paired: dict[str, dict[str, dict[str, str]]], dimension: str) -> bool:
    return all(
        all(row.get(dimension, "").casefold() in {"yes", "partial"} for row in rows.values())
        for rows in paired.values()
    )


def build_exclusion_register(
    workspace: ReviewWorkspace,
    *,
    reviewer_ids: tuple[str, str],
    mappings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    paired = workspace._paired(reviewer_ids, mappings, "stage1")
    adjudication = workspace.read("adjudication")
    adjudicated = {
        str(row["pair_id"]): row for row in adjudication["decisions"]
    }
    included: list[str] = []
    excluded: list[dict[str, str]] = []
    for pair_id, rows in sorted(paired.items()):
        values = [row.get("exclude_item", "").casefold() for row in rows.values()]
        decision = adjudicated.get(pair_id, {}).get("resolved_values", {}).get("exclude_item")
        verdict = decision or (_majority(values) if len(set(values)) == 1 else "unresolved")
        if verdict == "yes":
            excluded.append(
                {
                    "pair_id": pair_id,
                    "reason": "reviewer_or_adjudicated_exclusion",
                    "source": "adjudication" if decision else "unanimous_reviewers",
                }
            )
        elif verdict == "unresolved":
            excluded.append({"pair_id": pair_id, "reason": "unresolved_exclusion_dispute", "source": "queue"})
        else:
            included.append(pair_id)
    return workspace.write(
        "exclusion_register",
        {
            "receipt_kind": "exclusion_register",
            "included_pair_ids": included,
            "excluded_pairs": excluded,
            "included_count": len(included),
            "excluded_count": len(excluded),
        },
    )


def lock_reviewed_slice(
    workspace: ReviewWorkspace,
    *,
    c10_report: dict[str, Any],
    packet_commitment: str,
    scorer_sha256: str,
    endpoints_sha256: str,
    analysis_plan_sha256: str,
    system_identity_sha256: str,
    scientific_freeze_sha256: str,
    exact_commit: str,
) -> dict[str, Any]:
    genuine_pass = c10_report.get("status") == "C10_PASS"
    fixture_mechanics = workspace.fixture and c10_report.get("mechanics_status") == "C10_MECHANICS_PASS"
    if not (genuine_pass or fixture_mechanics):
        raise WorkflowError("the reviewed slice cannot be locked before C10 passes")
    if genuine_pass and workspace.fixture:
        raise WorkflowError("a fixture workspace can never produce a genuine C10 pass")
    enforce_active_packet(
        packet_version=PACKET_VERSION, commitment=packet_commitment, action="slice_lock"
    )
    register = workspace.read("exclusion_register")
    adjudication = workspace.read("adjudication")
    commitment = workspace.read("stage1_commitment")
    return workspace.write(
        "slice_lock",
        {
            "receipt_kind": "reviewed_slice_lock",
            "included_pair_ids": register["included_pair_ids"],
            "excluded_pairs": register["excluded_pairs"],
            "review_receipt_hashes": commitment["submission_hashes"],
            "adjudication_receipt_sha256": adjudication["receipt_sha256"],
            "c10_report_sha256": sha256_json(c10_report),
            "scorer_sha256": scorer_sha256,
            "endpoints_sha256": endpoints_sha256,
            "analysis_plan_sha256": analysis_plan_sha256,
            "system_identity_schema_sha256": system_identity_sha256,
            "scientific_freeze_sha256": scientific_freeze_sha256,
            "private_packet_commitment": packet_commitment,
            "exact_commit": exact_commit,
            "locked": True,
        },
    )


def authorize_model_execution(
    workspace: ReviewWorkspace, *, exact_commit: str, scientific_freeze_sha256: str
) -> dict[str, Any]:
    if not workspace.has("slice_lock"):
        raise WorkflowError("model execution is blocked: no reviewed-slice lock receipt exists")
    lock = workspace.read("slice_lock")
    checks = {
        "slice_locked": bool(lock.get("locked")),
        "commit_matches_lock": lock.get("exact_commit") == exact_commit,
        "freeze_matches_lock": lock.get("scientific_freeze_sha256") == scientific_freeze_sha256,
        "evidence_class_matches_workspace": lock.get("evidence_class") == workspace.evidence_class,
        "genuine_evidence_required_in_production": workspace.fixture
        or lock.get("counts_as_genuine_evidence") is True,
        "included_slice_non_empty": bool(lock.get("included_pair_ids")),
    }
    if not all(checks.values()):
        raise WorkflowError(
            f"model execution refused: {sorted(name for name, value in checks.items() if not value)}"
        )
    return workspace.write(
        "execution_authorization",
        {"receipt_kind": "model_execution_authorization", "checks": checks, "authorized": True},
    )


def workflow_status(workspace: ReviewWorkspace) -> dict[str, Any]:
    """Public-safe status. Reports stage completion only, never review content."""

    stages = {
        "qualification_receipts": sum(
            1 for path in workspace.receipts.glob("qualification_*.json")
        ),
        "stage1_submissions": sum(
            1 for path in workspace.receipts.glob("stage1_submission_*.json")
        ),
        "stage1_committed": workspace.has("stage1_commitment"),
        "stage2_unlocked": workspace.has("stage2_unlock"),
        "stage2_submissions": sum(
            1 for path in workspace.receipts.glob("stage2_submission_*.json")
        ),
        "disagreement_queue_built": workspace.has("disagreement_queue"),
        "adjudicated": workspace.has("adjudication"),
        "agreement_computed": workspace.has("agreement"),
        "slice_locked": workspace.has("slice_lock"),
        "execution_authorized": workspace.has("execution_authorization"),
    }
    return {
        "schema_version": "cab_review_ready_v2_workflow_status_v1",
        "evidence_class": workspace.evidence_class,
        "stages": stages,
        "c10_status": "C10_PENDING_GENUINE_REVIEW",
        "model_execution": "MODEL_EXECUTION_BLOCKED",
    }


__all__ = [
    "FIXTURE_EVIDENCE_CLASS",
    "GATING_DIMENSIONS",
    "GENUINE_EVIDENCE_CLASS",
    "STAGE2_DIMENSIONS",
    "STAGE2_FORM_COLUMNS",
    "ReviewWorkspace",
    "WorkflowError",
    "authorize_model_execution",
    "build_exclusion_register",
    "lock_reviewed_slice",
    "parse_review_csv",
    "run_c10",
    "validate_stage1_submission",
    "validate_stage2_submission",
    "workflow_status",
]
