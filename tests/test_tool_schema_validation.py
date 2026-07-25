from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.tool_schema_validation import validate_tool_schemas_for_dataset


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _tool(name: str) -> dict:
    return {
        "name": name,
        "description": f"{name} tool",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        "output_schema": {"type": "object", "properties": {"answer": {"type": "string"}}},
    }


def _dataset(tmp_path: Path, tasks: list[dict], tools: list[dict] | None = None) -> Path:
    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(dataset / "base_tasks.jsonl", tasks)
    _write_jsonl(dataset / "instances.jsonl", [{"instance_id": f"{task['task_id']}.clean", "condition": "clean", "base_task": task, "available_tools": task.get("available_tools", [])} for task in tasks])
    if tools is not None:
        (dataset / "tools.json").write_text(json.dumps({"tools": tools}), encoding="utf-8")
    return dataset


def _task(tools: list[str] | None = None, calls: list[dict] | None = None) -> dict:
    row = {
        "task_id": "task_1",
        "goal": {"user_instruction": "Use lookup.", "expected_final_answer": "ok"},
        "available_tools": tools or ["lookup"],
    }
    if calls is not None:
        row["expected_tool_calls"] = calls
    return row


def test_missing_tool_reference_flagged(tmp_path: Path) -> None:
    report = validate_tool_schemas_for_dataset(_dataset(tmp_path, [_task(["missing"])], tools=[]), repo_root=tmp_path)
    assert any(issue["issue_type"] == "tool_not_found" and issue["severity"] == "blocker" for issue in report["issues"])


def test_duplicate_tool_name_flagged(tmp_path: Path) -> None:
    report = validate_tool_schemas_for_dataset(_dataset(tmp_path, [_task()], tools=[_tool("lookup"), _tool("lookup")]), repo_root=tmp_path)
    assert any(issue["issue_type"] == "duplicate_tool_name" for issue in report["issues"])


def test_argument_mismatch_flagged(tmp_path: Path) -> None:
    task = _task(calls=[{"tool": "lookup", "arguments": {"bad_arg": "x"}}])
    report = validate_tool_schemas_for_dataset(_dataset(tmp_path, [task], tools=[_tool("lookup")]), repo_root=tmp_path)
    assert any(issue["issue_type"] == "argument_mismatch" and issue["severity"] == "blocker" for issue in report["issues"])


def test_unused_tool_missing_output_schema_is_warning(tmp_path: Path) -> None:
    unused = {
        "name": "unused",
        "description": "unused tool",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    }
    report = validate_tool_schemas_for_dataset(_dataset(tmp_path, [_task()], tools=[_tool("lookup"), unused]), repo_root=tmp_path)
    assert any(
        issue["issue_type"] == "missing_output_schema"
        and issue["affected_tool"] == "unused"
        and issue["severity"] == "warning"
        for issue in report["issues"]
    )


def test_grouped_issues_by_tool(tmp_path: Path) -> None:
    task_a = _task(["missing"])
    task_b = {
        **_task(["missing"]),
        "task_id": "task_2",
    }
    report = validate_tool_schemas_for_dataset(_dataset(tmp_path, [task_a, task_b], tools=[]), repo_root=tmp_path)
    root = [row for row in report["root_causes"] if row["issue_type"] == "tool_not_found" and row["affected_tool"] == "missing"]
    assert root
    assert root[0]["affected_task_count"] == 2


def test_clean_intervention_tool_drift_flagged_when_not_tool_intervention(tmp_path: Path) -> None:
    dataset = tmp_path / "data/processed/tiny"
    task = _task(["lookup"])
    _write_jsonl(
        dataset / "instances.jsonl",
        [
            {"instance_id": "task_1.clean", "condition": "clean", "base_task": task, "available_tools": ["lookup"]},
            {
                "instance_id": "task_1.memory_corruption",
                "condition": "intervention",
                "base_task": {**task, "available_tools": ["other"]},
                "available_tools": ["other"],
                "intervention": {"base_task_id": "task_1", "family": "memory_corruption"},
            },
        ],
    )
    (dataset / "tools.json").write_text(json.dumps({"tools": [_tool("lookup"), _tool("other")]}), encoding="utf-8")
    report = validate_tool_schemas_for_dataset(dataset, repo_root=tmp_path)
    assert any(issue["issue_type"] == "clean_intervention_tool_drift" for issue in report["issues"])


def test_valid_fixture_passes(tmp_path: Path) -> None:
    task = _task(calls=[{"tool": "lookup", "arguments": {"query": "policy"}}])
    report = validate_tool_schemas_for_dataset(_dataset(tmp_path, [task], tools=[_tool("lookup")]), repo_root=tmp_path)
    assert report["passed"] is True
    assert report["issues"] == []
