"""One-command, provider-free gate for the frozen CAB pre-run design."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import fields
from pathlib import Path
from typing import Any

from causal_agent_bench.metrics.endpoints_v3 import (
    PRIMARY_ENDPOINTS,
    SECONDARY_ENDPOINTS,
)
from causal_agent_bench.metrics.typed_final_answer import (
    SCORER_VERSION,
    TypedScoreResult,
)
from causal_agent_bench.runners.resource_planner import plan_all_scenarios

FINAL_STATE = "CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE"
EXTERNAL_BLOCKERS = ("HUMAN_VALIDATION_REQUIRED", "LIVE_EVIDENCE_REQUIRED")

REQUIRED_SCORE_FIELDS = (
    "task_completion_success",
    "safe_response_success",
    "contract_compliance",
    "answer_correct",
    "abstention_present",
    "abstention_opportunity",
    "abstention_correct",
    "false_abstention",
    "clarification_present",
    "clarification_correct",
    "refusal_present",
    "refusal_correct",
    "unavailable_tool_disclosure_present",
    "unavailable_tool_disclosure_correct",
    "recovery_plan_stated",
    "recovery_action_attempted",
    "recovery_action_succeeded",
    "task_recovered",
)

REQUIRED_REPORTS = (
    "CAB_PRE_RUN_SCIENTIFIC_HARDENING_REPORT.md",
    "cab_pre_run_scientific_hardening_handoff.md",
    "CURRENT_PROJECT_STATE.md",
    "reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_BASELINE.md",
    "reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_STATE.json",
    "reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_LEDGER.md",
    "reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_DECISIONS.md",
    "reports/pre_run_hardening/SCORER_SEMANTICS_REPAIR.md",
    "reports/pre_run_hardening/ENDPOINT_FREEZE.md",
    "reports/pre_run_hardening/INTERVENTION_REACHABILITY_REPORT.md",
    "reports/pre_run_hardening/COMPACT20_PACKET_V2_REPORT.md",
    "reports/pre_run_hardening/CONFIRMATORY_BALANCE_REPORT.md",
    "reports/pre_run_hardening/V2_EXECUTION_CANONICALIZATION.md",
    "reports/pre_run_hardening/RESOURCE_PLANNING_REPORT.md",
    "reports/pre_run_hardening/COMPACT20_POWER_PRECISION.md",
    "reports/pre_run_hardening/SCALE100_POWER_PRECISION.md",
    "reports/pre_run_hardening/SYSTEM_IDENTITY_REPORT.md",
    "reports/pre_run_hardening/TRANSFER_ARTIFACT_SCOPE_REPORT.md",
    "reports/pre_run_hardening/ANTI_REGRESSION_GATE_REPORT.md",
    "reports/pre_run_hardening/CAB_PRE_RUN_VALIDATION_LEDGER.md",
    "reports/pre_run_hardening/CAB_PRE_RUN_GITHUB_PUBLISH.md",
)


def scientific_hardening_check(repo_root: str | Path) -> dict[str, Any]:
    """Validate the frozen public design without reviews, models, or providers."""

    root = Path(repo_root).resolve()
    endpoint_spec = _read_json(root / "configs/pre_run/frozen_endpoints.json")
    compact = _read_json(root / "data/compact20_reviewed/compact20_v2_balance_report.json")
    compact_manifest = _read_json(root / "data/manifests/compact20_v2_public_manifest.json")
    packet = _read_json(
        root / "data/manifests/compact20_review_packet_v2_public_commitment.json"
    )
    reachability = _read_json(
        root / "reports/pre_run_scientific_hardening/compact20_reachability.json"
    )
    scale = _read_json(
        root / "data/manifests/scale100_confirmatory_v2_public_manifest.json"
    )
    transfer = _read_json(
        root / "data/manifests/naturalistic_transfer_v2_public_manifest.json"
    )
    power = _read_json(
        root / "reports/pre_run_hardening/POWER_PRECISION_RECOMMENDATION.json"
    )
    identity = _read_json(
        root
        / "reports/pre_run_scientific_hardening/evaluated_system_identity_frozen.json"
    )
    counters = _evidence_counters(root)
    score_fields = {field.name for field in fields(TypedScoreResult)}
    packet_dir = root / "data/human_validation/compact20_real_review"
    resource_matrix = plan_all_scenarios(root)

    compact_checks = compact_manifest.get("constraint_satisfaction_receipt") and (
        compact.get("family_counts")
        == {
            "memory_corruption": 5,
            "observation_conflict": 5,
            "tool_failure": 5,
            "tool_removal": 5,
        }
        and compact.get("unique_base_task_count", 0) >= 12
        and compact.get("anchor_count") == 4
        and compact.get("max_domain_share", 1.0) <= 0.25
        and compact.get("difficulty_counts", {}).get("easy", 0) >= 4
        and compact.get("difficulty_counts", {}).get("medium", 0) >= 6
        and compact.get("difficulty_counts", {}).get("hard", 0) >= 4
        and compact.get("difficulty_counts", {}).get("stress", 0) >= 2
        and all(len(row) >= 3 for row in compact.get("family_by_domain", {}).values())
        and all(len(row) >= 2 for row in compact.get("family_by_difficulty", {}).values())
    )
    scale_balance = scale.get("assignment_design", {})
    transfer_balance = transfer.get("assignment_design", {})
    artifact_scope = transfer.get("artifact_materialization", {})
    planner_studies = resource_matrix.get("studies", {})

    checks: dict[str, bool] = {
        "scorer_version_3": SCORER_VERSION == "3.0.0",
        "scorer_fields_distinct": set(REQUIRED_SCORE_FIELDS).issubset(score_fields),
        "endpoints_exact_and_frozen": (
            endpoint_spec.get("primary") == list(PRIMARY_ENDPOINTS)
            and endpoint_spec.get("secondary") == list(SECONDARY_ENDPOINTS)
            and endpoint_spec.get("status") == "CAB_ENDPOINTS_FROZEN_PRE_RUN"
            and endpoint_spec.get("scorer_version") == SCORER_VERSION
        ),
        "compact20_v2_constraints": bool(compact_checks),
        "compact20_old_hashes_invalidated": len(
            compact_manifest.get("prior_commitments_invalidated", [])
        )
        >= 3,
        "compact20_packet_hashes_current": (
            packet.get("prior_packet_invalidated") is True
            and packet.get("genuine_human_review_rows") == 0
            and _packet_hashes_match(packet_dir, packet.get("file_hashes", {}))
        ),
        "compact20_reachability": (
            reachability.get("passed") is True
            and reachability.get("instance_count") == 20
            and reachability.get("failed_count") == 0
        ),
        "scale_assignment_balance": _assignment_passes(scale_balance),
        "transfer_assignment_balance": _assignment_passes(transfer_balance),
        "v2_only_execution_templates": _v2_templates_pass(root),
        "resource_plans_manifest_driven": (
            {
                "compact20",
                "compact20_raac_light",
                "raac_ablations",
                "raac_equal_budget",
                "scale100",
                "scale100_raac_light",
                "transfer",
            }.issubset(planner_studies)
            and all(
                set(rows)
                == {"minimum", "planned", "conservative", "rerun_reserve"}
                for rows in planner_studies.values()
            )
        ),
        "power_assumptions_frozen": (
            power.get("assumptions_frozen_before_live_runs") is True
            and power.get("scientific_execution_performed") is False
            and 0.0 <= float(power.get("compact20_sesoi_power", -1)) <= 1.0
            and 0.0 <= float(power.get("scale100_sesoi_power", -1)) <= 1.0
        ),
        "system_identity_frozen_fail_closed": (
            identity.get("primary_lane_is_uniform") is True
            and identity.get("scientific_execution_allowed_before_binding") is False
            and bool(identity.get("frozen_contract_hash"))
            and identity.get("contract", {})
            .get("evidence_binding", {})
            .get("scorer_version")
            == SCORER_VERSION
        ),
        "artifact_rich_synthetic_transfer": (
            transfer.get("canonical_study_name") == "artifact_rich_synthetic_transfer"
            and artifact_scope.get("artifact_class") == "artifact_rich_synthetic"
            and artifact_scope.get("bundle_count") == 60
            and artifact_scope.get("artifact_file_count", 0) > 0
            and artifact_scope.get("all_gold_derivations_match") is True
            and artifact_scope.get("real_world_origin_claimed") is False
        ),
        "canonical_guidance": _guidance_passes(root),
        "required_reports_present": all((root / path).is_file() for path in REQUIRED_REPORTS),
        "genuine_evidence_counters_zero": all(value == 0 for value in counters.values()),
        "public_private_boundary": _public_private_boundary_passes(scale, transfer),
    }
    passed = all(checks.values())
    return {
        "schema_version": "cab_pre_run_scientific_hardening_gate_v1",
        "passed": passed,
        "state": FINAL_STATE if passed else "PRE_RUN_SCIENTIFIC_HARDENING_CHECK_FAILED",
        "checks": checks,
        "failed_checks": sorted(name for name, value in checks.items() if not value),
        "genuine_evidence": counters,
        "external_blockers": list(EXTERNAL_BLOCKERS),
        "scientific_execution_performed": False,
        "provider_calls_performed": 0,
        "next_action": (
            "Recruit and onboard two genuine qualified independent Compact-20 reviewers "
            "using the regenerated packet, plus a separate adjudicator."
        ),
    }


def _assignment_passes(payload: dict[str, Any]) -> bool:
    checks = payload.get("checks", {})
    family_difficulty = payload.get("family_by_difficulty", {})
    family_domain = payload.get("family_by_domain", {})
    difficulty_v = payload.get(
        "family_difficulty_cramers_v",
        family_difficulty.get("cramers_v", 1.0)
        if isinstance(family_difficulty, dict)
        else 1.0,
    )
    domain_v = payload.get(
        "family_domain_cramers_v",
        family_domain.get("cramers_v", 1.0)
        if isinstance(family_domain, dict)
        else 1.0,
    )
    return (
        payload.get("passed") is True
        and difficulty_v <= payload.get("association_threshold", 0.0)
        and domain_v <= payload.get("association_threshold", 0.0)
        and bool(checks)
        and all(checks.values())
        and bool(payload.get("deterministic_receipt"))
    )


def _packet_hashes_match(packet_dir: Path, hashes: Any) -> bool:
    if not isinstance(hashes, dict) or not hashes:
        return False
    return all(
        (packet_dir / name).is_file()
        and _sha256_file(packet_dir / name) == expected
        for name, expected in hashes.items()
    )


def _v2_templates_pass(root: Path) -> bool:
    required = (
        "configs/iclr/scale100_v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml",
        "configs/iclr/artifact_rich_transfer_v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml",
    )
    if not all((root / path).is_file() for path in required):
        return False
    return all(
        "SUPERSEDED" in (root / path).read_text(encoding="utf-8")
        for path in (
            "configs/generate_main500_confirmatory_v1.yaml",
            "configs/generate_naturalistic_transfer_v1.yaml",
            "configs/generate_scale100_confirmatory_v1.yaml",
        )
    )


def _guidance_passes(root: Path) -> bool:
    current = root / "CURRENT_PROJECT_STATE.md"
    if not current.is_file():
        return False
    body = current.read_text(encoding="utf-8")
    if FINAL_STATE not in body or any(blocker not in body for blocker in EXTERNAL_BLOCKERS):
        return False
    return all(
        "SUPERSEDED_BY: CURRENT_PROJECT_STATE.md"
        in (root / name).read_text(encoding="utf-8")
        for name in ("MASTER_STATUS.md", "PROJECT_STATUS.md", "NEXT_STEPS.md")
    )


def _public_private_boundary_passes(
    scale: dict[str, Any], transfer: dict[str, Any]
) -> bool:
    return all(
        payload.get("contains_task_text") is False
        and payload.get("contains_answers") is False
        and payload.get("contains_intervention_payloads") is False
        and payload.get("private_payload_root_must_be_ignored") is True
        and payload.get("scientific_execution_allowed") is False
        for payload in (scale, transfer)
    )


def _evidence_counters(root: Path) -> dict[str, int]:
    state = _read_json(root / "reports/level5_hardening/CAB_LEVEL5_HARDENING_STATE.json")
    evidence = state.get("genuine_evidence", {})
    adjudication_path = root / "data/human_validation/compact20_real_review/adjudication.csv"
    adjudications = 0
    if adjudication_path.is_file():
        with adjudication_path.open(encoding="utf-8", newline="") as handle:
            adjudications = sum(
                1
                for row in csv.DictReader(handle)
                if any(
                    str(row.get(key) or "").strip()
                    for key in ("final_label", "adjudicator_id", "rationale", "timestamp")
                )
            )
    return {
        "genuine_human_judgments": int(evidence.get("human_judgment_rows", 0)),
        "genuine_adjudications": adjudications,
        "real_model_trajectories": int(evidence.get("real_model_trajectories", 0)),
        "audited_real_runs": int(evidence.get("audited_real_runs", 0)),
        "paper_eligible_empirical_assets": int(
            evidence.get("paper_eligible_empirical_assets", 0)
        ),
        "supported_empirical_claims": int(evidence.get("supported_empirical_claims", 0)),
        "external_reproductions": int(
            evidence.get("independent_external_reproductions", 0)
        ),
        "protected_evaluator_pilots": int(evidence.get("protected_evaluator_pilots", 0)),
        "community_pilots": int(evidence.get("community_external_pilots", 0)),
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "EXTERNAL_BLOCKERS",
    "FINAL_STATE",
    "REQUIRED_REPORTS",
    "REQUIRED_SCORE_FIELDS",
    "scientific_hardening_check",
]
