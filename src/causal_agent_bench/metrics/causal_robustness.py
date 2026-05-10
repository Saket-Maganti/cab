from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any


def success_rate(rows: list[dict[str, Any]]) -> float | None:
    values = [float(row["metrics"]["final_success_binary"]) for row in rows if "final_success_binary" in row["metrics"]]
    return round(mean(values), 6) if values else None


def acrs(intervention_success_rate: float | None, clean_success_rate: float | None) -> float | None:
    if clean_success_rate in (None, 0.0) or intervention_success_rate is None:
        return None
    return round(intervention_success_rate / clean_success_rate, 6)


def degradation(clean_success_rate: float | None, intervention_success_rate: float | None) -> dict[str, float | None]:
    score = acrs(intervention_success_rate, clean_success_rate)
    absolute = (
        round(clean_success_rate - intervention_success_rate, 6)
        if clean_success_rate is not None and intervention_success_rate is not None
        else None
    )
    relative = round(1 - score, 6) if score is not None else None
    return {"absolute_degradation": absolute, "relative_degradation": relative}


def agent_robustness(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_agent[row["agent_name"]].append(row)
    output = {}
    for agent, agent_rows in by_agent.items():
        clean_rows = [row for row in agent_rows if row["diagnostics"].get("condition") == "clean"]
        intervention_rows = [row for row in agent_rows if row["diagnostics"].get("condition") == "intervention"]
        clean_rate = success_rate(clean_rows)
        intervention_rate = success_rate(intervention_rows)
        score = acrs(intervention_rate, clean_rate)
        family_rates = {}
        by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in intervention_rows:
            family = row["diagnostics"].get("intervention_family") or "unknown"
            by_family[family].append(row)
        for family, family_rows in sorted(by_family.items()):
            family_rate = success_rate(family_rows)
            family_rates[family] = {
                "success_rate": family_rate,
                "acrs_family": acrs(family_rate, clean_rate),
                **degradation(clean_rate, family_rate),
                "n": len(family_rows),
            }
        output[agent] = {
            "clean_success_rate": clean_rate,
            "intervention_success_rate": intervention_rate,
            "acrs": score,
            **degradation(clean_rate, intervention_rate),
            "n_trajectories": len(agent_rows),
            "families": family_rates,
        }
    return output
