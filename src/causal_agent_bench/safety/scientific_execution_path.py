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

APPROVED_V2_PATH_MARKERS = (
    "private_data/approved/",
    "approved_materialized_bundle",
    "approved_bundle/",
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
    if requests_scientific and v2_candidate and not any(
        marker in normalized for marker in APPROVED_V2_PATH_MARKERS
    ):
        raise ValueError(
            "UNAPPROVED_V2_SCIENTIFIC_PATH: genuine review, adjudication, C10, "
            "approved materialization, and a bound execution manifest are required"
        )


__all__ = [
    "APPROVED_V2_PATH_MARKERS",
    "OBSOLETE_EXECUTION_TOKENS",
    "assert_canonical_scientific_execution_path",
]
