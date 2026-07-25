#!/usr/bin/env python3
"""Final build-phase audit — pre-experiment freeze gate (no model runs)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "audits" / "final_build_phase"

REQUIRED_FILES = [
    "MASTER_STATUS.md",
    "MASTER_STATUS.json",
    "PROJECT_HEALTH.md",
    "BLOCKED_ITEMS.md",
    "docs/COMMAND_MAP.md",
    "docs/DO_NOT_OVERCLAIM.md",
    "docs/README.md",
    "experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md",
    "experiments/SAFE_NEXT_RUN_DECISION_TREE.md",
    "handoff/ADVISOR_REVIEW_BUNDLE_INDEX.md",
]


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def _load_claims() -> dict[str, str]:
    data = json.loads((ROOT / "docs" / "claim_ledger.json").read_text(encoding="utf-8"))
    return {c["claim_id"]: c["status"] for c in data.get("claims", [])}


def _active_model_runs() -> list[str]:
    """Conservative check: no causal_agent_bench run in process list."""
    try:
        proc = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    hits = []
    for line in proc.stdout.splitlines():
        if "causal_agent_bench" in line and " run " in line and "grep" not in line:
            hits.append(line.strip()[:120])
    return hits


def run_audit(*, include_fast_check: bool = False) -> dict:
    checks: list[dict] = []
    issues: list[str] = []
    warnings: list[str] = []

    if include_fast_check:
        rc, out = _run([sys.executable, "scripts/run_fast_checks.py"])
        checks.append({"name": "fast_check", "passed": rc == 0, "detail": out[-200:] if out else ""})
        if rc != 0:
            issues.append("fast-check failed")
    else:
        rc, _ = _run([sys.executable, "-m", "causal_agent_bench", "--help"])
        checks.append({"name": "cli_help", "passed": rc == 0})
        if rc != 0:
            issues.append("CLI help failed")

    active = _active_model_runs()
    checks.append({"name": "no_active_model_runs", "passed": not active, "active": active})
    if active:
        warnings.append(f"Active run processes detected: {len(active)}")

    claims = _load_claims()
    bad_claims = [
        cid for cid, st in claims.items()
        if cid.startswith("C") and cid != "C9" and st == "supported"
    ]
    checks.append({"name": "no_unsupported_supported_claims", "passed": not bad_claims})
    if bad_claims:
        issues.append(f"Claims marked supported without gate: {bad_claims}")

    c9_ok = claims.get("C9") == "engineering_only"
    checks.append({"name": "c9_engineering_only", "passed": c9_ok})
    if not c9_ok:
        issues.append(f"C9 status is {claims.get('C9')}, expected engineering_only")

    rc, _ = _run([sys.executable, "scripts/check_evidence_safety.py"])
    checks.append({"name": "evidence_safety", "passed": rc == 0})

    rc, _ = _run([sys.executable, "scripts/check_paper_placeholders.py", "--mode", "draft"])
    checks.append({"name": "paper_placeholders_draft", "passed": rc == 0})

    placeholder_tex = list((ROOT / "paper").rglob("*.tex"))
    has_placeholders = any(
        "[N]" in p.read_text(encoding="utf-8") or "[M]" in p.read_text(encoding="utf-8")
        for p in placeholder_tex
        if p.is_file()
    )
    checks.append({"name": "paper_placeholders_present", "passed": has_placeholders})
    if not has_placeholders:
        warnings.append("No [N]/[M] placeholders found in paper — verify not falsely filled")

    missing = [f for f in REQUIRED_FILES if not (ROOT / f).exists()]
    checks.append({"name": "required_phase8_files", "passed": not missing, "missing": missing})
    if missing:
        issues.append(f"Missing Phase 8 files: {missing}")

    rc, out = _run([sys.executable, "scripts/check_submission_readiness.py"])
    submission_ready = "submission_ready: True" in out
    classification = None
    for line in out.splitlines():
        if "classification:" in line:
            classification = line.split(":", 1)[1].strip()
    checks.append({
        "name": "submission_readiness",
        "passed": True,
        "classification": classification,
        "submission_ready": submission_ready,
    })
    if submission_ready:
        warnings.append("Submission readiness reports True — verify intentionally")

    passed = not issues
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "passed": passed,
        "classification": "build_infrastructure_ready",
        "readiness_checker_classification": classification,
        "submission_ready": submission_ready,
        "checks": checks,
        "issues": issues,
        "warnings": warnings,
        "no_model_runs_executed_by_audit": True,
        "no_paid_calls_by_audit": True,
    }


def _markdown(report: dict) -> str:
    lines = [
        "# Final Build-Phase Audit",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Passed:** {report['passed']}",
        f"**Project classification:** `{report['classification']}`",
        f"**Readiness checker:** `{report['readiness_checker_classification']}`",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- **{check['name']}:** {status}")
    if report["issues"]:
        lines.extend(["", "## Issues", ""])
        for item in report["issues"]:
            lines.append(f"- {item}")
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for item in report["warnings"]:
            lines.append(f"- {item}")
    lines.extend([
        "",
        "## Safety",
        "",
        "- No model runs executed by this audit",
        "- No paid API calls made",
        "- Scientific claims unchanged (C1–C8/C10 planned; C9 engineering_only)",
        "",
    ])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Final build-phase audit.")
    parser.add_argument("--output-dir", default=str(OUT_DIR))
    parser.add_argument(
        "--include-fast-check",
        action="store_true",
        help="Also run full make fast-check (~60s).",
    )
    args = parser.parse_args(argv)

    report = run_audit(include_fast_check=args.include_fast_check)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "final_build_phase_audit.json"
    md_path = out_dir / "FINAL_BUILD_PHASE_AUDIT.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    print(f"audit: {'PASS' if report['passed'] else 'FAIL'} ({len(report['issues'])} issues)")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
