from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    expected_final_answer: str | dict[str, Any] | None = None


class BaseTask(StrictModel):
    task_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)
    goal: TaskGoal
    available_tools: list[str] = Field(min_length=1)
    hidden_ground_truth: dict[str, Any] = Field(default_factory=dict)
    gold_tool_sequence: list[str] | None = None
    max_steps: int = Field(gt=0)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_tool_sequence(self) -> BaseTask:
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
    tool_availability_patch: dict[str, Any] = Field(default_factory=dict)
    memory_patch: dict[str, Any] = Field(default_factory=dict)
    tool_output_patch: dict[str, Any] = Field(default_factory=dict)
    instruction_patch: str | None = None
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
            "tool_availability_patch": tool_availability_patch,
            "memory_patch": memory_patch,
            "tool_output_patch": tool_output_patch,
            "instruction_patch": instruction_patch,
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
    run_id: str = Field(min_length=1)
    instance_id: str = Field(min_length=1)
    agent_name: str = Field(min_length=1)
    model_name: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    final_answer: str | None = None
    terminated_reason: str = Field(min_length=1)
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
