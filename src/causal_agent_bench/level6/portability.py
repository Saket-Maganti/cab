"""Language-neutral normalization and cross-implementation conformance."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): canonicalize(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite floating-point values are not portable")
        return 0.0 if value == 0.0 else float(format(value, ".15g"))
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("portable timestamps require an offset")
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if value is None or isinstance(value, str | int | bool):
        return value
    raise TypeError(f"unsupported portable value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def portable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def evaluate_conformance_vector(vector: dict[str, Any]) -> Any:
    kind = vector["kind"]
    payload = vector["input"]
    if kind == "scoring":
        tolerance = float(payload.get("tolerance", 0.0))
        return abs(float(payload["observed"]) - float(payload["expected"])) <= tolerance
    if kind == "recovery":
        return bool(
            payload["failure_step"] < payload["attempt_step"]
            and payload["action_id"] == payload["authorized_action_id"]
            and payload["tool"] in payload["allowed_tools"]
            and payload["returned_fact_ids"] == payload["required_fact_ids"]
        )
    if kind == "abstention":
        return bool(
            payload["routes_exhausted"]
            and payload["missing_fact_ids"]
            and not payload["recovery_available"]
        )
    if kind == "route_execution":
        return all(payload["step_predicates"]) and payload["final_answer_hash"] == payload["gold_hash"]
    if kind == "approval_verification":
        return payload["signature_valid"] and payload["bindings_valid"] and not payload["revoked"]
    if kind == "resource_planning":
        return payload["planned"] <= payload["budget"] and payload["planned"] >= 0
    if kind == "evidence_graph":
        nodes = set(payload["nodes"])
        return all(edge[0] in nodes and edge[1] in nodes for edge in payload["edges"])
    if kind == "certificate_verification":
        return bool(payload["subject_hash"] == payload["observed_hash"] and payload["signature_valid"])
    if kind == "canonical_hash":
        return portable_hash(payload)
    raise ValueError(f"unknown conformance vector kind: {kind}")


def default_conformance_vectors() -> list[dict[str, Any]]:
    vectors = [
        {"vector_id": "scoring-001", "kind": "scoring", "input": {"expected": 1.0, "observed": 1.0001, "tolerance": 0.001}},
        {"vector_id": "recovery-001", "kind": "recovery", "input": {"failure_step": 1, "attempt_step": 2, "action_id": "fallback", "authorized_action_id": "fallback", "tool": "verify_fact", "allowed_tools": ["verify_fact"], "returned_fact_ids": ["fact.a"], "required_fact_ids": ["fact.a"]}},
        {"vector_id": "abstention-001", "kind": "abstention", "input": {"routes_exhausted": True, "missing_fact_ids": ["fact.a"], "recovery_available": False}},
        {"vector_id": "route-001", "kind": "route_execution", "input": {"step_predicates": [True, True], "final_answer_hash": "a" * 64, "gold_hash": "a" * 64}},
        {"vector_id": "approval-001", "kind": "approval_verification", "input": {"signature_valid": True, "bindings_valid": True, "revoked": False}},
        {"vector_id": "resources-001", "kind": "resource_planning", "input": {"planned": 20, "budget": 25}},
        {"vector_id": "graph-001", "kind": "evidence_graph", "input": {"nodes": ["artifact", "fact", "answer"], "edges": [["artifact", "fact"], ["fact", "answer"]]}},
        {"vector_id": "certificate-001", "kind": "certificate_verification", "input": {"subject_hash": "b" * 64, "observed_hash": "b" * 64, "signature_valid": True}},
        {"vector_id": "hash-001", "kind": "canonical_hash", "input": {"z": -0.0, "a": [1, 2, 3]}},
    ]
    for vector in vectors:
        vector["expected"] = evaluate_conformance_vector(vector)
    return vectors


def run_cross_implementation_conformance(
    repo_root: str | Path,
    *,
    vectors_path: str | Path = "spec/level6/conformance_vectors.json",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    path = _resolve(root, vectors_path)
    vectors = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(vectors, list):
        raise ValueError("conformance vectors must be a JSON array")
    main = {
        str(vector["vector_id"]): evaluate_conformance_vector(vector)
        for vector in vectors
    }
    completed = subprocess.run(
        [sys.executable, str(root / "tools/level6_reference_runner.py"), str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    reference = json.loads(completed.stdout)
    checks = {
        vector_id: main[vector_id] == reference[vector_id]
        for vector_id in main
    }
    return {
        "schema_version": "cab_cross_implementation_conformance_v1",
        "status": "CAB_PORTABILITY_FOUNDATION_READY",
        "passed": all(checks.values()),
        "vector_count": len(vectors),
        "checks": checks,
        "main_results": main,
        "reference_results": reference,
        "alternate_implementation_is_external": False,
        "fixture_only": True,
    }


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


__all__ = [
    "canonical_json",
    "canonicalize",
    "default_conformance_vectors",
    "evaluate_conformance_vector",
    "portable_hash",
    "run_cross_implementation_conformance",
]
