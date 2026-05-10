from pathlib import Path

from causal_agent_bench.generation.base_tasks import generate_base_tasks
from causal_agent_bench.generation.instances import (
    BenchmarkGenerationConfig,
    generate_benchmark,
)
from causal_agent_bench.generation.interventions import generate_interventions_for_task
from causal_agent_bench.generation.quality_checks import check_base_task, check_intervention
from causal_agent_bench.schemas import BaseTask, TaskGoal
from causal_agent_bench.validation import validate_jsonl_file


def _config(tmp_path: Path) -> BenchmarkGenerationConfig:
    return BenchmarkGenerationConfig(
        seed=42,
        num_base_tasks=8,
        domains=["travel", "calendar_email", "file_spreadsheet", "policy_compliance"],
        difficulty_mix={"easy": 0.25, "medium": 0.5, "hard": 0.25},
        interventions_per_task=2,
        output_dir=str(tmp_path / "generated"),
    )


def test_generation_is_deterministic_by_seed(tmp_path):
    first = generate_benchmark(_config(tmp_path / "a"))
    second = generate_benchmark(_config(tmp_path / "b"))
    first_ids = [task.task_id for task in first["base_tasks"]]
    second_ids = [task.task_id for task in second["base_tasks"]]
    assert first_ids == second_ids
    assert [item.model_dump(mode="json") for item in first["instances"]] == [
        item.model_dump(mode="json") for item in second["instances"]
    ]


def test_requested_number_of_tasks_produced(tmp_path):
    result = generate_benchmark(_config(tmp_path))
    assert len(result["base_tasks"]) == 8
    assert len(result["interventions"]) == 16
    assert len(result["instances"]) == 24


def test_each_base_task_has_clean_instance(tmp_path):
    result = generate_benchmark(_config(tmp_path))
    instance_ids = {instance.instance_id for instance in result["instances"]}
    for task in result["base_tasks"]:
        assert f"{task.task_id}.clean" in instance_ids


def test_each_intervention_links_to_base_task(tmp_path):
    result = generate_benchmark(_config(tmp_path))
    base_ids = {task.task_id for task in result["base_tasks"]}
    for intervention in result["interventions"]:
        assert intervention.base_task_id in base_ids


def test_quality_checker_catches_bad_examples():
    bad = BaseTask(
        task_id="bad",
        domain="travel",
        difficulty="easy",
        goal=TaskGoal(
            user_instruction="Do it.",
            success_criteria=["ok"],
            required_information=[],
            forbidden_assumptions=[],
            expected_final_answer=None,
        ),
        available_tools=["search_database"],
        hidden_ground_truth={},
        gold_tool_sequence=[],
        max_steps=1,
        tags=[],
        metadata={},
    )
    issues = check_base_task(bad)
    assert "missing expected answer" in issues
    assert "no required tools" in issues
    assert "ambiguous success criteria" in issues

    good = generate_base_tasks(1, 1, ["travel"], {"easy": 1.0})[0]
    intervention = generate_interventions_for_task(good, seed=1, count=1, families=["tool_failure"])[0]
    broken = intervention.model_copy(update={"memory_patch": {"extra": "factor"}})
    assert "intervention changes too many factors" in check_intervention(good, broken)


def test_generated_jsonl_validates_with_schemas(tmp_path):
    result = generate_benchmark(_config(tmp_path))
    output_dir = Path(result["output_dir"])
    assert validate_jsonl_file(output_dir / "base_tasks.jsonl", "base_tasks")["invalid"] == 0
    assert validate_jsonl_file(output_dir / "interventions.jsonl", "interventions")["invalid"] == 0
    assert validate_jsonl_file(output_dir / "instances.jsonl", "instances")["invalid"] == 0
