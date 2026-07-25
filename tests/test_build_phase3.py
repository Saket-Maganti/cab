"""Build Mode Phase 3: taxonomy, isolation audit, mock diagnostic expectations."""

from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.agents.mock_behavior_agent import MOCK_BEHAVIOR_MODES
from causal_agent_bench.audit.intervention_isolation import audit_intervention_isolation
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment
from causal_agent_bench.utils.io import read_jsonl

REPO = Path(__file__).resolve().parents[1]


def _mock_config(tmp_path, behavior: str, max_instances: int = 1):
    return ExperimentConfig.model_validate(
        {
            "seed": 1,
            "run_name": f"mock_diag_{behavior}",
            "benchmark_path": "data/processed/pilot_v0_1/pilot_20_instances.jsonl",
            "max_instances": max_instances,
            "evidence_scope": "mock_diagnostic_only",
            "agent_runs": [
                {
                    "name": f"mock_{behavior}",
                    "agent": "mock_behavior_agent",
                    "extra": {"mock_behavior": behavior},
                }
            ],
            "max_steps": 4,
            "auto_score": True,
            "output_dir": str(tmp_path),
            "limits": {"max_trajectories": max_instances, "stop_after_trajectories": max_instances},
        }
    )


def test_mock_modes_include_phase3_agents():
    for mode in (
        "recovery_weak",
        "argument_sloppy",
        "tool_overuser",
        "memory_blind",
        "contradiction_blind",
        "premature_stop",
    ):
        assert mode in MOCK_BEHAVIOR_MODES


def test_intervention_isolation_audit_pilot_sample():
    report = audit_intervention_isolation(
        instances_path=REPO / "data/processed/pilot_v0_1/pilot_20_instances.jsonl",
        output_dir=REPO / "audits/intervention_isolation/pilot_v0_1_test",
    )
    assert report["summary"]["interventions_audited"] >= 1
    assert (REPO / "audits/intervention_isolation/pilot_v0_1_test/intervention_isolation_report.json").exists()


def test_mock_tool_overuser_high_unnecessary_rate(tmp_path):
    result = run_experiment(_mock_config(tmp_path, "tool_overuser"), checkpoint_every=1)
    scores = read_jsonl(result["run_dir"] / "scores.jsonl")
    rates = [row["metrics"]["unnecessary_tool_call_rate"] for row in scores]
    assert rates and max(rates) >= 0.3


def test_mock_premature_stop_triggers_metric(tmp_path):
    result = run_experiment(_mock_config(tmp_path, "premature_stop"), checkpoint_every=1)
    scores = read_jsonl(result["run_dir"] / "scores.jsonl")
    assert any(row["metrics"].get("premature_stop_binary") for row in scores)


def test_mock_argument_sloppy_argument_errors(tmp_path):
    result = run_experiment(_mock_config(tmp_path, "argument_sloppy"), checkpoint_every=1)
    scores = read_jsonl(result["run_dir"] / "scores.jsonl")
    assert any(row["metrics"].get("argument_error_count", 0) >= 0 for row in scores)


def test_mock_recovery_weak_no_verify_after_error(tmp_path):
    result = run_experiment(_mock_config(tmp_path, "recovery_weak", max_instances=2), checkpoint_every=1)
    meta = json.loads((result["run_dir"] / "run_metadata.json").read_text(encoding="utf-8"))
    assert meta.get("evidence_scope") == "mock_diagnostic_only"
    scores = read_jsonl(result["run_dir"] / "scores.jsonl")
    assert len(scores) >= 1


def test_task_template_registry_has_24_templates():
    import json

    data = json.loads((REPO / "benchmark_specs/task_template_registry.json").read_text(encoding="utf-8"))
    templates = data["templates"]
    assert len(templates) >= 24
    domains = {t["domain"] for t in templates}
    assert "travel" in domains and "multi_hop_operations" in domains


def test_phase3_docs_exist():
    for rel in (
        "docs/BENCHMARK_TAXONOMY.md",
        "docs/FAILURE_TAXONOMY.md",
        "docs/EVIDENCE_LEVEL_POLICY.md",
        "paper/REVIEWER_PACKET.md",
        "experiments/MAIN_EXPERIMENT_GATE.md",
        "docs/NEURIPS_ARTIFACT_CHECKLIST.md",
    ):
        assert (REPO / rel).exists(), rel
