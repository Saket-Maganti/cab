from pathlib import Path

from causal_agent_bench.environment import BenchmarkEnvironment
from causal_agent_bench.io import read_jsonl
from causal_agent_bench.schemas import AgentAction, BenchmarkInstance, InterventionSpec, ToolCall
from causal_agent_bench.tools import ToolRegistry


def _state():
    registry = ToolRegistry()
    return {
        "knowledge_base": registry.knowledge_base,
        "available_tools": registry.names,
        "tool_output_patch": {},
        "step_index": 0,
    }


def _instances() -> list[BenchmarkInstance]:
    return read_jsonl(Path("data/sample/instances.jsonl"), BenchmarkInstance)


def test_each_simulated_tool_is_deterministic():
    registry = ToolRegistry()
    cases = {
        "search_database": {"query": "Boston hotel", "domain": "travel"},
        "lookup_policy": {"policy_name": "refunds", "question": "Does 700 require approval?"},
        "check_calendar": {"date": "2026-06-03", "time_window": "13:00-15:00"},
        "read_file": {"file_id": "launch_note", "query": "revenue"},
        "query_spreadsheet": {"sheet_id": "revenue", "query": "Q2"},
        "calculate_price": {"items": [{"id": "saver_hotel", "price": 160}], "constraints": {"tax_rate": 0.1}},
        "compare_options": {
            "options": [{"id": "a", "price": 2}, {"id": "b", "price": 1}],
            "criteria": ["price"],
        },
        "send_email_draft": {"recipient": "mina@example.com", "subject": "Meeting", "body": "15:00?"},
        "book_stub": {"item_id": "saver_hotel", "confirmation_required": True},
        "verify_fact": {"claim": "700 refund approval", "evidence_ids": ["refund_threshold"]},
    }
    for tool_name, arguments in cases.items():
        first = registry.call(tool_name, arguments, _state())
        second = registry.call(tool_name, arguments, _state())
        assert first == second
        assert first.error is None


def test_invalid_arguments_return_useful_error():
    observation = ToolRegistry().call("search_database", {}, _state())
    assert observation.error == "invalid_arguments"
    assert "missing" in observation.output


def test_tool_failure_intervention_patch_works():
    state = _state()
    state["tool_output_patch"] = {
        "target_tool": "calculate_price",
        "error": "simulated_tool_failure",
        "partial_output": {"total": None},
    }
    observation = ToolRegistry().call(
        "calculate_price",
        {"items": [{"id": "x", "price": 10}], "constraints": {}},
        state,
    )
    assert observation.error == "simulated_tool_failure"
    assert observation.output == {"total": None}


def test_tool_corruption_intervention_patch_works():
    state = _state()
    state["tool_output_patch"] = {
        "target_tool": "calculate_price",
        "overrides": {"total": 999.99},
    }
    observation = ToolRegistry().call(
        "calculate_price",
        {"items": [{"id": "x", "price": 10}], "constraints": {}},
        state,
    )
    assert observation.error is None
    assert observation.is_corrupted is True
    assert observation.output["total"] == 999.99


def test_environment_max_steps_terminates():
    instance = _instances()[0].model_copy(
        update={"base_task": _instances()[0].base_task.model_copy(update={"max_steps": 1})}
    )
    env = BenchmarkEnvironment(instance, run_id="unit", agent_name="unit_agent")
    env.step(
        AgentAction(
            tool_call=ToolCall(
                tool_name="search_database",
                arguments={"query": "Boston", "domain": "travel"},
            )
        )
    )
    assert env.done is True
    assert env.terminated_reason == "max_steps"


def test_environment_trajectory_contains_expected_fields():
    instance = _instances()[0]
    env = BenchmarkEnvironment(instance, run_id="unit", agent_name="unit_agent")
    env.step(
        AgentAction(
            tool_call=ToolCall(
                tool_name="search_database",
                arguments={"query": "Boston", "domain": "travel"},
            )
        )
    )
    env.step(AgentAction(final_answer="saver_hotel total 176", stop=True))
    trajectory = env.trajectory()
    assert trajectory.run_id == "unit"
    assert trajectory.instance_id == instance.instance_id
    assert trajectory.steps[0]["observation"]["tool_name"] == "search_database"
    assert trajectory.final_answer == "saver_hotel total 176"
    assert trajectory.terminated_reason == "final_answer"


def test_clean_and_irrelevant_tool_intervention_differ_by_tool_patch_only():
    clean = next(instance for instance in _instances() if instance.instance_id == "travel_refund_hotel_001.clean")
    intervened = next(
        instance
        for instance in _instances()
        if instance.instance_id == "travel_refund_hotel_001.irrelevant_tools"
    )
    assert clean.base_task == intervened.base_task
    assert intervened.intervention is not None
    assert intervened.intervention.family == "irrelevant_tools"
    assert set(intervened.available_tools) - set(clean.available_tools) == {"read_file", "book_stub"}
    assert clean.initial_memory == intervened.initial_memory


def test_benchmark_environment_applies_memory_and_tool_availability_patches():
    memory_instance = next(
        instance
        for instance in _instances()
        if instance.instance_id == "policy_refund_approval_001.memory_corruption"
    )
    env = BenchmarkEnvironment(memory_instance)
    assert env.state["initial_memory"]["refund_threshold_memory"] == 1000

    base = _instances()[1].base_task
    intervention = InterventionSpec(
        intervention_id="calendar_email_slot_001.tool_removal.unit",
        base_task_id=base.task_id,
        family="tool_removal",
        description="Remove the calendar tool.",
        changed_factor="tool availability",
        expected_behavior="Agent should notice the missing calendar tool.",
        severity="medium",
        tool_availability_patch={"removed_tools": ["check_calendar"]},
        memory_patch={},
        tool_output_patch={},
        instruction_patch=None,
        metadata={},
    )
    instance = BenchmarkInstance(
        instance_id="calendar_email_slot_001.tool_removal.unit",
        base_task=base,
        condition="intervention",
        intervention=intervention,
        available_tools=base.available_tools,
        initial_memory={},
        environment_seed=21,
        metadata={},
    )
    env = BenchmarkEnvironment(instance)
    assert "check_calendar" not in env.available_tools
