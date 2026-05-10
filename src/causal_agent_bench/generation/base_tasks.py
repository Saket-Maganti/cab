from __future__ import annotations

import random

from causal_agent_bench.generation.templates import DOMAINS, TEMPLATES, difficulty_sequence
from causal_agent_bench.schemas import BaseTask, TaskGoal

DIFFICULTIES = ["easy", "medium", "hard", "stress"]


def generate_base_tasks(
    seed: int,
    num_base_tasks: int,
    domains: list[str] | None = None,
    difficulty_mix: dict[str, float] | None = None,
) -> list[BaseTask]:
    rng = random.Random(seed)
    selected_domains = domains or DOMAINS
    if not selected_domains:
        raise ValueError("at least one domain is required")
    for domain in selected_domains:
        if domain not in TEMPLATES:
            raise ValueError(f"unknown domain {domain!r}")

    tasks: list[BaseTask] = []
    for index in range(num_base_tasks):
        domain = selected_domains[index % len(selected_domains)]
        difficulty = _sample_difficulty(rng, difficulty_mix or {"medium": 1.0})
        template = TEMPLATES[domain]
        variant = index // len(selected_domains)
        sequence = difficulty_sequence(template.gold_tool_sequence, difficulty)
        available_tools = _available_tools(template.available_tools, sequence)
        instruction = _instruction_variant(template.instruction, difficulty, variant)
        task_id = f"{domain}_{difficulty}_{variant:03d}"
        tasks.append(
            BaseTask(
                task_id=task_id,
                domain=domain,
                difficulty=difficulty,
                goal=TaskGoal(
                    user_instruction=instruction,
                    success_criteria=list(template.success_criteria),
                    required_information=list(template.required_information),
                    forbidden_assumptions=list(template.forbidden_assumptions),
                    expected_final_answer=template.expected_final_answer,
                ),
                available_tools=available_tools,
                hidden_ground_truth={
                    **template.hidden_ground_truth,
                    "template_domain": domain,
                    "variant": variant,
                },
                gold_tool_sequence=sequence,
                max_steps=max(len(sequence) + 2, 4),
                tags=[*template.tags, difficulty],
                metadata={
                    "synthetic": True,
                    "generator_seed": seed,
                    "template_variant": variant,
                },
            )
        )
    return tasks


def _sample_difficulty(rng: random.Random, difficulty_mix: dict[str, float]) -> str:
    total = sum(max(weight, 0.0) for weight in difficulty_mix.values())
    if total <= 0:
        return "medium"
    threshold = rng.random() * total
    cumulative = 0.0
    for difficulty, weight in difficulty_mix.items():
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"unknown difficulty {difficulty!r}")
        cumulative += max(weight, 0.0)
        if threshold <= cumulative:
            return difficulty
    return next(reversed(difficulty_mix))


def _available_tools(base_tools: list[str], sequence: list[str]) -> list[str]:
    tools = list(base_tools)
    for tool in sequence:
        if tool not in tools:
            tools.append(tool)
    return tools


def _instruction_variant(instruction: str, difficulty: str, variant: int) -> str:
    suffixes = {
        "easy": "Keep the answer concise.",
        "medium": "Use the available tools before answering.",
        "hard": "Preserve intermediate evidence because later steps depend on it.",
        "stress": "Handle multiple constraints and explicitly note any conflicting evidence.",
    }
    return f"{instruction} {suffixes[difficulty]} Synthetic variant {variant}."
