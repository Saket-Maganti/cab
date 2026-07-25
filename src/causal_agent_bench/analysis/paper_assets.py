from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from causal_agent_bench.analysis.error_analysis import extract_error_cases
from causal_agent_bench.analysis.figures import build_all_figures
from causal_agent_bench.analysis.load_results import RunResults, load_run_results
from causal_agent_bench.analysis.statistics import build_statistical_report, statistical_report
from causal_agent_bench.analysis.tables import (
    _is_oracle_agent,
    ablation_results_table,
    asset_metadata,
    benchmark_statistics_table,
    human_validation_agreement_table,
    intervention_family_performance_table,
    main_agent_performance_table,
    oracle_sanity_check_table,
    paired_clean_vs_intervention_table,
    performance_vs_cost_table,
    ranking_instability_table,
    robustness_vs_cost_table,
    with_asset_metadata,
    write_table_bundle,
)
from causal_agent_bench.runners.evidence_scope import classify_evidence_scope
from causal_agent_bench.safety.export_guards import apply_export_watermark, validate_export_source
from causal_agent_bench.utils.io import write_json

ENGINEERING_ONLY_SCOPES = frozenset(
    {
        "pilot_stub_engineering_only",
        "deterministic_baseline_engineering",
        "engineering_only",
        "local_stub",
        "deterministic_smoke",
    }
)


@dataclass(frozen=True)
class TableAssetSpec:
    asset_id: str
    title: str
    caption: str
    builder: Callable[[RunResults], pd.DataFrame]


CANONICAL_TABLES: tuple[TableAssetSpec, ...] = (
    TableAssetSpec(
        "table1_benchmark_statistics",
        "Table 1: Benchmark statistics",
        "Table 1: Benchmark statistics for the evaluated bundle (base tasks, instances, domains).",
        benchmark_statistics_table,
    ),
    TableAssetSpec(
        "table2_main_agent_performance",
        "Table 2: Main agent performance",
        "Table 2: Clean success, intervention success, and ACRS by agent (oracle agents excluded).",
        main_agent_performance_table,
    ),
    TableAssetSpec(
        "table2_oracle_sanity_check",
        "Table 2 oracle sanity check",
        "Oracle sanity-check upper bound (not a realistic agent baseline).",
        oracle_sanity_check_table,
    ),
    TableAssetSpec(
        "table3_intervention_family_performance",
        "Table 3: Intervention-family performance",
        "Table 3: Per-intervention-family success and degradation metrics.",
        intervention_family_performance_table,
    ),
    TableAssetSpec(
        "table4_ablation_results",
        "Table 4: Ablations",
        "Table 4: Prompt/scaffold ablation results when ablation metadata is present.",
        ablation_results_table,
    ),
    TableAssetSpec(
        "table5_human_validation_agreement",
        "Table 5: Human validation",
        "Table 5: Human validation agreement (or placeholder until annotations exist).",
        human_validation_agreement_table,
    ),
    TableAssetSpec(
        "table6_performance_vs_cost",
        "Table 6: Performance and cost/runtime",
        "Table 6: Performance and recorded cost/runtime fields by agent; provenance determines whether cost is measured or estimated.",
        performance_vs_cost_table,
    ),
    TableAssetSpec(
        "table7_robustness_vs_cost",
        "Table 7: Robustness and cost/runtime",
        "Table 7: Robustness, degradation, and recorded resource-use fields by agent.",
        robustness_vs_cost_table,
    ),
    TableAssetSpec(
        "table8_paired_clean_vs_intervention",
        "Table 8: Matched clean/intervention outcomes",
        "Table 8: Matched clean/intervention estimates and paired effect sizes.",
        paired_clean_vs_intervention_table,
    ),
    TableAssetSpec(
        "table9_rank_comparison",
        "Table 9: Clean-success and robustness rank comparison",
        "Table 9: Point ranks and rank changes between clean success and robustness.",
        ranking_instability_table,
    ),
)

CANONICAL_FIGURES: tuple[dict[str, str], ...] = (
    {"asset_id": "figure1_benchmark_schematic", "title": "Figure 1: Benchmark overview", "caption": "Figure 1: Benchmark overview schematic (clean vs intervention conditions)."},
    {"asset_id": "figure2_clean_vs_intervention_success", "title": "Figure 2: Clean vs intervention", "caption": "Figure 2: Clean versus intervention success rates by agent."},
    {"asset_id": "figure3_intervention_family_degradation", "title": "Figure 3: Family degradation", "caption": "Figure 3: Intervention-family degradation relative to clean success."},
    {"asset_id": "figure4_ranking_instability", "title": "Figure 4: Ranking instability", "caption": "Figure 4: Ranking instability between clean success and ACRS."},
    {"asset_id": "figure5_cost_vs_robustness", "title": "Figure 5: Cost vs robustness", "caption": "Figure 5: Average cost per task versus ACRS (oracle excluded)."},
    {"asset_id": "figure6_trajectory_failure_taxonomy", "title": "Figure 6: Failure taxonomy", "caption": "Figure 6: Mined trajectory failure taxonomy counts (audit aid)."},
    {"asset_id": "figure7_human_judge_agreement", "title": "Figure 7: Human/judge agreement", "caption": "Figure 7: Human validation or LLM-judge agreement (when available)."},
    {"asset_id": "figure3_intervention_family_breakdown", "title": "Figure 3b: Family robustness profile", "caption": "Figure 3b: Intervention-family success by agent."},
)


def assess_run_for_paper_assets(data: RunResults) -> dict[str, Any]:
    agents = (
        sorted({str(name) for name in data.scores_df["agent_name"].dropna().unique()})
        if not data.scores_df.empty
        else []
    )
    non_oracle = [agent for agent in agents if not _is_oracle_agent(agent)]
    providers = set()
    if not data.trajectories_df.empty and "provider" in data.trajectories_df:
        providers = {
            str(value)
            for value in data.trajectories_df["provider"].dropna().unique()
            if str(value) not in {"", "None"}
        }
    run_name = str(data.run_metadata.get("run_name") or data.run_dir.name)
    evidence_scope = data.run_metadata.get("evidence_scope") or classify_evidence_scope(providers, run_name=run_name)
    engineering_only = (
        str(evidence_scope) in ENGINEERING_ONLY_SCOPES
        or "stub" in run_name.lower()
        or "smoke" in run_name.lower()
        or providers <= {"local_stub"}
    )
    oracle_only = bool(agents) and not non_oracle
    return {
        "evidence_scope": str(evidence_scope),
        "engineering_only": engineering_only,
        "oracle_only": oracle_only,
        "eligible_for_paper_claims": not engineering_only and not oracle_only,
        "agents": agents,
        "non_oracle_agents": non_oracle,
        "run_dir": str(data.run_dir),
        "run_name": run_name,
    }


def validate_paper_asset_run(
    assessment: dict[str, Any],
    *,
    allow_engineering_only: bool = False,
) -> list[str]:
    issues: list[str] = []
    if assessment.get("oracle_only"):
        issues.append(
            "run contains only oracle agents; paper tables/figures must exclude oracle from main claims"
        )
    if assessment.get("engineering_only") and not allow_engineering_only:
        issues.append(
            f"run evidence_scope={assessment.get('evidence_scope')!r} is engineering-only; "
            "pass --allow-engineering-only to export marked scaffold assets"
        )
    return issues


def export_paper_assets(
    run_dir: str | Path,
    *,
    write_global: bool = True,
    allow_engineering_only: bool = False,
    allow_incomplete: bool = False,
    allow_placeholder: bool = False,
    allow_mock_stub: bool = False,
) -> list[Path]:
    from causal_agent_bench.runners.run_completion import assert_complete_for_pipeline

    guard = validate_export_source(
        run_dir,
        allow_engineering_only=allow_engineering_only,
        allow_incomplete=allow_incomplete,
        allow_placeholder=allow_placeholder,
        allow_mock_stub=allow_mock_stub,
        operation="export-paper-assets",
    )
    assert_complete_for_pipeline(run_dir, operation="export-paper-assets", allow_incomplete=allow_incomplete)
    data = load_run_results(run_dir)
    assessment = assess_run_for_paper_assets(data)
    if guard.get("requires_watermark"):
        assessment = {**assessment, "engineering_only": True, "eligible_for_paper_claims": False}
    issues = validate_paper_asset_run(assessment, allow_engineering_only=allow_engineering_only)
    if issues:
        raise ValueError("; ".join(issues))
    watermark = guard.get("watermark")

    assets_dir = data.run_dir / "paper_assets"
    figure_dir = assets_dir / "figures"
    table_dir = assets_dir / "tables"
    paths: list[Path] = []
    manifest_entries: list[dict[str, Any]] = []

    paths.extend(_export_tables(data, table_dir, assessment, manifest_entries, watermark=watermark))
    paths.extend(
        _export_figures(data, figure_dir, assessment, manifest_entries, watermark=watermark)
    )
    paths.extend(extract_error_cases(data, data.run_dir / "error_cases"))
    paths.extend(build_statistical_report(data, assets_dir))

    metadata = asset_metadata(data)
    metadata["evidence_scope"] = assessment["evidence_scope"]
    metadata["engineering_only"] = str(assessment["engineering_only"])
    metadata["eligible_for_paper_claims"] = str(assessment["eligible_for_paper_claims"])
    metadata_path = assets_dir / "asset_metadata.json"
    write_json(metadata_path, metadata)
    paths.append(metadata_path)

    manifest = {
        "run_dir": str(data.run_dir),
        "assessment": assessment,
        "provenance": metadata,
        "assets": manifest_entries,
        "scope": (
            "engineering_only_scaffold"
            if assessment["engineering_only"]
            else "candidate_paper_assets_not_final_evidence_until_validated"
        ),
    }
    manifest_path = assets_dir / "paper_assets_manifest.json"
    write_json(manifest_path, manifest)
    paths.append(manifest_path)

    stats_path = assets_dir / "statistical_summary.json"
    write_json(stats_path, statistical_report(data))
    paths.append(stats_path)

    if write_global:
        root = Path.cwd()
        paths.extend(
            _export_tables(data, root / "tables", assessment, manifest_entries=None, watermark=watermark)
        )
        paths.extend(build_all_figures(data, root / "figures"))

    return paths


def _export_tables(
    data: RunResults,
    output_dir: Path,
    assessment: dict[str, Any],
    manifest_entries: list[dict[str, Any]] | None,
    *,
    watermark: str | None = None,
) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    metadata = asset_metadata(data)
    paths: list[Path] = []
    for spec in CANONICAL_TABLES:
        frame = with_asset_metadata(spec.builder(data), data)
        stem = out / spec.asset_id
        paths.extend(write_table_bundle(frame, stem))
        _watermark_table_bundle(stem, watermark)
        sidecar = _table_sidecar(spec, frame, metadata, assessment, watermark=watermark)
        sidecar_path = out / f"{spec.asset_id}.meta.json"
        write_json(sidecar_path, sidecar)
        paths.append(sidecar_path)
        if manifest_entries is not None:
            manifest_entries.append(sidecar)
    return paths


def _export_figures(
    data: RunResults,
    output_dir: Path,
    assessment: dict[str, Any],
    manifest_entries: list[dict[str, Any]] | None,
    *,
    watermark: str | None = None,
) -> list[Path]:
    paths = build_all_figures(data, output_dir)
    metadata = asset_metadata(data)
    for spec in CANONICAL_FIGURES:
        asset_id = spec["asset_id"]
        sidecar = _figure_sidecar(spec, metadata, assessment, output_dir, watermark=watermark)
        if asset_id == "figure7_human_judge_agreement":
            if not (Path(output_dir) / f"{asset_id}.png").exists():
                continue
        if asset_id == "figure1_benchmark_schematic":
            sidecar_path = Path(output_dir) / f"{asset_id}.meta.json"
        else:
            sidecar_path = Path(output_dir) / f"{asset_id}.meta.json"
        write_json(sidecar_path, sidecar)
        paths.append(sidecar_path)
        if manifest_entries is not None:
            manifest_entries.append(sidecar)
    return paths


def _table_sidecar(
    spec: TableAssetSpec,
    frame: pd.DataFrame,
    metadata: dict[str, str],
    assessment: dict[str, Any],
    *,
    watermark: str | None = None,
) -> dict[str, Any]:
    placeholder = "status" in frame.columns and bool((frame["status"] == "not yet run").any())
    return {
        "asset_id": spec.asset_id,
        "asset_type": "table",
        "title": spec.title,
        "caption": _caption_with_provenance(spec.caption, metadata, assessment, watermark=watermark),
        "formats": ["csv", "md", "tex"],
        "placeholder": placeholder,
        "provenance": metadata,
        "eligibility": assessment,
    }


def _figure_sidecar(
    spec: dict[str, str],
    metadata: dict[str, str],
    assessment: dict[str, Any],
    output_dir: Path,
    *,
    watermark: str | None = None,
) -> dict[str, Any]:
    asset_id = spec["asset_id"]
    formats = ["md"] if asset_id == "figure1_benchmark_schematic" else ["png", "pdf"]
    missing = [fmt for fmt in formats if not (Path(output_dir) / f"{asset_id}.{fmt}").exists()]
    return {
        "asset_id": asset_id,
        "asset_type": "figure",
        "title": spec["title"],
        "caption": _caption_with_provenance(
            spec["caption"], metadata, assessment, watermark=watermark
        ),
        "formats": formats,
        "missing_formats": missing,
        "placeholder": bool(missing) and asset_id != "figure7_human_judge_agreement",
        "provenance": metadata,
        "eligibility": assessment,
    }


def _caption_with_provenance(
    caption: str,
    metadata: dict[str, str],
    assessment: dict[str, Any],
    *,
    watermark: str | None = None,
) -> str:
    scope_note = (
        "Engineering-only export; not for final paper claims."
        if assessment.get("engineering_only")
        else "Candidate export; validate before paper claims."
    )
    if watermark:
        scope_note = f"{watermark}. {scope_note}"
    return (
        f"{caption} "
        f"[run={metadata.get('run_dir')}, config={metadata.get('config_hash')}, "
        f"dataset={metadata.get('dataset_version')}, models={metadata.get('model_ids')}, "
        f"seed={metadata.get('seed')}, git={metadata.get('git_commit')}. {scope_note}]"
    )


def _watermark_table_bundle(stem: Path, watermark: str | None) -> None:
    if not watermark:
        return
    for suffix in (".md", ".tex", ".csv"):
        path = stem.with_suffix(suffix)
        if path.exists() and suffix in {".md", ".tex"}:
            path.write_text(
                apply_export_watermark(path.read_text(encoding="utf-8"), watermark),
                encoding="utf-8",
            )
        elif path.exists() and suffix == ".csv":
            text = path.read_text(encoding="utf-8")
            if watermark not in text:
                path.write_text(f"# {watermark}\n{text}", encoding="utf-8")
