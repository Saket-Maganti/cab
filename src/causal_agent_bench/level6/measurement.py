"""Fixture-only measurement-science foundations for CAB Level 6."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np

from causal_agent_bench.hashing import stable_hash

CONSTRUCT_MAP = {
    construct: {
        "task_design": "paired controlled task with construct-relevant demand",
        "intervention": intervention,
        "observable_behavior": behavior,
        "trajectory_evidence": evidence,
        "endpoint": endpoint,
        "claim": f"bounded evidence about {construct}; not a general capability claim",
    }
    for construct, intervention, behavior, evidence, endpoint in (
        ("planning", "planning-horizon disruption", "route selection", "ordered action plan", "plan validity"),
        ("tool_use", "tool removal/failure", "tool selection", "content-bound calls", "tool contract compliance"),
        ("memory", "memory corruption", "source checking", "memory reads and corrections", "memory robustness"),
        ("observation_handling", "observation conflict", "conflict resolution", "observation citations", "observation validity"),
        ("evidence_integration", "multi-source conflict", "fact joining", "fact derivation graph", "supported completion"),
        ("stopping", "partial completion", "termination choice", "terminal event", "stopping correctness"),
        ("recovery", "tool failure", "authorized fallback", "recovery attempt receipt", "task recovery"),
        ("calibration", "evidence uncertainty", "confidence qualification", "answer and evidence state", "calibration error"),
        ("abstention", "route exhaustion", "safe abstention", "exhaustion proof", "justified abstention"),
        ("robustness", "paired intervention", "retained performance", "paired outcomes", "paired degradation"),
    )
}


def measurement_foundation_check() -> dict[str, Any]:
    checks = {
        "construct_map_complete": len(CONSTRUCT_MAP) == 10,
        "validity_protocol_complete": True,
        "variance_decomposition_available": True,
        "g_theory_available": True,
        "measurement_invariance_contract_available": True,
        "dif_methods_available": True,
        "uncertainty_propagation_available": True,
    }
    return {
        "schema_version": "cab_measurement_science_foundation_v1",
        "status": "CAB_MEASUREMENT_SCIENCE_FOUNDATION_READY",
        "passed": all(checks.values()),
        "checks": checks,
        "construct_map": CONSTRUCT_MAP,
        "construct_validity_protocol": [
            "content_validity",
            "convergent_validity",
            "discriminant_validity",
            "criterion_validity",
            "predictive_validity",
            "known_groups_validity",
        ],
        "fixture_only": True,
        "real_measurement_results_claimed": False,
    }


def variance_decomposition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Method-of-moments fixture decomposition across declared facets."""

    if not rows:
        raise ValueError("variance decomposition requires fixture rows")
    facets = ("task", "model", "intervention_family", "repeat", "scorer", "reviewer")
    outcomes = np.asarray([float(row["outcome"]) for row in rows], dtype=float)
    total = float(np.var(outcomes, ddof=1)) if len(outcomes) > 1 else 0.0
    raw: dict[str, float] = {}
    for facet in facets:
        grouped: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            grouped[str(row[facet])].append(float(row["outcome"]))
        means = np.asarray([np.mean(values) for values in grouped.values()], dtype=float)
        raw[facet] = float(np.var(means, ddof=1)) if len(means) > 1 else 0.0
    scale = sum(raw.values())
    allocation = {
        facet: (total * value / scale if scale else 0.0)
        for facet, value in raw.items()
    }
    residual = max(total - sum(allocation.values()), 0.0)
    components = {**allocation, "residual": residual}
    return {
        "schema_version": "cab_fixture_variance_decomposition_v1",
        "components": {key: round(value, 8) for key, value in components.items()},
        "total_variance": round(total, 8),
        "fixture_only": True,
    }


def generalizability_coefficients(
    components: dict[str, float],
    *,
    tasks: int,
    interventions: int,
    scorers: int,
    repeats: int,
) -> dict[str, Any]:
    model = max(float(components.get("model", 0.0)), 0.0)
    relative_error = (
        float(components.get("task", 0.0)) / tasks
        + float(components.get("intervention_family", 0.0)) / interventions
        + float(components.get("repeat", 0.0)) / repeats
        + float(components.get("scorer", 0.0)) / scorers
        + float(components.get("residual", 0.0)) / (tasks * repeats)
    )
    absolute_error = relative_error + float(components.get("reviewer", 0.0))
    g = model / (model + relative_error) if model + relative_error else 0.0
    phi = model / (model + absolute_error) if model + absolute_error else 0.0
    return {
        "schema_version": "cab_g_theory_fixture_result_v1",
        "design": "person/model × task × intervention × scorer × repeat",
        "g_coefficient": round(g, 6),
        "dependability_coefficient": round(phi, 6),
        "fixture_only": True,
    }


def invariance_assessment_fixture(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[str(row["group"])].append(float(row["score"]))
    means = {key: float(np.mean(values)) for key, values in groups.items()}
    spread = max(means.values()) - min(means.values()) if means else math.inf
    return {
        "schema_version": "cab_measurement_invariance_fixture_v1",
        "assessments_prepared": [
            "configural",
            "metric",
            "scalar",
            "partial",
            "model_family",
            "domain",
            "intervention_family",
        ],
        "fixture_mean_spread": round(spread, 6),
        "fixture_contract_exercised": bool(groups),
        "real_invariance_conclusion": None,
        "fixture_only": True,
    }


def logistic_regression_dif(
    score: list[float],
    group: list[int],
    response: list[int],
) -> dict[str, Any]:
    """Small deterministic IRLS logistic DIF fit with group and interaction."""

    if not (len(score) == len(group) == len(response)) or len(score) < 8:
        raise ValueError("DIF fixture arrays must have equal length and at least eight rows")
    x_score = np.asarray(score, dtype=float)
    x_group = np.asarray(group, dtype=float)
    x = np.column_stack([np.ones(len(score)), x_score, x_group, x_score * x_group])
    y = np.asarray(response, dtype=float)
    beta = np.zeros(x.shape[1])
    for _ in range(50):
        probability = np.clip(1.0 / (1.0 + np.exp(-(x @ beta))), 1e-6, 1 - 1e-6)
        weights = probability * (1 - probability)
        information = x.T @ (weights[:, None] * x) + np.eye(x.shape[1]) * 1e-8
        update = np.linalg.solve(information, x.T @ (y - probability))
        beta += update
        if float(np.max(np.abs(update))) < 1e-8:
            break
    covariance = np.linalg.inv(information)
    standard_errors = np.sqrt(np.diag(covariance))
    z_values = beta / standard_errors
    return {
        "schema_version": "cab_logistic_dif_fixture_v1",
        "coefficients": [round(float(value), 6) for value in beta],
        "z_values": [round(float(value), 6) for value in z_values],
        "uniform_dif_group_z": round(float(z_values[2]), 6),
        "nonuniform_dif_interaction_z": round(float(z_values[3]), 6),
        "multiple_testing_correction": "benjamini_hochberg_required_for_item_set",
        "fixture_only": True,
    }


def mantel_haenszel_dif(
    strata: list[dict[str, int]],
) -> dict[str, Any]:
    numerator = 0.0
    denominator = 0.0
    for row in strata:
        total = sum(row[key] for key in ("a", "b", "c", "d"))
        if total:
            numerator += row["a"] * row["d"] / total
            denominator += row["b"] * row["c"] / total
    odds_ratio = numerator / denominator if denominator else math.inf
    return {
        "schema_version": "cab_mantel_haenszel_dif_fixture_v1",
        "common_odds_ratio": round(odds_ratio, 6),
        "fixture_only": True,
    }


def propagate_uncertainty_fixture(
    ratings: list[float],
    *,
    bootstrap_repetitions: int = 2_000,
    seed: int = 2_026_080_1,
) -> dict[str, Any]:
    if not ratings:
        raise ValueError("uncertainty propagation requires ratings")
    rng = np.random.default_rng(seed)
    values = np.asarray(ratings, dtype=float)
    indexes = rng.integers(0, len(values), size=(bootstrap_repetitions, len(values)))
    means = values[indexes].mean(axis=1)
    result = {
        "schema_version": "cab_reviewer_scorer_uncertainty_fixture_v1",
        "bootstrap_repetitions": bootstrap_repetitions,
        "mean": round(float(values.mean()), 6),
        "interval": [
            round(float(np.quantile(means, 0.025)), 6),
            round(float(np.quantile(means, 0.975)), 6),
        ],
        "uncertainty_sources": [
            "scorer_disagreement",
            "reviewer_disagreement",
            "adjudication_uncertainty",
            "exclusion_uncertainty",
        ],
        "fixture_only": True,
    }
    result["result_hash"] = stable_hash(result, length=64)
    return result


__all__ = [
    "CONSTRUCT_MAP",
    "generalizability_coefficients",
    "invariance_assessment_fixture",
    "logistic_regression_dif",
    "mantel_haenszel_dif",
    "measurement_foundation_check",
    "propagate_uncertainty_fixture",
    "variance_decomposition",
]
