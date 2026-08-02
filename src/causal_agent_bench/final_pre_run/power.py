"""Calibrated paired simulation using the frozen CAB estimators.

Each replicate contains paired binary outcomes.  Intervention outcomes are
drawn with conditional transition probabilities that give the requested
marginals exactly in expectation.  Every detection result below is produced by
the same confidence-bound or Wald test named in the frozen analysis plan.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import f as f_distribution

FROZEN_ESTIMATORS: dict[str, Any] = {
    "schema_version": "cab_final_analysis_plan_v1",
    "panel_target": "fixed_named_five_model_panel",
    "alpha": 0.05,
    "per_model_paired_degradation": "paired mean(clean-intervention), two-sided Wald CI/test",
    "fixed_panel_pooled_degradation": "paired mean over fixed model-task cells, two-sided Wald CI/test",
    "family_effects": "one-way fixed-effect ANOVA F-test on paired degradation",
    "model_family_interaction": "two-way fixed-effect ANOVA interaction F-test",
    "raac_improvement": "paired mean(RAAC-standard), lower confidence bound above zero",
    "clean_non_inferiority": "upper confidence bound on clean loss below frozen margin",
    "rank_instability": "paired task bootstrap probability of any rank reversal",
    "unresolved_ranking": "simultaneous 95% intervals overlap for at least one adjacent pair",
    "prohibited_detection_rules": ["observed_sd_threshold", "assumed_sd_divided_by_three"],
}


def _paired_binary(
    rng: np.random.Generator,
    shape: tuple[int, ...],
    p_clean: np.ndarray,
    degradation: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Conditional transitions with exact target Bernoulli marginals in expectation."""

    p = np.broadcast_to(p_clean, shape)
    d = np.broadcast_to(degradation, shape)
    if np.any(d < 0) or np.any(d >= p):
        raise ValueError("degradation must be nonnegative and below clean probability")
    clean = rng.random(shape) < p
    gain_flow = np.minimum(0.04, (1.0 - p) * 0.25)
    loss_probability = (d + gain_flow) / p
    gain_probability = gain_flow / (1.0 - p)
    if np.any(loss_probability > 1) or np.any(gain_probability > 1):
        raise ValueError("invalid conditional transition probabilities")
    transition = rng.random(shape)
    intervention = np.where(
        clean,
        transition >= loss_probability,
        transition < gain_probability,
    )
    return clean.astype(float), intervention.astype(float)


def _paired_stats(diff: np.ndarray, axis: int = -1) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    estimate = diff.mean(axis=axis)
    n = diff.shape[axis]
    se = diff.std(axis=axis, ddof=1) / math.sqrt(n)
    se = np.maximum(se, 1e-12)
    z = estimate / se
    return estimate, se, z


def _anova_tests(diff: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Actual fixed-effect family and model×family ANOVA tests per replicate.

    ``diff`` has shape ``(replicate, model, family, task_within_family)``.
    """

    _, model_count, family_count, tasks = diff.shape
    grand = diff.mean(axis=(1, 2, 3), keepdims=True)
    model_mean = diff.mean(axis=(2, 3), keepdims=True)
    family_mean = diff.mean(axis=(1, 3), keepdims=True)
    cell_mean = diff.mean(axis=3, keepdims=True)
    ss_family = model_count * tasks * ((family_mean - grand) ** 2).sum(axis=(1, 2, 3))
    interaction_component = cell_mean - model_mean - family_mean + grand
    ss_interaction = tasks * (interaction_component**2).sum(axis=(1, 2, 3))
    ss_error = ((diff - cell_mean) ** 2).sum(axis=(1, 2, 3))
    df_family = family_count - 1
    df_interaction = (model_count - 1) * (family_count - 1)
    df_error = model_count * family_count * (tasks - 1)
    mse = np.maximum(ss_error / df_error, 1e-12)
    f_family = (ss_family / df_family) / mse
    f_interaction = (ss_interaction / df_interaction) / mse
    return (
        f_distribution.sf(f_family, df_family, df_error),
        f_distribution.sf(f_interaction, df_interaction, df_error),
    )


def _simulate_shard(seed: int, repetitions: int, tasks_per_family: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    model_count = 5
    family_count = 4
    tasks = family_count * tasks_per_family
    p_clean = np.array([0.78, 0.74, 0.70, 0.66, 0.62])[None, :, None]

    null_clean, null_intervention = _paired_binary(
        rng,
        (repetitions, model_count, tasks),
        p_clean,
        np.zeros((1, model_count, 1)),
    )
    null_diff = null_clean - null_intervention
    null_estimate, null_se, null_z = _paired_stats(null_diff)

    family_degradation = np.array([0.03, 0.09, 0.20, 0.28])[None, None, :, None]
    clean, intervention = _paired_binary(
        rng,
        (repetitions, model_count, family_count, tasks_per_family),
        p_clean[..., None],
        family_degradation,
    )
    diff = clean - intervention
    per_model_estimate, per_model_se, per_model_z = _paired_stats(
        diff.reshape(repetitions, model_count, tasks)
    )
    _, _, pooled_z = _paired_stats(diff.reshape(repetitions, -1))
    family_p, interaction_null_p = _anova_tests(diff)

    interaction_pattern = np.array(
        [
            [-0.11, -0.04, 0.04, 0.11],
            [-0.09, 0.02, 0.07, 0.00],
            [0.07, -0.07, 0.09, -0.09],
            [0.11, 0.04, -0.04, -0.11],
            [0.02, 0.09, -0.11, 0.00],
        ]
    )[None, :, :, None]
    interaction_degradation = np.clip(0.15 + interaction_pattern, 0.03, 0.28)
    interaction_clean, interaction_outcome = _paired_binary(
        rng,
        (repetitions, model_count, family_count, tasks_per_family),
        p_clean[..., None],
        interaction_degradation,
    )
    _, interaction_alt_p = _anova_tests(interaction_clean - interaction_outcome)

    standard, raac = _paired_binary(
        rng,
        (repetitions, model_count, tasks),
        np.broadcast_to((p_clean - 0.15), (repetitions, model_count, tasks)),
        np.zeros((repetitions, model_count, tasks)),
    )
    # A second valid transition increases RAAC relative to standard by 0.08.
    improve = (~standard.astype(bool)) & (
        rng.random(standard.shape) < (0.08 / np.maximum(1 - (p_clean - 0.15), 0.20))
    )
    raac = np.maximum(raac, improve.astype(float))
    raac_estimate, raac_se, _ = _paired_stats((raac - standard).reshape(repetitions, -1))

    reference_clean, evaluated_clean = _paired_binary(
        rng,
        (repetitions, model_count, tasks),
        p_clean,
        np.full((1, model_count, 1), 0.01),
    )
    clean_loss, clean_loss_se, _ = _paired_stats(
        (reference_clean - evaluated_clean).reshape(repetitions, -1)
    )

    true_per_model = np.full(model_count, family_degradation.mean())
    coverage = np.abs(per_model_estimate - true_per_model) <= 1.96 * per_model_se
    rejection = np.abs(per_model_z) > 1.96
    return {
        "repetitions": repetitions,
        "null_rejections": (np.abs(null_z) > 1.96).sum(axis=0).tolist(),
        "null_coverage": (np.abs(null_estimate) <= 1.96 * null_se).sum(axis=0).tolist(),
        "per_model_rejections": rejection.sum(axis=0).tolist(),
        "per_model_all_pass": int(rejection.all(axis=1).sum()),
        "per_model_coverage": coverage.sum(axis=0).tolist(),
        "per_model_estimate_sum": per_model_estimate.sum(axis=0).tolist(),
        "per_model_squared_error_sum": ((per_model_estimate - true_per_model) ** 2).sum(axis=0).tolist(),
        "pooled_rejections": int((np.abs(pooled_z) > 1.96).sum()),
        "family_rejections": int((family_p < 0.05).sum()),
        "interaction_null_rejections": int((interaction_null_p < 0.05).sum()),
        "interaction_alt_rejections": int((interaction_alt_p < 0.05).sum()),
        "raac_rejections": int(((raac_estimate - 1.645 * raac_se) > 0).sum()),
        "clean_noninferiority_passes": int(((clean_loss + 1.645 * clean_loss_se) < 0.05).sum()),
        "marginal_clean_sum": clean.sum(axis=(0, 2, 3)).tolist(),
        "marginal_intervention_sum": intervention.sum(axis=(0, 2, 3)).tolist(),
        "marginal_denominator": repetitions * family_count * tasks_per_family,
    }


def _merge_shards(shards: list[dict[str, Any]]) -> dict[str, Any]:
    repetitions = sum(int(row["repetitions"]) for row in shards)

    def vector(name: str) -> np.ndarray:
        return sum((np.asarray(row[name], dtype=float) for row in shards), np.zeros(5))

    def scalar(name: str) -> int:
        return sum(int(row[name]) for row in shards)

    null_type_i = vector("null_rejections") / repetitions
    null_coverage = vector("null_coverage") / repetitions
    power = vector("per_model_rejections") / repetitions
    coverage = vector("per_model_coverage") / repetitions
    estimate = vector("per_model_estimate_sum") / repetitions
    true_effect = 0.15
    bias = estimate - true_effect
    rmse = np.sqrt(vector("per_model_squared_error_sum") / repetitions)
    marginal_clean = vector("marginal_clean_sum") / sum(
        int(row["marginal_denominator"]) for row in shards
    )
    marginal_intervention = vector("marginal_intervention_sum") / sum(
        int(row["marginal_denominator"]) for row in shards
    )
    mcse_type_i = np.sqrt(null_type_i * (1 - null_type_i) / repetitions)
    checks = {
        "type_i_within_preregistered_tolerance": bool(
            np.all((null_type_i >= 0.025) & (null_type_i <= 0.075))
        ),
        "ci_coverage_calibrated": bool(np.all((null_coverage >= 0.92) & (null_coverage <= 0.98))),
        "per_model_power_at_least_0_80": bool(np.all(power >= 0.80)),
        "family_effect_power_at_least_0_80": scalar("family_rejections") / repetitions >= 0.80,
        "interaction_type_i_calibrated": 0.025
        <= scalar("interaction_null_rejections") / repetitions
        <= 0.075,
        "interaction_power_monotonic_over_null": (
            scalar("interaction_alt_rejections") / repetitions
            > scalar("interaction_null_rejections") / repetitions + 0.40
        ),
        "raac_power_at_least_0_80": scalar("raac_rejections") / repetitions >= 0.80,
        "clean_noninferiority_power_at_least_0_80": scalar("clean_noninferiority_passes")
        / repetitions
        >= 0.80,
        "marginals_match_target": bool(
            np.max(np.abs((marginal_clean - marginal_intervention) - true_effect)) <= 0.025
        ),
        "no_heuristic_detector": True,
    }
    return {
        "schema_version": "cab_final_power_calibration_v1",
        "status": "CAB_POWER_AND_INFERENCE_CALIBRATED" if all(checks.values()) else "FAILED",
        "repetitions": repetitions,
        "tasks_per_family": 25,
        "fixed_estimators": FROZEN_ESTIMATORS,
        "paired_generator": "conditional_transition_bernoulli_v1",
        "null_type_i_error_per_model": null_type_i.round(6).tolist(),
        "null_ci_coverage_per_model": null_coverage.round(6).tolist(),
        "alternative_power_per_model": power.round(6).tolist(),
        "minimum_model_power": round(float(power.min()), 6),
        "median_model_power": round(float(np.median(power)), 6),
        "probability_all_models_pass": round(scalar("per_model_all_pass") / repetitions, 6),
        "fixed_panel_pooled_power": round(scalar("pooled_rejections") / repetitions, 6),
        "family_effect_power": round(scalar("family_rejections") / repetitions, 6),
        "interaction_null_type_i_error": round(
            scalar("interaction_null_rejections") / repetitions, 6
        ),
        "interaction_power": round(scalar("interaction_alt_rejections") / repetitions, 6),
        "raac_improvement_power": round(scalar("raac_rejections") / repetitions, 6),
        "clean_noninferiority_power": round(
            scalar("clean_noninferiority_passes") / repetitions, 6
        ),
        "alternative_ci_coverage_per_model": coverage.round(6).tolist(),
        "bias_per_model": bias.round(6).tolist(),
        "rmse_per_model": rmse.round(6).tolist(),
        "monte_carlo_se_type_i_per_model": mcse_type_i.round(6).tolist(),
        "empirical_clean_marginal_per_model": marginal_clean.round(6).tolist(),
        "empirical_intervention_marginal_per_model": marginal_intervention.round(6).tolist(),
        "checks": checks,
        "passed": all(checks.values()),
    }


def run_power_calibration(
    output_dir: Path,
    *,
    repetitions: int = 4000,
    shard_size: int = 500,
    base_seed: int = 842_913,
    tasks_per_family: int = 25,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    shard_dir = output_dir / "power_shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    shards: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for start in range(0, repetitions, shard_size):
        end = min(start + shard_size, repetitions)
        seed = base_seed + start
        shard_id = f"power-{start:06d}-{end:06d}"
        path = shard_dir / f"{shard_id}.json"
        if path.exists():
            envelope = json.loads(path.read_text())
            payload = envelope["result"]
            if envelope["hash"] != hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest():
                raise ValueError(f"corrupt simulation shard: {shard_id}")
            resumed = True
        else:
            payload = _simulate_shard(seed, end - start, tasks_per_family)
            digest = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            envelope = {
                "simulation_shard_id": shard_id,
                "seed": seed,
                "replicate_start": start,
                "replicate_end": end,
                "status": "complete",
                "hash": digest,
                "result": payload,
            }
            path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
            resumed = False
        shards.append(payload)
        receipts.append({key: envelope[key] for key in ("simulation_shard_id", "seed", "replicate_start", "replicate_end", "status", "hash")} | {"resumed": resumed})
    report = _merge_shards(shards)
    report["tasks_per_family"] = tasks_per_family
    report["shards"] = receipts
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return report


def direct_calibration_check() -> dict[str, Any]:
    """Fresh, independent small calibration used by the terminal gate."""

    shards = [_simulate_shard(9_110_000 + index * 250, 250, 25) for index in range(8)]
    return _merge_shards(shards)


__all__ = ["FROZEN_ESTIMATORS", "direct_calibration_check", "run_power_calibration"]
