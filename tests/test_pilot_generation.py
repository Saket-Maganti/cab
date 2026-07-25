from collections import Counter
from pathlib import Path

from causal_agent_bench.generation.instances import BenchmarkGenerationConfig, generate_benchmark
from causal_agent_bench.generation.interventions import INTERVENTION_FAMILIES
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.utils.io import read_json, read_jsonl
from causal_agent_bench.validation import validate_jsonl_file

PILOT_DOMAINS = [
    "travel_planning",
    "calendar_email_workflow",
    "file_spreadsheet_qa",
    "shopping_comparison",
    "research_assistant",
    "policy_compliance",
    "coding_debugging",
    "operations_planning",
]


def _pilot_test_config(tmp_path: Path) -> BenchmarkGenerationConfig:
    return BenchmarkGenerationConfig(
        seed=20270511,
        benchmark_version="pilot_v0.1-test",
        num_base_tasks=32,
        domains=PILOT_DOMAINS,
        difficulty_mix={"easy": 0.25, "medium": 0.25, "hard": 0.25, "stress": 0.25},
        interventions_per_task=5,
        balanced_intervention_families=True,
        intervention_families=INTERVENTION_FAMILIES,
        dev_split_size=8,
        pilot_split_size=24,
        heldout_split_size=8,
        human_audit_sample_size=20,
        output_dir=str(tmp_path / "pilot_v0_1_test"),
    )


def test_pilot_generation_is_deterministic(tmp_path):
    first = generate_benchmark(_pilot_test_config(tmp_path / "a"))
    second = generate_benchmark(_pilot_test_config(tmp_path / "b"))

    assert [task.model_dump(mode="json") for task in first["base_tasks"]] == [
        task.model_dump(mode="json") for task in second["base_tasks"]
    ]
    assert [instance.model_dump(mode="json") for instance in first["instances"]] == [
        instance.model_dump(mode="json") for instance in second["instances"]
    ]


def test_pilot_schema_validity_and_required_outputs(tmp_path):
    result = generate_benchmark(_pilot_test_config(tmp_path))
    output_dir = Path(result["output_dir"])

    for filename, schema in [
        ("base_tasks.jsonl", "base_tasks"),
        ("interventions.jsonl", "interventions"),
        ("instances.jsonl", "instances"),
    ]:
        assert validate_jsonl_file(output_dir / filename, schema)["invalid"] == 0
    for filename in [
        "generation_report.json",
        "quality_report.md",
        "dataset_card.md",
        "splits.json",
        "human_audit_sample.jsonl",
    ]:
        assert (output_dir / filename).exists()


def test_pilot_has_all_domains_difficulties_and_intervention_families(tmp_path):
    result = generate_benchmark(_pilot_test_config(tmp_path))

    assert set(Counter(task.domain for task in result["base_tasks"])) == set(PILOT_DOMAINS)
    assert set(Counter(task.difficulty for task in result["base_tasks"])) == {
        "easy",
        "medium",
        "hard",
        "stress",
    }
    assert set(Counter(intervention.family for intervention in result["interventions"])) == set(
        INTERVENTION_FAMILIES
    )


def test_pilot_has_no_duplicate_instance_ids_and_reproducible_splits(tmp_path):
    first = generate_benchmark(_pilot_test_config(tmp_path / "a"))
    second = generate_benchmark(_pilot_test_config(tmp_path / "b"))
    instances = first["instances"]
    ids = [instance.instance_id for instance in instances]

    assert len(ids) == len(set(ids))
    assert read_json(Path(first["output_dir"]) / "splits.json") == read_json(
        Path(second["output_dir"]) / "splits.json"
    )


def test_human_audit_sample_has_expected_review_fields(tmp_path):
    result = generate_benchmark(_pilot_test_config(tmp_path))
    output_dir = Path(result["output_dir"])
    audit_rows = read_jsonl(output_dir / "human_audit_sample.jsonl")
    instances = read_jsonl(output_dir / "instances.jsonl", BenchmarkInstance)
    changes = {
        instance.intervention.expected_final_answer_change
        for instance in instances
        if instance.intervention is not None
    }

    assert len(audit_rows) == 20
    assert {"yes", "no", "unclear"}.issubset(changes)
    assert {
        "Is the task understandable?",
        "Is the correct answer/scoring label valid?",
        "Does the intervention preserve the high-level goal?",
        "Is the changed factor isolated?",
        "What, if anything, is ambiguous?",
    }.issubset(set(audit_rows[0]["review_questions"]))
