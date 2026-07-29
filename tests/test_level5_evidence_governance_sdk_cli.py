from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from causal_agent_bench import sdk
from causal_agent_bench.level5.core import EvidenceClass, content_hash
from causal_agent_bench.level5.evidence import (
    CertificateType,
    EdgeType,
    EvidenceGraph,
    NodeType,
    ResultRegistry,
    compile_claim,
    issue_certificate,
    model_card_template,
    verify_certificate,
)
from causal_agent_bench.level5.governance import (
    FOUNDATION_CAPABILITIES,
    GenuineEvidenceCounts,
    Level5BuildState,
    level5_check,
)
from causal_agent_bench.level5.plugins import ExampleScorerPlugin, PluginManager
from causal_agent_bench.level5.reproduction import run_red_team_fixture_campaign


def _node(graph, node_id, node_type=NodeType.RUN, public=True):
    return graph.add_node(
        node_id,
        node_type,
        content_hash(node_id),
        EvidenceClass.FIXTURE_ONLY,
        public=public,
    )


def test_evidence_graph_rejects_missing_parent_cycles_and_invalid_transition():
    graph = EvidenceGraph()
    first = _node(graph, "node.first")
    second = _node(graph, "node.second")
    graph.add_edge(first.node_id, second.node_id, EdgeType.GENERATED_FROM)
    with pytest.raises(ValueError, match="missing"):
        graph.add_edge("node.missing", second.node_id, EdgeType.SUPPORTS)
    with pytest.raises(ValueError, match="cycle"):
        graph.add_edge(second.node_id, first.node_id, EdgeType.GENERATED_FROM)
    with pytest.raises(ValueError, match="invalid evidence transition"):
        graph.transition(first.node_id, EvidenceClass.PAPER_ELIGIBLE_EVIDENCE)


def test_evidence_public_export_redacts_private_nodes():
    graph = EvidenceGraph()
    _node(graph, "node.public")
    _node(graph, "node.private", public=False)
    exported = graph.export_public()
    assert exported["redacted_node_count"] == 1
    assert [row["node_id"] for row in exported["nodes"]] == ["node.public"]


def test_certificate_verification_detects_tampering():
    graph = EvidenceGraph()
    node = _node(graph, "node.run")
    certificate = issue_certificate(CertificateType.RUN_INTEGRITY, node.node_id, [node])
    assert certificate["scientific_claim"] is False
    assert verify_certificate(certificate) is True
    certificate["subject_id"] = "tampered"
    assert verify_certificate(certificate) is False


def test_claim_compiler_reports_missing_and_ineligible_support():
    graph = EvidenceGraph()
    run = _node(graph, "node.run", NodeType.RUN)
    result = compile_claim("claim.1", {NodeType.RUN, NodeType.AUDIT}, [run])
    assert result["eligible"] is False
    assert result["missing_node_types"] == ["audit"]
    assert result["ineligible_evidence_nodes"] == ["node.run"]


def test_result_registry_correction_and_withdrawal_are_versioned():
    registry = ResultRegistry()
    registry.add("result.v1", {"score": 0.5, "uncertainty": [0.4, 0.6]})
    corrected = registry.correct(
        "result.v1", "result.v2", {"score": 0.6, "uncertainty": [0.5, 0.7]}
    )
    assert corrected["version"] == 2
    assert corrected["supersedes"] == "result.v1"
    withdrawn = registry.withdraw("result.v2", reason="scorer defect")
    assert withdrawn["status"] == "WITHDRAWN"


def test_model_card_keeps_results_blocked_without_real_evidence():
    card = model_card_template("model.fixture", "revision.fixture")
    assert card["clean_success"] == "BLOCKED_PENDING_AUDITED_REAL_EVIDENCE"
    assert card["evidence_status"] == "EXECUTION_PENDING"


def test_plugin_manager_exposes_typed_capabilities_and_blocks_duplicates():
    manager = PluginManager()
    plugin = ExampleScorerPlugin()
    manager.register(plugin)
    assert manager.capabilities()["cab.example_exact_scorer"] == [
        "exact_match",
        "fixture_safe",
    ]
    assert plugin.score("yes", " yes ") == 1.0
    with pytest.raises(ValueError, match="already registered"):
        manager.register(plugin)


def _foundation_state(**evidence):
    return Level5BuildState(
        starting_commit="bcd8bc4",
        foundation_capabilities=dict.fromkeys(FOUNDATION_CAPABILITIES, True),
        validation_passed=True,
        genuine_evidence=GenuineEvidenceCounts(**evidence),
    )


def test_level5_gate_reports_truthful_foundation_and_all_real_blockers():
    result = level5_check(_foundation_state())
    assert result["primary_state"] == "CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE"
    assert result["level5_complete"] is False
    assert result["blocked_states"] == [
        "HUMAN_VALIDATION_REQUIRED",
        "LIVE_EVIDENCE_REQUIRED",
        "EXTERNAL_REPLICATION_REQUIRED",
        "PROTECTED_EVALUATOR_PILOT_REQUIRED",
        "COMMUNITY_PILOT_REQUIRED",
    ]


def test_level5_complete_requires_every_genuine_gate():
    result = level5_check(
        _foundation_state(
            human_judgment_rows=40,
            real_model_trajectories=100,
            audited_real_runs=1,
            paper_eligible_empirical_assets=1,
            supported_empirical_claims=1,
            independent_external_reproductions=1,
            protected_evaluator_pilots=1,
            community_external_pilots=1,
        )
    )
    assert result["primary_state"] == "CAB_LEVEL5_COMPLETE"
    assert result["level5_complete"] is True


def test_public_sdk_surface_is_importable():
    assert sdk.SQLiteRegistry
    assert sdk.BenchmarkAuthoringSpec
    assert sdk.ContentAddressedStore
    assert sdk.PluginManager


def test_red_team_fixture_campaign_passes_with_manual_policy_boundaries():
    report = run_red_team_fixture_campaign()
    assert report["passed"] is True
    assert report["case_count"] == 15
    assert report["manual_policy_count"] > 0


def test_level5_cli_help_and_fixture_reproduction(tmp_path):
    env = {**os.environ, "PYTHONPATH": "src:."}
    help_result = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    for command in ("registry", "benchmark", "evaluator", "reproduce", "level5"):
        assert command in help_result.stdout
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "reproduce",
            "--workdir",
            str(tmp_path / "repro"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    receipt = json.loads(result.stdout)
    assert receipt["passed"] is True
    assert receipt["independent_reproduction"] is False
    assert receipt["checks"]["resumed_to_20"] is True
