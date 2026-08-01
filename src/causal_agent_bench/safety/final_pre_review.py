"""One-command final provider-free CAB pre-review hardening gate."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from causal_agent_bench.analysis.hierarchical_power import (
    validate_hierarchical_power_design,
)
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.smoke_calibration import (
    validate_smoke_and_staged_raac_plan,
)
from causal_agent_bench.safety.approval_receipt import verify_fixture_approval
from causal_agent_bench.safety.executable_reachability import (
    run_executable_reachability_check,
    run_gold_reconstruction_check,
    run_intervention_isolation_check,
    run_static_reachability_check,
)
from causal_agent_bench.safety.two_stage_review import validate_stage2_unlock

FINAL_STATE = "CAB_FINAL_PRE_REVIEW_HARDENING_COMPLETE"
PACKET_STATE = "COMPACT20_REVIEW_PACKET_EVIDENCE_VERIFIABLE"
EXTERNAL_BLOCKERS = ("HUMAN_VALIDATION_REQUIRED", "LIVE_EVIDENCE_REQUIRED")

REQUIRED_REPORTS = (
    "CAB_FINAL_PRE_REVIEW_HARDENING_REPORT.md",
    "cab_final_pre_review_handoff.md",
    "reports/final_pre_review/CAB_FINAL_PRE_REVIEW_BASELINE.md",
    "reports/final_pre_review/CAB_FINAL_PRE_REVIEW_STATE.json",
    "reports/final_pre_review/CAB_FINAL_PRE_REVIEW_LEDGER.md",
    "reports/final_pre_review/CAB_FINAL_PRE_REVIEW_DECISIONS.md",
    "reports/final_pre_review/REVIEWER_EVIDENCE_BUNDLE_REPORT.md",
    "reports/final_pre_review/TWO_STAGE_REVIEW_REPORT.md",
    "reports/final_pre_review/RECOVERY_AUTHORIZATION_REPORT.md",
    "reports/final_pre_review/EXECUTABLE_REACHABILITY_REPORT.md",
    "reports/final_pre_review/GOLD_RECONSTRUCTION_REPORT.md",
    "reports/final_pre_review/INTERVENTION_ISOLATION_REPORT.md",
    "reports/final_pre_review/CRYPTOGRAPHIC_APPROVAL_REPORT.md",
    "reports/final_pre_review/HIERARCHICAL_POWER_REPORT.md",
    "reports/final_pre_review/POWER_DESIGN_RECOMMENDATION.md",
    "reports/final_pre_review/SMOKE_CALIBRATION_READINESS.md",
    "reports/final_pre_review/STAGED_RAAC_PLAN.md",
    "reports/final_pre_review/CLEAN_RELEASE_REPORT.md",
    "reports/final_pre_review/TERMINOLOGY_AND_CLAIM_AUDIT.md",
    "reports/final_pre_review/ADVERSARIAL_AUDIT.md",
    "reports/final_pre_review/FINAL_PACKET_DRY_RUN.md",
    "reports/final_pre_review/FINAL_VALIDATION_LEDGER.md",
    "reports/final_pre_review/GITHUB_PUBLISH.md",
)


def final_pre_review_check(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    evidence = _read_json(root / "data/compact20_reviewed/reviewer_evidence/bundle_index.json")
    packet_dir = root / "data/human_validation/compact20_two_stage_review"
    packet = _read_json(packet_dir / "packet_manifest.json")
    unlock = validate_stage2_unlock(packet_dir)
    static = run_static_reachability_check(root)
    executable = run_executable_reachability_check(root)
    gold = run_gold_reconstruction_check(root)
    isolation = run_intervention_isolation_check(root)
    approval = verify_fixture_approval(root)
    power = validate_hierarchical_power_design(root)
    resources = validate_smoke_and_staged_raac_plan(root)
    recovery = _recovery_contract_check(root)
    clean_release = _read_json(root / "reports/final_pre_review/CLEAN_RELEASE_RECEIPT.json")
    adversarial = _read_json(root / "reports/final_pre_review/ADVERSARIAL_AUDIT.json")
    dry_run = _read_json(
        root / "reports/final_pre_review/fixture_dry_run/two_stage_fixture_dry_run.json"
    )
    counters = _evidence_counters(root)
    state = _read_json(root / "reports/final_pre_review/CAB_FINAL_PRE_REVIEW_STATE.json")
    workflow = root / ".github/workflows/final-pre-review-hardening.yml"
    checks = {
        "reviewer_evidence_bundles": (
            evidence.get("status") == "CAB_COMPACT_REVIEW_EVIDENCE_BUNDLES_READY"
            and evidence.get("candidate_count") == 20
            and evidence.get("gold_reconstruction_passed_count") == 20
            and evidence.get("intervention_isolation_passed_count") == 20
            and evidence.get("unsupported_fact_count") == 0
        ),
        "two_stage_packet": (
            packet.get("status") == "CAB_TWO_STAGE_HUMAN_REVIEW_READY"
            and packet.get("candidate_count") == 20
            and packet.get("stage1_gold_included") is False
            and packet.get("stage1_intended_route_included") is False
            and packet.get("stage1_scorer_included") is False
            and packet.get("stage2_locked") is True
            and packet.get("genuine_human_review_rows") == 0
            and unlock.get("passed") is False
        ),
        "recovery_authorization_v4": recovery["passed"],
        "static_reachability": static.get("passed") is True and static.get("instance_count") == 20,
        "executable_reachability": executable.get("passed") is True,
        "gold_reconstruction": gold.get("passed") is True,
        "intervention_isolation": isolation.get("passed") is True,
        "cryptographic_fixture_approval": approval.get("passed") is True
        and approval.get("approval_scope") == "fixture",
        "hierarchical_power": power.get("passed") is True,
        "smoke_and_staged_raac": resources.get("passed") is True,
        "clean_release": clean_release.get("passed") is True
        and clean_release.get("status") == "CAB_CLEAN_RELEASE_PATH_READY",
        "adversarial_audit": adversarial.get("passed") is True
        and adversarial.get("silent_critical_failure_count") == 0,
        "fixture_dry_run": dry_run.get("fixture_only") is True
        and dry_run.get("real_packet_unchanged_and_blank") is True,
        "genuine_evidence_counters_zero": all(value == 0 for value in counters.values()),
        "required_reports_present": all((root / path).is_file() for path in REQUIRED_REPORTS),
        "workflow_present": workflow.is_file(),
        "terminal_state_exact": (
            state.get("state") == FINAL_STATE
            and state.get("review_packet_state") == PACKET_STATE
            and state.get("human_validation_state") == EXTERNAL_BLOCKERS[0]
            and state.get("live_evidence_state") == EXTERNAL_BLOCKERS[1]
            and state.get("CAB_LEVEL5_COMPLETE") is False
        ),
    }
    passed = all(checks.values())
    result: dict[str, Any] = {
        "schema_version": "cab_final_pre_review_hardening_gate_v1",
        "passed": passed,
        "state": FINAL_STATE if passed else "CAB_FINAL_PRE_REVIEW_HARDENING_FAILED",
        "review_packet_state": PACKET_STATE if passed else "CHECK_FAILED",
        "human_validation_state": EXTERNAL_BLOCKERS[0],
        "live_evidence_state": EXTERNAL_BLOCKERS[1],
        "CAB_LEVEL5_COMPLETE": False,
        "checks": checks,
        "failed_checks": sorted(name for name, value in checks.items() if not value),
        "genuine_evidence": counters,
        "provider_calls_performed": 0,
        "model_calls_performed": 0,
        "scientific_execution_performed": False,
        "next_action": (
            "Recruit two genuine qualified independent reviewers, finalize and "
            "immutably commit Stage 1, unlock Stage 2, and use a separate adjudicator."
        ),
    }
    result["gate_hash"] = stable_hash(result, length=64)
    return result


def _recovery_contract_check(root: Path) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in (root / "data/compact20_reviewed/compact20_v2_instances.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    recoveries = [
        row
        for row in rows
        if row.get("condition") == "intervention"
        and row.get("intervention", {}).get("answer_contract") == "RECOVERY_ROUTE_REQUIRED"
    ]
    required = {
        "action_id",
        "action_type",
        "allowed_tool_names",
        "argument_schema",
        "preconditions",
        "failure_types",
        "success_predicate",
        "supported_fact_ids",
        "max_attempts",
        "cost",
        "terminal",
    }
    failures: list[str] = []
    for row in recoveries:
        scorer = row["intervention"]["scorer_policy"]
        contracts = scorer.get("recovery_authorizations", [])
        ids = set(scorer.get("required_recovery_actions", []))
        contract_ids = {contract.get("action_id") for contract in contracts}
        if not contracts or ids != contract_ids:
            failures.append(f"{row['instance_id']}:authorization_id_mismatch")
        for contract in contracts:
            if not required.issubset(contract):
                failures.append(f"{row['instance_id']}:missing_fields")
    return {
        "schema_version": "cab_recovery_authorization_v4_gate_v1",
        "status": "CAB_RECOVERY_AUTHORIZATION_V4_READY"
        if not failures and len(recoveries) == 5
        else "CAB_RECOVERY_AUTHORIZATION_V4_FAILED",
        "recovery_instance_count": len(recoveries),
        "failures": failures,
        "passed": not failures and len(recoveries) == 5,
    }


def _evidence_counters(root: Path) -> dict[str, int]:
    source = _read_json(root / "reports/level5_hardening/CAB_LEVEL5_HARDENING_STATE.json").get(
        "genuine_evidence", {}
    )
    adjudications = 0
    adjudication = root / "data/human_validation/compact20_two_stage_review/adjudication.csv"
    if adjudication.is_file():
        with adjudication.open(encoding="utf-8", newline="") as handle:
            adjudications = sum(
                1 for row in csv.DictReader(handle) if str(row.get("adjudicator_id") or "").strip()
            )
    return {
        "genuine_human_judgments": int(source.get("human_judgment_rows", 0)),
        "genuine_adjudications": adjudications,
        "real_model_trajectories": int(source.get("real_model_trajectories", 0)),
        "audited_real_runs": int(source.get("audited_real_runs", 0)),
        "paper_eligible_empirical_assets": int(source.get("paper_eligible_empirical_assets", 0)),
        "supported_empirical_claims": int(source.get("supported_empirical_claims", 0)),
        "external_reproductions": int(source.get("independent_external_reproductions", 0)),
        "protected_evaluator_pilots": int(source.get("protected_evaluator_pilots", 0)),
        "community_pilots": int(source.get("community_external_pilots", 0)),
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "EXTERNAL_BLOCKERS",
    "FINAL_STATE",
    "PACKET_STATE",
    "REQUIRED_REPORTS",
    "final_pre_review_check",
]
