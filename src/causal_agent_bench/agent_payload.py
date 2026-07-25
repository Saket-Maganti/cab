"""Canonical allowlist for task fields exposed to an evaluated agent.

Evaluation condition, intervention family, expected behaviour, scorer policy,
gold values, and evaluator-only metadata must never be included in the model
prompt.  Keeping the allowlist in one small module gives the runtime and static
leakage scanners the same definition of "agent visible".
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.schemas import BenchmarkInstance

AGENT_TASK_CONTEXT_FIELDS = frozenset(
    {
        "user_instruction",
        "instruction_patch",
        "success_criteria",
        "required_information",
        "forbidden_assumptions",
        "initial_memory",
        "max_steps",
    }
)

FORBIDDEN_AGENT_TASK_CONTEXT_FIELDS = frozenset(
    {
        "answer_contract",
        "base_task_id",
        "condition",
        "expected_final_answer",
        "gold_answer",
        "gold_answer_policy",
        "hidden_ground_truth",
        "instance_id",
        "intervention_expected_behavior",
        "intervention_family",
        "intervention_id",
        "scorer_policy",
        "scoring_notes",
        "task_id",
    }
)


def build_agent_task_context(instance: BenchmarkInstance) -> dict[str, Any]:
    """Return the complete, evaluator-blind task payload for an LLM agent."""

    intervention = instance.intervention
    return {
        "user_instruction": instance.base_task.goal.user_instruction,
        "instruction_patch": (
            intervention.instruction_patch if intervention is not None else None
        ),
        "success_criteria": list(instance.base_task.goal.success_criteria),
        "required_information": list(instance.base_task.goal.required_information),
        "forbidden_assumptions": list(
            instance.base_task.goal.forbidden_assumptions
        ),
        "initial_memory": dict(instance.initial_memory),
        "max_steps": instance.base_task.max_steps,
    }


def validate_agent_task_context(payload: dict[str, Any]) -> list[str]:
    """Validate the runtime payload shape without interpreting task content."""

    fields = set(payload)
    issues: list[str] = []
    unexpected = sorted(fields - AGENT_TASK_CONTEXT_FIELDS)
    if unexpected:
        issues.append(f"unexpected agent-visible task fields: {unexpected}")
    forbidden = sorted(fields & FORBIDDEN_AGENT_TASK_CONTEXT_FIELDS)
    if forbidden:
        issues.append(f"forbidden evaluator fields exposed to agent: {forbidden}")
    missing = sorted(AGENT_TASK_CONTEXT_FIELDS - fields)
    if missing:
        issues.append(f"missing canonical agent-visible task fields: {missing}")
    return issues


__all__ = [
    "AGENT_TASK_CONTEXT_FIELDS",
    "FORBIDDEN_AGENT_TASK_CONTEXT_FIELDS",
    "build_agent_task_context",
    "validate_agent_task_context",
]
