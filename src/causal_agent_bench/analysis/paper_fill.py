from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.analysis.load_results import RunResults, load_run_results
from causal_agent_bench.analysis.report import export_paper_assets
from causal_agent_bench.analysis.tables import (
    ablation_results_table,
    benchmark_statistics_table,
    main_agent_performance_table,
)
from causal_agent_bench.claim_ledger import CLAIM_ARTIFACT_MAP, update_claim_ledger
from causal_agent_bench.safety.claim_evidence_matrix import artifact_claim_eligibility
from causal_agent_bench.safety.common import classify_run_entry, strict_bool
from causal_agent_bench.safety.export_guards import validate_export_source

NON_SCIENTIFIC_EVIDENCE_SCOPES = frozenset(
    {
        "pilot_stub_engineering_only",
        "deterministic_baseline_engineering",
        "engineering_only_local_stub",
        "mock_diagnostic_only",
        "mock_diagnostic",
        "stub_engineering",
        "preliminary_or_engineering",
        "local_open_weight_unvalidated",
    }
)

CLAIM_FILL_MAP = CLAIM_ARTIFACT_MAP


@dataclass
class PaperFillSummary:
    base_tasks: int
    intervention_instances: int
    agents: int
    domains: str
    difficulty_levels: str
    avg_max_steps: str
    mean_absolute_degradation: float | None
    spearman_clean_vs_acrs: float | None
    benchmark_version: str
    evidence_scope: str
    config_hash: str
    run_dir: str
    model_ids: str
    git_commit: str | None
    main_finding: str
    cautious_prefix: str


@dataclass
class RunVerificationReport:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_scope: str | None = None
    non_oracle_agents: list[str] = field(default_factory=list)
    oracle_agents: list[str] = field(default_factory=list)


def verify_run_for_paper_fill(
    data: RunResults,
    *,
    allow_engineering_only: bool = False,
) -> RunVerificationReport:
    errors: list[str] = []
    warnings: list[str] = []
    metadata = data.run_metadata

    if not (data.run_dir / "scores.jsonl").exists() and not (data.run_dir / "aggregate_scores.json").exists():
        errors.append("missing scores (scores.jsonl or aggregate_scores.json)")
    if data.scores_df.empty:
        errors.append("no score records loaded")
    if data.instances_df.empty:
        errors.append("no benchmark instances loaded")
    if not metadata.get("config_hash"):
        errors.append("run metadata missing config_hash")

    dataset_version = _dataset_version(data)
    if not dataset_version or dataset_version == "unknown":
        warnings.append("dataset_version missing or unknown in run metadata")

    agents = sorted(data.aggregate.get("by_agent", {}))
    oracle = [agent for agent in agents if _is_oracle_agent(agent)]
    non_oracle = [agent for agent in agents if not _is_oracle_agent(agent)]

    if not non_oracle:
        errors.append("no non-oracle agents in aggregate scores")
    if not oracle:
        warnings.append("no oracle sanity-check agent found (recommended for upper-bound checks)")

    scope = _evidence_scope_from_data(data)
    if scope in NON_SCIENTIFIC_EVIDENCE_SCOPES and not allow_engineering_only:
        errors.append(
            f"evidence_scope {scope!r} is engineering-only; "
            "use --allow-engineering-only for draft previews or run paid/local LLM pilots"
        )
    classified = classify_run_entry({"path": str(data.run_dir)}, data.run_dir.parent.parent)
    if not allow_engineering_only and not classified["paper_eligible"]:
        errors.append(
            "run is not eligible for paper fill: "
            f"{classified['paper_eligibility_reason']} (classification={classified['classification']})"
        )

    if not allow_engineering_only:
        missing_models = [
            agent for agent in non_oracle if not _agent_has_model_metadata(data, agent)
        ]
        if missing_models:
            errors.append(
                "non-oracle agents missing provider/model metadata in trajectories: "
                + ", ".join(missing_models)
            )

    if not (data.run_dir / "paper_assets").exists():
        warnings.append("paper_assets/ missing; export will run during fill")

    return RunVerificationReport(
        passed=not errors,
        errors=errors,
        warnings=warnings,
        evidence_scope=scope,
        non_oracle_agents=non_oracle,
        oracle_agents=oracle,
    )


def build_paper_fill_summary(data: RunResults) -> PaperFillSummary:
    stats = {row["statistic"]: row["value"] for _, row in benchmark_statistics_table(data).iterrows()}
    perf = main_agent_performance_table(data)
    degradations = [
        float(value)
        for value in perf.get("absolute_degradation", [])
        if value is not None and str(value) != "nan"
    ]
    mean_deg = round(sum(degradations) / len(degradations), 3) if degradations else None
    ranking = data.aggregate.get("ranking_instability", {})
    spearman = ranking.get("spearman_clean_vs_acrs")
    version = _dataset_version(data)
    scope = _evidence_scope_from_data(data)
    prefix = _cautious_prefix(scope, version)
    return PaperFillSummary(
        base_tasks=int(stats.get("base_tasks", 0) or 0),
        intervention_instances=int(stats.get("intervention_instances", 0) or 0),
        agents=len(perf),
        domains=str(stats.get("domains", "not reported")),
        difficulty_levels=str(stats.get("difficulty_levels", "not reported")),
        avg_max_steps=str(stats.get("avg_max_steps", "not reported")),
        mean_absolute_degradation=mean_deg,
        spearman_clean_vs_acrs=float(spearman) if spearman is not None else None,
        benchmark_version=version,
        evidence_scope=scope,
        config_hash=str(data.run_metadata.get("config_hash", "unknown")),
        run_dir=_relative_run_dir(data.run_dir),
        model_ids=_model_ids(data),
        git_commit=data.run_metadata.get("git_commit"),
        main_finding=_main_finding_sentence(mean_deg, spearman, len(perf)),
        cautious_prefix=prefix,
    )


def fill_paper_from_run(
    run_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    allow_engineering_only: bool = False,
    allow_incomplete: bool = False,
    allow_placeholder: bool = False,
    allow_mock_stub: bool = False,
    export_assets: bool = True,
    write_global_tables: bool = True,
    update_ledger: bool = True,
    promote_to_supported: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root or Path.cwd()).resolve()
    run_path = Path(run_dir)
    if not run_path.exists():
        raise ValueError(f"run directory does not exist: {run_dir}")
    guard = validate_export_source(
        run_path,
        allow_engineering_only=allow_engineering_only,
        allow_incomplete=allow_incomplete,
        allow_placeholder=allow_placeholder,
        allow_mock_stub=allow_mock_stub,
        operation="fill-paper-from-run",
    )
    data = load_run_results(run_path)
    verification = verify_run_for_paper_fill(data, allow_engineering_only=allow_engineering_only)
    if not verification.passed:
        raise ValueError("run verification failed: " + "; ".join(verification.errors))

    if export_assets:
        export_paper_assets(
            data.run_dir,
            write_global=write_global_tables,
            allow_engineering_only=allow_engineering_only,
            allow_incomplete=allow_incomplete,
            allow_placeholder=allow_placeholder,
            allow_mock_stub=allow_mock_stub,
        )

    summary = build_paper_fill_summary(data)
    generated_dir = root / "paper" / "latexpaper" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    _write_generated_fragments(generated_dir, summary, data, root, guard=guard)

    mapping_path = root / "docs" / "PAPER_EVIDENCE_MAPPING.json"
    mapping_path.write_text(
        json.dumps(_build_evidence_mapping(summary, data, verification, root, guard=guard), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    ledger_updates: list[dict[str, Any]] = []
    if update_ledger:
        ledger_updates = _update_claim_ledger_from_fill(
            root / "docs" / "claim_ledger.json",
            summary,
            data,
            root,
            promote_to_supported=promote_to_supported,
        )

    return {
        "filled": True,
        "verification": asdict(verification),
        "summary": asdict(summary),
        "mapping_path": str(mapping_path.relative_to(root)),
        "generated_dir": str(generated_dir.relative_to(root)),
        "ledger_updates": ledger_updates,
        "warnings": verification.warnings,
        "export_guard": {
            "watermark": guard.get("watermark"),
            "requires_watermark": guard.get("requires_watermark"),
            "classification": guard.get("classification"),
        },
    }


def _export_warning_banner(guard: dict[str, Any] | None) -> str:
    if not guard or not guard.get("requires_watermark"):
        return ""
    watermark = str(guard.get("watermark") or "").strip()
    if not watermark:
        return ""
    return (
        f"% {watermark}\n"
        f"\\noindent\\textbf{{Evidence warning.}} {_latex_escape(watermark)}\\\\\n\n"
    )


def _write_generated_fragments(
    generated_dir: Path,
    summary: PaperFillSummary,
    data: RunResults,
    repo_root: Path,
    *,
    guard: dict[str, Any] | None = None,
) -> None:
    warning_banner = _export_warning_banner(guard)
    deg_text = f"{summary.mean_absolute_degradation:.3f}" if summary.mean_absolute_degradation is not None else "not estimated"
    rho_text = (
        f"{summary.spearman_clean_vs_acrs:.3f}"
        if summary.spearman_clean_vs_acrs is not None
        else "not estimated"
    )

    (generated_dir / "00_abstract.tex").write_text(
        warning_banner
        + "\n".join(
            [
                f"{summary.cautious_prefix} we evaluate {summary.base_tasks} base tasks, "
                f"{summary.intervention_instances} intervention instances, and {summary.agents} non-oracle agents "
                f"on \\benchmark\\ ({_latex_escape(summary.benchmark_version)}). "
                f"These results suggest that clean success may overstate robust competence by "
                f"{deg_text} points on average (absolute degradation), and that rankings under clean success "
                f"correlate with rankings under causal robustness with Spearman $\\rho={rho_text}$. "
                "This pilot summary is linked to a specific run directory and scorer; it is not a final scientific claim.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (generated_dir / "01_introduction_snippet.tex").write_text(
        warning_banner
        + "\n".join(
            [
                f"\\noindent\\textbf{{Pilot scope.}} {_latex_escape(_short_domains(summary.domains))}.",
                f"\\noindent {summary.cautious_prefix} {summary.main_finding}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (generated_dir / "03_benchmark_stats_table.tex").write_text(
        warning_banner + _benchmark_stats_table_tex(summary),
        encoding="utf-8",
    )

    (generated_dir / "07_results.tex").write_text(
        warning_banner + _results_body_tex(summary),
        encoding="utf-8",
    )

    (generated_dir / "08_human_validation.tex").write_text(
        warning_banner + _human_validation_tex(repo_root),
        encoding="utf-8",
    )

    (generated_dir / "09_ablations.tex").write_text(
        warning_banner + _ablations_tex(data, repo_root),
        encoding="utf-8",
    )


def _results_body_tex(summary: PaperFillSummary) -> str:
    deg = summary.mean_absolute_degradation
    rho = summary.spearman_clean_vs_acrs
    return "\n".join(
        [
            "\\section{Results}",
            "",
            f"{summary.cautious_prefix} Table~\\ref{{tab:main-performance}} and Figures~\\ref{{fig:family-breakdown}}--\\ref{{fig:ranking-instability}} "
            f"summarize a reproducible pilot linked to run \\texttt{{{_latex_escape(summary.run_dir)}}} "
            f"(config hash \\texttt{{{_latex_escape(summary.config_hash)}}}, evidence scope \\texttt{{{_latex_escape(summary.evidence_scope)}}}). "
            "These results suggest patterns in robustness under controlled interventions; they should not be generalized beyond this dataset version without further validation.",
            "",
            "\\subsection{RQ1: Does clean success overestimate robust competence?}",
            f"\\textbf{{Pilot observation.}} On this run, mean absolute degradation across non-oracle agents is "
            f"{deg if deg is not None else 'not estimated'}. This probes \\claimref{{C1}}.",
            "",
            "\\begin{table}[t]",
            "\\centering",
            "\\caption{Main agent performance (pilot run; non-oracle agents only).}",
            "\\label{tab:main-performance}",
            "\\resizebox{\\linewidth}{!}{%",
            "\\input{../../tables/table2_main_agent_performance.tex}",
            "}",
            "\\end{table}",
            "",
            "\\subsection{RQ2: Which intervention families cause the largest degradation?}",
            "",
            "\\begin{figure}[t]",
            "\\centering",
            "\\includegraphics[width=0.9\\linewidth]{../../figures/figure3_intervention_family_breakdown.png}",
            "\\caption{Intervention-family breakdown (pilot run).}",
            "\\label{fig:family-breakdown}",
            "\\end{figure}",
            "",
            "\\subsection{RQ3: Do clean-success rankings match causal-robustness rankings?}",
            f"Spearman correlation between clean-success and \\acrs\\ rankings is "
            f"{rho if rho is not None else 'not estimated'} on this run (\\claimref{{C4}}).",
            "",
            "\\begin{figure}[t]",
            "\\centering",
            "\\includegraphics[width=0.9\\linewidth]{../../figures/figure4_ranking_instability.png}",
            "\\caption{Ranking instability between clean success and \\acrs\\ (pilot run).}",
            "\\label{fig:ranking-instability}",
            "\\end{figure}",
            "",
            "\\subsection{RQ4: Do trajectory metrics expose failures hidden by final-answer scoring?}",
            "",
            "\\begin{figure}[t]",
            "\\centering",
            "\\includegraphics[width=0.9\\linewidth]{../../figures/figure6_trajectory_final_disagreement.png}",
            "\\caption{Trajectory vs final-success disagreement (pilot run).}",
            "\\label{fig:trajectory-disagreement}",
            "\\end{figure}",
            "",
            f"\\noindent\\textbf{{Evidence.}} Run directory: \\texttt{{{_latex_escape(summary.run_dir)}}}; models: {_latex_escape(summary.model_ids)}.",
            "",
        ]
    )


def _human_validation_tex(repo_root: Path) -> str:
    table_path = repo_root / "tables" / "table5_human_validation_agreement.csv"
    if _human_validation_ready(table_path):
        return "\n".join(
            [
                "\\section{Human Validation}",
                "",
                "In our pilot, we report human-validation agreement statistics from the annotated sample linked to this release. "
                "These results suggest improved auditability but do not by themselves establish deployment readiness.",
                "",
                "\\begin{table}[t]",
                "\\centering",
                "\\caption{Human validation agreement (pilot annotations).}",
                "\\label{tab:human-validation}",
                "\\input{../../tables/table5_human_validation_agreement.tex}",
                "\\end{table}",
                "",
            ]
        )
    return "\n".join(
        [
            "\\section{Human Validation}",
            "",
            "Human validation is not yet complete for paper claims. Table~5 remains a placeholder until annotations and adjudication are finished (\\claimref{C3}, \\claimref{C10}).",
            "",
        ]
    )


def _ablations_tex(data: RunResults, repo_root: Path) -> str:
    frame = ablation_results_table(data)
    if frame.empty or ("status" in frame.columns and (frame["status"] == "not yet run").any()):
        return "\n".join(
            [
                "\\section{Ablations}",
                "",
                "No ablation result is claimed in this draft. Run scaffold or prompt ablation configs before filling Table~4 (\\claimref{C6}).",
                "",
            ]
        )
    return "\n".join(
        [
            "\\section{Ablations}",
            "",
            "In our pilot, Table~\\ref{tab:ablations} reports prompt/scaffold ablations exported from the linked run. "
            "These results suggest selective robustness effects that should be read alongside cost and latency tradeoffs.",
            "",
            "\\begin{table}[t]",
            "\\centering",
            "\\caption{Prompt/scaffold ablations (pilot run).}",
            "\\label{tab:ablations}",
            "\\resizebox{\\linewidth}{!}{%",
            "\\input{../../tables/table4_ablation_results.tex}",
            "}",
            "\\end{table}",
            "",
        ]
    )


def _benchmark_stats_table_tex(summary: PaperFillSummary) -> str:
    return "\n".join(
        [
            "\\begin{table}[t]",
            "\\centering",
            f"\\caption{{Benchmark statistics for {_latex_escape(summary.benchmark_version)} (pilot-linked run).}}",
            "\\label{tab:benchmark-stats}",
            "\\begin{tabular}{ll}",
            "\\toprule",
            "Statistic & Value \\\\",
            "\\midrule",
            f"Base tasks & {summary.base_tasks} \\\\",
            f"Intervention instances & {summary.intervention_instances} \\\\",
            f"Domains & {_latex_escape(_short_domains(summary.domains))} \\\\",
            f"Difficulty levels & {_latex_escape(summary.difficulty_levels)} \\\\",
            f"Average maximum steps & {_latex_escape(summary.avg_max_steps)} \\\\",
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
        ]
    )


def _build_evidence_mapping(
    summary: PaperFillSummary,
    data: RunResults,
    verification: RunVerificationReport,
    repo_root: Path,
    *,
    guard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_rel = _relative_run_dir(data.run_dir)
    return {
        "schema_version": "paper_evidence_mapping_v1",
        "filled_at": datetime.now(UTC).isoformat(),
        "release_version": "0.1.0-rc1",
        "run_dir": run_rel,
        "config_hash": summary.config_hash,
        "dataset_version": summary.benchmark_version,
        "evidence_scope": summary.evidence_scope,
        "git_commit": summary.git_commit,
        "model_ids": summary.model_ids,
        "scorer": "deterministic_heuristic_v1",
        "non_oracle_agents": verification.non_oracle_agents,
        "oracle_agents": verification.oracle_agents,
        "summary": asdict(summary),
        "claim_artifacts": {
            claim_id: {"artifacts": artifacts, "run_artifacts": [f"{run_rel}/scores.jsonl"]}
            for claim_id, artifacts in CLAIM_FILL_MAP.items()
        },
        "generated_fragments": [
            "paper/latexpaper/generated/00_abstract.tex",
            "paper/latexpaper/generated/01_introduction_snippet.tex",
            "paper/latexpaper/generated/03_benchmark_stats_table.tex",
            "paper/latexpaper/generated/07_results.tex",
            "paper/latexpaper/generated/08_human_validation.tex",
            "paper/latexpaper/generated/09_ablations.tex",
        ],
        "limitations": [
            "Pilot fill does not promote claims to supported without human validation and --promote-to-supported.",
            "Engineering-only runs require --allow-engineering-only and must not be cited as scientific evidence.",
        ],
        "export_guard": {
            "watermark": guard.get("watermark") if guard else None,
            "requires_watermark": guard.get("requires_watermark") if guard else False,
            "classification": guard.get("classification") if guard else None,
        },
    }


def _update_claim_ledger_from_fill(
    ledger_path: Path,
    summary: PaperFillSummary,
    data: RunResults,
    repo_root: Path,
    *,
    promote_to_supported: bool,
) -> list[dict[str, Any]]:
    status = "engineering_only" if summary.evidence_scope in NON_SCIENTIFIC_EVIDENCE_SCOPES else "weakened"
    run_rel = _relative_run_dir(data.run_dir)
    evidence_base = [
        run_rel,
        f"{run_rel}/run_metadata.json",
        f"{run_rel}/scores.jsonl",
        "docs/PAPER_EVIDENCE_MAPPING.json",
    ]
    updates = []
    for claim_id, artifacts in CLAIM_FILL_MAP.items():
        claim_status = status
        if promote_to_supported and _claim_can_be_supported(claim_id, artifacts, data, repo_root):
            claim_status = "supported"
        if claim_id == "C10" and claim_status != "supported":
            continue
        updates.append(
            update_claim_ledger(
                ledger_path,
                claim_id=claim_id,
                status=claim_status,
                evidence_paths=evidence_base + artifacts,
                linked_run_dirs=[run_rel],
                linked_tables_figures=artifacts,
            )
        )
    return updates


def _human_validation_ready(table_path: Path) -> bool:
    if not table_path.exists():
        return False
    text = table_path.read_text(encoding="utf-8").lower()
    return "not yet run" not in text and "placeholder" not in text


def _claim_can_be_supported(
    claim_id: str,
    artifacts: list[str],
    data: RunResults,
    repo_root: Path,
) -> bool:
    if not _run_can_support_claims(data):
        return False
    if not artifacts:
        return False
    if not all(artifact_claim_eligibility(rel, repo_root)[0] for rel in artifacts):
        return False
    if claim_id in {"C3", "C10"}:
        human_table = repo_root / "tables" / "table5_human_validation_agreement.csv"
        return _human_validation_ready(human_table) and artifact_claim_eligibility(
            "tables/table5_human_validation_agreement.csv",
            repo_root,
        )[0]
    return claim_id in {"C1", "C2", "C4", "C5", "C6", "C7", "C8"}


def _run_can_support_claims(data: RunResults) -> bool:
    metadata = data.run_metadata or {}
    classified = classify_run_entry({"path": str(data.run_dir)}, data.run_dir.parent.parent)
    if classified["classification"] not in {"provider_backed_pilot", "main_benchmark"}:
        return False
    if not classified["paper_eligible"] or not strict_bool(metadata.get("scientific_evidence")):
        return False
    scope = str(metadata.get("evidence_scope") or "").lower()
    if scope in NON_SCIENTIFIC_EVIDENCE_SCOPES or any(
        marker in scope for marker in ("mock", "stub", "engineering", "preliminary", "incomplete", "interrupted")
    ):
        return False
    return not strict_bool(metadata.get("not_real_llm_behavior"))


def _dataset_version(data: RunResults) -> str:
    for key in ("dataset_version", "benchmark_version", "source_benchmark_version"):
        value = data.run_metadata.get(key)
        if value:
            return str(value)
    gen = data.run_dir / "generation_report.json"
    if gen.exists():
        payload = json.loads(gen.read_text(encoding="utf-8"))
        return str(payload.get("benchmark_version", "unknown"))
    return "unknown"


def _evidence_scope_from_data(data: RunResults) -> str:
    perf = main_agent_performance_table(data)
    if not perf.empty and "evidence_scope" in perf.columns:
        return str(perf["evidence_scope"].iloc[0])
    return str(data.run_metadata.get("evidence_scope", "unknown"))


def _model_ids(data: RunResults) -> str:
    if "model_name" not in data.trajectories_df.columns:
        return str(data.run_metadata.get("model", "not logged"))
    models = sorted(
        {
            str(value)
            for value in data.trajectories_df["model_name"].dropna().unique()
            if str(value)
        }
    )
    return ", ".join(models) if models else "not logged"


def _agent_has_model_metadata(data: RunResults, agent: str) -> bool:
    rows = data.trajectories_df[data.trajectories_df["agent_name"] == agent]
    if rows.empty:
        return False
    if "model_name" in rows.columns and rows["model_name"].notna().any():
        return True
    return bool(data.run_metadata.get("model"))


def _is_oracle_agent(agent: str) -> bool:
    return agent == "scripted_oracle_agent"


def _relative_run_dir(run_dir: Path) -> str:
    try:
        return run_dir.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return run_dir.as_posix()


def _cautious_prefix(scope: str, version: str) -> str:
    if scope in NON_SCIENTIFIC_EVIDENCE_SCOPES:
        return f"In an engineering-only pilot on \\benchmark\\ ({_latex_escape(version)}),"
    return f"In our pilot on \\benchmark\\ ({_latex_escape(version)}),"


def _main_finding_sentence(mean_deg: float | None, spearman: float | None, n_agents: int) -> str:
    parts = []
    if mean_deg is not None:
        parts.append(
            f"mean absolute degradation of {mean_deg:.3f} between clean and intervention conditions across {n_agents} agents"
        )
    if spearman is not None:
        parts.append(f"Spearman rank correlation $\\rho={spearman:.3f}$ between clean-success and \\acrs\\ rankings")
    if not parts:
        return "These results suggest that intervention stress tests expose robustness gaps not visible from clean success alone."
    return "These results suggest " + ", and that ".join(parts) + "."


def _short_domains(domains: str) -> str:
    if len(domains) <= 120:
        return domains
    return domains[:117] + "..."


def _latex_escape(text: str) -> str:
    escaped = str(text)
    for key, value in {"\\": "\\textbackslash{}", "_": "\\_", "%": "\\%", "&": "\\&", "#": "\\#"}.items():
        escaped = escaped.replace(key, value)
    return escaped
