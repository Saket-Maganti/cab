from __future__ import annotations

import io
import json
import tarfile
from copy import deepcopy
from pathlib import Path

import pytest

from causal_agent_bench.answer_contracts import RecoveryActionContract
from causal_agent_bench.cli_parsers import build_parser
from causal_agent_bench.level6.blinding import (
    build_physically_separated_review_archives,
)
from causal_agent_bench.level6.gate import (
    Level6EvidenceCounters,
    level6_completion_check,
    level6_foundation_check,
)
from causal_agent_bench.level6.gold import (
    compact_derivation_spec,
    reconstruct_in_isolated_directory,
)
from causal_agent_bench.level6.governance import (
    BenchmarkLifecycle,
    LifecycleTransition,
    governance_foundation_check,
)
from causal_agent_bench.level6.measurement import (
    generalizability_coefficients,
    invariance_assessment_fixture,
    logistic_regression_dif,
    mantel_haenszel_dif,
    measurement_foundation_check,
    propagate_uncertainty_fixture,
    variance_decomposition,
)
from causal_agent_bench.level6.portability import (
    run_cross_implementation_conformance,
)
from causal_agent_bench.level6.power import (
    HierarchicalSimulationConfig,
    analytic_power_report,
    run_hierarchical_monte_carlo,
)
from causal_agent_bench.level6.recovery import evaluate_recovery_attempts
from causal_agent_bench.level6.release import (
    _normalize_sdist_artifact,
    exact_final_tip_path_check,
)
from causal_agent_bench.level6.semantic import (
    build_compact_semantic_facts,
    build_controlled_evidence_artifact,
    validate_compact_semantic_facts,
)
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.utils.io import read_jsonl

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTANCES = read_jsonl(
    REPO_ROOT / "data/compact20_reviewed/compact20_v2_instances.jsonl",
    BenchmarkInstance,
)
CLEAN = [row for row in INSTANCES if row.condition == "clean"]


def test_semantic_fact_registry_is_explicit_and_rejects_permutation() -> None:
    travel = next(row for row in CLEAN if row.base_task.domain == "travel_planning")
    facts = build_compact_semantic_facts(travel)
    by_suffix = {row.fact_id.rsplit(".", 1)[-1]: row for row in facts}
    assert by_suffix["hotel_refundability"].source_field_or_locator.endswith(
        "hotel_refundable"
    )
    assert by_suffix["hotel_tax_rate"].source_field_or_locator.endswith("tax_rate")
    assert by_suffix["hotel_total_price"].normalized_value == 176.0
    permuted = [row.model_copy(deep=True) for row in facts]
    first = permuted[0].model_dump(mode="json")
    second = permuted[1].model_dump(mode="json")
    first["source_field_or_locator"], second["source_field_or_locator"] = (
        second["source_field_or_locator"],
        first["source_field_or_locator"],
    )
    first["hash"] = facts[0].hash
    second["hash"] = facts[1].hash
    with pytest.raises(ValueError):
        validate_compact_semantic_facts(
            travel,
            [
                *facts[2:],
                type(facts[0]).model_construct(**first),
                type(facts[1]).model_construct(**second),
            ],
        )


def test_all_compact_gold_reconstructs_without_hidden_ground_truth() -> None:
    for instance in CLEAN:
        artifact = build_controlled_evidence_artifact(
            instance,
            candidate_id=f"test.{instance.instance_id}",
        )
        serialized = json.dumps(artifact, sort_keys=True)
        assert "hidden_ground_truth" not in serialized
        assert "expected_final_answer" not in serialized
        result = reconstruct_in_isolated_directory(
            artifact,
            compact_derivation_spec(instance.base_task.domain),
        )
        assert result["output"] == instance.base_task.goal.expected_final_answer
        assert result["hidden_ground_truth_available"] is False
        assert result["derivation_graph"]["graph_hash"]


def test_gold_boundary_rejects_hidden_shortcut() -> None:
    instance = CLEAN[0]
    artifact = build_controlled_evidence_artifact(instance, candidate_id="hidden-attack")
    artifact["hidden_ground_truth"] = instance.base_task.hidden_ground_truth
    with pytest.raises(ValueError, match="forbidden hidden data"):
        reconstruct_in_isolated_directory(
            artifact,
            compact_derivation_spec(instance.base_task.domain),
        )


def test_two_stage_archives_are_physically_separated_and_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        build_physically_separated_review_archives(
            REPO_ROOT,
            output_root=tmp_path / "real",
        )
    result = build_physically_separated_review_archives(
        REPO_ROOT,
        output_root=tmp_path / "fixture",
        fixture_only=True,
    )
    assert result["status"] == "CAB_TRUE_TWO_STAGE_BLINDING_READY"
    assert result["stage1_leakage_scan"]["passed"] is True
    assert len(result["stage1_archives"]) == 3
    assert len(result["stage2_archives"]) == 3
    assert (tmp_path / "fixture/stage1").is_dir()
    assert (tmp_path / "fixture/stage2").is_dir()
    assert (tmp_path / "fixture/adjudication").is_dir()


def _recovery_contract() -> RecoveryActionContract:
    return RecoveryActionContract(
        action_id="fallback.read",
        action_type="tool_call",
        allowed_tool_names=["read_backup"],
        argument_schema={
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string"}},
            "additionalProperties": False,
        },
        preconditions=["prior_tool_failure_observed", "failed_tool:primary"],
        failure_types=["timeout"],
        success_predicate={"kind": "nonempty", "required_output_keys": ["value"]},
        supported_fact_ids=["fact.a"],
        max_attempts=1,
        cost=1,
        terminal=False,
    )


def _recovery_steps() -> list[dict[str, object]]:
    return [
        {
            "action": {"tool_call": {"tool_name": "primary", "arguments": {}}},
            "observation": {
                "tool_name": "primary",
                "error": "timeout",
                "failure_event_id": "failure-1",
            },
        },
        {
            "action": {
                "tool_call": {"tool_name": "read_backup", "arguments": {"id": "x"}},
                "metadata": {
                    "recovery_action": "fallback.read",
                    "recovery_marker": True,
                    "attempt_id": "attempt-1",
                    "failure_event_id": "failure-1",
                },
            },
            "observation": {
                "tool_name": "read_backup",
                "output": {"value": 1},
                "attempt_id": "attempt-1",
            },
        },
    ]


def test_recovery_v5_is_per_attempt_and_exact() -> None:
    contract = _recovery_contract()
    valid = evaluate_recovery_attempts(
        _recovery_steps(),
        [contract],
        final_answer_correct=True,
    )
    assert valid["succeeded"] is True
    assert valid["task_recovered"] is True
    assert valid["attempts"][0]["returned_fact_ids"][0].startswith("obsfact.")
    for mutation in ("wrong_action", "wrong_tool", "wrong_args", "stale_failure", "foreign_observation"):
        steps = deepcopy(_recovery_steps())
        if mutation == "wrong_action":
            steps[1]["action"]["metadata"]["recovery_action"] = "wrong"  # type: ignore[index]
        elif mutation == "wrong_tool":
            steps[1]["action"]["tool_call"]["tool_name"] = "unrelated"  # type: ignore[index]
        elif mutation == "wrong_args":
            steps[1]["action"]["tool_call"]["arguments"] = {}  # type: ignore[index]
        elif mutation == "stale_failure":
            steps[1]["action"]["metadata"]["failure_event_id"] = "stale"  # type: ignore[index]
        else:
            steps[1]["observation"]["attempt_id"] = "another-attempt"  # type: ignore[index]
        assert evaluate_recovery_attempts(steps, [contract])["succeeded"] is False


def test_power_modes_are_honestly_separated() -> None:
    analytic = analytic_power_report(tasks=20, effect=0.1)
    assert analytic["method_class"] == "ANALYTIC_PLANNING_APPROXIMATION"
    assert "simulations_completed" not in analytic
    assert "monte_carlo_standard_error" not in analytic
    simulation = run_hierarchical_monte_carlo(
        HierarchicalSimulationConfig(
            simulations=300,
            task_count=20,
            family_count=4,
            shard_size=75,
        )
    )
    assert simulation["simulations_completed"] == 300
    assert simulation["method_class"] == "TRUE_MONTE_CARLO_HIERARCHICAL_SIMULATION"
    assert "MODEL_SUPERPOPULATION_ESTIMAND" in simulation["estimands"]
    assert simulation["empirical_simulation_results"][
        "fixed_panel_paired_degradation"
    ]["monte_carlo_standard_error"] >= 0


def test_measurement_science_fixture_tooling() -> None:
    rows = [
        {
            "task": f"t{i % 4}",
            "model": f"m{i % 2}",
            "intervention_family": f"f{i % 2}",
            "repeat": str(i % 2),
            "scorer": f"s{i % 2}",
            "reviewer": f"r{i % 2}",
            "outcome": float(i % 2),
        }
        for i in range(16)
    ]
    decomposition = variance_decomposition(rows)
    g = generalizability_coefficients(
        decomposition["components"],
        tasks=4,
        interventions=2,
        scorers=2,
        repeats=2,
    )
    assert 0 <= g["g_coefficient"] <= 1
    assert measurement_foundation_check()["passed"] is True
    assert invariance_assessment_fixture(
        [{"group": "a", "score": 0.5}, {"group": "b", "score": 0.6}]
    )["real_invariance_conclusion"] is None
    assert logistic_regression_dif(
        list(range(8)),
        [0, 0, 0, 0, 1, 1, 1, 1],
        [0, 0, 1, 1, 0, 1, 1, 1],
    )["fixture_only"] is True
    assert mantel_haenszel_dif([{"a": 4, "b": 2, "c": 2, "d": 4}])[
        "common_odds_ratio"
    ] == 4.0
    assert propagate_uncertainty_fixture([0, 1, 1, 0], bootstrap_repetitions=100)[
        "fixture_only"
    ] is True


def test_governance_lifecycle_and_portability_foundations() -> None:
    assert governance_foundation_check()["passed"] is True
    with pytest.raises(ValueError):
        LifecycleTransition(
            benchmark_version="v1",
            from_state=BenchmarkLifecycle.RETIRED,
            to_state=BenchmarkLifecycle.ACTIVE,
            reason_codes=["invalid"],
            evidence_hashes=[],
        )
    assert run_cross_implementation_conformance(REPO_ROOT)["passed"] is True


def test_level6_gate_ready_but_completion_fails_without_genuine_evidence() -> None:
    gate = level6_foundation_check(REPO_ROOT)
    assert gate["state"] == "CAB_LEVEL6_FOUNDATION_READY"
    assert gate["CAB_LEVEL5_COMPLETE"] is False
    assert gate["CAB_LEVEL6_COMPLETE"] is False
    assert all(value == 0 for value in gate["genuine_evidence"].values())
    completion = level6_completion_check(
        Level6EvidenceCounters(),
        level5_complete=False,
        exact_final_tag_reproducible_build=False,
    )
    assert completion["CAB_LEVEL6_COMPLETE"] is False


def test_release_path_and_required_cli_surfaces() -> None:
    assert exact_final_tip_path_check(REPO_ROOT)["passed"] is True
    parser = build_parser()
    commands = (
        ["benchmark", "semantic-fact-check"],
        ["benchmark", "evidence-gold-check"],
        ["benchmark", "stage1-blinding-check"],
        ["benchmark", "causal-reachability-check"],
        ["recovery", "authorization-check"],
        ["power", "analytic-validate"],
        ["power", "simulate-validate"],
        ["measurement", "foundation-check"],
        ["antigaming", "foundation-check"],
        ["governance", "foundation-check"],
        ["portability", "conformance-check"],
        ["release", "final-tip-check"],
        ["level6", "foundation-check"],
    )
    assert all(parser.parse_args(command).command for command in commands)


def test_sdist_normalization_removes_wall_clock_and_owner_variance(tmp_path: Path) -> None:
    outputs: list[bytes] = []
    for index, mtime in enumerate((1_700_000_001, 1_800_000_002)):
        path = tmp_path / f"build-{index}" / "package.tar.gz"
        path.parent.mkdir()
        with tarfile.open(path, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
            payload = b"deterministic payload\n"
            member = tarfile.TarInfo("package-1.0/payload.txt")
            member.size = len(payload)
            member.mtime = mtime
            member.uid = 501 + index
            member.gid = 20 + index
            member.uname = f"builder-{index}"
            member.gname = f"group-{index}"
            archive.addfile(member, io.BytesIO(payload))
        _normalize_sdist_artifact(path, source_epoch=1_600_000_000)
        outputs.append(path.read_bytes())
    assert outputs[0] == outputs[1]
