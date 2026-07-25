from __future__ import annotations

import random
from collections import Counter

from causal_agent_bench.generation.templates import (
    DOMAINS,
    TEMPLATES,
    difficulty_sequence,
    normalize_domain,
)
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
        if normalize_domain(domain) not in TEMPLATES:
            raise ValueError(f"unknown domain {domain!r}")

    tasks: list[BaseTask] = []
    difficulty_plan = _difficulty_plan(rng, num_base_tasks, difficulty_mix or {"medium": 1.0})
    domain_seen: Counter[str] = Counter()
    for index in range(num_base_tasks):
        domain = selected_domains[index % len(selected_domains)]
        template_domain = normalize_domain(domain)
        if template_domain not in TEMPLATES:
            raise ValueError(f"unknown domain {domain!r}")
        difficulty = difficulty_plan[index]
        template = TEMPLATES[template_domain]
        variant = domain_seen[domain]
        domain_seen[domain] += 1
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
                user_instruction=instruction,
                success_criteria=list(template.success_criteria),
                forbidden_assumptions=list(template.forbidden_assumptions),
                available_tools=available_tools,
                required_tools=list(sequence),
                optional_tools=[tool for tool in available_tools if tool not in sequence],
                hidden_ground_truth={
                    **template.hidden_ground_truth,
                    "template_domain": template_domain,
                    "public_domain": domain,
                    "variant": variant,
                },
                gold_tool_sequence=sequence,
                partial_credit_criteria=_partial_credit_criteria(template.success_criteria),
                expected_evidence=list(template.required_information),
                max_steps=max(len(sequence) + 2, 4),
                tags=[*template.tags, difficulty],
                metadata={
                    "synthetic": True,
                    "task_style": "template",
                    "generator_seed": seed,
                    "template_variant": variant,
                    "pilot_v0_1_ready": True,
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


def _difficulty_plan(
    rng: random.Random,
    num_base_tasks: int,
    difficulty_mix: dict[str, float],
) -> list[str]:
    for difficulty in difficulty_mix:
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"unknown difficulty {difficulty!r}")
    total = sum(max(weight, 0.0) for weight in difficulty_mix.values())
    if total <= 0:
        return ["medium"] * num_base_tasks
    counts: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []
    assigned = 0
    for difficulty, weight in difficulty_mix.items():
        exact = num_base_tasks * max(weight, 0.0) / total
        count = int(exact)
        counts[difficulty] = count
        assigned += count
        remainders.append((exact - count, difficulty))
    for _, difficulty in sorted(remainders, reverse=True)[: num_base_tasks - assigned]:
        counts[difficulty] += 1
    plan = [difficulty for difficulty, count in counts.items() for _ in range(count)]
    rng.shuffle(plan)
    return plan


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


def _partial_credit_criteria(success_criteria: list[str]) -> list[str]:
    return [f"Partially satisfies: {criterion}" for criterion in success_criteria]
