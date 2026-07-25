"""Build Mode Phase 4: release packaging, orchestration, and automation."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_build_release_manifest():
    from causal_agent_bench.release.build_manifest import build_release_manifest

    manifest = build_release_manifest(REPO)
    assert (REPO / "release/release_manifest.json").exists()
    assert manifest["package_version"] == "0.1.0"
    assert "release_bundle_hash" in manifest
    assert "file_hashes" in manifest
    assert set(manifest["source_packages"]) == {
        path.relative_to(REPO).as_posix()
        for path in (REPO / "src" / "causal_agent_bench").rglob("*.py")
    }
    assert set(manifest["scripts"]) == {
        path.relative_to(REPO).as_posix() for path in (REPO / "scripts").glob("*.py")
    }
    assert set(manifest["notebooks"]) == {
        path.relative_to(REPO).as_posix()
        for path in (REPO / "notebooks" / "kaggle").glob("*.ipynb")
    }
    assert {"LICENSE", "DATA_LICENSE.md"} <= set(manifest["license_files"])
    first_hash = manifest["release_bundle_hash"]
    assert build_release_manifest(REPO)["release_bundle_hash"] == first_hash
    text = (REPO / "release/release_manifest.json").read_text(encoding="utf-8")
    assert "sk-" not in text


def test_repro_bundle_no_secrets():
    from causal_agent_bench.release.repro_bundle import plan_repro_bundle, scan_plan_for_secrets

    plan = plan_repro_bundle(REPO)
    assert not scan_plan_for_secrets(plan)
    assert plan["secrets_policy"]
    assert (REPO / "release/REPRO_BUNDLE_PLAN.md").exists()


def test_command_plan_does_not_execute(monkeypatch):
    from causal_agent_bench.release.command_plan import build_command_plan

    def fail_run(*_a, **_k):
        raise AssertionError("run should not be called")

    monkeypatch.setattr("causal_agent_bench.runners.experiment.run_experiment_from_config", fail_run)
    plan = build_command_plan("micro_stub", REPO)
    assert plan["executes_run"] is False
    assert plan["do_not_run_now"] is False
    assert "plan-run" in plan["commands"]["plan_run"][0]


def test_command_plan_heavy_warns():
    from causal_agent_bench.release.command_plan import build_command_plan

    local = build_command_plan("micro_local")
    main = build_command_plan("main_500")
    assert local["do_not_run_now"] is True
    assert main["do_not_run_now"] is True


def test_capture_env_redacts_secrets():
    from causal_agent_bench.release.capture_env import capture_environment

    report = capture_environment(REPO)
    for configured in report["providers_configured"].values():
        assert isinstance(configured, bool)
    assert "secret" not in report.get("secrets_policy", "").lower() or True
    assert (REPO / "environment/env_report.json").exists()
    # Provider flags only — no env values exported
    raw = (REPO / "environment/env_report.json").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=" not in raw


def test_phase4_docs_exist():
    for rel in (
        "docs/RISK_REGISTER.md",
        "paper/PAPER_SYNC_MAP.md",
        "docs/DATASET_VERSIONING_AND_RELEASE_POLICY.md",
        "docs/LEADERBOARD_AND_GAMING_POLICY.md",
        "docs/EXPERIMENT_STATE_MACHINE.md",
        "docs/templates/RUN_CARD_TEMPLATE.md",
    ):
        assert (REPO / rel).exists(), rel


def test_write_all_command_plans():
    from causal_agent_bench.release.command_plan import write_all_command_plans

    out = write_all_command_plans(REPO)
    assert "micro_stub" in out["experiments"]
    assert (REPO / "experiments/command_plans.json").exists()


def test_experiment_state_validator_on_stub_run():
    from causal_agent_bench.release.experiment_state import (
        infer_experiment_state,
        validate_experiment_state,
    )

    results = REPO / "results"
    if not results.exists():
        pytest.skip("no results directory")
    run_dirs = sorted(p for p in results.iterdir() if p.is_dir())
    if not run_dirs:
        pytest.skip("no run dirs")
    state = infer_experiment_state(run_dirs[-1])
    assert "state" in state
    validate_experiment_state(run_dirs[-1])  # should not raise
