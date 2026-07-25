from pathlib import Path

from causal_agent_bench.analysis.error_analysis import (
    generate_failure_gallery,
    mine_error_taxonomy,
    mine_filtered_cases,
)
from causal_agent_bench.analysis.load_results import (
    RunResults,
    contexts_to_dataframe,
    scores_to_dataframe,
    trajectories_to_dataframe,
)
from causal_agent_bench.schemas import (
    BaseTask,
    BenchmarkInstance,
    InterventionSpec,
    ScoreRecord,
    TaskGoal,
    Trajectory,
)


def _synthetic_error_run(tmp_path: Path) -> RunResults:
    base_task = BaseTask(
        task_id="item_task",
        domain="shopping",
        difficulty="medium",
        goal=TaskGoal(
            user_instruction="Look up the current price and inventory for SKU-12, then answer with the price.",
            success_criteria=["Answer includes the current price.", "Answer is supported by tool observations."],
            required_information=["current price", "inventory"],
            forbidden_assumptions=["Do not use stale memory."],
            expected_final_answer={"sku": "SKU-12", "price": "$12"},
        ),
        available_tools=["lookup_price", "verify_inventory", "weather_tool"],
        required_tools=["lookup_price", "verify_inventory"],
        gold_tool_sequence=["lookup_price", "verify_inventory"],
        hidden_ground_truth={"price": "$12", "inventory": "in_stock"},
        max_steps=4,
    )
    intervention = InterventionSpec(
        intervention_id="item_task.conflict",
        base_task_id="item_task",
        family="observation_conflict",
        description="The price observation conflicts with stale memory.",
        changed_factor="observation_consistency",
        expected_behavior="Notice the conflict and verify the current observation before answering.",
        expected_robust_behavior="Prefer verified current tool output over stale memory and report uncertainty if unresolved.",
        severity="medium",
        scoring_notes="Synthetic test intervention for failure-gallery mining.",
    )
    clean_instance = BenchmarkInstance(
        instance_id="item_task.clean",
        base_task=base_task,
        condition="clean",
        available_tools=base_task.available_tools,
        environment_seed=11,
    )
    intervention_instance = BenchmarkInstance(
        instance_id="item_task.conflict",
        base_task=base_task,
        condition="intervention",
        intervention=intervention,
        available_tools=base_task.available_tools,
        environment_seed=12,
    )

    bad_steps = [
        {
            "index": 0,
            "action": {
                "thought": "Check a quick external hint.",
                "tool_call": {"tool_name": "weather_tool", "arguments": {"city": "Boston"}},
            },
            "observation": {"tool_name": "weather_tool", "output": {"temp": 72}, "error": None},
        },
        {
            "index": 1,
            "parser_status": "invalid_argument_schema",
            "action": {
                "thought": "Try the price lookup.",
                "tool_call": {"tool_name": "lookup_price", "arguments": {"sku": None}},
            },
            "observation": {
                "tool_name": "lookup_price",
                "output": None,
                "error": "invalid_arguments",
            },
        },
        {
            "index": 2,
            "action": {
                "thought": "Try the same lookup again.",
                "tool_call": {"tool_name": "lookup_price", "arguments": {"sku": None}},
            },
            "observation": {
                "tool_name": "lookup_price",
                "output": None,
                "error": "invalid_arguments",
            },
        },
        {
            "index": 3,
            "action": {
                "thought": "Stop confidently.",
                "final_answer": "According to the tool result, SKU-12 costs $12.",
                "stop": True,
            },
            "observation": None,
        },
    ]
    bad_trajectory = Trajectory(
        run_id="synthetic-error-run",
        instance_id="item_task.conflict",
        agent_name="bad_agent",
        model_name="model-b",
        provider_model_metadata={"provider": "synthetic", "model": "model-b", "prompt_hash": "prompt-b"},
        token_cost_metadata={"estimated_cost_usd": 3.5, "token_usage": {"total_tokens": 1000}},
        metadata={"seed": 101, "estimated_cost_usd": 3.5},
        steps=bad_steps,
        final_answer="According to the tool result, SKU-12 costs $12.",
        terminated_reason="final_answer",
    )
    good_trajectory = Trajectory(
        run_id="synthetic-error-run",
        instance_id="item_task.conflict",
        agent_name="good_agent",
        model_name="model-a",
        provider_model_metadata={"provider": "synthetic", "model": "model-a", "prompt_hash": "prompt-a"},
        metadata={"seed": 102},
        steps=[
            {
                "index": 0,
                "action": {
                    "tool_call": {"tool_name": "lookup_price", "arguments": {"sku": "SKU-12"}},
                },
                "observation": {"tool_name": "lookup_price", "output": {"price": "$12"}, "error": None},
            },
            {
                "index": 1,
                "action": {
                    "tool_call": {"tool_name": "verify_inventory", "arguments": {"sku": "SKU-12"}},
                },
                "observation": {
                    "tool_name": "verify_inventory",
                    "output": {"inventory": "in_stock"},
                    "error": None,
                },
            },
            {
                "index": 2,
                "action": {"final_answer": "SKU-12 costs $12 and is in stock.", "stop": True},
            },
        ],
        final_answer="SKU-12 costs $12 and is in stock.",
        terminated_reason="final_answer",
    )
    fail_trajectory = Trajectory(
        run_id="synthetic-error-run",
        instance_id="item_task.conflict",
        agent_name="fragile_agent",
        model_name="model-c",
        provider_model_metadata={"provider": "synthetic", "model": "model-c", "prompt_hash": "prompt-c"},
        token_cost_metadata={"estimated_cost_usd": 8.0},
        metadata={"seed": 103, "estimated_cost_usd": 8.0},
        steps=bad_steps,
        final_answer="The current price is definitely $99.",
        terminated_reason="max_steps",
    )
    clean_trajectory = Trajectory(
        run_id="synthetic-error-run",
        instance_id="item_task.clean",
        agent_name="fragile_agent",
        model_name="model-c",
        provider_model_metadata={"provider": "synthetic", "model": "model-c", "prompt_hash": "prompt-c"},
        metadata={"seed": 104},
        steps=good_trajectory.steps,
        final_answer="SKU-12 costs $12 and is in stock.",
        terminated_reason="final_answer",
    )

    scores = [
        ScoreRecord(
            run_id="synthetic-error-run",
            instance_id="item_task.conflict",
            agent_name="bad_agent",
            metrics={
                "final_success_binary": 1,
                "final_success_partial": 1.0,
                "trajectory_success_binary": 0,
                "trajectory_faithfulness": 0.0,
                "trajectory_efficiency": 0.2,
                "required_tool_recall": 0.5,
                "tool_precision": 0.5,
                "invalid_tool_call_count": 0,
                "argument_error_count": 2,
                "argument_validity_rate": 0.0,
                "unnecessary_tool_call_rate": 0.333333,
                "missing_required_tool_count": 1,
                "tool_error_recovery_binary": False,
                "repeated_failed_call_count": 1,
                "premature_stop_binary": True,
                "max_step_failure_binary": False,
                "contradiction_detected_binary": False,
                "contradiction_resolved_binary": False,
                "memory_used_binary": False,
                "memory_verified_binary": False,
                "memory_blind_trust_failure_binary": False,
            },
            diagnostics={
                "condition": "intervention",
                "intervention_family": "observation_conflict",
                "base_task_id": "item_task",
            },
            metadata={"model_name": "model-b", "scorer": "synthetic_scorer_v1"},
        ),
        ScoreRecord(
            run_id="synthetic-error-run",
            instance_id="item_task.conflict",
            agent_name="good_agent",
            metrics={
                "final_success_binary": 1,
                "trajectory_success_binary": 1,
                "trajectory_faithfulness": 1.0,
                "trajectory_efficiency": 1.0,
            },
            diagnostics={
                "condition": "intervention",
                "intervention_family": "observation_conflict",
                "base_task_id": "item_task",
            },
            metadata={"model_name": "model-a", "scorer": "synthetic_scorer_v1"},
        ),
        ScoreRecord(
            run_id="synthetic-error-run",
            instance_id="item_task.conflict",
            agent_name="fragile_agent",
            metrics={
                "final_success_binary": 0,
                "trajectory_success_binary": 0,
                "trajectory_faithfulness": 0.0,
                "trajectory_efficiency": 0.2,
                "required_tool_recall": 0.5,
                "tool_precision": 0.5,
                "argument_error_count": 2,
                "missing_required_tool_count": 1,
                "tool_error_recovery_binary": False,
                "repeated_failed_call_count": 1,
                "premature_stop_binary": True,
                "max_step_failure_binary": True,
                "unnecessary_tool_call_rate": 0.333333,
                "contradiction_detected_binary": False,
                "contradiction_resolved_binary": False,
            },
            diagnostics={
                "condition": "intervention",
                "intervention_family": "observation_conflict",
                "base_task_id": "item_task",
            },
            metadata={"model_name": "model-c", "scorer": "synthetic_scorer_v1"},
        ),
        ScoreRecord(
            run_id="synthetic-error-run",
            instance_id="item_task.clean",
            agent_name="fragile_agent",
            metrics={
                "final_success_binary": 1,
                "trajectory_success_binary": 1,
                "trajectory_faithfulness": 1.0,
                "trajectory_efficiency": 1.0,
            },
            diagnostics={"condition": "clean", "intervention_family": None, "base_task_id": "item_task"},
            metadata={"model_name": "model-c", "scorer": "synthetic_scorer_v1"},
        ),
    ]
    trajectories = [bad_trajectory, good_trajectory, fail_trajectory, clean_trajectory]
    instances = [clean_instance, intervention_instance]
    return RunResults(
        run_dir=tmp_path / "synthetic-error-run",
        run_metadata={
            "run_id": "synthetic-error-run",
            "config_hash": "cfg123",
            "config_path": "configs/synthetic.yaml",
            "dataset_version": "synthetic-v0",
            "seed": 99,
            "git_commit": "abc123",
        },
        aggregate={},
        scores=scores,
        instances=instances,
        legacy_tasks=[],
        trajectories=trajectories,
        scores_df=scores_to_dataframe(scores),
        instances_df=contexts_to_dataframe(instances, []),
        trajectories_df=trajectories_to_dataframe(trajectories),
    )


def test_error_taxonomy_mines_synthetic_trajectory_signals(tmp_path):
    data = _synthetic_error_run(tmp_path)

    cases = mine_error_taxonomy(data, max_cases=10)

    for category in [
        "wrong_tool_selected",
        "required_tool_omitted",
        "tool_argument_malformed",
        "failure_to_recover_from_tool_error",
        "repeated_failed_calls",
        "premature_stopping",
        "overlong_inefficient_trajectory",
        "hallucinated_tool_result",
        "final_answer_unsupported_by_trajectory",
        "correct_final_answer_via_invalid_trajectory",
        "uncertainty_failure",
        "contradiction_missed",
    ]:
        assert cases[category], category

    case = cases["correct_final_answer_via_invalid_trajectory"][0]
    assert case["evidence"]["config_hash"] == "cfg123"
    assert case["evidence"]["prompt_hash"] == "prompt-b"
    assert case["raw_trajectory_excerpt"]
    assert case["expected_behavior"]["required_tools"] == ["lookup_price", "verify_inventory"]


def test_failure_filters_cover_requested_case_mining_views(tmp_path):
    data = _synthetic_error_run(tmp_path)

    filtered = mine_filtered_cases(data, max_cases=10)

    assert filtered["final_success_trajectory_failure"]
    assert filtered["clean_succeeds_intervention_fails"]
    assert filtered["model_a_succeeds_model_b_fails"]
    assert filtered["high_cost_low_quality"]
    contrast = filtered["model_a_succeeds_model_b_fails"][0]["signal"]
    assert "model-a" in contrast["successful_models"]
    assert "model-c" in contrast["failed_models"]


def test_failure_gallery_writes_taxonomy_filters_and_qualitative_examples(tmp_path):
    data = _synthetic_error_run(tmp_path)
    out = tmp_path / "gallery"

    paths = generate_failure_gallery(data, out, max_cases=3, include_legacy_aliases=True)
    names = {path.name for path in paths}

    assert "taxonomy.json" in names
    assert "premature_stopping.md" in names
    assert "premature_success.md" in names
    assert "qualitative_examples.md" in names
    assert (out / "filters" / "model_a_succeeds_model_b_fails.md").exists()
    text = (out / "tool_argument_malformed.md").read_text(encoding="utf-8")
    assert "Expected Behavior" in text
    assert "Actual Behavior" in text
    assert "Raw Trajectory Excerpt" in text
    assert "cfg123" in text
