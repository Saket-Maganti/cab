from causal_agent_bench.agents import make_agent
from causal_agent_bench.environment import SimulatedEnvironment
from causal_agent_bench.metrics.components import compute_trajectory_metrics
from causal_agent_bench.schemas import AgentAction, Trajectory
from causal_agent_bench.task import seed_tasks
from causal_agent_bench.tools import ToolRegistry


def test_metric_known_oracle_example():
    task = seed_tasks()[0]
    agent = make_agent("ScriptedOracleAgent")
    agent.reset(task, seed=1)
    env = SimulatedEnvironment(task, seed=1, max_steps=8)
    trajectory = Trajectory(task_id=task.task_id, agent_name=agent.name, seed=1)
    tool_specs = ToolRegistry().specs(task.available_tools)
    while not env.done:
        step = env.step(agent.act(trajectory.steps, tool_specs))
        trajectory.steps.append(step)
    trajectory.final_answer = env.final_answer
    metrics = compute_trajectory_metrics(task, trajectory)
    assert metrics["final_answer_correctness"] == 1.0
    assert metrics["tool_call_recall"] == 1.0
    assert metrics["tool_call_precision"] == 1.0
    assert metrics["premature_stop_rate"] == 0.0


def test_premature_stop_metric():
    task = seed_tasks()[0]
    trajectory = Trajectory(
        task_id=task.task_id,
        agent_name="unit",
        seed=1,
        final_answer="Choose saver_hotel at total 176.00.",
        steps=[
            {
                "index": 0,
                "action": AgentAction(
                    kind="final_answer",
                    final_answer="Choose saver_hotel at total 176.00.",
                ),
            }
        ],
    )
    metrics = compute_trajectory_metrics(task, trajectory)
    assert metrics["premature_stop_rate"] == 1.0
