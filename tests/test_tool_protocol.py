import json
from pathlib import Path

from causal_agent_bench.agents.llm_agents import DirectToolAgent
from causal_agent_bench.agents.llm_clients import LocalStubLLMClient
from causal_agent_bench.agents.tool_protocol import parse_tool_action
from causal_agent_bench.environment import BenchmarkEnvironment
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.tools.registry import ToolRegistry
from causal_agent_bench.utils.io import read_jsonl

REPO_ROOT = Path(__file__).resolve().parents[1]


def _tool_specs():
    return ToolRegistry().specs(["search_database", "calculate_price", "verify_fact"])


def _sample_instance() -> BenchmarkInstance:
    return read_jsonl(REPO_ROOT / "data/sample/instances.jsonl", BenchmarkInstance)[0]


def test_parser_accepts_markdown_code_fence_json():
    raw = """```json
{"action":"tool_call","thought":"need records","tool_name":"search_database","arguments":{"query":"hotel","domain":"travel"}}
```"""

    result = parse_tool_action(raw, available_tools=_tool_specs())

    assert result.outcome == "valid_tool_call"
    assert result.tool_name == "search_database"
    assert result.arguments["query"] == "hotel"
    assert result.metadata["repair_applied"] is True
    assert "markdown_code_fence" in result.metadata["repair_steps"]


def test_parser_accepts_prose_plus_json_without_semantic_repair():
    raw = 'I will answer now:\n{"action":"clarification","clarification":"Need the travel date.","stop":true}'

    result = parse_tool_action(raw, available_tools=_tool_specs())

    assert result.outcome == "clarification"
    assert result.final_answer == "Need the travel date."
    assert "prose_wrapped_json" in result.metadata["repair_steps"]


def test_parser_rejects_two_tool_calls_at_once():
    raw = json.dumps(
        {
            "tool_calls": [
                {"tool_name": "search_database", "arguments": {"query": "hotel"}},
                {"tool_name": "verify_fact", "arguments": {"claim": "x", "evidence_ids": []}},
            ]
        }
    )

    result = parse_tool_action(raw, available_tools=_tool_specs())

    assert result.outcome == "multiple_tool_calls"
    assert result.is_valid is False


def test_parser_reports_malformed_json():
    raw = '{"action":"tool_call","tool_name":"search_database","arguments":{"query":"hotel"}'

    result = parse_tool_action(raw, available_tools=_tool_specs())

    assert result.outcome == "invalid_json"
    assert result.is_valid is False


def test_parser_tracks_wrong_tool_name():
    raw = '{"action":"tool_call","tool_name":"live_web_search","arguments":{"query":"hotel"}}'

    result = parse_tool_action(raw, available_tools=_tool_specs())

    assert result.outcome == "unknown_tool"
    assert result.tool_name == "live_web_search"
    assert result.is_valid is False


def test_parser_tracks_invalid_argument_schema():
    raw = '{"action":"tool_call","tool_name":"search_database","arguments":{"query": 42}}'

    result = parse_tool_action(raw, available_tools=_tool_specs())

    assert result.outcome == "invalid_argument_schema"
    assert "expected string" in (result.error or "")


def test_parser_tracks_final_answer_without_required_evidence():
    raw = '{"action":"final_answer","final_answer":"The answer is saver_hotel.","stop":true}'

    result = parse_tool_action(
        raw,
        available_tools=_tool_specs(),
        observation_history=[],
        required_information=["hotel evidence"],
    )

    assert result.outcome == "final_answer_without_required_evidence"
    assert result.final_answer == "The answer is saver_hotel."
    assert result.is_valid is False


def test_agent_trajectory_preserves_raw_and_parsed_action():
    instance = _sample_instance()
    agent = DirectToolAgent(
        client=LocalStubLLMClient(
            [
                {
                    "content": (
                        "```json\n"
                        '{"action":"tool_call","thought":"need records","tool_name":"search_database",'
                        '"arguments":{"query":"hotel","domain":"travel"}}\n'
                        "```"
                    )
                }
            ]
        )
    )
    env = BenchmarkEnvironment(instance, run_id="test", agent_name=agent.name)
    agent.reset(instance, seed=1)

    step = env.step(agent.act(env.steps, env.registry.specs(env.available_tools)))

    assert step["raw_model_output"].startswith("```json")
    assert step["parsed_action"]["outcome"] == "valid_tool_call"
    assert step["action"]["metadata"]["parser_outcome"] == "valid_tool_call"
