import json
from pathlib import Path

import pandas as pd

from causal_agent_bench.analysis.error_analysis import extract_error_cases, mine_error_cases
from causal_agent_bench.analysis.figures import build_all_figures
from causal_agent_bench.analysis.human_validation import (
    ANNOTATION_DIMENSIONS,
    compute_agreement,
    export_human_validation_sample,
    summarize_human_validation_annotations,
)
from causal_agent_bench.analysis.llm_judge import calibrate_llm_judge, run_llm_judge
from causal_agent_bench.analysis.load_results import load_run_results
from causal_agent_bench.analysis.report import export_paper_assets
from causal_agent_bench.analysis.tables import (
    ablation_results_table,
    bootstrap_mean_ci,
    build_all_tables,
)
from causal_agent_bench.cli import main as cli_main
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment


def _analysis_run(tmp_path: Path) -> Path:
    config = ExperimentConfig.model_validate(
        {
            "seed": 17,
            "run_name": "analysis_smoke",
            "benchmark_path": "data/sample/instances.jsonl",
            "agents": ["random_tool_agent", "scripted_oracle_agent"],
            "max_steps": 8,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )
    return run_experiment(config)["run_dir"]


def test_analysis_loads_aggregate_scores(tmp_path):
    data = load_run_results(_analysis_run(tmp_path))
    assert data.aggregate["n_agents"] == 2
    assert not data.scores_df.empty
    assert not data.instances_df.empty


def test_figures_script_runs_on_smoke_output(tmp_path):
    data = load_run_results(_analysis_run(tmp_path))
    paths = build_all_figures(data, tmp_path / "figures")
    names = {path.name for path in paths}
    assert "figure1_benchmark_schematic.md" in names
    assert "figure2_clean_vs_intervention_success.png" in names
    assert "figure6_trajectory_failure_taxonomy.pdf" in names
    assert "figure5_cost_vs_robustness.png" in names
    schematic = (tmp_path / "figures" / "figure1_benchmark_schematic.md").read_text(
        encoding="utf-8"
    )
    assert "Asset Metadata" in schematic
    assert "config_hash" in schematic


def test_tables_are_created(tmp_path):
    data = load_run_results(_analysis_run(tmp_path))
    paths = build_all_tables(data, tmp_path / "tables")
    names = {path.name for path in paths}
    assert "table1_benchmark_statistics.csv" in names
    assert "table2_main_agent_performance.tex" in names
    assert "table2_oracle_sanity_check.csv" in names
    assert "table6_performance_vs_cost.csv" in names
    assert "table7_robustness_vs_cost.csv" in names
    assert "table5_human_validation_agreement.md" in names
    table = (tmp_path / "tables" / "table2_main_agent_performance.csv").read_text(
        encoding="utf-8"
    )
    assert "config_hash" in table
    assert "dataset_version" in table
    assert "scripted_oracle_agent" not in table
    oracle_table = (tmp_path / "tables" / "table2_oracle_sanity_check.csv").read_text(
        encoding="utf-8"
    )
    assert "scripted_oracle_agent" in oracle_table
    assert "sanity_check_upper_bound_not_realistic_agent" in oracle_table
    cost_table = (tmp_path / "tables" / "table6_performance_vs_cost.csv").read_text(
        encoding="utf-8"
    )
    assert "avg_cost_per_task_usd" in cost_table
    assert "cost_normalized_success" in cost_table
    robustness_cost_table = (
        tmp_path / "tables" / "table7_robustness_vs_cost.csv"
    ).read_text(encoding="utf-8")
    assert "cost_normalized_acrs" in robustness_cost_table


def test_ablation_table_export_uses_prompt_hash_metadata(tmp_path):
    config = ExperimentConfig.model_validate(
        {
            "seed": 23,
            "run_name": "ablation_table_smoke",
            "benchmark_path": "data/sample/instances.jsonl",
            "agent_runs": [
                {
                    "name": "memory_verification_off",
                    "agent": "direct_llm_tool_agent",
                    "provider": "local_stub",
                    "model": "local-stub",
                    "max_tokens": 64,
                    "retry_count": 0,
                    "extra": {
                        "prompt_file": "ablations/base_tool_agent.md",
                        "system_safety_file": "system_safety_ablation_minimal.md",
                        "ablation": {
                            "pair_id": "memory_verification",
                            "factor": "memory_verification_instruction",
                            "level": "without_memory_verification",
                            "comparison_role": "reference",
                        },
                    },
                },
                {
                    "name": "memory_verification_on",
                    "agent": "direct_llm_tool_agent",
                    "provider": "local_stub",
                    "model": "local-stub",
                    "max_tokens": 64,
                    "retry_count": 0,
                    "extra": {
                        "prompt_file": "ablations/base_tool_agent.md",
                        "prompt_addendum_file": "ablations/memory_verification_instruction.md",
                        "system_safety_file": "system_safety_ablation_minimal.md",
                        "ablation": {
                            "pair_id": "memory_verification",
                            "factor": "memory_verification_instruction",
                            "level": "with_memory_verification",
                            "comparison_role": "treatment",
                        },
                    },
                },
            ],
            "max_steps": 2,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )
    run_dir = run_experiment(config)["run_dir"]
    data = load_run_results(run_dir)

    table = ablation_results_table(data)
    rows = table.to_dict(orient="records")
    overall = [row for row in rows if row["intervention_family"] == "overall"]

    assert {row["level"] for row in overall} == {
        "without_memory_verification",
        "with_memory_verification",
    }
    assert all(row["prompt_version_hash"] for row in overall)
    assert all(row["prompt_template_hash"] for row in overall)
    assert "delta_success_vs_reference" in table.columns
    assert "tool_overuse" in table.columns

    out = tmp_path / "tables"
    build_all_tables(data, out)
    exported = (out / "table4_ablation_results.csv").read_text(encoding="utf-8")
    assert "memory_verification_instruction" in exported
    assert "prompt_version_hash" in exported

    cli_out = tmp_path / "cli_tables"
    cli_main(
        [
            "export-ablation-table",
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(cli_out),
            "--allow-engineering-only",
            "--allow-mock-stub",
        ]
    )
    cli_exported = (cli_out / "table4_ablation_results.csv").read_text(encoding="utf-8")
    assert "scorer_versions" in cli_exported
    assert "cab_typed_final_answer" in cli_exported


def test_bootstrap_function_is_deterministic():
    first = bootstrap_mean_ci([0, 1, 1, 0], seed=3)
    second = bootstrap_mean_ci([0, 1, 1, 0], seed=3)
    assert first == second
    assert first[0] == 0.5


def test_error_case_extraction_writes_categories(tmp_path):
    data = load_run_results(_analysis_run(tmp_path))
    cases = mine_error_cases(data, max_cases=2)
    assert "premature_stopping" in cases
    paths = extract_error_cases(data, tmp_path / "error_cases", max_cases=2)
    names = {path.name for path in paths}
    assert "premature_stopping.jsonl" in names
    assert "README.md" in names


def test_export_paper_assets_writes_run_local_assets(tmp_path):
    run_dir = _analysis_run(tmp_path)
    paths = export_paper_assets(
        run_dir, write_global=False, allow_engineering_only=True, allow_mock_stub=True
    )
    names = {path.name for path in paths}
    assert "statistical_summary.json" in names
    assert "stats_summary.json" in names
    assert "stats_summary.md" in names
    assert "asset_metadata.json" in names
    assert (run_dir / "paper_assets" / "figures" / "figure2_clean_vs_intervention_success.png").exists()
    assert (run_dir / "paper_assets" / "tables" / "table4_ablation_results.csv").exists()


def test_human_validation_export_writes_annotation_packets(tmp_path):
    run_dir = _analysis_run(tmp_path)
    manifest = export_human_validation_sample(
        run_dir,
        output_dir=tmp_path / "human_validation",
        sample_size=4,
        seed=3,
        annotators_per_item=2,
    )

    output_dir = Path(manifest["output_dir"])
    assert manifest["items_sampled"] == 4
    assert manifest["annotation_rows"] == 8
    assert (output_dir / "annotation_export.csv").exists()
    assert (output_dir / "annotation_export.jsonl").exists()
    assert (output_dir / "annotation_interface.html").exists()
    exported = pd.read_csv(output_dir / "annotation_export.csv")
    assert set(ANNOTATION_DIMENSIONS).issubset(exported.columns)
    assert {"domain", "difficulty", "intervention_family", "agent_name", "outcome"}.issubset(
        exported.columns
    )


def test_human_validation_agreement_summary_writes_report(tmp_path):
    annotations = tmp_path / "annotations.csv"
    rows = [
        {
            "item_id": "item1",
            "instance_id": "inst1",
            "agent_name": "agent_a",
            "annotator_id": "ann1",
            "task_understandable": "yes",
            "goal_preserved": "yes",
        },
        {
            "item_id": "item1",
            "instance_id": "inst1",
            "agent_name": "agent_a",
            "annotator_id": "ann2",
            "task_understandable": "yes",
            "goal_preserved": "no",
        },
        {
            "item_id": "item2",
            "instance_id": "inst2",
            "agent_name": "agent_b",
            "annotator_id": "ann1",
            "task_understandable": "no",
            "goal_preserved": "unclear",
        },
        {
            "item_id": "item2",
            "instance_id": "inst2",
            "agent_name": "agent_b",
            "annotator_id": "ann2",
            "task_understandable": "no",
            "goal_preserved": "unclear",
        },
    ]
    pd.DataFrame(rows).to_csv(annotations, index=False)

    summary = summarize_human_validation_annotations(
        annotations,
        output_dir=tmp_path / "validation_summary",
    )

    assert summary["agreement"]["task_understandable"]["percent_agreement"] == 1.0
    assert summary["agreement"]["goal_preserved"]["percent_agreement"] == 0.5
    assert summary["disagreement_examples"]
    assert (tmp_path / "validation_summary" / "validation_report.md").exists()
    assert (tmp_path / "validation_summary" / "table5_human_validation_agreement.csv").exists()


def test_human_validation_agreement_supports_multiple_annotators():
    rows = [
        {"item_id": "item1", "task_understandable": "yes"},
        {"item_id": "item1", "task_understandable": "yes"},
        {"item_id": "item1", "task_understandable": "no"},
        {"item_id": "item2", "task_understandable": "no"},
        {"item_id": "item2", "task_understandable": "no"},
        {"item_id": "item2", "task_understandable": "no"},
    ]

    agreement = compute_agreement(rows)

    assert agreement["task_understandable"]["items_with_two_or_more_annotations"] == 2
    assert agreement["task_understandable"]["krippendorffs_alpha"] is not None


def test_fake_llm_judge_writes_separate_labels_and_calibration(tmp_path):
    run_dir = _analysis_run(tmp_path)
    config = tmp_path / "judge.yaml"
    config.write_text(
        "\n".join(
            [
                "judge_provider: fake_judge",
                "judge_model: fake-judge-v1",
                "prompt_version: judge_v0",
                "temperature: 0.0",
                "max_tokens: 128",
                "retries: 0",
                "sample_size: 3",
                "seed: 5",
                "dimensions:",
                "  - final_answer_correctness",
                "  - recovery_behavior",
                "fake_judge: true",
            ]
        ),
        encoding="utf-8",
    )

    manifest = run_llm_judge(run_dir, config, output_dir=tmp_path / "judge")
    labels_path = Path(manifest["labels_path"])
    labels = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines()]

    assert manifest["safety"]["overwrites_deterministic_scores"] is False
    assert len(labels) == 6
    assert {label["dimension"] for label in labels} == {
        "final_answer_correctness",
        "recovery_behavior",
    }

    human_rows = []
    for label in labels:
        if label["dimension"] != "final_answer_correctness":
            continue
        human_rows.extend(
            [
                {
                    "item_id": label["item_id"],
                    "instance_id": label["instance_id"],
                    "agent_name": label["agent_name"],
                    "final_answer": "short answer",
                    "final_answer_label_correct": label["label"],
                },
                {
                    "item_id": label["item_id"],
                    "instance_id": label["instance_id"],
                    "agent_name": label["agent_name"],
                    "final_answer": "short answer",
                    "final_answer_label_correct": label["label"],
                },
            ]
        )
    human_path = tmp_path / "human.csv"
    pd.DataFrame(human_rows).to_csv(human_path, index=False)

    report = calibrate_llm_judge(labels_path, human_path, output_dir=tmp_path / "calibration")

    assert report["n_comparisons"] == len(human_rows) // 2
    assert report["agreement"]["percent_agreement"] == 1.0
    assert "bias_by_agent" in report
    assert "sensitivity_to_answer_length" in report
    assert (tmp_path / "calibration" / "judge_calibration_report.md").exists()
