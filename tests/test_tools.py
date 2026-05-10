from causal_agent_bench.intervention import apply_intervention
from causal_agent_bench.task import seed_tasks
from causal_agent_bench.tools import ToolRegistry


def test_calculate_price_is_deterministic():
    task = seed_tasks()[0]
    registry = ToolRegistry()
    args = {"item_ids": ["saver_hotel"], "tax_rate": 0.10}
    first = registry.call("calculate_price", args, task)
    second = registry.call("calculate_price", args, task)
    assert first == second
    assert first.output["total"] == 176.0


def test_tool_failure_intervention_returns_error():
    task = apply_intervention(seed_tasks()[0], "tool_failure")
    registry = ToolRegistry()
    target = task.intervention.params["target_tool"]
    observation = registry.call(target, task.expected_behavior.tool_arguments[target], task)
    assert not observation.ok
    assert observation.error == "simulated_tool_failure"
