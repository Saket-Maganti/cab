from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from causal_agent_bench.phase2 import dry_run_config
from causal_agent_bench.runners.config import load_experiment_config
from causal_agent_bench.runners.metadata import build_run_metadata
from causal_agent_bench.runners.zero_cost import check_zero_cost_readiness

REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_CONFIG = REPO_ROOT / "configs" / "pilot_zero_cost_matrix_20.yaml"
LOCAL_CONFIG = REPO_ROOT / "configs" / "pilot_free_local_20.yaml"


def _write_config(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _zero_cost_payload(**overrides) -> dict:
    payload = {
        "seed": 1,
        "run_name": "zero_cost_test",
        "cost_mode": "zero_cost",
        "allow_paid_calls": False,
        "scientific_evidence_level": "preliminary_or_engineering",
        "provider_type": "local",
        "benchmark_path": "data/sample/instances.jsonl",
        "budget": {
            "max_total_usd": 0,
            "max_calls": 100,
            "require_explicit_paid_approval": True,
            "strict_pricing": False,
        },
        "agent_runs": [
            {
                "name": "direct_tool_local",
                "agent": "direct_tool_agent",
                "provider": "local_openai",
                "model": "test-model",
                "base_url": "http://localhost:11434/v1",
                "budget_cap_usd": 0.0,
                "extra": {"prompt_file": "direct_tool_agent.md"},
            }
        ],
        "max_steps": 2,
        "num_repeats": 1,
        "output_dir": "results",
    }
    payload.update(overrides)
    return payload


def test_zero_cost_matrix_config_validates():
    config, _ = load_experiment_config(MATRIX_CONFIG)
    assert config.cost_mode == "zero_cost"
    assert config.allow_paid_calls is False
    assert config.effective_budget().max_total_usd == 0.0
    assert config.scientific_evidence_level == "preliminary_or_engineering"


def test_zero_cost_config_rejects_paid_openai(tmp_path):
    payload = _zero_cost_payload(
        agent_runs=[
            {
                "name": "bad_openai",
                "agent": "direct_tool_agent",
                "provider": "openai",
                "model": "gpt-test",
                "budget_cap_usd": 0.0,
            }
        ]
    )
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValidationError, match="zero_cost mode does not allow provider 'openai'"):
        load_experiment_config(path)


def test_zero_cost_config_rejects_allow_paid_calls(tmp_path):
    payload = _zero_cost_payload(allow_paid_calls=True)
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValidationError, match="allow_paid_calls: false"):
        load_experiment_config(path)


def test_zero_cost_config_rejects_nonzero_budget(tmp_path):
    payload = _zero_cost_payload(
        budget={"max_total_usd": 5.0, "max_calls": 100, "require_explicit_paid_approval": True}
    )
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValidationError, match="budget cap of 0"):
        load_experiment_config(path)


def test_zero_cost_config_rejects_paid_provider_without_free_tier(tmp_path):
    payload = _zero_cost_payload(
        agent_runs=[
            {
                "name": "bad_gemini",
                "agent": "direct_tool_agent",
                "provider": "gemini",
                "model": "gemini-test",
                "budget_cap_usd": 0.0,
            }
        ]
    )
    path = _write_config(tmp_path, payload)
    with pytest.raises(ValidationError, match="free_tier: true and zero pricing"):
        load_experiment_config(path)


def test_zero_cost_config_accepts_free_tier_gemini(tmp_path):
    payload = _zero_cost_payload(
        provider_type="free_tier",
        agent_runs=[
            {
                "name": "gemini_free",
                "agent": "direct_tool_agent",
                "provider": "gemini",
                "model": "gemini-2.0-flash",
                "budget_cap_usd": 0.0,
                "pricing": {"input_per_1m_tokens": 0.0, "output_per_1m_tokens": 0.0},
                "extra": {"free_tier": True},
            }
        ],
    )
    path = _write_config(tmp_path, payload)
    config, _ = load_experiment_config(path)
    assert config.cost_mode == "zero_cost"


def test_zero_cost_readiness_matrix_reaches_dry_run_ready():
    report = check_zero_cost_readiness(
        MATRIX_CONFIG,
        repo_root=REPO_ROOT,
        dry_run_output_dir=REPO_ROOT / "results" / "dry_runs",
    )
    assert report.verdict in {"dry_run_ready", "zero_cost_ready"}
    assert report.cost_estimate is not None
    assert report.cost_estimate["known_cost_upper_bound_usd"] == 0.0
    assert not any("oracle" in b for b in report.blockers)


def test_zero_cost_dry_run_no_paid_calls():
    report = dry_run_config(
        str(MATRIX_CONFIG),
        output_dir=str(REPO_ROOT / "results" / "dry_runs"),
    )
    assert report["paid_calls_made"] is False
    assert report["scientific_evidence"] is False
    assert report["safety"]["will_call_providers"] is False
    for sim in report.get("simulations") or []:
        assert sim.get("dry_provider") == "local_stub"
        assert sim.get("provider_calls_made") is False


def test_zero_cost_metadata_labels_preliminary():
    config, _ = load_experiment_config(MATRIX_CONFIG)
    metadata = build_run_metadata(
        config,
        config_hash="abc123",
        instances_count=120,
        cost_estimate={"known_cost_upper_bound_usd": 0.0, "budget_status": "within_budget"},
    )
    assert metadata["cost_mode"] == "zero_cost"
    assert metadata["scientific_evidence_level"] == "preliminary_or_engineering"
    assert metadata["paid_calls_made"] is False
    assert metadata["monetary_spend_expected_usd"] == 0.0
    assert "preliminary" in metadata["evidence_scope"]


def test_zero_cost_config_rejects_oracle(tmp_path):
    payload = _zero_cost_payload(
        agent_runs=[
            {
                "name": "oracle_bad",
                "agent": "scripted_oracle_agent",
                "provider": "local_openai",
                "model": "test",
                "base_url": "http://localhost:11434/v1",
                "budget_cap_usd": 0.0,
            }
        ]
    )
    path = _write_config(tmp_path, payload)
    report = check_zero_cost_readiness(path, repo_root=REPO_ROOT, run_dry_run=False)
    oracle_check = next(c for c in report.checks if c.name == "oracle_excluded")
    assert oracle_check.passed is False
    # A failing check keeps the severity declared by its caller.
    assert oracle_check.severity == "error"


def test_zero_cost_passing_checks_report_info_severity():
    report = check_zero_cost_readiness(MATRIX_CONFIG, repo_root=REPO_ROOT, run_dry_run=False)
    # cost_mode_zero_cost is declared severity="error" but passes for a zero-cost
    # config, so a passing check must downgrade its reported severity to "info".
    cost_mode_check = next(c for c in report.checks if c.name == "cost_mode_zero_cost")
    assert cost_mode_check.passed is True
    assert cost_mode_check.severity == "info"
    # No passing check should advertise a failure severity.
    assert all(c.severity == "info" for c in report.checks if c.passed)


def test_check_zero_cost_readiness_script():
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "check_zero_cost_readiness.py"),
            "--config",
            str(MATRIX_CONFIG),
            "--json",
            "--require",
            "dry_run_ready",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["verdict"] in {"dry_run_ready", "zero_cost_ready"}
    assert payload["cost_estimate"]["known_cost_upper_bound_usd"] == 0.0


def test_zero_cost_estimate_cost_cli():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "estimate-cost",
            "--config",
            str(MATRIX_CONFIG),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "0.0" in proc.stdout or "0" in proc.stdout
