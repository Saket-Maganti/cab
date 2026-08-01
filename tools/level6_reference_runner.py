#!/usr/bin/env python3
"""Independent minimal CAB Level-6 conformance runner.

This file intentionally imports only Python's standard library and consumes the
language-neutral golden vectors.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): canonicalize(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite float")
        return 0.0 if value == 0.0 else float(format(value, ".15g"))
    if value is None or isinstance(value, str | int | bool):
        return value
    raise TypeError(type(value).__name__)


def portable_hash(value: Any) -> str:
    encoded = json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluate(vector: dict[str, Any]) -> Any:
    kind = vector["kind"]
    value = vector["input"]
    if kind == "scoring":
        return abs(float(value["observed"]) - float(value["expected"])) <= float(value.get("tolerance", 0.0))
    if kind == "recovery":
        return value["failure_step"] < value["attempt_step"] and value["action_id"] == value["authorized_action_id"] and value["tool"] in value["allowed_tools"] and value["returned_fact_ids"] == value["required_fact_ids"]
    if kind == "abstention":
        return bool(value["routes_exhausted"] and value["missing_fact_ids"] and not value["recovery_available"])
    if kind == "route_execution":
        return all(value["step_predicates"]) and value["final_answer_hash"] == value["gold_hash"]
    if kind == "approval_verification":
        return value["signature_valid"] and value["bindings_valid"] and not value["revoked"]
    if kind == "resource_planning":
        return value["planned"] <= value["budget"] and value["planned"] >= 0
    if kind == "evidence_graph":
        nodes = set(value["nodes"])
        return all(edge[0] in nodes and edge[1] in nodes for edge in value["edges"])
    if kind == "certificate_verification":
        return value["subject_hash"] == value["observed_hash"] and value["signature_valid"]
    if kind == "canonical_hash":
        return portable_hash(value)
    raise ValueError(kind)


def main() -> int:
    vectors = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    results = {str(vector["vector_id"]): evaluate(vector) for vector in vectors}
    print(json.dumps(results, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
