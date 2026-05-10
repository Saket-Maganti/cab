from __future__ import annotations

from typing import Any


def rank_agents(agent_scores: dict[str, dict[str, Any]], metric: str) -> dict[str, int]:
    sorted_agents = sorted(
        agent_scores,
        key=lambda agent: (
            agent_scores[agent].get(metric) is None,
            -(agent_scores[agent].get(metric) or float("-inf")),
            agent,
        ),
    )
    return {agent: rank + 1 for rank, agent in enumerate(sorted_agents)}


def spearman_from_rankings(a: dict[str, int], b: dict[str, int]) -> float | None:
    agents = sorted(set(a) & set(b))
    n = len(agents)
    if n < 2:
        return None
    diff_sq = sum((a[agent] - b[agent]) ** 2 for agent in agents)
    return round(1 - (6 * diff_sq) / (n * (n * n - 1)), 6)


def ranking_instability(agent_scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    clean_rank = rank_agents(agent_scores, "clean_success_rate")
    acrs_rank = rank_agents(agent_scores, "acrs")
    return {
        "clean_success_ranking": clean_rank,
        "acrs_ranking": acrs_rank,
        "spearman_clean_vs_acrs": spearman_from_rankings(clean_rank, acrs_rank),
        "rank_delta": {agent: acrs_rank[agent] - clean_rank[agent] for agent in clean_rank},
    }
