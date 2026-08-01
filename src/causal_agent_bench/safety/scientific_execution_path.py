"""Fail-closed guards for obsolete or unapproved CAB scientific data paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

OBSOLETE_EXECUTION_TOKENS = (
    "scale100_confirmatory_v1_candidate",
    "naturalistic_transfer_v1_candidate",
    "main500_confirmatory_v1_candidate",
    "main_v0_1_500",
    "naturalistic_ministudy",
    "generate_scale100_confirmatory_v1",
    "generate_naturalistic_transfer_v1",
    "generate_main500_confirmatory_v1",
)

def assert_canonical_scientific_execution_path(
    config: Any,
    benchmark_path: str | Path,
) -> None:
    """Reject obsolete v1 always and unapproved v2 when evidence is requested."""

    normalized = Path(benchmark_path).as_posix().lower()
    obsolete = [token for token in OBSOLETE_EXECUTION_TOKENS if token in normalized]
    if obsolete:
        raise ValueError(
            "SUPERSEDED_SCIENTIFIC_EXECUTION_PATH: execution is disabled for "
            f"{obsolete}; preserve these artifacts for history/fixtures only"
        )
    scientific = bool(getattr(config, "scientific_evidence", False))
    evidence_level = str(
        getattr(config, "scientific_evidence_level", "default") or "default"
    )
    requests_scientific = scientific or evidence_level in {
        "pilot_supported",
        "main_supported",
    }
    v2_candidate = any(
        token in normalized
        for token in (
            "scale100_confirmatory_v2",
            "naturalistic_transfer_v2",
            "artifact_rich_synthetic_transfer",
            "compact20_v2",
        )
    )
    if requests_scientific and v2_candidate:
        receipt_path = getattr(config, "approval_receipt_path", None)
        if not receipt_path:
            raise ValueError(
                "CRYPTOGRAPHIC_APPROVAL_REQUIRED: an approved-looking path is "
                "not execution authorization"
            )
        from causal_agent_bench.safety.approval_receipt import (
            verify_approval_receipt,
        )

        benchmark = Path(benchmark_path)
        if not benchmark.is_absolute():
            benchmark = Path.cwd() / benchmark
        if not benchmark.is_file():
            raise ValueError(
                f"BOUND_BENCHMARK_MISSING: {benchmark}"
            )
        import hashlib

        benchmark_hash = hashlib.sha256(benchmark.read_bytes()).hexdigest()
        verification = verify_approval_receipt(
            receipt_path,
            repo_root=Path.cwd(),
            allowed_scope="scientific",
            expected_bindings={"task_pack": benchmark_hash},
        )
        if not verification["passed"]:
            raise ValueError(
                "CRYPTOGRAPHIC_APPROVAL_INVALID: "
                + ",".join(verification["errors"])
            )


__all__ = [
    "OBSOLETE_EXECUTION_TOKENS",
    "assert_canonical_scientific_execution_path",
]
