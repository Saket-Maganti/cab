"""Deterministic validation + leakage guards for CAB-Vision tasks.

This is the vision analogue of ``causal_agent_bench.safety.static_leakage``. The
single most important guard for a *visual* causal benchmark is that the task is
not answerable from text alone — so we check that the gold answer (and tell-tale
spoiler markers) never leak into the question string, and that every task is
actually backed by an image asset.

Checks implemented:
  1. no gold-answer text / spoiler markers in the question prompt,
  2. each referenced image exists OR is explicitly a placeholder,
  3. task family is in the controlled vocabulary,
  4. intervention fields exist for intervention/counterfactual families,
  5. answer choices are well-formed (delegated to schema, re-checked here),
  6. split is valid.

All functions return a list of ``Issue`` (empty == pass) so they compose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cab_vision.schemas.task_schema import (
    PAIRED_FAMILIES,
    TASK_FAMILIES,
    VALID_SPLITS,
    VisualCausalTask,
)

# Families whose answer genuinely depends on a described change and therefore
# must carry intervention metadata.
INTERVENTION_FAMILIES: frozenset[str] = frozenset(
    ["visual_intervention", "counterfactual_scene", "intervention_consistency"]
)

# Spoiler phrases that should never appear in a question prompt.
ANSWER_SPOILER_MARKERS: tuple[str, ...] = (
    "the answer is",
    "correct answer",
    "gold answer",
    "expected answer",
    "answer:",
    "the correct option",
)

_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Issue:
    task_id: str
    code: str
    severity: str  # "error" | "warning"
    message: str


def _normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def check_no_answer_in_prompt(
    task: VisualCausalTask, *, data_root: str | Path | None = None
) -> list[Issue]:
    """Fail if the gold answer text or a spoiler marker leaks into the question."""

    issues: list[Issue] = []
    norm_q = _normalize(task.question)

    for marker in ANSWER_SPOILER_MARKERS:
        if marker in task.question.lower():
            issues.append(
                Issue(
                    task.task_id,
                    "answer_spoiler_marker",
                    "error",
                    f"question contains spoiler marker {marker!r}",
                )
            )

    gold_norm = _normalize(task.gold_choice.text)
    # Only flag when the gold answer is a non-trivial multi-token phrase that
    # appears verbatim; single short tokens (e.g. "yes"/"no"/"2") are legitimate
    # and would create false positives.
    gold_tokens = gold_norm.split()
    if len(gold_tokens) >= 2 and gold_norm and gold_norm in norm_q:
        issues.append(
            Issue(
                task.task_id,
                "gold_answer_in_prompt",
                "error",
                f"gold answer text {task.gold_choice.text!r} appears verbatim in the question",
            )
        )
    return issues


def check_image_present_or_placeholder(
    task: VisualCausalTask, *, data_root: str | Path | None = None
) -> list[Issue]:
    """Each image must exist on disk OR be explicitly flagged as a placeholder."""

    issues: list[Issue] = []
    root = Path(data_root) if data_root is not None else None
    if not task.images:
        issues.append(
            Issue(task.task_id, "no_image", "error", "task has no image assets")
        )
        return issues
    for asset in task.images:
        if asset.is_placeholder:
            continue
        candidate = Path(asset.path)
        if root is not None and not candidate.is_absolute():
            candidate = root / asset.path
        if not candidate.exists():
            issues.append(
                Issue(
                    task.task_id,
                    "missing_image",
                    "error",
                    f"image asset {asset.asset_id!r} path {asset.path!r} "
                    "does not exist and is_placeholder is False",
                )
            )
    return issues


def check_task_family_valid(
    task: VisualCausalTask, *, data_root: str | Path | None = None
) -> list[Issue]:
    if task.family not in TASK_FAMILIES:
        return [
            Issue(
                task.task_id,
                "invalid_family",
                "error",
                f"family {task.family!r} not in {sorted(TASK_FAMILIES)}",
            )
        ]
    return []


def check_intervention_fields(
    task: VisualCausalTask, *, data_root: str | Path | None = None
) -> list[Issue]:
    """Intervention/counterfactual families must declare the changed factor."""

    issues: list[Issue] = []
    if task.family in INTERVENTION_FAMILIES:
        if not task.changed_factor:
            issues.append(
                Issue(
                    task.task_id,
                    "missing_changed_factor",
                    "error",
                    f"family {task.family!r} requires a non-empty changed_factor",
                )
            )
        if task.expected_answer_change not in {"yes", "no", "unclear"}:
            issues.append(
                Issue(
                    task.task_id,
                    "bad_expected_answer_change",
                    "error",
                    f"expected_answer_change {task.expected_answer_change!r} invalid",
                )
            )
    if task.family in PAIRED_FAMILIES:
        if task.pair_id is None:
            issues.append(
                Issue(
                    task.task_id,
                    "missing_pair_id",
                    "error",
                    f"paired family {task.family!r} requires pair_id",
                )
            )
        if task.condition not in {"observational", "interventional"}:
            issues.append(
                Issue(
                    task.task_id,
                    "missing_condition",
                    "error",
                    f"paired family {task.family!r} requires condition",
                )
            )
    return issues


def check_answer_choices_valid(
    task: VisualCausalTask, *, data_root: str | Path | None = None
) -> list[Issue]:
    """Re-validate answer choices independent of the pydantic constructor."""

    issues: list[Issue] = []
    if len(task.answer_choices) < 2:
        issues.append(
            Issue(task.task_id, "too_few_choices", "error", "need >= 2 answer choices")
        )
    indices = sorted(c.index for c in task.answer_choices)
    if indices != list(range(len(task.answer_choices))):
        issues.append(
            Issue(
                task.task_id,
                "bad_choice_indices",
                "error",
                f"choice indices must be contiguous 0..n-1; got {indices}",
            )
        )
    if not (0 <= task.gold_index < len(task.answer_choices)):
        issues.append(
            Issue(task.task_id, "gold_out_of_range", "error", "gold_index out of range")
        )
    return issues


def check_split_valid(
    task: VisualCausalTask, *, data_root: str | Path | None = None
) -> list[Issue]:
    if task.split not in VALID_SPLITS:
        return [
            Issue(
                task.task_id,
                "invalid_split",
                "error",
                f"split {task.split!r} not in {sorted(VALID_SPLITS)}",
            )
        ]
    return []


_CHECKS = (
    check_task_family_valid,
    check_split_valid,
    check_answer_choices_valid,
    check_intervention_fields,
    check_no_answer_in_prompt,
    check_image_present_or_placeholder,
)


def validate_task(
    task: VisualCausalTask, *, data_root: str | Path | None = None
) -> list[Issue]:
    """Run every check on a single task and return the combined issue list."""

    issues: list[Issue] = []
    for check in _CHECKS:
        issues.extend(check(task, data_root=data_root))
    return issues


def validate_dataset(
    tasks: list[VisualCausalTask], *, data_root: str | Path | None = None
) -> dict[str, Any]:
    """Validate a dataset and return a structured report.

    Also flags duplicate task_ids and cross-split pair leakage (the same
    ``pair_id`` appearing in more than one split), which would let a model see
    one member at train time and its partner at test time.
    """

    per_task: dict[str, list[Issue]] = {}
    seen_ids: set[str] = set()
    pair_splits: dict[str, set[str]] = {}
    dup_issues: list[Issue] = []

    for task in tasks:
        if task.task_id in seen_ids:
            dup_issues.append(
                Issue(task.task_id, "duplicate_task_id", "error", "duplicate task_id")
            )
        seen_ids.add(task.task_id)
        if task.pair_id is not None:
            pair_splits.setdefault(task.pair_id, set()).add(task.split)
        per_task[task.task_id] = validate_task(task, data_root=data_root)

    leakage_issues: list[Issue] = []
    for pair_id, splits in pair_splits.items():
        if len(splits) > 1:
            leakage_issues.append(
                Issue(
                    pair_id,
                    "cross_split_pair_leakage",
                    "error",
                    f"pair_id {pair_id!r} spans multiple splits {sorted(splits)}",
                )
            )

    all_issues = [i for issues in per_task.values() for i in issues]
    all_issues += dup_issues + leakage_issues
    errors = [i for i in all_issues if i.severity == "error"]
    return {
        "n_tasks": len(tasks),
        "n_errors": len(errors),
        "n_issues": len(all_issues),
        "ok": len(errors) == 0,
        "per_task": per_task,
        "dataset_issues": dup_issues + leakage_issues,
    }
