"""Deterministic hashing and canonical-JSON helpers for the V2 kernel.

Kept free of ``cryptography`` and of the retired ``final_pre_run`` generator so
that the V2 scientific kernel has no import path back into retired material.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FIXTURE_MARKER = "SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE"


def canonical_bytes(value: Any) -> bytes:
    """Canonical JSON encoding used for every hash in this package."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def derive_token(seed: bytes, label: str, size: int = 12) -> str:
    """Deterministic opaque token derived from a private seed and a label."""

    return hashlib.sha256(seed + b"|" + label.encode()).hexdigest()[:size]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def flatten(value: Any, locator: str = "$") -> list[tuple[str, Any]]:
    """Flatten a JSON-like value into ``(locator, leaf)`` pairs, sorted by key."""

    if isinstance(value, dict):
        return [item for key in sorted(value) for item in flatten(value[key], f"{locator}.{key}")]
    if isinstance(value, list):
        return [
            item for index, child in enumerate(value) for item in flatten(child, f"{locator}[{index}]")
        ]
    return [(locator, value)]


def structural_diff(before: Any, after: Any) -> list[dict[str, Any]]:
    """Enumerate every leaf-level difference between two JSON-like values."""

    left = dict(flatten(before))
    right = dict(flatten(after))
    changes: list[dict[str, Any]] = []
    for locator in sorted(set(left) | set(right)):
        if locator not in right:
            changes.append({"locator": locator, "change": "removed", "before": left[locator]})
        elif locator not in left:
            changes.append({"locator": locator, "change": "added", "after": right[locator]})
        elif left[locator] != right[locator]:
            changes.append(
                {
                    "locator": locator,
                    "change": "modified",
                    "before": left[locator],
                    "after": right[locator],
                }
            )
    return changes


__all__ = [
    "FIXTURE_MARKER",
    "canonical_bytes",
    "derive_token",
    "flatten",
    "read_json",
    "sha256_bytes",
    "sha256_file",
    "sha256_json",
    "structural_diff",
    "write_json",
]
