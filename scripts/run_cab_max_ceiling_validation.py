#!/usr/bin/env python3
"""Run and record CAB's complete provider-free validation ledger.

The suite never invokes a model or provider.  Expected fail-closed human and
execution gates are recorded as blocked prerequisites rather than test passes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports/CAB_VALIDATION_LEDGER.json"


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    lane: str
    command: tuple[str, ...]
    evidence_class: str
    expected_exit_codes: frozenset[int] = field(
        default_factory=lambda: frozenset({0})
    )
    blocked_exit_codes: frozenset[int] = field(default_factory=frozenset)
    timeout_seconds: int = 600
    required_for_build: bool = True


def _python_code(code: str) -> tuple[str, ...]:
    return (sys.executable, "-c", code)


def validation_plan(root: Path = ROOT) -> list[CheckSpec]:
    focused_tests = [
        "tests/test_typed_final_scorer.py",
        "tests/test_scorer_robustness_fixture_only.py",
        "tests/test_phase5_paired_metrics.py",
        "tests/test_statistical_reporting.py",
        "tests/test_max_ceiling_generation_contract.py",
        "tests/test_cab_split_registry.py",
        "tests/test_run_manifest_v2.py",
        "tests/test_cab_human_review_gate.py",
        "tests/test_kaggle_notebooks.py",
        "tests/test_max_ceiling_gate.py",
        "tests/test_cab_phase2_phase3_gate.py",
    ]
    for optional in (
        "tests/test_cab_leakage_gate.py",
        "tests/test_cab_paper_plumbing.py",
        "tests/test_phase15_paper_plumbing.py",
        "tests/test_max_ceiling_ci_surface.py",
    ):
        if (root / optional).exists():
            focused_tests.append(optional)

    return [
        CheckSpec(
            "package_imports",
            "fast",
            (sys.executable, "scripts/check_package_import.py"),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "cli_help",
            "fast",
            (sys.executable, "-m", "causal_agent_bench", "--help"),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "full_test_collection",
            "fast",
            (sys.executable, "-m", "pytest", "--collect-only", "-q", "-n0"),
            "ENGINEERING_ONLY",
            timeout_seconds=300,
        ),
        CheckSpec(
            "ruff",
            "fast",
            (sys.executable, "-m", "ruff", "check", "."),
            "ENGINEERING_ONLY",
            timeout_seconds=300,
        ),
        CheckSpec(
            "mypy",
            "fast",
            (sys.executable, "-m", "mypy"),
            "ENGINEERING_ONLY",
            timeout_seconds=600,
        ),
        CheckSpec(
            "focused_contract_tests",
            "fast",
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-n0",
                *focused_tests,
            ),
            "FIXTURE_ONLY",
            timeout_seconds=600,
        ),
        CheckSpec(
            "typed_scorer_fixture",
            "fast",
            _python_code(
                "import json; "
                "from causal_agent_bench.metrics.typed_final_answer import "
                "typed_scorer_fixture_self_check as f; "
                "r=f(); print(json.dumps(r, sort_keys=True)); "
                "raise SystemExit(0 if r.get('status') == 'PASS' else 1)"
            ),
            "FIXTURE_ONLY",
        ),
        CheckSpec(
            "paired_metrics_fixture",
            "fast",
            _python_code(
                "import json; "
                "from causal_agent_bench.metrics.causal_robustness import "
                "paired_metrics_fixture_self_check as f; "
                "r=f(); print(json.dumps(r, sort_keys=True)); "
                "raise SystemExit(0 if r.get('passed') else 1)"
            ),
            "FIXTURE_ONLY",
        ),
        CheckSpec(
            "canonical_split_registry",
            "fast",
            _python_code(
                "from causal_agent_bench.safety.split_registry import "
                "validate_canonical_split_registry as v; "
                "r=v('.'); print('\\n'.join(r) if r else 'SPLIT_REGISTRY_PASS'); "
                "raise SystemExit(1 if r else 0)"
            ),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "leakage_and_task_contract_gate",
            "fast",
            (
                (sys.executable, "scripts/cab_leakage_gate.py")
                if (root / "scripts/cab_leakage_gate.py").exists()
                else (
                    sys.executable,
                    "-c",
                    "raise SystemExit('scripts/cab_leakage_gate.py missing')",
                )
            ),
            "ENGINEERING_ONLY",
            timeout_seconds=600,
        ),
        CheckSpec(
            "claim_ledger",
            "fast",
            (sys.executable, "scripts/check_claim_ledger.py", "--mode", "draft"),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "config_audit",
            "fast",
            (sys.executable, "scripts/audit_configs.py"),
            "ENGINEERING_ONLY",
            timeout_seconds=300,
        ),
        CheckSpec(
            "git_diff_check",
            "fast",
            ("git", "diff", "--check"),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "human_review_c10",
            "medium",
            (sys.executable, "scripts/validate_cab_human_reviews.py"),
            "HUMAN_INPUT_REQUIRED",
            expected_exit_codes=frozenset({2}),
            blocked_exit_codes=frozenset({2}),
            required_for_build=False,
        ),
        CheckSpec(
            "kaggle_notebooks_static",
            "medium",
            (sys.executable, "scripts/validate_kaggle_notebooks.py"),
            "FIXTURE_ONLY",
            timeout_seconds=300,
        ),
        CheckSpec(
            "kaggle_notebooks_offline_fixture",
            "medium",
            (
                sys.executable,
                "scripts/validate_kaggle_notebooks.py",
                "--execute-offline",
            ),
            "FIXTURE_ONLY",
            timeout_seconds=600,
        ),
        CheckSpec(
            "evidence_safety",
            "medium",
            (
                sys.executable,
                "scripts/check_evidence_safety.py",
                "--mode",
                "submission",
            ),
            "ENGINEERING_ONLY",
            timeout_seconds=300,
        ),
        CheckSpec(
            "paper_placeholders_draft",
            "medium",
            (
                sys.executable,
                "scripts/check_paper_placeholders.py",
                "--mode",
                "draft",
            ),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "paper_section_contract",
            "medium",
            (
                sys.executable,
                "scripts/check_paper_section_contract.py",
                "--mode",
                "draft",
            ),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "paper_assets_draft",
            "medium",
            (
                sys.executable,
                "scripts/check_paper_assets.py",
                "--mode",
                "draft",
            ),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "bibliography",
            "medium",
            (sys.executable, "scripts/check_bibliography.py", "--all-sections"),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "reviewer_proofing",
            "medium",
            (sys.executable, "scripts/check_reviewer_proofing.py"),
            "ENGINEERING_ONLY",
        ),
        CheckSpec(
            "paper_draft_compile",
            "medium",
            ("make", "paper-draft"),
            "ENGINEERING_ONLY",
            timeout_seconds=600,
        ),
        CheckSpec(
            "repository_consistency",
            "medium",
            (sys.executable, "scripts/audit_repo_consistency.py"),
            "ENGINEERING_ONLY",
            timeout_seconds=300,
        ),
        CheckSpec(
            "security_scan",
            "medium",
            (sys.executable, "scripts/security_check.py"),
            "ENGINEERING_ONLY",
            timeout_seconds=900,
        ),
        CheckSpec(
            "release_manifest_refresh",
            "medium",
            (sys.executable, "scripts/build_release_manifest.py"),
            "ENGINEERING_ONLY",
            timeout_seconds=300,
        ),
        CheckSpec(
            "release_validation",
            "medium",
            (sys.executable, "scripts/release_check.py"),
            "ENGINEERING_ONLY",
            timeout_seconds=300,
        ),
        CheckSpec(
            "full_provider_free_tests",
            "full",
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-n0",
                "-m",
                "not model and not provider and not local_run",
            ),
            "ENGINEERING_ONLY",
            timeout_seconds=1200,
        ),
        CheckSpec(
            "unified_build_gate",
            "full",
            (
                sys.executable,
                "scripts/cab_max_ceiling_gate.py",
                "--scope",
                "build",
            ),
            "ENGINEERING_ONLY",
            timeout_seconds=900,
        ),
        CheckSpec(
            "unified_execution_gate_fail_closed",
            "full",
            (
                sys.executable,
                "scripts/cab_max_ceiling_gate.py",
                "--scope",
                "execution",
                "--no-write",
            ),
            "EXECUTION_PENDING",
            expected_exit_codes=frozenset({2}),
            blocked_exit_codes=frozenset({2}),
            timeout_seconds=900,
            required_for_build=False,
        ),
    ]


def run_validation(
    specs: list[CheckSpec],
    *,
    output_path: Path = DEFAULT_OUTPUT,
    append: bool = False,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_json(output_path) if append else None
    if existing is not None:
        replace_ids = {spec.check_id for spec in specs}
        existing["commands"] = [
            row
            for row in existing.get("commands", [])
            if isinstance(row, dict) and row.get("check_id") not in replace_ids
        ]
        payload = existing
        payload["appended_at"] = datetime.now(UTC).isoformat()
    else:
        payload = {
            "schema_version": "cab_validation_ledger_v1",
            "started_at": datetime.now(UTC).isoformat(),
            "repository_root": str(ROOT),
            "provider_or_model_execution_performed": False,
            "commands": [],
            "summary": {},
        }
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            value
            for value in (str(ROOT / "src"), str(ROOT), os.environ.get("PYTHONPATH", ""))
            if value
        ),
        "PYTHONHASHSEED": "0",
        "MPLCONFIGDIR": "/tmp/cab-mpl",
    }

    for spec in specs:
        started = datetime.now(UTC)
        monotonic_start = time.monotonic()
        timed_out = False
        try:
            process = subprocess.run(
                list(spec.command),
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=spec.timeout_seconds,
                check=False,
            )
            exit_code: int | None = process.returncode
            stdout = process.stdout
            stderr = process.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = None
            stdout = _to_text(exc.stdout)
            stderr = _to_text(exc.stderr)

        elapsed = round(time.monotonic() - monotonic_start, 3)
        if timed_out:
            outcome = "TIMEOUT"
            accepted = False
        elif exit_code in spec.blocked_exit_codes:
            outcome = "EXPECTED_BLOCKED"
            accepted = True
        elif exit_code in spec.expected_exit_codes:
            outcome = "PASS"
            accepted = True
        else:
            outcome = "FAIL"
            accepted = False
        row = {
            "check_id": spec.check_id,
            "lane": spec.lane,
            "command": shlex.join(spec.command),
            "argv": list(spec.command),
            "working_directory": str(ROOT),
            "started_at": started.isoformat(),
            "elapsed_seconds": elapsed,
            "exit_code": exit_code,
            "expected_exit_codes": sorted(spec.expected_exit_codes),
            "outcome": outcome,
            "accepted": accepted,
            "required_for_build": spec.required_for_build,
            "evidence_class": spec.evidence_class,
            "scientific_evidence": False,
            "stdout_tail": stdout[-8000:],
            "stderr_tail": stderr[-8000:],
            "metadata": _command_metadata(spec.check_id, stdout, stderr),
        }
        payload["commands"].append(row)
        payload["summary"] = _summary(payload["commands"])
        payload["updated_at"] = datetime.now(UTC).isoformat()
        _write_json(output_path, payload)
        print(
            f"[{outcome}] {spec.check_id} rc={exit_code} "
            f"elapsed={elapsed:.3f}s",
            flush=True,
        )

    payload["completed_at"] = datetime.now(UTC).isoformat()
    payload["summary"] = _summary(payload["commands"])
    _write_json(output_path, payload)
    return payload


def _command_metadata(check_id: str, stdout: str, stderr: str) -> dict[str, Any]:
    text = f"{stdout}\n{stderr}"
    metadata: dict[str, Any] = {}
    if check_id == "full_test_collection":
        matches = re.findall(r"(\d+)\s+tests?\s+collected", text)
        if matches:
            metadata["tests_collected"] = int(matches[-1])
    passed = re.findall(r"(\d+)\s+passed", text)
    failed = re.findall(r"(\d+)\s+failed", text)
    deselected = re.findall(r"(\d+)\s+deselected", text)
    if passed:
        metadata["tests_passed"] = int(passed[-1])
    if failed:
        metadata["tests_failed"] = int(failed[-1])
    if deselected:
        metadata["tests_deselected"] = int(deselected[-1])
    return metadata


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required_failures = [
        row["check_id"]
        for row in rows
        if row["required_for_build"] and not row["accepted"]
    ]
    return {
        "commands_run": len(rows),
        "passed": sum(row["outcome"] == "PASS" for row in rows),
        "expected_blocked": sum(
            row["outcome"] == "EXPECTED_BLOCKED" for row in rows
        ),
        "failed": sum(row["outcome"] == "FAIL" for row in rows),
        "timed_out": sum(row["outcome"] == "TIMEOUT" for row in rows),
        "required_build_failures": required_failures,
        "build_validation_passed": not required_failures,
        "scientific_evidence_created": False,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _to_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lane",
        choices=("fast", "medium", "full", "all"),
        default="all",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Run only this check ID (repeatable).",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--append",
        action="store_true",
        help="Replace selected check IDs in an existing ledger and preserve all others.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the validation plan without executing it.",
    )
    args = parser.parse_args(argv)

    plan = validation_plan(ROOT)
    if args.only:
        selected = [spec for spec in plan if spec.check_id in set(args.only)]
        missing = sorted(set(args.only) - {spec.check_id for spec in selected})
        if missing:
            parser.error(f"unknown check IDs: {', '.join(missing)}")
    elif args.lane == "all":
        selected = plan
    else:
        selected = [spec for spec in plan if spec.lane == args.lane]

    if args.list:
        for spec in selected:
            print(f"{spec.lane}\t{spec.check_id}\t{shlex.join(spec.command)}")
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    payload = run_validation(selected, output_path=output, append=args.append)
    return 0 if payload["summary"]["build_validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
