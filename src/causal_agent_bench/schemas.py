from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.answer_contracts import (
    AnswerContract,
    GoldAnswerPolicy,
    ScorerPolicy,
)

InterventionType = Literal[
    "tool_removal",
    "tool_failure",
    "tool_corruption",
    "irrelevant_tools",
    "memory_corruption",
    "observation_conflict",
    "ambiguous_instruction",
    "long_horizon_dependency",
    "premature_success_signal",
    "distractor_evidence",
    "web_broken_link",
    "web_stale_page",
    "web_conflicting_page",
    "web_irrelevant_search_result",
    "web_hidden_evidence",
]

ConditionType = Literal["clean", "intervention"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolSpec(StrictModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    failure_modes: list[str] = Field(default_factory=list)
    is_available: bool = True


class ToolCall(StrictModel):
    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    timestamp_step: int | None = Field(default=None, ge=0)
    call_id: str | None = None


ParserOutcome = Literal[
    "valid_tool_call",
    "valid_final_answer",
    "clarification",
    "invalid_json",
    "unknown_tool",
    "invalid_argument_schema",
    "multiple_tool_calls",
    "missing_action",
    "repeated_failed_call",
    "final_answer_without_required_evidence",
]


class ToolCallParseResult(StrictModel):
    """Auditable parse record for raw LLM action output."""

    raw_output: str | None = None
    repaired_json: dict[str, Any] | list[Any] | None = None
    action_type: Literal["tool_call", "final_answer", "clarification", "invalid"] = "invalid"
    outcome: ParserOutcome
    is_valid: bool
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    final_answer: str | None = None
    explanation: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolObservation(StrictModel):
    tool_name: str = Field(min_length=1)
    call_id: str | None = None
    output: dict[str, Any] | str | None = None
    error: str | None = None
    is_corrupted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_observation(cls, data: Any) -> Any:
        if isinstance(data, dict) and "ok" in data:
            data = dict(data)
            data.pop("ok", None)
        return data

    @property
    def ok(self) -> bool:
        return self.error is None


class AgentAction(StrictModel):
    thought: str | None = None
    tool_call: ToolCall | None = None
    final_answer: str | None = None
    stop: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_action(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "kind" not in data and "rationale" not in data:
            return data
        normalized = dict(data)
        kind = normalized.pop("kind", None)
        rationale = normalized.pop("rationale", None)
        if rationale is not None and "thought" not in normalized:
            normalized["thought"] = rationale
        if kind == "final_answer" and "stop" not in normalized:
            normalized["stop"] = True
        return normalized

    @model_validator(mode="after")
    def check_action_payload(self) -> AgentAction:
        has_tool = self.tool_call is not None
        has_answer = self.final_answer is not None
        final_with_tool_summary = (
            self.metadata.get("action_type") == "final-with-tool-summary"
            or self.metadata.get("final-with-tool-summary") is True
            or self.metadata.get("final_with_tool_summary") is True
        )
        if has_tool and has_answer and not final_with_tool_summary:
            raise ValueError(
                "AgentAction cannot contain both tool_call and final_answer unless metadata marks "
                "the action as final-with-tool-summary"
            )
        if not has_tool and not has_answer and not self.stop:
            raise ValueError("AgentAction requires a tool_call, final_answer, or stop=True")
        return self

    @property
    def kind(self) -> Literal["tool_call", "final_answer"]:
        if self.tool_call is not None and self.final_answer is None:
            return "tool_call"
        return "final_answer"

    @property
    def rationale(self) -> str | None:
        return self.thought


class TaskGoal(StrictModel):
    user_instruction: str = Field(min_length=1)
    success_criteria: list[str] = Field(min_length=1)
    required_information: list[str] = Field(default_factory=list)
    forbidden_assumptions: list[str] = Field(default_factory=list)
    expected_final_answer: Any = None


class BaseTask(StrictModel):
    task_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)
    goal: TaskGoal
    user_instruction: str | None = None
    success_criteria: list[str] = Field(default_factory=list)
    forbidden_assumptions: list[str] = Field(default_factory=list)
    available_tools: list[str] = Field(min_length=1)
    required_tools: list[str] = Field(default_factory=list)
    optional_tools: list[str] = Field(default_factory=list)
    hidden_ground_truth: dict[str, Any] = Field(default_factory=dict)
    gold_tool_sequence: list[str] | None = None
    expected_output_schema: dict[str, Any] = Field(default_factory=dict)
    answer_contract: AnswerContract | None = None
    gold_answer_policy: GoldAnswerPolicy | None = None
    scorer_policy: ScorerPolicy | None = None
    ambiguity_policy: dict[str, Any] = Field(default_factory=dict)
    abstention_policy: dict[str, Any] = Field(default_factory=dict)
    partial_credit_criteria: list[str] = Field(default_factory=list)
    expected_evidence: list[str] = Field(default_factory=list)
    max_steps: int = Field(gt=0)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_tool_sequence(self) -> BaseTask:
        if self.user_instruction is None:
            self.user_instruction = self.goal.user_instruction
        if not self.success_criteria:
            self.success_criteria = list(self.goal.success_criteria)
        if not self.forbidden_assumptions:
            self.forbidden_assumptions = list(self.goal.forbidden_assumptions)
        if len(set(self.available_tools)) != len(self.available_tools):
            raise ValueError("available_tools must not contain duplicates")
        if self.gold_tool_sequence is not None:
            missing = [tool for tool in self.gold_tool_sequence if tool not in self.available_tools]
            if missing:
                raise ValueError(f"gold_tool_sequence references unavailable tools: {missing}")
        return self


class InterventionSpec(StrictModel):
    intervention_id: str = Field(min_length=1)
    base_task_id: str = Field(min_length=1)
    family: InterventionType
    description: str = Field(min_length=1)
    changed_factor: str = Field(min_length=1)
    expected_behavior: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    target_factor: str | None = None
    non_target_factors: list[str] = Field(default_factory=list)
    acceptable_severity_range: list[str] = Field(default_factory=list)
    invalid_examples: list[str] = Field(default_factory=list)
    tool_availability_patch: dict[str, Any] = Field(default_factory=dict)
    memory_patch: dict[str, Any] = Field(default_factory=dict)
    tool_output_patch: dict[str, Any] = Field(default_factory=dict)
    instruction_patch: str | None = None
    patch_details: dict[str, Any] = Field(default_factory=dict)
    expected_robust_behavior: str | None = None
    expected_final_answer_change: Literal["yes", "no", "unclear"] = "no"
    intervention_validity_risk: str = "medium"
    scoring_notes: str = ""
    answer_contract: AnswerContract | None = None
    gold_answer_policy: GoldAnswerPolicy | None = None
    scorer_policy: ScorerPolicy | None = None
    valid_recovery_routes: list[str] = Field(default_factory=list)
    acceptable_abstention_conditions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_intervention(cls, data: Any) -> Any:
        if not isinstance(data, dict) or "family" in data:
            return data
        if "type" not in data:
            return data
        params = data.get("params", {})
        family = data["type"]
        intervention_id = data.get("intervention_id", f"unknown.{family}")
        base_task_id = data.get("base_task_id") or str(intervention_id).split(".")[0]
        tool_availability_patch: dict[str, Any] = {}
        memory_patch: dict[str, Any] = {}
        tool_output_patch: dict[str, Any] = {}
        instruction_patch = data.get("instruction_patch")
        if family == "tool_removal":
            tool_availability_patch = {"removed_tools": params.get("removed_tools", [])}
        elif family == "irrelevant_tools":
            tool_availability_patch = {"added_tools": params.get("added_tools", [])}
        elif family in {"tool_failure", "tool_corruption"}:
            tool_output_patch = params
        elif family == "memory_corruption":
            memory_patch = params
        elif family == "ambiguous_instruction":
            instruction_patch = params.get("ambiguity", "ambiguous instruction")
        else:
            tool_output_patch = params
        return {
            "intervention_id": intervention_id,
            "base_task_id": base_task_id,
            "family": family,
            "description": data.get("description", f"Legacy {family} intervention."),
            "changed_factor": data.get("changed_factor", family),
            "expected_behavior": data.get("expected_behavior", "Agent should adapt to the intervention."),
            "severity": data.get("severity", "medium"),
            "target_factor": data.get("target_factor"),
            "non_target_factors": data.get("non_target_factors", []),
            "acceptable_severity_range": data.get("acceptable_severity_range", []),
            "invalid_examples": data.get("invalid_examples", []),
            "tool_availability_patch": tool_availability_patch,
            "memory_patch": memory_patch,
            "tool_output_patch": tool_output_patch,
            "instruction_patch": instruction_patch,
            "patch_details": {
                "tool_availability_patch": tool_availability_patch,
                "memory_patch": memory_patch,
                "tool_output_patch": tool_output_patch,
                "instruction_patch": instruction_patch,
            },
            "expected_robust_behavior": data.get(
                "expected_robust_behavior",
                data.get("expected_behavior", "Agent should adapt to the intervention."),
            ),
            "expected_final_answer_change": data.get("expected_final_answer_change", "unclear"),
            "intervention_validity_risk": data.get("intervention_validity_risk", "medium"),
            "scoring_notes": data.get("scoring_notes", "Legacy intervention; scoring notes unavailable."),
            "metadata": {**data.get("metadata", {}), "legacy_params": params},
        }

    @property
    def type(self) -> InterventionType:
        return self.family

    @property
    def params(self) -> dict[str, Any]:
        if "legacy_params" in self.metadata:
            legacy = self.metadata["legacy_params"]
            return legacy if isinstance(legacy, dict) else {}
        return {
            **self.tool_availability_patch,
            **self.memory_patch,
            **self.tool_output_patch,
            **({"instruction_patch": self.instruction_patch} if self.instruction_patch else {}),
        }


class BenchmarkInstance(StrictModel):
    instance_id: str = Field(min_length=1)
    base_task: BaseTask
    condition: ConditionType
    intervention: InterventionSpec | None = None
    available_tools: list[str] = Field(min_length=1)
    initial_memory: dict[str, Any] = Field(default_factory=dict)
    environment_seed: int
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_condition_and_linkage(self) -> BenchmarkInstance:
        if len(set(self.available_tools)) != len(self.available_tools):
            raise ValueError("available_tools must not contain duplicates")
        if self.condition == "clean" and self.intervention is not None:
            raise ValueError("clean BenchmarkInstance must not include an intervention")
        if self.condition == "intervention":
            if self.intervention is None:
                raise ValueError("intervention BenchmarkInstance requires intervention")
            if self.intervention.base_task_id != self.base_task.task_id:
                raise ValueError(
                    "intervention.base_task_id must match benchmark instance base_task.task_id"
                )
        return self


class Trajectory(StrictModel):
    schema_version: str = "trajectory_v2"
    run_id: str = Field(min_length=1)
    instance_id: str = Field(min_length=1)
    base_task_id: str | None = None
    intervention_id: str | None = None
    agent_id: str | None = None
    agent_name: str = Field(min_length=1)
    model_name: str | None = None
    provider_model_metadata: dict[str, Any] = Field(default_factory=dict)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    final_answer: str | None = None
    terminated_reason: str = Field(min_length=1)
    stop_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    token_cost_metadata: dict[str, Any] = Field(default_factory=dict)
    raac_metadata: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_trajectory(cls, data: Any) -> Any:
        if not isinstance(data, dict) or "task_id" not in data:
            return data
        normalized = dict(data)
        task_id = normalized.pop("task_id")
        seed = normalized.pop("seed", None)
        success = normalized.pop("success", None)
        metrics = normalized.pop("metrics", None)
        metadata = dict(normalized.get("metadata", {}))
        if seed is not None:
            metadata["seed"] = seed
        if success is not None:
            metadata["success"] = success
        if metrics is not None:
            metadata["metrics"] = metrics
        normalized["metadata"] = metadata
        normalized.setdefault("run_id", metadata.get("run_id", "legacy"))
        normalized.setdefault("instance_id", task_id)
        normalized.setdefault("model_name", None)
        normalized.setdefault("terminated_reason", "unknown")
        return normalized

    @model_validator(mode="after")
    def populate_v2_fields(self) -> Trajectory:
        if self.base_task_id is None:
            value = self.metadata.get("base_task_id") or self.metadata.get("task_id")
            self.base_task_id = str(value) if value is not None else self.instance_id
        if self.intervention_id is None and self.metadata.get("intervention_id") is not None:
            self.intervention_id = str(self.metadata["intervention_id"])
        if self.agent_id is None:
            self.agent_id = self.metadata.get("agent_id") or self.agent_name
        if self.stop_reason is None:
            self.stop_reason = self.terminated_reason
        if not self.provider_model_metadata:
            self.provider_model_metadata = {
                key: value
                for key, value in {
                    "provider": self.metadata.get("provider"),
                    "model": self.metadata.get("model") or self.model_name,
                    "model_name": self.model_name,
                    "agent_type": self.metadata.get("agent_type"),
                    "prompt_hash": self.metadata.get("prompt_hash"),
                    "prompt_version_hash": self.metadata.get("prompt_version_hash"),
                }.items()
                if value is not None
            }
        if not self.token_cost_metadata:
            self.token_cost_metadata = {
                key: value
                for key, value in {
                    "token_usage": self.metadata.get("token_usage"),
                    "estimated_cost_usd": self.metadata.get("estimated_cost_usd"),
                    "latency_s": self.metadata.get("latency_s"),
                    "retry_count": self.metadata.get("retry_count"),
                    "llm_calls": self.metadata.get("llm_calls"),
                }.items()
                if value is not None
            }
        if not self.raac_metadata and isinstance(self.metadata.get("raac"), dict):
            self.raac_metadata = dict(self.metadata["raac"])
        return self

    @property
    def success(self) -> bool | None:
        value = self.metadata.get("success")
        return value if isinstance(value, bool) else None

    @property
    def metrics(self) -> dict[str, float | int | None]:
        metrics = self.metadata.get("metrics", {})
        return metrics if isinstance(metrics, dict) else {}

    @property
    def task_id(self) -> str:
        return self.instance_id

    @property
    def seed(self) -> int:
        seed = self.metadata.get("seed")
        return int(seed) if seed is not None else 0


class ScoreRecord(StrictModel):
    run_id: str = Field(min_length=1)
    instance_id: str = Field(min_length=1)
    agent_name: str = Field(min_length=1)
    metrics: dict[str, float | int | bool | str | None] = Field(default_factory=dict)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrajectoryStep(StrictModel):
    index: int = Field(ge=0)
    action: AgentAction
    observation: ToolObservation | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    raw_model_output: str | None = None
    parsed_action: dict[str, Any] | None = None
    step_index: int | None = Field(default=None, ge=0)
    tool_call: ToolCall | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    tool_result: ToolObservation | None = None
    parser_status: str | None = None
    tool_error_status: str | None = None
    recovery_marker: bool | str | None = None
    contradiction_marker: bool | str | None = None
    memory_use_marker: bool | str | None = None
    final_answer: str | None = None
    stop_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    token_cost_metadata: dict[str, Any] = Field(default_factory=dict)
    raac_state: str | None = None
    raac_decision: str | None = None
    raac_signals: list[str] = Field(default_factory=list)
    raac_trace_index: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def populate_v2_step_fields(self) -> TrajectoryStep:
        if self.step_index is None:
            self.step_index = self.index
        if self.tool_call is None and self.action.tool_call is not None:
            self.tool_call = self.action.tool_call
        if not self.tool_arguments and self.tool_call is not None:
            self.tool_arguments = dict(self.tool_call.arguments)
        if self.tool_result is None and self.observation is not None:
            self.tool_result = self.observation
        action_metadata = self.action.metadata
        if self.parser_status is None:
            parsed_outcome = None
            if isinstance(self.parsed_action, dict):
                parsed_outcome = self.parsed_action.get("outcome")
            self.parser_status = (
                action_metadata.get("parser_outcome") or parsed_outcome or "not_applicable"
            )
        if self.tool_error_status is None:
            self.tool_error_status = _derive_tool_error_status(
                action_metadata=action_metadata,
                observation=self.observation,
                has_tool_call=self.tool_call is not None,
            )
        if self.recovery_marker is None:
            self.recovery_marker = action_metadata.get("recovery_marker")
        if self.contradiction_marker is None:
            self.contradiction_marker = action_metadata.get("contradiction_marker")
        if self.memory_use_marker is None:
            self.memory_use_marker = action_metadata.get("memory_use_marker")
        if self.final_answer is None:
            self.final_answer = self.action.final_answer
        if not self.token_cost_metadata:
            self.token_cost_metadata = {
                key: value
                for key, value in {
                    "token_usage": action_metadata.get("token_usage"),
                    "estimated_cost_usd": action_metadata.get("estimated_cost_usd"),
                    "latency_s": action_metadata.get("latency_s"),
                    "llm_calls": action_metadata.get("llm_calls"),
                }.items()
                if value is not None
            }
        if self.raac_state is None:
            self.raac_state = action_metadata.get("raac_state")
        if self.raac_decision is None:
            self.raac_decision = action_metadata.get("raac_decision")
        if not self.raac_signals and action_metadata.get("raac_signal") is not None:
            self.raac_signals = [str(action_metadata["raac_signal"])]
        if self.raac_trace_index is None and action_metadata.get("raac_trace_index") is not None:
            self.raac_trace_index = int(action_metadata["raac_trace_index"])
        return self


class TrajectoryStepV2(StrictModel):
    step_index: int = Field(ge=0)
    raw_model_output: str | None = None
    parsed_action: ToolCallParseResult | None = None
    tool_call: ToolCall | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    tool_result: ToolObservation | None = None
    parser_status: str = "not_applicable"
    tool_error_status: str = "not_applicable"
    recovery_marker: bool | str | None = None
    contradiction_marker: bool | str | None = None
    memory_use_marker: bool | str | None = None
    final_answer: str | None = None
    stop_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    token_cost_metadata: dict[str, Any] = Field(default_factory=dict)
    action: AgentAction | None = None
    observation: ToolObservation | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    raac_state: str | None = None
    raac_decision: str | None = None
    raac_signals: list[str] = Field(default_factory=list)
    raac_trace_index: int | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def normalize_step(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        normalized.setdefault("step_index", normalized.get("index", 0))
        action_payload = normalized.get("action")
        observation_payload = normalized.get("observation")
        if normalized.get("tool_call") is None and isinstance(action_payload, dict):
            normalized["tool_call"] = action_payload.get("tool_call")
        if not normalized.get("tool_arguments") and isinstance(normalized.get("tool_call"), dict):
            normalized["tool_arguments"] = normalized["tool_call"].get("arguments", {})
        if normalized.get("tool_result") is None and observation_payload is not None:
            normalized["tool_result"] = observation_payload
        action_metadata = action_payload.get("metadata", {}) if isinstance(action_payload, dict) else {}
        parsed_action = normalized.get("parsed_action")
        parsed_outcome = parsed_action.get("outcome") if isinstance(parsed_action, dict) else None
        normalized.setdefault(
            "parser_status",
            action_metadata.get("parser_outcome") or parsed_outcome or "not_applicable",
        )
        normalized.setdefault(
            "tool_error_status",
            _derive_tool_error_status_from_payload(action_metadata, observation_payload, normalized),
        )
        normalized.setdefault("recovery_marker", action_metadata.get("recovery_marker"))
        normalized.setdefault("contradiction_marker", action_metadata.get("contradiction_marker"))
        normalized.setdefault("memory_use_marker", action_metadata.get("memory_use_marker"))
        normalized.setdefault("raac_state", action_metadata.get("raac_state"))
        normalized.setdefault("raac_decision", action_metadata.get("raac_decision"))
        if not normalized.get("raac_signals") and action_metadata.get("raac_signal") is not None:
            normalized["raac_signals"] = [str(action_metadata["raac_signal"])]
        normalized.setdefault("raac_trace_index", action_metadata.get("raac_trace_index"))
        if normalized.get("final_answer") is None and isinstance(action_payload, dict):
            normalized["final_answer"] = action_payload.get("final_answer")
        normalized.pop("index", None)
        return normalized


class TrajectoryV2(StrictModel):
    schema_version: Literal["trajectory_v2"] = "trajectory_v2"
    run_id: str = Field(min_length=1)
    instance_id: str = Field(min_length=1)
    base_task_id: str = Field(min_length=1)
    intervention_id: str | None = None
    agent_id: str = Field(min_length=1)
    agent_name: str = Field(min_length=1)
    model_name: str | None = None
    provider_model_metadata: dict[str, Any] = Field(default_factory=dict)
    steps: list[TrajectoryStepV2] = Field(default_factory=list)
    final_answer: str | None = None
    stop_reason: str = Field(min_length=1)
    terminated_reason: str = Field(min_length=1)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    token_cost_metadata: dict[str, Any] = Field(default_factory=dict)
    raac_metadata: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_trajectory(cls, data: Any) -> Any:
        if isinstance(data, Trajectory):
            data = data.model_dump(mode="python")
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        metadata = normalized.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        normalized.setdefault("schema_version", "trajectory_v2")
        normalized.setdefault(
            "base_task_id",
            metadata.get("base_task_id") or metadata.get("task_id") or normalized.get("instance_id"),
        )
        normalized.setdefault("intervention_id", metadata.get("intervention_id"))
        normalized.setdefault("agent_id", metadata.get("agent_id") or normalized.get("agent_name"))
        normalized.setdefault(
            "provider_model_metadata",
            {
                key: value
                for key, value in {
                    "provider": metadata.get("provider"),
                    "model": metadata.get("model") or normalized.get("model_name"),
                    "model_name": normalized.get("model_name"),
                    "agent_type": metadata.get("agent_type"),
                    "prompt_hash": metadata.get("prompt_hash"),
                    "prompt_version_hash": metadata.get("prompt_version_hash"),
                }.items()
                if value is not None
            },
        )
        normalized.setdefault("stop_reason", normalized.get("terminated_reason", "unknown"))
        normalized.setdefault("terminated_reason", normalized.get("stop_reason", "unknown"))
        normalized.setdefault(
            "token_cost_metadata",
            {
                key: value
                for key, value in {
                    "token_usage": metadata.get("token_usage"),
                    "estimated_cost_usd": metadata.get("estimated_cost_usd"),
                    "latency_s": metadata.get("latency_s"),
                    "retry_count": metadata.get("retry_count"),
                    "llm_calls": metadata.get("llm_calls"),
                }.items()
                if value is not None
            },
        )
        normalized.setdefault(
            "raac_metadata",
            metadata.get("raac") if isinstance(metadata.get("raac"), dict) else {},
        )
        return normalized


def _derive_tool_error_status(
    *,
    action_metadata: dict[str, Any],
    observation: ToolObservation | None,
    has_tool_call: bool,
) -> str:
    if action_metadata.get("invalid_action"):
        return "invalid_action"
    if observation is None:
        return "not_applicable" if not has_tool_call else "missing_observation"
    if observation.error:
        return "error"
    if observation.is_corrupted:
        return "corrupted"
    return "none"


def _derive_tool_error_status_from_payload(
    action_metadata: dict[str, Any],
    observation_payload: Any,
    step_payload: dict[str, Any],
) -> str:
    if action_metadata.get("invalid_action"):
        return "invalid_action"
    if not isinstance(observation_payload, dict):
        return "not_applicable" if step_payload.get("tool_call") is None else "missing_observation"
    if observation_payload.get("error"):
        return "error"
    if observation_payload.get("is_corrupted"):
        return "corrupted"
    return "none"


class ExpectedBehavior(StrictModel):
    """Legacy prototype oracle metadata used by deterministic baselines and metrics."""

    required_tools: list[str] = Field(default_factory=list)
    tool_sequence: list[str] = Field(default_factory=list)
    tool_arguments: dict[str, dict[str, Any]] = Field(default_factory=dict)
    acceptable_final_answers: list[str] = Field(default_factory=list)
    final_answer_contains: list[str] = Field(default_factory=list)
    must_detect_contradiction: bool = False
    must_verify_memory: bool = False
    allow_booking: bool = False


class BenchmarkTask(StrictModel):
    """Legacy prototype task model retained for smoke-run compatibility."""

    task_id: str = Field(min_length=1)
    clean_task_id: str | None = None
    domain: str = Field(min_length=1)
    user_goal: str = Field(min_length=1)
    available_tools: list[str] = Field(min_length=1)
    mock_data: dict[str, Any] = Field(default_factory=dict)
    expected_behavior: ExpectedBehavior
    intervention: InterventionSpec | None = None
    answer_contract: AnswerContract | None = None
    gold_answer_policy: GoldAnswerPolicy | None = None
    scorer_policy: ScorerPolicy | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_expected_tools_available(self) -> BenchmarkTask:
        available = set(self.available_tools)
        removed = set()
        if self.intervention is not None and self.intervention.family == "tool_removal":
            removed = set(self.intervention.tool_availability_patch.get("removed_tools", []))
        missing = [
            tool
            for tool in self.expected_behavior.required_tools
            if tool not in available and tool not in removed
        ]
        if missing:
            raise ValueError(f"required tools are unavailable: {missing}")
        return self


class GenerationConfig(StrictModel):
    seed: int = 0
    output_path: str
    n_tasks: int = Field(gt=0)
    domains: list[str] = Field(default_factory=list)
    interventions: list[InterventionType] = Field(default_factory=list)
    include_clean: bool = True


class RunConfig(StrictModel):
    run_name: str
    seed: int = 0
    tasks_path: str
    output_dir: str
    agents: list[str] = Field(min_length=1)
    max_steps: int = Field(default=8, ge=1)


class RunMetadata(StrictModel):
    run_id: str
    config_hash: str
    seed: int
    timestamp: datetime
    git_commit: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class ScoreSummary(StrictModel):
    run_dir: str
    by_agent: dict[str, dict[str, float | int | None]]
    by_task: dict[str, dict[str, float | int | None]]
    metadata: dict[str, Any] = Field(default_factory=dict)
