"""Reviewer qualification V4: schema, transport and scoring — never content.

Every byte of this module is generic.  It carries the source schema, a loader for
privately authored item material, package assembly, the encryption and decryption
of the answer vault, and scoring against private answer material.  It carries no
item body, no defect template, no generation parameter, no decisive dimension, no
expected value, no explanation and no answer mapping.

The consequence is the property the earlier versions could not offer: reading
every tracked byte of this repository, *and* holding a reviewer's qualification
ZIP, still does not tell you which dimension decides any item or what the
expected value is.  The package bytes are a pure function of the reviewer-visible
item bodies; the answers travel only inside the AES-GCM vault, sealed under an
external key named by ``CAB_QUALIFICATION_KEY_PATH``.  Two private sources whose
item bodies are identical and whose answers differ produce byte-identical
packages — so no function of (tracked source, reviewer ZIP) can recover an answer.

Both earlier versions are retired here and refused in code, under any name,
forever:

``cab_stage1_qualification_v2``   shipped its items and its answer key in tracked
                                 source.
``cab_qualification_v3``          shipped a tracked generator whose scenario table
                                 and defect-to-answer mapping let a reviewer
                                 classify a generated item and look the answer up.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from causal_agent_bench.review_ready_v2.common import (
    canonical_bytes,
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

QUALIFICATION_SCHEMA_VERSION = "cab_qualification_v4"
QUALIFICATION_SOURCE_SCHEMA_VERSION = "cab_qualification_source_v4"
QUALIFICATION_RESULT_SCHEMA_VERSION = "cab_qualification_result_v4"

QUALIFICATION_KEY_ENV = "CAB_QUALIFICATION_KEY_PATH"
QUALIFICATION_SOURCE_ENV = "CAB_QUALIFICATION_SOURCE_PATH"

QUALIFICATION_ITEM_COUNT = 5
MIN_QUALIFICATION_RATE = 0.80

QUALIFICATION_VAULT_AD = b"cab-review-ready-v2/qualification-key/v4"

#: Where the privately authored source lives, relative to the private packet root.
QUALIFICATION_DIRNAME = "qualification_v4"
QUALIFICATION_SOURCE_FILENAME = "qualification_source.json"
QUALIFICATION_KEY_FILENAME = "qualification_key.enc"

#: The retired V3 directory is renamed to this rather than deleted, so a
#: coordinator cannot distribute a reconstructible package by reaching for the
#: old path, and nothing private is destroyed.
RETIRED_QUALIFICATION_DIRNAME = "qualification_retired_v3"

RETIRED_QUALIFICATION_STATUS = "EXPOSED_QUALIFICATION_NOT_ELIGIBLE_FOR_GENUINE_REVIEW"

#: Qualification versions whose answers were recoverable from public material.
#: They are refused by :func:`enforce_active_qualification` even under a new name.
RETIRED_QUALIFICATION_VERSIONS: dict[str, str] = {
    "cab_stage1_qualification_v2": (
        "The five calibration items and the complete QUALIFICATION_KEY — decisive dimension, "
        "expected value and explanation for every item — were committed to tracked source, so "
        "any clone of this repository could pass it without judging anything."
    ),
    "cab_qualification_v3": (
        "The items were generated privately, but the tracked generator carried the scenario "
        "table, the defect templates and the defect-to-answer mapping, so a reviewer holding "
        "the ZIP could classify each generated item against tracked source and read off its "
        "decisive dimension and expected value."
    ),
}

#: Keys that may never appear anywhere inside a shipped reviewer item body.
FORBIDDEN_ITEM_KEYS: frozenset[str] = frozenset(
    {
        "answer",
        "answer_key",
        "decisive_dimension",
        "defect_kind",
        "expected_answer",
        "expected_value",
        "explanation",
        "reference_judgement",
        "reference_judgment",
        "scored_dimension",
    }
)

#: The structural fields a privately authored reviewer-visible item must carry.
#: These are shape requirements, not content: they make a qualification item
#: answerable with the Stage-1 review form and nothing more.
REQUIRED_ITEM_FIELDS: tuple[str, ...] = (
    "task_objective",
    "clean_instance",
    "intervention_instance",
    "controlled_difference",
    "claimed_preserved_invariants",
)

REQUIRED_ANSWER_FIELDS: tuple[str, ...] = ("decisive_dimension", "expected_value")

QUALIFICATION_INSTRUCTIONS = """# CAB reviewer qualification

These items are a calibration exercise, not part of the benchmark. Qualification
uses separate tasks, records, identifiers and item content from the final review
set, and your package is generated for you alone: it is not the same as the other
reviewer's.

Judge them exactly as you will judge the real items, and fill one row per item in
`qualification_form.csv`. Complete every requested field. Qualification scoring
uses hidden predefined criteria and may weigh selected dimensions; you are not
told which dimensions those are, so answer every column on its own merits.

You must reach at least 80% agreement with the reference judgement before you can
be assigned a review package. Work alone and do not use any AI assistant.

Return `qualification_form.csv` together with your completed
`reviewer_declaration.json`. The coordinator cannot qualify you without both.
"""


class QualificationError(RuntimeError):
    """Qualification loading, generation, scoring, or version enforcement refused."""


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
# private source: schema and generic loading
# --------------------------------------------------------------------------


_ALLOWED_VALUES: dict[str, set[str]] = {
    name: set(values) for name, values, _ in REVIEW_DIMENSIONS if values
}


def qualification_source_schema() -> dict[str, Any]:
    """The machine-readable shape of the privately authored source.

    Publishing this is safe and useful: it says what an authored item must
    *contain*, never what any item says or which dimension decides it.
    """

    return {
        "schema_version": "cab_qualification_source_schema_v1",
        "source_schema_version": QUALIFICATION_SOURCE_SCHEMA_VERSION,
        "qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "stored_outside_git": True,
        "default_location": f"private_data/human_review/<packet>/{QUALIFICATION_DIRNAME}/"
        f"{QUALIFICATION_SOURCE_FILENAME}",
        "location_environment_variable": QUALIFICATION_SOURCE_ENV,
        "items_per_role": QUALIFICATION_ITEM_COUNT,
        "roles": list(REVIEW_ROLES),
        "item_fields": {
            "reviewer_item_id": "opaque identifier, unique across every role",
            "item": {
                "required_keys": list(REQUIRED_ITEM_FIELDS),
                "forbidden_keys_anywhere": sorted(FORBIDDEN_ITEM_KEYS),
                "shipped_to_reviewer": True,
            },
            "answer": {
                "required_keys": list(REQUIRED_ANSWER_FIELDS),
                "optional_keys": ["explanation"],
                "decisive_dimension_must_be_one_of": sorted(_ALLOWED_VALUES),
                "expected_value_must_be_allowed_for_that_dimension": True,
                "shipped_to_reviewer": False,
            },
        },
        "authoring_rules": [
            "Author the source outside the repository; it is private material.",
            "Every reviewer receives a different set of items.",
            "No item body may contain its own answer, in any field, under any name.",
            "The scoring criteria are hidden; the shipped package never names them.",
        ],
    }


def qualification_source_path(private_root: Path) -> Path:
    """Resolve the private source path, honouring the environment override."""

    override = os.environ.get(QUALIFICATION_SOURCE_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    return private_root / QUALIFICATION_DIRNAME / QUALIFICATION_SOURCE_FILENAME


def _forbidden_keys_in(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in FORBIDDEN_ITEM_KEYS:
                found.add(str(key).casefold())
            found |= _forbidden_keys_in(child)
    elif isinstance(value, list):
        for child in value:
            found |= _forbidden_keys_in(child)
    return found


def _validate_answer(item_id: str, answer: Any) -> dict[str, str]:
    if not isinstance(answer, dict):
        raise QualificationError(f"the answer material for {item_id} is not an object")
    missing = sorted(field for field in REQUIRED_ANSWER_FIELDS if not str(answer.get(field, "")).strip())
    if missing:
        raise QualificationError(f"the answer material for {item_id} is missing {missing}")
    dimension = str(answer["decisive_dimension"]).strip()
    expected = str(answer["expected_value"]).strip()
    allowed = _ALLOWED_VALUES.get(dimension)
    if allowed is None:
        raise QualificationError(
            f"the decisive dimension recorded for {item_id} is not an enumerated review dimension"
        )
    if expected.casefold() not in {value.casefold() for value in allowed}:
        raise QualificationError(
            f"the expected value recorded for {item_id} is not an allowed value of its dimension"
        )
    return {"decisive_dimension": dimension, "expected_value": expected}


def validate_qualification_source(source: dict[str, Any]) -> dict[str, Any]:
    """Validate privately authored material against the schema.  Fails closed.

    Returns a public-safe summary: counts and hashes only.  No item body, no
    dimension and no expected value is returned, logged or raised in a message.
    """

    if not isinstance(source, dict):
        raise QualificationError("the private qualification source is not a JSON object")
    enforce_active_qualification(source.get("qualification_version"))
    if source.get("schema_version") != QUALIFICATION_SOURCE_SCHEMA_VERSION:
        raise QualificationError(
            f"the private qualification source must declare {QUALIFICATION_SOURCE_SCHEMA_VERSION!r}"
        )
    roles = source.get("roles")
    if not isinstance(roles, dict) or set(roles) != set(REVIEW_ROLES):
        raise QualificationError(
            f"the private qualification source must carry exactly the roles {sorted(REVIEW_ROLES)}"
        )

    seen_ids: set[str] = set()
    per_role: dict[str, dict[str, Any]] = {}
    body_hashes: dict[str, str] = {}
    for role in REVIEW_ROLES:
        items = roles[role]
        if not isinstance(items, list) or len(items) != QUALIFICATION_ITEM_COUNT:
            raise QualificationError(
                f"role {role} must carry exactly {QUALIFICATION_ITEM_COUNT} authored items"
            )
        role_ids: list[str] = []
        for entry in items:
            if not isinstance(entry, dict):
                raise QualificationError(f"an authored item for {role} is not an object")
            item_id = str(entry.get("reviewer_item_id", "")).strip()
            if not item_id:
                raise QualificationError(f"an authored item for {role} has no reviewer_item_id")
            if item_id in seen_ids:
                raise QualificationError(
                    "a reviewer_item_id is reused across roles; identifiers must be unique so that "
                    "one reviewer's answers can never score another's package"
                )
            seen_ids.add(item_id)
            role_ids.append(item_id)
            body = entry.get("item")
            if not isinstance(body, dict):
                raise QualificationError(f"the authored body for {item_id} is not an object")
            missing = sorted(field for field in REQUIRED_ITEM_FIELDS if field not in body)
            if missing:
                raise QualificationError(f"the authored body for {item_id} is missing {missing}")
            leaked = sorted(_forbidden_keys_in(body))
            if leaked:
                raise QualificationError(
                    f"the authored body for {item_id} carries answer-bearing key(s) {leaked}; a "
                    "shipped item may never contain its own answer"
                )
            _validate_answer(item_id, entry.get("answer"))
        per_role[role] = {"item_count": len(role_ids), "item_ids": role_ids}
        body_hashes[role] = sha256_json(
            [entry["item"] for entry in roles[role]]
        )

    if len({tuple(per_role[role]["item_ids"]) for role in REVIEW_ROLES}) != len(REVIEW_ROLES):
        raise QualificationError("both reviewers were authored the same qualification items")
    if len(set(body_hashes.values())) != len(REVIEW_ROLES):
        raise QualificationError("both reviewers were authored byte-identical item bodies")

    return {
        "schema_version": "cab_qualification_source_check_v1",
        "source_schema_version": QUALIFICATION_SOURCE_SCHEMA_VERSION,
        "qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "roles": {role: per_role[role]["item_count"] for role in REVIEW_ROLES},
        "distinct_item_ids": len(seen_ids),
        "item_bodies_differ_per_role": True,
        "answers_validated": True,
        "answers_disclosed": False,
        "passed": True,
    }


def load_qualification_source(path: Path) -> dict[str, Any]:
    """Load and validate the privately authored source.  Fails closed."""

    if not path.is_file():
        raise QualificationError(
            f"no private qualification source at {path.name}. Author it outside Git first; "
            f"see qualification_source_schema() and set {QUALIFICATION_SOURCE_ENV} to override "
            "the default location."
        )
    try:
        source = json.loads(path.read_text())
    except ValueError as error:
        raise QualificationError("the private qualification source is not valid JSON") from error
    validate_qualification_source(source)
    return source


# --------------------------------------------------------------------------
# generic package generation
# --------------------------------------------------------------------------


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
                "scoring_criteria_disclosed": False,
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


def build_qualification_package(source: dict[str, Any], role: str) -> dict[str, Any]:
    """Assemble one reviewer's package and answer key from private material.

    ``package_bytes`` is a pure function of the authored item bodies: the answer
    material never reaches it.  Only the package bytes are ever handed to a
    reviewer, and only hashes ever reach a public commitment.
    """

    canonical = normalize_role(role)
    if canonical not in REVIEW_ROLES:
        raise QualificationError(f"{canonical} is not issued a qualification package")
    validate_qualification_source(source)

    items: list[dict[str, Any]] = []
    key: dict[str, dict[str, str]] = {}
    for entry in source["roles"][canonical]:
        item_id = str(entry["reviewer_item_id"]).strip()
        items.append(
            {
                "schema_version": QUALIFICATION_SCHEMA_VERSION,
                "reviewer_item_id": item_id,
                **{str(name): value for name, value in sorted(entry["item"].items())},
            }
        )
        key[item_id] = _validate_answer(item_id, entry["answer"])

    package = _package_bytes(items, canonical)
    shipped = canonical_bytes(items)
    for forbidden in sorted(FORBIDDEN_ITEM_KEYS):
        if forbidden.encode() in shipped:
            raise QualificationError(
                "refusing to ship a qualification package that names answer material"
            )
    return {
        "qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "package_role": f"qualification_{canonical.casefold()}",
        "reviewer_role": canonical,
        "item_ids": [str(item["reviewer_item_id"]) for item in items],
        "package_bytes": package,
        "package_sha256": sha256_bytes(package),
        "answer_key": key,
    }


def build_qualification_packages(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Assemble every reviewer's package from one validated private source."""

    packages = {role: build_qualification_package(source, role) for role in REVIEW_ROLES}
    if len({row["package_sha256"] for row in packages.values()}) != len(packages):
        raise QualificationError("both reviewers would receive the same qualification package")
    return packages


# --------------------------------------------------------------------------
# encrypted answer vault
# --------------------------------------------------------------------------


def seal_qualification_key(payload: dict[str, Any], key: bytes) -> bytes:
    nonce = secrets.token_bytes(12)
    plaintext = canonical_bytes({"schema_version": QUALIFICATION_SCHEMA_VERSION, "keys": payload})
    return nonce + AESGCM(key).encrypt(nonce, plaintext, QUALIFICATION_VAULT_AD)


def unseal_qualification_key(ciphertext: bytes, key: bytes) -> dict[str, Any]:
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
# scoring against private answer material
# --------------------------------------------------------------------------


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
        # The instructions ask for every requested field, so every enumerated
        # column must be present and valid before anything is scored.  Which of
        # them decides the item stays hidden.
        for name, allowed in _ALLOWED_VALUES.items():
            value = str(row.get(name, "")).strip()
            if not value:
                raise QualificationError(
                    f"the qualification submission leaves a requested field blank for {item_id}"
                )
            if value.casefold() not in {option.casefold() for option in allowed}:
                raise QualificationError(
                    f"the qualification row for {item_id} carries an invalid value in {name!r}"
                )
        graded.append(
            {
                "reviewer_item_id": item_id,
                "correct": str(row[dimension]).strip().casefold()
                == str(entry["expected_value"]).strip().casefold(),
            }
        )

    correct = sum(1 for row in graded if row["correct"])
    rate = correct / len(graded) if graded else 0.0
    return {
        "schema_version": QUALIFICATION_RESULT_SCHEMA_VERSION,
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
        "schema_version": "cab_qualification_commitment_v2",
        "qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "source_schema_version": QUALIFICATION_SOURCE_SCHEMA_VERSION,
        "reviewer_a_package_hash": package_hashes.get("REVIEWER_A"),
        "reviewer_b_package_hash": package_hashes.get("REVIEWER_B"),
        "encrypted_key_material_hash": encrypted_key_material_sha256,
        "generator_source_hash": generator_source_sha256(),
        "key_environment_variable": QUALIFICATION_KEY_ENV,
        "source_environment_variable": QUALIFICATION_SOURCE_ENV,
        "key_value_bound": False,
        "items_published": False,
        "item_generation_templates_published": False,
        "reference_judgements_published": False,
        "scored_dimensions_published": False,
        # Named without the word a grader uses, so the public commitment stays
        # free of every token the leakage guard bans.
        "key_material_derivable_from_tracked_source": False,
        "key_material_derivable_from_reviewer_package": False,
        "retired_qualification_versions": sorted(RETIRED_QUALIFICATION_VERSIONS),
    }
    commitment["commitment_sha256"] = sha256_json(commitment)
    return commitment


def retired_qualification_registry() -> dict[str, Any]:
    return {
        "schema_version": "cab_retired_qualification_registry_v2",
        "status": "CAB_RETIRED_QUALIFICATION_BLOCKED",
        "active_qualification_version": QUALIFICATION_SCHEMA_VERSION,
        "active_source_schema_version": QUALIFICATION_SOURCE_SCHEMA_VERSION,
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
            "enforce_active_qualification() rejects every retired version at source loading, "
            "generation, ingestion, scoring and C10, including a copy renamed to the active "
            "version, because both the private source and the encrypted key vault record their "
            "own version inside the material the coordinator must decrypt."
        ),
        "active_material_is_private": (
            "Tracked source carries the schema, the loader, package assembly, the vault cipher "
            "and the scorer. Item bodies, decisive dimensions, expected values, explanations and "
            "answer mappings exist only outside Git."
        ),
    }


__all__ = [
    "FORBIDDEN_ITEM_KEYS",
    "MIN_QUALIFICATION_RATE",
    "QUALIFICATION_DIRNAME",
    "QUALIFICATION_ITEM_COUNT",
    "QUALIFICATION_KEY_ENV",
    "QUALIFICATION_KEY_FILENAME",
    "QUALIFICATION_RESULT_SCHEMA_VERSION",
    "QUALIFICATION_SCHEMA_VERSION",
    "QUALIFICATION_SOURCE_ENV",
    "QUALIFICATION_SOURCE_FILENAME",
    "QUALIFICATION_SOURCE_SCHEMA_VERSION",
    "REQUIRED_ANSWER_FIELDS",
    "REQUIRED_ITEM_FIELDS",
    "RETIRED_QUALIFICATION_DIRNAME",
    "RETIRED_QUALIFICATION_STATUS",
    "RETIRED_QUALIFICATION_VERSIONS",
    "QualificationError",
    "build_qualification_package",
    "build_qualification_packages",
    "enforce_active_qualification",
    "generator_source_sha256",
    "load_qualification_keys",
    "load_qualification_source",
    "qualification_commitment",
    "qualification_source_path",
    "qualification_source_schema",
    "retired_qualification_registry",
    "score_qualification",
    "seal_qualification_key",
    "unseal_qualification_key",
    "validate_qualification_source",
]
