from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from causal_agent_bench.agents.greedy_tool_agent import GreedyToolAgent
from causal_agent_bench.raac import (
    CANONICAL_POLICIES,
    EQUAL_BUDGET_CONTRACT,
    FIXTURE_SCENARIOS,
    LEGAL_TRANSITIONS,
    AnomalySignal,
    ComparisonMode,
    DecisionKind,
    ObservationEnvelope,
    PolicyVariant,
    RAACAgentWrapper,
    RAACController,
    RAACRunConfig,
    RAACState,
    RAACStateMachine,
    detect_anomaly_signals,
    get_policy,
    run_fixture_scenario,
)
from causal_agent_bench.raac.controller import ControllerCheckpoint
from causal_agent_bench.raac.kaggle import (
    REQUIRED_KAGGLE_ARMS,
    load_raac_kaggle_matrix,
    materialize_raac_kaggle_config,
)
from causal_agent_bench.raac.opportunities import raac_opportunity_flags
from causal_agent_bench.runners.config import AgentRunConfig, ExperimentConfig
from causal_agent_bench.runners.run_manifest_v2 import CanonicalRunManifest
from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, TaskGoal, Trajectory
from causal_agent_bench.trajectory import migrate_trajectory_v2, trajectory_to_markdown


def _decisions(name: str, variant: PolicyVariant | None = None) -> list[DecisionKind]:
    return [
        row.decision
        for row in run_fixture_scenario(name, variant=variant).decisions
    ]


def test_canonical_state_set_and_invalid_transition_fail_closed() -> None:
    assert set(RAACState) == {
        RAACState.PLAN,
        RAACState.ACT,
        RAACState.VALIDATE_OBSERVATION,
        RAACState.DETECT_ANOMALY,
        RAACState.RETRY,
        RAACState.ALTERNATE_ROUTE,
        RAACState.CROSS_CHECK,
        RAACState.CLARIFY,
        RAACState.ABSTAIN,
        RAACState.FINAL_VERIFY,
        RAACState.ANSWER,
        RAACState.TERMINATE,
    }
    assert set(LEGAL_TRANSITIONS) == set(RAACState)
    machine = RAACStateMachine()
    with pytest.raises(ValueError, match="invalid RAAC transition"):
        machine.transition(RAACState.ANSWER)


def test_all_required_observable_signal_types_are_detectable() -> None:
    events = {
        AnomalySignal.TOOL_ERROR: ObservationEnvelope(error="failed"),
        AnomalySignal.TIMEOUT: ObservationEnvelope(timed_out=True),
        AnomalySignal.MALFORMED_OUTPUT: ObservationEnvelope(raw_output="{"),
        AnomalySignal.MISSING_REQUIRED_FIELD: ObservationEnvelope(
            parsed_output={}, required_fields=("id",)
        ),
        AnomalySignal.SCHEMA_MISMATCH: ObservationEnvelope(schema_valid=False),
        AnomalySignal.CONTRADICTORY_OBSERVATION: ObservationEnvelope(
            contradicts_previous=True
        ),
        AnomalySignal.STALE_TIMESTAMP: ObservationEnvelope(
            observed_at=0, reference_time=10, max_staleness_seconds=1
        ),
        AnomalySignal.INCONSISTENT_REPEATED_RESULT: ObservationEnvelope(
            repeated_result_consistent=False
        ),
        AnomalySignal.PARTIAL_OUTPUT: ObservationEnvelope(partial=True),
        AnomalySignal.IMPOSSIBLE_VALUE: ObservationEnvelope(impossible_value=True),
        AnomalySignal.INSUFFICIENT_EVIDENCE: ObservationEnvelope(
            evidence_count=0, minimum_evidence=1
        ),
        AnomalySignal.UNVERIFIABLE_SUCCESS_SIGNAL: ObservationEnvelope(
            success_claimed=True, success_verifiable=False
        ),
        AnomalySignal.EXHAUSTED_TOKEN_BUDGET: ObservationEnvelope(
            reported_token_budget_exhausted=True
        ),
        AnomalySignal.EXHAUSTED_TOOL_BUDGET: ObservationEnvelope(
            reported_tool_budget_exhausted=True
        ),
        AnomalySignal.EXHAUSTED_RETRY_BUDGET: ObservationEnvelope(
            reported_retry_budget_exhausted=True
        ),
        AnomalySignal.INFRASTRUCTURE_FAILURE: ObservationEnvelope(
            infrastructure_failure=True
        ),
    }
    for expected, event in events.items():
        assert expected in detect_anomaly_signals(event)


def test_hidden_labels_gold_and_evaluator_metadata_are_ignored() -> None:
    public = {
        "error": "transient",
        "output": {
            "visible": "same",
            "gold_answer": "secret-a",
            "evaluator_metadata": {"score": 1},
        },
        "intervention_id": "secret-a",
        "condition_label": "intervention",
    }
    changed_hidden = deepcopy(public)
    changed_hidden["intervention_id"] = "secret-b"
    changed_hidden["condition_label"] = "clean"
    changed_hidden["output"]["gold_answer"] = "secret-b"
    first_event = ObservationEnvelope.from_payload(public)
    second_event = ObservationEnvelope.from_payload(changed_hidden)
    assert first_event == second_event
    assert "gold_answer" not in first_event.model_dump_json()
    first = RAACController().evaluate(first_event)
    second = RAACController().evaluate(second_event)
    assert first == second
    with pytest.raises(ValidationError):
        ObservationEnvelope.model_validate({"intervention_id": "not-accepted"})


def test_agent_wrapper_does_not_retain_gold_benchmark_instance() -> None:
    task = BaseTask(
        task_id="fixture",
        domain="fixture",
        difficulty="easy",
        goal=TaskGoal(user_instruction="Inspect the fixture.", success_criteria=["done"]),
        available_tools=["search_database"],
        hidden_ground_truth={"gold_answer": "never expose"},
        max_steps=2,
    )
    instance = BenchmarkInstance(
        instance_id="fixture.clean",
        base_task=task,
        condition="clean",
        available_tools=["search_database"],
        environment_seed=0,
    )
    wrapped = GreedyToolAgent(seed=0)
    controller_wrapper = RAACAgentWrapper(
        wrapped,
        RAACRunConfig(
            enabled=True,
            variant=PolicyVariant.RAAC_LIGHT,
            evidence_class="FIXTURE_ONLY",
        ),
    )
    controller_wrapper.reset(instance, seed=0)
    assert controller_wrapper.instance is None
    assert controller_wrapper.legacy_task is None
    assert wrapped.instance is instance


def test_clean_success_has_no_unnecessary_intervention_or_overhead() -> None:
    run = run_fixture_scenario("clean_success")
    assert [row.decision for row in run.decisions] == [DecisionKind.ANSWER]
    overhead = run.final_controller_metadata["overhead"]
    assert overhead == {
        "extra_model_calls": 0,
        "extra_tool_calls": 0,
        "retries": 0,
        "alternate_routes": 0,
        "verification_steps": 0,
        "clarification_steps": 0,
        "tokens": 0,
        "wall_clock_seconds": 0.0,
    }


def test_bounded_retry_and_alternate_route_recovery() -> None:
    decisions = _decisions("alternate_route_recovery", PolicyVariant.RAAC_LIGHT)
    assert decisions == [
        DecisionKind.RETRY_SAME_TOOL,
        DecisionKind.USE_ALTERNATE_TOOL,
        DecisionKind.ANSWER,
    ]
    run = run_fixture_scenario("persistent_failure", variant=PolicyVariant.RAAC_LIGHT)
    overhead = run.final_controller_metadata["overhead"]
    assert overhead["retries"] <= 1
    assert overhead["alternate_routes"] <= 1
    assert run.decisions[-1].decision == DecisionKind.ABSTAIN


def test_contradiction_stale_malformed_and_partial_routes() -> None:
    assert _decisions("conflicting_observations")[0] == DecisionKind.CROSS_CHECK_SOURCE
    assert _decisions("stale_memory")[0] == DecisionKind.VERIFY_CURRENT_EVIDENCE
    assert _decisions("malformed_output")[0] == DecisionKind.RETRY_SAME_TOOL
    assert _decisions("partial_output")[0] == DecisionKind.RETRY_SAME_TOOL


def test_clarification_abstention_and_false_abstention_fixture() -> None:
    assert _decisions("clarification")[0] == DecisionKind.REQUEST_CLARIFICATION
    assert _decisions("correct_abstention")[-1] == DecisionKind.ABSTAIN
    assert _decisions("false_abstention") == [DecisionKind.ABSTAIN]


def test_premature_success_is_verified() -> None:
    assert _decisions("premature_success_signal")[0] == DecisionKind.FINAL_VERIFICATION


def test_exhausted_budgets_and_infrastructure_failure_terminate_safely() -> None:
    exhausted = RAACController(PolicyVariant.RAAC_LIGHT).evaluate(
        ObservationEnvelope(
            reported_tool_budget_exhausted=True,
            insufficient_evidence=True,
        )
    )
    assert exhausted.decision == DecisionKind.ABSTAIN
    infra = RAACController(PolicyVariant.RAAC_FULL).evaluate(
        ObservationEnvelope(infrastructure_failure=True)
    )
    assert infra.decision == DecisionKind.TERMINATE_INFRASTRUCTURE_FAILURE
    assert infra.next_state == RAACState.TERMINATE


def test_equal_and_practical_budget_modes_are_explicit() -> None:
    light_equal = RAACController(
        PolicyVariant.RAAC_LIGHT, comparison_mode=ComparisonMode.EQUAL_BUDGET
    )
    full_equal = RAACController(
        PolicyVariant.RAAC_FULL, comparison_mode=ComparisonMode.EQUAL_BUDGET
    )
    assert light_equal.contract == full_equal.contract == EQUAL_BUDGET_CONTRACT
    light_practical = RAACController(PolicyVariant.RAAC_LIGHT)
    full_practical = RAACController(PolicyVariant.RAAC_FULL)
    assert light_practical.contract.max_extra_tool_calls < full_practical.contract.max_extra_tool_calls


def test_light_has_lower_persistent_failure_overhead_than_full() -> None:
    light = run_fixture_scenario("persistent_failure", variant=PolicyVariant.RAAC_LIGHT)
    full = run_fixture_scenario("persistent_failure", variant=PolicyVariant.RAAC_FULL)
    light_overhead = light.final_controller_metadata["overhead"]
    full_overhead = full.final_controller_metadata["overhead"]
    assert light_overhead["extra_tool_calls"] < full_overhead["extra_tool_calls"]
    assert light_overhead["tokens"] < full_overhead["tokens"]


def test_checkpoint_resume_is_deterministic_and_fail_closed() -> None:
    first_event, second_event, third_event = FIXTURE_SCENARIOS[
        "alternate_route_recovery"
    ].events
    uninterrupted = RAACController(PolicyVariant.RAAC_LIGHT)
    first = uninterrupted.evaluate(first_event)
    checkpoint = uninterrupted.checkpoint()
    second = uninterrupted.evaluate(second_event)
    third = uninterrupted.evaluate(third_event)

    resumed = RAACController.restore(checkpoint.model_dump(mode="json"))
    assert resumed.evaluate(second_event) == second
    assert resumed.evaluate(third_event) == third
    assert resumed.trace == uninterrupted.trace
    assert resumed.overhead == uninterrupted.overhead
    assert first.trace_index == 0

    tampered = checkpoint.model_dump(mode="json")
    tampered["policy_hash"] = "tampered"
    with pytest.raises(ValueError, match="policy hash mismatch"):
        RAACController.restore(ControllerCheckpoint.model_validate(tampered))


def test_repeated_fixture_runs_have_identical_traces() -> None:
    first = run_fixture_scenario("persistent_failure", variant=PolicyVariant.RAAC_FULL)
    second = run_fixture_scenario("persistent_failure", variant=PolicyVariant.RAAC_FULL)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_no_infinite_loop_and_evidence_class_preserved() -> None:
    for variant in CANONICAL_POLICIES:
        run = run_fixture_scenario("persistent_failure", variant=variant)
        policy = get_policy(variant)
        assert len(run.decisions) <= (
            policy.contract.max_retries
            + policy.contract.max_alternate_routes
            + policy.contract.max_verification_steps
            + policy.contract.max_clarification_steps
            + 2
        )
        assert all(row.evidence_class == "FIXTURE_ONLY" for row in run.decisions)
        assert run.final_controller_metadata["evidence_class"] == "FIXTURE_ONLY"
        assert run.final_controller_metadata["hidden_metadata_access"] is False


def test_runner_config_supports_global_and_per_agent_raac() -> None:
    global_policy = RAACRunConfig(enabled=True, variant=PolicyVariant.RAAC_LIGHT)
    override = RAACRunConfig(enabled=True, variant=PolicyVariant.RAAC_FULL)
    config = ExperimentConfig(
        run_name="fixture",
        benchmark_path="fixtures.jsonl",
        agents=["greedy_tool_agent"],
        raac=global_policy,
    )
    agent_run = config.iter_agent_runs()[0]
    assert config.resolved_raac(agent_run) == global_policy
    per_agent = AgentRunConfig(agent="greedy_tool_agent", raac=override)
    assert config.resolved_raac(per_agent) == override
    with pytest.raises(ValidationError, match="observable_signals_only"):
        RAACRunConfig(observable_signals_only=False)


def test_canonical_light_and_full_config_contracts_match_code() -> None:
    root = Path(__file__).resolve().parents[1] / "configs" / "raac"
    for filename, variant in (
        ("raac_light.yaml", PolicyVariant.RAAC_LIGHT),
        ("raac_full.yaml", PolicyVariant.RAAC_FULL),
    ):
        payload = yaml.safe_load((root / filename).read_text(encoding="utf-8"))
        assert payload["raac"]["variant"] == variant.value
        declared = payload["declared_compute_contract"]
        contract = get_policy(variant).contract.model_dump(mode="json")
        for key, value in declared.items():
            assert contract[key] == value


def test_kaggle_matrix_materializes_every_arm_in_both_budget_modes(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    matrix = load_raac_kaggle_matrix(root / "configs/raac/kaggle_t4x2_matrix.yaml")
    assert set(matrix["budget_modes"]) == {"equal_budget", "practical_budget"}
    source = root / "configs/raac/kaggle_t4x2_raac_TEMPLATE_NOT_APPROVED.yaml"
    for mode in matrix["budget_modes"]:
        output = materialize_raac_kaggle_config(
            source,
            tmp_path / f"{mode}.yaml",
            comparison_mode=mode,
        )
        raw = yaml.safe_load(output.read_text(encoding="utf-8"))
        config = ExperimentConfig.model_validate(raw)
        observed = {run.raac.variant for run in config.agent_runs if run.raac is not None}
        assert observed == REQUIRED_KAGGLE_ARMS
        assert {
            run.raac.comparison_mode.value
            for run in config.agent_runs
            if run.raac is not None
        } == {mode}
        assert config.template_only is True
        assert config.allow_paid_calls is False


def test_governed_kaggle_notebook_explicitly_carries_raac_matrix() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "notebooks/kaggle/CAB_T4X2_05_BASELINES_AND_ABLATIONS.ipynb"
    )
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = {
        cell["metadata"]["cab_role"]: cell["source"]
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    }
    configuration = cells["configuration"]
    for token in (
        "STANDARD_TOOL_USE",
        "RAAC_LIGHT",
        "RAAC_FULL",
        "VERIFY_ONLY",
        "RETRY_ONLY",
        "ABSTAIN_ONLY",
        "NO_CROSS_CHECK",
        "NO_ALTERNATE_ROUTE",
        "NO_FINAL_VERIFY",
        "equal_budget",
        "practical_budget",
        "RAAC_REQUIRED_COMPUTE_FIELDS",
    ):
        assert token in configuration
    assert "materialize_raac_kaggle_config" in cells["live_plan"]


def test_manifest_raac_fields_are_backward_compatible_and_typed() -> None:
    manifest = CanonicalRunManifest(
        study_id="fixture",
        run_id="fixture",
        benchmark_version="v1",
        split_role="dev",
        task_pack_hash="a",
        intervention_pack_hash="b",
        scorer_name="typed",
        scorer_version="1",
        scorer_policy_hash="c",
        code_revision="d",
        environment_hash="e",
        model_id="fixture",
        model_revision="fixture",
        provider="offline",
        adapter_version="1",
        quantization="none",
        device="cpu",
        gpu_count=0,
        seed=0,
        repeat=0,
        prompt_version="1",
        prompt_hash="f",
        tool_budget=0,
        token_budget=0,
        timeout_seconds=1,
        retry_policy={},
        trajectory_path="trajectories.jsonl",
        score_path="scores.jsonl",
        audit_state="FIXTURE_ONLY",
        evidence_class="FIXTURE_ONLY",
        raac_policy={"variant": "RAAC_LIGHT"},
        raac_comparison_mode="practical_budget",
        raac_overhead={"extra_tool_calls": 0},
    )
    assert manifest.raac_policy == {"variant": "RAAC_LIGHT"}


def test_trajectory_v2_and_scorer_opportunity_integration() -> None:
    fixture = run_fixture_scenario(
        "alternate_route_recovery", variant=PolicyVariant.RAAC_LIGHT
    )
    trajectory = Trajectory(
        run_id="fixture",
        instance_id="fixture-instance",
        agent_name="fixture-agent",
        steps=[],
        final_answer="fixture",
        terminated_reason="final_answer",
        raac_metadata=fixture.final_controller_metadata,
        metadata={"raac": fixture.final_controller_metadata},
    )
    migrated = migrate_trajectory_v2(trajectory)
    assert migrated.raac_metadata["variant"] == "RAAC_LIGHT"
    assert "## RAAC" in trajectory_to_markdown(migrated)
    flags = raac_opportunity_flags(trajectory)
    assert flags["raac_enabled_binary"] is True
    assert flags["raac_recovery_opportunity_binary"] is True
    assert flags["raac_anomaly_signal_count"] == 2
