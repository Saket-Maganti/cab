"""No-run cost estimator and provider-pilot run planner."""

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

DEFAULT_PROMPT_TOKEN_RANGE = (1000, 2000)


def build_run_cost_estimate(
    repo_root: str | Path,
    *,
    config_path: str | Path,
    output_dir: str | Path = "reports/cost_estimates",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = root / config_file
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    estimate = estimate_run_cost(config_file, repo_root=root)
    # Surface a clear summary/verdicts block so report-quality and dashboards see it.
    if "summary" not in estimate or not isinstance(estimate.get("summary"), dict):
        estimate["summary"] = {
            "config_path": str(config_file),
            "pricing_known": estimate.get("pricing_known"),
            "estimated_low_cost_usd": estimate.get("estimated_low_cost_usd"),
            "estimated_high_cost_usd": estimate.get("estimated_high_cost_usd"),
            "warnings_count": len(estimate.get("warnings") or []),
            "blockers_count": len(estimate.get("blockers") or []),
        }
    if "verdicts" not in estimate or not isinstance(estimate.get("verdicts"), dict):
        estimate["verdicts"] = {
            "pricing_known": bool(estimate.get("pricing_known")),
            "no_blockers": len(estimate.get("blockers") or []) == 0,
            "ready_for_budget_review": bool(estimate.get("pricing_known")) and len(estimate.get("blockers") or []) == 0,
        }
    if "scope" not in estimate:
        estimate["scope"] = "Static cost estimate only; no provider/API call is made."
    md = run_cost_estimate_markdown(estimate)
    md_path, json_path = write_dual_report(
        stem="run_cost_estimate",
        payload=estimate,
        markdown=md,
        output_dir=out,
    )
    estimate["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(estimate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return estimate


def estimate_run_cost(config_path: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = root / config_file
    raw = _load_yaml(config_file)
    warnings: list[str] = []
    blockers: list[str] = []
    agent_runs = raw.get("agent_runs") or [
        {
            "agent": agent,
            "provider": raw.get("provider"),
            "model": raw.get("model"),
            "max_tokens": raw.get("max_tokens", 1024),
            "pricing": raw.get("pricing", {}),
        }
        for agent in raw.get("agents", [])
    ]
    benchmark_path = _resolve_benchmark_path(raw, config_file, root)
    instance_count = _count_jsonl(benchmark_path)
    if raw.get("max_instances") is not None:
        instance_count = min(instance_count, int(raw["max_instances"]))
    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    if limits.get("max_instances") is not None:
        instance_count = min(instance_count, int(limits["max_instances"]))
    agent_count = len(agent_runs)
    num_repeats = int(raw.get("num_repeats") or 1)
    max_steps = int(limits.get("max_steps_per_instance") or raw.get("max_steps") or 1)
    max_trajectories = _first_int(
        limits.get("max_trajectories"),
        limits.get("stop_after_trajectories"),
        raw.get("max_trajectories"),
    )
    trajectories = instance_count * max(agent_count, 1) * num_repeats
    if max_trajectories is not None:
        trajectories = min(trajectories, max_trajectories)
    estimated_model_calls = trajectories * max_steps

    pricing_registry = _load_pricing_registry(raw, config_file, root)
    per_agent: list[dict[str, Any]] = []
    total_prompt_low = 0
    total_prompt_high = 0
    total_completion_high = 0
    known_low_cost = 0.0
    known_high_cost = 0.0
    all_pricing_known = True

    for agent_run in agent_runs:
        provider = str(agent_run.get("provider") or raw.get("provider") or "").strip()
        model = str(agent_run.get("model") or raw.get("model") or "").strip()
        per_call_prompt = _prompt_range(agent_run)
        completion_tokens = int(
            limits.get("max_output_tokens") or agent_run.get("max_tokens") or raw.get("max_tokens") or 1024
        )
        calls = estimated_model_calls if provider else 0
        prompt_low = calls * per_call_prompt[0]
        prompt_high = calls * per_call_prompt[1]
        completion_high = calls * completion_tokens
        pricing, pricing_source, pricing_known = _resolve_pricing(
            raw,
            agent_run,
            provider=provider,
            model=model,
            pricing_registry=pricing_registry,
        )
        evidence_provider = bool(provider and is_real_provider_type(provider))
        if not evidence_provider:
            warnings.append(
                f"Agent {agent_run.get('name') or agent_run.get('agent')} uses local/mock/oracle/non-provider family; not provider evidence."
            )
        low_cost: float | None = None
        high_cost: float | None = None
        if provider and evidence_provider and pricing_known:
            low_cost = _cost(prompt_low, 0, pricing)
            high_cost = _cost(prompt_high, completion_high, pricing)
            known_low_cost += low_cost
            known_high_cost += high_cost
        elif provider and evidence_provider:
            all_pricing_known = False
            warnings.append(f"Pricing unknown for provider={provider!r}, model={model!r}; cost is not assumed zero.")
        per_agent.append(
            {
                "agent": agent_run.get("agent"),
                "name": agent_run.get("name"),
                "provider": provider or None,
                "model": model or None,
                "provider_evidence_candidate": evidence_provider,
                "estimated_model_calls": calls,
                "estimated_prompt_tokens_low": prompt_low,
                "estimated_prompt_tokens_high": prompt_high,
                "estimated_completion_tokens_high": completion_high,
                "pricing_source": pricing_source,
                "pricing_known": pricing_known,
                "estimated_low_cost_usd": round(low_cost, 8) if low_cost is not None else None,
                "estimated_high_cost_usd": round(high_cost, 8) if high_cost is not None else None,
            }
        )
        total_prompt_low += prompt_low
        total_prompt_high += prompt_high
        total_completion_high += completion_high

    budget_cap = _budget_cap(raw)
    allow_paid_calls = bool(raw.get("allow_paid_calls", False))
    is_template = _is_template_config(raw, config_file)
    if not allow_paid_calls:
        blockers.append("allow_paid_calls=false; run is not approved for paid execution.")
    if is_template:
        blockers.append("config appears to be a template/pending-approval file and is not runnable as-is.")
    if budget_cap is None:
        warnings.append("No budget cap detected.")
    elif all_pricing_known and known_high_cost > budget_cap:
        blockers.append(f"Estimated high cost ${known_high_cost:.4f} exceeds budget cap ${budget_cap:.4f}.")
    if not all_pricing_known:
        warnings.append("Unknown pricing prevents a complete dollar estimate.")

    budget = raw.get("budget") if isinstance(raw.get("budget"), dict) else {}
    approval = raw.get("approval") if isinstance(raw.get("approval"), dict) else {}
    approval_status = {
        "advisor_approved": bool(approval.get("advisor_approved")),
        "budget_approved": bool(approval.get("budget_approved")),
        "approved_for_dry_run": bool(approval.get("approved_for_dry_run")),
        "approved_for_live_run": bool(approval.get("approved_for_live_run")),
    }
    if budget.get("max_calls") is not None and estimated_model_calls > int(budget["max_calls"]):
        blockers.append(
            f"Estimated model calls {estimated_model_calls} exceed budget.max_calls {budget['max_calls']}."
        )
    runtime_range_minutes = _runtime_range_minutes(estimated_model_calls)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static cost/run planner only; no benchmark, provider, API key, or model call is invoked.",
        "config_path": str(config_file),
        "config_run_name": raw.get("run_name"),
        "template_or_pending_approval": is_template,
        "runnable_without_approval": False if blockers else allow_paid_calls,
        "not_runnable_without_approval": bool(blockers) or is_template or not allow_paid_calls,
        "approval_status": approval_status,
        "provider_families": sorted({str(row.get("provider") or "") for row in per_agent if row.get("provider")}),
        "allow_paid_calls": allow_paid_calls,
        "benchmark_path": str(benchmark_path) if benchmark_path else None,
        "number_of_instances": instance_count,
        "number_of_agent_runs": agent_count,
        "num_repeats": num_repeats,
        "number_of_trajectories": trajectories,
        "max_trajectories": max_trajectories,
        "max_steps_per_trajectory": max_steps,
        "estimated_model_calls": estimated_model_calls,
        "estimated_prompt_tokens_low": total_prompt_low,
        "estimated_prompt_tokens_high": total_prompt_high,
        "estimated_completion_tokens_high": total_completion_high,
        "estimated_total_tokens_low": total_prompt_low,
        "estimated_total_tokens_high": total_prompt_high + total_completion_high,
        "estimated_low_cost_usd": round(known_low_cost, 8) if all_pricing_known else None,
        "estimated_high_cost_usd": round(known_high_cost, 8) if all_pricing_known else None,
        "price_source": "config/model_pricing if present; otherwise unknown",
        "pricing_known": all_pricing_known,
        "budget_cap_usd": budget_cap,
        "budget_cap_exists": budget_cap is not None,
        "rate_limit_risk": _rate_limit_risk(estimated_model_calls, budget),
        "expected_runtime_range_minutes": runtime_range_minutes,
        "stop_conditions": _stop_conditions(raw, limits),
        "resume_checkpoint_requirements": (
            "Use checkpoint/resume metadata before provider execution; do not run templates in place."
        ),
        "agent_runs": per_agent,
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
    }


def run_cost_estimate_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Run Cost Estimate",
        "",
        f"Generated: {report['generated_at']}",
        "",
        report["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Config: `{report['config_path']}`",
                f"- Run name: `{report.get('config_run_name')}`",
                f"- Runnable without approval: `{report['runnable_without_approval']}`",
                f"- Not runnable without approval: `{report.get('not_runnable_without_approval', True)}`",
                f"- Template/pending: `{report['template_or_pending_approval']}`",
                f"- allow_paid_calls: `{report['allow_paid_calls']}`",
                f"- Approval status: `{report.get('approval_status')}`",
                f"- Provider families: `{report.get('provider_families')}`",
                f"- Trajectories: {report['number_of_trajectories']}",
                f"- Estimated model calls: {report['estimated_model_calls']}",
                f"- Total tokens range: {report['estimated_total_tokens_low']} to {report['estimated_total_tokens_high']}",
                f"- Estimated cost range: `{report['estimated_low_cost_usd']}` to `{report['estimated_high_cost_usd']}` USD",
                f"- Budget cap: `{report['budget_cap_usd']}`",
                f"- Rate-limit risk: `{report['rate_limit_risk']}`",
            ],
        ),
        section_markdown("Blockers", [f"- {item}" for item in report["blockers"]]),
        section_markdown("Warnings", [f"- {item}" for item in report["warnings"]]),
        "## Agent Runs",
        "",
    ]
    for row in report["agent_runs"]:
        lines.extend(
            [
                f"### `{row.get('name') or row.get('agent')}`",
                "",
                f"- Provider/model: `{row['provider']}` / `{row['model']}`",
                f"- Provider evidence candidate: `{row['provider_evidence_candidate']}`",
                f"- Calls: {row['estimated_model_calls']}",
                f"- Pricing: `{row['pricing_source']}` known=`{row['pricing_known']}`",
                f"- High cost: `{row['estimated_high_cost_usd']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _resolve_benchmark_path(raw: dict[str, Any], config_file: Path, root: Path) -> Path | None:
    value = raw.get("benchmark_path")
    if not value and raw.get("benchmark_dir"):
        value = str(Path(str(raw["benchmark_dir"])) / "instances.jsonl")
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_absolute() else root / path


def _count_jsonl(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _first_int(*values: Any) -> int | None:
    for value in values:
        if value is not None:
            return int(value)
    return None


def _prompt_range(agent_run: dict[str, Any]) -> tuple[int, int]:
    extra = agent_run.get("extra") if isinstance(agent_run.get("extra"), dict) else {}
    estimate = extra.get("input_tokens_per_call_estimate")
    if estimate is not None:
        value = int(estimate)
        return (value, value)
    return DEFAULT_PROMPT_TOKEN_RANGE


def _load_pricing_registry(raw: dict[str, Any], config_file: Path, root: Path) -> list[dict[str, Any]]:
    value = raw.get("pricing_registry_path")
    if not value:
        return []
    path = Path(str(value))
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("models"), list):
        return [row for row in data["models"] if isinstance(row, dict)]
    return []


def _resolve_pricing(
    raw: dict[str, Any],
    agent_run: dict[str, Any],
    *,
    provider: str,
    model: str,
    pricing_registry: list[dict[str, Any]],
) -> tuple[dict[str, float], str, bool]:
    pricing = agent_run.get("pricing") if isinstance(agent_run.get("pricing"), dict) else {}
    if _pricing_complete(pricing):
        return pricing, "agent_run.pricing", True
    config_pricing = raw.get("pricing") if isinstance(raw.get("pricing"), dict) else {}
    if _pricing_complete(config_pricing):
        return config_pricing, "config.pricing", True
    cost_models = raw.get("cost_models") if isinstance(raw.get("cost_models"), dict) else {}
    provider_models = cost_models.get(provider) if isinstance(cost_models.get(provider), dict) else {}
    for key in (model, "*", "default"):
        row = provider_models.get(key)
        if isinstance(row, dict) and _pricing_complete(row):
            return row, f"config.cost_models.{provider}.{key}", True
    for row in pricing_registry:
        if row.get("provider") != provider:
            continue
        if row.get("model_id") in {model, "default"} and row.get("pricing_known") is not False:
            candidate = {
                "input_per_1m_tokens": row.get("input_per_1m_tokens"),
                "output_per_1m_tokens": row.get("output_per_1m_tokens"),
            }
            if _pricing_complete(candidate):
                return candidate, f"pricing_registry:{row.get('model_id')}", True
    return {}, "unknown", False


def _pricing_complete(pricing: dict[str, Any]) -> bool:
    return pricing.get("input_per_1m_tokens") is not None and pricing.get("output_per_1m_tokens") is not None


def _cost(input_tokens: int, output_tokens: int, pricing: dict[str, Any]) -> float:
    return (
        input_tokens * float(pricing["input_per_1m_tokens"])
        + output_tokens * float(pricing["output_per_1m_tokens"])
    ) / 1_000_000


def _budget_cap(raw: dict[str, Any]) -> float | None:
    budget = raw.get("budget") if isinstance(raw.get("budget"), dict) else {}
    value = budget.get("max_total_usd", raw.get("budget_cap_usd"))
    return float(value) if value is not None else None


def _rate_limit_risk(calls: int, budget: dict[str, Any]) -> str:
    max_calls = budget.get("max_calls")
    if max_calls is not None and calls > int(max_calls):
        return "high"
    if calls > 1000:
        return "medium"
    return "low"


def _runtime_range_minutes(calls: int) -> dict[str, float]:
    return {"low": round(calls * 1.0 / 60, 2), "high": round(calls * 5.0 / 60, 2)}


def _stop_conditions(raw: dict[str, Any], limits: dict[str, Any]) -> dict[str, Any]:
    return {
        "max_instances": raw.get("max_instances") or limits.get("max_instances"),
        "max_trajectories": limits.get("max_trajectories"),
        "stop_after_trajectories": limits.get("stop_after_trajectories"),
        "max_runtime_minutes": limits.get("max_runtime_minutes"),
        "max_steps_per_instance": limits.get("max_steps_per_instance") or raw.get("max_steps"),
    }


def _is_template_config(raw: dict[str, Any], config_file: Path) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in (
            config_file.name,
            raw.get("run_name"),
            raw.get("evidence_scope"),
            json.dumps(raw.get("agent_runs", []), sort_keys=True),
        )
    ).lower()
    return any(marker in haystack for marker in ("template", "pending", "placeholder", "set_before_run"))


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
