"""Fail-closed Phase 15 paper/result asset plumbing.

This module is intentionally stricter than the legacy engineering asset
exporter.  It will not emit an empirical bundle unless every source run carries
an audited ``cab_run_manifest_v2`` whose evidence class is exactly
``PAPER_ELIGIBLE_EVIDENCE``.  Fixture, preliminary, incomplete, and merely
provider-backed runs are refused without an override path.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from causal_agent_bench.analysis.error_analysis import generate_failure_gallery
from causal_agent_bench.analysis.figures import (
    figure2_clean_vs_intervention,
    figure3_intervention_family_degradation,
    figure4_ranking_instability,
)
from causal_agent_bench.analysis.load_results import RunResults, load_run_results
from causal_agent_bench.analysis.statistics import statistical_report
from causal_agent_bench.analysis.tables import (
    ablation_results_table,
    asset_metadata,
    intervention_family_performance_table,
    main_agent_performance_table,
    ranking_instability_table,
    with_asset_metadata,
    write_table_bundle,
)
from causal_agent_bench.runners.run_completion import infer_completion_state
from causal_agent_bench.runners.run_manifest_v2 import CanonicalRunManifest
from causal_agent_bench.utils.io import write_json

PAPER_EVIDENCE_CLASS = "PAPER_ELIGIBLE_EVIDENCE"
AUDITED_HUMAN_EVIDENCE_CLASSES = frozenset(
    {"AUDITED_REAL_EVIDENCE", PAPER_EVIDENCE_CLASS}
)

REQUIRED_PHASE15_ASSET_FAMILIES = (
    "main_performance",
    "family_robustness",
    "rank_comparison",
    "rank_uncertainty",
    "transition_profiles",
    "scorer_sensitivity",
    "intervention_validity",
    "naturalistic_transfer",
    "ablations",
    "failure_gallery",
    "cost_runtime_appendix",
)

REQUIRED_SOURCE_ROLES = (
    "main",
    "naturalistic",
    "ablation",
    "scorer_validation",
    "intervention_validity",
)


@dataclass(frozen=True)
class Phase15AssetContract:
    asset_id: str
    family: str
    kind: str
    source_role: str
    generator: str
    outputs: tuple[str, ...]
    minimum_input: str


PHASE15_ASSET_CONTRACTS = (
    Phase15AssetContract(
        "table_main_performance",
        "main_performance",
        "table",
        "main",
        "main_agent_performance_table",
        (
            "tables/table_main_performance.csv",
            "tables/table_main_performance.md",
            "tables/table_main_performance.tex",
        ),
        "Audited Main-500 matched scores for at least three non-oracle models.",
    ),
    Phase15AssetContract(
        "figure_main_performance",
        "main_performance",
        "figure",
        "main",
        "figure2_clean_vs_intervention",
        (
            "figures/figure_main_performance.png",
            "figures/figure_main_performance.pdf",
        ),
        "Audited Main-500 clean and intervention success.",
    ),
    Phase15AssetContract(
        "table_family_robustness",
        "family_robustness",
        "table",
        "main",
        "intervention_family_performance_table",
        (
            "tables/table_family_robustness.csv",
            "tables/table_family_robustness.md",
            "tables/table_family_robustness.tex",
        ),
        "Family-matched audited intervention outcomes.",
    ),
    Phase15AssetContract(
        "figure_family_robustness_heatmap",
        "family_robustness",
        "figure",
        "main",
        "figure3_intervention_family_degradation",
        (
            "figures/figure_family_robustness_heatmap.png",
            "figures/figure_family_robustness_heatmap.pdf",
        ),
        "Family-matched audited intervention outcomes.",
    ),
    Phase15AssetContract(
        "table_rank_comparison",
        "rank_comparison",
        "table",
        "main",
        "ranking_instability_table",
        (
            "tables/table_rank_comparison.csv",
            "tables/table_rank_comparison.md",
            "tables/table_rank_comparison.tex",
        ),
        "Common matched units for at least three eligible non-oracle models.",
    ),
    Phase15AssetContract(
        "figure_clean_rank_vs_robustness_rank",
        "rank_comparison",
        "figure",
        "main",
        "figure4_ranking_instability",
        (
            "figures/figure_clean_rank_vs_robustness_rank.png",
            "figures/figure_clean_rank_vs_robustness_rank.pdf",
        ),
        "Common matched units for at least three eligible non-oracle models.",
    ),
    Phase15AssetContract(
        "table_rank_uncertainty",
        "rank_uncertainty",
        "table",
        "main",
        "_rank_uncertainty_table",
        (
            "tables/table_rank_uncertainty.csv",
            "tables/table_rank_uncertainty.md",
            "tables/table_rank_uncertainty.tex",
        ),
        "Clustered rank bootstrap with reportable replicates.",
    ),
    Phase15AssetContract(
        "figure_rank_probability",
        "rank_uncertainty",
        "figure",
        "main",
        "_rank_probability_figure",
        (
            "figures/figure_rank_probability.png",
            "figures/figure_rank_probability.pdf",
        ),
        "Pairwise rank probability matrix from clustered bootstrap.",
    ),
    Phase15AssetContract(
        "table_transition_profiles",
        "transition_profiles",
        "table",
        "main",
        "_transition_profile_table",
        (
            "tables/table_transition_profiles.csv",
            "tables/table_transition_profiles.md",
            "tables/table_transition_profiles.tex",
        ),
        "Complete matched clean/intervention pairs.",
    ),
    Phase15AssetContract(
        "figure_transition_matrix",
        "transition_profiles",
        "figure",
        "main",
        "_transition_matrix_figure",
        (
            "figures/figure_transition_matrix.png",
            "figures/figure_transition_matrix.pdf",
        ),
        "Complete matched clean/intervention pairs.",
    ),
    Phase15AssetContract(
        "figure_model_robustness_profile",
        "transition_profiles",
        "figure",
        "main",
        "_model_robustness_profile_figure",
        (
            "figures/figure_model_robustness_profile.png",
            "figures/figure_model_robustness_profile.pdf",
        ),
        "Audited per-family robustness estimates.",
    ),
    Phase15AssetContract(
        "table_scorer_sensitivity",
        "scorer_sensitivity",
        "table",
        "scorer_validation",
        "_scorer_sensitivity_table",
        (
            "tables/table_scorer_sensitivity.csv",
            "tables/table_scorer_sensitivity.md",
            "tables/table_scorer_sensitivity.tex",
        ),
        "Blinded human scorer error rates and preregistered sensitivity scenarios.",
    ),
    Phase15AssetContract(
        "figure_scorer_sensitivity",
        "scorer_sensitivity",
        "figure",
        "scorer_validation",
        "_scorer_sensitivity_figure",
        (
            "figures/figure_scorer_sensitivity.png",
            "figures/figure_scorer_sensitivity.pdf",
        ),
        "Blinded human scorer error rates and preregistered sensitivity scenarios.",
    ),
    Phase15AssetContract(
        "table_intervention_validity",
        "intervention_validity",
        "table",
        "intervention_validity",
        "_intervention_validity_table",
        (
            "tables/table_intervention_validity.csv",
            "tables/table_intervention_validity.md",
            "tables/table_intervention_validity.tex",
        ),
        "Two independent genuine reviewers, adjudication, and C10 PASS.",
    ),
    Phase15AssetContract(
        "table_naturalistic_transfer",
        "naturalistic_transfer",
        "table",
        "naturalistic",
        "main_agent_performance_table",
        (
            "tables/table_naturalistic_transfer.csv",
            "tables/table_naturalistic_transfer.md",
            "tables/table_naturalistic_transfer.tex",
        ),
        "Audited naturalistic-transfer split with provenance and privacy review.",
    ),
    Phase15AssetContract(
        "figure_naturalistic_transfer",
        "naturalistic_transfer",
        "figure",
        "naturalistic",
        "figure2_clean_vs_intervention",
        (
            "figures/figure_naturalistic_transfer.png",
            "figures/figure_naturalistic_transfer.pdf",
        ),
        "Audited naturalistic-transfer split with provenance and privacy review.",
    ),
    Phase15AssetContract(
        "table_ablations",
        "ablations",
        "table",
        "ablation",
        "ablation_results_table",
        (
            "tables/table_ablations.csv",
            "tables/table_ablations.md",
            "tables/table_ablations.tex",
        ),
        "Audited frozen-task ablation with prompt hashes and equal budgets.",
    ),
    Phase15AssetContract(
        "failure_gallery",
        "failure_gallery",
        "document",
        "main",
        "generate_failure_gallery",
        (
            "failure_gallery/taxonomy.json",
            "failure_gallery/README.md",
            "failure_gallery/qualitative_examples.md",
        ),
        "Audited trajectories; examples retain run and scorer provenance.",
    ),
    Phase15AssetContract(
        "table_cost_runtime_appendix",
        "cost_runtime_appendix",
        "table",
        "main",
        "_cost_runtime_table",
        (
            "tables/table_cost_runtime_appendix.csv",
            "tables/table_cost_runtime_appendix.md",
            "tables/table_cost_runtime_appendix.tex",
        ),
        "Measured, not estimated, per-trajectory cost and runtime.",
    ),
    Phase15AssetContract(
        "figure_cost_vs_robustness",
        "cost_runtime_appendix",
        "figure",
        "main",
        "_measured_cost_vs_robustness_figure",
        (
            "figures/figure_cost_vs_robustness.png",
            "figures/figure_cost_vs_robustness.pdf",
        ),
        "Measured, not estimated, per-trajectory cost and runtime.",
    ),
)


def phase15_asset_contract() -> dict[str, Any]:
    """Return the complete design-only registry without inspecting or writing results."""

    represented = {contract.family for contract in PHASE15_ASSET_CONTRACTS}
    missing = sorted(set(REQUIRED_PHASE15_ASSET_FAMILIES) - represented)
    return {
        "schema_version": "cab_phase15_asset_contract_v1",
        "evidence_class": "DESIGN_ONLY",
        "scientific_evidence": False,
        "paper_eligible": False,
        "required_source_roles": list(REQUIRED_SOURCE_ROLES),
        "required_families": list(REQUIRED_PHASE15_ASSET_FAMILIES),
        "represented_families": sorted(represented),
        "missing_families": missing,
        "complete": not missing,
        "assets": [asdict(contract) for contract in PHASE15_ASSET_CONTRACTS],
    }


def validate_phase15_source(run_dir: str | Path) -> dict[str, Any]:
    """Inspect one run without mutation and enforce canonical paper eligibility."""

    run_path = Path(run_dir).resolve()
    issues: list[str] = []
    manifest_path, manifest_payload = _load_manifest_payload(run_path)
    manifest: CanonicalRunManifest | None = None
    if manifest_payload is None:
        issues.append(
            "missing canonical run manifest "
            "(expected run_manifest_v2.json or canonical_run_manifest.json)"
        )
    else:
        try:
            manifest = CanonicalRunManifest.model_validate(manifest_payload)
        except Exception as exc:
            issues.append(f"invalid canonical run manifest: {type(exc).__name__}")

    metadata = _load_metadata(run_path)
    if not metadata:
        issues.append("missing run_metadata.json/metadata.json")

    if manifest is not None:
        if manifest.evidence_class != PAPER_EVIDENCE_CLASS:
            issues.append(
                f"manifest evidence_class={manifest.evidence_class!r}; "
                f"requires {PAPER_EVIDENCE_CLASS}"
            )
        if manifest.status != "audited":
            issues.append(f"manifest status={manifest.status!r}; requires 'audited'")
        if not manifest.scientific_evidence:
            issues.append("manifest scientific_evidence is not true")
        if not manifest.paper_eligible:
            issues.append("manifest paper_eligible is not true")
        if manifest.run_id != run_path.name:
            issues.append(
                f"manifest run_id={manifest.run_id!r} does not match directory {run_path.name!r}"
            )
        issues.extend(_manifest_pin_issues(manifest))

    if metadata:
        if str(metadata.get("evidence_class") or "") != PAPER_EVIDENCE_CLASS:
            issues.append("run metadata does not declare PAPER_ELIGIBLE_EVIDENCE")
        if metadata.get("scientific_evidence") is not True:
            issues.append("run metadata scientific_evidence is not literal true")
        if metadata.get("paper_eligible") is not True:
            issues.append("run metadata paper_eligible is not literal true")
        audit_state = str(metadata.get("audit_state") or metadata.get("status") or "").lower()
        if audit_state not in {"audited", "paper_eligible", "paper_eligible_evidence"}:
            issues.append("run metadata audit state is not audited")

    completion: dict[str, Any] = {}
    if run_path.exists():
        completion = infer_completion_state(run_path)
        if completion.get("completion_state") != "complete":
            issues.append(
                "run is not complete "
                f"({completion.get('completed_trajectories')}/"
                f"{completion.get('expected_trajectories')})"
            )
    else:
        issues.append("run directory does not exist")

    for filename in ("aggregate_scores.json", "scores.jsonl", "trajectories.jsonl"):
        if not (run_path / filename).is_file():
            issues.append(f"missing required result artifact: {filename}")
    if not (run_path / "instances.jsonl").is_file() and not (run_path / "tasks.jsonl").is_file():
        issues.append("missing required task artifact: instances.jsonl or tasks.jsonl")
    if (run_path / "INCOMPLETE_RUN.json").exists():
        issues.append("INCOMPLETE_RUN.json is present")

    return {
        "run_dir": str(run_path),
        "eligible": not issues,
        "issues": issues,
        "manifest_path": str(manifest_path) if manifest_path is not None else None,
        "manifest": manifest.model_dump(mode="json") if manifest is not None else None,
        "completion": completion,
    }


def validate_phase15_asset_bundle(
    source_dirs: Mapping[str, str | Path],
) -> dict[str, Any]:
    """Validate all source roles and asset-specific prerequisites without writes."""

    issues: list[str] = []
    unknown_roles = sorted(set(source_dirs) - set(REQUIRED_SOURCE_ROLES))
    if unknown_roles:
        issues.append("unknown source roles: " + ", ".join(unknown_roles))
    missing_roles = [role for role in REQUIRED_SOURCE_ROLES if role not in source_dirs]
    if missing_roles:
        issues.append("missing source roles: " + ", ".join(missing_roles))

    source_states: dict[str, dict[str, Any]] = {}
    for role in REQUIRED_SOURCE_ROLES:
        if role not in source_dirs:
            continue
        state = validate_phase15_source(source_dirs[role])
        source_states[role] = state
        issues.extend(f"{role}: {issue}" for issue in state["issues"])

    if issues:
        return _bundle_validation_payload(source_states, issues, {})

    loaded: dict[str, RunResults] = {
        role: load_run_results(Path(source_dirs[role]), ensure_scores=False)
        for role in REQUIRED_SOURCE_ROLES
    }
    specialized: dict[str, Any] = {}

    main = loaded["main"]
    non_oracle = sorted(
        {
            str(name)
            for name in main.scores_df.get("agent_name", pd.Series(dtype=object)).dropna()
            if "oracle" not in str(name).lower()
        }
    )
    if len(non_oracle) < 3:
        issues.append(
            f"main: rank assets require at least 3 non-oracle models/agents; found {len(non_oracle)}"
        )

    main_stats = statistical_report(main)
    specialized["main_statistics"] = main_stats
    rank = _dict(main_stats.get("rank_uncertainty"))
    if rank.get("state") != "ok" or int(rank.get("n_boot_valid") or 0) <= 0:
        issues.append("main: rank uncertainty has no reportable clustered bootstrap replicates")
    if not _transition_rows(main_stats):
        issues.append("main: no complete matched transition profiles")

    main_manifest = _dict(source_states["main"].get("manifest"))
    if main_manifest.get("cost_status") != "MEASURED":
        issues.append("main: cost/runtime appendix requires cost_status='MEASURED'")
    if not _has_measured_cost_and_runtime(main):
        issues.append("main: measured per-trajectory cost and latency are missing")

    natural_manifest = _dict(source_states["naturalistic"].get("manifest"))
    if "naturalistic" not in _study_marker(natural_manifest, loaded["naturalistic"]):
        issues.append("naturalistic: manifest study_id or split_role must identify naturalistic transfer")
    issues.extend(
        f"naturalistic: {issue}"
        for issue in _naturalistic_release_review_issues(loaded["naturalistic"])
    )

    ablation_manifest = _dict(source_states["ablation"].get("manifest"))
    if "ablation" not in _study_marker(ablation_manifest, loaded["ablation"]):
        issues.append("ablation: manifest study_id or split_role must identify an ablation study")
    issues.extend(
        f"ablation: {issue}" for issue in _ablation_contract_issues(loaded["ablation"])
    )

    scorer_report_path, scorer_report = _find_scorer_validation_report(
        Path(source_dirs["scorer_validation"])
    )
    scorer_issues = _validate_scorer_report(scorer_report)
    issues.extend(f"scorer_validation: {issue}" for issue in scorer_issues)
    specialized["scorer_report_path"] = (
        str(scorer_report_path) if scorer_report_path is not None else None
    )
    specialized["scorer_report"] = scorer_report

    human_report_path, human_report = _find_human_review_report(
        Path(source_dirs["intervention_validity"])
    )
    human_issues = _validate_human_report(human_report)
    issues.extend(f"intervention_validity: {issue}" for issue in human_issues)
    specialized["human_report_path"] = (
        str(human_report_path) if human_report_path is not None else None
    )
    specialized["human_report"] = human_report

    return _bundle_validation_payload(source_states, issues, specialized)


def export_phase15_asset_bundle(
    source_dirs: Mapping[str, str | Path],
    output_dir: str | Path,
) -> list[Path]:
    """Build the complete empirical bundle only after every strict gate passes."""

    validation = validate_phase15_asset_bundle(source_dirs)
    if not validation["passed"]:
        raise ValueError(
            "refusing Phase 15 paper asset export: " + "; ".join(validation["issues"])
        )

    output = Path(output_dir).resolve()
    if output.exists():
        raise ValueError(f"refusing to overwrite existing Phase 15 bundle: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    loaded = {
        role: load_run_results(Path(source_dirs[role]), ensure_scores=False)
        for role in REQUIRED_SOURCE_ROLES
    }
    stats = statistical_report(loaded["main"])
    scorer_report = _dict(validation["specialized"].get("scorer_report"))
    human_report = _dict(validation["specialized"].get("human_report"))

    with tempfile.TemporaryDirectory(
        prefix=".cab_phase15_",
        dir=output.parent,
    ) as temporary:
        stage = Path(temporary) / output.name
        table_dir = stage / "tables"
        figure_dir = stage / "figures"
        failure_dir = stage / "failure_gallery"
        table_dir.mkdir(parents=True)
        figure_dir.mkdir(parents=True)

        paths: list[Path] = []
        paths.extend(
            _write_table(
                main_agent_performance_table(loaded["main"]),
                table_dir / "table_main_performance",
                loaded["main"],
                "table_main_performance",
            )
        )
        paths.extend(
            _write_table(
                intervention_family_performance_table(loaded["main"]),
                table_dir / "table_family_robustness",
                loaded["main"],
                "table_family_robustness",
            )
        )
        paths.extend(
            _write_table(
                ranking_instability_table(loaded["main"]),
                table_dir / "table_rank_comparison",
                loaded["main"],
                "table_rank_comparison",
            )
        )
        paths.extend(
            _write_table(
                _rank_uncertainty_table(stats),
                table_dir / "table_rank_uncertainty",
                loaded["main"],
                "table_rank_uncertainty",
            )
        )
        paths.extend(
            _write_table(
                _transition_profile_table(stats),
                table_dir / "table_transition_profiles",
                loaded["main"],
                "table_transition_profiles",
            )
        )
        paths.extend(
            _write_table(
                _scorer_sensitivity_table(scorer_report),
                table_dir / "table_scorer_sensitivity",
                loaded["scorer_validation"],
                "table_scorer_sensitivity",
            )
        )
        paths.extend(
            _write_table(
                _intervention_validity_table(human_report),
                table_dir / "table_intervention_validity",
                loaded["intervention_validity"],
                "table_intervention_validity",
            )
        )
        paths.extend(
            _write_table(
                main_agent_performance_table(loaded["naturalistic"]),
                table_dir / "table_naturalistic_transfer",
                loaded["naturalistic"],
                "table_naturalistic_transfer",
            )
        )
        paths.extend(
            _write_table(
                ablation_results_table(loaded["ablation"]),
                table_dir / "table_ablations",
                loaded["ablation"],
                "table_ablations",
            )
        )
        paths.extend(
            _write_table(
                _cost_runtime_table(loaded["main"]),
                table_dir / "table_cost_runtime_appendix",
                loaded["main"],
                "table_cost_runtime_appendix",
            )
        )

        paths.extend(
            _write_figure(
                figure2_clean_vs_intervention(loaded["main"]),
                figure_dir / "figure_main_performance",
                loaded["main"],
                "figure_main_performance",
            )
        )
        paths.extend(
            _write_figure(
                figure3_intervention_family_degradation(loaded["main"]),
                figure_dir / "figure_family_robustness_heatmap",
                loaded["main"],
                "figure_family_robustness_heatmap",
            )
        )
        paths.extend(
            _write_figure(
                figure4_ranking_instability(loaded["main"]),
                figure_dir / "figure_clean_rank_vs_robustness_rank",
                loaded["main"],
                "figure_clean_rank_vs_robustness_rank",
            )
        )
        paths.extend(
            _write_figure(
                _rank_probability_figure(stats),
                figure_dir / "figure_rank_probability",
                loaded["main"],
                "figure_rank_probability",
            )
        )
        paths.extend(
            _write_figure(
                _transition_matrix_figure(stats),
                figure_dir / "figure_transition_matrix",
                loaded["main"],
                "figure_transition_matrix",
            )
        )
        paths.extend(
            _write_figure(
                _model_robustness_profile_figure(loaded["main"]),
                figure_dir / "figure_model_robustness_profile",
                loaded["main"],
                "figure_model_robustness_profile",
            )
        )
        paths.extend(
            _write_figure(
                _scorer_sensitivity_figure(scorer_report),
                figure_dir / "figure_scorer_sensitivity",
                loaded["scorer_validation"],
                "figure_scorer_sensitivity",
            )
        )
        paths.extend(
            _write_figure(
                figure2_clean_vs_intervention(loaded["naturalistic"]),
                figure_dir / "figure_naturalistic_transfer",
                loaded["naturalistic"],
                "figure_naturalistic_transfer",
            )
        )
        paths.extend(
            _write_figure(
                _measured_cost_vs_robustness_figure(loaded["main"]),
                figure_dir / "figure_cost_vs_robustness",
                loaded["main"],
                "figure_cost_vs_robustness",
            )
        )
        paths.extend(generate_failure_gallery(loaded["main"], failure_dir))
        failure_sidecar = failure_dir / "failure_gallery.meta.json"
        write_json(
            failure_sidecar,
            _asset_sidecar("failure_gallery", "document", loaded["main"]),
        )
        paths.append(failure_sidecar)

        manifest_path = stage / "phase15_asset_bundle_manifest.json"
        staged_manifest = {
            "schema_version": "cab_phase15_asset_bundle_v1",
            "evidence_class": PAPER_EVIDENCE_CLASS,
            "scientific_evidence": True,
            "paper_eligible": True,
            "claim_promotion_performed": False,
            "sources": {
                role: validation["source_states"][role]["manifest"]
                for role in REQUIRED_SOURCE_ROLES
            },
            "contract": phase15_asset_contract(),
            "assets": [
                str(path.relative_to(stage))
                for path in sorted(paths)
                if path.exists()
            ],
        }
        write_json(manifest_path, staged_manifest)
        paths.append(manifest_path)

        shutil.move(str(stage), str(output))

    return [output / path.relative_to(stage) for path in paths]


def _bundle_validation_payload(
    source_states: dict[str, dict[str, Any]],
    issues: list[str],
    specialized: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "cab_phase15_asset_preflight_v1",
        "passed": not issues,
        "evidence_class": "ENGINEERING_ONLY",
        "scientific_evidence": False,
        "paper_assets_written": False,
        "claim_promotion_performed": False,
        "issues": issues,
        "source_states": source_states,
        "specialized": specialized,
        "contract_complete": phase15_asset_contract()["complete"],
    }


def _load_manifest_payload(run_path: Path) -> tuple[Path | None, dict[str, Any] | None]:
    candidates = (
        run_path / "run_manifest_v2.json",
        run_path / "canonical_run_manifest.json",
        run_path / "run_manifest.json",
    )
    for path in candidates:
        payload = _read_json_object(path)
        if payload is not None and payload.get("schema_version") == "cab_run_manifest_v2":
            return path, payload
    return None, None


def _manifest_pin_issues(manifest: CanonicalRunManifest) -> list[str]:
    issues: list[str] = []
    sha256_fields = (
        "task_pack_hash",
        "intervention_pack_hash",
        "scorer_policy_hash",
        "environment_hash",
        "prompt_hash",
    )
    for field in sha256_fields:
        value = str(getattr(manifest, field))
        if re.fullmatch(r"[0-9a-f]{64}", value) is None:
            issues.append(f"manifest {field} is not a pinned SHA-256")
    if re.fullmatch(r"[0-9a-f]{7,64}", manifest.code_revision) is None:
        issues.append("manifest code_revision is not a pinned revision hash")
    for field in (
        "study_id",
        "benchmark_version",
        "split_role",
        "scorer_name",
        "scorer_version",
        "model_id",
        "model_revision",
        "provider",
        "adapter_version",
        "prompt_version",
    ):
        value = str(getattr(manifest, field)).upper()
        if "REPLACE" in value or "PIN_BEFORE_EXECUTION" in value or value == "UNKNOWN":
            issues.append(f"manifest {field} remains a template placeholder")
    return issues


def _load_metadata(run_path: Path) -> dict[str, Any]:
    for name in ("run_metadata.json", "metadata.json"):
        payload = _read_json_object(run_path / name)
        if payload is not None:
            return payload
    return {}


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _study_marker(manifest: dict[str, Any], data: RunResults) -> str:
    fields = (
        manifest.get("study_id"),
        manifest.get("split_role"),
        data.run_metadata.get("study_id"),
        data.run_metadata.get("study_type"),
        data.run_metadata.get("split_role"),
    )
    return " ".join(str(value).lower() for value in fields if value)


def _has_measured_cost_and_runtime(data: RunResults) -> bool:
    if not data.trajectories:
        return False
    for trajectory in data.trajectories:
        metadata = trajectory.metadata
        if metadata.get("cost_status") != "MEASURED":
            return False
        if not isinstance(metadata.get("measured_cost_usd"), int | float):
            return False
        if not isinstance(metadata.get("latency_s"), int | float):
            return False
    return True


def _ablation_contract_issues(data: RunResults) -> list[str]:
    required = {"pair_id", "factor", "level", "comparison_role"}
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for trajectory in data.trajectories:
        raw = trajectory.metadata.get("ablation")
        if not isinstance(raw, dict) or not raw:
            continue
        missing = sorted(required - set(raw))
        if missing:
            issues.append(
                f"trajectory {trajectory.instance_id} ablation metadata missing "
                + ", ".join(missing)
            )
            continue
        if not trajectory.metadata.get("prompt_version_hash"):
            issues.append(
                f"trajectory {trajectory.instance_id} lacks prompt_version_hash"
            )
        rows.append(raw)
    if not rows:
        return ["no trajectory carries a complete ablation contract", *issues]

    roles_by_pair: dict[str, set[str]] = {}
    for row in rows:
        pair_id = str(row.get("pair_id"))
        roles_by_pair.setdefault(pair_id, set()).add(str(row.get("comparison_role")))
    for pair_id, roles in sorted(roles_by_pair.items()):
        if not {"reference", "treatment"}.issubset(roles):
            issues.append(
                f"ablation pair {pair_id!r} lacks both reference and treatment roles"
            )
    return issues


def _naturalistic_release_review_issues(data: RunResults) -> list[str]:
    review = data.run_metadata.get("naturalistic_release_review")
    if not isinstance(review, dict):
        return ["missing naturalistic_release_review metadata"]
    issues: list[str] = []
    for field in (
        "provenance_verified",
        "license_verified",
        "privacy_review_passed",
        "pii_scan_passed",
        "prompt_injection_scan_passed",
    ):
        if review.get(field) is not True:
            issues.append(f"naturalistic_release_review.{field} is not literal true")
    removal_procedure = review.get("removal_procedure")
    if not isinstance(removal_procedure, str) or not removal_procedure.strip():
        issues.append("naturalistic_release_review.removal_procedure is missing")
    return issues


def _find_scorer_validation_report(run_path: Path) -> tuple[Path | None, dict[str, Any]]:
    candidates = (
        run_path / "scorer_validation" / "scorer_sensitivity.json",
        run_path / "human_validation" / "scorer_sensitivity.json",
        run_path / "paper_inputs" / "scorer_sensitivity.json",
    )
    for path in candidates:
        payload = _read_json_object(path)
        if payload is not None:
            return path, payload
    return None, {}


def _validate_scorer_report(report: dict[str, Any]) -> list[str]:
    if not report:
        return ["missing scorer_sensitivity.json"]
    issues: list[str] = []
    if str(report.get("evidence_class") or "") not in AUDITED_HUMAN_EVIDENCE_CLASSES:
        issues.append("scorer report is not audited human evidence")
    if str(report.get("human_review_state") or "") != "HUMAN_REVIEW_COMPLETE":
        issues.append("scorer report human_review_state is not HUMAN_REVIEW_COMPLETE")
    if report.get("validation_threshold_met") is not True:
        issues.append("scorer report validation_threshold_met is not literal true")
    if int(report.get("independent_reviewer_count") or 0) < 2:
        issues.append("scorer report has fewer than two independent reviewers")
    if int(report.get("genuine_human_row_count") or 0) <= 0:
        issues.append("scorer report has no genuine human rows")
    if report.get("adjudication_complete") is not True:
        issues.append("scorer report adjudication_complete is not literal true")
    if not str(report.get("scorer_name") or "").strip():
        issues.append("scorer report is missing scorer_name")
    if not str(report.get("scorer_version") or "").strip():
        issues.append("scorer report is missing scorer_version")
    scenarios = report.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        issues.append("scorer report has no preregistered sensitivity scenarios")
    elif any(not _valid_scorer_scenario(row) for row in scenarios):
        issues.append("scorer report contains an incomplete sensitivity scenario")
    return issues


def _valid_scorer_scenario(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if not all(
        key in value
        for key in (
            "agent",
            "scenario",
            "false_positive_rate",
            "false_negative_rate",
            "acrs",
            "absolute_degradation",
        )
    ):
        return False
    if not str(value.get("agent") or "").strip() or not str(value.get("scenario") or "").strip():
        return False
    for field in ("false_positive_rate", "false_negative_rate", "acrs"):
        field_value = value.get(field)
        if isinstance(field_value, bool) or not isinstance(field_value, int | float):
            return False
        if not 0.0 <= float(field_value) <= 1.0:
            return False
    degradation = value.get("absolute_degradation")
    return (
        not isinstance(degradation, bool)
        and isinstance(degradation, int | float)
        and -1.0 <= float(degradation) <= 1.0
    )


def _find_human_review_report(run_path: Path) -> tuple[Path | None, dict[str, Any]]:
    candidates = (
        run_path / "human_review_gate.json",
        run_path / "human_validation" / "human_review_gate.json",
        run_path / "human_validation" / "summary" / "human_review_gate.json",
    )
    for path in candidates:
        payload = _read_json_object(path)
        if payload is not None:
            return path, payload
    return None, {}


def _validate_human_report(report: dict[str, Any]) -> list[str]:
    if not report:
        return ["missing human_review_gate.json"]
    issues: list[str] = []
    if report.get("c10_state") != "PASS":
        issues.append("C10 is not PASS")
    if report.get("human_review_state") != "HUMAN_REVIEW_COMPLETE":
        issues.append("human review is not complete")
    if int(report.get("genuine_human_row_count") or 0) <= 0:
        issues.append("no genuine human rows")
    if report.get("unresolved_disagreements"):
        issues.append("unresolved human-review disagreements remain")
    if str(report.get("evidence_class") or "") not in AUDITED_HUMAN_EVIDENCE_CLASSES:
        issues.append("human-review report is not audited real evidence")
    expected = int(report.get("expected_review_groups") or 0)
    complete = int(report.get("complete_review_groups") or 0)
    if expected <= 0 or complete != expected:
        issues.append("human-review coverage is incomplete")
    policy = _dict(report.get("policy"))
    minimum = policy.get("min_raw_agreement")
    agreement = report.get("raw_agreement")
    if (
        isinstance(minimum, bool)
        or not isinstance(minimum, int | float)
        or isinstance(agreement, bool)
        or not isinstance(agreement, int | float)
        or float(agreement) < float(minimum)
    ):
        issues.append("human-review raw agreement does not meet the registered threshold")
    final_validity = report.get("final_validity")
    if not isinstance(final_validity, dict) or not final_validity or not all(
        decision is True for decision in final_validity.values()
    ):
        issues.append("not every reviewed candidate has a final valid decision")
    return issues


def _transition_rows(stats: dict[str, Any]) -> list[dict[str, Any]]:
    paired = stats.get("paired_clean_vs_intervention")
    rows: list[dict[str, Any]] = []
    if not isinstance(paired, list):
        return rows
    for agent_row in paired:
        if not isinstance(agent_row, dict):
            continue
        profile = agent_row.get("transition_profile")
        if not isinstance(profile, dict):
            continue
        for transition, payload in profile.items():
            row = _dict(payload)
            rows.append(
                {
                    "agent": agent_row.get("agent"),
                    "transition": transition,
                    "count": row.get("count"),
                    "rate": row.get("rate"),
                    "n_pairs": agent_row.get("n_pairs"),
                }
            )
    return rows


def _rank_uncertainty_table(stats: dict[str, Any]) -> pd.DataFrame:
    rank = _dict(stats.get("rank_uncertainty"))
    agents = rank.get("agents")
    if not isinstance(agents, list) or not agents:
        raise ValueError("rank uncertainty table requires reportable agents")
    expected = _dict(rank.get("expected_rank"))
    intervals = _dict(rank.get("rank_ci"))
    changes = _dict(rank.get("probability_rank_changed_from_clean"))
    probabilities = _dict(rank.get("rank_probabilities"))
    rows = []
    for agent in agents:
        interval = intervals.get(agent)
        interval = interval if isinstance(interval, list) else [None, None]
        rows.append(
            {
                "agent": agent,
                "expected_robustness_rank": expected.get(agent),
                "rank_ci_low": interval[0] if interval else None,
                "rank_ci_high": interval[1] if len(interval) > 1 else None,
                "probability_rank_changed_from_clean": changes.get(agent),
                "rank_probabilities": json.dumps(probabilities.get(agent), sort_keys=True),
                "n_boot_valid": rank.get("n_boot_valid"),
                "cluster_key": rank.get("cluster_key"),
            }
        )
    return pd.DataFrame(rows)


def _transition_profile_table(stats: dict[str, Any]) -> pd.DataFrame:
    rows = _transition_rows(stats)
    if not rows:
        raise ValueError("transition profile table requires complete matched pairs")
    return pd.DataFrame(rows)


def _scorer_sensitivity_table(report: dict[str, Any]) -> pd.DataFrame:
    scenarios = report.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scorer sensitivity requires audited human-error scenarios")
    return pd.DataFrame([row for row in scenarios if isinstance(row, dict)])


def _intervention_validity_table(report: dict[str, Any]) -> pd.DataFrame:
    coverage = report.get("coverage")
    if not isinstance(coverage, dict) or not coverage:
        raise ValueError("intervention validity requires non-empty reviewed coverage")
    rows: list[dict[str, Any]] = []
    for candidate_id, reviews in sorted(coverage.items()):
        if not isinstance(reviews, dict):
            continue
        for review_file, summary in sorted(reviews.items()):
            row = _dict(summary)
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "review_file": review_file,
                    "independent_reviewer_count": row.get("independent_reviewer_count"),
                    "agreement": row.get("agreement"),
                    "adjudicated": row.get("adjudicated"),
                    "final_valid": row.get("final_valid"),
                    "c10_state": report.get("c10_state"),
                    "raw_agreement": report.get("raw_agreement"),
                }
            )
    if not rows:
        raise ValueError("intervention validity report has no exportable review groups")
    return pd.DataFrame(rows)


def _cost_runtime_table(data: RunResults) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    agents = sorted({trajectory.agent_name for trajectory in data.trajectories})
    for agent in agents:
        if "oracle" in agent.lower():
            continue
        trajectories = [
            trajectory for trajectory in data.trajectories if trajectory.agent_name == agent
        ]
        costs = [
            _required_float(trajectory.metadata.get("measured_cost_usd"))
            for trajectory in trajectories
        ]
        latencies = [
            _required_float(trajectory.metadata.get("latency_s"))
            for trajectory in trajectories
        ]
        aggregate = _dict(_dict(data.aggregate.get("by_agent")).get(agent))
        rows.append(
            {
                "agent": agent,
                "n_trajectories": len(trajectories),
                "cost_status": "MEASURED",
                "total_cost_usd": round(float(sum(costs)), 6),
                "mean_cost_per_trajectory_usd": round(float(np.mean(costs)), 6),
                "mean_latency_s": round(float(np.mean(latencies)), 6),
                "median_latency_s": round(float(np.median(latencies)), 6),
                "clean_success": aggregate.get("clean_success_rate"),
                "intervention_success": aggregate.get("intervention_success_rate"),
                "acrs": aggregate.get("acrs"),
                "absolute_degradation": aggregate.get("absolute_degradation"),
                "relative_degradation": aggregate.get("relative_degradation"),
            }
        )
    if not rows:
        raise ValueError("cost/runtime appendix requires measured non-oracle trajectories")
    return pd.DataFrame(rows)


def _rank_probability_figure(stats: dict[str, Any]) -> plt.Figure:
    rank = _dict(stats.get("rank_uncertainty"))
    matrix = _dict(rank.get("pairwise_rank_probability_matrix"))
    agents = [str(agent) for agent in rank.get("agents", [])]
    if not agents or not matrix:
        raise ValueError("rank probability figure requires a probability matrix")
    values = np.asarray(
        [
            [_required_float(_dict(matrix.get(row)).get(column)) for column in agents]
            for row in agents
        ]
    )
    fig, ax = plt.subplots(figsize=(max(6, len(agents)), max(5, len(agents) * 0.8)))
    image = ax.imshow(values, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(np.arange(len(agents)))
    ax.set_xticklabels(agents, rotation=30, ha="right")
    ax.set_yticks(np.arange(len(agents)))
    ax.set_yticklabels(agents)
    ax.set_xlabel("Comparison model")
    ax.set_ylabel("Row model")
    ax.set_title("Probability row model ranks above comparison model")
    for row in range(len(agents)):
        for column in range(len(agents)):
            ax.text(column, row, f"{values[row, column]:.2f}", ha="center", va="center")
    fig.colorbar(image, ax=ax, label="Rank probability")
    fig.tight_layout()
    return fig


def _transition_matrix_figure(stats: dict[str, Any]) -> plt.Figure:
    frame = _transition_profile_table(stats)
    matrix = frame.pivot(index="agent", columns="transition", values="rate").fillna(0.0)
    values = matrix.to_numpy(dtype=float)
    fig, ax = plt.subplots(
        figsize=(max(7, matrix.shape[1] * 1.5), max(4, matrix.shape[0] * 0.7))
    )
    image = ax.imshow(values, vmin=0, vmax=1, cmap="Blues", aspect="auto")
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels(matrix.columns, rotation=30, ha="right")
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index)
    ax.set_title("Matched clean-to-intervention transition profiles")
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            ax.text(column, row, f"{values[row, column]:.2f}", ha="center", va="center")
    fig.colorbar(image, ax=ax, label="Transition rate")
    fig.tight_layout()
    return fig


def _model_robustness_profile_figure(data: RunResults) -> plt.Figure:
    rows = []
    for agent, agent_row in _dict(data.aggregate.get("by_agent")).items():
        if "oracle" in str(agent).lower() or not isinstance(agent_row, dict):
            continue
        families = agent_row.get("families")
        if not isinstance(families, dict):
            continue
        for family, payload in families.items():
            family_row = _dict(payload)
            rows.append(
                {
                    "agent": str(agent),
                    "family": str(family),
                    "acrs_family": family_row.get("acrs_family"),
                }
            )
    if not rows:
        raise ValueError("model robustness profile requires per-family ACRS")
    frame = pd.DataFrame(rows)
    matrix = frame.pivot(index="family", columns="agent", values="acrs_family").sort_index()
    fig, ax = plt.subplots(figsize=(max(8, matrix.shape[0] * 0.8), 5))
    x = np.arange(matrix.shape[0])
    for agent in matrix.columns:
        ax.plot(x, matrix[agent], marker="o", label=str(agent))
    ax.set_xticks(x)
    ax.set_xticklabels(matrix.index, rotation=35, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Matched family ACRS")
    ax.set_title("Model robustness profile by intervention family")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def _scorer_sensitivity_figure(report: dict[str, Any]) -> plt.Figure:
    frame = _scorer_sensitivity_table(report)
    required = {"agent", "scenario", "acrs"}
    if not required.issubset(frame.columns):
        raise ValueError("scorer sensitivity scenarios lack agent/scenario/ACRS")
    fig, ax = plt.subplots(figsize=(max(8, len(frame["scenario"].unique()) * 1.2), 5))
    scenarios = list(dict.fromkeys(str(value) for value in frame["scenario"]))
    x = np.arange(len(scenarios))
    for agent, agent_rows in frame.groupby("agent"):
        by_scenario = {
            str(row["scenario"]): float(row["acrs"])
            for row in agent_rows.to_dict(orient="records")
        }
        ax.plot(
            x,
            [by_scenario.get(scenario, np.nan) for scenario in scenarios],
            marker="o",
            label=str(agent),
        )
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=30, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Scorer-adjusted ACRS")
    ax.set_title("Sensitivity to human-estimated scorer error")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def _measured_cost_vs_robustness_figure(data: RunResults) -> plt.Figure:
    frame = _cost_runtime_table(data)
    if "acrs" not in frame or frame["acrs"].dropna().empty:
        raise ValueError("cost/robustness figure requires measured cost and ACRS")
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(
        frame["mean_cost_per_trajectory_usd"],
        frame["acrs"],
        s=80,
        color="#4C78A8",
    )
    for row in frame.to_dict(orient="records"):
        ax.annotate(
            str(row["agent"]),
            (
                float(row["mean_cost_per_trajectory_usd"]),
                float(row["acrs"]),
            ),
            fontsize=8,
            xytext=(4, 4),
            textcoords="offset points",
        )
    ax.set_xlabel("Measured mean cost per trajectory (USD)")
    ax.set_ylabel("ACRS")
    ax.set_ylim(0, 1.05)
    ax.set_title("Measured cost versus robustness")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


def _write_table(
    frame: pd.DataFrame,
    stem: Path,
    data: RunResults,
    asset_id: str,
) -> list[Path]:
    if frame.empty or (
        "status" in frame
        and frame["status"].astype(str).str.lower().isin({"not yet run", "placeholder"}).any()
    ):
        raise ValueError(f"refusing placeholder or empty empirical table: {asset_id}")
    annotated = with_asset_metadata(frame, data)
    paths = write_table_bundle(annotated, stem)
    sidecar = stem.with_suffix(".meta.json")
    write_json(sidecar, _asset_sidecar(asset_id, "table", data))
    return [*paths, sidecar]


def _write_figure(
    figure: plt.Figure,
    stem: Path,
    data: RunResults,
    asset_id: str,
) -> list[Path]:
    png = stem.with_suffix(".png")
    pdf = stem.with_suffix(".pdf")
    figure.savefig(png, dpi=180)
    figure.savefig(pdf)
    plt.close(figure)
    sidecar = stem.with_suffix(".meta.json")
    write_json(sidecar, _asset_sidecar(asset_id, "figure", data))
    return [png, pdf, sidecar]


def _asset_sidecar(asset_id: str, asset_type: str, data: RunResults) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "placeholder": False,
        "scientific_evidence": True,
        "evidence_class": PAPER_EVIDENCE_CLASS,
        "eligible_for_paper_claims": True,
        "claim_promotion_performed": False,
        "provenance": asset_metadata(data),
    }


def _required_float(value: Any) -> float:
    if not isinstance(value, int | float | str):
        raise ValueError(f"expected numeric paper asset value, got {value!r}")
    return float(value)
