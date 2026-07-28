"""Permanent contamination handling for protected held-out material.

The public repository may retain already-exposed data for transparent
development and audit use, but those rows are permanently ineligible for
confirmatory or paper-eligible evaluation.  Replacement payloads live under an
ignored private root; Git contains only a non-reversible public commitment
manifest.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
import subprocess
import tarfile
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

PUBLIC_MANIFEST_PATH = Path("data/manifests/heldout_challenge_v2_public_manifest.json")
CONTAMINATION_REGISTRY_PATH = Path("data/manifests/CAB_PUBLIC_CONTAMINATION_REGISTRY.json")
PRIVATE_ROOT = Path("private_data/heldout_challenge_v2")
PRIVATE_LOCK_PATH = PRIVATE_ROOT / "private_lock.json"

PERMANENT_DISPOSITIONS = frozenset(
    {
        "PUBLIC_DEVELOPMENT_ONLY",
        "PILOT_ONLY",
        "CONTAMINATED_NOT_CONFIRMATORY",
        "INVALID_FOR_FUTURE_EVALUATION",
    }
)
FORBIDDEN_PUBLIC_MANIFEST_FIELDS = frozenset(
    {
        "answer",
        "answers",
        "base_tasks",
        "expected_final_answer",
        "gold_answer",
        "hidden_ground_truth",
        "instance_ids",
        "instances",
        "intervention_payload",
        "intervention_payloads",
        "interventions",
        "private_key",
        "private_seed",
        "prompt",
        "prompts",
        "seed",
        "seed_hex",
        "task_ids",
        "task_text",
        "tasks",
        "user_instruction",
    }
)
REQUIRED_COMMITMENTS = frozenset(
    {
        "seed_hmac_sha256",
        "id_namespace_hmac_sha256",
        "base_task_membership_hmac_sha256",
        "instance_membership_hmac_sha256",
    }
)
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_ARCHIVE_SUFFIXES = (
    ".zip",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".gz",
    ".7z",
    ".rar",
)


def validate_protected_heldout_architecture(
    repo_root: str | Path,
    *,
    public_manifest_path: str | Path = PUBLIC_MANIFEST_PATH,
    contamination_registry_path: str | Path = CONTAMINATION_REGISTRY_PATH,
    split_registry_path: str | Path = ("data/manifests/CAB_CANONICAL_SPLIT_REGISTRY.json"),
    private_root: str | Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    """Validate public commitments, permanent invalidation, and private boundary."""

    root = Path(repo_root).resolve()
    manifest_file = _resolve(root, public_manifest_path)
    contamination_file = _resolve(root, contamination_registry_path)
    split_file = _resolve(root, split_registry_path)
    private_dir = _resolve(root, private_root)
    issues: list[dict[str, Any]] = []

    manifest = _load_json(manifest_file, issues, "public_manifest_invalid")
    contamination = _load_json(
        contamination_file,
        issues,
        "contamination_registry_invalid",
    )
    split_registry = _load_json(split_file, issues, "split_registry_invalid")

    issues.extend(
        validate_public_manifest_payload(
            manifest,
            path=_relative(manifest_file, root),
        )
    )
    issues.extend(
        validate_contamination_registry_payload(
            contamination,
            path=_relative(contamination_file, root),
        )
    )
    issues.extend(
        _validate_split_role_dispositions(
            split_registry,
            contamination,
            manifest_path=_relative(manifest_file, root),
            path=_relative(split_file, root),
        )
    )

    ignore_probe = private_dir / "protected_tasks.jsonl"
    private_root_ignored = _git_check_ignored(root, ignore_probe)
    if not private_root_ignored:
        issues.append(
            _issue(
                "private_payload_path_not_ignored",
                _relative(ignore_probe, root),
                "gitignore",
                "Private held-out payload paths must be ignored before materialization.",
            )
        )

    tracked_private = sorted(
        path
        for path in _git_ls_files(root)
        if path == _relative(private_dir, root)
        or path.startswith(f"{_relative(private_dir, root)}/")
    )
    for path in tracked_private:
        issues.append(
            _issue(
                "private_payload_git_tracked",
                path,
                "git_index",
                "Private held-out files must never enter the public Git index.",
            )
        )

    exposed_ids, exposed_namespaces, public_texts = _exposed_material(
        root,
        contamination,
    )
    private_ids, private_texts, private_payload_materialized = _private_material(private_dir)
    reused_ids = find_exposed_id_reuse(
        exposed_ids,
        exposed_namespaces,
        private_ids,
    )
    for value in reused_ids:
        issues.append(
            _issue(
                "exposed_id_reused",
                _relative(private_dir, root),
                "private_identifiers",
                f"Private replacement reuses an exposed identifier or namespace: {value}",
            )
        )

    overlaps = find_text_overlaps(public_texts, private_texts)
    for overlap in overlaps[:25]:
        issues.append(
            _issue(
                "public_private_task_overlap",
                _relative(private_dir, root),
                "private_payload",
                (
                    "Private replacement has exact or near-duplicate public text "
                    f"(similarity={overlap['similarity']:.3f})."
                ),
            )
        )

    marker_values = {
        *private_ids,
        _relative(private_dir, root),
    }
    embedded_paths: list[str] = []
    if marker_values:
        for tracked_path in sorted(_git_ls_files(root)):
            suffix = tracked_path.lower()
            if not (suffix.endswith(".ipynb") or suffix.endswith(_ARCHIVE_SUFFIXES)):
                continue
            candidate = root / tracked_path
            if scan_artifact_for_markers(candidate, marker_values):
                embedded_paths.append(tracked_path)
                issues.append(
                    _issue(
                        "protected_content_embedded_in_container",
                        tracked_path,
                        "content",
                        "A tracked notebook or archive embeds private identifiers/content.",
                    )
                )

    blockers = [issue for issue in issues if issue["severity"] in {"blocker", "error"}]
    return {
        "schema_version": "cab_protected_heldout_architecture_audit_v1",
        "scope": (
            "Static contamination, public-manifest, private-path, identifier, "
            "overlap, notebook, and archive checks. No model execution."
        ),
        "evidence_class": "ENGINEERING_ONLY",
        "public_manifest_path": _relative(manifest_file, root),
        "contamination_registry_path": _relative(contamination_file, root),
        "private_root": _relative(private_dir, root),
        "private_root_ignored": private_root_ignored,
        "tracked_private_file_count": len(tracked_private),
        "permanently_contaminated_record_count": len(contamination.get("records", []))
        if isinstance(contamination.get("records"), list)
        else 0,
        "exposed_identifier_count": len(exposed_ids),
        "exposed_namespace_count": len(exposed_namespaces),
        "private_identifier_count": len(private_ids),
        "private_payload_materialized": private_payload_materialized,
        "reused_identifier_count": len(reused_ids),
        "public_private_overlap_count": len(overlaps),
        "embedded_notebook_or_archive_count": len(embedded_paths),
        "passed": not blockers,
        "issues": issues,
    }


def validate_public_manifest_payload(
    payload: Mapping[str, Any],
    *,
    path: str = str(PUBLIC_MANIFEST_PATH),
) -> list[dict[str, Any]]:
    """Validate that a public manifest contains commitments, never payloads."""

    issues: list[dict[str, Any]] = []
    if payload.get("schema_version") != "cab_protected_heldout_public_manifest_v2":
        issues.append(
            _issue(
                "public_manifest_schema_invalid",
                path,
                "schema_version",
                "Expected cab_protected_heldout_public_manifest_v2.",
            )
        )
    if payload.get("split_version") != "heldout_challenge_v2":
        issues.append(
            _issue(
                "public_manifest_split_version_invalid",
                path,
                "split_version",
                "Replacement split must use heldout_challenge_v2.",
            )
        )
    if payload.get("public_metadata_only") is not True:
        issues.append(
            _issue(
                "public_manifest_not_metadata_only",
                path,
                "public_metadata_only",
                "Public manifest must explicitly be metadata-only.",
            )
        )
    if payload.get("scientific_execution_allowed") is not False:
        issues.append(
            _issue(
                "public_manifest_execution_unlocked",
                path,
                "scientific_execution_allowed",
                "Public commitments cannot unlock scientific execution.",
            )
        )
    if payload.get("paper_eligible") is not False:
        issues.append(
            _issue(
                "public_manifest_paper_eligible",
                path,
                "paper_eligible",
                "A pre-execution public manifest cannot be paper-eligible.",
            )
        )

    for key, value in _walk_mapping(payload):
        if key.lower() in FORBIDDEN_PUBLIC_MANIFEST_FIELDS:
            issues.append(
                _issue(
                    "public_manifest_forbidden_field",
                    path,
                    key,
                    f"Forbidden payload-bearing public field: {key}",
                )
            )
        if isinstance(value, str) and _looks_like_reversible_encoding(value):
            issues.append(
                _issue(
                    "public_manifest_reversible_encoding",
                    path,
                    key,
                    "Long base64-like values are forbidden in the public manifest.",
                )
            )

    commitments = payload.get("commitments")
    if not isinstance(commitments, Mapping):
        issues.append(
            _issue(
                "public_manifest_commitments_missing",
                path,
                "commitments",
                "Non-reversible commitments are required.",
            )
        )
    else:
        if commitments.get("algorithm") != "HMAC-SHA256_WITH_PRIVATE_KEY":
            issues.append(
                _issue(
                    "public_manifest_commitment_algorithm_invalid",
                    path,
                    "commitments.algorithm",
                    "Commitments must use a private-key HMAC, not a reversible seed hash.",
                )
            )
        for field in sorted(REQUIRED_COMMITMENTS):
            if not _HEX_64.fullmatch(str(commitments.get(field, ""))):
                issues.append(
                    _issue(
                        "public_manifest_commitment_invalid",
                        path,
                        f"commitments.{field}",
                        "Expected a 64-character lowercase HMAC-SHA256 commitment.",
                    )
                )

    counts = payload.get("aggregate_counts")
    if not isinstance(counts, Mapping):
        issues.append(
            _issue(
                "public_manifest_aggregate_counts_missing",
                path,
                "aggregate_counts",
                "Aggregate target counts are required.",
            )
        )
    else:
        for field in ("target_base_task_count", "target_instance_count"):
            value = counts.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                issues.append(
                    _issue(
                        "public_manifest_aggregate_count_invalid",
                        path,
                        f"aggregate_counts.{field}",
                        "Target counts must be positive integers.",
                    )
                )
    return _dedupe_issues(issues)


def validate_contamination_registry_payload(
    payload: Mapping[str, Any],
    *,
    path: str = str(CONTAMINATION_REGISTRY_PATH),
) -> list[dict[str, Any]]:
    """Validate permanent, fail-closed scientific dispositions."""

    issues: list[dict[str, Any]] = []
    if payload.get("schema_version") != "cab_public_contamination_registry_v1":
        issues.append(
            _issue(
                "contamination_registry_schema_invalid",
                path,
                "schema_version",
                "Expected cab_public_contamination_registry_v1.",
            )
        )
    policy = payload.get("policy")
    if not isinstance(policy, Mapping) or any(
        policy.get(field) is not expected
        for field, expected in {
            "deletion_restores_secrecy": False,
            "history_rewrite_restores_scientific_eligibility": False,
            "paper_eligible_evidence_allowed": False,
            "public_exposure_is_permanent": True,
        }.items()
    ):
        issues.append(
            _issue(
                "contamination_registry_policy_not_permanent",
                path,
                "policy",
                "Exposure must remain permanently ineligible even after deletion/rewrite.",
            )
        )

    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return [
            *issues,
            _issue(
                "contamination_registry_records_missing",
                path,
                "records",
                "At least one explicit public-exposure record is required.",
            ),
        ]

    seen: set[str] = set()
    for index, record in enumerate(records):
        field = f"records[{index}]"
        if not isinstance(record, Mapping):
            issues.append(
                _issue(
                    "contamination_registry_record_invalid",
                    path,
                    field,
                    "Every contamination record must be an object.",
                )
            )
            continue
        record_id = str(record.get("record_id", ""))
        if not record_id or record_id in seen:
            issues.append(
                _issue(
                    "contamination_registry_record_id_invalid",
                    path,
                    f"{field}.record_id",
                    "Record IDs must be non-empty and unique.",
                )
            )
        seen.add(record_id)
        disposition = record.get("scientific_disposition")
        if disposition not in PERMANENT_DISPOSITIONS:
            issues.append(
                _issue(
                    "contamination_disposition_invalid",
                    path,
                    f"{field}.scientific_disposition",
                    f"Unknown permanent disposition: {disposition!r}",
                )
            )
        for boolean_field in (
            "confirmatory_eligible",
            "paper_eligible",
            "external_validity_eligible",
        ):
            if record.get(boolean_field) is not False:
                issues.append(
                    _issue(
                        "contaminated_record_eligibility_unlocked",
                        path,
                        f"{field}.{boolean_field}",
                        "Publicly exposed records must remain ineligible.",
                    )
                )
        if not re.fullmatch(r"[0-9a-f]{40}", str(record.get("exposure_commit", ""))):
            issues.append(
                _issue(
                    "contamination_exposure_commit_invalid",
                    path,
                    f"{field}.exposure_commit",
                    "A full 40-character exposure commit is required.",
                )
            )
        prefixes = record.get("path_prefixes")
        if not isinstance(prefixes, list) or not prefixes:
            issues.append(
                _issue(
                    "contamination_path_prefix_missing",
                    path,
                    f"{field}.path_prefixes",
                    "Each exposure requires one or more public path prefixes.",
                )
            )
        if not _HEX_64.fullmatch(str(record.get("canonical_source_sha256_at_exposure", ""))):
            issues.append(
                _issue(
                    "contamination_source_commitment_invalid",
                    path,
                    f"{field}.canonical_source_sha256_at_exposure",
                    "A SHA-256 commitment to the exposed source is required.",
                )
            )
    return _dedupe_issues(issues)


def path_is_registered_contamination(
    path: str,
    contamination_registry: Mapping[str, Any],
) -> bool:
    """Whether a public legacy payload path has an explicit disposition."""

    records = contamination_registry.get("records", [])
    if not isinstance(records, list):
        return False
    return any(
        isinstance(record, Mapping)
        and any(
            path.startswith(str(prefix))
            for prefix in record.get("path_prefixes", [])
            if isinstance(prefix, str)
        )
        for record in records
    )


def find_exposed_id_reuse(
    exposed_ids: Iterable[str],
    exposed_namespaces: Iterable[str],
    private_ids: Iterable[str],
) -> list[str]:
    """Return private identifiers that reuse an exposed ID or namespace."""

    exact = {value for value in exposed_ids if value}
    namespaces = {value for value in exposed_namespaces if value}
    reused: set[str] = set()
    for value in private_ids:
        if not value:
            continue
        if value in exact or any(
            value == namespace
            or value.startswith(
                (f"{namespace}__", f"{namespace}."),
            )
            for namespace in namespaces
        ):
            reused.add(value)
    return sorted(reused)


def find_text_overlaps(
    public_texts: Iterable[str],
    private_texts: Iterable[str],
    *,
    threshold: float = 0.85,
) -> list[dict[str, Any]]:
    """Find exact or token-Jaccard near duplicates without exposing text."""

    public_profiles = [
        (_normalize_text(text), _token_set(text)) for text in public_texts if _normalize_text(text)
    ]
    overlaps: list[dict[str, Any]] = []
    for private_index, private_text in enumerate(private_texts):
        normalized = _normalize_text(private_text)
        if not normalized:
            continue
        private_tokens = _token_set(private_text)
        best = 0.0
        exact = False
        for public_normalized, public_tokens in public_profiles:
            if normalized == public_normalized:
                best = 1.0
                exact = True
                break
            union = private_tokens | public_tokens
            similarity = len(private_tokens & public_tokens) / len(union) if union else 0.0
            best = max(best, similarity)
        if best >= threshold:
            overlaps.append(
                {
                    "private_index": private_index,
                    "similarity": best,
                    "exact": exact,
                }
            )
    return overlaps


def scan_artifact_for_markers(
    path: str | Path,
    markers: Iterable[str],
) -> bool:
    """Scan text, notebook, zip, or tar content for protected markers."""

    candidate = Path(path)
    marker_bytes = [value.encode("utf-8") for value in markers if isinstance(value, str) and value]
    if not marker_bytes or not candidate.is_file():
        return False
    lowered = candidate.name.lower()
    try:
        if lowered.endswith(".zip"):
            with zipfile.ZipFile(candidate) as archive:
                return any(
                    _bytes_contain(archive.read(name), marker_bytes)
                    for name in archive.namelist()
                    if not name.endswith("/")
                )
        if lowered.endswith((".tar", ".tar.gz", ".tgz")):
            with tarfile.open(candidate) as archive:
                for member in archive.getmembers():
                    if not member.isfile():
                        continue
                    handle = archive.extractfile(member)
                    if handle is not None and _bytes_contain(
                        handle.read(),
                        marker_bytes,
                    ):
                        return True
            return False
        return _bytes_contain(candidate.read_bytes(), marker_bytes)
    except (OSError, tarfile.TarError, zipfile.BadZipFile):
        return False


def _validate_split_role_dispositions(
    split_registry: Mapping[str, Any],
    contamination: Mapping[str, Any],
    *,
    manifest_path: str,
    path: str,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    records = {
        str(record.get("record_id")): record
        for record in contamination.get("records", [])
        if isinstance(record, Mapping) and record.get("record_id")
    }
    roles = split_registry.get("roles", [])
    if not isinstance(roles, list):
        return [
            _issue(
                "split_registry_roles_invalid",
                path,
                "roles",
                "Canonical split roles must be a list.",
            )
        ]

    required_protected_v2_sources = {
        "scale100_confirmatory_v2_protected": (
            "data/manifests/scale100_confirmatory_v2_public_manifest.json"
        ),
        "naturalistic_transfer_v2_protected": (
            "data/manifests/naturalistic_transfer_v2_public_manifest.json"
        ),
        "heldout_challenge_v2_protected": manifest_path,
    }
    protected_v2_seen: set[str] = set()
    for index, role in enumerate(roles):
        if not isinstance(role, Mapping):
            continue
        role_name = str(role.get("role", ""))
        contamination_id = role.get("contamination_record_id")
        if contamination_id:
            record = records.get(str(contamination_id))
            if record is None:
                issues.append(
                    _issue(
                        "split_role_contamination_record_missing",
                        path,
                        f"roles[{index}].contamination_record_id",
                        f"Unknown contamination record: {contamination_id}",
                    )
                )
                continue
            if role.get("scientific_disposition") != record.get("scientific_disposition"):
                issues.append(
                    _issue(
                        "split_role_contamination_disposition_mismatch",
                        path,
                        f"roles[{index}].scientific_disposition",
                        "Canonical role must inherit its permanent disposition.",
                    )
                )
            if "confirmatory" in role_name.lower() or (role_name == "heldout_challenge"):
                issues.append(
                    _issue(
                        "contaminated_role_mislabelled_confirmatory",
                        path,
                        f"roles[{index}].role",
                        f"Exposed role remains misleadingly named {role_name!r}.",
                    )
                )
            if role.get("release_tier") == "hidden_or_delayed_test_pack":
                issues.append(
                    _issue(
                        "contaminated_role_hidden_tier",
                        path,
                        f"roles[{index}].release_tier",
                        "Publicly exposed data cannot retain a hidden release tier.",
                    )
                )
            for field in (
                "confirmatory_eligible",
                "paper_eligible",
                "scientific_execution_allowed",
            ):
                if role.get(field) is not False:
                    issues.append(
                        _issue(
                            "contaminated_role_eligibility_unlocked",
                            path,
                            f"roles[{index}].{field}",
                            "Contaminated canonical roles must remain ineligible.",
                        )
                    )

        if role_name in required_protected_v2_sources:
            protected_v2_seen.add(role_name)
            expected_source = required_protected_v2_sources[role_name]
            if role.get("source") != expected_source:
                issues.append(
                    _issue(
                        "protected_v2_source_not_public_manifest",
                        path,
                        f"roles[{index}].source",
                        (
                            f"{role_name} must point only to its public commitment "
                            "manifest."
                        ),
                    )
                )
            if role.get("source_kind") != "public_commitment_manifest":
                issues.append(
                    _issue(
                        "protected_v2_source_kind_invalid",
                        path,
                        f"roles[{index}].source_kind",
                        "Protected v2 roles expose commitment manifests, never payloads.",
                    )
                )
            if role.get("release_tier") != "hidden_or_delayed_test_pack":
                issues.append(
                    _issue(
                        "protected_v2_release_tier_invalid",
                        path,
                        f"roles[{index}].release_tier",
                        "Protected v2 must remain hidden/delayed.",
                    )
                )
            if role.get("public_payload") is not False:
                issues.append(
                    _issue(
                        "protected_v2_public_payload_flag_invalid",
                        path,
                        f"roles[{index}].public_payload",
                        "Protected v2 public Git contains commitments only.",
                    )
                )
            if role.get("membership_visibility") != "PRIVATE_COMMITMENT_ONLY":
                issues.append(
                    _issue(
                        "protected_v2_membership_visibility_invalid",
                        path,
                        f"roles[{index}].membership_visibility",
                        "Protected v2 membership must remain commitment-only.",
                    )
                )
            for field in (
                "confirmatory_eligible",
                "paper_eligible",
                "scientific_execution_allowed",
            ):
                if role.get(field) is not False:
                    issues.append(
                        _issue(
                            "protected_v2_eligibility_unlocked",
                            path,
                            f"roles[{index}].{field}",
                            (
                                "Protected candidate roles require human review and "
                                "cannot yet support scientific execution."
                            ),
                        )
                    )
            if (
                role_name != "heldout_challenge_v2_protected"
                and role.get("status") != "HUMAN_INPUT_REQUIRED"
            ):
                issues.append(
                    _issue(
                        "protected_v2_human_review_status_invalid",
                        path,
                        f"roles[{index}].status",
                        "Scale100 and naturalistic v2 require unresolved human input.",
                    )
                )
    missing_protected_v2 = sorted(
        set(required_protected_v2_sources) - protected_v2_seen
    )
    for role_name in missing_protected_v2:
        issues.append(
            _issue(
                "protected_v2_role_missing",
                path,
                "roles",
                f"Canonical registry must include {role_name}.",
            )
        )
    return issues


def _exposed_material(
    root: Path,
    contamination: Mapping[str, Any],
) -> tuple[set[str], set[str], list[str]]:
    exposed_ids: set[str] = set()
    namespaces: set[str] = set()
    texts: list[str] = []
    records = contamination.get("records", [])
    if not isinstance(records, list):
        return exposed_ids, namespaces, texts
    for record in records:
        if not isinstance(record, Mapping):
            continue
        namespaces.update(
            str(value)
            for value in record.get("exposed_id_namespaces", [])
            if isinstance(value, str) and value
        )
        path = str(record.get("canonical_source_path", ""))
        commit = str(record.get("exposure_commit", ""))
        if not path or not commit:
            continue
        content = _git_show(root, commit, path)
        ids, task_texts = _jsonl_ids_and_texts(content)
        exposed_ids.update(ids)
        texts.extend(task_texts)
    return exposed_ids, namespaces, texts


def _private_material(
    private_root: Path,
) -> tuple[set[str], list[str], bool]:
    identifiers: set[str] = set()
    texts: list[str] = []
    lock = private_root / "private_lock.json"
    if lock.is_file():
        try:
            payload = json.loads(lock.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        if isinstance(payload, Mapping):
            for field in ("base_task_ids", "instance_ids"):
                values = payload.get(field, [])
                if isinstance(values, list):
                    identifiers.update(
                        str(value) for value in values if isinstance(value, str) and value
                    )
    materialized = False
    for path in sorted(private_root.glob("*.jsonl")):
        if not path.is_file():
            continue
        materialized = True
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        ids, task_texts = _jsonl_ids_and_texts(content)
        identifiers.update(ids)
        texts.extend(task_texts)
    return identifiers, texts, materialized


def _jsonl_ids_and_texts(content: str) -> tuple[set[str], list[str]]:
    identifiers: set[str] = set()
    texts: list[str] = []
    for line in content.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, Mapping):
            continue
        for field in ("task_id", "base_task_id", "instance_id"):
            value = row.get(field)
            if isinstance(value, str) and value:
                identifiers.add(value)
        base = row.get("base_task")
        if isinstance(base, Mapping):
            value = base.get("task_id")
            if isinstance(value, str) and value:
                identifiers.add(value)
        for candidate in (row, base):
            if not isinstance(candidate, Mapping):
                continue
            goal = candidate.get("goal")
            if isinstance(goal, Mapping):
                text = goal.get("user_instruction")
                if isinstance(text, str) and text.strip():
                    texts.append(text)
            direct = candidate.get("user_instruction")
            if isinstance(direct, str) and direct.strip():
                texts.append(direct)
    return identifiers, texts


def _walk_mapping(
    value: Mapping[str, Any],
) -> Iterable[tuple[str, Any]]:
    for key, child in value.items():
        yield str(key), child
        if isinstance(child, Mapping):
            yield from _walk_mapping(child)
        elif isinstance(child, list):
            for item in child:
                if isinstance(item, Mapping):
                    yield from _walk_mapping(item)


def _looks_like_reversible_encoding(value: str) -> bool:
    stripped = value.strip()
    if len(stripped) < 96 or len(stripped) % 4:
        return False
    try:
        decoded = base64.b64decode(stripped, validate=True)
    except (ValueError, binascii.Error):
        return False
    return len(decoded) >= 64


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _bytes_contain(content: bytes, markers: list[bytes]) -> bool:
    return any(marker in content for marker in markers)


def _git_check_ignored(root: Path, path: Path) -> bool:
    process = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", str(path)],
        cwd=root,
        check=False,
        capture_output=True,
    )
    return process.returncode == 0


def _git_ls_files(root: Path) -> set[str]:
    process = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        return set()
    return {line.strip() for line in process.stdout.splitlines() if line.strip()}


def _git_show(root: Path, commit: str, path: str) -> str:
    process = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return process.stdout if process.returncode == 0 else ""


def _load_json(
    path: Path,
    issues: list[dict[str, Any]],
    code: str,
) -> dict[str, Any]:
    if not path.is_file():
        issues.append(_issue(code, str(path), "file", "Required JSON file is missing."))
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(_issue(code, str(path), "json", f"Invalid JSON: {type(exc).__name__}."))
        return {}
    if not isinstance(payload, dict):
        issues.append(_issue(code, str(path), "json", "Top-level JSON value must be an object."))
        return {}
    return payload


def _issue(
    code: str,
    path: str,
    field: str,
    detail: str,
    *,
    severity: str = "blocker",
) -> dict[str, Any]:
    return {
        "file": path,
        "field": field,
        "severity": severity,
        "code": code,
        "detail": detail,
        "suggested_repair": (
            "Keep exposed rows permanently non-confirmatory and regenerate a "
            "private v2 candidate under the ignored private root."
        ),
        "automatic_repair_status": "not_attempted",
        "unresolved_human_review_state": False,
    }


def _dedupe_issues(
    issues: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (
            str(issue.get("code")),
            str(issue.get("file")),
            str(issue.get("field")),
        )
        if key not in seen:
            seen.add(key)
            output.append(issue)
    return output


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "CONTAMINATION_REGISTRY_PATH",
    "FORBIDDEN_PUBLIC_MANIFEST_FIELDS",
    "PERMANENT_DISPOSITIONS",
    "PRIVATE_LOCK_PATH",
    "PRIVATE_ROOT",
    "PUBLIC_MANIFEST_PATH",
    "find_exposed_id_reuse",
    "find_text_overlaps",
    "path_is_registered_contamination",
    "scan_artifact_for_markers",
    "validate_contamination_registry_payload",
    "validate_protected_heldout_architecture",
    "validate_public_manifest_payload",
]
