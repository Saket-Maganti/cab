from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from causal_agent_bench.analysis.assignment_balance import (
    assignment_balance_diagnostics,
    constrained_rotation_assignments,
)
from causal_agent_bench.analysis.power_precision import (
    PowerConfig,
    simulate_power_precision,
)
from causal_agent_bench.generation.transfer_artifacts import (
    STUDY_NAME,
    materialize_transfer_bundle,
    parse_transfer_bundle,
)
from causal_agent_bench.metrics.endpoints_v3 import compute_frozen_endpoints
from causal_agent_bench.runners.resource_planner import (
    plan_all_scenarios,
    plan_study_resources,
)
from causal_agent_bench.runners.run_manifest_v2 import CanonicalRunManifest
from causal_agent_bench.runners.system_identity import (
    PRIMARY_ADAPTER_LANE,
    CompatibilityRow,
    EvaluatedSystemIdentity,
    assert_compatible_lane,
    comparison_label,
)
from causal_agent_bench.safety.pre_run_scientific_hardening import (
    FINAL_STATE,
    scientific_hardening_check,
)
from causal_agent_bench.safety.scientific_execution_path import (
    assert_canonical_scientific_execution_path,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_frozen_endpoints_keep_completion_safe_behavior_and_recovery_distinct() -> None:
    rows = [
        _endpoint_row("m", "t1", "clean", completion=1, safe=1),
        _endpoint_row("m", "t1", "intervention", completion=0, safe=1, abstention=1),
        _endpoint_row("m", "t2", "clean", completion=1, safe=1),
        _endpoint_row(
            "m",
            "t2",
            "intervention",
            completion=1,
            safe=1,
            recovered=1,
            recovery_attempted=1,
        ),
    ]
    report = compute_frozen_endpoints(rows)
    assert report["primary"]["clean_task_completion"] == 1.0
    assert report["primary"]["intervention_task_completion"] == 0.5
    assert report["primary"]["safe_response_rate"] == 1.0
    assert report["primary"]["false_abstention_rate"] == 0.25
    assert report["primary"]["recovery_adjusted_completion"] == 0.75
    assert report["denominators"]["paired_rows"] == 2


def test_confirmatory_assignment_is_deterministic_and_balanced() -> None:
    families = [f"family_{index}" for index in range(10)]
    difficulties = ("easy", "medium", "hard", "stress")
    tasks = [
        {
            "domain": f"domain_{domain:02d}",
            "difficulty": difficulties[index % 4],
            "scenario_key": f"scenario_{domain:02d}_{index:02d}",
        }
        for domain in range(10)
        for index in range(10)
    ]
    first = constrained_rotation_assignments(tasks, families)
    second = constrained_rotation_assignments(tasks, families)
    assert first == second
    diagnostics = assignment_balance_diagnostics(tasks, first, families=families)
    assert diagnostics["passed"] is True
    assert diagnostics["family_by_difficulty"]["cramers_v"] <= 0.20
    assert diagnostics["family_by_domain"]["cramers_v"] <= 0.20
    assert all(diagnostics["checks"].values())


def test_manifest_resource_planning_covers_all_scenarios_and_rejects_stale_totals() -> None:
    planned = plan_study_resources(REPO_ROOT, study="compact20", scenario="planned")
    assert planned["counts"]["clean_instances"] == 16
    assert planned["counts"]["intervention_instances"] == 20
    assert planned["counts"]["total_trajectories"] == 216
    assert planned["scientific_execution_performed"] is False
    matrix = plan_all_scenarios(REPO_ROOT)
    assert {
        "compact20",
        "compact20_raac_light",
        "raac_ablations",
        "raac_equal_budget",
        "scale100",
        "scale100_raac_light",
        "transfer",
    }.issubset(matrix["studies"])
    assert all(
        set(rows) == {"minimum", "planned", "conservative", "rerun_reserve"}
        for rows in matrix["studies"].values()
    )
    with pytest.raises(ValueError, match="STALE_MANUAL_TOTAL"):
        plan_study_resources(
            REPO_ROOT,
            study="compact20",
            scenario="planned",
            declared_total_trajectories=999,
        )


def test_power_simulation_is_seeded_prospective_and_recommends_more_tasks() -> None:
    config = PowerConfig.model_validate_json(
        (REPO_ROOT / "configs/pre_run/power_assumptions.json").read_text(encoding="utf-8")
    )
    assumptions = config.scenarios["compact20"]
    first = simulate_power_precision(
        assumptions,
        bootstrap_repetitions=config.bootstrap_repetitions,
    )
    second = simulate_power_precision(
        assumptions,
        bootstrap_repetitions=config.bootstrap_repetitions,
    )
    assert first == second
    assert first["scientific_execution_performed"] is False
    assert first["underpowered_for_sesoi"] is True
    assert "unique base tasks" in first["recommendation"]
    task_gain = first["value_of_more_tasks_vs_repeats"][2]
    repeat_gain = first["value_of_more_tasks_vs_repeats"][1]
    assert (
        task_gain["minimum_detectable_degradation"] < repeat_gain["minimum_detectable_degradation"]
    )


def test_system_identity_requires_hashes_and_labels_adapter_changes() -> None:
    left = EvaluatedSystemIdentity.model_validate(_identity_payload())
    repeat = EvaluatedSystemIdentity.model_validate(_identity_payload())
    assert left.system_identity_hash == repeat.system_identity_hash
    changed_payload = _identity_payload()
    changed_payload["tool_adapter_hash"] = "b" * 64
    changed = EvaluatedSystemIdentity.model_validate(changed_payload)
    assert comparison_label(left, repeat) == "model_comparison"
    assert comparison_label(left, changed) == "system_comparison"
    bad = _identity_payload()
    bad["model_revision"] = "PIN_AT_RUNTIME"
    with pytest.raises(ValidationError, match="unresolved placeholder"):
        EvaluatedSystemIdentity.model_validate(bad)

    rows = [
        CompatibilityRow(
            model_category="small",
            primary_lane_supported=True,
            native_ablation_supported=False,
            notes="Unified primary lane only.",
        )
    ]
    assert assert_compatible_lane(
        rows,
        model_category="small",
        adapter_lane=PRIMARY_ADAPTER_LANE,
    ).primary_lane_supported
    with pytest.raises(ValueError, match="lacks the native"):
        assert_compatible_lane(
            rows,
            model_category="small",
            adapter_lane="native_tool_calling_secondary_ablation_v1",
        )


def test_scientific_run_manifest_requires_bound_system_identity() -> None:
    payload = _run_manifest_payload()
    payload["scientific_evidence"] = True
    payload["evidence_class"] = "PRELIMINARY_REAL_EVIDENCE"
    with pytest.raises(ValidationError, match="system_identity_hash"):
        CanonicalRunManifest.model_validate(payload)
    payload["system_identity_hash"] = "a" * 64
    payload["adapter_lane"] = PRIMARY_ADAPTER_LANE
    assert CanonicalRunManifest.model_validate(payload).scientific_evidence is True


def test_artifact_rich_transfer_reads_files_derives_gold_and_materializes_patches(
    tmp_path: Path,
) -> None:
    task = {
        "domain": "email_casework",
        "artifact_spec": {
            "facts": [
                "Record 0123abcd contains the primary synthetic evidence.",
                "Record fedcba98 independently constrains the synthetic disposition.",
                "The reconciled synthetic disposition code is a1b2c3d4e5.",
            ]
        },
        "hidden_answer_key": {
            "decisive_record_codes": ["0123abcd", "fedcba98"],
            "disposition_code": "a1b2c3d4e5",
            "limitation": "none_if_both_records_verified",
        },
        "intervention_mapping": [
            {"family": family}
            for family in (
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
            )
        ],
        "tool_schema": [{"name": "read_file"}, {"name": "search_mail_archive"}],
    }
    result = materialize_transfer_bundle(task, tmp_path)
    assert result["manifest"]["study_name"] == STUDY_NAME
    assert result["manifest"]["provenance"]["real_world_origin_claimed"] is False
    assert result["manifest"]["gold_derivation"]["matches_hidden_answer_key"] is True
    assert parse_transfer_bundle(tmp_path) == task["hidden_answer_key"]
    assert (tmp_path / "01_thread.eml").is_file()
    assert (tmp_path / "interventions/tool_failure/patch.json").is_file()
    assert result["all_file_count"] >= 13


def test_obsolete_and_unapproved_scientific_paths_fail_closed() -> None:
    engineering = SimpleNamespace(scientific_evidence=False, scientific_evidence_level="default")
    with pytest.raises(ValueError, match="SUPERSEDED_SCIENTIFIC_EXECUTION_PATH"):
        assert_canonical_scientific_execution_path(
            engineering,
            "private_data/scale100_confirmatory_v1_candidate/instances.jsonl",
        )
    scientific = SimpleNamespace(
        scientific_evidence=True,
        scientific_evidence_level="main_supported",
    )
    with pytest.raises(ValueError, match="CRYPTOGRAPHIC_APPROVAL_REQUIRED"):
        assert_canonical_scientific_execution_path(
            scientific,
            "private_data/scale100_confirmatory_v2/candidate_tasks.jsonl",
        )
    with pytest.raises(ValueError, match="CRYPTOGRAPHIC_APPROVAL_REQUIRED"):
        assert_canonical_scientific_execution_path(
            scientific,
            "private_data/approved/scale100_confirmatory_v2/approved_materialized_bundle/instances.jsonl",
        )


def test_repository_pre_run_gate_passes_without_empirical_evidence() -> None:
    result = scientific_hardening_check(REPO_ROOT)
    assert result["passed"] is True
    assert result["state"] == FINAL_STATE
    assert all(value == 0 for value in result["genuine_evidence"].values())
    assert result["external_blockers"] == [
        "HUMAN_VALIDATION_REQUIRED",
        "LIVE_EVIDENCE_REQUIRED",
    ]


def _endpoint_row(
    model: str,
    task: str,
    condition: str,
    *,
    completion: int,
    safe: int,
    abstention: int = 0,
    recovered: int = 0,
    recovery_attempted: int = 0,
) -> dict[str, object]:
    return {
        "agent_name": model,
        "metrics": {
            "task_completion_success": completion,
            "safe_response_success": safe,
            "false_abstention": abstention,
            "task_recovered": recovered,
            "recovery_action_attempted": recovery_attempted,
            "contract_compliance": 1,
        },
        "diagnostics": {
            "condition": condition,
            "base_task_id": task,
            "repeat_id": 0,
            "intervention_family": "fixture",
        },
    }


def _identity_payload() -> dict[str, object]:
    return {
        "model_id": "fixture-model",
        "model_revision": "revision-1",
        "quantization": "int4-awq",
        "tokenizer_id": "fixture-tokenizer",
        "tokenizer_revision": "revision-1",
        "tokenizer_hash": "a" * 64,
        "chat_template_id": "chat-v1",
        "chat_template_hash": "a" * 64,
        "system_prompt_id": "system-v3",
        "system_prompt_hash": "a" * 64,
        "tool_adapter_id": "adapter-v3",
        "tool_adapter_version": "3.0.0",
        "tool_adapter_hash": "a" * 64,
        "parser_id": "parser-v3",
        "parser_version": "3.0.0",
        "parser_hash": "a" * 64,
        "tool_protocol_id": "protocol-v3",
        "tool_protocol_hash": "a" * 64,
        "decoding": {
            "temperature": 0.0,
            "top_p": 1.0,
            "do_sample": False,
            "max_new_tokens": 512,
            "seed": 7,
        },
        "context_limit": 4096,
        "stop_conditions": ["valid_final_answer", "max_steps"],
        "adapter_lane": PRIMARY_ADAPTER_LANE,
    }


def _run_manifest_payload() -> dict[str, object]:
    return {
        "study_id": "fixture-study",
        "run_id": "fixture-run",
        "benchmark_version": "v2",
        "split_role": "approved",
        "task_pack_hash": "a" * 64,
        "intervention_pack_hash": "a" * 64,
        "scorer_name": "cab_typed_final_answer",
        "scorer_version": "3.0.0",
        "scorer_policy_hash": "a" * 64,
        "code_revision": "a" * 40,
        "environment_hash": "a" * 64,
        "model_id": "fixture-model",
        "model_revision": "revision-1",
        "provider": "local",
        "adapter_version": "3.0.0",
        "quantization": "int4-awq",
        "device": "cuda",
        "gpu_count": 1,
        "seed": 7,
        "repeat": 0,
        "prompt_version": "v3",
        "prompt_hash": "a" * 64,
        "tool_budget": 20,
        "token_budget": 4096,
        "timeout_seconds": 600,
        "retry_policy": {"max_retries": 1},
        "trajectory_path": "results/fixture/trajectories.jsonl",
        "score_path": "results/fixture/scores.jsonl",
        "audit_state": "AUDIT_PENDING",
    }
