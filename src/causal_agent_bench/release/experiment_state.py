"""Experiment run state machine validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from causal_agent_bench.runners.run_completion import infer_completion_state, load_run_metadata
from causal_agent_bench.safety.common import classify_run_entry

VALID_STATES = frozenset(
    {
        "not_started",
        "planned",
        "dry_run_ready",
        "zero_cost_ready",
        "running",
        "interrupted",
        "complete_engineering",
        "complete_preliminary",
        "provider_pilot_complete",
        "human_validation_ready",
        "main_experiment_ready",
        "submission_ready",
        "blocked",
    }
)

NON_SCIENTIFIC_SCOPES = frozenset(
    {
        "pilot_stub_engineering_only",
        "deterministic_baseline_engineering",
        "mock_diagnostic_only",
        "dry_run",
    }
)


def infer_experiment_state(run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    if not run_dir.exists():
        return {"state": "not_started", "run_dir": str(run_dir), "issues": ["run directory missing"]}

    completion = infer_completion_state(run_dir)
    metadata = load_run_metadata(run_dir)
    scope = str(metadata.get("evidence_scope", "")).lower()
    run_status = completion["run_status"]
    issues: list[str] = []

    repo_root = run_dir.resolve().parent.parent
    classified = classify_run_entry({"path": str(run_dir.resolve())}, repo_root)
    classification = str(classified.get("classification", "unknown_needs_review"))

    if run_status == "dry_run":
        state = "dry_run_ready"
    elif run_status in {"incomplete", "running"}:
        state = "running" if run_status == "running" else "blocked"
    elif run_status == "interrupted" or classification == "interrupted":
        state = "interrupted"
    elif run_status == "complete":
        if classification in {"mock_diagnostic", "stub_engineering"}:
            state = "complete_engineering"
        elif classification == "local_preliminary":
            state = "complete_preliminary"
        elif classification == "incomplete":
            state = "blocked"
            issues.append("run marked complete but classification=incomplete")
        elif classification == "complete_engineering_only":
            state = "complete_engineering"
        elif classification == "provider_backed_pilot" and classified.get("paper_eligible"):
            state = "provider_pilot_complete"
        elif (classification == "main_benchmark" and classified.get("paper_eligible")) or (classification == "complete_scientific_evidence" and classified.get("paper_eligible")):
            state = "main_experiment_ready"
        else:
            state = "complete_preliminary"
    else:
        state = "blocked"
        issues.append(f"unknown run_status: {run_status}")

    if (run_dir / "human_validation").exists():
        state = "human_validation_ready"

    allowed_claims = _allowed_claims(state)
    forbidden = _forbidden_commands(state)

    return {
        "state": state,
        "run_dir": str(run_dir.resolve()),
        "run_status": run_status,
        "evidence_scope": scope,
        "classification": classification,
        "paper_eligible": classified.get("paper_eligible"),
        "scientific_evidence": completion.get("scientific_evidence"),
        "allowed_claims": allowed_claims,
        "forbidden_commands": forbidden,
        "issues": issues,
    }


def _allowed_claims(state: str) -> list[str]:
    mapping = {
        "not_started": [],
        "planned": [],
        "dry_run_ready": ["engineering pipeline checks"],
        "zero_cost_ready": ["engineering pipeline checks"],
        "running": [],
        "interrupted": ["none — mark interrupted only"],
        "complete_engineering": ["engineering_only", "mock_diagnostic"],
        "complete_preliminary": ["local_preliminary wording only"],
        "provider_pilot_complete": ["pilot wording only"],
        "human_validation_ready": ["validation subset claims"],
        "main_experiment_ready": ["main experiment claims per claim ledger"],
        "submission_ready": ["submission-ready claims per ledger"],
        "blocked": [],
    }
    return mapping.get(state, [])


def _forbidden_commands(state: str) -> list[str]:
    if state in {"complete_engineering", "interrupted", "incomplete"}:
        return [
            "export-paper-assets without --allow-incomplete",
            "update-claim-ledger --promote-to-supported",
            "fill-paper-from-run --promote-to-supported",
        ]
    if state in {"dry_run_ready", "planned"}:
        return ["score/analyze as scientific evidence"]
    return []


def validate_experiment_state(run_dir: str | Path) -> list[str]:
    result = infer_experiment_state(run_dir)
    issues = list(result.get("issues", []))
    state = result["state"]
    if state not in VALID_STATES:
        issues.append(f"invalid state: {state}")
    if state == "interrupted" and (Path(run_dir) / "paper_assets").exists():
        issues.append("interrupted run has paper_assets — overclaim risk")
    if state == "complete_engineering" and result.get("scientific_evidence"):
        issues.append("engineering run marked scientific_evidence=true")
    return issues
