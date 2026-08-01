from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.manipulation_checks import (
    INTERVENTION_CHECK_LINKAGE,
    REQUIRED_DETERMINISTIC_CHECKS,
    build_manipulation_check_report,
    evaluate_manipulation_check,
)

REPO = Path(__file__).resolve().parents[1]


def _instance(family: str, **updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "instance_id": f"task.{family}",
        "available_tools": ["fallback"],
        "initial_memory": {},
        "intervention": {
            "family": family,
            "tool_availability_patch": {},
            "tool_output_patch": {},
            "memory_patch": {},
            "metadata": {},
        },
    }
    row.update(updates)
    return row


def test_required_check_registry_is_complete() -> None:
    assert set(INTERVENTION_CHECK_LINKAGE.values()) >= (
        REQUIRED_DETERMINISTIC_CHECKS
    )


def test_eight_required_deterministic_checks_pass() -> None:
    rows = [
        _instance(
            "tool_removal",
            intervention={
                "family": "tool_removal",
                "tool_availability_patch": {
                    "removed_tools": ["required"]
                },
            },
        ),
        _instance(
            "tool_failure",
            intervention={
                "family": "tool_failure",
                "tool_output_patch": {
                    "target_tool": "search",
                    "error": "deterministic_failure",
                },
            },
        ),
        _instance(
            "web_stale_page",
            intervention={
                "family": "web_stale_page",
                "tool_output_patch": {
                    "source_timestamp": "2025-01-01T00:00:00Z",
                    "reference_timestamp": "2025-03-01T00:00:00Z",
                    "staleness_threshold_days": 30,
                },
            },
        ),
        _instance(
            "observation_conflict",
            intervention={
                "family": "observation_conflict",
                "tool_output_patch": {
                    "conflicting_observation": {
                        "source_a": "approved",
                        "source_b": "denied",
                    }
                },
            },
        ),
        _instance(
            "premature_success_signal",
            intervention={
                "family": "premature_success_signal",
                "tool_output_patch": {
                    "premature_completion_message": "Looks complete."
                },
            },
        ),
        _instance(
            "web_hidden_evidence",
            intervention={
                "family": "web_hidden_evidence",
                "tool_output_patch": {
                    "hidden_evidence": {"record_id": "required"}
                },
            },
        ),
        _instance(
            "distractor_evidence",
            intervention={
                "family": "distractor_evidence",
                "tool_output_patch": {
                    "distractor_record": {"record_id": "irrelevant"}
                },
            },
        ),
        _instance(
            "memory_corruption",
            initial_memory={"is_corrupted": True},
            intervention={
                "family": "memory_corruption",
                "memory_patch": {"is_corrupted": True},
            },
        ),
    ]
    results = [evaluate_manipulation_check(row) for row in rows]
    assert {result["check_name"] for result in results} == (
        REQUIRED_DETERMINISTIC_CHECKS
    )
    assert all(result["status"] == "PASS" for result in results)


def test_missing_marker_blocks_instead_of_guessing() -> None:
    result = evaluate_manipulation_check(_instance("tool_failure"))
    assert result["status"] == "BLOCKED"
    assert result["passed"] is None
    assert result["reason_code"] == "FAILURE_MARKER_MISSING"


def test_report_links_every_compact20_candidate_deterministically() -> None:
    manifest = (
        REPO
        / "data/compact20_reviewed/compact20_reviewed_manifest.json"
    )
    instances = (
        REPO
        / "data/compact20_reviewed/compact20_v2_instances.jsonl"
    )
    first = build_manipulation_check_report(manifest, instances)
    second = build_manipulation_check_report(manifest, instances)
    assert first == second
    assert first["candidate_count"] == 20
    assert first["record_count"] == 20
    assert first["all_candidates_linked"] is True
    assert first["all_applicable_checks_passed"] is True
    assert len(
        {
            record["linkage_id"]
            for record in first["records"]
        }
    ) == 20


def test_report_fails_when_candidate_instance_is_missing(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "c1",
                        "intervention_instance_id": "missing",
                        "family": "tool_removal",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    instances = tmp_path / "instances.jsonl"
    instances.write_text("", encoding="utf-8")
    report = build_manipulation_check_report(manifest, instances)
    assert report["all_applicable_checks_passed"] is False
    assert report["blocked_count"] == 1
