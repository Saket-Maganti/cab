from causal_agent_bench.intervention import ALL_INTERVENTIONS, apply_intervention
from causal_agent_bench.task import seed_tasks


def test_all_interventions_generate_valid_tasks():
    base = seed_tasks()[0]
    for intervention_type in ALL_INTERVENTIONS:
        task = apply_intervention(base, intervention_type)
        assert task.intervention is not None
        assert task.intervention.type == intervention_type
        assert task.clean_task_id == base.task_id


def test_tool_removal_removes_required_tool():
    base = seed_tasks()[0]
    task = apply_intervention(base, "tool_removal")
    removed = task.intervention.params["removed_tools"]
    assert removed[0] not in task.available_tools
    assert removed[0] in task.expected_behavior.required_tools
