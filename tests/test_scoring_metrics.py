
from causal_agent_bench.metrics.causal_robustness import acrs
from causal_agent_bench.metrics.final_success import score_final_success
from causal_agent_bench.metrics.recovery import score_recovery
from causal_agent_bench.metrics.statistics import ranking_instability
from causal_agent_bench.metrics.tool_use import score_tool_use
from causal_agent_bench.metrics.trajectory import score_contradiction, score_memory
from causal_agent_bench.metrics.v2 import aggregate_metrics_v2
from causal_agent_bench.schemas import (
    BaseTask,
    BenchmarkInstance,
    InterventionSpec,
    TaskGoal,
    Trajectory,
)
from causal_agent_bench.scoring import score_run
from causal_agent_bench.utils.io import read_json, write_jsonl


def _task() -> BaseTask:
    return BaseTask(
        task_id="unit_task",
        domain="travel",
        difficulty="easy",
        goal=TaskGoal(
            user_instruction="Pick option b and report total 10.",
            success_criteria=["Names option b", "Reports total 10"],
            required_information=["option", "total"],
            forbidden_assumptions=[],
            expected_final_answer={"option": "option_b", "total": 10},
        ),
        available_tools=["search_database", "calculate_price", "verify_fact"],
        hidden_ground_truth={"option": "option_b", "total": 10},
        gold_tool_sequence=["search_database", "calculate_price"],
        max_steps=5,
        tags=[],
        metadata={},
    )


def _instance(condition="clean", intervention=None) -> BenchmarkInstance:
    return BenchmarkInstance(
        instance_id="unit_task.clean" if condition == "clean" else f"unit_task.{intervention.family}",
        base_task=_task(),
        condition=condition,
        intervention=intervention,
        available_tools=_task().available_tools,
        initial_memory={},
        environment_seed=1,
        metadata={},
    )


def _trajectory(agent="agent_a", answer="option_b total 10", steps=None, reason="final_answer") -> Trajectory:
    return Trajectory(
        run_id="unit",
        instance_id="unit_task.clean",
        agent_name=agent,
        model_name=None,
        steps=steps or [],
        final_answer=answer,
        terminated_reason=reason,
        metadata={},
    )


def _tool_step(index, tool, error=None, output=None, thought=None, corrupted=False):
    return {
        "index": index,
        "action": {
            "thought": thought,
            "tool_call": {"tool_name": tool, "arguments": {"x": 1}, "timestamp_step": None, "call_id": None},
            "final_answer": None,
            "stop": False,
            "metadata": {},
        },
        "observation": {
            "tool_name": tool,
            "call_id": f"c{index}",
            "output": output or {"text": "option_b total 10"},
            "error": error,
            "is_corrupted": corrupted,
            "metadata": {},
        },
        "state": {},
    }


def test_final_success_scorer():
    scores = score_final_success(_instance(), _trajectory())
    assert scores["final_success_binary"] == 1
    assert scores["final_success_partial"] == 1.0


def test_tool_precision_recall():
    traj = _trajectory(
        steps=[
            _tool_step(0, "search_database"),
            _tool_step(1, "verify_fact"),
        ]
    )
    scores = score_tool_use(_instance(), traj)
    assert scores["required_tool_recall"] == 0.5
    assert scores["tool_precision"] == 0.5
    assert scores["missing_required_tool_count"] == 1


def test_acrs_and_zero_clean_success():
    assert acrs(0.5, 1.0) == 0.5
    assert acrs(0.5, 0.0) is None
    assert acrs(0.5, None) is None


def test_ranking_instability():
    result = ranking_instability(
        {
            "a": {"clean_success_rate": 1.0, "acrs": 0.2},
            "b": {"clean_success_rate": 0.8, "acrs": 0.9},
        }
    )
    assert result["clean_success_ranking"]["a"] == 1
    assert result["acrs_ranking"]["b"] == 1
    assert result["rank_delta"]["a"] == 1


def test_recovery_detection():
    traj = _trajectory(
        steps=[
            _tool_step(0, "calculate_price", error="simulated_tool_failure"),
            _tool_step(1, "verify_fact"),
        ]
    )
    scores = score_recovery(traj)
    assert scores["tool_error_recovery_binary"] is True
    assert scores["steps_to_recovery"] == 1


def test_contradiction_detection():
    intervention = InterventionSpec(
        intervention_id="unit_task.observation_conflict",
        base_task_id="unit_task",
        family="observation_conflict",
        description="conflict",
        changed_factor="observation consistency",
        expected_behavior="resolve conflict",
        severity="high",
        tool_availability_patch={},
        memory_patch={},
        tool_output_patch={"target_tool": "search_database"},
        instruction_patch=None,
        metadata={},
    )
    traj = _trajectory(
        steps=[
            _tool_step(
                0,
                "search_database",
                output={"conflicting_observation": {"source_a": "yes", "source_b": "no"}},
                thought="I see a conflict and will verify because sources disagree.",
            )
        ]
    )
    scores = score_contradiction(_instance("intervention", intervention), traj)
    assert scores["contradiction_detected_binary"] is True
    assert scores["contradiction_resolved_binary"] is True


def test_memory_blind_trust_detection():
    intervention = InterventionSpec(
        intervention_id="unit_task.memory_corruption",
        base_task_id="unit_task",
        family="memory_corruption",
        description="memory",
        changed_factor="memory correctness",
        expected_behavior="verify memory",
        severity="high",
        tool_availability_patch={},
        memory_patch={"stale": True},
        tool_output_patch={},
        instruction_patch=None,
        metadata={},
    )
    traj = _trajectory(answer="wrong old memory answer", steps=[])
    scores = score_memory(_instance("intervention", intervention), traj)
    assert scores["memory_used_binary"] is True
    assert scores["memory_verified_binary"] is False
    assert scores["memory_blind_trust_failure_binary"] is True


def test_aggregate_score_generation(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    clean = _instance()
    intervention = InterventionSpec(
        intervention_id="unit_task.tool_failure",
        base_task_id="unit_task",
        family="tool_failure",
        description="fail",
        changed_factor="tool reliability",
        expected_behavior="recover",
        severity="medium",
        tool_availability_patch={},
        memory_patch={},
        tool_output_patch={"target_tool": "calculate_price", "error": "simulated"},
        instruction_patch=None,
        metadata={},
    )
    intervened = _instance("intervention", intervention)
    write_jsonl(run_dir / "instances.jsonl", [clean, intervened])
    write_jsonl(
        run_dir / "trajectories.jsonl",
        [
            _trajectory(agent="agent_a", steps=[_tool_step(0, "search_database"), _tool_step(1, "calculate_price")]),
            _trajectory(
                agent="agent_a",
                steps=[_tool_step(0, "search_database"), _tool_step(1, "calculate_price")],
            ).model_copy(update={"instance_id": intervened.instance_id}),
        ],
    )
    score_run(run_dir)
    assert (run_dir / "scores.jsonl").exists()
    assert (run_dir / "aggregate_scores.json").exists()
    assert (run_dir / "aggregate_scores.csv").exists()
    assert (run_dir / "score_report.md").exists()
    aggregate = read_json(run_dir / "aggregate_scores.json")
    assert aggregate["n_score_records"] == 2
    assert aggregate["by_agent"]["agent_a"]["clean_success_rate"] == 1.0
    assert (run_dir / "metrics_v2.json").exists()
    assert (run_dir / "metrics_v2.csv").exists()
    assert (run_dir / "metrics_v2.md").exists()
    assert (run_dir / "metrics_v2.tex").exists()


def test_metrics_v2_toy_values_and_undefined_acrs():
    records = [
        _score_record("agent_a", "clean", "clean1", final=1, recall=1, precision=1, invalid=0),
        _score_record("agent_a", "clean", "clean2", final=0, recall=0.5, precision=0.5, invalid=1),
        _score_record("agent_a", "intervention", "int1", family="tool_failure", final=1, recovery=True, abstain=True),
        _score_record("agent_a", "intervention", "int2", family="memory_corruption", final=0, memory_verified=False, blind=True, premature=True),
        _score_record("agent_b", "clean", "clean1", final=0),
        _score_record("agent_b", "intervention", "int1", final=1),
    ]

    summary = aggregate_metrics_v2(records)
    agent_a = summary["by_agent"]["agent_a"]["metrics"]
    agent_b = summary["by_agent"]["agent_b"]["metrics"]

    assert agent_a["clean_success"] == 0.5
    assert agent_a["intervention_success"] == 0.5
    assert agent_a["acrs"] == 1.0
    assert agent_a["absolute_degradation"] == 0.0
    assert agent_a["relative_degradation"] == 0.0
    assert agent_a["tool_recall"] == 0.75
    assert agent_a["invalid_call_rate"] == 0.25
    assert agent_a["recovery_rate_after_tool_failure"] == 1.0
    assert agent_a["blind_corrupted_memory_trust_rate"] == 1.0
    assert agent_a["premature_stopping_rate"] == 1.0
    assert agent_a["correct_abstention_uncertainty_rate"] == 1.0
    assert summary["by_agent"]["agent_a"]["families"]["tool_failure"]["acrs_family"] == 2.0
    assert summary["by_agent"]["agent_a"]["confidence_intervals"]["clean_success"]["low"] is not None
    assert agent_b["clean_success"] == 0.0
    assert agent_b["acrs"] is None


def _score_record(
    agent,
    condition,
    instance_id,
    *,
    family=None,
    final=0,
    recall=None,
    precision=None,
    invalid=0,
    recovery=None,
    abstain=None,
    memory_verified=None,
    blind=None,
    premature=None,
):
    from causal_agent_bench.schemas import ScoreRecord

    return ScoreRecord(
        run_id="toy",
        instance_id=instance_id,
        agent_name=agent,
        metrics={
            "final_success_binary": final,
            "required_tool_recall": recall,
            "tool_precision": precision,
            "invalid_tool_call_count": invalid,
            "tool_error_recovery_binary": recovery,
            "correct_abstention_uncertainty_binary": abstain,
            "contradiction_detected_binary": None,
            "contradiction_resolved_binary": None,
            "memory_verified_binary": memory_verified,
            "memory_blind_trust_failure_binary": blind,
            "premature_stop_binary": premature,
            "trajectory_efficiency": 1.0,
        },
        diagnostics={"condition": condition, "intervention_family": family},
        metadata={},
    )
