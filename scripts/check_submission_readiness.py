#!/usr/bin/env python3
"""Classify submission and experiment readiness without running model jobs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.runners.index_runs import index_runs
from causal_agent_bench.safety.common import classify_run_entry

READINESS_LEVELS = (
    "engineering_scaffold",
    "deterministic_prototype",
    "local_preliminary",
    "provider_pilot",
    "main_experiment_ready",
    "submission_ready",
)


def _load_claim_ledger() -> dict:
    return json.loads((REPO_ROOT / "docs" / "claim_ledger.json").read_text(encoding="utf-8"))


def _run_script(script: str, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def classify_readiness(repo_root: Path = REPO_ROOT) -> dict:
    runs = index_runs(repo_root / "results")
    classified_runs = [classify_run_entry(run, repo_root) for run in runs]
    blockers: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    completed_non_oracle = [
        run
        for run in runs
        if run["completion_state"] == "complete"
        and not run["oracle_agents"]
        and run["status"] not in {"dry_run", "interrupted"}
    ]
    provider_runs = [
        run
        for run in classified_runs
        if run["classification"] in {"provider_backed_pilot", "main_benchmark"} and run["paper_eligible"]
    ]
    local_runs = [
        run
        for run in completed_non_oracle
        if run.get("provider_type") == "local" or "local" in str(run.get("path", "")).lower()
    ]
    stub_runs = [
        run
        for run in runs
        if run["completion_state"] == "complete" and "stub" in str(run.get("run_name", "")).lower()
    ]
    interrupted_used = [
        run for run in runs if run["status"] == "interrupted" and run.get("key_metrics")
    ]

    if not completed_non_oracle:
        blockers.append("No completed non-oracle run exists.")
        next_actions.append("Complete a stub or micro mock run for engineering validation.")
    if not provider_runs:
        blockers.append("No completed provider-backed non-oracle pilot run.")
        next_actions.append("Run a bounded paid pilot with explicit budget approval.")
    if any(run["status"] == "interrupted" for run in runs):
        warnings.append("Interrupted runs present in results index.")
    if interrupted_used:
        blockers.append("Incomplete runs appear indexed with metrics (do not use as evidence).")

    ledger = _load_claim_ledger()
    unsupported = [
        claim["claim_id"]
        for claim in ledger.get("claims", [])
        if claim.get("claim_id", "").startswith("C") and claim.get("status") not in {"planned", "engineering_only"}
    ]
    if unsupported:
        blockers.append(f"Claims marked beyond planned/engineering_only: {unsupported}")

    human_val = repo_root / "data" / "human_validation" / "sample.jsonl"
    if not human_val.exists():
        blockers.append("Human validation sample/annotations missing.")
        next_actions.append("Export and annotate a human validation sample.")

    sec_rc, _ = _run_script("security_check.py")
    if sec_rc != 0:
        blockers.append("security_check.py failed.")

    paper_draft_rc, _ = _run_script("validate_paper_assets.py", "--mode", "draft")
    if paper_draft_rc != 0:
        warnings.append("Paper asset draft validation reported issues.")

    paper_sub_rc, _ = _run_script("validate_paper_assets.py", "--mode", "submission")
    if paper_sub_rc != 0:
        blockers.append("Paper asset submission validation failed.")

    placeholder_rc, _ = _run_script("check_paper_placeholders.py", "--mode", "submission")
    if placeholder_rc != 0:
        blockers.append("Paper placeholders remain (submission mode).")

    level = "engineering_scaffold"
    if stub_runs:
        level = "deterministic_prototype"
    if local_runs:
        level = "local_preliminary"
    if provider_runs:
        level = "provider_pilot"
    if provider_runs and len(completed_non_oracle) >= 3:
        level = "main_experiment_ready"

    submission_ready = level in {"main_experiment_ready", "submission_ready"} and not blockers
    if submission_ready:
        level = "submission_ready"

    return {
        "level": level,
        "submission_ready": submission_ready,
        "completed_non_oracle_runs": len(completed_non_oracle),
        "provider_pilot_runs": len(provider_runs),
        "local_preliminary_runs": len(local_runs),
        "stub_runs": len(stub_runs),
        "blockers": blockers,
        "warnings": warnings,
        "next_required_actions": next_actions,
    }


def main() -> int:
    report = classify_readiness()
    print("# Submission readiness")
    print(f"- classification: {report['level']}")
    print(f"- submission_ready: {report['submission_ready']}")
    print(f"- completed_non_oracle_runs: {report['completed_non_oracle_runs']}")
    print(f"- provider_pilot_runs: {report['provider_pilot_runs']}")
    if report["blockers"]:
        print("\n## Blockers")
        for item in report["blockers"]:
            print(f"- {item}")
    if report["warnings"]:
        print("\n## Warnings")
        for item in report["warnings"]:
            print(f"- {item}")
    if report["next_required_actions"]:
        print("\n## Next required actions")
        for item in report["next_required_actions"]:
            print(f"- {item}")
    return 0 if report["submission_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
