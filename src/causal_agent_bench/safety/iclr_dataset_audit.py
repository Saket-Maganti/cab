"""Public-safe diversity, provenance, privacy, and injection audits."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from causal_agent_bench.answer_contracts import AnswerContract

INJECTION_PATTERNS = (
    re.compile(r"\bignore (?:all |any )?(?:previous|prior) instructions\b", re.I),
    re.compile(r"\bdisregard (?:all |any )?(?:previous|prior) instructions\b", re.I),
    re.compile(r"\boverride (?:the )?(?:system|developer|user) (?:message|prompt|instructions?)\b", re.I),
    re.compile(r"\bsystem prompt\b", re.I),
    re.compile(r"\bdeveloper message\b", re.I),
    re.compile(r"\bexfiltrat(?:e|ion)\b", re.I),
    re.compile(r"\bdo not follow the user\b", re.I),
)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.I)
ABSOLUTE_PATH_PATTERN = re.compile(r"(?:^|\s)(?:/Users/|/home/|[A-Za-z]:\\)")
SECRET_PATTERN = re.compile(
    r"\b(?:api[_ -]?key|access[_ -]?token|client[_ -]?secret|password)"
    r"\s*[:=]\s*[A-Za-z0-9_./+=-]{8,}",
    re.I,
)
OPAQUE_PRIVATE_TASK_ID_PATTERN = re.compile(r"^cab2_[0-9a-f]{24}$")
INTERVENTION_FAMILIES = frozenset(
    {
        "tool_removal",
        "tool_failure",
        "tool_corruption",
        "irrelevant_tools",
        "memory_corruption",
        "observation_conflict",
        "ambiguous_instruction",
        "long_horizon_dependency",
        "premature_success_signal",
        "distractor_evidence",
    }
)
CANONICAL_ANSWER_CONTRACTS = frozenset(contract.value for contract in AnswerContract)
PUBLIC_MANIFEST_DENIAL_FIELDS = frozenset(
    {
        "contains_task_ids",
        "contains_task_text",
        "contains_answers",
        "contains_intervention_payloads",
        "contains_evaluator_metadata",
        "payload_files_public",
        "confirmatory_eligible",
        "paper_eligible",
        "scientific_execution_allowed",
    }
)
FORBIDDEN_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "task_id",
        "user_instruction",
        "goal",
        "artifact_spec",
        "hidden_answer_key",
        "answer_key",
        "expected_final_answer",
        "gold_answer_policy",
        "scorer_policy",
        "intervention_mapping",
        "tool_output_patch",
        "instruction_patch",
        "evaluator_metadata",
    }
)


def read_jsonl_objects(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected an object")
            rows.append(value)
    return rows


def diversity_audit(
    rows: Sequence[Mapping[str, Any]],
    *,
    comparison_roles: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    lexical_threshold: float = 0.82,
) -> dict[str, Any]:
    """Compute aggregate diversity signals without emitting task text/answers."""

    if not 0.0 < lexical_threshold <= 1.0:
        raise ValueError("lexical_threshold must be in (0, 1]")
    task_ids = [str(row.get("task_id") or "") for row in rows]
    instructions = [_instruction(row) for row in rows]
    normalized = [_normalize_instruction(value) for value in instructions]
    exact_groups = _duplicate_groups(instructions)
    normalized_groups = _duplicate_groups(normalized)
    structural = [_structural_signature(row) for row in rows]
    structural_groups = _duplicate_groups(structural)
    coarse_structural = [_coarse_structural_signature(row) for row in rows]
    coarse_structural_groups = _duplicate_groups(coarse_structural)
    answer_hashes = [
        value for row in rows if (value := _answer_hash(row)) is not None
    ]
    answer_groups = _duplicate_groups(answer_hashes)
    lexical_similarity = _lexical_similarity_summary(
        normalized,
        primary_threshold=lexical_threshold,
    )
    role_overlap: dict[str, dict[str, int]] = {}
    current_ids = {value for value in task_ids if value}
    current_instructions = {value for value in instructions if value}
    current_normalized = {value for value in normalized if value}
    current_content = {
        str(_metadata(row).get("content_hash"))
        for row in rows
        if _metadata(row).get("content_hash")
    }
    current_answers = {
        value for row in rows if (value := _answer_hash(row)) is not None
    }
    for role, reference_rows in (comparison_roles or {}).items():
        reference_ids = {
            str(row.get("task_id"))
            for row in reference_rows
            if row.get("task_id")
        }
        reference_content = {
            str(_metadata(row).get("content_hash"))
            for row in reference_rows
            if _metadata(row).get("content_hash")
        }
        reference_instructions = {
            value
            for row in reference_rows
            if (value := _instruction(row))
        }
        reference_normalized = {
            _normalize_instruction(value) for value in reference_instructions
        }
        reference_answers = {
            value
            for row in reference_rows
            if (value := _answer_hash(row)) is not None
        }
        role_overlap[str(role)] = {
            "task_id_overlap": len(current_ids & reference_ids),
            "content_hash_overlap": len(current_content & reference_content),
            "exact_instruction_overlap": len(
                current_instructions & reference_instructions
            ),
            "normalized_instruction_overlap": len(
                current_normalized & reference_normalized
            ),
            "answer_hash_overlap": len(current_answers & reference_answers),
            "lexical_near_duplicate_pair_count": _cross_near_duplicate_count(
                normalized,
                [_normalize_instruction(value) for value in reference_instructions],
                lexical_threshold,
            ),
        }
    domains = Counter(str(row.get("domain") or "unknown") for row in rows)
    difficulties = Counter(str(row.get("difficulty") or "unknown") for row in rows)
    contracts = Counter(str(row.get("answer_contract") or "unknown") for row in rows)
    noncanonical_contract_count = sum(
        count
        for contract, count in contracts.items()
        if contract not in CANONICAL_ANSWER_CONTRACTS
    )
    sources = Counter(
        str(_metadata(row).get("source") or _metadata(row).get("provenance") or "unknown")
        for row in rows
    )
    tool_combinations = Counter(
        "+".join(sorted(str(tool) for tool in row.get("available_tools", [])))
        for row in rows
    )
    task_styles = Counter(str(_metadata(row).get("task_style") or "unknown") for row in rows)
    intervention_families: Counter[str] = Counter()
    manipulation_check_count = 0
    missing_manipulation_check_count = 0
    for row in rows:
        for intervention in _intervention_mappings(row):
            intervention_families[
                str(intervention.get("family") or "unknown")
            ] += 1
            check = intervention.get("manipulation_check")
            if (
                isinstance(check, Mapping)
                and check.get("check_id")
                and check.get("criterion")
                and check.get("human_confirmation_required") is True
            ):
                manipulation_check_count += 1
            else:
                missing_manipulation_check_count += 1
    role_overlap_count = sum(
        sum(values.values())
        for values in role_overlap.values()
    )
    template_ids = {
        str(_metadata(row).get("template_id"))
        for row in rows
        if _metadata(row).get("template_id")
    }
    scenario_ids = {
        str(_metadata(row).get("scenario_id"))
        for row in rows
        if _metadata(row).get("scenario_id")
    }
    content_hashes = [
        str(_metadata(row).get("content_hash"))
        for row in rows
        if _metadata(row).get("content_hash")
    ]
    return {
        "schema_version": "cab_iclr_diversity_audit_v1",
        "raw_task_count": len(rows),
        "unique_task_id_count": len(current_ids),
        "unique_template_id_count": len(template_ids),
        "template_id_missing_count": sum(
            not bool(_metadata(row).get("template_id")) for row in rows
        ),
        "unique_scenario_id_count": len(scenario_ids),
        "unique_workflow_class_count": len(
            {str(row.get("workflow_class")) for row in rows if row.get("workflow_class")}
        ),
        "normalized_instruction_pattern_count": len(set(normalized)),
        "genuinely_distinct_lower_bound": min(
            len(current_ids),
            len(set(normalized)),
            len(set(structural)),
        ),
        "domain_counts": dict(sorted(domains.items())),
        "difficulty_counts": dict(sorted(difficulties.items())),
        "tool_combination_count": len(tool_combinations),
        "answer_contract_counts": dict(sorted(contracts.items())),
        "canonical_answer_contract_count": len(
            set(contracts) & CANONICAL_ANSWER_CONTRACTS
        ),
        "noncanonical_answer_contract_task_count": noncanonical_contract_count,
        "source_type_counts": dict(sorted(sources.items())),
        "task_style_counts": dict(sorted(task_styles.items())),
        "intervention_family_counts": dict(sorted(intervention_families.items())),
        "manipulation_check_count": manipulation_check_count,
        "missing_manipulation_check_count": missing_manipulation_check_count,
        "content_hash_count": len(content_hashes),
        "unique_content_hash_count": len(set(content_hashes)),
        "exact_duplicate_group_count": len(exact_groups),
        "exact_duplicate_task_count": sum(len(group) for group in exact_groups),
        "normalized_duplicate_group_count": len(normalized_groups),
        "structural_duplicate_group_count": len(structural_groups),
        "coarse_structural_archetype_count": len(set(coarse_structural)),
        "coarse_structural_duplicate_group_count": len(coarse_structural_groups),
        "coarse_structural_duplicate_task_count": sum(
            len(group) for group in coarse_structural_groups
        ),
        "lexical_near_duplicate_pair_count": lexical_similarity[
            "primary_threshold_pair_count"
        ],
        "lexical_similarity_summary": lexical_similarity,
        "lexical_threshold": lexical_threshold,
        "answer_overlap_group_count": len(answer_groups),
        "role_overlap": role_overlap,
        "role_overlap_signal_count": role_overlap_count,
        "template_variant_risk": (
            "not_assessable_missing_template_ids"
            if not template_ids
            else
            "high"
            if len(rows) / len(template_ids) >= 4
            else "moderate"
            if len(rows) / len(template_ids) >= 2
            else "low"
        ),
        "human_validation_complete": False,
        "confirmatory_ready": False,
        "paper_eligible": False,
        "evidence_class": "ENGINEERING_ONLY",
    }


def naturalistic_safety_audit(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Audit aggregate naturalistic provenance/privacy/injection requirements."""

    missing_provenance = 0
    missing_licence = 0
    missing_privacy = 0
    missing_injection_requirement = 0
    missing_answer_isolation = 0
    injection_matches = 0
    non_example_email_matches = 0
    absolute_path_matches = 0
    secret_matches = 0
    label_revealing_ids = 0
    nonopaque_task_ids = 0
    visible_hidden_field_declarations = 0
    provenance_counts: Counter[str] = Counter()
    licence_counts: Counter[str] = Counter()
    artifact_counts: Counter[str] = Counter()
    for row in rows:
        metadata = _metadata(row)
        provenance = str(metadata.get("provenance") or metadata.get("source") or "")
        licence = str(metadata.get("license") or "")
        privacy = str(metadata.get("privacy_review") or metadata.get("pii_policy") or "")
        visible_text = _visible_text(row)
        task_id = str(row.get("task_id") or "").lower()
        if not provenance:
            missing_provenance += 1
        else:
            provenance_counts[provenance] += 1
        if not licence:
            missing_licence += 1
        else:
            licence_counts[licence] += 1
        if not privacy:
            missing_privacy += 1
        if metadata.get("injection_scan_required") is not True:
            missing_injection_requirement += 1
        if metadata.get("answer_key_isolated_from_agent_payload") is not True:
            missing_answer_isolation += 1
        artifact_counts[str(metadata.get("artifact_type") or "unknown")] += 1
        injection_matches += sum(
            bool(pattern.search(visible_text)) for pattern in INJECTION_PATTERNS
        )
        for domain in EMAIL_PATTERN.findall(visible_text):
            if domain.lower() not in {"example.com", "example.org", "example.net"}:
                non_example_email_matches += 1
        absolute_path_matches += int(bool(ABSOLUTE_PATH_PATTERN.search(visible_text)))
        secret_matches += int(bool(SECRET_PATTERN.search(visible_text)))
        label_revealing_ids += int(
            any(family in task_id for family in INTERVENTION_FAMILIES)
        )
        nonopaque_task_ids += int(not bool(OPAQUE_PRIVATE_TASK_ID_PATTERN.fullmatch(task_id)))
        visible_fields = metadata.get("visible_context_fields")
        if isinstance(visible_fields, Sequence) and not isinstance(
            visible_fields, (str, bytes)
        ):
            visible_hidden_field_declarations += int(
                bool(
                    {
                        "hidden_answer_key",
                        "intervention_mapping",
                        "gold_answer_policy",
                        "scorer_policy",
                    }
                    & {str(value) for value in visible_fields}
                )
            )
    blockers = {
        "missing_provenance": missing_provenance,
        "missing_licence": missing_licence,
        "missing_privacy_policy": missing_privacy,
        "missing_injection_scan_requirement": missing_injection_requirement,
        "missing_answer_isolation_attestation": missing_answer_isolation,
        "prompt_injection_match_count": injection_matches,
        "non_example_email_match_count": non_example_email_matches,
        "absolute_path_match_count": absolute_path_matches,
        "secret_pattern_match_count": secret_matches,
        "label_revealing_task_id_count": label_revealing_ids,
        "nonopaque_task_id_count": nonopaque_task_ids,
        "visible_hidden_field_declaration_count": visible_hidden_field_declarations,
    }
    return {
        "schema_version": "cab_naturalistic_safety_audit_v1",
        "task_count": len(rows),
        "provenance_counts": dict(sorted(provenance_counts.items())),
        "licence_counts": dict(sorted(licence_counts.items())),
        "artifact_type_counts": dict(sorted(artifact_counts.items())),
        "artifact_type_count": len(artifact_counts),
        "blocker_counts": blockers,
        "static_passed": not any(blockers.values()),
        "privacy_human_review_required": True,
        "injection_human_review_required": True,
        "answer_contract_human_review_required": True,
        "confirmatory_ready": False,
        "paper_eligible": False,
        "evidence_class": "ENGINEERING_ONLY",
    }


def public_safe_manifest(
    *,
    dataset_id: str,
    files: Sequence[str | Path],
    diversity: Mapping[str, Any],
    safety: Mapping[str, Any] | None,
    scientific_disposition: str,
    private_payload_root: str,
) -> dict[str, Any]:
    """Build a public aggregate manifest with no IDs, prompts, or answers."""

    file_records = []
    for value in files:
        path = Path(value)
        if not path.exists():
            continue
        file_records.append(
            {
                "role": path.name,
                "sha256": _sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    allowed_diversity = {
        key: diversity.get(key)
        for key in (
            "raw_task_count",
            "unique_task_id_count",
            "unique_template_id_count",
            "template_id_missing_count",
            "unique_scenario_id_count",
            "unique_workflow_class_count",
            "normalized_instruction_pattern_count",
            "genuinely_distinct_lower_bound",
            "domain_counts",
            "difficulty_counts",
            "tool_combination_count",
            "answer_contract_counts",
            "canonical_answer_contract_count",
            "noncanonical_answer_contract_task_count",
            "source_type_counts",
            "task_style_counts",
            "intervention_family_counts",
            "manipulation_check_count",
            "missing_manipulation_check_count",
            "content_hash_count",
            "unique_content_hash_count",
            "exact_duplicate_group_count",
            "normalized_duplicate_group_count",
            "structural_duplicate_group_count",
            "coarse_structural_archetype_count",
            "coarse_structural_duplicate_group_count",
            "coarse_structural_duplicate_task_count",
            "lexical_near_duplicate_pair_count",
            "lexical_similarity_summary",
            "answer_overlap_group_count",
            "role_overlap",
            "role_overlap_signal_count",
            "template_variant_risk",
        )
    }
    private_payload_commitment = hashlib.sha256(
        json.dumps(
            file_records,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    base_task_commitment = next(
        (
            str(record["sha256"])
            for record in file_records
            if record["role"] == "candidate_tasks.jsonl"
        ),
        None,
    )
    return {
        "schema_version": "cab_public_safe_candidate_manifest_v1",
        "dataset_id": dataset_id,
        "scientific_disposition": scientific_disposition,
        "confirmatory_eligible": False,
        "human_validation_state": "HUMAN_INPUT_REQUIRED",
        "private_payload_root": private_payload_root,
        "private_payload_root_must_be_ignored": True,
        "payload_files_public": False,
        "contains_task_ids": False,
        "contains_task_text": False,
        "contains_answers": False,
        "contains_intervention_payloads": False,
        "contains_evaluator_metadata": False,
        "aggregate_diversity": allowed_diversity,
        "aggregate_safety": (
            {
                "task_count": safety.get("task_count"),
                "artifact_type_count": safety.get("artifact_type_count"),
                "blocker_counts": safety.get("blocker_counts"),
                "static_passed": safety.get("static_passed"),
            }
            if safety is not None
            else None
        ),
        "private_file_commitments": file_records,
        "commitments": {
            "algorithm": "SHA-256",
            "base_task_payload_commitment_sha256": base_task_commitment,
            "private_payload_commitment_sha256": private_payload_commitment,
        },
        "paper_eligible": False,
        "scientific_execution_allowed": False,
        "evidence_class": "HUMAN_INPUT_REQUIRED",
    }


def _instruction(row: Mapping[str, Any]) -> str:
    direct = row.get("user_instruction")
    if direct:
        return str(direct)
    goal = row.get("goal")
    if isinstance(goal, Mapping):
        return str(goal.get("user_instruction") or "")
    return ""


def _metadata(row: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, Mapping) else {}


def _visible_text(row: Mapping[str, Any]) -> str:
    metadata = _metadata(row)
    declared = metadata.get("visible_context_fields")
    if isinstance(declared, Sequence) and not isinstance(declared, (str, bytes)):
        fields = [str(value) for value in declared]
    else:
        fields = ["user_instruction", "artifact_spec", "answer_contract", "tool_schema"]
    visible = {field: row.get(field) for field in fields if field in row}
    return json.dumps(visible, sort_keys=True, ensure_ascii=False)


def _normalize_instruction(text: str) -> str:
    normalized = text.lower()
    normalized = EMAIL_PATTERN.sub("<email>", normalized)
    normalized = re.sub(r"\b\d+(?:[.:/-]\d+)*\b", "<num>", normalized)
    normalized = re.sub(r"\b(?:variant|artifact|ticket|case|record)\s*[-:#]?\s*<num>\b", "<id>", normalized)
    normalized = re.sub(r"[^a-z<>]+", " ", normalized)
    return " ".join(normalized.split())


def _structural_signature(row: Mapping[str, Any]) -> str:
    metadata = _metadata(row)
    schema = row.get("expected_output_schema")
    schema_keys: list[str] = []
    if isinstance(schema, Mapping):
        properties = schema.get("properties")
        if isinstance(properties, Mapping):
            schema_keys = sorted(str(key) for key in properties)
    payload = {
        "domain": row.get("domain"),
        "template": (
            metadata.get("template_id")
            or metadata.get("scenario_id")
            or row.get("workflow_class")
        ),
        "workflow_class": row.get("workflow_class"),
        "artifact_type": (
            metadata.get("artifact_type")
            or (
                row.get("artifact_spec", {}).get("artifact_type")
                if isinstance(row.get("artifact_spec"), Mapping)
                else None
            )
        ),
        "tools": sorted(str(tool) for tool in row.get("available_tools", [])),
        "required_tools": sorted(str(tool) for tool in row.get("required_tools", [])),
        "answer_contract": row.get("answer_contract"),
        "schema_keys": schema_keys,
        "criteria_count": len(row.get("success_criteria", [])),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _coarse_structural_signature(row: Mapping[str, Any]) -> str:
    metadata = _metadata(row)
    artifact_spec = row.get("artifact_spec")
    artifact_type = metadata.get("artifact_type")
    if not artifact_type and isinstance(artifact_spec, Mapping):
        artifact_type = artifact_spec.get("artifact_type")
    payload = {
        "domain": row.get("domain"),
        "artifact_class": _normalize_identifier(str(artifact_type or "")),
        "tools": sorted(str(tool) for tool in row.get("available_tools", [])),
        "required_tools": sorted(str(tool) for tool in row.get("required_tools", [])),
        "answer_contract": row.get("answer_contract"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _normalize_identifier(value: str) -> str:
    value = value.lower()
    value = re.sub(r"\d+", "<num>", value)
    return re.sub(
        r"(?:_|-)(?:variant|bundle|case|record|task)?_?<num>$",
        "",
        value,
    )


def _answer_hash(row: Mapping[str, Any]) -> str | None:
    goal = row.get("goal")
    answer: Any = None
    if isinstance(goal, Mapping):
        answer = goal.get("expected_final_answer")
    if answer is None:
        policy = row.get("gold_answer_policy")
        if isinstance(policy, Mapping):
            answer = policy.get("expected")
    if answer is None:
        answer = row.get("hidden_answer_key")
    if answer is None:
        return None
    return hashlib.sha256(
        json.dumps(answer, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _intervention_mappings(
    row: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    value = row.get("intervention_mapping")
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _duplicate_groups(values: Sequence[str]) -> list[list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for index, value in enumerate(values):
        groups[value].append(index)
    return [indices for indices in groups.values() if len(indices) > 1]


def _near_duplicate_count(values: Sequence[str], threshold: float) -> int:
    token_sets = [set(value.split()) for value in values]
    count = 0
    for left in range(len(token_sets)):
        for right in range(left + 1, len(token_sets)):
            union = token_sets[left] | token_sets[right]
            similarity = (
                len(token_sets[left] & token_sets[right]) / len(union)
                if union
                else 1.0
            )
            if similarity >= threshold and values[left] != values[right]:
                count += 1
    return count


def _cross_near_duplicate_count(
    left_values: Sequence[str],
    right_values: Sequence[str],
    threshold: float,
) -> int:
    left_sets = [set(value.split()) for value in left_values if value]
    right_sets = [set(value.split()) for value in right_values if value]
    count = 0
    for left_value in left_sets:
        for right_value in right_sets:
            union = left_value | right_value
            similarity = (
                len(left_value & right_value) / len(union) if union else 1.0
            )
            if similarity >= threshold:
                count += 1
    return count


def _lexical_similarity_summary(
    values: Sequence[str],
    *,
    primary_threshold: float,
) -> dict[str, Any]:
    token_sets = [set(value.split()) for value in values]
    similarities: list[float] = []
    for left in range(len(token_sets)):
        for right in range(left + 1, len(token_sets)):
            union = token_sets[left] | token_sets[right]
            similarity = (
                len(token_sets[left] & token_sets[right]) / len(union)
                if union
                else 1.0
            )
            if values[left] != values[right]:
                similarities.append(similarity)
    ordered = sorted(similarities)
    return {
        "pair_count": len(ordered),
        "primary_threshold": primary_threshold,
        "primary_threshold_pair_count": sum(
            value >= primary_threshold for value in ordered
        ),
        "threshold_pair_counts": {
            f"{threshold:.2f}": sum(value >= threshold for value in ordered)
            for threshold in (0.70, 0.75, 0.82, 0.90)
        },
        "median_similarity": (
            round(ordered[len(ordered) // 2], 6) if ordered else None
        ),
        "p95_similarity": (
            round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 6)
            if ordered
            else None
        ),
        "maximum_similarity": round(ordered[-1], 6) if ordered else None,
    }


def public_manifest_payload_issues(
    manifest: Mapping[str, Any],
    *,
    private_rows: Sequence[Mapping[str, Any]] = (),
) -> list[str]:
    """Return leak-safe issue codes for a public candidate manifest."""

    issues: list[str] = []
    for field in sorted(PUBLIC_MANIFEST_DENIAL_FIELDS):
        if manifest.get(field) is not False:
            issues.append(f"denial_field_not_false:{field}")
    if manifest.get("human_validation_state") != "HUMAN_INPUT_REQUIRED":
        issues.append("human_validation_state_not_pending")
    if manifest.get("private_payload_root_must_be_ignored") is not True:
        issues.append("private_payload_ignore_requirement_missing")
    serialized = json.dumps(manifest, sort_keys=True, ensure_ascii=False)
    if ABSOLUTE_PATH_PATTERN.search(serialized):
        issues.append("absolute_private_path_present")
    for path, value in _walk_json(manifest):
        if path and path[-1] in FORBIDDEN_PUBLIC_PAYLOAD_KEYS:
            issues.append(f"forbidden_payload_key:{path[-1]}")
        if isinstance(value, str) and value.startswith(("data:", "base64:")):
            issues.append("reversible_encoding_marker_present")
    for row in private_rows:
        task_id = str(row.get("task_id") or "")
        instruction = _instruction(row)
        answer = row.get("hidden_answer_key")
        if task_id and task_id in serialized:
            issues.append("private_task_id_present")
        if instruction and instruction in serialized:
            issues.append("private_instruction_present")
        if answer is not None:
            answer_text = json.dumps(
                answer,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            if answer_text and answer_text in serialized:
                issues.append("private_answer_present")
    return sorted(set(issues))


def _walk_json(
    value: Any,
    path: tuple[str, ...] = (),
) -> list[tuple[tuple[str, ...], Any]]:
    rows = [(path, value)]
    if isinstance(value, Mapping):
        for key, item in value.items():
            rows.extend(_walk_json(item, (*path, str(key))))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            rows.extend(_walk_json(item, (*path, str(index))))
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
