"""Fail-closed Stage-1 leakage audit.

The scanner extracts every Stage-1 archive in memory and compares its filenames,
archive metadata and file contents against the private Stage-2 material.  It
reports aggregate counts and package hashes only; leaked values are never
printed, logged, or written to any report.
"""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any

from causal_agent_bench.review_ready_v2.common import flatten, sha256_bytes
from causal_agent_bench.review_ready_v2.models import PRIVATE_PAIR_FIELDS, PairSpec

FORBIDDEN_STRUCTURAL_KEYS = frozenset(
    {
        *PRIVATE_PAIR_FIELDS,
        "abstention_opportunity",
        "accepted_variants",
        "answer_contract",
        "authorized_action_id",
        "authorization_scope",
        "base_task_id",
        "clarification_requirement",
        "clean_gold",
        "clean_instance_id",
        "expected_answer",
        "expected_response_type",
        "fallback_tool",
        "gold",
        "intervention_gold",
        "intervention_instance_id",
        "pair_id",
        "recovery_authorization",
        "route_kind",
        "route_requirement",
        "scorer_contract",
        "scorer_id",
        "stage2",
    }
)

FORBIDDEN_TOKENS = (
    "abstain",
    "authorization_scope",
    "abstention",
    "answer_key",
    "clarification_required",
    "clean_gold",
    "expected_answer",
    "gold_answer",
    "must_reference_input_key",
    "recovery_only",
    "route_kind",
    "scorer",
    "stage2",
    "stage_2",
)

UNSAFE_PATH_MARKERS = ("..", "/", "\\", ":")


def _extract(payload: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        return {info.filename: archive.read(info) for info in archive.infolist()}


def _archive_metadata(payload: bytes) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        return [
            {
                "name": info.filename,
                "date_time": list(info.date_time),
                "comment": info.comment.decode(errors="replace"),
                "extra_len": len(info.extra),
                "is_dir": info.is_dir(),
            }
            for info in archive.infolist()
        ]


def _structural_keys(payload: bytes) -> set[str]:
    import json

    try:
        parsed = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        return set()

    def walk(value: Any) -> set[str]:
        found: set[str] = set()
        if isinstance(value, dict):
            for key, child in value.items():
                found.add(str(key).casefold())
                found |= walk(child)
        elif isinstance(value, list):
            for child in value:
                found |= walk(child)
        return found

    return walk(parsed)


def _word_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_.:\-]+", text.casefold()))


def permitted_vocabulary(pair: PairSpec) -> set[str]:
    """Strings a Stage-1 item may legitimately contain for this pair.

    Evidence leaves, tool vocabulary and the prompt's own answer-format tokens
    are not secrets: concealing them would mean concealing the task.
    """

    tokens: set[str] = set()
    for state in (pair.clean_environment, pair.intervention_environment):
        tokens |= {str(leaf).casefold() for _, leaf in flatten(state.sources)}
        tokens |= {str(leaf).casefold() for _, leaf in flatten(state.memory)}
        for contract in state.tools:
            tokens.add(contract.tool_id.casefold())
            tokens.add(contract.scope_source.casefold())
            tokens |= {value.casefold() for value in contract.provides_inputs}
            tokens |= {value.casefold() for value in contract.returned_fields}
    tokens |= _word_tokens(pair.clean_prompt)
    tokens |= _word_tokens(pair.shared_goal)
    return tokens


def pair_secrets(pair: PairSpec) -> tuple[set[str], set[str]]:
    """Return ``(archive_wide_secrets, per_item_derived_components)``."""

    permitted = permitted_vocabulary(pair)
    strong = {
        pair.clean_gold_private,
        pair.intervention_gold_or_policy_private,
        pair.pair_id,
        pair.base_task_id,
        pair.clean_instance_id,
        pair.intervention_instance_id,
    }
    for private in (
        pair.recovery_authorization_private,
        pair.abstention_opportunity_private,
        pair.clarification_requirement_private,
    ):
        if not private:
            continue
        for _, leaf in flatten(private):
            if not isinstance(leaf, str):
                continue
            # Opaque authorization ids are secrets; identifiers and input-key names
            # are shared structural vocabulary and legitimately appear in Stage 1.
            if leaf.startswith("recover-") or (len(leaf) >= 24 and " " in leaf and leaf.casefold() not in permitted):
                strong.add(leaf)
    derived = {
        component
        for gold in (pair.clean_gold_private, pair.intervention_gold_or_policy_private)
        for component in gold.split("|")
        if component and component.casefold() not in permitted
    }
    return {value for value in strong if value}, derived


def stage2_secrets(pairs: list[PairSpec]) -> dict[str, list[str]]:
    strong: set[str] = set()
    derived: set[str] = set()
    for pair in pairs:
        pair_strong, pair_derived = pair_secrets(pair)
        strong |= pair_strong
        derived |= pair_derived
    return {"archive_wide": sorted(strong), "per_item_derived": sorted(derived)}


def scan_stage1_archive(
    payload: bytes,
    pairs: list[PairSpec],
    *,
    label: str,
    mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    files = _extract(payload)
    metadata = _archive_metadata(payload)
    blob = b"\n".join(files[name] for name in sorted(files)).lower()
    names_blob = "\n".join(sorted(files)).casefold()

    structural_hits = sorted(
        {
            key
            for name in files
            if name.endswith(".json")
            for key in _structural_keys(files[name])
            if key in FORBIDDEN_STRUCTURAL_KEYS
        }
    )
    token_hits = sorted({token for token in FORBIDDEN_TOKENS if token.encode() in blob})

    by_pair_id = {pair.pair_id: pair for pair in pairs}
    archive_wide: set[str] = set()
    for pair in pairs:
        archive_wide |= pair_secrets(pair)[0]
    archive_hits = sum(1 for value in archive_wide if value.casefold().encode() in blob)
    name_hits = sum(1 for value in archive_wide if value.casefold() in names_blob)

    item_hits = 0
    items_scanned = 0
    for reviewer_item_id, pair_id in sorted((mapping or {}).items()):
        item_path = f"items/{reviewer_item_id}.json"
        scanned_pair = by_pair_id.get(pair_id)
        if scanned_pair is None or item_path not in files:
            continue
        items_scanned += 1
        item_tokens = _word_tokens(files[item_path].decode())
        item_hits += sum(
            1 for component in pair_secrets(scanned_pair)[1] if component.casefold() in item_tokens
        )

    unsafe_paths = sorted(
        name
        for name in files
        if name.startswith("/")
        or ".." in name.split("/")
        or "\\" in name
        or name.rsplit("/", 1)[-1].startswith(".")
    )
    nonzero_metadata = [
        row
        for row in metadata
        if row["comment"] or row["extra_len"] or row["date_time"] != [1980, 1, 1, 0, 0, 0]
    ]
    checks = {
        "no_forbidden_structural_keys": not structural_hits,
        "no_forbidden_tokens": not token_hits,
        "no_archive_wide_stage2_value_present": archive_hits == 0,
        "no_derived_gold_component_in_its_own_item": item_hits == 0,
        "no_stage2_value_in_a_filename": name_hits == 0,
        "no_unsafe_or_hidden_paths": not unsafe_paths,
        "archive_metadata_normalised": not nonzero_metadata,
        "no_reference_key_file": not any("answer" in name.casefold() for name in files),
        "no_source_code_shipped": not any(name.endswith((".py", ".pyc", ".so")) for name in files),
    }
    return {
        "package": label,
        "sha256": sha256_bytes(payload),
        "file_count": len(files),
        "byte_size": len(payload),
        "items_value_scanned": items_scanned,
        "forbidden_structural_key_count": len(structural_hits),
        "forbidden_token_count": len(token_hits),
        "archive_wide_hit_count": archive_hits,
        "per_item_derived_hit_count": item_hits,
        "filename_hit_count": name_hits,
        "unsafe_path_count": len(unsafe_paths),
        "checks": checks,
        "passed": all(checks.values()),
    }


def stage1_leakage_audit(
    packages: dict[str, bytes],
    pairs: list[PairSpec],
    mappings: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    rows = [
        scan_stage1_archive(
            payload, pairs, label=label, mapping=(mappings or {}).get(label)
        )
        for label, payload in sorted(packages.items())
    ]
    passed = bool(rows) and all(row["passed"] for row in rows)
    secrets = stage2_secrets(pairs)
    return {
        "schema_version": "cab_review_ready_v2_stage1_leakage_audit_v1",
        "status": "CAB_STAGE1_LEAKAGE_AUDIT_PASSED" if passed else "CAB_STAGE1_LEAKAGE_AUDIT_FAILED",
        "package_count": len(rows),
        "archive_wide_secret_count": len(secrets["archive_wide"]),
        "per_item_derived_secret_count": len(secrets["per_item_derived"]),
        "packages": rows,
        "leaked_values_are_never_printed": True,
        "passed": passed,
    }


def usability_audit(packages: dict[str, bytes]) -> dict[str, Any]:
    """Automated package usability checks. No human review is performed here."""

    rows: list[dict[str, Any]] = []
    orders: dict[str, list[str]] = {}
    for label, payload in sorted(packages.items()):
        files = _extract(payload)
        manifest_bytes = files.get("manifest.json", b"{}")
        import json

        manifest = json.loads(manifest_bytes)
        items = manifest.get("items", [])
        item_ids = [str(row["reviewer_item_id"]) for row in items]
        orders[label] = item_ids
        form = files.get("review_form.csv", files.get("qualification_form.csv", b"")).decode()
        form_rows = [line for line in form.strip().splitlines()[1:] if line.strip()]
        checks = {
            "manifest_present": "manifest.json" in files,
            "instructions_present": any(name.endswith("INSTRUCTIONS.md") for name in files),
            # Stage-1 packages still ship the free-text conflict form; qualification
            # packages ship the structured declaration the coordinator ingests.
            # Either satisfies the requirement that a reviewer is asked to declare.
            "conflict_declaration_present": "CONFLICT_OF_INTEREST.md" in files
            or "reviewer_declaration.json" in files,
            "form_present": bool(form),
            "every_referenced_file_exists": all(str(row["item_path"]) in files for row in items),
            "one_form_row_per_item": len(form_rows) == len(items),
            "form_rows_match_item_ids": [line.split(",")[0] for line in form_rows] == item_ids,
            "opaque_ids_unique": len(set(item_ids)) == len(item_ids),
            "items_parse_as_json": all(
                _parses(files[str(row["item_path"])]) for row in items if str(row["item_path"]) in files
            ),
            "no_private_manifest_shipped": "private_manifest.json" not in files,
            "package_size_reasonable": len(payload) < 4_000_000,
        }
        rows.append(
            {
                "package": label,
                "sha256": sha256_bytes(payload),
                "item_count": len(items),
                "checks": checks,
                "passed": all(checks.values()),
            }
        )
    reviewer_orders = [order for label, order in sorted(orders.items()) if label.startswith("stage1_reviewer")]
    independent = (
        len(reviewer_orders) < 2
        or len({tuple(order) for order in reviewer_orders}) == len(reviewer_orders)
    )
    passed = all(row["passed"] for row in rows) and independent
    return {
        "schema_version": "cab_review_ready_v2_usability_audit_v1",
        "status": "CAB_STAGE1_USABILITY_CHECKS_PASSED" if passed else "CAB_STAGE1_USABILITY_CHECKS_FAILED",
        "reviewer_orders_independent": independent,
        "packages": rows,
        "human_pilot_performed": False,
        "passed": passed,
    }


def _parses(payload: bytes) -> bool:
    import json

    try:
        json.loads(payload)
    except ValueError:
        return False
    return True


def package_digest(packages: dict[str, bytes]) -> dict[str, str]:
    return {label: sha256_bytes(payload) for label, payload in sorted(packages.items())}


__all__ = [
    "FORBIDDEN_STRUCTURAL_KEYS",
    "FORBIDDEN_TOKENS",
    "UNSAFE_PATH_MARKERS",
    "package_digest",
    "pair_secrets",
    "permitted_vocabulary",
    "scan_stage1_archive",
    "stage1_leakage_audit",
    "stage2_secrets",
    "usability_audit",
]
