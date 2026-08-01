"""Deterministic incomplete-block assignment and public-safe balance diagnostics."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Final

from causal_agent_bench.hashing import stable_hash

ASSIGNMENT_DESIGN_VERSION: Final[str] = "cab_constrained_rotation_bibd_v1"
ASSOCIATION_THRESHOLD: Final[float] = 0.20
DIFFICULTY_ORDER: Final[dict[str, int]] = {
    "easy": 0,
    "medium": 1,
    "hard": 2,
    "stress": 3,
}


def constrained_rotation_assignments(
    tasks: list[dict[str, Any]],
    families: list[str],
    *,
    block_size: int = 5,
) -> list[list[str]]:
    """Assign consecutive rotated family blocks within domain task clusters."""

    if not families or not 0 < block_size < len(families):
        raise ValueError("block_size must be positive and smaller than family count")
    by_domain: dict[str, list[int]] = defaultdict(list)
    for index, task in enumerate(tasks):
        by_domain[str(task["domain"])].append(index)
    output: list[list[str] | None] = [None] * len(tasks)
    for domain_index, domain in enumerate(sorted(by_domain)):
        ordered = sorted(
            by_domain[domain],
            key=lambda index: (
                DIFFICULTY_ORDER.get(str(tasks[index]["difficulty"]), 99),
                str(tasks[index].get("scenario_key") or ""),
            ),
        )
        for local_index, task_index in enumerate(ordered):
            start = (local_index + 3 * domain_index) % len(families)
            output[task_index] = [
                families[(start + offset) % len(families)]
                for offset in range(block_size)
            ]
    if any(value is None for value in output):
        raise AssertionError("assignment algorithm left an unassigned task")
    return [list(value or []) for value in output]


def assignment_balance_diagnostics(
    tasks: list[dict[str, Any]],
    assignments: list[list[str]],
    *,
    families: list[str],
) -> dict[str, Any]:
    if len(tasks) != len(assignments):
        raise ValueError("task and assignment counts differ")
    records = [
        {
            "family": family,
            "difficulty": str(task["difficulty"]),
            "domain": str(task["domain"]),
            "block": task_index,
        }
        for task_index, (task, assigned) in enumerate(
            zip(tasks, assignments, strict=True)
        )
        for family in assigned
    ]
    family_difficulty = _association(records, "family", "difficulty")
    family_domain = _association(records, "family", "domain")
    difficulty_domain = _association(records, "difficulty", "domain")
    family_diff_table = family_difficulty["table"]
    family_domain_table = family_domain["table"]
    difficulties = sorted(
        {str(task["difficulty"]) for task in tasks},
        key=lambda value: DIFFICULTY_ORDER.get(value, 99),
    )
    domains = sorted({str(task["domain"]) for task in tasks})
    no_empty_family_difficulty = all(
        int(family_diff_table.get(family, {}).get(difficulty, 0)) > 0
        for family in families
        for difficulty in difficulties
    )
    each_family_multiple_domains = all(
        sum(
            int(count) > 0
            for count in family_domain_table.get(family, {}).values()
        )
        >= 2
        for family in families
    )
    each_domain_multiple_families = all(
        sum(
            int(family_domain_table.get(family, {}).get(domain, 0)) > 0
            for family in families
        )
        >= 2
        for domain in domains
    )
    checks = {
        "no_empty_family_difficulty_cell": no_empty_family_difficulty,
        "each_family_spans_every_difficulty": no_empty_family_difficulty,
        "each_family_spans_multiple_domains": each_family_multiple_domains,
        "each_domain_receives_multiple_families": each_domain_multiple_families,
        "family_difficulty_cramers_v_below_threshold": (
            family_difficulty["cramers_v"] <= ASSOCIATION_THRESHOLD
        ),
        "family_domain_cramers_v_below_threshold": (
            family_domain["cramers_v"] <= ASSOCIATION_THRESHOLD
        ),
        "task_blocks_have_fixed_size": (
            len({len(assignment) for assignment in assignments}) == 1
            and bool(assignments)
        ),
        "family_repetition_explicit": all(
            sum(family in assignment for assignment in assignments) > 1
            for family in families
        ),
    }
    receipt_payload = {
        "design_version": ASSIGNMENT_DESIGN_VERSION,
        "task_count": len(tasks),
        "family_order": families,
        "block_size": len(assignments[0]) if assignments else 0,
        "aggregate_assignment_sequence": [
            {
                "domain": str(task["domain"]),
                "difficulty": str(task["difficulty"]),
                "families": assignment,
            }
            for task, assignment in zip(tasks, assignments, strict=True)
        ],
    }
    return {
        "schema_version": "cab_assignment_balance_diagnostics_v1",
        "design_version": ASSIGNMENT_DESIGN_VERSION,
        "association_threshold": ASSOCIATION_THRESHOLD,
        "task_count": len(tasks),
        "intervention_assignment_count": len(records),
        "family_count": len(families),
        "difficulty_count": len(difficulties),
        "domain_count": len(domains),
        "block_summary": {
            "block_count": len(assignments),
            "block_size": len(assignments[0]) if assignments else 0,
            "task_cluster_key": "domain",
            "rotation_stride": 3,
            "repeated_interventions_explicit": True,
        },
        "family_by_difficulty": family_difficulty,
        "family_by_domain": family_domain,
        "difficulty_by_domain": difficulty_domain,
        "checks": checks,
        "passed": all(checks.values()),
        "deterministic_receipt": stable_hash(receipt_payload, length=64),
    }


def _association(
    records: list[dict[str, Any]],
    row_key: str,
    column_key: str,
) -> dict[str, Any]:
    row_labels = sorted({str(record[row_key]) for record in records})
    column_labels = sorted(
        {str(record[column_key]) for record in records},
        key=lambda value: DIFFICULTY_ORDER.get(value, 99),
    )
    counts = Counter(
        (str(record[row_key]), str(record[column_key])) for record in records
    )
    row_totals = Counter(str(record[row_key]) for record in records)
    column_totals = Counter(str(record[column_key]) for record in records)
    total = len(records)
    table: dict[str, dict[str, int]] = {
        row: {column: counts[(row, column)] for column in column_labels}
        for row in row_labels
    }
    residuals: dict[str, dict[str, float]] = {}
    chi_squared = 0.0
    mutual_information = 0.0
    for row in row_labels:
        residuals[row] = {}
        for column in column_labels:
            observed = counts[(row, column)]
            expected = row_totals[row] * column_totals[column] / total
            if expected > 0:
                chi_squared += (observed - expected) ** 2 / expected
                denominator = math.sqrt(
                    expected
                    * (1 - row_totals[row] / total)
                    * (1 - column_totals[column] / total)
                )
                residuals[row][column] = round(
                    (observed - expected) / denominator if denominator else 0.0,
                    6,
                )
            if observed:
                p_xy = observed / total
                p_x = row_totals[row] / total
                p_y = column_totals[column] / total
                mutual_information += p_xy * math.log(p_xy / (p_x * p_y))
    minimum_dimension = min(len(row_labels) - 1, len(column_labels) - 1)
    cramers_v = math.sqrt(
        chi_squared / (total * minimum_dimension)
    ) if total and minimum_dimension > 0 else 0.0
    return {
        "row_variable": row_key,
        "column_variable": column_key,
        "table": table,
        "standardized_residuals": residuals,
        "chi_squared": round(chi_squared, 6),
        "cramers_v": round(cramers_v, 6),
        "mutual_information_nats": round(mutual_information, 6),
    }


__all__ = [
    "ASSIGNMENT_DESIGN_VERSION",
    "ASSOCIATION_THRESHOLD",
    "assignment_balance_diagnostics",
    "constrained_rotation_assignments",
]
