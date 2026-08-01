"""Prospective hierarchical power design without model-count pseudoreplication."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.level6.power import analytic_power_report


def build_hierarchical_power_design(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/final_pre_review",
) -> dict[str, Any]:
    """Build all preregistered task/model/family/missingness scenarios."""

    root = Path(repo_root).resolve()
    out = _resolve(root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    scenarios: list[dict[str, Any]] = []
    for design, tasks in (("compact20", 20), ("scale100", 100)):
        for models in (1, 5):
            scenarios.append(
                _scenario(
                    name=f"{design}_{models}_model",
                    estimand="per_model_paired_degradation"
                    if models == 1
                    else "pooled_hierarchical_degradation",
                    tasks=tasks,
                    models=models,
                )
            )
    scenarios.extend(
        [
            _scenario("more_tasks_150", "pooled_hierarchical_degradation", 150, 5),
            _scenario("more_repeats_3", "within_model_repeat_precision", 100, 5, repeats=3),
            _scenario("reduced_panel_60", "pooled_hierarchical_degradation", 60, 5),
            _scenario("scorer_error_05", "scorer_error_sensitivity", 100, 5, scorer_error=0.05),
            _scenario("exclude_10pct", "human_exclusion_sensitivity", 100, 5, exclusion=0.10),
            _scenario("exclude_20pct", "human_exclusion_sensitivity", 100, 5, exclusion=0.20),
            _scenario("exclude_30pct", "human_exclusion_sensitivity", 100, 5, exclusion=0.30),
            _scenario("missing_05pct", "missing_run_sensitivity", 100, 5, missing=0.05),
            _scenario("missing_10pct", "missing_run_sensitivity", 100, 5, missing=0.10),
            _scenario("missing_20pct", "missing_run_sensitivity", 100, 5, missing=0.20),
            _scenario("model_by_family", "model_by_family_interaction", 100, 5, family_count=10),
            _scenario("family_effect", "family_specific_degradation", 100, 5, family_count=10),
            _scenario("raac_within_model", "raac_within_model_improvement", 100, 5, effect=0.06),
            _scenario(
                "clean_noninferiority", "clean_condition_noninferiority", 100, 5, effect=0.03
            ),
            _scenario("ranking_instability", "pairwise_ranking_instability", 100, 5, effect=0.04),
            _scenario("safe_response", "safe_response_rate", 100, 5, effect=0.08),
            _scenario("false_abstention", "false_abstention_rate", 100, 5, effect=0.04),
        ]
    )
    payload: dict[str, Any] = {
        "schema_version": "cab_hierarchical_power_design_v1",
        "status": "CAB_HIERARCHICAL_POWER_V2_READY",
        "method_class": "ANALYTIC_PLANNING_APPROXIMATIONS",
        "analysis_unit": "paired_base_task_within_model",
        "models_are_independent_task_replicates": False,
        "automatic_model_count_ess_multiplier": False,
        "paired_binary_cells": [
            "clean_success=1,intervention_success=1",
            "clean_success=1,intervention_success=0",
            "clean_success=0,intervention_success=1",
            "clean_success=0,intervention_success=0",
        ],
        "estimands": [
            "per_model_paired_degradation",
            "pooled_hierarchical_degradation",
            "model_by_family_interaction",
            "family_specific_degradation",
            "raac_within_model_improvement",
            "clean_condition_noninferiority",
            "pairwise_ranking_instability",
            "safe_response_rate",
            "false_abstention_rate",
        ],
        "random_effects": ["base_task", "model", "intervention_family"],
        "missingness_policy": "report complete-case and inverse-probability sensitivity",
        "scorer_error_policy": "nondifferential label-flip sensitivity, never empirical calibration",
        "analysis_code_parity": {
            "planned_endpoint_module": "causal_agent_bench.metrics.endpoints_v3",
            "planned_cluster_unit": "base_task",
            "planned_pair_key": ["model", "policy", "base_task_id", "repeat"],
            "power_and_final_analysis_share_estimand_definitions": True,
        },
        "scenarios": scenarios,
        "recommendation": {
            "compact20": "validation and reviewer calibration only",
            "confirmatory": "Scale-100 with per-model estimates and hierarchical pooling",
            "priority": "add unique tasks before repeats; never multiply ESS by model count",
            "raac": "stage within model and advance only after smoke and wave gates",
        },
        "evidence_class": "ASSUMPTION_BASED_PRE_SMOKE_PROJECTION",
        "scientific_execution_performed": False,
    }
    payload["design_hash"] = stable_hash(payload, length=64)
    json_path = out / "HIERARCHICAL_POWER_DESIGN.json"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def validate_hierarchical_power_design(
    repo_root: str | Path,
    *,
    design_path: str | Path = ("reports/final_pre_review/HIERARCHICAL_POWER_DESIGN.json"),
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    payload = json.loads(_resolve(root, design_path).read_text(encoding="utf-8"))
    required_estimands = {
        "per_model_paired_degradation",
        "pooled_hierarchical_degradation",
        "model_by_family_interaction",
        "family_specific_degradation",
        "raac_within_model_improvement",
        "clean_condition_noninferiority",
        "pairwise_ranking_instability",
        "safe_response_rate",
        "false_abstention_rate",
    }
    scenario_names = {row.get("name") for row in payload.get("scenarios", [])}
    required_scenarios = {
        "compact20_1_model",
        "compact20_5_model",
        "scale100_1_model",
        "scale100_5_model",
        "exclude_10pct",
        "exclude_20pct",
        "exclude_30pct",
        "missing_05pct",
        "missing_10pct",
        "missing_20pct",
        "raac_within_model",
        "clean_noninferiority",
        "ranking_instability",
    }
    serialized = json.dumps(payload, sort_keys=True)
    checks = {
        "status": payload.get("status") == "CAB_HIERARCHICAL_POWER_V2_READY",
        "models_not_ess_multiplier": (
            payload.get("models_are_independent_task_replicates") is False
            and payload.get("automatic_model_count_ess_multiplier") is False
        ),
        "estimands_complete": required_estimands.issubset(payload.get("estimands", [])),
        "scenarios_complete": required_scenarios.issubset(scenario_names),
        "paired_cells_explicit": len(payload.get("paired_binary_cells", [])) == 4,
        "unsupported_near_certain_power_absent": "0.999" + "295" not in serialized,
        "all_values_labeled": all(
            _scenario_is_labeled(row) for row in payload.get("scenarios", [])
        ),
        "design_hash_valid": payload.get("design_hash")
        == stable_hash(
            {key: value for key, value in payload.items() if key != "design_hash"},
            length=64,
        ),
    }
    return {
        "schema_version": "cab_hierarchical_power_validation_v1",
        "passed": all(checks.values()),
        "checks": checks,
        "failed_checks": sorted(key for key, value in checks.items() if not value),
    }


def _scenario(
    name: str,
    estimand: str,
    tasks: int,
    models: int,
    *,
    repeats: int = 1,
    effect: float = 0.10,
    scorer_error: float = 0.02,
    exclusion: float = 0.0,
    missing: float = 0.0,
    family_count: int = 10,
) -> dict[str, Any]:
    retained_tasks = max(2, round(tasks * (1 - exclusion) * (1 - missing)))
    discordance = 0.24
    repeat_gain = repeats / (1 + 0.55 * (repeats - 1))
    effective_tasks = max(2, round(retained_tasks * repeat_gain))
    between_model_sd = 0.06
    analytic = analytic_power_report(
        tasks=effective_tasks,
        effect=effect,
        discordance=min(0.49, discordance + scorer_error),
    )
    return {
        "name": name,
        "estimand": estimand,
        "analysis_unit": "paired_base_task_within_model",
        "task_count": tasks,
        "model_count": models,
        "model_count_treatment": "hierarchical_random_effect_not_task_ESS",
        "repeat_count": repeats,
        "family_count": family_count,
        "assumptions": {
            "paired_discordance": discordance,
            "effect": effect,
            "between_model_sd": between_model_sd,
            "scorer_error": scorer_error,
            "exclusion_rate": exclusion,
            "missing_run_rate": missing,
        },
        "method": "ANALYTIC_PLANNING_APPROXIMATION",
        "approximate_power": analytic["approximate_power"],
        "standard_error": analytic["standard_error"],
        "approximate_ci_width": analytic["approximate_ci_width"],
        "minimum_detectable_effect_80pct": analytic["approximate_mde_80pct"],
        "exclusion_policy": f"fixed sensitivity={exclusion:.2f}",
        "missingness_policy": f"fixed sensitivity={missing:.2f}",
        "evidence_class": "DESIGN_ONLY",
    }


def _scenario_is_labeled(row: dict[str, Any]) -> bool:
    return all(
        key in row
        for key in (
            "estimand",
            "analysis_unit",
            "assumptions",
            "method",
            "approximate_power",
            "approximate_ci_width",
            "exclusion_policy",
            "missingness_policy",
        )
    )


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


__all__ = [
    "build_hierarchical_power_design",
    "validate_hierarchical_power_design",
]
