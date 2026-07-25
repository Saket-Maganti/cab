from pathlib import Path

import pytest

from causal_agent_bench.agents.llm_agents import DirectToolAgent
from causal_agent_bench.agents.llm_clients import LLMResponse, TokenUsage
from causal_agent_bench.environment import BenchmarkEnvironment
from causal_agent_bench.runners.commercial import (
    BudgetPreflightExceededError,
    PaidCallsNotAllowedError,
    enforce_budget_preflight,
    enforce_paid_call_policy,
    finalize_commercial_run_metadata,
)
from causal_agent_bench.runners.config import ExperimentConfig, load_experiment_config
from causal_agent_bench.runners.experiment import run_experiment
from causal_agent_bench.runners.redaction import redact_config_for_persistence
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.utils.io import read_json, read_jsonl

REPO_ROOT = Path(__file__).resolve().parents[1]


class FakeCommercialClient:
    provider_name = "openai"

    def is_configured(self) -> bool:
        return True

    def complete(self, messages, tools, config):
        return LLMResponse(
            content='{"thought": "done", "final_answer": "commercial fake ok", "stop": true}',
            usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            model_name=config.model,
            provider_name=self.provider_name,
            latency_s=0.1,
            estimated_cost_usd=0.001,
            retries=0,
            response_id="fake-commercial-1",
            metadata={"api_version": "fake-v1"},
        )


def _sample_instance() -> BenchmarkInstance:
    instances = read_jsonl(REPO_ROOT / "data/sample/instances.jsonl", BenchmarkInstance)
    return instances[0]


def test_paid_calls_require_explicit_allow_flag():
    config = ExperimentConfig.model_validate(
        {
            "seed": 1,
            "run_name": "paid_blocked",
            "benchmark_path": "data/sample/instances.jsonl",
            "allow_paid_calls": False,
            "agent_runs": [
                {
                    "agent": "direct_tool_agent",
                    "provider": "openai",
                    "model": "gpt-test",
                }
            ],
        }
    )

    with pytest.raises(PaidCallsNotAllowedError):
        enforce_paid_call_policy(config)


def test_budget_preflight_blocks_over_cap():
    config = ExperimentConfig.model_validate(
        {
            "seed": 1,
            "run_name": "budget_blocked",
            "benchmark_path": "data/sample/instances.jsonl",
            "allow_paid_calls": True,
            "budget_cap_usd": 0.01,
            "cost_models": {
                "openai": {
                    "default": {
                        "input_per_1m_tokens": 100.0,
                        "output_per_1m_tokens": 100.0,
                    }
                }
            },
            "agent_runs": [
                {
                    "agent": "direct_tool_agent",
                    "provider": "openai",
                    "model": "gpt-test",
                    "max_tokens": 1000,
                    "extra": {"input_tokens_per_call_estimate": 5000},
                }
            ],
            "max_steps": 4,
        }
    )

    with pytest.raises(BudgetPreflightExceededError):
        enforce_budget_preflight(config)


def test_redaction_strips_secrets_and_environment_dumps():
    raw = {
        "api_key": "sk-live-should-not-persist",
        "environment": {"OPENAI_API_KEY": "secret"},
        "agent_runs": [{"model": "${OPENAI_MODEL_ID:-}"}],
    }

    redacted = redact_config_for_persistence(raw)

    assert redacted["api_key"] == "<redacted>"
    assert "environment" not in redacted
    assert redacted["agent_runs"][0]["model"] == "${OPENAI_MODEL_ID:-}"


def test_commercial_configs_validate_and_require_allow_paid_calls():
    for path in (
        "configs/commercial_api_pilot_small_20.yaml",
        "configs/commercial_api_pilot_medium_100.yaml",
        "configs/commercial_api_main_500.yaml",
        "configs/commercial_api_ablation_20.yaml",
    ):
        config, _ = load_experiment_config(REPO_ROOT / path)
        assert config.allow_paid_calls is True
        enforce_paid_call_policy(config)
        estimate = enforce_budget_preflight(config)
        assert estimate["known_cost_upper_bound_usd"] is not None


def test_fake_commercial_provider_metadata_on_trajectory():
    instance = _sample_instance()
    agent = DirectToolAgent(
        provider="openai",
        model="gpt-fake-commercial",
        client=FakeCommercialClient(),
        pricing={"input_per_1m_tokens": 1.0, "output_per_1m_tokens": 2.0},
        api_version="fake-v1",
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))
    metadata = agent.run_metadata()

    assert action.final_answer is not None
    assert metadata["provider"] == "openai"
    assert metadata["model_id"] == "gpt-fake-commercial"
    assert metadata["api_version"] == "fake-v1"
    assert metadata["sampling_parameters"]["temperature"] == 0.0
    assert metadata["prompt_version_hash"]
    assert metadata["estimated_cost_usd"] == 0.001
    assert metadata["actual_estimated_cost_usd"] == 0.001
    assert metadata["total_retries"] == 0
    assert metadata["llm_calls"][0]["prompt_hash"]


def test_run_metadata_records_preflight_cost_and_finalize_actual_cost(tmp_path):
    config = ExperimentConfig.model_validate(
        {
            "seed": 3,
            "run_name": "commercial_stub_run",
            "benchmark_path": "data/sample/instances.jsonl",
            "allow_paid_calls": False,
            "agent_runs": [
                {
                    "name": "direct_stub",
                    "agent": "direct_tool_agent",
                    "provider": "local_stub",
                    "model": "local-stub",
                    "retry_count": 0,
                }
            ],
            "max_steps": 2,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": False,
        }
    )

    run_dir = run_experiment(config)["run_dir"]
    metadata = read_json(run_dir / "run_metadata.json")

    assert metadata["allow_paid_calls"] is False
    assert metadata["uses_paid_providers"] is False
    assert metadata["cost_estimate_preflight_usd"] == 0.0
    assert metadata["redaction"]["api_keys_persisted"] is False
    saved_config = (run_dir / "config.yaml").read_text(encoding="utf-8")
    assert "sk-" not in saved_config

    finalized = finalize_commercial_run_metadata(run_dir)
    assert finalized["actual_estimated_cost_usd"] == 0.0
    assert "prompt_hashes" in finalized
