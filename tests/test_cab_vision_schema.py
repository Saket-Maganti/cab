"""Tests for the CAB-Vision task schema and leakage/validation guards."""

from __future__ import annotations

from pathlib import Path

import pytest

from cab_vision.schemas.task_schema import (
    TASK_FAMILIES,
    AnswerChoice,
    VisualAsset,
    VisualCausalTask,
    load_tasks_jsonl,
)
from cab_vision.validation.leakage_checks import (
    check_image_present_or_placeholder,
    check_no_answer_in_prompt,
    validate_dataset,
    validate_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = REPO_ROOT / "data" / "cab_vision" / "examples" / "sample_tasks.jsonl"


def _task(**overrides) -> VisualCausalTask:
    base = {
        "task_id": "t1",
        "family": "visual_intervention",
        "split": "test",
        "domain": "physical",
        "question": "If the support block is taken away, what happens to the object on top?",
        "images": [
            VisualAsset(asset_id="a1", path="x/none.png", role="primary", is_placeholder=True)
        ],
        "answer_choices": [
            AnswerChoice(index=0, text="It stays put"),
            AnswerChoice(index=1, text="It drops to the ground"),
        ],
        "gold_index": 1,
        "changed_factor": "support_present",
        "expected_answer_change": "yes",
    }
    base.update(overrides)
    return VisualCausalTask(**base)


# --- schema construction -----------------------------------------------------


def test_valid_task_constructs():
    task = _task()
    assert task.family in TASK_FAMILIES
    assert task.gold_choice.text == "It drops to the ground"


def test_duplicate_choice_text_rejected():
    with pytest.raises(ValueError):
        _task(
            answer_choices=[
                AnswerChoice(index=0, text="same"),
                AnswerChoice(index=1, text="SAME"),
            ],
            gold_index=0,
        )


def test_non_contiguous_choice_indices_rejected():
    with pytest.raises(ValueError):
        _task(
            answer_choices=[
                AnswerChoice(index=0, text="a"),
                AnswerChoice(index=2, text="b"),
            ],
            gold_index=0,
        )


def test_paired_family_requires_pair_id_and_condition():
    with pytest.raises(ValueError):
        _task(family="intervention_consistency", pair_id=None, condition=None)


def test_action_family_requires_a_valid_action():
    with pytest.raises(ValueError):
        _task(
            family="action_selection",
            answer_choices=[
                AnswerChoice(index=0, text="go left", is_valid_action=False),
                AnswerChoice(index=1, text="go right", is_valid_action=False),
            ],
            gold_index=0,
        )


# --- leakage / validation guards --------------------------------------------


def test_no_answer_in_prompt_passes_clean_task():
    assert check_no_answer_in_prompt(_task()) == []


def test_gold_answer_leak_detected():
    leaky = _task(
        question="If the block is removed it drops to the ground; what happens?",
    )
    issues = check_no_answer_in_prompt(leaky)
    assert any(i.code == "gold_answer_in_prompt" for i in issues)


def test_spoiler_marker_detected():
    leaky = _task(question="What happens next? The answer is obvious from the scene.")
    issues = check_no_answer_in_prompt(leaky)
    assert any(i.code == "answer_spoiler_marker" for i in issues)


def test_missing_real_image_detected():
    task = _task(
        images=[VisualAsset(asset_id="a1", path="does/not/exist.png", is_placeholder=False)]
    )
    issues = check_image_present_or_placeholder(task)
    assert any(i.code == "missing_image" for i in issues)


def test_placeholder_image_allowed():
    assert check_image_present_or_placeholder(_task()) == []


def test_intervention_family_requires_changed_factor():
    task = _task(changed_factor=None)
    issues = validate_task(task)
    assert any(i.code == "missing_changed_factor" for i in issues)


def test_validate_task_clean_passes():
    assert validate_task(_task()) == []


# --- sample dataset ----------------------------------------------------------


def test_sample_file_exists():
    assert SAMPLE_PATH.exists(), f"missing sample file {SAMPLE_PATH}"


def test_sample_tasks_load_and_validate():
    tasks = load_tasks_jsonl(SAMPLE_PATH)
    assert len(tasks) >= 8
    report = validate_dataset(tasks, data_root=REPO_ROOT)
    assert report["ok"], report["per_task"]
    assert report["n_errors"] == 0


def test_sample_covers_multiple_families():
    tasks = load_tasks_jsonl(SAMPLE_PATH)
    families = {t.family for t in tasks}
    # at least the four core families must be represented
    assert {
        "visual_intervention",
        "counterfactual_scene",
        "spurious_cue",
        "action_selection",
    } <= families


def test_sample_has_a_complete_pair():
    tasks = load_tasks_jsonl(SAMPLE_PATH)
    pair_ids = [t.pair_id for t in tasks if t.pair_id]
    # at least one pair_id appears for both conditions
    from collections import Counter

    counts = Counter(pair_ids)
    assert any(c >= 2 for c in counts.values())
