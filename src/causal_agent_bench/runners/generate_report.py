from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.runners.run_completion import infer_completion_state, load_run_metadata
from causal_agent_bench.runners.run_status import build_run_status, resolve_run_dir
from causal_agent_bench.utils.io import read_json


def _load_config(run_dir: Path) -> dict[str, Any]:
    for name in ("config.yaml", "config.json"):
        path = run_dir / name
        if path.exists():
            if path.suffix == ".json":
                return read_json(path)
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


def _load_errors(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "errors.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_metrics(run_dir: Path) -> dict[str, Any]:
    agg_path = run_dir / "aggregate_scores.json"
    return read_json(agg_path) if agg_path.exists() else {}


def _model_ids(metadata: dict[str, Any]) -> list[str]:
    models: list[str] = []
    for run in metadata.get("agent_runs") or []:
        model = run.get("model")
        if model:
            models.append(str(model))
    return models


def _analysis_assets(run_dir: Path) -> dict[str, bool]:
    return {
        "analysis_report_md": (run_dir / "analysis_report.md").exists(),
        "aggregate_scores_json": (run_dir / "aggregate_scores.json").exists(),
        "scores_jsonl": (run_dir / "scores.jsonl").exists(),
        "paper_assets_dir": (run_dir / "paper_assets").is_dir(),
        "failure_gallery_md": (run_dir / "failure_gallery.md").exists(),
        "report_md": (run_dir / "report.md").exists(),
    }


def _run_label(state: dict[str, Any], metadata: dict[str, Any]) -> str:
    if state["run_status"] == "dry_run":
        return "dry_run"
    if state["completion_state"] != "complete":
        return "incomplete"
    agents = metadata.get("agents") or []
    if any("stub" in str(a).lower() or "mock" in str(a).lower() for a in agents):
        return "stub_or_mock"
    if metadata.get("scientific_evidence_level") == "preliminary_or_engineering":
        return "preliminary"
    return "candidate"


def _claim_usability(state: dict[str, Any], metadata: dict[str, Any], label: str) -> dict[str, Any]:
    engineering = label in {"dry_run", "stub_or_mock", "incomplete"} or metadata.get("evidence_scope") in {
        "local_stub",
        "engineering_only",
        "deterministic_smoke",
    }
    usable = (
        state["completion_state"] == "complete"
        and not state["oracle_agents"]
        and not state["allow_paid_calls"]
        and state["run_status"] not in {"dry_run", "interrupted"}
        and label not in {"dry_run", "stub_or_mock", "incomplete"}
    )
    return {
        "usable_for_final_claims": usable,
        "usable_for_preliminary_observations": state["completion_state"] == "complete"
        and state["run_status"] not in {"dry_run"},
        "engineering_or_preliminary_only": engineering or state["completion_state"] != "complete",
        "run_label": label,
        "claim_safety_warning": (
            "NOT usable for C1–C8/C10 scientific claims."
            if not usable
            else "Pilot-level only; human validation and provider runs still required."
        ),
        "rationale": _usability_rationale(state, metadata, usable, engineering, label),
    }


def _usability_rationale(
    state: dict[str, Any],
    metadata: dict[str, Any],
    usable: bool,
    engineering: bool,
    label: str,
) -> str:
    if label == "incomplete":
        return "Run incomplete; cannot support scientific claims."
    if label == "dry_run":
        return "Dry-run only; no model evidence."
    if state["oracle_agents"]:
        return "Oracle agents present; exclude from realistic model rankings."
    if label == "stub_or_mock" or engineering:
        return "Stub/mock/engineering run; preliminary infrastructure validation only."
    if usable:
        return "Completed non-oracle run; may support pilot-level review with validation."
    return "Does not meet claim-support thresholds."


def build_run_report(run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    status = build_run_status(run_dir)
    metadata = load_run_metadata(run_dir)
    state = infer_completion_state(run_dir)
    config = _load_config(run_dir)
    metrics = _load_metrics(run_dir)
    errors = _load_errors(run_dir)
    label = _run_label(state, metadata)
    warnings: list[str] = []
    if state["completion_state"] != "complete":
        warnings.append("Run is incomplete or interrupted.")
    if label in {"stub_or_mock", "dry_run"}:
        warnings.append(f"Run labeled {label}; engineering/preliminary only.")
    if metadata.get("scientific_evidence_level") == "preliminary_or_engineering":
        warnings.append("Evidence level is preliminary_or_engineering.")
    if status.get("oracle_agents"):
        warnings.append(f"Oracle agents: {', '.join(status['oracle_agents'])}")
    if not metrics:
        warnings.append("No aggregate metrics found (run may be unscored).")

    usability = _claim_usability(state, metadata, label)
    assets = _analysis_assets(run_dir)
    return {
        "run_dir": str(run_dir),
        "run_id": run_dir.name,
        "run_label": label,
        "status": status,
        "completion_state": state["completion_state"],
        "evidence_level": status["evidence_level"],
        "metadata": metadata,
        "config": config,
        "config_hash": status.get("config_hash"),
        "dataset": metadata.get("benchmark_location") or metadata.get("benchmark_instances_path"),
        "agents": metadata.get("agents") or [],
        "provider_type": metadata.get("provider_type"),
        "model_ids": _model_ids(metadata),
        "paid_calls": {"allowed": state["allow_paid_calls"], "made": state["paid_calls_made"]},
        "oracle_agents": state["oracle_agents"],
        "trajectories": {
            "completed": state["completed_trajectories"],
            "expected": state["expected_trajectories"],
            "percent": state.get("progress_percent"),
        },
        "errors_count": len(errors),
        "errors": errors[:20],
        "metrics_available": bool(metrics),
        "metrics": {
            "aggregate": metrics,
            "by_agent": metrics.get("by_agent", {}),
            "n_score_records": metrics.get("n_score_records"),
        },
        "analysis_assets": assets,
        "pipeline_allowed": {
            "score": status["score_allowed_default"],
            "analyze": status["analyze_allowed_default"],
            "export": status["export_allowed_default"],
        },
        "warnings": warnings,
        "claim_usability": usability,
    }


def render_report_markdown(report: dict[str, Any]) -> str:
    status = report["status"]
    usability = report["claim_usability"]
    lines = [
        "# CausalAgentBench Run Report",
        "",
        f"- **Run ID:** `{report['run_id']}`",
        f"- **Run label:** {report['run_label']}",
        f"- **Status:** {status['run_status']}",
        f"- **Completion state:** {report['completion_state']}",
        f"- **Evidence level:** {report['evidence_level']}",
        f"- **Config hash:** {report.get('config_hash')}",
        f"- **Dataset:** `{report.get('dataset')}`",
        f"- **Provider type:** {report.get('provider_type')}",
        f"- **Model IDs:** {', '.join(report.get('model_ids') or []) or 'none'}",
        f"- **Agents:** {', '.join(report.get('agents') or []) or 'unknown'}",
        f"- **Trajectories:** {report['trajectories']['completed']}/{report['trajectories']['expected']}",
        f"- **Errors:** {report['errors_count']}",
        f"- **Paid calls allowed:** {report['paid_calls']['allowed']}",
        f"- **Paid calls made:** {report['paid_calls']['made']}",
        f"- **Oracle agents:** {', '.join(report['oracle_agents']) or 'none'}",
        "",
        "## Pipeline",
        f"- score allowed (default): {report['pipeline_allowed']['score']}",
        f"- analyze allowed (default): {report['pipeline_allowed']['analyze']}",
        f"- export allowed (default): {report['pipeline_allowed']['export']}",
        "",
        "## Claim usability",
        f"- **Final claims:** {usability['usable_for_final_claims']}",
        f"- **Preliminary observations:** {usability['usable_for_preliminary_observations']}",
        f"- **Engineering/preliminary only:** {usability['engineering_or_preliminary_only']}",
        f"- **Warning:** {usability['claim_safety_warning']}",
        f"- **Rationale:** {usability['rationale']}",
        "",
        "## Analysis assets",
    ]
    for key, present in report["analysis_assets"].items():
        lines.append(f"- {key}: {present}")
    lines.extend(["", "## Warnings"])
    lines.extend(f"- {w}" for w in report["warnings"])
    lines.append("- none")
    lines.extend(["", "## Metrics summary"])
    if report["metrics_available"]:
        for agent, row in sorted((report["metrics"].get("by_agent") or {}).items()):
            clean = row.get("clean_success_rate", row.get("final_success_rate"))
            acrs = row.get("acrs")
            lines.append(f"- **{agent}:** clean={clean}, ACRS={acrs}")
    else:
        lines.append("- metrics unavailable")
    return "\n".join(lines) + "\n"


def render_report_html(report: dict[str, Any]) -> str:
    body = escape(render_report_markdown(report)).replace("\n", "<br>\n")
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>CausalAgentBench Run Report</title></head>"
        f"<body><pre style='font-family:sans-serif;white-space:pre-wrap'>{body}</pre></body></html>"
    )


def write_run_report(run_dir: str | Path, *, include_html: bool = True) -> dict[str, Path]:
    run_dir = Path(run_dir)
    report = build_run_report(run_dir)
    paths = {
        "markdown": run_dir / "report.md",
        "json": run_dir / "report.json",
    }
    paths["markdown"].write_text(render_report_markdown(report), encoding="utf-8")
    paths["json"].write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if include_html:
        html_path = run_dir / "report.html"
        html_path.write_text(render_report_html(report), encoding="utf-8")
        paths["html"] = html_path
    return paths


def generate_report(
    run_dir: str | Path | None = None,
    *,
    latest: bool = False,
    include_html: bool = True,
) -> dict[str, Path]:
    return write_run_report(resolve_run_dir(run_dir, latest=latest), include_html=include_html)
