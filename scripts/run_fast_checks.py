#!/usr/bin/env python3
"""Fast local/CI checks — no long model runs."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def run(cmd: list[str], *, label: str) -> None:
    print(f"\n==> {label}")
    print("$", " ".join(cmd))
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{SRC}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(SRC)
    )
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def main() -> int:
    started = time.monotonic()
    py = sys.executable
    run([py, "-m", "ruff", "check", "."], label="ruff lint")
    run([py, "-m", "mypy"], label="mypy typed core")
    run([py, "-m", "causal_agent_bench", "--help"], label="CLI help")
    run(
        [
            py,
            "-m",
            "pytest",
            "-q",
            "tests/test_run_management.py",
            "tests/test_zero_cost_readiness.py",
            "tests/test_experiment_runner.py",
            "tests/test_io_repro_cli.py",
            "tests/test_build_phase2.py",
            "tests/test_build_phase3.py",
            "tests/test_build_phase4.py",
            "tests/test_build_phase5.py",
            "tests/test_build_phase6.py",
            "tests/test_build_phase7.py",
            "tests/test_build_phase8.py",
            "tests/test_build_phase9.py",
            "--maxfail=1",
        ],
        label="fast pytest subset",
    )
    for config in [
        "configs/pilot_free_local_micro_3.yaml",
        "configs/pilot_stub_micro_3.yaml",
        "configs/pilot_mock_agents_10.yaml",
        "configs/pilot_mock_diagnostic_micro.yaml",
    ]:
        run(
            [py, "scripts/check_zero_cost_readiness.py", "--config", config, "--require", "zero_cost_ready"],
            label=f"zero-cost readiness: {config}",
        )
    run([py, "-m", "causal_agent_bench", "validate-config", "--config", "configs/pilot_stub_micro_3.yaml"], label="validate micro stub config")
    run([py, "-m", "causal_agent_bench", "plan-run", "--config", "configs/pilot_stub_micro_3.yaml"], label="plan-run stub micro")
    run([py, "-m", "causal_agent_bench", "plan-run", "--config", "configs/pilot_mock_diagnostic_micro.yaml"], label="plan-run mock diagnostic micro")
    run([py, "scripts/check_claim_ledger.py"], label="claim ledger")
    run([py, "scripts/check_paper_placeholders.py", "--mode", "draft"], label="paper placeholders draft")
    run([py, "scripts/check_evidence_safety.py"], label="evidence safety")
    subprocess.run([py, "scripts/check_run_index.py"], cwd=ROOT, check=False)
    run(
        [
            py,
            "-m",
            "pytest",
            "-q",
            "-n0",
            "tests/test_mega_cleanup.py",
            "tests/test_god_tier_status.py",
            "tests/test_check_run_index.py",
            "tests/test_safety_reports.py",
        ],
        label="governance pytest lane",
    )
    run([py, "scripts/god_tier_status.py", "--json"], label="god-tier status")
    run([py, "scripts/security_check.py"], label="security check")
    elapsed = time.monotonic() - started
    print(f"\nfast checks completed in {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
