from __future__ import annotations

from copy import deepcopy
from typing import Any

from causal_agent_bench.agents.registry import get_agent
from causal_agent_bench.environment import BenchmarkEnvironment
from causal_agent_bench.schemas import AgentAction, BenchmarkInstance, Trajectory


def execute_agent_on_instance(
    *,
    agent_name: str,
    instance: BenchmarkInstance,
    run_id: str,
    seed: int,
    repeat: int,
    max_steps: int,
    save_observations: bool,
    save_agent_thoughts: bool,
) -> Trajectory:
    agent = get_agent(agent_name, seed=seed)
    env = BenchmarkEnvironment(instance, run_id=run_id, agent_name=agent.name)
    env.max_steps = max_steps
    agent.reset(instance, seed=seed)

    for _ in range(max_steps):
        if env.done:
            break
        action = agent.act(env.steps, env.registry.specs(env.available_tools))
        if not isinstance(action, AgentAction):
            action = AgentAction.model_validate(action)
        env.step(action)

    trajectory = env.trajectory()
    if not env.done:
        trajectory.terminated_reason = "max_steps"
    trajectory.metadata.update(
        {
            "repeat": repeat,
            "seed": seed,
            "run_key": f"{agent.name}:{instance.instance_id}:{repeat}",
            "max_steps": max_steps,
        }
    )
    if not save_observations or not save_agent_thoughts:
        trajectory = _strip_trajectory(
            trajectory,
            save_observations=save_observations,
            save_agent_thoughts=save_agent_thoughts,
        )
    return trajectory


def _strip_trajectory(
    trajectory: Trajectory,
    *,
    save_observations: bool,
    save_agent_thoughts: bool,
) -> Trajectory:
    payload = trajectory.model_dump(mode="python")
    stripped_steps: list[dict[str, Any]] = []
    for step in payload["steps"]:
        step_copy = deepcopy(step)
        if not save_observations:
            step_copy["observation"] = None
        if not save_agent_thoughts:
            action = step_copy.get("action")
            if isinstance(action, dict):
                action["thought"] = None
        stripped_steps.append(step_copy)
    payload["steps"] = stripped_steps
    return Trajectory.model_validate(payload)
