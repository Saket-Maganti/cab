"""Fixture-only tests: the validator resolves the code-level tool registry.

The benchmark ships tool schemas as Python classes (the simulated tool
environment), not per-dataset schema files. These tests pin that tasks
referencing registry tools are not falsely reported as ``tool_not_found`` and
that genuinely missing tools are still flagged.
"""

from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.tool_schema_validation import (
    load_code_registry_tool_specs,
    validate_tool_schemas_for_dataset,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _dataset(tmp_path: Path, available_tools: list[str]) -> Path:
    dataset = tmp_path / "data/processed/tiny"
    task = {
        "task_id": "task_1",
        "goal": {"user_instruction": "Do it.", "expected_final_answer": "ok"},
        "available_tools": available_tools,
        "gold_tool_sequence": available_tools,
    }
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(
        dataset / "instances.jsonl",
        [{"instance_id": "task_1.clean", "condition": "clean", "base_task": task, "available_tools": available_tools}],
    )
    return dataset


def test_code_registry_specs_loaded() -> None:
    names = {spec["name"] for spec in load_code_registry_tool_specs()}
    # Core simulated tools must be discoverable for static validation.
    for required in ("read_file", "search_database", "verify_fact", "web_open_page"):
        assert required in names
    # Every registry spec carries input + output schemas authored in code.
    for spec in load_code_registry_tool_specs():
        assert spec["input_schema"]
        assert spec["output_schema"]
        assert spec["source"] == "code_registry"


def test_registry_tools_not_flagged_tool_not_found(tmp_path: Path) -> None:
    report = validate_tool_schemas_for_dataset(
        _dataset(tmp_path, ["read_file", "search_database", "verify_fact"]),
        repo_root=tmp_path,
    )
    assert report["blockers"] == 0
    assert not any(issue["issue_type"] == "tool_not_found" for issue in report["issues"])
    assert report["unresolved_referenced_tools"] == []
    assert report["tool_schema_sources"]["code_registry"] is True


def test_registry_resolution_suppresses_environment_warning(tmp_path: Path) -> None:
    report = validate_tool_schemas_for_dataset(
        _dataset(tmp_path, ["read_file", "calculate_price"]),
        repo_root=tmp_path,
    )
    # Tools resolve against the repo-default code registry, so there is no
    # "missing tool environment" warning noise.
    assert not any(
        issue["issue_type"] == "missing_tool_environment_reference" for issue in report["issues"]
    )


def test_genuinely_missing_tool_still_flagged(tmp_path: Path) -> None:
    report = validate_tool_schemas_for_dataset(
        _dataset(tmp_path, ["read_file", "not_a_real_tool"]),
        repo_root=tmp_path,
    )
    found = [issue for issue in report["issues"] if issue["issue_type"] == "tool_not_found"]
    assert len(found) == 1
    assert found[0]["affected_tool"] == "not_a_real_tool"
    assert found[0]["severity"] == "blocker"
    assert report["unresolved_referenced_tools"] == ["not_a_real_tool"]


def test_conditional_requirement_tool_not_warned(tmp_path: Path) -> None:
    # web_follow_link has a "href OR link_text" rule enforced in code, so it has
    # no flat `required` list; the validator must not flag it.
    report = validate_tool_schemas_for_dataset(
        _dataset(tmp_path, ["web_follow_link"]),
        repo_root=tmp_path,
    )
    assert not any(
        issue["issue_type"] == "tool_required_fields_missing" for issue in report["issues"]
    )
