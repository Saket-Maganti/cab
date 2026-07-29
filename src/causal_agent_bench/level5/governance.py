"""Level-5 maturity gate, governance state, and release receipt helpers."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.level5.core import content_hash, file_sha256, utc_now


class Level5State(StrEnum):
    FOUNDATION_INCOMPLETE = "LEVEL5_FOUNDATION_INCOMPLETE"
    PLATFORM_FOUNDATION_COMPLETE = "CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE"
    HUMAN_VALIDATION_REQUIRED = "HUMAN_VALIDATION_REQUIRED"
    LIVE_EVIDENCE_REQUIRED = "LIVE_EVIDENCE_REQUIRED"
    EXTERNAL_REPLICATION_REQUIRED = "EXTERNAL_REPLICATION_REQUIRED"
    PROTECTED_EVALUATOR_PILOT_REQUIRED = "PROTECTED_EVALUATOR_PILOT_REQUIRED"
    COMMUNITY_PILOT_REQUIRED = "COMMUNITY_PILOT_REQUIRED"
    RELEASE_CANDIDATE = "LEVEL5_RELEASE_CANDIDATE"
    COMPLETE = "CAB_LEVEL5_COMPLETE"


FOUNDATION_CAPABILITIES = (
    "architecture",
    "experiment_registry",
    "benchmark_factory",
    "execution_os",
    "artifact_store",
    "observability",
    "reliability_lab",
    "human_review_os",
    "protected_evaluator_fixture",
    "public_sdk_cli",
    "plugin_system",
    "evidence_graph",
    "certification",
    "reproduction_harness",
    "red_team_harness",
    "governance",
    "release_engineering",
)

HARDENING_CAPABILITIES = (
    "ordered_registry_migrations",
    "concurrent_scheduler",
    "operational_backends",
    "physical_fault_injection",
    "durable_review_application",
    "hardened_evaluator_pilot_contract",
    "persistent_evidence_graph",
    "certificate_revocation_and_transparency",
    "benchmark_and_plugin_hardening",
    "cleanroom_internal_reproduction",
    "level5_coverage_gate",
    "strict_documentation",
    "redteam_hardening",
    "provider_free_suite",
    "packaging_and_release",
)

HARDENING_BLOCKERS = (
    Level5State.HUMAN_VALIDATION_REQUIRED,
    Level5State.LIVE_EVIDENCE_REQUIRED,
    Level5State.EXTERNAL_REPLICATION_REQUIRED,
    Level5State.PROTECTED_EVALUATOR_PILOT_REQUIRED,
    Level5State.COMMUNITY_PILOT_REQUIRED,
)


class GenuineEvidenceCounts(BaseModel):
    human_judgment_rows: int = Field(default=0, ge=0)
    real_model_trajectories: int = Field(default=0, ge=0)
    audited_real_runs: int = Field(default=0, ge=0)
    paper_eligible_empirical_assets: int = Field(default=0, ge=0)
    supported_empirical_claims: int = Field(default=0, ge=0)
    independent_external_reproductions: int = Field(default=0, ge=0)
    protected_evaluator_pilots: int = Field(default=0, ge=0)
    community_external_pilots: int = Field(default=0, ge=0)


class Level5BuildState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    starting_commit: str
    foundation_capabilities: dict[str, bool]
    validation_passed: bool
    genuine_evidence: GenuineEvidenceCounts = Field(default_factory=GenuineEvidenceCounts)
    critical_red_team_issues: int = Field(default=0, ge=0)
    protected_payloads_committed: int = Field(default=0, ge=0)
    generated_at: str = Field(default_factory=utc_now)

    @classmethod
    def from_path(cls, path: str | Path) -> Level5BuildState:
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))


class HardeningBuildState(BaseModel):
    """Machine-readable foundation status; it cannot promote scientific evidence."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    baseline_commit: str
    primary_state: str
    hardening_capabilities: dict[str, bool]
    genuine_evidence: GenuineEvidenceCounts = Field(default_factory=GenuineEvidenceCounts)
    critical_unresolved_issues: int = Field(default=0, ge=0)
    protected_payloads_committed: int = Field(default=0, ge=0)
    production_secrets_committed: int = Field(default=0, ge=0)
    generated_at: str = Field(default_factory=utc_now)

    @classmethod
    def from_path(cls, path: str | Path) -> HardeningBuildState:
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))


def level5_check(state: Level5BuildState) -> dict[str, Any]:
    missing_capabilities = [
        capability
        for capability in FOUNDATION_CAPABILITIES
        if not state.foundation_capabilities.get(capability, False)
    ]
    evidence = state.genuine_evidence
    blockers: list[Level5State] = []
    if missing_capabilities or not state.validation_passed:
        primary = Level5State.FOUNDATION_INCOMPLETE
    else:
        primary = Level5State.PLATFORM_FOUNDATION_COMPLETE
    if evidence.human_judgment_rows == 0:
        blockers.append(Level5State.HUMAN_VALIDATION_REQUIRED)
    if evidence.audited_real_runs == 0 or evidence.real_model_trajectories == 0:
        blockers.append(Level5State.LIVE_EVIDENCE_REQUIRED)
    if evidence.independent_external_reproductions == 0:
        blockers.append(Level5State.EXTERNAL_REPLICATION_REQUIRED)
    if evidence.protected_evaluator_pilots == 0:
        blockers.append(Level5State.PROTECTED_EVALUATOR_PILOT_REQUIRED)
    if evidence.community_external_pilots == 0:
        blockers.append(Level5State.COMMUNITY_PILOT_REQUIRED)
    if state.critical_red_team_issues:
        blockers.append(Level5State.FOUNDATION_INCOMPLETE)
    if state.protected_payloads_committed:
        blockers.append(Level5State.FOUNDATION_INCOMPLETE)

    complete_requirements = (
        primary is Level5State.PLATFORM_FOUNDATION_COMPLETE
        and not blockers
        and evidence.paper_eligible_empirical_assets > 0
        and evidence.supported_empirical_claims > 0
    )
    if complete_requirements:
        primary = Level5State.COMPLETE
    elif primary is Level5State.PLATFORM_FOUNDATION_COMPLETE and not blockers:
        primary = Level5State.RELEASE_CANDIDATE
    return {
        "primary_state": primary.value,
        "foundation_complete": not missing_capabilities and state.validation_passed,
        "level5_complete": primary is Level5State.COMPLETE,
        "blocked_states": [blocker.value for blocker in dict.fromkeys(blockers)],
        "missing_foundation_capabilities": missing_capabilities,
        "genuine_evidence": evidence.model_dump(mode="json"),
        "critical_red_team_issues": state.critical_red_team_issues,
        "protected_payloads_committed": state.protected_payloads_committed,
    }


def hardening_check(state: HardeningBuildState) -> dict[str, Any]:
    missing = [
        capability
        for capability in HARDENING_CAPABILITIES
        if not state.hardening_capabilities.get(capability, False)
    ]
    evidence = state.genuine_evidence
    counter_values = evidence.model_dump(mode="json")
    boundaries_preserved = all(value == 0 for value in counter_values.values())
    ready = (
        not missing
        and not state.critical_unresolved_issues
        and not state.protected_payloads_committed
        and not state.production_secrets_committed
        and boundaries_preserved
    )
    return {
        "primary_state": (
            "CAB_LEVEL5_HARDENED_FOUNDATION_READY"
            if ready
            else "PARTIAL_SUCCESS_HARDENING_REMAINS"
        ),
        "hardening_ready": ready,
        "missing_hardening_capabilities": missing,
        "blocked_states": [value.value for value in HARDENING_BLOCKERS],
        "genuine_evidence": counter_values,
        "scientific_boundaries_preserved": boundaries_preserved,
        "critical_unresolved_issues": state.critical_unresolved_issues,
        "protected_payloads_committed": state.protected_payloads_committed,
        "production_secrets_committed": state.production_secrets_committed,
        "level5_complete": False,
        "evaluator_state": "PROTECTED_EVALUATOR_HARDENED_PILOT_READY",
    }


def write_build_state(state: Level5BuildState, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def signed_checksum_manifest(
    files: list[str | Path],
    *,
    root: str | Path,
    development_signature: bool = True,
) -> dict[str, Any]:
    root = Path(root).resolve()
    rows: list[dict[str, str]] = []
    for value in sorted(Path(path).resolve() for path in files):
        relative = value.relative_to(root).as_posix()
        rows.append({"path": relative, "sha256": file_sha256(value)})
    unsigned = {
        "schema_version": "1.0",
        "files": rows,
        "created_at": utc_now(),
        "development_signature": development_signature,
    }
    return {
        **unsigned,
        "manifest_hash": content_hash(unsigned),
        "signature_interface": "development-hash-only" if development_signature else "external-signer",
    }


def validate_governance_templates(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    required = [
        ".github/ISSUE_TEMPLATE/benchmark_pack.yml",
        ".github/ISSUE_TEMPLATE/plugin.yml",
        ".github/ISSUE_TEMPLATE/security_report.yml",
        "docs/level5/GOVERNANCE_CHARTER.md",
        "docs/level5/CORRECTIONS_APPEALS_AND_RETIREMENT.md",
    ]
    missing = [path for path in required if not (root / path).is_file()]
    return {"passed": not missing, "missing": missing, "required_count": len(required)}


__all__ = [
    "FOUNDATION_CAPABILITIES",
    "HARDENING_BLOCKERS",
    "HARDENING_CAPABILITIES",
    "GenuineEvidenceCounts",
    "HardeningBuildState",
    "Level5BuildState",
    "Level5State",
    "hardening_check",
    "level5_check",
    "signed_checksum_manifest",
    "validate_governance_templates",
    "write_build_state",
]
