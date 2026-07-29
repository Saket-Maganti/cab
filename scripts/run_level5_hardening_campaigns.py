#!/usr/bin/env python3
"""Generate compact, provider-free Level-5 hardening campaign receipts."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from causal_agent_bench.level5.evaluator import run_evaluator_malicious_campaign
from causal_agent_bench.level5.execution import (
    run_crash_consistency_demo,
    run_scheduler_stress,
)
from causal_agent_bench.level5.redteam import run_hardening_redteam_campaign
from causal_agent_bench.level5.reliability import run_fixture_chaos_campaign


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument(
        "--evaluator-image",
        default="cab/evaluator-fixture:local",
        help="A prebuilt local image; this script never pulls an image.",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.workdir.mkdir(parents=True, exist_ok=True)

    scheduler = run_scheduler_stress(args.workdir / "scheduler")
    scheduler["crash_consistency"] = run_crash_consistency_demo(
        args.workdir / "crash-consistency"
    )
    _write(args.output_dir / "SCHEDULER_STRESS_REPORT.json", scheduler)

    faults = run_fixture_chaos_campaign(workdir=args.workdir / "faults")
    _write(args.output_dir / "REAL_FAULT_INJECTION_REPORT.json", faults)

    evaluator = run_evaluator_malicious_campaign(
        image=args.evaluator_image,
        execute_containers=shutil.which("docker") is not None,
    )
    evaluator["requested_image"] = args.evaluator_image
    evaluator["image_pull_performed"] = False
    _write(args.output_dir / "EVALUATOR_MALICIOUS_FIXTURE_REPORT.json", evaluator)

    redteam = run_hardening_redteam_campaign()
    _write(args.output_dir / "REDTEAM_HARDENING_REPORT.json", redteam)

    summary = {
        "scheduler_passed": scheduler["passed"],
        "crash_consistency_passed": scheduler["crash_consistency"]["passed"],
        "fault_campaign_passed": faults["passed"],
        "evaluator_campaign_passed": evaluator["passed"],
        "evaluator_not_executed_count": evaluator["not_executed_count"],
        "redteam_passed": redteam["passed"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
