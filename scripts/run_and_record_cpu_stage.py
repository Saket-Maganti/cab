#!/usr/bin/env python3
"""Run one provider-free CPU validation command and append a durable ledger row."""

from __future__ import annotations

import argparse
import json
import os
import resource
import shlex
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
LEDGER_JSONL = REPORTS / "CAB_CPU_EXECUTION_LEDGER.jsonl"
LEDGER_MD = REPORTS / "CAB_CPU_EXECUTION_LEDGER.md"
LOG_DIR = Path("/tmp/cab_cpu_execution_logs")


def timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def disk_bytes(path: Path) -> int:
    stat = os.statvfs(path)
    return stat.f_bavail * stat.f_frsize


def render_markdown() -> None:
    entries = [
        json.loads(line)
        for line in LEDGER_JSONL.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    lines = [
        "# CAB CPU Execution Ledger",
        "",
        "Measurements are `MEASURED_ON_LOCAL_M4`. Peak RSS is the maximum child-process "
        "resident set observed by `getrusage`; `null` means unavailable.",
        "",
        "| Run | Command | Seconds | Exit | Expected | Peak RSS MiB | Disk Δ MiB | Status |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for entry in entries:
        command = entry["command"].replace("|", "\\|")
        peak = entry["peak_resident_memory_bytes"]
        peak_text = "" if peak is None else f"{peak / 1024 / 1024:.1f}"
        delta = (entry["disk_after_bytes"] - entry["disk_before_bytes"]) / 1024 / 1024
        lines.append(
            f"| {entry['run_id']} | `{command}` | {entry['elapsed_seconds']:.3f} | "
            f"{entry['exit_code']} | {entry['expected_exit_code']} | {peak_text} | "
            f"{delta:.2f} | {entry['status']} |"
        )
        if entry["failure_summary"]:
            lines.extend(["", f"- **{entry['run_id']} note:** {entry['failure_summary']}"])
    lines.extend(
        [
            "",
            "Full command logs are retained outside the repository under "
            "`/tmp/cab_cpu_execution_logs` for this execution session.",
            "",
        ]
    )
    LEDGER_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-exit", type=int, default=0)
    parser.add_argument("--evidence-class", default="CPU_VALIDATION")
    parser.add_argument("--generated-path", action="append", default=[])
    parser.add_argument("--failure-summary", default="")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")

    REPORTS.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    command_text = shlex.join(args.command)
    log_path = LOG_DIR / f"{args.run_id.replace('/', '_')}.log"
    start = timestamp()
    start_clock = time.perf_counter()
    disk_before = disk_bytes(ROOT)
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.run(
            args.command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    disk_after = disk_bytes(ROOT)
    elapsed = time.perf_counter() - start_clock
    end = timestamp()
    peak_bytes = max(usage_after, usage_before)
    # macOS reports ru_maxrss in bytes; Linux reports KiB.
    if os.uname().sysname != "Darwin":
        peak_bytes *= 1024
    status = "PASS" if process.returncode == args.expected_exit else "UNEXPECTED_FAILURE"
    summary = args.failure_summary
    if status != "PASS" and not summary:
        tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-8:]
        summary = " / ".join(line.strip() for line in tail if line.strip())[:1000]
    summary = summary.replace(f"{ROOT}/", "<REPO>/")
    entry = {
        "run_id": args.run_id,
        "command": command_text,
        "working_directory": ".",
        "start_timestamp": start,
        "end_timestamp": end,
        "elapsed_seconds": round(elapsed, 6),
        "exit_code": process.returncode,
        "expected_exit_code": args.expected_exit,
        "peak_resident_memory_bytes": peak_bytes or None,
        "disk_before_bytes": disk_before,
        "disk_after_bytes": disk_after,
        "generated_paths": args.generated_path,
        "evidence_class": args.evidence_class,
        "status": status,
        "failure_summary": summary,
        "log_path": str(log_path),
    }
    with LEDGER_JSONL.open("a", encoding="utf-8") as ledger:
        ledger.write(json.dumps(entry, sort_keys=True) + "\n")
    render_markdown()
    print(json.dumps(entry, indent=2))
    if log_path.exists():
        print(f"\n--- tail: {log_path} ---")
        print("\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]))
    return 0 if status == "PASS" else process.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
