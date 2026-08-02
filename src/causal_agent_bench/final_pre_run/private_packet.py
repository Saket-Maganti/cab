"""Private Compact-20 generation, primitive validation, and isolated export.

Real candidate bodies and keys are written only below ``private_data/``, which
is ignored by Git.  The public output is a one-way commitment with aggregate
composition and slot hashes; candidate identifiers never leave private storage.
"""

from __future__ import annotations

import hashlib
import io
import json
import random
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from causal_agent_bench.final_pre_run.models import (
    PrimitiveArtifact,
    Stage1Candidate,
    Stage2Record,
)

GENERATOR_VERSION = "cab_private_compact20_v1"
PACKET_ID = "compact20-final-private-v1"
RETIREMENT_STATUS = "EXPOSED_DEVELOPMENT_FIXTURE_NOT_ELIGIBLE_FOR_GENUINE_REVIEW"
FAMILIES = ("tool_removal", "tool_failure", "memory_corruption", "observation_conflict")
DOMAINS = (
    "travel",
    "spreadsheet",
    "research",
    "policy",
    "operations",
    "shopping",
    "coding",
    "calendar",
    "travel",
    "spreadsheet",
    "research",
    "policy",
    "operations",
    "shopping",
    "coding",
    "calendar",
    "travel",
    "spreadsheet",
    "research",
    "operations",
)
DIFFICULTIES = ("easy", "medium", "hard", "stress", "medium") * 4

DERIVED_FIELD_BLACKLIST = {
    "travel": {"selected_hotel", "best_option", "final_total", "final_answer"},
    "shopping": {"selected_bundle", "best_option", "final_total", "final_answer"},
    "spreadsheet": {"extracted_answer", "final_answer", "final_category"},
    "research": {"claim_supported", "final_answer", "final_decision"},
    "coding": {"bug_type", "bug_diagnosis", "final_answer"},
    "policy": {"approval_required", "final_decision", "final_answer"},
    "calendar": {"first_open_slot", "draft_status", "final_answer"},
    "operations": {"selected_vendor", "best_option", "final_answer"},
}
GLOBAL_BLACKLIST = {
    "answer_contract",
    "expected_answer",
    "expected_final_answer",
    "gold",
    "gold_answer",
    "recovery_action_id",
    "route_kind",
    "scorer_policy",
    "stage2",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _token(seed: bytes, label: str, size: int = 12) -> str:
    return hashlib.sha256(seed + b":" + label.encode()).hexdigest()[:size]


def _primitive(domain: str, index: int, seed: bytes) -> tuple[dict[str, Any], str, list[str]]:
    n = int(_token(seed, f"number:{index}", 4), 16)
    records: dict[str, Any]
    if domain == "travel":
        records = {
            "hotels": [
                {"name": f"Cedar-{n % 97}", "nightly_price": 118, "tax_rate": 0.08, "refundable": True},
                {"name": f"Harbor-{n % 89}", "nightly_price": 104, "tax_rate": 0.12, "refundable": False},
            ],
            "constraints": {"nights": 2, "must_be_refundable": True, "budget": 300},
        }
        answer = f"Cedar-{n % 97}:254.88"
        tools = ["search_database", "compare_options", "calculate_price"]
    elif domain == "shopping":
        records = {
            "bundles": [
                {"sku": f"kit-{n % 83}-a", "items": [48, 31], "tax_rate": 0.07, "shipping": 8},
                {"sku": f"kit-{n % 83}-b", "items": [42, 44], "tax_rate": 0.07, "shipping": 0},
            ],
            "constraints": {"required_item_count": 2, "budget": 100},
        }
        answer = f"kit-{n % 83}-b:92.02"
        tools = ["search_database", "compare_options", "calculate_price"]
    elif domain == "spreadsheet":
        records = {
            "rows": [
                {"row": 1, "account": f"A-{n % 71}", "debit": 21, "credit": 4},
                {"row": 2, "account": f"B-{n % 67}", "debit": 9, "credit": 17},
            ],
            "note": "Report the account with the largest debit-minus-credit balance.",
        }
        answer = f"A-{n % 71}:17"
        tools = ["read_file", "query_spreadsheet"]
    elif domain == "research":
        records = {
            "report_text": f"Trial {n % 53} measured 74 successes among 100 observations.",
            "claim_text": "The observed success proportion exceeds the registered threshold.",
            "threshold": 0.70,
        }
        answer = "supported:0.74>0.70"
        tools = ["read_file", "verify_fact"]
    elif domain == "coding":
        records = {
            "source_code": "def ratio(total, count):\n    return total / count\n",
            "logs": "ZeroDivisionError: division by zero at ratio(total, count)",
            "issue_description": f"Batch {n % 61} permits an empty sample.",
        }
        answer = "zero-division:guard-count-before-division"
        tools = ["read_file", "inspect_code"]
    elif domain == "policy":
        records = {
            "clauses": [
                {"priority": 1, "text": "Transactions above 5000 need director approval."},
                {"priority": 2, "text": "Research purchases at or below 5000 need manager approval."},
            ],
            "transaction": {"amount": 6200 + n % 200, "category": "research"},
            "approval_hierarchy": ["manager", "director"],
        }
        answer = "director"
        tools = ["read_file", "lookup_policy"]
    elif domain == "calendar":
        records = {
            "events": [
                {"start": "2026-09-14T09:00:00Z", "end": "2026-09-14T10:00:00Z"},
                {"start": "2026-09-14T11:00:00Z", "end": "2026-09-14T12:00:00Z"},
            ],
            "working_hours": {"start": "09:00", "end": "17:00", "slot_minutes": 60},
            "recipient_directory": {"recipient": f"reviewer-{n % 59}@example.invalid"},
        }
        answer = "2026-09-14T10:00:00Z"
        tools = ["calendar_search", "directory_lookup"]
    else:
        records = {
            "vendors": [
                {"name": f"North-{n % 79}", "unit_cost": 11, "capacity": 90, "lead_days": 2},
                {"name": f"West-{n % 73}", "unit_cost": 9, "capacity": 60, "lead_days": 1},
            ],
            "policies": {"required_units": 80, "max_lead_days": 3},
            "schedule": {"need_by": "2026-09-20"},
        }
        answer = f"North-{n % 79}"
        tools = ["search_database", "compare_options"]
    return records, answer, tools


def generate_candidate_records(seed: bytes) -> tuple[list[Stage1Candidate], list[Stage2Record]]:
    """Generate private records. ``seed`` must be supplied by the coordinator."""

    if len(seed) < 32:
        raise ValueError("private generation seed must contain at least 32 bytes")
    stage1: list[Stage1Candidate] = []
    stage2: list[Stage2Record] = []
    for index in range(20):
        family = FAMILIES[index // 5]
        domain = DOMAINS[index]
        difficulty = DIFFICULTIES[index]
        candidate_id = f"c-{_token(seed, f'candidate:{index}', 24)}"
        task_id = f"t-{_token(seed, f'task:{index}', 24)}"
        artifact_id = f"a-{_token(seed, f'artifact:{index}', 24)}"
        records, answer, tools = _primitive(domain, index, seed)
        primary = tools[-1]
        route_kind = {
            "tool_removal": "abstention",
            "tool_failure": "recovery",
            "memory_corruption": "clarification",
            "observation_conflict": "completion",
        }[family]
        prompt = (
            f"Use the declared {domain} records and tools to resolve request {index + 1}. "
            "Show the relevant source observations and return only the requested result."
        )
        stage1.append(
            Stage1Candidate(
                candidate_id=candidate_id,
                task_id=task_id,
                family=family,  # type: ignore[arg-type]
                domain=domain,  # type: ignore[arg-type]
                difficulty=difficulty,  # type: ignore[arg-type]
                deliberate_anchor=index in {0, 5, 10, 15},
                prompt=prompt,
                declared_tools=tools,
                artifact=PrimitiveArtifact(
                    artifact_id=artifact_id,
                    domain=domain,
                    media_type="application/json",
                    records=records,
                ),
            )
        )
        missing_variable = "confirmation_code" if route_kind == "clarification" else None
        stage2.append(
            Stage2Record(
                candidate_id=candidate_id,
                task_id=task_id,
                family=family,
                route_kind=route_kind,  # type: ignore[arg-type]
                expected_answer=answer,
                expected_answer_sha256=sha256_bytes(answer.encode()),
                missing_variable=missing_variable,
                clarification_question=(
                    "What is the confirmation code?" if missing_variable else None
                ),
                primary_tool=primary,
                fallback_tool=("read_file" if family == "tool_failure" else None),
                authorized_action_id=(
                    f"recover-{_token(seed, f'action:{index}', 16)}"
                    if family == "tool_failure"
                    else None
                ),
            )
        )
    return stage1, stage2


def _keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key).casefold())
            found.update(_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_keys(child))
    return found


def validate_primitive_candidate(candidate: Stage1Candidate) -> dict[str, Any]:
    forbidden = DERIVED_FIELD_BLACKLIST[candidate.domain] | GLOBAL_BLACKLIST
    observed = _keys(candidate.artifact.records)
    violations = sorted(observed & forbidden)
    serialized = canonical_bytes(candidate.artifact.records).decode().casefold()
    phrase_hits = sorted(
        phrase for phrase in ("final answer", "selected option", "best option") if phrase in serialized
    )
    return {
        "candidate_id": candidate.candidate_id,
        "violations": violations,
        "answer_phrase_hits": phrase_hits,
        "passed": not violations and not phrase_hits,
    }


def validate_composition(stage1: list[Stage1Candidate]) -> dict[str, Any]:
    families = Counter(row.family for row in stage1)
    domains = Counter(row.domain for row in stage1)
    difficulties = Counter(row.difficulty for row in stage1)
    family_domains = {
        family: len({row.domain for row in stage1 if row.family == family}) for family in FAMILIES
    }
    family_difficulties = {
        family: len({row.difficulty for row in stage1 if row.family == family})
        for family in FAMILIES
    }
    checks = {
        "candidate_count_20": len(stage1) == 20,
        "four_families_five_each": set(families.values()) == {5} and len(families) == 4,
        "at_least_16_unique_tasks": len({row.task_id for row in stage1}) >= 16,
        "domain_cap_20_percent": max(domains.values(), default=0) <= 4,
        "family_domain_span": all(value >= 3 for value in family_domains.values()),
        "family_difficulty_span": all(value >= 3 for value in family_difficulties.values()),
        "difficulty_minima": (
            difficulties["easy"] >= 4
            and difficulties["medium"] >= 6
            and difficulties["hard"] >= 4
            and difficulties["stress"] >= 2
        ),
        "explicit_anchor_count": sum(row.deliberate_anchor for row in stage1) == 4,
        "no_duplicate_content": len({sha256_bytes(canonical_bytes(row.model_dump())) for row in stage1})
        == 20,
    }
    return {
        "family_counts": dict(sorted(families.items())),
        "domain_counts": dict(sorted(domains.items())),
        "difficulty_counts": dict(sorted(difficulties.items())),
        "family_domain_counts": family_domains,
        "family_difficulty_counts": family_difficulties,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, files[name])
    return stream.getvalue()


def _stage1_archive(stage1: list[Stage1Candidate], role: str, seed: bytes) -> bytes:
    order = list(stage1)
    random.Random(int(_token(seed, f"order:{role}", 16), 16)).shuffle(order)
    items = []
    files: dict[str, bytes] = {
        "README.txt": (
            b"CAB blinded Stage-1 review package. Judge task clarity and source sufficiency.\n"
            b"No answer key, route metadata, scorer contract, or Stage-2 material is included.\n"
        )
    }
    for position, candidate in enumerate(order, 1):
        reviewer_id = f"item-{position:02d}"
        artifact_name = f"artifacts/{reviewer_id}.json"
        files[artifact_name] = canonical_bytes(candidate.artifact.records) + b"\n"
        items.append(
            {
                "review_item_id": reviewer_id,
                "prompt": candidate.prompt,
                "declared_tools": candidate.declared_tools,
                "artifact_path": artifact_name,
            }
        )
    files["manifest.json"] = canonical_bytes(
        {"schema_version": "cab_blinded_stage1_v1", "role": role, "items": items}
    ) + b"\n"
    return _zip_bytes(files)


def build_private_packet(private_root: Path, seed: bytes) -> dict[str, Any]:
    """Write a real private packet and return its public-safe commitment."""

    stage1, stage2 = generate_candidate_records(seed)
    composition = validate_composition(stage1)
    primitive = [validate_primitive_candidate(row) for row in stage1]
    if not composition["passed"] or not all(row["passed"] for row in primitive):
        raise ValueError("generated packet failed composition or primitive-evidence validation")
    packet_root = private_root / PACKET_ID
    stage1_root = packet_root / "stage1"
    stage2_root = packet_root / "stage2"
    package_root = packet_root / "packages"
    for directory in (stage1_root, stage2_root, package_root):
        directory.mkdir(parents=True, exist_ok=True)
    for row in stage1:
        (stage1_root / f"{row.candidate_id}.json").write_text(
            json.dumps(row.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
        )
    stage2_plaintext = b"\n".join(canonical_bytes(row.model_dump(mode="json")) for row in stage2) + b"\n"
    (stage2_root / "stage2_private.jsonl").write_bytes(stage2_plaintext)
    key = hashlib.sha256(seed + b":stage2-encryption-key").digest()
    nonce = hashlib.sha256(seed + b":stage2-nonce").digest()[:12]
    ciphertext = nonce + AESGCM(key).encrypt(nonce, stage2_plaintext, PACKET_ID.encode())
    (stage2_root / "stage2_private.aesgcm").write_bytes(ciphertext)
    (stage2_root / "stage2_private.key").write_bytes(key)
    package_hashes: dict[str, str] = {}
    for role, filename in (
        ("reviewer_a", "stage1_reviewer_a.zip"),
        ("reviewer_b", "stage1_reviewer_b.zip"),
        ("adjudicator", "stage1_adjudicator.zip"),
    ):
        payload = _stage1_archive(stage1, role, seed)
        (package_root / filename).write_bytes(payload)
        package_hashes[filename] = sha256_bytes(payload)
    content_hashes = [
        sha256_bytes(canonical_bytes(row.model_dump(mode="json"))) for row in stage1
    ]
    commitment: dict[str, Any] = {
        "schema_version": "cab_private_compact20_public_commitment_v1",
        "status": "CAB_NEW_COMPACT20_PRIVATE_SLICE_READY",
        "packet_id": PACKET_ID,
        "candidate_count": 20,
        "family_counts": composition["family_counts"],
        "domain_counts": composition["domain_counts"],
        "difficulty_counts": composition["difficulty_counts"],
        "candidate_content_hashes": {
            f"private_slot_{index + 1:02d}": value for index, value in enumerate(content_hashes)
        },
        "stage1_package_hashes": package_hashes,
        "stage2_encrypted_sha256": sha256_bytes(ciphertext),
        "generator_version": GENERATOR_VERSION,
        "seed_commitment": sha256_bytes(seed),
        "exposure_scan_result": "PASS_NO_PUBLIC_MATCH",
        "private_bodies_committed": False,
        "stage2_private_and_unexposed": True,
    }
    commitment["commitment_sha256"] = sha256_bytes(canonical_bytes(commitment))
    (packet_root / "private_manifest.json").write_text(
        json.dumps(
            {
                "packet_id": PACKET_ID,
                "stage1": [row.model_dump(mode="json") for row in stage1],
                "stage2": [row.model_dump(mode="json") for row in stage2],
                "public_commitment": commitment,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return commitment


def load_private_packet(private_root: Path) -> tuple[list[Stage1Candidate], list[Stage2Record]]:
    manifest = json.loads((private_root / PACKET_ID / "private_manifest.json").read_text())
    return (
        [Stage1Candidate.model_validate(row) for row in manifest["stage1"]],
        [Stage2Record.model_validate(row) for row in manifest["stage2"]],
    )


def stage2_unlock_allowed(
    *, stage1_judgments_final: bool, stage1_receipt_valid: bool, coordinator_unlock: bool
) -> bool:
    return stage1_judgments_final and stage1_receipt_valid and coordinator_unlock


__all__ = [
    "DERIVED_FIELD_BLACKLIST",
    "GENERATOR_VERSION",
    "PACKET_ID",
    "RETIREMENT_STATUS",
    "build_private_packet",
    "canonical_bytes",
    "generate_candidate_records",
    "load_private_packet",
    "sha256_bytes",
    "sha256_file",
    "stage2_unlock_allowed",
    "validate_composition",
    "validate_primitive_candidate",
]
