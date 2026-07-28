from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest
import yaml

from causal_agent_bench.generation.instances import (
    BenchmarkGenerationConfig,
    generate_benchmark,
)
from causal_agent_bench.safety.heldout_release import (
    validate_heldout_release_policy,
)
from causal_agent_bench.safety.protected_heldout import (
    find_exposed_id_reuse,
    find_text_overlaps,
    scan_artifact_for_markers,
    validate_contamination_registry_payload,
    validate_protected_heldout_architecture,
    validate_public_manifest_payload,
)
from causal_agent_bench.safety.split_registry import (
    build_canonical_split_registry,
)

ROOT = Path(__file__).resolve().parents[1]


def test_live_protected_architecture_is_fail_closed_and_passes() -> None:
    report = validate_heldout_release_policy(ROOT)
    assert report["passed"] is True, report["issues"]
    assert report["tracked_protected_payload_count"] == 0
    assert report["registered_public_contaminated_payload_count"] >= 16
    assert report["unregistered_public_contaminated_payload_count"] == 0
    assert report["release_manifest_private_payload_count"] == 0

    architecture = report["protected_architecture"]
    assert architecture["passed"] is True, architecture["issues"]
    assert architecture["private_root_ignored"] is True
    assert architecture["tracked_private_file_count"] == 0
    assert architecture["permanently_contaminated_record_count"] == 8
    assert architecture["reused_identifier_count"] == 0
    assert architecture["public_private_overlap_count"] == 0
    assert architecture["embedded_notebook_or_archive_count"] == 0
    assert architecture["private_payload_materialized"] is False


def test_public_manifest_contains_only_safe_commitments() -> None:
    path = ROOT / "data/manifests/heldout_challenge_v2_public_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert validate_public_manifest_payload(payload) == []
    serialized = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "user_instruction",
        "expected_final_answer",
        "hidden_ground_truth",
        "task_ids",
        "instance_ids",
        "seed_hex",
        "commitment_key",
    ):
        assert forbidden not in serialized


def test_public_safe_candidate_manifests_use_honest_generic_commitments() -> None:
    expected_counts = {
        "scale100_confirmatory_v2_public_manifest.json": {
            "base_task_count": 100,
            "intervention_count": 500,
            "instance_count": 600,
        },
        "naturalistic_transfer_v2_public_manifest.json": {
            "base_task_count": 60,
            "intervention_count": 300,
            "instance_count": 360,
        },
    }
    for filename, counts in expected_counts.items():
        payload = json.loads(
            (ROOT / "data/manifests" / filename).read_text(encoding="utf-8")
        )
        assert payload["schema_version"] == "cab_public_safe_candidate_manifest_v1"
        assert payload["aggregate_counts"] == counts
        assert payload["commitments"]["algorithm"] == "SHA-256"
        assert len(
            payload["commitments"]["base_task_payload_commitment_sha256"]
        ) == 64
        assert len(payload["commitments"]["private_payload_commitment_sha256"]) == 64
        assert not any("hmac" in key.lower() for key in payload["commitments"])
        for field in (
            "contains_task_ids",
            "contains_task_text",
            "contains_answers",
            "contains_intervention_payloads",
            "contains_evaluator_metadata",
            "payload_files_public",
        ):
            assert payload[field] is False


def test_public_manifest_rejects_payload_fields_and_reversible_encoding() -> None:
    path = ROOT / "data/manifests/heldout_challenge_v2_public_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["unsafe_nested"] = {
        "task_text": "private prompt",
        "encoded": "Y" * 128,
    }
    codes = {issue["code"] for issue in validate_public_manifest_payload(payload)}
    assert "public_manifest_forbidden_field" in codes
    assert "public_manifest_reversible_encoding" in codes


def test_contamination_registry_is_permanent_and_ineligible() -> None:
    path = ROOT / "data/manifests/CAB_PUBLIC_CONTAMINATION_REGISTRY.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert validate_contamination_registry_payload(payload) == []
    assert payload["policy"]["deletion_restores_secrecy"] is False
    assert payload["policy"]["history_rewrite_restores_scientific_eligibility"] is False
    for record in payload["records"]:
        assert record["confirmatory_eligible"] is False
        assert record["paper_eligible"] is False
        assert record["external_validity_eligible"] is False


def test_exposed_roles_cannot_be_mistaken_for_confirmatory_roles() -> None:
    roles = {row["role"]: row for row in build_canonical_split_registry(ROOT)["roles"]}
    contaminated = [row for row in roles.values() if row.get("contamination_record_id")]
    assert contaminated
    for row in contaminated:
        assert "confirmatory" not in row["role"]
        assert row["role"] != "heldout_challenge"
        assert row["scientific_disposition"] == "CONTAMINATED_NOT_CONFIRMATORY"
        assert row["release_tier"] == "development_release"
        assert row["confirmatory_eligible"] is False
        assert row["scientific_execution_allowed"] is False
        assert row["paper_eligible"] is False
    protected = roles["heldout_challenge_v2_protected"]
    assert protected["source"].endswith("heldout_challenge_v2_public_manifest.json")
    assert protected["public_payload"] is False
    assert protected["confirmatory_eligible"] is False
    assert protected["membership_visibility"] == "PRIVATE_COMMITMENT_ONLY"
    protected_review_roles = {
        "scale100_confirmatory_v2_protected": (100, 500, 600),
        "naturalistic_transfer_v2_protected": (60, 300, 360),
    }
    for role_name, expected_counts in protected_review_roles.items():
        row = roles[role_name]
        base_count, intervention_count, instance_count = expected_counts
        assert row["unique_base_task_count"] == base_count
        assert row["intervention_count"] == intervention_count
        assert row["instance_count"] == instance_count
        assert row["status"] == "HUMAN_INPUT_REQUIRED"
        assert row["membership_visibility"] == "PRIVATE_COMMITMENT_ONLY"
        assert row["public_payload"] is False
        assert row["confirmatory_eligible"] is False
        assert row["scientific_execution_allowed"] is False
        assert row["paper_eligible"] is False


def test_exposed_identifier_and_near_duplicate_reuse_are_detected() -> None:
    assert find_exposed_id_reuse(
        {"public_task_1"},
        {"main500_v1"},
        {
            "fresh_private_task",
            "public_task_1",
            "main500_v1__task_9",
        },
    ) == ["main500_v1__task_9", "public_task_1"]

    public = ["Reconcile the disputed invoice using the signed purchase order and tax record."]
    private = [
        "Reconcile the disputed invoice using the signed purchase order and tax record.",
        "Diagnose a novel deployment failure from a private incident timeline.",
    ]
    overlaps = find_text_overlaps(public, private)
    assert overlaps == [{"private_index": 0, "similarity": 1.0, "exact": True}]


def test_notebook_and_archive_marker_scans_detect_embedded_content(
    tmp_path: Path,
) -> None:
    marker = "cab_private_marker_71f9"
    notebook = tmp_path / "unsafe.ipynb"
    notebook.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": [f"PRIVATE_ID = '{marker}'"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("payload.json", json.dumps({"private_id": marker}))
    clean = tmp_path / "clean.ipynb"
    clean.write_text('{"cells": []}', encoding="utf-8")

    assert scan_artifact_for_markers(notebook, {marker}) is True
    assert scan_artifact_for_markers(archive, {marker}) is True
    assert scan_artifact_for_markers(clean, {marker}) is False


def test_public_generator_cannot_create_confirmatory_pack(
    tmp_path: Path,
) -> None:
    config = BenchmarkGenerationConfig(
        seed=17,
        benchmark_version="forbidden-confirmatory",
        id_namespace="private_v2",
        num_base_tasks=1,
        domains=["travel_planning"],
        interventions_per_task=0,
        output_dir=str(tmp_path / "forbidden"),
        scientific_disposition="PRIVATE_CANDIDATE_PENDING_REVIEW",
        confirmatory_eligible=True,
    )
    with pytest.raises(ValueError, match="public deterministic generator"):
        generate_benchmark(config)
    assert not Path(config.output_dir).exists()


def test_legacy_generation_configs_are_explicitly_contaminated() -> None:
    for relative in (
        "configs/generate_scale100_confirmatory_v1.yaml",
        "configs/generate_naturalistic_transfer_v1.yaml",
        "configs/generate_main500_confirmatory_v1.yaml",
    ):
        payload = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
        assert payload["scientific_disposition"] == "CONTAMINATED_NOT_CONFIRMATORY"
        assert payload["confirmatory_eligible"] is False


def test_private_root_is_ignored_and_untracked() -> None:
    ignored = subprocess.run(
        [
            "git",
            "check-ignore",
            "--quiet",
            "private_data/heldout_challenge_v2/protected_tasks.jsonl",
        ],
        cwd=ROOT,
        check=False,
    )
    assert ignored.returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files", "--", "private_data/"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert tracked.stdout.strip() == ""


def test_exposure_inventory_has_required_per_artifact_fields() -> None:
    path = ROOT / "reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["repository"]["history_rewritten"] is False
    assert payload["summary"]["artifact_count"] == len(payload["artifacts"])
    assert payload["summary"]["artifact_count"] > 0
    required = {
        "path",
        "current_tracking_state",
        "exposure_commit",
        "task_text_exposed",
        "answer_exposed",
        "intervention_metadata_exposed",
        "evaluator_metadata_exposed",
        "severity",
        "scientific_disposition",
        "allowed_future_use",
    }
    assert all(required <= set(row) for row in payload["artifacts"])
    by_path = {row["path"]: row for row in payload["artifacts"]}
    exposed = by_path["data/processed/main500_confirmatory_v1_candidate/heldout_instances.jsonl"]
    assert exposed["exposure_commit"].startswith("ca9c13b")
    assert exposed["task_text_exposed"] is True
    assert exposed["answer_exposed"] is True
    assert exposed["intervention_metadata_exposed"] is True
    assert exposed["evaluator_metadata_exposed"] is True
    assert exposed["scientific_disposition"] == "CONTAMINATED_NOT_CONFIRMATORY"


def test_history_policy_forbids_scientific_restoration_by_rewrite() -> None:
    text = (ROOT / "docs/PUBLIC_HELDOUT_CONTAMINATION_AND_HISTORY_POLICY.md").read_text(
        encoding="utf-8"
    )
    assert "No history rewrite is authorized" in text
    assert "does **not** change any scientific disposition" in text
    assert "deletion" in text.lower()
    assert "private_data/heldout_challenge_v2/" in text


def test_direct_architecture_validator_matches_release_gate() -> None:
    report = validate_protected_heldout_architecture(ROOT)
    assert report["passed"] is True, report["issues"]
