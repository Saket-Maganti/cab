"""Runner-facing RAAC configuration."""

from __future__ import annotations

from pydantic import model_validator

from causal_agent_bench.raac.contracts import ComputeContract
from causal_agent_bench.raac.types import (
    ComparisonMode,
    EvidenceClass,
    PolicyVariant,
    StrictModel,
)


class RAACRunConfig(StrictModel):
    enabled: bool = False
    variant: PolicyVariant = PolicyVariant.RAAC_LIGHT
    comparison_mode: ComparisonMode = ComparisonMode.PRACTICAL_BUDGET
    equal_budget_contract: ComputeContract | None = None
    evidence_class: EvidenceClass = "EXECUTION_PENDING"
    observable_signals_only: bool = True
    checkpoint_every_decision: int = 1

    @model_validator(mode="after")
    def fail_closed_on_unsafe_configuration(self) -> RAACRunConfig:
        if not self.observable_signals_only:
            raise ValueError("RAAC requires observable_signals_only=true")
        if self.checkpoint_every_decision < 1:
            raise ValueError("checkpoint_every_decision must be at least 1")
        if self.equal_budget_contract is not None:
            if self.comparison_mode != ComparisonMode.EQUAL_BUDGET:
                raise ValueError(
                    "equal_budget_contract is only valid with comparison_mode=equal_budget"
                )
        if self.variant == PolicyVariant.ORACLE_ENGINEERING_ONLY:
            if self.evidence_class not in {"DESIGN_ONLY", "ENGINEERING_ONLY", "FIXTURE_ONLY"}:
                raise ValueError("oracle control must remain DESIGN/ENGINEERING/FIXTURE evidence")
        return self
