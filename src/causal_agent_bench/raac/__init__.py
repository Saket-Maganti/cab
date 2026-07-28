"""Recovery-Aware Agent Control (RAAC)."""

from causal_agent_bench.raac.adapters import (
    OpenModelRAACAdapter,
    ProviderRAACAdapter,
    RAACAgentWrapper,
    RAACControlHooks,
)
from causal_agent_bench.raac.baselines import (
    BASELINE_WRAPPERS,
    ControlPolicyWrapper,
    get_baseline_wrapper,
)
from causal_agent_bench.raac.config import RAACRunConfig
from causal_agent_bench.raac.contracts import (
    EQUAL_BUDGET_CONTRACT,
    ComputeContract,
    OverheadAccounting,
)
from causal_agent_bench.raac.controller import ControllerCheckpoint, RAACController
from causal_agent_bench.raac.fixtures import (
    FIXTURE_SCENARIOS,
    FixtureRun,
    FixtureScenario,
    run_all_fixtures,
    run_fixture_scenario,
)
from causal_agent_bench.raac.kaggle import (
    REQUIRED_KAGGLE_ARMS,
    load_raac_kaggle_matrix,
    materialize_raac_kaggle_config,
)
from causal_agent_bench.raac.opportunities import raac_opportunity_flags
from causal_agent_bench.raac.policy import (
    CANONICAL_POLICIES,
    PolicyDefinition,
    comparison_contract,
    get_policy,
)
from causal_agent_bench.raac.signals import (
    FORBIDDEN_POLICY_KEYS,
    ObservationEnvelope,
    detect_anomaly_signals,
)
from causal_agent_bench.raac.state_machine import LEGAL_TRANSITIONS, RAACStateMachine
from causal_agent_bench.raac.types import (
    AnomalySignal,
    BudgetSnapshot,
    ComparisonMode,
    DecisionKind,
    PolicyVariant,
    RAACDecision,
    RAACState,
    ReasonCode,
)

__all__ = [
    "BASELINE_WRAPPERS",
    "CANONICAL_POLICIES",
    "EQUAL_BUDGET_CONTRACT",
    "FIXTURE_SCENARIOS",
    "FORBIDDEN_POLICY_KEYS",
    "LEGAL_TRANSITIONS",
    "REQUIRED_KAGGLE_ARMS",
    "AnomalySignal",
    "BudgetSnapshot",
    "ComparisonMode",
    "ComputeContract",
    "ControlPolicyWrapper",
    "ControllerCheckpoint",
    "DecisionKind",
    "FixtureRun",
    "FixtureScenario",
    "ObservationEnvelope",
    "OpenModelRAACAdapter",
    "OverheadAccounting",
    "PolicyDefinition",
    "PolicyVariant",
    "ProviderRAACAdapter",
    "RAACAgentWrapper",
    "RAACControlHooks",
    "RAACController",
    "RAACDecision",
    "RAACRunConfig",
    "RAACState",
    "RAACStateMachine",
    "ReasonCode",
    "comparison_contract",
    "detect_anomaly_signals",
    "get_baseline_wrapper",
    "get_policy",
    "load_raac_kaggle_matrix",
    "materialize_raac_kaggle_config",
    "raac_opportunity_flags",
    "run_all_fixtures",
    "run_fixture_scenario",
]
