from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.analysis.hierarchical_power import (
    validate_hierarchical_power_design,
)
from causal_agent_bench.cli_parsers import build_parser
from causal_agent_bench.runners.smoke_calibration import (
    validate_smoke_and_staged_raac_plan,
)
from causal_agent_bench.safety.executable_reachability import (
    run_executable_reachability_check,
    run_gold_reconstruction_check,
    run_intervention_isolation_check,
    run_static_reachability_check,
)
from causal_agent_bench.safety.two_stage_review import validate_stage2_unlock

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_compact20_evidence_bundles_are_inspectable_and_complete() -> None:
    result = json.loads(
        (REPO_ROOT / "data/compact20_reviewed/reviewer_evidence/bundle_index.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["status"] == "CAB_COMPACT_REVIEW_EVIDENCE_BUNDLES_READY"
    assert result["candidate_count"] == 20
    assert result["gold_reconstruction_passed_count"] == 20
    assert result["intervention_isolation_passed_count"] == 20
    assert result["unsupported_fact_count"] == 0
    for row in result["bundles"]:
        bundle = json.loads((REPO_ROOT / row["path"]).read_text(encoding="utf-8"))
        assert bundle["artifact_inventory"]
        assert bundle["required_fact_ids"]
        assert bundle["redactions"]["model_identity_absent"] is True


def test_two_stage_packet_keeps_gold_and_scorer_out_of_stage1() -> None:
    packet_dir = REPO_ROOT / "data/human_validation/compact20_two_stage_review"
    packet = json.loads((packet_dir / "packet_manifest.json").read_text(encoding="utf-8"))
    assert packet["status"] == "CAB_TWO_STAGE_HUMAN_REVIEW_READY"
    assert packet["stage1_gold_included"] is False
    assert packet["stage1_intended_route_included"] is False
    assert packet["stage1_scorer_included"] is False
    assert packet["stage2_locked"] is True
    assert packet["genuine_human_review_rows"] == 0
    assert validate_stage2_unlock(packet_dir)["passed"] is False
    first = json.loads(
        (packet_dir / "stage1_review_items.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    serialized = json.dumps(first, sort_keys=True)
    assert "gold_answer_policy" not in serialized
    assert "scorer_policy" not in serialized


def test_static_and_executable_reachability_are_distinct_and_pass_20_of_20() -> None:
    static = run_static_reachability_check(REPO_ROOT)
    executable = run_executable_reachability_check(REPO_ROOT)
    gold = run_gold_reconstruction_check(REPO_ROOT)
    isolation = run_intervention_isolation_check(REPO_ROOT)
    assert static["gate_kind"] == "static_intervention_policy_reachability"
    assert static["passed_count"] == 20
    assert executable["gate_kind"] == "executable_intervention_reachability"
    assert executable["passed_count"] == 20
    assert executable["unsupported_fact_count"] == 0
    assert gold["passed_count"] == 20
    assert isolation["passed_count"] == 20


def test_hierarchical_power_and_staged_resource_plans_validate() -> None:
    power = json.loads(
        (REPO_ROOT / "reports/final_pre_review/HIERARCHICAL_POWER_DESIGN.json").read_text(
            encoding="utf-8"
        )
    )
    assert power["models_are_independent_task_replicates"] is False
    assert power["automatic_model_count_ess_multiplier"] is False
    assert validate_hierarchical_power_design(REPO_ROOT)["passed"] is True
    resources = {
        "smoke": json.loads(
            (REPO_ROOT / "reports/final_pre_review/SMOKE_CALIBRATION_READINESS.json").read_text(
                encoding="utf-8"
            )
        ),
        "staged_raac": json.loads(
            (REPO_ROOT / "reports/final_pre_review/STAGED_RAAC_PLAN.json").read_text(
                encoding="utf-8"
            )
        ),
    }
    assert resources["smoke"]["gpu_runtime_label"] == ("ASSUMPTION_BASED_PRE_SMOKE_PROJECTION")
    assert resources["staged_raac"]["full_81000_trajectory_run_is_immediate_default"] is False
    assert validate_smoke_and_staged_raac_plan(REPO_ROOT)["passed"] is True


def test_required_final_pre_review_cli_surfaces_parse() -> None:
    parser = build_parser()
    commands = (
        ["benchmark", "static-reachability-check"],
        ["benchmark", "executable-reachability-check"],
        ["benchmark", "gold-reconstruction-check"],
        ["benchmark", "intervention-isolation-check"],
        ["approval", "verify", "--fixture"],
        ["power", "validate"],
        ["final-pre-review", "check"],
    )
    assert all(parser.parse_args(command).command for command in commands)
