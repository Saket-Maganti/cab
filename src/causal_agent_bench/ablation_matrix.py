from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

matplotlib.use("Agg")

from causal_agent_bench.analysis.load_results import load_run_results
from causal_agent_bench.analysis.tables import dataframe_to_markdown, write_table_bundle
from causal_agent_bench.runners.config import ExperimentConfig, load_experiment_config
from causal_agent_bench.runners.costing import estimate_experiment_cost
from causal_agent_bench.runners.experiment import run_experiment
from causal_agent_bench.utils.io import git_commit, write_json

DEFAULT_FACTOR_ORDER = (
    "prompt_style",
    "self_check",
    "memory_verification",
    "recovery_instruction",
    "contradiction_instruction",
    "uncertainty_instruction",
)


class MatrixSafeguards(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_cells: int = Field(default=32, ge=1)
    max_estimated_cost_usd: float | None = Field(default=0.0, ge=0)
    max_instances_per_cell: int | None = Field(default=None, ge=1)
    require_dry_run_before_execute: bool = False
    block_paid_providers_without_flag: bool = True


class BaseModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: str = "direct_llm_tool_agent"
    provider: str = "local_stub"
    model: str = "local-stub"
    temperature: float = 0.0
    max_tokens: int = Field(default=512, ge=1)
    retry_count: int = Field(default=0, ge=0)
    timeout: float = Field(default=30.0, gt=0)
    budget_cap_usd: float | None = Field(default=0.0, ge=0)
    task_budget_cap_usd: float | None = Field(default=None, ge=0)
    allow_paid_calls: bool = False


class AblationMatrixConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matrix_version: str = "1.0"
    seed: int = 0
    run_name: str = Field(min_length=1)
    benchmark_path: str
    output_dir: str = "results/ablation_matrix"
    max_steps: int = Field(default=8, ge=1)
    num_repeats: int = Field(default=1, ge=1)
    auto_score: bool = True
    allow_paid_calls: bool = False
    base_model: BaseModelConfig = Field(default_factory=BaseModelConfig)
    factors: dict[str, list[str]]
    strategy: str = "baseline_plus_one"
    cells: list[dict[str, str]] = Field(default_factory=list)
    safeguards: MatrixSafeguards = Field(default_factory=MatrixSafeguards)

    @model_validator(mode="after")
    def validate_factors(self) -> AblationMatrixConfig:
        for name in self.factors:
            if name not in DEFAULT_FACTOR_ORDER:
                allowed = ", ".join(DEFAULT_FACTOR_ORDER)
                raise ValueError(f"unknown factor {name!r}; expected one of: {allowed}")
            if len(self.factors[name]) < 1:
                raise ValueError(f"factor {name!r} must have at least one level")
        if self.strategy == "explicit" and not self.cells:
            raise ValueError("strategy 'explicit' requires a non-empty cells list")
        return self


@dataclass(frozen=True)
class FactorLevelSpec:
    agent: str | None = None
    prompt_addendum_file: str | None = None
    ablation_level: str | None = None


FACTOR_LEVELS: dict[str, dict[str, FactorLevelSpec]] = {
    "prompt_style": {
        "direct": FactorLevelSpec(ablation_level="direct"),
        "react": FactorLevelSpec(
            prompt_addendum_file="ablations/react_style_instruction.md",
            ablation_level="react_style",
        ),
    },
    "self_check": {
        "off": FactorLevelSpec(agent="direct_llm_tool_agent", ablation_level="without_self_check"),
        "on": FactorLevelSpec(
            agent="self_checking_llm_agent",
            prompt_addendum_file="ablations/self_check_instruction.md",
            ablation_level="with_self_check",
        ),
    },
    "memory_verification": {
        "off": FactorLevelSpec(ablation_level="without_memory_verification"),
        "on": FactorLevelSpec(
            prompt_addendum_file="ablations/memory_verification_instruction.md",
            ablation_level="with_memory_verification",
        ),
    },
    "recovery_instruction": {
        "off": FactorLevelSpec(ablation_level="without_recovery_instruction"),
        "on": FactorLevelSpec(
            prompt_addendum_file="ablations/tool_failure_recovery_instruction.md",
            ablation_level="with_recovery_instruction",
        ),
    },
    "contradiction_instruction": {
        "off": FactorLevelSpec(ablation_level="without_contradiction_resolution"),
        "on": FactorLevelSpec(
            prompt_addendum_file="ablations/contradiction_resolution_instruction.md",
            ablation_level="with_contradiction_resolution",
        ),
    },
    "uncertainty_instruction": {
        "off": FactorLevelSpec(ablation_level="without_uncertainty_abstention"),
        "on": FactorLevelSpec(
            prompt_addendum_file="ablations/uncertainty_abstention_instruction.md",
            ablation_level="with_uncertainty_abstention",
        ),
    },
}


def load_ablation_matrix_config(path: str | Path) -> AblationMatrixConfig:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return AblationMatrixConfig.model_validate(payload)


def expand_matrix_cells(config: AblationMatrixConfig) -> list[dict[str, str]]:
    factor_order = [name for name in DEFAULT_FACTOR_ORDER if name in config.factors]
    if config.strategy == "explicit":
        return [dict(cell) for cell in config.cells]
    if config.strategy == "baseline_plus_one":
        baseline = {name: config.factors[name][0] for name in factor_order}
        cells = [dict(baseline)]
        for name in factor_order:
            levels = config.factors[name]
            if len(levels) < 2:
                continue
            variant = dict(baseline)
            variant[name] = levels[1]
            cells.append(variant)
        return cells
    if config.strategy == "full_factorial":
        level_lists = [config.factors[name] for name in factor_order]
        return [
            dict(zip(factor_order, combo, strict=True))
            for combo in itertools.product(*level_lists)
        ]
    raise ValueError(f"unknown matrix strategy {config.strategy!r}")


def cell_id_from_factors(factors: dict[str, str]) -> str:
    return "__".join(f"{key}_{factors[key]}" for key in sorted(factors))


def build_cell_experiment_config(
    matrix: AblationMatrixConfig,
    factors: dict[str, str],
) -> tuple[dict[str, Any], str]:
    base = matrix.base_model
    agent = base.agent
    prompt_addendum_files: list[str] = []
    ablation_factors: dict[str, str] = {}
    for factor_name, level in factors.items():
        levels = FACTOR_LEVELS.get(factor_name)
        if levels is None or level not in levels:
            allowed = ", ".join(sorted(FACTOR_LEVELS.get(factor_name, {})))
            raise ValueError(f"unknown level {level!r} for factor {factor_name!r}; allowed: {allowed}")
        spec = levels[level]
        if spec.agent:
            agent = spec.agent
        if spec.prompt_addendum_file:
            prompt_addendum_files.append(spec.prompt_addendum_file)
        ablation_factors[factor_name] = level

    cell_id = cell_id_from_factors(factors)
    extra: dict[str, Any] = {
        "prompt_file": "ablations/base_tool_agent.md",
        "system_safety_file": "system_safety_ablation_minimal.md",
        "ablation": {
            "matrix_version": matrix.matrix_version,
            "matrix_run_name": matrix.run_name,
            "cell_id": cell_id,
            "factors": ablation_factors,
            "comparison_role": "matrix_cell",
        },
    }
    if len(prompt_addendum_files) == 1:
        extra["prompt_addendum_file"] = prompt_addendum_files[0]
    elif len(prompt_addendum_files) > 1:
        extra["prompt_addendum_files"] = prompt_addendum_files

    raw = {
        "seed": matrix.seed,
        "run_name": f"{matrix.run_name}__{cell_id}",
        "benchmark_path": matrix.benchmark_path,
        "max_steps": matrix.max_steps,
        "num_repeats": matrix.num_repeats,
        "output_dir": str(Path(matrix.output_dir) / matrix.run_name / "cells" / cell_id / "run"),
        "auto_score": matrix.auto_score,
        "allow_paid_calls": base.allow_paid_calls,
        "agent_runs": [
            {
                "name": cell_id,
                "agent": agent,
                "provider": base.provider,
                "model": base.model,
                "temperature": base.temperature,
                "max_tokens": base.max_tokens,
                "retry_count": base.retry_count,
                "timeout": base.timeout,
                "budget_cap_usd": base.budget_cap_usd,
                "task_budget_cap_usd": base.task_budget_cap_usd,
                "extra": extra,
            }
        ],
    }
    return raw, cell_id


def plan_ablation_matrix(
    matrix_path: str | Path,
    *,
    matrix_output_dir: str | Path | None = None,
) -> dict[str, Any]:
    matrix = load_ablation_matrix_config(matrix_path)
    cells = expand_matrix_cells(matrix)
    if len(cells) > matrix.safeguards.max_cells:
        raise ValueError(
            f"matrix expands to {len(cells)} cells but max_cells={matrix.safeguards.max_cells}"
        )

    root = Path(matrix_output_dir) if matrix_output_dir else Path(matrix.output_dir) / matrix.run_name
    root.mkdir(parents=True, exist_ok=True)
    cell_records: list[dict[str, Any]] = []
    total_cost = 0.0
    cost_known = True
    for factors in cells:
        raw, cell_id = build_cell_experiment_config(matrix, factors)
        cell_dir = root / "cells" / cell_id
        cell_dir.mkdir(parents=True, exist_ok=True)
        config_path = cell_dir / "config.yaml"
        config_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
        experiment = ExperimentConfig.model_validate(raw)
        estimate = estimate_experiment_cost(experiment)
        cell_cost = estimate.get("known_cost_upper_bound_usd")
        if cell_cost is None:
            cost_known = False
        else:
            total_cost += float(cell_cost)
        cell_records.append(
            {
                "cell_id": cell_id,
                "factors": factors,
                "config_path": str(config_path),
                "planned_run_dir": str(cell_dir / "run"),
                "cost_estimate": estimate,
            }
        )

    if cost_known and matrix.safeguards.max_estimated_cost_usd is not None:
        if total_cost > matrix.safeguards.max_estimated_cost_usd:
            raise ValueError(
                f"estimated matrix cost {total_cost:.4f} exceeds max_estimated_cost_usd="
                f"{matrix.safeguards.max_estimated_cost_usd}"
            )

    if matrix.safeguards.block_paid_providers_without_flag:
        provider = matrix.base_model.provider
        if provider not in {"local_stub", "local_openai"} and not matrix.base_model.allow_paid_calls:
            raise ValueError(
                f"provider {provider!r} requires allow_paid_calls=true on base_model"
            )

    manifest = {
        "matrix_version": matrix.matrix_version,
        "matrix_config_path": str(Path(matrix_path).resolve()),
        "run_name": matrix.run_name,
        "strategy": matrix.strategy,
        "n_cells": len(cell_records),
        "cells": cell_records,
        "total_estimated_cost_usd": round(total_cost, 6) if cost_known else None,
        "git_commit": git_commit(Path.cwd()),
        "scope": "Ablation matrix plan; not scientific evidence until validated provider runs.",
    }
    write_json(root / "matrix_manifest.json", manifest)
    (root / "matrix_plan.md").write_text(_matrix_plan_markdown(manifest), encoding="utf-8")
    return manifest


def run_ablation_matrix(
    matrix_path: str | Path,
    *,
    execute: bool = False,
    matrix_output_dir: str | Path | None = None,
    skip_existing: bool = True,
    replan: bool = False,
) -> dict[str, Any]:
    matrix = load_ablation_matrix_config(matrix_path)
    root = Path(matrix_output_dir) if matrix_output_dir else Path(matrix.output_dir) / matrix.run_name
    manifest_path = root / "matrix_manifest.json"
    if execute and matrix.safeguards.require_dry_run_before_execute and not replan:
        if not manifest_path.exists():
            raise ValueError(
                "execute blocked: require_dry_run_before_execute is true; "
                "run without --execute first to write matrix_manifest.json"
            )
        manifest = _read_manifest(root)
    else:
        manifest = plan_ablation_matrix(matrix_path, matrix_output_dir=matrix_output_dir)
    if not execute:
        return manifest
    run_results: list[dict[str, Any]] = []
    for cell in manifest["cells"]:
        config_path = Path(cell["config_path"])
        planned_run = Path(cell["planned_run_dir"])
        existing = _find_scored_run_dir(planned_run)
        if skip_existing and existing is not None:
            run_results.append(
                {"cell_id": cell["cell_id"], "run_dir": str(existing), "status": "skipped"}
            )
            cell["actual_run_dir"] = str(existing)
            continue
        result = run_experiment_from_config_path(config_path)
        run_dir = result["run_dir"]
        cell["actual_run_dir"] = str(run_dir)
        run_results.append(
            {
                "cell_id": cell["cell_id"],
                "run_dir": str(run_dir),
                "status": "completed",
                "n_trajectories": len(result.get("trajectories", [])),
            }
        )
    manifest["run_results"] = run_results
    write_json(root / "matrix_manifest.json", manifest)
    aggregate = aggregate_ablation_matrix(root)
    export_paths = export_ablation_matrix_artifacts(root, aggregate)
    manifest["aggregate_paths"] = [str(path) for path in export_paths]
    write_json(root / "matrix_manifest.json", manifest)
    return manifest


def run_experiment_from_config_path(config_path: Path) -> dict[str, Any]:
    config, raw = _load_raw_config(config_path)
    return run_experiment(config, raw_config=raw)


def _load_raw_config(config_path: Path) -> tuple[ExperimentConfig, dict[str, Any]]:
    return load_experiment_config(config_path)


def aggregate_ablation_matrix(matrix_root: str | Path) -> pd.DataFrame:
    root = Path(matrix_root)
    manifest = _read_manifest(root)
    rows: list[dict[str, Any]] = []
    for cell in manifest.get("cells", []):
        run_dir = _resolve_cell_run_dir(root, cell)
        if run_dir is None:
            continue
        data = load_run_results(run_dir)
        agent_names = sorted(data.aggregate.get("by_agent", {}))
        if not agent_names:
            continue
        agent = agent_names[0]
        aggregate_row = data.aggregate["by_agent"][agent]
        trajectories = data.trajectories_df
        rows.append(
            {
                "cell_id": cell["cell_id"],
                **cell.get("factors", {}),
                "agent": agent,
                "clean_success": aggregate_row.get("clean_success_rate"),
                "intervention_success": aggregate_row.get("intervention_success_rate"),
                "acrs": aggregate_row.get("acrs"),
                "estimated_cost_usd": _round_metric(
                    trajectories.get("estimated_cost_usd", pd.Series(dtype=float)).dropna().sum()
                    if not trajectories.empty
                    else aggregate_row.get("avg_cost_per_task_usd")
                ),
                "avg_latency_s": _round_metric(
                    trajectories.get("latency_s", pd.Series(dtype=float)).dropna().mean()
                    if not trajectories.empty
                    else aggregate_row.get("avg_latency_per_task_s")
                ),
                "unnecessary_tool_call_rate": aggregate_row.get("unnecessary_tool_call_rate"),
                "tool_overuse": aggregate_row.get("unnecessary_tool_call_rate"),
                "run_dir": str(run_dir),
                "config_hash": data.run_metadata.get("config_hash"),
                "evidence_scope": data.run_metadata.get("evidence_scope"),
            }
        )
    if not rows:
        return pd.DataFrame(
            [
                {
                    "status": "not yet run",
                    "note": "No completed matrix cells with aggregate scores were found.",
                }
            ]
        )
    return pd.DataFrame(rows)


def export_ablation_matrix_artifacts(matrix_root: str | Path, frame: pd.DataFrame | None = None) -> list[Path]:
    root = Path(matrix_root)
    frame = frame if frame is not None else aggregate_ablation_matrix(root)
    out = root / "exports"
    out.mkdir(parents=True, exist_ok=True)
    paths = write_table_bundle(frame, out / "ablation_matrix_table")
    meta = {
        "matrix_root": str(root),
        "git_commit": git_commit(Path.cwd()),
        "n_rows": len(frame),
        "columns": list(frame.columns),
    }
    meta_path = out / "ablation_matrix_table.meta.json"
    write_json(meta_path, meta)
    paths.append(meta_path)
    heatmap_paths = _export_acrs_heatmap(frame, out / "ablation_matrix_acrs_heatmap")
    paths.extend(heatmap_paths)
    summary_path = out / "ablation_matrix_aggregate.json"
    write_json(summary_path, frame.to_dict(orient="records"))
    paths.append(summary_path)
    (out / "ablation_matrix_aggregate.md").write_text(
        dataframe_to_markdown(frame),
        encoding="utf-8",
    )
    paths.append(out / "ablation_matrix_aggregate.md")
    return paths


def _export_acrs_heatmap(frame: pd.DataFrame, stem: Path) -> list[Path]:
    if frame.empty or "acrs" not in frame.columns or frame["acrs"].isna().all():
        return []
    plot_frame = frame.copy()
    plot_frame["label"] = plot_frame.apply(_cell_label, axis=1)
    values = plot_frame["acrs"].fillna(0).to_numpy(dtype=float).reshape(-1, 1)
    fig, ax = plt.subplots(figsize=(4, max(4, len(plot_frame) * 0.35)))
    image = ax.imshow(values, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks([0])
    ax.set_xticklabels(["ACRS"])
    ax.set_yticks(range(len(plot_frame)))
    ax.set_yticklabels(plot_frame["label"])
    ax.set_title("Ablation matrix ACRS")
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    png = stem.with_suffix(".png")
    pdf = stem.with_suffix(".pdf")
    fig.savefig(png, dpi=180)
    fig.savefig(pdf)
    plt.close(fig)
    return [png, pdf]


def _cell_label(row: pd.Series) -> str:
    if "cell_id" in row and pd.notna(row["cell_id"]):
        return str(row["cell_id"])
    parts = [f"{key}={row[key]}" for key in DEFAULT_FACTOR_ORDER if key in row and pd.notna(row[key])]
    return ", ".join(parts) if parts else "cell"


def _matrix_plan_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Ablation Matrix Plan",
        "",
        f"- Matrix version: `{manifest.get('matrix_version')}`",
        f"- Strategy: `{manifest.get('strategy')}`",
        f"- Cells: `{manifest.get('n_cells')}`",
        f"- Estimated total cost (USD): `{manifest.get('total_estimated_cost_usd')}`",
        "",
        "| Cell | Factors | Config |",
        "|---|---|---|",
    ]
    for cell in manifest.get("cells", []):
        factors = ", ".join(f"{key}={value}" for key, value in sorted(cell.get("factors", {}).items()))
        lines.append(f"| `{cell['cell_id']}` | {factors} | `{cell['config_path']}` |")
    lines.append("")
    return "\n".join(lines)


def _read_manifest(root: Path) -> dict[str, Any]:
    from causal_agent_bench.utils.io import read_json

    return read_json(root / "matrix_manifest.json")


def _resolve_cell_run_dir(root: Path, cell: dict[str, Any]) -> Path | None:
    actual = cell.get("actual_run_dir")
    if actual:
        path = Path(actual)
        if path.exists() and (path / "aggregate_scores.json").exists():
            return path
    planned = Path(cell.get("planned_run_dir", ""))
    resolved = _find_scored_run_dir(planned)
    if resolved is not None:
        return resolved
    candidate = root / "cells" / cell["cell_id"] / "run"
    return _find_scored_run_dir(candidate)


def _find_scored_run_dir(base: Path) -> Path | None:
    if not base.exists():
        return None
    if (base / "aggregate_scores.json").exists():
        return base
    for child in sorted(base.iterdir(), reverse=True):
        if child.is_dir() and (child / "aggregate_scores.json").exists():
            return child
    return None


def _round_metric(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)
