"""Pre-run smoke ingestion and staged RAAC execution contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.resource_planner import plan_all_scenarios


class SmokeMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cab_smoke_measurement_v1"]
    smoke_run_id: str = Field(min_length=1)
    system_identity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    code_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    task_pack_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trajectory_count: int = Field(ge=1)
    completed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    latency_seconds: list[float] = Field(min_length=1)
    throughput_trajectories_per_hour: float = Field(gt=0)
    shard_count: int = Field(ge=1)
    storage_bytes: int = Field(ge=0)
    failure_counts: dict[str, int]
    kaggle_runtime_seconds: float | None = Field(default=None, gt=0)
    cpu_merge_scoring_seconds: float = Field(ge=0)
    measured_at: str = Field(min_length=1)
    evidence_class: Literal["FIXTURE_MEASUREMENT", "LIVE_SMOKE_MEASUREMENT"]

    @model_validator(mode="after")
    def counts_reconcile(self) -> SmokeMeasurement:
        if self.completed_count + self.failed_count != self.trajectory_count:
            raise ValueError("completed + failed must equal trajectory_count")
        if len(self.latency_seconds) != self.trajectory_count:
            raise ValueError("one latency value is required per trajectory")
        return self


def build_smoke_and_staged_raac_plan(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/final_pre_review",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = _resolve(root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    resource_matrix = plan_all_scenarios(root)
    smoke_schema = SmokeMeasurement.model_json_schema()
    schema_path = out / "SMOKE_MEASUREMENT_SCHEMA.json"
    schema_path.write_text(
        json.dumps(smoke_schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    smoke: dict[str, Any] = {
        "schema_version": "cab_smoke_calibration_readiness_v1",
        "status": "CAB_SMOKE_CALIBRATION_AND_STAGED_RAAC_PLAN_READY",
        "exact_manifest_counts": {
            study: rows["planned"]["counts"] for study, rows in resource_matrix["studies"].items()
        },
        "assumptions": {
            "source": "configs/pre_run/study_execution_manifests.json",
            "classification": "ASSUMPTION_BASED_PRE_SMOKE_PROJECTION",
        },
        "fixture_measurements": {
            "available": True,
            "classification": "FIXTURE_MEASUREMENT_NOT_LIVE_PERFORMANCE",
        },
        "live_smoke_measurements": {
            "available": False,
            "classification": "LIVE_SMOKE_REQUIRED",
            "ingestion_schema": schema_path.relative_to(root).as_posix(),
        },
        "future_summary_fields": [
            "median_latency_seconds",
            "p90_latency_seconds",
            "latency_confidence_interval",
            "system_throughput_trajectories_per_hour",
            "shard_count",
            "storage_bytes",
            "failure_counts",
            "kaggle_runtime_seconds",
            "cpu_merge_scoring_seconds",
        ],
        "projected_intervals": {
            "allowed_before_smoke": False,
            "method_after_smoke": "cluster bootstrap by base task and shard",
        },
        "full_measurements": {
            "available": False,
            "classification": "LIVE_EVIDENCE_REQUIRED",
        },
        "gpu_runtime_label": "ASSUMPTION_BASED_PRE_SMOKE_PROJECTION",
        "scientific_execution_performed": False,
    }
    smoke["readiness_hash"] = stable_hash(smoke, length=64)
    smoke_path = out / "SMOKE_CALIBRATION_READINESS.json"
    smoke_path.write_text(
        json.dumps(smoke, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    waves = [
        {
            "wave": "A",
            "scope": "provider-free deterministic fixtures",
            "maximum_trajectories": 36,
            "requires": ["all static and executable final-pre-review gates pass"],
            "continue_when": ["zero integrity failures", "zero merge mismatches"],
            "stop_when": ["any silent corruption", "any manifest mismatch"],
        },
        {
            "wave": "B",
            "scope": "approved live smoke, one model within model",
            "maximum_trajectories": 72,
            "requires": ["cryptographic scientific approval", "Wave A pass"],
            "continue_when": ["failure rate <= 5%", "resource interval finite"],
            "stop_when": ["approval invalid", "p90 runtime exceeds budget"],
        },
        {
            "wave": "C",
            "scope": "Compact-20 staged RAAC within model",
            "maximum_trajectories": 432,
            "requires": ["Wave B calibrated", "human C10 passed"],
            "continue_when": ["no scorer drift", "no safety regression"],
            "stop_when": ["false-abstention regression", "ranking unstable beyond plan"],
        },
        {
            "wave": "D",
            "scope": "Scale confirmatory staged expansion",
            "maximum_trajectories": 8100,
            "requires": ["Wave C pass", "renewed content-bound approval"],
            "continue_when": ["predeclared precision and integrity gates pass"],
            "stop_when": ["missingness > 10%", "budget or power assumptions invalidated"],
        },
    ]
    staged: dict[str, Any] = {
        "schema_version": "cab_staged_raac_execution_plan_v1",
        "status": "CAB_SMOKE_CALIBRATION_AND_STAGED_RAAC_PLAN_READY",
        "waves": waves,
        "full_81000_trajectory_run_is_immediate_default": False,
        "full_run_requires_new_decision_and_receipt": True,
        "comparison_unit": "within_model_paired_base_task",
        "scientific_execution_performed": False,
    }
    staged["plan_hash"] = stable_hash(staged, length=64)
    staged_path = out / "STAGED_RAAC_PLAN.json"
    staged_path.write_text(
        json.dumps(staged, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"smoke": smoke, "staged_raac": staged}


def validate_smoke_and_staged_raac_plan(
    repo_root: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    smoke = json.loads(
        (root / "reports/final_pre_review/SMOKE_CALIBRATION_READINESS.json").read_text(
            encoding="utf-8"
        )
    )
    staged = json.loads(
        (root / "reports/final_pre_review/STAGED_RAAC_PLAN.json").read_text(encoding="utf-8")
    )
    checks = {
        "pre_smoke_label": smoke.get("gpu_runtime_label")
        == "ASSUMPTION_BASED_PRE_SMOKE_PROJECTION",
        "no_fake_live_measurements": smoke.get("live_smoke_measurements", {}).get("available")
        is False,
        "future_fields_complete": len(smoke.get("future_summary_fields", [])) >= 9,
        "waves_exact": [row.get("wave") for row in staged.get("waves", [])] == ["A", "B", "C", "D"],
        "full_run_not_default": staged.get("full_81000_trajectory_run_is_immediate_default")
        is False,
        "every_wave_has_rules": all(
            row.get("continue_when") and row.get("stop_when") for row in staged.get("waves", [])
        ),
    }
    return {
        "schema_version": "cab_smoke_staged_raac_validation_v1",
        "passed": all(checks.values()),
        "checks": checks,
    }


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


__all__ = [
    "SmokeMeasurement",
    "build_smoke_and_staged_raac_plan",
    "validate_smoke_and_staged_raac_plan",
]
