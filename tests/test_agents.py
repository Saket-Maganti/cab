from pathlib import Path

from causal_agent_bench.agents import get_agent, list_agents
from causal_agent_bench.io import read_jsonl
from causal_agent_bench.runners.runner import run_benchmark, run_config_from_mapping
from causal_agent_bench.schemas import AgentAction, BenchmarkInstance
from causal_agent_bench.tools import ToolRegistry

BASELINE_NAMES = [
    "random_tool_agent",
    "scripted_oracle_agent",
    "greedy_tool_agent",
    "react_stub_agent",
    "planner_executor_stub_agent",
]

LLM_BASELINE_NAMES = [
    "direct_llm_tool_agent",
    "react_style_llm_agent",
    "planner_executor_llm_agent",
    "self_checking_llm_agent",
    "memory_verifying_llm_agent",
    "recovery_prompt_llm_agent",
    "tool_conservative_llm_agent",
]


def _instance() -> BenchmarkInstance:
    return read_jsonl("data/sample/instances.jsonl", BenchmarkInstance)[0]


def test_all_baseline_agents_instantiate():
    for name in BASELINE_NAMES + LLM_BASELINE_NAMES:
        assert get_agent(name).name == name


def test_all_baseline_agents_return_valid_action():
    instance = _instance()
    tool_specs = ToolRegistry().specs(instance.available_tools)
    for name in BASELINE_NAMES + LLM_BASELINE_NAMES:
        agent = get_agent(name, seed=3)
        agent.reset(instance)
        action = agent.act([], tool_specs)
        assert isinstance(action, AgentAction)


def test_random_agent_is_deterministic_with_fixed_seed():
    instance = _instance()
    tool_specs = ToolRegistry().specs(instance.available_tools)
    first = get_agent("random_tool_agent", seed=11)
    second = get_agent("random_tool_agent", seed=11)
    first.reset(instance)
    second.reset(instance)
    assert first.act([], tool_specs) == second.act([], tool_specs)


def test_oracle_agent_follows_gold_sequence():
    instance = _instance()
    tool_specs = ToolRegistry().specs(instance.available_tools)
    agent = get_agent("scripted_oracle_agent")
    agent.reset(instance)
    action = agent.act([], tool_specs)
    assert action.tool_call is not None
    assert action.tool_call.tool_name == instance.base_task.gold_tool_sequence[0]


def test_greedy_agent_selects_plausible_tool():
    instance = _instance()
    tool_specs = ToolRegistry().specs(instance.available_tools)
    agent = get_agent("greedy_tool_agent")
    agent.reset(instance)
    action = agent.act([], tool_specs)
    assert action.tool_call is not None
    assert action.tool_call.tool_name == "search_database"


def test_agent_registry_lists_and_aliases():
    names = list_agents()
    assert "random_tool_agent" in names
    assert "planner_executor_stub_agent" in names
    assert "memory_verifying_llm_agent" in names
    assert get_agent("RandomToolAgent").name == "random_tool_agent"
    assert get_agent("ReActStyleLLMAgent").name == "react_style_llm_agent"


def test_planner_executor_does_not_use_schema_gold_sequence():
    instance = _instance()
    modified_base = instance.base_task.model_copy(
        update={
            "available_tools": [*instance.base_task.available_tools, "lookup_policy"],
            "gold_tool_sequence": ["lookup_policy"],
        }
    )
    modified = instance.model_copy(
        update={
            "base_task": modified_base,
            "available_tools": [*instance.available_tools, "lookup_policy"],
        }
    )
    tool_specs = ToolRegistry().specs(modified.available_tools)
    agent = get_agent("planner_executor_stub_agent")
    agent.reset(modified)
    action = agent.act([], tool_specs)
    assert action.tool_call is not None
    assert action.tool_call.tool_name == "search_database"


def test_runner_can_run_all_baseline_agents_on_smoke_config(tmp_path):
    raw = {
        "seed": 7,
        "run_name": "smoke",
        "num_tasks": 5,
        "task_domains": ["travel", "calendar_email"],
        "interventions": ["tool_failure", "irrelevant_tools"],
        "agents": BASELINE_NAMES,
    }
    raw["output_dir"] = str(tmp_path)
    config = run_config_from_mapping(raw)
    assert config.agents == BASELINE_NAMES
    trajectories = run_benchmark(config)
    assert len(trajectories) == raw["num_tasks"] * len(BASELINE_NAMES)
    assert (Path(config.output_dir) / "trajectories.jsonl").exists()
