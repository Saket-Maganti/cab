from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from causal_agent_bench.safety.benchmark_quality import audit_benchmark_dataset

REPO = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _task(task_id: str = "task_1", *, expected: bool = True, tools: bool = True) -> dict:
    goal = {
        "user_instruction": "Find the answer.",
        "success_criteria": ["Answer correctly."],
    }
    if expected:
        goal["expected_final_answer"] = "answer"
    return {
        "task_id": task_id,
        "domain": "policy",
        "difficulty": "easy",
        "goal": goal,
        "available_tools": ["lookup"] if tools else [],
        "tool_specs": [
            {
                "name": "lookup",
                "description": "Lookup facts.",
                "input_schema": {},
                "output_schema": {},
            }
        ]
        if tools
        else [],
        "metadata": {"scenario": "tiny fixture"},
    }


def _clean(task: dict, instance_id: str = "task_1.clean") -> dict:
    return {
        "instance_id": instance_id,
        "base_task": task,
        "condition": "clean",
        "intervention": None,
        "available_tools": list(task.get("available_tools", [])),
        "initial_memory": {},
        "environment_seed": 1,
        "metadata": {},
    }


def _intervention(task: dict, instance_id: str = "task_1.tool_failure") -> dict:
    return {
        "instance_id": instance_id,
        "base_task": task,
        "condition": "intervention",
        "intervention": {
            "intervention_id": instance_id,
            "base_task_id": task["task_id"],
            "family": "tool_failure",
            "changed_factor": "tool reliability",
            "tool_output_patch": {"target_tool": "lookup", "error": "simulated"},
            "expected_final_answer_change": "no",
        },
        "available_tools": list(task.get("available_tools", [])),
        "initial_memory": {},
        "environment_seed": 2,
        "metadata": {},
    }


def _dataset(tmp_path: Path, *, with_splits: bool = False) -> Path:
    dataset = tmp_path / "data"
    task = _task()
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(dataset / "interventions.jsonl", [_intervention(task)["intervention"]])
    _write_jsonl(dataset / "instances.jsonl", [_clean(task), _intervention(task)])
    if with_splits:
        (dataset / "splits.json").write_text(
            json.dumps(
                {
                    "split_policy": "fixture",
                    "splits": {
                        "dev": {"base_task_ids": [], "instance_ids": []},
                        "heldout": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean", "task_1.tool_failure"]},
                    },
                }
            ),
            encoding="utf-8",
        )
    return dataset


def _issue_ids(report: dict) -> set[str]:
    return {issue["id"] for issue in report["issues"]}


def test_duplicate_ids_detected(tmp_path: Path) -> None:
    dataset = tmp_path / "data"
    task = _task()
    _write_jsonl(dataset / "base_tasks.jsonl", [task, task])
    _write_jsonl(dataset / "instances.jsonl", [_clean(task), _clean(task)])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert "duplicate_task_id" in _issue_ids(report)
    assert "duplicate_instance_id" in _issue_ids(report)


def test_missing_clean_and_intervention_pairs_detected(tmp_path: Path) -> None:
    dataset = tmp_path / "data"
    task = _task()
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(dataset / "instances.jsonl", [_intervention(task)])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert "missing_clean_pair" in _issue_ids(report)

    _write_jsonl(dataset / "instances.jsonl", [_clean(task)])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert "missing_intervention_pair" in _issue_ids(report)


def test_missing_expected_output_detected(tmp_path: Path) -> None:
    dataset = tmp_path / "data"
    task = _task(expected=False)
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(dataset / "instances.jsonl", [_clean(task), _intervention(task)])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert "missing_expected_output" in _issue_ids(report)


def test_missing_tool_specs_detected(tmp_path: Path) -> None:
    dataset = tmp_path / "data"
    task = _task(tools=False)
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(dataset / "instances.jsonl", [_clean(task), _intervention(task)])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert "missing_tool_specs" in _issue_ids(report)


def test_registry_tools_do_not_trigger_missing_tool_specs(tmp_path: Path) -> None:
    # A task that names code-registry tools has a resolvable schema even without
    # an inline tool_specs block, so it must not be flagged missing_tool_specs.
    dataset = tmp_path / "data"
    task = _task()
    task["available_tools"] = ["read_file", "search_database"]
    clean = _clean(task)
    clean["available_tools"] = ["read_file", "search_database"]
    intervention = _intervention(task)
    intervention["available_tools"] = ["read_file", "search_database"]
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(dataset / "instances.jsonl", [clean, intervention])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert "missing_tool_specs" not in _issue_ids(report)


def test_heldout_split_missing_blocks_main_not_provider_pilot(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert "missing_split_metadata" in _issue_ids(report)
    assert report["verdicts"]["ready_for_provider_pilot"] is True
    assert report["verdicts"]["ready_for_main_claims"] is False


def test_valid_tiny_fixture_can_pass_provider_pilot_quality_gate(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path, with_splits=True)
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert report["verdicts"]["ready_for_provider_pilot"] is True
    assert report["verdicts"]["ready_for_main_claims"] is True
    assert report["scores"]["provider_pilot_readiness_score"] >= 80
    assert report["scores"]["overall_quality_score"] >= 80


def test_benchmark_quality_cli_writes_report_without_runner_calls(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    out = tmp_path / "reports"
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "benchmark-quality",
            "--repo-root",
            str(tmp_path),
            "--benchmark-dir",
            str(dataset),
            "--output-dir",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    payload = json.loads(result.stdout)
    assert Path(payload["report"]["json"]).exists()
    assert Path(payload["report"]["markdown"]).exists()


def test_score_output_has_all_fields(tmp_path: Path) -> None:
    report = audit_benchmark_dataset(_dataset(tmp_path, with_splits=True), repo_root=tmp_path)
    scores = report["scores"]
    for key in (
        "overall_quality_score",
        "provider_pilot_readiness_score",
        "main_benchmark_readiness_score",
        "release_readiness_score",
        "breakdown",
    ):
        assert key in scores
    assert {row["category"] for row in scores["breakdown"]} >= {"pair_completeness", "heldout_split_status"}


def test_duplicate_ids_reduce_and_block_score(tmp_path: Path) -> None:
    dataset = tmp_path / "data"
    task = _task()
    _write_jsonl(dataset / "base_tasks.jsonl", [task, task])
    _write_jsonl(dataset / "instances.jsonl", [_clean(task), _clean(task)])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert report["scores"]["provider_pilot_readiness_score"] <= 49
    assert any(row["category"] == "duplicate_ids" and row["score"] == 0 for row in report["scores"]["breakdown"])


def test_missing_heldout_blocks_main_readiness_score(tmp_path: Path) -> None:
    report = audit_benchmark_dataset(_dataset(tmp_path), repo_root=tmp_path)
    assert report["scores"]["main_benchmark_readiness_score"] <= 49


def test_missing_expected_output_reduces_provider_score(tmp_path: Path) -> None:
    dataset = tmp_path / "data"
    task = _task(expected=False)
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(dataset / "instances.jsonl", [_clean(task), _intervention(task)])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    assert report["scores"]["provider_pilot_readiness_score"] <= 45
    assert report["recommended_fixes"]


def test_high_risk_intervention_reduces_score(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path, with_splits=True)
    task = _task()
    high_risk = _intervention(task, "task_1.memory_corruption")["intervention"]
    high_risk["family"] = "memory_corruption"
    high_risk["severity"] = "high"
    _write_jsonl(dataset / "interventions.jsonl", [high_risk])
    report = audit_benchmark_dataset(dataset, repo_root=tmp_path)
    high_risk_row = next(row for row in report["scores"]["breakdown"] if row["category"] == "high_risk_interventions")
    assert high_risk_row["score"] < 100
