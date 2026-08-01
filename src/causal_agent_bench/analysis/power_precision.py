"""Deterministic prospective power and precision calculations for CAB."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import NormalDist
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.hashing import stable_hash

NORMAL = NormalDist()
Z_95 = NORMAL.inv_cdf(0.975)
Z_ONE_SIDED_95 = NORMAL.inv_cdf(0.95)
Z_POWER_80 = NORMAL.inv_cdf(0.80)


class PowerAssumptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_task_count: int = Field(ge=2)
    interventions_per_task: float = Field(gt=0)
    models: int = Field(ge=1)
    policies: int = Field(ge=1)
    repeats: int = Field(ge=1)
    clean_success: float = Field(ge=0, le=1)
    intervention_success: float = Field(ge=0, le=1)
    paired_discordance: float = Field(gt=0, le=1)
    intraclass_correlation: float = Field(ge=0, lt=1)
    family_heterogeneity: float = Field(ge=0)
    scorer_error: float = Field(ge=0, lt=0.5)
    human_exclusion_rate: float = Field(ge=0, lt=1)
    missing_run_rate: float = Field(ge=0, lt=1)
    sesoi: float = Field(gt=0, lt=1)
    equivalence_margin: float = Field(gt=0, lt=1)
    raac_improvement: float = Field(gt=0, lt=1)
    family_count: int = Field(ge=1)
    seed: int


class PowerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cab_power_assumptions_v1"]
    bootstrap_repetitions: int = Field(ge=100)
    scenarios: dict[str, PowerAssumptions]


def simulate_power_precision(
    assumptions: PowerAssumptions,
    *,
    bootstrap_repetitions: int,
) -> dict[str, Any]:
    """Return stable analytic precision plus seeded rank simulations."""

    effective_tasks = _effective_task_count(assumptions)
    se = _paired_standard_error(assumptions, effective_tasks)
    expected_degradation = assumptions.clean_success - assumptions.intervention_success
    ci_width = 2 * Z_95 * se
    mdd = (Z_ONE_SIDED_95 + Z_POWER_80) * se
    sesoi_power = _one_sided_power(assumptions.sesoi, se)
    observed_effect_power = _one_sided_power(expected_degradation, se)
    raac_se = se * math.sqrt(2)
    raac_power = _one_sided_power(assumptions.raac_improvement, raac_se)
    family_se = math.sqrt(
        (se**2) * assumptions.family_count
        + assumptions.family_heterogeneity**2
    )
    rank = _rank_simulation(assumptions, se, draws=10_000)
    alternatives = [
        _design_value(assumptions, task_multiplier=1.25, repeat_increment=0),
        _design_value(assumptions, task_multiplier=1.0, repeat_increment=1),
        _design_value(assumptions, task_multiplier=2.0, repeat_increment=0),
    ]
    sensitivity = [
        _sensitivity_row(assumptions, exclusion, scorer_error)
        for exclusion in (0.0, assumptions.human_exclusion_rate, 0.20)
        for scorer_error in (0.0, assumptions.scorer_error, 0.08)
    ]
    payload: dict[str, Any] = {
        "schema_version": "cab_prospective_power_precision_v1",
        "assumptions": assumptions.model_dump(mode="json"),
        "effective_task_count": round(effective_tasks, 6),
        "expected_degradation": round(expected_degradation, 6),
        "expected_confidence_interval_width": round(ci_width, 6),
        "minimum_detectable_degradation_80pct_power": round(mdd, 6),
        "power_for_preregistered_sesoi": round(sesoi_power, 6),
        "power_for_expected_degradation": round(observed_effect_power, 6),
        "raac_improvement_power": round(raac_power, 6),
        "noninferiority_precision_half_width": round(Z_95 * se, 6),
        "equivalence_margin": assumptions.equivalence_margin,
        "equivalence_margin_resolved_at_expected_precision": (
            Z_95 * se <= assumptions.equivalence_margin
        ),
        "family_effect_precision_half_width": round(Z_95 * family_se, 6),
        "rank_change_probability": rank["rank_change_probability"],
        "unresolved_ranking_probability": rank[
            "unresolved_ranking_probability"
        ],
        "value_of_more_tasks_vs_repeats": alternatives,
        "exclusion_and_scorer_error_sensitivity": sensitivity,
        "bootstrap_design": {
            "repetitions": bootstrap_repetitions,
            "cluster_unit": "base_task",
            "paired_resampling": True,
            "stratify_by": ["model", "policy", "intervention_family"],
            "workload_replicate_cells": (
                bootstrap_repetitions
                * assumptions.models
                * assumptions.policies
                * assumptions.family_count
            ),
        },
        "underpowered_for_sesoi": sesoi_power < 0.80,
        "scientific_execution_performed": False,
        "evidence_class": "DESIGN_ONLY",
    }
    payload["recommendation"] = (
        "Increase unique base tasks before increasing repeats."
        if payload["underpowered_for_sesoi"]
        else "Planned unique-task count meets the prospective 80% SESOI-power target."
    )
    payload["simulation_receipt"] = stable_hash(payload, length=64)
    return payload


def build_power_reports(
    repo_root: str | Path,
    *,
    config_path: str | Path = "configs/pre_run/power_assumptions.json",
    output_dir: str | Path = "reports/pre_run_hardening",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    config_file = _resolve(root, config_path)
    config = PowerConfig.model_validate_json(config_file.read_text(encoding="utf-8"))
    out = _resolve(root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    reports: dict[str, dict[str, Any]] = {}
    paths: dict[str, dict[str, str]] = {}
    for name, assumptions in sorted(config.scenarios.items()):
        report = simulate_power_precision(
            assumptions,
            bootstrap_repetitions=config.bootstrap_repetitions,
        )
        stem = name.upper()
        json_path = out / f"{stem}_POWER_PRECISION.json"
        md_path = out / f"{stem}_POWER_PRECISION.md"
        json_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        md_path.write_text(_markdown(name, report), encoding="utf-8")
        reports[name] = report
        paths[name] = {"json": str(json_path), "markdown": str(md_path)}
    recommendation = {
        "schema_version": "cab_power_recommendation_receipt_v1",
        "compact20_sesoi_power": reports["compact20"][
            "power_for_preregistered_sesoi"
        ],
        "scale100_sesoi_power": reports["scale100"][
            "power_for_preregistered_sesoi"
        ],
        "decision": (
            "Use Compact-20 for validation/piloting only; use Scale-100 for "
            "confirmatory completion endpoints after human approval."
        ),
        "assumptions_frozen_before_live_runs": True,
        "scientific_execution_performed": False,
    }
    recommendation["receipt"] = stable_hash(recommendation, length=64)
    receipt_path = out / "POWER_PRECISION_RECOMMENDATION.json"
    receipt_path.write_text(
        json.dumps(recommendation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "reports": reports,
        "paths": paths,
        "recommendation": recommendation,
        "recommendation_path": str(receipt_path),
    }


def _effective_task_count(a: PowerAssumptions) -> float:
    retained = a.base_task_count * (1 - a.human_exclusion_rate) * (1 - a.missing_run_rate)
    repeated_measurement_gain = a.repeats / (1 + (a.repeats - 1) * a.intraclass_correlation)
    intervention_design_effect = 1 + (a.interventions_per_task - 1) * a.intraclass_correlation
    return retained * repeated_measurement_gain / intervention_design_effect


def _paired_standard_error(a: PowerAssumptions, effective_tasks: float) -> float:
    scorer_variance = a.scorer_error * (1 - a.scorer_error)
    numerator = a.paired_discordance * (1 - a.paired_discordance) + scorer_variance
    return math.sqrt(numerator / max(effective_tasks * a.models * a.policies, 1.0))


def _one_sided_power(effect: float, standard_error: float) -> float:
    return NORMAL.cdf(effect / standard_error - Z_ONE_SIDED_95)


def _rank_simulation(
    a: PowerAssumptions,
    standard_error: float,
    *,
    draws: int,
) -> dict[str, float]:
    rng = random.Random(a.seed)
    baseline = [0.60 + index * 0.06 for index in range(a.models)]
    original = sorted(range(a.models), key=lambda index: baseline[index], reverse=True)
    changes = 0
    unresolved = 0
    for _ in range(draws):
        observed = [
            score + rng.gauss(0.0, standard_error) for score in baseline
        ]
        ranking = sorted(range(a.models), key=lambda index: observed[index], reverse=True)
        changes += ranking != original
        ordered = sorted(observed, reverse=True)
        unresolved += any(
            ordered[index] - ordered[index + 1] <= 2 * Z_95 * standard_error
            for index in range(len(ordered) - 1)
        )
    return {
        "rank_change_probability": round(changes / draws, 6),
        "unresolved_ranking_probability": round(unresolved / draws, 6),
    }


def _design_value(
    a: PowerAssumptions,
    *,
    task_multiplier: float,
    repeat_increment: int,
) -> dict[str, Any]:
    alternative = a.model_copy(
        update={
            "base_task_count": math.ceil(a.base_task_count * task_multiplier),
            "repeats": a.repeats + repeat_increment,
        }
    )
    effective = _effective_task_count(alternative)
    se = _paired_standard_error(alternative, effective)
    return {
        "base_task_count": alternative.base_task_count,
        "repeats": alternative.repeats,
        "minimum_detectable_degradation": round(
            (Z_ONE_SIDED_95 + Z_POWER_80) * se,
            6,
        ),
        "sesoi_power": round(_one_sided_power(a.sesoi, se), 6),
    }


def _sensitivity_row(
    a: PowerAssumptions,
    exclusion: float,
    scorer_error: float,
) -> dict[str, Any]:
    alternative = a.model_copy(
        update={
            "human_exclusion_rate": exclusion,
            "scorer_error": scorer_error,
        }
    )
    effective = _effective_task_count(alternative)
    se = _paired_standard_error(alternative, effective)
    return {
        "human_exclusion_rate": exclusion,
        "scorer_error": scorer_error,
        "expected_ci_width": round(2 * Z_95 * se, 6),
        "sesoi_power": round(_one_sided_power(a.sesoi, se), 6),
    }


def _markdown(name: str, report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {name.replace('_', ' ').title()} Prospective Power and Precision",
            "",
            "Status: `DESIGN_ONLY`; assumptions were frozen before any live scientific run.",
            "",
            f"- Expected 95% CI width: `{report['expected_confidence_interval_width']}`",
            f"- 80% minimum detectable degradation: `{report['minimum_detectable_degradation_80pct_power']}`",
            f"- Power at preregistered SESOI: `{report['power_for_preregistered_sesoi']}`",
            f"- RAAC improvement power: `{report['raac_improvement_power']}`",
            f"- Family-effect half-width: `{report['family_effect_precision_half_width']}`",
            f"- Rank-change probability: `{report['rank_change_probability']}`",
            f"- Unresolved-ranking probability: `{report['unresolved_ranking_probability']}`",
            "",
            f"Recommendation: {report['recommendation']}",
            "",
            "No empirical outcome, model run, human judgment, or paper-eligible evidence is represented here.",
            "",
        ]
    )


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


__all__ = [
    "PowerAssumptions",
    "PowerConfig",
    "build_power_reports",
    "simulate_power_precision",
]
