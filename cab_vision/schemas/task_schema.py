"""Draft task schema for CAB-Vision.

A CAB-Vision task is a *visually grounded causal decision*. The defining
property (vs. ordinary VQA) is that the correct answer depends on a causal
relation in the image(s) — an intervention, a counterfactual scene change, a
cue-conflict, or an action constraint — and must not be answerable from the
question text alone.

Design mirrors the strictness of ``causal_agent_bench.schemas`` (pydantic v2,
``extra="forbid"``) so the vision benchmark inherits the same discipline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --- Controlled vocabularies -------------------------------------------------

TaskFamily = Literal[
    "visual_intervention",  # remove/block/move/replace object X -> effect on Y
    "counterfactual_scene",  # before/after pair -> causal consequence
    "spurious_cue",  # misleading correlated cue present; must not infer cause
    "action_selection",  # choose a causally valid next action from the scene
    "causal_chain",  # produce/select an image-grounded causal explanation
    "intervention_consistency",  # observational vs interventional paired query
]

TASK_FAMILIES: frozenset[str] = frozenset(
    [
        "visual_intervention",
        "counterfactual_scene",
        "spurious_cue",
        "action_selection",
        "causal_chain",
        "intervention_consistency",
    ]
)

# Families that come as observational/interventional (or before/after) pairs and
# are scored with pairwise causal-consistency metrics.
PAIRED_FAMILIES: frozenset[str] = frozenset(
    ["counterfactual_scene", "intervention_consistency"]
)

# Families whose answer choices denote agent actions (scored with action validity).
ACTION_FAMILIES: frozenset[str] = frozenset(["action_selection"])

Split = Literal["train", "dev", "test", "hidden_test"]
VALID_SPLITS: frozenset[str] = frozenset(["train", "dev", "test", "hidden_test"])

Condition = Literal["observational", "interventional"]
AnswerChange = Literal["yes", "no", "unclear"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VisualAsset(StrictModel):
    """One image (or video / image-pair member) attached to a task.

    ``is_placeholder=True`` declares that ``path`` is intentionally a stand-in
    (e.g. during prototyping) so validators do not require the file to exist.
    Real tasks must set ``is_placeholder=False`` and ship the asset.
    """

    asset_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    role: Literal["primary", "before", "after", "context", "video"] = "primary"
    is_placeholder: bool = False
    sha256: str | None = None
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnswerChoice(StrictModel):
    """A single multiple-choice option."""

    index: int = Field(ge=0)
    text: str = Field(min_length=1)
    # Optional flags used by spurious-cue / action-validity scoring.
    is_spurious_trap: bool = False  # the option the misleading cue suggests
    is_valid_action: bool | None = None  # for action_selection tasks


class VisualCausalTask(StrictModel):
    """A single visually grounded causal-decision task instance.

    The contract enforced by validators:
      * ``family`` and ``split`` are in the controlled vocabularies,
      * the gold answer text never appears in ``question`` (no label leakage),
      * every referenced image exists OR is explicitly a placeholder,
      * intervention/counterfactual families declare the changed factor and the
        expected-answer-change flag,
      * paired tasks carry a ``pair_id`` and a ``condition``.
    """

    task_id: str = Field(min_length=1)
    family: TaskFamily
    split: Split
    domain: str = Field(min_length=1)  # e.g. physical, driving, household, medical
    question: str = Field(min_length=1)

    images: list[VisualAsset] = Field(min_length=1)
    answer_choices: list[AnswerChoice] = Field(min_length=2)
    gold_index: int = Field(ge=0)

    # Causal/intervention annotation -----------------------------------------
    condition: Condition | None = None  # required for paired families
    pair_id: str | None = None  # links the observational/interventional members
    intervention_type: str | None = None  # remove/block/move/replace/occlude/...
    changed_factor: str | None = None  # the single factor altered
    # Whether the correct answer should change vs the paired/observational case.
    expected_answer_change: AnswerChange = "unclear"

    # Free-form / grounded explanation gold (for causal_chain family).
    gold_causal_chain: list[str] = Field(default_factory=list)

    # Provenance / quality.
    is_synthetic: bool = True
    requires_image: bool = True  # must be False only if deliberately a text-control
    human_validated: bool = False
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # --- derived helpers -----------------------------------------------------

    @property
    def gold_choice(self) -> AnswerChoice:
        return self.answer_choices[self.gold_index]

    @property
    def spurious_index(self) -> int | None:
        for choice in self.answer_choices:
            if choice.is_spurious_trap:
                return choice.index
        return None

    @property
    def valid_action_indices(self) -> list[int]:
        return [c.index for c in self.answer_choices if c.is_valid_action]

    # --- structural validation (cheap, schema-level) -------------------------

    @model_validator(mode="after")
    def _check_structure(self) -> VisualCausalTask:
        # answer-choice indices must be 0..n-1 and unique
        indices = [c.index for c in self.answer_choices]
        if sorted(indices) != list(range(len(self.answer_choices))):
            raise ValueError(
                f"answer_choices indices must be 0..{len(self.answer_choices) - 1}; got {indices}"
            )
        texts = [c.text.strip().lower() for c in self.answer_choices]
        if len(set(texts)) != len(texts):
            raise ValueError("answer_choices texts must be unique")
        if self.gold_index >= len(self.answer_choices):
            raise ValueError(
                f"gold_index {self.gold_index} out of range for {len(self.answer_choices)} choices"
            )
        if self.family in PAIRED_FAMILIES and self.pair_id is None:
            raise ValueError(f"family {self.family!r} requires a pair_id")
        if self.family in PAIRED_FAMILIES and self.condition is None:
            raise ValueError(f"family {self.family!r} requires a condition")
        if self.family in ACTION_FAMILIES and not self.valid_action_indices:
            raise ValueError(
                "action_selection tasks must mark at least one choice is_valid_action=True"
            )
        return self


def load_tasks_jsonl(path: str | Path) -> list[VisualCausalTask]:
    """Load and validate a JSONL file of CAB-Vision tasks."""

    tasks: list[VisualCausalTask] = []
    text = Path(path).read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        tasks.append(VisualCausalTask.model_validate(payload))
    return tasks
