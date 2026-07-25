"""Static governance checks for the tiny provider pilot lane."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.runners.run_completion import (
    infer_completion_state,
    load_run_metadata,
    trajectory_count,
)
from causal_agent_bench.safety.common import is_real_provider_type, strict_bool

MAX_TINY_PROVIDER_TRAJECTORIES = 5
BLOCKED_FINAL_CLAIMS = frozenset({*(f"C{i}" for i in range(1, 9)), "C10"})

SCORER_SANITY_ISSUE_CATEGORIES = frozenset(
    {
        "scorer_correct",
        "model_actually_wrong",
        "paraphrase_mismatch",
        "numeric_tolerance_issue",
        "date_or_time_format_issue",
        "list_or_set_mismatch",
        "abstention_correctness_issue",
        "false_positive_substring_match",
        "false_negative_strict_match",
        "gold_policy_issue",
        "unclear_manual_review_needed",
    }
)

REQUIRED_POSTRUN_REPORTS = {
    "postrun_audit": "TINY_PROVIDER_PILOT_POSTRUN_AUDIT.md",
    "trajectory_review": "TINY_PROVIDER_PILOT_TRAJECTORY_REVIEW.csv",
    "scorer_sanity_markdown": "SCORER_SANITY_TINY_PROVIDER_PILOT.md",
    "scorer_sanity_csv": "SCORER_SANITY_TINY_PROVIDER_PILOT.csv",
}


def analyze_live_authorization_text(text: str) -> dict[str, Any]:
    """Return whether the self-authorization text is unambiguous for live spend."""

    lowered = text.lower()
    live_marker = "live-run approval: yes" in lowered
    contradictions = []
    for marker in (
        "i authorize only the dry-run/preflight",
        "i do not authorize live paid provider calls",
        "live provider calls: not approved",
        "live-run approval: no",
    ):
        if marker in lowered:
            contradictions.append(marker)
    return {
        "live_approval_marker": live_marker,
        "contradictions": contradictions,
        "explicit_live_approval": live_marker and not contradictions,
    }


def audit_tiny_provider_config_lock(config_path: str | Path) -> dict[str, Any]:
    """Check that the approved tiny config is locked after any live attempt."""

    path = Path(config_path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    issues = []
    if raw.get("allow_paid_calls") is not False:
        issues.append(
            {
                "id": "allow_paid_calls_still_true",
                "message": "allow_paid_calls must be false after the tiny provider run finishes or fails.",
            }
        )
    return {
        "config_path": str(path),
        "allow_paid_calls": raw.get("allow_paid_calls"),
        "locked": not issues,
        "issues": issues,
    }


def audit_tiny_provider_postrun_artifacts(
    run_dir: str | Path,
    *,
    reports_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Audit tiny provider outputs without promoting evidence or reading secrets."""

    run_path = Path(run_dir)
    reports_path = Path(reports_dir) if reports_dir is not None else run_path.parents[1] / "reports"
    metadata = load_run_metadata(run_path)
    state = infer_completion_state(run_path)
    completed = int(state.get("completed_trajectories") or 0)
    observed_trajectories = trajectory_count(run_path)
    providers = _providers_from_metadata(metadata)
    provider_backed = any(is_real_provider_type(provider) for provider in providers)
    provider_outputs_present = provider_backed and max(completed, observed_trajectories) > 0
    issues: list[dict[str, str]] = []

    if max(completed, observed_trajectories) > MAX_TINY_PROVIDER_TRAJECTORIES:
        issues.append(
            {
                "id": "trajectory_cap_exceeded",
                "message": "Tiny provider pilot output exceeds the 5-trajectory cap.",
            }
        )

    incomplete_marker = any(
        (run_path / name).exists()
        for name in ("INCOMPLETE_RUN.json", "INCOMPLETE_RUN.md", "RUN_STATUS.md")
    )
    if provider_outputs_present and (state.get("completion_state") != "complete" or incomplete_marker):
        issues.append(
            {
                "id": "incomplete_provider_run_blocked_from_evidence",
                "message": "Incomplete provider output cannot be used as evidence.",
            }
        )

    if provider_outputs_present:
        for key, filename in REQUIRED_POSTRUN_REPORTS.items():
            if not (reports_path / filename).exists():
                issues.append(
                    {
                        "id": f"{key}_missing",
                        "message": f"Required post-run report is missing: {filename}.",
                    }
                )

    promoted_claims = _promoted_claims_from_metadata(metadata)
    blocked_promotions = sorted(promoted_claims & BLOCKED_FINAL_CLAIMS)
    if blocked_promotions:
        issues.append(
            {
                "id": "final_claim_promotion_forbidden",
                "message": "Tiny provider pilot cannot promote final claims: "
                + ", ".join(blocked_promotions),
            }
        )

    if provider_outputs_present and strict_bool(metadata.get("scientific_evidence")):
        issues.append(
            {
                "id": "scientific_evidence_true_for_tiny_pilot",
                "message": "Tiny/debug provider pilot outputs must remain preliminary, not scientific evidence.",
            }
        )

    return {
        "run_dir": str(run_path),
        "reports_dir": str(reports_path),
        "provider_backed": provider_backed,
        "provider_outputs_present": provider_outputs_present,
        "providers": sorted(providers),
        "completed_trajectories": completed,
        "observed_trajectories": observed_trajectories,
        "completion_state": state.get("completion_state"),
        "issues": issues,
        "paper_evidence_allowed": False,
        "provider_integration_sanity_allowed": provider_outputs_present
        and not any(issue["id"] == "incomplete_provider_run_blocked_from_evidence" for issue in issues),
    }


def _providers_from_metadata(metadata: dict[str, Any]) -> set[str]:
    providers: set[str] = set()
    for key in ("provider_type", "provider"):
        value = metadata.get(key)
        if value:
            providers.add(str(value))
    for value in metadata.get("providers") or []:
        if value:
            providers.add(str(value))
    for agent_run in metadata.get("agent_runs") or []:
        if isinstance(agent_run, dict) and agent_run.get("provider"):
            providers.add(str(agent_run["provider"]))
    return providers


def _promoted_claims_from_metadata(metadata: dict[str, Any]) -> set[str]:
    claims: set[str] = set()
    for key in ("supported_claims", "promoted_claims", "claims_promoted"):
        value = metadata.get(key)
        if isinstance(value, list):
            claims.update(str(item) for item in value)
    updates = metadata.get("claim_status_updates")
    if isinstance(updates, dict):
        for claim_id, status in updates.items():
            if str(status).lower() == "supported":
                claims.add(str(claim_id))
    if isinstance(updates, list):
        for row in updates:
            if isinstance(row, dict) and str(row.get("status")).lower() == "supported":
                claim_id = row.get("claim_id")
                if claim_id:
                    claims.add(str(claim_id))
    return claims
