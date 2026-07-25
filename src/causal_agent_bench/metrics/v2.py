from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from causal_agent_bench.metrics.causal_robustness import acrs, degradation
from causal_agent_bench.metrics.statistics import ranking_instability
from causal_agent_bench.schemas import ScoreRecord
from causal_agent_bench.utils.io import write_json

RATE_METRICS = [
    "clean_success",
    "intervention_success",
    "tool_recall",
    "tool_precision",
    "invalid_call_rate",
    "recovery_rate_after_tool_failure",
    "contradiction_detection_rate",
    "contradiction_resolution_rate",
    "memory_verification_rate",
    "blind_corrupted_memory_trust_rate",
    "premature_stopping_rate",
    "correct_abstention_uncertainty_rate",
    "trajectory_efficiency",
]


def aggregate_metrics_v2(records: list[ScoreRecord]) -> dict[str, Any]:
    by_agent: dict[str, list[ScoreRecord]] = defaultdict(list)
    for record in records:
        by_agent[record.agent_name].append(record)
    agents = {agent: _agent_metrics(agent_records) for agent, agent_records in sorted(by_agent.items())}
    ranking = ranking_instability(
        {
            agent: {
                "clean_success_rate": row["metrics"].get("clean_success"),
                "acrs": row["metrics"].get("acrs"),
            }
            for agent, row in agents.items()
        }
    )
    return {
        "schema_version": "metrics_v2",
        "n_score_records": len(records),
        "by_agent": agents,
        "ranking_instability": ranking,
        "metric_definitions": metric_cards(),
    }


def export_metrics_v2(run_dir: str | Path, metrics_v2: dict[str, Any]) -> list[Path]:
    out = Path(run_dir)
    paths = [
        out / "metrics_v2.json",
        out / "metrics_v2.csv",
        out / "metrics_v2.md",
        out / "metrics_v2.tex",
    ]
    write_json(paths[0], metrics_v2)
    rows = _flat_agent_rows(metrics_v2)
    _write_csv(paths[1], rows)
    paths[2].write_text(_markdown_table(rows), encoding="utf-8")
    paths[3].write_text(_latex_table(rows), encoding="utf-8")
    return paths


def metric_cards() -> dict[str, dict[str, str]]:
    return {
        "clean_success": _card("Mean final success on clean instances.", "Higher is better.", "Can be high for brittle agents.", "Do not use alone as robustness evidence."),
        "intervention_success": _card("Mean final success on intervention instances.", "Higher is better under perturbation.", "Can hide invalid trajectories.", "Do not compare without clean success."),
        "absolute_degradation": _card("clean_success - intervention_success.", "Lower degradation is better.", "Depends on clean baseline.", "Undefined if either split is absent."),
        "relative_degradation": _card("1 - ACRS.", "Lower is better.", "Undefined when clean success is zero.", "Do not use when clean success is zero."),
        "acrs": _card("intervention_success / clean_success.", "1 means intervention success equals clean success.", "Can be high for poor agents if both rates are low.", "Undefined when clean success is zero."),
        "per_family_acrs": _card("Per-family intervention success divided by clean success.", "Shows family-specific robustness.", "Noisy for small family counts.", "Do not rank agents on tiny families."),
        "tool_recall": _card("Mean required-tool recall.", "Higher means required tools were used.", "May reward unnecessary extra calls.", "Use with tool precision."),
        "tool_precision": _card("Mean required-tool precision among tool calls.", "Higher means fewer irrelevant calls.", "Can be undefined or low for abstaining agents.", "Use with final success."),
        "invalid_call_rate": _card("Mean invalid tool call count > 0 indicator.", "Lower is better.", "Sensitive to environment/parser rules.", "Do not treat as semantic correctness."),
        "recovery_rate_after_tool_failure": _card("Mean recovery indicator on rows with tool failures.", "Higher is better.", "Only defined when failures occur.", "Do not compare if no failure rows exist."),
        "contradiction_detection_rate": _card("Mean contradiction detection indicator.", "Higher is better when conflicts exist.", "Keyword heuristic may miss paraphrases.", "Requires human validation."),
        "contradiction_resolution_rate": _card("Mean contradiction resolution indicator.", "Higher is better.", "Resolution may be shallow.", "Use with examples."),
        "memory_verification_rate": _card("Mean memory verification indicator.", "Higher is better for memory tasks.", "May undercount implicit verification.", "Use mostly on memory conditions."),
        "blind_corrupted_memory_trust_rate": _card("Mean blind-trust failure indicator.", "Lower is better.", "Depends on final-success heuristic.", "Use with memory-corruption examples."),
        "premature_stopping_rate": _card("Mean premature-stop indicator.", "Lower is better.", "Requires reliable required-tool metadata.", "Do not use when tools are optional."),
        "correct_abstention_uncertainty_rate": _card("Mean uncertainty/limitation response after failures.", "Higher is better when evidence is insufficient.", "Can reward over-cautious answers.", "Use only for failure/ambiguity conditions."),
        "trajectory_efficiency": _card("Required tool count divided by actual tool-call count, capped at 1.", "Higher means fewer extra calls.", "Can reward too few calls if paired with poor success.", "Use with success and recall."),
        "cost_normalized_robustness": _card("ACRS divided by mean estimated cost plus one.", "Higher means robustness per cost unit.", "Cost metadata may be missing or approximate.", "Do not compare across unpriced providers."),
        "latency_normalized_robustness": _card("ACRS divided by mean latency plus one.", "Higher means robustness per second.", "Latency depends on environment and provider.", "Do not compare local and remote runs directly."),
        "rank_instability": _card("Rank changes between clean success and ACRS.", "Large deltas show clean performance can mislead.", "Unstable for few agents.", "Do not use with one agent."),
    }


def _agent_metrics(records: list[ScoreRecord]) -> dict[str, Any]:
    clean = [record for record in records if record.diagnostics.get("condition") == "clean"]
    interventions = [record for record in records if record.diagnostics.get("condition") == "intervention"]
    clean_success = _mean_metric(clean, "final_success_binary")
    intervention_success = _mean_metric(interventions, "final_success_binary")
    score = acrs(intervention_success, clean_success)
    family_metrics = _family_metrics(interventions, clean_success)
    metrics = {
        "clean_success": clean_success,
        "intervention_success": intervention_success,
        "acrs": score,
        **degradation(clean_success, intervention_success),
        "tool_recall": _mean_metric(records, "required_tool_recall"),
        "tool_precision": _mean_metric(records, "tool_precision"),
        "invalid_call_rate": _indicator_rate(records, "invalid_tool_call_count"),
        "recovery_rate_after_tool_failure": _mean_metric(records, "tool_error_recovery_binary"),
        "contradiction_detection_rate": _mean_metric(records, "contradiction_detected_binary"),
        "contradiction_resolution_rate": _mean_metric(records, "contradiction_resolved_binary"),
        "memory_verification_rate": _mean_metric(records, "memory_verified_binary"),
        "blind_corrupted_memory_trust_rate": _mean_metric(records, "memory_blind_trust_failure_binary"),
        "premature_stopping_rate": _mean_metric(records, "premature_stop_binary"),
        "correct_abstention_uncertainty_rate": _mean_metric(records, "correct_abstention_uncertainty_binary"),
        "trajectory_efficiency": _mean_metric(records, "trajectory_efficiency"),
        "avg_cost_per_task_usd": _mean_metadata(records, "estimated_cost_usd"),
        "avg_latency_per_task_s": _mean_metadata(records, "latency_s"),
        "avg_model_calls_per_task": _mean_metadata(records, "model_call_count"),
        "avg_tool_calls_per_task": _mean_metadata(records, "tool_call_count"),
        "cost_normalized_robustness": _normalized(score, _mean_metadata(records, "estimated_cost_usd")),
        "latency_normalized_robustness": _normalized(score, _mean_metadata(records, "latency_s")),
    }
    return {
        "n": len(records),
        "metrics": metrics,
        "confidence_intervals": {
            metric: _ci_for_metric(records, metric) for metric in RATE_METRICS
        },
        "families": family_metrics,
    }


def _family_metrics(records: list[ScoreRecord], clean_success: float | None) -> dict[str, dict[str, Any]]:
    by_family: dict[str, list[ScoreRecord]] = defaultdict(list)
    for record in records:
        by_family[str(record.diagnostics.get("intervention_family") or "unknown")].append(record)
    output = {}
    for family, family_records in sorted(by_family.items()):
        success = _mean_metric(family_records, "final_success_binary")
        output[family] = {
            "n": len(family_records),
            "success_rate": success,
            "acrs_family": acrs(success, clean_success),
            **degradation(clean_success, success),
            "confidence_interval": _wilson_ci(_values(family_records, "final_success_binary")),
        }
    return output


def _mean_metric(records: list[ScoreRecord], key: str) -> float | None:
    values = _values(records, key)
    return round(mean(values), 6) if values else None


def _indicator_rate(records: list[ScoreRecord], key: str) -> float | None:
    values = []
    for record in records:
        value = record.metrics.get(key)
        if value is None:
            continue
        values.append(1.0 if float(value) > 0 else 0.0)
    return round(mean(values), 6) if values else None


def _values(records: list[ScoreRecord], key: str) -> list[float]:
    values = []
    for record in records:
        value = record.metrics.get(key)
        if value is None or isinstance(value, str):
            continue
        values.append(float(value))
    return values


def _mean_metadata(records: list[ScoreRecord], key: str) -> float | None:
    values = []
    for record in records:
        value = record.metadata.get(key)
        if value is None:
            value = record.metadata.get("token_cost_metadata", {}).get(key) if isinstance(record.metadata.get("token_cost_metadata"), dict) else None
        if value is not None:
            values.append(float(value))
    return round(mean(values), 6) if values else None


def _normalized(score: float | None, denominator: float | None) -> float | None:
    if score is None or denominator is None:
        return None
    return round(score / (1 + denominator), 6)


def _ci_for_metric(records: list[ScoreRecord], metric: str) -> dict[str, float | None]:
    mapping = {
        "clean_success": ("final_success_binary", "clean"),
        "intervention_success": ("final_success_binary", "intervention"),
        "tool_recall": ("required_tool_recall", None),
        "tool_precision": ("tool_precision", None),
        "recovery_rate_after_tool_failure": ("tool_error_recovery_binary", None),
        "contradiction_detection_rate": ("contradiction_detected_binary", None),
        "contradiction_resolution_rate": ("contradiction_resolved_binary", None),
        "memory_verification_rate": ("memory_verified_binary", None),
        "blind_corrupted_memory_trust_rate": ("memory_blind_trust_failure_binary", None),
        "premature_stopping_rate": ("premature_stop_binary", None),
        "correct_abstention_uncertainty_rate": ("correct_abstention_uncertainty_binary", None),
        "trajectory_efficiency": ("trajectory_efficiency", None),
    }
    if metric == "invalid_call_rate":
        values = []
        for record in records:
            value = record.metrics.get("invalid_tool_call_count")
            if value is not None:
                values.append(1.0 if float(value) > 0 else 0.0)
        return _ci_payload(values)
    if metric not in mapping:
        return {"mean": None, "low": None, "high": None}
    key, condition = mapping[metric]
    filtered = [
        record for record in records
        if condition is None or record.diagnostics.get("condition") == condition
    ]
    return _ci_payload(_values(filtered, key))


def _ci_payload(values: list[float]) -> dict[str, float | None]:
    low, high = _wilson_ci(values)
    return {"mean": round(mean(values), 6) if values else None, "low": low, "high": high}


def _wilson_ci(values: list[float], z: float = 1.96) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    # Wilson interval for bounded rates; for fractional metrics this is a conservative summary.
    n = len(values)
    phat = sum(values) / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / denom
    return round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6)


def _flat_agent_rows(metrics_v2: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for agent, payload in sorted(metrics_v2.get("by_agent", {}).items()):
        row = {"agent": agent, "n": payload.get("n")}
        row.update(payload.get("metrics", {}))
        for metric, ci in payload.get("confidence_intervals", {}).items():
            row[f"{metric}_ci95"] = _ci_text(ci.get("low"), ci.get("high"))
        rows.append(row)
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row}) if rows else ["agent"]
    preferred = ["agent", "n", "clean_success", "intervention_success", "acrs"]
    fields = preferred + [field for field in fields if field not in preferred]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No metrics._\n"
    fields = ["agent", "clean_success", "intervention_success", "acrs", "absolute_degradation", "tool_recall", "tool_precision", "premature_stopping_rate"]
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(row.get(field)) for field in fields) + " |")
    return "\n".join(lines) + "\n"


def _latex_table(rows: list[dict[str, Any]]) -> str:
    lines = ["\\begin{tabular}{lrrrr}", "\\toprule", "Agent & Clean & Intervention & ACRS & Abs. degradation \\\\", "\\midrule"]
    for row in rows:
        lines.append(
            f"{row.get('agent')} & {_fmt(row.get('clean_success'))} & {_fmt(row.get('intervention_success'))} & {_fmt(row.get('acrs'))} & {_fmt(row.get('absolute_degradation'))} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def _card(definition: str, interpretation: str, failure_modes: str, when_not_to_use: str) -> dict[str, str]:
    return {
        "definition": definition,
        "interpretation": interpretation,
        "failure_modes": failure_modes,
        "when_not_to_use": when_not_to_use,
    }


def _ci_text(low: float | None, high: float | None) -> str | None:
    if low is None or high is None:
        return None
    return f"[{low:.3f}, {high:.3f}]"


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
