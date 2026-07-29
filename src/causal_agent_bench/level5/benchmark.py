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
from causal_agent_bench.level5.registry import SQLiteRegistry

MAX_AUTHORING_BYTES = 1_000_000
MAX_AUTHORING_DEPTH = 16
MAX_AUTHORING_NODES = 10_000
MAX_SCHEMA_PROPERTIES = 128


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
        _validate_bounded_value(self.input_schema, context=f"tool {self.name} schema")
        properties = self.input_schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ValueError("tool input_schema.properties must be an object")
        if len(properties) > MAX_SCHEMA_PROPERTIES:
            raise ValueError("tool input_schema has too many properties")
        if any(
            isinstance(value, str)
            and (
                value.startswith(("http://", "https://", "file://"))
                or ".." in value.split("/")
            )
            for key, value in _walk_pairs(self.input_schema)
            if key in {"$ref", "$id"}
        ):
            raise ValueError("remote or traversal schema references are forbidden")
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
    difficulty: str = Field(default="UNSPECIFIED", max_length=64)


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
        raw = path.read_bytes()
        if len(raw) > MAX_AUTHORING_BYTES:
            raise ValueError(
                f"authoring file exceeds {MAX_AUTHORING_BYTES} byte safety limit"
            )
        text = raw.decode("utf-8")
        if path.suffix.lower() == ".json":
            value = json.loads(text)
        else:
            documents = list(yaml.safe_load_all(text))
            if len(documents) != 1:
                raise ValueError("authoring YAML must contain exactly one document")
            value = documents[0]
        _validate_bounded_value(value, context="authoring document")
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


def _walk_pairs(value: Any) -> list[tuple[str, Any]]:
    pairs: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            pairs.append((str(key), item))
            pairs.extend(_walk_pairs(item))
    elif isinstance(value, list):
        for item in value:
            pairs.extend(_walk_pairs(item))
    return pairs


def _validate_bounded_value(value: Any, *, context: str) -> None:
    """Reject parser-amplification and deeply nested authoring payloads."""

    seen: set[int] = set()
    node_count = 0

    def visit(item: Any, depth: int) -> None:
        nonlocal node_count
        node_count += 1
        if node_count > MAX_AUTHORING_NODES:
            raise ValueError(f"{context} exceeds the node-count safety limit")
        if depth > MAX_AUTHORING_DEPTH:
            raise ValueError(f"{context} exceeds the nesting-depth safety limit")
        if isinstance(item, (dict, list)):
            identity = id(item)
            if identity in seen:
                raise ValueError(f"{context} contains aliases or recursive structures")
            seen.add(identity)
            values = item.values() if isinstance(item, dict) else item
            for child in values:
                visit(child, depth + 1)
        elif isinstance(item, str) and len(item.encode("utf-8")) > MAX_AUTHORING_BYTES:
            raise ValueError(f"{context} contains an oversized string")

    visit(value, 0)


def _validate_scorer_tool_contract(task: BaseTaskSpec) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_.-]{2,127}(?::[a-z0-9_.-]+)?", task.scorer_binding):
        raise ValueError("scorer_binding must be a versionable, typed identifier")
    answer_kind = task.answer_contract.kind
    if answer_kind == "json" and not any(
        tool.input_schema.get("type") == "object" for tool in task.tools
    ):
        raise ValueError("JSON answer contracts require an object-capable tool")
    if task.answer_contract.normalization not in {
        "strip",
        "lower_strip",
        "canonical_json",
        "integer",
        "number",
        "boolean",
    }:
        raise ValueError("unknown answer normalization contract")
    if task.answer_contract.normalization == "canonical_json" and answer_kind != "json":
        raise ValueError("canonical_json normalization requires a JSON answer contract")


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
    _validate_scorer_tool_contract(task)
    if not re.fullmatch(
        r"[a-z][a-z0-9_.-]{2,127}(?::[a-z0-9_.-]+)?",
        intervention.manipulation_check,
    ):
        raise ValueError("manipulation_check must name a deterministic fixture contract")
    if set(intervention.hidden_fields).intersection(
        {"prompt", "tools", "answer_contract", "target_hash", "gold_answer"}
    ):
        raise ValueError("hidden fields collide with governed public or answer fields")
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
        "source_id": task.source_id,
        "author_id": task.author_id,
        "difficulty": task.difficulty,
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


class BenchmarkRepository:
    """Append-only benchmark provenance and lifecycle records in the CAB registry."""

    def __init__(self, registry: SQLiteRegistry) -> None:
        self.registry = registry
        self.registry.initialize()

    def record_compilation(self, compiled: CompiledInstance) -> str:
        payload = {
            "public": compiled.public,
            "receipt": compiled.receipt.model_dump(mode="json"),
            "private_commitment": compiled.receipt.private_hash,
        }
        return self._append(
            compiled.receipt.benchmark_id,
            "COMPILATION",
            payload,
            TaskLifecycle.STATIC_VALIDATED,
            public=True,
        )

    def transition(
        self,
        benchmark_id: str,
        current: TaskLifecycle,
        target: TaskLifecycle,
        *,
        evidence: dict[str, Any],
    ) -> str:
        advance_lifecycle(current, target)
        if target in {TaskLifecycle.C10_ELIGIBLE, TaskLifecycle.FROZEN} and not evidence.get(
            "active_certificate_ids"
        ):
            raise ValueError("certified review evidence is required for this transition")
        return self._append(
            benchmark_id,
            "LIFECYCLE_TRANSITION",
            {
                "from": current.value,
                "to": target.value,
                "evidence": evidence,
            },
            target,
            public=True,
        )

    def records(self, benchmark_id: str) -> list[dict[str, Any]]:
        with self.registry._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM benchmark_records
                WHERE benchmark_id = ?
                ORDER BY created_at, record_id
                """,
                (benchmark_id,),
            ).fetchall()
        return [
            {
                **dict(row),
                "payload": json.loads(str(row["payload_json"])),
                "public": bool(row["public"]),
            }
            for row in rows
        ]

    def _append(
        self,
        benchmark_id: str,
        record_type: str,
        payload: dict[str, Any],
        lifecycle: TaskLifecycle,
        *,
        public: bool,
    ) -> str:
        payload_json = canonical_json(payload)
        payload_hash = content_hash(payload)
        record_id = f"benchmark.{content_hash([benchmark_id, record_type, payload_hash])[:24]}"
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO benchmark_records(
                    record_id, benchmark_id, record_type, payload_json, payload_hash,
                    lifecycle, public, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    benchmark_id,
                    record_type,
                    payload_json,
                    payload_hash,
                    lifecycle.value,
                    int(public),
                    utc_now(),
                ),
            )
            row = connection.execute(
                "SELECT payload_hash FROM benchmark_records WHERE record_id = ?",
                (record_id,),
            ).fetchone()
            if row is None or row["payload_hash"] != payload_hash:
                raise RuntimeError("benchmark record idempotency collision")
        return record_id


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
    dimension_names = (
        "domain",
        "intervention_family",
        "split_role",
        "scorer_binding",
        "privacy_class",
        "source_id",
        "author_id",
        "difficulty",
    )
    dimensions = {
        name: dict(sorted(Counter(str(row.get(name, "UNKNOWN")) for row in instances).items()))
        for name in dimension_names
    }
    dimensions["answer_kind"] = dict(
        sorted(
            Counter(
                str(row.get("answer_contract", {}).get("kind", "UNKNOWN"))
                for row in instances
            ).items()
        )
    )
    dimensions["tool_family"] = dict(
        sorted(
            Counter(
                str(tool.get("name", "UNKNOWN"))
                for row in instances
                for tool in row.get("tools", [])
            ).items()
        )
    )
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
    concentration = {
        name: (
            max(counts.values()) / sum(counts.values())
            if counts and sum(counts.values())
            else 0.0
        )
        for name, counts in dimensions.items()
    }
    split_commitment = content_hash(
        sorted(
            (
                str(row.get("instance_id", "")),
                str(row.get("split_role", "UNKNOWN")),
                str(row.get("privacy_class", "UNKNOWN")),
            )
            for row in instances
        )
    )
    failures = []
    if exact:
        failures.append("EXACT_DUPLICATES")
    if normalised_duplicates:
        failures.append("NORMALISED_DUPLICATES")
    if len(instances) >= 4:
        failures.extend(
            f"{name.upper()}_CONCENTRATION"
            for name, ratio in concentration.items()
            if name in {"domain", "source_id", "author_id", "intervention_family"}
            and ratio > 0.75
        )
    return {
        "count": len(instances),
        "exact_duplicates": sorted(exact),
        "normalised_duplicates": sorted(normalised_duplicates),
        "structural_duplicate_count": sum(
            count - 1 for count in Counter(structural_fingerprints).values() if count > 1
        ),
        "dimensions": dimensions,
        "concentration": concentration,
        "split_commitment": split_commitment,
        "failures": sorted(failures),
        "semantic_plugin": "OPTIONAL_NOT_LOADED",
        "passed": not failures,
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
    "BenchmarkRepository",
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
