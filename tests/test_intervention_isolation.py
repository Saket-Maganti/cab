from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.intervention_isolation import audit_intervention_isolation_instances


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _task() -> dict:
    return {
        "task_id": "task_1",
        "domain": "policy",
        "difficulty": "easy",
        "goal": {
            "user_instruction": "Check policy.",
            "success_criteria": ["Answer with the threshold."],
            "expected_final_answer": "500",
        },
        "available_tools": ["lookup"],
        "hidden_ground_truth": {"threshold": 500},
        "max_steps": 3,
    }


def _clean() -> dict:
    task = _task()
    return {
        "instance_id": "task_1.clean",
        "base_task": task,
        "condition": "clean",
        "available_tools": ["lookup"],
        "initial_memory": {},
        "environment_seed": 1,
        "metadata": {},
    }


def _intervention(
    *,
    family: str = "memory_corruption",
    tools: list[str] | None = None,
    memory: dict | None = None,
    task: dict | None = None,
) -> dict:
    base_task = task or _task()
    return {
        "instance_id": f"task_1.{family}",
        "base_task": base_task,
        "condition": "intervention",
        "available_tools": tools if tools is not None else ["lookup"],
        "initial_memory": memory if memory is not None else {"threshold": 1000},
        "environment_seed": 2,
        "intervention": {
            "intervention_id": f"task_1.{family}",
            "base_task_id": "task_1",
            "family": family,
            "changed_factor": "memory",
            "memory_patch": {"threshold": 1000} if family == "memory_corruption" else {},
            "tool_output_patch": {"target_tool": "lookup", "error": "simulated"} if family == "tool_failure" else {},
            "expected_final_answer_change": "no",
        },
        "metadata": {},
    }


def _audit(tmp_path: Path, rows: list[dict], taxonomy_path: Path | None = None) -> dict:
    path = tmp_path / "instances.jsonl"
    _write_jsonl(path, rows)
    return audit_intervention_isolation_instances(path, repo_root=tmp_path, taxonomy_path=taxonomy_path)


def _taxonomy(tmp_path: Path) -> Path:
    path = tmp_path / "taxonomy.yaml"
    path.write_text(
        "\n".join(
            [
                "version: test",
                "interventions:",
                "  - intervention_type: memory_corruption",
                "    description: test",
                "    intended_causal_factor: memory",
                "    allowed_changed_fields: [initial_memory, memory_patch, patch_details]",
                "    expected_unchanged_fields: [available_tools, expected_final_answer, user_instruction]",
                "    answer_preservation: answer_preserving",
                "    requires_human_review: true",
                "    severity_if_violated: blocker",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_isolated_single_field_intervention_passes(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention()])
    row = report["pairs"][0]
    assert row["isolation_status"] in {"isolated", "likely_isolated"}
    assert row["unexpected_changed_fields"] == []
    assert row["isolation_score"] >= 80
    assert report["summary"]["isolation_score"] >= 80


def test_taxonomy_loaded(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention()], taxonomy_path=_taxonomy(tmp_path))
    assert report["taxonomy"]["loaded"] is True
    assert report["taxonomy"]["source"] == "file"


def test_taxonomy_allowed_changed_fields_pass(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention()], taxonomy_path=_taxonomy(tmp_path))
    row = report["pairs"][0]
    assert row["unexpected_changed_fields"] == []
    assert row["isolation_status"] in {"isolated", "likely_isolated"}


def test_taxonomy_disallowed_field_changes_fail(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention(tools=["lookup", "extra"])], taxonomy_path=_taxonomy(tmp_path))
    row = report["pairs"][0]
    assert row["isolation_status"] == "multi_factor_change"
    assert "available_tools" in row["unexpected_changed_fields"]


def test_unrelated_field_change_detected(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention(tools=["lookup", "extra"])])
    row = report["pairs"][0]
    assert row["isolation_status"] == "multi_factor_change"
    assert "available_tools" in row["unexpected_changed_fields"]
    assert row["risk_score"] > 0


def test_multiple_field_changes_detected(tmp_path: Path) -> None:
    changed_task = _task()
    changed_task["goal"] = dict(changed_task["goal"], user_instruction="Different goal.")
    report = _audit(
        tmp_path,
        [_clean(), _intervention(family="tool_failure", tools=["lookup", "extra"], memory={"x": 1}, task=changed_task)],
    )
    row = report["pairs"][0]
    assert row["isolation_status"] == "multi_factor_change"
    assert row["severity"] in {"warning", "blocker"}
    assert report["top_riskiest_pairs"]


def test_missing_clean_pair_detected(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_intervention()])
    assert report["pairs"][0]["isolation_status"] == "missing_clean_pair"
    assert report["pairs"][0]["severity"] == "blocker"


def test_missing_intervention_pair_detected(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean()])
    assert report["pairs"][0]["isolation_status"] == "missing_intervention_pair"


def test_wrong_field_for_intervention_type_becomes_blocker_or_warning(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention(family="memory_corruption", tools=["lookup", "extra"], memory={})])
    row = report["pairs"][0]
    assert row["isolation_status"] in {"multi_factor_change", "needs_review"}
    assert row["severity"] in {"warning", "blocker"}


def test_unknown_intervention_type_becomes_needs_review(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention(family="novel_intervention", memory={})])
    row = report["pairs"][0]
    assert row["isolation_status"] == "needs_review"
    assert row["severity"] == "warning"


def test_answer_preserving_violation_detected(tmp_path: Path) -> None:
    changed_task = _task()
    changed_task["goal"] = dict(changed_task["goal"], expected_final_answer="600")
    report = _audit(tmp_path, [_clean(), _intervention(family="memory_corruption", task=changed_task)], taxonomy_path=_taxonomy(tmp_path))
    row = report["pairs"][0]
    assert row["isolation_status"] == "multi_factor_change"
    assert "expected_final_answer" in row["unexpected_changed_fields"]
    assert row["severity"] == "blocker"


def test_missing_taxonomy_fallback_works(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention()], taxonomy_path=tmp_path / "missing.yaml")
    assert report["taxonomy"]["loaded"] is False
    assert report["pairs"][0]["isolation_status"] in {"isolated", "likely_isolated"}


def test_per_intervention_type_score_and_risk_ranking_produced(tmp_path: Path) -> None:
    report = _audit(tmp_path, [_clean(), _intervention(), _intervention(family="tool_failure", memory={}, tools=["lookup", "extra"])])
    assert "memory_corruption" in report["summary"]["per_intervention_type_score"]
    assert report["top_riskiest_pairs"]
    assert report["recommended_manual_review"]


def test_metadata_only_change_not_blocker(tmp_path: Path) -> None:
    intervention = _intervention()
    intervention["metadata"] = {"review_notes": "static review only"}
    report = _audit(tmp_path, [_clean(), intervention])
    row = report["pairs"][0]
    assert "metadata_only" in row["benign_change_categories"]
    assert row["severity"] != "blocker"


def test_formatting_only_change_not_blocker(tmp_path: Path) -> None:
    changed_task = _task()
    changed_task["goal"] = dict(changed_task["goal"], user_instruction="Check   policy.")
    report = _audit(tmp_path, [_clean(), _intervention(task=changed_task)])
    row = report["pairs"][0]
    assert "formatting_only" in row["benign_change_categories"]
    assert row["severity"] != "blocker"


def test_semantic_multi_factor_change_still_blocker(tmp_path: Path) -> None:
    changed_task = _task()
    changed_task["goal"] = dict(changed_task["goal"], user_instruction="Check a different policy.")
    report = _audit(tmp_path, [_clean(), _intervention(family="tool_failure", tools=["lookup", "extra"], memory={}, task=changed_task)])
    row = report["pairs"][0]
    assert row["isolation_status"] == "multi_factor_change"
    assert row["severity"] == "blocker"
    assert "tool_schema" in row["semantic_change_categories"]
    assert "prompt_surface" in row["semantic_change_categories"]


def test_long_horizon_dependency_expected_fields_not_automatic_blocker(tmp_path: Path) -> None:
    changed_task = _task()
    changed_task["goal"] = dict(changed_task["goal"], user_instruction="Check policy after verifying the dependency chain.")
    changed_task["max_steps"] = 5
    report = _audit(tmp_path, [_clean(), _intervention(family="long_horizon_dependency", memory={}, task=changed_task)])
    row = report["pairs"][0]
    assert row["severity"] in {"informational", "warning"}
    assert row["severity"] != "blocker"
    assert "prompt_surface" in row["semantic_change_categories"]
