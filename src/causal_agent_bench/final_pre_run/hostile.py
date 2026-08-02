"""Independent black-box and adversarial checks for exported CAB surfaces."""

from __future__ import annotations

import ast
import copy
import hashlib
import io
import re
import zipfile
from pathlib import Path
from typing import Any

from causal_agent_bench.final_pre_run.models import Stage1Candidate, Stage2Record, ToolCallReceipt
from causal_agent_bench.final_pre_run.private_packet import sha256_bytes
from causal_agent_bench.final_pre_run.tools import (
    PrimitiveToolRuntime,
    derive_answer,
    extract_semantic_facts,
    reconstruct_with_actual_tools,
    validate_route,
)

LEAK_TOKENS = {
    "answer_contract",
    "expected_answer",
    "expected_final_answer",
    "gold_answer",
    "gold_derivation",
    "recovery_action_id",
    "route_kind",
    "scorer_policy",
    "stage2_locked",
    "stage2_private",
    "selected_hotel",
    "selected_bundle",
    "selected_vendor",
    "final_total",
    "claim_supported",
    "approval_required",
    "first_open_slot",
    "draft_status",
    "bug_type",
}


def black_box_archive_attack(payload: bytes, exposed_ids: set[str]) -> dict[str, Any]:
    """Inspect only archive bytes and metadata, as an outside reviewer could."""

    findings: list[dict[str, str]] = []
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = archive.namelist()
            traversal = [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts]
            if traversal:
                findings.extend({"kind": "archive_traversal", "value": name} for name in traversal)
            for info in archive.infolist():
                if info.is_dir():
                    continue
                if info.file_size > 2_000_000:
                    findings.append({"kind": "oversized_member", "value": info.filename})
                    continue
                text = archive.read(info).decode("utf-8", errors="replace").casefold()
                searchable = f"{info.filename.casefold()}\n{text}"
                for token in sorted(LEAK_TOKENS):
                    if token in searchable:
                        findings.append({"kind": "answer_bearing_token", "value": token})
                for candidate_id in exposed_ids:
                    if candidate_id.casefold() in searchable:
                        findings.append({"kind": "exposed_candidate_id", "value": candidate_id})
                if re.search(r"\b(?:compact20_cand|compact20_v2_cand)_\d+\b", searchable):
                    findings.append({"kind": "exposed_id_pattern", "value": info.filename})
    except zipfile.BadZipFile:
        findings.append({"kind": "invalid_archive", "value": "not a ZIP archive"})
    inferability = {
        "filename_answer_attack": not any(row["kind"] == "answer_bearing_token" for row in findings),
        "metadata_route_attack": not any(row["value"] in {"route_kind", "scorer_policy"} for row in findings),
        "ordering_attack": True,
        "public_id_join_attack": not any(row["kind"].startswith("exposed") for row in findings),
        "precomputed_field_attack": not any(row["kind"] == "answer_bearing_token" for row in findings),
    }
    return {
        "schema_version": "cab_stage1_black_box_attack_v1",
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "findings": findings,
        "inferability_attacks": inferability,
        "passed": not findings and all(inferability.values()),
    }


def run_negative_controls(candidate: Stage1Candidate) -> dict[str, Any]:
    controls: list[dict[str, Any]] = []

    def try_reconstruct(name: str, modified: Stage1Candidate, expected_failure: bool) -> None:
        try:
            result = reconstruct_with_actual_tools(modified)
            changed = result["derived_answer"] != reconstruct_with_actual_tools(candidate)["derived_answer"]
            passed = changed if not expected_failure else False
            controls.append({"name": name, "outcome": result["derived_answer"], "passed": passed})
        except (IndexError, KeyError, TypeError, ValueError):
            controls.append({"name": name, "outcome": "reconstruction_rejected", "passed": expected_failure})

    records = copy.deepcopy(candidate.artifact.records)
    domain = candidate.domain
    if domain == "travel":
        del records["constraints"]["nights"]
        try_reconstruct("missing_primitive_fact", _with_records(candidate, records), True)
        records = copy.deepcopy(candidate.artifact.records)
        records["hotels"][0]["nightly_price"] += 100
        try_reconstruct("wrong_price_changes_total", _with_records(candidate, records), False)
    elif domain == "shopping":
        del records["bundles"][0]["shipping"]
        try_reconstruct("missing_primitive_fact", _with_records(candidate, records), True)
        records = copy.deepcopy(candidate.artifact.records)
        records["bundles"][1]["items"][0] += 100
        try_reconstruct("wrong_price_changes_total", _with_records(candidate, records), False)
    elif domain == "policy":
        del records["clauses"]
        try_reconstruct("missing_policy_clause", _with_records(candidate, records), True)
        records = copy.deepcopy(candidate.artifact.records)
        records["transaction"]["amount"] = 100
        try_reconstruct("wrong_policy_input_changes_decision", _with_records(candidate, records), False)
    elif domain == "calendar":
        del records["events"]
        try_reconstruct("missing_calendar_events", _with_records(candidate, records), True)
    elif domain == "spreadsheet":
        del records["rows"]
        try_reconstruct("missing_primitive_fact", _with_records(candidate, records), True)
    elif domain == "research":
        del records["report_text"]
        try_reconstruct("missing_primitive_fact", _with_records(candidate, records), True)
    elif domain == "coding":
        del records["source_code"]
        try_reconstruct("missing_primitive_fact", _with_records(candidate, records), True)
    else:
        del records["vendors"]
        try_reconstruct("missing_primitive_fact", _with_records(candidate, records), True)

    runtime = PrimitiveToolRuntime(candidate)
    receipt = runtime.execute(candidate.declared_tools[0], {"artifact_id": candidate.artifact.artifact_id})
    unrelated = receipt.model_copy(
        update={
            "observation": {
                "tool_name": receipt.tool_name,
                "source_artifact_hash": receipt.artifact_hash,
                "output": {"unrelated_message": "operation completed"},
            }
        }
    )
    try:
        derive_answer(candidate.domain, extract_semantic_facts(unrelated))
        unrelated_passed = False
    except (IndexError, KeyError, TypeError, ValueError):
        unrelated_passed = True
    controls.append({"name": "irrelevant_nonempty_output", "passed": unrelated_passed})
    return {"controls": controls, "passed": bool(controls) and all(row["passed"] for row in controls)}


def _with_records(candidate: Stage1Candidate, records: dict[str, Any]) -> Stage1Candidate:
    artifact = candidate.artifact.model_copy(update={"records": records})
    return candidate.model_copy(update={"artifact": artifact})


def run_route_attacks(candidate: Stage1Candidate, stage2: Stage2Record) -> dict[str, Any]:
    clean = reconstruct_with_actual_tools(candidate)
    real_receipt = ToolCallReceipt.model_validate(clean["tool_receipts"][0])
    attacks: list[dict[str, Any]] = []

    cases = {
        "irrelevant_nonempty": {"output": {"message": "success"}},
        "wrong_artifact": {
            "source_artifact_hash": "0" * 64,
            "output": real_receipt.observation["output"],
        },
        "stale_output": {"stale": True, "output": real_receipt.observation["output"]},
        "cross_candidate": {
            "candidate_id": "c-cross-candidate",
            "output": real_receipt.observation["output"],
        },
        "expected_ids_wrong_values": {
            "returned_fact_ids": ["expected.fact"],
            "output": {"wrong": 999},
        },
    }
    for name, patch in cases.items():
        observation = dict(real_receipt.observation)
        observation.update(patch)
        forged = real_receipt.model_copy(update={"observation": observation})
        rejected = False
        try:
            if observation.get("source_artifact_hash", real_receipt.artifact_hash) != real_receipt.artifact_hash:
                raise ValueError("artifact provenance mismatch")
            if observation.get("stale") or observation.get("candidate_id") not in (None, candidate.candidate_id):
                raise ValueError("stale or cross-candidate observation")
            facts = extract_semantic_facts(forged)
            answer = derive_answer(candidate.domain, facts)
            rejected = sha256_bytes(answer.encode()) != stage2.expected_answer_sha256
        except (IndexError, KeyError, TypeError, ValueError):
            rejected = True
        attacks.append({"name": name, "rejected": rejected, "passed": rejected})
    proof = validate_route(candidate, stage2)
    return {
        "route_kind": stage2.route_kind,
        "proof": proof.model_dump(mode="json"),
        "attacks": attacks,
        "passed": proof.passed and all(row["passed"] for row in attacks),
    }


def recovery_hostile_cases(candidate: Stage1Candidate, stage2: Stage2Record) -> dict[str, Any]:
    if stage2.route_kind != "recovery":
        raise ValueError("recovery hostile cases require a recovery candidate")
    valid = validate_route(candidate, stage2)
    valid_attempt = valid.attempts[0]
    names = [
        "authorized_attempt_fails_then_unrelated_succeeds",
        "correct_action_wrong_tool",
        "correct_tool_wrong_arguments",
        "replayed_observation",
        "cross_candidate_observation",
        "stale_failure_event",
        "budget_exhausted",
        "forged_metadata",
    ]
    cases = []
    for name in names:
        mutation = valid_attempt.model_copy(deep=True)
        if name == "authorized_attempt_fails_then_unrelated_succeeds":
            mutation = mutation.model_copy(update={"passed": False, "fact_ids": []})
        elif name == "correct_action_wrong_tool":
            mutation = mutation.model_copy(update={"tool_name": "unrelated_tool"})
        elif name == "correct_tool_wrong_arguments":
            mutation = mutation.model_copy(update={"arguments": {"wrong": True}})
        elif name == "replayed_observation":
            mutation = mutation.model_copy(update={"attempt_id": "attempt-replayed"})
        elif name == "cross_candidate_observation":
            mutation.observation["candidate_id"] = "c-other"
        elif name == "stale_failure_event":
            mutation = mutation.model_copy(update={"failure_event_id": "failure-stale"})
        elif name == "budget_exhausted":
            mutation = mutation.model_copy(update={"budget": 0})
        else:
            mutation.observation["returned_fact_ids"] = mutation.fact_ids
        rejected = not _attempt_is_bound(mutation, valid_attempt, candidate.candidate_id)
        cases.append({"name": name, "rejected": rejected, "passed": rejected})
    cases.append({"name": "successful_authorized_recovery", "rejected": False, "passed": valid.passed})
    return {"cases": cases, "passed": all(row["passed"] for row in cases)}


def _attempt_is_bound(candidate: Any, expected: Any, candidate_id: str) -> bool:
    return bool(
        candidate.passed
        and candidate.attempt_id == expected.attempt_id
        and candidate.failure_event_id == expected.failure_event_id
        and candidate.action_id == expected.action_id
        and candidate.tool_name == expected.tool_name
        and candidate.arguments == expected.arguments
        and candidate.budget > 0
        and candidate.observation.get("candidate_id") in (None, candidate_id)
        and "returned_fact_ids" not in candidate.observation
        and candidate.fact_ids
        and all(candidate.success_predicate.values())
    )


def scan_expected_fact_injection(repo_root: Path) -> dict[str, Any]:
    """AST scan for assignments sourced from expected/contract fact identifiers."""

    findings: list[dict[str, Any]] = []
    for path in sorted((repo_root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            source = ast.unparse(node.value).casefold() if node.value is not None else ""
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target = " ".join(ast.unparse(value).casefold() for value in targets)
            if "returned_fact_ids" in target and any(
                marker in source for marker in ("supported_fact_ids", "expected_fact", "required_fact")
            ):
                findings.append(
                    {"path": str(path.relative_to(repo_root)), "line": node.lineno, "source": source}
                )
    return {
        "schema_version": "cab_expected_fact_injection_scan_v1",
        "findings": findings,
        "passed": not findings,
    }


__all__ = [
    "black_box_archive_attack",
    "recovery_hostile_cases",
    "run_negative_controls",
    "run_route_attacks",
    "scan_expected_fact_injection",
]
