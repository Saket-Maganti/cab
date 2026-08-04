"""Prospective power and rank-instability calibration.

Everything here is a *planning* simulation over assumed parameters.  None of it
is an empirical finding, none of it licenses a claim, and the module refuses to
describe Compact-20 as anything other than a pilot / feasibility design.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats

PLAN_SCHEMA = "cab_review_ready_v2_power_plan_v1"

COMPACT_STATUS = (
    "PILOT_FEASIBILITY_PROTOCOL_VALIDATION_SCORER_AUDIT_RUNTIME_CALIBRATION_EFFECT_DIRECTION_ONLY"
)
COMPACT_LABEL = "pilot"
CONFIRMATORY_DESIGN = "scale100"

INFERENCE_SCOPE = (
    "Inference applies to the fixed evaluated model panel unless a model-superpopulation "
    "design is separately preregistered."
)

FIXED_PANEL_CLEAN_SUCCESS = (0.72, 0.68, 0.65, 0.61, 0.55)
FAMILIES = ("tool_removal", "tool_failure", "memory_corruption", "observation_conflict")
FAMILY_DEGRADATION_MULTIPLIER = {
    "tool_removal": 1.30,
    "tool_failure": 1.00,
    "memory_corruption": 0.85,
    "observation_conflict": 0.70,
}

# Assumed model x family interaction: every model has its own sensitivity
# profile, and each column averages to the marginal multiplier above. Without a
# true interaction in the data-generating process, "interaction power" would
# merely measure the test's false-positive rate.
MODEL_FAMILY_SENSITIVITY = (
    (1.30, 0.80, 1.05, 0.55),
    (1.55, 1.25, 0.65, 0.60),
    (1.20, 0.85, 1.00, 0.75),
    (1.05, 1.15, 0.70, 0.90),
    (1.40, 0.95, 0.85, 0.70),
)
SESOI_GRID = (0.03, 0.05, 0.08, 0.10, 0.15)
DEGRADATION_REGIMES = {"small": (0.03, 0.05), "medium": (0.08, 0.10), "large": (0.15,)}

DEFAULT_REPLICATES = 2000
DEFAULT_SEED = 20260804
SCORER_NOISE = 0.02
MISSING_TRAJECTORY_RATE = 0.02
ITEM_DIFFICULTY_SD = 0.35
MEANINGFUL_SCORE_GAP = 0.02


def _logit(value: np.ndarray | float) -> np.ndarray:
    clipped = np.clip(value, 1e-6, 1 - 1e-6)
    return np.log(clipped / (1 - clipped))


def _expit(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-value))


def _simulate_panel(
    rng: np.random.Generator,
    *,
    pairs: int,
    mean_degradation: float,
    panel: tuple[float, ...],
    repeats: int = 1,
    interaction: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(clean, intervention, family_index)`` success indicators.

    A shared latent item-difficulty term induces the clean/intervention
    correlation; family multipliers make degradation family-specific; scorer
    noise flips a small fraction of outcomes; missing trajectories are dropped.
    """

    models = len(panel)
    columns = pairs * repeats
    family_index = np.tile(np.arange(pairs) % len(FAMILIES), repeats)
    difficulty = np.tile(rng.normal(0.0, ITEM_DIFFICULTY_SD, size=pairs), repeats)
    if interaction:
        multipliers = np.array(MODEL_FAMILY_SENSITIVITY)[:models][:, family_index]
    else:
        marginal = np.array([FAMILY_DEGRADATION_MULTIPLIER[FAMILIES[i]] for i in family_index])
        multipliers = np.repeat(marginal[None, :], models, axis=0)
    clean_probability = _expit(_logit(np.array(panel))[:, None] - difficulty[None, :])
    intervention_probability = np.clip(clean_probability - mean_degradation * multipliers, 0.0, 1.0)

    clean = rng.random((models, columns)) < clean_probability
    intervention = rng.random((models, columns)) < intervention_probability
    clean = np.where(rng.random((models, columns)) < SCORER_NOISE, ~clean, clean)
    intervention = np.where(rng.random((models, columns)) < SCORER_NOISE, ~intervention, intervention)
    observed = rng.random((models, columns)) >= MISSING_TRAJECTORY_RATE
    return clean & observed, intervention & observed, family_index


def _ranks(scores: np.ndarray) -> np.ndarray:
    return stats.rankdata(-scores, method="average")


def rank_instability_simulation(
    *,
    mean_degradation: float,
    pairs: int = 20,
    replicates: int = DEFAULT_REPLICATES,
    seed: int = DEFAULT_SEED,
    panel: tuple[float, ...] = FIXED_PANEL_CLEAN_SUCCESS,
) -> dict[str, Any]:
    """Probability of a meaningful rank reversal under an assumed degradation."""

    rng = np.random.default_rng(seed)
    reversals = 0
    top_changes = 0
    ties = 0
    spearman: list[float] = []
    kendall: list[float] = []
    max_shift: list[int] = []
    for _ in range(replicates):
        clean, intervention, _ = _simulate_panel(
            rng, pairs=pairs, mean_degradation=mean_degradation, panel=panel
        )
        clean_score = clean.mean(axis=1)
        intervention_score = intervention.mean(axis=1)
        clean_rank = _ranks(clean_score)
        intervention_rank = _ranks(intervention_score)
        if len(set(np.round(intervention_score, 6))) < len(intervention_score):
            ties += 1
        max_shift.append(int(np.abs(clean_rank - intervention_rank).max()))
        # A reversal is *meaningful* when two models swap order and their clean
        # separation was itself larger than the smallest difference we care about.
        order = np.argsort(-clean_score)
        meaningful = False
        for upper in range(len(order)):
            for lower in range(upper + 1, len(order)):
                above, below = order[upper], order[lower]
                if (
                    intervention_score[below] > intervention_score[above]
                    and clean_score[above] - clean_score[below] >= MEANINGFUL_SCORE_GAP
                ):
                    meaningful = True
        reversals += int(meaningful)
        top_changes += int(np.argmax(clean_score) != np.argmax(intervention_score))
        if clean_score.std() > 0 and intervention_score.std() > 0:
            spearman.append(float(stats.spearmanr(clean_rank, intervention_rank).statistic))
            kendall.append(float(stats.kendalltau(clean_rank, intervention_rank).statistic))
    spearman_array = np.nan_to_num(np.array(spearman or [1.0]), nan=1.0)
    kendall_array = np.nan_to_num(np.array(kendall or [1.0]), nan=1.0)
    return {
        "assumed_mean_degradation": mean_degradation,
        "pairs": pairs,
        "replicates": replicates,
        "panel_size": len(panel),
        "probability_of_meaningful_rank_reversal": round(reversals / replicates, 4),
        "probability_of_top_model_identity_change": round(top_changes / replicates, 4),
        "probability_of_tied_intervention_scores": round(ties / replicates, 4),
        "mean_max_rank_shift": round(float(np.mean(max_shift)), 3),
        "spearman_mean": round(float(spearman_array.mean()), 4),
        "spearman_p05": round(float(np.percentile(spearman_array, 5)), 4),
        "kendall_mean": round(float(kendall_array.mean()), 4),
        "kendall_p05": round(float(np.percentile(kendall_array, 5)), 4),
        "is_empirical_finding": False,
    }


def _interaction_statistic(
    drop: np.ndarray, one_hot: np.ndarray, counts: np.ndarray
) -> float:
    """Two-way interaction sum of squares of the model x family degradation table."""

    cell = (drop @ one_hot) / counts
    residual = (
        cell
        - cell.mean(axis=1, keepdims=True)
        - cell.mean(axis=0, keepdims=True)
        + cell.mean()
    )
    return float((residual**2).sum())


def _interaction_rejection_rate(
    *,
    mean_degradation: float,
    pairs: int,
    repeats: int,
    replicates: int,
    permutations: int,
    seed: int,
    alpha: float,
    panel: tuple[float, ...],
    interaction: bool,
) -> float:
    """Permutation test that respects the paired, item-clustered design.

    A chi-square independence test is invalid here: every model sees the same
    items, so their degradation counts are positively correlated and the test is
    badly conservative.  Permuting family labels across items preserves item
    difficulty and each model's overall degradation while destroying only the
    model x family interaction, which is exactly the null of interest.
    """

    rng = np.random.default_rng(seed)
    families = len(FAMILIES)
    rejections = 0
    for _ in range(replicates):
        clean, intervention, family_index = _simulate_panel(
            rng,
            pairs=pairs,
            mean_degradation=mean_degradation,
            panel=panel,
            repeats=repeats,
            interaction=interaction,
        )
        drop = (clean.astype(float) - intervention.astype(float)).clip(min=0)
        one_hot = np.eye(families)[family_index]
        counts = one_hot.sum(axis=0)
        observed = _interaction_statistic(drop, one_hot, counts)
        exceeded = 0
        for _ in range(permutations):
            permuted = np.eye(families)[rng.permutation(family_index)]
            if _interaction_statistic(drop, permuted, permuted.sum(axis=0)) >= observed:
                exceeded += 1
        pvalue = (1 + exceeded) / (1 + permutations)
        rejections += int(pvalue < alpha)
    return rejections / replicates if replicates else 0.0


def interaction_power(
    *,
    mean_degradation: float,
    pairs: int = 100,
    repeats: int = 3,
    replicates: int = 200,
    permutations: int = 199,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
    panel: tuple[float, ...] = FIXED_PANEL_CLEAN_SUCCESS,
) -> dict[str, Any]:
    """Power for the model x family interaction under the assumed profiles.

    The companion null rejection rate is reported so the number reads as a real
    power estimate rather than an artefact: under a no-interaction
    data-generating process the same test must reject at about ``alpha``.
    """

    power = _interaction_rejection_rate(
        mean_degradation=mean_degradation,
        pairs=pairs,
        repeats=repeats,
        replicates=replicates,
        permutations=permutations,
        seed=seed + 7,
        alpha=alpha,
        panel=panel,
        interaction=True,
    )
    null_rate = _interaction_rejection_rate(
        mean_degradation=mean_degradation,
        pairs=pairs,
        repeats=repeats,
        replicates=replicates,
        permutations=permutations,
        seed=seed + 4242,
        alpha=alpha,
        panel=panel,
        interaction=False,
    )
    return {
        "assumed_mean_degradation": mean_degradation,
        "pairs": pairs,
        "repeats_per_pair": repeats,
        "replicates": replicates,
        "permutations": permutations,
        "test": "within-design permutation of family labels across items",
        "alpha": alpha,
        "estimated_power": round(power, 4),
        "null_rejection_rate": round(null_rate, 4),
        "test_calibrated_under_null": null_rate <= alpha + 0.04,
        "meets_confirmatory_adequacy": power >= 0.80,
        "designation": "confirmatory" if power >= 0.80 else "secondary_exploratory",
        "is_empirical_finding": False,
    }


def paired_degradation_power(
    *,
    mean_degradation: float,
    pairs: int = 100,
    repeats: int = 1,
    replicates: int = 400,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
    panel: tuple[float, ...] = FIXED_PANEL_CLEAN_SUCCESS,
) -> dict[str, Any]:
    """Power for the primary paired clean-vs-intervention degradation estimand.

    Two variants are reported: the panel-average degradation, and the stricter
    conjunctive claim that degradation is present for *every* member of the fixed
    panel (Bonferroni-corrected across the five models).
    """

    rng = np.random.default_rng(seed + 11)
    models = len(panel)
    panel_hits = 0
    conjunctive_hits = 0
    for _ in range(replicates):
        clean, intervention, _ = _simulate_panel(
            rng, pairs=pairs, mean_degradation=mean_degradation, panel=panel, repeats=repeats
        )
        difference = clean.astype(float) - intervention.astype(float)
        pooled = difference.mean(axis=0)
        panel_hits += int(
            pooled.std(ddof=1) > 0
            and stats.ttest_1samp(pooled, 0.0, alternative="greater").pvalue < alpha
        )
        per_model = [
            stats.ttest_1samp(row, 0.0, alternative="greater").pvalue
            if row.std(ddof=1) > 0
            else 1.0
            for row in difference
        ]
        conjunctive_hits += int(max(per_model) < alpha / models)
    return {
        "assumed_mean_degradation": mean_degradation,
        "pairs": pairs,
        "repeats_per_pair": repeats,
        "replicates": replicates,
        "alpha": alpha,
        "panel_average_power": round(panel_hits / replicates, 4),
        "every_model_degrades_power": round(conjunctive_hits / replicates, 4),
        "meets_confirmatory_adequacy": panel_hits / replicates >= 0.80,
        "is_empirical_finding": False,
    }


def sesoi_sensitivity(
    *, pairs: int = 20, replicates: int = 800, seed: int = DEFAULT_SEED
) -> list[dict[str, Any]]:
    return [
        rank_instability_simulation(
            mean_degradation=value, pairs=pairs, replicates=replicates, seed=seed + index
        )
        for index, value in enumerate(SESOI_GRID)
    ]


def build_power_plan(*, replicates: int = 800) -> dict[str, Any]:
    """Deterministic prospective power plan for the reviewer-ready design."""

    compact = sesoi_sensitivity(pairs=20, replicates=replicates)
    scale = [
        rank_instability_simulation(
            mean_degradation=value, pairs=100, replicates=replicates, seed=DEFAULT_SEED + 100 + index
        )
        for index, value in enumerate(SESOI_GRID)
    ]
    interaction = [
        interaction_power(
            mean_degradation=value,
            pairs=100,
            repeats=3,
            replicates=max(replicates // 6, 120),
            permutations=199,
        )
        for value in SESOI_GRID
    ]
    adequate = [row for row in interaction if row["meets_confirmatory_adequacy"]]
    # Noise floor: how often the leaderboard "reverses" with no degradation at
    # all. Without this, a high reversal probability could be read as an effect
    # when it is only sampling noise on a closely spaced panel.
    compact_floor = rank_instability_simulation(
        mean_degradation=0.0, pairs=20, replicates=replicates, seed=DEFAULT_SEED + 900
    )
    scale_floor = rank_instability_simulation(
        mean_degradation=0.0, pairs=100, replicates=replicates, seed=DEFAULT_SEED + 901
    )
    compact_excess = round(
        compact[-1]["probability_of_meaningful_rank_reversal"]
        - compact_floor["probability_of_meaningful_rank_reversal"],
        4,
    )
    scale_excess = round(
        scale[-1]["probability_of_meaningful_rank_reversal"]
        - scale_floor["probability_of_meaningful_rank_reversal"],
        4,
    )
    regimes = {
        name: {
            "assumed_mean_degradations": list(values),
            "compact20_reversal_probability": [
                row["probability_of_meaningful_rank_reversal"]
                for row in compact
                if row["assumed_mean_degradation"] in values
            ],
            "scale100_reversal_probability": [
                row["probability_of_meaningful_rank_reversal"]
                for row in scale
                if row["assumed_mean_degradation"] in values
            ],
        }
        for name, values in DEGRADATION_REGIMES.items()
    }
    degradation = [
        paired_degradation_power(mean_degradation=value, pairs=100, replicates=max(replicates // 3, 200))
        for value in SESOI_GRID
    ]
    degradation_compact = [
        paired_degradation_power(mean_degradation=value, pairs=20, replicates=max(replicates // 3, 200))
        for value in SESOI_GRID
    ]
    powered_from = [
        row["assumed_mean_degradation"] for row in degradation if row["meets_confirmatory_adequacy"]
    ]
    return {
        "schema_version": PLAN_SCHEMA,
        "status": "CAB_POWER_PLAN_CALIBRATED",
        "primary_confirmatory_estimand": {
            "name": "paired clean-vs-intervention degradation on the fixed model panel",
            "design": "scale100",
            "scale100_grid": degradation,
            "compact20_grid": degradation_compact,
            "adequately_powered_at_degradations": powered_from,
            "designation": "confirmatory" if powered_from else "underpowered",
            "inference_scope": INFERENCE_SCOPE,
        },
        "compact20": {
            "label": COMPACT_LABEL,
            "status": COMPACT_STATUS,
            "confirmatory": False,
            "adequately_powered_for_broad_claims": False,
            "purposes": [
                "feasibility",
                "protocol_validation",
                "scorer_audit_basis",
                "runtime_and_resource_calibration",
                "effect_direction_exploration",
            ],
            "rank_instability_sensitivity": compact,
        },
        "scale100": {
            "label": "primary_confirmatory",
            "confirmatory": True,
            "inference_scope": INFERENCE_SCOPE,
            "model_superpopulation_design_preregistered": False,
            "rank_instability_sensitivity": scale,
        },
        "rank_instability_claim": {
            "estimand": "probability of at least one meaningful rank reversal between clean and intervention leaderboards on a fixed five-model panel",
            "meaningful_reversal_definition": {
                "min_rank_shift": 1,
                "min_absolute_score_gap": MEANINGFUL_SCORE_GAP,
            },
            "prospectively_calibrated": True,
            "regimes": regimes,
            "noise_floor": {
                "compact20_zero_degradation_reversal_probability": compact_floor[
                    "probability_of_meaningful_rank_reversal"
                ],
                "scale100_zero_degradation_reversal_probability": scale_floor[
                    "probability_of_meaningful_rank_reversal"
                ],
                "compact20_excess_over_floor_at_largest_effect": compact_excess,
                "scale100_excess_over_floor_at_largest_effect": scale_excess,
            },
            "calibration_warning": (
                "On this closely spaced five-model panel the raw reversal probability is dominated "
                "by sampling noise: it is already high with zero degradation. The raw probability "
                "is therefore NOT a usable estimand. Any rank-instability claim must be stated as "
                "excess over the matched zero-degradation noise floor, and Compact-20 must not be "
                "used for it at all."
            ),
            "raw_reversal_probability_is_a_usable_estimand": False,
            "excess_over_noise_floor_discriminates_at_scale100": scale_excess >= 0.10,
        },
        "model_family_interaction": {
            "designation": "confirmatory" if adequate else "secondary_exploratory",
            "reason": (
                "Power reaches the 0.80 confirmatory bar only at the assumed degradations listed "
                "below; the interaction is therefore designated secondary/exploratory for every "
                "other regime."
                if not adequate
                else "Power meets the 0.80 confirmatory bar across the examined grid."
            ),
            "adequate_at_degradations": [row["assumed_mean_degradation"] for row in adequate],
            "grid": interaction,
        },
        "simulation_parameters": {
            "fixed_panel_clean_success": list(FIXED_PANEL_CLEAN_SUCCESS),
            "family_degradation_multipliers": FAMILY_DEGRADATION_MULTIPLIER,
            "model_family_sensitivity_matrix": [list(row) for row in MODEL_FAMILY_SENSITIVITY],
            "scorer_noise_rate": SCORER_NOISE,
            "missing_trajectory_rate": MISSING_TRAJECTORY_RATE,
            "item_difficulty_sd": ITEM_DIFFICULTY_SD,
            "sesoi_grid": list(SESOI_GRID),
            "seed": DEFAULT_SEED,
            "deterministic": True,
        },
        "separation_of_claims": {
            "planning_assumptions": [
                "fixed five-model panel clean success rates",
                "family-specific degradation multipliers",
                "scorer noise and missing-trajectory rates",
            ],
            "powered_estimands": ["clean-vs-intervention paired degradation on Scale-100"],
            "exploratory_estimands": [
                "model x family interaction",
                "Compact-20 effect direction",
                "rank instability, reported only as excess over the matched noise floor",
            ],
            "unsupported_generalizations": [
                "any statement about LLM agents in general rather than the evaluated panel",
                "any claim that Compact-20 is confirmatory",
                "any raw rank-reversal probability reported without its matched noise floor",
            ],
        },
        "empirical_results_present": False,
        "genuine_model_trajectories": 0,
    }


__all__ = [
    "COMPACT_LABEL",
    "COMPACT_STATUS",
    "CONFIRMATORY_DESIGN",
    "DEGRADATION_REGIMES",
    "FIXED_PANEL_CLEAN_SUCCESS",
    "INFERENCE_SCOPE",
    "MODEL_FAMILY_SENSITIVITY",
    "PLAN_SCHEMA",
    "SESOI_GRID",
    "build_power_plan",
    "interaction_power",
    "paired_degradation_power",
    "rank_instability_simulation",
    "sesoi_sensitivity",
]
