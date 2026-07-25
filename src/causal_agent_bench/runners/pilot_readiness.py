from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from causal_agent_bench.agents.llm_clients import list_provider_status
from causal_agent_bench.phase2 import dry_run_config, validate_config_file
from causal_agent_bench.runners.commercial import uses_paid_providers
from causal_agent_bench.runners.config import (
    ORACLE_AGENT_NAMES,
    PAID_PROVIDERS,
    PROVIDER_MODEL_ENV_VARS,
    ExperimentConfig,
    load_experiment_config,
)
from causal_agent_bench.runners.costing import estimate_experiment_cost
from causal_agent_bench.runners.metadata import build_run_metadata
from causal_agent_bench.utils.io import load_yaml

ReadinessVerdict = Literal["not_ready", "dry_run_ready", "cost_estimate_ready", "paid_pilot_ready"]

REQUIRED_RUN_METADATA_FIELDS = (
    "timestamp",
    "git_commit",
    "config_hash",
    "seed",
    "run_name",
    "number_of_instances",
    "agents",
    "providers",
    "model_ids",
    "benchmark_instances_path",
    "max_steps",
    "num_repeats",
    "budget_cap_usd",
    "allow_paid_calls",
    "uses_paid_providers",
    "cost_estimate_preflight_usd",
    "provider_runs",
    "redaction",
)

_ENV_REF_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")
_UNSAFE_OUTPUT_DIRS = frozenset({"/", ".", ""})


@dataclass
class ReadinessCheck:
    name: str
    passed: bool
    severity: Literal["info", "warning", "error"] = "info"
    message: str = ""
    fix: str | None = None


@dataclass
class PilotReadinessReport:
    config_path: str
    verdict: ReadinessVerdict
    checks: list[ReadinessCheck] = field(default_factory=list)
    provider_status: list[dict[str, Any]] = field(default_factory=list)
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
            "provider_status": self.provider_status,
            "cost_estimate": self.cost_estimate,
            "dry_run": {
                "executed": self.dry_run_summary is not None,
                "would_execute": (self.dry_run_summary or {}).get("would_execute"),
                "provider_calls_made": (self.dry_run_summary or {})
                .get("safety", {})
                .get("will_call_providers"),
            },
            "metadata_fields_declared": sorted(
                (self.metadata_preview or {}).keys()
            ),
        }


def check_pilot_readiness(
    config_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    dry_run_output_dir: str | Path | None = "results/dry_runs",
    run_dry_run: bool = True,
) -> PilotReadinessReport:
    """Evaluate whether a provider pilot config is ready for dry-run, costing, or paid execution."""

    path = Path(config_path)
    root = Path(repo_root or Path.cwd())
    checks: list[ReadinessCheck] = []
    blockers: list[str] = []

    def add(
        name: str,
        passed: bool,
        *,
        severity: Literal["info", "warning", "error"] = "info",
        message: str = "",
        fix: str | None = None,
        blocker: bool = False,
    ) -> None:
        checks.append(
            ReadinessCheck(
                name=name,
                passed=passed,
                severity=severity,
                message=message,
                fix=fix,
            )
        )
        if blocker and not passed:
            blockers.append(message or name)

    add(
        "config_exists",
        path.exists(),
        severity="error",
        message=f"Config file {'found' if path.exists() else 'missing'}: {path}",
        blocker=True,
    )
    if not path.exists():
        return _finalize(path, checks, blockers)

    raw: dict[str, Any] | None = None
    config: ExperimentConfig | None = None
    try:
        raw = load_yaml(path)
        config, _ = load_experiment_config(path)
        add("config_parses", True, message="Config parsed as ExperimentConfig.")
    except ValidationError as exc:
        add(
            "config_parses",
            False,
            severity="error",
            message=f"Config validation failed: {exc.errors()[0]['msg']}",
            fix="Fix the YAML fields reported by validate-config.",
            blocker=True,
        )
        return _finalize(path, checks, blockers)
    except Exception as exc:  # pragma: no cover - defensive
        add(
            "config_parses",
            False,
            severity="error",
            message=f"Config could not be loaded: {exc}",
            blocker=True,
        )
        return _finalize(path, checks, blockers)

    assert config is not None
    assert raw is not None

    pricing_registry = None
    pricing_path = config.resolved_pricing_registry_path(root)
    if pricing_path is not None and pricing_path.exists():
        from causal_agent_bench.runners.registries import load_model_pricing_registry

        pricing_registry = load_model_pricing_registry(pricing_path)
    provider_path = config.resolved_provider_registry_path(root)
    if provider_path is not None and provider_path.exists():
        from causal_agent_bench.runners.registries import load_provider_registry

        # Loaded for validation side-effect (raises on a malformed registry).
        load_provider_registry(provider_path)

    benchmark_path = config.resolved_benchmark_path(root)
    add(
        "dataset_exists",
        benchmark_path.exists(),
        severity="error",
        message=f"Benchmark dataset {'found' if benchmark_path.exists() else 'missing'}: {benchmark_path}",
        fix="Generate the dataset or update benchmark_path.",
        blocker=True,
    )

    agent_runs = config.iter_agent_runs()
    provider_agents = [run for run in agent_runs if run.provider in PAID_PROVIDERS]
    add(
        "provider_backed_agents_exist",
        bool(provider_agents),
        severity="error",
        message=(
            f"Found {len(provider_agents)} paid-provider agent run(s)."
            if provider_agents
            else "No paid-provider agent_runs entries found."
        ),
        fix="Add agent_runs entries with provider: openai/anthropic/gemini/openrouter.",
        blocker=True,
    )

    oracle_runs = [run for run in agent_runs if run.agent in ORACLE_AGENT_NAMES]
    add(
        "no_oracle_agents",
        not oracle_runs,
        severity="error",
        message=(
            "No oracle agents in provider pilot config."
            if not oracle_runs
            else f"Oracle agent(s) disallowed in provider configs: {[run.agent for run in oracle_runs]}"
        ),
        fix="Remove scripted_oracle_agent from provider pilot configs.",
        blocker=True,
    )

    output_dir = config.resolved_output_dir(root)
    output_safe = _output_dir_is_safe(output_dir, root)
    add(
        "output_directory_safe",
        output_safe,
        severity="error" if not output_safe else "info",
        message=f"Output directory resolves to {output_dir}",
        fix="Set output_dir to a subdirectory such as results/.",
        blocker=not output_safe,
    )

    provider_status = list_provider_status()
    status_by_provider = {row["provider"]: row for row in provider_status}
    for agent_run in provider_agents:
        provider = agent_run.provider or ""
        env_vars = _model_env_vars(agent_run, raw, provider)
        model_configured = bool(agent_run.model)
        add(
            f"model_id:{agent_run.run_id()}",
            model_configured or bool(env_vars),
            severity="warning" if not model_configured else "info",
            message=(
                f"Model configured for {agent_run.run_id()}: {agent_run.model!r}"
                if model_configured
                else f"Model empty for {agent_run.run_id()}; expected env var(s): {', '.join(env_vars) or 'unknown'}"
            ),
            fix=f"Set {' or '.join(env_vars)} or hard-code model in the config.",
        )

        key_env_vars = _api_key_env_vars(agent_run, status_by_provider.get(provider, {}))
        key_present = any(os.getenv(name) for name in key_env_vars)
        add(
            f"provider_key:{provider}",
            key_present,
            severity="warning",
            message=(
                f"API key configured for {provider} via {', '.join(key_env_vars)}"
                if key_present
                else f"API key not configured for {provider}; set one of {', '.join(key_env_vars)}"
            ),
            fix=f"Export {' or '.join(key_env_vars)} before paid runs. Values are never printed.",
        )

        pricing_details = config.resolved_pricing_details(
            agent_run,
            pricing_registry=pricing_registry,
        )
        pricing = pricing_details["rates"]
        add(
            f"pricing:{agent_run.run_id()}",
            bool(pricing_details["pricing_known"] and pricing),
            severity="warning",
            message=(
                "Pricing configured."
                if pricing_details["pricing_known"] and pricing
                else "Pricing unknown; numeric cost upper bound will be unavailable."
            ),
            fix="Add pricing to configs/model_pricing.yaml, cost_models, or agent_run.pricing.",
        )

    structured_budget = config.budget is not None
    run_budget = config.budget_cap_usd is not None
    agent_budgets = all(run.budget_cap_usd is not None for run in provider_agents)
    add(
        "budget_cap_exists",
        structured_budget and run_budget and agent_budgets,
        severity="warning",
        message=(
            f"budget.max_total_usd={config.budget.max_total_usd if config.budget else None}; "
            f"per-agent caps={'set' if agent_budgets else 'missing'}."
        ),
        fix="Add a structured budget block and budget_cap_usd on each provider agent run.",
    )

    run_max_calls = config.max_api_calls is not None
    agent_max_calls = all(run.max_api_calls is not None for run in provider_agents)
    add(
        "max_api_calls_exists",
        structured_budget and run_max_calls and agent_max_calls,
        severity="warning",
        message=(
            f"budget.max_calls={config.budget.max_calls if config.budget else config.max_api_calls}; "
            f"per-agent caps={'set' if agent_max_calls else 'missing'}."
        ),
        fix="Add budget.max_calls and max_api_calls on each provider agent run.",
    )

    prompt_checks_ok = all(
        bool(run.extra.get("prompt_file")) for run in provider_agents
    )
    add(
        "prompt_templates_declared",
        prompt_checks_ok,
        severity="warning",
        message="Prompt template filenames declared in agent_runs.extra.prompt_file."
        if prompt_checks_ok
        else "One or more provider agent runs lack extra.prompt_file.",
        fix="Add extra.prompt_file and optional extra.prompt_version for logging.",
    )

    cost_estimate: dict[str, Any] | None = None
    try:
        cost_estimate = estimate_experiment_cost(config, config_path=path, repo_root=root)
        upper = cost_estimate.get("known_cost_upper_bound_usd")
        pricing_known = upper is not None
        add(
            "cost_estimate_supported",
            pricing_known,
            severity="warning",
            message=(
                f"Conservative cost upper bound: ${upper:.4f}"
                if pricing_known
                else "Cost upper bound unknown because pricing is incomplete."
            ),
        )
        if config.budget_cap_usd is not None and upper is not None and upper > config.budget_cap_usd:
            add(
                "budget_preflight_within_cap",
                False,
                severity="error",
                message=(
                    f"Estimated cost ${upper:.4f} exceeds budget_cap_usd ${config.budget_cap_usd:.4f}"
                ),
                fix="Raise budget_cap_usd or reduce instances/steps/pricing assumptions.",
                blocker=True,
            )
        else:
            add(
                "budget_preflight_within_cap",
                True,
                message="Estimated cost is within budget_cap_usd or budget cap is unset.",
            )
    except Exception as exc:
        add(
            "cost_estimate_supported",
            False,
            severity="warning",
            message=f"Cost estimation failed: {exc}",
        )

    metadata_preview = build_run_metadata(config, "readiness-preview", 0, cost_estimate=cost_estimate)
    missing_metadata = [
        field_name
        for field_name in REQUIRED_RUN_METADATA_FIELDS
        if field_name not in metadata_preview
    ]
    add(
        "metadata_fields_declared",
        not missing_metadata,
        severity="error" if missing_metadata else "info",
        message=(
            "Required run metadata fields will be recorded."
            if not missing_metadata
            else f"Missing metadata fields: {missing_metadata}"
        ),
        blocker=bool(missing_metadata),
    )
    redaction_ok = metadata_preview.get("redaction", {}).get("api_keys_persisted") is False
    add(
        "api_keys_redacted_in_metadata",
        redaction_ok,
        severity="error",
        message="Run metadata declares api_keys_persisted=false.",
        blocker=not redaction_ok,
    )

    dry_run_summary: dict[str, Any] | None = None
    if run_dry_run:
        try:
            dry_run_summary = dry_run_config(
                path,
                output_dir=dry_run_output_dir,
            )
            would_execute = bool(dry_run_summary.get("would_execute"))
            provider_calls = dry_run_summary.get("safety", {}).get("will_call_providers")
            add(
                "dry_run_works",
                would_execute and provider_calls is False,
                severity="error",
                message=(
                    "Dry-run succeeded without provider calls."
                    if would_execute and provider_calls is False
                    else f"Dry-run did not complete safely: {dry_run_summary.get('reason', 'unknown')}"
                ),
                fix="Run validate-config and fix reported issues before dry-run.",
                blocker=True,
            )
            report_text = json.dumps(dry_run_summary, sort_keys=True)
            add(
                "dry_run_no_secrets_logged",
                not _contains_secret_material(report_text),
                severity="error",
                message="Dry-run report contains no raw API key material.",
                blocker=True,
            )
        except Exception as exc:
            add(
                "dry_run_works",
                False,
                severity="error",
                message=f"Dry-run failed: {exc}",
                blocker=True,
            )

    validation = validate_config_file(path)
    if uses_paid_providers(config):
        add(
            "allow_paid_calls_declared",
            True,
            severity="info",
            message=f"allow_paid_calls={config.allow_paid_calls}",
        )
        if not config.allow_paid_calls:
            add(
                "paid_calls_enabled",
                False,
                severity="warning",
                message="Paid providers configured but allow_paid_calls is false (safe default).",
                fix="Set allow_paid_calls: true only after reviewing estimate-cost output.",
            )

    keys_ready = all(
        any(os.getenv(name) for name in _api_key_env_vars(run, status_by_provider.get(run.provider or "", {})))
        for run in provider_agents
    )
    models_ready = all(bool(run.model) for run in provider_agents)
    pricing_ready = all(
        config.resolved_pricing_details(run, pricing_registry=pricing_registry)["pricing_known"]
        for run in provider_agents
    )
    budgets_ready = (
        config.budget is not None
        and config.budget_cap_usd is not None
        and all(run.budget_cap_usd is not None for run in provider_agents)
        and all(run.max_api_calls is not None for run in provider_agents)
        and config.max_api_calls is not None
    )
    dry_run_ready = not blockers and dry_run_summary is not None and dry_run_summary.get("would_execute")
    cost_ready = (
        dry_run_ready
        and pricing_ready
        and budgets_ready
        and cost_estimate is not None
        and cost_estimate.get("known_cost_upper_bound_usd") is not None
    )
    paid_ready = (
        cost_ready
        and keys_ready
        and models_ready
        and config.allow_paid_calls
        and validation.get("ready_to_run")
    )

    if paid_ready:
        verdict: ReadinessVerdict = "paid_pilot_ready"
    elif cost_ready:
        verdict = "cost_estimate_ready"
    elif dry_run_ready:
        verdict = "dry_run_ready"
    else:
        verdict = "not_ready"

    report = _finalize(path, checks, blockers)
    report.verdict = verdict
    report.provider_status = provider_status
    report.cost_estimate = cost_estimate
    report.dry_run_summary = dry_run_summary
    report.metadata_preview = metadata_preview
    return report


def _finalize(path: Path, checks: list[ReadinessCheck], blockers: list[str]) -> PilotReadinessReport:
    verdict: ReadinessVerdict = "not_ready"
    if blockers:
        verdict = "not_ready"
    return PilotReadinessReport(
        config_path=str(path),
        verdict=verdict,
        checks=checks,
        blockers=blockers,
    )


def _contains_secret_material(text: str) -> bool:
    lowered = text.lower()
    if "sk-" in lowered or " Bearer sk-" in text:
        return True
    for marker in ('"api_key": "', "'api_key': '", '"secret": "', "'secret': '"):
        if marker in text:
            value_start = text.index(marker) + len(marker)
            snippet = text[value_start : value_start + 12]
            if snippet and snippet[0] not in {"<", "$"}:
                return True
    return False


def _output_dir_is_safe(output_dir: Path, repo_root: Path) -> bool:
    resolved = output_dir.resolve()
    text = str(resolved)
    if text in _UNSAFE_OUTPUT_DIRS or resolved == Path("/"):
        return False
    return not (resolved == repo_root.resolve() and output_dir.name == ".")


def _model_env_vars(agent_run: Any, raw: dict[str, Any], provider: str) -> tuple[str, ...]:
    if agent_run.model:
        return ()
    refs = _env_refs_for_agent_run(agent_run.run_id(), raw)
    if refs:
        return refs
    return PROVIDER_MODEL_ENV_VARS.get(provider, ())


def _env_refs_for_agent_run(run_id: str, raw: dict[str, Any]) -> tuple[str, ...]:
    for entry in raw.get("agent_runs", []):
        name = entry.get("name") or entry.get("agent")
        if name != run_id:
            continue
        model_value = entry.get("model")
        if isinstance(model_value, str):
            return tuple(match.group(1) for match in _ENV_REF_PATTERN.finditer(model_value))
    return ()


def _api_key_env_vars(agent_run: Any, status: dict[str, Any]) -> tuple[str, ...]:
    if agent_run.api_key_env:
        return (agent_run.api_key_env,)
    env_vars = status.get("env_vars") or []
    return tuple(env_vars)


def format_readiness_report(report: PilotReadinessReport) -> str:
    lines = [
        f"# Pilot readiness: {report.verdict}",
        "",
        f"- Config: `{report.config_path}`",
        f"- Verdict: `{report.verdict}`",
        "",
        "## Checks",
        "",
    ]
    for check in report.checks:
        status = "pass" if check.passed else check.severity
        lines.append(f"- [{status}] **{check.name}**: {check.message}")
        if check.fix and not check.passed:
            lines.append(f"  - fix: {check.fix}")
    if report.blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in report.blockers:
            lines.append(f"- {blocker}")
    if report.cost_estimate and report.cost_estimate.get("known_cost_upper_bound_usd") is not None:
        lines.extend(
            [
                "",
                "## Cost estimate",
                "",
                f"- Upper bound (USD): `{report.cost_estimate['known_cost_upper_bound_usd']}`",
                f"- Budget status: `{report.cost_estimate.get('budget_status')}`",
            ]
        )
    return "\n".join(lines) + "\n"
