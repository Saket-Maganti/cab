from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from causal_agent_bench.phase2 import dry_run_config
from causal_agent_bench.runners.commercial import (
    PaidCallsNotAllowedError,
    PaidRunGateError,
    check_paid_run_gates,
    enforce_paid_call_policy,
    enforce_paid_run_gates,
)
from causal_agent_bench.runners.config import load_experiment_config
from causal_agent_bench.runners.costing import estimate_config_cost
from causal_agent_bench.runners.registries import (
    load_model_pricing_registry,
    load_provider_registry,
    resolve_pricing_from_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_CONFIG = REPO_ROOT / "configs" / "pilot_multi_provider_20.yaml"


def _write_config(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _paid_payload(**overrides) -> dict:
    payload = {
        "seed": 1,
        "run_name": "pricing_test",
        "allow_paid_calls": False,
        "benchmark_path": "data/sample/instances.jsonl",
        "provider_registry_path": "configs/providers.yaml",
        "pricing_registry_path": "configs/model_pricing.yaml",
        "budget": {
            "max_total_usd": 25.0,
            "max_calls": 500,
            "require_explicit_paid_approval": True,
            "strict_pricing": True,
        },
        "agent_runs": [
            {
                "name": "direct_tool_openai",
                "agent": "direct_tool_agent",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "budget_cap_usd": 10.0,
                "max_api_calls": 100,
                "extra": {"input_tokens_per_call_estimate": 500},
            }
        ],
        "max_steps": 2,
        "num_repeats": 1,
        "output_dir": "results",
    }
    payload.update(overrides)
    return payload


def test_provider_and_pricing_registries_load():
    providers = load_provider_registry(REPO_ROOT / "configs/providers.yaml")
    pricing = load_model_pricing_registry(REPO_ROOT / "configs/model_pricing.yaml")
    assert "openai" in providers.providers
    assert any(entry.provider == "openai" and entry.pricing_known for entry in pricing.models)


def test_known_pricing_from_registry(tmp_path):
    config_path = _write_config(tmp_path, _paid_payload())
    config, _ = load_experiment_config(config_path)
    registry = load_model_pricing_registry(REPO_ROOT / "configs/model_pricing.yaml")
    details = config.resolved_pricing_details(
        config.iter_agent_runs()[0],
        pricing_registry=registry,
    )
    assert details["pricing_known"] is True
    assert details["rates"]["input_per_1m_tokens"] == 0.15


def test_unknown_pricing_warning(tmp_path):
    config_path = _write_config(
        tmp_path,
        _paid_payload(
            agent_runs=[
                {
                    "name": "compatible_agent",
                    "agent": "direct_tool_agent",
                    "provider": "openai_compatible",
                    "model": "unknown-model",
                    "budget_cap_usd": 10.0,
                    "max_api_calls": 100,
                    "extra": {"input_tokens_per_call_estimate": 500},
                }
            ],
        ),
    )
    estimate = estimate_config_cost(config_path)
    assert estimate["pricing_known"] is False
    assert estimate["known_cost_upper_bound_usd"] is None
    assert any("Unknown pricing" in warning for warning in estimate["warnings"])
    resolved = resolve_pricing_from_registry(
        load_model_pricing_registry(REPO_ROOT / "configs/model_pricing.yaml"),
        provider="openai_compatible",
        model="unknown-model",
    )
    assert resolved.pricing_known is False


def test_budget_exceeded_blocks_run(tmp_path):
    config_path = _write_config(
        tmp_path,
        _paid_payload(
            budget={
                "max_total_usd": 0.001,
                "max_calls": 500,
                "require_explicit_paid_approval": True,
                "strict_pricing": True,
            }
        ),
    )
    estimate = estimate_config_cost(config_path)
    assert estimate["run_allowed"] is False
    assert any("exceeds budget cap" in reason for reason in estimate["run_blocked_reasons"])


def test_budget_missing_blocks_paid_run(tmp_path):
    payload = _paid_payload()
    payload.pop("budget")
    config_path = _write_config(tmp_path, payload)
    estimate = estimate_config_cost(config_path)
    assert estimate["run_allowed"] is False
    assert any("budget" in reason.lower() for reason in estimate["run_blocked_reasons"])


def test_model_id_env_var_missing_blocks_paid_run(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL_ID", raising=False)
    config_path = _write_config(
        tmp_path,
        _paid_payload(
            agent_runs=[
                {
                    "name": "direct_tool_openai",
                    "agent": "direct_tool_agent",
                    "provider": "openai",
                    "model": "${OPENAI_MODEL_ID:-}",
                    "budget_cap_usd": 10.0,
                    "max_api_calls": 100,
                    "extra": {"input_tokens_per_call_estimate": 500},
                }
            ],
        ),
    )
    estimate = estimate_config_cost(config_path)
    assert estimate["run_allowed"] is False
    assert any("model ID missing" in reason for reason in estimate["run_blocked_reasons"])


def test_provider_disabled_warning_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config_path = _write_config(tmp_path, _paid_payload())
    report = check_paid_run_gates(load_experiment_config(config_path)[0], config_path=config_path)
    assert report["run_allowed"] is False
    assert any("provider key missing" in reason for reason in report["run_blocked_reasons"])


def test_dry_run_allowed_without_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config_path = _write_config(tmp_path, _paid_payload())
    report = dry_run_config(config_path, output_dir=tmp_path / "dry_runs")
    assert report["would_execute"] is True
    assert report["safety"]["will_call_providers"] is False


def test_real_run_blocked_without_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("OPENAI_MODEL_ID", "gpt-4o-mini")
    config_path = _write_config(tmp_path, _paid_payload(allow_paid_calls=False))
    config, _ = load_experiment_config(config_path)
    with pytest.raises(PaidRunGateError):
        enforce_paid_run_gates(config, config_path=config_path)


def test_paid_run_blocked_without_allow_flag_even_if_keys_present(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("OPENAI_MODEL_ID", "gpt-4o-mini")
    config_path = _write_config(tmp_path, _paid_payload(allow_paid_calls=False))
    config, _ = load_experiment_config(config_path)
    with pytest.raises(PaidCallsNotAllowedError):
        enforce_paid_call_policy(config)


def test_estimate_cost_reports_required_fields():
    estimate = estimate_config_cost(PILOT_CONFIG)
    for key in (
        "config_path",
        "dataset_path",
        "number_of_agents",
        "number_of_instances",
        "expected_max_calls",
        "estimated_input_tokens",
        "estimated_output_tokens",
        "per_provider",
        "total_cost_estimate_usd",
        "run_budget_cap_usd",
        "run_allowed",
    ):
        assert key in estimate
    assert estimate["number_of_agents"] == 3
    assert estimate["pricing_known"] is True


def test_pilot_config_estimate_cost_cli():
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
    payload = json.loads(result.stdout)
    assert payload["run_allowed"] is False
    assert payload["total_cost_estimate_usd"] is not None
