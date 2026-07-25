from __future__ import annotations

from pathlib import Path

from scripts.run_cab_max_ceiling_validation import (
    _command_metadata,
    _summary,
    validation_plan,
)

ROOT = Path(__file__).resolve().parents[1]


def test_validation_plan_is_provider_free_and_covers_required_lanes() -> None:
    plan = validation_plan(ROOT)
    ids = {row.check_id for row in plan}
    assert {"fast", "medium", "full"} == {row.lane for row in plan}
    assert {
        "package_imports",
        "full_test_collection",
        "typed_scorer_fixture",
        "paired_metrics_fixture",
        "leakage_and_task_contract_gate",
        "canonical_split_registry",
        "human_review_c10",
        "kaggle_notebooks_offline_fixture",
        "security_scan",
        "claim_ledger",
        "paper_draft_compile",
        "release_validation",
        "full_provider_free_tests",
        "unified_build_gate",
    } <= ids
    rendered = "\n".join(" ".join(row.command).lower() for row in plan)
    assert "allow_paid_calls=true" not in rendered
    assert "run_live=true" not in rendered


def test_expected_blocker_does_not_fail_build_summary() -> None:
    rows = [
        {
            "check_id": "build",
            "outcome": "PASS",
            "required_for_build": True,
            "accepted": True,
        },
        {
            "check_id": "human",
            "outcome": "EXPECTED_BLOCKED",
            "required_for_build": False,
            "accepted": True,
        },
    ]
    summary = _summary(rows)
    assert summary["build_validation_passed"] is True
    assert summary["expected_blocked"] == 1


def test_collection_metadata_parser() -> None:
    assert _command_metadata(
        "full_test_collection",
        "937 tests collected in 1.23s\n",
        "",
    )["tests_collected"] == 937
