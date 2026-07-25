from __future__ import annotations

from pathlib import Path

import pytest

from causal_agent_bench.runners.run_manifest_v2 import (
    CanonicalRunManifest,
    append_run_ledger,
    validate_merge_manifests,
    validate_run_ledger,
    write_manifest_template,
)


def _manifest(**updates):
    payload = {
        "study_id": "fixture-study",
        "run_id": "fixture-run",
        "benchmark_version": "fixture-v1",
        "split_role": "dev_fixture",
        "task_pack_hash": "a" * 64,
        "intervention_pack_hash": "b" * 64,
        "scorer_name": "typed",
        "scorer_version": "1",
        "scorer_policy_hash": "c" * 64,
        "code_revision": "d" * 40,
        "environment_hash": "e" * 64,
        "model_id": "fake-adapter",
        "model_revision": "fixture",
        "provider": "offline_fixture",
        "adapter_version": "1",
        "quantization": "none",
        "device": "cpu",
        "gpu_count": 0,
        "seed": 7,
        "repeat": 0,
        "prompt_version": "fixture-v1",
        "prompt_hash": "f" * 64,
        "tool_budget": 2,
        "token_budget": 128,
        "timeout_seconds": 10,
        "retry_policy": {"max_retries": 0, "equal_across_models": True},
        "trajectory_path": "tmp/trajectories.jsonl",
        "score_path": "tmp/scores.jsonl",
        "audit_state": "FIXTURE_ONLY",
        "evidence_class": "FIXTURE_ONLY",
        "scientific_evidence": False,
        "paper_eligible": False,
    }
    payload.update(updates)
    return CanonicalRunManifest.model_validate(payload)


def test_append_only_ledger_hash_chain_and_dedup(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    first = _manifest()
    assert append_run_ledger(path, first)["appended"] is True
    assert append_run_ledger(path, first)["deduplicated"] is True
    second = _manifest(run_id="fixture-run-2", repeat=1)
    assert append_run_ledger(path, second)["appended"] is True
    assert validate_run_ledger(path) == []
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_conflicting_duplicate_run_id_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    append_run_ledger(path, _manifest())
    with pytest.raises(ValueError, match="conflicting ledger"):
        append_run_ledger(path, _manifest(seed=999))


def test_merge_validator_is_exact_and_fail_closed() -> None:
    manifest = _manifest()
    report = validate_merge_manifests(
        [manifest],
        completed_keys=[("a", 0), ("b", 0)],
        expected_task_ids=["a", "b"],
        expected_repeats=[0],
    )
    assert report["passed"] is True
    bad = validate_merge_manifests(
        [manifest],
        completed_keys=[("a", 0), ("a", 0)],
        expected_task_ids=["a", "b"],
        expected_repeats=[0],
    )
    assert bad["passed"] is False
    assert bad["duplicate_keys"] == [("a", 0)]
    assert bad["missing_keys"] == [("b", 0)]


def test_paper_eligibility_requires_audited_real_evidence() -> None:
    with pytest.raises(ValueError, match="PAPER_ELIGIBLE_EVIDENCE"):
        _manifest(paper_eligible=True)


def test_template_is_valid_and_non_runnable(tmp_path: Path) -> None:
    path = write_manifest_template(tmp_path / "template.json")
    text = path.read_text(encoding="utf-8")
    assert "REPLACE_BEFORE_EXECUTION" in text
    assert '"scientific_evidence": false' in text
    assert '"paper_eligible": false' in text
    assert "ESTIMATE_NOT_MEASURED" in text

