from __future__ import annotations

import json
from pathlib import Path

import pytest

from causal_agent_bench.cli import main
from causal_agent_bench.level5.cleanroom import run_cleanroom_reproduction
from causal_agent_bench.level5.governance import (
    HARDENING_CAPABILITIES,
    GenuineEvidenceCounts,
    HardeningBuildState,
    hardening_check,
)
from causal_agent_bench.level5.redteam import run_hardening_redteam_campaign

REPO_ROOT = Path(__file__).resolve().parents[1]


def _cli(argv: list[str], capsys) -> dict:
    main(argv)
    output = capsys.readouterr().out
    return json.loads(output)


def test_hardening_gate_exact_ready_state_and_scientific_boundaries(tmp_path):
    state = HardeningBuildState(
        baseline_commit="a" * 40,
        primary_state="CAB_LEVEL5_HARDENED_FOUNDATION_READY",
        hardening_capabilities=dict.fromkeys(HARDENING_CAPABILITIES, True),
    )
    result = hardening_check(state)
    assert result["primary_state"] == "CAB_LEVEL5_HARDENED_FOUNDATION_READY"
    assert result["hardening_ready"] is True
    assert result["level5_complete"] is False
    assert result["blocked_states"] == [
        "HUMAN_VALIDATION_REQUIRED",
        "LIVE_EVIDENCE_REQUIRED",
        "EXTERNAL_REPLICATION_REQUIRED",
        "PROTECTED_EVALUATOR_PILOT_REQUIRED",
        "COMMUNITY_PILOT_REQUIRED",
    ]
    assert result["evaluator_state"] == "PROTECTED_EVALUATOR_HARDENED_PILOT_READY"

    incomplete = state.model_copy(
        update={
            "hardening_capabilities": {
                **state.hardening_capabilities,
                "strict_documentation": False,
            },
            "genuine_evidence": GenuineEvidenceCounts(human_judgment_rows=1),
            "critical_unresolved_issues": 1,
        }
    )
    failed = hardening_check(incomplete)
    assert failed["primary_state"] == "PARTIAL_SUCCESS_HARDENING_REMAINS"
    assert failed["scientific_boundaries_preserved"] is False
    assert failed["missing_hardening_capabilities"] == ["strict_documentation"]

    path = tmp_path / "state.json"
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    assert HardeningBuildState.from_path(path) == state


def test_hardening_redteam_executes_every_attack_without_critical_gap():
    report = run_hardening_redteam_campaign()
    assert report["passed"] is True
    assert report["executed_cases"] == 22
    assert report["critical_unresolved_count"] == 0
    assert report["outcomes"]["NOT_MITIGATED"] == 0
    assert report["manual_policy_count"] == 1
    manual = next(row for row in report["cases"] if row["outcome"] == "MANUAL_REVIEW")
    assert manual["automatically_mitigated"] is False
    assert manual["evidence"]["decision_state"] == "PENDING_GENUINE_HUMAN_REVIEW"


def test_level5_cli_registry_benchmark_artifacts_and_gate_surfaces(tmp_path, capsys):
    database = tmp_path / "registry.sqlite3"
    assert _cli(["registry", "init", "--path", str(database)], capsys)[
        "schema_version"
    ] == 3
    assert _cli(["registry", "version", "--path", str(database)], capsys)[
        "supported_schema_version"
    ] == 3
    assert _cli(
        ["registry", "migrate", "--path", str(database), "--dry-run"],
        capsys,
    )["migrations"] == []
    assert _cli(["registry", "events", "--path", str(database)], capsys)["events"] == []
    assert _cli(["registry", "doctor", "--path", str(database)], capsys)["passed"]
    export = tmp_path / "registry.json"
    assert _cli(
        [
            "registry",
            "export",
            "--path",
            str(database),
            "--output",
            str(export),
        ],
        capsys,
    )["exported"]
    backup = tmp_path / "backup.sqlite3"
    assert _cli(
        [
            "registry",
            "backup",
            "--path",
            str(database),
            "--output",
            str(backup),
        ],
        capsys,
    )["backed_up"]
    restored = tmp_path / "restored.sqlite3"
    assert _cli(
        [
            "registry",
            "restore",
            "--path",
            str(restored),
            "--backup",
            str(backup),
        ],
        capsys,
    )["verification"]["passed"]

    spec = tmp_path / "authoring.yaml"
    assert _cli(
        ["benchmark", "init", "--spec", str(spec), "--output-dir", str(tmp_path)],
        capsys,
    )["initialized"]
    output_dir = tmp_path / "compiled"
    assert _cli(
        [
            "benchmark",
            "compile",
            "--spec",
            str(spec),
            "--output-dir",
            str(output_dir),
        ],
        capsys,
    )["compiled"]
    assert _cli(
        ["benchmark", "validate", "--spec", str(spec), "--output-dir", str(output_dir)],
        capsys,
    )["valid"]
    assert _cli(
        ["benchmark", "diversity", "--spec", str(spec), "--output-dir", str(output_dir)],
        capsys,
    )["passed"]
    assert _cli(
        [
            "benchmark",
            "review-packet",
            "--spec",
            str(spec),
            "--output-dir",
            str(output_dir),
        ],
        capsys,
    )["items"] == 1
    with pytest.raises(SystemExit) as freeze:
        main(
            [
                "benchmark",
                "freeze",
                "--spec",
                str(spec),
                "--output-dir",
                str(output_dir),
            ]
        )
    assert freeze.value.code == 2
    capsys.readouterr()
    assert _cli(
        ["benchmark", "retire", "--spec", str(spec), "--output-dir", str(output_dir)],
        capsys,
    )["planned"]

    manifest = tmp_path / "manifest.json"
    assert _cli(["plan", "--output", str(manifest), "--shards", "2"], capsys)[
        "dry_run"
    ]
    assert _cli(["run", "--dry-run"], capsys)["will_call_models"] is False
    assert _cli(
        [
            "review",
            "serve",
            "--check",
            "--data-dir",
            str(tmp_path / "review"),
        ],
        capsys,
    )["ready"]
    assert _cli(["plugins", "list"], capsys)["registered"]
    assert _cli(
        [
            "env",
            "doctor",
            "--repo-root",
            str(REPO_ROOT),
        ],
        capsys,
    )["passed"]

    state = HardeningBuildState(
        baseline_commit="a" * 40,
        primary_state="CAB_LEVEL5_HARDENED_FOUNDATION_READY",
        hardening_capabilities=dict.fromkeys(HARDENING_CAPABILITIES, True),
    )
    state_path = tmp_path / "hardening.json"
    state_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    gate = _cli(
        ["level5", "hardening-check", "--state", str(state_path)],
        capsys,
    )
    assert gate["hardening_ready"]


def test_level5_cli_evaluator_evidence_certificates_reproduction_and_reliability(
    tmp_path,
    capsys,
):
    assert _cli(
        ["evaluator", "audit", "--text", "BEGIN_PRIVATE_TASK"],
        capsys,
    )["passed"] is False
    receipt_path = tmp_path / "receipt.json"
    receipt = _cli(
        ["evaluator", "run-fixture", "--output", str(receipt_path)],
        capsys,
    )
    assert receipt["evidence_class"] == "FIXTURE_ONLY"

    certificate_db = tmp_path / "certificates.sqlite3"
    certificate = _cli(
        [
            "certificate",
            "issue-fixture",
            "--path",
            str(certificate_db),
        ],
        capsys,
    )
    certificate_id = certificate["certificate_id"]
    assert _cli(
        [
            "certificate",
            "verify",
            "--path",
            str(certificate_db),
            "--certificate-id",
            certificate_id,
        ],
        capsys,
    )["passed"]
    assert _cli(
        ["certificate", "list", "--path", str(certificate_db)],
        capsys,
    )["certificates"]
    assert _cli(
        ["certificate", "transparency-verify", "--path", str(certificate_db)],
        capsys,
    )["passed"]
    assert _cli(
        [
            "certificate",
            "revoke",
            "--path",
            str(certificate_db),
            "--certificate-id",
            certificate_id,
            "--reason",
            "fixture retirement",
        ],
        capsys,
    )["revocation_id"]
    with pytest.raises(SystemExit):
        main(
            [
                "certificate",
                "verify",
                "--path",
                str(certificate_db),
                "--certificate-id",
                certificate_id,
            ]
        )
    capsys.readouterr()

    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [{"node_id": "node.fixture"}],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    assert _cli(
        ["evidence", "verify", "--graph", str(graph_path)],
        capsys,
    )["passed"]
    assert _cli(
        [
            "evidence",
            "trace",
            "--graph",
            str(graph_path),
            "--node-id",
            "node.fixture",
        ],
        capsys,
    )["related_edges"] == []
    assert _cli(
        [
            "model-card",
            "--model-id",
            "model.fixture",
            "--revision",
            "v1",
        ],
        capsys,
    )["evidence_status"] == "EXECUTION_PENDING"

    reliability_path = tmp_path / "faults.json"
    fault_report = _cli(
        [
            "reliability",
            "campaign",
            "--fault",
            "disk_full",
            "--output",
            str(reliability_path),
        ],
        capsys,
    )
    assert fault_report["passed"] and fault_report["case_count"] == 1
    reproduction = _cli(
        ["reproduce", "--workdir", str(tmp_path / "reproduction")],
        capsys,
    )
    assert reproduction["passed"]
    redteam_path = tmp_path / "legacy-redteam.json"
    assert _cli(
        ["redteam", "--output", str(redteam_path)],
        capsys,
    )["passed"]


@pytest.mark.slow
def test_cleanroom_reproduction_uses_committed_archive_and_clean_environment(tmp_path):
    report = run_cleanroom_reproduction(
        REPO_ROOT,
        tmp_path / "cleanroom.json",
        source_commit="HEAD",
        execute_container=False,
    )
    assert report["passed"] is True
    assert report["source_commit"]
    assert report["wheel_hash"]
    assert report["sdist_hash"]
    assert report["modes"]["clean_environment"] == "INTERNAL_CLEAN_ENVIRONMENT"
    assert report["modes"]["clean_checkout"] == "INTERNAL_CLEAN_CHECKOUT"
    assert report["modes"]["container"]["state"] == "NOT_EXECUTED"
    assert report["external_independent_reproduction"] == "NOT_EXECUTED"
    assert report["discrepancies"] == []
