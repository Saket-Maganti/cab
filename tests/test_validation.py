import pytest
from pydantic import ValidationError

from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, InterventionSpec, TaskGoal
from causal_agent_bench.validation import (
    validate_instance,
    validate_intervention,
    validate_jsonl_file,
    validate_task,
)


def _base_task() -> BaseTask:
    return BaseTask(
        task_id="travel_unit_001",
        domain="travel",
        difficulty="easy",
        goal=TaskGoal(
            user_instruction="Find the cheapest refundable option.",
            success_criteria=["Names the option."],
            required_information=["price", "refundability"],
            forbidden_assumptions=["Do not assume non-refundable options are acceptable."],
            expected_final_answer="option_b",
        ),
        available_tools=["search_database", "compare_options"],
        hidden_ground_truth={"best": "option_b"},
        gold_tool_sequence=["search_database", "compare_options"],
        max_steps=4,
        tags=["unit"],
        metadata={"synthetic": True},
    )


def _intervention(base_task: BaseTask) -> InterventionSpec:
    return InterventionSpec(
        intervention_id=f"{base_task.task_id}.tool_failure",
        base_task_id=base_task.task_id,
        family="tool_failure",
        description="The comparison tool fails.",
        changed_factor="tool reliability",
        expected_behavior="Agent should recover or report the limitation.",
        severity="medium",
        tool_availability_patch={},
        memory_patch={},
        tool_output_patch={"target_tool": "compare_options", "error": "simulated_tool_failure"},
        instruction_patch=None,
        metadata={"synthetic": True},
    )


def test_valid_base_task():
    assert validate_task(_base_task()) == []


def test_invalid_base_task_duplicate_tools():
    with pytest.raises(ValidationError):
        BaseTask(
            task_id="bad",
            domain="travel",
            difficulty="easy",
            goal=TaskGoal(
                user_instruction="Do it.",
                success_criteria=["Done."],
                required_information=[],
                forbidden_assumptions=[],
                expected_final_answer=None,
            ),
            available_tools=["search_database", "search_database"],
            hidden_ground_truth={},
            gold_tool_sequence=None,
            max_steps=3,
            tags=[],
            metadata={},
        )


def test_valid_intervention():
    base_task = _base_task()
    assert validate_intervention(base_task, _intervention(base_task)) == []


def test_invalid_intervention_family():
    base_task = _base_task()
    payload = _intervention(base_task).model_dump(mode="python")
    payload["family"] = "not_a_family"
    with pytest.raises(ValidationError):
        InterventionSpec.model_validate(payload)


def test_benchmark_instance_linking():
    base_task = _base_task()
    intervention = _intervention(base_task)
    instance = BenchmarkInstance(
        instance_id="travel_unit_001.tool_failure",
        base_task=base_task,
        condition="intervention",
        intervention=intervention,
        available_tools=base_task.available_tools,
        initial_memory={},
        environment_seed=7,
        metadata={},
    )
    assert validate_instance(instance) == []


def test_jsonl_validation():
    summary = validate_jsonl_file("data/sample/instances.jsonl", "instances")
    assert summary["total"] == 9
    assert summary["valid"] == 9
    assert summary["invalid"] == 0
