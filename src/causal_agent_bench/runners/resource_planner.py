"""Manifest-driven CAB trajectory, resource, and shard planning."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.hashing import stable_hash

ScenarioName = Literal["minimum", "planned", "conservative", "rerun_reserve"]


class StudyPlanningSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: str
    count_source: Literal["compact20", "aggregate_counts"]
    planned_models: int = Field(ge=1)
    planned_policies: int = Field(ge=1)
    planned_repeats: int = Field(ge=1)


class PlanningAssumptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bootstrap_repetitions: int = Field(ge=1)
    cpu_seconds_per_trajectory: float = Field(gt=0)
    expected_files_per_shard: int = Field(ge=1)
    gpu_seconds_per_model_call: float = Field(gt=0)
    mean_model_calls_per_trajectory: float = Field(gt=0)
    storage_kib_per_trajectory: float = Field(gt=0)
    target_trajectories_per_shard: int = Field(ge=1)


class ResourcePlannerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cab_study_execution_planner_v1"]
    assumptions: PlanningAssumptions
    studies: dict[str, StudyPlanningSpec]

    @model_validator(mode="after")
    def require_canonical_studies(self) -> ResourcePlannerConfig:
        required = {
            "compact20",
            "compact20_raac_light",
            "scale100",
            "scale100_raac_light",
            "raac_equal_budget",
            "raac_ablations",
            "transfer",
        }
        if not required.issubset(self.studies):
            raise ValueError(
                f"planner is missing canonical studies: {sorted(required - set(self.studies))}"
            )
        return self


def plan_study_resources(
    repo_root: str | Path,
    *,
    study: str,
    scenario: ScenarioName = "planned",
    config_path: str | Path = "configs/pre_run/study_execution_manifests.json",
    shard_override: int | None = None,
    declared_total_trajectories: int | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    config_file = _resolve(root, config_path)
    config = ResourcePlannerConfig.model_validate_json(
        config_file.read_text(encoding="utf-8")
    )
    if study not in config.studies:
        raise ValueError(
            f"unknown study {study!r}; expected one of {sorted(config.studies)}"
        )
    spec = config.studies[study]
    manifest_path = _resolve(root, spec.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    counts = _manifest_counts(manifest, spec.count_source)
    models, policies, repeats, rerun_fraction = _scenario_dimensions(spec, scenario)
    trajectories_without_reserve = (
        counts["instance_count"] * models * policies * repeats
    )
    rerun_trajectories = math.ceil(
        trajectories_without_reserve * rerun_fraction
    )
    total_trajectories = trajectories_without_reserve + rerun_trajectories
    if (
        declared_total_trajectories is not None
        and declared_total_trajectories != total_trajectories
    ):
        raise ValueError(
            "STALE_MANUAL_TOTAL: declared total "
            f"{declared_total_trajectories} != manifest-derived {total_trajectories}"
        )
    assumptions = config.assumptions
    shard_count = shard_override or max(
        1,
        math.ceil(
            total_trajectories / assumptions.target_trajectories_per_shard
        ),
    )
    if shard_count < 1:
        raise ValueError("shard count must be positive")
    trajectories_per_shard = math.ceil(total_trajectories / shard_count)
    model_calls = math.ceil(
        total_trajectories * assumptions.mean_model_calls_per_trajectory
    )
    expected_files = (
        shard_count * assumptions.expected_files_per_shard + 6
    )
    bootstrap_workload = (
        assumptions.bootstrap_repetitions
        * models
        * max(counts["family_count"], 1)
        * policies
    )
    manifest_hash = _sha256_file(manifest_path)
    payload: dict[str, Any] = {
        "schema_version": "cab_manifest_driven_resource_plan_v1",
        "study": study,
        "scenario": scenario,
        "manifest_path": spec.manifest,
        "manifest_sha256": manifest_hash,
        "planner_config_sha256": _sha256_file(config_file),
        "counts": {
            **counts,
            "models": models,
            "policies": policies,
            "repeats": repeats,
            "seeds": repeats,
            "trajectories_without_reserve": trajectories_without_reserve,
            "rerun_reserve_trajectories": rerun_trajectories,
            "total_trajectories": total_trajectories,
        },
        "shards": {
            "shard_count": shard_count,
            "maximum_trajectories_per_shard": trajectories_per_shard,
            "expected_files": expected_files,
            "merge_requires_exact_manifest_hash": True,
        },
        "resources": {
            "model_calls": model_calls,
            "storage_gib": round(
                total_trajectories
                * assumptions.storage_kib_per_trajectory
                / (1024 * 1024),
                6,
            ),
            "gpu_hours": round(
                model_calls * assumptions.gpu_seconds_per_model_call / 3600,
                6,
            ),
            "cpu_merge_scoring_hours": round(
                total_trajectories
                * assumptions.cpu_seconds_per_trajectory
                / 3600,
                6,
            ),
            "bootstrap_replicate_cells": bootstrap_workload,
        },
        "assumptions": assumptions.model_dump(mode="json"),
        "manual_total_accepted": declared_total_trajectories,
        "scientific_execution_performed": False,
        "evidence_class": "DESIGN_ONLY",
    }
    payload["plan_receipt"] = stable_hash(payload, length=64)
    return payload


def plan_all_scenarios(
    repo_root: str | Path,
    *,
    config_path: str | Path = "configs/pre_run/study_execution_manifests.json",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    config_file = _resolve(root, config_path)
    config = ResourcePlannerConfig.model_validate_json(
        config_file.read_text(encoding="utf-8")
    )
    scenarios: tuple[ScenarioName, ...] = (
        "minimum",
        "planned",
        "conservative",
        "rerun_reserve",
    )
    plans = {
        study: {
            scenario: plan_study_resources(
                root,
                study=study,
                scenario=scenario,
                config_path=config_file,
            )
            for scenario in scenarios
        }
        for study in sorted(config.studies)
    }
    payload = {
        "schema_version": "cab_resource_plan_matrix_v1",
        "studies": plans,
        "scientific_execution_performed": False,
    }
    payload["matrix_receipt"] = stable_hash(payload, length=64)
    return payload


def _manifest_counts(
    manifest: dict[str, Any],
    source: str,
) -> dict[str, int]:
    if source == "compact20":
        clean = int(manifest.get("unique_base_task_count") or 0)
        intervention = int(manifest.get("candidate_count") or 0)
        family_count = 4
    else:
        aggregate = manifest.get("aggregate_counts")
        if not isinstance(aggregate, dict):
            raise ValueError("public manifest lacks aggregate_counts")
        clean = int(aggregate.get("base_task_count") or 0)
        intervention = int(aggregate.get("intervention_count") or 0)
        assignment = manifest.get("assignment_design")
        family_count = int(
            assignment.get("family_count", 0)
            if isinstance(assignment, dict)
            else 0
        )
    if clean <= 0 or intervention <= 0:
        raise ValueError("manifest-derived clean/intervention counts must be positive")
    return {
        "tasks": clean,
        "clean_instances": clean,
        "intervention_instances": intervention,
        "instance_count": clean + intervention,
        "family_count": family_count,
    }


def _scenario_dimensions(
    spec: StudyPlanningSpec,
    scenario: ScenarioName,
) -> tuple[int, int, int, float]:
    if scenario == "minimum":
        return 1, 1, 1, 0.0
    if scenario == "planned":
        return (
            spec.planned_models,
            spec.planned_policies,
            spec.planned_repeats,
            0.0,
        )
    if scenario == "conservative":
        return (
            spec.planned_models,
            spec.planned_policies,
            spec.planned_repeats + 1,
            0.0,
        )
    return (
        spec.planned_models,
        spec.planned_policies,
        spec.planned_repeats,
        0.20,
    )


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "ResourcePlannerConfig",
    "plan_all_scenarios",
    "plan_study_resources",
]
