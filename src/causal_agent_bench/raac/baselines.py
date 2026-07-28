"""Declarative wrappers for RAAC baselines and ablations."""

from __future__ import annotations

from dataclasses import dataclass

from causal_agent_bench.raac.controller import RAACController
from causal_agent_bench.raac.policy import PolicyDefinition, get_policy
from causal_agent_bench.raac.types import ComparisonMode, EvidenceClass, PolicyVariant


@dataclass(frozen=True)
class ControlPolicyWrapper:
    variant: PolicyVariant
    display_name: str

    @property
    def policy(self) -> PolicyDefinition:
        return get_policy(self.variant)

    def controller(
        self,
        *,
        comparison_mode: ComparisonMode = ComparisonMode.PRACTICAL_BUDGET,
        evidence_class: EvidenceClass = "ENGINEERING_ONLY",
    ) -> RAACController:
        if self.variant == PolicyVariant.ORACLE_ENGINEERING_ONLY:
            evidence_class = "ENGINEERING_ONLY"
        return RAACController(
            self.variant,
            comparison_mode=comparison_mode,
            evidence_class=evidence_class,
        )


BASELINE_WRAPPERS: dict[PolicyVariant, ControlPolicyWrapper] = {
    PolicyVariant.DIRECT_ANSWER: ControlPolicyWrapper(
        PolicyVariant.DIRECT_ANSWER, "direct answer"
    ),
    PolicyVariant.STANDARD_TOOL_USE: ControlPolicyWrapper(
        PolicyVariant.STANDARD_TOOL_USE, "standard tool use"
    ),
    PolicyVariant.REACT_STYLE: ControlPolicyWrapper(PolicyVariant.REACT_STYLE, "ReAct-style"),
    PolicyVariant.SELF_CHECK: ControlPolicyWrapper(PolicyVariant.SELF_CHECK, "self-check"),
    PolicyVariant.ORACLE_ENGINEERING_ONLY: ControlPolicyWrapper(
        PolicyVariant.ORACLE_ENGINEERING_ONLY, "oracle engineering-only control"
    ),
}


def get_baseline_wrapper(variant: PolicyVariant | str) -> ControlPolicyWrapper:
    key = PolicyVariant(variant)
    if key not in BASELINE_WRAPPERS:
        raise ValueError(f"{key.value} is not a baseline wrapper")
    return BASELINE_WRAPPERS[key]
