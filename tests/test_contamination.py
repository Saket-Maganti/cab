import json
from pathlib import Path

import pytest

from causal_agent_bench.contamination.audit import (
    apply_canary_metadata,
    assign_canary_strings,
    contamination_report_markdown,
    make_canary_string,
    run_contamination_audit,
    template_fingerprint,
)
from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, InterventionSpec, TaskGoal


def _task(task_id: str, instruction: str, *, hidden: dict | None = None) -> BaseTask:
    return BaseTask(
        task_id=task_id,
        domain="travel_planning",
        difficulty="medium",
        goal=TaskGoal(
            user_instruction=instruction,
            success_criteria=["Answer is supported by tool output."],
            expected_final_answer={"value": task_id},
        ),
        available_tools=["search_database", "compare_options"],
        hidden_ground_truth=hidden or {"template_domain": "travel", "variant": 0},
        gold_tool_sequence=["search_database"],
        max_steps=4,
        metadata={"synthetic": True},
    )


def _split_policy(task_splits: dict[str, str]) -> dict:
    grouped: dict[str, list[str]] = {}
    for task_id, split_name in task_splits.items():
        grouped.setdefault(split_name, []).append(task_id)
    return {
        "benchmark_version": "test_v0",
        "policy_name": "release_disjoint_v1",
        "splits": {
            split_name: {"base_task_ids": task_ids}
            for split_name, task_ids in grouped.items()
        },
    }


def test_template_fingerprint_is_stable():
    task = _task("travel_planning_medium_000", "Find the refundable hotel option under budget.")
    assert template_fingerprint(task) == template_fingerprint(task)


def test_canary_assignment_targets_hidden_splits_only():
    tasks = [
        _task("public_task", "Public instruction for development."),
        _task("hidden_task", "Hidden instruction for held-out evaluation."),
    ]
    policy = _split_policy({"public_task": "pilot", "hidden_task": "test"})
    canaries = assign_canary_strings(tasks, policy, dataset_version="test_v0")
    assert "public_task" not in canaries
    assert canaries["hidden_task"].startswith("CAB-CANARY-test_v0-")


def test_apply_canary_metadata_writes_task_metadata():
    tasks = [_task("hidden_task", "Hidden instruction for held-out evaluation.")]
    policy = _split_policy({"hidden_task": "test"})
    updated = apply_canary_metadata(tasks, policy, dataset_version="test_v0")
    assert updated[0].metadata["contamination_canary"].startswith("CAB-CANARY-")


def test_near_duplicate_flags_public_hidden_pair(tmp_path: Path):
    benchmark_dir = tmp_path / "bundle"
    benchmark_dir.mkdir()
    public_task = _task(
        "public_task",
        "Find the refundable hotel option in Boston with the lowest total price and report the option id.",
    )
    hidden_task = _task(
        "hidden_task",
        "Find the refundable hotel option in Boston with the lowest total price and report the option id and tax.",
    )
    policy = _split_policy({"public_task": "pilot", "hidden_task": "test"})
    (benchmark_dir / "base_tasks.jsonl").write_text(
        "\n".join(task.model_dump_json() for task in [public_task, hidden_task]) + "\n",
        encoding="utf-8",
    )
    (benchmark_dir / "interventions.jsonl").write_text("", encoding="utf-8")
    instance = BenchmarkInstance(
        instance_id="public_task.clean",
        base_task=public_task,
        condition="clean",
        available_tools=public_task.available_tools,
        environment_seed=1,
    )
    (benchmark_dir / "instances.jsonl").write_text(instance.model_dump_json() + "\n", encoding="utf-8")
    (benchmark_dir / "splits.json").write_text(json.dumps(policy), encoding="utf-8")

    report = run_contamination_audit(benchmark_dir, near_duplicate_threshold=0.8)
    categories = {finding["category"] for finding in report["findings"]}
    assert "near_duplicate_instruction" in categories
    assert contamination_report_markdown(report).startswith("# Contamination")


def test_hidden_ground_truth_leak_detected(tmp_path: Path):
    secret = "SECRET_GROUND_TRUTH_VALUE_12345"
    task = _task("hidden_task", "Answer using verified tool output only.", hidden={"answer": secret})
    intervention = InterventionSpec(
        intervention_id="hidden_task.tool_failure",
        base_task_id="hidden_task",
        family="tool_failure",
        description="Internal intervention description that should not appear in prompts.",
        changed_factor="tool_reliability",
        expected_behavior="Recover from the tool failure using an alternate tool.",
        expected_robust_behavior="Verify with a second tool before answering.",
        severity="medium",
        scoring_notes="Internal scoring notes should remain private.",
        patch_details={"mode": "forced_failure", "target_tool": "search_database"},
    )
    instance = BenchmarkInstance(
        instance_id="hidden_task.tool_failure",
        base_task=task,
        condition="intervention",
        intervention=intervention,
        available_tools=task.available_tools,
        environment_seed=2,
        metadata={"hidden_probe": secret},
    )
    benchmark_dir = tmp_path / "leak_bundle"
    benchmark_dir.mkdir()
    (benchmark_dir / "base_tasks.jsonl").write_text(task.model_dump_json() + "\n", encoding="utf-8")
    (benchmark_dir / "interventions.jsonl").write_text(intervention.model_dump_json() + "\n", encoding="utf-8")
    (benchmark_dir / "instances.jsonl").write_text(instance.model_dump_json() + "\n", encoding="utf-8")
    policy = _split_policy({"hidden_task": "test"})
    (benchmark_dir / "splits.json").write_text(json.dumps(policy), encoding="utf-8")

    report = run_contamination_audit(benchmark_dir)
    categories = {finding["category"] for finding in report["findings"]}
    assert "intervention_expected_behavior_exposed" not in categories


def test_audit_runs_on_frozen_pilot_bundle():
    frozen = Path("data/frozen/pilot_v0.1")
    if not (frozen / "splits.json").exists():
        pytest.skip("frozen pilot bundle not available")
    report = run_contamination_audit(frozen)
    assert "fingerprinting" in report
    assert "canaries" in report
    assert report["summary"]["n_base_tasks"] > 0


def test_make_canary_string_is_deterministic():
    assert make_canary_string("pilot_v0.1", "task_a") == make_canary_string("pilot_v0.1", "task_a")
    assert make_canary_string("pilot_v0.1", "task_a") != make_canary_string("pilot_v0.1", "task_b")
