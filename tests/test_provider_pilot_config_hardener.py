from __future__ import annotations

from pathlib import Path

import yaml

from causal_agent_bench.safety.provider_pilot_config_hardener import (
    build_provider_pilot_config_hardening_report,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_template_is_blocked_as_candidate(tmp_path: Path) -> None:
    cfg = tmp_path / "provider_pilot_tiny_template.yaml"
    _write(
        cfg,
        {
            "run_name": "provider_pilot_template",
            "output_dir": "results",
            "evidence_scope": "provider_pilot_pending_verification",
            "allow_paid_calls": False,
            "limits": {"max_instances": 5, "max_runtime_minutes": 10, "stop_after_trajectories": 5},
            "budget_cap_usd": 5,
            "agent_runs": [{"agent": "react", "provider": "anthropic", "model": "claude-3-sonnet"}],
        },
    )
    report = build_provider_pilot_config_hardening_report(tmp_path, config_path=cfg, output_dir=tmp_path / "out")
    assert report["verdicts"]["blocked"] is True
    assert any(c["id"] == "template_used_as_candidate" for c in report["blockers"])


def test_missing_budget_cap_blocks(tmp_path: Path) -> None:
    cfg = tmp_path / "approved_pilot.yaml"
    _write(
        cfg,
        {
            "run_name": "approved_pilot",
            "output_dir": "results",
            "evidence_scope": "provider_pilot_pending_verification",
            "allow_paid_calls": False,
            "limits": {"max_instances": 5, "max_runtime_minutes": 10, "stop_after_trajectories": 5},
            "agent_runs": [{"agent": "react", "provider": "anthropic", "model": "claude-3-sonnet"}],
        },
    )
    report = build_provider_pilot_config_hardening_report(tmp_path, config_path=cfg, output_dir=tmp_path / "out")
    assert any(c["id"] == "missing_budget_cap" for c in report["blockers"])


def test_oracle_agent_is_blocked(tmp_path: Path) -> None:
    cfg = tmp_path / "approved_pilot.yaml"
    _write(
        cfg,
        {
            "run_name": "approved_pilot",
            "output_dir": "results",
            "evidence_scope": "provider_pilot_pending_verification",
            "allow_paid_calls": False,
            "limits": {"max_instances": 5, "max_runtime_minutes": 10, "stop_after_trajectories": 5},
            "budget_cap_usd": 5,
            "agent_runs": [{"agent": "oracle_baseline", "provider": "anthropic", "model": "claude"}],
        },
    )
    report = build_provider_pilot_config_hardening_report(tmp_path, config_path=cfg, output_dir=tmp_path / "out")
    assert any(c["id"] == "non_evidence_agent" for c in report["blockers"])


def test_scientific_evidence_true_blocked(tmp_path: Path) -> None:
    cfg = tmp_path / "approved_pilot.yaml"
    _write(
        cfg,
        {
            "run_name": "approved_pilot",
            "output_dir": "results",
            "evidence_scope": "provider_pilot_pending_verification",
            "scientific_evidence": True,  # forbidden
            "allow_paid_calls": False,
            "limits": {"max_instances": 5, "stop_after_trajectories": 5},
            "budget_cap_usd": 5,
            "agent_runs": [{"agent": "react", "provider": "anthropic", "model": "claude"}],
        },
    )
    report = build_provider_pilot_config_hardening_report(tmp_path, config_path=cfg, output_dir=tmp_path / "out")
    assert any("forbidden_field_true" in c["id"] for c in report["blockers"])
    assert report["verdicts"]["any_forbidden_true"] is True


def test_clean_candidate_passes(tmp_path: Path) -> None:
    cfg = tmp_path / "approved_pilot.yaml"
    _write(
        cfg,
        {
            "run_name": "approved_pilot_small",
            "output_dir": "results",
            "evidence_scope": "provider_pilot_pending_verification",
            "allow_paid_calls": False,
            "scientific_evidence": False,
            "limits": {"max_instances": 5, "max_runtime_minutes": 10, "stop_after_trajectories": 5},
            "budget_cap_usd": 5,
            "agent_runs": [{"agent": "react", "provider": "anthropic", "model": "claude-3-sonnet"}],
            "approval": {"advisor_approved": False, "approved_for_dry_run": False, "budget_approved": False},
        },
    )
    report = build_provider_pilot_config_hardening_report(tmp_path, config_path=cfg, output_dir=tmp_path / "out")
    assert report["verdicts"]["blocked"] is False
    assert report["verdicts"]["candidate_safe_to_send_to_preflight"] is True


def test_missing_config_is_blocked(tmp_path: Path) -> None:
    report = build_provider_pilot_config_hardening_report(tmp_path, config_path=tmp_path / "missing.yaml", output_dir=tmp_path / "out")
    assert report["verdicts"]["blocked"] is True
    assert any(c["id"] == "config_missing" for c in report["blockers"])
