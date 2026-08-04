"""Assemble the private reviewer packet and its public-safe commitment.

Everything that identifies or reveals a task stays under ``private_data/``,
which Git ignores.  The public commitment carries aggregate composition,
one-way slot hashes and package hashes only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.common import (
    canonical_bytes,
    sha256_bytes,
    sha256_json,
    write_json,
)
from causal_agent_bench.review_ready_v2.design import design_audit
from causal_agent_bench.review_ready_v2.hostile import hostile_route_audit
from causal_agent_bench.review_ready_v2.leakage import stage1_leakage_audit, usability_audit
from causal_agent_bench.review_ready_v2.models import PairSpec
from causal_agent_bench.review_ready_v2.operators import isolation_audit
from causal_agent_bench.review_ready_v2.pairs import build_all_pairs
from causal_agent_bench.review_ready_v2.qualification import (
    QUALIFICATION_KEY,
    build_qualification_package,
)
from causal_agent_bench.review_ready_v2.routes import validate_pair_routes
from causal_agent_bench.review_ready_v2.stage1 import build_stage1_package
from causal_agent_bench.review_ready_v2.vault import load_or_create_key, write_vault

GENERATOR_VERSION = "cab_review_ready_v2_pair_generator_v1"
COMMITMENT_SCHEMA = "cab_review_ready_v2_public_commitment_v1"

PRIVATE_ROOT_TEMPLATE = "private_data/human_review/{version}"


def private_root_for(repo_root: Path) -> Path:
    return repo_root / PRIVATE_ROOT_TEMPLATE.format(version=PACKET_VERSION)


def stage2_record(pair: PairSpec) -> dict[str, Any]:
    """The Stage-2 payload: gold, contracts, policies and their rationale."""

    return {
        "pair_id": pair.pair_id,
        "semantic_objective_id": pair.semantic_objective_id,
        "intervention_family": pair.intervention_family,
        "route_requirement_clean": pair.route_requirement_clean,
        "route_requirement_intervention": pair.route_requirement_intervention,
        "clean_gold": pair.clean_gold_private,
        "intervention_gold_or_policy": pair.intervention_gold_or_policy_private,
        "clean_answer_contract": pair.clean_answer_contract_private,
        "intervention_answer_contract": pair.intervention_answer_contract_private,
        "clean_scorer_contract": pair.clean_scorer_contract_private,
        "intervention_scorer_contract": pair.intervention_scorer_contract_private,
        "recovery_authorization": pair.recovery_authorization_private,
        "abstention_opportunity": pair.abstention_opportunity_private,
        "clarification_requirement": pair.clarification_requirement_private,
        "source_to_gold_rationale": {
            "required_input_keys": list(pair.required_input_keys),
            "counterparty": pair.counterparty,
            "counterparty_resolvable_inputs": list(pair.counterparty_resolvable_inputs),
            "derivation": (
                "Every required input is obtained from a declared, capability-bounded tool "
                "observation; the answer follows by arithmetic, comparison, sorting, filtering, "
                "set membership and date reasoning over those observations alone."
            ),
        },
        "model_outputs_included": False,
    }


def build_packet(repo_root: Path, seed: bytes, *, private_root: Path | None = None) -> dict[str, Any]:
    """Generate the packet, run every gate, and return the public commitment."""

    pairs = build_all_pairs(seed)
    design = design_audit(pairs)
    if not design["passed"]:
        raise ValueError("design audit failed; refusing to write a packet")
    isolation = [
        isolation_audit(pair.clean_environment, pair.intervention_environment, pair.intervention_patch)
        for pair in pairs
    ]
    if not all(row["passed"] for row in isolation):
        raise ValueError("intervention isolation audit failed; refusing to write a packet")
    routes = [validate_pair_routes(pair) for pair in pairs]
    if not all(row["passed"] for row in routes):
        raise ValueError("causal route validation failed; refusing to write a packet")
    hostile = hostile_route_audit(pairs)
    if not hostile["passed"]:
        raise ValueError("hostile route audit failed; refusing to write a packet")

    root = private_root or private_root_for(repo_root)
    coordinator = root / "coordinator"
    stage1_dir = root / "stage1"
    qualification_dir = root / "qualification"
    stage2_dir = root / "stage2"
    mappings_dir = root / "mappings"
    for directory in (coordinator, stage1_dir, qualification_dir, stage2_dir, mappings_dir):
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)

    packages: dict[str, bytes] = {}
    mappings: dict[str, dict[str, str]] = {}
    package_hashes: dict[str, str] = {}
    for role in ("stage1_reviewer_a", "stage1_reviewer_b"):
        payload, mapping, _ = build_stage1_package(pairs, seed, role)
        packages[role] = payload
        mappings[role] = mapping
        package_hashes[f"{role}.zip"] = sha256_bytes(payload)
        (stage1_dir / f"{role}.zip").write_bytes(payload)
        (stage1_dir / f"{role}.zip").chmod(0o600)
        write_json(mappings_dir / f"{role}_mapping.json", {"reviewer_item_to_pair": mapping})
        (mappings_dir / f"{role}_mapping.json").chmod(0o600)

    qualification_payload = build_qualification_package()
    audited = {**packages, "qualification_packet": qualification_payload}
    leakage = stage1_leakage_audit(audited, pairs, mappings)
    if not leakage["passed"]:
        raise ValueError("Stage-1 leakage audit failed; refusing to publish reviewer packages")
    usability = usability_audit(audited)
    if not usability["passed"]:
        raise ValueError("Stage-1 usability audit failed; refusing to publish reviewer packages")

    (qualification_dir / "qualification_packet.zip").write_bytes(qualification_payload)
    (qualification_dir / "qualification_packet.zip").chmod(0o600)
    write_json(qualification_dir / "qualification_key.json", QUALIFICATION_KEY)
    (qualification_dir / "qualification_key.json").chmod(0o600)

    key_path, key = load_or_create_key(repo_root)
    records = [stage2_record(pair) for pair in pairs]
    vault = write_vault(stage2_dir / "stage2_vault.enc", records, key)

    write_json(
        coordinator / "private_pairs.json",
        {"packet_version": PACKET_VERSION, "pairs": [pair.model_dump(mode="json") for pair in pairs]},
    )
    write_json(coordinator / "design_audit.json", design)
    write_json(coordinator / "route_proofs.json", {"pairs": routes})
    write_json(coordinator / "isolation_audit.json", {"pairs": isolation})
    for name in ("private_pairs.json", "design_audit.json", "route_proofs.json", "isolation_audit.json"):
        (coordinator / name).chmod(0o600)

    slot_hashes = {
        f"private_slot_{index:02d}": sha256_json(pair.model_dump(mode="json"))
        for index, pair in enumerate(pairs, 1)
    }
    commitment: dict[str, Any] = {
        "schema_version": COMMITMENT_SCHEMA,
        "status": "CAB_NEW_PRIVATE_COMPACT20_V2_READY",
        "packet_version": PACKET_VERSION,
        "generator_version": GENERATOR_VERSION,
        "pair_count": len(pairs),
        "unit_of_evaluation": "clean_intervention_pair",
        "family_counts": design["composition"]["family_counts"],
        "domain_counts": design["composition"]["domain_counts"],
        "difficulty_counts": design["composition"]["difficulty_counts"],
        "family_route_matrix": design["confounding"]["family_route_matrix"],
        "distinct_semantic_objectives": design["composition"]["distinct_non_anchor_objectives"],
        "distinct_objective_signatures": design["semantic_diversity"]["distinct_objective_signatures"],
        "anchor_group_count": len(design["anchors"]["groups"]),
        "pair_content_hashes": slot_hashes,
        "stage1_package_hashes": package_hashes,
        "qualification_package_sha256": sha256_bytes(qualification_payload),
        "stage2_vault_sha256": vault["vault_sha256"],
        "stage2_key_environment_variable": "CAB_STAGE2_KEY_PATH",
        "stage2_key_stored_in_repository": False,
        "stage2_plaintext_persisted": False,
        "seed_commitment": sha256_bytes(seed),
        "private_bodies_committed": False,
        "gates": {
            "design_audit_passed": design["passed"],
            "intervention_isolation_passed": all(row["passed"] for row in isolation),
            "causal_route_validation_passed": all(row["passed"] for row in routes),
            "hostile_route_audit_passed": hostile["passed"],
            "stage1_leakage_audit_passed": leakage["passed"],
            "stage1_usability_audit_passed": usability["passed"],
        },
        "hostile_attack_count": hostile["attack_count"],
        "genuine_human_judgments": 0,
        "genuine_model_trajectories": 0,
        "c10_status": "C10_PENDING_GENUINE_REVIEW",
    }
    commitment["commitment_sha256"] = sha256_bytes(canonical_bytes(commitment))
    reports = {
        "design_audit": design,
        "isolation": isolation,
        "routes": routes,
        "hostile": hostile,
        "leakage": leakage,
        "usability": usability,
        "vault": vault,
        "key_path_is_external": str(key_path.resolve()).startswith(str(repo_root.resolve())) is False,
    }
    return {"commitment": commitment, "reports": reports, "private_root": str(root)}


def load_pairs(private_root: Path) -> list[PairSpec]:
    import json

    payload = json.loads((private_root / "coordinator" / "private_pairs.json").read_text())
    return [PairSpec.model_validate(row) for row in payload["pairs"]]


__all__ = [
    "COMMITMENT_SCHEMA",
    "GENERATOR_VERSION",
    "build_packet",
    "load_pairs",
    "private_root_for",
    "stage2_record",
]
