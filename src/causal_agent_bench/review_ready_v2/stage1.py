"""Stage-1 reviewer packages: what a reviewer sees, and nothing more.

A Stage-1 item exposes the shared goal, both instances of the pair, the
controlled difference between them, the primitive evidence and the declared tool
capabilities.  It never exposes gold, accepted variants, scorer internals, route
labels, the expected response type, the recovery binding, the abstention or
clarification requirement, private identifiers, or any Stage-2 material.
"""

from __future__ import annotations

import io
import random
import zipfile
from typing import Any

from causal_agent_bench.review_ready_v2.common import (
    canonical_bytes,
    derive_token,
    sha256_bytes,
    structural_diff,
)
from causal_agent_bench.review_ready_v2.models import PairSpec, ToolContract
from causal_agent_bench.review_ready_v2.operators import canonical_state

STAGE1_SCHEMA_VERSION = "cab_stage1_pair_review_v2"
REVIEW_FORM_SCHEMA_VERSION = "cab_stage1_review_form_v2"

REVIEW_DIMENSIONS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("task_clarity", ("1", "2", "3", "4", "5"), "Is the user's objective stated clearly enough to act on?"),
    ("clean_goal_clear", ("yes", "no"), "Is the goal of the clean instance unambiguous?"),
    (
        "clean_evidence_sufficient",
        ("yes", "no"),
        "Does the clean instance contain enough primitive evidence to complete the task?",
    ),
    ("clean_solvable", ("yes", "no"), "Is the clean instance solvable with the declared capabilities?"),
    (
        "intervention_understandable",
        ("yes", "no"),
        "Can you tell what changed between the two instances?",
    ),
    (
        "intended_factor_identifiable",
        ("yes", "no"),
        "Does the observed difference match the declared intended changed factor?",
    ),
    ("goal_preserved", ("yes", "no"), "Is the user's goal identical in both instances?"),
    (
        "single_factor_isolation",
        ("yes", "no"),
        "Did exactly one factor change, with nothing else altered?",
    ),
    (
        "preserved_invariants_hold",
        ("yes", "no", "partial"),
        "Do the claimed preserved invariants actually hold?",
    ),
    (
        "primitive_evidence_adequate",
        ("yes", "no"),
        "Is the evidence primitive — facts only, no pre-computed conclusion?",
    ),
    (
        "declared_tools_adequate",
        ("yes", "no"),
        "Are the declared capabilities adequate and accurately described?",
    ),
    ("intervention_realistic", ("1", "2", "3", "4", "5"), "How realistic is this disruption in practice?"),
    (
        "ambiguity_present",
        ("none", "minor", "material"),
        "Is there ambiguity that could make two competent responders disagree?",
    ),
    (
        "response_space_structurally_valid",
        ("yes", "no", "unsure"),
        "Given only what you can see, does at least one defensible response exist for the intervention instance?",
    ),
    ("exclude_item", ("yes", "no"), "Should this item be excluded from the benchmark slice?"),
    ("reviewer_confidence", ("1", "2", "3", "4", "5"), "How confident are you in this row?"),
    ("notes", (), "Free text. Required when exclude_item=yes or ambiguity_present=material."),
)

REVIEW_FORM_COLUMNS = ("reviewer_item_id", *(name for name, _, _ in REVIEW_DIMENSIONS))

FORM_VALIDATION_RULES = (
    "Every item in manifest.json must appear exactly once in review_form.csv.",
    "Every cell except notes must be one of the enumerated values for that column.",
    "notes is required when exclude_item=yes or when ambiguity_present=material.",
    "Do not leave any cell blank; use the enumerated value that best matches your judgement.",
    "Do not add, remove, reorder or rename columns or rows.",
)


def _public_tool(contract: ToolContract) -> dict[str, Any]:
    """Tool view with the recovery binding stripped."""

    return {
        "tool_id": contract.tool_id,
        "capability": contract.declared_capability,
        "reads_source": contract.scope_source,
        "arguments": list(contract.allowed_arguments),
        "returns_fields": list(contract.returned_fields),
        "declared_failure_modes": list(contract.failure_modes),
        "access_tier": "standard" if contract.authorization_scope == "standard" else "restricted",
    }


def _instance_view(pair: PairSpec, *, intervention: bool) -> dict[str, Any]:
    state = pair.intervention_environment if intervention else pair.clean_environment
    return {
        "instance": "intervention" if intervention else "clean",
        "goal": state.goal,
        "evidence": state.sources,
        "working_memory": state.memory,
        "source_precedence": state.source_trust,
        "declared_tools": [_public_tool(contract) for contract in state.tools],
        "tools_reported_failing": sorted(state.injected_failures),
    }


def _public_state(pair: PairSpec, *, intervention: bool) -> dict[str, Any]:
    """Canonical state with tools rendered through the public projection.

    Diffing the raw state would republish the raw tool contracts - including the
    recovery binding - inside the observed diff, so the diff is computed over
    the same sanitized view the reviewer already sees.
    """

    state = pair.intervention_environment if intervention else pair.clean_environment
    public = canonical_state(state)
    public["tools"] = {
        contract.tool_id: _public_tool(contract) for contract in state.tools
    }
    return public


def _difference_view(pair: PairSpec) -> dict[str, Any]:
    diff = structural_diff(
        _public_state(pair, intervention=False), _public_state(pair, intervention=True)
    )
    before = dict(pair.intervention_patch.before)
    after = dict(pair.intervention_patch.after)
    for payload in (before, after):
        tool = payload.get("tool")
        if isinstance(tool, dict):
            payload["tool"] = _public_tool(ToolContract.model_validate(tool))
    return {
        "intervention_family": pair.intervention_family,
        "operator": pair.intervention_operator,
        "intended_changed_factor": pair.intended_changed_factor,
        "changed_locators": list(pair.intervention_patch.target_locators),
        "before": before,
        "after": after,
        "author_rationale": pair.intervention_patch.rationale,
        "observed_structural_diff": diff,
    }


def stage1_item(pair: PairSpec, reviewer_item_id: str) -> dict[str, Any]:
    return {
        "schema_version": STAGE1_SCHEMA_VERSION,
        "reviewer_item_id": reviewer_item_id,
        "domain": pair.domain,
        "difficulty": pair.difficulty,
        "task_objective": pair.clean_prompt,
        "shared_goal": pair.shared_goal,
        "clean_instance": _instance_view(pair, intervention=False),
        "intervention_instance": _instance_view(pair, intervention=True),
        "controlled_difference": _difference_view(pair),
        "claimed_preserved_invariants": list(pair.preserved_invariants),
        "evidence_field_manifest": pair.primitive_evidence_manifest,
        "what_you_are_not_shown": [
            "the expected result for either instance",
            "the expected response type for the intervention instance",
            "the grading rules, response format contract, or accepted variants",
            "any material held back for the second review stage",
        ],
    }


def _review_form_csv(item_ids: list[str]) -> bytes:
    header = ",".join(REVIEW_FORM_COLUMNS)
    rows = [header]
    rows.extend(item_id + "," * (len(REVIEW_FORM_COLUMNS) - 1) for item_id in item_ids)
    return ("\n".join(rows) + "\n").encode()


def _review_form_schema() -> bytes:
    return canonical_bytes(
        {
            "schema_version": REVIEW_FORM_SCHEMA_VERSION,
            "columns": [
                {
                    "name": name,
                    "allowed_values": list(values) if values else "free_text",
                    "question": question,
                }
                for name, values, question in REVIEW_DIMENSIONS
            ],
            "validation_rules": list(FORM_VALIDATION_RULES),
            "prefilled": False,
        }
    ) + b"\n"


REVIEWER_INSTRUCTIONS = """# CAB Stage-1 reviewer instructions

You are one of two independent reviewers. Read all of this before you start.

## What you are judging

You are judging whether each **pair** is a scientifically valid controlled
comparison. Each item shows the same user goal twice: a *clean* instance and an
*intervention* instance produced by changing exactly one declared factor.

You are **not** judging whether a model would answer correctly, and you are not
being asked what the right answer is. You are judging clarity, evidence
sufficiency, goal preservation, single-factor isolation, invariant preservation,
realism and ambiguity.

## Independence

- Work alone. Do not discuss any item with the other reviewer, with the
  benchmark authors, or with anyone else.
- Do not use any AI assistant, language model, or automated judgement aid for
  any part of this review. Your judgements must be your own.
- If you are an author or co-author of this benchmark, or you have any other
  conflict of interest, stop now and tell the coordinator.
- Complete and return the conflict-of-interest declaration before you begin.

## Confidentiality

- Do not copy, publish, post, or share any item, artifact or archive.
- Do not upload any part of this package to any external service.
- Delete your local copy once the coordinator confirms receipt.

## How to work

1. Read `manifest.json` for the item list.
2. For each item, open `items/<reviewer_item_id>.json`.
3. Compare the clean and intervention instances, then read
   `controlled_difference` and check it against what you actually observe.
4. Fill exactly one row per item in `review_form.csv`.
5. Follow `review_form.schema.json`: every cell takes one of the enumerated
   values, and `notes` is required whenever you set `exclude_item=yes` or
   `ambiguity_present=material`.

Expect roughly 8-12 minutes per item. Do not rush the isolation judgement; it is
the one that matters most.

## Submitting

- Return the completed `review_form.csv` unchanged in structure, plus the signed
  conflict-of-interest declaration.
- Send it only to the coordinator, by the channel they specified.

## Corrections

If you need to change a submitted row, send a full corrected `review_form.csv`
and say clearly that it supersedes the previous one. Do not send partial diffs.
The coordinator records only the latest validated submission, and every
submission is hash-bound.

## If something is wrong with this package

If a file is missing, an item does not open, a path is broken, or an item makes
no sense at all, do not guess and do not repair it yourself. Stop and contact
the coordinator with the `reviewer_item_id`. A malformed package is a defect on
our side, not a judgement you should absorb.
"""

CONFLICT_DECLARATION = """# Conflict-of-interest declaration

Reviewer pseudonymous ID: ____________________
Date: ____________________

Confirm each statement by writing YES next to it.

1. I am not an author or co-author of this benchmark. ____
2. I have no financial, professional or personal interest in the outcome. ____
3. I did not use any AI assistant or language model for any part of this
   review. ____
4. I did not discuss any item with the other reviewer or with anyone else. ____
5. I did not copy, share, publish or upload any part of this package. ____

Signature: ____________________
"""


def zip_bytes(files: dict[str, bytes]) -> bytes:
    """Deterministic archive: fixed timestamps, sorted names, no extra metadata."""

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, files[name])
    return stream.getvalue()


def reviewer_order(pairs: list[PairSpec], seed: bytes, role: str) -> list[PairSpec]:
    order = list(pairs)
    random.Random(int(derive_token(seed, f"order:{role}", 16), 16)).shuffle(order)
    return order


def build_stage1_package(
    pairs: list[PairSpec], seed: bytes, role: str
) -> tuple[bytes, dict[str, str], list[dict[str, Any]]]:
    """Return ``(archive_bytes, reviewer_item_id -> pair_id, manifest_items)``."""

    ordered = reviewer_order(pairs, seed, role)
    prefix = "RA" if role.endswith("_a") else "RB"
    mapping: dict[str, str] = {}
    manifest_items: list[dict[str, Any]] = []
    files: dict[str, bytes] = {}
    for position, pair in enumerate(ordered, 1):
        reviewer_item_id = f"{prefix}-{position:02d}"
        mapping[reviewer_item_id] = pair.pair_id
        item = stage1_item(pair, reviewer_item_id)
        files[f"items/{reviewer_item_id}.json"] = canonical_bytes(item) + b"\n"
        manifest_items.append(
            {
                "reviewer_item_id": reviewer_item_id,
                "item_path": f"items/{reviewer_item_id}.json",
                "domain": pair.domain,
                "difficulty": pair.difficulty,
                "intervention_family": pair.intervention_family,
            }
        )
    files["manifest.json"] = (
        canonical_bytes(
            {
                "schema_version": STAGE1_SCHEMA_VERSION,
                "package_role": role,
                "item_count": len(manifest_items),
                "items": manifest_items,
                "review_form": "review_form.csv",
                "review_form_schema": "review_form.schema.json",
                "instructions": "REVIEWER_INSTRUCTIONS.md",
                "conflict_declaration": "CONFLICT_OF_INTEREST.md",
                "withheld_material_included": False,
                "reference_solutions_included": False,
            }
        )
        + b"\n"
    )
    files["review_form.csv"] = _review_form_csv([row["reviewer_item_id"] for row in manifest_items])
    files["review_form.schema.json"] = _review_form_schema()
    files["REVIEWER_INSTRUCTIONS.md"] = REVIEWER_INSTRUCTIONS.encode()
    files["CONFLICT_OF_INTEREST.md"] = CONFLICT_DECLARATION.encode()
    return zip_bytes(files), mapping, manifest_items


def package_sha256(payload: bytes) -> str:
    return sha256_bytes(payload)


__all__ = [
    "CONFLICT_DECLARATION",
    "FORM_VALIDATION_RULES",
    "REVIEWER_INSTRUCTIONS",
    "REVIEW_DIMENSIONS",
    "REVIEW_FORM_COLUMNS",
    "REVIEW_FORM_SCHEMA_VERSION",
    "STAGE1_SCHEMA_VERSION",
    "build_stage1_package",
    "package_sha256",
    "reviewer_order",
    "stage1_item",
    "zip_bytes",
]
