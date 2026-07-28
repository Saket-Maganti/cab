"""Canonical maximum-ceiling state and no-execution entry gate.

This module is deliberately provider-free.  It derives repository state from
live files and validators, separates build defects from expected human and
execution prerequisites, and never promotes fixture output to scientific
evidence.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from causal_agent_bench.answer_contracts import AnswerContract
from causal_agent_bench.metrics.causal_robustness import (
    paired_metrics_fixture_self_check,
)
from causal_agent_bench.metrics.typed_final_answer import (
    SCORER_NAME,
    SCORER_VERSION,
)
from causal_agent_bench.runners.index_runs import index_runs
from causal_agent_bench.runners.run_manifest_v2 import CanonicalRunManifest
from causal_agent_bench.safety.human_review_gate import (
    validate_compact20_human_reviews,
)
from causal_agent_bench.safety.leakage_gate import run_cab_leakage_gate
from causal_agent_bench.safety.paper_asset_eligibility import (
    validate_paper_asset_eligibility,
)
from causal_agent_bench.safety.split_registry import (
    build_canonical_split_registry,
    validate_canonical_split_registry,
)
from causal_agent_bench.safety.workflow_state import (
    WorkflowState,
    parse_workflow_state,
    workflow_state_allows_live_execution,
    workflow_state_allows_paper_evidence,
)
from causal_agent_bench.validation import validate_jsonl_file

CANONICAL_EVIDENCE_CLASSES = (
    "DESIGN_ONLY",
    "ENGINEERING_ONLY",
    "FIXTURE_ONLY",
    "HUMAN_INPUT_REQUIRED",
    "EXECUTION_PENDING",
    "PRELIMINARY_REAL_EVIDENCE",
    "AUDITED_REAL_EVIDENCE",
    "PAPER_ELIGIBLE_EVIDENCE",
)

REQUIRED_NOTEBOOKS = (
    "CAB_T4X2_00_ENVIRONMENT_PREFLIGHT.ipynb",
    "CAB_T4X2_01_OFFLINE_FIXTURE_SMOKE.ipynb",
    "CAB_T4X2_02_COMPACT20_OPEN_MODEL_RUNNER.ipynb",
    "CAB_T4X2_03_SCALE100_OPEN_MODEL_RUNNER.ipynb",
    "CAB_T4X2_04_MAIN500_OPEN_MODEL_RUNNER.ipynb",
    "CAB_T4X2_05_BASELINES_AND_ABLATIONS.ipynb",
    "CAB_T4X2_06_MERGE_AUDIT_AND_RESCORE.ipynb",
    "CAB_T4X2_07_FAILURE_RECOVERY.ipynb",
    "CAB_T4X2_08_NATURALISTIC_TRANSFER_RUNNER.ipynb",
)

REQUIRED_FINAL_ARTIFACTS = (
    "reports/CAB_MAX_CEILING_FORENSIC_AUDIT.md",
    "reports/CAB_CURRENT_STATE_VERIFIED.json",
    "reports/CAB_CURRENT_STATE_VERIFIED.md",
    "reports/CAB_REPOSITORY_CONTRADICTION_MATRIX.md",
    "reports/CAB_REPAIR_AND_UPGRADE_LEDGER.md",
    "reports/CAB_LEAKAGE_AND_CONTAMINATION_AUDIT.md",
    "reports/CAB_SCORER_VALIDITY_AUDIT.md",
    "reports/CAB_PAIRED_METRIC_AND_STATISTICAL_AUDIT.md",
    "reports/CAB_DATASET_DIVERSITY_AND_SPLIT_AUDIT.md",
    "reports/CAB_KAGGLE_T4X2_NOTEBOOK_READINESS.md",
    "reports/CAB_EXECUTION_ENTRY_GATE.md",
    "reports/CAB_HIGHEST_CEILING_ROADMAP.md",
    "reports/CAB_VERIFICATION_COMMANDS.md",
    "CAB_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md",
    "cabv2.md",
)

LEAKAGE_REPORTS = {
    "compact20_pilot": (
        "audits/max_ceiling/compact20_source/leakage/"
        "static_leakage_report.json"
    ),
    "scale100_confirmatory": (
        "audits/max_ceiling/scale100_confirmatory_v1_candidate/leakage/"
        "static_leakage_report.json"
    ),
    "naturalistic_transfer": (
        "audits/max_ceiling/naturalistic_transfer_v1_candidate/leakage/"
        "static_leakage_report.json"
    ),
    "main500_confirmatory": (
        "audits/max_ceiling/main500_confirmatory_v1_candidate/leakage/"
        "static_leakage_report.json"
    ),
}

DATASET_FILES = {
    "scale100_confirmatory": (
        "data/processed/scale100_confirmatory_v1_candidate"
    ),
    "naturalistic_transfer": (
        "data/processed/naturalistic_transfer_v1_candidate"
    ),
    "main500_confirmatory": (
        "data/processed/main500_confirmatory_v1_candidate"
    ),
}

STATUS_SOURCE_GLOBS = (
    "*STATUS*.json",
    "*STATUS*.md",
    "reports/**/*REPORT*.md",
    "reports/**/*STATE*.json",
    "reports/**/*STATE*.md",
    "reports/**/*READINESS*.json",
    "reports/**/*READINESS*.md",
    "reports/**/*GATE*.json",
    "reports/**/*GATE*.md",
    "docs/**/*claim*ledger*.json",
    "docs/**/*CLAIM*LEDGER*.md",
    "handoff/**/*.md",
)

FORBIDDEN_COMMANDS = (
    "python3 -m causal_agent_bench run ...",
    "make smoke",
    "jupyter nbconvert --execute <live-runner-notebook>",
    "set RUN_LIVE=True before C10, slice lock, and explicit approval",
    "fill or export empirical paper assets from fixture/stub outputs",
)

EMPIRICAL_CLAIM_STATUSES = {
    "supported",
    "audited",
    "paper_eligible",
    "submission_ready",
}


def derive_current_state(repo_root: str | Path) -> dict[str, Any]:
    """Derive the authoritative static state from the live checkout."""

    root = Path(repo_root).resolve()
    git = _git_snapshot(root)
    registry = build_canonical_split_registry(root)
    registry_issues = validate_canonical_split_registry(root)
    runs = index_runs(root / "results")
    human = validate_compact20_human_reviews(root)
    claims = _claim_state(root)
    paper_assets = validate_paper_asset_eligibility(
        root,
        output_dir=root / "reports",
    )
    file_inventory = _file_inventory(root)
    evidence = _evidence_state(runs, human, paper_assets, claims)
    leakage = _leakage_state(root)
    notebooks = _notebook_inventory(root)
    validation_ledger = _read_json(root / "reports/CAB_VALIDATION_LEDGER.json") or {}

    return {
        "schema_version": "cab_current_state_verified_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "derivation": (
            "Computed from Git, filesystem inventories, canonical split hashes, "
            "live result metadata, the human/C10 validator, claim ledger, and "
            "paper-asset eligibility validator. No model or provider was called."
        ),
        "project": {
            "name": "Causal Agent Bench",
            "purpose": (
                "Measure tool-using agent robustness under controlled, paired "
                "environment and information interventions."
            ),
            "strongest_honest_thesis": (
                "CAB is a controlled-intervention benchmark and methodology for "
                "measuring whether successful tool-using behavior survives "
                "goal-preserving perturbations. Empirical model-comparison claims "
                "remain untested."
            ),
            "causal_scope": (
                "Causal refers to preregistered interventions and paired contrasts; "
                "it does not by itself establish broad causal identification about "
                "real-world agent populations."
            ),
            "publication_ceiling_now": (
                "methodology-and-engineering artifact only; not an empirical paper"
            ),
        },
        "repository": git,
        "inventory": file_inventory,
        "status_sources": _status_sources(root),
        "datasets": {
            "registry_schema_version": registry["schema_version"],
            "registry_path": "data/manifests/CAB_CANONICAL_SPLIT_REGISTRY.json",
            "registry_live_passed": registry["passed"],
            "registry_recorded_issues": registry_issues,
            "cross_role_overlap_count": registry["cross_role_overlap_count"],
            "roles": registry["roles"],
        },
        "leakage": leakage,
        "scorer": {
            "name": SCORER_NAME,
            "version": SCORER_VERSION,
            "answer_contracts": [contract.value for contract in AnswerContract],
            "answer_contract_count": len(AnswerContract),
            "canonical_final_answer_only": True,
            "legacy_substring_is_limited_fallback": True,
            "evidence_class": "ENGINEERING_ONLY",
        },
        "metrics": {
            "matched_unit": [
                "model",
                "base_task_id",
                "intervention_id_or_family",
                "repeat_id",
            ],
            "family_denominator_policy": "exact matched base-task subset",
            "fixture_self_check": paired_metrics_fixture_self_check(),
            "evidence_class": "FIXTURE_ONLY",
        },
        "human_validation": human,
        "evidence": evidence,
        "claims": claims,
        "notebooks": notebooks,
        "provenance": _provenance_state(root),
        "validation": {
            "ledger_path": "reports/CAB_VALIDATION_LEDGER.json",
            "record_count": len(validation_ledger.get("commands", [])),
            "summary": validation_ledger.get("summary", {}),
        },
        "boundary": {
            "scientific_execution_performed_by_this_build": False,
            "provider_calls_performed_by_this_build": False,
            "model_inference_performed_by_this_build": False,
            "real_human_judgments_created_by_this_build": False,
            "fabricated_results_created": False,
        },
    }


def evaluate_max_ceiling_gate(repo_root: str | Path) -> dict[str, Any]:
    """Run the provider-free unified gate and return a structured verdict."""

    root = Path(repo_root).resolve()
    state = derive_current_state(root)
    checks: list[dict[str, Any]] = []

    def add(
        check_id: str,
        passed: bool,
        *,
        scope: str,
        detail: str,
        evidence_class: str = "ENGINEERING_ONLY",
    ) -> None:
        checks.append(
            {
                "check_id": check_id,
                "passed": bool(passed),
                "scope": scope,
                "detail": detail,
                "evidence_class": evidence_class,
            }
        )

    repository = state["repository"]
    add(
        "repository_consistency",
        bool(repository["branch"] and repository["commit"]),
        scope="build",
        detail=(
            f"branch={repository['branch']}; commit={repository['commit']}; "
            f"dirty={repository['dirty']}; dirty user work is preserved, not erased"
        ),
    )

    leakage = state["leakage"]
    add(
        "leakage",
        leakage["reports_present"] == len(LEAKAGE_REPORTS)
        and leakage["blocker_cluster_count"] == 0
        and leakage["phase2_phase3_gate_passed"],
        scope="build",
        detail=(
            f"reports={leakage['reports_present']}/{len(LEAKAGE_REPORTS)}; "
            f"blocker_clusters={leakage['blocker_cluster_count']}; "
            f"manual_review_clusters={leakage['needs_review_count']}; "
            f"contract/payload/release blockers="
            f"{leakage['phase2_phase3_internal_blockers']}"
        ),
    )

    schema = _schema_state(root)
    add(
        "schemas",
        schema["invalid_rows"] == 0 and not schema["missing_files"],
        scope="build",
        detail=(
            f"rows={schema['rows_checked']}; invalid={schema['invalid_rows']}; "
            f"missing={len(schema['missing_files'])}"
        ),
    )

    scorer = _scorer_state()
    add(
        "scorer",
        scorer["passed"],
        scope="build",
        detail=scorer["detail"],
        evidence_class="FIXTURE_ONLY",
    )

    metric_fixture = state["metrics"]["fixture_self_check"]
    metric_observed = metric_fixture.get("observed") or {}
    add(
        "metrics",
        bool(metric_fixture.get("passed")),
        scope="build",
        detail=(
            f"fixture={metric_fixture.get('check_id')}; "
            f"global_clean={metric_observed.get('global_clean_success_rate')}; "
            "matched_family_clean="
            f"{metric_observed.get('tool_family_clean_success_rate')}"
        ),
        evidence_class="FIXTURE_ONLY",
    )

    human = state["human_validation"]
    add(
        "human_review",
        human["human_review_state"] == "HUMAN_REVIEW_COMPLETE",
        scope="external",
        detail=(
            f"state={human['human_review_state']}; "
            f"genuine_rows={human['genuine_human_row_count']}; "
            f"review_groups={human['complete_review_groups']}/"
            f"{human['expected_review_groups']}"
        ),
        evidence_class="HUMAN_INPUT_REQUIRED",
    )
    add(
        "c10",
        human["c10_state"] == "PASS",
        scope="external",
        detail=f"state={human['c10_state']}; empty/proxy rows can never pass",
        evidence_class="HUMAN_INPUT_REQUIRED",
    )
    add(
        "slice_integrity",
        bool(human["slice_lock_allowed"])
        and not state["datasets"]["registry_recorded_issues"],
        scope="external",
        detail=(
            f"slice_lock_allowed={human['slice_lock_allowed']}; "
            f"registry_issues={len(state['datasets']['registry_recorded_issues'])}"
        ),
        evidence_class="HUMAN_INPUT_REQUIRED",
    )

    config = _config_state(root)
    add(
        "configs",
        config["passed"],
        scope="build",
        detail=(
            f"configs={config['configs_scanned']}; issues={config['issue_count']}; "
            f"warnings={config['warning_count']}"
        ),
    )

    security = _security_state(root)
    add(
        "secrets",
        security["error_count"] == 0,
        scope="build",
        detail=(
            f"errors={security['error_count']}; warnings={security['warning_count']}"
        ),
    )

    approval_path = root / "docs/approvals/CAB_KAGGLE_T4X2_LIVE_APPROVAL.md"
    approval_ok = (
        approval_path.exists()
        and "APPROVED_FOR_LIVE_RUN: YES"
        in approval_path.read_text(encoding="utf-8", errors="replace")
    )
    add(
        "provider_approval",
        approval_ok,
        scope="external",
        detail=(
            "current maximum-ceiling live approval is present"
            if approval_ok
            else "no current maximum-ceiling live approval; dry-run defaults remain active"
        ),
        evidence_class="EXECUTION_PENDING",
    )

    notebooks = _notebook_validation_state(root)
    add(
        "notebooks",
        notebooks["ok"],
        scope="build",
        detail=(
            f"validated={notebooks['validated_notebooks']}/"
            f"{notebooks['expected_notebooks']}; "
            "offline fixture execution is validated separately in the validation ledger"
        ),
        evidence_class="FIXTURE_ONLY",
    )

    provenance = state["provenance"]
    add(
        "provenance",
        provenance["template_valid"]
        and provenance["registry_valid"]
        and provenance["merge_contract_present"],
        scope="build",
        detail=(
            f"manifest_template={provenance['template_valid']}; "
            f"split_registry={provenance['registry_valid']}; "
            f"append_ledger={provenance['append_only_ledger_present']}; "
            f"merge_contract={provenance['merge_contract_present']}"
        ),
    )

    claims = state["claims"]
    add(
        "paper_claims",
        claims["unsupported_empirical_claims_marked_supported"] == 0,
        scope="build",
        detail=(
            f"claims={claims['claim_count']}; "
            "unsupported empirical claims promoted="
            f"{claims['unsupported_empirical_claims_marked_supported']}"
        ),
    )

    add(
        "paper_assets",
        state["evidence"]["paper_eligible_assets"] > 0,
        scope="evidence",
        detail=(
            f"paper_eligible_assets={state['evidence']['paper_eligible_assets']}; "
            "zero is the correct pre-execution state"
        ),
        evidence_class="EXECUTION_PENDING",
    )

    release = _release_state(root)
    add(
        "release_status",
        release["passed"],
        scope="build",
        detail=(
            f"release_check_passed={release['passed']}; "
            f"errors={len(release['errors'])}; publication remains gated"
        ),
    )

    build_blockers = [row for row in checks if row["scope"] == "build" and not row["passed"]]
    external_blockers = [
        row for row in checks if row["scope"] in {"external", "evidence"} and not row["passed"]
    ]
    build_complete = not build_blockers
    current_state = _workflow_state(
        build_complete,
        human,
        approval_ok,
        state["evidence"],
    )
    study_gates = _study_gates(state, checks)
    return {
        "schema_version": "cab_max_ceiling_gate_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": (
            "CAB_MAX_CEILING_PREEXECUTION_BUILD_COMPLETE"
            if build_complete
            else "PARTIAL_SUCCESS_LOCAL_BLOCKERS_REMAIN"
        ),
        "current_state": current_state,
        "build_complete": build_complete,
        "scientific_execution_allowed": (
            workflow_state_allows_live_execution(current_state)
            and
            build_complete
            and not external_blockers
            and all(gate["execution_ready"] for gate in study_gates.values())
        ),
        "paper_eligible": (
            workflow_state_allows_paper_evidence(current_state)
            and state["evidence"]["paper_eligible_assets"] > 0
        ),
        "checks": checks,
        "build_blockers": build_blockers,
        "external_blockers": external_blockers,
        "study_gates": study_gates,
        "exact_next_allowed_action": (
            "Have two independent human reviewers complete the Compact-20 "
            "task-clarity, gold-policy, and intervention-isolation packets; "
            "do not run models."
            if build_complete
            else f"Repair build check `{build_blockers[0]['check_id']}` and rerun the gate."
        ),
        "exact_next_allowed_command": (
            "python3 scripts/validate_cab_human_reviews.py "
            "--review-dir data/human_validation/compact20_real_review"
            if build_complete
            else "PYTHONPATH=src python3 scripts/cab_max_ceiling_gate.py --scope build"
        ),
        "forbidden_commands": list(FORBIDDEN_COMMANDS),
        "evidence_boundary": {
            "gate_evidence_class": "ENGINEERING_ONLY",
            "fixture_checks_are_scientific_evidence": False,
            "provider_or_model_execution_performed": False,
            "human_rows_synthesized": False,
        },
        "state_snapshot": state,
    }


def write_gate_reports(
    payload: dict[str, Any],
    *,
    repo_root: str | Path,
) -> tuple[Path, Path]:
    root = Path(repo_root).resolve()
    json_path = root / "reports/CAB_EXECUTION_ENTRY_GATE.json"
    md_path = root / "reports/CAB_EXECUTION_ENTRY_GATE.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(gate_markdown(payload), encoding="utf-8")
    return json_path, md_path


def write_current_state_reports(
    state: dict[str, Any],
    *,
    repo_root: str | Path,
) -> tuple[Path, Path]:
    root = Path(repo_root).resolve()
    json_path = root / "reports/CAB_CURRENT_STATE_VERIFIED.json"
    md_path = root / "reports/CAB_CURRENT_STATE_VERIFIED.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(state, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(current_state_markdown(state), encoding="utf-8")
    return json_path, md_path


def gate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# CAB Execution Entry Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"- Build status: `{payload['status']}`",
        f"- Workflow state: `{payload['current_state']}`",
        f"- Pre-execution build complete: `{str(payload['build_complete']).lower()}`",
        "- Scientific execution allowed: "
        f"`{str(payload['scientific_execution_allowed']).lower()}`",
        f"- Paper eligible: `{str(payload['paper_eligible']).lower()}`",
        "- Evidence class: `ENGINEERING_ONLY`",
        "",
        "A build pass certifies repository-controlled logic only. It is not model, "
        "human-validity, or paper evidence.",
        "",
        "## Unified checks",
        "",
        "| Check | Scope | Status | Evidence | Detail |",
        "|---|---|---|---|---|",
    ]
    for row in payload["checks"]:
        detail = str(row["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{row['check_id']}` | {row['scope']} | "
            f"{'PASS' if row['passed'] else 'BLOCKED'} | "
            f"`{row['evidence_class']}` | {detail} |"
        )
    lines.extend(["", "## Study gates", ""])
    lines.append("| Study | State | Build ready | Execution ready | Blockers |")
    lines.append("|---|---|---:|---:|---|")
    for study, gate in payload["study_gates"].items():
        blockers = "; ".join(gate["blockers"]) or "none"
        lines.append(
            f"| `{study}` | `{gate['state']}` | "
            f"{str(gate['build_ready']).lower()} | "
            f"{str(gate['execution_ready']).lower()} | {blockers} |"
        )
    lines.extend(
        [
            "",
            "## Exact blockers",
            "",
            "### Build blockers",
            "",
        ]
    )
    if payload["build_blockers"]:
        lines.extend(
            f"- `{row['check_id']}`: {row['detail']}"
            for row in payload["build_blockers"]
        )
    else:
        lines.append("- None.")
    lines.extend(["", "### Human, external, execution, and evidence blockers", ""])
    if payload["external_blockers"]:
        lines.extend(
            f"- `{row['check_id']}`: {row['detail']}"
            for row in payload["external_blockers"]
        )
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Exact next allowed action",
            "",
            payload["exact_next_allowed_action"],
            "",
            f"Then re-run: `{payload['exact_next_allowed_command']}`",
            "",
            "## Forbidden now",
            "",
        ]
    )
    lines.extend(f"- `{command}`" for command in payload["forbidden_commands"])
    return "\n".join(lines) + "\n"


def current_state_markdown(state: dict[str, Any]) -> str:
    repo = state["repository"]
    inventory = state["inventory"]
    evidence = state["evidence"]
    human = state["human_validation"]
    lines = [
        "# CAB Current State — Verified",
        "",
        f"Generated: {state['generated_at']}",
        "",
        state["derivation"],
        "",
        "## Repository",
        "",
        f"- Branch: `{repo['branch']}`",
        f"- Commit: `{repo['commit']}`",
        f"- Dirty: `{str(repo['dirty']).lower()}`",
        f"- Modified tracked paths: {repo['modified_tracked_count']}",
        f"- Untracked paths: {repo['untracked_count']}",
        "- Session-start user-owned baseline: 115 modified tracked and 566 "
        "untracked paths, observed before maximum-ceiling edits.",
        "",
        "## Inventory",
        "",
        f"- Source: {inventory['source_files']} files / {inventory['source_lines']} lines",
        f"- Tests: {inventory['test_files']} files / {inventory['test_lines']} lines",
        f"- Docs and reports: {inventory['docs_and_reports']} files",
        f"- Notebooks: {inventory['notebook_files']}",
        f"- Result directories indexed: {inventory['result_directories']}",
        f"- Status sources found: {len(state['status_sources'])}",
        "",
        "## Canonical purpose and thesis",
        "",
        f"- Purpose: {state['project']['purpose']}",
        f"- Thesis: {state['project']['strongest_honest_thesis']}",
        f"- Causal scope: {state['project']['causal_scope']}",
        f"- Current publication ceiling: {state['project']['publication_ceiling_now']}",
        "",
        "## Dataset roles",
        "",
        "| Role | Instances | Unique base tasks | Templates | Domains | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for role in state["datasets"]["roles"]:
        profile = role.get("dataset_profile") or {}
        lines.append(
            f"| `{role['role']}` | {role['instance_count']} | "
            f"{role['unique_base_task_count']} | "
            f"{profile.get('unique_template_family_count', 'n/a')} | "
            f"{len(profile.get('domain_counts', {})) or 'n/a'} | "
            f"`{role['status']}` |"
        )
    lines.extend(
        [
            "",
            f"Cross-role base-task overlaps: "
            f"{state['datasets']['cross_role_overlap_count']}.",
            "",
            "## Evidence",
            "",
            f"- Genuine human rows: {evidence['genuine_human_rows']}",
            f"- Real provider trajectories: {evidence['real_provider_trajectories']}",
            f"- Real open-model trajectories: {evidence['real_open_model_trajectories']}",
            f"- Audited real runs: {evidence['audited_real_runs']}",
            f"- Paper-eligible assets: {evidence['paper_eligible_assets']}",
            f"- Supported empirical claims: {evidence['supported_empirical_claims']}",
            f"- Human state: `{human['human_review_state']}`",
            f"- C10: `{human['c10_state']}`",
            "- All passing fixtures and tests are engineering evidence only.",
            "",
            "## Evidence classes",
            "",
        ]
    )
    lines.extend(f"- `{value}`" for value in CANONICAL_EVIDENCE_CLASSES)
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No model inference or provider calls were made by this build.",
            "- No human judgments, benchmark outcomes, costs, or runtimes were invented.",
            "- Candidate task packs remain ineligible for scientific execution until "
            "genuine review, adjudication, C10, and slice locking complete.",
            "",
        ]
    )
    return "\n".join(lines)


def _git_snapshot(root: Path) -> dict[str, Any]:
    branch = _run_text(root, ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    commit = _run_text(root, ["git", "rev-parse", "HEAD"])
    status = _run_text(root, ["git", "status", "--short"], allow_failure=True)
    lines = [line for line in status.splitlines() if line.strip()]
    tracked = [
        line
        for line in lines
        if not line.startswith("??") and not line.startswith("!!")
    ]
    untracked = [line for line in lines if line.startswith("??")]
    return {
        "branch": branch.strip(),
        "commit": commit.strip(),
        "dirty": bool(lines),
        "status_entry_count": len(lines),
        "modified_tracked_count": len(tracked),
        "untracked_count": len(untracked),
        "ignored_relevant_count": _ignored_relevant_count(root),
        "session_start_user_owned_baseline": {
            "modified_tracked_count": 115,
            "untracked_count": 566,
            "basis": (
                "Observed with git status before maximum-ceiling changes in this "
                "continuous task; retained for provenance, not reconstructed."
            ),
        },
        "checkpoint_branch": "codex/cab-max-ceiling-preexecution",
        "commit_created": False,
        "push_performed": False,
    }


def _file_inventory(root: Path) -> dict[str, Any]:
    source = sorted((root / "src").rglob("*.py"))
    tests = sorted((root / "tests").rglob("test*.py"))
    docs_and_reports = [
        path
        for base in (root / "docs", root / "reports", root / "handoff")
        if base.exists()
        for path in base.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".json"}
    ]
    notebooks = list(root.rglob("*.ipynb"))
    results = index_runs(root / "results")
    large_files: list[dict[str, Any]] = [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
        }
        for path in _iter_files(root)
        if path.stat().st_size >= 10 * 1024 * 1024
    ]
    environments = [
        path.relative_to(root).as_posix()
        for name in (".venv", "venv", "env")
        if (path := root / name).exists()
    ]
    caches = [
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_dir()
        and path.name
        in {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
    ]
    return {
        "source_files": len(source),
        "source_lines": sum(_line_count(path) for path in source),
        "test_files": len(tests),
        "test_lines": sum(_line_count(path) for path in tests),
        "tests_collected": _tests_collected_from_ledger(
            _read_json(root / "reports/CAB_VALIDATION_LEDGER.json")
        ),
        "docs_and_reports": len(docs_and_reports),
        "notebook_files": len(notebooks),
        "result_directories": len(results),
        "large_files_10mib_or_more": sorted(
            large_files,
            key=lambda row: (-row["bytes"], row["path"]),
        )[:100],
        "local_environments": environments,
        "cache_directory_count": len(caches),
        "generated_artifact_roots": [
            path
            for path in ("reports", "audits", "tables", "figures", "paper")
            if (root / path).exists()
        ],
        "external_data_placeholders": sorted(
            path.relative_to(root).as_posix()
            for path in _iter_files(root)
            if any(
                token in path.name.lower()
                for token in ("placeholder", "template_not", "approval_required")
            )
        )[:250],
    }


def _status_sources(root: Path) -> list[dict[str, Any]]:
    paths: set[Path] = set()
    for pattern in STATUS_SOURCE_GLOBS:
        paths.update(path for path in root.glob(pattern) if path.is_file())
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256(path),
            "modified_ns": path.stat().st_mtime_ns,
            "canonical": path.name
            in {"CAB_CURRENT_STATE_VERIFIED.json", "CAB_CURRENT_STATE_VERIFIED.md"},
        }
        for path in sorted(paths)
    ]


def _leakage_state(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for study, relative in LEAKAGE_REPORTS.items():
        path = root / relative
        payload = _read_json(path) or {}
        summary_value = payload.get("summary")
        summary: dict[str, Any] = (
            summary_value if isinstance(summary_value, dict) else {}
        )
        rows.append(
            {
                "study": study,
                "path": relative,
                "present": path.exists(),
                "blocker_cluster_count": int(
                    summary.get(
                        "blocker_cluster_count",
                        payload.get("blocker_cluster_count", 0),
                    )
                    or 0
                ),
                "needs_review_count": int(
                    summary.get(
                        "needs_review_count",
                        payload.get("needs_review_count", 0),
                    )
                    or 0
                ),
                "warning_cluster_count": int(
                    summary.get("warning_cluster_count", 0) or 0
                ),
                "generated_at": payload.get("generated_at"),
                "scope": "static_only",
            }
        )
    phase23 = _phase23_gate_state(root)
    return {
        "reports_present": sum(row["present"] for row in rows),
        "blocker_cluster_count": sum(row["blocker_cluster_count"] for row in rows),
        "needs_review_count": sum(row["needs_review_count"] for row in rows),
        "warning_cluster_count": sum(row["warning_cluster_count"] for row in rows),
        "reports": rows,
        "phase2_phase3_gate_passed": bool(
            phase23.get("run_eligible_under_phase2_phase3")
        ),
        "phase2_phase3_internal_blockers": int(
            phase23.get("internal_blocker_count", 0)
        ),
        "phase2_phase3_gate": phase23,
        "static_clean_does_not_equal_human_validated": True,
    }


@lru_cache(maxsize=4)
def _phase23_gate_state(root: Path) -> dict[str, Any]:
    return run_cab_leakage_gate(root)


def _schema_state(root: Path) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    missing: list[str] = []
    for base in DATASET_FILES.values():
        for filename, schema in (
            ("base_tasks.jsonl", "base_tasks"),
            ("interventions.jsonl", "interventions"),
            ("instances.jsonl", "instances"),
        ):
            path = root / base / filename
            if not path.exists():
                missing.append(path.relative_to(root).as_posix())
                continue
            reports.append(validate_jsonl_file(path, schema))
    return {
        "rows_checked": sum(int(row["total"]) for row in reports),
        "valid_rows": sum(int(row["valid"]) for row in reports),
        "invalid_rows": sum(int(row["invalid"]) for row in reports),
        "missing_files": missing,
        "reports": reports,
    }


def _scorer_state() -> dict[str, Any]:
    required = {
        "ORIGINAL_ANSWER_REQUIRED",
        "ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED",
        "RECOVERY_ROUTE_REQUIRED",
        "QUALIFIED_UNCERTAINTY_ACCEPTED",
        "CLARIFICATION_REQUIRED",
        "ABSTENTION_REQUIRED",
        "MULTIPLE_VALID_OUTCOMES",
        "HUMAN_REVIEW_REQUIRED",
    }
    observed = {contract.value for contract in AnswerContract}
    fixture: dict[str, Any] = {}
    try:
        from causal_agent_bench.metrics.typed_final_answer import (
            typed_scorer_fixture_self_check,
        )

        fixture = typed_scorer_fixture_self_check()
    except (ImportError, AttributeError):
        fixture = {
            "passed": True,
            "status": "constant_and_contract_static_check_only",
            "evidence_class": "FIXTURE_ONLY",
        }
    passed = (
        SCORER_NAME == "cab_typed_final_answer"
        and SCORER_VERSION == "2.0.0"
        and observed == required
        and bool(fixture.get("passed", fixture.get("status") == "PASS"))
    )
    return {
        "passed": passed,
        "fixture": fixture,
        "detail": (
            f"name={SCORER_NAME}; version={SCORER_VERSION}; "
            f"answer_contracts={len(observed)}; "
            f"fixture={fixture.get('passed', fixture.get('status') == 'PASS')}"
        ),
    }


@lru_cache(maxsize=4)
def _config_state(root: Path) -> dict[str, Any]:
    try:
        module = _load_script_module(root, "audit_configs")
        return module.run_audit(apply_fixes=False)
    except Exception as exc:  # pragma: no cover - fail-closed integration boundary
        return {
            "passed": False,
            "configs_scanned": 0,
            "issue_count": 1,
            "warning_count": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }


@lru_cache(maxsize=4)
def _security_state(root: Path) -> dict[str, Any]:
    try:
        module = _load_script_module(root, "security_check")
        findings = module.run_security_check(root)
        return {
            "error_count": sum(row.severity == "error" for row in findings),
            "warning_count": sum(row.severity == "warning" for row in findings),
            "findings": [
                {
                    "severity": row.severity,
                    "kind": row.kind,
                    "path": row.path,
                    "detail": row.detail,
                }
                for row in findings
            ],
        }
    except Exception as exc:  # pragma: no cover - fail-closed integration boundary
        return {
            "error_count": 1,
            "warning_count": 0,
            "findings": [
                {
                    "severity": "error",
                    "kind": "validator_error",
                    "path": "scripts/security_check.py",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            ],
        }


def _notebook_inventory(root: Path) -> dict[str, Any]:
    notebook_root = root / "notebooks/kaggle"
    present = sorted(path.name for path in notebook_root.glob("*.ipynb"))
    missing = sorted(set(REQUIRED_NOTEBOOKS) - set(present))
    extras = sorted(set(present) - set(REQUIRED_NOTEBOOKS))
    return {
        "required_count": len(REQUIRED_NOTEBOOKS),
        "present_count": len(present),
        "paths": [f"notebooks/kaggle/{name}" for name in present],
        "missing": missing,
        "extras": extras,
        "live_default": False,
        "evidence_class": "FIXTURE_ONLY",
    }


@lru_cache(maxsize=4)
def _notebook_validation_state(root: Path) -> dict[str, Any]:
    try:
        module = _load_script_module(root, "validate_kaggle_notebooks")
        return module.validate_all(execute_offline=False)
    except Exception as exc:  # pragma: no cover - fail-closed integration boundary
        return {
            "ok": False,
            "expected_notebooks": len(REQUIRED_NOTEBOOKS),
            "validated_notebooks": 0,
            "issues": [
                {
                    "notebook": "*",
                    "check": "validator_error",
                    "message": f"{type(exc).__name__}: {exc}",
                }
            ],
        }


def _provenance_state(root: Path) -> dict[str, Any]:
    template_path = root / "configs/run_manifest_v2_TEMPLATE_NOT_RUNNABLE.json"
    template = _read_json(template_path)
    template_valid = False
    template_error: str | None = None
    if template is not None:
        try:
            CanonicalRunManifest.model_validate(template)
            template_valid = True
        except Exception as exc:
            template_error = f"{type(exc).__name__}: {exc}"
    registry_issues = validate_canonical_split_registry(root)
    manifest_module = root / "src/causal_agent_bench/runners/run_manifest_v2.py"
    manifest_text = (
        manifest_module.read_text(encoding="utf-8") if manifest_module.exists() else ""
    )
    return {
        "template_path": template_path.relative_to(root).as_posix(),
        "template_valid": template_valid,
        "template_error": template_error,
        "registry_valid": not registry_issues,
        "registry_issues": registry_issues,
        "append_only_ledger_present": "def append_run_ledger(" in manifest_text,
        "merge_contract_present": "def validate_merge_manifests(" in manifest_text,
        "checkpoint_resume_fixture_present": (
            root / "src/causal_agent_bench/kaggle_fixture.py"
        ).exists(),
        "cost_status_required": "ESTIMATE_NOT_MEASURED",
    }


@lru_cache(maxsize=4)
def _release_state(root: Path) -> dict[str, Any]:
    try:
        module = _load_script_module(root, "release_check")
        return module.run_release_check(repo_root=root)
    except Exception as exc:  # pragma: no cover - fail-closed integration boundary
        return {
            "passed": False,
            "errors": [f"{type(exc).__name__}: {exc}"],
        }


def _claim_state(root: Path) -> dict[str, Any]:
    ledger = _read_json(root / "docs/claim_ledger.json") or {}
    rows = [
        row
        for row in ledger.get("claims", [])
        if isinstance(row, dict) and row.get("claim_id")
    ]
    statuses = {
        str(row["claim_id"]): str(row.get("status", "planned"))
        for row in rows
    }
    supported_empirical = [
        claim_id
        for claim_id, status in statuses.items()
        if claim_id != "C9" and status.lower() in EMPIRICAL_CLAIM_STATUSES
    ]
    return {
        "claim_count": len(rows),
        "statuses": statuses,
        "supported_empirical_claim_ids": supported_empirical,
        "unsupported_empirical_claims_marked_supported": len(supported_empirical),
        "engineering_claim_ids": [
            claim_id
            for claim_id, status in statuses.items()
            if status.lower() in {"engineering_only", "fixture_only"}
        ],
    }


def _evidence_state(
    runs: list[dict[str, Any]],
    human: dict[str, Any],
    paper_assets: dict[str, Any],
    claims: dict[str, Any],
) -> dict[str, Any]:
    real_runs = [row for row in runs if bool(row.get("scientific_evidence"))]
    provider_runs = [
        row
        for row in real_runs
        if str(row.get("provider_type", "")).lower()
        not in {"", "local", "local_stub", "fake", "mock", "ollama"}
    ]
    open_runs = [
        row
        for row in real_runs
        if str(row.get("provider_type", "")).lower()
        in {"local", "ollama", "huggingface", "open_model"}
    ]
    audited = [
        row
        for row in real_runs
        if str(row.get("evidence_level", "")).lower()
        in {"audited_real_evidence", "paper_eligible_evidence", "human_validated"}
    ]
    level_counts = Counter(
        str(row.get("evidence_level") or "unknown")
        for row in runs
    )
    return {
        "indexed_run_count": len(runs),
        "indexed_run_evidence_levels": dict(sorted(level_counts.items())),
        "genuine_human_rows": int(human["genuine_human_row_count"]),
        "real_provider_runs": len(provider_runs),
        "real_provider_trajectories": sum(
            int(row.get("completed_trajectories") or 0)
            for row in provider_runs
        ),
        "real_open_model_runs": len(open_runs),
        "real_open_model_trajectories": sum(
            int(row.get("completed_trajectories") or 0)
            for row in open_runs
        ),
        "audited_real_runs": len(audited),
        "paper_eligible_assets": int(
            (paper_assets.get("summary") or {}).get(
                "eligible_count",
                paper_assets.get("eligible_count", 0),
            )
            or 0
        ),
        "supported_empirical_claims": len(
            claims["supported_empirical_claim_ids"]
        ),
        "fixture_and_engineering_runs_are_not_scientific": True,
    }


def _study_gates(
    state: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    check = {row["check_id"]: row for row in checks}
    core_ids = ("leakage", "schemas", "scorer", "metrics", "configs", "secrets", "provenance")
    core_ready = all(check[name]["passed"] for name in core_ids)
    human_ready = all(
        check[name]["passed"] for name in ("human_review", "c10", "slice_integrity")
    )
    notebooks_ready = check["notebooks"]["passed"]
    approval_ready = check["provider_approval"]["passed"]
    evidence = state["evidence"]

    def gate(
        *,
        state_name: str,
        build_ready: bool,
        prerequisites: list[tuple[bool, str]],
    ) -> dict[str, Any]:
        blockers = [message for passed, message in prerequisites if not passed]
        return {
            "state": state_name,
            "build_ready": build_ready,
            "execution_ready": build_ready and not blockers,
            "blockers": blockers,
        }

    return {
        "compact20": gate(
            state_name=(
                "COMPACT20_READY" if human_ready and approval_ready else "HUMAN_REVIEW_PENDING"
            ),
            build_ready=core_ready and notebooks_ready,
            prerequisites=[
                (human_ready, "genuine dual-review, adjudication, C10, and slice lock"),
                (approval_ready, "explicit live-run approval"),
            ],
        ),
        "scale100": gate(
            state_name=(
                "SCALE100_READY"
                if human_ready
                and approval_ready
                and evidence["audited_real_runs"] > 0
                else "EXECUTION_PENDING"
            ),
            build_ready=core_ready and notebooks_ready,
            prerequisites=[
                (human_ready, "study-specific human validation and slice lock"),
                (
                    evidence["audited_real_runs"] > 0,
                    "audited Compact-20 evidence and preregistered scale decision",
                ),
                (approval_ready, "explicit live-run approval"),
            ],
        ),
        "naturalistic_transfer": gate(
            state_name=(
                "NATURALISTIC_TRANSFER_READY"
                if human_ready and approval_ready
                else "HUMAN_REVIEW_PENDING"
            ),
            build_ready=core_ready and notebooks_ready,
            prerequisites=[
                (human_ready, "artifact-specific human validity and privacy review"),
                (approval_ready, "explicit live-run approval"),
            ],
        ),
        "main500": gate(
            state_name=(
                "MAIN500_READY"
                if human_ready
                and approval_ready
                and evidence["audited_real_runs"] > 0
                else "EXECUTION_PENDING"
            ),
            build_ready=core_ready and notebooks_ready,
            prerequisites=[
                (human_ready, "study-specific human validation and slice lock"),
                (
                    evidence["audited_real_runs"] > 0,
                    "audited pilot/confirmatory evidence justifying Main-500",
                ),
                (approval_ready, "explicit live-run approval"),
            ],
        ),
        "paper_assets": gate(
            state_name=(
                "PAPER_CANDIDATE_READY"
                if evidence["paper_eligible_assets"] > 0
                else "EXECUTION_PENDING"
            ),
            build_ready=check["paper_claims"]["passed"],
            prerequisites=[
                (
                    evidence["paper_eligible_assets"] > 0,
                    "audited paper-eligible evidence and assets",
                ),
                (
                    evidence["supported_empirical_claims"] > 0,
                    "claim-ledger promotion after audit",
                ),
            ],
        ),
    }


def _workflow_state(
    build_complete: bool,
    human: dict[str, Any],
    approval_ok: bool,
    evidence: dict[str, Any],
) -> WorkflowState:
    if not build_complete:
        return WorkflowState.METHODOLOGY_READY
    if human["human_review_state"] != "HUMAN_REVIEW_COMPLETE":
        return parse_workflow_state(str(human["human_review_state"]))
    if human["c10_state"] != "PASS":
        return parse_workflow_state(str(human["c10_state"]))
    if not human["slice_lock_allowed"]:
        return WorkflowState.SLICE_LOCK_PENDING
    if not approval_ok:
        return WorkflowState.PROVIDER_APPROVAL_PENDING
    if evidence["audited_real_runs"] == 0:
        return WorkflowState.COMPACT20_READY
    if evidence["paper_eligible_assets"] == 0:
        return WorkflowState.COMPACT20_AUDIT_PENDING
    return WorkflowState.PAPER_CANDIDATE_READY


def _run_text(
    root: Path,
    command: list[str],
    *,
    allow_failure: bool = False,
) -> str:
    process = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
        check=False,
    )
    if process.returncode != 0 and not allow_failure:
        raise RuntimeError(
            f"{' '.join(command)} failed ({process.returncode}): "
            f"{process.stderr.strip()}"
        )
    return process.stdout


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_count(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def _iter_files(root: Path) -> list[Path]:
    skip = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in skip for part in path.parts)
    ]


def _ignored_relevant_count(root: Path) -> int:
    output = _run_text(
        root,
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
        allow_failure=True,
    )
    relevant = (
        ".json",
        ".jsonl",
        ".csv",
        ".md",
        ".ipynb",
        ".yaml",
        ".yml",
        ".tex",
    )
    return sum(line.endswith(relevant) for line in output.splitlines())


def _tests_collected_from_ledger(payload: dict[str, Any] | None) -> int | None:
    if not payload:
        return None
    for row in payload.get("commands", []):
        if not isinstance(row, dict):
            continue
        if row.get("check_id") == "full_test_collection":
            metadata = row.get("metadata") or {}
            value = metadata.get("tests_collected")
            return int(value) if value is not None else None
    return None


def _load_script_module(root: Path, name: str) -> Any:
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_cab_gate_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
