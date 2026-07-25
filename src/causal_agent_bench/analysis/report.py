from __future__ import annotations

from pathlib import Path

from causal_agent_bench.analysis.load_results import RunResults, load_run_results

# ``export_paper_assets`` lives in paper_assets.py; re-exported here (and via
# analysis/__init__.py) for backwards-compatible import paths.
from causal_agent_bench.analysis.paper_assets import export_paper_assets as export_paper_assets
from causal_agent_bench.analysis.tables import dataframe_to_markdown, main_agent_performance_table


def analyze_run(run_dir: str | Path, *, allow_incomplete: bool = False) -> Path:
    from causal_agent_bench.runners.run_completion import assert_complete_for_pipeline

    state = assert_complete_for_pipeline(run_dir, operation="analyze", allow_incomplete=allow_incomplete)
    data = load_run_results(run_dir)
    report_path = data.run_dir / "analysis_report.md"
    report = _analysis_report(data)
    if state["completion_state"] != "complete":
        report = (
            "> **INCOMPLETE / PRELIMINARY RUN** — not final scientific evidence.\n\n" + report
        )
    report_path.write_text(report, encoding="utf-8")
    return report_path


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
