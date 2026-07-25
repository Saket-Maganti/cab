from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from causal_agent_bench.runners.generate_report import build_run_report


def _agent_metrics(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not report.get("metrics_available"):
        return {}
    return report.get("metrics", {}).get("by_agent") or {}


def compare_runs(run_dir_a: str | Path, run_dir_b: str | Path) -> dict[str, Any]:
    a = build_run_report(run_dir_a)
    b = build_run_report(run_dir_b)
    warnings: list[str] = []

    if a.get("dataset") != b.get("dataset"):
        warnings.append("Dataset paths differ between runs.")
    if a["status"]["run_status"] != "complete":
        warnings.append(f"Run A incomplete: {a['run_id']}")
    if b["status"]["run_status"] != "complete":
        warnings.append(f"Run B incomplete: {b['run_id']}")
    if not a.get("metrics_available"):
        warnings.append("Run A metrics unavailable.")
    if not b.get("metrics_available"):
        warnings.append("Run B metrics unavailable.")

    agents_a = set(a.get("agents") or [])
    agents_b = set(b.get("agents") or [])
    metrics_a = _agent_metrics(a)
    metrics_b = _agent_metrics(b)
    shared_agents = sorted(agents_a & agents_b)
    metric_diffs: list[dict[str, Any]] = []
    for agent in shared_agents:
        row_a = metrics_a.get(agent, {})
        row_b = metrics_b.get(agent, {})
        metric_diffs.append(
            {
                "agent": agent,
                "clean_success_a": row_a.get("clean_success_rate", row_a.get("final_success_rate")),
                "clean_success_b": row_b.get("clean_success_rate", row_b.get("final_success_rate")),
                "acrs_a": row_a.get("acrs"),
                "acrs_b": row_b.get("acrs"),
            }
        )

    return {
        "run_a": a["run_id"],
        "run_b": b["run_id"],
        "run_a_path": a["run_dir"],
        "run_b_path": b["run_dir"],
        "status": {"a": a["status"]["run_status"], "b": b["status"]["run_status"]},
        "evidence_level": {"a": a["evidence_level"], "b": b["evidence_level"]},
        "run_label": {"a": a["run_label"], "b": b["run_label"]},
        "configs": {
            "a_hash": a.get("config_hash"),
            "b_hash": b.get("config_hash"),
            "same_hash": a.get("config_hash") == b.get("config_hash"),
        },
        "datasets": {"a": a.get("dataset"), "b": b.get("dataset"), "match": a.get("dataset") == b.get("dataset")},
        "provider_type": {"a": a.get("provider_type"), "b": b.get("provider_type")},
        "model_ids": {"a": a.get("model_ids"), "b": b.get("model_ids")},
        "agents": {
            "a": sorted(agents_a),
            "b": sorted(agents_b),
            "only_a": sorted(agents_a - agents_b),
            "only_b": sorted(agents_b - agents_a),
            "shared": shared_agents,
        },
        "completion": {"a": a["trajectories"], "b": b["trajectories"]},
        "paid_calls": {"a": a["paid_calls"], "b": b["paid_calls"]},
        "oracle_agents": {"a": a["oracle_agents"], "b": b["oracle_agents"]},
        "errors_count": {"a": a["errors_count"], "b": b["errors_count"]},
        "metrics_available": {"a": a.get("metrics_available"), "b": b.get("metrics_available")},
        "metric_diffs": metric_diffs,
        "claim_usability": {"a": a["claim_usability"], "b": b["claim_usability"]},
        "warnings": warnings,
    }


def format_compare_report(comparison: dict[str, Any]) -> str:
    lines = [
        "# Run comparison",
        "",
        f"- **Run A:** `{comparison['run_a']}`",
        f"- **Run B:** `{comparison['run_b']}`",
        f"- **Status:** {comparison['status']['a']} vs {comparison['status']['b']}",
        f"- **Evidence:** {comparison['evidence_level']['a']} vs {comparison['evidence_level']['b']}",
        f"- **Config hash match:** {comparison['configs']['same_hash']}",
        f"- **Dataset match:** {comparison['datasets']['match']}",
        "",
        "## Completion",
        f"- A: {comparison['completion']['a']['completed']}/{comparison['completion']['a']['expected']} "
        f"({comparison['completion']['a'].get('percent')}%)",
        f"- B: {comparison['completion']['b']['completed']}/{comparison['completion']['b']['expected']} "
        f"({comparison['completion']['b'].get('percent')}%)",
        "",
        "## Metrics",
    ]
    if comparison["metric_diffs"]:
        for row in comparison["metric_diffs"]:
            lines.append(
                f"- **{row['agent']}:** clean {row['clean_success_a']} → {row['clean_success_b']}, "
                f"ACRS {row['acrs_a']} → {row['acrs_b']}"
            )
    else:
        lines.append("- metrics unavailable or no shared agents")
    lines.extend(["", "## Warnings"])
    lines.extend(f"- {w}" for w in comparison["warnings"])
    lines.append("- none")
    return "\n".join(lines) + "\n"


def write_compare_artifacts(
    run_dir_a: str | Path,
    run_dir_b: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    comparison = compare_runs(run_dir_a, run_dir_b)
    out = Path(output_dir) if output_dir else Path(run_dir_a)
    md_path = out / "run_comparison.md"
    json_path = out / "run_comparison.json"
    md_path.write_text(format_compare_report(comparison), encoding="utf-8")
    json_path.write_text(json.dumps(comparison, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"markdown": md_path, "json": json_path}
