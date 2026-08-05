#!/usr/bin/env python3
"""Run every legal local CPU gate and write down what actually happened.

One process runs the gates in order and records each one's exit status, duration
and output tail, so the ledger is a record of a run rather than a transcription
of one.  A gate that fails is recorded as failed and the run keeps going, because
a summary that stops at the first failure hides the other three.

Nothing here invokes a model or a provider, and nothing here can authorize one.
Parallelism is bounded on purpose: this is expected to run on a 16 GiB laptop,
and an unbounded worker count there produces memory failures that look like test
failures.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "post_human_review"

#: Tail kept per gate.  Enough to see a failure, short enough that the ledger
#: stays readable and never becomes a place logs are hidden.
OUTPUT_TAIL_LINES = 24

#: Gates known to fail for reasons that predate this work, with the commit the
#: failure was reproduced at.  This does not excuse them and does not make the
#: run pass — a listed gate is still recorded as failed.  It records *why*, so a
#: reader is not left to guess whether the change under test caused it.
#:
#: Anything not on this list failing is a regression.
KNOWN_PREEXISTING: dict[str, dict[str, str]] = {
    "leakage_gate": {
        "reproduced_at": "22dbff07056492bdeaa02fb82a75110282bf1f4c",
        "cause": (
            "task_intervention_lint reports contract blockers on the public development splits "
            "(compact20_pilot 3, scale100 600, naturalistic 432, main500 3000, contaminated "
            "held-out 300). Identical counts at the starting commit and at its parent."
        ),
    },
    "max_ceiling_validation": {
        "reproduced_at": "22dbff07056492bdeaa02fb82a75110282bf1f4c",
        "cause": (
            "its unified_build_gate check inherits the leakage blockers above, and additionally "
            "reads the production review workspace, which correctly reports HUMAN_REVIEW_INCOMPLETE "
            "because this review was imported under a separate origin that production gates refuse "
            "by design."
        ),
    },
}


@dataclass(frozen=True)
class Gate:
    gate_id: str
    purpose: str
    command: tuple[str, ...]


def gates(*, workers: int) -> tuple[Gate, ...]:
    python = sys.executable
    return (
        Gate("fast_check", "the repository's own fast pre-commit gate", (python, "scripts/run_fast_checks.py")),
        Gate(
            "ruff",
            "lint the whole tree",
            (python, "-m", "ruff", "check", "."),
        ),
        Gate("mypy", "type-check the whole tree", (python, "-m", "mypy")),
        Gate("codespell", "spelling in prose and identifiers", ("codespell",)),
        Gate(
            "pytest_full",
            f"the complete provider-free test suite, bounded to {workers} workers",
            (python, "-m", "pytest", "-q", f"-n{workers}"),
        ),
        Gate(
            "max_ceiling_validation",
            "the recorded provider-free validation ledger, every lane",
            (
                python,
                "scripts/run_cab_max_ceiling_validation.py",
                "--lane",
                "all",
                "--output",
                "reports/post_human_review/CAB_VALIDATION_LEDGER.json",
            ),
        ),
        Gate(
            "structured_data",
            "every tracked JSON, YAML, CSV and notebook parses",
            (python, "scripts/validate_tracked_structured_data.py"),
        ),
        Gate("security_check", "no secret or private material is tracked", (python, "scripts/security_check.py")),
        Gate("leakage_gate", "no held-out material reachable from public files", (python, "scripts/cab_leakage_gate.py")),
        Gate("release_check", "release inventory and packaging invariants", (python, "scripts/release_check.py")),
        Gate(
            "kaggle_notebooks_static",
            "T4x2 notebooks: valid JSON, no stale outputs, no filename dependence",
            (python, "scripts/validate_kaggle_notebooks.py"),
        ),
        Gate(
            "kaggle_notebooks_offline",
            "T4x2 notebooks actually executed offline against fixtures",
            (python, "scripts/validate_kaggle_notebooks.py", "--execute-offline"),
        ),
        Gate(
            "kaggle_cpu_notebooks_static",
            "CPU notebooks match their generator and carry no committed output",
            (python, "scripts/validate_kaggle_cpu_notebooks.py"),
        ),
        Gate(
            "kaggle_cpu_notebooks_offline",
            "CPU notebooks executed offline against a randomly renamed bundle",
            (python, "scripts/validate_kaggle_cpu_notebooks.py", "--execute-offline"),
        ),
        Gate(
            "kaggle_arbitrary_name_probe",
            "the real bundle is found by content under hostile names and shapes",
            (python, "scripts/cab_kaggle_arbitrary_name_probe.py"),
        ),
    )


def run_gate(gate: Gate, env: dict[str, str]) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        list(gate.command),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    duration = round(time.monotonic() - started, 2)
    output = (completed.stdout or "") + (completed.stderr or "")
    tail = [line for line in output.strip().splitlines() if line.strip()][-OUTPUT_TAIL_LINES:]
    return {
        "gate_id": gate.gate_id,
        "purpose": gate.purpose,
        "command": " ".join(gate.command),
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "duration_seconds": duration,
        "output_tail": tail,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
    }


def _pytest_counts(entry: dict[str, Any]) -> dict[str, int]:
    """Pull the pass/fail/skip counts out of pytest's own summary line."""

    counts: dict[str, int] = {}
    for line in reversed(entry.get("output_tail") or []):
        if " passed" not in line and " failed" not in line and " error" not in line:
            continue
        for token in ("passed", "failed", "skipped", "xfailed", "error", "errors"):
            for index, word in enumerate(line.replace(",", " ").split()):
                if word.rstrip(",") == token and index:
                    previous = line.replace(",", " ").split()[index - 1]
                    if previous.isdigit():
                        counts[token] = int(previous)
        if counts:
            break
    return counts


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Local CPU execution ledger",
        "",
        f"- Recorded: `{summary['recorded_at_utc']}`",
        f"- Commit: `{summary['commit']}`",
        f"- Worktree clean at start: `{summary['tracked_worktree_clean_at_start']}`",
        f"- Host: `{summary['host']['platform']}`, "
        f"{summary['host']['cpu_count']} CPUs, pytest workers `{summary['pytest_workers']}`",
        f"- Gates: **{summary['passed_gate_count']}/{summary['gate_count']} passed**",
        f"- Regressions introduced here: **{summary['regressions'] or 'none'}**",
        f"- Failing for reasons that predate this work: "
        f"`{summary['failed_gates_preexisting'] or 'none'}`",
        f"- Model or provider invoked: `{summary['model_or_provider_invoked']}`",
        f"- Genuine model trajectories: `{summary['genuine_model_trajectories']}`",
        "",
        "| Gate | Result | Seconds | What it checks |",
        "| --- | --- | ---: | --- |",
    ]
    for entry in summary["gates"]:
        if entry["passed"]:
            result = "pass"
        elif entry.get("preexisting"):
            result = f"**FAIL ({entry['exit_code']})** — pre-existing"
        else:
            result = f"**FAIL ({entry['exit_code']})** — regression"
        lines.append(
            f"| `{entry['gate_id']}` | {result} | {entry['duration_seconds']:.1f} | {entry['purpose']} |"
        )
    if summary["failed_gates"]:
        lines += ["", "## Failed gates", ""]
        for entry in summary["gates"]:
            if entry["passed"]:
                continue
            lines += [f"### `{entry['gate_id']}`", ""]
            known = entry.get("preexisting")
            if known:
                lines += [
                    f"Pre-existing. Reproduced unchanged at `{known['reproduced_at']}`, "
                    f"before any commit in this line of work.",
                    "",
                    known["cause"],
                    "",
                ]
            lines += ["```text", *entry["output_tail"], "```", ""]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="pytest worker count. Bounded deliberately; never use -n auto on a 16 GiB machine.",
    )
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8 on this machine")

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT / "src"), str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)

    def git(*command: str) -> str:
        return subprocess.run(
            ["git", *command], cwd=REPO_ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()

    clean_at_start = not git("status", "--porcelain", "--untracked-files=no")
    entries = [run_gate(gate, env) for gate in gates(workers=args.workers)]
    for entry in entries:
        known = KNOWN_PREEXISTING.get(entry["gate_id"])
        if not entry["passed"] and known:
            entry["preexisting"] = known
    failed = [entry["gate_id"] for entry in entries if not entry["passed"]]
    regressions = [gate_id for gate_id in failed if gate_id not in KNOWN_PREEXISTING]
    by_id = {entry["gate_id"]: entry for entry in entries}

    summary = {
        "schema_version": "cab_local_cpu_validation_summary_v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "commit": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "tracked_worktree_clean_at_start": clean_at_start,
        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "pytest_workers": args.workers,
        "gate_count": len(entries),
        "passed_gate_count": sum(1 for entry in entries if entry["passed"]),
        "failed_gates": failed,
        "failed_gates_preexisting": [gate for gate in failed if gate in KNOWN_PREEXISTING],
        "regressions": regressions,
        "no_regressions": not regressions,
        "passed": not failed,
        "pytest_counts": _pytest_counts(by_id.get("pytest_full", {})),
        # Stated rather than assumed: this driver runs no provider client and
        # every gate it invokes is provider-free by construction.
        "model_or_provider_invoked": False,
        "genuine_model_trajectories": 0,
        "gates": entries,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "LOCAL_CPU_VALIDATION_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    with (args.output_dir / "LOCAL_CPU_EXECUTION_LEDGER.jsonl").open("w") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    (args.output_dir / "LOCAL_CPU_EXECUTION_LEDGER.md").write_text(markdown(summary))

    print(
        json.dumps(
            {key: value for key, value in summary.items() if key != "gates"},
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    if shutil.which("git") is None:
        raise SystemExit("git is required to record the ledger")
    raise SystemExit(main())
