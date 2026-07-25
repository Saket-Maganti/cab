import json
import os
import subprocess
import sys
from pathlib import Path

from causal_agent_bench.generation.instances import BenchmarkGenerationConfig, generate_benchmark

REPO = Path(__file__).resolve().parents[1]


def test_module_help_runs():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "--help"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "validate" in result.stdout
    assert "export-paper-assets" in result.stdout
    assert "doctor" in result.stdout
    assert "list-providers" in result.stdout
    assert "estimate-cost" in result.stdout
    assert "validate-config" in result.stdout
    assert "dry-run" in result.stdout
    assert "audit-interventions" in result.stdout
    assert "freeze-dataset" in result.stdout
    assert "summarize-run" in result.stdout
    assert "export-human-validation" in result.stdout
    assert "summarize-human-validation" in result.stdout
    assert "run-llm-judge" in result.stdout
    assert "calibrate-llm-judge" in result.stdout
    assert "export-ablation-table" in result.stdout
    assert "ablation-matrix" in result.stdout
    assert "batch-plan" in result.stdout
    assert "batch-merge" in result.stdout
    assert "failure-report" in result.stdout
    assert "update-claim-ledger" in result.stdout
    assert "run-health" in result.stdout
    assert "validate-paper-assets" in result.stdout
    assert "claim-evidence" in result.stdout
    assert "all-safety-reports" in result.stdout
    assert "benchmark-quality" in result.stdout
    assert "intervention-isolation-audit" in result.stdout
    assert "synthetic-fixture-check" in result.stdout
    assert "human-validation-packet" in result.stdout
    assert "estimate-run-cost" in result.stdout
    assert "method-figure-scaffolds" in result.stdout
    assert "release-readiness" in result.stdout
    assert "all-no-run-reports" in result.stdout
    assert "dataset-issue-triage" in result.stdout
    assert "provider-pilot-preflight" in result.stdout
    assert "human-validation-dry-run-sample" in result.stdout
    assert "method-appendix" in result.stdout
    assert "evidence-dashboard" in result.stdout
    assert "lint-config-metadata" in result.stdout
    assert "repair-plan" in result.stdout
    assert "benchmark-cards" in result.stdout
    assert "validate-gold-outputs" in result.stdout
    assert "validate-tool-schemas" in result.stdout
    assert "static-leakage-check" in result.stdout
    assert "benchmark-manifest" in result.stdout
    assert "config-profiles" in result.stdout
    assert "advisor-review-packet" in result.stdout
    assert "paper-readiness-map" in result.stdout
    assert "compare-mini-study" in result.stdout


def test_placeholder_validate_runs_without_explicit_path():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "validate"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "validated" in result.stdout or "No task file found" in result.stdout


def test_doctor_runs():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "doctor"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "CausalAgentBench doctor" in result.stdout
    assert "values intentionally not displayed" in result.stdout


def test_list_providers_runs_without_keys():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "list-providers"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "openai" in result.stdout
    assert "OPENAI_API_KEY" in result.stdout


def test_estimate_cost_runs_on_pilot_config():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "estimate-cost",
            "--config",
            "configs/pilot_multi_provider_20.yaml",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "pilot_multi_provider_20" in result.stdout
    assert "llm_calls_upper_bound" in result.stdout


def test_validate_config_runs_on_smoke_config():
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "validate-config",
            "--config",
            "configs/smoke.yaml",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["config_type"] == "experiment"


def test_dry_run_does_not_execute_agents(tmp_path):
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "dry-run",
            "--config",
            "configs/smoke.yaml",
            "--output-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["safety"]["will_call_providers"] is False
    assert payload["planned_trajectories"] > 0
    assert payload["tool_schema_report"]["valid"] is True
    assert len(payload["simulations"]) == payload["num_agent_runs"]
    report_dir = payload["report_dir"]
    assert os.path.exists(os.path.join(report_dir, "dry_run_report.json"))
    assert os.path.exists(os.path.join(report_dir, "dry_run_report.md"))


def test_validate_config_invalid_config_fails_clearly(tmp_path):
    config = tmp_path / "bad.yaml"
    config.write_text(
        "run_name: bad\nbenchmark_path: data/sample/instances.jsonl\n",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "validate-config",
            "--config",
            str(config),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert "agents" in payload["message"] or "agent_runs" in payload["message"]
    assert payload["details"]
    assert "Add agents" in json.dumps(payload["details"])


def test_validate_config_reports_missing_api_key_safely(tmp_path):
    config = tmp_path / "provider.yaml"
    config.write_text(
        "\n".join(
            [
                "run_name: provider_missing_key",
                "benchmark_path: data/sample/instances.jsonl",
                "agent_runs:",
                "  - name: direct_tool_openai",
                "    agent: direct_tool_agent",
                "    provider: openai",
                "    model: test-model",
                "max_steps: 2",
            ]
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": "src"}
    env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "validate-config",
            "--config",
            str(config),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["ready_to_run"] is False
    assert "OPENAI_API_KEY" in result.stdout
    assert "not configured" in result.stdout
    assert "sk-test" not in result.stdout


def test_provider_commands_do_not_print_secret_values():
    secret = "sk-test-secret-that-must-not-appear"
    env = {**os.environ, "PYTHONPATH": "src", "OPENAI_API_KEY": secret}
    result = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "list-providers"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "openai: configured" in result.stdout
    assert secret not in result.stdout


def test_all_no_run_reports_includes_upgrade_reports(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "data/instances.jsonl").write_text('{"instance_id": "fixture"}\n', encoding="utf-8")
    claims = {
        "claims": [
            {"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)
        ]
        + [{"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "planned"}]
    }
    (tmp_path / "docs/claim_ledger.json").write_text(json.dumps(claims), encoding="utf-8")
    (tmp_path / "docs/POST_PROVIDER_PILOT_CHECKLIST.md").write_text("checklist", encoding="utf-8")
    (tmp_path / "configs/provider_pilot_tiny_template.yaml").write_text(
        "\n".join(
            [
                "run_name: provider_pilot_tiny_template",
                "benchmark_path: data/instances.jsonl",
                "allow_paid_calls: false",
                "budget_cap_usd: 1.0",
                "evidence_scope: provider_pilot_pending_verification",
                "scientific_evidence: false",
                "max_instances: 1",
                "limits:",
                "  stop_after_trajectories: 1",
                "  max_runtime_minutes: 5",
                "  max_steps_per_instance: 2",
                "agent_runs:",
                "  - agent: direct_tool_agent",
                "    provider: openai",
                "    model: ${OPENAI_MODEL_ID}",
            ]
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "all-no-run-reports",
            "--repo-root",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "reports"),
            "--config",
            str(tmp_path / "configs/provider_pilot_tiny_template.yaml"),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    payload = json.loads(result.stdout)
    assert payload["safety"] == "static_no_run_only"
    for key in (
        "dataset_issue_triage",
        "provider_pilot_preflight",
        "human_validation_dry_run_sample",
        "method_appendix",
        "evidence_dashboard",
        "config_metadata_lint",
        "repair_plan",
        "benchmark_cards",
        "gold_output_validation",
        "tool_schema_validation",
        "static_leakage",
        "benchmark_manifest",
        "config_profiles",
        "advisor_review_packet",
        "paper_readiness_map",
        "report_quality_check",
        "publication_readiness",
        "answer_leakage_repair",
        "governance_os",
        "next_action_plan",
        "readiness_war_room",
        "release_blocker_report",
        "split_metadata_repair",
        "god_tier_status",
    ):
        assert key in payload["reports"]


def test_validate_config_flags_secret_like_yaml_without_printing_value(tmp_path):
    secret = "sk-test-secret-in-yaml"
    config = tmp_path / "secret.yaml"
    config.write_text(
        "\n".join(
            [
                "run_name: secret_yaml",
                "benchmark_path: data/sample/instances.jsonl",
                "agent_runs:",
                "  - name: direct_tool_openai",
                "    agent: direct_tool_agent",
                "    provider: openai",
                "    model: test-model",
                "    extra:",
                f"      api_key: {secret}",
            ]
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "validate-config",
            "--config",
            str(config),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["ready_to_run"] is False
    assert "Secret-like config keys detected" in result.stdout
    assert "agent_runs[0].extra.api_key" in result.stdout
    assert secret not in result.stdout


def test_audit_interventions_command_writes_reports(tmp_path):
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "audit-interventions",
            "--benchmark-dir",
            "data/sample",
            "--output-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["counts"]["instances"] > 0
    assert "validity_score_counts" in payload
    assert (tmp_path / "intervention_audit_report.md").exists()
    report = json.loads((tmp_path / "intervention_audit_report.json").read_text(encoding="utf-8"))
    assert "instance_validity_scores" in report
    assert report["instance_validity_scores"]
    assert report["provenance"]["instances_path"] == "data/sample/instances.jsonl"
    assert report["provenance"]["scope"].startswith("Intervention validity audit only")


def _freeze_source(tmp_path: Path) -> Path:
    result = generate_benchmark(
        BenchmarkGenerationConfig(
            seed=1234,
            benchmark_version="pytest_freeze_source",
            num_base_tasks=8,
            domains=["travel", "calendar_email", "file_spreadsheet", "policy_compliance"],
            difficulty_mix={"easy": 0.5, "medium": 0.5},
            interventions_per_task=2,
            dev_split_size=2,
            heldout_split_size=2,
            output_dir=str(tmp_path / "source"),
        )
    )
    return Path(result["output_dir"])


def test_freeze_dataset_command_writes_manifest(tmp_path):
    source_dir = _freeze_source(tmp_path)
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "freeze-dataset",
            "--source-dir",
            str(source_dir),
            "--version",
            "pytest_freeze",
            "--output-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["frozen"] is True
    manifest_path = tmp_path / "pytest_freeze" / "freeze_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["dataset_hash"]
    assert manifest["task_counts"]["base_tasks"] == 8
    assert manifest["intervention_counts"]["interventions"] == 16
    assert manifest["quality_audit_summary"]["passed"] is True
    assert manifest["leakage_report"]["passed"] is True
    assert (tmp_path / "pytest_freeze" / "benchmark_card_snapshot.md").exists()
    for split_name in ["dev", "pilot", "validation", "test", "heldout_templates"]:
        assert (tmp_path / "pytest_freeze" / f"{split_name}_base_tasks.jsonl").exists()
        assert (tmp_path / "pytest_freeze" / f"{split_name}_instances.jsonl").exists()


def test_freeze_dataset_command_fails_if_quality_audit_fails(tmp_path):
    source_dir = _freeze_source(tmp_path)
    interventions_path = source_dir / "interventions.jsonl"
    rows = [
        json.loads(line)
        for line in interventions_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows[0].pop("target_factor", None)
    rows[0]["metadata"]["goal_preserved"] = False
    interventions_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "freeze-dataset",
            "--source-dir",
            str(source_dir),
            "--version",
            "pytest_bad_freeze",
            "--output-dir",
            str(tmp_path / "frozen"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["frozen"] is False
    assert "quality audit failed" in payload["message"]


def test_freeze_dataset_hash_is_deterministic_for_same_source(tmp_path):
    source_dir = _freeze_source(tmp_path)
    env = {**os.environ, "PYTHONPATH": "src"}
    hashes = []
    for output_name in ["freeze_a", "freeze_b"]:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "causal_agent_bench",
                "freeze-dataset",
                "--source-dir",
                str(source_dir),
                "--version",
                "pytest_deterministic",
                "--output-dir",
                str(tmp_path / output_name),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(result.stdout)
        hashes.append(payload["dataset_hash"])

    assert hashes[0] == hashes[1]


def test_summarize_run_command_writes_summary(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_name": "pytest",
                "timestamp": "2026-05-12T00:00:00+00:00",
                "config_hash": "abc123",
                "dataset_version": "test",
                "agents": ["random_tool_agent"],
                "model_ids": [],
                "number_of_instances": 1,
                "agent_runs": [{"agent": "random_tool_agent"}],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "aggregate_scores.json").write_text('{"n_score_records": 1}\n', encoding="utf-8")
    (run_dir / "trajectories.jsonl").write_text('{"x": 1}\n', encoding="utf-8")
    (run_dir / "errors.jsonl").write_text("", encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "summarize-run",
            "--run-dir",
            str(run_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(result.stdout)
    assert payload["run_name"] == "pytest"
    assert (run_dir / "run_summary.md").exists()


def test_update_claim_ledger_command_lists_and_updates(tmp_path):
    ledger = tmp_path / "claim_ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "C-test",
                        "short_name": "test_claim",
                        "status": "planned",
                        "required_evidence": "evidence",
                        "current_evidence_paths": [],
                        "blocking_items": [],
                        "owner": "pytest",
                        "last_updated": "2026-05-12",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": "src"}
    listed = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "update-claim-ledger",
            "--ledger",
            str(ledger),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert json.loads(listed.stdout)["updated"] is False
    updated = subprocess.run(
        [
            sys.executable,
            "-m",
            "causal_agent_bench",
            "update-claim-ledger",
            "--ledger",
            str(ledger),
            "--claim-id",
            "C-test",
            "--status",
            "engineering_only",
            "--evidence-path",
            "README.md",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert json.loads(updated.stdout)["claim"]["status"] == "engineering_only"
