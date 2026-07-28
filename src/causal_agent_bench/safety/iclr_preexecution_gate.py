"""Unified, provider-free ICLR pre-execution readiness gate.

This gate composes the existing maximum-ceiling, contamination, split,
human-review, release, notebook, and paper-safety checks.  Expected human and
empirical prerequisites are kept separate from build defects so an honest
pre-execution checkout can settle at ``HUMAN_VALIDATION_REQUIRED``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.raac import (
    BASELINE_WRAPPERS,
    CANONICAL_POLICIES,
    FORBIDDEN_POLICY_KEYS,
    LEGAL_TRANSITIONS,
    PolicyVariant,
    RAACState,
)
from causal_agent_bench.safety.max_ceiling_gate import evaluate_max_ceiling_gate
from causal_agent_bench.safety.protected_heldout import (
    validate_protected_heldout_architecture,
)
from causal_agent_bench.safety.split_registry import build_canonical_split_registry
from causal_agent_bench.safety.workflow_state import WorkflowState

ICLR_REQUIRED_FILES: tuple[str, ...] = (
    "reports/ICLR_ULTIMATE_ONESHOT_LEDGER.md",
    "reports/ICLR_ONESHOT_CURRENT_STATE.json",
    "reports/ICLR_ONESHOT_CURRENT_STATE.md",
    "reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json",
    "docs/PUBLIC_HELDOUT_CONTAMINATION_AND_HISTORY_POLICY.md",
    "docs/RAAC_METHOD.md",
    "docs/RAAC_FAIRNESS_AND_BUDGET_POLICY.md",
    "experiments/RAAC_ABLATION_PLAN.md",
    "docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md",
    "docs/HUMAN_REVIEW_RESOURCE_PLAN.md",
    "docs/MAIN_SET_RESOURCE_AWARE_DECISION_POLICY.md",
    "docs/M4_LOW_MEMORY_WORKFLOW.md",
    "docs/KAGGLE_T4X2_OPERATIONS.md",
    "docs/ICLR_CONFIRMATORY_ANALYSIS_PLAN.md",
    "CAB_ICLR_PAPER_CLAIM_LEDGER.md",
    "reviews/ICLR_PREEXECUTION_REVIEWER_GAUNTLET.md",
    "CAB_ICLR_COMPLETE_EXECUTION_AND_EXPERIMENT_HANDBOOK.md",
    "src/causal_agent_bench/analysis/iclr_preexecution.py",
    "src/causal_agent_bench/resources.py",
    "data/manifests/scale100_confirmatory_v2_public_manifest.json",
    "data/manifests/naturalistic_transfer_v2_public_manifest.json",
)

PROTECTED_V2_EXPECTATIONS: Mapping[str, tuple[int, int, int]] = {
    "scale100_confirmatory_v2_protected": (100, 500, 600),
    "naturalistic_transfer_v2_protected": (60, 300, 360),
    "heldout_challenge_v2_protected": (50, 250, 300),
}

FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "Do not execute Compact-20, Scale-100, naturalistic transfer, or Main-500.",
    "Do not call provider APIs, run local/Hugging Face models, or launch Kaggle jobs.",
    "Do not treat fixture, proxy, or engineering output as scientific evidence.",
    "Do not fill paper results, rankings, intervals, or RAAC effects before audited runs.",
    "Do not expose private task payloads, answers, intervention labels, or evaluator metadata.",
)


def evaluate_iclr_preexecution_readiness(
    repo_root: str | Path,
    *,
    max_ceiling_report: Mapping[str, Any] | None = None,
    protected_report: Mapping[str, Any] | None = None,
    registry_report: Mapping[str, Any] | None = None,
    required_files: Sequence[str] = ICLR_REQUIRED_FILES,
) -> dict[str, Any]:
    """Return the unified ICLR state without performing scientific execution."""

    root = Path(repo_root).resolve()
    maximum = dict(max_ceiling_report or evaluate_max_ceiling_gate(root))
    protected = dict(
        protected_report or validate_protected_heldout_architecture(root)
    )
    registry = dict(registry_report or build_canonical_split_registry(root))
    checks: list[dict[str, Any]] = []

    _add_check(
        checks,
        "maximum_ceiling_build",
        bool(maximum.get("build_complete")),
        detail=(
            f"build_complete={bool(maximum.get('build_complete'))}; "
            f"build_blockers={len(_rows(maximum.get('build_blockers')))}"
        ),
    )
    _add_check(
        checks,
        "protected_split_architecture",
        bool(protected.get("passed")),
        detail=(
            f"passed={bool(protected.get('passed'))}; "
            f"issue_count={len(_rows(protected.get('issues')))}"
        ),
    )
    missing_files = [value for value in required_files if not (root / value).is_file()]
    _add_check(
        checks,
        "required_iclr_artifacts",
        not missing_files,
        detail=(
            "all required pre-execution artifacts are present"
            if not missing_files
            else "missing=" + ",".join(missing_files)
        ),
    )

    roles = {
        str(row.get("role")): row
        for row in _rows(registry.get("roles"))
        if row.get("role")
    }
    registry_issues = _protected_role_issues(roles)
    _add_check(
        checks,
        "protected_v2_registry",
        bool(registry.get("passed")) and not registry_issues,
        detail=(
            f"registry_passed={bool(registry.get('passed'))}; "
            f"overlaps={int(registry.get('cross_role_overlap_count', 0))}; "
            f"issues={registry_issues}"
        ),
    )

    required_raac_variants = {
        PolicyVariant.RAAC_LIGHT,
        PolicyVariant.RAAC_FULL,
        PolicyVariant.VERIFY_ONLY,
        PolicyVariant.RETRY_ONLY,
        PolicyVariant.ABSTAIN_ONLY,
        PolicyVariant.NO_CROSS_CHECK,
        PolicyVariant.NO_ALTERNATE_ROUTE,
        PolicyVariant.NO_FINAL_VERIFY,
    }
    available_variants = set(CANONICAL_POLICIES)
    _add_check(
        checks,
        "raac_method",
        required_raac_variants <= available_variants
        and len(RAACState) == 12
        and bool(LEGAL_TRANSITIONS)
        and len(BASELINE_WRAPPERS) >= 5
        and bool(FORBIDDEN_POLICY_KEYS),
        detail=(
            f"states={len(RAACState)}; policies={len(CANONICAL_POLICIES)}; "
            f"baselines={len(BASELINE_WRAPPERS)}; hidden_keys={len(FORBIDDEN_POLICY_KEYS)}"
        ),
    )

    notebook_state = _mapping(
        _mapping(maximum.get("state_snapshot")).get("notebooks")
    )
    _add_check(
        checks,
        "kaggle_notebooks",
        notebook_state.get("present_count") == 9
        and notebook_state.get("required_count") == 9
        and notebook_state.get("live_default") is False,
        detail=(
            f"present={notebook_state.get('present_count')}/"
            f"{notebook_state.get('required_count')}; "
            f"live_default={notebook_state.get('live_default')}"
        ),
    )

    build_blockers = [row for row in checks if not row["passed"]]
    evidence = _evidence_counts(maximum)
    human = _mapping(
        _mapping(maximum.get("state_snapshot")).get("human_validation")
    )
    state = derive_iclr_state(
        build_complete=not build_blockers,
        human_state=str(human.get("human_review_state") or ""),
        c10_state=str(human.get("c10_state") or ""),
        slice_lock_allowed=human.get("slice_lock_allowed") is True,
        evidence_counts=evidence,
    )
    blockers = _state_blockers(
        state,
        build_blockers=build_blockers,
        human=human,
        evidence=evidence,
    )
    next_action = _next_action(state, build_blockers)
    exit_code = exit_code_for_state(state)

    return {
        "schema_version": "cab_iclr_preexecution_gate_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "current_state": state.value,
        "status": (
            "BUILD_INCOMPLETE"
            if exit_code == 1
            else "EXPECTED_HUMAN_OR_EVIDENCE_BLOCK"
            if exit_code == 2
            else "READY"
        ),
        "exit_code": exit_code,
        "build_complete": not build_blockers,
        "checks": checks,
        "build_blockers": build_blockers,
        "blockers": blockers,
        "exact_next_allowed_action": next_action,
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "evidence_counts": evidence,
        "scientific_execution_allowed": False,
        "paper_eligible": evidence["paper_eligible_assets"] > 0
        and evidence["supported_empirical_claims"] > 0,
        "evidence_boundary": {
            "scientific_execution_performed_by_gate": False,
            "provider_or_model_calls_performed_by_gate": False,
            "human_rows_created_by_gate": False,
            "fixture_output_is_scientific_evidence": False,
        },
    }


def derive_iclr_state(
    *,
    build_complete: bool,
    human_state: str,
    c10_state: str,
    slice_lock_allowed: bool,
    evidence_counts: Mapping[str, int],
) -> WorkflowState:
    """Map canonical prerequisite facts to the public ICLR workflow state."""

    if not build_complete:
        return WorkflowState.ICLR_BUILD_INCOMPLETE
    if human_state != "HUMAN_REVIEW_COMPLETE":
        return WorkflowState.HUMAN_VALIDATION_REQUIRED
    if c10_state != "PASS" or not slice_lock_allowed:
        return WorkflowState.C10_PENDING
    if evidence_counts.get("audited_real_runs", 0) == 0:
        return WorkflowState.COMPACT20_READY
    if evidence_counts.get("paper_eligible_assets", 0) == 0:
        return WorkflowState.COMPACT20_AUDIT_REQUIRED
    if evidence_counts.get("supported_empirical_claims", 0) == 0:
        return WorkflowState.ICLR_EMPIRICAL_PACKAGE_READY
    return WorkflowState.ICLR_SUBMISSION_CANDIDATE


def exit_code_for_state(state: WorkflowState) -> int:
    """Return 1 for build defects, 2 for expected external blocks, else 0."""

    if state is WorkflowState.ICLR_BUILD_INCOMPLETE:
        return 1
    if state in {
        WorkflowState.HUMAN_VALIDATION_REQUIRED,
        WorkflowState.C10_PENDING,
        WorkflowState.COMPACT20_AUDIT_REQUIRED,
    }:
        return 2
    return 0


def _evidence_counts(maximum: Mapping[str, Any]) -> dict[str, int]:
    evidence = _mapping(_mapping(maximum.get("state_snapshot")).get("evidence"))
    return {
        "genuine_human_rows": int(evidence.get("genuine_human_rows") or 0),
        "real_trajectories": int(evidence.get("real_provider_trajectories") or 0)
        + int(evidence.get("real_open_model_trajectories") or 0),
        "audited_real_runs": int(evidence.get("audited_real_runs") or 0),
        "paper_eligible_assets": int(evidence.get("paper_eligible_assets") or 0),
        "supported_empirical_claims": int(
            evidence.get("supported_empirical_claims") or 0
        ),
    }


def _protected_role_issues(
    roles: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    issues: list[str] = []
    for role, (base_count, intervention_count, instance_count) in (
        PROTECTED_V2_EXPECTATIONS.items()
    ):
        row = roles.get(role)
        if row is None:
            issues.append(f"{role}:missing")
            continue
        expected = {
            "unique_base_task_count": base_count,
            "intervention_count": intervention_count,
            "instance_count": instance_count,
            "membership_visibility": "PRIVATE_COMMITMENT_ONLY",
            "confirmatory_eligible": False,
            "paper_eligible": False,
            "scientific_execution_allowed": False,
        }
        for field, value in expected.items():
            if row.get(field) != value:
                issues.append(f"{role}:{field}")
    return issues


def _state_blockers(
    state: WorkflowState,
    *,
    build_blockers: Sequence[Mapping[str, Any]],
    human: Mapping[str, Any],
    evidence: Mapping[str, int],
) -> list[dict[str, str]]:
    if state is WorkflowState.ICLR_BUILD_INCOMPLETE:
        return [
            {
                "code": str(row.get("check_id")),
                "class": "BUILD",
                "detail": str(row.get("detail")),
            }
            for row in build_blockers
        ]
    blockers: list[dict[str, str]] = []
    if state is WorkflowState.HUMAN_VALIDATION_REQUIRED:
        blockers.extend(
            [
                {
                    "code": "GENUINE_HUMAN_REVIEW_REQUIRED",
                    "class": "HUMAN",
                    "detail": (
                        f"genuine_rows={evidence['genuine_human_rows']}; "
                        f"state={human.get('human_review_state')}"
                    ),
                },
                {
                    "code": "C10_PENDING",
                    "class": "HUMAN",
                    "detail": str(human.get("c10_state") or "C10_PENDING"),
                },
                {
                    "code": "SLICE_LOCK_PENDING",
                    "class": "HUMAN",
                    "detail": "slice locking is forbidden until human validation and C10 pass",
                },
            ]
        )
    if evidence["audited_real_runs"] == 0:
        blockers.append(
            {
                "code": "AUDITED_EXECUTION_PENDING",
                "class": "EXECUTION",
                "detail": "no audited real model runs exist",
            }
        )
    if evidence["paper_eligible_assets"] == 0:
        blockers.append(
            {
                "code": "PAPER_EVIDENCE_PENDING",
                "class": "EMPIRICAL",
                "detail": "no paper-eligible empirical assets exist",
            }
        )
    return blockers


def _next_action(
    state: WorkflowState,
    build_blockers: Sequence[Mapping[str, Any]],
) -> str:
    if state is WorkflowState.ICLR_BUILD_INCOMPLETE:
        first = build_blockers[0] if build_blockers else {}
        return (
            f"Repair build check `{first.get('check_id', 'unknown')}` and rerun "
            "`python3 scripts/check_iclr_preexecution_readiness.py`."
        )
    if state is WorkflowState.HUMAN_VALIDATION_REQUIRED:
        return (
            "Complete the blank Compact-20 review packet with two independent, "
            "qualified human reviewers; do not run models."
        )
    if state is WorkflowState.C10_PENDING:
        return "Adjudicate disagreements and run the canonical C10 validator."
    if state is WorkflowState.COMPACT20_READY:
        return "Run the CPU preflight before any explicitly approved Compact-20 pilot."
    if state is WorkflowState.COMPACT20_AUDIT_REQUIRED:
        return "Audit the completed Compact-20 evidence before any scale-up decision."
    return "Follow the canonical execution handbook for the next preregistered stage."


def _add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    passed: bool,
    *,
    detail: str,
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "passed": bool(passed),
            "scope": "BUILD",
            "detail": detail,
            "evidence_class": "ENGINEERING_ONLY",
        }
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


__all__ = [
    "FORBIDDEN_ACTIONS",
    "ICLR_REQUIRED_FILES",
    "PROTECTED_V2_EXPECTATIONS",
    "derive_iclr_state",
    "evaluate_iclr_preexecution_readiness",
    "exit_code_for_state",
]
