"""Retired-packet registry, active-path registry, and their enforcement.

Retirement is not documentation.  Every ingestion, C10 evaluation, slice lock and
execution authorization calls :func:`enforce_active_packet`, which refuses any
retired packet — including a renamed copy carrying the same public commitment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.common import read_json

RETIREMENT_STATUS = "EXPOSED_OR_INVALID_DEVELOPMENT_FIXTURE_NOT_ELIGIBLE_FOR_GENUINE_REVIEW"
REGISTRY_SCHEMA = "cab_review_ready_v2_retired_packet_registry_v1"
PATH_REGISTRY_SCHEMA = "cab_review_ready_v2_active_path_registry_v1"

RETIRED_PACKETS: tuple[dict[str, Any], ...] = (
    {
        "packet_version": "compact20-public-development",
        "retirement_reason": (
            "Candidate bodies, task content and review metadata were published in the tracked "
            "repository during development, so no genuine reviewer can be blind to them."
        ),
        "public_commitment_or_hash_if_safe": None,
        "known_public_paths": [
            "data/human_validation/no_api_task_review/compact20_candidate_manifest.json",
        ],
    },
    {
        "packet_version": "compact20_real_review",
        "retirement_reason": (
            "Review artifacts were produced against publicly visible candidates and partly by an "
            "AI proxy, which the C10 contract forbids as genuine human evidence."
        ),
        "public_commitment_or_hash_if_safe": None,
        "known_public_paths": [
            "data/human_validation/no_api_task_review/compact20_task_review_AI_PROXY_TEST_ONLY.csv",
            "data/human_validation/no_api_task_review/compact20_gold_policy_review_AI_PROXY_TEST_ONLY.csv",
        ],
    },
    {
        "packet_version": "compact20-reviewed-v1",
        "retirement_reason": (
            "The reviewed manifest exposed Stage-2 gold, scorer policy, answer contracts, recovery "
            "routes and abstention opportunities in public Git history."
        ),
        "public_commitment_or_hash_if_safe": None,
        "known_public_paths": ["data/compact20_reviewed/compact20_reviewed_manifest.json"],
    },
    {
        "packet_version": "compact20-v2-instances",
        "retirement_reason": (
            "The V2 instance file was a public development artifact; its identifiers and bodies "
            "are contaminated for the purposes of blind review."
        ),
        "public_commitment_or_hash_if_safe": None,
        "known_public_paths": ["data/compact20_reviewed/compact20_v2_instances.jsonl"],
    },
    {
        "packet_version": "compact20-final-private-v1",
        "retirement_reason": (
            "Scientifically invalid kernel: intervention family was perfectly confounded with the "
            "required response type, interventions were declared rather than applied to a clean "
            "instance, anchors were boolean flags on unrelated rows, prompts were generic "
            "placeholders, abstention was asserted without route exhaustion, recovery leaned on a "
            "general artifact-reader oracle, and Stage-2 plaintext sat beside its own key."
        ),
        "public_commitment_or_hash_if_safe": (
            "f4767f10ef0c5edadb2a22a5445450fba5583a99eee8aff709a0537c86e6e66f"
        ),
        "known_public_paths": ["data/manifests/compact20_final_private_commitment.json"],
        "retired_stage1_package_hashes": [
            "35e2521d2843f5b5b3e8b5d75f5169fc48d246c9f6dbccd3f42a39659c42b52e",
            "213e35847448dc93ffe982d92a5d04dc979343bf102c65260c21ae09e1777e15",
            "e4de5be7075d09d18fcb24075a32bde1d319213caba999c256d072b0cb7a8487",
        ],
        "retired_stage2_commitment": (
            "2bf5e0b536bada749c89a7421fad2f5f3b67dac7543ded7167cf5084e63d940d"
        ),
    },
)


class RetiredPacketError(ValueError):
    """A retired packet was offered to a gate that only accepts the active packet."""


def retired_packet_registry() -> dict[str, Any]:
    entries = [
        {
            **entry,
            "status": RETIREMENT_STATUS,
            "eligible_for_genuine_review": False,
            "eligible_for_c10": False,
            "eligible_for_model_execution": False,
            "eligible_for_paper_claims": False,
            "replacement_version": PACKET_VERSION,
        }
        for entry in RETIRED_PACKETS
    ]
    return {
        "schema_version": REGISTRY_SCHEMA,
        "status": "CAB_RETIRED_PACKETS_BLOCKED",
        "active_packet_version": PACKET_VERSION,
        "retired_packet_count": len(entries),
        "enforcement": (
            "Enforced in code by enforce_active_packet(); a renamed copy carrying a retired public "
            "commitment or a retired Stage-1 package hash is rejected on identity, not on name."
        ),
        "retired_packets": entries,
    }


def retired_versions() -> set[str]:
    return {str(entry["packet_version"]) for entry in RETIRED_PACKETS}


def retired_hashes() -> set[str]:
    hashes: set[str] = set()
    for entry in RETIRED_PACKETS:
        commitment = entry.get("public_commitment_or_hash_if_safe")
        if commitment:
            hashes.add(str(commitment))
        hashes.update(str(value) for value in entry.get("retired_stage1_package_hashes", []))
        stage2 = entry.get("retired_stage2_commitment")
        if stage2:
            hashes.add(str(stage2))
    return hashes


def is_retired(*, packet_version: str | None = None, commitment: str | None = None) -> bool:
    if packet_version and packet_version in retired_versions():
        return True
    return bool(commitment and commitment in retired_hashes())


def enforce_active_packet(
    *,
    packet_version: str | None,
    commitment: str | None = None,
    action: str,
    package_hashes: dict[str, str] | None = None,
) -> None:
    """Fail closed unless this is the active packet.

    ``action`` names the gate for the error message: ingestion, C10, slice lock,
    or execution authorization.
    """

    offered_hashes = set((package_hashes or {}).values())
    if commitment:
        offered_hashes.add(commitment)
    colliding = sorted(offered_hashes & retired_hashes())
    if colliding:
        raise RetiredPacketError(
            f"{action} refused: the material carries a retired packet identity "
            f"({len(colliding)} retired hash match(es)). {RETIREMENT_STATUS}"
        )
    if packet_version in retired_versions():
        raise RetiredPacketError(
            f"{action} refused: packet version {packet_version!r} is retired. {RETIREMENT_STATUS}"
        )
    if packet_version != PACKET_VERSION:
        raise RetiredPacketError(
            f"{action} refused: expected the active packet {PACKET_VERSION!r}, got {packet_version!r}."
        )


def active_path_registry(repo_root: Path) -> dict[str, Any]:
    private_root = f"private_data/human_review/{PACKET_VERSION}"
    return {
        "schema_version": PATH_REGISTRY_SCHEMA,
        "status": "CAB_CANONICAL_PATHS_UPDATED",
        "active_private_packet_version": PACKET_VERSION,
        "active_private_root": private_root,
        "active_stage1_package_paths": [
            f"{private_root}/stage1/stage1_reviewer_a.zip",
            f"{private_root}/stage1/stage1_reviewer_b.zip",
        ],
        "active_qualification_package_path": f"{private_root}/qualification/qualification_packet.zip",
        "active_stage2_vault_path": f"{private_root}/stage2/stage2_vault.enc",
        "external_key_environment_variable": "CAB_STAGE2_KEY_PATH",
        "active_review_schema": "cab_stage1_pair_review_v2",
        "active_review_form_schema": "cab_stage1_review_form_v2",
        "active_c10_contract": "configs/human_validation/c10_contract_v2.json",
        "active_scientific_freeze": "reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json",
        "active_public_commitment": "reports/reviewer_ready_v2/PUBLIC_PACKET_COMMITMENT.json",
        "retired_packet_registry": "reports/reviewer_ready_v2/RETIRED_PACKET_REGISTRY.json",
        "canonical_review_runbook": "docs/HUMAN_REVIEW_READY_V2_RUNBOOK.md",
        "canonical_reviewer_instructions": "docs/STAGE1_REVIEWER_INSTRUCTIONS_V2.md",
        "canonical_coordinator_runbook": "docs/STAGE2_COORDINATOR_RUNBOOK_V2.md",
        "canonical_scientific_design": "docs/COMPACT20_V2_SCIENTIFIC_DESIGN.md",
        "canonical_security_policy": "docs/PRIVATE_PACKET_SECURITY_POLICY.md",
        "canonical_cli_commands": [
            "generate-private-packet",
            "validate-private-packet",
            "generate-stage1-packages",
            "validate-stage1-packages",
            "ingest-reviewer-qualification",
            "ingest-stage1",
            "validate-stage1-submissions",
            "commit-stage1",
            "unlock-stage2",
            "generate-stage2-packages",
            "ingest-stage2",
            "validate-stage2-submissions",
            "build-disagreement-queue",
            "ingest-adjudication",
            "compute-agreement",
            "run-c10",
            "build-exclusion-register",
            "lock-reviewed-slice",
            "authorize-model-execution",
        ],
        "cli_entry_point": "scripts/cab_review_ready_v2.py",
        "superseded_paths": {
            "private_data/final_hostile_pre_run/compact20-final-private-v1": "RETIRED",
            "data/manifests/compact20_final_private_commitment.json": "RETIRED_COMMITMENT_RECORD",
            "reports/final_hostile_pre_run/SCIENTIFIC_FREEZE_MANIFEST.json": "SUPERSEDED_BY_FREEZE_V2",
        },
        "repository_root_relative": True,
        "repo_root_checked": str(repo_root.name),
    }


def verify_active_paths(repo_root: Path) -> dict[str, Any]:
    """Confirm that every tracked path the registry names actually exists."""

    registry = active_path_registry(repo_root)
    tracked_keys = (
        "active_c10_contract",
        "active_scientific_freeze",
        "active_public_commitment",
        "retired_packet_registry",
        "canonical_review_runbook",
        "canonical_reviewer_instructions",
        "canonical_coordinator_runbook",
        "canonical_scientific_design",
        "canonical_security_policy",
        "cli_entry_point",
    )
    missing = sorted(key for key in tracked_keys if not (repo_root / str(registry[key])).exists())
    private_root = repo_root / str(registry["active_private_root"])
    checks = {
        "every_tracked_canonical_path_exists": not missing,
        "private_root_is_git_ignored": "private_data/" in (repo_root / ".gitignore").read_text(),
        "active_version_is_not_retired": not is_retired(packet_version=PACKET_VERSION),
        "private_root_present_or_not_yet_generated": True,
    }
    return {
        "registry": registry,
        "missing_tracked_paths": missing,
        "private_root_generated": private_root.is_dir(),
        "checks": checks,
        "passed": all(checks.values()),
    }


def retirement_enforcement_report() -> dict[str, Any]:
    """Demonstrate, by exercising the gate, that retirement is enforced in code."""

    gates = ("stage1_ingestion", "c10_evaluation", "slice_lock", "model_execution_authorization")
    rows: list[dict[str, Any]] = []
    for gate in gates:
        for entry in RETIRED_PACKETS:
            rejected = False
            try:
                enforce_active_packet(
                    packet_version=str(entry["packet_version"]),
                    commitment=entry.get("public_commitment_or_hash_if_safe"),
                    action=gate,
                )
            except RetiredPacketError:
                rejected = True
            rows.append({"gate": gate, "packet_version": entry["packet_version"], "rejected": rejected})
    renamed_rejected = False
    try:
        enforce_active_packet(
            packet_version=PACKET_VERSION,
            commitment="f4767f10ef0c5edadb2a22a5445450fba5583a99eee8aff709a0537c86e6e66f",
            action="renamed_copy_probe",
        )
    except RetiredPacketError:
        renamed_rejected = True
    checks = {
        "every_retired_packet_rejected_at_every_gate": all(row["rejected"] for row in rows),
        "renamed_copy_with_retired_commitment_rejected": renamed_rejected,
        "active_packet_accepted": _active_accepted(),
    }
    return {
        "schema_version": "cab_review_ready_v2_retirement_enforcement_v1",
        "status": "CAB_RETIRED_PACKETS_BLOCKED" if all(checks.values()) else "RETIREMENT_NOT_ENFORCED",
        "probe_count": len(rows) + 1,
        "rows": rows,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _active_accepted() -> bool:
    try:
        enforce_active_packet(packet_version=PACKET_VERSION, action="self_check")
    except RetiredPacketError:
        return False
    return True


def load_registry(path: Path) -> dict[str, Any]:
    return read_json(path)


__all__ = [
    "PATH_REGISTRY_SCHEMA",
    "REGISTRY_SCHEMA",
    "RETIRED_PACKETS",
    "RETIREMENT_STATUS",
    "RetiredPacketError",
    "active_path_registry",
    "enforce_active_packet",
    "is_retired",
    "load_registry",
    "retired_hashes",
    "retired_packet_registry",
    "retired_versions",
    "retirement_enforcement_report",
    "verify_active_paths",
]
