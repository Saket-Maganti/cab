from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.split_registry import (
    CANONICAL_SPLIT_REGISTRY_PATH,
    build_canonical_split_registry,
    validate_canonical_split_registry,
    write_canonical_split_registry,
)
from scripts.generate_cab_split_registry import main as split_registry_main


def test_live_study_roles_are_materialized_hashed_and_disjoint(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    payload = build_canonical_split_registry(root)
    assert payload["role_count"] == 9
    assert payload["cross_role_overlap_count"] == 0
    assert payload["passed"] is True
    for row in payload["roles"]:
        assert row["source_exists"] is True
        assert len(row["source_sha256"]) == 64
        assert len(row["membership_sha256"]) == 64
        assert row["paper_eligible"] is False
        assert row["scientific_execution_allowed"] is False

    output = tmp_path / "registry.json"
    write_canonical_split_registry(root, output_path=output)
    assert validate_canonical_split_registry(root, registry_path=output) == []


def test_confirmatory_role_counts_are_explicit() -> None:
    root = Path(__file__).resolve().parents[1]
    roles = {
        row["role"]: row for row in build_canonical_split_registry(root)["roles"]
    }
    assert roles["compact20_pilot"]["candidate_count"] == 20
    assert roles["compact20_pilot"]["instance_count"] == 30
    assert roles["scale100_public_development_v1"]["unique_base_task_count"] == 100
    assert roles["main500_public_development_v1"]["unique_base_task_count"] == 500
    assert roles["heldout_challenge_v1_contaminated"]["unique_base_task_count"] == 50
    assert roles["naturalistic_public_development_v1"]["unique_base_task_count"] == 72
    protected = roles["heldout_challenge_v2_protected"]
    assert protected["unique_base_task_count"] == 50
    assert protected["instance_count"] == 300
    assert protected["membership_visibility"] == "PRIVATE_COMMITMENT_ONLY"
    assert protected["public_payload"] is False
    assert protected["confirmatory_eligible"] is False
    scale_v2 = roles["scale100_confirmatory_v2_protected"]
    assert scale_v2["unique_base_task_count"] == 100
    assert scale_v2["intervention_count"] == 500
    assert scale_v2["instance_count"] == 600
    assert scale_v2["status"] == "HUMAN_INPUT_REQUIRED"
    assert scale_v2["membership_visibility"] == "PRIVATE_COMMITMENT_ONLY"
    naturalistic_v2 = roles["naturalistic_transfer_v2_protected"]
    assert naturalistic_v2["unique_base_task_count"] == 60
    assert naturalistic_v2["intervention_count"] == 300
    assert naturalistic_v2["instance_count"] == 360
    assert naturalistic_v2["status"] == "HUMAN_INPUT_REQUIRED"
    assert naturalistic_v2["membership_visibility"] == "PRIVATE_COMMITMENT_ONLY"


def test_split_registry_cli_check_is_read_only_and_passes(capsys) -> None:
    root = Path(__file__).resolve().parents[1]
    registry = root / CANONICAL_SPLIT_REGISTRY_PATH
    before = registry.read_bytes()

    assert split_registry_main(["--check"]) == 0

    assert registry.read_bytes() == before
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "check"
    assert payload["passed"] is True
