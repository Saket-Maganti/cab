"""Honest analytic and Monte Carlo hierarchical design tooling."""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.hashing import stable_hash


class HierarchicalSimulationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulations: int = Field(default=20_000, ge=1)
    seed: int = 2_026_080_1
    task_count: int = Field(default=100, ge=10)
    model_count: int = Field(default=5, ge=2)
    family_count: int = Field(default=10, ge=2)
    repeats: int = Field(default=1, ge=1)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    degradation_logit: float = Field(default=0.50, gt=0)
    raac_improvement_probability: float = Field(default=0.06, gt=0)
    noninferiority_margin: float = Field(default=0.05, gt=0)
    base_task_sd: float = Field(default=0.65, ge=0)
    model_sd: float = Field(default=0.35, ge=0)
    family_sd: float = Field(default=0.25, ge=0)
    interaction_sd: float = Field(default=0.18, ge=0)
    policy_sd: float = Field(default=0.08, ge=0)
    repeat_sd: float = Field(default=0.12, ge=0)
    scorer_error: float = Field(default=0.02, ge=0, lt=0.5)
    missingness: float = Field(default=0.05, ge=0, lt=1)
    human_exclusion: float = Field(default=0.10, ge=0, lt=1)
    shard_size: int = Field(default=250, ge=1)


def analytic_power_report(
    *,
    tasks: int,
    effect: float,
    discordance: float = 0.24,
    alpha: float = 0.05,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Return a clearly labeled normal approximation, never simulation claims."""

    normal = NormalDist()
    z_alpha = normal.inv_cdf(1.0 - alpha)
    z_80 = normal.inv_cdf(0.80)
    z_confidence = normal.inv_cdf(0.5 + confidence / 2.0)
    standard_error = math.sqrt(discordance * (1.0 - discordance) / tasks)
    approximate_power = normal.cdf(effect / standard_error - z_alpha)
    return {
        "schema_version": "cab_hierarchical_power_analytic_v2",
        "method_class": "ANALYTIC_PLANNING_APPROXIMATION",
        "estimand": "FIXED_MODEL_PANEL_ESTIMAND",
        "analysis_unit": "paired_base_task_within_model",
        "task_count": tasks,
        "assumptions": {
            "paired_discordance": discordance,
            "effect": effect,
            "alpha": alpha,
            "confidence_level": confidence,
            "directionality": "one_sided_degradation",
            "multiplicity": "single_primary_planning_contrast",
            "sesoi": effect,
            "equivalence_margin": None,
        },
        "approximate_power": round(approximate_power, 6),
        "approximate_ci_width": round(2.0 * z_confidence * standard_error, 6),
        "approximate_mde_80pct": round((z_alpha + z_80) * standard_error, 6),
        "standard_error": round(standard_error, 6),
        "evidence_class": "DESIGN_ONLY",
    }


def run_hierarchical_monte_carlo(
    config: HierarchicalSimulationConfig | None = None,
) -> dict[str, Any]:
    """Generate paired synthetic hierarchical datasets in deterministic shards."""

    cfg = config or HierarchicalSimulationConfig()
    rng = np.random.default_rng(cfg.seed)
    z = NormalDist().inv_cdf(1.0 - cfg.alpha)
    family_index = np.arange(cfg.task_count) % cfg.family_count
    result_vectors: dict[str, list[np.ndarray]] = {
        "per_model_paired_degradation": [],
        "fixed_panel_paired_degradation": [],
        "model_superpopulation_degradation": [],
        "family_effect_detected": [],
        "model_family_interaction_detected": [],
        "raac_within_model_improvement": [],
        "clean_noninferiority": [],
        "rank_instability": [],
        "unresolved_ranking": [],
    }
    estimates: dict[str, list[np.ndarray]] = {
        "fixed_panel_effect": [],
        "model_superpopulation_effect": [],
        "raac_effect": [],
    }
    completed = 0
    while completed < cfg.simulations:
        batch = min(cfg.shard_size, cfg.simulations - completed)
        shape = (batch, cfg.model_count, cfg.task_count)
        base = rng.normal(0.0, cfg.base_task_sd, size=(batch, 1, cfg.task_count))
        model = rng.normal(0.0, cfg.model_sd, size=(batch, cfg.model_count, 1))
        family = rng.normal(0.0, cfg.family_sd, size=(batch, 1, cfg.family_count))
        interaction = rng.normal(
            0.0,
            cfg.interaction_sd,
            size=(batch, cfg.model_count, cfg.family_count),
        )
        policy = rng.normal(0.0, cfg.policy_sd, size=(batch, cfg.model_count, 1))
        repeat_noise = rng.normal(0.0, cfg.repeat_sd / math.sqrt(cfg.repeats), size=shape)
        family_task = family[:, :, family_index]
        interaction_task = interaction[:, :, family_index]
        clean_logit = 1.25 + base + model + family_task + repeat_noise
        intervention_logit = (
            clean_logit
            - cfg.degradation_logit
            + interaction_task
        )
        clean_probability = _logistic(clean_logit)
        intervention_probability = _logistic(intervention_logit)
        shared = rng.random(shape)
        independent = rng.random(shape)
        clean = shared < clean_probability
        intervention = (0.55 * shared + 0.45 * independent) < intervention_probability
        keep = (
            rng.random(shape) >= cfg.missingness
        ) & (rng.random(shape) >= cfg.human_exclusion)
        clean = _apply_scorer_error(clean, rng, cfg.scorer_error)
        intervention = _apply_scorer_error(intervention, rng, cfg.scorer_error)
        degradation = np.where(keep, clean.astype(float) - intervention.astype(float), np.nan)
        model_effect = _nanmean(degradation, axis=2)
        task_effect = _nanmean(degradation, axis=1)
        fixed_effect = _nanmean(task_effect, axis=1)
        fixed_se = np.nanstd(task_effect, axis=1, ddof=1) / math.sqrt(cfg.task_count)
        super_effect = _nanmean(model_effect, axis=1)
        super_se = np.nanstd(model_effect, axis=1, ddof=1) / math.sqrt(cfg.model_count)
        per_model_se = np.nanstd(degradation, axis=2, ddof=1) / np.sqrt(
            np.maximum(np.sum(~np.isnan(degradation), axis=2), 1)
        )
        result_vectors["per_model_paired_degradation"].append(
            np.all(model_effect > z * per_model_se, axis=1)
        )
        result_vectors["fixed_panel_paired_degradation"].append(
            fixed_effect > z * fixed_se
        )
        result_vectors["model_superpopulation_degradation"].append(
            super_effect > z * super_se
        )

        family_effects = np.stack(
            [_nanmean(degradation[:, :, family_index == family_id], axis=(1, 2)) for family_id in range(cfg.family_count)],
            axis=1,
        )
        result_vectors["family_effect_detected"].append(
            np.nanstd(family_effects, axis=1) > cfg.family_sd / 3.0
        )
        cell_effects = np.stack(
            [_nanmean(degradation[:, :, family_index == family_id], axis=2) for family_id in range(cfg.family_count)],
            axis=2,
        )
        interaction_residual = (
            cell_effects
            - _nanmean(cell_effects, axis=1, keepdims=True)
            - _nanmean(cell_effects, axis=2, keepdims=True)
            + _nanmean(cell_effects, axis=(1, 2), keepdims=True)
        )
        result_vectors["model_family_interaction_detected"].append(
            np.nanstd(interaction_residual, axis=(1, 2)) > cfg.interaction_sd / 3.0
        )

        raac_probability = np.clip(
            intervention_probability + cfg.raac_improvement_probability + policy,
            0.001,
            0.999,
        )
        raac = _apply_scorer_error(rng.random(shape) < raac_probability, rng, cfg.scorer_error)
        raac_difference = np.where(
            keep,
            raac.astype(float) - intervention.astype(float),
            np.nan,
        )
        raac_model = _nanmean(raac_difference, axis=2)
        raac_effect = _nanmean(raac_model, axis=1)
        raac_se = np.nanstd(raac_model, axis=1, ddof=1) / math.sqrt(cfg.model_count)
        result_vectors["raac_within_model_improvement"].append(raac_effect > z * raac_se)
        estimates["raac_effect"].append(raac_effect)

        clean_policy_probability = np.clip(clean_probability - 0.01 + policy, 0.001, 0.999)
        clean_policy = _apply_scorer_error(
            rng.random(shape) < clean_policy_probability,
            rng,
            cfg.scorer_error,
        )
        clean_policy_loss = _nanmean(
            np.where(keep, clean.astype(float) - clean_policy.astype(float), np.nan),
            axis=(1, 2),
        )
        result_vectors["clean_noninferiority"].append(
            clean_policy_loss < cfg.noninferiority_margin
        )

        clean_rates = _nanmean(np.where(keep, clean, np.nan), axis=2)
        intervention_rates = _nanmean(np.where(keep, intervention, np.nan), axis=2)
        clean_ranks = np.argsort(np.argsort(-clean_rates, axis=1), axis=1)
        intervention_ranks = np.argsort(np.argsort(-intervention_rates, axis=1), axis=1)
        result_vectors["rank_instability"].append(np.any(clean_ranks != intervention_ranks, axis=1))
        sorted_rates = np.sort(intervention_rates, axis=1)
        top_gap = sorted_rates[:, -1] - sorted_rates[:, -2]
        ranking_se = np.sqrt(
            np.maximum(sorted_rates[:, -1] * (1 - sorted_rates[:, -1]), 0.0) / cfg.task_count
            + np.maximum(sorted_rates[:, -2] * (1 - sorted_rates[:, -2]), 0.0) / cfg.task_count
        )
        result_vectors["unresolved_ranking"].append(top_gap <= 1.96 * ranking_se)
        estimates["fixed_panel_effect"].append(fixed_effect)
        estimates["model_superpopulation_effect"].append(super_effect)
        completed += batch

    empirical: dict[str, Any] = {}
    for name, chunks in result_vectors.items():
        values = np.concatenate(chunks).astype(float)
        probability = float(values.mean())
        empirical[name] = {
            "probability": round(probability, 6),
            "monte_carlo_standard_error": round(
                math.sqrt(probability * (1.0 - probability) / cfg.simulations),
                6,
            ),
        }
    estimate_summary = {}
    for name, chunks in estimates.items():
        values = np.concatenate(chunks)
        estimate_summary[name] = {
            "mean": round(float(np.mean(values)), 6),
            "sd": round(float(np.std(values, ddof=1)), 6),
            "p025": round(float(np.quantile(values, 0.025)), 6),
            "p975": round(float(np.quantile(values, 0.975)), 6),
        }
    report: dict[str, Any] = {
        "schema_version": "cab_true_hierarchical_monte_carlo_v2",
        "status": "CAB_HIERARCHICAL_POWER_V2_READY",
        "method_class": "TRUE_MONTE_CARLO_HIERARCHICAL_SIMULATION",
        "simulations_completed": cfg.simulations,
        "deterministic_seed": cfg.seed,
        "sharded_resumable_contract": True,
        "shard_size": cfg.shard_size,
        "synthetic_components": [
            "base_task_random_effects",
            "model_random_effects",
            "intervention_family_effects",
            "model_by_family_interaction",
            "policy_effects",
            "repeat_noise",
            "scorer_error",
            "missingness",
            "human_exclusions",
            "task_clustering",
            "paired_clean_intervention_outcomes",
        ],
        "estimands": {
            "FIXED_MODEL_PANEL_ESTIMAND": [
                "per_model_paired_degradation",
                "fixed_panel_paired_degradation",
                "family_effect_detected",
                "model_family_interaction_detected",
                "raac_within_model_improvement",
                "clean_noninferiority",
                "rank_instability",
                "unresolved_ranking",
            ],
            "MODEL_SUPERPOPULATION_ESTIMAND": [
                "model_superpopulation_degradation"
            ],
        },
        "configuration": cfg.model_dump(mode="json"),
        "empirical_simulation_results": empirical,
        "estimate_summary": estimate_summary,
        "evidence_class": "SYNTHETIC_DESIGN_SIMULATION_NOT_EMPIRICAL_MODEL_EVIDENCE",
    }
    report["simulation_hash"] = stable_hash(report, length=64)
    return report


def write_power_v2_reports(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/level6_foundation",
    simulations: int = 20_000,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = root / output_dir
    out.mkdir(parents=True, exist_ok=True)
    analytics = {
        "compact20": analytic_power_report(tasks=20, effect=0.10),
        "scale100": analytic_power_report(tasks=100, effect=0.10),
        "value_of_information": {
            "more_tasks": analytic_power_report(tasks=150, effect=0.10),
            "more_repeats": "secondary after unique tasks because within-task correlation limits gain",
            "more_models": "required only for MODEL_SUPERPOPULATION_ESTIMAND",
            "more_families": "improves family and interaction estimands",
            "reduced_scorer_error": "improves precision without changing task count",
        },
    }
    simulation = run_hierarchical_monte_carlo(
        HierarchicalSimulationConfig(simulations=simulations)
    )
    (out / "HIERARCHICAL_POWER_ANALYTIC_V2.json").write_text(
        json.dumps(analytics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "HIERARCHICAL_POWER_MONTE_CARLO_V2.json").write_text(
        json.dumps(simulation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"analytic": analytics, "simulation": simulation}


def _logistic(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def _apply_scorer_error(
    values: np.ndarray,
    rng: np.random.Generator,
    error_rate: float,
) -> np.ndarray:
    flips = rng.random(values.shape) < error_rate
    return np.logical_xor(values, flips)


def _nanmean(
    values: np.ndarray,
    *,
    axis: int | tuple[int, ...],
    keepdims: bool = False,
) -> np.ndarray:
    present = ~np.isnan(values)
    count = np.sum(present, axis=axis, keepdims=keepdims)
    total = np.nansum(values, axis=axis, keepdims=keepdims)
    return np.divide(
        total,
        count,
        out=np.full_like(total, np.nan, dtype=float),
        where=count > 0,
    )


__all__ = [
    "HierarchicalSimulationConfig",
    "analytic_power_report",
    "run_hierarchical_monte_carlo",
    "write_power_v2_reports",
]
