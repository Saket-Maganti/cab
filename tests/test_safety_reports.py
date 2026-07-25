"""Tests for low-compute evidence governance and export guards."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from causal_agent_bench.agents.mock_behavior_agent import (
    EXPECTED_FAILURE_CATEGORY,
    MOCK_BEHAVIOR_MODES,
    MockBehaviorAgent,
)
from causal_agent_bench.analysis.failure_gallery_doc import (
    build_gallery_examples,
    render_paper_short_tex,
)
from causal_agent_bench.analysis.load_results import RunResults
from causal_agent_bench.analysis.paper_fill import (
    _claim_can_be_supported,
    _export_warning_banner,
    fill_paper_from_run,
)
from causal_agent_bench.claim_ledger import (
    CLAIM_ARTIFACT_MAP,
    MANUAL_SUPPORTED_OVERRIDE_NOTE,
    load_ledger,
    update_claim_ledger,
    update_claim_ledger_from_run,
)
from causal_agent_bench.release.experiment_state import infer_experiment_state
from causal_agent_bench.safety.claim_evidence_matrix import (
    _section_allowed,
    build_claim_evidence_matrix,
)
from causal_agent_bench.safety.common import classify_run_entry, strict_bool
from causal_agent_bench.safety.export_guards import (
    apply_export_watermark,
    validate_export_source,
)
from causal_agent_bench.safety.paper_asset_eligibility import validate_paper_asset_eligibility
from causal_agent_bench.safety.paper_todo_inventory import build_paper_todo_inventory
from causal_agent_bench.safety.run_health import build_run_health_report
from causal_agent_bench.schemas import ToolSpec

REPO = Path(__file__).resolve().parents[1]


def _write_run_index(tmp_path: Path, entries: list[dict]) -> Path:
    results = tmp_path / "results"
    results.mkdir(parents=True, exist_ok=True)
    jsonl = results / "RUN_INDEX.jsonl"
    with jsonl.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return results


def _minimal_run(tmp_path: Path, name: str, metadata: dict) -> Path:
    run_dir = tmp_path / "results" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (run_dir / "checkpoint.json").write_text(
        json.dumps({"completed": metadata.get("n_instances", 1), "total": metadata.get("n_instances", 1), "status": "complete"}),
        encoding="utf-8",
    )
    (run_dir / "trajectories.jsonl").write_text("{}\n", encoding="utf-8")
    return run_dir


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    scientific = _minimal_run(
        tmp_path,
        "scientific_complete",
        {
            "run_name": "main_experiment_verified",
            "config_hash": "abc123",
            "evidence_scope": "commercial_api_experiment_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": True,
            "agents": ["gpt_agent"],
            "n_instances": 2,
        },
    )
    mock = _minimal_run(
        tmp_path,
        "mock_diag",
        {
            "run_name": "diag_mock",
            "config_hash": "mock1",
            "evidence_scope": "mock_diagnostic_only",
            "provider_type": "mock",
            "scientific_evidence": False,
            "not_real_llm_behavior": True,
            "agents": ["mock_behavior_agent"],
            "n_instances": 1,
        },
    )
    interrupted = _minimal_run(
        tmp_path,
        "interrupted_run",
        {
            "run_name": "pilot_interrupted",
            "config_hash": "int1",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": False,
            "agents": ["gpt_agent"],
            "n_instances": 3,
        },
    )
    (interrupted / "INCOMPLETE_RUN.json").write_text('{"reason": "stopped"}', encoding="utf-8")
    (interrupted / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 3, "status": "interrupted"}),
        encoding="utf-8",
    )

    entries = [
        {
            "run_id": scientific.name,
            "path": str(scientific),
            "status": "complete",
            "completion_state": "complete",
            "scientific_evidence": True,
            "evidence_level": "commercial_api_experiment_unvalidated",
            "provider_type": "openai",
            "completed_trajectories": 2,
            "expected_trajectories": 2,
            "agents": ["gpt_agent"],
        },
        {
            "run_id": mock.name,
            "path": str(mock),
            "status": "complete",
            "completion_state": "complete",
            "scientific_evidence": False,
            "evidence_level": "mock_diagnostic_only",
            "provider_type": "mock",
            "completed_trajectories": 1,
            "expected_trajectories": 1,
            "agents": ["mock_behavior_agent"],
        },
        {
            "run_id": interrupted.name,
            "path": str(interrupted),
            "status": "interrupted",
            "completion_state": "incomplete",
            "scientific_evidence": False,
            "evidence_level": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "completed_trajectories": 1,
            "expected_trajectories": 3,
            "agents": ["gpt_agent"],
        },
        {
            "run_id": "no_metadata",
            "path": str(tmp_path / "results" / "ghost"),
            "status": "unknown",
            "completion_state": "incomplete",
            "scientific_evidence": False,
            "evidence_level": "unknown",
            "provider_type": "unknown",
            "completed_trajectories": 0,
            "expected_trajectories": None,
            "agents": [],
        },
    ]
    _write_run_index(tmp_path, entries)
    return tmp_path


def test_run_health_classifications(fixture_repo: Path) -> None:
    report = build_run_health_report(fixture_repo, output_dir=fixture_repo / "reports")
    by_id = {r["run_id"]: r for r in report["runs"]}
    assert by_id["mock_diag"]["classification"] == "mock_diagnostic"
    assert by_id["interrupted_run"]["classification"] == "interrupted"
    assert by_id["scientific_complete"]["paper_eligible"] is True
    assert by_id["mock_diag"]["paper_eligible"] is False
    assert report["summary"]["interrupted_count"] >= 1


def test_strict_bool_parsing_for_evidence_gates() -> None:
    assert strict_bool("false") is False
    assert strict_bool("0") is False
    assert strict_bool("") is False
    assert strict_bool(None) is False
    assert strict_bool("no") is False
    assert strict_bool("true") is True
    assert strict_bool("1") is True
    assert strict_bool("yes") is True
    assert strict_bool("maybe") is False


def test_provider_pilot_requires_strict_scientific_metadata(tmp_path: Path) -> None:
    provider_false = _minimal_run(
        tmp_path,
        "provider_false",
        {
            "run_name": "commercial_api_pilot_false",
            "config_hash": "pf",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": "false",
            "agents": ["gpt_agent"],
            "n_instances": 1,
        },
    )
    row = classify_run_entry({"path": str(provider_false)}, tmp_path)
    assert row["classification"] != "provider_backed_pilot"
    assert row["scientific_evidence"] is False

    for provider_type in ("local", "mock", "stub"):
        run_dir = _minimal_run(
            tmp_path,
            f"{provider_type}_provider",
            {
                "run_name": f"{provider_type}_pilot",
                "config_hash": provider_type,
                "evidence_scope": "commercial_api_pilot_unvalidated",
                "provider_type": provider_type,
                "scientific_evidence": True,
                "agents": ["gpt_agent"],
                "n_instances": 1,
            },
        )
        row = classify_run_entry({"path": str(run_dir)}, tmp_path)
        assert row["classification"] != "provider_backed_pilot"

    incomplete = _minimal_run(
        tmp_path,
        "provider_incomplete",
        {
            "run_name": "commercial_api_pilot_incomplete",
            "config_hash": "inc",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": True,
            "agents": ["gpt_agent"],
            "n_instances": 3,
        },
    )
    (incomplete / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 3, "status": "interrupted"}),
        encoding="utf-8",
    )
    (incomplete / "INCOMPLETE_RUN.json").write_text('{"reason": "test"}', encoding="utf-8")
    row = classify_run_entry({"path": str(incomplete)}, tmp_path)
    assert row["classification"] != "provider_backed_pilot"

    missing_meta = tmp_path / "results" / "missing_meta_run"
    missing_meta.mkdir(parents=True)
    (missing_meta / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 1, "status": "complete"}),
        encoding="utf-8",
    )
    row = classify_run_entry({"path": str(missing_meta)}, tmp_path)
    assert row["classification"] != "provider_backed_pilot"

    complete_provider = _minimal_run(
        tmp_path,
        "complete_provider",
        {
            "run_name": "commercial_api_pilot_complete",
            "config_hash": "ok",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": True,
            "agents": ["gpt_agent"],
            "n_instances": 1,
        },
    )
    row = classify_run_entry({"path": str(complete_provider)}, tmp_path)
    assert row["classification"] == "provider_backed_pilot"
    assert row["paper_eligible"] is True


def test_claim_matrix_blocks_scientific_without_verified_runs(fixture_repo: Path) -> None:
    ledger = {
        "schema_version": 2,
        "claims": [
            {
                "claim_id": f"C{i}",
                "claim_text": f"Claim {i}",
                "short_name": f"c{i}",
                "status": "planned",
                "required_evidence": "run",
                "linked_run_dirs": [],
                "linked_tables_figures": [],
                "linked_validation_files": [],
                "current_evidence_paths": [],
                "blocking_items": [],
                "notes": "",
                "owner": "test",
                "last_updated": "2026-05-20",
            }
            for i in range(1, 11)
        ],
    }
    (fixture_repo / "docs").mkdir(exist_ok=True)
    (fixture_repo / "docs" / "claim_ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    report = build_claim_evidence_matrix(fixture_repo, output_dir=fixture_repo / "reports", write_tex=False)
    statuses = {c["claim_id"]: c["status"] for c in report["claims"]}
    assert statuses["C1"] in {"partially_supported", "blocked"}
    assert statuses["C9"] in {"engineering_only", "partially_supported"}
    assert statuses["C10"] in {"blocked", "partially_supported"}
    assert all(
        statuses[cid] != "supported"
        for cid in ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C10"]
    )


def test_paper_asset_eligibility_missing_meta(tmp_path: Path) -> None:
    tables = tmp_path / "tables"
    tables.mkdir()
    (tables / "table2_main_agent_performance.csv").write_text("agent,score\na,1\n", encoding="utf-8")
    report = validate_paper_asset_eligibility(tmp_path, output_dir=tmp_path / "reports")
    flagged = {a["path"] for a in report["flagged_assets"]}
    assert "tables/table2_main_agent_performance.csv" in flagged


def test_generated_tex_without_metadata_is_not_claim_eligible(tmp_path: Path) -> None:
    generated = tmp_path / "paper" / "latexpaper" / "generated"
    sections = tmp_path / "paper" / "latexpaper" / "sections"
    generated.mkdir(parents=True)
    sections.mkdir(parents=True)
    (generated / "07_results.tex").write_text(
        "\\section{Results}\nOur experiments demonstrate a main result.\n",
        encoding="utf-8",
    )
    (generated / "08_human_validation.tex").write_text(
        "Human validation is not yet complete.\n",
        encoding="utf-8",
    )
    (generated / "09_ablations.tex").write_text(
        "Ablation results not yet run.\n",
        encoding="utf-8",
    )
    (sections / "01_introduction.tex").write_text(
        "\\section{Introduction}\nThis section defines the benchmark.\n",
        encoding="utf-8",
    )
    report = validate_paper_asset_eligibility(tmp_path, output_dir=tmp_path / "reports")
    by_path = {asset["path"]: asset for asset in report["assets"]}
    assert by_path["paper/latexpaper/generated/07_results.tex"]["classification"] != "eligible_for_paper_claims"
    assert by_path["paper/latexpaper/generated/08_human_validation.tex"]["classification"] != "eligible_for_paper_claims"
    assert by_path["paper/latexpaper/generated/09_ablations.tex"]["classification"] != "eligible_for_paper_claims"
    assert by_path["paper/latexpaper/sections/01_introduction.tex"]["classification"] != "eligible_for_paper_claims"


def test_paper_todo_detects_placeholder(tmp_path: Path) -> None:
    paper = tmp_path / "paper" / "latexpaper" / "generated"
    paper.mkdir(parents=True)
    (paper / "results.tex").write_text(
        "% TODO: fill results\nnot yet run\nReport [N] examples and TODO_NUM later.\n",
        encoding="utf-8",
    )
    report = build_paper_todo_inventory(tmp_path, output_dir=tmp_path / "reports")
    kinds = {i["kind"] for i in report["items"]}
    assert "TODO" in kinds
    assert "not yet run" in kinds
    assert "numeric_placeholder" in kinds


def test_export_guard_refuses_mock_without_override(fixture_repo: Path) -> None:
    mock_dir = fixture_repo / "results" / "mock_diag"
    with pytest.raises(ValueError, match="refusing"):
        validate_export_source(mock_dir, operation="test")


def test_export_guard_issue_specific_overrides(fixture_repo: Path, tmp_path: Path) -> None:
    mock_dir = fixture_repo / "results" / "mock_diag"
    with pytest.raises(ValueError, match="mock/stub"):
        validate_export_source(mock_dir, allow_incomplete=True, operation="test")
    with pytest.raises(ValueError, match="scientific_evidence=false"):
        validate_export_source(mock_dir, allow_mock_stub=True, operation="test")

    guard = validate_export_source(
        mock_dir,
        allow_mock_stub=True,
        allow_engineering_only=True,
        operation="test",
    )
    assert "MOCK/STUB ONLY" in guard["watermark"]
    assert "NOT SCIENTIFIC EVIDENCE" in guard["watermark"]

    missing_meta = tmp_path / "results" / "missing_meta"
    missing_meta.mkdir(parents=True)
    (missing_meta / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 1, "status": "complete"}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing run metadata"):
        validate_export_source(
            missing_meta,
            allow_incomplete=True,
            allow_mock_stub=True,
            allow_engineering_only=True,
            allow_placeholder=True,
            operation="test",
        )


def test_export_guard_override_watermark(fixture_repo: Path) -> None:
    mock_dir = fixture_repo / "results" / "mock_diag"
    guard = validate_export_source(
        mock_dir,
        allow_mock_stub=True,
        allow_engineering_only=True,
        operation="test",
    )
    assert guard["requires_watermark"] is True
    text = apply_export_watermark("\\section{}", guard["watermark"])
    assert "NOT SCIENTIFIC EVIDENCE" in text or "MOCK" in text


def test_export_guard_accepts_scientific_fixture(fixture_repo: Path) -> None:
    run_dir = fixture_repo / "results" / "scientific_complete"
    guard = validate_export_source(run_dir, operation="test")
    assert guard["allowed"] is True


def test_claim_matrix_uses_figure_metadata(tmp_path: Path) -> None:
    run_dir = _minimal_run(
        tmp_path,
        "provider_scientific",
        {
            "run_name": "commercial_api_pilot_complete",
            "config_hash": "ok",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": True,
            "agents": ["gpt_agent"],
            "n_instances": 1,
        },
    )
    _write_run_index(
        tmp_path,
        [
            {
                "run_id": run_dir.name,
                "path": str(run_dir),
                "status": "complete",
                "completion_state": "complete",
                "provider_type": "openai",
                "scientific_evidence": True,
                "evidence_level": "commercial_api_pilot_unvalidated",
                "completed_trajectories": 1,
                "expected_trajectories": 1,
                "agents": ["gpt_agent"],
            }
        ],
    )
    figures = tmp_path / "figures"
    figures.mkdir()
    (figures / "figure_ok.png").write_bytes(b"png")
    (figures / "figure_ok.meta.json").write_text(
        json.dumps(
            {
                "scientific_evidence": True,
                "evidence_scope": "commercial_api_pilot_unvalidated",
                "eligibility": {"eligible_for_paper_claims": True},
            }
        ),
        encoding="utf-8",
    )
    (figures / "figure_engineering.png").write_bytes(b"png")
    (figures / "figure_engineering.meta.json").write_text(
        json.dumps(
            {
                "scientific_evidence": False,
                "evidence_scope": "mock_diagnostic_only",
                "eligibility": {"eligible_for_paper_claims": False, "engineering_only": True},
            }
        ),
        encoding="utf-8",
    )
    ledger = {
        "schema_version": 2,
        "claims": [
            {
                "claim_id": "C1",
                "claim_text": "Claim 1",
                "short_name": "c1",
                "status": "planned",
                "required_evidence": "figure",
                "linked_run_dirs": [],
                "linked_tables_figures": [
                    "figures/figure_ok.png",
                    "figures/figure_engineering.png",
                    "figures/figure_missing.png",
                ],
                "linked_validation_files": [],
                "current_evidence_paths": [],
                "blocking_items": [],
                "notes": "",
                "owner": "test",
                "last_updated": "2026-05-20",
            }
        ],
    }
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "claim_ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    report = build_claim_evidence_matrix(tmp_path, output_dir=tmp_path / "reports", write_tex=False)
    row = report["claims"][0]
    assert "figures/figure_ok.png" in row["eligible_artifacts"]
    assert any("figures/figure_engineering.png" in item for item in row["ineligible_artifacts"])
    assert any("figures/figure_missing.png" in item for item in row["ineligible_artifacts"])
    assert row["status"] != "supported"


def _run_results_stub(run_dir: Path, metadata: dict) -> RunResults:
    return RunResults(
        run_dir=run_dir,
        run_metadata=metadata,
        aggregate={},
        scores=[],
        instances=[],
        legacy_tasks=[],
        trajectories=[],
        scores_df=pd.DataFrame(),
        instances_df=pd.DataFrame(),
        trajectories_df=pd.DataFrame(),
    )


def _eligible_asset(repo_root: Path, rel: str) -> None:
    path = repo_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".csv":
        path.write_text("agent,score\na,1\n", encoding="utf-8")
    else:
        path.write_bytes(b"asset")
    (path.parent / f"{path.stem}.meta.json").write_text(
        json.dumps(
            {
                "scientific_evidence": True,
                "evidence_scope": "commercial_api_pilot_unvalidated",
                "eligibility": {"eligible_for_paper_claims": True},
            }
        ),
        encoding="utf-8",
    )


def test_paper_fill_claim_promotion_requires_eligible_run_and_assets(tmp_path: Path) -> None:
    metadata = {
        "run_name": "commercial_api_pilot_complete",
        "config_hash": "ok",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": True,
        "agents": ["gpt_agent"],
        "n_instances": 1,
    }
    run_dir = _minimal_run(tmp_path, "provider_scientific_for_fill", metadata)
    data = _run_results_stub(run_dir, metadata)
    _eligible_asset(tmp_path, "tables/table2_main_agent_performance.csv")
    _eligible_asset(tmp_path, "figures/figure2_clean_vs_intervention_success.png")
    assert _claim_can_be_supported(
        "C1",
        [
            "tables/table2_main_agent_performance.csv",
            "figures/figure2_clean_vs_intervention_success.png",
        ],
        data,
        tmp_path,
    )

    mock_metadata = {
        **metadata,
        "evidence_scope": "mock_diagnostic_only",
        "provider_type": "mock",
        "scientific_evidence": False,
    }
    mock_dir = _minimal_run(tmp_path, "mock_for_fill", mock_metadata)
    mock_data = _run_results_stub(mock_dir, mock_metadata)
    assert not _claim_can_be_supported(
        "C1",
        [
            "tables/table2_main_agent_performance.csv",
            "figures/figure2_clean_vs_intervention_success.png",
        ],
        mock_data,
        tmp_path,
    )

    assert not _claim_can_be_supported(
        "C1",
        ["tables/table2_main_agent_performance.csv", "figures/missing_metadata.png"],
        data,
        tmp_path,
    )
    _eligible_asset(tmp_path, "figures/figure6_trajectory_final_disagreement.png")
    table5 = tmp_path / "tables" / "table5_human_validation_agreement.csv"
    table5.write_text("status\nnot yet run\n", encoding="utf-8")
    assert not _claim_can_be_supported(
        "C3",
        ["figures/figure6_trajectory_final_disagreement.png"],
        data,
        tmp_path,
    )


def test_failure_gallery_tex_warning_is_visible(tmp_path: Path) -> None:
    examples, provenance = build_gallery_examples(None, repo_root=tmp_path)
    tex = render_paper_short_tex(examples, provenance)
    visible_lines = "\n".join(
        line for line in tex.splitlines() if not line.lstrip().startswith("%")
    )
    assert "not empirical evidence" in visible_lines
    assert "not empirical evidence" in tex


def test_mock_behaviors_instantiate_without_api() -> None:
    for mode in (
        "premature_stopper",
        "contradiction_blind",
        "memory_blind",
        "argument_sloppy",
        "recovery_weak",
        "tool_overuser",
        "final_answer_hallucinator",
        "retry_loop_agent",
    ):
        assert mode in MOCK_BEHAVIOR_MODES
        agent = MockBehaviorAgent(mock_behavior=mode)
        tool = ToolSpec(
            name="verify_fact",
            description="verify",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
        action = agent.act([], [tool])
        assert action is not None
        assert mode in EXPECTED_FAILURE_CATEGORY


def test_diagnostic_configs_cap_trajectories() -> None:
    diag_dir = REPO / "configs" / "diagnostics"
    expected = {
        "argument_sloppy",
        "contradiction_blind",
        "final_answer_hallucinator",
        "memory_blind",
        "premature_stopper",
        "recovery_weak",
        "retry_loop_agent",
        "tool_overuser",
    }
    found = set()
    for path in diag_dir.glob("mock_*.yaml"):
        text = path.read_text(encoding="utf-8")
        for mode in expected:
            if f"mock_behavior: {mode}" in text:
                found.add(mode)
        assert "max_trajectories: 3" in text or "stop_after_trajectories: 3" in text
        assert "scientific_evidence: false" in text
        assert "deployment_class: mock_diagnostic_only" in text
        assert "not_real_llm_behavior: true" in text
        assert "provider_type: local" in text
    assert expected <= found


def test_cli_run_health_smoke(fixture_repo: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "run-health",
            "--repo-root",
            str(fixture_repo),
            "--results-root",
            "results",
            "--output-dir",
            str(fixture_repo / "reports"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=fixture_repo,
    )
    assert "total_runs" in result.stdout


def test_classify_missing_metadata() -> None:
    entry = {"run_id": "x", "path": "/nonexistent/run", "status": "unknown"}
    row = classify_run_entry(entry, Path("/tmp"))
    assert row["classification"] in {"unknown_needs_review", "incomplete"}
    assert row["paper_eligible"] is False


def _ledger_with_claims(tmp_path: Path, claim_ids: list[str] | None = None) -> Path:
    ids = claim_ids or [f"C{i}" for i in range(1, 11)]
    claims = [
        {
            "claim_id": claim_id,
            "claim_text": f"Claim {claim_id}",
            "short_name": claim_id.lower(),
            "status": "planned",
            "required_evidence": "verified run",
            "linked_run_dirs": [],
            "linked_tables_figures": list(CLAIM_ARTIFACT_MAP.get(claim_id, [])),
            "linked_validation_files": [],
            "current_evidence_paths": [],
            "blocking_items": [],
            "notes": "",
            "owner": "pytest",
            "last_updated": "2026-05-20",
        }
        for claim_id in ids
    ]
    ledger_path = tmp_path / "docs" / "claim_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps({"schema_version": 2, "claims": claims}), encoding="utf-8")
    return ledger_path


def _fillable_run(tmp_path: Path, name: str, metadata: dict) -> Path:
    from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, TaskGoal, Trajectory
    from causal_agent_bench.scoring import score_run
    from causal_agent_bench.utils.io import write_jsonl

    run_dir = _minimal_run(tmp_path, name, metadata)
    base_task = BaseTask(
        task_id="unit_task",
        domain="travel",
        difficulty="easy",
        goal=TaskGoal(
            user_instruction="Pick option b and report total 10.",
            success_criteria=["Names option b", "Reports total 10"],
            required_information=["option", "total"],
            forbidden_assumptions=[],
            expected_final_answer={"option": "option_b", "total": 10},
        ),
        available_tools=["search_database", "calculate_price", "verify_fact"],
        hidden_ground_truth={"option": "option_b", "total": 10},
        gold_tool_sequence=["search_database", "calculate_price"],
        max_steps=5,
        tags=[],
        metadata={},
    )
    clean_instance = BenchmarkInstance(
        instance_id="unit_task.clean",
        base_task=base_task,
        condition="clean",
        available_tools=base_task.available_tools,
        environment_seed=1,
    )
    write_jsonl(run_dir / "instances.jsonl", [clean_instance])
    write_jsonl(
        run_dir / "trajectories.jsonl",
        [
            Trajectory(
                run_id=name,
                instance_id="unit_task.clean",
                agent_name="gpt_agent",
                model_name="gpt-test",
                steps=[],
                final_answer="option_b total 10",
                terminated_reason="final_answer",
            ),
            Trajectory(
                run_id=name,
                instance_id="unit_task.clean",
                agent_name="scripted_oracle_agent",
                model_name="oracle",
                steps=[],
                final_answer="option_b total 10",
                terminated_reason="final_answer",
            ),
        ],
    )
    score_run(run_dir)
    return run_dir


def _visible_tex_lines(tex: str) -> str:
    return "\n".join(line for line in tex.splitlines() if not line.lstrip().startswith("%"))


@pytest.mark.parametrize(
    "metadata,match",
    [
        (
            {
                "run_name": "mock_run",
                "config_hash": "m1",
                "evidence_scope": "mock_diagnostic_only",
                "provider_type": "mock",
                "scientific_evidence": False,
                "not_real_llm_behavior": True,
                "deployment_class": "mock_diagnostic_only",
                "agents": ["mock_behavior_agent"],
                "n_instances": 1,
            },
            "mock",
        ),
        (
            {
                "run_name": "stub_run",
                "config_hash": "s1",
                "evidence_scope": "pilot_stub_engineering_only",
                "provider_type": "stub",
                "scientific_evidence": False,
                "agents": ["gpt_agent"],
                "n_instances": 1,
            },
            "stub",
        ),
        (
            {
                "run_name": "local_run",
                "config_hash": "l1",
                "evidence_scope": "local_model_preliminary",
                "provider_type": "local",
                "scientific_evidence": False,
                "agents": ["gpt_agent"],
                "n_instances": 1,
            },
            "local",
        ),
        (
            {
                "run_name": "eng_run",
                "config_hash": "e1",
                "evidence_scope": "engineering_only_local_stub",
                "provider_type": "local_stub",
                "scientific_evidence": False,
                "engineering_only": True,
                "agents": ["gpt_agent"],
                "n_instances": 1,
            },
            "scientific_evidence",
        ),
    ],
)
def test_promote_to_supported_refuses_unsafe_runs(tmp_path: Path, metadata: dict, match: str) -> None:
    run_dir = _minimal_run(tmp_path, metadata["run_name"], metadata)
    ledger = _ledger_with_claims(tmp_path, ["C1"])
    with pytest.raises(ValueError, match=match):
        update_claim_ledger_from_run(
            ledger,
            run_dir,
            repo_root=tmp_path,
            claim_ids=["C1"],
            promote_to_supported=True,
        )
    payload = load_ledger(ledger)
    assert payload["claims"][0]["status"] == "planned"


def test_promote_to_supported_refuses_missing_metadata(tmp_path: Path) -> None:
    run_dir = tmp_path / "results" / "no_meta"
    run_dir.mkdir(parents=True)
    (run_dir / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 1, "status": "complete"}),
        encoding="utf-8",
    )
    ledger = _ledger_with_claims(tmp_path, ["C1"])
    with pytest.raises(ValueError, match="missing"):
        update_claim_ledger_from_run(
            ledger,
            run_dir,
            repo_root=tmp_path,
            claim_ids=["C1"],
            promote_to_supported=True,
        )


def test_promote_to_supported_refuses_scientific_evidence_false_string(tmp_path: Path) -> None:
    run_dir = _minimal_run(
        tmp_path,
        "sci_false",
        {
            "run_name": "commercial_api_pilot_false",
            "config_hash": "sf",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": "false",
            "agents": ["gpt_agent"],
            "n_instances": 1,
        },
    )
    ledger = _ledger_with_claims(tmp_path, ["C1"])
    with pytest.raises(ValueError, match="scientific_evidence"):
        update_claim_ledger_from_run(
            ledger,
            run_dir,
            repo_root=tmp_path,
            claim_ids=["C1"],
            promote_to_supported=True,
        )


def test_promote_to_supported_refuses_table5_placeholder_for_human_validation(tmp_path: Path) -> None:
    metadata = {
        "run_name": "commercial_api_pilot_complete",
        "config_hash": "ok",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": True,
        "agents": ["gpt_agent"],
        "n_instances": 1,
    }
    run_dir = _minimal_run(tmp_path, "provider_ok", metadata)
    _eligible_asset(tmp_path, "figures/figure6_trajectory_final_disagreement.png")
    table5 = tmp_path / "tables" / "table5_human_validation_agreement.csv"
    table5.parent.mkdir(parents=True, exist_ok=True)
    table5.write_text("status\nnot yet run\n", encoding="utf-8")
    ledger = _ledger_with_claims(tmp_path, ["C3"])
    with pytest.raises(ValueError, match=r"human-validation|no claims could be promoted"):
        update_claim_ledger_from_run(
            ledger,
            run_dir,
            repo_root=tmp_path,
            claim_ids=["C3"],
            promote_to_supported=True,
        )


def test_cli_update_claim_ledger_promote_refuses_unsafe_fixture(tmp_path: Path) -> None:
    run_dir = _minimal_run(
        tmp_path,
        "mock_cli",
        {
            "run_name": "mock_cli",
            "config_hash": "m",
            "evidence_scope": "mock_diagnostic_only",
            "provider_type": "mock",
            "scientific_evidence": False,
            "agents": ["mock_behavior_agent"],
            "n_instances": 1,
        },
    )
    ledger = _ledger_with_claims(tmp_path, ["C1"])
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "update-claim-ledger",
            "--ledger",
            str(ledger),
            "--repo-root",
            str(tmp_path),
            "--run-dir",
            str(run_dir),
            "--promote-to-supported",
            "--claim-id",
            "C1",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode != 0
    assert "refusing promote-to-supported" in proc.stdout + proc.stderr


def test_promote_to_supported_only_promotes_matching_claims(tmp_path: Path) -> None:
    metadata = {
        "run_name": "commercial_api_pilot_complete",
        "config_hash": "ok",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": True,
        "agents": ["gpt_agent"],
        "n_instances": 1,
    }
    run_dir = _minimal_run(tmp_path, "provider_ok", metadata)
    _eligible_asset(tmp_path, "tables/table2_main_agent_performance.csv")
    _eligible_asset(tmp_path, "figures/figure2_clean_vs_intervention_success.png")
    ledger = _ledger_with_claims(tmp_path, ["C1", "C3", "C10"])
    result = update_claim_ledger_from_run(
        ledger,
        run_dir,
        repo_root=tmp_path,
        promote_to_supported=True,
    )
    assert result["claims_promoted"] == ["C1"]
    payload = load_ledger(ledger)
    by_id = {c["claim_id"]: c for c in payload["claims"]}
    assert by_id["C1"]["status"] == "supported"
    assert by_id["C3"]["status"] == "planned"
    assert by_id["C10"]["status"] == "planned"


def test_promote_to_supported_leaves_c1_c8_c10_unsupported_without_evidence(tmp_path: Path) -> None:
    metadata = {
        "run_name": "commercial_api_pilot_complete",
        "config_hash": "ok",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": True,
        "agents": ["gpt_agent"],
        "n_instances": 1,
    }
    run_dir = _minimal_run(tmp_path, "provider_partial", metadata)
    ledger = _ledger_with_claims(tmp_path)
    with pytest.raises(ValueError, match="no claims could be promoted"):
        update_claim_ledger_from_run(
            ledger,
            run_dir,
            repo_root=tmp_path,
            promote_to_supported=True,
        )
    payload = load_ledger(ledger)
    for claim in payload["claims"]:
        if claim["claim_id"] in {"C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C10"}:
            assert claim["status"] != "supported"


def test_paper_fill_override_fragments_include_visible_not_scientific_warning(tmp_path: Path) -> None:
    metadata = {
        "run_name": "eng_fill",
        "config_hash": "ef",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": False,
        "agents": ["gpt_agent", "scripted_oracle_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "eng_fill", metadata)
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    _ledger_with_claims(repo)
    shutil_copy_claim_ledger = (REPO / "docs" / "claim_ledger.json").read_text(encoding="utf-8")
    (repo / "docs" / "claim_ledger.json").write_text(shutil_copy_claim_ledger, encoding="utf-8")

    report = fill_paper_from_run(
        run_dir,
        repo_root=repo,
        allow_engineering_only=True,
        export_assets=False,
        write_global_tables=False,
        update_ledger=False,
    )
    assert report["filled"] is True
    abstract = (repo / "paper" / "latexpaper" / "generated" / "00_abstract.tex").read_text(encoding="utf-8")
    visible = _visible_tex_lines(abstract)
    assert "NOT SCIENTIFIC EVIDENCE" in visible
    assert "Evidence warning" in visible


def test_paper_fill_mock_stub_override_includes_mock_warning(tmp_path: Path) -> None:
    metadata = {
        "run_name": "mock_fill",
        "config_hash": "mf",
        "evidence_scope": "mock_diagnostic_only",
        "provider_type": "mock",
        "scientific_evidence": False,
        "not_real_llm_behavior": True,
        "deployment_class": "mock_diagnostic_only",
        "agents": ["mock_behavior_agent", "scripted_oracle_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "mock_fill", metadata)
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "claim_ledger.json").write_text(
        (REPO / "docs" / "claim_ledger.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    fill_paper_from_run(
        run_dir,
        repo_root=repo,
        allow_engineering_only=True,
        allow_mock_stub=True,
        export_assets=False,
        write_global_tables=False,
        update_ledger=False,
    )
    results_tex = (repo / "paper" / "latexpaper" / "generated" / "07_results.tex").read_text(encoding="utf-8")
    visible = _visible_tex_lines(results_tex)
    assert "MOCK/STUB ONLY" in visible or "MOCK" in visible


def test_paper_fill_incomplete_override_includes_incomplete_warning(tmp_path: Path) -> None:
    metadata = {
        "run_name": "inc_fill",
        "config_hash": "if",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": False,
        "agents": ["gpt_agent", "scripted_oracle_agent"],
        "n_instances": 3,
    }
    run_dir = _fillable_run(tmp_path, "inc_fill", metadata)
    (run_dir / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 3, "status": "interrupted"}),
        encoding="utf-8",
    )
    (run_dir / "INCOMPLETE_RUN.json").write_text('{"reason": "test"}', encoding="utf-8")
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "claim_ledger.json").write_text(
        (REPO / "docs" / "claim_ledger.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    fill_paper_from_run(
        run_dir,
        repo_root=repo,
        allow_engineering_only=True,
        allow_incomplete=True,
        export_assets=False,
        write_global_tables=False,
        update_ledger=False,
    )
    intro = (repo / "paper" / "latexpaper" / "generated" / "01_introduction_snippet.tex").read_text(
        encoding="utf-8"
    )
    visible = _visible_tex_lines(intro)
    assert "INCOMPLETE" in visible


def test_paper_fill_scientific_fixture_omits_engineering_warning(tmp_path: Path) -> None:
    metadata = {
        "run_name": "sci_fill",
        "config_hash": "sf",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": True,
        "agents": ["gpt_agent", "scripted_oracle_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "sci_fill", metadata)
    guard = validate_export_source(run_dir, operation="test")
    banner = _export_warning_banner(guard)
    assert "NOT SCIENTIFIC EVIDENCE" not in banner


def test_ablation_export_guard_refuses_unsafe_sources(tmp_path: Path) -> None:
    from scripts.export_ablation_table import export_ablation_table

    metadata = {
        "run_name": "mock_ablation",
        "config_hash": "ma",
        "evidence_scope": "mock_diagnostic_only",
        "provider_type": "mock",
        "scientific_evidence": False,
        "not_real_llm_behavior": True,
        "deployment_class": "mock_diagnostic_only",
        "agents": ["mock_behavior_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "mock_ablation", metadata)
    with pytest.raises(ValueError, match=r"allow-mock-stub|allow-engineering-only"):
        export_ablation_table(run_dir, output_dir=tmp_path / "out")


def test_ablation_export_guard_refuses_missing_metadata(tmp_path: Path) -> None:
    from scripts.export_ablation_table import export_ablation_table

    run_dir = tmp_path / "results" / "ablation_no_meta"
    run_dir.mkdir(parents=True)
    (run_dir / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 1, "status": "complete"}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing run metadata"):
        export_ablation_table(run_dir, output_dir=tmp_path / "out")


def test_ablation_export_guard_refuses_incomplete_source(tmp_path: Path) -> None:
    from scripts.export_ablation_table import export_ablation_table

    metadata = {
        "run_name": "inc_ablation",
        "config_hash": "ia",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": True,
        "agents": ["gpt_agent"],
        "n_instances": 3,
    }
    run_dir = _fillable_run(tmp_path, "inc_ablation", metadata)
    (run_dir / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 3, "status": "interrupted"}),
        encoding="utf-8",
    )
    (run_dir / "INCOMPLETE_RUN.json").write_text('{"reason": "test"}', encoding="utf-8")
    with pytest.raises(ValueError, match="allow-incomplete"):
        export_ablation_table(run_dir, output_dir=tmp_path / "out")


def test_ablation_export_guard_allows_scientific_fixture(tmp_path: Path) -> None:
    from scripts.export_ablation_table import export_ablation_table

    metadata = {
        "run_name": "sci_ablation",
        "config_hash": "sa",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": True,
        "agents": ["gpt_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "sci_ablation", metadata)
    paths = export_ablation_table(run_dir, output_dir=tmp_path / "out")
    assert {path.suffix for path in paths} == {".csv", ".md", ".tex"}
    assert all(path.exists() for path in paths)


def test_ablation_export_override_outputs_visible_warning(tmp_path: Path) -> None:
    from scripts.export_ablation_table import export_ablation_table

    metadata = {
        "run_name": "mock_ablation_override",
        "config_hash": "mao",
        "evidence_scope": "mock_diagnostic_only",
        "provider_type": "mock",
        "scientific_evidence": False,
        "not_real_llm_behavior": True,
        "deployment_class": "mock_diagnostic_only",
        "agents": ["mock_behavior_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "mock_ablation_override", metadata)
    paths = export_ablation_table(
        run_dir,
        output_dir=tmp_path / "out",
        allow_engineering_only=True,
        allow_mock_stub=True,
    )
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.suffix in {".md", ".tex"})
    visible = _visible_tex_lines(text)
    assert "MOCK/STUB ONLY" in visible
    assert "NOT SCIENTIFIC EVIDENCE" in visible


def test_failure_gallery_engineering_override_visible_warning(tmp_path: Path) -> None:
    metadata = {
        "run_name": "gallery_eng",
        "config_hash": "ge",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": False,
        "agents": ["gpt_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "gallery_eng", metadata)
    guard = validate_export_source(
        run_dir,
        allow_engineering_only=True,
        operation="export-failure-gallery",
    )
    examples, provenance = build_gallery_examples(
        _run_results_stub(run_dir, metadata),
        repo_root=tmp_path,
        guard=guard,
    )
    tex = render_paper_short_tex(examples, provenance)
    visible = _visible_tex_lines(tex)
    assert "not scientific evidence" in visible.lower() or "NOT SCIENTIFIC" in visible


def test_failure_gallery_mock_stub_visible_warning(tmp_path: Path) -> None:
    metadata = {
        "run_name": "gallery_mock",
        "config_hash": "gm",
        "evidence_scope": "mock_diagnostic_only",
        "provider_type": "mock",
        "scientific_evidence": False,
        "not_real_llm_behavior": True,
        "agents": ["mock_behavior_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "gallery_mock", metadata)
    guard = validate_export_source(
        run_dir,
        allow_engineering_only=True,
        allow_mock_stub=True,
        operation="export-failure-gallery",
    )
    examples, provenance = build_gallery_examples(
        _run_results_stub(run_dir, metadata),
        repo_root=tmp_path,
        guard=guard,
    )
    visible = _visible_tex_lines(render_paper_short_tex(examples, provenance))
    assert "MOCK" in visible or "mock" in visible.lower()


def test_failure_gallery_incomplete_visible_warning(tmp_path: Path) -> None:
    metadata = {
        "run_name": "gallery_inc",
        "config_hash": "gi",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": False,
        "agents": ["gpt_agent"],
        "n_instances": 3,
    }
    run_dir = _fillable_run(tmp_path, "gallery_inc", metadata)
    (run_dir / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 3, "status": "interrupted"}),
        encoding="utf-8",
    )
    (run_dir / "INCOMPLETE_RUN.json").write_text('{"reason": "test"}', encoding="utf-8")
    guard = validate_export_source(
        run_dir,
        allow_engineering_only=True,
        allow_incomplete=True,
        operation="export-failure-gallery",
    )
    examples, provenance = build_gallery_examples(
        _run_results_stub(run_dir, metadata),
        repo_root=tmp_path,
        guard=guard,
    )
    visible = _visible_tex_lines(render_paper_short_tex(examples, provenance))
    assert "INCOMPLETE" in visible


def test_failure_gallery_scientific_fixture_can_omit_engineering_warning(tmp_path: Path) -> None:
    metadata = {
        "run_name": "gallery_sci",
        "config_hash": "gs",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": True,
        "agents": ["gpt_agent"],
        "n_instances": 1,
    }
    run_dir = _fillable_run(tmp_path, "gallery_sci", metadata)
    examples, provenance = build_gallery_examples(
        _run_results_stub(run_dir, metadata),
        repo_root=tmp_path,
        guard=validate_export_source(run_dir, operation="test"),
    )
    tex = render_paper_short_tex(examples, provenance)
    visible = _visible_tex_lines(tex)
    assert "engineering-only diagnostic" not in visible.lower()


def test_failure_gallery_direct_helper_uses_strict_boolean_metadata(tmp_path: Path) -> None:
    false_metadata = {
        "run_name": "gallery_false_string",
        "config_hash": "gfs",
        "evidence_scope": "commercial_api_pilot_unvalidated",
        "provider_type": "openai",
        "scientific_evidence": "false",
        "not_real_llm_behavior": "false",
        "engineering_only": "false",
        "agents": ["gpt_agent"],
        "n_instances": 1,
    }
    false_dir = _minimal_run(tmp_path, "gallery_false_string", false_metadata)
    examples, provenance = build_gallery_examples(
        _run_results_stub(false_dir, false_metadata),
        repo_root=tmp_path,
    )
    visible = _visible_tex_lines(render_paper_short_tex(examples, provenance))
    assert "not scientific evidence" in visible.lower()

    true_metadata = {
        **false_metadata,
        "run_name": "gallery_true_string",
        "config_hash": "gts",
        "scientific_evidence": "true",
    }
    true_dir = _minimal_run(tmp_path, "gallery_true_string", true_metadata)
    examples, provenance = build_gallery_examples(
        _run_results_stub(true_dir, true_metadata),
        repo_root=tmp_path,
    )
    visible = _visible_tex_lines(render_paper_short_tex(examples, provenance))
    assert "engineering-only diagnostic" not in visible.lower()


def test_experiment_state_refuses_provider_pilot_when_scientific_false(tmp_path: Path) -> None:
    run_dir = _minimal_run(
        tmp_path,
        "commercial_pilot_false",
        {
            "run_name": "commercial_api_pilot_scope_only",
            "config_hash": "pf",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": "false",
            "agents": ["gpt_agent"],
            "n_instances": 1,
        },
    )
    state = infer_experiment_state(run_dir)
    assert state["state"] != "provider_pilot_complete"


def test_experiment_state_refuses_local_and_mock_provider_types(tmp_path: Path) -> None:
    for provider_type, scope in (
        ("local", "commercial_api_pilot_unvalidated"),
        ("mock", "commercial_api_pilot_unvalidated"),
        ("stub", "commercial_api_pilot_unvalidated"),
    ):
        run_dir = _minimal_run(
            tmp_path,
            f"exp_{provider_type}",
            {
                "run_name": f"{provider_type}_pilot",
                "config_hash": provider_type,
                "evidence_scope": scope,
                "provider_type": provider_type,
                "scientific_evidence": True,
                "agents": ["gpt_agent"],
                "n_instances": 1,
            },
        )
        assert infer_experiment_state(run_dir)["state"] != "provider_pilot_complete"


def test_experiment_state_refuses_incomplete_run(tmp_path: Path) -> None:
    run_dir = _minimal_run(
        tmp_path,
        "exp_incomplete",
        {
            "run_name": "commercial_api_pilot_incomplete",
            "config_hash": "inc",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": True,
            "agents": ["gpt_agent"],
            "n_instances": 3,
        },
    )
    (run_dir / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 3, "status": "interrupted"}),
        encoding="utf-8",
    )
    (run_dir / "INCOMPLETE_RUN.json").write_text('{"reason": "test"}', encoding="utf-8")
    assert infer_experiment_state(run_dir)["state"] != "provider_pilot_complete"


def test_experiment_state_accepts_complete_provider_fixture(tmp_path: Path) -> None:
    run_dir = _minimal_run(
        tmp_path,
        "exp_provider_ok",
        {
            "run_name": "commercial_api_pilot_complete",
            "config_hash": "ok",
            "evidence_scope": "commercial_api_pilot_unvalidated",
            "provider_type": "openai",
            "scientific_evidence": True,
            "agents": ["gpt_agent"],
            "n_instances": 1,
        },
    )
    state = infer_experiment_state(run_dir)
    assert state["state"] == "provider_pilot_complete"
    assert state["paper_eligible"] is True


def test_manual_supported_refuses_without_strict_evidence(tmp_path: Path) -> None:
    ledger = _ledger_with_claims(tmp_path, ["C1"])
    evidence = tmp_path / "README.md"
    evidence.write_text("placeholder evidence", encoding="utf-8")
    with pytest.raises(ValueError, match=r"refusing manual status=supported|ineligible"):
        update_claim_ledger(
            ledger,
            claim_id="C1",
            status="supported",
            evidence_paths=[evidence.name],
            linked_run_dirs=["results/nonexistent_run"],
            repo_root=tmp_path,
        )


def test_manual_supported_force_adds_visible_warning(tmp_path: Path) -> None:
    ledger_path = tmp_path / "docs" / "claim_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "claims": [
                    {
                        "claim_id": "C9",
                        "claim_text": "Reproducibility",
                        "short_name": "c9",
                        "status": "planned",
                        "required_evidence": "smoke",
                        "linked_run_dirs": [],
                        "linked_tables_figures": [],
                        "linked_validation_files": [],
                        "current_evidence_paths": [],
                        "blocking_items": [],
                        "notes": "",
                        "owner": "pytest",
                        "last_updated": "2026-05-20",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    evidence = tmp_path / "README.md"
    evidence.write_text("manual override evidence", encoding="utf-8")
    run_dir = _minimal_run(
        tmp_path,
        "manual_force_run",
        {
            "run_name": "stub",
            "config_hash": "x",
            "evidence_scope": "mock_diagnostic_only",
            "provider_type": "mock",
            "scientific_evidence": False,
            "agents": ["mock_behavior_agent"],
            "n_instances": 1,
        },
    )
    result = update_claim_ledger(
        ledger_path,
        claim_id="C9",
        status="supported",
        evidence_paths=[evidence.name],
        linked_run_dirs=[str(run_dir.relative_to(tmp_path))],
        repo_root=tmp_path,
        force_manual_supported=True,
    )
    assert result["force_manual_supported"] is True
    claim = load_ledger(ledger_path)["claims"][0]
    assert MANUAL_SUPPORTED_OVERRIDE_NOTE in claim["notes"]


def test_cli_manual_supported_refuses_without_force(tmp_path: Path) -> None:
    ledger = _ledger_with_claims(tmp_path, ["C1"])
    (tmp_path / "README.md").write_text("evidence", encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "update-claim-ledger",
            "--ledger",
            str(ledger),
            "--repo-root",
            str(tmp_path),
            "--claim-id",
            "C1",
            "--status",
            "supported",
            "--evidence-path",
            "README.md",
            "--linked-run-dir",
            "results/ghost",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode != 0
    assert "refusing manual status=supported" in proc.stdout + proc.stderr


def test_non_supported_status_update_still_works(tmp_path: Path) -> None:
    ledger = _ledger_with_claims(tmp_path, ["C1"])
    update_claim_ledger(
        ledger,
        claim_id="C1",
        status="engineering_only",
        notes="pipeline check only",
        repo_root=tmp_path,
    )
    claim = load_ledger(ledger)["claims"][0]
    assert claim["status"] == "engineering_only"


def test_partially_supported_not_allowed_in_abstract_or_conclusion() -> None:
    for claim_id in ("C1", "C3", "C10"):
        allowed = _section_allowed(claim_id, "partially_supported")
        assert allowed["abstract"] is False
        assert allowed["conclusion"] is False
        assert allowed["limitations/future_work_only"] is True
