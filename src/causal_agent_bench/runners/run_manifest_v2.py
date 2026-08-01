"""Canonical run-manifest and append-only ledger contracts.

The helpers are usable in fixture mode without executing a model.  They make
provenance, merge compatibility, and evidence classification explicit before a
future run is allowed to start.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EvidenceClass = Literal[
    "DESIGN_ONLY",
    "ENGINEERING_ONLY",
    "FIXTURE_ONLY",
    "HUMAN_INPUT_REQUIRED",
    "EXECUTION_PENDING",
    "PRELIMINARY_REAL_EVIDENCE",
    "AUDITED_REAL_EVIDENCE",
    "PAPER_ELIGIBLE_EVIDENCE",
]
RunStatus = Literal[
    "planned",
    "preflight_passed",
    "running",
    "checkpointed",
    "complete",
    "incomplete",
    "failed",
    "interrupted",
    "audit_pending",
    "audited",
]


class CanonicalRunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cab_run_manifest_v2"] = "cab_run_manifest_v2"
    study_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    benchmark_version: str = Field(min_length=1)
    split_role: str = Field(min_length=1)
    task_pack_hash: str = Field(min_length=1)
    intervention_pack_hash: str = Field(min_length=1)
    scorer_name: str = Field(min_length=1)
    scorer_version: str = Field(min_length=1)
    scorer_policy_hash: str = Field(min_length=1)
    code_revision: str = Field(min_length=1)
    environment_hash: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    adapter_version: str = Field(min_length=1)
    adapter_lane: Literal[
        "cab_json_tool_protocol_v3",
        "native_tool_calling_secondary_ablation_v1",
    ] | None = None
    system_identity_hash: str | None = None
    quantization: str
    device: str = Field(min_length=1)
    gpu_count: int = Field(ge=0)
    seed: int
    repeat: int = Field(ge=0)
    prompt_version: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=1)
    tool_budget: int = Field(ge=0)
    token_budget: int = Field(ge=0)
    timeout_seconds: int = Field(gt=0)
    retry_policy: dict[str, Any]
    raac_policy: dict[str, Any] | None = None
    raac_comparison_mode: Literal["equal_budget", "practical_budget"] | None = None
    raac_overhead: dict[str, Any] = Field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: RunStatus = "planned"
    cost_usd: float | None = Field(default=None, ge=0)
    cost_status: Literal["ESTIMATE_NOT_MEASURED", "MEASURED", "NOT_APPLICABLE"] = (
        "ESTIMATE_NOT_MEASURED"
    )
    trajectory_path: str = Field(min_length=1)
    score_path: str = Field(min_length=1)
    audit_state: str = Field(min_length=1)
    evidence_class: EvidenceClass = "EXECUTION_PENDING"
    scientific_evidence: bool = False
    paper_eligible: bool = False

    @model_validator(mode="after")
    def enforce_evidence_transitions(self) -> CanonicalRunManifest:
        real_evidence = {
            "PRELIMINARY_REAL_EVIDENCE",
            "AUDITED_REAL_EVIDENCE",
            "PAPER_ELIGIBLE_EVIDENCE",
        }
        if self.scientific_evidence and self.evidence_class not in real_evidence:
            raise ValueError("scientific_evidence requires a real-evidence class")
        if self.scientific_evidence:
            if self.scorer_version != "3.0.0":
                raise ValueError(
                    "scientific evidence requires scorer semantics version 3.0.0"
                )
            if self.system_identity_hash is None or not re.fullmatch(
                r"[0-9a-f]{64}", self.system_identity_hash
            ):
                raise ValueError(
                    "scientific evidence requires a bound system_identity_hash"
                )
            if self.adapter_lane is None:
                raise ValueError("scientific evidence requires an explicit adapter_lane")
        if self.paper_eligible:
            if self.evidence_class != "PAPER_ELIGIBLE_EVIDENCE":
                raise ValueError("paper_eligible requires PAPER_ELIGIBLE_EVIDENCE")
            if self.status != "audited" or not self.scientific_evidence:
                raise ValueError("paper eligibility requires audited scientific evidence")
        if self.cost_status == "MEASURED" and self.status in {"planned", "preflight_passed"}:
            raise ValueError("a planned/preflight run cannot claim measured cost")
        if self.end_time is not None and self.start_time is not None:
            if self.end_time < self.start_time:
                raise ValueError("end_time must not precede start_time")
        return self


def append_run_ledger(
    ledger_path: str | Path,
    manifest: CanonicalRunManifest,
) -> dict[str, Any]:
    """Append a hash-chained manifest, refusing duplicate-ID conflicts."""

    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prior_rows = _read_ledger(path)
    manifest_payload = manifest.model_dump(mode="json")
    manifest_hash = _hash_payload(manifest_payload)
    for row in prior_rows:
        if row.get("run_id") != manifest.run_id:
            continue
        if row.get("manifest_hash") == manifest_hash:
            return {
                "appended": False,
                "deduplicated": True,
                "run_id": manifest.run_id,
                "record_hash": row.get("record_hash"),
            }
        raise ValueError(f"conflicting ledger record for run_id={manifest.run_id}")

    previous_hash = prior_rows[-1].get("record_hash") if prior_rows else None
    record = {
        "ledger_schema_version": "cab_append_only_run_ledger_v1",
        "recorded_at": datetime.now(UTC).isoformat(),
        "previous_record_hash": previous_hash,
        "manifest_hash": manifest_hash,
        **manifest_payload,
    }
    record["record_hash"] = _hash_payload(record)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return {
        "appended": True,
        "deduplicated": False,
        "run_id": manifest.run_id,
        "record_hash": record["record_hash"],
    }


def validate_run_ledger(ledger_path: str | Path) -> list[str]:
    path = Path(ledger_path)
    rows = _read_ledger(path)
    issues: list[str] = []
    seen: set[str] = set()
    previous_hash: str | None = None
    for index, row in enumerate(rows, 1):
        run_id = str(row.get("run_id", ""))
        if not run_id:
            issues.append(f"row {index}: missing run_id")
        elif run_id in seen:
            issues.append(f"row {index}: duplicate run_id {run_id}")
        seen.add(run_id)
        if row.get("previous_record_hash") != previous_hash:
            issues.append(f"row {index}: broken previous_record_hash chain")
        recorded_hash = row.get("record_hash")
        candidate = {key: value for key, value in row.items() if key != "record_hash"}
        if recorded_hash != _hash_payload(candidate):
            issues.append(f"row {index}: record_hash mismatch")
        previous_hash = str(recorded_hash) if recorded_hash else None
        manifest_fields = {
            key: value
            for key, value in row.items()
            if key
            not in {
                "ledger_schema_version",
                "recorded_at",
                "previous_record_hash",
                "manifest_hash",
                "record_hash",
            }
        }
        try:
            manifest = CanonicalRunManifest.model_validate(manifest_fields)
        except Exception as exc:  # pydantic formats the exact field failures
            issues.append(f"row {index}: invalid manifest ({type(exc).__name__})")
            continue
        if row.get("manifest_hash") != _hash_payload(manifest.model_dump(mode="json")):
            issues.append(f"row {index}: manifest_hash mismatch")
    return issues


def validate_merge_manifests(
    manifests: list[CanonicalRunManifest],
    *,
    completed_keys: list[tuple[str, int]],
    expected_task_ids: list[str],
    expected_repeats: list[int],
) -> dict[str, Any]:
    """Check merge invariants and exact task/repeat completeness."""

    invariant_fields = (
        "study_id",
        "benchmark_version",
        "split_role",
        "task_pack_hash",
        "intervention_pack_hash",
        "scorer_version",
        "scorer_policy_hash",
        "model_id",
        "model_revision",
        "adapter_lane",
        "system_identity_hash",
        "prompt_hash",
        "raac_policy",
        "raac_comparison_mode",
    )
    conflicts: list[str] = []
    if manifests:
        reference = manifests[0]
        for manifest in manifests[1:]:
            for field in invariant_fields:
                if getattr(reference, field) != getattr(manifest, field):
                    conflicts.append(field)
    counts: dict[tuple[str, int], int] = {}
    for key in completed_keys:
        counts[key] = counts.get(key, 0) + 1
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    expected = {
        (task_id, repeat)
        for task_id in expected_task_ids
        for repeat in expected_repeats
    }
    actual = set(completed_keys)
    missing = sorted(expected - actual)
    extras = sorted(actual - expected)
    evidence_classes = sorted({manifest.evidence_class for manifest in manifests})
    if len(evidence_classes) > 1:
        conflicts.append("evidence_class")
    return {
        "manifest_count": len(manifests),
        "invariant_conflicts": sorted(set(conflicts)),
        "duplicate_keys": duplicates,
        "missing_keys": missing,
        "extra_keys": extras,
        "evidence_classes": evidence_classes,
        "passed": not conflicts and not duplicates and not missing and not extras,
    }


def write_manifest_template(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "cab_run_manifest_v2",
        "study_id": "REPLACE_BEFORE_EXECUTION",
        "run_id": "REPLACE_BEFORE_EXECUTION",
        "benchmark_version": "REPLACE_WITH_FROZEN_VERSION",
        "split_role": "REPLACE_WITH_CANONICAL_ROLE",
        "task_pack_hash": "PIN_BEFORE_EXECUTION",
        "intervention_pack_hash": "PIN_BEFORE_EXECUTION",
        "scorer_name": "cab_typed_policy_scorer",
        "scorer_version": "PIN_BEFORE_EXECUTION",
        "scorer_policy_hash": "PIN_BEFORE_EXECUTION",
        "code_revision": "PIN_BEFORE_EXECUTION",
        "environment_hash": "PIN_BEFORE_EXECUTION",
        "model_id": "PIN_BEFORE_EXECUTION",
        "model_revision": "PIN_BEFORE_EXECUTION",
        "provider": "PIN_BEFORE_EXECUTION",
        "adapter_version": "PIN_BEFORE_EXECUTION",
        "adapter_lane": None,
        "system_identity_hash": None,
        "quantization": "none",
        "device": "PIN_BEFORE_EXECUTION",
        "gpu_count": 0,
        "seed": 0,
        "repeat": 0,
        "prompt_version": "PIN_BEFORE_EXECUTION",
        "prompt_hash": "PIN_BEFORE_EXECUTION",
        "tool_budget": 0,
        "token_budget": 0,
        "timeout_seconds": 1,
        "retry_policy": {"max_retries": 0, "equal_across_models": True},
        "raac_policy": None,
        "raac_comparison_mode": None,
        "raac_overhead": {},
        "start_time": None,
        "end_time": None,
        "status": "planned",
        "cost_usd": None,
        "cost_status": "ESTIMATE_NOT_MEASURED",
        "trajectory_path": "results/REPLACE/trajectories.jsonl",
        "score_path": "results/REPLACE/scores.jsonl",
        "audit_state": "EXECUTION_PENDING",
        "evidence_class": "EXECUTION_PENDING",
        "scientific_evidence": False,
        "paper_eligible": False,
    }
    CanonicalRunManifest.model_validate(payload)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                rows.append({})
                continue
            rows.append(payload if isinstance(payload, dict) else {})
    return rows


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
