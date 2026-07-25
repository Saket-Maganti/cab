from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from statistics import mean
from typing import Any


def rate(values: Sequence[float | int | bool | None]) -> float | None:
    observed = [float(value) for value in values if value is not None]
    return round(mean(observed), 6) if observed else None


def acrs_ratio(intervention_success: float | None, clean_success: float | None) -> float | None:
    if clean_success is None or intervention_success is None or clean_success == 0.0:
        return None
    return round(intervention_success / clean_success, 6)


def degradation_metrics(clean_success: float | None, intervention_success: float | None) -> dict[str, float | None]:
    score = acrs_ratio(intervention_success, clean_success)
    absolute = (
        round(clean_success - intervention_success, 6)
        if clean_success is not None and intervention_success is not None
        else None
    )
    relative = round(1.0 - score, 6) if score is not None else None
    return {
        "acrs": score,
        "absolute_degradation": absolute,
        "relative_degradation": relative,
    }


def family_acrs(
    rows: list[dict[str, Any]],
    *,
    success_key: str = "success",
    condition_key: str = "condition",
    family_key: str = "family",
) -> dict[str, Any]:
    clean_success = rate([row.get(success_key) for row in rows if row.get(condition_key) == "clean"])
    intervention_rows = [row for row in rows if row.get(condition_key) == "intervention"]
    intervention_success = rate([row.get(success_key) for row in intervention_rows])
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in intervention_rows:
        by_family[str(row.get(family_key) or "unknown")].append(row)
    families = {}
    for family, family_rows in sorted(by_family.items()):
        family_success = rate([row.get(success_key) for row in family_rows])
        families[family] = {
            "n": len(family_rows),
            "success_rate": family_success,
            **degradation_metrics(clean_success, family_success),
        }
    family_acrs_values: list[float] = []
    for payload in families.values():
        family_acrs_value = payload.get("acrs")
        if family_acrs_value is not None:
            family_acrs_values.append(float(family_acrs_value))
    return {
        "clean_success": clean_success,
        "intervention_success": intervention_success,
        **degradation_metrics(clean_success, intervention_success),
        "families": families,
        "macro_family_acrs": rate(family_acrs_values),
        "micro_family_acrs": acrs_ratio(intervention_success, clean_success),
        "worst_family_robustness": min(family_acrs_values) if family_acrs_values else None,
        "fixture_only_not_evidence": True,
    }


def rank_with_ties(scores: dict[str, float | None], *, higher_is_better: bool = True) -> dict[str, float | None]:
    observed = [(agent, score) for agent, score in scores.items() if score is not None]
    observed.sort(key=lambda item: (-item[1] if higher_is_better else item[1], item[0]))
    ranks: dict[str, float | None] = {agent: None for agent, score in scores.items() if score is None}
    index = 0
    while index < len(observed):
        score = observed[index][1]
        tied = [observed[index][0]]
        cursor = index + 1
        while cursor < len(observed) and observed[cursor][1] == score:
            tied.append(observed[cursor][0])
            cursor += 1
        average_rank = (index + 1 + cursor) / 2.0
        for agent in tied:
            ranks[agent] = average_rank
        index = cursor
    return ranks


def rank_shift(clean_scores: dict[str, float | None], robustness_scores: dict[str, float | None]) -> dict[str, Any]:
    clean_rank = rank_with_ties(clean_scores)
    robust_rank = rank_with_ties(robustness_scores)
    agents = sorted(set(clean_rank) | set(robust_rank))
    rank_delta: dict[str, float | None] = {}
    for agent in agents:
        clean_value = clean_rank.get(agent)
        robust_value = robust_rank.get(agent)
        rank_delta[agent] = (
            round(robust_value - clean_value, 6)
            if clean_value is not None and robust_value is not None
            else None
        )
    return {
        "clean_rank": clean_rank,
        "robustness_rank": robust_rank,
        "rank_delta": rank_delta,
        "fixture_only_not_evidence": True,
    }


def abstention_correctness(rows: list[dict[str, Any]]) -> float | None:
    relevant = [row for row in rows if row.get("abstention_required") is True]
    if not relevant:
        return None
    return rate([row.get("abstained") is True and row.get("success") in (1, True) for row in relevant])


def scorer_adjusted_success(rows: list[dict[str, Any]]) -> float | None:
    reviewed = [row for row in rows if row.get("manual_review_status") == "complete"]
    if not reviewed:
        return None
    return rate([row.get("manual_success") for row in reviewed])
