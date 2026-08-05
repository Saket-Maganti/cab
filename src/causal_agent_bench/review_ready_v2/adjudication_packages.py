"""Adjudicator packages: disputed items only, with the evidence to decide them.

The disagreement queues record *that* two reviewers disagreed; they do not carry
enough of the item to settle the disagreement.  An adjudicator handed only a
queue is being asked to arbitrate from the parties' assertions alone, which is
not adjudication.  These packages carry the evidence, and only for the disputed
items:

Stage 1 — the clean and intervention task context, the primitive evidence, the
controlled difference with its intended changed factor, the claimed preserved
invariants, the declared tool capabilities, and both reviewers' values,
confidence and notes.  Stage-2 gold, contracts, scorer material and route policy
are withheld exactly as they are from a Stage-1 reviewer.

Stage 2 — the withheld material that is actually in dispute: gold and policy,
accepted variants, the answer and scorer contracts, the applicability map, the
recovery, abstention and clarification policies where they exist, and both
reviewers' values, confidence and notes.

Neither package contains a single non-disputed item, and each is bound to the
packet commitment, the stage, the disagreement-queue hash, the disputed item ids,
the adjudicator's assignment, the scientific freeze, the exact commit, and its
own archive hash.  Adjudication cannot be ingested against any other package.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.adjudication import (
    REQUIRED_DECISION_FIELDS,
    STAGE1,
    STAGE2,
)
from causal_agent_bench.review_ready_v2.common import canonical_bytes, sha256_bytes, sha256_json
from causal_agent_bench.review_ready_v2.stage1 import zip_bytes

STAGE1_PACKAGE_SCHEMA_VERSION = "cab_stage1_adjudicator_package_v1"
STAGE2_PACKAGE_SCHEMA_VERSION = "cab_stage2_adjudicator_package_v1"
BINDING_SCHEMA_VERSION = "cab_adjudicator_package_binding_v1"

PACKAGE_FILENAMES: dict[str, str] = {
    STAGE1: "stage1_adjudicator_package.zip",
    STAGE2: "stage2_adjudicator_package.zip",
}

#: Everything each package is permanently bound to.  ``package_sha256`` cannot
#: live inside the archive it hashes, so it is carried by the sealed receipt.
BINDING_FIELDS: tuple[str, ...] = (
    "private_packet_commitment",
    "stage",
    "disagreement_queue_sha256",
    "disputed_pair_ids",
    "adjudicator_assignment_sha256",
    "adjudicator_pseudonym_sha256",
    "scientific_freeze_sha256",
    "exact_commit",
)

#: Stage-2 keys that must never appear in a Stage-1 adjudicator package.
STAGE2_ONLY_KEYS: frozenset[str] = frozenset(
    {
        "abstention_opportunity",
        "accepted_variants",
        "clarification_requirement",
        "clean_answer_contract",
        "clean_gold",
        "clean_scorer_contract",
        "intervention_answer_contract",
        "intervention_gold_or_policy",
        "intervention_scorer_contract",
        "recovery_authorization",
        "route_requirement_clean",
        "route_requirement_intervention",
        "source_to_gold_rationale",
        "stage2_dimension_applicability",
    }
)

#: Stage-2 evidence an adjudicator must be given for a disputed item.
STAGE2_REQUIRED_EVIDENCE: tuple[str, ...] = (
    "clean_gold",
    "intervention_gold_or_policy",
    "clean_answer_contract",
    "intervention_answer_contract",
    "clean_scorer_contract",
    "intervention_scorer_contract",
    "route_requirement_clean",
    "route_requirement_intervention",
    "stage2_dimension_applicability",
)

#: Conditional Stage-2 policies, included only where the item actually has one.
STAGE2_CONDITIONAL_EVIDENCE: tuple[str, ...] = (
    "recovery_authorization",
    "abstention_opportunity",
    "clarification_requirement",
)


class AdjudicationPackageError(ValueError):
    """An adjudicator package could not be built, or failed its binding check."""


STAGE1_ADJUDICATOR_INSTRUCTIONS = """# CAB Stage-1 adjudication

You are adjudicating only the items on which the two independent reviewers did
not jointly accept a Stage-1 dimension. Non-disputed items are not in this
package and are not yours to revisit.

For each disputed item you are given both instances of the pair, the primitive
evidence, the controlled difference with its declared intended changed factor,
the claimed preserved invariants, the declared tool capabilities, and both
reviewers' values, confidence and notes for that dimension.

You are **not** shown the expected result, the accepted variants, the answer or
scorer contracts, or any other second-stage material. Stage 1 is about whether
the pair is a valid controlled comparison, and nothing else.

For every row in `adjudication_form.json` give either a `final_value` that
accepts under the frozen rule, or `exclude_item = YES`. There is no third
option: an unresolved objection cannot enter the benchmark. Every decision needs
a rationale, a concrete evidence reference, and a 1-5 confidence.

Work alone. Do not use any AI assistant. You must not be either reviewer.
"""

STAGE2_ADJUDICATOR_INSTRUCTIONS = """# CAB Stage-2 adjudication

You are adjudicating only the items on which the two independent reviewers did
not jointly accept a Stage-2 dimension. Non-disputed items are not in this
package.

For each disputed item you are given the withheld material itself: the expected
result and policy, the accepted variants, the answer and scorer contracts, the
route requirements, the applicability map, and the recovery, abstention or
clarification policy where the item has one. You are also given both reviewers'
values, confidence and notes.

You are judging whether that material is correct and defensible. For every row in
`adjudication_form.json` give either a `final_value` that accepts under the
frozen rule, or `exclude_item = YES`. `NOT_APPLICABLE` accepts only for a
conditional dimension the applicability map marks structurally inapplicable.
Every decision needs a rationale, a concrete evidence reference, and a 1-5
confidence.

This package contains unpublished benchmark material. Do not copy, share, quote
or upload any part of it. Delete your local copy once the coordinator confirms
receipt. Work alone, use no AI assistant, and you must not be either reviewer.
"""


def disputed_pair_ids(queue: dict[str, Any]) -> list[str]:
    """The distinct items a queue actually disputes, in stable order."""

    return sorted({str(row["pair_id"]) for row in queue.get("disputes", [])})


def _disputes_by_pair(queue: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in queue.get("disputes", []):
        grouped.setdefault(str(row["pair_id"]), []).append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: str(row["dimension"]))
    return grouped


def _reviewer_view(
    rows: dict[str, dict[str, str]], dimension: str
) -> dict[str, dict[str, str]]:
    """Both reviewers' value, confidence and notes for one disputed dimension."""

    return {
        role: {
            "value": str(row.get(dimension, "")).strip(),
            "reviewer_confidence": str(row.get("reviewer_confidence", "")).strip(),
            "notes": str(row.get("notes", "")).strip(),
        }
        for role, row in sorted(rows.items())
    }


def adjudication_form(queue: dict[str, Any]) -> list[dict[str, Any]]:
    """One prefilled-but-undecided row per disputed dimension."""

    return [
        {
            "pair_id": str(row["pair_id"]),
            "dimension": str(row["dimension"]),
            "final_value": "",
            "rationale": "",
            "evidence_reference": "",
            "confidence": "",
            "exclude_item": "NO",
        }
        for row in sorted(
            queue.get("disputes", []),
            key=lambda row: (str(row["pair_id"]), str(row["dimension"])),
        )
    ]


def package_binding(
    *,
    stage: str,
    queue: dict[str, Any],
    private_packet_commitment: str,
    adjudicator_assignment_sha256: str,
    adjudicator_pseudonym_sha256: str,
    scientific_freeze_sha256: str,
    exact_commit: str,
    stage2_issuance_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    """The identity every adjudicator package is permanently bound to."""

    if stage not in (STAGE1, STAGE2):
        raise AdjudicationPackageError(f"unknown adjudication stage {stage!r}")
    queue_hash = str(queue.get("receipt_sha256") or sha256_json(queue))
    binding: dict[str, Any] = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "stage": stage,
        "private_packet_commitment": str(private_packet_commitment),
        "disagreement_queue_schema_version": str(queue.get("schema_version", "")),
        "disagreement_queue_sha256": queue_hash,
        "disputed_pair_ids": disputed_pair_ids(queue),
        "disputed_dimension_count": int(queue.get("disputed_dimension_count", 0)),
        "adjudicator_assignment_sha256": str(adjudicator_assignment_sha256),
        "adjudicator_pseudonym_sha256": str(adjudicator_pseudonym_sha256),
        "scientific_freeze_sha256": str(scientific_freeze_sha256),
        "exact_commit": str(exact_commit),
        "stage2_issuance_hashes": dict(sorted((stage2_issuance_hashes or {}).items())),
        "non_disputed_items_included": False,
        "adjudicator_is_neither_reviewer": True,
    }
    missing = sorted(field for field in BINDING_FIELDS if not str(binding.get(field, "")).strip())
    if missing and missing != ["disputed_pair_ids"]:
        raise AdjudicationPackageError(f"the adjudicator package binding is missing {missing}")
    binding["binding_sha256"] = sha256_json(binding)
    return binding


def _common_files(
    *, stage: str, queue: dict[str, Any], binding: dict[str, Any], instructions: str
) -> dict[str, bytes]:
    return {
        "binding.json": canonical_bytes(binding) + b"\n",
        "adjudication_form.json": canonical_bytes(adjudication_form(queue)) + b"\n",
        "ADJUDICATOR_INSTRUCTIONS.md": instructions.encode(),
        "acceptance_rule.json": canonical_bytes(
            {
                "stage": stage,
                "required_decision_fields": list(REQUIRED_DECISION_FIELDS),
                "rule": (
                    "For each disputed dimension give a final value that accepts under the frozen "
                    "rule, or set exclude_item=YES. There is no third option: an unresolved "
                    "objection cannot enter the benchmark."
                ),
                "disputed_items_only": True,
            }
        )
        + b"\n",
    }


def build_stage1_adjudicator_package(
    *,
    queue: dict[str, Any],
    stage1_views: dict[str, dict[str, Any]],
    paired_rows: dict[str, dict[str, dict[str, str]]],
    binding: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the Stage-1 adjudicator archive.  Disputed items only.

    ``stage1_views`` maps a disputed pair id to the same sanitized Stage-1 item
    view a reviewer received; ``paired_rows`` maps it to both reviewers' rows.
    """

    if binding.get("stage") != STAGE1:
        raise AdjudicationPackageError("a Stage-1 package needs a Stage-1 binding")
    grouped = _disputes_by_pair(queue)
    files = _common_files(
        stage=STAGE1, queue=queue, binding=binding, instructions=STAGE1_ADJUDICATOR_INSTRUCTIONS
    )
    included: list[str] = []
    for pair_id in disputed_pair_ids(queue):
        view = stage1_views.get(pair_id)
        if view is None:
            raise AdjudicationPackageError(
                f"no Stage-1 evidence was supplied for disputed item {pair_id}"
            )
        leaked = sorted(STAGE2_ONLY_KEYS & set(_all_keys(view)))
        if leaked:
            raise AdjudicationPackageError(
                f"refusing to ship Stage-2 material in a Stage-1 adjudicator package: {leaked}"
            )
        rows = paired_rows.get(pair_id, {})
        payload = {
            "schema_version": STAGE1_PACKAGE_SCHEMA_VERSION,
            "pair_id": pair_id,
            "task_objective": view.get("task_objective"),
            "shared_goal": view.get("shared_goal"),
            "clean_instance": view.get("clean_instance"),
            "intervention_instance": view.get("intervention_instance"),
            "controlled_difference": view.get("controlled_difference"),
            "intended_changed_factor": (view.get("controlled_difference") or {}).get(
                "intended_changed_factor"
            ),
            "claimed_preserved_invariants": view.get("claimed_preserved_invariants"),
            "primitive_evidence_manifest": view.get("evidence_field_manifest"),
            "declared_tool_capabilities": {
                "clean": (view.get("clean_instance") or {}).get("declared_tools"),
                "intervention": (view.get("intervention_instance") or {}).get("declared_tools"),
            },
            "disputed_dimensions": [
                {
                    "dimension": str(row["dimension"]),
                    "reasons": list(row.get("reasons", [])),
                    "reviewers": _reviewer_view(rows, str(row["dimension"])),
                }
                for row in grouped.get(pair_id, [])
            ],
            "withheld_from_this_package": [
                "the expected result for either instance",
                "the accepted variants, answer contract and scorer contract",
                "the route requirement and every second-stage policy",
            ],
        }
        files[f"items/{pair_id}.json"] = canonical_bytes(payload) + b"\n"
        included.append(pair_id)

    files["manifest.json"] = (
        canonical_bytes(
            {
                "schema_version": STAGE1_PACKAGE_SCHEMA_VERSION,
                "stage": STAGE1,
                "disputed_item_count": len(included),
                "items": [{"pair_id": pair_id, "item_path": f"items/{pair_id}.json"} for pair_id in included],
                "binding": "binding.json",
                "form": "adjudication_form.json",
                "instructions": "ADJUDICATOR_INSTRUCTIONS.md",
                "stage2_material_included": False,
                "non_disputed_items_included": False,
            }
        )
        + b"\n"
    )
    payload_bytes = zip_bytes(files)
    return {
        "stage": STAGE1,
        "schema_version": STAGE1_PACKAGE_SCHEMA_VERSION,
        "filename": PACKAGE_FILENAMES[STAGE1],
        "disputed_pair_ids": included,
        "package_bytes": payload_bytes,
        "package_sha256": sha256_bytes(payload_bytes),
        "binding": binding,
    }


def build_stage2_adjudicator_package(
    *,
    queue: dict[str, Any],
    stage2_records: dict[str, dict[str, Any]],
    applicability: dict[str, dict[str, bool]],
    paired_rows: dict[str, dict[str, dict[str, str]]],
    binding: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the Stage-2 adjudicator archive.  Disputed items only."""

    if binding.get("stage") != STAGE2:
        raise AdjudicationPackageError("a Stage-2 package needs a Stage-2 binding")
    grouped = _disputes_by_pair(queue)
    files = _common_files(
        stage=STAGE2, queue=queue, binding=binding, instructions=STAGE2_ADJUDICATOR_INSTRUCTIONS
    )
    included: list[str] = []
    for pair_id in disputed_pair_ids(queue):
        record = stage2_records.get(pair_id)
        if record is None:
            raise AdjudicationPackageError(
                f"no Stage-2 record was supplied for disputed item {pair_id}"
            )
        missing = sorted(field for field in STAGE2_REQUIRED_EVIDENCE if field not in record)
        if missing:
            raise AdjudicationPackageError(
                f"the Stage-2 record for {pair_id} lacks required adjudication evidence: {missing}"
            )
        rows = paired_rows.get(pair_id, {})
        payload = {
            "schema_version": STAGE2_PACKAGE_SCHEMA_VERSION,
            "pair_id": pair_id,
            "semantic_objective_id": record.get("semantic_objective_id"),
            "intervention_family": record.get("intervention_family"),
            **{field: record[field] for field in STAGE2_REQUIRED_EVIDENCE},
            **{
                field: record[field]
                for field in STAGE2_CONDITIONAL_EVIDENCE
                if record.get(field)
            },
            "conditional_policies_absent": [
                field for field in STAGE2_CONDITIONAL_EVIDENCE if not record.get(field)
            ],
            "applicability": dict(applicability.get(pair_id, {})),
            "source_to_gold_rationale": record.get("source_to_gold_rationale"),
            "disputed_dimensions": [
                {
                    "dimension": str(row["dimension"]),
                    "applicable": bool(row.get("applicable", True)),
                    "reasons": list(row.get("reasons", [])),
                    "reviewers": _reviewer_view(rows, str(row["dimension"])),
                }
                for row in grouped.get(pair_id, [])
            ],
        }
        files[f"items/{pair_id}.json"] = canonical_bytes(payload) + b"\n"
        included.append(pair_id)

    files["manifest.json"] = (
        canonical_bytes(
            {
                "schema_version": STAGE2_PACKAGE_SCHEMA_VERSION,
                "stage": STAGE2,
                "disputed_item_count": len(included),
                "items": [{"pair_id": pair_id, "item_path": f"items/{pair_id}.json"} for pair_id in included],
                "binding": "binding.json",
                "form": "adjudication_form.json",
                "instructions": "ADJUDICATOR_INSTRUCTIONS.md",
                "withheld_material_included": True,
                "non_disputed_items_included": False,
            }
        )
        + b"\n"
    )
    payload_bytes = zip_bytes(files)
    return {
        "stage": STAGE2,
        "schema_version": STAGE2_PACKAGE_SCHEMA_VERSION,
        "filename": PACKAGE_FILENAMES[STAGE2],
        "disputed_pair_ids": included,
        "package_bytes": payload_bytes,
        "package_sha256": sha256_bytes(payload_bytes),
        "binding": binding,
    }


def _all_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            found |= _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            found |= _all_keys(child)
    return found


def verify_package_binding(
    receipt: dict[str, Any],
    *,
    stage: str,
    queue: dict[str, Any],
    package_sha256: str,
    adjudicator_assignment_sha256: str,
) -> dict[str, bool]:
    """Fail closed unless this adjudication answers the package we issued."""

    checks = {
        "package_is_for_this_stage": str(receipt.get("stage")) == stage,
        "package_hash_matches_the_issued_package": str(receipt.get("package_sha256", "")).strip().casefold()
        == str(package_sha256).strip().casefold(),
        "package_answers_the_current_queue": str(receipt.get("disagreement_queue_sha256"))
        == str(queue.get("receipt_sha256") or sha256_json(queue)),
        "package_covers_exactly_the_disputed_items": list(receipt.get("disputed_pair_ids", []))
        == disputed_pair_ids(queue),
        "package_was_issued_to_this_adjudicator": str(receipt.get("adjudicator_assignment_sha256"))
        == str(adjudicator_assignment_sha256),
    }
    failed = sorted(name for name, value in checks.items() if not value)
    if failed:
        raise AdjudicationPackageError(
            f"the {stage} adjudication was submitted against a stale or different package: {failed}"
        )
    return checks


__all__ = [
    "BINDING_FIELDS",
    "BINDING_SCHEMA_VERSION",
    "PACKAGE_FILENAMES",
    "STAGE1_ADJUDICATOR_INSTRUCTIONS",
    "STAGE1_PACKAGE_SCHEMA_VERSION",
    "STAGE2_ADJUDICATOR_INSTRUCTIONS",
    "STAGE2_CONDITIONAL_EVIDENCE",
    "STAGE2_ONLY_KEYS",
    "STAGE2_PACKAGE_SCHEMA_VERSION",
    "STAGE2_REQUIRED_EVIDENCE",
    "AdjudicationPackageError",
    "adjudication_form",
    "build_stage1_adjudicator_package",
    "build_stage2_adjudicator_package",
    "disputed_pair_ids",
    "package_binding",
    "verify_package_binding",
]
