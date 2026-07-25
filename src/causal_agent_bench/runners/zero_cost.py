from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from causal_agent_bench.runners.config import (
    ORACLE_AGENT_NAMES,
    PAID_PROVIDERS,
    PROVIDER_MODEL_ENV_VARS,
    ZERO_COST_BLOCKED_PROVIDERS,
    ZERO_COST_LOCAL_PROVIDERS,
    AgentRunConfig,
    ExperimentConfig,
    is_free_tier_agent_run,
    load_experiment_config,
)
from causal_agent_bench.runners.costing import estimate_experiment_cost

ZeroCostVerdict = Literal["not_ready", "dry_run_ready", "zero_cost_ready"]

_ENV_REF_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")


@dataclass
class ZeroCostCheck:
    name: str
    passed: bool
    severity: Literal["info", "warning", "error"] = "info"
    message: str = ""
    fix: str | None = None


@dataclass
class ZeroCostReadinessReport:
    config_path: str
    verdict: ZeroCostVerdict
    checks: list[ZeroCostCheck] = field(default_factory=list)
    cost_estimate: dict[str, Any] | None = None
    dry_run_summary: dict[str, Any] | None = None
    metadata_preview: dict[str, Any] | None = None
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_path": self.config_path,
            "verdict": self.verdict,
            "blockers": self.blockers,
            "checks": [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "severity": check.severity,
                    "message": check.message,
                    "fix": check.fix,
                }
                for check in self.checks
            ],
            "cost_estimate": self.cost_estimate,
            "dry_run": {
                "executed": self.dry_run_summary is not None,
                "paid_calls_made": (self.dry_run_summary or {}).get("paid_calls_made"),
                "scientific_evidence": (self.dry_run_summary or {}).get("scientific_evidence"),
            },
            "metadata_preview": {
                key: self.metadata_preview.get(key)
                for key in (
                    "cost_mode",
                    "scientific_evidence_level",
                    "provider_type",
                    "paid_calls_made",
                    "uses_paid_providers",
                    "evidence_scope",
                )
                if self.metadata_preview
            },
        }


def zero_cost_provider_allowed(agent_run: AgentRunConfig) -> bool:
    provider = agent_run.provider
    if provider is None:
        return True
    if provider in ZERO_COST_LOCAL_PROVIDERS:
        return True
    if provider in ZERO_COST_BLOCKED_PROVIDERS:
        return False
    if provider in PAID_PROVIDERS:
        return is_free_tier_agent_run(agent_run)
    return provider == "openai_compatible"


def uses_monetary_providers(config: ExperimentConfig) -> bool:
    """Return True when any agent run could incur non-zero API spend."""
    for agent_run in config.iter_agent_runs():
        if agent_run.provider in ZERO_COST_LOCAL_PROVIDERS:
            continue
        if is_free_tier_agent_run(agent_run):
            continue
        if agent_run.provider in PAID_PROVIDERS:
            return True
    return False


def resolve_zero_cost_evidence_scope(config: ExperimentConfig) -> str:
    if config.evidence_scope:
        return config.evidence_scope
    providers = {run.provider for run in config.iter_agent_runs() if run.provider}
    localish = providers & ZERO_COST_LOCAL_PROVIDERS
    free_tier = {
        run.provider
        for run in config.iter_agent_runs()
        if run.provider and is_free_tier_agent_run(run)
    }
    if localish and free_tier:
        return "zero_cost_mixed_local_and_free_tier_preliminary"
    if free_tier:
        return "zero_cost_free_tier_preliminary"
    if localish:
        return "zero_cost_local_preliminary"
    return "zero_cost_preliminary_unvalidated"


def zero_cost_metadata_fields(config: ExperimentConfig) -> dict[str, Any]:
    return {
        "cost_mode": config.cost_mode,
        "scientific_evidence_level": config.scientific_evidence_level,
        "provider_type": config.provider_type,
        "paid_calls_made": False,
        "monetary_spend_expected_usd": 0.0,
        "evidence_scope": resolve_zero_cost_evidence_scope(config),
        "scientific_scope": "preliminary_or_engineering_only",
    }


def check_zero_cost_readiness(
    config_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    dry_run_output_dir: str | Path | None = "results/dry_runs",
    run_dry_run: bool = True,
) -> ZeroCostReadinessReport:
    path = Path(config_path)
    root = Path(repo_root or Path.cwd())
    checks: list[ZeroCostCheck] = []
    blockers: list[str] = []

    def add(
        name: str,
        passed: bool,
        *,
        severity: Literal["info", "warning", "error"] = "info",
        message: str = "",
        fix: str | None = None,
        blocking: bool = False,
    ) -> None:
        checks.append(
            ZeroCostCheck(
                name=name,
                passed=passed,
                # Passing checks are purely informational; the declared severity
                # only describes how bad the check is when it fails.
                severity="info" if passed else severity,
                message=message,
                fix=fix,
            )
        )
        if not passed and blocking:
            blockers.append(message or name)

    config: ExperimentConfig | None = None
    try:
        config, _ = load_experiment_config(path if path.is_absolute() else root / path)
        add("config_valid", True, message="Config parsed and validated.")
    except ValidationError as exc:
        add(
            "config_valid",
            False,
            severity="error",
            message=f"Config validation failed: {exc.errors()[0]['msg']}",
            fix="Fix YAML schema errors before zero-cost readiness.",
            blocking=True,
        )
        return ZeroCostReadinessReport(
            config_path=str(path),
            verdict="not_ready",
            checks=checks,
            blockers=blockers,
        )

    assert config is not None

    add(
        "cost_mode_zero_cost",
        config.cost_mode == "zero_cost",
        severity="error",
        message=f"cost_mode={config.cost_mode!r}",
        fix="Set cost_mode: zero_cost in the experiment config.",
        blocking=True,
    )
    add(
        "allow_paid_calls_false",
        config.allow_paid_calls is False,
        severity="error",
        message=f"allow_paid_calls={config.allow_paid_calls}",
        fix="Zero-cost configs must keep allow_paid_calls: false.",
        blocking=True,
    )

    effective_budget = config.effective_budget()
    budget_cap = effective_budget.max_total_usd if effective_budget else config.budget_cap_usd
    add(
        "budget_cap_zero",
        budget_cap == 0.0,
        severity="error",
        message=f"budget cap={budget_cap}",
        fix="Set budget.max_total_usd: 0 (or budget_cap_usd: 0).",
        blocking=True,
    )

    if effective_budget and effective_budget.require_explicit_paid_approval:
        add(
            "require_explicit_paid_approval",
            True,
            message="require_explicit_paid_approval is true (expected for zero-cost).",
        )

    oracle_hits = [
        run.run_id()
        for run in config.iter_agent_runs()
        if run.agent in ORACLE_AGENT_NAMES
    ]
    add(
        "oracle_excluded",
        not oracle_hits,
        severity="error",
        message=f"oracle agents found: {oracle_hits}" if oracle_hits else "no oracle agents",
        fix="Remove scripted_oracle_agent from zero-cost configs.",
        blocking=True,
    )

    disallowed: list[str] = []
    for agent_run in config.iter_agent_runs():
        if not zero_cost_provider_allowed(agent_run):
            disallowed.append(
                f"{agent_run.run_id()}:{agent_run.provider}"
            )
    add(
        "providers_zero_cost_only",
        not disallowed,
        severity="error",
        message=(
            "all providers are local or free-tier"
            if not disallowed
            else f"disallowed providers: {disallowed}"
        ),
        fix=(
            "Use local_openai/local_stub or mark gemini/openrouter agent runs with "
            "extra.free_tier: true and zero pricing."
        ),
        blocking=True,
    )

    add(
        "scientific_evidence_level",
        config.scientific_evidence_level == "preliminary_or_engineering",
        severity="warning",
        message=f"scientific_evidence_level={config.scientific_evidence_level!r}",
        fix="Set scientific_evidence_level: preliminary_or_engineering.",
    )

    benchmark_path = config.resolved_benchmark_path(root)
    add(
        "benchmark_exists",
        benchmark_path.exists(),
        severity="error",
        message=str(benchmark_path),
        fix="Generate or point benchmark_path to an existing instances.jsonl file.",
        blocking=True,
    )

    cost_estimate = estimate_experiment_cost(config, config_path=path, repo_root=root)
    upper = cost_estimate.get("known_cost_upper_bound_usd")
    add(
        "estimated_cost_zero",
        upper == 0.0,
        severity="error",
        message=f"estimated upper bound=${upper}",
        fix="Ensure free-tier agent runs use zero pricing and local providers only.",
        blocking=True,
    )

    provider_ready = True
    for agent_run in config.iter_agent_runs():
        provider = agent_run.provider
        if provider in ZERO_COST_LOCAL_PROVIDERS:
            model = _resolved_model(agent_run)
            base_url = agent_run.base_url or os.getenv("LOCAL_OPENAI_BASE_URL", "")
            if not model:
                add(
                    f"local_model:{agent_run.run_id()}",
                    False,
                    severity="warning",
                    message="LOCAL_OPENAI_MODEL_ID / model field not set",
                    fix="Export LOCAL_OPENAI_MODEL_ID or set model in config before real local run.",
                )
                provider_ready = False
            if provider == "local_openai" and not base_url:
                add(
                    f"local_base_url:{agent_run.run_id()}",
                    False,
                    severity="warning",
                    message="LOCAL_OPENAI_BASE_URL / base_url not set",
                    fix="Start Ollama/vLLM and set LOCAL_OPENAI_BASE_URL (e.g. http://localhost:11434/v1).",
                )
                provider_ready = False
            continue
        if is_free_tier_agent_run(agent_run):
            env_vars = _provider_env_vars(provider, agent_run)
            key_ok = any(os.getenv(name) for name in env_vars.get("api_keys", []))
            model = _resolved_model(agent_run)
            add(
                f"free_tier_key:{agent_run.run_id()}",
                key_ok,
                severity="warning",
                message=f"free-tier key configured={key_ok} for {provider}",
                fix=f"Set one of {env_vars.get('api_keys')} for real free-tier runs (not required for dry-run).",
            )
            add(
                f"free_tier_model:{agent_run.run_id()}",
                bool(model),
                severity="warning",
                message=f"model={model!r}",
                fix=f"Set {env_vars.get('model_env')} before real free-tier run.",
            )
            if not key_ok or not model:
                provider_ready = False

    dry_run_summary: dict[str, Any] | None = None
    if run_dry_run and not blockers:
        from causal_agent_bench.phase2 import dry_run_config

        try:
            dry_run_summary = dry_run_config(
                str(path if path.is_absolute() else root / path),
                output_dir=str(dry_run_output_dir) if dry_run_output_dir else None,
            )
            add(
                "dry_run_executed",
                True,
                message="dry-run completed",
            )
            add(
                "dry_run_no_paid_calls",
                dry_run_summary.get("paid_calls_made") is False,
                severity="error",
                message=f"paid_calls_made={dry_run_summary.get('paid_calls_made')}",
                fix="Dry-run must not call paid providers.",
                blocking=True,
            )
            add(
                "dry_run_not_scientific_evidence",
                dry_run_summary.get("scientific_evidence") is False,
                severity="error",
                message=f"scientific_evidence={dry_run_summary.get('scientific_evidence')}",
                blocking=True,
            )
            simulations = dry_run_summary.get("simulations") or []
            sim_ok = all(sim.get("ok") for sim in simulations)
            add(
                "dry_run_simulations_ok",
                sim_ok,
                severity="error",
                message=f"{sum(1 for s in simulations if s.get('ok'))}/{len(simulations)} simulations OK",
                blocking=True,
            )
        except Exception as exc:
            add(
                "dry_run_executed",
                False,
                severity="error",
                message=str(exc),
                fix="Fix config or benchmark issues preventing dry-run.",
                blocking=True,
            )

    metadata_preview: dict[str, Any] | None = None
    if config is not None and not blockers:
        from causal_agent_bench.runners.metadata import build_run_metadata

        metadata_preview = build_run_metadata(
            config,
            config_hash="preview",
            instances_count=0,
            cost_estimate=cost_estimate,
        )
        metadata_preview.update(zero_cost_metadata_fields(config))

    verdict: ZeroCostVerdict = "not_ready"
    if blockers:
        verdict = "not_ready"
    elif provider_ready and dry_run_summary is not None:
        verdict = "zero_cost_ready"
    elif dry_run_summary is not None:
        verdict = "dry_run_ready"

    return ZeroCostReadinessReport(
        config_path=str(path),
        verdict=verdict,
        checks=checks,
        cost_estimate=cost_estimate,
        dry_run_summary=dry_run_summary,
        metadata_preview=metadata_preview,
        blockers=blockers,
    )


def format_zero_cost_report(report: ZeroCostReadinessReport) -> str:
    lines = [
        "# Zero-Cost Readiness Report",
        "",
        f"- **Config:** `{report.config_path}`",
        f"- **Verdict:** `{report.verdict}`",
        "",
    ]
    if report.blockers:
        lines.append("## Blockers")
        lines.extend(f"- {item}" for item in report.blockers)
        lines.append("")
    lines.append("## Checks")
    for check in report.checks:
        status = "PASS" if check.passed else check.severity.upper()
        lines.append(f"- [{status}] **{check.name}**: {check.message}")
        if check.fix and not check.passed:
            lines.append(f"  - Fix: {check.fix}")
    if report.cost_estimate:
        lines.extend(
            [
                "",
                "## Cost estimate",
                f"- Upper bound: ${report.cost_estimate.get('known_cost_upper_bound_usd')}",
                f"- Budget status: {report.cost_estimate.get('budget_status')}",
                f"- Run allowed (cost gate): {report.cost_estimate.get('run_allowed')}",
            ]
        )
    if report.dry_run_summary:
        lines.extend(
            [
                "",
                "## Dry-run",
                f"- paid_calls_made: {report.dry_run_summary.get('paid_calls_made')}",
                f"- scientific_evidence: {report.dry_run_summary.get('scientific_evidence')}",
            ]
        )
    return "\n".join(lines) + "\n"


def _resolved_model(agent_run: AgentRunConfig) -> str:
    model = agent_run.model or ""
    if model and not _ENV_REF_PATTERN.search(model):
        return model
    provider = agent_run.provider
    if provider:
        for env_name in PROVIDER_MODEL_ENV_VARS.get(provider, ()):
            value = os.getenv(env_name, "")
            if value:
                return value
    return ""


def _provider_env_vars(provider: str | None, agent_run: AgentRunConfig) -> dict[str, Any]:
    api_keys: list[str] = []
    model_env = None
    if provider == "gemini":
        api_keys = ["GOOGLE_API_KEY", "GEMINI_API_KEY"]
        model_env = "GEMINI_MODEL_ID"
    elif provider == "openrouter":
        api_keys = ["OPENROUTER_API_KEY"]
        model_env = "OPENROUTER_MODEL_ID"
    elif provider == "local_openai":
        model_env = "LOCAL_OPENAI_MODEL_ID"
    return {"api_keys": api_keys, "model_env": model_env}
