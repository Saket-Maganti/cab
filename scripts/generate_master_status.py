#!/usr/bin/env python3
"""Generate MASTER_STATUS.md/json — single pre-experiment status pack."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.runners.index_runs import index_runs
from causal_agent_bench.safety.common import classify_run_entry

CLASSIFICATION = "build_infrastructure_ready"
READINESS_NOTE = (
    "Readiness checker may report local_preliminary due to indexed local/stub runs; "
    "no provider pilot or supported empirical claims."
)

BUILT = [
    "Pydantic schemas (tasks, interventions, instances, trajectories, scores)",
    "Deterministic benchmark generation (pilot_v0.1, main_v0.1 candidate)",
    "Simulated tools and local environment execution",
    "Experiment runner (config hash, resume, limits, scoring, metadata)",
    "Run management (plan-run, index-runs, mark-interrupted, run-status)",
    "Mock/stub agents and mock diagnostic configs",
    "Analysis export (tables, figures, failure gallery, leaderboard)",
    "Claim ledger + evidence safety validators",
    "Paper draft with placeholder protection",
    "Reviewer/advisor handoff package (Phases 5–8)",
    "Release/reproducibility scaffolding (manifest, repro bundle plan)",
    "Human validation export protocol (no annotations yet)",
    "CI fast-check workflows",
    "Consistency audits (repo, config, build phase)",
    "Phase 9 engineering demo bundle (mock micro E2E validated)",
]

NOT_BUILT = [
    "Completed provider-backed pilot on frozen split",
    "Human validation annotations / agreement tables",
    "Main 500-task multi-provider experiment",
    "Supported C1–C8 or C10 empirical claims",
    "Final NeurIPS-ready results or acceptance guarantee",
    "Frozen benchmark v1.0 with full human audit sign-off",
]

SAFE_COMMANDS = [
    "make fast-check",
    "make doctor",
    "make plan-micro",
    "make audit-repo",
    "make audit-configs",
    "make check-readiness",
    "make status",
    "python3 scripts/generate_master_status.py",
    "python3 scripts/final_build_phase_audit.py",
    "python3 scripts/check_evidence_safety.py",
    "python3 scripts/check_claim_ledger.py",
    "python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml",
    "python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml",
    "python3 -m causal_agent_bench index-runs",
    "python3 -m causal_agent_bench dry-run --config configs/pilot_stub_micro_3.yaml",
]

DANGEROUS_COMMANDS = [
    "python3 -m causal_agent_bench run --config configs/pilot_openai_20.yaml  # paid",
    "python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml  # paid",
    "python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml  # long local",
    "python3 -m causal_agent_bench run --config configs/commercial_api_main_500.yaml  # main scale",
    "python3 -m causal_agent_bench fill-paper-from-run  # without verified pilot",
    "make smoke  # runs smoke config",
]

NEXT_STEPS = [
    "Review experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md",
    "Review experiments/SAFE_NEXT_RUN_DECISION_TREE.md",
    "When ready: mock micro run (configs/pilot_mock_diagnostic_micro.yaml) — engineering only",
    "After mock: optional stub micro (configs/pilot_stub_micro_3.yaml) — pipeline check",
    "Before any paid run: budget approval + estimate-cost + freeze checklist gate",
    "Export human validation sample after first complete non-stub pilot",
]


def _load_readiness() -> dict:
    path = ROOT / "scripts" / "check_submission_readiness.py"
    spec = importlib.util.spec_from_file_location("check_submission_readiness", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.classify_readiness(ROOT)


def _evidence_map(runs: list[dict]) -> dict:
    buckets = {
        "dry_run": [],
        "stub_engineering": [],
        "mock_diagnostic": [],
        "interrupted_local": [],
        "local_preliminary": [],
        "provider_pilot": [],
        "human_validated": [],
        "main_experiment": [],
    }
    for run in runs:
        classified = classify_run_entry(run, ROOT)
        classification = classified["classification"]
        name = str(run.get("run_name", "")).lower()
        status = run.get("status", "")
        completion = run.get("completion_state", "")
        provider = str(run.get("provider_type", "")).lower()

        if classification == "mock_diagnostic" and (status == "dry_run" or "dry_run" in name):
            buckets["dry_run"].append(run.get("run_name"))
        elif classification == "mock_diagnostic":
            buckets["mock_diagnostic"].append(run.get("run_name"))
        elif classification == "stub_engineering":
            buckets["stub_engineering"].append(run.get("run_name"))
        elif classification in {"interrupted", "incomplete"} or status == "interrupted" or completion == "incomplete":
            buckets["interrupted_local"].append(run.get("run_name"))
        elif classification == "provider_backed_pilot" and classified["paper_eligible"]:
            buckets["provider_pilot"].append(run.get("run_name"))
        elif classification == "main_benchmark" and classified["paper_eligible"]:
            buckets["main_experiment"].append(run.get("run_name"))
        elif completion == "complete" and ("local" in name or provider == "local"):
            buckets["local_preliminary"].append(run.get("run_name"))
    return {k: {"count": len(v), "examples": v[:3]} for k, v in buckets.items()}


def build_master_status() -> dict:
    readiness = _load_readiness()
    ledger = json.loads((ROOT / "docs" / "claim_ledger.json").read_text(encoding="utf-8"))
    claims = {c["claim_id"]: c["status"] for c in ledger.get("claims", [])}
    runs = index_runs(ROOT / "results")

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "executive_status": {
            "classification": CLASSIFICATION,
            "readiness_checker_level": readiness.get("level"),
            "submission_ready": readiness.get("submission_ready", False),
            "note": READINESS_NOTE,
        },
        "what_is_built": BUILT,
        "what_is_not_built": NOT_BUILT,
        "evidence_map": _evidence_map(runs),
        "safe_commands": SAFE_COMMANDS,
        "dangerous_commands": DANGEROUS_COMMANDS,
        "next_steps_ordered": NEXT_STEPS,
        "advisor_handoff": {
            "safe_to_show": True,
            "caveats": [
                "Engineering scaffold only — not submission-ready",
                "Mock/stub runs are not real LLM behavior",
                "C1–C8/C10 remain planned",
                "Use handoff/ADVISOR_REVIEW_BUNDLE_INDEX.md",
            ],
        },
        "paper_readiness": {
            "can_write_now": [
                "Problem statement and motivation",
                "Benchmark design and intervention framework",
                "Metric definitions (ACRS, trajectory diagnostics)",
                "Experimental setup (planned)",
                "Limitations and ethics",
            ],
            "must_wait": [
                "Results tables with real numbers",
                "Ranking / performance claims",
                "Human validation agreement statistics",
                "Abstract empirical claims ([N], [M], [K], [X], [rho])",
            ],
        },
        "experiment_readiness": {
            "safest_tiny_run": {
                "config": "configs/pilot_mock_diagnostic_micro.yaml",
                "type": "mock diagnostic micro",
                "evidence_level": "mock_diagnostic",
                "allowed_claims": "engineering_only — detector wiring only",
                "requires_approval": False,
            },
            "next_after_mock": {
                "config": "configs/pilot_stub_micro_3.yaml",
                "type": "stub micro",
                "evidence_level": "stub_engineering",
                "allowed_claims": "pipeline reproducibility only (C9)",
            },
        },
        "claims": claims,
        "blockers": readiness.get("blockers", []),
        "build_phases_completed": [
            "Phase 2–8",
            "Phase 9: mock demo, advisor-ready freeze, E2E validation",
        ],
        "phase9_demo_run": {
            "run_directory": "results/20260520T072032Z_pilot_mock_diagnostic_micro",
            "config": "configs/pilot_mock_diagnostic_micro.yaml",
            "evidence_level": "mock_diagnostic_only",
            "scientific_evidence": False,
            "not_real_llm_behavior": True,
            "bundle": "demo/ENGINEERING_DEMO_BUNDLE.md",
        },
    }


def _markdown(status: dict) -> str:
    ex = status["executive_status"]
    lines = [
        "# Master Status — CausalAgentBench",
        "",
        f"**Generated:** {status['generated_at']}",
        f"**Classification:** `{ex['classification']}`",
        f"**Readiness checker:** `{ex['readiness_checker_level']}` · submission_ready={ex['submission_ready']}",
        "",
        f"> {ex['note']}",
        "",
        "## 1. Executive status",
        "",
        "The repository is a **build-infrastructure-ready** research scaffold: benchmark design,",
        "tooling, docs, and validation gates are in place. Empirical claims remain **planned**.",
        "",
        "## 2. What is built",
        "",
    ]
    for item in status["what_is_built"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 3. What is not built / not proven", ""])
    for item in status["what_is_not_built"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 4. Evidence map", ""])
    for level, data in status["evidence_map"].items():
        lines.append(f"- **{level}:** {data['count']} runs" + (f" (e.g. {data['examples']})" if data["examples"] else ""))
    lines.extend(["", "## 5. Safe commands", ""])
    for cmd in status["safe_commands"]:
        lines.append(f"```bash\n{cmd}\n```")
    lines.extend(["", "## 6. Dangerous / heavy commands (require approval)", ""])
    for cmd in status["dangerous_commands"]:
        lines.append(f"- `{cmd}`")
    lines.extend(["", "## 7. Next exact steps", ""])
    for i, step in enumerate(status["next_steps_ordered"], 1):
        lines.append(f"{i}. {step}")
    lines.extend(["", "## 8. Advisor / professor handoff", ""])
    ah = status["advisor_handoff"]
    lines.append(f"- **Safe to show:** {ah['safe_to_show']}")
    for c in ah["caveats"]:
        lines.append(f"- {c}")
    lines.extend(["", "## 9. Paper readiness", ""])
    lines.append("**Can write now:**")
    for item in status["paper_readiness"]["can_write_now"]:
        lines.append(f"- {item}")
    lines.append("\n**Must wait for experiments:**")
    for item in status["paper_readiness"]["must_wait"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 10. Experiment readiness (tiny run when ready)", ""])
    tiny = status["experiment_readiness"]["safest_tiny_run"]
    lines.append(f"- **Safest:** `{tiny['config']}` ({tiny['type']})")
    lines.append(f"- Evidence level: {tiny['evidence_level']}")
    lines.append(f"- Allowed claims: {tiny['allowed_claims']}")
    nxt = status["experiment_readiness"]["next_after_mock"]
    lines.append(f"- **Then:** `{nxt['config']}` ({nxt['type']})")
    lines.extend(["", "## Claims", ""])
    for cid, st in sorted(status["claims"].items()):
        lines.append(f"- **{cid}:** {st}")
    lines.extend(["", "## Blockers", ""])
    for b in status["blockers"]:
        lines.append(f"- {b}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate MASTER_STATUS pack.")
    parser.parse_args(argv)
    status = build_master_status()
    md_path = ROOT / "MASTER_STATUS.md"
    json_path = ROOT / "MASTER_STATUS.json"
    md_path.write_text(_markdown(status), encoding="utf-8")
    json_path.write_text(json.dumps(status, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
