"""Safe experiment command plans — print only, never execute runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EXPERIMENT_SPECS: dict[str, dict[str, Any]] = {
    "micro_stub": {
        "title": "Micro stub (engineering)",
        "config": "configs/pilot_stub_micro_3.yaml",
        "evidence_level": "stub_engineering",
        "expected_runtime_s": 15,
        "expected_cost_usd": 0,
        "approval_needed": False,
        "do_not_run_now": False,
        "warning": "Engineering only — not real LLM behavior.",
    },
    "micro_local": {
        "title": "Micro local open-weight (preliminary)",
        "config": "configs/pilot_free_local_micro_3.yaml",
        "evidence_level": "local_model_preliminary",
        "expected_runtime_s": 600,
        "expected_cost_usd": 0,
        "approval_needed": True,
        "do_not_run_now": True,
        "warning": "DO NOT RUN NOW without explicit approval — Ollama/local model calls.",
    },
    "provider_pilot": {
        "title": "Provider pilot (20 tasks)",
        "config": "configs/pilot_multi_provider_20.yaml",
        "evidence_level": "provider_pilot",
        "expected_runtime_s": 3600,
        "expected_cost_usd": 25,
        "approval_needed": True,
        "do_not_run_now": True,
        "warning": "DO NOT RUN NOW — paid API calls require budget approval.",
    },
    "main_500": {
        "title": "Main 500-task experiment",
        "config": "configs/main_500_multi_provider.yaml",
        "evidence_level": "main_experiment",
        "expected_runtime_s": 86400,
        "expected_cost_usd": 500,
        "approval_needed": True,
        "do_not_run_now": True,
        "warning": "DO NOT RUN NOW — main experiment gate must pass first.",
    },
}


def _commands_for_experiment(spec: dict[str, Any]) -> dict[str, list[str]]:
    config = spec["config"]
    return {
        "preflight": [
            "make fast-check",
            "python3 scripts/check_submission_readiness.py",
            f"python3 -m causal_agent_bench validate-config --config {config}",
            f"python3 scripts/check_zero_cost_readiness.py --config {config} --require zero_cost_ready",
        ],
        "plan_run": [f"python3 -m causal_agent_bench plan-run --config {config}"],
        "readiness": [
            "python3 scripts/check_submission_readiness.py",
            "python3 scripts/check_claim_ledger.py --mode draft",
        ],
        "dry_run": [
            f"python3 -m causal_agent_bench dry-run --config {config} --output-dir results/dry_runs",
        ],
        "run": [f"python3 -m causal_agent_bench run --config {config}"],
        "post_run": [
            "python3 -m causal_agent_bench run-status --latest",
            "python3 -m causal_agent_bench generate-report --latest",
            "python3 -m causal_agent_bench score --run-dir results/<run_dir>",
            "python3 -m causal_agent_bench analyze --run-dir results/<run_dir>",
            "python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>",
        ],
        "audit": [
            "python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/pilot_v0.1",
            "python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl",
            "python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml",
        ],
        "claim_ledger": [
            "python3 scripts/check_claim_ledger.py --mode draft",
            "python3 scripts/check_evidence_safety.py",
        ],
    }


def build_command_plan(experiment: str, repo_root: str | Path | None = None) -> dict[str, Any]:
    if experiment not in EXPERIMENT_SPECS:
        allowed = ", ".join(sorted(EXPERIMENT_SPECS))
        raise ValueError(f"unknown experiment {experiment!r}; expected one of: {allowed}")

    spec = EXPERIMENT_SPECS[experiment]
    return {
        "experiment": experiment,
        "title": spec["title"],
        "config": spec["config"],
        "generated_at": datetime.now(UTC).isoformat(),
        "evidence_level": spec["evidence_level"],
        "expected_runtime_s": spec["expected_runtime_s"],
        "expected_cost_usd": spec["expected_cost_usd"],
        "approval_needed": spec["approval_needed"],
        "do_not_run_now": spec["do_not_run_now"],
        "warning": spec["warning"],
        "commands": _commands_for_experiment(spec),
        "executes_run": False,
    }


def format_command_plan(plan: dict[str, Any]) -> str:
    lines = [
        f"# Command plan: {plan['experiment']}",
        "",
        f"**{plan['title']}**",
        f"- Config: `{plan['config']}`",
        f"- Evidence level: `{plan['evidence_level']}`",
        f"- Expected runtime: ~{plan['expected_runtime_s']}s",
        f"- Expected cost: ${plan['expected_cost_usd']}",
        f"- Approval needed: {plan['approval_needed']}",
        "",
    ]
    if plan["do_not_run_now"]:
        lines.extend([f"> **{plan['warning']}**", ""])
    for section, cmds in plan["commands"].items():
        lines.append(f"## {section}")
        lines.append("```bash")
        lines.extend(cmds)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def write_all_command_plans(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root or Path.cwd()).resolve()
    plans = {name: build_command_plan(name, root) for name in EXPERIMENT_SPECS}
    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "experiments": plans,
    }
    exp_dir = root / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "command_plans.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_lines = ["# Experiment Command Plans", "", "Generated command blocks only — **never auto-executed**.", ""]
    for plan in plans.values():
        md_lines.append(format_command_plan(plan))
        md_lines.append("---")
        md_lines.append("")
    (exp_dir / "COMMAND_PLANS.md").write_text("\n".join(md_lines), encoding="utf-8")
    return out
