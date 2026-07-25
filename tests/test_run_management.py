"""Tests for run management, limits, and incomplete-run guards."""

from __future__ import annotations

import pytest

from causal_agent_bench.agents.mock_behavior_agent import MockBehaviorAgent
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment
from causal_agent_bench.runners.limits import RunLimiter, warn_if_huge_local_run
from causal_agent_bench.runners.mark_interrupted import mark_run_interrupted
from causal_agent_bench.runners.plan_run import plan_run
from causal_agent_bench.runners.run_completion import infer_completion_state
from causal_agent_bench.schemas import ToolSpec


def _smoke_config(tmp_path, **overrides):
    payload = {
        "seed": 1,
        "run_name": "run_mgmt_smoke",
        "benchmark_path": "data/processed/pilot_v0_1/pilot_20_instances.jsonl",
        "max_instances": 2,
        "agent_runs": [
            {
                "name": "mock_helpful",
                "agent": "mock_behavior_agent",
                "extra": {"mock_behavior": "helpful"},
            }
        ],
        "max_steps": 2,
        "auto_score": False,
        "output_dir": str(tmp_path),
        "limits": {"max_trajectories": 2, "stop_after_trajectories": 2},
    }
    payload.update(overrides)
    return ExperimentConfig.model_validate(payload)


def test_mock_behavior_modes():
    agent = MockBehaviorAgent(seed=0, mock_behavior="premature_stop")
    tool = ToolSpec(
        name="search_web",
        description="search",
        input_schema={"type": "object"},
        output_schema={"type": "object"},
    )
    action = agent.act([], [tool])
    assert action.final_answer is not None


def test_run_limiter_stops_after_n():
    limiter = RunLimiter(stop_after_trajectories=1)
    assert limiter.should_stop_before_trajectory(0) is None
    limiter.note_trajectory_completed()
    assert limiter.should_stop_before_trajectory(1) is not None


def test_mock_run_completes_fast(tmp_path):
    result = run_experiment(_smoke_config(tmp_path), checkpoint_every=1)
    run_dir = result["run_dir"]
    assert len(result["completed_keys"]) == 2
    state = infer_completion_state(run_dir)
    assert state["run_status"] == "complete"


def test_mark_interrupted_and_score_guard(tmp_path):
    result = run_experiment(_smoke_config(tmp_path, limits={"max_trajectories": 1, "stop_after_trajectories": 1}), checkpoint_every=1)
    run_dir = result["run_dir"]
    mark_run_interrupted(run_dir, reason="test interrupt")
    state = infer_completion_state(run_dir)
    assert state["run_status"] == "interrupted"
    from causal_agent_bench.scoring import score_run

    with pytest.raises(ValueError, match="refusing score"):
        score_run(run_dir)
    score_run(run_dir, allow_incomplete=True)


def test_plan_run_stub_micro():
    plan = plan_run("configs/pilot_stub_micro_3.yaml")
    assert plan["expected_trajectories"] == 3
    assert plan["allow_paid_calls"] is False


def test_resume_duplicate_prevention(tmp_path):
    first = run_experiment(_smoke_config(tmp_path), checkpoint_every=1)
    run_dir = first["run_dir"]
    second = run_experiment(_smoke_config(tmp_path), resume_dir=run_dir, checkpoint_every=1)
    assert second["trajectories"] == []
    assert len(second["completed_keys"]) == 2


def test_monitor_watch_stops_on_terminal_status(tmp_path, capsys):
    from causal_agent_bench.runners.monitor import monitor_run

    result = run_experiment(_smoke_config(tmp_path), checkpoint_every=1)
    run_dir = result["run_dir"]
    # A completed run is terminal: watch refreshes once and stops, ignoring the cap.
    monitor_run(run_dir, watch=True, interval_seconds=0, max_iterations=5)
    out = capsys.readouterr().out
    assert out.count("# Run status") == 1


def test_monitor_watch_respects_iteration_cap(monkeypatch, capsys):
    from causal_agent_bench.runners import monitor as monitor_mod

    monkeypatch.setattr(monitor_mod, "resolve_run_dir", lambda run_dir, latest=False: run_dir)
    monkeypatch.setattr(monitor_mod, "build_run_status", lambda path: {"run_status": "incomplete"})
    monkeypatch.setattr(monitor_mod, "format_run_status", lambda status: "# Run status\n")
    # Non-terminal status: watch loops until the iteration cap is reached.
    monitor_mod.monitor_run("ignored", watch=True, interval_seconds=0, max_iterations=3)
    out = capsys.readouterr().out
    assert out.count("# Run status") == 3


def test_monitor_no_watch_prints_once(tmp_path, capsys):
    from causal_agent_bench.runners.monitor import monitor_run

    result = run_experiment(_smoke_config(tmp_path), checkpoint_every=1)
    run_dir = result["run_dir"]
    monitor_run(run_dir, watch=False, max_iterations=5)
    out = capsys.readouterr().out
    assert out.count("# Run status") == 1


def test_huge_local_warning():
    config = ExperimentConfig.model_validate(
        {
            "seed": 1,
            "run_name": "big",
            "benchmark_path": "data/processed/pilot_v0_1/pilot_20_instances.jsonl",
            "agent_runs": [{"name": "local", "agent": "direct_tool_agent", "provider": "local_openai"}],
        }
    )
    warnings = warn_if_huge_local_run(config, expected_trajectories=360)
    assert any("hours" in w.lower() or "360" in w for w in warnings)
