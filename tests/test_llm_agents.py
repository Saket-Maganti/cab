import json
import os
from pathlib import Path

import pytest

from causal_agent_bench.agents.llm_agents import (
    DirectLLMToolAgent,
    DirectToolAgent,
    MemoryVerifyingLLMAgent,
    PlannerExecutorAgent,
    PlannerExecutorLLMAgent,
    ReActStyleLLMAgent,
    RecoveryPromptLLMAgent,
    SelfCheckAgent,
    SelfCheckingLLMAgent,
    ToolConservativeLLMAgent,
)
from causal_agent_bench.agents.llm_clients import (
    LLMResponse,
    LocalOpenAICompatibleClient,
    LocalStubLLMClient,
    ModelConfig,
    OpenAIClient,
    OpenAICompatibleClient,
    ProviderConfigurationError,
    ProviderRateLimitError,
    TokenUsage,
    list_provider_status,
)
from causal_agent_bench.environment import BenchmarkEnvironment
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.costing import estimate_experiment_cost
from causal_agent_bench.runners.experiment import run_experiment
from causal_agent_bench.schemas import BenchmarkInstance, Trajectory
from causal_agent_bench.tools import ToolRegistry
from causal_agent_bench.utils.io import read_json, read_jsonl

REPO_ROOT = Path(__file__).resolve().parents[1]


def _sample_instance(index: int = 0) -> BenchmarkInstance:
    return read_jsonl(REPO_ROOT / "data/sample/instances.jsonl", BenchmarkInstance)[index]


def read_json_from_message(content: str) -> dict:
    parsed = json.loads(content)
    assert isinstance(parsed, dict)
    return parsed


def _travel_tool_response() -> dict:
    return {
        "tool_calls": [
            {
                "name": "search_database",
                "arguments": {"query": "refundable hotel Boston", "domain": "travel"},
                "call_id": "stub-search",
            }
        ],
        "content": '{"thought": "Need hotel evidence."}',
    }


def _price_tool_response() -> dict:
    return {
        "tool_calls": [
            {
                "name": "calculate_price",
                "arguments": {
                    "items": [{"id": "saver_hotel", "price": 160, "quantity": 1}],
                    "constraints": {"tax_rate": 0.1, "currency": "USD"},
                },
                "call_id": "stub-price",
            }
        ],
        "content": '{"thought": "Need price calculation."}',
    }


def test_direct_tool_agent_executes_tool_call():
    instance = _sample_instance(0)
    agent = DirectToolAgent(client=LocalStubLLMClient([_travel_tool_response()]))
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))
    step = env.step(action)

    assert step["action"]["tool_call"]["tool_name"] == "search_database"
    assert step["observation"]["tool_name"] == "search_database"
    assert step["observation"]["error"] is None
    assert step["action"]["metadata"]["llm_calls"][0]["estimated_cost_usd"] == 0.0


def test_invalid_tool_call_is_logged_by_environment():
    instance = _sample_instance(0)
    agent = DirectToolAgent(
        client=LocalStubLLMClient(
            [
                {
                    "tool_calls": [
                        {
                            "name": "live_web_search",
                            "arguments": {"query": "forbidden"},
                            "call_id": "bad-call",
                        }
                    ]
                }
            ]
        )
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    step = env.step(agent.act(env.steps, env.registry.specs(env.available_tools)))

    assert step["observation"]["error"] == "unknown_tool"
    assert "live_web_search" not in env.registry.names


def test_max_steps_are_enforced_for_llm_agent():
    instance = _sample_instance(0)
    loop_client = LocalStubLLMClient([_travel_tool_response()], repeat_last=True)
    agent = DirectToolAgent(client=loop_client)
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    env.max_steps = 1
    agent.reset(instance, seed=1)

    env.step(agent.act(env.steps, env.registry.specs(env.available_tools)))

    assert env.done is True
    assert env.terminated_reason == "max_steps"


def test_tool_failure_is_visible_to_agent_and_final_answer_recorded():
    instance = next(
        item
        for item in read_jsonl(REPO_ROOT / "data/sample/instances.jsonl", BenchmarkInstance)
        if item.intervention is not None and item.intervention.family == "tool_failure"
    )
    agent = DirectToolAgent(
        client=LocalStubLLMClient(
                [
                _price_tool_response(),
                {
                    "content": (
                        '{"thought": "The previous observation showed simulated_tool_failure.", '
                        '"final_answer": "Unable to answer confidently because the required tool failed.", '
                        '"stop": true}'
                    )
                },
            ]
        )
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    env.step(agent.act(env.steps, env.registry.specs(env.available_tools)))
    env.step(agent.act(env.steps, env.registry.specs(env.available_tools)))
    trajectory = env.trajectory()

    assert trajectory.steps[0]["observation"]["error"] == "simulated_tool_failure"
    assert "failed" in (trajectory.final_answer or "").lower()
    assert trajectory.terminated_reason == "final_answer"


def test_planner_executor_agent_uses_plan_then_tool():
    instance = _sample_instance(0)
    agent = PlannerExecutorAgent(
        client=LocalStubLLMClient(
            [
                {"content": '{"plan": ["search for refundable hotels"]}'},
                _travel_tool_response(),
            ]
        )
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))

    assert agent.plan is not None
    assert action.tool_call is not None
    assert len(agent.llm_calls) == 2
    assert agent.llm_calls[0]["phase"] == "plan"


def test_self_check_agent_verifies_before_final_answer():
    instance = _sample_instance(0)
    agent = SelfCheckAgent(
        client=LocalStubLLMClient(
            [
                {"content": '{"thought": "Candidate ready.", "final_answer": "saver_hotel 176", "stop": true}'},
                {
                    "tool_calls": [
                        {
                            "name": "verify_fact",
                            "arguments": {
                                "claim": "saver_hotel total is 176",
                                "evidence_ids": ["travel_saver_hotel"],
                            },
                        }
                    ],
                    "content": '{"thought": "Need verification before final."}',
                },
            ]
        )
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))

    assert action.tool_call is not None
    assert action.tool_call.tool_name == "verify_fact"
    assert action.metadata["candidate_final_answer"] == "saver_hotel 176"


def test_runner_records_llm_metadata_with_local_stub(tmp_path):
    config = ExperimentConfig.model_validate(
        {
            "seed": 7,
            "run_name": "llm_stub",
            "benchmark_path": "data/sample/instances.jsonl",
            "agent_runs": [
                {
                    "name": "direct_stub",
                    "agent": "direct_tool_agent",
                    "provider": "local_stub",
                    "model": "local-stub",
                    "max_tokens": 64,
                }
            ],
            "max_steps": 2,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )

    run_dir = run_experiment(config)["run_dir"]
    trajectories = read_jsonl(run_dir / "trajectories.jsonl", Trajectory)
    aggregate = read_json(run_dir / "aggregate_summary.json")

    assert trajectories
    assert trajectories[0].agent_name == "direct_stub"
    assert trajectories[0].metadata["provider"] == "local_stub"
    assert "token_usage" in trajectories[0].metadata
    assert "estimated_cost_usd" in trajectories[0].metadata
    assert "model_call_count" in trajectories[0].metadata
    assert "tool_call_count" in trajectories[0].metadata
    assert aggregate["n_agents"] == 1
    assert "avg_cost_per_task_usd" in aggregate["by_agent"]["direct_stub"]


def test_cost_estimate_treats_local_stub_as_zero_cost():
    config = ExperimentConfig.model_validate(
        {
            "seed": 7,
            "run_name": "estimate",
            "benchmark_path": "data/sample/instances.jsonl",
            "agent_runs": [
                {
                    "name": "direct_stub",
                    "agent": "direct_tool_agent",
                    "provider": "local_stub",
                    "model": "local-stub",
                    "max_tokens": 64,
                }
            ],
            "max_steps": 2,
        }
    )

    estimate = estimate_experiment_cost(config)

    assert estimate["instances"] == 9
    assert estimate["agent_runs"][0]["llm_calls_upper_bound"] == 18
    assert estimate["agent_runs"][0]["known_output_cost_upper_bound_usd"] == 0.0


def test_cost_model_config_estimates_provider_model_cost():
    config = ExperimentConfig.model_validate(
        {
            "seed": 7,
            "run_name": "estimate_cost_model",
            "benchmark_path": "data/sample/instances.jsonl",
            "agent_runs": [
                {
                    "name": "direct_openai",
                    "agent": "direct_tool_agent",
                    "provider": "openai",
                    "model": "fake-model",
                    "max_tokens": 100,
                    "extra": {"input_tokens_per_call_estimate": 50},
                }
            ],
            "cost_models": {
                "openai": {
                    "fake-model": {
                        "input_per_1m_tokens": 1.0,
                        "output_per_1m_tokens": 2.0,
                    }
                }
            },
            "max_steps": 2,
        }
    )

    estimate = estimate_experiment_cost(config)
    row = estimate["agent_runs"][0]

    assert row["pricing_source"] == "cost_models.openai.fake-model"
    assert row["input_tokens_upper_bound"] == 900
    assert row["output_tokens_upper_bound"] == 1800
    assert row["known_cost_upper_bound_usd"] == 0.0045


def test_openai_missing_api_key_fails_without_printing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = OpenAIClient()

    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        client.complete([], [], ModelConfig(provider="openai", model="test-model"))


class CountingFakeClient:
    provider_name = "fake_provider"

    def __init__(self) -> None:
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    def complete(self, messages, tools, config):
        self.calls += 1
        return LLMResponse(
            content='{"thought": "cached answer", "final_answer": "cached final", "stop": true}',
            usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
            model_name=config.model,
            provider_name=self.provider_name,
            latency_s=0.123,
            estimated_cost_usd=0.0001,
            response_id=f"fake-{self.calls}",
        )


class CapturingFakeClient:
    provider_name = "capturing_fake"

    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.calls = []

    def is_configured(self) -> bool:
        return True

    def complete(self, messages, tools, config):
        self.calls.append({"messages": messages, "tools": tools, "config": config})
        response = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        return LLMResponse(
            content=response.get("content"),
            tool_calls=[],
            usage=TokenUsage(input_tokens=1, output_tokens=1, total_tokens=2),
            model_name=config.model,
            provider_name=self.provider_name,
            latency_s=0.0,
            estimated_cost_usd=0.0,
        )


class RateLimitedFakeClient:
    provider_name = "fake_rate_limited"

    def is_configured(self) -> bool:
        return True

    def complete(self, messages, tools, config):
        raise ProviderRateLimitError("rate limited; no secret here")


class TokenCountingFakeClient:
    provider_name = "token_fake"

    def __init__(self) -> None:
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    def complete(self, messages, tools, config):
        self.calls += 1
        return LLMResponse(
            content='{"thought": "done", "final_answer": "priced answer", "stop": true}',
            usage=TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            model_name=config.model,
            provider_name=self.provider_name,
            latency_s=0.25,
            estimated_cost_usd=None,
            response_id=f"token-{self.calls}",
        )


def test_llm_cache_reuses_response_and_logs_hashes(tmp_path):
    instance = _sample_instance(0)
    fake = CountingFakeClient()
    agent = DirectToolAgent(
        provider="openai_compatible",
        model="fake-model",
        client=fake,
        cache_dir=str(tmp_path / "llm_cache"),
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=123)

    first = agent.act(env.steps, env.registry.specs(env.available_tools))
    second = agent.act(env.steps, env.registry.specs(env.available_tools))

    assert first.final_answer == "cached final"
    assert second.final_answer == "cached final"
    assert fake.calls == 1
    assert agent.llm_calls[0]["cache_hit"] is False
    assert agent.llm_calls[1]["cache_hit"] is True
    assert agent.llm_calls[0]["prompt_hash"]
    assert agent.llm_calls[0]["response_hash"]
    assert agent.llm_calls[0]["tool_state_hash"]
    assert agent.llm_calls[1]["estimated_cost_usd"] == 0.0
    assert list((tmp_path / "llm_cache").glob("*.json"))


def test_fake_token_counts_drive_call_and_trajectory_cost_metadata():
    instance = _sample_instance(0)
    fake = TokenCountingFakeClient()
    agent = DirectToolAgent(
        provider="openai_compatible",
        model="fake-model",
        client=fake,
        pricing={"input_per_1m_tokens": 1.0, "output_per_1m_tokens": 2.0},
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=123)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))
    env.step(action)
    metadata = agent.run_metadata()
    call = metadata["llm_calls"][0]

    assert fake.calls == 1
    assert call["prompt_tokens"] == 1000
    assert call["completion_tokens"] == 500
    assert call["total_tokens"] == 1500
    assert call["estimated_cost_usd"] == 0.002
    assert call["latency_s"] == 0.25
    assert call["retries"] == 0
    assert call["provider"] == "token_fake"
    assert metadata["estimated_cost_usd"] == 0.002
    assert metadata["model_call_count"] == 1
    assert metadata["prompt_tokens"] == 1000
    assert action.metadata["estimated_cost_usd"] == 0.002
    assert action.metadata["token_usage"]["total_tokens"] == 1500


def test_task_budget_cap_blocks_provider_call_before_spending():
    instance = _sample_instance(0)
    fake = TokenCountingFakeClient()
    agent = DirectToolAgent(
        provider="openai_compatible",
        model="fake-model",
        client=fake,
        max_cost_per_task_usd=0.0,
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=123)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))
    call = action.metadata["llm_calls"][0]

    assert fake.calls == 0
    assert action.stop is True
    assert "cost budget" in (action.final_answer or "")
    assert call["provider_call_made"] is False
    assert call["metadata"]["budget_scope"] == "task"


def test_named_llm_baselines_use_shared_prompt_hash_metadata():
    agents = [
        DirectLLMToolAgent(),
        ReActStyleLLMAgent(),
        PlannerExecutorLLMAgent(),
        SelfCheckingLLMAgent(),
        MemoryVerifyingLLMAgent(),
        RecoveryPromptLLMAgent(),
        ToolConservativeLLMAgent(),
    ]

    hashes = {agent.prompt_version_hash for agent in agents}

    assert len(hashes) == len(agents)
    for agent in agents:
        metadata = agent.run_metadata()
        assert metadata["provider"] == "local_stub"
        assert metadata["prompt_version_hash"]
        assert metadata["prompt_template_hash"]
        assert metadata["prompt_files"]["agent"].endswith(".md")


def test_memory_verifying_agent_injects_memory_verification_instruction():
    instance = next(
        item
        for item in read_jsonl(REPO_ROOT / "data/sample/instances.jsonl", BenchmarkInstance)
        if item.intervention is not None and item.intervention.family == "memory_corruption"
    )
    client = CapturingFakeClient(
        [
            {
                "content": (
                    '{"thought": "Verify stale memory.", "tool_name": "verify_fact", '
                    '"arguments": {"claim": "refund threshold", "evidence_ids": ["refund_threshold"]}, '
                    '"action": "tool_call"}'
                )
            }
        ]
    )
    agent = MemoryVerifyingLLMAgent(client=client)
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))

    assert action.tool_call is not None
    assert action.tool_call.tool_name == "verify_fact"
    assert "Initial memory is present" in client.calls[0]["messages"][1].content
    assert action.metadata["llm_phase"] == "memory_verify"


def test_recovery_and_conservative_agents_add_targeted_instructions():
    instance = _sample_instance(0)
    failed_history = [
        {
            "index": 0,
            "action": {"tool_call": {"tool_name": "search_database", "arguments": {"query": "x"}}},
            "observation": {"tool_name": "search_database", "error": "simulated_tool_failure"},
        }
    ]
    recovery_client = CapturingFakeClient(
        [
            {
                "content": (
                    '{"thought": "Cannot recover.", '
                    '"final_answer": "Unable to answer confidently because the tool failed.", '
                    '"stop": true}'
                )
            }
        ]
    )
    recovery_agent = RecoveryPromptLLMAgent(client=recovery_client)
    recovery_agent.reset(instance, seed=1)

    recovery_action = recovery_agent.act(
        failed_history,
        ToolRegistry().specs(instance.available_tools),
    )

    assert recovery_action.final_answer is not None
    assert "Do not repeat the same failed call unchanged" in recovery_client.calls[0]["messages"][1].content
    assert recovery_action.metadata["llm_phase"] == "recovery"

    conservative_client = CapturingFakeClient(
        [
            {
                "content": (
                    '{"thought": "Need one focused lookup.", "tool_name": "search_database", '
                    '"arguments": {"query": "Boston refundable hotel", "domain": "travel"}, '
                    '"action": "tool_call"}'
                )
            }
        ]
    )
    conservative_agent = ToolConservativeLLMAgent(client=conservative_client)
    conservative_agent.reset(instance, seed=1)

    conservative_action = conservative_agent.act([], ToolRegistry().specs(instance.available_tools))

    assert conservative_action.tool_call is not None
    assert "Use a tool only if it is necessary" in conservative_client.calls[0]["messages"][1].content
    assert conservative_action.metadata["llm_phase"] == "conservative_act"


def test_ablation_prompt_controls_are_logged_and_change_payload_shape():
    instance = _sample_instance(0)
    client = CapturingFakeClient(
        [
            {
                "content": (
                    'Before acting: {"action": "tool_call", "thought": "Need search.", '
                    '"tool_name": "search_database", '
                    '"arguments": {"query": "Boston refundable hotel", "domain": "travel"}}'
                )
            }
        ]
    )
    agent = DirectLLMToolAgent(
        client=client,
        prompt_file="ablations/base_tool_agent.md",
        prompt_addendum_file="ablations/memory_verification_instruction.md",
        system_safety_file="system_safety_ablation_minimal.md",
        action_protocol="flexible_text",
        tool_description_mode="short",
        step_budget_reminder=True,
        ablation={
            "pair_id": "memory_verification",
            "factor": "memory_verification_instruction",
            "level": "with_memory_verification",
            "comparison_role": "treatment",
        },
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))
    user_payload = read_json_from_message(client.calls[0]["messages"][1].content)

    assert action.tool_call is not None
    assert "Ablation factor: memory verification" in client.calls[0]["messages"][0].content
    assert user_payload["response_contract"]["mode"] == "flexible_text"
    assert user_payload["step_budget_reminder"]
    assert user_payload["available_tools"][0].keys() == {"name", "description", "is_available"}
    assert action.metadata["prompt_addendum_file"] == "ablations/memory_verification_instruction.md"
    assert action.metadata["action_protocol"] == "flexible_text"
    assert action.metadata["tool_description_mode"] == "short"
    assert action.metadata["ablation"]["factor"] == "memory_verification_instruction"
    assert agent.run_metadata()["prompt_files"]["prompt_addendum"] == "ablations/memory_verification_instruction.md"


def test_provider_error_becomes_logged_final_answer():
    instance = _sample_instance(0)
    agent = DirectToolAgent(
        provider="openai_compatible",
        model="fake-model",
        client=RateLimitedFakeClient(),
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))

    assert action.final_answer is not None
    assert "provider failed" in action.final_answer
    call = action.metadata["llm_calls"][0]
    assert call["provider_error_class"] == "ProviderRateLimitError"
    assert call["estimated_cost_usd"] == 0.0


def test_empty_response_logs_hash_and_parse_failure():
    instance = _sample_instance(0)
    agent = DirectToolAgent(client=LocalStubLLMClient([LLMResponse(content="")]))
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    action = agent.act(env.steps, env.registry.specs(env.available_tools))

    assert action.stop is True
    assert action.metadata["parse_error"] is True
    assert action.metadata["llm_calls"][0]["response_hash"]


def test_openai_compatible_provider_abstractions_are_safe(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_BASE_URL", raising=False)
    status = {row["provider"]: row for row in list_provider_status()}

    assert status["openai_compatible"]["requires_api_key"] is True
    assert "OPENAI_COMPATIBLE_API_KEY" in status["openai_compatible"]["env_vars"]
    assert status["openai_compatible"]["base_url_env"] == "OPENAI_COMPATIBLE_BASE_URL"
    assert status["local_openai"]["requires_api_key"] is False
    assert status["local_openai"]["openai_compatible"] is True

    generic = OpenAICompatibleClient()
    local = LocalOpenAICompatibleClient()
    assert generic.endpoint_for(
        ModelConfig(provider="openai_compatible", model="m", base_url="http://host:1234/v1")
    ) == "http://host:1234/v1/chat/completions"
    assert local.endpoint_for(ModelConfig(provider="local_openai", model="m")).endswith(
        "/v1/chat/completions"
    )


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL_ID"),
    reason="OpenAI integration test requires OPENAI_API_KEY and OPENAI_MODEL_ID",
)
def test_openai_provider_integration_is_opt_in_only():
    client = OpenAIClient()
    assert client.is_configured()
