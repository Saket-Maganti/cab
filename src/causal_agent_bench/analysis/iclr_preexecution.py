"""Pre-execution statistical contracts for the CAB ICLR study.

The functions in this module are deliberately data-agnostic. They make the
planned analyses executable on fixtures while refusing to manufacture
scientific evidence or silently coerce incomplete inputs.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from scipy import stats

DEFAULT_PREDICTORS: tuple[str, ...] = (
    "clean_success",
    "acrs",
    "clean_conditioned_robustness",
    "recovery_score",
    "abstention_score",
    "worst_family_robustness",
)


def paired_equivalence_test(
    clean: Sequence[float],
    intervention: Sequence[float],
    *,
    equivalence_margin: float,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Two one-sided tests for a preregistered paired equivalence region."""

    if equivalence_margin <= 0:
        raise ValueError("equivalence_margin must be positive")
    if not 0 < alpha < 0.5:
        raise ValueError("alpha must be in (0, 0.5)")
    left = np.asarray(clean, dtype=float)
    right = np.asarray(intervention, dtype=float)
    if left.size != right.size:
        raise ValueError("clean and intervention must have equal length")
    if left.size < 2:
        return {
            "state": "blocked_insufficient_pairs",
            "n_pairs": int(left.size),
            "equivalent": None,
            "evidence_class": "ENGINEERING_ONLY",
        }
    differences = left - right
    if not np.all(np.isfinite(differences)):
        return {
            "state": "blocked_nonfinite_values",
            "n_pairs": int(left.size),
            "equivalent": None,
            "evidence_class": "ENGINEERING_ONLY",
        }
    mean_difference = float(differences.mean())
    standard_error = float(differences.std(ddof=1) / math.sqrt(differences.size))
    if standard_error == 0.0:
        equivalent = abs(mean_difference) < equivalence_margin
        return {
            "state": "degenerate_exact_difference",
            "n_pairs": int(left.size),
            "mean_difference": round(mean_difference, 6),
            "equivalence_margin": equivalence_margin,
            "p_lower": 0.0 if mean_difference > -equivalence_margin else 1.0,
            "p_upper": 0.0 if mean_difference < equivalence_margin else 1.0,
            "equivalent": equivalent,
            "evidence_class": "ENGINEERING_ONLY",
        }
    degrees_of_freedom = int(differences.size - 1)
    lower_t = (mean_difference + equivalence_margin) / standard_error
    upper_t = (mean_difference - equivalence_margin) / standard_error
    p_lower = float(stats.t.sf(lower_t, degrees_of_freedom))
    p_upper = float(stats.t.cdf(upper_t, degrees_of_freedom))
    critical = float(stats.t.ppf(1.0 - alpha, degrees_of_freedom))
    ci = [
        mean_difference - critical * standard_error,
        mean_difference + critical * standard_error,
    ]
    return {
        "state": "ok",
        "method": "paired_tost",
        "n_pairs": int(left.size),
        "mean_difference": round(mean_difference, 6),
        "equivalence_margin": equivalence_margin,
        "alpha": alpha,
        "confidence_interval": [round(value, 6) for value in ci],
        "p_lower": round(p_lower, 6),
        "p_upper": round(p_upper, 6),
        "equivalent": p_lower < alpha and p_upper < alpha,
        "evidence_class": "ENGINEERING_ONLY",
    }


def missingness_diagnostics(
    rows: Sequence[Mapping[str, Any]],
    *,
    required_fields: Sequence[str],
    group_fields: Sequence[str] = ("agent", "condition", "intervention_family"),
) -> dict[str, Any]:
    """Report field- and group-specific missingness without dropping rows."""

    field_missing = Counter[str]()
    group_counts: dict[str, Counter[str]] = {
        field: Counter() for field in group_fields
    }
    group_missing: dict[str, dict[str, Counter[str]]] = {
        field: defaultdict(Counter) for field in group_fields
    }
    for row in rows:
        missing = [
            field
            for field in required_fields
            if field not in row or _is_missing(row.get(field))
        ]
        field_missing.update(missing)
        for group_field in group_fields:
            group = str(row.get(group_field, "<missing-group>"))
            group_counts[group_field][group] += 1
            for field in missing:
                group_missing[group_field][group][field] += 1
    row_count = len(rows)
    field_rates = {
        field: (
            round(field_missing[field] / row_count, 6)
            if row_count
            else None
        )
        for field in required_fields
    }
    return {
        "state": "ok" if rows else "blocked_no_rows",
        "row_count": row_count,
        "required_fields": list(required_fields),
        "field_missing_counts": {
            field: field_missing[field] for field in required_fields
        },
        "field_missing_rates": field_rates,
        "group_counts": {
            field: dict(sorted(counts.items()))
            for field, counts in group_counts.items()
        },
        "group_missing_counts": {
            field: {
                group: dict(sorted(counts.items()))
                for group, counts in sorted(groups.items())
            }
            for field, groups in group_missing.items()
        },
        "complete_case_count": sum(
            1
            for row in rows
            if all(
                field in row and not _is_missing(row.get(field))
                for field in required_fields
            )
        ),
        "evidence_class": "ENGINEERING_ONLY",
    }


def opportunity_denominator_check(
    rows: Sequence[Mapping[str, Any]],
    *,
    opportunity_field: str,
    outcome_field: str,
) -> dict[str, Any]:
    """Validate that recovery/abstention rates use eligible opportunities."""

    opportunity_count = 0
    outcome_count = 0
    invalid_outcomes: list[int] = []
    missing_outcomes: list[int] = []
    for index, row in enumerate(rows):
        opportunity = row.get(opportunity_field)
        outcome = row.get(outcome_field)
        if not isinstance(opportunity, bool):
            continue
        if opportunity:
            opportunity_count += 1
            if not isinstance(outcome, bool):
                missing_outcomes.append(index)
            elif outcome:
                outcome_count += 1
        elif outcome is True:
            invalid_outcomes.append(index)
    issues: list[str] = []
    if invalid_outcomes:
        issues.append("positive_outcome_without_opportunity")
    if missing_outcomes:
        issues.append("missing_outcome_for_opportunity")
    return {
        "state": (
            "blocked_no_opportunities"
            if opportunity_count == 0
            else "invalid"
            if issues
            else "ok"
        ),
        "opportunity_count": opportunity_count,
        "positive_outcome_count": outcome_count,
        "rate": (
            round(outcome_count / opportunity_count, 6)
            if opportunity_count
            else None
        ),
        "invalid_outcome_row_indices": invalid_outcomes,
        "missing_outcome_row_indices": missing_outcomes,
        "issues": issues,
        "evidence_class": "ENGINEERING_ONLY",
    }


def naturalistic_predictive_validity(
    rows: Sequence[Mapping[str, Any]],
    *,
    outcome_field: str = "naturalistic_success",
    predictor_fields: Sequence[str] = DEFAULT_PREDICTORS,
    family_field: str = "model_family",
    seed: int = 20260728,
    n_boot: int = 1000,
) -> dict[str, Any]:
    """Correlation, regression, calibration, and leave-family-out planning.

    Rows are model-level or model-by-repeat summaries. This function never
    promotes their evidence class; callers must pass audited inputs through the
    separate paper-asset gate.
    """

    if n_boot < 1:
        raise ValueError("n_boot must be positive")
    complete: list[dict[str, Any]] = []
    for row in rows:
        candidate_values = [
            row.get(outcome_field),
            *(row.get(field) for field in predictor_fields),
        ]
        if all(_finite_number(value) for value in candidate_values):
            complete.append(dict(row))
    if len(complete) < 4:
        return {
            "state": "blocked_insufficient_complete_rows",
            "input_row_count": len(rows),
            "complete_row_count": len(complete),
            "minimum_complete_rows": 4,
            "scientific_evidence": False,
            "evidence_class": "ENGINEERING_ONLY",
        }

    outcome = np.asarray(
        [float(row[outcome_field]) for row in complete],
        dtype=float,
    )
    correlations: dict[str, dict[str, Any]] = {}
    rng = np.random.default_rng(seed)
    for predictor in predictor_fields:
        predictor_values = np.asarray(
            [float(row[predictor]) for row in complete],
            dtype=float,
        )
        if np.all(predictor_values == predictor_values[0]) or np.all(
            outcome == outcome[0]
        ):
            correlations[predictor] = {
                "state": "undefined_constant_input",
                "pearson": None,
                "spearman": None,
                "bootstrap_pearson_ci": [None, None],
            }
            continue
        pearson = float(stats.pearsonr(predictor_values, outcome).statistic)
        spearman = float(stats.spearmanr(predictor_values, outcome).statistic)
        boot_values: list[float] = []
        for _ in range(n_boot):
            indices = rng.integers(0, len(complete), size=len(complete))
            sampled_x = predictor_values[indices]
            sampled_y = outcome[indices]
            if np.all(sampled_x == sampled_x[0]) or np.all(sampled_y == sampled_y[0]):
                continue
            boot_values.append(float(stats.pearsonr(sampled_x, sampled_y).statistic))
        correlations[predictor] = {
            "state": "ok" if boot_values else "bootstrap_degenerate",
            "pearson": round(pearson, 6),
            "spearman": round(spearman, 6),
            "bootstrap_pearson_ci": _percentile_interval(boot_values),
            "n_boot_valid": len(boot_values),
        }

    design = np.asarray(
        [
            [1.0, *(float(row[field]) for field in predictor_fields)]
            for row in complete
        ],
        dtype=float,
    )
    coefficients, _, rank, singular = np.linalg.lstsq(design, outcome, rcond=None)
    predicted = design @ coefficients
    regression = {
        "state": "ok" if rank == design.shape[1] else "rank_deficient",
        "coefficient_names": ["intercept", *predictor_fields],
        "coefficients": [round(float(value), 6) for value in coefficients],
        "design_rank": int(rank),
        "design_columns": int(design.shape[1]),
        "condition_number": (
            round(float(singular[0] / singular[-1]), 6)
            if singular.size and singular[-1] > 0
            else None
        ),
        "r_squared": _r_squared(outcome, predicted),
        "mean_absolute_error": round(float(np.mean(np.abs(outcome - predicted))), 6),
    }
    families = sorted(
        {
            str(row.get(family_field))
            for row in complete
            if row.get(family_field) not in (None, "")
        }
    )
    leave_family_out: list[dict[str, Any]] = []
    for family in families:
        test_indices = [
            index
            for index, row in enumerate(complete)
            if str(row.get(family_field)) == family
        ]
        train_indices = [
            index for index in range(len(complete)) if index not in test_indices
        ]
        if len(train_indices) < design.shape[1] or not test_indices:
            leave_family_out.append(
                {
                    "held_out_family": family,
                    "state": "blocked_insufficient_training_rows",
                }
            )
            continue
        fit, _, train_rank, _ = np.linalg.lstsq(
            design[train_indices],
            outcome[train_indices],
            rcond=None,
        )
        test_prediction = design[test_indices] @ fit
        leave_family_out.append(
            {
                "held_out_family": family,
                "state": "ok" if train_rank == design.shape[1] else "rank_deficient",
                "test_rows": len(test_indices),
                "mean_absolute_error": round(
                    float(np.mean(np.abs(outcome[test_indices] - test_prediction))),
                    6,
                ),
            }
        )
    return {
        "state": "ok",
        "input_row_count": len(rows),
        "complete_row_count": len(complete),
        "outcome_field": outcome_field,
        "predictor_fields": list(predictor_fields),
        "correlations": correlations,
        "regression": regression,
        "calibration": _calibration_summary(predicted, outcome),
        "leave_one_family_out": leave_family_out,
        "limitations": [
            "Model-level rows are a small panel unless independently expanded.",
            "Correlations are predictive associations, not causal effects.",
            "Leave-one-model-out is reportable only when the model count supports it.",
        ],
        "scientific_evidence": False,
        "evidence_class": "ENGINEERING_ONLY",
    }


def mixed_effects_binary_contract(
    rows: Sequence[Mapping[str, Any]],
    *,
    outcome_field: str,
    fixed_effects: Sequence[str],
    cluster_field: str = "base_task_id",
    minimum_clusters: int = 10,
) -> dict[str, Any]:
    """Return a fail-closed preregistered mixed-effects fitting contract."""

    complete = [
        row
        for row in rows
        if row.get(outcome_field) in (0, 1, False, True)
        and row.get(cluster_field) not in (None, "")
        and all(row.get(field) not in (None, "") for field in fixed_effects)
    ]
    clusters = {str(row[cluster_field]) for row in complete}
    outcomes = {int(bool(row[outcome_field])) for row in complete}
    blockers: list[str] = []
    if len(clusters) < minimum_clusters:
        blockers.append("insufficient_clusters")
    if len(outcomes) < 2:
        blockers.append("outcome_has_no_variation")
    if len(complete) <= len(fixed_effects) + 2:
        blockers.append("insufficient_complete_rows")
    formula = (
        f"{outcome_field} ~ "
        + (" + ".join(fixed_effects) if fixed_effects else "1")
    )
    return {
        "state": "blocked" if blockers else "ready_for_preregistered_fit",
        "formula": formula,
        "random_intercept": cluster_field,
        "complete_row_count": len(complete),
        "cluster_count": len(clusters),
        "minimum_clusters": minimum_clusters,
        "blockers": blockers,
        "fit_policy": (
            "Fit only after design review; report convergence, singularity, "
            "cluster count, fixed effects, and sensitivity to simpler paired models."
        ),
        "evidence_class": "ENGINEERING_ONLY",
    }


def raac_clean_tradeoff(
    rows: Sequence[Mapping[str, Any]],
    *,
    policy_field: str = "policy",
    baseline_policy: str = "STANDARD_TOOL_USE",
    clean_success_field: str = "clean_success",
    robust_success_field: str = "robust_success",
    extra_calls_field: str = "extra_calls",
    latency_field: str = "wall_clock_seconds",
) -> dict[str, Any]:
    """Summarize clean-performance and robustness trade-offs by RAAC policy."""

    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        policy = row.get(policy_field)
        required = (
            row.get(clean_success_field),
            row.get(robust_success_field),
            row.get(extra_calls_field),
            row.get(latency_field),
        )
        if policy is not None and all(_finite_number(value) for value in required):
            grouped[str(policy)].append(row)
    if baseline_policy not in grouped:
        return {
            "state": "blocked_missing_baseline",
            "baseline_policy": baseline_policy,
            "evidence_class": "ENGINEERING_ONLY",
        }
    baseline = _policy_means(
        grouped[baseline_policy],
        clean_success_field,
        robust_success_field,
        extra_calls_field,
        latency_field,
    )
    comparisons: list[dict[str, Any]] = []
    for policy, policy_rows in sorted(grouped.items()):
        summary = _policy_means(
            policy_rows,
            clean_success_field,
            robust_success_field,
            extra_calls_field,
            latency_field,
        )
        comparisons.append(
            {
                "policy": policy,
                **summary,
                "clean_success_delta_vs_baseline": _rounded_difference(
                    summary["clean_success"],
                    baseline["clean_success"],
                ),
                "robust_success_delta_vs_baseline": _rounded_difference(
                    summary["robust_success"],
                    baseline["robust_success"],
                ),
                "extra_calls_delta_vs_baseline": _rounded_difference(
                    summary["extra_calls"],
                    baseline["extra_calls"],
                ),
                "latency_delta_vs_baseline": _rounded_difference(
                    summary["wall_clock_seconds"],
                    baseline["wall_clock_seconds"],
                ),
            }
        )
    return {
        "state": "ok",
        "baseline_policy": baseline_policy,
        "comparisons": comparisons,
        "evidence_class": "ENGINEERING_ONLY",
        "scientific_evidence": False,
    }


def cost_efficiency_frontier(
    points: Sequence[Mapping[str, Any]],
    *,
    name_field: str = "policy",
    cost_field: str = "mean_cost",
    performance_field: str = "robust_success",
) -> dict[str, Any]:
    """Return the non-dominated cost/performance frontier."""

    valid = [
        (
            str(point[name_field]),
            float(point[cost_field]),
            float(point[performance_field]),
        )
        for point in points
        if point.get(name_field) is not None
        and _finite_number(point.get(cost_field))
        and _finite_number(point.get(performance_field))
        and float(point[cost_field]) >= 0
    ]
    frontier: list[tuple[str, float, float]] = []
    dominated: list[str] = []
    for candidate_name, candidate_cost, candidate_performance in valid:
        is_dominated = any(
            other_name != candidate_name
            and other_cost <= candidate_cost
            and other_performance >= candidate_performance
            and (
                other_cost < candidate_cost
                or other_performance > candidate_performance
            )
            for other_name, other_cost, other_performance in valid
        )
        if is_dominated:
            dominated.append(candidate_name)
        else:
            frontier.append(
                (candidate_name, candidate_cost, candidate_performance)
            )
    frontier.sort(key=lambda point: (point[1], -point[2], point[0]))
    return {
        "state": "ok" if valid else "blocked_no_valid_points",
        "frontier": [
            {"name": name, "cost": cost, "performance": performance}
            for name, cost, performance in frontier
        ],
        "dominated": sorted(dominated),
        "input_point_count": len(points),
        "valid_point_count": len(valid),
        "evidence_class": "ENGINEERING_ONLY",
    }


def clustered_bootstrap_shard(
    pairs: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    replicate_start: int,
    replicate_stop: int,
    cluster_field: str = "base_task_id",
) -> dict[str, Any]:
    """Compute a deterministic, independently resumable bootstrap shard."""

    if replicate_start < 0 or replicate_stop <= replicate_start:
        raise ValueError("replicate range must satisfy 0 <= start < stop")
    normalized = _valid_pairs(pairs, cluster_field)
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        clusters[str(row[cluster_field])].append(row)
    cluster_ids = sorted(clusters)
    if not cluster_ids:
        return {
            "state": "blocked_no_clusters",
            "seed": seed,
            "replicate_start": replicate_start,
            "replicate_stop": replicate_stop,
            "samples": [],
            "evidence_class": "FIXTURE_ONLY",
        }
    samples: list[dict[str, Any]] = []
    for replicate in range(replicate_start, replicate_stop):
        rng = np.random.default_rng(np.random.SeedSequence([seed, replicate]))
        sampled_ids = rng.choice(cluster_ids, size=len(cluster_ids), replace=True)
        sampled_rows = [
            row
            for cluster_id in sampled_ids
            for row in clusters[str(cluster_id)]
        ]
        clean = np.asarray([row["clean_success"] for row in sampled_rows], dtype=float)
        intervention = np.asarray(
            [row["intervention_success"] for row in sampled_rows],
            dtype=float,
        )
        clean_rate = float(clean.mean())
        intervention_rate = float(intervention.mean())
        samples.append(
            {
                "replicate": replicate,
                "clean_success": round(clean_rate, 8),
                "intervention_success": round(intervention_rate, 8),
                "absolute_degradation": round(clean_rate - intervention_rate, 8),
                "acrs": (
                    round(intervention_rate / clean_rate, 8)
                    if clean_rate > 0
                    else None
                ),
            }
        )
    return {
        "state": "ok",
        "seed": seed,
        "replicate_start": replicate_start,
        "replicate_stop": replicate_stop,
        "cluster_field": cluster_field,
        "cluster_count": len(cluster_ids),
        "samples": samples,
        "evidence_class": "FIXTURE_ONLY",
    }


def merge_clustered_bootstrap_shards(
    shards: Sequence[Mapping[str, Any]],
    *,
    expected_replicates: int,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Merge shards and fail on duplicates, gaps, or incompatible seeds."""

    if expected_replicates < 1:
        raise ValueError("expected_replicates must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    seeds = {shard.get("seed") for shard in shards if shard.get("state") == "ok"}
    samples: dict[int, Mapping[str, Any]] = {}
    duplicates: list[int] = []
    for shard in shards:
        for sample in shard.get("samples", []):
            if not isinstance(sample, Mapping):
                continue
            replicate = int(sample["replicate"])
            if replicate in samples:
                duplicates.append(replicate)
            else:
                samples[replicate] = sample
    expected = set(range(expected_replicates))
    observed = set(samples)
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    issues: list[str] = []
    if len(seeds) != 1:
        issues.append("incompatible_seeds")
    if duplicates:
        issues.append("duplicate_replicates")
    if missing:
        issues.append("missing_replicates")
    if unexpected:
        issues.append("unexpected_replicates")
    intervals: dict[str, list[float | None]] = {}
    for metric in (
        "clean_success",
        "intervention_success",
        "absolute_degradation",
        "acrs",
    ):
        values = [
            float(samples[index][metric])
            for index in sorted(samples)
            if samples[index].get(metric) is not None
        ]
        intervals[metric] = _percentile_interval(values, alpha=alpha)
    return {
        "state": "invalid" if issues else "ok",
        "expected_replicates": expected_replicates,
        "observed_replicates": len(samples),
        "seed": next(iter(seeds)) if len(seeds) == 1 else None,
        "duplicate_replicates": sorted(set(duplicates)),
        "missing_replicates": missing,
        "unexpected_replicates": unexpected,
        "issues": issues,
        "confidence_intervals": intervals,
        "evidence_class": "FIXTURE_ONLY",
    }


def _valid_pairs(
    pairs: Sequence[Mapping[str, Any]],
    cluster_field: str,
) -> list[dict[str, Any]]:
    return [
        {
            **dict(row),
            "clean_success": float(row["clean_success"]),
            "intervention_success": float(row["intervention_success"]),
        }
        for row in pairs
        if row.get(cluster_field) not in (None, "")
        and _finite_number(row.get("clean_success"))
        and _finite_number(row.get("intervention_success"))
    ]


def _policy_means(
    rows: Sequence[Mapping[str, Any]],
    clean_field: str,
    robust_field: str,
    calls_field: str,
    latency_field: str,
) -> dict[str, Any]:
    return {
        "n": len(rows),
        "clean_success": _mean_field(rows, clean_field),
        "robust_success": _mean_field(rows, robust_field),
        "extra_calls": _mean_field(rows, calls_field),
        "wall_clock_seconds": _mean_field(rows, latency_field),
    }


def _mean_field(rows: Sequence[Mapping[str, Any]], field: str) -> float:
    return round(float(np.mean([float(row[field]) for row in rows])), 6)


def _calibration_summary(
    predicted: np.ndarray,
    observed: np.ndarray,
    *,
    bins: int = 5,
) -> list[dict[str, Any]]:
    clipped = np.clip(predicted, 0.0, 1.0)
    boundaries = np.linspace(0.0, 1.0, bins + 1)
    output: list[dict[str, Any]] = []
    for index in range(bins):
        lower = boundaries[index]
        upper = boundaries[index + 1]
        mask = (
            (clipped >= lower)
            & (clipped <= upper if index == bins - 1 else clipped < upper)
        )
        if not np.any(mask):
            continue
        output.append(
            {
                "bin": index + 1,
                "lower": round(float(lower), 6),
                "upper": round(float(upper), 6),
                "n": int(np.sum(mask)),
                "mean_prediction": round(float(np.mean(clipped[mask])), 6),
                "mean_outcome": round(float(np.mean(observed[mask])), 6),
            }
        )
    return output


def _r_squared(observed: np.ndarray, predicted: np.ndarray) -> float | None:
    total = float(np.sum((observed - observed.mean()) ** 2))
    if total == 0.0:
        return None
    residual = float(np.sum((observed - predicted) ** 2))
    return round(1.0 - residual / total, 6)


def _percentile_interval(
    values: Sequence[float],
    *,
    alpha: float = 0.05,
) -> list[float | None]:
    if not values:
        return [None, None]
    return [
        round(float(np.quantile(values, alpha / 2.0)), 6),
        round(float(np.quantile(values, 1.0 - alpha / 2.0)), 6),
    ]


def _rounded_difference(left: float, right: float) -> float:
    return round(left - right, 6)


def _is_missing(value: Any) -> bool:
    return value is None or value == "" or (
        isinstance(value, float) and not math.isfinite(value)
    )


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float, np.integer, np.floating))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    ) or isinstance(value, bool)
