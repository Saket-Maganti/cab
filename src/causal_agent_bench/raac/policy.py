"""Canonical RAAC variants, ablations, and baseline control policies."""

from __future__ import annotations

import hashlib
import json

from pydantic import ConfigDict

from causal_agent_bench.raac.contracts import EQUAL_BUDGET_CONTRACT, ComputeContract
from causal_agent_bench.raac.types import ComparisonMode, PolicyVariant, StrictModel


class PolicyDefinition(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant: PolicyVariant
    description: str
    contract: ComputeContract
    enable_retry: bool = False
    enable_alternate_route: bool = False
    enable_cross_check: bool = False
    enable_verification: bool = False
    enable_clarification: bool = False
    enable_abstention: bool = False
    enable_final_verify: bool = False
    abstain_on_any_anomaly: bool = False
    baseline_wrapper: bool = False
    oracle_engineering_only: bool = False

    def policy_hash(self) -> str:
        payload = self.model_dump(mode="json")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


_LIGHT = ComputeContract(
    max_extra_model_calls=3,
    max_extra_tool_calls=3,
    max_retries=1,
    max_alternate_routes=1,
    max_verification_steps=1,
    max_clarification_steps=0,
    token_budget=384,
    wall_clock_budget_seconds=30.0,
    termination_rule=(
        "After one retry, one optional alternate route, and one verification, answer only with "
        "sufficient observable evidence; otherwise qualify or abstain."
    ),
)

_FULL = ComputeContract(
    max_extra_model_calls=8,
    max_extra_tool_calls=6,
    max_retries=2,
    max_alternate_routes=2,
    max_verification_steps=3,
    max_clarification_steps=1,
    token_budget=1536,
    wall_clock_budget_seconds=90.0,
    termination_rule=(
        "Resolve observable anomalies within all declared ceilings, then answer, qualify, "
        "abstain, or terminate on infrastructure failure."
    ),
)

_NO_OVERHEAD = ComputeContract(
    max_extra_model_calls=0,
    max_extra_tool_calls=0,
    max_retries=0,
    max_alternate_routes=0,
    max_verification_steps=0,
    max_clarification_steps=0,
    token_budget=0,
    wall_clock_budget_seconds=1.0,
    termination_rule="Return control to the wrapped baseline without RAAC recovery actions.",
)

_SELF_CHECK = ComputeContract(
    max_extra_model_calls=1,
    max_extra_tool_calls=1,
    max_retries=0,
    max_alternate_routes=0,
    max_verification_steps=1,
    max_clarification_steps=0,
    token_budget=256,
    wall_clock_budget_seconds=20.0,
    termination_rule="Perform at most one self-check, then answer or qualify.",
)


def _full_policy(variant: PolicyVariant, description: str, **updates: bool) -> PolicyDefinition:
    values = {
        "enable_retry": True,
        "enable_alternate_route": True,
        "enable_cross_check": True,
        "enable_verification": True,
        "enable_clarification": True,
        "enable_abstention": True,
        "enable_final_verify": True,
    }
    values.update(updates)
    return PolicyDefinition(
        variant=variant,
        description=description,
        contract=_FULL,
        **values,
    )


CANONICAL_POLICIES: dict[PolicyVariant, PolicyDefinition] = {
    PolicyVariant.RAAC_LIGHT: PolicyDefinition(
        variant=PolicyVariant.RAAC_LIGHT,
        description="Low-overhead bounded recovery for constrained Kaggle execution.",
        contract=_LIGHT,
        enable_retry=True,
        enable_alternate_route=True,
        enable_verification=True,
        enable_abstention=True,
        enable_final_verify=True,
    ),
    PolicyVariant.RAAC_FULL: _full_policy(
        PolicyVariant.RAAC_FULL,
        "Full bounded recovery, contradiction resolution, clarification, and abstention.",
    ),
    PolicyVariant.VERIFY_ONLY: PolicyDefinition(
        variant=PolicyVariant.VERIFY_ONLY,
        description="Ablation retaining verification without retry, routing, or clarification.",
        contract=_FULL,
        enable_verification=True,
        enable_abstention=True,
        enable_final_verify=True,
    ),
    PolicyVariant.RETRY_ONLY: PolicyDefinition(
        variant=PolicyVariant.RETRY_ONLY,
        description="Ablation retaining bounded same-tool retries only.",
        contract=_FULL,
        enable_retry=True,
    ),
    PolicyVariant.ABSTAIN_ONLY: PolicyDefinition(
        variant=PolicyVariant.ABSTAIN_ONLY,
        description="Ablation that abstains on any detected observable anomaly.",
        contract=_NO_OVERHEAD,
        enable_abstention=True,
        abstain_on_any_anomaly=True,
    ),
    PolicyVariant.NO_CROSS_CHECK: _full_policy(
        PolicyVariant.NO_CROSS_CHECK,
        "Full RAAC without cross-source contradiction checks.",
        enable_cross_check=False,
    ),
    PolicyVariant.NO_ALTERNATE_ROUTE: _full_policy(
        PolicyVariant.NO_ALTERNATE_ROUTE,
        "Full RAAC without alternate tool or route selection.",
        enable_alternate_route=False,
    ),
    PolicyVariant.NO_FINAL_VERIFY: _full_policy(
        PolicyVariant.NO_FINAL_VERIFY,
        "Full RAAC without a final verification stage.",
        enable_final_verify=False,
    ),
    PolicyVariant.DIRECT_ANSWER: PolicyDefinition(
        variant=PolicyVariant.DIRECT_ANSWER,
        description="Direct-answer baseline wrapper with no recovery overhead.",
        contract=_NO_OVERHEAD,
        baseline_wrapper=True,
    ),
    PolicyVariant.STANDARD_TOOL_USE: PolicyDefinition(
        variant=PolicyVariant.STANDARD_TOOL_USE,
        description="Standard tool-use baseline wrapper with no RAAC recovery.",
        contract=_NO_OVERHEAD,
        baseline_wrapper=True,
    ),
    PolicyVariant.REACT_STYLE: PolicyDefinition(
        variant=PolicyVariant.REACT_STYLE,
        description="ReAct-style baseline wrapper; native reasoning is not counted as RAAC.",
        contract=_NO_OVERHEAD,
        baseline_wrapper=True,
    ),
    PolicyVariant.SELF_CHECK: PolicyDefinition(
        variant=PolicyVariant.SELF_CHECK,
        description="One-step self-check baseline wrapper.",
        contract=_SELF_CHECK,
        enable_verification=True,
        enable_final_verify=True,
        baseline_wrapper=True,
    ),
    PolicyVariant.ORACLE_ENGINEERING_ONLY: PolicyDefinition(
        variant=PolicyVariant.ORACLE_ENGINEERING_ONLY,
        description=(
            "Engineering-only upper-control wrapper; never eligible as behavioral evidence."
        ),
        contract=_FULL,
        enable_retry=True,
        enable_alternate_route=True,
        enable_cross_check=True,
        enable_verification=True,
        enable_clarification=True,
        enable_abstention=True,
        enable_final_verify=True,
        baseline_wrapper=True,
        oracle_engineering_only=True,
    ),
}


def get_policy(variant: PolicyVariant | str) -> PolicyDefinition:
    return CANONICAL_POLICIES[PolicyVariant(variant)]


def comparison_contract(
    policy: PolicyDefinition,
    mode: ComparisonMode | str,
    *,
    equal_budget_contract: ComputeContract | None = None,
) -> ComputeContract:
    comparison = ComparisonMode(mode)
    if comparison == ComparisonMode.PRACTICAL_BUDGET:
        return policy.contract
    return equal_budget_contract or EQUAL_BUDGET_CONTRACT
