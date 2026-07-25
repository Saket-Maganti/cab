from pathlib import Path

from causal_agent_bench.analysis.mini_study import compare_mini_study
from causal_agent_bench.generation.instances import BenchmarkGenerationConfig, generate_benchmark
from causal_agent_bench.generation.naturalistic import generate_naturalistic_base_tasks
from causal_agent_bench.generation.naturalistic_templates import NATURALISTIC_DOMAINS
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment


def _mini_generation_config(output_dir: Path, *, task_style: str) -> BenchmarkGenerationConfig:
    return BenchmarkGenerationConfig(
        seed=20270541,
        benchmark_version=f"mini_study_{task_style}_test",
        task_style=task_style,
        num_base_tasks=40,
        domains=(
            [
                "travel_planning",
                "calendar_email_workflow",
                "file_spreadsheet_qa",
                "shopping_comparison",
                "research_assistant",
                "policy_compliance",
                "coding_debugging",
                "operations_planning",
            ]
            if task_style == "template"
            else NATURALISTIC_DOMAINS
        ),
        difficulty_mix={"easy": 0.25, "medium": 0.25, "hard": 0.25, "stress": 0.25},
        interventions_per_task=5,
        balanced_intervention_families=True,
        output_dir=str(output_dir),
    )


def test_naturalistic_generation_produces_40_tasks_with_artifact_metadata(tmp_path):
    tasks = generate_naturalistic_base_tasks(seed=41, num_base_tasks=40, domains=NATURALISTIC_DOMAINS)

    assert len(tasks) == 40
    assert all(task.metadata.get("task_style") == "naturalistic" for task in tasks)
    artifact_types = {task.metadata.get("artifact_type") for task in tasks}
    assert "email_thread" in artifact_types
    assert "bug_report" in artifact_types
    assert "Mock artifact" in tasks[0].goal.user_instruction


def test_template_and_naturalistic_benchmark_generation(tmp_path):
    template = generate_benchmark(_mini_generation_config(tmp_path, task_style="template"))
    naturalistic = generate_benchmark(_mini_generation_config(tmp_path, task_style="naturalistic"))

    assert template["generation_report"]["counts"]["base_tasks"] == 40
    assert naturalistic["generation_report"]["counts"]["base_tasks"] == 40
    template_tasks = template["base_tasks"]
    naturalistic_tasks = naturalistic["base_tasks"]
    assert template_tasks[0].metadata["task_style"] == "template"
    assert naturalistic_tasks[0].metadata["task_style"] == "naturalistic"


def _stub_run_config(tmp_path: Path, benchmark_path: Path, run_name: str) -> ExperimentConfig:
    return ExperimentConfig.model_validate(
        {
            "seed": 41,
            "run_name": run_name,
            "benchmark_path": str(benchmark_path),
            "agent_runs": [
                {
                    "name": "direct_stub",
                    "agent": "direct_tool_agent",
                    "provider": "local_stub",
                    "model": "local-stub",
                    "retry_count": 0,
                }
            ],
            "max_steps": 4,
            "num_repeats": 1,
            "output_dir": str(tmp_path / "runs"),
            "auto_score": True,
        }
    )


def test_compare_mini_study_exports_table_and_report(tmp_path):
    template_dir = tmp_path / "template_data"
    naturalistic_dir = tmp_path / "naturalistic_data"
    generate_benchmark(_mini_generation_config(template_dir, task_style="template"))
    generate_benchmark(_mini_generation_config(naturalistic_dir, task_style="naturalistic"))

    template_run = run_experiment(
        _stub_run_config(
            tmp_path,
            template_dir / "pilot_instances.jsonl",
            "mini_study_template_stub",
        )
    )["run_dir"]
    naturalistic_run = run_experiment(
        _stub_run_config(
            tmp_path,
            naturalistic_dir / "pilot_instances.jsonl",
            "mini_study_naturalistic_stub",
        )
    )["run_dir"]

    report = compare_mini_study(
        template_run,
        naturalistic_run,
        output_dir=tmp_path / "comparison",
    )

    assert report["comparison"]["families_compared"]
    assert (tmp_path / "comparison" / "mini_study_comparison.json").exists()
    assert (tmp_path / "comparison" / "table_mini_study_family_comparison.csv").exists()
    assert (tmp_path / "comparison" / "mini_study_paper_paragraph.tex").exists()
    assert report["qualitative_examples"]
