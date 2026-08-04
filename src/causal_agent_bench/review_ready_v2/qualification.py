"""Reviewer qualification: public generator, private content, private answers.

This module is deliberately content-free.  It carries the schema, the generator
logic, the validation logic, the public instructions, empty templates and safe
commitments — and nothing else.  The instantiated calibration items and their
answer key are derived from the private packet seed and written only to ignored
private storage; the key is encrypted under an external key named by
``CAB_QUALIFICATION_KEY_PATH``.

Reading every tracked byte of this repository therefore tells you how
qualification works, and tells you nothing about which dimension decides any
particular item or what the expected answer is.

The earlier version, ``cab_stage1_qualification_v2``, shipped its items and its
answer key inside tracked source.  It is retired here and refused in code, under
any name, forever.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from causal_agent_bench.review_ready_v2.common import (
    canonical_bytes,
    derive_token,
    sha256_bytes,
    sha256_file,
    sha256_json,
)
from causal_agent_bench.review_ready_v2.declarations import (
    DECLARATION_INSTRUCTIONS,
    declaration_template,
)
from causal_agent_bench.review_ready_v2.keys import ExternalKeyError, load_external_key
from causal_agent_bench.review_ready_v2.roles import (
    REVIEW_ROLES,
    RoleError,
    normalize_role,
)
from causal_agent_bench.review_ready_v2.stage1 import (
    FORM_VALIDATION_RULES,
    REVIEW_DIMENSIONS,
    REVIEW_FORM_COLUMNS,
    zip_bytes,
)

QUALIFICATION_SCHEMA_VERSION = "cab_qualification_v3"
QUALIFICATION_KEY_ENV = "CAB_QUALIFICATION_KEY_PATH"
QUALIFICATION_ITEM_COUNT = 5
MIN_QUALIFICATION_RATE = 0.80

QUALIFICATION_VAULT_AD = b"cab-review-ready-v2/qualification-key/v3"

RETIRED_QUALIFICATION_STATUS = "EXPOSED_QUALIFICATION_NOT_ELIGIBLE_FOR_GENUINE_REVIEW"

#: Qualification versions whose items and/or answers reached tracked Git history.
#: They are refused by :func:`enforce_active_qualification` even under a new name.
RETIRED_QUALIFICATION_VERSIONS: dict[str, str] = {
    "cab_stage1_qualification_v2": (
        "The five calibration items and the complete QUALIFICATION_KEY — decisive dimension, "
        "expected value and explanation for every item — were committed to tracked source, so "
        "any clone of this repository could pass it without judging anything."
    ),
}

QUALIFICATION_INSTRUCTIONS = """# CAB reviewer qualification

These items are a calibration exercise, not part of the benchmark. They use
different tasks, different domains and different records from the review set,
and they are generated specifically for you: your package is not the same as the
other reviewer's.

Judge them exactly as you will judge the real items, and fill one row per item in
`qualification_form.csv`. Every dimension is scored, so answer all of them; one
dimension per item decides whether the calibration passes, and you are not told
which one.

You must reach at least 80% agreement with the reference judgement before you can
be assigned a review package. Work alone and do not use any AI assistant.

Return `qualification_form.csv` together with your completed
`reviewer_declaration.json`. The coordinator cannot qualify you without both.
"""


class QualificationError(RuntimeError):
    """Qualification generation, scoring, or version enforcement refused."""


def enforce_active_qualification(schema_version: str | None) -> None:
    """Fail closed unless this is the active, never-published qualification."""

    version = str(schema_version or "")
    if version in RETIRED_QUALIFICATION_VERSIONS:
        raise QualificationError(
            f"qualification version {version!r} is retired: "
            f"{RETIRED_QUALIFICATION_VERSIONS[version]} {RETIRED_QUALIFICATION_STATUS}"
        )
    if version != QUALIFICATION_SCHEMA_VERSION:
        raise QualificationError(
            f"expected the active qualification {QUALIFICATION_SCHEMA_VERSION!r}, got {version!r}"
        )


# --------------------------------------------------------------------------
# generator logic (public) — content is produced only from the private seed
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _Scenario:
    """A calibration setting: two sources, two capabilities, one small task."""

    key: str
    domain: str
    objective: str
    primary_source: str
    primary_ref_prefix: str
    primary_numeric_field: str
    policy_source: str
    policy_numeric_field: str
    primary_tool: str
    policy_tool: str
    answer_field: str
    secondary_field: str


_SCENARIOS: tuple[_Scenario, ...] = (
    _Scenario(
        "library", "civic", "give the latest return date that avoids a fine",
        "loan_record", "LN", "loan_day", "lending_policy", "loan_days",
        "loan_record_reader", "lending_policy_reader", "due_date_already_computed", "branch",
    ),
    _Scenario(
        "gym", "commerce", "give the amount owed for this billing period",
        "membership_record", "GM", "months_due", "rate_card", "monthly_fee",
        "membership_reader", "rate_card_reader", "amount_due_already_computed", "tier",
    ),
    _Scenario(
        "parking", "civic", "say whether the permit covers overnight parking",
        "permit_record", "PK", "bay_number", "zone_rules", "overnight_cutoff_hour",
        "permit_reader", "zone_rule_reader", "coverage_already_decided", "zone",
    ),
    _Scenario(
        "market_pitch", "commerce", "give the licence class this pitch needs",
        "pitch_record", "FT", "days_per_week", "licence_schedule", "max_days_per_week",
        "pitch_reader", "licence_schedule_reader", "licence_class_already_chosen", "site",
    ),
    _Scenario(
        "bike_share", "logistics", "give the fare for the rider's last trip",
        "trip_record", "BS", "minutes", "fare_table", "band_ceiling",
        "trip_reader", "fare_table_reader", "fare_already_computed", "dock",
    ),
    _Scenario(
        "clinic_slot", "operations", "give the earliest appointment slot that fits the rule",
        "booking_record", "CL", "requested_hour", "scheduling_rule", "earliest_hour",
        "booking_reader", "scheduling_rule_reader", "slot_already_selected", "room",
    ),
    _Scenario(
        "parcel", "logistics", "give the delivery window for this parcel",
        "consignment_record", "PC", "transit_days", "service_matrix", "window_days",
        "consignment_reader", "service_matrix_reader", "window_already_computed", "depot",
    ),
    _Scenario(
        "utility", "operations", "give the meter reading band for this account",
        "meter_record", "UT", "units_used", "tariff_bands", "band_ceiling",
        "meter_reader", "tariff_band_reader", "band_already_assigned", "meter_class",
    ),
)

#: Each defect kind names the dimension that decides the item and the value a
#: competent reviewer must give.  Which kind lands on which scenario is decided
#: by the private seed, so this table reveals nothing about a real package.
_DEFECT_KINDS: tuple[tuple[str, str, str], ...] = (
    ("clean_single_tool_removal", "single_factor_isolation", "yes"),
    ("two_fields_changed", "single_factor_isolation", "no"),
    ("goal_replaced", "goal_preserved", "no"),
    ("precomputed_answer_in_evidence", "primitive_evidence_adequate", "no"),
    ("policy_source_unreadable", "clean_evidence_sufficient", "no"),
    ("claimed_invariant_violated", "preserved_invariants_hold", "no"),
)

_POSITIVE_KIND = _DEFECT_KINDS[0][0]


def _tool(tool_id: str, source: str) -> dict[str, Any]:
    return {
        "tool_id": tool_id,
        "capability": f"read the {source.replace('_', ' ')}",
        "reads_source": source,
        "arguments": ["reference"],
        "returns_fields": ["*"],
        "access_tier": "standard",
    }


def _instance(
    scenario: _Scenario, numbers: dict[str, int], *, reference: str
) -> dict[str, Any]:
    return {
        "goal": f"A user asks you to {scenario.objective}.",
        "evidence": {
            scenario.primary_source: {
                "reference": reference,
                scenario.primary_numeric_field: numbers["primary"],
                scenario.secondary_field: f"{scenario.secondary_field}-{numbers['secondary']}",
            },
            scenario.policy_source: [
                {"band": "standard", scenario.policy_numeric_field: numbers["policy"]},
                {"band": "extended", scenario.policy_numeric_field: numbers["policy_alt"]},
            ],
        },
        "declared_tools": [
            _tool(scenario.primary_tool, scenario.primary_source),
            _tool(scenario.policy_tool, scenario.policy_source),
        ],
        "tools_reported_failing": [],
    }


def _apply_defect(
    kind: str, scenario: _Scenario, clean: dict[str, Any], numbers: dict[str, int]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    """Return ``(clean, intervention, controlled_difference, invariants)``."""

    import copy

    clean = copy.deepcopy(clean)
    intervention = copy.deepcopy(clean)
    invariants = ["goal_text_identical", "non_target_sources_identical"]
    difference: dict[str, Any] = {
        "intervention_family": "tool_removal",
        "intended_changed_factor": "declared_tool_capability_availability",
        "changed_locators": [f"$.tools.{scenario.policy_tool}"],
        "author_rationale": (
            f"The {scenario.policy_source.replace('_', ' ')} capability is revoked; "
            "nothing else changes."
        ),
    }

    if kind == "clean_single_tool_removal":
        intervention["declared_tools"] = [
            tool for tool in intervention["declared_tools"] if tool["tool_id"] != scenario.policy_tool
        ]
    elif kind == "two_fields_changed":
        difference = {
            "intervention_family": "observation_conflict",
            "intended_changed_factor": "cross_source_observation_consistency",
            "changed_locators": [f"$.sources.{scenario.primary_source}.{scenario.primary_numeric_field}"],
            "author_rationale": (
                f"One field of the {scenario.primary_source.replace('_', ' ')} is changed to "
                "conflict with the policy table."
            ),
        }
        record = intervention["evidence"][scenario.primary_source]
        record[scenario.primary_numeric_field] = numbers["primary"] + numbers["delta"]
        record[scenario.secondary_field] = f"{scenario.secondary_field}-{numbers['secondary'] + 1}"
    elif kind == "goal_replaced":
        difference = {
            "intervention_family": "memory_corruption",
            "intended_changed_factor": "task_critical_memory_field_validity",
            "changed_locators": ["$.memory.cycle_reference"],
            "author_rationale": "A stale working-memory field is corrupted; the goal is unchanged.",
        }
        intervention["goal"] = (
            f"A user asks you to close the {scenario.primary_source.replace('_', ' ')} "
            "and confirm the closure date."
        )
    elif kind == "precomputed_answer_in_evidence":
        for state in (clean, intervention):
            state["evidence"][scenario.primary_source][scenario.answer_field] = (
                f"resolved-value-{numbers['primary'] + numbers['policy']}"
            )
        intervention["declared_tools"] = [
            tool for tool in intervention["declared_tools"] if tool["tool_id"] != scenario.policy_tool
        ]
    elif kind == "policy_source_unreadable":
        for state in (clean, intervention):
            state["declared_tools"] = [
                tool for tool in state["declared_tools"] if tool["tool_id"] != scenario.policy_tool
            ]
        difference = {
            "intervention_family": "tool_failure",
            "intended_changed_factor": "declared_tool_runtime_success",
            "changed_locators": ["$.injected_failures"],
            "author_rationale": (
                f"The {scenario.primary_source.replace('_', ' ')} capability now fails at runtime."
            ),
        }
        intervention["tools_reported_failing"] = [scenario.primary_tool]
    elif kind == "claimed_invariant_violated":
        difference = {
            "intervention_family": "tool_failure",
            "intended_changed_factor": "declared_tool_runtime_success",
            "changed_locators": ["$.injected_failures"],
            "author_rationale": (
                f"The {scenario.primary_source.replace('_', ' ')} capability now fails at runtime; "
                "every source is untouched."
            ),
        }
        intervention["tools_reported_failing"] = [scenario.primary_tool]
        intervention["evidence"][scenario.policy_source][0][scenario.policy_numeric_field] = (
            numbers["policy"] + numbers["delta"]
        )
    else:  # pragma: no cover - the table above is exhaustive
        raise QualificationError(f"unknown qualification defect kind {kind!r}")
    return clean, intervention, difference, invariants


def _numbers(seed: bytes, label: str) -> dict[str, int]:
    raw = derive_token(seed, f"qualification:numbers:{label}", 16)
    values = [int(raw[index : index + 2], 16) for index in range(0, 16, 2)]
    return {
        "primary": 2 + values[0] % 40,
        "secondary": 1 + values[1] % 90,
        "policy": 5 + values[2] % 50,
        "policy_alt": 55 + values[3] % 40,
        "delta": 1 + values[4] % 7,
        "reference": 1000 + values[5] * 7 + values[6],
    }


def _plan(seed: bytes, role: str) -> list[tuple[_Scenario, str]]:
    """Seed-derived (scenario, defect kind) plan.  Different for each role."""

    canonical = normalize_role(role)
    import random

    rng = random.Random(int(derive_token(seed, f"qualification:plan:{canonical}", 16), 16))
    scenarios = list(_SCENARIOS)
    rng.shuffle(scenarios)
    negative_kinds = [kind for kind, _, _ in _DEFECT_KINDS if kind != _POSITIVE_KIND]
    rng.shuffle(negative_kinds)
    kinds = [_POSITIVE_KIND, *negative_kinds[: QUALIFICATION_ITEM_COUNT - 1]]
    rng.shuffle(kinds)
    return list(zip(scenarios[:QUALIFICATION_ITEM_COUNT], kinds, strict=True))


def _expected_for(kind: str) -> tuple[str, str]:
    for name, dimension, value in _DEFECT_KINDS:
        if name == kind:
            return dimension, value
    raise QualificationError(f"unknown qualification defect kind {kind!r}")


def build_private_qualification(seed: bytes, role: str) -> dict[str, Any]:
    """Instantiate one reviewer's package and its answer key from the seed.

    The return value is private.  Only the package bytes are ever handed to a
    reviewer, and only the hashes ever reach a public commitment.
    """

    canonical = normalize_role(role)
    if canonical not in REVIEW_ROLES:
        raise QualificationError(f"{canonical} is not issued a qualification package")
    if len(seed) < 16:
        raise QualificationError("the qualification seed must be at least 16 bytes")

    items: list[dict[str, Any]] = []
    key: dict[str, dict[str, str]] = {}
    for position, (scenario, kind) in enumerate(_plan(seed, canonical), 1):
        item_id = "Q-" + derive_token(seed, f"qualification:item:{canonical}:{position}", 8).upper()
        numbers = _numbers(seed, f"{canonical}:{scenario.key}:{position}")
        reference = f"{scenario.primary_ref_prefix}-{numbers['reference']}"
        base = _instance(scenario, numbers, reference=reference)
        clean, intervention, difference, invariants = _apply_defect(kind, scenario, base, numbers)
        items.append(
            {
                "schema_version": QUALIFICATION_SCHEMA_VERSION,
                "reviewer_item_id": item_id,
                "scenario": scenario.key,
                "domain": scenario.domain,
                "task_objective": clean["goal"],
                "clean_instance": clean,
                "intervention_instance": intervention,
                "controlled_difference": difference,
                "claimed_preserved_invariants": invariants,
            }
        )
        dimension, expected = _expected_for(kind)
        key[item_id] = {
            "decisive_dimension": dimension,
            "expected_value": expected,
            "defect_kind": kind,
        }

    package = _package_bytes(items, canonical)
    return {
        "qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "package_role": f"qualification_{canonical.casefold()}",
        "reviewer_role": canonical,
        "item_ids": [str(item["reviewer_item_id"]) for item in items],
        "package_bytes": package,
        "package_sha256": sha256_bytes(package),
        "answer_key": key,
    }


def _empty_form(item_ids: list[str]) -> bytes:
    rows = [",".join(REVIEW_FORM_COLUMNS)]
    rows.extend(item_id + "," * (len(REVIEW_FORM_COLUMNS) - 1) for item_id in item_ids)
    return ("\n".join(rows) + "\n").encode()


def _package_bytes(items: list[dict[str, Any]], role: str) -> bytes:
    item_ids = [str(item["reviewer_item_id"]) for item in items]
    files: dict[str, bytes] = {
        f"items/{item['reviewer_item_id']}.json": canonical_bytes(item) + b"\n" for item in items
    }
    files["manifest.json"] = (
        canonical_bytes(
            {
                "schema_version": QUALIFICATION_SCHEMA_VERSION,
                "package_role": f"qualification_{role.casefold()}",
                "item_count": len(item_ids),
                "items": [
                    {"reviewer_item_id": item_id, "item_path": f"items/{item_id}.json"}
                    for item_id in item_ids
                ],
                "form": "qualification_form.csv",
                "declaration": "reviewer_declaration.json",
                "pass_threshold": MIN_QUALIFICATION_RATE,
                # Named so that no shipped byte contains the words a grader uses.
                "reference_judgements_included": False,
                "scored_dimension_disclosed": False,
                "reuses_review_set_tasks": False,
            }
        )
        + b"\n"
    )
    files["qualification_form.csv"] = _empty_form(item_ids)
    files["QUALIFICATION_INSTRUCTIONS.md"] = QUALIFICATION_INSTRUCTIONS.encode()
    files["DECLARATION_INSTRUCTIONS.md"] = DECLARATION_INSTRUCTIONS.encode()
    files["reviewer_declaration.json"] = canonical_bytes(declaration_template()) + b"\n"
    files["review_form.schema.json"] = (
        canonical_bytes(
            {
                "columns": [
                    {"name": name, "allowed_values": list(values) if values else "free_text"}
                    for name, values, _ in REVIEW_DIMENSIONS
                ],
                "validation_rules": list(FORM_VALIDATION_RULES),
            }
        )
        + b"\n"
    )
    return zip_bytes(files)


# --------------------------------------------------------------------------
# encrypted answer key
# --------------------------------------------------------------------------


def seal_qualification_key(payload: dict[str, Any], key: bytes) -> bytes:
    nonce = secrets.token_bytes(12)
    plaintext = canonical_bytes({"schema_version": QUALIFICATION_SCHEMA_VERSION, "keys": payload})
    return nonce + AESGCM(key).encrypt(nonce, plaintext, QUALIFICATION_VAULT_AD)


def unseal_qualification_key(ciphertext: bytes, key: bytes) -> dict[str, Any]:
    import json

    if len(ciphertext) <= 12:
        raise QualificationError("the qualification key vault is truncated")
    try:
        plaintext = AESGCM(key).decrypt(ciphertext[:12], ciphertext[12:], QUALIFICATION_VAULT_AD)
    except InvalidTag as error:
        raise QualificationError(
            "the qualification key vault failed authentication with this key"
        ) from error
    payload = json.loads(plaintext)
    enforce_active_qualification(payload.get("schema_version"))
    keys = payload.get("keys")
    if not isinstance(keys, dict):
        raise QualificationError("the qualification key vault does not contain a key map")
    return keys


def load_qualification_keys(vault_path: Path, repo_root: Path) -> dict[str, Any]:
    """Coordinator-mode decryption.  Fails closed without the external key."""

    if not vault_path.is_file():
        raise QualificationError(
            f"no encrypted qualification key at {vault_path.name}; generate the private "
            "qualification packages first"
        )
    try:
        key = load_external_key(QUALIFICATION_KEY_ENV, repo_root)
    except ExternalKeyError as error:
        raise QualificationError(f"qualification scoring requires the answer key: {error}") from error
    return unseal_qualification_key(vault_path.read_bytes(), key)


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------


_ALLOWED_VALUES = {name: set(values) for name, values, _ in REVIEW_DIMENSIONS if values}


def score_qualification(
    submission: dict[str, dict[str, str]],
    answer_key: dict[str, Any],
    *,
    reviewer_role: str,
    already_qualified_roles: set[str] | None = None,
) -> dict[str, Any]:
    """Score one reviewer against their own private key.

    The result carries counts and per-item correctness only.  It never carries a
    decisive dimension, an expected value, or an explanation, so a qualification
    receipt can be written to disk and quoted in a report without leaking the key.
    """

    try:
        canonical = normalize_role(reviewer_role)
    except RoleError as error:
        raise QualificationError(str(error)) from error
    if canonical in (already_qualified_roles or set()):
        raise QualificationError(
            f"{canonical} already holds a qualification receipt; a reviewer id cannot be reused"
        )
    if not isinstance(submission, dict) or not submission:
        raise QualificationError("the qualification submission is empty or malformed")

    expected_items = set(answer_key)
    offered_items = {str(item).strip() for item in submission}
    missing = sorted(expected_items - offered_items)
    unexpected = sorted(offered_items - expected_items)
    if missing:
        raise QualificationError(
            f"the qualification submission is incomplete: {len(missing)} item(s) unanswered"
        )
    if unexpected:
        raise QualificationError(
            f"the qualification submission carries {len(unexpected)} row(s) that are not in this "
            "reviewer's package"
        )

    graded: list[dict[str, Any]] = []
    for item_id in sorted(expected_items):
        entry = answer_key[item_id]
        dimension = str(entry["decisive_dimension"])
        row = submission[item_id]
        if not isinstance(row, dict):
            raise QualificationError(f"the qualification row for {item_id} is malformed")
        raw = row.get(dimension)
        if raw is None or str(raw).strip() == "":
            raise QualificationError(
                f"the qualification submission does not answer every dimension for {item_id}"
            )
        for name, allowed in _ALLOWED_VALUES.items():
            value = str(row.get(name, "")).strip().casefold()
            if value and value not in allowed:
                raise QualificationError(
                    f"the qualification row for {item_id} carries an invalid value in {name!r}"
                )
        graded.append(
            {
                "reviewer_item_id": item_id,
                "correct": str(raw).strip().casefold() == str(entry["expected_value"]).casefold(),
            }
        )

    correct = sum(1 for row in graded if row["correct"])
    rate = correct / len(graded) if graded else 0.0
    return {
        "schema_version": "cab_qualification_result_v3",
        "qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "reviewer_role": canonical,
        "item_count": len(graded),
        "correct_count": correct,
        "rate": round(rate, 4),
        "threshold": MIN_QUALIFICATION_RATE,
        "graded": graded,
        "qualified": rate >= MIN_QUALIFICATION_RATE,
        "answer_key_disclosed": False,
    }


# --------------------------------------------------------------------------
# public commitment and registry
# --------------------------------------------------------------------------


def generator_source_sha256() -> str:
    return sha256_file(Path(__file__).resolve())


def qualification_commitment(
    *,
    package_hashes: dict[str, str],
    encrypted_key_material_sha256: str,
) -> dict[str, Any]:
    """The only qualification facts that may be published."""

    commitment = {
        "schema_version": "cab_qualification_commitment_v1",
        "qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "reviewer_a_package_hash": package_hashes.get("REVIEWER_A"),
        "reviewer_b_package_hash": package_hashes.get("REVIEWER_B"),
        "encrypted_key_material_hash": encrypted_key_material_sha256,
        "generator_source_hash": generator_source_sha256(),
        "key_environment_variable": QUALIFICATION_KEY_ENV,
        "key_value_bound": False,
        "items_published": False,
        "reference_judgements_published": False,
        "scored_dimensions_published": False,
        "retired_qualification_versions": sorted(RETIRED_QUALIFICATION_VERSIONS),
    }
    commitment["commitment_sha256"] = sha256_json(commitment)
    return commitment


def retired_qualification_registry() -> dict[str, Any]:
    return {
        "schema_version": "cab_retired_qualification_registry_v1",
        "status": "CAB_RETIRED_QUALIFICATION_BLOCKED",
        "active_qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "retired_versions": [
            {
                "qualification_version": version,
                "reason": reason,
                "status": RETIRED_QUALIFICATION_STATUS,
                "eligible_for_genuine_review": False,
                "eligible_for_c10": False,
            }
            for version, reason in sorted(RETIRED_QUALIFICATION_VERSIONS.items())
        ],
        "enforcement": (
            "enforce_active_qualification() rejects every retired version at generation, "
            "ingestion, scoring and C10, including a copy renamed to the active version, "
            "because the encrypted key vault records its own version inside the ciphertext."
        ),
    }


__all__ = [
    "MIN_QUALIFICATION_RATE",
    "QUALIFICATION_ITEM_COUNT",
    "QUALIFICATION_KEY_ENV",
    "QUALIFICATION_SCHEMA_VERSION",
    "RETIRED_QUALIFICATION_STATUS",
    "RETIRED_QUALIFICATION_VERSIONS",
    "QualificationError",
    "build_private_qualification",
    "enforce_active_qualification",
    "generator_source_sha256",
    "load_qualification_keys",
    "qualification_commitment",
    "retired_qualification_registry",
    "score_qualification",
    "seal_qualification_key",
    "unseal_qualification_key",
]
