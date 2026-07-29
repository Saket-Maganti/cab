"""Shared Level-5 types, hashing, privacy, and serialization primitives."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class EvidenceClass(StrEnum):
    """Canonical evidence classes ordered by governance, not by numeric rank."""

    DESIGN_ONLY = "DESIGN_ONLY"
    ENGINEERING_ONLY = "ENGINEERING_ONLY"
    FIXTURE_ONLY = "FIXTURE_ONLY"
    HUMAN_INPUT_REQUIRED = "HUMAN_INPUT_REQUIRED"
    EXECUTION_PENDING = "EXECUTION_PENDING"
    PRELIMINARY_REAL_EVIDENCE = "PRELIMINARY_REAL_EVIDENCE"
    AUDITED_REAL_EVIDENCE = "AUDITED_REAL_EVIDENCE"
    PAPER_ELIGIBLE_EVIDENCE = "PAPER_ELIGIBLE_EVIDENCE"


class ActorClass(StrEnum):
    SYSTEM = "SYSTEM"
    HUMAN_REVIEWER = "HUMAN_REVIEWER"
    HUMAN_ADJUDICATOR = "HUMAN_ADJUDICATOR"
    FIXTURE = "FIXTURE"
    MODEL = "MODEL"
    EXTERNAL_REPRODUCER = "EXTERNAL_REPRODUCER"


PRIVATE_KEY_PATTERN = re.compile(
    r"(?:^|_)(?:private|protected|secret|answer|gold|reviewer_identity|task_payload)(?:_|$)",
    re.IGNORECASE,
)
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{2,127}$")


def utc_now() -> str:
    """Return a stable UTC ISO-8601 timestamp."""

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible data deterministically."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def content_hash(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_typed_id(value: str, *, label: str = "id") -> str:
    if not ID_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must match {ID_PATTERN.pattern!r}: {value!r}")
    return value


def reject_private_fields(value: Any, *, path: str = "$") -> None:
    """Fail closed when a public/registry payload contains protected fields."""

    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if PRIVATE_KEY_PATTERN.search(key_text):
                raise ValueError(f"private field is forbidden at {path}.{key_text}")
            reject_private_fields(child, path=f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_fields(child, path=f"{path}[{index}]")


def redact_sensitive(value: Any) -> Any:
    """Return a public-safe copy suitable for logs and exports."""

    if isinstance(value, dict):
        return {
            str(key): (
                "[REDACTED]"
                if PRIVATE_KEY_PATTERN.search(str(key))
                else redact_sensitive(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(child) for child in value]
    return value


__all__ = [
    "ActorClass",
    "EvidenceClass",
    "canonical_json",
    "content_hash",
    "file_sha256",
    "redact_sensitive",
    "reject_private_fields",
    "sha256_bytes",
    "utc_now",
    "validate_typed_id",
]
