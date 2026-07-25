"""Fixture-only tests for mega cleanup pass (no runs, no providers)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from causal_agent_bench.safety.answer_leakage_repair import validate_answer_leakage_cleared
from causal_agent_bench.safety.common import compute_run_index_freshness
from causal_agent_bench.safety.provider_pilot_preflight import validate_provider_pilot_preflight
from causal_agent_bench.safety.static_leakage import check_static_leakage_for_dataset


def test_webshadow_docs_hub_instruction_has_no_answer_leak() -> None:
    dataset = Path("data/processed/web_shadow_25")
    if not dataset.exists():
        return
    report = check_static_leakage_for_dataset(dataset, repo_root=Path("."))
    blockers = [
        c
        for c in report.get("root_causes") or []
        if c.get("cluster_classification") == "answer_leakage" and c.get("leakage_risk") == "blocker"
    ]
    assert blockers == [], f"answer leakage blockers remain: {[b.get('root_cause_id') for b in blockers]}"


def test_heldout_instances_validate_after_repair() -> None:
    path = Path("data/processed/web_shadow_25/heldout_instances.jsonl")
    if not path.exists():
        return
    result = validate_answer_leakage_cleared(Path("."), path)
    assert result.get("passed"), result.get("remaining")


def test_stale_index_detection_fixture(tmp_path: Path) -> None:
    results = tmp_path / "results"
    results.mkdir()
    for name in ("run_a", "run_b"):
        run_dir = results / name
        run_dir.mkdir()
        (run_dir / "run_metadata.json").write_text('{"run_id": "' + name + '"}\n', encoding="utf-8")
    (results / "RUN_INDEX.jsonl").write_text(json.dumps({"run_id": "run_a"}) + "\n", encoding="utf-8")
    freshness = compute_run_index_freshness(tmp_path, results_root=results)
    assert freshness["index_stale"] is True
    assert freshness["live_run_count"] == 2
    assert freshness["indexed_run_count"] == 1


def test_provider_template_not_live_ready() -> None:
    report = validate_provider_pilot_preflight(
        Path("configs/provider_pilot_tiny_template.yaml"),
        repo_root=Path("."),
    )
    assert report["verdicts"]["ready_for_live_provider_run"] is False


def test_approved_provider_config_requires_self_authorization_and_blocks_live_run() -> None:
    approval = Path("docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md")
    approved = Path("configs/provider_pilot_tiny_APPROVED.yaml")
    assert approval.exists()
    assert approved.exists()
    raw = yaml.safe_load(approved.read_text(encoding="utf-8"))
    assert raw["allow_paid_calls"] is False
    assert raw["approval"]["approved_for_dry_run"] is True
    assert raw["approval"]["approved_for_live_run"] is False
    assert raw["scientific_evidence"] is False


def test_dry_run_checklist_forbids_live_run() -> None:
    text = Path("docs/PROVIDER_PILOT_DRY_RUN_CHECKLIST.md").read_text(encoding="utf-8")
    assert "Forbidden before live approval" in text


def test_real_template_safety_fields() -> None:
    raw = yaml.safe_load(Path("configs/provider_pilot_tiny_template.yaml").read_text(encoding="utf-8"))
    assert raw["allow_paid_calls"] is False
    assert raw["template_only"] is True
    assert raw["scientific_evidence"] is False
