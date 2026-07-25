"""Fixture-only provider-pilot preparation tests (no runs, no APIs)."""

from __future__ import annotations

from pathlib import Path

import yaml

from causal_agent_bench.safety.provider_pilot_preflight import validate_provider_pilot_preflight
from causal_agent_bench.safety.run_cost_estimator import estimate_run_cost


def test_dry_run_checklist_no_run_now_instruction() -> None:
    text = Path("docs/PROVIDER_PILOT_DRY_RUN_CHECKLIST.md").read_text(encoding="utf-8")
    assert "dry-run" in text.lower()
    assert "Forbidden before live approval" in text
    assert "run now" not in text.lower()
    assert "claim promotion" in text.lower()


def test_preparation_status_documents_blocked_state() -> None:
    text = Path("PROVIDER_PILOT_PREPARATION_STATUS.md").read_text(encoding="utf-8")
    assert "Blocked" in text
    assert "Commands not to run now" in text
    assert "0" in text


def test_real_template_not_live_run_ready() -> None:
    report = validate_provider_pilot_preflight(
        Path("configs/provider_pilot_tiny_template.yaml"),
        repo_root=Path("."),
    )
    assert report["verdicts"]["ready_for_live_provider_run"] is False
    assert report["gate_summary"]["gate_status"] in {"template_safe_but_not_runnable", "blocked"}


def test_cost_estimator_marks_template_not_runnable() -> None:
    report = estimate_run_cost(Path("configs/provider_pilot_tiny_template.yaml"), repo_root=Path("."))
    assert report["not_runnable_without_approval"] is True
    assert report["template_or_pending_approval"] is True
    assert report["allow_paid_calls"] is False


def test_approval_forms_exist() -> None:
    root = Path("docs/approvals")
    for name in (
        "ADVISOR_APPROVAL_FORM.md",
        "BUDGET_APPROVAL_FORM.md",
        "PROVIDER_MODEL_SELECTION_FORM.md",
        "RISK_ACKNOWLEDGEMENT.md",
        "provider_pilot_approval_schema.json",
    ):
        assert (root / name).exists()


def test_approved_config_has_self_authorization_and_stays_dry_run_only() -> None:
    approval = Path("docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md")
    approved = Path("configs/provider_pilot_tiny_APPROVED.yaml")
    assert approval.exists()
    assert approved.exists()

    approval_text = approval.read_text(encoding="utf-8")
    raw = yaml.safe_load(approved.read_text(encoding="utf-8"))
    assert "Dry-run approval: Yes" in approval_text
    assert "Live-run approval: No" in approval_text
    assert raw["allow_paid_calls"] is False
    assert raw["approval"]["approved_for_dry_run"] is True
    assert raw["approval"]["approved_for_live_run"] is False
    assert raw["budget"]["max_total_usd"] <= 5
    assert raw["budget"]["max_calls"] <= 30
    assert raw["limits"]["max_trajectories"] <= 5
    assert raw["evidence_scope"] == "provider_pilot_debug_or_preliminary"


def test_post_run_checklist_covers_safety_steps() -> None:
    text = Path("docs/POST_PROVIDER_PILOT_CHECKLIST.md").read_text(encoding="utf-8")
    for phrase in (
        "INCOMPLETE_RUN",
        "run-health",
        "validate-paper-assets",
        "claim-evidence",
        "check_evidence_safety",
        "C3",
        "C10",
    ):
        assert phrase in text
