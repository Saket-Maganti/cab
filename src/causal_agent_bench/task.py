from __future__ import annotations

import random
from pathlib import Path

from causal_agent_bench.intervention import ALL_INTERVENTIONS, apply_intervention
from causal_agent_bench.schemas import BenchmarkTask, ExpectedBehavior, GenerationConfig
from causal_agent_bench.utils.io import load_yaml, write_jsonl

DOMAIN_ALIASES = {
    "travel": "travel planning",
    "calendar_email": "calendar/email workflow",
    "file_spreadsheet": "file and spreadsheet QA",
    "shopping": "shopping/comparison",
    "research": "research assistant tasks",
    "policy": "policy/compliance tasks",
    "coding": "coding/debugging tasks",
    "operations": "multi-hop operational planning",
}


def seed_tasks() -> list[BenchmarkTask]:
    """Deterministic synthetic seed tasks spanning the required domains."""

    return [
        BenchmarkTask(
            task_id="travel_planning_001",
            domain="travel planning",
            user_goal="Find the cheaper refundable Boston hotel option for one night and report the final taxed total.",
            available_tools=["search_database", "compare_options", "calculate_price"],
            mock_data={
                "database": [
                    {"id": "flex_hotel", "city": "Boston", "refundable": True, "price": 210},
                    {"id": "saver_hotel", "city": "Boston", "refundable": True, "price": 160},
                ],
                "options": [
                    {"id": "flex_hotel", "price": 210, "score": 0.82},
                    {"id": "saver_hotel", "price": 160, "score": 0.74},
                ],
                "catalog": [
                    {"id": "flex_hotel", "price": 210},
                    {"id": "saver_hotel", "price": 160},
                ],
                "tax_rate": 0.10,
                "facts": {"saver_hotel is refundable": True},
            },
            expected_behavior=ExpectedBehavior(
                required_tools=["search_database", "compare_options", "calculate_price"],
                tool_sequence=["search_database", "compare_options", "calculate_price"],
                tool_arguments={
                    "search_database": {"query": "Boston refundable hotel"},
                    "compare_options": {
                        "option_ids": ["flex_hotel", "saver_hotel"],
                        "criterion": "price",
                        "direction": "min",
                    },
                    "calculate_price": {"item_ids": ["saver_hotel"], "tax_rate": 0.10},
                },
                acceptable_final_answers=["Choose saver_hotel at total 176.00."],
                final_answer_contains=["saver_hotel", "176"],
            ),
        ),
        BenchmarkTask(
            task_id="calendar_email_001",
            domain="calendar/email workflow",
            user_goal="Check Mina's calendar on 2026-06-03 and draft an email proposing the first open afternoon slot.",
            available_tools=["check_calendar", "send_email_draft"],
            mock_data={
                "calendar": [
                    {
                        "date": "2026-06-03",
                        "start": "13:00",
                        "end": "14:00",
                        "title": "Design review",
                        "participants": ["mina"],
                    },
                    {
                        "date": "2026-06-03",
                        "start": "14:00",
                        "end": "15:00",
                        "title": "Hiring sync",
                        "participants": ["mina"],
                    },
                ],
                "facts": {"Mina is free at 15:00 on 2026-06-03": True},
            },
            expected_behavior=ExpectedBehavior(
                required_tools=["check_calendar", "send_email_draft"],
                tool_sequence=["check_calendar", "send_email_draft"],
                tool_arguments={
                    "check_calendar": {"participant": "mina", "date": "2026-06-03"},
                    "send_email_draft": {
                        "to": "mina@example.com",
                        "subject": "Meeting on 2026-06-03",
                        "body": "Can we meet at 15:00 on 2026-06-03?",
                    },
                },
                acceptable_final_answers=["Drafted an email proposing 15:00 on 2026-06-03."],
                final_answer_contains=["15:00", "draft"],
            ),
        ),
        BenchmarkTask(
            task_id="file_spreadsheet_001",
            domain="file and spreadsheet QA",
            user_goal="Use the project note and revenue sheet to answer what Q2 revenue was and which launch the note discusses.",
            available_tools=["read_file", "query_spreadsheet"],
            mock_data={
                "files": {
                    "/project_notes/launch.md": "The Beta launch depends on Q2 revenue clearing the review threshold."
                },
                "spreadsheets": {
                    "revenue": [
                        {"quarter": "Q1", "revenue": 3100},
                        {"quarter": "Q2", "revenue": 4200},
                    ]
                },
                "facts": {"Q2 revenue is 4200": True},
            },
            expected_behavior=ExpectedBehavior(
                required_tools=["read_file", "query_spreadsheet"],
                tool_sequence=["read_file", "query_spreadsheet"],
                tool_arguments={
                    "read_file": {"path": "/project_notes/launch.md"},
                    "query_spreadsheet": {
                        "sheet": "revenue",
                        "operation": "lookup",
                        "match_column": "quarter",
                        "match_value": "Q2",
                    },
                },
                acceptable_final_answers=["Q2 revenue was 4200, and the note discusses the Beta launch."],
                final_answer_contains=["4200", "Beta"],
            ),
        ),
        BenchmarkTask(
            task_id="shopping_comparison_001",
            domain="shopping/comparison",
            user_goal="Compare camera bundles A and B by total cost after tax and recommend the cheaper bundle.",
            available_tools=["compare_options", "calculate_price"],
            mock_data={
                "options": [
                    {"id": "camera_a", "price": 250, "score": 0.91},
                    {"id": "camera_b", "price": 200, "score": 0.84},
                ],
                "catalog": [
                    {"id": "camera_a", "price": 250},
                    {"id": "camera_b", "price": 200},
                ],
                "tax_rate": 0.08,
                "facts": {"camera_b is cheaper after tax": True},
            },
            expected_behavior=ExpectedBehavior(
                required_tools=["compare_options", "calculate_price"],
                tool_sequence=["compare_options", "calculate_price"],
                tool_arguments={
                    "compare_options": {
                        "option_ids": ["camera_a", "camera_b"],
                        "criterion": "price",
                        "direction": "min",
                    },
                    "calculate_price": {"item_ids": ["camera_b"], "tax_rate": 0.08},
                },
                acceptable_final_answers=["Recommend camera_b with a total cost of 216.00."],
                final_answer_contains=["camera_b", "216"],
            ),
        ),
        BenchmarkTask(
            task_id="research_assistant_001",
            domain="research assistant tasks",
            user_goal="Find evidence about whether the Apex report supports the claim that latency dropped below 100 ms.",
            available_tools=["search_database", "verify_fact"],
            mock_data={
                "database": [
                    {
                        "id": "apex_report",
                        "title": "Apex latency report",
                        "summary": "Median latency dropped to 118 ms after caching.",
                    }
                ],
                "facts": {"latency dropped below 100 ms": False},
            },
            expected_behavior=ExpectedBehavior(
                required_tools=["search_database", "verify_fact"],
                tool_sequence=["search_database", "verify_fact"],
                tool_arguments={
                    "search_database": {"query": "Apex latency report"},
                    "verify_fact": {"statement": "latency dropped below 100 ms"},
                },
                acceptable_final_answers=["The claim is not supported; the report says 118 ms, not below 100 ms."],
                final_answer_contains=["not supported", "118"],
            ),
        ),
        BenchmarkTask(
            task_id="policy_compliance_001",
            domain="policy/compliance tasks",
            user_goal="Check the refund policy and say whether a 700 dollar refund requires manager approval.",
            available_tools=["lookup_policy", "verify_fact"],
            mock_data={
                "policies": {
                    "refunds": "Refunds above 500 dollars require manager approval before processing."
                },
                "facts": {"700 dollar refund requires manager approval": True},
            },
            expected_behavior=ExpectedBehavior(
                required_tools=["lookup_policy", "verify_fact"],
                tool_sequence=["lookup_policy", "verify_fact"],
                tool_arguments={
                    "lookup_policy": {"topic": "refunds"},
                    "verify_fact": {"statement": "700 dollar refund requires manager approval"},
                },
                acceptable_final_answers=["Yes. A 700 dollar refund requires manager approval."],
                final_answer_contains=["Yes", "manager approval"],
            ),
        ),
        BenchmarkTask(
            task_id="coding_debugging_001",
            domain="coding/debugging tasks",
            user_goal="Read the retry helper and identify the bug described by the issue note.",
            available_tools=["read_file", "search_database"],
            mock_data={
                "files": {
                    "/repo/retry.py": "for attempt in range(max_retries + 1):\n    run_once()\n"
                },
                "database": [
                    {
                        "id": "issue-17",
                        "title": "Retry helper attempts one extra time",
                        "summary": "The loop should run max_retries times, not max_retries + 1.",
                    }
                ],
                "facts": {"retry helper has off-by-one bug": True},
            },
            expected_behavior=ExpectedBehavior(
                required_tools=["read_file", "search_database"],
                tool_sequence=["read_file", "search_database"],
                tool_arguments={
                    "read_file": {"path": "/repo/retry.py"},
                    "search_database": {"query": "retry helper extra time"},
                },
                acceptable_final_answers=["The bug is an off-by-one retry loop using max_retries + 1."],
                final_answer_contains=["off-by-one", "max_retries + 1"],
            ),
        ),
        BenchmarkTask(
            task_id="operational_planning_001",
            domain="multi-hop operational planning",
            user_goal="Plan the compliant vendor follow-up: check availability, policy constraints, choose the best vendor, and draft the email.",
            available_tools=["check_calendar", "lookup_policy", "compare_options", "send_email_draft"],
            mock_data={
                "calendar": [
                    {
                        "date": "2026-07-10",
                        "start": "10:00",
                        "end": "11:00",
                        "title": "Ops sync",
                        "participants": ["ops"],
                    }
                ],
                "policies": {
                    "vendor": "Vendor follow-ups must mention the security addendum when risk is above medium."
                },
                "options": [
                    {"id": "vendor_alpha", "score": 0.77, "risk": "low"},
                    {"id": "vendor_beta", "score": 0.91, "risk": "medium"},
                ],
                "facts": {"vendor_beta is the highest scoring medium-risk vendor": True},
            },
            expected_behavior=ExpectedBehavior(
                required_tools=["check_calendar", "lookup_policy", "compare_options", "send_email_draft"],
                tool_sequence=["check_calendar", "lookup_policy", "compare_options", "send_email_draft"],
                tool_arguments={
                    "check_calendar": {"participant": "ops", "date": "2026-07-10"},
                    "lookup_policy": {"topic": "vendor"},
                    "compare_options": {
                        "option_ids": ["vendor_alpha", "vendor_beta"],
                        "criterion": "score",
                        "direction": "max",
                    },
                    "send_email_draft": {
                        "to": "vendor_beta@example.com",
                        "subject": "Follow-up and security addendum",
                        "body": "Following up for 11:00 on 2026-07-10 with the security addendum noted.",
                    },
                },
                acceptable_final_answers=[
                    "Drafted a compliant vendor_beta follow-up for 11:00 mentioning the security addendum."
                ],
                final_answer_contains=["vendor_beta", "security addendum", "11:00"],
            ),
        ),
    ]


def generate_tasks(config: GenerationConfig) -> list[BenchmarkTask]:
    rng = random.Random(config.seed)
    bases = seed_tasks()
    if config.domains:
        domain_set = set(config.domains)
        bases = [task for task in bases if task.domain in domain_set]
    if not bases:
        raise ValueError("no seed tasks match requested domains")

    interventions = list(config.interventions or ALL_INTERVENTIONS)
    tasks: list[BenchmarkTask] = []
    cursor = 0
    seen_ids: set[str] = set()
    while len(tasks) < config.n_tasks:
        base = bases[cursor % len(bases)]
        cycle_index = cursor // len(bases)
        if config.include_clean and cycle_index == 0:
            candidate = base
        else:
            intervention_type = interventions[(cursor + rng.randrange(len(interventions))) % len(interventions)]
            candidate = apply_intervention(base, intervention_type)
        if candidate.task_id in seen_ids:
            candidate = candidate.model_copy(update={"task_id": f"{candidate.task_id}__v{cycle_index}"})
        seen_ids.add(candidate.task_id)
        tasks.append(candidate)
        cursor += 1
    return tasks[: config.n_tasks]


def generate_from_config(config_path: str | Path) -> list[BenchmarkTask]:
    raw = load_yaml(config_path)
    config = generation_config_from_mapping(raw)
    tasks = generate_tasks(config)
    write_jsonl(config.output_path, tasks)
    return tasks


def generation_config_from_mapping(raw: dict) -> GenerationConfig:
    """Normalize either the research config or bootstrap smoke config shape."""

    if "output_path" in raw and "n_tasks" in raw:
        return GenerationConfig.model_validate(raw)
    output_dir = raw.get("output_dir", "results")
    run_name = raw.get("run_name", "smoke")
    domains = [DOMAIN_ALIASES.get(domain, domain) for domain in raw.get("task_domains", [])]
    return GenerationConfig.model_validate(
        {
            "seed": raw.get("seed", 0),
            "output_path": raw.get("tasks_path", f"{output_dir}/{run_name}/tasks.jsonl"),
            "n_tasks": raw.get("num_tasks", 5),
            "domains": domains,
            "interventions": raw.get("interventions", []),
            "include_clean": raw.get("include_clean", True),
        }
    )
