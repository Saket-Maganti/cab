from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from causal_agent_bench.phase2 import dry_run_config
from causal_agent_bench.runners.config import load_experiment_config
from causal_agent_bench.runners.pilot_readiness import check_pilot_readiness
from causal_agent_bench.runners.redaction import redact_config_for_persistence

REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_CONFIG = REPO_ROOT / "configs" / "pilot_multi_provider_20.yaml"


def _write_config(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _base_provider_payload(**overrides) -> dict:
    payload = {
        "seed": 1,
        "run_name": "pilot_test",
        "allow_paid_calls": False,
        "benchmark_path": "data/sample/instances.jsonl",
        "budget_cap_usd": 10.0,
        "max_api_calls": 100,
        "cost_models": {
            "openai": {
                "default": {
                    "input_per_1m_tokens": 2.0,
                    "output_per_1m_tokens": 8.0,
                }
            }
        },
        "agent_runs": [
            {
                "name": "direct_tool_openai",
                "agent": "direct_tool_agent",
                "provider": "openai",
                "model": "gpt-test",
                "temperature": 0.0,
                "max_tokens": 256,
                "retry_count": 1,
                "timeout": 30,
                "budget_cap_usd": 5.0,
                "max_api_calls": 50,
                "extra": {
                    "prompt_file": "direct_tool_agent.md",
                    "prompt_version": "v1",
                    "input_tokens_per_call_estimate": 500,
                },
            }
        ],
        "max_steps": 2,
        "num_repeats": 1,
        "output_dir": "results",
    }
    payload.update(overrides)
    return payload


def test_pilot_config_reaches_cost_estimate_ready_without_keys():
    report = check_pilot_readiness(
        PILOT_CONFIG,
        repo_root=REPO_ROOT,
        dry_run_output_dir=REPO_ROOT / "results" / "dry_runs",
    )
    assert report.verdict in {"dry_run_ready", "cost_estimate_ready"}
    assert report.cost_estimate is not None
    assert report.cost_estimate["known_cost_upper_bound_usd"] is not None
    key_checks = [check for check in report.checks if check.name.startswith("provider_key:")]
    assert key_checks
    assert all(not check.passed for check in key_checks)


def test_missing_provider_key_reported_without_printing_secret(capsys, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = check_pilot_readiness(
        PILOT_CONFIG,
        repo_root=REPO_ROOT,
        run_dry_run=False,
    )
    captured = capsys.readouterr().out + capsys.readouterr().err
    assert "sk-" not in captured
    key_check = next(check for check in report.checks if check.name == "provider_key:openai")
    assert key_check.passed is False
    assert "OPENAI_API_KEY" in key_check.message


def test_missing_model_id_surfaces_env_var_hint(tmp_path):
    config_path = _write_config(
        tmp_path,
        _base_provider_payload(
            agent_runs=[
                {
                    "name": "direct_tool_openai",
                    "agent": "direct_tool_agent",
                    "provider": "openai",
                    "model": "${OPENAI_MODEL_ID:-}",
                    "budget_cap_usd": 5.0,
                    "max_api_calls": 50,
                    "extra": {"prompt_file": "direct_tool_agent.md"},
                }
            ],
        ),
    )
    report = check_pilot_readiness(config_path, repo_root=REPO_ROOT, run_dry_run=False)
    model_check = next(check for check in report.checks if check.name == "model_id:direct_tool_openai")
    assert model_check.passed is True
    assert "OPENAI_MODEL_ID" in model_check.message
    assert "empty" in model_check.message.lower() or "expected env" in model_check.message.lower()


def test_missing_pricing_marks_cost_unknown(tmp_path):
    config_path = _write_config(
        tmp_path,
        _base_provider_payload(
            pricing_registry_path=None,
            cost_models={},
            agent_runs=[
                {
                    "name": "direct_tool_openai",
                    "agent": "direct_tool_agent",
                    "provider": "openai",
                    "model": "gpt-test",
                    "budget_cap_usd": 5.0,
                    "max_api_calls": 50,
                    "extra": {"prompt_file": "direct_tool_agent.md"},
                }
            ],
        ),
    )
    report = check_pilot_readiness(config_path, repo_root=REPO_ROOT, run_dry_run=False)
    pricing_check = next(check for check in report.checks if check.name == "pricing:direct_tool_openai")
    assert pricing_check.passed is False
    assert report.cost_estimate is not None
    assert report.cost_estimate["known_cost_upper_bound_usd"] is None


def test_budget_cap_exceeded_is_blocking(tmp_path):
    config_path = _write_config(
        tmp_path,
        _base_provider_payload(
            budget_cap_usd=0.0001,
            agent_runs=[
                {
                    "name": "direct_tool_openai",
                    "agent": "direct_tool_agent",
                    "provider": "openai",
                    "model": "gpt-test",
                    "budget_cap_usd": 5.0,
                    "max_api_calls": 50,
                    "max_tokens": 4000,
                    "extra": {
                        "prompt_file": "direct_tool_agent.md",
                        "input_tokens_per_call_estimate": 5000,
                    },
                }
            ],
            max_steps=8,
        ),
    )
    report = check_pilot_readiness(config_path, repo_root=REPO_ROOT, run_dry_run=False)
    budget_check = next(check for check in report.checks if check.name == "budget_preflight_within_cap")
    assert budget_check.passed is False
    assert report.verdict == "not_ready"


def test_dry_run_does_not_call_providers(tmp_path):
    config_path = _write_config(tmp_path, _base_provider_payload())
    report = dry_run_config(config_path, output_dir=tmp_path / "dry_runs")
    assert report["would_execute"] is True
    assert report["safety"]["will_call_providers"] is False
    assert report["safety"]["provider_calls_replaced_with_local_stub"] is True
    readiness = check_pilot_readiness(
        config_path,
        repo_root=REPO_ROOT,
        dry_run_output_dir=tmp_path / "dry_runs",
    )
    dry_check = next(check for check in readiness.checks if check.name == "dry_run_works")
    assert dry_check.passed is True


def test_api_keys_redacted_in_persisted_config_and_metadata(tmp_path):
    raw = _base_provider_payload()
    raw_with_secret = dict(raw)
    raw_with_secret["api_key"] = "sk-live-should-not-persist"
    redacted = redact_config_for_persistence(raw_with_secret)
    assert redacted["api_key"] == "<redacted>"

    config_path = _write_config(tmp_path, _base_provider_payload())
    report = check_pilot_readiness(config_path, repo_root=REPO_ROOT, run_dry_run=False)
    redaction_check = next(
        check for check in report.checks if check.name == "api_keys_redacted_in_metadata"
    )
    assert redaction_check.passed is True


def test_oracle_agent_rejected_in_provider_pilot_config(tmp_path):
    payload = _base_provider_payload(
        agent_runs=[
            {
                "name": "oracle_openai",
                "agent": "scripted_oracle_agent",
                "provider": "openai",
                "model": "gpt-test",
                "budget_cap_usd": 5.0,
                "max_api_calls": 50,
            }
        ],
    )
    config_path = _write_config(tmp_path, payload)
    with pytest.raises(ValueError):
        load_experiment_config(config_path)


def test_required_run_metadata_fields_declared(tmp_path):
    config_path = _write_config(tmp_path, _base_provider_payload())
    report = check_pilot_readiness(config_path, repo_root=REPO_ROOT, run_dry_run=False)
    metadata_check = next(check for check in report.checks if check.name == "metadata_fields_declared")
    assert metadata_check.passed is True
    assert report.metadata_preview is not None
    assert report.metadata_preview["redaction"]["api_keys_persisted"] is False


def test_check_pilot_readiness_script_runs():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_pilot_readiness.py",
            "--config",
            "configs/pilot_multi_provider_20.yaml",
            "--require",
            "cost_estimate_ready",
            "--json",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["verdict"] in {"cost_estimate_ready", "paid_pilot_ready"}
    assert payload["dry_run"]["provider_calls_made"] is False


def test_estimate_cost_cli_after_config_update():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "estimate-cost",
            "--config",
            "configs/pilot_multi_provider_20.yaml",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "known_cost_upper_bound_usd" in result.stdout
    assert "null" not in result.stdout.split("known_cost_upper_bound_usd")[1][:40]
