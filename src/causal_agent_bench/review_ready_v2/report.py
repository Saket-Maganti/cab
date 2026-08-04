"""Public-safe reports.

Every function here deliberately drops private identifiers.  Reports carry
aggregate counts, matrices, statuses and hashes; they never carry a prompt, a
record, an answer, a route label per item, or a private pair identifier.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.power import COMPACT_LABEL, COMPACT_STATUS, INFERENCE_SCOPE

HONEST_STATUS_BLOCK = (
    "HUMAN_VALIDATION_REQUIRED",
    "C10_PENDING_GENUINE_REVIEW",
    "MODEL_EXECUTION_BLOCKED",
    "GENUINE_HUMAN_JUDGMENTS=0",
    "GENUINE_MODEL_TRAJECTORIES=0",
    "PAPER_ELIGIBLE_EMPIRICAL_ASSETS=0",
    "SUPPORTED_EMPIRICAL_CLAIMS=0",
    "CAB_LEVEL5_COMPLETE=false",
    "CAB_LEVEL6_COMPLETE=false",
)

NEXT_HUMAN_ACTION = (
    "Recruit two independent qualified reviewers, give each only their assigned frozen Stage-1 "
    "package and qualification materials, keep Stage 2 inaccessible until both qualified Stage-1 "
    "submissions are validated and committed, then continue through the canonical two-stage "
    "workflow."
)


def public_design_summary(design: dict[str, Any]) -> dict[str, Any]:
    anchors = design["anchors"]
    return {
        "schema_version": "cab_review_ready_v2_public_design_summary_v1",
        "status": design["status"],
        "composition": {
            "family_counts": design["composition"]["family_counts"],
            "domain_counts": design["composition"]["domain_counts"],
            "difficulty_counts": design["composition"]["difficulty_counts"],
            "distinct_non_anchor_objectives": design["composition"]["distinct_non_anchor_objectives"],
            "checks": design["composition"]["checks"],
        },
        "semantic_diversity": {
            "distinct_objective_signatures": design["semantic_diversity"][
                "distinct_objective_signatures"
            ],
            "archetype_counts": design["semantic_diversity"]["archetype_counts"],
            "domain_archetypes": design["semantic_diversity"]["domain_archetypes"],
            "family_archetypes": design["semantic_diversity"]["family_archetypes"],
            "prompt_similarity_violation_count": len(
                design["semantic_diversity"]["prompt_similarity_violations"]
            ),
            "checks": design["semantic_diversity"]["checks"],
        },
        "anchors": {
            "group_count": len(anchors["groups"]),
            "groups": [
                {
                    "anchor_group_id": row["anchor_group_id"],
                    "family": row["family"],
                    "route": "withheld_until_stage2",
                    "checks": row["checks"],
                    "passed": row["passed"],
                }
                for row in anchors["groups"]
            ],
            "checks": anchors["checks"],
        },
        "confounding": {
            "family_route_matrix": design["confounding"]["family_route_matrix"],
            "routes_per_family": design["confounding"]["routes_per_family"],
            "families_per_route": design["confounding"]["families_per_route"],
            "domain_family_matrix": design["confounding"]["domain_family_matrix"],
            "difficulty_family_matrix": design["confounding"]["difficulty_family_matrix"],
            "archetype_family_matrix": design["confounding"]["archetype_family_matrix"],
            "route_difficulty_matrix": design["confounding"]["route_difficulty_matrix"],
            "checks": design["confounding"]["checks"],
        },
        "passed": design["passed"],
    }


def public_isolation_summary(isolation: list[dict[str, Any]]) -> dict[str, Any]:
    operators: dict[str, int] = {}
    mutation_counts: dict[str, int] = {}
    for row in isolation:
        operators[row["operator"]] = operators.get(row["operator"], 0) + 1
        factor = row["intended_changed_factor"]
        mutation_counts[factor] = mutation_counts.get(factor, 0) + 1
    return {
        "schema_version": "cab_review_ready_v2_public_isolation_summary_v1",
        "status": "CAB_INTERVENTION_OPERATORS_EXECUTABLE"
        if all(row["passed"] for row in isolation)
        else "CAB_INTERVENTION_ISOLATION_FAILED",
        "pair_count": len(isolation),
        "operator_counts": dict(sorted(operators.items())),
        "intended_changed_factor_counts": dict(sorted(mutation_counts.items())),
        "pairs_with_exactly_one_mutation_unit": sum(
            row["checks"]["exactly_one_intended_mutation_unit"] for row in isolation
        ),
        "pairs_with_no_unexpected_mutation": sum(
            row["checks"]["no_unexpected_mutation"] for row in isolation
        ),
        "pairs_with_goal_preserved": sum(row["checks"]["goal_text_identical"] for row in isolation),
        "total_enumerated_diff_leaves": sum(len(row["diff"]) for row in isolation),
        "passed": all(row["passed"] for row in isolation),
    }


def public_route_summary(routes: list[dict[str, Any]]) -> dict[str, Any]:
    kinds: dict[str, int] = {}
    observations = 0
    facts = 0
    for row in routes:
        kind = row["intervention"]["route_kind"]
        kinds[kind] = kinds.get(kind, 0) + 1
        observations += len(row["clean"]["observations"]) + len(row["intervention"]["observations"])
        facts += len(row["clean"]["facts"]) + len(row["intervention"]["facts"])
    return {
        "schema_version": "cab_review_ready_v2_public_route_summary_v1",
        "status": "CAB_CAUSAL_ROUTE_VALIDATION_PASSED"
        if all(row["passed"] for row in routes)
        else "CAB_CAUSAL_ROUTE_VALIDATION_FAILED",
        "pair_count": len(routes),
        "intervention_route_counts": dict(sorted(kinds.items())),
        "executed_tool_observations": observations,
        "derived_facts": facts,
        "hidden_gold_visible_during_derivation": False,
        "undeclared_oracle_used": False,
        "passed": all(row["passed"] for row in routes),
    }


def public_hostile_summary(hostile: dict[str, Any]) -> dict[str, Any]:
    by_attack: dict[str, int] = {}
    for row in hostile["rows"]:
        for case in row["attacks"]:
            by_attack[case["attack"]] = by_attack.get(case["attack"], 0) + 1
    return {
        "schema_version": "cab_review_ready_v2_public_hostile_summary_v1",
        "status": hostile["status"],
        "pair_count": hostile["pair_count"],
        "attack_count": hostile["attack_count"],
        "attacks_by_kind": dict(sorted(by_attack.items())),
        "surviving_attack_count": len(hostile["surviving_attacks"]),
        "passed": hostile["passed"],
    }


def public_leakage_summary(leakage: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "cab_review_ready_v2_public_leakage_summary_v1",
        "status": leakage["status"],
        "package_count": leakage["package_count"],
        "archive_wide_secret_count": leakage["archive_wide_secret_count"],
        "per_item_derived_secret_count": leakage["per_item_derived_secret_count"],
        "packages": [
            {
                "package": row["package"],
                "sha256": row["sha256"],
                "file_count": row["file_count"],
                "items_value_scanned": row["items_value_scanned"],
                "forbidden_structural_key_count": row["forbidden_structural_key_count"],
                "forbidden_token_count": row["forbidden_token_count"],
                "archive_wide_hit_count": row["archive_wide_hit_count"],
                "per_item_derived_hit_count": row["per_item_derived_hit_count"],
                "checks": row["checks"],
                "passed": row["passed"],
            }
            for row in leakage["packages"]
        ],
        "leaked_values_are_never_printed": True,
        "passed": leakage["passed"],
    }


def build_readiness_report(
    *,
    commitment: dict[str, Any],
    design: dict[str, Any],
    isolation: dict[str, Any],
    routes: dict[str, Any],
    hostile: dict[str, Any],
    leakage: dict[str, Any],
    usability: dict[str, Any],
    vault: dict[str, Any],
    fixture: dict[str, Any],
    retirement: dict[str, Any],
    paths: dict[str, Any],
    power: dict[str, Any],
    freeze: dict[str, Any],
    attestation: dict[str, Any],
) -> dict[str, Any]:
    gates = {
        "CAB_NEW_PRIVATE_COMPACT20_V2_READY": commitment["status"]
        == "CAB_NEW_PRIVATE_COMPACT20_V2_READY",
        "CAB_CLEAN_INTERVENTION_PAIRING_VALIDATED": routes["passed"],
        "CAB_SEMANTIC_DIVERSITY_VALIDATED": design["passed"],
        "CAB_TRUE_ANCHORS_VALIDATED": design["anchors"]["checks"]["every_anchor_group_valid"],
        "CAB_INTERVENTION_OPERATORS_EXECUTABLE": isolation["passed"],
        "CAB_ROUTE_RESPONSE_CONFOUND_REDUCED": design["confounding"]["checks"][
            "no_family_maps_to_exactly_one_route"
        ]
        and design["confounding"]["checks"]["no_route_confined_to_one_family"],
        "CAB_STAGE1_PACKAGES_READY": usability["passed"],
        "CAB_STAGE1_LEAKAGE_AUDIT_PASSED": leakage["passed"],
        "CAB_STAGE2_ENCRYPTED_AND_KEY_EXTERNAL": vault["passed"],
        "CAB_TWO_STAGE_WORKFLOW_E2E_FIXTURE_VALIDATED": fixture["passed"],
        "CAB_CANONICAL_PATHS_UPDATED": paths["passed"],
        "CAB_RETIRED_PACKETS_BLOCKED": retirement["passed"],
        "CAB_SCIENTIFIC_FREEZE_V2_VALID": freeze["passed"],
        "CAB_ROUTE_HOSTILE_AUDIT_PASSED": hostile["passed"],
        "CAB_POWER_PLAN_CALIBRATED": power["status"] == "CAB_POWER_PLAN_CALIBRATED",
    }
    # The exact-commit attestation is deliberately NOT a tracked gate: a receipt
    # cannot truthfully live inside the commit it attests. The repository tracks
    # the policy; the receipt itself is written outside after the final commit
    # and verified with `verify-attestation`.
    ready = all(gates.values())
    return {
        "schema_version": "cab_review_ready_v2_readiness_report_v1",
        "status": "CAB_REVIEWER_READY_V2_REPAIR_COMPLETE" if ready else "CAB_REVIEWER_READY_V2_BLOCKED",
        "packet_version": PACKET_VERSION,
        "gates": gates,
        "blocking_gates": sorted(name for name, value in gates.items() if not value),
        "packet": {
            "public_commitment_sha256": commitment["commitment_sha256"],
            "pair_count": commitment["pair_count"],
            "unit_of_evaluation": commitment["unit_of_evaluation"],
            "family_counts": commitment["family_counts"],
            "domain_counts": commitment["domain_counts"],
            "difficulty_counts": commitment["difficulty_counts"],
            "family_route_matrix": commitment["family_route_matrix"],
            "distinct_semantic_objectives": commitment["distinct_semantic_objectives"],
            "anchor_group_count": commitment["anchor_group_count"],
            "stage1_package_hashes": commitment["stage1_package_hashes"],
            "qualification_package_sha256": commitment["qualification_package_sha256"],
            "stage2_vault_sha256": commitment["stage2_vault_sha256"],
            "stage2_key_environment_variable": commitment["stage2_key_environment_variable"],
            "stage2_key_stored_in_repository": False,
        },
        "external_exact_commit_attestation": {
            "required_before_distribution": True,
            "tracked_policy": "reports/reviewer_ready_v2/ATTESTATION_POLICY.json",
            "why_not_tracked": (
                "An exact-commit attestation cannot be committed inside the commit it attests, so "
                "it is written outside the repository after the final tracked commit."
            ),
            "verify_with": "python3 scripts/cab_review_ready_v2.py verify-attestation",
            "status_when_this_report_was_generated": attestation["status"],
            "present_when_this_report_was_generated": attestation.get(
                "attestation_present", False
            ),
        },
        "audits": {
            "design": design["status"],
            "isolation": isolation["status"],
            "routes": routes["status"],
            "hostile": hostile["status"],
            "hostile_attack_count": hostile["attack_count"],
            "leakage": leakage["status"],
            "usability": usability["status"],
            "fixture_e2e": fixture["status"],
            "retirement_enforcement": retirement["status"],
            "scientific_freeze": freeze["status"],
        },
        "scientific_scope": {
            "compact20_label": COMPACT_LABEL,
            "compact20_status": COMPACT_STATUS,
            "compact20_confirmatory": False,
            "inference_scope": INFERENCE_SCOPE,
            "model_family_interaction_designation": power["model_family_interaction"]["designation"],
            "primary_confirmatory_estimand": power["primary_confirmatory_estimand"]["name"],
            "primary_estimand_powered_at": power["primary_confirmatory_estimand"][
                "adequately_powered_at_degradations"
            ],
            "rank_instability_raw_probability_usable": power["rank_instability_claim"][
                "raw_reversal_probability_is_a_usable_estimand"
            ],
            "rank_instability_calibration_warning": power["rank_instability_claim"][
                "calibration_warning"
            ],
        },
        "genuine_evidence_counters": {
            "genuine_human_judgments": 0,
            "genuine_model_trajectories": 0,
            "paper_eligible_empirical_assets": 0,
            "supported_empirical_claims": 0,
            "provider_calls_performed": 0,
            "model_calls_performed": 0,
        },
        "honest_status": list(HONEST_STATUS_BLOCK),
        "next_human_action": NEXT_HUMAN_ACTION,
        "CAB_LEVEL5_COMPLETE": False,
        "CAB_LEVEL6_COMPLETE": False,
    }


def readiness_markdown(report: dict[str, Any]) -> str:
    packet = report["packet"]
    audits = report["audits"]
    scope = report["scientific_scope"]
    lines = [
        "# CAB reviewer-ready V2 readiness report",
        "",
        f"`{report['status']}`",
        "",
        f"Packet version: `{report['packet_version']}`",
        f"Public commitment: `{packet['public_commitment_sha256']}`",
        "",
        "## Gates",
        "",
        "| Gate | Status |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| `{name}` | {'PASS' if value else 'BLOCKED'} |" for name, value in sorted(report["gates"].items())
    )
    lines += [
        "",
        "## Packet composition",
        "",
        f"- Twenty explicit clean/intervention pairs; unit of evaluation is `{packet['unit_of_evaluation']}`.",
        f"- Families: `{packet['family_counts']}`",
        f"- Domains: `{packet['domain_counts']}`",
        f"- Difficulty: `{packet['difficulty_counts']}`",
        f"- Distinct semantic objectives (non-anchor): {packet['distinct_semantic_objectives']}",
        f"- True controlled anchor groups: {packet['anchor_group_count']}",
        "",
        "### Family x required response type",
        "",
        "| Family | Completion | Recovery | Clarification | Abstention |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for family, row in sorted(packet["family_route_matrix"].items()):
        lines.append(
            f"| {family} | {row['completion']} | {row['recovery']} | "
            f"{row['clarification']} | {row['abstention']} |"
        )
    lines += [
        "",
        "## External exact-commit attestation",
        "",
        "An exact-commit attestation cannot be committed inside the commit it attests. The",
        "repository tracks the policy at `reports/reviewer_ready_v2/ATTESTATION_POLICY.json`;",
        "the receipt is written outside the repository after the final tracked commit. Verify",
        "it with:",
        "",
        "```bash",
        "python3 scripts/cab_review_ready_v2.py verify-attestation",
        "```",
        "",
        f"Status when this report was generated: "
        f"`{report['external_exact_commit_attestation']['status_when_this_report_was_generated']}`",
        "",
        "## Audits",
        "",
    ]
    lines.extend(f"- `{name}`: `{value}`" for name, value in sorted(audits.items()))
    lines += [
        "",
        "## Scientific scope",
        "",
        f"- Compact-20 is a **{scope['compact20_label']}**: {scope['compact20_status']}.",
        f"- {scope['inference_scope']}",
        f"- Primary confirmatory estimand: {scope['primary_confirmatory_estimand']}; adequately "
        f"powered at assumed mean degradations {scope['primary_estimand_powered_at']}.",
        f"- Model x family interaction: **{scope['model_family_interaction_designation']}**.",
        f"- Raw rank-reversal probability usable as an estimand: "
        f"**{scope['rank_instability_raw_probability_usable']}**. "
        f"{scope['rank_instability_calibration_warning']}",
        "",
        "## Genuine evidence",
        "",
    ]
    lines.extend(
        f"- `{name}`: {value}" for name, value in sorted(report["genuine_evidence_counters"].items())
    )
    lines += ["", "## Honest status", ""]
    lines.extend(f"- `{value}`" for value in report["honest_status"])
    lines += ["", "## Exact next human action", "", f"> {report['next_human_action']}", ""]
    return "\n".join(lines)


__all__ = [
    "HONEST_STATUS_BLOCK",
    "NEXT_HUMAN_ACTION",
    "build_readiness_report",
    "public_design_summary",
    "public_hostile_summary",
    "public_isolation_summary",
    "public_leakage_summary",
    "public_route_summary",
    "readiness_markdown",
]
