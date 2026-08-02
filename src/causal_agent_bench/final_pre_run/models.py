"""Strict data contracts for the private Compact-20 replacement."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PrimitiveArtifact(StrictModel):
    artifact_id: str = Field(min_length=8)
    domain: str
    media_type: Literal["application/json", "text/plain"]
    records: dict[str, Any]


class Stage1Candidate(StrictModel):
    candidate_id: str = Field(min_length=16)
    task_id: str = Field(min_length=16)
    family: Literal[
        "tool_removal", "tool_failure", "memory_corruption", "observation_conflict"
    ]
    domain: Literal[
        "travel",
        "shopping",
        "spreadsheet",
        "research",
        "coding",
        "policy",
        "calendar",
        "operations",
    ]
    difficulty: Literal["easy", "medium", "hard", "stress"]
    deliberate_anchor: bool
    prompt: str
    declared_tools: list[str] = Field(min_length=1)
    artifact: PrimitiveArtifact


class Stage2Record(StrictModel):
    candidate_id: str
    task_id: str
    family: str
    route_kind: Literal["completion", "recovery", "clarification", "abstention"]
    expected_answer: str
    expected_answer_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    missing_variable: str | None = None
    clarification_question: str | None = None
    primary_tool: str
    fallback_tool: str | None = None
    authorized_action_id: str | None = None


class ExtractedFact(StrictModel):
    fact_id: str
    source_artifact_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_locator: str
    observed_value: Any
    normalized_value: Any
    extraction_rule: str
    confidence_or_deterministic_status: Literal["deterministic"] = "deterministic"


class ToolCallReceipt(StrictModel):
    call_id: str
    candidate_id: str
    tool_name: str
    arguments: dict[str, Any]
    artifact_hash: str
    status: Literal["success", "failure"]
    failure_class: str | None = None
    observation: dict[str, Any]


class RecoveryAttemptReceipt(StrictModel):
    attempt_id: str
    failure_event_id: str
    action_id: str
    tool_name: str
    arguments: dict[str, Any]
    observation: dict[str, Any]
    fact_ids: list[str]
    success_predicate: dict[str, Any]
    budget: int = Field(ge=0)
    temporal_order: int = Field(ge=0)
    passed: bool


class RouteProof(StrictModel):
    candidate_id: str
    route_kind: Literal["completion", "recovery", "clarification", "abstention"]
    edges: list[dict[str, Any]]
    extracted_fact_ids: list[str]
    derived_answer: str
    route_inventory: list[dict[str, Any]]
    attempts: list[RecoveryAttemptReceipt] = Field(default_factory=list)
    passed: bool
