"""Compute contracts, fair-comparison modes, and auditable overhead accounting."""

from __future__ import annotations

from pydantic import Field, model_validator

from causal_agent_bench.raac.types import BudgetSnapshot, StrictModel


class ComputeContract(StrictModel):
    max_extra_model_calls: int = Field(ge=0)
    max_extra_tool_calls: int = Field(ge=0)
    max_retries: int = Field(ge=0)
    max_alternate_routes: int = Field(ge=0)
    max_verification_steps: int = Field(ge=0)
    max_clarification_steps: int = Field(ge=0)
    token_budget: int = Field(ge=0)
    wall_clock_budget_seconds: float = Field(gt=0)
    termination_rule: str = Field(min_length=1)

    def initial_budget(self) -> BudgetSnapshot:
        return BudgetSnapshot(
            extra_model_calls=self.max_extra_model_calls,
            extra_tool_calls=self.max_extra_tool_calls,
            retries=self.max_retries,
            alternate_routes=self.max_alternate_routes,
            verification_steps=self.max_verification_steps,
            clarification_steps=self.max_clarification_steps,
            tokens=self.token_budget,
            wall_clock_seconds=self.wall_clock_budget_seconds,
        )


EQUAL_BUDGET_CONTRACT = ComputeContract(
    max_extra_model_calls=8,
    max_extra_tool_calls=6,
    max_retries=2,
    max_alternate_routes=2,
    max_verification_steps=3,
    max_clarification_steps=1,
    token_budget=1536,
    wall_clock_budget_seconds=90.0,
    termination_rule=(
        "Terminate on infrastructure failure or when the shared ceiling cannot fund a legal "
        "next action; otherwise answer, qualify, or abstain."
    ),
)


class OverheadAccounting(StrictModel):
    extra_model_calls: int = Field(default=0, ge=0)
    extra_tool_calls: int = Field(default=0, ge=0)
    retries: int = Field(default=0, ge=0)
    alternate_routes: int = Field(default=0, ge=0)
    verification_steps: int = Field(default=0, ge=0)
    clarification_steps: int = Field(default=0, ge=0)
    tokens: int = Field(default=0, ge=0)
    wall_clock_seconds: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def coherent_subcounts(self) -> OverheadAccounting:
        if self.retries + self.alternate_routes > self.extra_tool_calls:
            raise ValueError("retry and alternate-route counts cannot exceed extra tool calls")
        if self.verification_steps > self.extra_tool_calls:
            raise ValueError("verification steps cannot exceed extra tool calls")
        return self

    def within(self, contract: ComputeContract) -> bool:
        return (
            self.extra_model_calls <= contract.max_extra_model_calls
            and self.extra_tool_calls <= contract.max_extra_tool_calls
            and self.retries <= contract.max_retries
            and self.alternate_routes <= contract.max_alternate_routes
            and self.verification_steps <= contract.max_verification_steps
            and self.clarification_steps <= contract.max_clarification_steps
            and self.tokens <= contract.token_budget
            and self.wall_clock_seconds <= contract.wall_clock_budget_seconds
        )

    def delta(self, other: OverheadAccounting) -> dict[str, float | int]:
        return {
            field: getattr(self, field) - getattr(other, field)
            for field in type(self).model_fields
        }


class ActionCost(StrictModel):
    extra_model_calls: int = Field(default=0, ge=0)
    extra_tool_calls: int = Field(default=0, ge=0)
    retries: int = Field(default=0, ge=0)
    alternate_routes: int = Field(default=0, ge=0)
    verification_steps: int = Field(default=0, ge=0)
    clarification_steps: int = Field(default=0, ge=0)
    tokens: int = Field(default=0, ge=0)
