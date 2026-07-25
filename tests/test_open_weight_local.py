import json

from causal_agent_bench.agents.llm_clients import (
    LLMToolCall,
    LocalOpenAICompatibleClient,
    Message,
    ModelConfig,
)
from causal_agent_bench.runners.config import load_experiment_config
from causal_agent_bench.runners.evidence_scope import (
    classify_evidence_scope,
    classify_scientific_scope,
)
from causal_agent_bench.runners.metadata import build_run_metadata


def test_local_openai_client_uses_fake_endpoint(monkeypatch):
    captured: dict[str, str] = {}

    def fake_post(endpoint, payload, headers, timeout):
        captured["endpoint"] = endpoint
        captured["model"] = payload["model"]
        return {
            "id": "chatcmpl-local-test",
            "model": payload["model"],
            "choices": [
                {
                    "message": {
                        "content": '{"thought": "done", "final_answer": "local ok", "stop": true}',
                        "tool_calls": [],
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
        }

    monkeypatch.setattr(
        "causal_agent_bench.agents.llm_clients._post_json",
        fake_post,
    )
    client = LocalOpenAICompatibleClient()
    config = ModelConfig(
        provider="local_openai",
        model="qwen2.5:7b",
        base_url="http://127.0.0.1:11434/v1",
    )
    response = client.complete(
        [Message(role="user", content="hello")],
        [],
        config,
    )

    assert captured["endpoint"] == "http://127.0.0.1:11434/v1/chat/completions"
    assert captured["model"] == "qwen2.5:7b"
    assert response.provider_name == "local_openai"
    assert "local ok" in (response.content or "")


def test_local_openai_client_parses_tool_calls(monkeypatch):
    def fake_post(endpoint, payload, headers, timeout):
        return {
            "id": "chatcmpl-tool",
            "model": payload["model"],
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "search_database",
                                    "arguments": json.dumps({"query": "hotels"}),
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
        }

    monkeypatch.setattr(
        "causal_agent_bench.agents.llm_clients._post_json",
        fake_post,
    )
    client = LocalOpenAICompatibleClient()
    response = client.complete(
        [Message(role="user", content="search")],
        [],
        ModelConfig(provider="local_openai", model="local-model", base_url="http://localhost:8000/v1"),
    )

    assert len(response.tool_calls) == 1
    assert response.tool_calls[0] == LLMToolCall(
        name="search_database",
        arguments={"query": "hotels"},
        call_id="call_1",
    )


def test_evidence_scope_labels_local_open_weight_separately():
    assert (
        classify_evidence_scope({"local_openai"}, run_name="pilot_local_openai_compatible_20")
        == "local_open_weight_unvalidated"
    )
    assert (
        classify_evidence_scope({"openai"}, run_name="pilot_openai_20")
        == "commercial_api_pilot_unvalidated"
    )
    assert (
        classify_evidence_scope({"local_openai", "openai"})
        == "mixed_local_and_api_do_not_merge"
    )
    assert classify_evidence_scope({"local_stub"}) == "pilot_stub_engineering_only"


def test_scientific_scope_for_local_open_weight():
    assert (
        classify_scientific_scope({"local_openai"}, run_name="main_local_openai_compatible_100")
        == "local_open_weight_pilot_or_experiment"
    )


def test_local_openai_configs_validate():
    for path in (
        "configs/pilot_local_openai_compatible_20.yaml",
        "configs/main_local_openai_compatible_100.yaml",
    ):
        config, _ = load_experiment_config(path)
        assert "local_openai_compatible" in config.run_name
        providers = {run.provider for run in config.iter_agent_runs() if run.provider}
        assert "local_openai" in providers
        assert classify_evidence_scope(providers, run_name=config.run_name) == (
            "local_open_weight_unvalidated"
        )


def test_run_metadata_includes_local_evidence_scope():
    from causal_agent_bench.runners.config import AgentRunConfig, ExperimentConfig

    config = ExperimentConfig(
        seed=1,
        run_name="pilot_local_openai_compatible_20",
        benchmark_path="data/sample/instances.jsonl",
        agent_runs=[
            AgentRunConfig(
                agent="direct_tool_agent",
                provider="local_openai",
                model="qwen2.5:7b",
                base_url="http://localhost:11434/v1",
            )
        ],
    )
    metadata = build_run_metadata(config, "abc123", instances_count=20)

    assert metadata["providers"] == ["local_openai"]
    assert metadata["evidence_scope"] == "local_open_weight_unvalidated"
    assert metadata["scientific_scope"] == "local_open_weight_pilot_or_experiment"
    assert metadata["deployment_class"] == "local_open_weight_unvalidated"
