from __future__ import annotations

from pathlib import Path

from causal_agent_bench.analysis.error_analysis import extract_error_cases
from causal_agent_bench.analysis.figures import build_all_figures
from causal_agent_bench.analysis.load_results import RunResults, load_run_results
from causal_agent_bench.analysis.tables import (
    build_all_tables,
    dataframe_to_markdown,
    main_agent_performance_table,
    statistical_summary,
)
from causal_agent_bench.utils.io import write_json


def analyze_run(run_dir: str | Path) -> Path:
    data = load_run_results(run_dir)
    report_path = data.run_dir / "analysis_report.md"
    report_path.write_text(_analysis_report(data), encoding="utf-8")
    return report_path


def export_paper_assets(run_dir: str | Path, *, write_global: bool = True) -> list[Path]:
    data = load_run_results(run_dir)
    assets_dir = data.run_dir / "paper_assets"
    figure_dir = assets_dir / "figures"
    table_dir = assets_dir / "tables"
    error_dir = data.run_dir / "error_cases"
    paths: list[Path] = []
    paths.extend(build_all_figures(data, figure_dir))
    paths.extend(build_all_tables(data, table_dir))
    paths.extend(extract_error_cases(data, error_dir))
    stats_path = assets_dir / "statistical_summary.json"
    write_json(stats_path, statistical_summary(data))
    paths.append(stats_path)

    if write_global:
        root = Path.cwd()
        paths.extend(build_all_figures(data, root / "figures"))
        paths.extend(build_all_tables(data, root / "tables"))

    return paths


def _analysis_report(data: RunResults) -> str:
    perf = main_agent_performance_table(data)
    lines = [
        "# CausalAgentBench Analysis Report",
        "",
        "This report is generated from deterministic run artifacts. It is descriptive and should not be treated as a scientific claim until the planned experiments and validation are complete.",
        "",
        f"- Run directory: `{data.run_dir}`",
        f"- Instances: {data.aggregate.get('n_instances', len(data.instances))}",
        f"- Agents: {data.aggregate.get('n_agents', data.scores_df['agent_name'].nunique() if not data.scores_df.empty else 0)}",
        f"- Score records: {data.aggregate.get('n_score_records', len(data.scores))}",
        "",
        "## Main Agent Performance",
        "",
        dataframe_to_markdown(perf).strip(),
        "",
        "## Ranking Instability",
        "",
        f"- Spearman clean-vs-ACRS: `{data.aggregate.get('ranking_instability', {}).get('spearman_clean_vs_acrs')}`",
        "",
        "## Paper Asset Export",
        "",
        "Run:",
        "",
        f"```bash\npython -m causal_agent_bench export-paper-assets --run-dir {data.run_dir}\n```",
        "",
        "## Caveats",
        "",
        "- Deterministic heuristic scoring is auditable but incomplete.",
        "- Oracle baselines are sanity checks and should not be interpreted as deployable agents.",
        "- Placeholder tables remain for ablations and human validation until those runs exist.",
    ]
    return "\n".join(lines) + "\n"
