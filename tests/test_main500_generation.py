from collections import Counter
from pathlib import Path

from causal_agent_bench.generation.instances import BenchmarkGenerationConfig, generate_benchmark
from causal_agent_bench.generation.interventions import INTERVENTION_FAMILIES
from causal_agent_bench.utils.io import read_json
from causal_agent_bench.validation import validate_jsonl_file

MAIN_500_DOMAINS = [
    "travel_planning",
    "calendar_email_workflow",
    "file_qa",
    "spreadsheet_qa",
    "shopping_comparison",
    "research_assistant",
    "policy_compliance",
    "coding_debugging",
    "operations_planning",
    "customer_support_workflow",
    "finance_admin_workflow",
    "data_cleaning_workflow",
]


def _config(tmp_path: Path) -> BenchmarkGenerationConfig:
    return BenchmarkGenerationConfig(
        seed=20270513,
        benchmark_version="main_v0.1_500-test",
        num_base_tasks=60,
        domains=MAIN_500_DOMAINS,
        difficulty_mix={"easy": 0.25, "medium": 0.35, "hard": 0.3, "stress": 0.1},
        interventions_per_task=5,
        balanced_intervention_families=True,
        intervention_families=INTERVENTION_FAMILIES,
        dev_split_size=12,
        pilot_split_size=60,
        human_audit_sample_size=24,
        output_dir=str(tmp_path / "main_500_test"),
    )


def test_expanded_generator_covers_12_domains_and_balances_interventions(tmp_path):
    result = generate_benchmark(_config(tmp_path))
    base_tasks = result["base_tasks"]
    interventions = result["interventions"]
    instances = result["instances"]

    assert len(base_tasks) == 60
    assert len(interventions) == 300
    assert len(instances) == 360
    assert set(Counter(task.domain for task in base_tasks)) == set(MAIN_500_DOMAINS)
    assert set(Counter(task.difficulty for task in base_tasks)) == {
        "easy",
        "medium",
        "hard",
        "stress",
    }
    assert set(Counter(intervention.family for intervention in interventions)) == set(
        INTERVENTION_FAMILIES
    )


def test_expanded_generator_reports_statistics_and_passes_validation(tmp_path):
    result = generate_benchmark(_config(tmp_path))
    output_dir = Path(result["output_dir"])
    report = read_json(output_dir / "generation_report.json")

    assert report["statistics"]["average_interventions_per_task"] == 5.0
    assert report["statistics"]["average_required_tools"] >= 1.0
    assert report["duplicates"]["task_ids"] == []
    assert report["duplicates"]["instance_ids"] == []
    assert validate_jsonl_file(output_dir / "base_tasks.jsonl", "base_tasks")["invalid"] == 0
    assert validate_jsonl_file(output_dir / "interventions.jsonl", "interventions")["invalid"] == 0
    assert validate_jsonl_file(output_dir / "instances.jsonl", "instances")["invalid"] == 0
    assert result["quality_report"]["passed"] is True
