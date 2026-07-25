#!/usr/bin/env python3
"""Generate PROJECT_STATUS.md/json — single snapshot of repo state."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.runners.index_runs import index_runs

BUILD_PHASES = [
    "Phase 2: reports, dashboards, readiness",
    "Phase 3: benchmark quality and reviewer package",
    "Phase 4: automation, release packaging, orchestration",
    "Phase 5: paper package, advisor handoff, review simulation",
    "Phase 6: visuals, docs navigation, demo package",
    "Phase 7: consolidation, quality gate, tech debt",
    "Phase 8: pre-experiment freeze and master status pack",
]

SAFE_COMMANDS = [
    "make fast-check",
    "make doctor",
    "make plan-micro",
    "make audit-repo",
    "make audit-configs",
    "make check-readiness",
    "python3 scripts/generate_project_status.py",
    "python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml",
    "python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml",
    "python3 scripts/check_submission_readiness.py",
]

UNSAFE_COMMANDS = [
    "python3 -m causal_agent_bench run --config configs/pilot_openai_20.yaml",
    "python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml",
    "python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml",
    "make smoke  # runs model stub smoke config",
]


def _run_check(script: str, *args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {"exit_code": proc.returncode, "output_tail": proc.stdout[-800:] + proc.stderr[-800:]}


def _fast_check_ok() -> bool:
    proc = subprocess.run(
        ["make", "fast-check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def build_status(*, run_fast_check: bool = False) -> dict:
    import importlib.util

    path = ROOT / "scripts" / "check_submission_readiness.py"
    spec = importlib.util.spec_from_file_location("check_submission_readiness", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    readiness = mod.classify_readiness(ROOT)
    ledger = json.loads((ROOT / "docs" / "claim_ledger.json").read_text(encoding="utf-8"))
    claims = {row["claim_id"]: row["status"] for row in ledger.get("claims", [])}
    runs = index_runs(ROOT / "results")

    completed = [r for r in runs if r["completion_state"] == "complete"]
    interrupted = [r for r in runs if r["status"] == "interrupted"]
    stub_runs = [r for r in completed if "stub" in str(r.get("run_name", "")).lower()]
    mock_runs = [r for r in completed if "mock" in str(r.get("run_name", "")).lower()]

    checks = {
        "claim_ledger": _run_check("check_claim_ledger.py"),
        "evidence_safety": _run_check("check_evidence_safety.py"),
        "paper_placeholders_draft": _run_check("check_paper_placeholders.py", "--mode", "draft"),
    }

    fast_check = None
    if run_fast_check:
        started = time.monotonic()
        fast_check = {"passed": _fast_check_ok(), "runtime_seconds": round(time.monotonic() - started, 1)}

    artifacts_ready = [
        "docs/README.md",
        "docs/REPO_MAP.md",
        "docs/GLOSSARY.md",
        "docs/CLI_REFERENCE.md",
        "handoff/ADVISOR_DEMO_SCRIPT.md",
        "handoff/PROFESSOR_READY_CHECKLIST.md",
        "audits/repo_consistency/REPO_CONSISTENCY_AUDIT.md",
        "audits/config_consistency/CONFIG_AUDIT.md",
        "paper/latexpaper/figures/figure1_benchmark_overview_placeholder.png",
        "release/release_manifest.json",
    ]
    artifacts_blocked = [
        "provider-backed pilot run (complete)",
        "human validation annotations",
        "main experiment (500 tasks)",
        "submission-ready paper numbers",
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": readiness.get("level"),
        "submission_ready": readiness.get("submission_ready", False),
        "build_phases_completed": BUILD_PHASES,
        "fast_check": fast_check,
        "checks": {k: v["exit_code"] for k, v in checks.items()},
        "evidence_status": {
            "claims": claims,
            "completed_runs": len(completed),
            "interrupted_runs": len(interrupted),
            "stub_runs": len(stub_runs),
            "mock_runs": len(mock_runs),
            "provider_pilot_runs": readiness.get("provider_pilot_runs", 0),
        },
        "blockers": readiness.get("blockers", []),
        "warnings": readiness.get("warnings", []),
        "next_steps": readiness.get("next_required_actions", []),
        "artifacts_ready": [p for p in artifacts_ready if (ROOT / p).exists()],
        "artifacts_blocked": artifacts_blocked,
        "paper_status": {
            "placeholders_present": True,
            "submission_validation": "not_ready",
            "placeholder_figures_only": True,
        },
        "experiment_status": {
            "main_gate": "NO-GO",
            "provider_pilot": "not_run",
            "human_validation": "not_started",
        },
        "safe_commands": SAFE_COMMANDS,
        "unsafe_commands": UNSAFE_COMMANDS,
    }


def _markdown(status: dict) -> str:
    lines = [
        "# Project Status",
        "",
        f"**Generated:** {status['generated_at']}",
        f"**Classification:** `{status['classification']}`",
        f"**Submission ready:** {status['submission_ready']}",
        "",
        "## Build phases completed",
        "",
    ]
    for phase in status["build_phases_completed"]:
        lines.append(f"- {phase}")
    lines.extend(["", "## Fast checks", ""])
    if status["fast_check"]:
        fc = status["fast_check"]
        lines.append(f"- `make fast-check`: {'PASS' if fc['passed'] else 'FAIL'} ({fc['runtime_seconds']}s)")
    else:
        lines.append("- Run `make fast-check` locally (skipped during status generation)")
    lines.extend(["", "## Evidence status", ""])
    ev = status["evidence_status"]
    lines.append(f"- Completed runs: {ev['completed_runs']} (stub={ev['stub_runs']}, mock={ev['mock_runs']})")
    lines.append(f"- Interrupted runs: {ev['interrupted_runs']}")
    lines.append(f"- Provider pilot runs: {ev['provider_pilot_runs']}")
    lines.extend(["", "### Claim ledger", ""])
    for cid, st in sorted(status["evidence_status"]["claims"].items()):
        lines.append(f"- **{cid}:** {st}")
    lines.extend(["", "## Blockers", ""])
    for item in status["blockers"]:
        lines.append(f"- {item}")
    if not status["blockers"]:
        lines.append("- none")
    lines.extend(["", "## Ready artifacts", ""])
    for item in status["artifacts_ready"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Blocked artifacts", ""])
    for item in status["artifacts_blocked"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Safe commands", ""])
    for cmd in status["safe_commands"]:
        lines.append(f"```bash\n{cmd}\n```")
    lines.extend(["", "## Do not run (without approval)", ""])
    for cmd in status["unsafe_commands"]:
        lines.append(f"- `{cmd}`")
    lines.extend(["", "## Next recommended steps", ""])
    for step in status["next_steps"]:
        lines.append(f"- {step}")
    if not status["next_steps"]:
        lines.append("- Review `handoff/PROFESSOR_READY_CHECKLIST.md` before advisor meeting")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate PROJECT_STATUS files.")
    parser.add_argument("--run-fast-check", action="store_true", help="Also run make fast-check (slower).")
    args = parser.parse_args(argv)

    status = build_status(run_fast_check=args.run_fast_check)
    md_path = ROOT / "PROJECT_STATUS.md"
    json_path = ROOT / "PROJECT_STATUS.json"
    md_path.write_text(_markdown(status), encoding="utf-8")
    json_path.write_text(json.dumps(status, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
