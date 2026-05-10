from pathlib import Path

from causal_agent_bench.analysis.error_analysis import extract_error_cases, mine_error_cases
from causal_agent_bench.analysis.figures import build_all_figures
from causal_agent_bench.analysis.load_results import load_run_results
from causal_agent_bench.analysis.report import export_paper_assets
from causal_agent_bench.analysis.tables import bootstrap_mean_ci, build_all_tables
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
    assert "figure6_trajectory_final_disagreement.pdf" in names


def test_tables_are_created(tmp_path):
    data = load_run_results(_analysis_run(tmp_path))
    paths = build_all_tables(data, tmp_path / "tables")
    names = {path.name for path in paths}
    assert "table1_benchmark_statistics.csv" in names
    assert "table2_main_agent_performance.tex" in names
    assert "table5_human_validation_agreement.md" in names


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
    paths = export_paper_assets(run_dir, write_global=False)
    names = {path.name for path in paths}
    assert "statistical_summary.json" in names
    assert (run_dir / "paper_assets" / "figures" / "figure2_clean_vs_intervention_success.png").exists()
    assert (run_dir / "paper_assets" / "tables" / "table4_ablation_results.csv").exists()
