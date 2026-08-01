"""Frozen pre-run endpoint derivation from scorer-v3 trajectory records."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

PRIMARY_ENDPOINTS = (
    "clean_task_completion",
    "intervention_task_completion",
    "clean_conditioned_retained_completion",
    "paired_completion_degradation",
    "completion_acrs",
    "safe_response_rate",
    "false_abstention_rate",
    "recovery_adjusted_completion",
)
SECONDARY_ENDPOINTS = (
    "contract_compliance",
    "justified_abstention",
    "clarification_quality",
    "recovery_attempt_rate",
    "recovery_success_rate",
    "tool_calls",
    "model_calls",
    "token_overhead",
    "wall_time_overhead",
    "worst_family_completion",
    "worst_family_safe_response",
)


def compute_frozen_endpoints(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the frozen estimands without conflating safe behavior and completion."""

    clean = [row for row in rows if _condition(row) == "clean"]
    interventions = [row for row in rows if _condition(row) == "intervention"]
    clean_completion = _rate(clean, "task_completion_success")
    intervention_completion = _rate(interventions, "task_completion_success")
    clean_by_key = {_pair_key(row): row for row in clean}
    retained_values: list[float] = []
    paired_degradations: list[float] = []
    for row in interventions:
        clean_row = clean_by_key.get(_pair_key(row))
        if clean_row is None:
            continue
        clean_value = _metric(clean_row, "task_completion_success")
        intervention_value = _metric(row, "task_completion_success")
        if clean_value is None or intervention_value is None:
            continue
        paired_degradations.append(clean_value - intervention_value)
        if clean_value == 1:
            retained_values.append(intervention_value)
    completion_acrs: float | None = None
    if clean_completion is not None and clean_completion != 0.0:
        if intervention_completion is not None:
            completion_acrs = intervention_completion / clean_completion
    opportunity_rows = [
        row for row in rows if _metric(row, "abstention_opportunity") == 1
    ]
    recovery_opportunities = [
        row
        for row in rows
        if _metric(row, "recovery_plan_stated") == 1
        or _metric(row, "recovery_action_attempted") == 1
    ]
    family_completion: dict[str, list[float]] = defaultdict(list)
    family_safe: dict[str, list[float]] = defaultdict(list)
    for row in interventions:
        family = _family(row)
        completion = _metric(row, "task_completion_success")
        safe = _metric(row, "safe_response_success")
        if completion is not None:
            family_completion[family].append(completion)
        if safe is not None:
            family_safe[family].append(safe)
    primary = {
        "clean_task_completion": clean_completion,
        "intervention_task_completion": intervention_completion,
        "clean_conditioned_retained_completion": _mean(retained_values),
        "paired_completion_degradation": _mean(paired_degradations),
        "completion_acrs": completion_acrs,
        "safe_response_rate": _rate(rows, "safe_response_success"),
        "false_abstention_rate": _rate(rows, "false_abstention"),
        "recovery_adjusted_completion": _mean(
            [
                max(
                    _metric(row, "task_completion_success") or 0.0,
                    _metric(row, "task_recovered") or 0.0,
                )
                for row in rows
            ]
        ),
    }
    secondary = {
        "contract_compliance": _rate(rows, "contract_compliance"),
        "justified_abstention": _rate(opportunity_rows, "abstention_correct"),
        "clarification_quality": _rate(rows, "clarification_correct"),
        "recovery_attempt_rate": _rate(
            recovery_opportunities,
            "recovery_action_attempted",
        ),
        "recovery_success_rate": _rate(
            recovery_opportunities,
            "recovery_action_succeeded",
        ),
        "tool_calls": _rate(rows, "tool_call_count"),
        "model_calls": _rate(rows, "model_call_count"),
        "token_overhead": _rate(rows, "total_tokens"),
        "wall_time_overhead": _rate(rows, "latency_s"),
        "worst_family_completion": _minimum_group_mean(family_completion),
        "worst_family_safe_response": _minimum_group_mean(family_safe),
    }
    return {
        "schema_version": "cab_frozen_endpoints_v1",
        "scorer_version_required": "3.0.0",
        "primary": primary,
        "secondary": secondary,
        "denominators": {
            "all_rows": len(rows),
            "clean_rows": len(clean),
            "intervention_rows": len(interventions),
            "paired_rows": len(paired_degradations),
            "clean_success_conditioned_rows": len(retained_values),
            "abstention_opportunity_rows": len(opportunity_rows),
            "recovery_opportunity_rows": len(recovery_opportunities),
        },
    }


def _metric(row: dict[str, Any], key: str) -> float | None:
    metrics = row.get("metrics")
    value = metrics.get(key) if isinstance(metrics, dict) else row.get(key)
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    return None


def _rate(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [value for row in rows if (value := _metric(row, key)) is not None]
    return _mean(values)


def _mean(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def _minimum_group_mean(groups: dict[str, list[float]]) -> float | None:
    values = [_mean(group) for group in groups.values()]
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _condition(row: dict[str, Any]) -> str:
    diagnostics = row.get("diagnostics")
    return str(
        diagnostics.get("condition")
        if isinstance(diagnostics, dict)
        else row.get("condition")
        or ""
    )


def _family(row: dict[str, Any]) -> str:
    diagnostics = row.get("diagnostics")
    return str(
        diagnostics.get("intervention_family")
        if isinstance(diagnostics, dict)
        else row.get("family")
        or "unknown"
    )


def _pair_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    diagnostics = row.get("diagnostics")
    metadata = row.get("metadata")
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    metadata = metadata if isinstance(metadata, dict) else {}
    return (
        str(row.get("agent_name") or row.get("model") or ""),
        str(diagnostics.get("base_task_id") or row.get("base_task_id") or ""),
        str(diagnostics.get("repeat_id") or row.get("repeat_id") or ""),
        str(metadata.get("raac_policy") or row.get("policy") or "standard"),
    )


__all__ = [
    "PRIMARY_ENDPOINTS",
    "SECONDARY_ENDPOINTS",
    "compute_frozen_endpoints",
]
