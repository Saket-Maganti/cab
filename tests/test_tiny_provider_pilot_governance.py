from __future__ import annotations

import json
from pathlib import Path

import yaml

from causal_agent_bench.safety.provider_pilot_preflight import validate_provider_pilot_preflight
from causal_agent_bench.safety.tiny_provider_pilot import (
    BLOCKED_FINAL_CLAIMS,
    MAX_TINY_PROVIDER_TRAJECTORIES,
    REQUIRED_POSTRUN_REPORTS,
    SCORER_SANITY_ISSUE_CATEGORIES,
    analyze_live_authorization_text,
    audit_tiny_provider_config_lock,
    audit_tiny_provider_postrun_artifacts,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _provider_run(tmp_path: Path, *, trajectories: int = 1, metadata: dict | None = None) -> Path:
    run_dir = tmp_path / "results" / "tiny_provider"
    run_dir.mkdir(parents=True, exist_ok=True)
    base_meta = {
        "run_name": "provider_pilot_tiny_APPROVED",
        "config_hash": "testhash",
        "evidence_scope": "provider_pilot_debug_or_preliminary",
        "provider_type": "openai",
        "providers": ["openai"],
        "scientific_evidence": False,
        "allow_paid_calls": False,
        "agents": ["direct_tool_provider_pilot"],
        "n_instances": trajectories,
        "num_repeats": 1,
    }
    if metadata:
        base_meta.update(metadata)
    _write_json(run_dir / "run_metadata.json", base_meta)
    _write_json(
        run_dir / "checkpoint.json",
        {"completed": trajectories, "total": trajectories, "status": "complete"},
    )
    rows = [
        {"instance_id": f"task_{idx}.clean", "agent_name": "direct_tool_provider_pilot"}
        for idx in range(trajectories)
    ]
    run_dir.joinpath("trajectories.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return run_dir


def _write_required_reports(reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    for filename in REQUIRED_POSTRUN_REPORTS.values():
        (reports_dir / filename).write_text("fixture\n", encoding="utf-8")


def _approved_config_payload(**updates: object) -> dict:
    payload = {
        "run_name": "provider_pilot_tiny_APPROVED",
        "benchmark_path": "data/instances.jsonl",
        "allow_paid_calls": False,
        "budget_cap_usd": 5.0,
        "evidence_scope": "provider_pilot_debug_or_preliminary",
        "scientific_evidence": False,
        "require_dry_run_before_live": True,
        "max_instances": 1,
        "limits": {
            "max_trajectories": 1,
            "stop_after_trajectories": 1,
            "max_runtime_minutes": 10,
            "max_steps_per_instance": 4,
        },
        "agent_runs": [
            {
                "name": "direct_tool_provider_pilot",
                "agent": "direct_tool_agent",
                "provider": "openai",
                "model": "gpt-4o-mini",
            }
        ],
        "approval": {
            "advisor_approved": True,
            "budget_approved": True,
            "approved_for_dry_run": True,
            "approved_for_live_run": False,
            "approved_by": "Saket Maganti",
            "approval_date": "2026-06-13",
            "advisor_approval_id": "SELF-AUTHORIZATION-TINY-PROVIDER-PILOT",
            "max_budget_usd": 5.0,
        },
    }
    payload.update(updates)
    return payload


def test_live_authorization_requires_unambiguous_live_approval() -> None:
    text = """
    Live-run approval: Yes

    I authorize only the dry-run/preflight preparation stage at this time.
    I do not authorize live paid provider calls yet.
    """
    report = analyze_live_authorization_text(text)
    assert report["live_approval_marker"] is True
    assert report["explicit_live_approval"] is False
    assert report["contradictions"]


def test_allow_paid_calls_cannot_remain_true_after_run(tmp_path: Path) -> None:
    config = tmp_path / "provider_pilot_tiny_APPROVED.yaml"
    config.write_text(
        yaml.safe_dump({"run_name": "provider_pilot_tiny_APPROVED", "allow_paid_calls": True}),
        encoding="utf-8",
    )
    report = audit_tiny_provider_config_lock(config)
    assert report["locked"] is False
    assert {issue["id"] for issue in report["issues"]} == {"allow_paid_calls_still_true"}


def test_tiny_provider_postrun_requires_manual_review_and_scorer_sanity(tmp_path: Path) -> None:
    run_dir = _provider_run(tmp_path)
    report = audit_tiny_provider_postrun_artifacts(run_dir, reports_dir=tmp_path / "reports")
    issue_ids = {issue["id"] for issue in report["issues"]}
    assert "trajectory_review_missing" in issue_ids
    assert "scorer_sanity_markdown_missing" in issue_ids
    assert "scorer_sanity_csv_missing" in issue_ids
    assert "postrun_audit_missing" in issue_ids
    assert report["paper_evidence_allowed"] is False


def test_incomplete_provider_run_is_blocked_from_evidence(tmp_path: Path) -> None:
    run_dir = _provider_run(tmp_path, trajectories=3)
    _write_required_reports(tmp_path / "reports")
    _write_json(run_dir / "checkpoint.json", {"completed": 1, "total": 3, "status": "interrupted"})
    _write_json(run_dir / "INCOMPLETE_RUN.json", {"reason": "fixture interruption"})
    report = audit_tiny_provider_postrun_artifacts(run_dir, reports_dir=tmp_path / "reports")
    issue_ids = {issue["id"] for issue in report["issues"]}
    assert "incomplete_provider_run_blocked_from_evidence" in issue_ids
    assert report["paper_evidence_allowed"] is False


def test_tiny_provider_caps_trajectories_and_cannot_promote_final_claims(tmp_path: Path) -> None:
    run_dir = _provider_run(
        tmp_path,
        trajectories=MAX_TINY_PROVIDER_TRAJECTORIES + 1,
        metadata={"claims_promoted": ["C1", "C10"]},
    )
    _write_required_reports(tmp_path / "reports")
    report = audit_tiny_provider_postrun_artifacts(run_dir, reports_dir=tmp_path / "reports")
    issue_ids = {issue["id"] for issue in report["issues"]}
    assert "trajectory_cap_exceeded" in issue_ids
    assert "final_claim_promotion_forbidden" in issue_ids
    assert {"C1", "C10"} <= BLOCKED_FINAL_CLAIMS


def test_tiny_provider_yaml_rejects_api_keys(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "POST_PROVIDER_PILOT_CHECKLIST.md").write_text("checklist", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "instances.jsonl").write_text("{}\n", encoding="utf-8")
    config = tmp_path / "provider_pilot_tiny_APPROVED.yaml"
    config.write_text(
        yaml.safe_dump(_approved_config_payload(api_key="placeholder-secret-should-never-be-here")),
        encoding="utf-8",
    )
    report = validate_provider_pilot_preflight(config, repo_root=tmp_path)
    blocker_ids = {check["id"] for check in report["checks"] if check["severity"] == "blocker"}
    assert "api_key_in_config" in blocker_ids


def test_scorer_sanity_categories_are_closed_set() -> None:
    expected = {
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
    assert expected == SCORER_SANITY_ISSUE_CATEGORIES
