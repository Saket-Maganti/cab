"""Canonical, hashed study-role registry for the CAB pre-execution build."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CANONICAL_SPLIT_REGISTRY_PATH = Path("data/manifests/CAB_CANONICAL_SPLIT_REGISTRY.json")

ROLE_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "role": "dev_fixture",
        "source": "data/sample/instances.jsonl",
        "evidence_class": "FIXTURE_ONLY",
        "release_tier": "development_release",
        "human_validation_required": False,
    },
    {
        "role": "compact20_pilot",
        "source": "data/compact20_reviewed/compact20_reviewed_manifest.json",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "release_tier": "harness_only_release",
        "human_validation_required": True,
    },
    {
        "role": "scale100_confirmatory",
        "source": "data/processed/scale100_confirmatory_v1_candidate/pilot_instances.jsonl",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "release_tier": "hidden_or_delayed_test_pack",
        "human_validation_required": True,
    },
    {
        "role": "naturalistic_transfer",
        "source": "data/processed/naturalistic_transfer_v1_candidate/pilot_instances.jsonl",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "release_tier": "hidden_or_delayed_test_pack",
        "human_validation_required": True,
    },
    {
        "role": "main500_confirmatory",
        "source": "data/processed/main500_confirmatory_v1_candidate/pilot_instances.jsonl",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "release_tier": "hidden_or_delayed_test_pack",
        "human_validation_required": True,
    },
    {
        "role": "heldout_challenge",
        "source": "data/processed/main500_confirmatory_v1_candidate/heldout_instances.jsonl",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "release_tier": "hidden_or_delayed_test_pack",
        "post_study_release_tier": "post_study_full_release",
        "human_validation_required": True,
    },
)


def build_canonical_split_registry(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    roles: list[dict[str, Any]] = []
    memberships: dict[str, set[str]] = {}

    for definition in ROLE_SOURCES:
        source = root / definition["source"]
        if definition["role"] == "compact20_pilot":
            instance_ids, base_task_ids = _compact20_members(source)
        else:
            instance_ids, base_task_ids = _jsonl_members(source)
        memberships[definition["role"]] = base_task_ids
        profile = _dataset_profile(source) if source.suffix == ".jsonl" else {}
        roles.append(
            {
                **definition,
                "source_exists": source.exists(),
                "source_sha256": _sha256_file(source) if source.exists() else None,
                "membership_sha256": _sha256_values(instance_ids),
                "base_task_membership_sha256": _sha256_values(base_task_ids),
                "instance_count": len(instance_ids),
                "unique_base_task_count": len(base_task_ids),
                "candidate_count": (
                    _compact20_candidate_count(source)
                    if definition["role"] == "compact20_pilot"
                    else None
                ),
                "status": (
                    "FIXTURE_READY"
                    if definition["role"] == "dev_fixture" and instance_ids
                    else "HUMAN_REVIEW_PENDING"
                    if instance_ids
                    else "MATERIALIZATION_PENDING"
                ),
                "dataset_profile": profile,
                "scientific_execution_allowed": False,
                "paper_eligible": False,
            }
        )

    overlaps: list[dict[str, Any]] = []
    role_names = [row["role"] for row in roles]
    for index, left in enumerate(role_names):
        for right in role_names[index + 1 :]:
            shared = sorted(memberships[left] & memberships[right])
            if shared:
                overlaps.append(
                    {
                        "role_a": left,
                        "role_b": right,
                        "shared_base_task_count": len(shared),
                        "sample_base_task_ids": shared[:10],
                        "severity": "blocker",
                    }
                )

    return {
        "schema_version": "cab_canonical_split_registry_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "PRE_EXECUTION_STATIC_REGISTRY",
        "immutability": (
            "Membership and source hashes must be regenerated and reviewed before any "
            "result-affecting task change. A changed hash creates a new benchmark version."
        ),
        "role_count": len(roles),
        "roles": roles,
        "cross_role_overlaps": overlaps,
        "cross_role_overlap_count": len(overlaps),
        "passed": all(row["source_exists"] for row in roles) and not overlaps,
        "paper_eligible": False,
        "scientific_execution_allowed": False,
    }


def write_canonical_split_registry(
    repo_root: str | Path,
    *,
    output_path: str | Path = CANONICAL_SPLIT_REGISTRY_PATH,
) -> tuple[Path, dict[str, Any]]:
    root = Path(repo_root).resolve()
    payload = build_canonical_split_registry(root)
    output = Path(output_path)
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output, payload


def validate_canonical_split_registry(
    repo_root: str | Path,
    *,
    registry_path: str | Path = CANONICAL_SPLIT_REGISTRY_PATH,
) -> list[str]:
    root = Path(repo_root).resolve()
    path = Path(registry_path)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        return [f"missing canonical split registry: {path}"]
    try:
        recorded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"invalid JSON in canonical split registry: {path}"]
    current = build_canonical_split_registry(root)
    issues: list[str] = []
    recorded_roles = {
        row.get("role"): row
        for row in recorded.get("roles", [])
        if isinstance(row, dict) and row.get("role")
    }
    for row in current["roles"]:
        prior = recorded_roles.get(row["role"])
        if prior is None:
            issues.append(f"missing role in registry: {row['role']}")
            continue
        for field in (
            "source",
            "source_sha256",
            "membership_sha256",
            "base_task_membership_sha256",
            "instance_count",
            "unique_base_task_count",
        ):
            if prior.get(field) != row.get(field):
                issues.append(
                    f"{row['role']}: recorded {field} does not match live source"
                )
    if current["cross_role_overlaps"]:
        issues.append(
            f"incompatible role overlap: {len(current['cross_role_overlaps'])} pair(s)"
        )
    return issues


def _compact20_members(path: Path) -> tuple[set[str], set[str]]:
    if not path.exists():
        return set(), set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set(), set()
    rows = payload.get("candidates", []) if isinstance(payload, dict) else []
    instance_ids: set[str] = set()
    base_task_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        base = str(row.get("base_task_id", "")).strip()
        if base:
            base_task_ids.add(base)
        for key in ("clean_instance_id", "intervention_instance_id"):
            value = str(row.get(key, "")).strip()
            if value:
                instance_ids.add(value)
    return instance_ids, base_task_ids


def _compact20_candidate_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    rows = payload.get("candidates", []) if isinstance(payload, dict) else []
    return sum(1 for row in rows if isinstance(row, dict) and row.get("candidate_id"))


def _jsonl_members(path: Path) -> tuple[set[str], set[str]]:
    instance_ids: set[str] = set()
    base_task_ids: set[str] = set()
    for row in _read_jsonl(path):
        instance_id = str(row.get("instance_id", "")).strip()
        if instance_id:
            instance_ids.add(instance_id)
        base_payload = row.get("base_task")
        base_task_id = ""
        if isinstance(base_payload, dict):
            base_task_id = str(base_payload.get("task_id", "")).strip()
        if not base_task_id:
            base_task_id = str(row.get("base_task_id", "")).strip()
        if not base_task_id and instance_id:
            base_task_id = instance_id.rsplit(".", 1)[0]
        if base_task_id:
            base_task_ids.add(base_task_id)
    return instance_ids, base_task_ids


def _dataset_profile(path: Path) -> dict[str, Any]:
    rows = _read_jsonl(path)
    base_tasks: dict[str, dict[str, Any]] = {}
    families: Counter[str] = Counter()
    conditions: Counter[str] = Counter()
    for row in rows:
        base = row.get("base_task")
        if isinstance(base, dict):
            task_id = str(base.get("task_id", ""))
            if task_id:
                base_tasks[task_id] = base
        condition = str(row.get("condition", "unknown"))
        conditions[condition] += 1
        intervention = row.get("intervention")
        if isinstance(intervention, dict) and intervention.get("family"):
            families[str(intervention["family"])] += 1

    domains = Counter(str(row.get("domain", "unknown")) for row in base_tasks.values())
    difficulty = Counter(str(row.get("difficulty", "unknown")) for row in base_tasks.values())
    tool_combinations = {
        tuple(sorted(str(tool) for tool in row.get("available_tools", [])))
        for row in base_tasks.values()
    }
    answer_types = Counter(
        _answer_type((row.get("goal") or {}).get("expected_final_answer"))
        for row in base_tasks.values()
    )
    normalized_patterns = {
        _normalize_instruction(
            str(row.get("user_instruction") or (row.get("goal") or {}).get("user_instruction") or "")
        )
        for row in base_tasks.values()
    }
    template_ids = {
        (
            str(row.get("domain", "unknown")),
            str((row.get("metadata") or {}).get("template_domain", "unknown")),
        )
        for row in base_tasks.values()
    }
    naturalistic_count = sum(
        1
        for row in base_tasks.values()
        if (row.get("metadata") or {}).get("task_style") == "naturalistic"
    )
    return {
        "raw_instance_count": len(rows),
        "unique_base_task_count": len(base_tasks),
        "unique_template_family_count": len(template_ids),
        "normalized_instruction_pattern_count": len(normalized_patterns),
        "domain_counts": dict(sorted(domains.items())),
        "difficulty_counts": dict(sorted(difficulty.items())),
        "tool_combination_count": len(tool_combinations),
        "answer_type_counts": dict(sorted(answer_types.items())),
        "condition_counts": dict(sorted(conditions.items())),
        "intervention_family_counts": dict(sorted(families.items())),
        "naturalistic_task_count": naturalistic_count,
        "naturalistic_share": (
            round(naturalistic_count / len(base_tasks), 6) if base_tasks else 0.0
        ),
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
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
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _answer_type(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "list"
    return "string"


def _normalize_instruction(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"\b\d+(?:\.\d+)?\b", "<num>", lowered)
    lowered = re.sub(r"synthetic variant <num>\.?", "", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_values(values: set[str]) -> str:
    serialized = "\n".join(sorted(values)).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()
