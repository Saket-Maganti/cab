"""Synthetic trajectory fixture diagnostics.

These helpers validate deterministic metric-diagnostic fixtures only. They do
not interpret fixtures as real LLM behavior or scientific evidence.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

REQUIRED_METADATA = {
    "synthetic_fixture": True,
    "not_real_llm_behavior": True,
    "scientific_evidence": False,
    "deployment_class": "metric_diagnostic_only",
    "paper_eligible": False,
}
EXPECTED_FAILURE_CATEGORIES = frozenset(
    {
        "tool_overuse",
        "premature_stopper",
        "contradiction_blind",
        "memory_blind",
        "argument_sloppy",
        "recovery_weak",
        "final_answer_hallucinator",
        "retry_loop_agent",
    }
)


def build_synthetic_fixture_report(
    repo_root: str | Path,
    *,
    fixtures_dir: str | Path = "tests/fixtures/synthetic_trajectories",
    output_dir: str | Path = "reports/synthetic_fixtures",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    fixture_root = Path(fixtures_dir)
    if not fixture_root.is_absolute():
        fixture_root = root / fixture_root
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    fixtures = load_synthetic_fixtures(fixture_root)
    results = [validate_synthetic_fixture(name, fixture) for name, fixture in fixtures.items()]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Synthetic metric diagnostics only; not real LLM behavior and not scientific evidence.",
        "fixtures_dir": str(fixture_root),
        "summary": {
            "fixture_count": len(results),
            "passed": sum(1 for item in results if item["passed"]),
            "failed": sum(1 for item in results if not item["passed"]),
        },
        "fixtures": results,
    }
    md = synthetic_fixture_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="synthetic_fixture_metric_report",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load_synthetic_fixtures(fixtures_dir: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(fixtures_dir)
    fixtures: dict[str, dict[str, Any]] = {}
    if not root.exists():
        return fixtures
    for path in sorted(root.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            fixtures[path.stem] = value
    return fixtures


def validate_synthetic_fixture(name: str, fixture: dict[str, Any]) -> dict[str, Any]:
    metadata = fixture.get("metadata") if isinstance(fixture.get("metadata"), dict) else {}
    errors: list[str] = []
    warnings: list[str] = []
    for key, expected in REQUIRED_METADATA.items():
        if metadata.get(key) != expected:
            errors.append(f"metadata.{key} must be {expected!r}")
    category = str(metadata.get("expected_failure_category") or fixture.get("expected_failure_category") or "")
    if category not in EXPECTED_FAILURE_CATEGORIES:
        errors.append("expected failure category missing or unknown")
    signals = analyze_trajectory_signals(fixture)
    expected_signal = str(metadata.get("expected_metric_signal") or "")
    if expected_signal and not signals["flags"].get(expected_signal, False):
        errors.append(f"expected signal {expected_signal!r} was not detected")
    if metadata.get("scientific_evidence") is True:
        errors.append("synthetic fixture cannot be scientific_evidence=true")
    if metadata.get("paper_eligible") is True:
        errors.append("synthetic fixture cannot be paper_eligible=true")
    if not fixture.get("steps"):
        warnings.append("fixture has no steps")
    return {
        "fixture": name,
        "expected_failure_category": category,
        "expected_metric_signal": expected_signal,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "signals": signals,
    }


def analyze_trajectory_signals(trajectory: dict[str, Any]) -> dict[str, Any]:
    steps = trajectory.get("steps") if isinstance(trajectory.get("steps"), list) else []
    tool_calls: list[tuple[str, str]] = []
    invalid_arguments = 0
    tool_errors = 0
    recovery_after_error = False
    saw_error = False
    contradiction_present = False
    contradiction_addressed = False
    memory_required = False
    memory_verified = False

    for step in steps:
        if not isinstance(step, dict):
            continue
        tool_call = step.get("tool_call") if isinstance(step.get("tool_call"), dict) else None
        args = step.get("tool_arguments") or (tool_call or {}).get("arguments") or {}
        if tool_call:
            tool_calls.append((str(tool_call.get("tool_name") or "unknown"), json.dumps(args, sort_keys=True)))
        parser_status = str(step.get("parser_status") or "")
        if parser_status == "invalid_argument_schema" or (
            isinstance(args, dict) and args.get("__malformed__") is True
        ):
            invalid_arguments += 1
        if step.get("tool_error_status") in {"error", "failed", "tool_error"}:
            tool_errors += 1
            saw_error = True
        if saw_error and step.get("recovery_marker") is True:
            recovery_after_error = True
        if step.get("contradiction_marker") in {True, "present", "ignored"}:
            contradiction_present = True
        if step.get("contradiction_marker") in {"addressed", "resolved"}:
            contradiction_addressed = True
        if step.get("memory_use_marker") in {"required", "missing", "ignored"}:
            memory_required = True
        if step.get("memory_use_marker") in {"verified", "used_verified_memory"}:
            memory_verified = True
    call_counts = Counter(tool_calls)
    final_answer = str(trajectory.get("final_answer") or "")
    metadata = trajectory.get("metadata") if isinstance(trajectory.get("metadata"), dict) else {}
    flags = {
        "excessive_tool_calls": len(tool_calls) >= int(metadata.get("tool_call_overuse_threshold", 6)),
        "too_few_steps": len(steps) <= int(metadata.get("premature_step_threshold", 1)),
        "missing_final_answer": not bool(final_answer.strip()),
        "repeated_calls": any(count >= 3 for count in call_counts.values()),
        "unsupported_final_answer": "unsupported" in final_answer.lower()
        or metadata.get("unsupported_final_answer") is True,
        "ignored_contradiction": contradiction_present and not contradiction_addressed,
        "ignored_memory_verification": memory_required and not memory_verified,
        "failed_recovery_after_tool_error": tool_errors > 0 and not recovery_after_error,
        "malformed_tool_args": invalid_arguments > 0,
    }
    return {
        "step_count": len(steps),
        "tool_call_count": len(tool_calls),
        "repeated_call_count": sum(count for count in call_counts.values() if count >= 2),
        "tool_error_count": tool_errors,
        "invalid_argument_count": invalid_arguments,
        "flags": flags,
    }


def synthetic_fixture_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Synthetic Fixture Metric Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Fixtures: {summary['fixture_count']}",
                f"- Passed: {summary['passed']}",
                f"- Failed: {summary['failed']}",
            ],
        ),
        "## Fixtures",
        "",
    ]
    for fixture in payload["fixtures"]:
        lines.extend(
            [
                f"### `{fixture['fixture']}`",
                "",
                f"- Category: `{fixture['expected_failure_category']}`",
                f"- Expected signal: `{fixture['expected_metric_signal']}`",
                f"- Passed: `{fixture['passed']}`",
                f"- Detected flags: {', '.join(k for k, v in fixture['signals']['flags'].items() if v) or '(none)'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
