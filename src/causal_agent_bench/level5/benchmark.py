"""Governed benchmark authoring DSL and deterministic intervention compiler."""

from __future__ import annotations

import json
import re
from collections import Counter
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.level5.core import canonical_json, content_hash, utc_now


class PrivacyClass(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    PROTECTED = "PROTECTED"


class SplitRole(StrEnum):
    PUBLIC_FIXTURE = "PUBLIC_FIXTURE"
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATION = "VALIDATION"
    CONFIRMATORY = "CONFIRMATORY"
    PROTECTED_EVALUATION = "PROTECTED_EVALUATION"


class TaskLifecycle(StrEnum):
    DRAFT = "DRAFT"
    STATIC_VALIDATED = "STATIC_VALIDATED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    ADJUDICATION_REQUIRED = "ADJUDICATION_REQUIRED"
    C10_ELIGIBLE = "C10_ELIGIBLE"
    FROZEN = "FROZEN"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"
    CONTAMINATED = "CONTAMINATED"


LIFECYCLE_TRANSITIONS: dict[TaskLifecycle, frozenset[TaskLifecycle]] = {
    TaskLifecycle.DRAFT: frozenset({TaskLifecycle.STATIC_VALIDATED}),
    TaskLifecycle.STATIC_VALIDATED: frozenset({TaskLifecycle.HUMAN_REVIEW_REQUIRED}),
    TaskLifecycle.HUMAN_REVIEW_REQUIRED: frozenset(
        {TaskLifecycle.ADJUDICATION_REQUIRED, TaskLifecycle.C10_ELIGIBLE}
    ),
    TaskLifecycle.ADJUDICATION_REQUIRED: frozenset(
        {TaskLifecycle.HUMAN_REVIEW_REQUIRED, TaskLifecycle.C10_ELIGIBLE}
    ),
    TaskLifecycle.C10_ELIGIBLE: frozenset({TaskLifecycle.FROZEN}),
    TaskLifecycle.FROZEN: frozenset({TaskLifecycle.ACTIVE}),
    TaskLifecycle.ACTIVE: frozenset(
        {TaskLifecycle.DEPRECATED, TaskLifecycle.CONTAMINATED}
    ),
    TaskLifecycle.DEPRECATED: frozenset(
        {TaskLifecycle.RETIRED, TaskLifecycle.CONTAMINATED}
    ),
    TaskLifecycle.RETIRED: frozenset(),
    TaskLifecycle.CONTAMINATED: frozenset({TaskLifecycle.RETIRED}),
}


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    description: str
    input_schema: dict[str, Any]

    @model_validator(mode="after")
    def validate_schema(self) -> ToolSpec:
        if self.input_schema.get("type") != "object":
            raise ValueError("tool input_schema.type must be 'object'")
        return self


class AnswerContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(pattern=r"^(exact|string|integer|number|boolean|json)$")
    target_hash: str = Field(min_length=16)
    normalization: str = "strip"


class BaseTaskSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,127}$")
    prompt: str = Field(min_length=1)
    domain: str
    tools: list[ToolSpec] = Field(min_length=1)
    answer_contract: AnswerContract
    gold_source: str
    solvability_contract: str
    scorer_binding: str
    source_id: str
    author_id: str
    licence: str
    privacy_class: PrivacyClass = PrivacyClass.PUBLIC
    split_role: SplitRole = SplitRole.PUBLIC_FIXTURE


class InterventionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intervention_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,127}$")
    family: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    parameters: dict[str, Any]
    mechanism_count: int = Field(default=1, ge=1)
    expected_target_hash: str = Field(min_length=16)
    invariance_contract: str = Field(min_length=1)
    manipulation_check: str = Field(min_length=1)
    expected_opportunity: str = Field(min_length=1)
    prompt_suffix: str = ""
    hidden_fields: dict[str, Any] = Field(default_factory=dict)


class BenchmarkAuthoringSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    benchmark_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,127}$")
    base_task: BaseTaskSpec
    intervention: InterventionSpec

    @classmethod
    def from_path(cls, path: str | Path) -> BenchmarkAuthoringSpec:
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        value = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
        return cls.model_validate(value)


class CompilationReceipt(BaseModel):
    schema_version: str = "1.0"
    benchmark_id: str
    base_task_id: str
    intervention_id: str
    instance_id: str
    base_hash: str
    intervention_hash: str
    public_hash: str
    private_hash: str | None
    compiled_at: str
    compiler_version: str = "cab-level5-1"


class CompiledInstance(BaseModel):
    public: dict[str, Any]
    private: dict[str, Any] | None
    receipt: CompilationReceipt


def compile_intervention(spec: BenchmarkAuthoringSpec) -> CompiledInstance:
    """Compile one authoring spec, rejecting uncontrolled or leaky interventions."""

    task = spec.base_task
    intervention = spec.intervention
    if intervention.mechanism_count != 1:
        raise ValueError("exactly one controlled intervention mechanism is required")
    if intervention.expected_target_hash != task.answer_contract.target_hash:
        raise ValueError("intervention changes the target answer without an answer contract")
    if not intervention.manipulation_check.strip():
        raise ValueError("missing manipulation check")
    tool_names = [tool.name for tool in task.tools]
    if len(tool_names) != len(set(tool_names)):
        raise ValueError("tool role collision: duplicate tool names")
    public_text = canonical_json(
        {
            "prompt": task.prompt,
            "prompt_suffix": intervention.prompt_suffix,
            "manipulation_check": intervention.manipulation_check,
        }
    )
    if task.answer_contract.target_hash in public_text or "gold_answer" in public_text.lower():
        raise ValueError("public answer leakage")
    if task.split_role is SplitRole.CONFIRMATORY and task.privacy_class is PrivacyClass.PUBLIC:
        raise ValueError("confirmatory tasks cannot be authored as public payloads")

    base_hash = content_hash(task.model_dump(mode="json"))
    intervention_hash = content_hash(intervention.model_dump(mode="json"))
    instance_id = f"inst.{content_hash([base_hash, intervention_hash])[:24]}"
    public = {
        "schema_version": spec.schema_version,
        "benchmark_id": spec.benchmark_id,
        "instance_id": instance_id,
        "task_id": task.task_id,
        "domain": task.domain,
        "prompt": f"{task.prompt}{intervention.prompt_suffix}",
        "tools": [tool.model_dump(mode="json") for tool in task.tools],
        "answer_contract": {
            "kind": task.answer_contract.kind,
            "normalization": task.answer_contract.normalization,
        },
        "intervention_family": intervention.family,
        "manipulation_check": intervention.manipulation_check,
        "expected_opportunity": intervention.expected_opportunity,
        "scorer_binding": task.scorer_binding,
        "licence": task.licence,
        "privacy_class": task.privacy_class.value,
        "split_role": task.split_role.value,
    }
    private = (
        {
            "instance_id": instance_id,
            "target_hash": task.answer_contract.target_hash,
            "gold_source": task.gold_source,
            "hidden_fields": intervention.hidden_fields,
        }
        if intervention.hidden_fields or task.privacy_class is not PrivacyClass.PUBLIC
        else None
    )
    receipt = CompilationReceipt(
        benchmark_id=spec.benchmark_id,
        base_task_id=task.task_id,
        intervention_id=intervention.intervention_id,
        instance_id=instance_id,
        base_hash=base_hash,
        intervention_hash=intervention_hash,
        public_hash=content_hash(public),
        private_hash=content_hash(private) if private is not None else None,
        compiled_at=utc_now(),
    )
    return CompiledInstance(public=public, private=private, receipt=receipt)


def advance_lifecycle(current: TaskLifecycle, target: TaskLifecycle) -> TaskLifecycle:
    if target not in LIFECYCLE_TRANSITIONS[current]:
        raise ValueError(f"illegal task lifecycle transition: {current.value} -> {target.value}")
    return target


def _normalise_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", value.lower())).strip()


def diversity_report(instances: list[dict[str, Any]]) -> dict[str, Any]:
    """Return deterministic, offline diversity and duplicate diagnostics."""

    texts = [str(instance.get("prompt", "")) for instance in instances]
    exact = [text for text, count in Counter(texts).items() if count > 1]
    normalised = [_normalise_text(text) for text in texts]
    normalised_duplicates = [
        text for text, count in Counter(normalised).items() if count > 1
    ]
    dimensions = {
        name: dict(sorted(Counter(str(row.get(name, "UNKNOWN")) for row in instances).items()))
        for name in (
            "domain",
            "intervention_family",
            "split_role",
            "scorer_binding",
            "privacy_class",
        )
    }
    structural_fingerprints = [
        content_hash(
            {
                "tools": sorted(tool.get("name", "") for tool in row.get("tools", [])),
                "answer_kind": row.get("answer_contract", {}).get("kind"),
                "family": row.get("intervention_family"),
            }
        )
        for row in instances
    ]
    return {
        "count": len(instances),
        "exact_duplicates": sorted(exact),
        "normalised_duplicates": sorted(normalised_duplicates),
        "structural_duplicate_count": sum(
            count - 1 for count in Counter(structural_fingerprints).values() if count > 1
        ),
        "dimensions": dimensions,
        "semantic_plugin": "OPTIONAL_NOT_LOADED",
        "passed": not exact and not normalised_duplicates,
    }


def build_review_packet(compiled: list[CompiledInstance]) -> dict[str, Any]:
    """Build a blinded packet containing no target hashes or private payloads."""

    items = [
        {
            "review_item_id": f"review.{content_hash(item.public)[:24]}",
            "instance": item.public,
            "checks": {
                "invariance": None,
                "manipulation": None,
                "solvability": None,
                "notes": "",
            },
        }
        for item in sorted(compiled, key=lambda value: value.receipt.instance_id)
    ]
    return {
        "schema_version": "1.0",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "blinded": True,
        "items": items,
        "coverage": {"required_reviews_per_item": 2, "item_count": len(items)},
    }


def write_compilation(
    compiled: CompiledInstance,
    output_dir: str | Path,
    *,
    allow_private: bool = False,
) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    public_path = output / "instance.public.json"
    receipt_path = output / "compilation_receipt.json"
    public_path.write_text(
        json.dumps(compiled.public, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt_path.write_text(
        compiled.receipt.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    paths = [public_path, receipt_path]
    if allow_private and compiled.private is not None:
        private_path = output / "instance.private.json"
        private_path.write_text(
            json.dumps(compiled.private, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        paths.append(private_path)
    return paths


__all__ = [
    "AnswerContract",
    "BaseTaskSpec",
    "BenchmarkAuthoringSpec",
    "CompilationReceipt",
    "CompiledInstance",
    "InterventionSpec",
    "PrivacyClass",
    "SplitRole",
    "TaskLifecycle",
    "ToolSpec",
    "advance_lifecycle",
    "build_review_packet",
    "compile_intervention",
    "diversity_report",
    "write_compilation",
]
