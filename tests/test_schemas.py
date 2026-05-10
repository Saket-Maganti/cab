import pytest
from pydantic import ValidationError

from causal_agent_bench.schemas import BenchmarkTask, ExpectedBehavior
from causal_agent_bench.task import seed_tasks


def test_seed_tasks_validate():
    tasks = seed_tasks()
    assert len(tasks) == 8
    assert {task.domain for task in tasks} >= {"travel planning", "coding/debugging tasks"}


def test_required_tool_must_be_available():
    with pytest.raises(ValidationError):
        BenchmarkTask(
            task_id="bad",
            domain="unit",
            user_goal="Do the thing",
            available_tools=["search_database"],
            expected_behavior=ExpectedBehavior(required_tools=["read_file"]),
        )
