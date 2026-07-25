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
    agent_run_id: str | None = None,
    agent_kwargs: dict[str, Any] | None = None,
) -> Trajectory:
    agent = get_agent(agent_name, seed=seed, **(agent_kwargs or {}))
    trajectory_agent_name = agent_run_id or agent.name
    env = BenchmarkEnvironment(
        instance,
        run_id=run_id,
        agent_name=trajectory_agent_name,
        model_name=getattr(agent, "model_name", None),
    )
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
            "run_key": f"{trajectory_agent_name}:{instance.instance_id}:{repeat}",
            "max_steps": max_steps,
            "agent_type": agent.name,
        }
    )
    if hasattr(agent, "run_metadata"):
        trajectory.metadata.update(agent.run_metadata())
    _attach_trajectory_cost_summary(trajectory)
    trajectory = Trajectory.model_validate(trajectory.model_dump(mode="python"))
    if not save_observations or not save_agent_thoughts:
        trajectory = _strip_trajectory(
            trajectory,
            save_observations=save_observations,
            save_agent_thoughts=save_agent_thoughts,
        )
    return trajectory


def _attach_trajectory_cost_summary(trajectory: Trajectory) -> None:
    tool_call_count = 0
    for step in trajectory.steps:
        action = step.get("action") if isinstance(step, dict) else None
        if isinstance(action, dict) and isinstance(action.get("tool_call"), dict):
            tool_call_count += 1
    llm_calls = trajectory.metadata.get("llm_calls")
    if not isinstance(llm_calls, list):
        llm_calls = []
    usage = trajectory.metadata.get("token_usage")
    if not isinstance(usage, dict):
        usage = {}
    model_call_count = sum(1 for call in llm_calls if call.get("provider_call_made", True))
    total_retries = sum(int(call.get("retries") or 0) for call in llm_calls)
    trajectory.metadata.update(
        {
            "model_call_count": model_call_count,
            "llm_call_count": len(llm_calls),
            "tool_call_count": tool_call_count,
            "total_retries": total_retries,
            "prompt_tokens": usage.get("input_tokens", trajectory.metadata.get("prompt_tokens", 0)),
            "completion_tokens": usage.get(
                "output_tokens",
                trajectory.metadata.get("completion_tokens", 0),
            ),
            "total_tokens": usage.get("total_tokens", trajectory.metadata.get("total_tokens", 0)),
        }
    )


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
