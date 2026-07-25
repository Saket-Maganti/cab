from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from statistics import mean
from typing import Any

import numpy as np

from causal_agent_bench.metrics.causal_robustness import (
    NEAR_ZERO_CLEAN_THRESHOLD,
    denominator_policy,
)

# `scipy.stats` is imported lazily inside the two functions that use it
# (bca_bootstrap_ci, ranking_instability). scipy costs ~0.4s to import, so
# keeping it off module-load time speeds up every CLI command and any importer
# of this foundational module that doesn't hit the bootstrap/kendall paths.


def adjust_pvalues(
    pvalues: Sequence[float | None],
    *,
    method: str = "holm",
) -> list[float | None]:
    """Return family-wise / FDR adjusted p-values, preserving input order.

    ``method="holm"`` applies the Holm-Bonferroni step-down correction (controls
    the family-wise error rate); ``method="bh"`` applies the Benjamini-Hochberg
    step-up procedure (controls the false discovery rate). ``None`` entries are
    treated as "no test" and pass through as ``None`` (and are excluded from the
    multiplicity count ``m``). Implemented locally to avoid a statsmodels
    dependency and to stay deterministic across scipy versions.
    """

    indexed = [(i, float(p)) for i, p in enumerate(pvalues) if p is not None]
    adjusted: list[float | None] = [None] * len(pvalues)
    m = len(indexed)
    if m == 0:
        return adjusted
    order = sorted(indexed, key=lambda item: item[1])
    if method == "holm":
        running = 0.0
        for rank, (idx, p) in enumerate(order):
            running = max(running, min(1.0, (m - rank) * p))
            adjusted[idx] = round(running, 6)
    elif method in {"bh", "fdr_bh", "benjamini_hochberg"}:
        running = 1.0
        for rank in range(m - 1, -1, -1):
            idx, p = order[rank]
            running = min(running, min(1.0, p * m / (rank + 1)))
            adjusted[idx] = round(running, 6)
    else:
        raise ValueError(f"unknown method {method!r}; expected 'holm' or 'bh'")
    return adjusted


def cliffs_delta(a: Sequence[float], b: Sequence[float]) -> float | None:
    """Cliff's delta non-parametric effect size for ``a`` vs ``b`` in [-1, 1].

    Positive values mean ``a`` tends to exceed ``b``. Complements Cohen's dz when
    the paired differences are non-normal (the regime where Wilcoxon is used).
    """

    a_vals = [float(x) for x in a]
    b_vals = [float(x) for x in b]
    if not a_vals or not b_vals:
        return None
    a_arr = np.asarray(a_vals)[:, None]
    b_arr = np.asarray(b_vals)[None, :]
    greater = int(np.sum(a_arr > b_arr))
    less = int(np.sum(a_arr < b_arr))
    return round((greater - less) / (len(a_vals) * len(b_vals)), 6)


def paired_binary_test(
    clean: Sequence[int | bool | float],
    intervention: Sequence[int | bool | float],
) -> dict[str, Any]:
    """Exact McNemar test for matched binary outcomes.

    The result includes the full transition table so an all-concordant sample is
    explicit (``p_value=None``) rather than being mistaken for a failed test.
    """

    from scipy import stats

    clean_values = _binary_vector(clean, name="clean")
    intervention_values = _binary_vector(
        intervention,
        name="intervention",
    )
    if len(clean_values) != len(intervention_values):
        raise ValueError("clean and intervention must have equal length")
    transitions = {
        "success_to_success": 0,
        "success_to_failure": 0,
        "failure_to_success": 0,
        "failure_to_failure": 0,
    }
    for clean_value, intervention_value in zip(
        clean_values,
        intervention_values,
        strict=True,
    ):
        transitions[
            {
                (1, 1): "success_to_success",
                (1, 0): "success_to_failure",
                (0, 1): "failure_to_success",
                (0, 0): "failure_to_failure",
            }[(clean_value, intervention_value)]
        ] += 1
    success_to_failure = transitions["success_to_failure"]
    failure_to_success = transitions["failure_to_success"]
    discordant = success_to_failure + failure_to_success
    p_value = None
    if discordant:
        p_value = round(
            float(
                stats.binomtest(
                    min(success_to_failure, failure_to_success),
                    n=discordant,
                    p=0.5,
                    alternative="two-sided",
                ).pvalue
            ),
            6,
        )
    return {
        "test": "exact_mcnemar_binomial",
        "n_pairs": len(clean_values),
        "discordant_pair_count": discordant,
        **transitions,
        "p_value": p_value,
        "test_state": (
            "ok" if discordant else "undefined_no_discordant_pairs"
        ),
    }


def paired_effect_sizes(
    clean: Sequence[float],
    intervention: Sequence[float],
) -> dict[str, float | None]:
    """Effect sizes that preserve the clean/intervention matching."""

    clean_values = np.asarray([float(value) for value in clean], dtype=float)
    intervention_values = np.asarray(
        [float(value) for value in intervention],
        dtype=float,
    )
    if clean_values.size != intervention_values.size:
        raise ValueError("clean and intervention must have equal length")
    if clean_values.size == 0:
        return {
            "mean_paired_difference": None,
            "cohen_dz": None,
            "matched_rank_biserial": None,
            "matched_odds_ratio": None,
        }
    differences = clean_values - intervention_values
    difference_sd = (
        float(differences.std(ddof=1))
        if differences.size > 1
        else 0.0
    )
    positive = int(np.sum(differences > 0))
    negative = int(np.sum(differences < 0))
    discordant = positive + negative
    return {
        "mean_paired_difference": round(
            float(differences.mean()),
            6,
        ),
        "cohen_dz": (
            round(float(differences.mean()) / difference_sd, 6)
            if difference_sd > 0.0
            else None
        ),
        "matched_rank_biserial": (
            round((positive - negative) / discordant, 6)
            if discordant
            else None
        ),
        # Haldane-Anscombe correction keeps the matched odds ratio finite
        # when one discordant cell is zero.
        "matched_odds_ratio": (
            round((positive + 0.5) / (negative + 0.5), 6)
            if discordant
            else None
        ),
    }


def paired_bootstrap(
    pairs: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    n_boot: int = 1000,
    alpha: float = 0.05,
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, Any]:
    """Pair-level percentile bootstrap for the core robustness endpoints."""

    return _bootstrap_pairs(
        _validated_pairs(pairs),
        seed=seed,
        n_boot=n_boot,
        alpha=alpha,
        resampling_unit="pair_id",
        strata_key=None,
        near_zero_threshold=near_zero_threshold,
    )


def clustered_paired_bootstrap(
    pairs: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    n_boot: int = 1000,
    alpha: float = 0.05,
    cluster_key: str = "base_task_id",
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, Any]:
    """Bootstrap base-task clusters, retaining correlated variants together."""

    return _bootstrap_pairs(
        _validated_pairs(pairs),
        seed=seed,
        n_boot=n_boot,
        alpha=alpha,
        resampling_unit=cluster_key,
        strata_key=None,
        near_zero_threshold=near_zero_threshold,
    )


def stratified_paired_bootstrap(
    pairs: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    n_boot: int = 1000,
    alpha: float = 0.05,
    strata_key: str = "intervention_family",
    cluster_key: str = "base_task_id",
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, Any]:
    """Bootstrap base-task clusters separately within each family stratum."""

    return _bootstrap_pairs(
        _validated_pairs(pairs),
        seed=seed,
        n_boot=n_boot,
        alpha=alpha,
        resampling_unit=cluster_key,
        strata_key=strata_key,
        near_zero_threshold=near_zero_threshold,
    )


def rank_bootstrap(
    pairs: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    n_boot: int = 1000,
    alpha: float = 0.05,
    metric: str = "acrs",
    cluster_key: str = "base_task_id",
    agent_key: str = "agent_name",
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, Any]:
    """Cluster-bootstrap rankings over the common task support.

    Resampling is synchronized across agents. Only base-task clusters observed
    for every agent are rank-comparable; exclusions are reported explicitly.
    Pairwise matrix entries are ``P(row ranks above column)`` with ties worth
    one half.
    """

    valid_pairs = _validated_pairs(pairs)
    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in valid_pairs:
        agent = pair.get(agent_key)
        if agent is None:
            continue
        by_agent[str(agent)].append(pair)
    agents = sorted(by_agent)
    empty = {
        "metric": metric,
        "agents": agents,
        "n_boot_requested": n_boot,
        "n_boot_valid": 0,
        "cluster_key": cluster_key,
        "common_cluster_count": 0,
        "common_pair_unit_count": 0,
        "rank_probabilities": {},
        "expected_rank": {},
        "rank_ci": {},
        "pairwise_rank_probability_matrix": {},
        "probability_rank_changed_from_clean": {},
        "state": "insufficient_agents_or_common_clusters",
        "fixture_only_not_evidence": True,
    }
    if len(agents) < 2:
        return empty
    support_by_agent: dict[str, set[tuple[str, str, str]]] = {}
    for agent, agent_pairs in by_agent.items():
        support: set[tuple[str, str, str]] = set()
        for pair in agent_pairs:
            support_key = _pair_support_key(
                pair,
                cluster_key=cluster_key,
            )
            if support_key is not None:
                support.add(support_key)
        support_by_agent[agent] = support
    common_support = set.intersection(
        *(support_by_agent[agent] for agent in agents)
    )
    common_clusters = {
        support[0] for support in common_support
    }
    empty["common_cluster_count"] = len(common_clusters)
    empty["common_pair_unit_count"] = len(common_support)
    empty["agent_pair_unit_counts"] = {
        agent: len(support_by_agent[agent]) for agent in agents
    }
    empty["excluded_noncommon_pair_unit_count"] = len(
        set.union(*(support_by_agent[agent] for agent in agents))
        - common_support
    )
    if not common_support:
        return empty

    cluster_list = sorted(common_clusters)
    common_pairs_by_agent = {
        agent: [
            pair
            for pair in by_agent[agent]
            if _pair_support_key(pair, cluster_key=cluster_key)
            in common_support
        ]
        for agent in agents
    }
    rng = np.random.default_rng(seed)
    robust_rank_samples: dict[str, list[float]] = {
        agent: [] for agent in agents
    }
    clean_rank_samples: dict[str, list[float]] = {
        agent: [] for agent in agents
    }
    point_robust_scores = {
        agent: _ranking_metric(
            common_pairs_by_agent[agent],
            metric,
            near_zero_threshold=near_zero_threshold,
        )
        for agent in agents
    }
    point_clean_scores = {
        agent: _point_estimates(
            common_pairs_by_agent[agent],
            near_zero_threshold=near_zero_threshold,
        )["clean_success_rate"]
        for agent in agents
    }
    point_robust_ranks = _average_ranks(point_robust_scores)
    point_clean_ranks = _average_ranks(point_clean_scores)

    for _ in range(n_boot):
        sampled_clusters = rng.choice(
            cluster_list,
            size=len(cluster_list),
            replace=True,
        ).tolist()
        robust_scores: dict[str, float | None] = {}
        clean_scores: dict[str, float | None] = {}
        for agent in agents:
            sampled_pairs: list[dict[str, Any]] = []
            agent_pairs_by_cluster: dict[
                str,
                list[dict[str, Any]],
            ] = defaultdict(list)
            for pair in common_pairs_by_agent[agent]:
                cluster = pair.get(cluster_key)
                if cluster is not None:
                    agent_pairs_by_cluster[str(cluster)].append(pair)
            for cluster in sampled_clusters:
                sampled_pairs.extend(agent_pairs_by_cluster[str(cluster)])
            estimates = _point_estimates(
                sampled_pairs,
                near_zero_threshold=near_zero_threshold,
            )
            robust_scores[agent] = _ranking_metric(
                sampled_pairs,
                metric,
                near_zero_threshold=near_zero_threshold,
            )
            clean_scores[agent] = estimates["clean_success_rate"]
        if any(value is None for value in robust_scores.values()):
            continue
        robust_ranks = _average_ranks(robust_scores)
        clean_ranks = _average_ranks(clean_scores)
        for agent in agents:
            robust_rank = robust_ranks[agent]
            clean_rank = clean_ranks[agent]
            assert robust_rank is not None
            assert clean_rank is not None
            robust_rank_samples[agent].append(float(robust_rank))
            clean_rank_samples[agent].append(float(clean_rank))

    n_valid = len(robust_rank_samples[agents[0]])
    if not n_valid:
        empty["state"] = "no_reportable_bootstrap_replicates"
        return empty
    rank_probabilities: dict[str, dict[str, float]] = {}
    expected_rank: dict[str, float] = {}
    rank_ci: dict[str, list[float]] = {}
    rank_change: dict[str, float] = {}
    for agent in agents:
        samples = robust_rank_samples[agent]
        counts = {
            _rank_label(rank): samples.count(rank) / n_valid
            for rank in sorted(set(samples))
        }
        rank_probabilities[agent] = {
            rank: round(probability, 6)
            for rank, probability in counts.items()
        }
        expected_rank[agent] = round(float(np.mean(samples)), 6)
        rank_ci[agent] = [
            round(float(np.quantile(samples, alpha / 2.0)), 6),
            round(
                float(np.quantile(samples, 1.0 - alpha / 2.0)),
                6,
            ),
        ]
        rank_change[agent] = round(
            sum(
                robust != clean
                for robust, clean in zip(
                    samples,
                    clean_rank_samples[agent],
                    strict=True,
                )
            )
            / n_valid,
            6,
        )
    probability_matrix: dict[str, dict[str, float]] = {}
    for row_agent in agents:
        probability_matrix[row_agent] = {}
        for column_agent in agents:
            if row_agent == column_agent:
                probability = 0.5
            else:
                probability = mean(
                    1.0
                    if row_rank < column_rank
                    else 0.5
                    if row_rank == column_rank
                    else 0.0
                    for row_rank, column_rank in zip(
                        robust_rank_samples[row_agent],
                        robust_rank_samples[column_agent],
                        strict=True,
                    )
                )
            probability_matrix[row_agent][column_agent] = round(
                probability,
                6,
            )

    common_point_agents = [
        agent
        for agent in agents
        if point_clean_ranks.get(agent) is not None
        and point_robust_ranks.get(agent) is not None
    ]
    spearman = None
    kendall = None
    if len(common_point_agents) >= 2:
        from scipy import stats

        clean_rank_vector = [
            point_clean_ranks[agent] for agent in common_point_agents
        ]
        robust_rank_vector = [
            point_robust_ranks[agent] for agent in common_point_agents
        ]
        if (
            len(set(clean_rank_vector)) > 1
            and len(set(robust_rank_vector)) > 1
        ):
            spearman_result = stats.spearmanr(
                clean_rank_vector,
                robust_rank_vector,
            )
            kendall_result = stats.kendalltau(
                clean_rank_vector,
                robust_rank_vector,
            )
            if spearman_result.statistic == spearman_result.statistic:
                spearman = round(float(spearman_result.statistic), 6)
            if kendall_result.statistic == kendall_result.statistic:
                kendall = round(float(kendall_result.statistic), 6)

    return {
        "metric": metric,
        "agents": agents,
        "n_boot_requested": n_boot,
        "n_boot_valid": n_valid,
        "cluster_key": cluster_key,
        "common_cluster_count": len(common_clusters),
        "common_pair_unit_count": len(common_support),
        "agent_pair_unit_counts": empty["agent_pair_unit_counts"],
        "excluded_noncommon_pair_unit_count": empty[
            "excluded_noncommon_pair_unit_count"
        ],
        "point_clean_ranking": point_clean_ranks,
        "point_robustness_ranking": point_robust_ranks,
        "point_rank_delta": {
            agent: _rank_difference(
                point_robust_ranks.get(agent),
                point_clean_ranks.get(agent),
            )
            for agent in agents
        },
        "spearman_clean_vs_robustness": spearman,
        "kendall_clean_vs_robustness": kendall,
        "rank_probabilities": rank_probabilities,
        "expected_rank": expected_rank,
        "rank_ci": rank_ci,
        "pairwise_rank_probability_matrix": probability_matrix,
        "probability_rank_changed_from_clean": rank_change,
        "state": "ok",
        "fixture_only_not_evidence": True,
    }


def scorer_error_sensitivity(
    pairs: Sequence[Mapping[str, Any]],
    *,
    false_positive_rate: float,
    false_negative_rate: float,
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, Any]:
    """Correct observed binary rates under an explicit scorer-error scenario.

    This is a sensitivity calculation, not evidence that the supplied error
    rates are correct. Real use must source them from blinded human review.
    """

    if not (0.0 <= false_positive_rate < 1.0):
        raise ValueError("false_positive_rate must be in [0, 1)")
    if not (0.0 <= false_negative_rate < 1.0):
        raise ValueError("false_negative_rate must be in [0, 1)")
    identification = 1.0 - false_positive_rate - false_negative_rate
    baseline = _point_estimates(
        _validated_pairs(pairs),
        near_zero_threshold=near_zero_threshold,
    )
    if identification <= 0.0:
        return {
            "available": False,
            "state": "unidentifiable_error_rates_sum_to_one_or_more",
            "assumed_false_positive_rate": false_positive_rate,
            "assumed_false_negative_rate": false_negative_rate,
            "baseline": baseline,
            "corrected": None,
            "fixture_only_not_evidence": True,
        }

    def corrected(value: float | None) -> float | None:
        if value is None:
            return None
        return min(
            1.0,
            max(
                0.0,
                (value - false_positive_rate) / identification,
            ),
        )

    corrected_clean = corrected(baseline["clean_success_rate"])
    corrected_intervention = corrected(
        baseline["intervention_success_rate"]
    )
    denominator = denominator_policy(
        corrected_clean,
        n_pairs=baseline["n_pairs"],
        near_zero_threshold=near_zero_threshold,
    )
    corrected_acrs = (
        round(corrected_intervention / corrected_clean, 6)
        if denominator["ratio_reportable"]
        and corrected_intervention is not None
        and corrected_clean is not None
        else None
    )
    corrected_payload = {
        "clean_success_rate": (
            round(corrected_clean, 6)
            if corrected_clean is not None
            else None
        ),
        "intervention_success_rate": (
            round(corrected_intervention, 6)
            if corrected_intervention is not None
            else None
        ),
        "absolute_degradation": (
            round(corrected_clean - corrected_intervention, 6)
            if corrected_clean is not None
            and corrected_intervention is not None
            else None
        ),
        "acrs": corrected_acrs,
        "relative_degradation": (
            round(1.0 - corrected_acrs, 6)
            if corrected_acrs is not None
            else None
        ),
        "denominator_policy": denominator,
    }
    return {
        "available": baseline["n_pairs"] > 0,
        "state": (
            "sensitivity_scenario_only"
            if baseline["n_pairs"] > 0
            else "no_complete_pairs"
        ),
        "assumed_false_positive_rate": false_positive_rate,
        "assumed_false_negative_rate": false_negative_rate,
        "assumption_source_required": (
            "blinded human scorer-sanity sample"
        ),
        "baseline": baseline,
        "corrected": corrected_payload,
        "fixture_only_not_evidence": True,
    }


def bca_bootstrap_ci(
    values: Sequence[float],
    *,
    seed: int,
    n_boot: int = 1000,
    alpha: float = 0.05,
    statistic: Callable[[np.ndarray], float] = np.mean,
) -> list[float | None]:
    """Bias-corrected and accelerated (BCa) bootstrap CI for ``statistic``.

    BCa adjusts the percentile interval for median bias (``z0``) and for skew of
    the sampling distribution (acceleration ``a`` from a jackknife), giving more
    accurate coverage than the plain percentile method for the small, skewed
    success-rate samples this benchmark produces. Falls back to the percentile
    interval when the sample is degenerate (n < 2 or a constant statistic).
    """

    from scipy import stats

    arr = np.asarray([float(v) for v in values], dtype=float)
    n = arr.size
    if n < 2:
        return [None, None]
    rng = np.random.default_rng(seed)
    theta_hat = float(statistic(arr))
    boot = np.array(
        [float(statistic(rng.choice(arr, size=n, replace=True))) for _ in range(n_boot)]
    )
    lo_q, hi_q = alpha / 2.0, 1.0 - alpha / 2.0
    proportion_less = float(np.mean(boot < theta_hat))
    if proportion_less <= 0.0 or proportion_less >= 1.0:
        return [round(float(np.quantile(boot, lo_q)), 6), round(float(np.quantile(boot, hi_q)), 6)]
    z0 = float(stats.norm.ppf(proportion_less))
    jackknife = np.array([float(statistic(np.delete(arr, i))) for i in range(n)])
    jack_mean = float(jackknife.mean())
    deviations = jack_mean - jackknife
    denom = 6.0 * float(np.sum(deviations**2)) ** 1.5
    acceleration = float(np.sum(deviations**3) / denom) if denom != 0 else 0.0

    def _adjusted_quantile(z_alpha: float) -> float:
        adjusted = z0 + (z0 + z_alpha) / (1.0 - acceleration * (z0 + z_alpha))
        return float(stats.norm.cdf(adjusted))

    lo_p = _adjusted_quantile(float(stats.norm.ppf(lo_q)))
    hi_p = _adjusted_quantile(float(stats.norm.ppf(hi_q)))
    return [
        round(float(np.quantile(boot, lo_p)), 6),
        round(float(np.quantile(boot, hi_p)), 6),
    ]


def rank_agents(
    agent_scores: dict[str, dict[str, Any]],
    metric: str,
) -> dict[str, int]:
    def _sort_key(agent: str) -> tuple[bool, float, str]:
        # Distinguish a genuinely MISSING metric (None) from a real value of
        # exactly 0.0. The old form `-(value or float("-inf"))` treated 0.0 as
        # falsy and mapped it to +inf, ranking a 0.0 agent below a negative one.
        value = agent_scores[agent].get(metric)
        return (value is None, -value if value is not None else 0.0, agent)

    sorted_agents = sorted(agent_scores, key=_sort_key)
    return {agent: rank + 1 for rank, agent in enumerate(sorted_agents)}


def spearman_from_rankings(a: dict[str, int], b: dict[str, int]) -> float | None:
    agents = sorted(set(a) & set(b))
    n = len(agents)
    if n < 2:
        return None
    from scipy import stats

    result = stats.spearmanr(
        [a[agent] for agent in agents],
        [b[agent] for agent in agents],
    )
    if result.statistic != result.statistic:
        return None
    return round(float(result.statistic), 6)


def ranking_instability(agent_scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    from scipy import stats

    clean_rank = rank_agents(agent_scores, "clean_success_rate")
    acrs_rank = rank_agents(agent_scores, "acrs")
    observed_agents = sorted(
        agent
        for agent, scores in agent_scores.items()
        if scores.get("clean_success_rate") is not None
        and scores.get("acrs") is not None
    )
    clean_tied_rank = _average_ranks(
        {
            agent: agent_scores[agent].get("clean_success_rate")
            for agent in observed_agents
        }
    )
    acrs_tied_rank = _average_ranks(
        {
            agent: agent_scores[agent].get("acrs")
            for agent in observed_agents
        }
    )
    agents = sorted(set(clean_tied_rank) & set(acrs_tied_rank))
    spearman = None
    kendall_tau = None
    if len(agents) >= 2:
        clean_values = [clean_tied_rank[agent] for agent in agents]
        acrs_values = [acrs_tied_rank[agent] for agent in agents]
        if len(set(clean_values)) > 1 and len(set(acrs_values)) > 1:
            spearman_result = stats.spearmanr(clean_values, acrs_values)
            result = stats.kendalltau(
                clean_values,
                acrs_values,
            )
            if spearman_result.statistic == spearman_result.statistic:
                spearman = round(float(spearman_result.statistic), 6)
            if result.statistic == result.statistic:
                kendall_tau = round(float(result.statistic), 6)
    return {
        "clean_success_ranking": clean_rank,
        "acrs_ranking": acrs_rank,
        "clean_success_tied_ranking": clean_tied_rank,
        "acrs_tied_ranking": acrs_tied_rank,
        "spearman_clean_vs_acrs": spearman,
        "kendall_tau_clean_vs_acrs": kendall_tau,
        "rank_delta": {
            agent: _rank_difference(
                acrs_tied_rank.get(agent),
                clean_tied_rank.get(agent),
            )
            for agent in clean_rank
        },
        "rank_comparable_agent_count": len(observed_agents),
        "excluded_agents_missing_metric": sorted(
            set(agent_scores) - set(observed_agents)
        ),
    }


def _bootstrap_pairs(
    pairs: list[dict[str, Any]],
    *,
    seed: int,
    n_boot: int,
    alpha: float,
    resampling_unit: str,
    strata_key: str | None,
    near_zero_threshold: float,
) -> dict[str, Any]:
    if n_boot < 1:
        raise ValueError("n_boot must be >= 1")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    point = _point_estimates(
        pairs,
        near_zero_threshold=near_zero_threshold,
    )
    if not pairs:
        return {
            "point_estimate": point,
            "confidence_intervals": {
                key: [None, None]
                for key in (
                    "clean_success_rate",
                    "intervention_success_rate",
                    "absolute_degradation",
                    "relative_degradation",
                    "acrs",
                    "conditional_robustness_among_clean_successes",
                )
            },
            "n_boot_requested": n_boot,
            "n_boot_valid_by_metric": {},
            "resampling_unit": resampling_unit,
            "strata_key": strata_key,
            "cluster_count": 0,
            "state": "no_complete_pairs",
            "fixture_only_not_evidence": True,
        }

    by_stratum: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for index, pair in enumerate(pairs):
        stratum = (
            str(pair.get(strata_key))
            if strata_key is not None
            else "__all__"
        )
        unit = pair.get(resampling_unit)
        if unit is None:
            if resampling_unit == "pair_id":
                unit = f"pair_index:{index}"
            else:
                raise ValueError(
                    f"pair is missing resampling unit {resampling_unit!r}"
                )
        by_stratum[stratum][str(unit)].append(pair)

    rng = np.random.default_rng(seed)
    boot_values: dict[str, list[float]] = defaultdict(list)
    metric_names = (
        "clean_success_rate",
        "intervention_success_rate",
        "absolute_degradation",
        "relative_degradation",
        "acrs",
        "conditional_robustness_among_clean_successes",
    )
    for _ in range(n_boot):
        sample: list[dict[str, Any]] = []
        for units in by_stratum.values():
            unit_names = sorted(units)
            sampled_units = rng.choice(
                unit_names,
                size=len(unit_names),
                replace=True,
            ).tolist()
            for unit in sampled_units:
                sample.extend(units[str(unit)])
        estimates = _point_estimates(
            sample,
            near_zero_threshold=near_zero_threshold,
        )
        for metric_name in metric_names:
            value = estimates[metric_name]
            if value is not None:
                boot_values[metric_name].append(float(value))
    intervals = {
        metric_name: _percentile_interval(
            boot_values[metric_name],
            alpha=alpha,
        )
        for metric_name in metric_names
    }
    return {
        "point_estimate": point,
        "confidence_intervals": intervals,
        "n_boot_requested": n_boot,
        "n_boot_valid_by_metric": {
            metric_name: len(boot_values[metric_name])
            for metric_name in metric_names
        },
        "resampling_unit": resampling_unit,
        "strata_key": strata_key,
        "cluster_count": len(
            {
                str(pair.get(resampling_unit))
                for pair in pairs
                if pair.get(resampling_unit) is not None
            }
        ),
        "stratum_count": len(by_stratum),
        "state": "ok",
        "fixture_only_not_evidence": True,
    }


def _point_estimates(
    pairs: Sequence[Mapping[str, Any]],
    *,
    near_zero_threshold: float,
) -> dict[str, Any]:
    clean = [float(pair["clean_success"]) for pair in pairs]
    intervention = [
        float(pair["intervention_success"]) for pair in pairs
    ]
    clean_rate = round(float(np.mean(clean)), 6) if clean else None
    intervention_rate = (
        round(float(np.mean(intervention)), 6)
        if intervention
        else None
    )
    denominator = denominator_policy(
        clean_rate,
        n_pairs=len(clean),
        near_zero_threshold=near_zero_threshold,
    )
    score = (
        round(intervention_rate / clean_rate, 6)
        if denominator["ratio_reportable"]
        and intervention_rate is not None
        and clean_rate is not None
        else None
    )
    conditional_values = [
        float(intervention_value)
        for clean_value, intervention_value in zip(
            clean,
            intervention,
            strict=True,
        )
        if clean_value == 1.0
    ]
    conditional = (
        round(float(np.mean(conditional_values)), 6)
        if conditional_values
        else None
    )
    return {
        "n_pairs": len(clean),
        "clean_success_rate": clean_rate,
        "intervention_success_rate": intervention_rate,
        "absolute_degradation": (
            round(clean_rate - intervention_rate, 6)
            if clean_rate is not None
            and intervention_rate is not None
            else None
        ),
        "relative_degradation": (
            round(1.0 - score, 6) if score is not None else None
        ),
        "acrs": score,
        "conditional_robustness_among_clean_successes": conditional,
        "denominator_policy": denominator,
    }


def _ranking_metric(
    pairs: Sequence[Mapping[str, Any]],
    metric: str,
    *,
    near_zero_threshold: float,
) -> float | None:
    estimates = _point_estimates(
        pairs,
        near_zero_threshold=near_zero_threshold,
    )
    aliases = {
        "conditional_robustness": (
            "conditional_robustness_among_clean_successes"
        ),
        "intervention_success": "intervention_success_rate",
    }
    key = aliases.get(metric, metric)
    valid_keys = {
        "acrs",
        "conditional_robustness_among_clean_successes",
        "intervention_success_rate",
        "absolute_degradation",
    }
    if key not in valid_keys:
        raise ValueError(
            "metric must be one of 'acrs', 'conditional_robustness', "
            "'intervention_success_rate', or 'absolute_degradation'"
        )
    if key == "absolute_degradation":
        value = estimates[key]
        return -float(value) if value is not None else None
    value = estimates.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def _validated_pairs(
    pairs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    valid: list[dict[str, Any]] = []
    for pair in pairs:
        if pair.get("completeness_state", "complete") != "complete":
            continue
        clean = pair.get("clean_success")
        intervention = pair.get("intervention_success")
        if clean not in (0, 1, False, True):
            raise ValueError("pair clean_success must be binary")
        if intervention not in (0, 1, False, True):
            raise ValueError("pair intervention_success must be binary")
        valid.append(dict(pair))
    return valid


def _binary_vector(
    values: Sequence[int | bool | float],
    *,
    name: str,
) -> list[int]:
    output: list[int] = []
    for value in values:
        if value not in (0, 1, False, True):
            raise ValueError(f"{name} values must be binary")
        output.append(int(value))
    return output


def _average_ranks(
    scores: Mapping[str, float | None],
) -> dict[str, float | None]:
    observed = {
        agent: float(score)
        for agent, score in scores.items()
        if score is not None
    }
    output: dict[str, float | None] = {
        agent: None for agent, score in scores.items() if score is None
    }
    if not observed:
        return output
    from scipy import stats

    agents = sorted(observed)
    ranks = stats.rankdata(
        [-observed[agent] for agent in agents],
        method="average",
    )
    output.update(
        {
            agent: float(rank)
            for agent, rank in zip(agents, ranks, strict=True)
        }
    )
    return output


def _percentile_interval(
    values: Sequence[float],
    *,
    alpha: float,
) -> list[float | None]:
    if not values:
        return [None, None]
    return [
        round(float(np.quantile(values, alpha / 2.0)), 6),
        round(float(np.quantile(values, 1.0 - alpha / 2.0)), 6),
    ]


def _rank_label(rank: float) -> str:
    return str(int(rank)) if rank.is_integer() else str(rank)


def _pair_support_key(
    pair: Mapping[str, Any],
    *,
    cluster_key: str,
) -> tuple[str, str, str] | None:
    cluster = pair.get(cluster_key)
    intervention = pair.get("intervention_id_or_family") or pair.get(
        "intervention_family"
    )
    repeat = pair.get("repeat_id")
    if cluster is None or intervention is None or repeat is None:
        return None
    return str(cluster), str(intervention), str(repeat)


def _rank_difference(
    robustness_rank: float | None,
    clean_rank: float | None,
) -> float | None:
    if robustness_rank is None or clean_rank is None:
        return None
    return round(float(robustness_rank) - float(clean_rank), 6)
