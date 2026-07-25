"""Static config profile classification for no-run governance."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.safety.common import (
    is_real_provider_type,
    section_markdown,
    strict_bool,
    write_dual_report,
)

PROFILES = {
    "smoke_engineering",
    "mock_diagnostic",
    "oracle_sanity",
    "local_preliminary",
    "provider_pilot_template",
    "provider_pilot_approved",
    "commercial_api",
    "main_benchmark_candidate",
    "ablation",
    "unknown_needs_review",
}


def build_config_profiles(
    repo_root: str | Path,
    *,
    config_dir: str | Path = "configs",
    output_dir: str | Path = "reports/config_profiles",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    configs = Path(config_dir)
    if not configs.is_absolute():
        configs = root / configs
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    profiles = [
        classify_config_profile(path, repo_root=root)
        for path in sorted(configs.rglob("*.yaml"))
    ] if configs.exists() else []
    summary = {
        "config_count": len(profiles),
        "profile_counts": _counts(row["profile"] for row in profiles),
        "issue_count": sum(len(row["safety_issues"]) for row in profiles),
        "claims_promoted": False,
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static config profile classification only; no configs are run and no providers are called.",
        "summary": summary,
        "profiles": profiles,
    }
    md = config_profiles_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="config_profiles",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def classify_config_profile(path: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = root / config_path
    rel = _rel(config_path, root)
    raw = _read_yaml(config_path)
    issues: list[dict[str, str]] = []
    profile = _profile_for_config(raw, rel, root)
    provider_type = _provider_type(raw)
    allow_paid_calls = raw.get("allow_paid_calls")
    agent_type = _agent_type(raw)
    trajectory_cap = _trajectory_cap(raw)
    budget_cap = _budget_cap(raw)
    scientific_evidence_default = raw.get("scientific_evidence", False)
    evidence_scope = str(raw.get("evidence_scope") or "unknown")

    approval = raw.get("approval") if isinstance(raw.get("approval"), dict) else {}
    has_approval_markers = bool(
        approval.get("advisor_approval_id")
        and (approval.get("approved_for_live_run") or approval.get("approved_for_dry_run"))
    )
    if profile == "provider_pilot_approved" and not has_approval_markers:
        profile = "provider_pilot_template" if "template" in rel.lower() else "unknown_needs_review"
        issues.append(_issue("approval_markers_missing", "Provider-pilot approved profile requires machine-readable approval markers."))
    if profile == "provider_pilot_approved" and not is_real_provider_type(provider_type):
        profile = "unknown_needs_review"
        issues.append(_issue("approved_provider_not_real", "Approved provider config must use a provider-backed provider type."))
    if profile in {"provider_pilot_template", "smoke_engineering", "mock_diagnostic", "oracle_sanity", "local_preliminary"} and strict_bool(scientific_evidence_default):
        issues.append(_issue("non_empirical_profile_scientific_evidence_true", "Local/mock/oracle/template configs must not default to paper evidence."))
    if profile == "provider_pilot_template" and allow_paid_calls is not False:
        issues.append(_issue("provider_template_paid_calls_not_false", "Provider pilot templates must keep allow_paid_calls=false."))
    if profile == "commercial_api":
        issues.append(_issue("commercial_api_not_auto_paper_evidence", "Commercial API configs are not automatically paper evidence."))
    if profile == "main_benchmark_candidate" and not _has_split_or_frozen_metadata(raw, root):
        issues.append(_issue("main_candidate_missing_split_metadata", "Main benchmark candidates require split/heldout/frozen metadata."))
    if profile == "unknown_needs_review":
        issues.append(_issue("unknown_profile_needs_review", "Config did not match a known safe profile."))
    if is_real_provider_type(provider_type) and allow_paid_calls is None:
        issues.append(_issue("allow_paid_calls_missing", "Provider-looking configs must set allow_paid_calls explicitly."))

    readiness_status = _readiness_status(profile, issues, allow_paid_calls)
    return {
        "path": rel,
        "profile": profile,
        "allow_paid_calls": allow_paid_calls,
        "provider_type": provider_type,
        "agent_type": agent_type,
        "trajectory_cap": trajectory_cap,
        "budget_cap": budget_cap,
        "scientific_evidence_default": scientific_evidence_default,
        "evidence_scope": evidence_scope,
        "safety_issues": issues,
        "readiness_status": readiness_status,
        "paper_eligible_by_default": False,
    }


def config_profiles_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Config Profiles",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Configs scanned: {summary['config_count']}",
                f"- Profile counts: {summary['profile_counts']}",
                f"- Safety issues: {summary['issue_count']}",
                "- Claims promoted: `False`",
            ],
        ),
        "## Profiles",
        "",
        "| Path | Profile | Paid calls | Provider | Evidence scope | Readiness | Issues |",
        "|---|---|---:|---|---|---|---:|",
    ]
    for row in payload["profiles"]:
        lines.append(
            f"| `{row['path']}` | `{row['profile']}` | `{row['allow_paid_calls']}` | "
            f"`{row['provider_type']}` | `{row['evidence_scope']}` | `{row['readiness_status']}` | {len(row['safety_issues'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def _profile_for_config(raw: dict[str, Any], rel: str, root: Path) -> str:
    haystack = " ".join([rel, str(raw.get("run_name", "")), str(raw.get("evidence_scope", "")), str(raw.get("provider", "")), json.dumps(raw.get("agent_runs", []), sort_keys=True, default=str)]).lower()
    provider = _provider_type(raw)
    approval = raw.get("approval") if isinstance(raw.get("approval"), dict) else {}
    if "smoke" in haystack:
        return "smoke_engineering"
    if "mock" in haystack or "stub" in haystack or raw.get("not_real_llm_behavior") is True:
        return "mock_diagnostic"
    if "oracle" in haystack:
        return "oracle_sanity"
    if "ablation" in haystack:
        return "ablation"
    if "template" in haystack and "provider" in haystack:
        return "provider_pilot_template"
    if "approved" in haystack or approval:
        return "provider_pilot_approved"
    if "commercial_api" in haystack or "commercial api" in haystack:
        return "commercial_api"
    if "main" in haystack and is_real_provider_type(provider):
        return "main_benchmark_candidate"
    if "local" in haystack or not is_real_provider_type(provider):
        return "local_preliminary" if provider and provider not in {"unknown", ""} else "unknown_needs_review"
    if "pilot" in haystack and is_real_provider_type(provider):
        return "provider_pilot_template"
    return "unknown_needs_review"


def _provider_type(raw: dict[str, Any]) -> str:
    if raw.get("provider"):
        return str(raw.get("provider")).lower()
    providers = []
    if isinstance(raw.get("agent_runs"), list):
        for row in raw["agent_runs"]:
            if isinstance(row, dict) and row.get("provider"):
                providers.append(str(row["provider"]).lower())
    if not providers:
        return "unknown"
    unique = sorted(set(providers))
    return unique[0] if len(unique) == 1 else "mixed:" + ",".join(unique)


def _agent_type(raw: dict[str, Any]) -> str:
    agents = []
    if isinstance(raw.get("agent_runs"), list):
        agents = [str(row.get("agent") or row.get("name") or "") for row in raw["agent_runs"] if isinstance(row, dict)]
    elif isinstance(raw.get("agents"), list):
        agents = [str(agent) for agent in raw["agents"]]
    return ",".join(sorted({agent for agent in agents if agent})) or "unknown"


def _trajectory_cap(raw: dict[str, Any]) -> Any:
    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    for key in ("max_instances", "max_api_calls", "max_trajectories", "stop_after_trajectories"):
        if raw.get(key) is not None:
            return raw.get(key)
        if limits.get(key) is not None:
            return limits.get(key)
    return None


def _budget_cap(raw: dict[str, Any]) -> Any:
    budget = raw.get("budget") if isinstance(raw.get("budget"), dict) else {}
    return raw.get("budget_cap_usd") if raw.get("budget_cap_usd") is not None else budget.get("max_total_usd")


def _has_split_or_frozen_metadata(raw: dict[str, Any], root: Path) -> bool:
    if raw.get("split") or raw.get("eval_split") or raw.get("frozen_dataset") or raw.get("dataset_version"):
        return True
    benchmark = raw.get("benchmark_path") or raw.get("instances_path") or raw.get("dataset_path")
    if not benchmark:
        return False
    path = Path(str(benchmark))
    if not path.is_absolute():
        path = root / path
    base = path.parent if path.suffix else path
    return (base / "splits.json").exists() or (base / "freeze_manifest.json").exists()


def _readiness_status(profile: str, issues: list[dict[str, str]], allow_paid_calls: Any) -> str:
    if any("missing" in issue["id"] or "not_real" in issue["id"] for issue in issues):
        return "needs_review"
    if profile == "provider_pilot_approved":
        return "ready_for_advisor_review" if allow_paid_calls is False else "approved_copy_review_required"
    if profile == "provider_pilot_template":
        return "template_only"
    if profile in {"smoke_engineering", "mock_diagnostic", "oracle_sanity", "local_preliminary", "ablation"}:
        return "engineering_only"
    if profile == "commercial_api":
        return "not_paper_evidence_without_run_review"
    if profile == "main_benchmark_candidate":
        return "candidate_needs_freeze_review"
    return "needs_review"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _issue(issue_id: str, message: str) -> dict[str, str]:
    return {"id": issue_id, "severity": "warning", "message": message}


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
