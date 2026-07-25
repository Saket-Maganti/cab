"""Fixture-only tests: long_horizon_dependency isolation matches the generator.

The generator delivers long_horizon_dependency via a ``tool_output_patch``
dependency marker with ``expected_final_answer_change="no"`` (see
``generation/interventions.py``). The isolation taxonomy must treat that as the
intended causal factor — not as an unexpected multi-factor change.
"""

from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.intervention_isolation import (
    audit_intervention_isolation_instances,
    built_in_intervention_taxonomy,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _base_task() -> dict:
    return {
        "task_id": "task_1",
        "domain": "travel",
        "difficulty": "easy",
        "goal": {
            "user_instruction": "Plan the trip.",
            "success_criteria": ["Use the earlier observation."],
            "expected_final_answer": "depart 9am",
        },
        "available_tools": ["search_database", "compare_options"],
        "hidden_ground_truth": {"answer": "depart 9am"},
        "max_steps": 4,
    }


def _clean() -> dict:
    return {
        "instance_id": "task_1.clean",
        "base_task": _base_task(),
        "condition": "clean",
        "available_tools": ["search_database", "compare_options"],
        "initial_memory": {},
        "environment_seed": 1,
        "metadata": {},
    }


def _long_horizon() -> dict:
    return {
        "instance_id": "task_1.long_horizon_dependency",
        "base_task": _base_task(),
        "condition": "intervention",
        "available_tools": ["search_database", "compare_options"],
        "initial_memory": {},
        "environment_seed": 2,
        "intervention": {
            "intervention_id": "task_1.long_horizon_dependency",
            "base_task_id": "task_1",
            "family": "long_horizon_dependency",
            "tool_output_patch": {
                "target_tool": "search_database",
                "dependency_marker": "later arguments depend on this observation",
            },
            "expected_final_answer_change": "no",
        },
        "metadata": {},
    }


def test_long_horizon_taxonomy_uses_tool_output_patch() -> None:
    policy = built_in_intervention_taxonomy()["long_horizon_dependency"]
    assert "tool_output_patch" in policy["allowed_changed_fields"]
    assert "observation_conflict" in policy["allowed_change_categories"]
    # The user instruction must be expected-unchanged for this intervention.
    assert "user_instruction" in policy["expected_unchanged_fields"]
    assert policy["answer_preservation"] == "answer_preserving"


def test_long_horizon_dependency_pair_is_isolated(tmp_path: Path) -> None:
    path = tmp_path / "instances.jsonl"
    _write_jsonl(path, [_clean(), _long_horizon()])
    report = audit_intervention_isolation_instances(path, repo_root=tmp_path)

    by_type = report["summary"]["per_intervention_type_score"]
    assert "long_horizon_dependency" in by_type
    # Changing only tool_output_patch is the intended factor -> high isolation, no
    # multi-factor blocker.
    assert by_type["long_horizon_dependency"]["score"] >= 80
    assert report["summary"]["multi_factor_count"] == 0
    assert report["summary"]["blockers"] == 0

    record = next(r for r in report["pairs"] if r["intervention_type"] == "long_horizon_dependency")
    assert record["isolation_status"] in {"isolated", "likely_isolated"}
    assert record.get("unexpected_changed_fields", []) == []
