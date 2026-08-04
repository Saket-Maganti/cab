"""Strict contracts for the paired Compact-20 V2 scientific kernel.

The unit of evaluation is a *pair*: one base task instantiated as a clean
instance and as an intervention instance produced by applying exactly one
executable environment operator to the clean instance.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Family = Literal["tool_removal", "tool_failure", "memory_corruption", "observation_conflict"]
Route = Literal["completion", "recovery", "clarification", "abstention"]
Domain = Literal[
    "travel",
    "shopping",
    "spreadsheet",
    "research",
    "coding",
    "policy",
    "calendar",
    "operations",
]
Difficulty = Literal["easy", "medium", "hard", "stress"]
Capability = Literal[
    "collection_read", "record_lookup", "memory_read", "document_read", "indexed_lookup"
]
Authorization = Literal["standard", "recovery_only"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolContract(StrictModel):
    """A capability-bounded tool.

    Every tool is scoped to exactly one named source in the environment and to a
    declared field projection.  No tool may return an entire artifact, and there
    is no general-purpose file reader in the scientific route.
    """

    tool_id: str = Field(min_length=3)
    declared_capability: Capability
    scope_source: str = Field(min_length=1)
    allowed_arguments: list[str] = Field(default_factory=list)
    argument_bindings: dict[str, str] = Field(default_factory=dict)
    returned_fields: list[str] = Field(min_length=1)
    failure_modes: list[str] = Field(min_length=1)
    authorization_scope: Authorization = "standard"
    provides_inputs: list[str] = Field(min_length=1)

    @property
    def trust_key(self) -> str:
        return f"memory:{self.scope_source}" if self.declared_capability == "memory_read" else self.scope_source


class EnvironmentState(StrictModel):
    """A fully instantiated task environment."""

    goal: str = Field(min_length=10)
    sources: dict[str, Any]
    memory: dict[str, Any] = Field(default_factory=dict)
    source_trust: dict[str, int] = Field(default_factory=dict)
    tools: list[ToolContract] = Field(min_length=1)
    injected_failures: dict[str, str] = Field(default_factory=dict)

    def tool(self, tool_id: str) -> ToolContract | None:
        for contract in self.tools:
            if contract.tool_id == tool_id:
                return contract
        return None


class InterventionPatch(StrictModel):
    """The declared, enumerable mutation an operator applies."""

    operator: Literal[
        "remove_tool", "inject_tool_failure", "corrupt_memory_field", "inject_conflicting_observation"
    ]
    intended_changed_factor: str
    target_locators: list[str] = Field(min_length=1)
    before: dict[str, Any]
    after: dict[str, Any]
    rationale: str


class Observation(StrictModel):
    """A real tool observation. Never carries gold, route labels, or fact hints."""

    call_id: str
    tool_id: str
    arguments: dict[str, Any]
    status: Literal["success", "failure"]
    failure_class: str | None = None
    source_ref: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    step_index: int = Field(ge=0)


class DerivedFact(StrictModel):
    fact_id: str
    input_key: str
    source_locator: str
    observed_value: Any
    from_call_id: str
    extraction_rule: str = "scoped_projection_v2"


class RecoveryReceipt(StrictModel):
    attempt_id: str
    failure_event_id: str
    authorized_action_id: str
    tool_id: str
    arguments: dict[str, Any]
    failure_step_index: int = Field(ge=0)
    attempt_step_index: int = Field(ge=0)
    budget_remaining: int = Field(ge=0)
    supplied_input_keys: list[str]
    observation_call_id: str
    passed: bool
    reasons: list[str] = Field(default_factory=list)


class RouteProof(StrictModel):
    pair_id: str
    instance: Literal["clean", "intervention"]
    route_kind: Route
    observations: list[Observation]
    facts: list[DerivedFact]
    route_inventory: list[dict[str, Any]]
    derived_answer: str | None = None
    clarification_target: str | None = None
    abstention_reason: str | None = None
    recovery: RecoveryReceipt | None = None
    hidden_gold_visible_during_derivation: bool = False
    undeclared_oracle_used: bool = False
    checks: dict[str, bool] = Field(default_factory=dict)
    passed: bool


class AnchorSpec(StrictModel):
    anchor_group_id: str
    anchor_source_pair_id: str
    allowed_nuisance_differences: list[str] = Field(min_length=1)
    forbidden_semantic_differences: list[str] = Field(min_length=1)


class PairSpec(StrictModel):
    """The private machine-readable specification for one evaluation pair."""

    pair_id: str
    base_task_id: str
    semantic_objective_id: str
    task_archetype: str
    domain: Domain
    difficulty: Difficulty
    intervention_family: Family
    route_requirement_clean: Route
    route_requirement_intervention: Route
    anchor: AnchorSpec | None = None
    clean_instance_id: str
    intervention_instance_id: str
    shared_goal: str
    clean_prompt: str
    intervention_prompt: str
    clean_environment: EnvironmentState
    intervention_environment: EnvironmentState
    primitive_evidence_manifest: dict[str, list[str]]
    declared_tool_contracts: list[ToolContract]
    intervention_operator: str
    intervention_patch: InterventionPatch
    intended_changed_factor: str
    preserved_invariants: list[str] = Field(min_length=1)
    required_input_keys: list[str] = Field(min_length=1)
    counterparty: str
    counterparty_resolvable_inputs: list[str] = Field(default_factory=list)
    # --- private-only fields: never enter Stage 1 -------------------------------
    clean_gold_private: str
    intervention_gold_or_policy_private: str
    clean_answer_contract_private: dict[str, Any]
    intervention_answer_contract_private: dict[str, Any]
    clean_scorer_contract_private: dict[str, Any]
    intervention_scorer_contract_private: dict[str, Any]
    recovery_authorization_private: dict[str, Any] | None = None
    abstention_opportunity_private: dict[str, Any] | None = None
    clarification_requirement_private: dict[str, Any] | None = None


PRIVATE_PAIR_FIELDS = (
    "clean_gold_private",
    "intervention_gold_or_policy_private",
    "clean_answer_contract_private",
    "intervention_answer_contract_private",
    "clean_scorer_contract_private",
    "intervention_scorer_contract_private",
    "recovery_authorization_private",
    "abstention_opportunity_private",
    "clarification_requirement_private",
    "route_requirement_clean",
    "route_requirement_intervention",
)
"""Fields that must never be serialized into a Stage-1 reviewer package."""


__all__ = [
    "PRIVATE_PAIR_FIELDS",
    "AnchorSpec",
    "Capability",
    "DerivedFact",
    "Difficulty",
    "Domain",
    "EnvironmentState",
    "Family",
    "InterventionPatch",
    "Observation",
    "PairSpec",
    "RecoveryReceipt",
    "Route",
    "RouteProof",
    "StrictModel",
    "ToolContract",
]
