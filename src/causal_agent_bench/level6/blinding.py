"""Physically separated two-stage review archives and fail-closed unlocks."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.hashing import stable_hash

STAGE1_FORBIDDEN_KEYS = {
    "accepted_answers",
    "answer_contract",
    "clean_gold_derivation",
    "derivation_graph",
    "gold_answer_policy",
    "gold_derivation",
    "intended_recovery_route",
    "recovery_authorizations",
    "required_recovery_actions",
    "scorer_policy",
    "stage2_locked_items",
}


class Stage1FinalizationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "cab_stage1_finalization_receipt_v2"
    packet_hashes: dict[str, str]
    judgment_hashes: dict[str, str]
    reviewer_receipt_hashes: dict[str, str]
    finalized: bool
    fixture_only: bool = False


class Stage2UnlockReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "cab_stage2_unlock_receipt_v2"
    stage1_finalization_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    coordinator_id: str = Field(min_length=1)
    coordinator_signature: str = Field(min_length=1)
    unlocked: bool
    fixture_only: bool = False


def build_physically_separated_review_archives(
    repo_root: str | Path,
    *,
    output_root: str | Path = "private_data/review_packages",
    unlock_receipt: Stage2UnlockReceipt | None = None,
    fixture_only: bool = False,
) -> dict[str, Any]:
    """Create role archives under separate roots; real Stage 2 requires unlock."""

    root = Path(repo_root).resolve()
    destination = _resolve(root, output_root)
    stage1_root = destination / "stage1"
    stage2_root = destination / "stage2"
    adjudication_root = destination / "adjudication"
    for directory in (stage1_root, stage2_root, adjudication_root):
        directory.mkdir(parents=True, exist_ok=True)
    evidence_index = _read_json(
        root / "data/compact20_reviewed/reviewer_evidence/bundle_index.json"
    )
    stage1_items = []
    stage2_items = []
    for row in evidence_index.get("bundles", []):
        bundle_path = root / row["path"]
        bundle = _read_json(bundle_path)
        candidate_dir = bundle_path.parent
        stage1_items.append(
            {
                "schema_version": "cab_stage1_review_item_v2",
                "candidate_id": bundle["candidate_id"],
                "task": _read_json(candidate_dir / "clean_fixture.json"),
                "intervention": _read_json(candidate_dir / "intervention_fixture.json"),
                "reviewer_visible_artifact": _read_json(
                    candidate_dir / "controlled_evidence.json"
                ),
                "tool_contracts": _read_json(candidate_dir / "tool_contracts.json"),
                "tool_transcripts": _read_json(candidate_dir / "tool_transcripts.json"),
                "semantic_fact_labels": [
                    fact["canonical_label"]
                    for fact in _read_json(candidate_dir / "controlled_evidence.json")["facts"]
                ],
                "blank_stage1_judgment": {},
                "fixture_only": fixture_only,
            }
        )
        stage2_items.append(
            {
                "schema_version": "cab_stage2_review_item_v2",
                "candidate_id": bundle["candidate_id"],
                "gold_derivation": _read_json(candidate_dir / "gold_derivation.json"),
                "answer_and_scorer_contracts": _stage2_contracts(
                    root,
                    bundle["intervention_instance_id"],
                ),
                "recovery_authorizations": bundle["recovery_authorizations"],
                "intervention_routes": bundle["intervention_routes"],
                "blank_stage2_judgment": {},
                "fixture_only": fixture_only,
            }
        )

    stage1_payload = {
        "schema_version": "cab_stage1_role_packet_v2",
        "items": stage1_items,
        "gold_included": False,
        "scorer_included": False,
        "fixture_only": fixture_only,
    }
    leakage = scan_stage1_payload(stage1_payload)
    if not leakage["passed"]:
        raise ValueError(f"Stage-1 leakage detected: {leakage['findings']}")
    stage1_archives = {}
    for role in ("reviewer_a", "reviewer_b", "adjudicator"):
        path = stage1_root / f"stage1_{role}.zip"
        _write_role_archive(path, "stage1_review_items.json", stage1_payload, role)
        stage1_archives[path.name] = _archive_row(path, root)

    stage2_allowed = bool(
        fixture_only
        or (
            unlock_receipt is not None
            and unlock_receipt.unlocked
            and not unlock_receipt.fixture_only
        )
    )
    if not stage2_allowed:
        raise PermissionError(
            "real Stage-2 generation requires finalized Stage-1 receipts and a genuine coordinator unlock"
        )
    stage2_payload = {
        "schema_version": "cab_stage2_role_packet_v2",
        "stage1_packet_hashes": {
            name: row["sha256"] for name, row in stage1_archives.items()
        },
        "unlock_receipt": unlock_receipt.model_dump(mode="json") if unlock_receipt else None,
        "items": stage2_items,
        "fixture_only": fixture_only,
    }
    stage2_archives = {}
    for role in ("reviewer_a", "reviewer_b", "adjudicator"):
        archive_root = adjudication_root if role == "adjudicator" else stage2_root
        path = archive_root / f"stage2_{role}.zip"
        _write_role_archive(path, "stage2_review_items.json", stage2_payload, role)
        stage2_archives[path.name] = _archive_row(path, root)
    manifest: dict[str, Any] = {
        "schema_version": "cab_physically_separated_review_archives_v2",
        "status": "CAB_TRUE_TWO_STAGE_BLINDING_READY",
        "stage1_root": _display_path(stage1_root, root),
        "stage2_root": _display_path(stage2_root, root),
        "adjudication_root": _display_path(adjudication_root, root),
        "stage1_archives": stage1_archives,
        "stage2_archives": stage2_archives,
        "stage1_leakage_scan": leakage,
        "stage2_generated_after_unlock": stage2_allowed,
        "fixture_only": fixture_only,
        "genuine_human_review_rows": 0,
    }
    manifest["manifest_hash"] = stable_hash(manifest, length=64)
    (destination / "archive_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def scan_stage1_payload(payload: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                normalized = str(key).casefold()
                if normalized in STAGE1_FORBIDDEN_KEYS or normalized.startswith("stage2_"):
                    findings.append(f"{path}.{key}")
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")

    walk(payload, "stage1")
    return {
        "passed": not findings,
        "findings": sorted(set(findings)),
        "scanned_for": sorted(STAGE1_FORBIDDEN_KEYS),
    }


def validate_stage2_unlock_receipts(
    finalization: Stage1FinalizationReceipt,
    unlock: Stage2UnlockReceipt,
) -> dict[str, Any]:
    expected = stable_hash(finalization.model_dump(mode="json"), length=64)
    checks = {
        "stage1_finalized": finalization.finalized,
        "packet_hashes_present": bool(finalization.packet_hashes),
        "judgment_hashes_present": bool(finalization.judgment_hashes),
        "reviewer_receipts_present": bool(finalization.reviewer_receipt_hashes),
        "binding_valid": unlock.stage1_finalization_hash == expected,
        "coordinator_authorized": unlock.unlocked,
        "genuine_boundary_preserved": not (
            not finalization.fixture_only and unlock.fixture_only
        ),
    }
    return {"passed": all(checks.values()), "checks": checks}


def _stage2_contracts(root: Path, instance_id: str) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in (
            root / "data/compact20_reviewed/compact20_v2_instances.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    row = next(value for value in rows if value["instance_id"] == instance_id)
    intervention = row["intervention"]
    return {
        "answer_contract": intervention.get("answer_contract"),
        "gold_answer_policy": intervention.get("gold_answer_policy"),
        "scorer_policy": intervention.get("scorer_policy"),
    }


def _write_role_archive(path: Path, name: str, payload: dict[str, Any], role: str) -> None:
    encoded = json.dumps(
        {**payload, "role": role},
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(info, encoded)


def _archive_row(path: Path, root: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        unsafe = [
            name
            for name in archive.namelist()
            if name.startswith("/") or ".." in Path(name).parts
        ]
    return {
        "path": _display_path(path, root),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "archive_traversal_entries": unsafe,
    }


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


__all__ = [
    "Stage1FinalizationReceipt",
    "Stage2UnlockReceipt",
    "build_physically_separated_review_archives",
    "scan_stage1_payload",
    "validate_stage2_unlock_receipts",
]
