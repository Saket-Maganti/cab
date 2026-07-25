from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from causal_agent_bench.analysis.load_results import RunResults
from causal_agent_bench.analysis.tables import (
    _is_oracle_agent,
    _scorer_versions,
    asset_metadata,
    dataframe_to_markdown,
)
from causal_agent_bench.metrics.causal_robustness import agent_robustness
from causal_agent_bench.utils.io import read_json

LEADERBOARD_SCHEMA_VERSION = "1.0"
LEADERBOARD_SCHEMA_ID = "causal_agent_bench.leaderboard.v1"

SPLIT_ALIASES: dict[str, tuple[str, ...]] = {
    "public_dev": ("dev", "pilot"),
    "dev": ("dev",),
    "pilot": ("pilot",),
    "validation": ("validation",),
    "test": ("test",),
    "heldout_templates": ("heldout_templates",),
}

OFFICIAL_HEADLINE_SPLITS = frozenset({"test"})
ENGINEERING_SPLITS = frozenset({"public_dev", "dev", "pilot", "validation"})

CONTAMINATION_WARNING = (
    "Causal Agent Bench leaderboards are diagnostic instruments, not static product "
    "leaderboards. Training, prompt tuning, or hyperparameter search on the held-out test "
    "split, repeated test submissions, oracle-agent inclusion, undisclosed scaffold changes, "
    "or treating local stub/smoke runs as scientific evidence will invalidate comparability. "
    "See docs/LEADERBOARD_PROTOCOL.md and docs/SPLIT_PROTOCOL.md."
)

REPORTING_RULES: dict[str, Any] = {
    "exclude_oracle_agents": True,
    "oracle_agent_ids": ["scripted_oracle_agent"],
    "disclose_prompts_and_scaffolds": True,
    "disclose_model_version": True,
    "disclose_cost_and_retries": True,
    "no_training_on_held_out_test": True,
    "official_headline_split": "test",
    "engineering_splits": sorted(ENGINEERING_SPLITS),
    "reserved_splits": ["heldout_templates"],
}


def default_splits_path(data: RunResults) -> Path:
    version = str(data.run_metadata.get("dataset_version") or "").strip()
    if version:
        candidate = Path("data/frozen") / version / "splits.json"
        if candidate.exists():
            return candidate
    return Path("data/frozen/pilot_v0.1/splits.json")


def load_split_policy(path: str | Path) -> dict[str, Any]:
    return read_json(Path(path))


def base_task_ids_for_eval_split(policy: dict[str, Any], eval_split: str) -> set[str]:
    if eval_split == "unfiltered":
        return set()
    split_names = SPLIT_ALIASES.get(eval_split)
    if split_names is None:
        raise ValueError(
            f"Unknown eval_split {eval_split!r}. "
            f"Expected one of: unfiltered, {', '.join(sorted(SPLIT_ALIASES))}."
        )
    base_ids: set[str] = set()
    splits = policy.get("splits", {})
    for name in split_names:
        section = splits.get(name)
        if not section:
            raise ValueError(f"Split {name!r} not found in splits policy.")
        base_ids.update(str(task_id) for task_id in section.get("base_task_ids", []))
    return base_ids


def filter_scores_by_base_tasks(scores: pd.DataFrame, base_task_ids: set[str]) -> pd.DataFrame:
    if scores.empty or not base_task_ids:
        return scores
    frame = scores.copy()
    if "base_task_id" not in frame.columns:
        if "diagnostic_base_task_id" in frame.columns:
            frame["base_task_id"] = frame["diagnostic_base_task_id"]
        else:
            frame["base_task_id"] = frame["instance_id"]
    return frame[frame["base_task_id"].astype(str).isin(base_task_ids)]


def scores_df_to_robustness_rows(scores: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in scores.to_dict(orient="records"):
        rows.append(
            {
                "agent_name": record["agent_name"],
                "metrics": {"final_success_binary": record.get("final_success_binary")},
                "diagnostics": {
                    "condition": record.get("diagnostic_condition"),
                    "intervention_family": record.get("diagnostic_intervention_family"),
                },
            }
        )
    return rows


def compute_split_metrics(data: RunResults, eval_split: str, splits_path: Path | None) -> dict[str, dict[str, Any]]:
    if eval_split == "unfiltered":
        return dict(data.aggregate.get("by_agent", {}))
    policy = load_split_policy(splits_path or default_splits_path(data))
    base_ids = base_task_ids_for_eval_split(policy, eval_split)
    filtered = filter_scores_by_base_tasks(data.scores_df, base_ids)
    return agent_robustness(scores_df_to_robustness_rows(filtered))


def _load_agent_run_configs(run_dir: Path) -> dict[str, dict[str, Any]]:
    config_path = run_dir / "config.yaml"
    if not config_path.exists():
        return {}
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    mapping: dict[str, dict[str, Any]] = {}
    for run in raw.get("agent_runs") or []:
        if not isinstance(run, dict):
            continue
        name = str(run.get("name") or run.get("agent") or "")
        if name:
            mapping[name] = run
    for agent in raw.get("agents") or []:
        if isinstance(agent, str):
            mapping.setdefault(agent, {"agent": agent})
    return mapping


def _agent_trajectory_metadata(data: RunResults, agent: str) -> dict[str, Any]:
    trajectories = data.trajectories_df
    if trajectories.empty or "agent_name" not in trajectories.columns:
        return {}
    agent_rows = trajectories[trajectories["agent_name"] == agent]
    if agent_rows.empty:
        return {}
    first = agent_rows.iloc[0]
    return {
        "agent_type": first.get("agent_type"),
        "model": first.get("model"),
        "provider": first.get("provider"),
        "prompt_version_hash": first.get("prompt_version_hash"),
        "prompt_template_hash": first.get("prompt_template_hash"),
        "prompt_files": first.get("prompt_files"),
    }


def _entry_id(agent: str, model: str, eval_split: str, run_dir: Path) -> str:
    payload = f"{LEADERBOARD_SCHEMA_ID}|{run_dir}|{agent}|{model}|{eval_split}"
    from causal_agent_bench.hashing import stable_hash

    return stable_hash({"payload": payload})[:16]


def build_leaderboard_entry(
    data: RunResults,
    *,
    agent: str,
    metrics: dict[str, Any],
    eval_split: str,
    agent_config: dict[str, Any] | None = None,
    trajectory_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agent_config = agent_config or {}
    trajectory_meta = trajectory_meta or {}
    model_ids = data.run_metadata.get("model_ids")
    default_model = model_ids[0] if isinstance(model_ids, list) and model_ids else "unknown"
    model = agent_config.get("model") or trajectory_meta.get("model") or default_model
    if isinstance(model, list):
        model = model[0] if model else "unknown"
    provider = agent_config.get("provider") or trajectory_meta.get("provider") or "unknown"
    agent_scaffold = (
        agent_config.get("agent")
        or trajectory_meta.get("agent_type")
        or agent
    )
    aggregate_row = data.aggregate.get("by_agent", {}).get(agent, {})
    trajectories = data.trajectories_df
    agent_trajectories = (
        trajectories[trajectories["agent_name"] == agent] if not trajectories.empty else trajectories
    )
    provenance = asset_metadata(data)
    submitted_at = provenance.get("timestamp") or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    families = metrics.get("families") or {}
    per_family_scores = {
        family: {
            "success_rate": row.get("success_rate"),
            "acrs_family": row.get("acrs_family"),
            "n": row.get("n"),
            "absolute_degradation": row.get("absolute_degradation"),
            "relative_degradation": row.get("relative_degradation"),
        }
        for family, row in sorted(families.items())
    }
    return {
        "entry_id": _entry_id(agent, str(model), eval_split, data.run_dir),
        "model": str(model),
        "agent_scaffold": str(agent_scaffold),
        "agent_run_name": agent,
        "provider": str(provider),
        "submitted_at": submitted_at,
        "dataset_version": provenance.get("dataset_version") or "unknown",
        "eval_split": eval_split,
        "leaderboard_eligibility": _leaderboard_eligibility(data, eval_split),
        "clean_success": metrics.get("clean_success_rate"),
        "intervention_success": metrics.get("intervention_success_rate"),
        "acrs": metrics.get("acrs"),
        "absolute_degradation": metrics.get("absolute_degradation"),
        "relative_degradation": metrics.get("relative_degradation"),
        "estimated_cost_usd": _round_metric(
            agent_trajectories.get("estimated_cost_usd", pd.Series(dtype=float)).dropna().sum()
            if not agent_trajectories.empty
            else aggregate_row.get("avg_cost_per_task_usd")
        ),
        "avg_cost_per_task_usd": aggregate_row.get("avg_cost_per_task_usd"),
        "avg_latency_s": _round_metric(
            agent_trajectories.get("latency_s", pd.Series(dtype=float)).dropna().mean()
            if not agent_trajectories.empty
            else aggregate_row.get("avg_latency_per_task_s")
        ),
        "per_family_scores": per_family_scores,
        "n_trajectories": metrics.get("n_trajectories"),
        "evidence_scope": data.run_metadata.get("evidence_scope") or "unknown",
        "engineering_only": _is_engineering_only(data),
        "retry_count": agent_config.get("retry_count"),
        "temperature": agent_config.get("temperature"),
        "prompt_version_hash": trajectory_meta.get("prompt_version_hash"),
        "prompt_template_hash": trajectory_meta.get("prompt_template_hash"),
        "prompt_files": trajectory_meta.get("prompt_files"),
        "config_hash": provenance.get("config_hash"),
        "seed": provenance.get("seed"),
        "git_commit": provenance.get("git_commit"),
        "run_dir": provenance.get("run_dir"),
        "scorer_versions": provenance.get("scorer_versions") or _scorer_versions(data),
    }


def _leaderboard_eligibility(data: RunResults, eval_split: str) -> str:
    if _is_engineering_only(data):
        return "engineering_export_only_not_official_submission"
    if eval_split in OFFICIAL_HEADLINE_SPLITS:
        return "eligible_for_official_headline_if_all_reporting_rules_met"
    if eval_split in ENGINEERING_SPLITS:
        return "engineering_or_method_development_only"
    if eval_split == "heldout_templates":
        return "reserved_split_not_for_public_ranking"
    if eval_split == "unfiltered":
        return "unfiltered_run_export_verify_eval_split_before_claims"
    return "verify_split_policy_before_claims"


def _is_engineering_only(data: RunResults) -> bool:
    scope = str(data.run_metadata.get("evidence_scope") or "")
    if scope in {"engineering_only", "local_stub", "deterministic_smoke"}:
        return True
    if scope.endswith("_unvalidated") or "stub" in scope or "smoke" in scope:
        return True
    run_name = str(data.run_metadata.get("run_name") or data.run_dir.name).lower()
    return "stub" in run_name or "smoke" in run_name or "dry_run" in run_name


def _round_metric(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 6)


def build_leaderboard_entries(
    data: RunResults,
    *,
    eval_split: str = "unfiltered",
    splits_path: Path | None = None,
) -> list[dict[str, Any]]:
    metrics_by_agent = compute_split_metrics(data, eval_split, splits_path)
    agent_configs = _load_agent_run_configs(data.run_dir)
    entries: list[dict[str, Any]] = []
    for agent, metrics in sorted(metrics_by_agent.items()):
        if _is_oracle_agent(agent):
            continue
        entries.append(
            build_leaderboard_entry(
                data,
                agent=agent,
                metrics=metrics,
                eval_split=eval_split,
                agent_config=agent_configs.get(agent),
                trajectory_meta=_agent_trajectory_metadata(data, agent),
            )
        )
    return entries


def build_leaderboard_document(
    data: RunResults,
    *,
    eval_split: str = "unfiltered",
    splits_path: Path | None = None,
) -> dict[str, Any]:
    policy_path = splits_path or default_splits_path(data)
    split_policy_name = None
    if eval_split != "unfiltered" and policy_path.exists():
        split_policy_name = load_split_policy(policy_path).get("policy_name")
    provenance = asset_metadata(data)
    return {
        "schema_version": LEADERBOARD_SCHEMA_VERSION,
        "schema_id": LEADERBOARD_SCHEMA_ID,
        "generated_at": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "eval_split": eval_split,
        "split_policy_name": split_policy_name,
        "splits_path": str(policy_path) if eval_split != "unfiltered" else None,
        "contamination_warning": CONTAMINATION_WARNING,
        "reporting_rules": REPORTING_RULES,
        "provenance": provenance,
        "entries": build_leaderboard_entries(data, eval_split=eval_split, splits_path=splits_path),
    }


def leaderboard_to_dataframe(document: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for entry in document.get("entries", []):
        row = {key: value for key, value in entry.items() if key != "per_family_scores"}
        row["per_family_scores_json"] = json.dumps(
            entry.get("per_family_scores") or {}, sort_keys=True
        )
        rows.append(row)
    if not rows:
        return pd.DataFrame(
            [
                {
                    "status": "empty",
                    "note": "No non-oracle leaderboard rows were found for this run.",
                    "eval_split": document.get("eval_split"),
                }
            ]
        )
    return pd.DataFrame(rows)


def leaderboard_to_markdown(document: dict[str, Any]) -> str:
    lines = [
        "# Causal Agent Bench Leaderboard Export",
        "",
        f"- Schema: `{document.get('schema_id')}` v{document.get('schema_version')}",
        f"- Generated: `{document.get('generated_at')}`",
        f"- Eval split: `{document.get('eval_split')}`",
        f"- Split policy: `{document.get('split_policy_name') or 'n/a'}`",
        f"- Run dir: `{document.get('provenance', {}).get('run_dir', 'unknown')}`",
        "",
        "## Reporting rules",
        "",
    ]
    for key, value in (document.get("reporting_rules") or {}).items():
        lines.append(f"- **{key}**: `{value}`")
    lines.extend(
        [
            "",
            "## Contamination / gaming warning",
            "",
            document.get("contamination_warning", ""),
            "",
            "## Entries",
            "",
            dataframe_to_markdown(leaderboard_to_dataframe(document)),
        ]
    )
    return "\n".join(lines)


def export_leaderboard(
    run_dir: str | Path,
    output_dir: str | Path | None = None,
    *,
    eval_split: str = "unfiltered",
    splits_path: str | Path | None = None,
    allow_engineering_only: bool = False,
    allow_incomplete: bool = False,
    allow_placeholder: bool = False,
    allow_mock_stub: bool = False,
) -> list[Path]:
    from causal_agent_bench.analysis.load_results import load_run_results
    from causal_agent_bench.safety.export_guards import (
        apply_export_watermark,
        validate_export_source,
    )

    guard = validate_export_source(
        run_dir,
        allow_engineering_only=allow_engineering_only,
        allow_incomplete=allow_incomplete,
        allow_placeholder=allow_placeholder,
        allow_mock_stub=allow_mock_stub,
        operation="export-leaderboard",
    )
    data = load_run_results(run_dir)
    resolved_splits = Path(splits_path) if splits_path else None
    document = build_leaderboard_document(
        data, eval_split=eval_split, splits_path=resolved_splits
    )
    out = Path(output_dir) if output_dir else Path(run_dir) / "leaderboard"
    out.mkdir(parents=True, exist_ok=True)
    stem = f"leaderboard_v1_{eval_split}"
    json_path = out / f"{stem}.json"
    csv_path = out / f"{stem}.csv"
    md_path = out / f"{stem}.md"
    json_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    leaderboard_to_dataframe(document).to_csv(csv_path, index=False)
    md_body = leaderboard_to_markdown(document)
    if guard.get("watermark"):
        md_body = apply_export_watermark(md_body, guard["watermark"])
    md_path.write_text(md_body, encoding="utf-8")
    return [json_path, csv_path, md_path]
