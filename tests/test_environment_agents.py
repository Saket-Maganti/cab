from causal_agent_bench.agents import make_agent
from causal_agent_bench.environment import SimulatedEnvironment
from causal_agent_bench.schemas import Trajectory
from causal_agent_bench.task import seed_tasks
from causal_agent_bench.tools import ToolRegistry


def test_environment_step_with_oracle_finishes():
    task = seed_tasks()[0]
    agent = make_agent("ScriptedOracleAgent")
    agent.reset(task, seed=1)
    env = SimulatedEnvironment(task, seed=1, max_steps=8)
    trajectory = Trajectory(task_id=task.task_id, agent_name=agent.name, seed=1)
    tool_specs = ToolRegistry().specs(task.available_tools)
    while not env.done:
        step = env.step(agent.act(trajectory.steps, tool_specs))
        trajectory.steps.append(step)
    assert env.success is True
    assert env.final_answer is not None


def test_baseline_agents_emit_valid_actions():
    task = seed_tasks()[1]
    for name in [
        "RandomToolAgent",
        "ScriptedOracleAgent",
        "GreedyToolAgent",
        "ReActStyleStubAgent",
        "PlannerExecutorStubAgent",
    ]:
        agent = make_agent(name)
        agent.reset(task, seed=1)
        action = agent.act([], ToolRegistry().specs(task.available_tools))
        assert action.kind in {"tool_call", "final_answer"}
