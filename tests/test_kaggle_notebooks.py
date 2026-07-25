from __future__ import annotations

import json
from pathlib import Path

import pytest

from causal_agent_bench.kaggle_fixture import (
    FIXTURE_EVIDENCE_CLASS,
    assert_shards_complete_and_disjoint,
    build_fixture_work_items,
    deterministic_shards,
    merge_fixture_shards,
    run_fixture_worker,
    verify_integrity_manifest,
    write_integrity_manifest,
)
from scripts.build_kaggle_notebooks import write_notebooks
from scripts.validate_kaggle_notebooks import (
    EXPECTED_NOTEBOOKS,
    NOTEBOOK_DIR,
    validate_all,
    validate_notebook_static,
)


def test_exact_nine_kaggle_notebooks_exist_and_match_generator() -> None:
    observed = {path.name for path in NOTEBOOK_DIR.glob("*.ipynb")}
    assert observed == set(EXPECTED_NOTEBOOKS)
    assert len(observed) == 9
    write_notebooks(check=True)


def test_kaggle_notebook_static_validator_returns_structured_pass() -> None:
    report = validate_all(execute_offline=False)
    assert report["ok"] is True
    assert report["expected_notebooks"] == 9
    assert report["validated_notebooks"] == 9
    assert report["scientific_execution_performed"] is False
    assert report["issues"] == []
    assert all(row["static_checks"] >= 20 for row in report["results"])


def test_validator_reports_a_missing_selected_notebook(tmp_path: Path) -> None:
    report = validate_all(
        selected=[str(tmp_path / "missing.ipynb")],
        execute_offline=True,
    )
    assert report["ok"] is False
    assert report["validated_notebooks"] == 0
    assert report["issues"][0]["check"] == "inventory"


def test_all_kaggle_notebooks_execute_offline_fixture_path() -> None:
    report = validate_all(execute_offline=True)
    assert report["ok"] is True
    assert report["offline_executed_notebooks"] == 9
    assert report["offline_fixture_receipts"] == 9 * 8
    assert report["scientific_execution_performed"] is False
    assert all(row["offline_executed"] is True for row in report["results"])


@pytest.mark.parametrize(
    ("mutation", "expected_check"),
    [
        ("live_true", "live_default"),
        ("hardcoded_home", "paths"),
        ("cell_order", "cell_order"),
        ("syntax", "python_syntax"),
    ],
)
def test_static_validator_rejects_unsafe_or_invalid_notebooks(
    tmp_path: Path,
    mutation: str,
    expected_check: str,
) -> None:
    source = NOTEBOOK_DIR / EXPECTED_NOTEBOOKS[0]
    notebook = json.loads(source.read_text(encoding="utf-8"))
    if mutation == "live_true":
        unsafe_live_default = "RUN_LIVE = " + "True"
        notebook["cells"][1]["source"] = notebook["cells"][1]["source"].replace(
            "RUN_LIVE = False",
            unsafe_live_default,
        )
    elif mutation == "hardcoded_home":
        unsafe_home = "/" + "Users/example/private"
        notebook["cells"][1]["source"] += f'\nUNSAFE_PATH = Path("{unsafe_home}")\n'
    elif mutation == "cell_order":
        notebook["cells"][2], notebook["cells"][3] = (
            notebook["cells"][3],
            notebook["cells"][2],
        )
    elif mutation == "syntax":
        notebook["cells"][2]["source"] += "\nif broken syntax\n"
    else:
        raise AssertionError(f"unhandled mutation {mutation}")
    mutated = tmp_path / source.name
    mutated.write_text(json.dumps(notebook), encoding="utf-8")

    result, _ = validate_notebook_static(mutated)
    assert result.ok is False
    assert expected_check in {issue.check for issue in result.issues}


def test_fixture_sharding_is_deterministic_disjoint_and_complete() -> None:
    rows = build_fixture_work_items("TEST_NOTEBOOK", 11)
    first = deterministic_shards(rows, worker_count=2)
    second = deterministic_shards(list(reversed(rows)), worker_count=2)
    assert first == second
    expected = {str(row["item_id"]) for row in rows}
    assert_shards_complete_and_disjoint(first, expected_ids=expected)
    assert {str(row["item_id"]) for row in first[0]}.isdisjoint(
        {str(row["item_id"]) for row in first[1]}
    )


def test_fixture_checkpoint_resume_is_idempotent_and_model_free(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixture"
    rows = build_fixture_work_items("RECOVERY_TEST", 6)
    shards = deterministic_shards(rows, worker_count=2)
    for worker_id, shard in enumerate(shards):
        first = run_fixture_worker(
            fixture_root,
            worker_id=worker_id,
            rows=shard,
            max_new_items=1,
        )
        assert first["processed_this_call"] == 1
        resumed = run_fixture_worker(fixture_root, worker_id=worker_id, rows=shard)
        assert resumed["pending"] == 0
        repeated = run_fixture_worker(fixture_root, worker_id=worker_id, rows=shard)
        assert repeated["processed_this_call"] == 0

    report = merge_fixture_shards(
        fixture_root,
        expected_item_ids={str(row["item_id"]) for row in rows},
        worker_count=2,
    )
    assert report["status"] == "FIXTURE_MERGE_COMPLETE"
    receipts_path = fixture_root / "merged" / "fixture_receipts.jsonl"
    receipts = [
        json.loads(line)
        for line in receipts_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    result_shaped_fields = {
        "answer",
        "final_answer",
        "label",
        "metric",
        "model_output",
        "prediction",
        "score",
        "trajectory",
    }
    assert all(row["evidence_class"] == FIXTURE_EVIDENCE_CLASS for row in receipts)
    assert all(not (set(row) & result_shaped_fields) for row in receipts)


def test_fixture_merge_and_manifest_fail_closed_on_corruption(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixture"
    rows = build_fixture_work_items("CORRUPTION_TEST", 4)
    shards = deterministic_shards(rows, worker_count=2)
    for worker_id, shard in enumerate(shards):
        run_fixture_worker(fixture_root, worker_id=worker_id, rows=shard)

    expected = {str(row["item_id"]) for row in rows}
    merge_fixture_shards(
        fixture_root,
        expected_item_ids=expected,
        worker_count=2,
    )
    write_integrity_manifest(fixture_root)
    assert verify_integrity_manifest(fixture_root)["ok"] is True

    merged = fixture_root / "merged" / "fixture_receipts.jsonl"
    merged.write_text(merged.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
    verification = verify_integrity_manifest(fixture_root)
    assert verification["ok"] is False
    assert any(
        problem.startswith(("size:", "sha256:"))
        for problem in verification["problems"]
    )

    duplicate = json.loads(
        (fixture_root / "shards" / "worker_00" / "fixture_receipts.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    worker_one = fixture_root / "shards" / "worker_01" / "fixture_receipts.jsonl"
    worker_one.write_text(
        worker_one.read_text(encoding="utf-8") + json.dumps(duplicate) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicates"):
        merge_fixture_shards(
            fixture_root,
            expected_item_ids=expected,
            worker_count=2,
        )
