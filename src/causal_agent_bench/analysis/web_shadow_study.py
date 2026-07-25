from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from causal_agent_bench.analysis.load_results import load_run_results
from causal_agent_bench.analysis.tables import dataframe_to_markdown, write_table_bundle
from causal_agent_bench.utils.io import write_json


def compare_web_shadow_interfaces(
    api_run_dir: str | Path,
    web_run_dir: str | Path,
    *,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Compare simulated API vs static web snapshot tool interfaces."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    api_data = load_run_results(api_run_dir)
    web_data = load_run_results(web_run_dir)

    api_metrics = _interface_metrics(api_data, interface="api")
    web_metrics = _interface_metrics(web_data, interface="web_snapshot")
    paired = _paired_scenario_comparison(api_data, web_data)
    report = {
        "schema_version": "web_shadow_study_v1",
        "api_run_dir": str(api_data.run_dir),
        "web_run_dir": str(web_data.run_dir),
        "api_evidence_scope": api_data.run_metadata.get("evidence_scope"),
        "web_evidence_scope": web_data.run_metadata.get("evidence_scope"),
        "api_summary": api_metrics,
        "web_summary": web_metrics,
        "paired_scenarios": paired,
        "limitations": _limitations(),
        "scope": (
            "Engineering comparison of tool-interface degradation patterns on a frozen static web snapshot. "
            "Not a claim about real-world web browsing or external validity until validated with live models "
            "and human review."
        ),
    }

    table = _comparison_table(api_metrics, web_metrics, paired)
    table_paths = write_table_bundle(table, output_path / "table_web_shadow_interface_comparison")
    write_json(output_path / "web_shadow_comparison.json", report)
    markdown = _report_markdown(report, table)
    (output_path / "web_shadow_comparison.md").write_text(markdown, encoding="utf-8")
    return {
        "output_dir": str(output_path),
        "table_paths": table_paths,
        "report": report,
    }


def _interface_metrics(run_data: Any, interface: str) -> dict[str, Any]:
    records = [
        record
        for record in run_data.score_records
        if _record_interface(record) == interface or interface in str(record.instance_id)
    ]
    if not records:
        records = list(run_data.score_records)
    clean = [r for r in records if r.diagnostics.get("condition") == "clean"]
    intervention = [r for r in records if r.diagnostics.get("condition") == "intervention"]
    return {
        "interface": interface,
        "record_count": len(records),
        "clean_success_rate": _mean_metric(clean, "final_success"),
        "intervention_success_rate": _mean_metric(intervention, "final_success"),
        "mean_recovery_score": _mean_metric(intervention, "recovery_score"),
        "family_breakdown": _family_breakdown(intervention),
    }


def _record_interface(record: Any) -> str | None:
    metadata = getattr(record, "metadata", {}) or {}
    diagnostics = getattr(record, "diagnostics", {}) or {}
    task_id = str(diagnostics.get("base_task_id", ""))
    if "web_snapshot" in task_id:
        return "web_snapshot"
    if "api" in task_id:
        return "api"
    return metadata.get("tool_interface")


def _mean_metric(records: list[Any], key: str) -> float | None:
    if not records:
        return None
    values = [float(record.metrics.get(key, 0.0)) for record in records]
    return round(sum(values) / len(values), 4)


def _family_breakdown(records: list[Any]) -> dict[str, float | None]:
    buckets: dict[str, list[float]] = {}
    for record in records:
        family = str(record.diagnostics.get("intervention_family") or "unknown")
        buckets.setdefault(family, []).append(float(record.metrics.get("final_success", 0.0)))
    return {family: round(sum(values) / len(values), 4) for family, values in buckets.items()}


def _paired_scenario_comparison(api_data: Any, web_data: Any) -> list[dict[str, Any]]:
    api_by_key = _scenario_index(api_data)
    web_by_key = _scenario_index(web_data)
    rows = []
    for key in sorted(set(api_by_key) & set(web_by_key)):
        api_clean = api_by_key[key].get("clean")
        web_clean = web_by_key[key].get("clean")
        api_drop = _degradation(api_by_key[key])
        web_drop = _degradation(web_by_key[key])
        rows.append(
            {
                "scenario_key": key,
                "api_clean_success": api_clean,
                "web_clean_success": web_clean,
                "api_intervention_drop": api_drop,
                "web_intervention_drop": web_drop,
                "pattern_delta": None
                if api_drop is None or web_drop is None
                else round(web_drop - api_drop, 4),
            }
        )
    return rows


def _scenario_index(run_data: Any) -> dict[str, dict[str, float | None]]:
    index: dict[str, dict[str, float | None]] = {}
    for record in run_data.score_records:
        diagnostics = record.diagnostics
        base_task_id = str(diagnostics.get("base_task_id", ""))
        key = _scenario_key(base_task_id)
        condition = str(diagnostics.get("condition", "unknown"))
        index.setdefault(key, {})[condition] = float(record.metrics.get("final_success", 0.0))
    return index


def _scenario_key(base_task_id: str) -> str:
    parts = base_task_id.split("_")
    if len(parts) >= 4:
        return "_".join(parts[3:-1]) if parts[-1] in {"easy", "medium", "hard", "stress"} else "_".join(parts[3:])
    return base_task_id


def _degradation(scenario_records: dict[str, float | None]) -> float | None:
    clean = scenario_records.get("clean")
    if clean is None:
        return None
    intervention_values = [value for key, value in scenario_records.items() if key != "clean" and value is not None]
    if not intervention_values:
        return None
    mean_intervention = sum(intervention_values) / len(intervention_values)
    return round(clean - mean_intervention, 4)


def _comparison_table(
    api_metrics: dict[str, Any],
    web_metrics: dict[str, Any],
    paired: list[dict[str, Any]],
) -> pd.DataFrame:
    summary_rows = [
        {
            "metric": "clean_success_rate",
            "api": api_metrics.get("clean_success_rate"),
            "web_snapshot": web_metrics.get("clean_success_rate"),
        },
        {
            "metric": "intervention_success_rate",
            "api": api_metrics.get("intervention_success_rate"),
            "web_snapshot": web_metrics.get("intervention_success_rate"),
        },
        {
            "metric": "mean_recovery_score",
            "api": api_metrics.get("mean_recovery_score"),
            "web_snapshot": web_metrics.get("mean_recovery_score"),
        },
    ]
    if paired:
        summary_rows.append(
            {
                "metric": "mean_intervention_drop_delta_web_minus_api",
                "api": None,
                "web_snapshot": round(
                    sum(row["pattern_delta"] for row in paired if row["pattern_delta"] is not None)
                    / max(1, len([row for row in paired if row["pattern_delta"] is not None])),
                    4,
                ),
            }
        )
    return pd.DataFrame(summary_rows)


def _report_markdown(report: dict[str, Any], table: pd.DataFrame) -> str:
    lines = [
        "# Web shadow study comparison",
        "",
        report["scope"],
        "",
        "## Limitations",
        report["limitations"],
        "",
        "## Interface summary",
        dataframe_to_markdown(table),
        "",
        f"API run: `{report['api_run_dir']}`",
        f"Web run: `{report['web_run_dir']}`",
    ]
    return "\n".join(lines)


def _limitations() -> str:
    return (
        "- Static HTML snapshot only; no live network, cookies, JavaScript rendering, or auth flows.\n"
        "- Synthetic Acme site; not representative of real product/support/legal pages.\n"
        "- Stub or pilot runs are engineering smoke tests, not scientific external-validity evidence.\n"
        "- API-interface tasks use mirrored interventions, not identical causal factors as web interventions."
    )
