"""Power-plan, freeze, path-registry and reporting tests for reviewer-ready V2.

Provider-free and deterministic.  No test here performs model execution, genuine
human review, or produces genuine evidence.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from causal_agent_bench.review_ready_v2.cli import COMMANDS, build_parser
from causal_agent_bench.review_ready_v2.freeze import (
    FROZEN_CONFIGS,
    FROZEN_DOCS,
    FROZEN_SOURCES,
    attestation_policy,
    verify_attestation,
    verify_freeze,
)
from causal_agent_bench.review_ready_v2.power import (
    COMPACT_LABEL,
    COMPACT_STATUS,
    INFERENCE_SCOPE,
    SESOI_GRID,
    build_power_plan,
    interaction_power,
    rank_instability_simulation,
)
from causal_agent_bench.review_ready_v2.registry import active_path_registry, verify_active_paths
from causal_agent_bench.review_ready_v2.report import HONEST_STATUS_BLOCK, NEXT_HUMAN_ACTION

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports/reviewer_ready_v2"

REQUIRED_COMMANDS = (
    "generate-private-packet",
    "validate-private-packet",
    "generate-stage1-packages",
    "validate-stage1-packages",
    "ingest-reviewer-qualification",
    "ingest-stage1",
    "validate-stage1-submissions",
    "commit-stage1",
    "unlock-stage2",
    "generate-stage2-packages",
    "ingest-stage2",
    "validate-stage2-submissions",
    "build-disagreement-queue",
    "ingest-adjudication",
    "compute-agreement",
    "run-c10",
    "build-exclusion-register",
    "lock-reviewed-slice",
    "authorize-model-execution",
)


# ---------------------------------------------------------------------------
# power and claims
# ---------------------------------------------------------------------------


def test_compact20_is_labelled_a_pilot() -> None:
    assert COMPACT_LABEL == "pilot"
    assert "CONFIRMATORY" not in COMPACT_STATUS.replace("PROTOCOL_VALIDATION", "")
    assert "FEASIBILITY" in COMPACT_STATUS


def test_inference_scope_is_fixed_panel() -> None:
    assert "fixed evaluated model panel" in INFERENCE_SCOPE
    assert "superpopulation" in INFERENCE_SCOPE


def test_rank_instability_simulation_is_deterministic() -> None:
    first = rank_instability_simulation(mean_degradation=0.08, pairs=20, replicates=120)
    second = rank_instability_simulation(mean_degradation=0.08, pairs=20, replicates=120)
    assert first == second
    assert first["is_empirical_finding"] is False
    assert 0.0 <= first["probability_of_meaningful_rank_reversal"] <= 1.0


def test_sesoi_grid_includes_small_effects() -> None:
    assert SESOI_GRID == (0.03, 0.05, 0.08, 0.10, 0.15)


def test_interaction_test_is_calibrated_under_the_null() -> None:
    result = interaction_power(mean_degradation=0.10, pairs=100, replicates=120, permutations=99)
    assert result["test_calibrated_under_null"], result
    assert result["null_rejection_rate"] <= result["alpha"] + 0.04
    assert result["is_empirical_finding"] is False


def test_interaction_designation_matches_its_power() -> None:
    result = interaction_power(mean_degradation=0.10, pairs=100, replicates=120, permutations=99)
    expected = "confirmatory" if result["estimated_power"] >= 0.80 else "secondary_exploratory"
    assert result["designation"] == expected


@pytest.mark.slow
def test_power_plan_is_internally_consistent() -> None:
    plan = build_power_plan(replicates=200)
    assert plan["status"] == "CAB_POWER_PLAN_CALIBRATED"
    assert plan["compact20"]["confirmatory"] is False
    assert plan["compact20"]["adequately_powered_for_broad_claims"] is False
    assert plan["empirical_results_present"] is False
    assert plan["genuine_model_trajectories"] == 0

    claim = plan["rank_instability_claim"]
    assert "noise_floor" in claim
    assert claim["raw_reversal_probability_is_a_usable_estimand"] is False
    assert "noise floor" in claim["calibration_warning"]

    interaction = plan["model_family_interaction"]
    if interaction["designation"] == "confirmatory":
        assert all(row["estimated_power"] >= 0.80 for row in interaction["grid"])
    else:
        assert not interaction["adequate_at_degradations"] or all(
            row["estimated_power"] >= 0.80
            for row in interaction["grid"]
            if row["assumed_mean_degradation"] in interaction["adequate_at_degradations"]
        )

    primary = plan["primary_confirmatory_estimand"]
    powered = primary["adequately_powered_at_degradations"]
    for row in primary["scale100_grid"]:
        assert (row["assumed_mean_degradation"] in powered) == (row["panel_average_power"] >= 0.80)
    assert all(row["panel_average_power"] < 0.80 for row in primary["compact20_grid"])


# ---------------------------------------------------------------------------
# tracked reports
# ---------------------------------------------------------------------------


def _report(name: str) -> dict:
    path = REPORT_DIR / name
    if not path.is_file():
        pytest.skip(f"{name} has not been generated in this working tree")
    return json.loads(path.read_text())


def test_public_commitment_carries_no_private_content() -> None:
    commitment = _report("PUBLIC_PACKET_COMMITMENT.json")
    blob = json.dumps(commitment)
    assert commitment["private_bodies_committed"] is False
    assert commitment["stage2_key_stored_in_repository"] is False
    assert commitment["stage2_plaintext_persisted"] is False
    assert all(key.startswith("private_slot_") for key in commitment["pair_content_hashes"])
    for banned in ("clean_gold", "intervention_gold", "prompt", "records", "answer"):
        assert banned not in blob
    assert commitment["c10_status"] == "C10_PENDING_GENUINE_REVIEW"
    assert commitment["genuine_human_judgments"] == 0
    assert commitment["genuine_model_trajectories"] == 0


def test_readiness_report_is_honest() -> None:
    report = _report("REVIEWER_READINESS_REPORT.json")
    attestation = report["external_exact_commit_attestation"]
    assert attestation["required_before_distribution"] is True
    assert attestation["verify_with"].endswith("verify-attestation")
    assert "CAB_EXACT_COMMIT_ATTESTATION_CREATED" not in report["gates"]
    counters = report["genuine_evidence_counters"]
    assert all(value == 0 for value in counters.values())
    assert report["CAB_LEVEL5_COMPLETE"] is False
    assert report["CAB_LEVEL6_COMPLETE"] is False
    assert report["next_human_action"] == NEXT_HUMAN_ACTION
    assert set(report["honest_status"]) == set(HONEST_STATUS_BLOCK)


def test_retired_registry_report_blocks_every_prior_packet() -> None:
    registry = _report("RETIRED_PACKET_REGISTRY.json")
    assert registry["status"] == "CAB_RETIRED_PACKETS_BLOCKED"
    assert registry["retired_packet_count"] >= 5
    assert "compact20-final-private-v1" in {
        row["packet_version"] for row in registry["retired_packets"]
    }


def test_leakage_report_never_prints_values() -> None:
    report = _report("STAGE1_LEAKAGE_AUDIT.json")
    assert report["leaked_values_are_never_printed"] is True
    safe_row_keys = {
        "package",
        "sha256",
        "file_count",
        "items_value_scanned",
        "forbidden_structural_key_count",
        "forbidden_token_count",
        "archive_wide_hit_count",
        "per_item_derived_hit_count",
        "checks",
        "passed",
    }
    for row in report["packages"]:
        # The report may only carry counts, hashes and booleans - never a value.
        assert set(row) == safe_row_keys, sorted(set(row) - safe_row_keys)
        assert all(isinstance(value, int) for value in row.values() if not isinstance(value, str | bool | dict))
        assert all(isinstance(value, bool) for value in row["checks"].values())


# ---------------------------------------------------------------------------
# canonical paths and freeze
# ---------------------------------------------------------------------------


def test_active_path_registry_lists_every_workflow_command() -> None:
    registry = active_path_registry(REPO_ROOT)
    assert registry["active_private_packet_version"] == "compact20-review-ready-v2"
    assert set(REQUIRED_COMMANDS) <= set(registry["canonical_cli_commands"])
    assert registry["external_key_environment_variable"] == "CAB_STAGE2_KEY_PATH"
    assert "compact20-final-private-v1" in json.dumps(registry["superseded_paths"])


def test_canonical_tracked_paths_exist() -> None:
    report = verify_active_paths(REPO_ROOT)
    if report["missing_tracked_paths"] == ["reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json"]:
        pytest.skip("freeze has not been generated in this working tree")
    assert report["passed"], report["missing_tracked_paths"]


def test_cli_exposes_every_required_command() -> None:
    assert set(REQUIRED_COMMANDS) <= set(COMMANDS)
    parser = build_parser()
    args = parser.parse_args(["status"])
    assert args.command == "status"
    assert args.fixture is False


def test_frozen_surface_covers_the_scientific_kernel() -> None:
    for relative in FROZEN_SOURCES:
        assert (REPO_ROOT / relative).is_file(), relative
    for binding in FROZEN_CONFIGS.values():
        assert (REPO_ROOT / binding).is_file(), binding
    for binding in FROZEN_DOCS.values():
        assert (REPO_ROOT / binding).is_file(), binding


def test_scientific_freeze_verifies() -> None:
    path = REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json"
    if not path.is_file():
        pytest.skip("freeze has not been generated in this working tree")
    report = verify_freeze(REPO_ROOT)
    generator = json.loads(path.read_text())["generator"]
    committed = subprocess.run(
        ["git", "cat-file", "-e", f"{generator['source_commit']}:{generator['path']}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    structural = {
        name: value
        for name, value in report["checks"].items()
        if not name.startswith("generator_commit")
    }
    assert all(structural.values()), report["mismatched_paths"]
    if committed.returncode == 0:
        assert report["passed"], report["checks"]


def test_attestation_policy_requires_an_external_exact_commit_receipt() -> None:
    policy = attestation_policy()
    assert policy["attestation_model"] == "EXTERNAL_EXACT_COMMIT"
    assert "exact_commit" in policy["required_fields"]
    assert policy["location_template"].startswith("~/.cab/attestations/")


def test_missing_attestation_is_reported_as_pending() -> None:
    report = verify_attestation(REPO_ROOT, REPO_ROOT / "does-not-exist.json")
    assert report["passed"] is False
    assert report["status"] == "EXTERNAL_EXACT_COMMIT_ATTESTATION_PENDING"
