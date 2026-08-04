"""Composition, semantic-diversity, anchor and confounding audits.

Unique identifiers are never accepted as evidence of unique tasks.  Diversity is
measured from objective signatures, task archetypes, structural schema
signatures, gold-derivation signatures and prompt shingle similarity, all
computed deterministically without any model.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from causal_agent_bench.review_ready_v2.catalog import OBJECTIVES, TARGET_FAMILY_ROUTE_MATRIX
from causal_agent_bench.review_ready_v2.common import flatten, sha256_json
from causal_agent_bench.review_ready_v2.models import PairSpec

FAMILIES = ("tool_removal", "tool_failure", "memory_corruption", "observation_conflict")
ROUTES = ("completion", "recovery", "clarification", "abstention")
DIFFICULTY_TARGET = {"easy": 4, "medium": 8, "hard": 4, "stress": 4}
MIN_DISTINCT_OBJECTIVES = 16
MAX_ARCHETYPE_REUSE = 2
MAX_PROMPT_SIMILARITY = 0.5
SHINGLE_SIZE = 3


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def shingles(text: str, size: int = SHINGLE_SIZE) -> set[str]:
    words = _tokens(text)
    if len(words) < size:
        return {" ".join(words)}
    return {" ".join(words[index : index + size]) for index in range(len(words) - size + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def structural_schema_signature(pair: PairSpec) -> str:
    fields = sorted(
        f"{source}.{field}"
        for source, declared in pair.primitive_evidence_manifest.items()
        for field in declared
    )
    return sha256_json(fields)[:16]


def required_operation_signature(pair: PairSpec) -> str:
    return sha256_json(
        {
            "archetype": pair.task_archetype,
            "inputs": sorted(pair.required_input_keys),
            "capabilities": sorted(
                {contract.declared_capability for contract in pair.declared_tool_contracts}
            ),
        }
    )[:16]


def gold_derivation_signature(pair: PairSpec) -> str:
    parts = pair.clean_gold_private.split("|")
    kinds = []
    for part in parts:
        if re.fullmatch(r"-?\d+(\.\d+)?", part):
            kinds.append("numeric")
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}(T.*)?", part):
            kinds.append("temporal")
        elif re.search(r"[A-Z]{3}|\.", part):
            kinds.append("identifier")
        else:
            kinds.append("token")
    return sha256_json({"arity": len(parts), "kinds": kinds, "archetype": pair.task_archetype})[:16]


def objective_signature(pair: PairSpec) -> str:
    return sha256_json(
        {
            "archetype": pair.task_archetype,
            "schema": structural_schema_signature(pair),
            "operations": required_operation_signature(pair),
            "derivation": gold_derivation_signature(pair),
            "goal_tokens": sorted(set(_tokens(pair.shared_goal))),
        }
    )[:20]


def non_anchor(pairs: list[PairSpec]) -> list[PairSpec]:
    return [pair for pair in pairs if pair.anchor is None]


def composition_audit(pairs: list[PairSpec]) -> dict[str, Any]:
    families = Counter(pair.intervention_family for pair in pairs)
    domains = Counter(pair.domain for pair in pairs)
    difficulties = Counter(pair.difficulty for pair in pairs)
    objectives = {pair.semantic_objective_id for pair in non_anchor(pairs)}
    checks = {
        "pair_count_is_twenty": len(pairs) == 20,
        "four_families_five_pairs_each": len(families) == 4 and set(families.values()) == {5},
        "at_least_eight_domains": len(domains) >= 8,
        "no_domain_above_three_pairs": max(domains.values(), default=0) <= 3,
        "difficulty_distribution_exact": dict(difficulties) == DIFFICULTY_TARGET,
        "sixteen_distinct_non_anchor_objectives": len(objectives) == MIN_DISTINCT_OBJECTIVES,
        "four_anchor_pairs": sum(pair.anchor is not None for pair in pairs) == 4,
        "every_pair_has_both_instances": all(
            pair.clean_instance_id and pair.intervention_instance_id for pair in pairs
        ),
        "clean_route_always_completion": all(
            pair.route_requirement_clean == "completion" for pair in pairs
        ),
        "no_duplicate_pair_ids": len({pair.pair_id for pair in pairs}) == len(pairs),
    }
    return {
        "family_counts": dict(sorted(families.items())),
        "domain_counts": dict(sorted(domains.items())),
        "difficulty_counts": dict(sorted(difficulties.items())),
        "distinct_non_anchor_objectives": len(objectives),
        "checks": checks,
        "passed": all(checks.values()),
    }


def semantic_diversity_audit(pairs: list[PairSpec]) -> dict[str, Any]:
    base = non_anchor(pairs)
    signatures = {pair.pair_id: objective_signature(pair) for pair in base}
    archetypes = Counter(pair.task_archetype for pair in base)
    domain_archetypes = {
        domain: sorted({pair.task_archetype for pair in base if pair.domain == domain})
        for domain in sorted({pair.domain for pair in base})
    }
    family_archetypes = {
        family: sorted({pair.task_archetype for pair in base if pair.intervention_family == family})
        for family in FAMILIES
    }
    prompt_shingles = {pair.pair_id: shingles(pair.clean_prompt) for pair in base}
    similarities: list[dict[str, Any]] = []
    for index, left in enumerate(base):
        for right in base[index + 1 :]:
            score = jaccard(prompt_shingles[left.pair_id], prompt_shingles[right.pair_id])
            if score >= MAX_PROMPT_SIMILARITY:
                similarities.append(
                    {"left": left.pair_id, "right": right.pair_id, "jaccard": round(score, 4)}
                )
    generic_prompts = [
        pair.pair_id
        for pair in pairs
        if re.search(r"resolve request \d+|using the declared records", pair.clean_prompt, re.I)
    ]
    checks = {
        "at_least_sixteen_distinct_objective_signatures": len(set(signatures.values()))
        >= MIN_DISTINCT_OBJECTIVES,
        "archetype_reuse_within_limit": max(archetypes.values(), default=0) <= MAX_ARCHETYPE_REUSE,
        "no_domain_maps_to_a_single_operation_type": all(
            len(value) >= 2 for value in domain_archetypes.values()
        ),
        "no_family_uses_a_single_archetype": all(
            len(value) >= 3 for value in family_archetypes.values()
        ),
        "no_prompt_template_cluster_dominates": not similarities,
        "no_generic_placeholder_prompts": not generic_prompts,
        "distinct_structural_schemas": len({structural_schema_signature(pair) for pair in base}) >= 14,
        "distinct_derivation_signatures": len({gold_derivation_signature(pair) for pair in base}) >= 8,
    }
    return {
        "distinct_objective_signatures": len(set(signatures.values())),
        "archetype_counts": dict(sorted(archetypes.items())),
        "domain_archetypes": domain_archetypes,
        "family_archetypes": family_archetypes,
        "prompt_similarity_violations": similarities,
        "generic_prompt_pairs": generic_prompts,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _numeric_multiset(pair: PairSpec) -> list[float]:
    return sorted(
        float(leaf)
        for _, leaf in flatten(pair.clean_environment.sources)
        if isinstance(leaf, int | float) and not isinstance(leaf, bool)
    )


def _string_leaves(pair: PairSpec) -> list[str]:
    return sorted(str(leaf) for _, leaf in flatten(pair.clean_environment.sources) if isinstance(leaf, str))


def _record_order(pair: PairSpec) -> list[Any]:
    return [
        list(value)
        for _, value in sorted(pair.clean_environment.sources.items())
        if isinstance(value, list)
    ]


def anchor_audit(pairs: list[PairSpec]) -> dict[str, Any]:
    index = {pair.pair_id: pair for pair in pairs}
    groups: list[dict[str, Any]] = []
    for pair in pairs:
        if pair.anchor is None:
            continue
        source = index[pair.anchor.anchor_source_pair_id]
        checks = {
            "same_semantic_objective": source.semantic_objective_id == pair.semantic_objective_id,
            "same_task_archetype": source.task_archetype == pair.task_archetype,
            "same_difficulty": source.difficulty == pair.difficulty,
            "same_intervention_family": source.intervention_family == pair.intervention_family,
            "same_route_requirement": (
                source.route_requirement_intervention == pair.route_requirement_intervention
            ),
            "same_required_inputs": sorted(source.required_input_keys)
            == sorted(pair.required_input_keys),
            "same_goal_text": source.shared_goal == pair.shared_goal,
            "same_prompt_text": source.clean_prompt == pair.clean_prompt,
            "same_answer_logic_numeric_values": _numeric_multiset(source) == _numeric_multiset(pair),
            "same_gold_derivation_signature": gold_derivation_signature(source)
            == gold_derivation_signature(pair),
            "same_intervention_operator": source.intervention_operator == pair.intervention_operator,
            "identifier_labels_differ": _string_leaves(source) != _string_leaves(pair),
            "record_order_differs": _record_order(source) != _record_order(pair),
            "instances_are_not_byte_identical": source.clean_environment.model_dump(mode="json")
            != pair.clean_environment.model_dump(mode="json"),
            "declared_nuisance_axes_present": bool(pair.anchor.allowed_nuisance_differences),
            "declared_forbidden_axes_present": bool(pair.anchor.forbidden_semantic_differences),
        }
        groups.append(
            {
                "anchor_group_id": pair.anchor.anchor_group_id,
                "source_pair_id": source.pair_id,
                "anchor_pair_id": pair.pair_id,
                "family": pair.intervention_family,
                "route": pair.route_requirement_intervention,
                "checks": checks,
                "passed": all(checks.values()),
            }
        )
    checks = {
        "exactly_four_anchor_groups": len(groups) == 4,
        "every_anchor_group_valid": all(row["passed"] for row in groups),
        "anchors_span_all_four_families": len({row["family"] for row in groups}) == 4,
        "anchor_sources_are_non_anchor_pairs": all(
            index[str(row["source_pair_id"])].anchor is None for row in groups
        ),
    }
    return {"groups": groups, "checks": checks, "passed": all(checks.values())}


def _matrix(pairs: list[PairSpec], row_key: str, column_key: str) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for pair in pairs:
        row = str(getattr(pair, row_key))
        column = str(getattr(pair, column_key))
        matrix.setdefault(row, {})[column] = matrix.setdefault(row, {}).get(column, 0) + 1
    return {row: dict(sorted(values.items())) for row, values in sorted(matrix.items())}


def confounding_audit(pairs: list[PairSpec]) -> dict[str, Any]:
    family_route = _matrix(pairs, "intervention_family", "route_requirement_intervention")
    normalised = {
        family: {route: family_route.get(family, {}).get(route, 0) for route in ROUTES}
        for family in FAMILIES
    }
    routes_per_family = {family: sum(1 for value in row.values() if value) for family, row in normalised.items()}
    families_per_route = {
        route: sum(1 for family in FAMILIES if normalised[family][route]) for route in ROUTES
    }
    domain_family = _matrix(pairs, "domain", "intervention_family")
    difficulty_family = _matrix(pairs, "difficulty", "intervention_family")
    archetype_family = _matrix(pairs, "task_archetype", "intervention_family")
    route_difficulty = _matrix(pairs, "route_requirement_intervention", "difficulty")
    checks = {
        "matches_frozen_target_matrix": normalised == TARGET_FAMILY_ROUTE_MATRIX,
        "no_family_maps_to_exactly_one_route": all(value >= 2 for value in routes_per_family.values()),
        "no_route_confined_to_one_family": all(value >= 2 for value in families_per_route.values()),
        "no_domain_confined_to_one_family": all(len(row) >= 2 for row in domain_family.values()),
        "no_difficulty_confined_to_one_family": all(
            len(row) >= 2 for row in difficulty_family.values()
        ),
        "every_family_spans_three_difficulties": all(
            len({pair.difficulty for pair in pairs if pair.intervention_family == family}) >= 3
            for family in FAMILIES
        ),
        "every_family_spans_three_domains": all(
            len({pair.domain for pair in pairs if pair.intervention_family == family}) >= 3
            for family in FAMILIES
        ),
        "every_route_spans_two_difficulties": all(len(row) >= 2 for row in route_difficulty.values()),
    }
    return {
        "family_route_matrix": normalised,
        "routes_per_family": routes_per_family,
        "families_per_route": families_per_route,
        "domain_family_matrix": domain_family,
        "difficulty_family_matrix": difficulty_family,
        "archetype_family_matrix": archetype_family,
        "route_difficulty_matrix": route_difficulty,
        "checks": checks,
        "passed": all(checks.values()),
    }


def design_audit(pairs: list[PairSpec]) -> dict[str, Any]:
    composition = composition_audit(pairs)
    diversity = semantic_diversity_audit(pairs)
    anchors = anchor_audit(pairs)
    confounding = confounding_audit(pairs)
    passed = all(row["passed"] for row in (composition, diversity, anchors, confounding))
    return {
        "schema_version": "cab_review_ready_v2_design_audit_v1",
        "status": "CAB_SEMANTIC_DIVERSITY_VALIDATED" if passed else "CAB_DESIGN_AUDIT_FAILED",
        "objective_catalog_size": len(OBJECTIVES),
        "composition": composition,
        "semantic_diversity": diversity,
        "anchors": anchors,
        "confounding": confounding,
        "passed": passed,
    }


__all__ = [
    "anchor_audit",
    "composition_audit",
    "confounding_audit",
    "design_audit",
    "gold_derivation_signature",
    "jaccard",
    "objective_signature",
    "required_operation_signature",
    "semantic_diversity_audit",
    "shingles",
    "structural_schema_signature",
]
