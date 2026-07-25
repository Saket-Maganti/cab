from __future__ import annotations

import random
from collections import Counter

from causal_agent_bench.generation.base_tasks import (
    _available_tools,
    _difficulty_plan,
    _partial_credit_criteria,
)
from causal_agent_bench.generation.naturalistic_templates import (
    ARTIFACT_SNIPPETS,
    NATURALISTIC_DOMAINS,
    NATURALISTIC_TEMPLATES,
)
from causal_agent_bench.generation.templates import difficulty_sequence
from causal_agent_bench.schemas import BaseTask, TaskGoal


def generate_naturalistic_base_tasks(
    seed: int,
    num_base_tasks: int,
    domains: list[str] | None = None,
    difficulty_mix: dict[str, float] | None = None,
) -> list[BaseTask]:
    rng = random.Random(seed)
    selected_domains = domains or NATURALISTIC_DOMAINS
    for domain in selected_domains:
        if domain not in NATURALISTIC_TEMPLATES:
            raise ValueError(f"unknown naturalistic domain {domain!r}")

    tasks: list[BaseTask] = []
    difficulty_plan = _difficulty_plan(rng, num_base_tasks, difficulty_mix or {"medium": 1.0})
    domain_seen: Counter[str] = Counter()
    for index in range(num_base_tasks):
        domain = selected_domains[index % len(selected_domains)]
        template = NATURALISTIC_TEMPLATES[domain]
        variant = domain_seen[domain]
        domain_seen[domain] += 1
        difficulty = difficulty_plan[index]
        sequence = difficulty_sequence(template.gold_tool_sequence, difficulty)
        available_tools = _available_tools(template.available_tools, sequence)
        instruction = _naturalistic_instruction(template.domain, template.instruction, variant, difficulty)
        task_id = f"natural_{domain}_{difficulty}_{variant:03d}"
        artifact_type = domain.replace("mock_", "", 1)
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
                    "template_domain": domain,
                    "variant": variant,
                    "artifact_type": artifact_type,
                },
                gold_tool_sequence=sequence,
                partial_credit_criteria=_partial_credit_criteria(template.success_criteria),
                expected_evidence=list(template.required_information),
                max_steps=max(len(sequence) + 2, 4),
                tags=[*template.tags, difficulty, "naturalistic"],
                metadata={
                    "synthetic": True,
                    "task_style": "naturalistic",
                    "artifact_type": artifact_type,
                    "generator_seed": seed,
                    "template_variant": variant,
                    "mini_study_ready": True,
                    "provenance": "repository-authored deterministic synthetic artifact template",
                    "license": "DATA_LICENSE.md",
                    "privacy_review": "synthetic_only_static_review_required_before_release",
                    "pii_policy": "no real personal data; reject non-synthetic identifiers",
                    "injection_scan_required": True,
                    "answer_key_isolated_from_agent_payload": True,
                    "human_validation_state": "HUMAN_INPUT_REQUIRED",
                },
            )
        )
    return tasks


def _naturalistic_instruction(domain: str, core_instruction: str, variant: int, difficulty: str) -> str:
    snippets = ARTIFACT_SNIPPETS.get(domain, ["Mock local artifact available in the deterministic environment."])
    artifact = snippets[variant % len(snippets)]
    suffixes = {
        "easy": "Keep the answer concise and cite the artifact explicitly.",
        "medium": "Use the available tools before answering and cite the artifact.",
        "hard": "Preserve intermediate evidence because later steps depend on it.",
        "stress": "Handle conflicting evidence in the artifact bundle and note uncertainty if needed.",
    }
    return f"{artifact}\n\n{core_instruction}\n\n{suffixes[difficulty]}"
