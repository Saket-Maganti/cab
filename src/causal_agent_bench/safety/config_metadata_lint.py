"""Static config and metadata linter for no-run safety gates."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.safety.common import (
    is_real_provider_type,
    section_markdown,
    write_dual_report,
)


def build_config_metadata_lint(
    repo_root: str | Path,
    *,
    config_dir: str | Path = "configs",
    output_dir: str | Path = "reports/config_lint",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    configs = Path(config_dir)
    if not configs.is_absolute():
        configs = root / configs
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    issues: list[dict[str, Any]] = []
    for path in sorted(configs.rglob("*.yaml")) if configs.exists() else []:
        issues.extend(lint_config_file(path, repo_root=root))
    severity_counts: dict[str, int] = {}
    for issue in issues:
        severity_counts[issue["severity"]] = severity_counts.get(issue["severity"], 0) + 1
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static config/metadata lint only; no API keys, providers, or benchmark runs.",
        "config_count": len(list(configs.rglob("*.yaml"))) if configs.exists() else 0,
        "issue_count": len(issues),
        "summary": {
            "config_count": len(list(configs.rglob("*.yaml"))) if configs.exists() else 0,
            "issue_count": len(issues),
            "blockers": severity_counts.get("blocker", 0),
            "warnings": severity_counts.get("warning", 0),
            "informational": severity_counts.get("informational", 0),
        },
        "verdicts": {
            "lint_passed": severity_counts.get("blocker", 0) == 0,
            "needs_review": severity_counts.get("warning", 0) > 0 or severity_counts.get("blocker", 0) > 0,
        },
        "issues": sorted(issues, key=lambda row: (row["severity"], row["path"], row["id"])),
    }
    md = config_metadata_lint_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="config_metadata_lint",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def lint_config_file(path: str | Path, *, repo_root: str | Path | None = None) -> list[dict[str, Any]]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    config_path = Path(path)
    rel = _rel(config_path, root)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return [_issue(rel, "blocker", "invalid_yaml", str(exc))]
    if not isinstance(raw, dict):
        return [_issue(rel, "blocker", "invalid_config_root", "Config root is not a mapping.")]
    issues: list[dict[str, Any]] = []
    agent_runs = raw.get("agent_runs") if isinstance(raw.get("agent_runs"), list) else []
    providers = [str(run.get("provider") or raw.get("provider") or "") for run in agent_runs if isinstance(run, dict)]
    if not providers and raw.get("provider"):
        providers = [str(raw.get("provider"))]
    provider_backed = any(is_real_provider_type(provider) for provider in providers)
    mockish = _mockish(raw, rel, agent_runs)
    if provider_backed:
        if "allow_paid_calls" not in raw:
            issues.append(_issue(rel, "blocker", "allow_paid_calls_missing", "Provider config must set allow_paid_calls explicitly."))
        if raw.get("budget_cap_usd") is None and not (isinstance(raw.get("budget"), dict) and raw["budget"].get("max_total_usd") is not None):
            issues.append(_issue(rel, "blocker", "budget_cap_missing", "Provider config must have a budget cap."))
        if not _trajectory_cap(raw):
            issues.append(_issue(rel, "blocker", "trajectory_cap_missing", "Provider config must have tiny trajectory/stop caps."))
    if mockish:
        if raw.get("scientific_evidence") is not False:
            issues.append(_issue(rel, "warning", "mock_scientific_evidence_not_false", "Mock/synthetic configs must be non-scientific."))
        if "not_real_llm_behavior" not in raw and "mock" in rel.lower():
            issues.append(_issue(rel, "warning", "mock_missing_not_real_llm_behavior", "Mock configs should mark not_real_llm_behavior."))
    if "oracle" in rel.lower() and "engineering" not in str(raw.get("evidence_scope", "")).lower() and raw.get("evidence_scope") != "oracle_sanity_only":
        issues.append(_issue(rel, "warning", "oracle_not_engineering_only", "Oracle configs should be engineering/oracle-only."))
    if "template" in rel.lower() and raw.get("allow_paid_calls") is not False:
        issues.append(_issue(rel, "blocker", "template_runnable_by_default", "Provider pilot templates must not be runnable by default."))
    if "approved" in rel.lower() and "approval" not in raw:
        issues.append(_issue(rel, "warning", "approved_missing_approval_markers", "APPROVED config should include machine-readable approval markers."))
    if (provider_backed or mockish) and not raw.get("evidence_scope"):
        issues.append(_issue(rel, "warning", "evidence_scope_missing", "Config should declare evidence_scope."))
    if provider_backed and any(not is_real_provider_type(provider) for provider in providers):
        issues.append(_issue(rel, "warning", "mixed_provider_types", "Provider-looking config includes local/mock provider entries."))
    if _provider_looking_local(rel, providers):
        issues.append(_issue(rel, "warning", "provider_name_local_provider", "Config name looks provider-backed but provider is local/mock/stub."))
    return issues


def config_metadata_lint_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Config Metadata Lint",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown("Summary", [f"- Configs scanned: {payload['config_count']}", f"- Issues: {payload['issue_count']}"]),
        "## Issues",
        "",
    ]
    if not payload["issues"]:
        lines.append("- (none)")
    for issue in payload["issues"]:
        lines.append(f"- `{issue['severity']}` `{issue['path']}` `{issue['id']}`: {issue['message']}")
    lines.append("")
    return "\n".join(lines)


def _issue(path: str, severity: str, issue_id: str, message: str) -> dict[str, str]:
    return {"path": path, "severity": severity, "id": issue_id, "message": message}


def _mockish(raw: dict[str, Any], rel: str, agent_runs: list[Any]) -> bool:
    haystack = " ".join([rel, str(raw.get("provider", "")), str(raw.get("run_name", "")), json.dumps(agent_runs, sort_keys=True)]).lower()
    return any(marker in haystack for marker in ("mock", "stub", "synthetic", "local_stub"))


def _trajectory_cap(raw: dict[str, Any]) -> bool:
    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    return any(raw.get(key) is not None for key in ("max_instances", "max_api_calls")) or any(
        limits.get(key) is not None for key in ("max_trajectories", "stop_after_trajectories", "max_instances")
    )


def _provider_looking_local(rel: str, providers: list[str]) -> bool:
    name = rel.lower()
    provider_looking = any(marker in name for marker in ("provider", "openai", "anthropic", "gemini", "openrouter"))
    local_provider = providers and all(not is_real_provider_type(provider) for provider in providers)
    return provider_looking and local_provider


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
