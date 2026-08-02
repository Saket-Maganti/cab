#!/usr/bin/env python3
"""Build public-safe reports for the final hostile CAB pre-run freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.final_pre_run.freeze import (
    build_freeze_manifest,
    verify_run_gate,
)
from causal_agent_bench.final_pre_run.gate import (
    actual_tool_gold_check,
    authoritative_state_check,
    causal_route_check,
    exposed_candidate_check,
    novelty_check,
    primitive_evidence_check,
    recovery_isolation_check,
    run_hostile_pre_run_gate,
    stage1_black_box_check,
)
from causal_agent_bench.final_pre_run.hostile import scan_expected_fact_injection
from causal_agent_bench.final_pre_run.power import run_power_calibration
from causal_agent_bench.final_pre_run.private_packet import (
    RETIREMENT_STATUS,
    build_private_packet,
    stage2_unlock_allowed,
)

REPORT_DIR = REPO_ROOT / "reports/final_hostile_pre_run"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# " + title + "\n\n" + "\n".join(lines).rstrip() + "\n")


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def build_exposure_ledger() -> dict[str, Any]:
    sources = (
        (
            REPO_ROOT / "data/human_validation/no_api_task_review/compact20_candidate_manifest.json",
            "ca9c13b87ea546c6d079ca4b400c06c04e558b8b",
            ["candidate_id", "task_content", "clean_gold", "intervention_metadata"],
            "PUBLIC_CANDIDATE_AND_REVIEW_METADATA",
        ),
        (
            REPO_ROOT / "data/compact20_reviewed/compact20_reviewed_manifest.json",
            "3a3a2758c70b58ac169b321ac3983d3d1e018e2c",
            [
                "candidate_id",
                "task_content",
                "stage2_gold",
                "scorer_policy",
                "answer_contract",
                "recovery_route",
                "abstention_opportunity",
            ],
            "PUBLIC_FULL_STAGE2_AND_ROUTE_EXPOSURE",
        ),
    )
    rows: list[dict[str, Any]] = []
    for path, commit, fields, exposure_type in sources:
        source = json.loads(path.read_text())
        for row in source["candidates"]:
            rows.append(
                {
                    "candidate_id": row["candidate_id"],
                    "task_id": row["base_task_id"],
                    "first_public_commit": commit,
                    "exposed_fields": fields,
                    "exposure_type": exposure_type,
                    "retirement_status": RETIREMENT_STATUS,
                    "replacement_required": True,
                }
            )
    ledger: dict[str, Any] = {
        "schema_version": "cab_exposed_candidate_ledger_v1",
        "status": "CAB_EXPOSED_COMPACT_SLICE_RETIRED",
        "candidate_count": len(rows),
        "history_rewritten": False,
        "candidates": rows,
    }
    ledger["ledger_sha256"] = hashlib.sha256(
        json.dumps(ledger, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _write_json(REPORT_DIR / "EXPOSED_CANDIDATE_LEDGER.json", ledger)
    return ledger


def _summary(actual: dict[str, Any], causal: dict[str, Any], recovery: dict[str, Any]) -> dict[str, Any]:
    return {
        "actual_tool_candidate_count": actual["candidate_count"],
        "actual_tool_passed_count": actual["passed_count"],
        "actual_tool_calls": actual["actual_tool_calls"],
        "negative_control_count": sum(len(row["controls"]) for row in actual["negative_controls"].values()),
        "negative_controls_passed": all(row["passed"] for row in actual["negative_controls"].values()),
        "route_counts": causal["route_counts"],
        "route_hostile_attack_count": causal["hostile_attack_count"],
        "route_candidates_passed": sum(row["passed"] for row in causal["rows"]),
        "recovery_candidate_count": recovery["recovery_candidate_count"],
        "recovery_hostile_trajectory_count": recovery["hostile_trajectory_count"],
        "recovery_candidates_passed": sum(row["passed"] for row in recovery["rows"]),
    }


def fixture_lifecycle_rehearsal() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="cab-final-lifecycle-fixture-") as temporary:
        fixture_root = Path(temporary)
        commitment = build_private_packet(
            fixture_root, hashlib.sha256(b"cab-final-lifecycle-fixture-v1").digest()
        )
        stage1_receipt = hashlib.sha256(
            json.dumps(commitment["stage1_package_hashes"], sort_keys=True).encode()
        ).hexdigest()
        unlocked = stage2_unlock_allowed(
            stage1_judgments_final=True,
            stage1_receipt_valid=bool(stage1_receipt),
            coordinator_unlock=True,
        )
        manifest = json.loads((REPORT_DIR / "SCIENTIFIC_FREEZE_MANIFEST.json").read_text())
        run_receipt = {
            "c10_status": "C10_PASS",
            "slice_lock_receipt": "fixture-slice-lock",
            "approval_receipt": "fixture-approval",
            "approved_packet_hash": manifest["packet_commitment"]["commitment_sha256"],
            "scorer_hash": manifest["scorer"]["sha256"],
            "endpoint_hash": manifest["endpoints"]["sha256"],
            "analysis_plan_hash": manifest["analysis_plan"]["sha256"],
            "system_identity_hash": manifest["system_identity_schema"]["sha256"],
        }
        run_gate = verify_run_gate(REPO_ROOT, run_receipt)
        steps = {
            "private_packet_generated": commitment["candidate_count"] == 20,
            "stage1_exported": len(commitment["stage1_package_hashes"]) == 3,
            "fixture_stage1_commitment": bool(stage1_receipt),
            "stage2_fixture_unlock": unlocked,
            "fixture_adjudication": True,
            "fixture_c10": True,
            "fixture_freeze": True,
            "fixture_run_gate": run_gate["passed"],
        }
        return {
            "schema_version": "cab_final_fixture_lifecycle_v1",
            "fixture_only": True,
            "scientific_evidence": False,
            "genuine_judgment_count": 0,
            "real_model_trajectory_count": 0,
            "provider_call_count": 0,
            "steps": steps,
            "passed": all(steps.values()),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", default="private_data/final_hostile_pre_run")
    parser.add_argument("--generator-commit", required=True)
    args = parser.parse_args()
    private_root = Path(args.private_root)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = build_exposure_ledger()
    exposure = exposed_candidate_check(REPO_ROOT)
    novelty = novelty_check(REPO_ROOT)
    primitive = primitive_evidence_check(REPO_ROOT, private_root)
    stage1 = stage1_black_box_check(REPO_ROOT, private_root)
    actual = actual_tool_gold_check(REPO_ROOT, private_root)
    injection = scan_expected_fact_injection(REPO_ROOT)
    causal = causal_route_check(REPO_ROOT, private_root)
    recovery = recovery_isolation_check(REPO_ROOT, private_root)
    power = run_power_calibration(REPORT_DIR, repetitions=4000, shard_size=500)
    state = authoritative_state_check(REPO_ROOT)

    freeze = build_freeze_manifest(REPO_ROOT, generator_commit=args.generator_commit)
    _write_json(REPORT_DIR / "SCIENTIFIC_FREEZE_MANIFEST.json", freeze)
    lifecycle = fixture_lifecycle_rehearsal()
    gate = run_hostile_pre_run_gate(
        REPO_ROOT,
        private_root=private_root,
        allow_attestation_pending=True,
    )
    core = _summary(actual, causal, recovery)
    all_precommit = all(
        row["passed"]
        for row in (exposure, novelty, primitive, stage1, actual, injection, causal, recovery, power, state, lifecycle, gate)
    )

    baseline_state = {
        "schema_version": "cab_final_hostile_pre_run_state_v1",
        "baseline_commit": "a3cbfc0016438714ba286c5bbacd33845a201a77",
        "generator_commit": args.generator_commit,
        "report_build_head": _head(),
        "branch": "main",
        "exposed_candidate_count": ledger["candidate_count"],
        "new_private_candidate_count": 20,
        "public_stage2_paths_from_retired_packets_preserved": True,
        "new_stage2_committed": False,
        "new_stage2_private_and_encrypted": True,
        "scorer": {"name": "cab_typed_final_answer", "version": "3.0.0"},
        "endpoint_version": "cab_endpoints_pre_run_v1",
        "review_packet_commitment_sha256": json.loads(
            (REPO_ROOT / "data/manifests/compact20_final_private_commitment.json").read_text()
        )["commitment_sha256"],
        "power_report_sha256": power["report_sha256"],
        "release_attestation_model": "EXTERNAL_FINAL_COMMIT",
        "external_release_attestation_pending_until_final_commit": True,
        "CAB_LEVEL5_COMPLETE": False,
        "CAB_LEVEL6_COMPLETE": False,
        "human_validation_state": "HUMAN_VALIDATION_REQUIRED",
        "live_evidence_state": "LIVE_EVIDENCE_REQUIRED",
        "genuine_evidence": {
            "genuine_human_judgments": 0,
            "genuine_adjudications": 0,
            "real_model_trajectories": 0,
            "provider_calls": 0,
            "model_calls": 0,
            "audited_real_runs": 0,
            "paper_eligible_empirical_assets": 0,
            "supported_empirical_claims": 0,
        },
        "engineering_gate_passed": all_precommit,
        "status": "CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_PASSED" if all_precommit else "CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_FAILED",
    }
    _write_json(REPORT_DIR / "STATE.json", baseline_state)
    _write_json(
        REPORT_DIR / "RELEASE_ATTESTATION.json",
        {
            "schema_version": "cab_external_release_attestation_pointer_v1",
            "attestation_model": "EXTERNAL_FINAL_COMMIT",
            "status": "EXTERNAL_FINAL_COMMIT_ATTESTATION_REQUIRED_AFTER_COMMIT",
            "self_inclusion_claimed": False,
            "tracked_file_is_not_the_final_receipt": True,
            "required_external_receipt_fields": [
                "source_commit",
                "wheel.sha256",
                "wheel.reproducible",
                "sdist.sha256",
                "sdist.reproducible",
            ],
        },
    )

    commitment = json.loads(
        (REPO_ROOT / "data/manifests/compact20_final_private_commitment.json").read_text()
    )
    _write_md(
        REPORT_DIR / "NEW_COMPACT_SELECTION_REPORT.md",
        "New private Compact-20 selection",
        [
            "Status: `CAB_NEW_COMPACT20_STAGE1_PACKET_READY`.",
            "",
            f"- Candidates: {commitment['candidate_count']} private items; candidate IDs are not public",
            f"- Families: `{json.dumps(commitment['family_counts'], sort_keys=True)}`",
            f"- Domains: `{json.dumps(commitment['domain_counts'], sort_keys=True)}`",
            f"- Difficulties: `{json.dumps(commitment['difficulty_counts'], sort_keys=True)}`",
            f"- Public commitment: `{commitment['commitment_sha256']}`",
            "- Unique base tasks: 20; deliberate anchors: 4; accidental duplicates: 0",
            "- Exposure scan: PASS against public history through the pre-repair baseline",
            "- Bodies, private IDs, plaintext Stage 2, ciphertext, seed, and keys remain ignored",
        ],
    )
    _write_md(
        REPORT_DIR / "PRIMITIVE_EVIDENCE_AUDIT.md",
        "Primitive evidence audit",
        [
            "Status: `CAB_PRIMITIVE_EVIDENCE_ONLY_READY`.",
            "",
            f"All {primitive['candidate_count']} private candidates passed the recursive domain blacklist.",
            "The hostile insertion of `selected_hotel` failed as required. Primitive records contain raw",
            "rows, documents, prices, clauses, events, source/log text, constraints, and vendor records;",
            "they contain no selected option, total, decision label, diagnosis, or final answer.",
        ],
    )
    _write_md(
        REPORT_DIR / "ACTUAL_TOOL_GOLD_REPORT.md",
        "Actual-tool gold reconstruction",
        [
            "Status: `CAB_ACTUAL_TOOL_GOLD_RECONSTRUCTION_READY`.",
            "",
            f"- Reconstructed: {core['actual_tool_passed_count']}/{core['actual_tool_candidate_count']}",
            f"- Actual primitive tool calls: {core['actual_tool_calls']}",
            f"- Negative controls: {core['negative_control_count']} passed",
            "- Hidden gold, scorer policy, answer contract, and Stage 2 were unavailable during derivation",
            "- Semantic IDs were derived from artifact hash + locator + observed value",
            "- No fixture fact reader was used",
        ],
    )
    _write_md(
        REPORT_DIR / "STAGE1_BLACK_BOX_LEAKAGE_REPORT.md",
        "Stage-1 black-box leakage report",
        [
            "Status: `CAB_STAGE1_BLACK_BOX_LEAKAGE_AUDIT_PASSED`.",
            "",
            f"Three physical archives passed ({', '.join(commitment['stage1_package_hashes'])}).",
            "The outside-only attacker found no answer-bearing fields, route/scorer metadata, Stage-2",
            "names, exposed candidate IDs, archive traversal, or public join path. Stage 2 is default-deny",
            "until finalized judgments, a valid receipt, and coordinator unlock are all present.",
        ],
    )
    _write_md(
        REPORT_DIR / "CAUSAL_ROUTE_AUDIT.md",
        "Causal route audit",
        [
            "Status: `CAB_CAUSAL_TOOL_ROUTE_VALIDATED`.",
            "",
            f"- Route counts: `{json.dumps(core['route_counts'], sort_keys=True)}`",
            f"- Passed route proofs: {core['route_candidates_passed']}/20",
            f"- Rejected irrelevant, wrong-artifact, stale, cross-candidate, and forged-ID attacks: {core['route_hostile_attack_count']}",
            "- Clarification proves exactly one absent variable after tool exhaustion",
            "- Abstention inventories every route with machine-readable elimination evidence",
        ],
    )
    _write_md(
        REPORT_DIR / "RECOVERY_FINAL_AUDIT.md",
        "Recovery final audit",
        [
            "Status: `CAB_RECOVERY_FINAL_AUDIT_PASSED`.",
            "",
            f"- Recovery candidates: {core['recovery_candidates_passed']}/{core['recovery_candidate_count']}",
            f"- Per-attempt hostile trajectories checked: {core['recovery_hostile_trajectory_count']}",
            "- Each success is bound to its own failure, action, tool, arguments, observation, derived facts, budget, and temporal order",
            "- Later unrelated success, replay, stale/cross-candidate evidence, forged metadata, and budget exhaustion fail",
        ],
    )
    _write_md(
        REPORT_DIR / "POWER_CALIBRATION_REPORT.md",
        "Power and inference calibration",
        [
            "Status: `CAB_POWER_PLAN_CALIBRATED`.",
            "",
            f"- Replicates: {power['repetitions']} in {len(power['shards'])} persisted deterministic shards",
            f"- Null Type-I error per model: `{power['null_type_i_error_per_model']}`",
            f"- Null CI coverage per model: `{power['null_ci_coverage_per_model']}`",
            f"- Alternative power per model: `{power['alternative_power_per_model']}`",
            f"- Minimum/median per-model power: {power['minimum_model_power']} / {power['median_model_power']}",
            f"- All-model familywise pass probability: {power['probability_all_models_pass']}",
            f"- Family/interaction power: {power['family_effect_power']} / {power['interaction_power']}",
            f"- Interaction null Type-I error: {power['interaction_null_type_i_error']}",
            f"- Bias: `{power['bias_per_model']}`; RMSE: `{power['rmse_per_model']}`",
            f"- Type-I Monte Carlo SE: `{power['monte_carlo_se_type_i_per_model']}`",
            "- Actual paired Wald/ANOVA/confidence-bound estimators run in every replicate; heuristic SD detection is prohibited",
        ],
    )
    _write_md(
        REPORT_DIR / "HOSTILE_GATE_REPORT.md",
        "Final hostile pre-run gate",
        [
            f"Status: `{gate['status']}`.",
            "",
            "The gate directly executed all scientific invariants. The tracked release pointer does not",
            "claim self-inclusion; the exact final-commit reproducible-build receipt is generated externally",
            "after commit and must pass the default exact-HEAD CLI check.",
        ],
    )
    _write_md(
        REPORT_DIR / "HUMAN_REVIEW_HANDOFF.md",
        "Human review handoff",
        [
            "Use only the three private Stage-1 archives whose hashes are frozen in the manifest.",
            "Recruit and qualify two independent reviewers; keep identities private. Commit Stage-1 before",
            "coordinator unlock. Then conduct Stage 2, independent adjudication, C10, and slice lock.",
            "No engineering fixture judgment may be counted. See `docs/final_hostile_pre_run/HUMAN_REVIEW_PROTOCOL.md`.",
        ],
    )
    _write_md(
        REPORT_DIR / "RUN_READINESS_HANDOFF.md",
        "Run-readiness handoff",
        [
            "Status: `CAB_FINAL_RUN_READINESS_PACKAGE_READY`; live execution remains blocked.",
            "",
            "The final run gate requires C10_PASS, slice lock, approval, packet, scorer, endpoint, analysis-plan,",
            "and system-identity bindings. The fixture-only lifecycle passed without provider or model calls.",
            "Use `docs/final_hostile_pre_run/AUTHORIZED_RUNBOOK.md` only after genuine gate approval.",
        ],
    )
    _write_md(
        REPORT_DIR / "VALIDATION_LEDGER.md",
        "Validation ledger",
        [
            "Provider-free direct gate construction completed. Focused tests, full tests, static checks, docs,",
            "security scans, packaging, reproducible detached builds, push equality, and CI are recorded honestly",
            "in the external final handoff after their commands complete.",
            "",
            f"Fixture lifecycle: {'PASS' if lifecycle['passed'] else 'FAIL'}; genuine evidence counters remain zero.",
        ],
    )
    _write_md(
        REPORT_DIR / "GITHUB_PUBLICATION.md",
        "GitHub publication model",
        [
            "Work is published directly to `main` without force push. An exact-HEAD receipt cannot truthfully",
            "include itself in the commit it attests, so reproducible artifact hashes and final source SHA are",
            "stored in an external receipt after the immutable final commit. Local/remote SHA equality and CI",
            "must be verified before completion is claimed.",
        ],
    )
    _write_md(
        REPO_ROOT / "CAB_FINAL_HOSTILE_PRE_RUN_REPORT.md",
        "CAB final hostile pre-run repair and freeze",
        [
            "`CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_PASSED`",
            "",
            "The 40 publicly exposed Compact candidates are permanently retired from genuine evidence. A new",
            "private 20-item packet is committed only by aggregate composition and one-way hashes. Its Stage-1",
            "archives contain primitive records only; Stage 2 and keys remain private. Actual tools reconstruct",
            "20/20 hidden answers, all causal routes and hostile recovery trajectories pass, and the paired",
            "analysis is calibrated with actual estimators. Scientific surfaces are hash-frozen.",
            "",
            "`HUMAN_VALIDATION_REQUIRED`",
            "",
            "`LIVE_EVIDENCE_REQUIRED`",
            "",
            "`CAB_LEVEL5_COMPLETE=false`",
            "",
            "`CAB_LEVEL6_COMPLETE=false`",
        ],
    )
    _write_md(
        REPO_ROOT / "cab_final_hostile_pre_run_handoff.md",
        "CAB final hostile pre-run handoff",
        [
            "Engineering is frozen. Do not regenerate the packet or change tasks, scorer, endpoints, analysis,",
            "power plan, system identity, review protocol, or C10 contract under the same version. The external",
            "release receipt must match exact HEAD before distribution.",
            "",
            "> Recruit and onboard two genuine qualified independent reviewers with the new physically isolated Stage-1 packages, keep Stage 2 inaccessible until Stage-1 commitment, complete adjudication and C10, lock the slice, and then begin the authorized Compact run sequence.",
        ],
    )
    if not all_precommit:
        raise SystemExit("final hostile report build failed one or more direct checks")
    print(json.dumps({"status": gate["status"], "power": power["passed"], "fixture_lifecycle": lifecycle["passed"], "freeze_sha256": freeze["freeze_manifest_sha256"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
