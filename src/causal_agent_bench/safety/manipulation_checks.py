"""Deterministic manipulation checks and intervention-to-check linkage.

These checks verify that a declared intervention marker is present in a
serialized benchmark instance. They are engineering evidence only: a passing
marker does not replace independent human judgments about isolation, realism,
goal preservation, or solvability.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.hashing import stable_hash

CHECK_VERSION = "cab_manipulation_checks_v1"

INTERVENTION_CHECK_LINKAGE: dict[str, str] = {
    "tool_removal": "tool_absent",
    "tool_failure": "tool_failure_injected",
    "tool_corruption": "tool_corruption_injected",
    "irrelevant_tools": "distractor_presence",
    "memory_corruption": "memory_corruption",
    "observation_conflict": "conflicting_observations",
    "ambiguous_instruction": "instruction_ambiguity",
    "long_horizon_dependency": "dependency_marker",
    "premature_success_signal": "premature_success_signal",
    "distractor_evidence": "distractor_presence",
    "web_broken_link": "tool_failure_injected",
    "web_stale_page": "stale_timestamp_threshold",
    "web_conflicting_page": "conflicting_observations",
    "web_irrelevant_search_result": "distractor_presence",
    "web_hidden_evidence": "missing_evidence",
}

REQUIRED_DETERMINISTIC_CHECKS = frozenset(
    {
        "tool_absent",
        "tool_failure_injected",
        "stale_timestamp_threshold",
        "conflicting_observations",
        "premature_success_signal",
        "missing_evidence",
        "distractor_presence",
        "memory_corruption",
    }
)

CheckFunction = Callable[[dict[str, Any]], tuple[bool | None, str, dict[str, Any]]]


def evaluate_manipulation_check(
    instance: dict[str, Any],
    *,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    """Evaluate the registered deterministic check for one intervention."""

    intervention = _mapping(instance.get("intervention"))
    family = str(intervention.get("family") or "").strip()
    check_name = INTERVENTION_CHECK_LINKAGE.get(family)
    instance_id = str(instance.get("instance_id") or "").strip()
    linkage_id = stable_hash(
        {
            "version": CHECK_VERSION,
            "candidate_id": candidate_id,
            "instance_id": instance_id,
            "family": family,
            "check": check_name,
        },
        length=24,
    )
    if not family:
        return _check_result(
            linkage_id=linkage_id,
            candidate_id=candidate_id,
            instance_id=instance_id,
            family=family,
            check_name=None,
            passed=None,
            reason_code="MISSING_INTERVENTION_FAMILY",
            diagnostics={},
        )
    if check_name is None:
        return _check_result(
            linkage_id=linkage_id,
            candidate_id=candidate_id,
            instance_id=instance_id,
            family=family,
            check_name=None,
            passed=None,
            reason_code="UNREGISTERED_INTERVENTION_FAMILY",
            diagnostics={},
        )
    function = _CHECK_FUNCTIONS[check_name]
    passed, reason_code, diagnostics = function(instance)
    return _check_result(
        linkage_id=linkage_id,
        candidate_id=candidate_id,
        instance_id=instance_id,
        family=family,
        check_name=check_name,
        passed=passed,
        reason_code=reason_code,
        diagnostics=diagnostics,
    )


def build_manipulation_check_report(
    candidate_manifest_path: str | Path,
    instances_path: str | Path,
) -> dict[str, Any]:
    """Build a deterministic, candidate-linked manipulation-check report."""

    manifest_path = Path(candidate_manifest_path)
    source_path = Path(instances_path)
    manifest = _read_json_object(manifest_path)
    candidates = manifest.get("candidates")
    candidate_rows = candidates if isinstance(candidates, list) else []
    instances = _read_jsonl(source_path)
    by_instance = {
        str(row.get("instance_id") or ""): row
        for row in instances
        if str(row.get("instance_id") or "")
    }
    records: list[dict[str, Any]] = []
    for raw_candidate in sorted(
        (row for row in candidate_rows if isinstance(row, dict)),
        key=lambda row: str(row.get("candidate_id") or ""),
    ):
        candidate_id = str(raw_candidate.get("candidate_id") or "").strip()
        instance_id = str(
            raw_candidate.get("intervention_instance_id") or ""
        ).strip()
        instance = by_instance.get(instance_id)
        if instance is None:
            records.append(
                _check_result(
                    linkage_id=stable_hash(
                        {
                            "version": CHECK_VERSION,
                            "candidate_id": candidate_id,
                            "instance_id": instance_id,
                            "check": "missing_instance",
                        },
                        length=24,
                    ),
                    candidate_id=candidate_id,
                    instance_id=instance_id,
                    family=str(raw_candidate.get("family") or ""),
                    check_name=INTERVENTION_CHECK_LINKAGE.get(
                        str(raw_candidate.get("family") or "")
                    ),
                    passed=None,
                    reason_code="INTERVENTION_INSTANCE_NOT_FOUND",
                    diagnostics={},
                )
            )
            continue
        records.append(
            evaluate_manipulation_check(
                instance,
                candidate_id=candidate_id,
            )
        )
    passed_count = sum(record["status"] == "PASS" for record in records)
    failed_count = sum(record["status"] == "FAIL" for record in records)
    blocked_count = sum(record["status"] == "BLOCKED" for record in records)
    all_linked = bool(records) and all(record["check_name"] for record in records)
    all_passed = bool(records) and all(record["status"] == "PASS" for record in records)
    return {
        "schema_version": CHECK_VERSION,
        "evidence_class": "ENGINEERING_ONLY",
        "scope": (
            "Deterministic marker presence only; does not establish causal "
            "isolation or replace human review."
        ),
        "candidate_manifest": _portable_path(manifest_path),
        "candidate_manifest_sha256": _sha256_file(manifest_path),
        "instances_path": _portable_path(source_path),
        "instances_sha256": _sha256_file(source_path),
        "linkage_registry": dict(sorted(INTERVENTION_CHECK_LINKAGE.items())),
        "required_check_kinds_present": sorted(
            REQUIRED_DETERMINISTIC_CHECKS
            & set(INTERVENTION_CHECK_LINKAGE.values())
        ),
        "candidate_count": len(candidate_rows),
        "record_count": len(records),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "blocked_count": blocked_count,
        "all_candidates_linked": all_linked,
        "all_applicable_checks_passed": all_passed,
        "records": records,
    }


def write_manipulation_check_report(
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _check_result(
    *,
    linkage_id: str,
    candidate_id: str | None,
    instance_id: str,
    family: str,
    check_name: str | None,
    passed: bool | None,
    reason_code: str,
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    status = "PASS" if passed is True else "FAIL" if passed is False else "BLOCKED"
    return {
        "linkage_id": linkage_id,
        "candidate_id": candidate_id,
        "instance_id": instance_id,
        "intervention_family": family,
        "check_name": check_name,
        "deterministic": True,
        "status": status,
        "passed": passed,
        "reason_code": reason_code,
        "diagnostics": diagnostics,
        "evidence_class": "ENGINEERING_ONLY",
    }


def _tool_absent(instance: dict[str, Any]) -> tuple[bool | None, str, dict[str, Any]]:
    intervention = _mapping(instance.get("intervention"))
    patch = _mapping(intervention.get("tool_availability_patch"))
    removed = _string_list(patch.get("removed_tools"))
    available = set(_string_list(instance.get("available_tools")))
    if not removed:
        return None, "REMOVED_TOOLS_MARKER_MISSING", {}
    still_available = sorted(set(removed) & available)
    return (
        not still_available,
        "REMOVED_TOOLS_ABSENT" if not still_available else "REMOVED_TOOL_STILL_AVAILABLE",
        {"removed_tool_count": len(removed), "still_available": still_available},
    )


def _tool_failure_injected(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    patch = _tool_output_patch(instance)
    target = str(patch.get("target_tool") or "").strip()
    failure_marker = patch.get("error") or patch.get("failure") or patch.get("broken_link")
    if not target or not _present(failure_marker):
        return None, "FAILURE_MARKER_MISSING", {"target_tool_present": bool(target)}
    return True, "DETERMINISTIC_FAILURE_MARKER_PRESENT", {"target_tool": target}


def _tool_corruption_injected(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    patch = _tool_output_patch(instance)
    target = str(patch.get("target_tool") or "").strip()
    corruption = (
        patch.get("overrides")
        or patch.get("corruption")
        or patch.get("incorrect_output")
    )
    if not target or not isinstance(corruption, dict) or not corruption:
        return None, "CORRUPTION_MARKER_MISSING", {"target_tool_present": bool(target)}
    return True, "DETERMINISTIC_CORRUPTION_MARKER_PRESENT", {"target_tool": target}


def _stale_timestamp_threshold(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    patch = _tool_output_patch(instance)
    metadata = _mapping(_mapping(instance.get("intervention")).get("metadata"))
    source_raw = (
        patch.get("source_timestamp")
        or patch.get("content_timestamp")
        or patch.get("stale_timestamp")
    )
    reference_raw = (
        patch.get("reference_timestamp")
        or metadata.get("reference_timestamp")
        or metadata.get("evaluation_timestamp")
    )
    threshold_raw = (
        patch.get("staleness_threshold_days")
        or metadata.get("staleness_threshold_days")
    )
    try:
        threshold_days = float(str(threshold_raw))
        source = _parse_datetime(source_raw)
        reference = _parse_datetime(reference_raw)
    except (TypeError, ValueError):
        return None, "STALE_TIMESTAMP_INPUT_MISSING_OR_INVALID", {}
    age_days = (reference - source).total_seconds() / 86_400
    passed = threshold_days >= 0 and age_days > threshold_days
    return (
        passed,
        "STALE_THRESHOLD_EXCEEDED" if passed else "STALE_THRESHOLD_NOT_EXCEEDED",
        {
            "age_days": round(age_days, 6),
            "threshold_days": threshold_days,
        },
    )


def _conflicting_observations(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    patch = _tool_output_patch(instance)
    conflict = (
        patch.get("conflicting_observation")
        or patch.get("conflicting_observations")
        or patch.get("conflict")
    )
    if not isinstance(conflict, dict) or len(conflict) < 2:
        return None, "CONFLICT_MARKER_MISSING", {}
    values = {
        json.dumps(value, sort_keys=True, default=str)
        for value in conflict.values()
    }
    passed = len(values) > 1
    return (
        passed,
        "DISTINCT_CONFLICTING_VALUES_PRESENT"
        if passed
        else "CONFLICT_VALUES_IDENTICAL",
        {"source_count": len(conflict), "distinct_value_count": len(values)},
    )


def _premature_success_signal(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    patch = _tool_output_patch(instance)
    signal = (
        patch.get("premature_completion_message")
        or patch.get("premature_success_signal")
        or patch.get("success_signal")
    )
    if not isinstance(signal, str) or not signal.strip():
        return None, "PREMATURE_SUCCESS_MARKER_MISSING", {}
    return True, "PREMATURE_SUCCESS_MARKER_PRESENT", {}


def _missing_evidence(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    patch = _tool_output_patch(instance)
    marker_keys = {
        "hidden_evidence",
        "missing_evidence",
        "removed_evidence",
        "evidence_omitted",
    }
    found = sorted(key for key in marker_keys if _present(patch.get(key)))
    if not found:
        return None, "MISSING_EVIDENCE_MARKER_ABSENT", {}
    return True, "MISSING_EVIDENCE_MARKER_PRESENT", {"marker_keys": found}


def _distractor_presence(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    intervention = _mapping(instance.get("intervention"))
    tool_patch = _mapping(intervention.get("tool_availability_patch"))
    output_patch = _tool_output_patch(instance)
    added_tools = _string_list(tool_patch.get("added_tools"))
    marker_keys = sorted(
        key
        for key in (
            "distractor_record",
            "irrelevant_result",
            "irrelevant_search_result",
        )
        if _present(output_patch.get(key))
    )
    if not added_tools and not marker_keys:
        return None, "DISTRACTOR_MARKER_MISSING", {}
    return True, "DISTRACTOR_MARKER_PRESENT", {
        "added_tool_count": len(added_tools),
        "marker_keys": marker_keys,
    }


def _memory_corruption(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    intervention = _mapping(instance.get("intervention"))
    patch = _mapping(intervention.get("memory_patch"))
    initial = _mapping(instance.get("initial_memory"))
    combined = {**patch, **initial}
    marker_keys = sorted(
        key
        for key, value in combined.items()
        if _present(value)
        and any(token in key.lower() for token in ("corrupt", "stale", "outdated"))
    )
    if not marker_keys:
        return None, "MEMORY_CORRUPTION_MARKER_MISSING", {}
    return True, "MEMORY_CORRUPTION_MARKER_PRESENT", {"marker_keys": marker_keys}


def _instruction_ambiguity(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    intervention = _mapping(instance.get("intervention"))
    patch = intervention.get("instruction_patch")
    if not isinstance(patch, str) or not patch.strip():
        return None, "INSTRUCTION_AMBIGUITY_MARKER_MISSING", {}
    return True, "INSTRUCTION_AMBIGUITY_MARKER_PRESENT", {}


def _dependency_marker(
    instance: dict[str, Any],
) -> tuple[bool | None, str, dict[str, Any]]:
    patch = _tool_output_patch(instance)
    marker = patch.get("dependency_marker") or patch.get("dependency")
    if not _present(marker):
        return None, "DEPENDENCY_MARKER_MISSING", {}
    return True, "DEPENDENCY_MARKER_PRESENT", {}


_CHECK_FUNCTIONS: dict[str, CheckFunction] = {
    "tool_absent": _tool_absent,
    "tool_failure_injected": _tool_failure_injected,
    "tool_corruption_injected": _tool_corruption_injected,
    "stale_timestamp_threshold": _stale_timestamp_threshold,
    "conflicting_observations": _conflicting_observations,
    "premature_success_signal": _premature_success_signal,
    "missing_evidence": _missing_evidence,
    "distractor_presence": _distractor_presence,
    "memory_corruption": _memory_corruption,
    "instruction_ambiguity": _instruction_ambiguity,
    "dependency_marker": _dependency_marker,
}


def _tool_output_patch(instance: dict[str, Any]) -> dict[str, Any]:
    intervention = _mapping(instance.get("intervention"))
    direct = _mapping(intervention.get("tool_output_patch"))
    if direct:
        return direct
    details = _mapping(intervention.get("patch_details"))
    return _mapping(details.get("tool_output_patch"))


def _parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp is missing")
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _present(value: Any) -> bool:
    return value is not None and value is not False and value != ""


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)
