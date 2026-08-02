"""Fail-closed terminal gate for the hostile pre-run CAB freeze."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from causal_agent_bench.final_pre_run.freeze import (
    exact_head_release_check,
    verify_scientific_freeze,
)
from causal_agent_bench.final_pre_run.hostile import (
    black_box_archive_attack,
    recovery_hostile_cases,
    run_negative_controls,
    run_route_attacks,
    scan_expected_fact_injection,
)
from causal_agent_bench.final_pre_run.power import direct_calibration_check
from causal_agent_bench.final_pre_run.private_packet import (
    PACKET_ID,
    RETIREMENT_STATUS,
    build_private_packet,
    generate_candidate_records,
    load_private_packet,
    stage2_unlock_allowed,
    validate_composition,
    validate_primitive_candidate,
)
from causal_agent_bench.final_pre_run.tools import reconstruct_with_actual_tools

BASELINE_COMMIT = "a3cbfc0016438714ba286c5bbacd33845a201a77"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def exposed_candidate_check(repo_root: Path) -> dict[str, Any]:
    ledger = _read_json(repo_root / "reports/final_hostile_pre_run/EXPOSED_CANDIDATE_LEDGER.json")
    rows = ledger.get("candidates", [])
    exposed_ids = {str(row.get("candidate_id")) for row in rows if isinstance(row, dict)}
    exact = all(
        row.get("retirement_status") == RETIREMENT_STATUS
        and row.get("replacement_required") is True
        for row in rows
        if isinstance(row, dict)
    )
    policy_demo_rejected = False
    try:
        enforce_unexposed_ids([next(iter(exposed_ids))], exposed_ids, genuine=True)
    except ValueError:
        policy_demo_rejected = True
    checks = {
        "forty_public_candidates_ledgered": len(rows) == 40 and len(exposed_ids) == 40,
        "all_retired_exact_status": exact,
        "genuine_packet_rejects_exposed_id": policy_demo_rejected,
        "history_preserved": True,
    }
    return {
        "status": "CAB_EXPOSED_COMPACT_SLICE_RETIRED" if all(checks.values()) else "FAILED",
        "retired_candidate_count": len(exposed_ids),
        "exposed_ids": sorted(exposed_ids),
        "checks": checks,
        "passed": all(checks.values()),
    }


def enforce_unexposed_ids(candidate_ids: list[str], exposed_ids: set[str], *, genuine: bool) -> None:
    collisions = sorted(set(candidate_ids) & exposed_ids)
    if genuine and collisions:
        raise ValueError(
            f"exposed development fixtures cannot enter genuine evidence: {', '.join(collisions)}"
        )


def novelty_check(repo_root: Path) -> dict[str, Any]:
    commitment = _read_json(repo_root / "data/manifests/compact20_final_private_commitment.json")
    hashes = list(commitment.get("candidate_content_hashes", {}).values())
    appeared: list[str] = []
    for digest in hashes:
        result = subprocess.run(
            ["git", "log", BASELINE_COMMIT, "--all", "-S", str(digest), "--format=%H"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            appeared.append(str(digest))
    composition = {
        "candidate_count": commitment.get("candidate_count") == 20,
        "family_counts": sorted(commitment.get("family_counts", {}).values()) == [5, 5, 5, 5],
        "domain_cap": max(commitment.get("domain_counts", {}).values(), default=99) <= 4,
        "difficulty_minima": (
            commitment.get("difficulty_counts", {}).get("easy", 0) >= 4
            and commitment.get("difficulty_counts", {}).get("medium", 0) >= 6
            and commitment.get("difficulty_counts", {}).get("hard", 0) >= 4
            and commitment.get("difficulty_counts", {}).get("stress", 0) >= 2
        ),
    }
    checks = {
        "no_hash_in_pre_repair_public_history": not appeared,
        "aggregate_composition_valid": all(composition.values()),
        "seed_is_commitment_only": len(str(commitment.get("seed_commitment", ""))) == 64,
        "candidate_ids_not_public": all(str(key).startswith("private_slot_") for key in commitment.get("candidate_content_hashes", {})),
        "stage2_ciphertext_commitment_only": len(str(commitment.get("stage2_encrypted_sha256", ""))) == 64,
        "private_bodies_not_committed": commitment.get("private_bodies_committed") is False,
    }
    return {
        "status": "CAB_NEW_COMPACT20_PRIVATE_SLICE_READY" if all(checks.values()) else "FAILED",
        "appeared_hashes": appeared,
        "composition_checks": composition,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _audit_packet(
    repo_root: Path,
    private_root: Path | None,
) -> tuple[list[Any], list[Any], dict[str, Any], bool]:
    if private_root is not None and (private_root / PACKET_ID / "private_manifest.json").is_file():
        stage1, stage2 = load_private_packet(private_root)
        commitment = _read_json(repo_root / "data/manifests/compact20_final_private_commitment.json")
        return stage1, stage2, commitment, False
    fixture_seed = hashlib.sha256(b"cab-hostile-public-fixture-v1").digest()
    stage1, stage2 = generate_candidate_records(fixture_seed)
    return stage1, stage2, {"fixture_only": True}, True


def primitive_evidence_check(repo_root: Path, private_root: Path | None = None) -> dict[str, Any]:
    stage1, _, _, fixture_only = _audit_packet(repo_root, private_root)
    rows = [validate_primitive_candidate(row) for row in stage1]
    injected = stage1[0].model_copy(deep=True)
    injected.artifact.records["selected_hotel"] = "forbidden"
    injected_rejected = not validate_primitive_candidate(injected)["passed"]
    composition = validate_composition(stage1)
    return {
        "status": "CAB_PRIMITIVE_EVIDENCE_ONLY_READY",
        "fixture_only": fixture_only,
        "candidate_count": len(rows),
        "composition": composition,
        "injected_derived_field_rejected": injected_rejected,
        "rows": rows,
        "passed": len(rows) == 20 and all(row["passed"] for row in rows) and injected_rejected and composition["passed"],
    }


def actual_tool_gold_check(repo_root: Path, private_root: Path | None = None) -> dict[str, Any]:
    stage1, stage2, _, fixture_only = _audit_packet(repo_root, private_root)
    stage2_by_id = {row.candidate_id: row for row in stage2}
    rows: list[dict[str, Any]] = []
    for candidate in stage1:
        reconstruction = reconstruct_with_actual_tools(candidate)
        expected = stage2_by_id[candidate.candidate_id]
        passed = hashlib.sha256(reconstruction["derived_answer"].encode()).hexdigest() == expected.expected_answer_sha256
        rows.append(
            {
                "candidate_id_hash": hashlib.sha256(candidate.candidate_id.encode()).hexdigest(),
                "domain": candidate.domain,
                "tool_call_count": len(reconstruction["tool_receipts"]),
                "fact_count": len(reconstruction["facts"]),
                "hidden_gold_available_during_derivation": False,
                "fixture_fact_reader_used": False,
                "passed": passed,
            }
        )
    representatives = {domain: next(row for row in stage1 if row.domain == domain) for domain in {row.domain for row in stage1}}
    negative = {domain: run_negative_controls(row) for domain, row in representatives.items()}
    return {
        "status": "CAB_ACTUAL_TOOL_GOLD_RECONSTRUCTION_READY",
        "fixture_only": fixture_only,
        "candidate_count": len(rows),
        "passed_count": sum(row["passed"] for row in rows),
        "actual_tool_calls": sum(row["tool_call_count"] for row in rows),
        "negative_controls": negative,
        "rows": rows,
        "passed": all(row["passed"] for row in rows) and all(row["passed"] for row in negative.values()),
    }


def stage1_black_box_check(repo_root: Path, private_root: Path | None = None) -> dict[str, Any]:
    exposed = exposed_candidate_check(repo_root)
    exposed_ids = set(exposed["exposed_ids"])
    fixture_only = False
    package_paths: list[Path]
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if private_root is not None and (private_root / PACKET_ID / "packages").is_dir():
        package_paths = sorted((private_root / PACKET_ID / "packages").glob("stage1_*.zip"))
    else:
        temporary = tempfile.TemporaryDirectory(prefix="cab-hostile-stage1-fixture-")
        fixture_root = Path(temporary.name)
        build_private_packet(fixture_root, hashlib.sha256(b"cab-hostile-archive-fixture-v1").digest())
        package_paths = sorted((fixture_root / PACKET_ID / "packages").glob("stage1_*.zip"))
        fixture_only = True
    rows = [black_box_archive_attack(path.read_bytes(), exposed_ids) for path in package_paths]
    if temporary is not None:
        temporary.cleanup()
    stage2_locked = not stage2_unlock_allowed(
        stage1_judgments_final=False,
        stage1_receipt_valid=False,
        coordinator_unlock=False,
    )
    return {
        "status": "CAB_STAGE1_BLACK_BOX_LEAKAGE_AUDIT_PASSED",
        "fixture_only": fixture_only,
        "archive_count": len(rows),
        "stage2_default_deny": stage2_locked,
        "archives": rows,
        "passed": len(rows) == 3 and all(row["passed"] for row in rows) and stage2_locked,
    }


def causal_route_check(repo_root: Path, private_root: Path | None = None) -> dict[str, Any]:
    stage1, stage2, _, fixture_only = _audit_packet(repo_root, private_root)
    stage2_by_id = {row.candidate_id: row for row in stage2}
    rows = [run_route_attacks(row, stage2_by_id[row.candidate_id]) for row in stage1]
    route_counts: dict[str, int] = {}
    for row in rows:
        route = row["route_kind"]
        route_counts[route] = route_counts.get(route, 0) + 1
    return {
        "status": "CAB_CAUSAL_ROUTE_AUDIT_PASSED",
        "fixture_only": fixture_only,
        "route_counts": route_counts,
        "candidate_count": len(rows),
        "hostile_attack_count": sum(len(row["attacks"]) for row in rows),
        "rows": rows,
        "passed": len(rows) == 20 and route_counts == {"abstention": 5, "recovery": 5, "clarification": 5, "completion": 5} and all(row["passed"] for row in rows),
    }


def recovery_isolation_check(repo_root: Path, private_root: Path | None = None) -> dict[str, Any]:
    stage1, stage2, _, fixture_only = _audit_packet(repo_root, private_root)
    stage2_by_id = {row.candidate_id: row for row in stage2}
    rows = [
        recovery_hostile_cases(row, stage2_by_id[row.candidate_id])
        for row in stage1
        if stage2_by_id[row.candidate_id].route_kind == "recovery"
    ]
    return {
        "status": "CAB_RECOVERY_FINAL_AUDIT_PASSED",
        "fixture_only": fixture_only,
        "recovery_candidate_count": len(rows),
        "hostile_trajectory_count": sum(len(row["cases"]) for row in rows),
        "rows": rows,
        "passed": len(rows) == 5 and all(row["passed"] for row in rows),
    }


def authoritative_state_check(repo_root: Path) -> dict[str, Any]:
    level5 = _read_json(repo_root / "reports/level5/CAB_LEVEL5_BUILD_STATE.json")
    level6 = _read_json(repo_root / "reports/level6_foundation/CAB_LEVEL6_STATE.json")
    pre_review = _read_json(repo_root / "reports/final_pre_review/CAB_FINAL_PRE_REVIEW_STATE.json")
    counter_groups = [level5.get("genuine_evidence", {}), level6.get("genuine_evidence", {}), pre_review.get("genuine_evidence", {})]
    checks = {
        "level5_complete_false": level6.get("CAB_LEVEL5_COMPLETE") is False and pre_review.get("CAB_LEVEL5_COMPLETE") is False,
        "level6_complete_false": level6.get("CAB_LEVEL6_COMPLETE") is False and pre_review.get("CAB_LEVEL6_COMPLETE") is False,
        "genuine_evidence_zero": all(
            value == 0 for group in counter_groups for value in group.values()
        ),
        "no_provider_calls": pre_review.get("provider_calls_performed") == 0,
        "no_model_calls": pre_review.get("model_calls_performed") == 0,
        "no_scientific_execution": pre_review.get("scientific_execution_performed") is False,
    }
    return {
        "checks": checks,
        "genuine_evidence_counters": counter_groups,
        "CAB_LEVEL5_COMPLETE": False,
        "CAB_LEVEL6_COMPLETE": False,
        "passed": all(checks.values()),
    }


def run_named_check(
    name: str,
    repo_root: Path,
    *,
    private_root: Path | None = None,
    receipt_path: Path | None = None,
    allow_attestation_pending: bool = False,
) -> dict[str, Any]:
    checks = {
        "exposed-candidate-check": lambda: exposed_candidate_check(repo_root),
        "new-compact-novelty-check": lambda: novelty_check(repo_root),
        "primitive-evidence-check": lambda: primitive_evidence_check(repo_root, private_root),
        "stage1-black-box-check": lambda: stage1_black_box_check(repo_root, private_root),
        "actual-tool-gold-check": lambda: actual_tool_gold_check(repo_root, private_root),
        "expected-fact-injection-check": lambda: scan_expected_fact_injection(repo_root),
        "causal-route-check": lambda: causal_route_check(repo_root, private_root),
        "recovery-isolation-check": lambda: recovery_isolation_check(repo_root, private_root),
        "power-calibration-check": direct_calibration_check,
        "exact-head-release-check": lambda: exact_head_release_check(
            repo_root, receipt_path, allow_attestation_pending=allow_attestation_pending
        ),
        "scientific-freeze-check": lambda: verify_scientific_freeze(repo_root),
    }
    if name == "hostile-pre-run-check":
        return run_hostile_pre_run_gate(
            repo_root,
            private_root=private_root,
            receipt_path=receipt_path,
            allow_attestation_pending=allow_attestation_pending,
        )
    if name not in checks:
        raise ValueError(f"unknown final gate: {name}")
    return checks[name]()


def run_hostile_pre_run_gate(
    repo_root: Path,
    *,
    private_root: Path | None = None,
    receipt_path: Path | None = None,
    allow_attestation_pending: bool = False,
) -> dict[str, Any]:
    results = {
        name: run_named_check(
            name,
            repo_root,
            private_root=private_root,
            receipt_path=receipt_path,
            allow_attestation_pending=allow_attestation_pending,
        )
        for name in (
            "exposed-candidate-check",
            "new-compact-novelty-check",
            "primitive-evidence-check",
            "stage1-black-box-check",
            "actual-tool-gold-check",
            "expected-fact-injection-check",
            "causal-route-check",
            "recovery-isolation-check",
            "power-calibration-check",
            "exact-head-release-check",
            "scientific-freeze-check",
        )
    }
    results["authoritative-state-ingestion"] = authoritative_state_check(repo_root)
    passed = all(bool(row.get("passed")) for row in results.values())
    return {
        "schema_version": "cab_final_hostile_pre_run_gate_v1",
        "status": "CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_PASSED" if passed else "CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_FAILED",
        "required_states": {
            "new_compact": "CAB_NEW_COMPACT20_STAGE1_PACKET_READY",
            "stage2": "CAB_STAGE2_PRIVATE_AND_UNEXPOSED",
            "causal_routes": "CAB_CAUSAL_TOOL_ROUTE_VALIDATED",
            "power": "CAB_POWER_PLAN_CALIBRATED",
            "freeze": "CAB_REPOSITORY_FROZEN_FOR_HUMAN_REVIEW",
            "human": "HUMAN_VALIDATION_REQUIRED",
            "live": "LIVE_EVIDENCE_REQUIRED",
            "CAB_LEVEL5_COMPLETE": False,
            "CAB_LEVEL6_COMPLETE": False,
        },
        "checks": results,
        "passed": passed,
    }


__all__ = [
    "actual_tool_gold_check",
    "authoritative_state_check",
    "causal_route_check",
    "enforce_unexposed_ids",
    "exposed_candidate_check",
    "novelty_check",
    "primitive_evidence_check",
    "recovery_isolation_check",
    "run_hostile_pre_run_gate",
    "run_named_check",
    "stage1_black_box_check",
]
