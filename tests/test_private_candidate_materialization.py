from __future__ import annotations

import json
from pathlib import Path

import pytest

from causal_agent_bench.answer_contracts import AnswerContract
from scripts.materialize_iclr_private_candidates import materialize


def _packet(count: int = 3) -> dict:
    tasks = []
    distinctions = ["ownership", "retention", "escalation", "scheduling"]
    for index in range(count):
        distinction = distinctions[index]
        tasks.append(
            {
                "scenario_key": f"scenario-{index}",
                "domain": f"domain-{index}",
                "workflow_class": f"workflow-{index}",
                "difficulty": "medium",
                "instruction": (
                    f"Inspect the private synthetic {distinction} artifact; "
                    f"reconcile the {distinction} evidence trail and return its "
                    "documented decision with a citation."
                ),
                "artifact_type": f"artifact-{index}",
                "artifact_facts": [
                    f"evidence-{index}-a",
                    f"evidence-{index}-b",
                ],
                "answer_key": {"decision": f"decision-{index}"},
                "answer_contract": (
                    AnswerContract.ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED.value
                ),
                "tools": ["read_file", f"verify_{index}"],
                "intervention_families": ["tool_failure", "observation_conflict"],
                "licence": "repository-authored",
            }
        )
    return {
        "dataset_id": "test_private_v2",
        "split_role": "test_private_v2_protected",
        "target_count": count,
        "tasks": tasks,
    }


def test_materialization_is_deterministic_and_public_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    private = repo / "private_data"
    private.mkdir(parents=True)
    authoring = private / "authoring.json"
    authoring.write_text(json.dumps(_packet()), encoding="utf-8")
    seed = private / "seed.txt"
    seed.write_text("a" * 64, encoding="utf-8")
    public = repo / "data" / "manifests" / "public.json"
    output = private / "output"

    import scripts.materialize_iclr_private_candidates as module

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    first = materialize(authoring, seed, output, public)
    first_payload = (output / "candidate_tasks.jsonl").read_text(encoding="utf-8")
    first_public = public.read_text(encoding="utf-8")
    second = materialize(authoring, seed, output, public)
    assert (output / "candidate_tasks.jsonl").read_text(encoding="utf-8") == first_payload
    assert public.read_text(encoding="utf-8") == first_public
    assert first["private_manifest"] == second["private_manifest"]
    assert "Inspect private synthetic" not in first_public
    assert "decision-0" not in first_public
    assert first["public_manifest"]["candidate_materialized"] is True
    assert first["public_manifest"]["contains_task_ids"] is False
    assert (
        first["public_manifest"]["aggregate_diversity"][
            "noncanonical_answer_contract_task_count"
        ]
        == 0
    )
    assert first["public_manifest"]["review_commitments"][
        "completed_human_judgment_count"
    ] == 0


def test_materialization_rejects_public_authoring_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    authoring = repo / "authoring.json"
    authoring.write_text(json.dumps(_packet()), encoding="utf-8")
    private = repo / "private_data"
    private.mkdir()
    seed = private / "seed.txt"
    seed.write_text("b" * 64, encoding="utf-8")
    import scripts.materialize_iclr_private_candidates as module

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    with pytest.raises(ValueError, match="private_data"):
        materialize(
            authoring,
            seed,
            private / "output",
            repo / "public.json",
        )


def test_materialization_rejects_superficial_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    private = repo / "private_data"
    private.mkdir(parents=True)
    packet = _packet()
    packet["tasks"][1]["instruction"] = packet["tasks"][0]["instruction"]
    authoring = private / "authoring.json"
    authoring.write_text(json.dumps(packet), encoding="utf-8")
    seed = private / "seed.txt"
    seed.write_text("c" * 64, encoding="utf-8")
    import scripts.materialize_iclr_private_candidates as module

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    with pytest.raises(ValueError, match="instructions must be exactly unique"):
        materialize(
            authoring,
            seed,
            private / "output",
            repo / "public.json",
        )


def test_materialization_rejects_noncanonical_answer_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    private = repo / "private_data"
    private.mkdir(parents=True)
    packet = _packet()
    packet["tasks"][0]["answer_contract"] = "JSON_DECISION_WITH_EVIDENCE"
    authoring = private / "authoring.json"
    authoring.write_text(json.dumps(packet), encoding="utf-8")
    seed = private / "seed.txt"
    seed.write_text("d" * 64, encoding="utf-8")
    import scripts.materialize_iclr_private_candidates as module

    monkeypatch.setattr(module, "REPO_ROOT", repo)
    with pytest.raises(ValueError, match="not a canonical CAB contract"):
        materialize(
            authoring,
            seed,
            private / "output",
            repo / "public.json",
        )
