from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from causal_agent_bench.analysis.load_results import RunResults
from causal_agent_bench.metrics.causal_robustness import (
    matched_pair_outcomes,
    summarize_complete_pairs,
)
from causal_agent_bench.metrics.statistics import (
    adjust_pvalues,
    bca_bootstrap_ci,
    cliffs_delta,
    clustered_paired_bootstrap,
    paired_binary_test,
    paired_bootstrap,
    paired_effect_sizes,
    rank_bootstrap,
    stratified_paired_bootstrap,
)
from causal_agent_bench.utils.io import write_json

MIN_PAIRED_TASKS = 20
MIN_FAMILY_ROWS = 20
MANY_FAMILIES_THRESHOLD = 5


def build_statistical_report(data: RunResults, output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = statistical_report(data)
    json_path = out / "stats_summary.json"
    md_path = out / "stats_summary.md"
    write_json(json_path, summary)
    md_path.write_text(statistical_report_markdown(summary), encoding="utf-8")
    return [json_path, md_path]


def statistical_report(data: RunResults, *, seed: int = 12345) -> dict[str, Any]:
    scores = data.scores_df.copy()
    if scores.empty:
        return {
            "schema_version": "stats_summary_v1",
            "paired_clean_vs_intervention": [],
            "family_bootstrap": [],
            "agent_bootstrap": [],
            "rank_correlation": {},
            "rank_uncertainty": {},
            "scorer_sensitivity": {
                "state": "HUMAN_INPUT_REQUIRED",
                "reason": "no score records available",
            },
            "warnings": ["no score records available"],
            "evidence_class": "FIXTURE_ONLY",
            "scientific_evidence": False,
        }
    scores = _with_base_task_id(scores)
    paired = paired_clean_intervention_tests(scores, seed=seed)
    family = intervention_family_bootstrap(scores, seed=seed + 1)
    agent = agent_level_bootstrap(scores, seed=seed + 2)
    warnings = statistical_warnings(scores, paired, family)
    ledgers = _pair_ledgers(scores)
    complete_pairs = [
        pair
        for ledger in ledgers.values()
        for pair in ledger["complete_pairs"]
    ]
    rank_uncertainty = rank_bootstrap(
        complete_pairs,
        seed=seed + 3,
    )
    return {
        "schema_version": "stats_summary_v2_paired",
        "paired_clean_vs_intervention": paired,
        "family_bootstrap": family,
        "agent_bootstrap": agent,
        "multiple_comparison_correction": multiple_comparison_correction(paired),
        "rank_correlation": data.aggregate.get("ranking_instability", {}),
        "rank_uncertainty": rank_uncertainty,
        "rank_probability_matrix": rank_uncertainty.get(
            "pairwise_rank_probability_matrix",
            {},
        ),
        "scorer_sensitivity": {
            "state": "HUMAN_INPUT_REQUIRED",
            "reason": (
                "No validated scorer false-positive/false-negative rates are "
                "available. Use metrics.statistics.scorer_error_sensitivity "
                "only with rates estimated from blinded human review."
            ),
            "scientific_evidence": False,
        },
        "pseudoreplication": {
            "intervention_pair_count": len(complete_pairs),
            "unique_base_task_count": len(
                {pair["base_task_id"] for pair in complete_pairs}
            ),
            "template_count": len(
                {
                    pair["template_id"]
                    for pair in complete_pairs
                    if pair.get("template_id") is not None
                }
            ),
            "domain_count": len(
                {
                    pair["domain"]
                    for pair in complete_pairs
                    if pair.get("domain") is not None
                }
            ),
            "family_count": len(
                {
                    pair["intervention_family"]
                    for pair in complete_pairs
                }
            ),
            "clustering_unit": "base_task_id",
        },
        "effect_sizes": {
            "absolute_degradation": [
                {
                    "agent": row["agent"],
                    "n_pairs": row["n_pairs"],
                    "absolute_degradation": row["absolute_degradation"],
                    "cohen_dz": row["cohen_dz"],
                    "matched_rank_biserial": row[
                        "matched_rank_biserial"
                    ],
                    "matched_odds_ratio": row["matched_odds_ratio"],
                }
                for row in paired
            ],
            "per_family_degradation": [
                {
                    "agent": row["agent"],
                    "intervention_family": row["intervention_family"],
                    "absolute_degradation": row["absolute_degradation"],
                    "relative_degradation": row["relative_degradation"],
                }
                for row in family
            ],
        },
        "warnings": warnings,
        "scope": (
            "Fixture-safe paired statistical summary. It is not scientific "
            "evidence without completed runs, validated scoring, and evidence gates."
        ),
        "evidence_class": "FIXTURE_ONLY",
        "scientific_evidence": False,
    }


def paired_clean_intervention_tests(
    scores: pd.DataFrame,
    *,
    seed: int = 0,
    n_boot: int = 1000,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (agent, ledger) in enumerate(_pair_ledgers(scores).items()):
        pairs = ledger["complete_pairs"]
        if not pairs:
            rows.append(
                _empty_pair_row(
                    str(agent),
                    pairing_summary=ledger["pairing_summary"],
                )
            )
            continue
        summary = summarize_complete_pairs(pairs)
        clean = pd.Series(
            [pair["clean_success"] for pair in pairs],
            dtype=float,
        )
        intervention = pd.Series(
            [pair["intervention_success"] for pair in pairs],
            dtype=float,
        )
        diff = clean - intervention
        effects = paired_effect_sizes(clean.tolist(), intervention.tolist())
        binary_test = paired_binary_test(
            clean.tolist(),
            intervention.tolist(),
        )
        row_bootstrap = paired_bootstrap(
            pairs,
            seed=seed + index,
            n_boot=n_boot,
        )
        cluster_bootstrap = clustered_paired_bootstrap(
            pairs,
            seed=seed + 1000 + index,
            n_boot=n_boot,
        )
        stratified_bootstrap = stratified_paired_bootstrap(
            pairs,
            seed=seed + 2000 + index,
            n_boot=n_boot,
        )
        ci_bca = bca_bootstrap_ci(
            diff.tolist(),
            seed=seed + 5000 + index,
            n_boot=n_boot,
        )
        rows.append(
            {
                "agent": str(agent),
                "n_pairs": len(pairs),
                "unique_base_task_count": summary[
                    "unique_base_task_count"
                ],
                "mean_clean": summary["clean_success_rate"],
                "mean_intervention": summary[
                    "intervention_success_rate"
                ],
                "absolute_degradation": summary[
                    "absolute_degradation"
                ],
                "relative_degradation": summary[
                    "relative_degradation"
                ],
                "acrs": summary["acrs"],
                "conditional_robustness_among_clean_successes": summary[
                    "conditional_robustness_among_clean_successes"
                ],
                "conditional_degradation_among_clean_successes": summary[
                    "conditional_degradation_among_clean_successes"
                ],
                "transition_profile": summary["transition_profile"],
                "denominator_policy": summary["denominator_policy"],
                "cohen_dz": effects["cohen_dz"],
                "matched_rank_biserial": effects[
                    "matched_rank_biserial"
                ],
                "matched_odds_ratio": effects["matched_odds_ratio"],
                "cliffs_delta": cliffs_delta(
                    clean.tolist(),
                    intervention.tolist(),
                ),
                "paired_t_p_value": _paired_t(clean, intervention),
                "wilcoxon_p_value": _wilcoxon(clean, intervention),
                "paired_binary_test": binary_test,
                "mcnemar_exact_p_value": binary_test["p_value"],
                # The headline CI is cluster-aware. Pair-level and
                # family-stratified versions remain visible as sensitivity
                # analyses.
                "bootstrap_ci": {
                    "absolute_degradation": cluster_bootstrap[
                        "confidence_intervals"
                    ]["absolute_degradation"],
                    "acrs": cluster_bootstrap[
                        "confidence_intervals"
                    ]["acrs"],
                },
                "paired_bootstrap": row_bootstrap,
                "clustered_bootstrap": cluster_bootstrap,
                "stratified_bootstrap": stratified_bootstrap,
                "bootstrap_ci_bca": {"absolute_degradation": ci_bca},
                "pairing_summary": ledger["pairing_summary"],
                "invalid_pair_count": len(ledger["invalid_pairs"]),
                "invalid_pairs": ledger["invalid_pairs"],
                "clustering_unit": "base_task_id",
                "evidence_class": "FIXTURE_ONLY",
                "scientific_evidence": False,
            }
        )
    return rows


def intervention_family_bootstrap(
    scores: pd.DataFrame,
    *,
    seed: int = 0,
    n_boot: int = 1000,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for agent, ledger in _pair_ledgers(scores).items():
        by_family: dict[str, list[dict[str, Any]]] = {}
        for pair in ledger["complete_pairs"]:
            by_family.setdefault(
                str(pair["intervention_family"]),
                [],
            ).append(pair)
        for family, family_pairs in sorted(by_family.items()):
            summary = summarize_complete_pairs(family_pairs)
            bootstrap = clustered_paired_bootstrap(
                family_pairs,
                seed=seed + len(rows),
                n_boot=n_boot,
            )
            rows.append(
                {
                    "agent": str(agent),
                    "intervention_family": str(family),
                    "n": len(family_pairs),
                    "unique_base_task_count": summary[
                        "unique_base_task_count"
                    ],
                    # This is the exact clean subset corresponding to this
                    # family's interventions, not the agent-global clean mean.
                    "clean_success": summary["clean_success_rate"],
                    "family_success": summary[
                        "intervention_success_rate"
                    ],
                    "acrs_family": summary["acrs"],
                    "absolute_degradation": summary[
                        "absolute_degradation"
                    ],
                    "relative_degradation": summary[
                        "relative_degradation"
                    ],
                    "conditional_robustness_among_clean_successes": summary[
                        "conditional_robustness_among_clean_successes"
                    ],
                    "transition_profile": summary["transition_profile"],
                    "denominator_policy": summary[
                        "denominator_policy"
                    ],
                    "success_ci": bootstrap["confidence_intervals"][
                        "intervention_success_rate"
                    ],
                    "degradation_ci": bootstrap[
                        "confidence_intervals"
                    ]["absolute_degradation"],
                    "acrs_ci": bootstrap["confidence_intervals"]["acrs"],
                    "clustered_bootstrap": bootstrap,
                    "clean_denominator_scope": (
                        "exact_corresponding_base_task_repeat_subset"
                    ),
                    "clustering_unit": "base_task_id",
                    "evidence_class": "FIXTURE_ONLY",
                    "scientific_evidence": False,
                }
            )
    return rows


def agent_level_bootstrap(
    scores: pd.DataFrame,
    *,
    seed: int = 0,
    n_boot: int = 1000,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (agent, ledger) in enumerate(_pair_ledgers(scores).items()):
        pairs = ledger["complete_pairs"]
        summary = summarize_complete_pairs(pairs)
        bootstrap = clustered_paired_bootstrap(
            pairs,
            seed=seed + index,
            n_boot=n_boot,
        )
        intervals = bootstrap["confidence_intervals"]
        rows.append(
            {
                "agent": str(agent),
                "n_pairs": len(pairs),
                "unique_base_task_count": summary[
                    "unique_base_task_count"
                ],
                "clean_success": summary["clean_success_rate"],
                "clean_success_ci": intervals["clean_success_rate"],
                "intervention_success": summary[
                    "intervention_success_rate"
                ],
                "intervention_success_ci": intervals[
                    "intervention_success_rate"
                ],
                "acrs": summary["acrs"],
                "acrs_ci": intervals["acrs"],
                "absolute_degradation": summary[
                    "absolute_degradation"
                ],
                "absolute_degradation_ci": intervals[
                    "absolute_degradation"
                ],
                "conditional_robustness_among_clean_successes": summary[
                    "conditional_robustness_among_clean_successes"
                ],
                "conditional_robustness_ci": intervals[
                    "conditional_robustness_among_clean_successes"
                ],
                "macro_acrs": summary["macro_acrs"],
                "micro_acrs": summary["micro_acrs"],
                "worst_family_robustness": summary[
                    "worst_family_robustness"
                ],
                "clustered_bootstrap": bootstrap,
                "pairing_summary": ledger["pairing_summary"],
                "invalid_pair_count": len(ledger["invalid_pairs"]),
                "clustering_unit": "base_task_id",
                "evidence_class": "FIXTURE_ONLY",
                "scientific_evidence": False,
            }
        )
    return rows


def multiple_comparison_correction(
    paired_rows: list[dict[str, Any]],
    *,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Holm-Bonferroni and Benjamini-Hochberg adjusted p-values across agents.

    The benchmark reports paired t, Wilcoxon, and exact McNemar tests per agent,
    so reported p-values are subject to multiplicity. Holm controls family-wise
    error and Benjamini-Hochberg controls false discovery rate.
    """

    tests: list[dict[str, Any]] = []
    for row in paired_rows:
        for test_name in (
            "paired_t_p_value",
            "wilcoxon_p_value",
            "mcnemar_exact_p_value",
        ):
            tests.append(
                {"agent": row["agent"], "test": test_name, "p_value": row.get(test_name)}
            )
    p_values = [test["p_value"] for test in tests]
    holm = adjust_pvalues(p_values, method="holm")
    benjamini_hochberg = adjust_pvalues(p_values, method="bh")
    for test, holm_p, bh_p in zip(tests, holm, benjamini_hochberg, strict=True):
        test["holm_adjusted_p_value"] = holm_p
        test["benjamini_hochberg_adjusted_p_value"] = bh_p
        test["significant_holm"] = holm_p is not None and holm_p <= alpha
    return {
        "alpha": alpha,
        "n_tests": sum(1 for p in p_values if p is not None),
        "methods": ["holm", "benjamini_hochberg"],
        "tests": tests,
    }


def statistical_warnings(
    scores: pd.DataFrame,
    paired_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
) -> list[str]:
    warnings = []
    families = sorted(
        str(value)
        for value in scores.get("diagnostic_intervention_family", pd.Series(dtype=object)).dropna().unique()
    )
    if len(families) > MANY_FAMILIES_THRESHOLD:
        warnings.append(
            f"multiple comparisons: {len(families)} intervention families tested; treat uncorrected p-values as descriptive"
        )
    for row in paired_rows:
        if row.get("n_pairs", 0) < MIN_PAIRED_TASKS:
            warnings.append(
                f"minimum sample-size warning: {row.get('agent')} has only {row.get('n_pairs')} paired base tasks"
            )
        if row.get("invalid_pair_count", 0):
            warnings.append(
                f"pair-completeness warning: {row.get('agent')} has "
                f"{row.get('invalid_pair_count')} invalid or incomplete pair unit(s)"
            )
        denominator = row.get("denominator_policy", {})
        if denominator.get("state") not in {None, "stable"}:
            warnings.append(
                f"denominator warning: {row.get('agent')} ACRS is "
                f"{denominator.get('state')} and is not reportable"
            )
        if row.get("n_pairs", 0) > row.get(
            "unique_base_task_count",
            row.get("n_pairs", 0),
        ):
            warnings.append(
                f"pseudoreplication warning: {row.get('agent')} has "
                f"{row.get('n_pairs')} intervention pairs over "
                f"{row.get('unique_base_task_count')} unique base tasks; "
                "use base-task clustered intervals"
            )
    for row in family_rows:
        if row.get("n", 0) < MIN_FAMILY_ROWS:
            warnings.append(
                f"minimum family-size warning: {row.get('agent')} / {row.get('intervention_family')} has n={row.get('n')}"
            )
    if scores["agent_name"].nunique() < 2:
        warnings.append("rank correlation warning: fewer than two agents")
    return warnings


def statistical_report_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Statistical Summary",
        "",
        "This report is descriptive until final experiments and validation are complete.",
        "",
        "## Paired Clean vs Intervention",
        "",
        "| Agent | Pairs | Clean | Intervention | Abs degradation | Rel degradation | ACRS | paired t p | Wilcoxon p |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.get("paired_clean_vs_intervention", []):
        lines.append(
            f"| `{row['agent']}` | {row['n_pairs']} | {_fmt(row['mean_clean'])} | {_fmt(row['mean_intervention'])} | {_fmt(row['absolute_degradation'])} | {_fmt(row['relative_degradation'])} | {_fmt(row['acrs'])} | {_fmt(row['paired_t_p_value'])} | {_fmt(row['wilcoxon_p_value'])} |"
        )
    rank = summary.get("rank_correlation", {})
    lines.extend(
        [
            "",
            "## Rank Correlation",
            "",
            f"- Spearman clean-success vs ACRS: `{rank.get('spearman_clean_vs_acrs')}`",
            f"- Kendall tau clean-success vs ACRS: `{rank.get('kendall_tau_clean_vs_acrs')}`",
        ]
    )
    correction = summary.get("multiple_comparison_correction")
    if correction and correction.get("tests"):
        lines.extend(
            [
                "",
                "## Multiple-comparison correction",
                "",
                f"Adjusted across {correction.get('n_tests')} paired test(s) "
                f"(alpha={correction.get('alpha')}).",
                "",
                "| Agent | Test | Raw p | Holm p | BH p | Sig (Holm) |",
                "|---|---|---:|---:|---:|:--:|",
            ]
        )
        for test in correction["tests"]:
            sig = "✓" if test.get("significant_holm") else ""
            lines.append(
                f"| `{test['agent']}` | {test['test']} | {_fmt(test['p_value'])} | "
                f"{_fmt(test['holm_adjusted_p_value'])} | "
                f"{_fmt(test['benjamini_hochberg_adjusted_p_value'])} | {sig} |"
            )
    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )
    warnings = summary.get("warnings", [])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def _empty_pair_row(
    agent: str,
    *,
    pairing_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pairing_summary = pairing_summary or {}
    return {
        "agent": agent,
        "n_pairs": 0,
        "unique_base_task_count": 0,
        "mean_clean": None,
        "mean_intervention": None,
        "absolute_degradation": None,
        "relative_degradation": None,
        "acrs": None,
        "conditional_robustness_among_clean_successes": None,
        "conditional_degradation_among_clean_successes": None,
        "transition_profile": {},
        "denominator_policy": {
            "state": "missing_clean_condition",
            "ratio_reportable": False,
            "near_zero_threshold": 0.05,
            "n_pairs": 0,
        },
        "cohen_dz": None,
        "matched_rank_biserial": None,
        "matched_odds_ratio": None,
        "cliffs_delta": None,
        "paired_t_p_value": None,
        "wilcoxon_p_value": None,
        "paired_binary_test": {
            "test": "exact_mcnemar_binomial",
            "n_pairs": 0,
            "discordant_pair_count": 0,
            "p_value": None,
            "test_state": "undefined_no_discordant_pairs",
        },
        "mcnemar_exact_p_value": None,
        "bootstrap_ci": {"absolute_degradation": [None, None], "acrs": [None, None]},
        "paired_bootstrap": {},
        "clustered_bootstrap": {},
        "stratified_bootstrap": {},
        "bootstrap_ci_bca": {"absolute_degradation": [None, None]},
        "pairing_summary": pairing_summary,
        "invalid_pair_count": pairing_summary.get(
            "invalid_pair_count",
            0,
        ),
        "invalid_pairs": [],
        "clustering_unit": "base_task_id",
        "evidence_class": "FIXTURE_ONLY",
        "scientific_evidence": False,
    }


def _with_base_task_id(scores: pd.DataFrame) -> pd.DataFrame:
    if "base_task_id" in scores.columns:
        return scores
    normalized = scores.copy()
    if "diagnostic_base_task_id" in normalized.columns:
        normalized["base_task_id"] = normalized["diagnostic_base_task_id"]
    else:
        normalized["base_task_id"] = normalized["instance_id"]
    return normalized


def _pair_ledgers(scores: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Convert flattened score rows to the canonical matched-pair ledger."""

    normalized = _with_base_task_id(scores)
    return matched_pair_outcomes(
        normalized.to_dict(orient="records"),
        evidence_class="FIXTURE_ONLY",
    )


def _paired_t(clean: pd.Series, intervention: pd.Series) -> float | None:
    if len(clean) <= 1:
        return None
    diff = clean - intervention
    if diff.std(ddof=1) == 0:
        return None
    result = stats.ttest_rel(clean, intervention)
    return _round(float(result.pvalue)) if result.pvalue == result.pvalue else None


def _wilcoxon(clean: pd.Series, intervention: pd.Series) -> float | None:
    if len(clean) <= 1 or (clean - intervention).abs().sum() == 0:
        return None
    try:
        result = stats.wilcoxon(clean, intervention)
    except ValueError:
        return None
    return _round(float(result.pvalue)) if result.pvalue == result.pvalue else None


def _bootstrap_paired_ci(
    joined: pd.DataFrame,
    *,
    seed: int,
    n_boot: int,
) -> dict[str, list[float | None]]:
    if joined.empty:
        return {"absolute_degradation": [None, None], "acrs": [None, None]}
    rng = np.random.default_rng(seed)
    diffs = []
    ratios = []
    indices = np.arange(len(joined))
    for _ in range(n_boot):
        sample = joined.iloc[rng.choice(indices, size=len(indices), replace=True)]
        clean_mean = float(sample["clean"].mean())
        intervention_mean = float(sample["intervention"].mean())
        diffs.append(clean_mean - intervention_mean)
        if clean_mean:
            ratios.append(intervention_mean / clean_mean)
    return {
        "absolute_degradation": _quantile_ci(diffs),
        "acrs": _quantile_ci(ratios),
    }


def _bootstrap_mean_ci(values: list[float], *, seed: int, n_boot: int) -> list[float | None]:
    if not values:
        return [None, None]
    rng = np.random.default_rng(seed)
    array = np.asarray(values, dtype=float)
    means = [float(rng.choice(array, size=array.size, replace=True).mean()) for _ in range(n_boot)]
    return _quantile_ci(means)


def _bootstrap_difference_ci(
    clean_values: list[float],
    intervention_values: list[float],
    *,
    seed: int,
    n_boot: int,
) -> list[float | None]:
    if not clean_values or not intervention_values:
        return [None, None]
    rng = np.random.default_rng(seed)
    clean = np.asarray(clean_values, dtype=float)
    intervention = np.asarray(intervention_values, dtype=float)
    diffs = [
        float(rng.choice(clean, size=clean.size, replace=True).mean())
        - float(rng.choice(intervention, size=intervention.size, replace=True).mean())
        for _ in range(n_boot)
    ]
    return _quantile_ci(diffs)


def _bootstrap_ratio_ci(
    intervention_values: list[float],
    clean_values: list[float],
    *,
    seed: int,
    n_boot: int,
) -> list[float | None]:
    if not clean_values or not intervention_values:
        return [None, None]
    rng = np.random.default_rng(seed)
    clean = np.asarray(clean_values, dtype=float)
    intervention = np.asarray(intervention_values, dtype=float)
    ratios = []
    for _ in range(n_boot):
        clean_mean = float(rng.choice(clean, size=clean.size, replace=True).mean())
        if clean_mean:
            ratios.append(float(rng.choice(intervention, size=intervention.size, replace=True).mean()) / clean_mean)
    return _quantile_ci(ratios)


def _quantile_ci(values: list[float]) -> list[float | None]:
    if not values:
        return [None, None]
    return [
        _round(float(np.quantile(values, 0.025))),
        _round(float(np.quantile(values, 0.975))),
    ]


def _numeric(series: pd.Series) -> list[float]:
    return [float(value) for value in series if pd.notna(value)]


def _mean(values: list[float]) -> float | None:
    return _round(float(np.mean(values))) if values else None


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if denominator is None or denominator == 0.0 or numerator is None:
        return None
    return _round(numerator / denominator)


def _round(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
