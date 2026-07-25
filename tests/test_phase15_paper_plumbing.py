"""Provider-free tests for the Phase 15 paper/result contract."""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path

from causal_agent_bench.analysis.phase15_assets import (
    PAPER_EVIDENCE_CLASS,
    REQUIRED_PHASE15_ASSET_FAMILIES,
    export_phase15_asset_bundle,
    phase15_asset_contract,
    validate_phase15_asset_bundle,
    validate_phase15_source,
)
from causal_agent_bench.runners.run_manifest_v2 import write_manifest_template

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_phase15_contract_represents_every_required_asset_family() -> None:
    contract = phase15_asset_contract()
    assert contract["complete"] is True
    assert contract["missing_families"] == []
    assert set(contract["represented_families"]) == set(REQUIRED_PHASE15_ASSET_FAMILIES)
    assert contract["evidence_class"] == "DESIGN_ONLY"
    assert contract["scientific_evidence"] is False
    assert contract["paper_eligible"] is False

    generators = {asset["generator"] for asset in contract["assets"]}
    assert {
        "main_agent_performance_table",
        "intervention_family_performance_table",
        "ranking_instability_table",
        "_rank_uncertainty_table",
        "_transition_profile_table",
        "_scorer_sensitivity_table",
        "_intervention_validity_table",
        "ablation_results_table",
        "generate_failure_gallery",
        "_cost_runtime_table",
    }.issubset(generators)


def test_phase15_export_api_has_no_ineligible_evidence_override() -> None:
    parameters = inspect.signature(export_phase15_asset_bundle).parameters
    assert set(parameters) == {"source_dirs", "output_dir"}
    assert not any(name.startswith("allow_") for name in parameters)


def test_preflight_refuses_missing_sources_without_writing(tmp_path: Path) -> None:
    output = tmp_path / "paper_assets"
    validation = validate_phase15_asset_bundle({})
    assert validation["passed"] is False
    assert validation["paper_assets_written"] is False
    assert any("missing source roles" in issue for issue in validation["issues"])
    assert not output.exists()

    try:
        export_phase15_asset_bundle({}, output)
    except ValueError as exc:
        assert "refusing Phase 15 paper asset export" in str(exc)
    else:
        raise AssertionError("expected missing-source bundle to be refused")
    assert not output.exists()


def test_execution_pending_manifest_is_never_paper_asset_eligible(tmp_path: Path) -> None:
    run_dir = tmp_path / "execution_pending_run"
    run_dir.mkdir()
    manifest_path = write_manifest_template(run_dir / "run_manifest_v2.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["run_id"] = run_dir.name
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "evidence_class": "EXECUTION_PENDING",
                "scientific_evidence": False,
                "paper_eligible": False,
                "audit_state": "EXECUTION_PENDING",
            }
        ),
        encoding="utf-8",
    )

    state = validate_phase15_source(run_dir)
    assert state["eligible"] is False
    assert any(PAPER_EVIDENCE_CLASS in issue for issue in state["issues"])
    assert any("scientific_evidence" in issue for issue in state["issues"])
    assert any("paper_eligible" in issue for issue in state["issues"])


def test_claim_ledger_explicitly_maps_all_phase15_fields_without_promotion() -> None:
    payload = json.loads((REPO_ROOT / "docs" / "claim_ledger.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 3
    required = {
        "required_study",
        "required_evidence",
        "validation_threshold",
        "current_state",
        "allowed_wording",
        "forbidden_wording",
        "paper_location",
    }
    for claim in payload["claims"]:
        assert required.issubset(claim)
        assert claim["required_study"]
        assert claim["required_evidence"]
        assert claim["validation_threshold"]
        assert claim["current_state"]
        assert claim["allowed_wording"]
        assert claim["forbidden_wording"]
        assert claim["paper_location"]
        if claim["claim_id"] == "C9":
            assert claim["status"] == "engineering_only"
        else:
            assert claim["status"] == "planned"


def test_contract_cli_is_provider_free_and_does_not_write_results(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "export_phase15_paper_assets.py"),
            "--list-contract",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["complete"] is True
    assert payload["evidence_class"] == "DESIGN_ONLY"
    assert set(tmp_path.iterdir()) == before
