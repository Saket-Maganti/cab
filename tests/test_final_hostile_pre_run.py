from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from causal_agent_bench.final_pre_run.gate import enforce_unexposed_ids
from causal_agent_bench.final_pre_run.hostile import (
    black_box_archive_attack,
    recovery_hostile_cases,
    run_negative_controls,
    run_route_attacks,
)
from causal_agent_bench.final_pre_run.power import direct_calibration_check
from causal_agent_bench.final_pre_run.private_packet import (
    PACKET_ID,
    build_private_packet,
    generate_candidate_records,
    load_private_packet,
    stage2_unlock_allowed,
    validate_composition,
    validate_primitive_candidate,
)
from causal_agent_bench.final_pre_run.tools import (
    PrimitiveToolRuntime,
    extract_semantic_facts,
    reconstruct_with_actual_tools,
)


def _seed() -> bytes:
    return hashlib.sha256(b"cab-final-hostile-test-seed").digest()


def test_private_packet_is_balanced_primitive_and_physically_separated(tmp_path: Path) -> None:
    commitment = build_private_packet(tmp_path, _seed())
    stage1, _ = load_private_packet(tmp_path)
    assert validate_composition(stage1)["passed"] is True
    assert all(validate_primitive_candidate(row)["passed"] for row in stage1)
    assert commitment["candidate_count"] == 20
    assert commitment["private_bodies_committed"] is False
    assert len(commitment["candidate_content_hashes"]) == 20
    assert set(commitment["stage1_package_hashes"]) == {
        "stage1_adjudicator.zip",
        "stage1_reviewer_a.zip",
        "stage1_reviewer_b.zip",
    }
    assert (tmp_path / PACKET_ID / "stage2/stage2_private.aesgcm").is_file()
    assert (tmp_path / PACKET_ID / "stage2/stage2_private.key").is_file()


def test_derived_field_and_exposed_id_are_rejected() -> None:
    stage1, _ = generate_candidate_records(_seed())
    injected = stage1[0].model_copy(deep=True)
    injected.artifact.records["selected_hotel"] = "answer"
    assert validate_primitive_candidate(injected)["passed"] is False
    with pytest.raises(ValueError, match="exposed development fixtures"):
        enforce_unexposed_ids(["compact20_cand_01"], {"compact20_cand_01"}, genuine=True)


def test_actual_tools_reconstruct_without_hidden_gold_and_reject_injection() -> None:
    stage1, stage2 = generate_candidate_records(_seed())
    for candidate, hidden in zip(stage1, stage2, strict=True):
        result = reconstruct_with_actual_tools(candidate)
        assert result["hidden_gold_available_during_derivation"] is False
        assert result["fixture_fact_reader_used"] is False
        assert hashlib.sha256(result["derived_answer"].encode()).hexdigest() == hidden.expected_answer_sha256
    runtime = PrimitiveToolRuntime(stage1[0])
    receipt = runtime.execute(stage1[0].declared_tools[0], {"artifact_id": stage1[0].artifact.artifact_id})
    forged = receipt.model_copy(deep=True)
    forged.observation["returned_fact_ids"] = ["expected.fact"]
    with pytest.raises(ValueError, match="injection"):
        extract_semantic_facts(forged)


def test_route_and_recovery_attacks_fail_closed() -> None:
    stage1, stage2 = generate_candidate_records(_seed())
    results = [run_route_attacks(candidate, hidden) for candidate, hidden in zip(stage1, stage2, strict=True)]
    assert all(row["passed"] for row in results)
    assert {row["route_kind"] for row in results} == {
        "completion",
        "recovery",
        "clarification",
        "abstention",
    }
    recovery = [
        recovery_hostile_cases(candidate, hidden)
        for candidate, hidden in zip(stage1, stage2, strict=True)
        if hidden.route_kind == "recovery"
    ]
    assert len(recovery) == 5
    assert all(row["passed"] for row in recovery)


def test_negative_controls_and_black_box_attacker(tmp_path: Path) -> None:
    build_private_packet(tmp_path, _seed())
    stage1, _ = load_private_packet(tmp_path)
    representatives = {row.domain: row for row in stage1}
    assert all(run_negative_controls(row)["passed"] for row in representatives.values())
    packages = (tmp_path / PACKET_ID / "packages").glob("*.zip")
    assert all(black_box_archive_attack(path.read_bytes(), {"compact20_cand_01"})["passed"] for path in packages)


def test_stage2_unlock_is_conjunctive_and_default_deny() -> None:
    assert not stage2_unlock_allowed(
        stage1_judgments_final=True,
        stage1_receipt_valid=True,
        coordinator_unlock=False,
    )
    assert stage2_unlock_allowed(
        stage1_judgments_final=True,
        stage1_receipt_valid=True,
        coordinator_unlock=True,
    )


def test_power_calibration_runs_actual_tests() -> None:
    report = direct_calibration_check()
    assert report["passed"] is True
    assert report["checks"]["type_i_within_preregistered_tolerance"] is True
    assert report["checks"]["ci_coverage_calibrated"] is True
    assert report["checks"]["no_heuristic_detector"] is True
    assert min(report["alternative_power_per_model"]) >= 0.8
