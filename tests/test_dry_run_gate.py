from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from causal_agent_bench.phase2 import dry_run_config
from causal_agent_bench.runners.config import load_experiment_config
from causal_agent_bench.utils.io import read_json

REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_CONFIG = REPO_ROOT / "configs" / "pilot_multi_provider_20.yaml"


def _write_config(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _paid_payload(**overrides) -> dict:
    payload = {
        "seed": 1,
        "run_name": "dry_run_gate_test",
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


def test_pilot_multi_provider_dry_run_has_required_fields(tmp_path):
    report = dry_run_config(PILOT_CONFIG, output_dir=tmp_path / "dry_runs")
    assert report["dry_run"] is True
    assert report["would_execute"] is True
    assert report["paid_calls_made"] is False
    assert report["scientific_evidence"] is False
    assert report["config_hash"]
    assert report["provider_readiness"]["uses_paid_providers"] is True
    assert report["model_id_warnings"]
    assert report["cost_summary"]["total_cost_estimate_usd"] is not None
    assert report["cost_summary"]["budget_status"] == "within_budget"
    assert report["safety"]["will_call_providers"] is False
    report_dir = Path(report["report_dir"])
    assert (report_dir / "config.yaml").exists()
    assert (report_dir / "config_hash.txt").exists()
    assert (report_dir / "dry_run_metadata.json").exists()
    assert (report_dir / "simulations.jsonl").exists()
    metadata = read_json(report_dir / "dry_run_metadata.json")
    assert metadata["paid_calls_made"] is False
    assert metadata["scientific_evidence"] is False


def test_dry_run_never_invokes_paid_provider_client(tmp_path):
    from causal_agent_bench.agents import llm_agents

    config_path = _write_config(tmp_path, _paid_payload())
    providers_used: list[str] = []
    real_get = llm_agents.get_llm_client

    def tracking_get(provider: str):
        providers_used.append(provider)
        return real_get(provider)

    with patch.object(llm_agents, "get_llm_client", side_effect=tracking_get):
        report = dry_run_config(config_path, output_dir=tmp_path / "dry_runs")
    assert report["paid_calls_made"] is False
    assert all(sim.get("provider_calls_made") is False for sim in report["simulations"])
    assert providers_used
    assert all(provider == "local_stub" for provider in providers_used)


def test_dry_run_output_redacts_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-should-not-appear-in-dry-run")
    config_path = _write_config(tmp_path, _paid_payload())
    report = dry_run_config(config_path, output_dir=tmp_path / "dry_runs")
    saved = Path(report["report_dir"]) / "config.yaml"
    text = saved.read_text(encoding="utf-8")
    dumped = json.dumps(report)
    assert "sk-test-should-not-appear-in-dry-run" not in text
    assert "sk-test-should-not-appear-in-dry-run" not in dumped


def test_oracle_provider_config_rejected(tmp_path):
    config_path = _write_config(
        tmp_path,
        _paid_payload(
            agent_runs=[
                {
                    "name": "oracle_openai",
                    "agent": "scripted_oracle_agent",
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "budget_cap_usd": 10.0,
                    "max_api_calls": 100,
                }
            ],
        ),
    )
    with pytest.raises(ValueError):
        load_experiment_config(config_path)


def test_dry_run_includes_cost_estimate_and_prompt_hashes(tmp_path):
    config_path = _write_config(tmp_path, _paid_payload())
    report = dry_run_config(config_path, output_dir=tmp_path / "dry_runs")
    assert report["cost_estimate"]["total_cost_estimate_usd"] is not None
    assert report["cost_summary"]["expected_max_calls"] > 0
    assert isinstance(report["prompt_hashes"], list)
    assert report["prompt_hashes"] or all(
        sim.get("prompt_version_hash") for sim in report["simulations"] if sim.get("ok")
    )
