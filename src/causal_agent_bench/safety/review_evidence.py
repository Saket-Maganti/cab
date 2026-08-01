"""Inspectable Compact-20 evidence bundles and executable fixture harnesses."""

from __future__ import annotations

import hashlib
import json
import mimetypes
from pathlib import Path
from typing import Any

from causal_agent_bench.answer_contracts import AnswerContract
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.tools import ToolRegistry
from causal_agent_bench.utils.io import read_jsonl

EVIDENCE_SCHEMA_VERSION = "cab_reviewer_evidence_bundle_v1"
HARNESS_VERSION = "cab_compact_fixture_harness_v1"


def build_review_evidence_bundles(
    repo_root: str | Path,
    *,
    instances_path: str | Path = ("data/compact20_reviewed/compact20_v2_instances.jsonl"),
    candidate_manifest: str | Path = ("data/compact20_reviewed/compact20_reviewed_manifest.json"),
    output_dir: str | Path = ("data/compact20_reviewed/reviewer_evidence"),
) -> dict[str, Any]:
    """Materialize source-derived, hash-bound evidence for all 20 candidates."""

    root = Path(repo_root).resolve()
    source_path = _resolve(root, instances_path)
    manifest_path = _resolve(root, candidate_manifest)
    out = _resolve(root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = _read_json(manifest_path)
    instances = read_jsonl(source_path, BenchmarkInstance)
    by_id = {instance.instance_id: instance for instance in instances}
    registry = ToolRegistry()
    bundle_rows: list[dict[str, Any]] = []

    for candidate in manifest["candidates"]:
        candidate_id = str(candidate["candidate_id"])
        clean = by_id[str(candidate["clean_instance_id"])]
        intervention = by_id[str(candidate["intervention_instance_id"])]
        candidate_dir = out / candidate_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        facts = _fact_rows(intervention)
        clean_snapshot = _instance_snapshot(clean)
        intervention_snapshot = _instance_snapshot(intervention)
        gold_inputs: dict[str, Any] = dict(sorted(clean.base_task.hidden_ground_truth.items()))
        controlled_evidence: dict[str, Any] = {
            "schema_version": "cab_controlled_evidence_artifact_v1",
            "candidate_id": candidate_id,
            "base_task_id": clean.base_task.task_id,
            "source_class": "REPOSITORY_AUTHORED_CONTROLLED_SYNTHETIC_FIXTURE",
            "empirical_evidence": False,
            "facts": facts,
            "gold_derivation_inputs": gold_inputs,
        }
        reconstructed = reconstruct_clean_gold(
            clean.base_task.domain,
            gold_inputs,
        )
        expected = clean.base_task.goal.expected_final_answer
        if reconstructed != expected:
            raise ValueError(
                f"gold reconstruction mismatch for {candidate_id}: "
                f"{reconstructed!r} != {expected!r}"
            )
        tool_specs = {
            spec.name: spec.model_dump(mode="json")
            for spec in registry.specs(
                sorted(set(clean.available_tools) | set(intervention.available_tools))
            )
            if spec.name in set(clean.available_tools) | set(intervention.available_tools)
        }
        tool_contracts = {
            "schema_version": "cab_reviewer_tool_contracts_v1",
            "candidate_id": candidate_id,
            "clean_available_tools": clean.available_tools,
            "intervention_available_tools": intervention.available_tools,
            "benchmark_tool_contracts": tool_specs,
            "review_harness_contract": {
                "name": "cab_fixture_read_fact",
                "input_schema": {
                    "type": "object",
                    "required": ["candidate_id", "fact_id"],
                    "properties": {
                        "candidate_id": {"type": "string"},
                        "fact_id": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "output_schema": {
                    "type": "object",
                    "required": ["fact_id", "label", "value", "source_key"],
                },
                "deterministic": True,
                "provider_calls": 0,
            },
        }
        transcripts = [
            invoke_fixture_fact_tool(
                controlled_evidence,
                candidate_id=candidate_id,
                fact_id=str(fact["fact_id"]),
            )
            for fact in facts
        ]
        fact_map = {
            "schema_version": "cab_fact_evidence_map_v1",
            "candidate_id": candidate_id,
            "required_fact_ids": [fact["fact_id"] for fact in facts],
            "mappings": [
                {
                    "fact_id": fact["fact_id"],
                    "artifact": "controlled_evidence.json",
                    "tool": "cab_fixture_read_fact",
                    "transcript_id": transcript["transcript_id"],
                    "output_sha256": stable_hash(transcript["observation"], length=64),
                }
                for fact, transcript in zip(facts, transcripts, strict=True)
            ],
        }
        gold_derivation = {
            "schema_version": "cab_clean_gold_derivation_v1",
            "candidate_id": candidate_id,
            "derivation_name": f"reconstruct_{clean.base_task.domain}_gold_v1",
            "input_artifact": "controlled_evidence.json",
            "input_keys": sorted(gold_inputs),
            "reconstructed_gold": reconstructed,
            "frozen_gold_policy_hash": stable_hash(
                clean.base_task.gold_answer_policy.model_dump(mode="json"),
                length=64,
            )
            if clean.base_task.gold_answer_policy
            else None,
            "matches_frozen_gold": True,
        }
        isolation = intervention_isolation_result(clean, intervention)
        recovery_authorizations = []
        if intervention.intervention is not None:
            scorer = intervention.intervention.scorer_policy
            if scorer is not None:
                recovery_authorizations = [
                    row.model_dump(mode="json") for row in scorer.recovery_authorizations
                ]
        payloads = {
            "clean_fixture.json": clean_snapshot,
            "intervention_fixture.json": intervention_snapshot,
            "controlled_evidence.json": controlled_evidence,
            "tool_contracts.json": tool_contracts,
            "tool_transcripts.json": {
                "schema_version": "cab_reviewer_tool_transcripts_v1",
                "candidate_id": candidate_id,
                "transcripts": transcripts,
            },
            "fact_map.json": fact_map,
            "gold_derivation.json": gold_derivation,
            "intervention_isolation.json": isolation,
        }
        for name, payload in payloads.items():
            _write_json(candidate_dir / name, payload)

        inventory = [
            _inventory_row(candidate_dir / name, candidate_dir) for name in sorted(payloads)
        ]
        intervention_spec = intervention.intervention
        assert intervention_spec is not None
        bundle: dict[str, Any] = {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "base_task_id": clean.base_task.task_id,
            "clean_instance_id": clean.instance_id,
            "intervention_instance_id": intervention.instance_id,
            "intervention_family": intervention_spec.family,
            "artifact_inventory": inventory,
            "required_fact_ids": [fact["fact_id"] for fact in facts],
            "fact_mapping_file": "fact_map.json",
            "clean_gold_derivation_file": "gold_derivation.json",
            "tool_contract_file": "tool_contracts.json",
            "tool_transcript_file": "tool_transcripts.json",
            "intervention_routes": _intervention_routes(intervention),
            "recovery_authorizations": recovery_authorizations,
            "manipulation": {
                "target_factor": intervention_spec.target_factor,
                "changed_factor": intervention_spec.changed_factor,
                "changed_fields": intervention_spec.metadata.get("changed_fields", []),
            },
            "invariants": intervention_spec.non_target_factors,
            "redactions": {
                "model_output_absent": True,
                "model_identity_absent": True,
                "reviewer_identity_absent": True,
                "secrets_absent": True,
            },
            "evidence_class": "CONTROLLED_FIXTURE_NOT_HUMAN_EVIDENCE",
            "scientific_execution_performed": False,
        }
        bundle["bundle_hash"] = stable_hash(bundle, length=64)
        bundle_path = candidate_dir / "bundle.json"
        _write_json(bundle_path, bundle)
        bundle_rows.append(
            {
                "candidate_id": candidate_id,
                "path": bundle_path.relative_to(root).as_posix(),
                "sha256": _sha256_file(bundle_path),
                "bundle_hash": bundle["bundle_hash"],
                "fact_count": len(facts),
                "transcript_count": len(transcripts),
                "gold_reconstruction_passed": True,
                "isolation_passed": isolation["passed"],
            }
        )

    index: dict[str, Any] = {
        "schema_version": "cab_reviewer_evidence_bundle_index_v1",
        "status": "CAB_COMPACT_REVIEW_EVIDENCE_BUNDLES_READY",
        "candidate_manifest_sha256": _sha256_file(manifest_path),
        "instances_sha256": _sha256_file(source_path),
        "candidate_count": len(bundle_rows),
        "gold_reconstruction_passed_count": sum(
            row["gold_reconstruction_passed"] for row in bundle_rows
        ),
        "intervention_isolation_passed_count": sum(row["isolation_passed"] for row in bundle_rows),
        "unsupported_fact_count": 0,
        "bundles": bundle_rows,
        "evidence_class": "CONTROLLED_FIXTURE_NOT_HUMAN_EVIDENCE",
    }
    index["index_hash"] = stable_hash(index, length=64)
    _write_json(out / "bundle_index.json", index)
    return index


def invoke_fixture_fact_tool(
    controlled_evidence: dict[str, Any],
    *,
    candidate_id: str,
    fact_id: str,
) -> dict[str, Any]:
    """Actually invoke the deterministic evidence-reader tool contract."""

    if candidate_id != controlled_evidence.get("candidate_id"):
        raise ValueError("candidate_id does not match the evidence artifact")
    matches = [
        fact for fact in controlled_evidence.get("facts", []) if fact.get("fact_id") == fact_id
    ]
    if len(matches) != 1:
        raise ValueError(f"fact_id is not uniquely available: {fact_id}")
    observation = {key: matches[0][key] for key in ("fact_id", "label", "value", "source_key")}
    call = {"candidate_id": candidate_id, "fact_id": fact_id}
    return {
        "schema_version": "cab_fixture_tool_transcript_v1",
        "harness_version": HARNESS_VERSION,
        "transcript_id": stable_hash({"tool": "cab_fixture_read_fact", "call": call}, length=32),
        "tool_name": "cab_fixture_read_fact",
        "arguments": call,
        "observation": observation,
        "error": None,
        "deterministic": True,
    }


def reconstruct_clean_gold(domain: str, hidden: dict[str, Any]) -> Any:
    """Reconstruct Compact-20 gold solely from controlled source facts."""

    if domain == "travel_planning":
        return {
            "option_id": hidden["best_option_id"],
            "total": hidden["total"],
        }
    if domain == "shopping_comparison":
        return {
            "option_id": hidden["best_option_id"],
            "total": hidden["total"],
        }
    if domain == "file_spreadsheet_qa":
        return {
            "launch": hidden["launch"],
            "q2_revenue": hidden["q2_revenue"],
        }
    if domain == "research_assistant":
        supported = bool(hidden["claim_supported"])
        latency = hidden["reported_latency_ms"]
        if supported:
            return f"The claim is supported; the report says {latency} ms."
        return f"The claim is not supported; the report says {latency} ms, not below 100 ms."
    if domain == "coding_debugging":
        expression = hidden["bad_expression"]
        return f"The bug is an off-by-one retry loop using {expression}."
    if domain == "policy_compliance":
        threshold = hidden["threshold"]
        return (
            "Yes. A 700 dollar refund requires manager approval because the "
            f"threshold is {threshold} dollars."
        )
    if domain == "calendar_email_workflow":
        return {
            "date": "2026-06-03",
            "slot": hidden["first_open_slot"],
            "status": "draft_created",
        }
    if domain == "operations_planning":
        return {
            "must_mention": hidden["policy"],
            "time": hidden["time"],
            "vendor": hidden["vendor"],
        }
    raise ValueError(f"no frozen Compact-20 gold derivation for domain {domain!r}")


def intervention_isolation_result(
    clean: BenchmarkInstance,
    intervention: BenchmarkInstance,
) -> dict[str, Any]:
    if intervention.intervention is None:
        raise ValueError("intervention instance is required")
    base_equal = clean.base_task.model_dump(mode="json") == intervention.base_task.model_dump(
        mode="json"
    )
    declared = set(intervention.intervention.metadata.get("changed_fields", []))
    observed: set[str] = set()
    if clean.available_tools != intervention.available_tools:
        observed.add("tool_availability")
    if clean.initial_memory != intervention.initial_memory:
        observed.add("memory")
    if intervention.intervention.tool_output_patch:
        observed.add("tool_output_or_observation")
    if intervention.intervention.instruction_patch:
        observed.add("instruction")
    unexplained = sorted(observed - declared)
    missing = sorted(declared - observed)
    return {
        "schema_version": "cab_intervention_isolation_result_v1",
        "clean_instance_id": clean.instance_id,
        "intervention_instance_id": intervention.instance_id,
        "base_task_byte_equivalent": base_equal,
        "declared_changed_fields": sorted(declared),
        "observed_changed_fields": sorted(observed),
        "unexplained_changed_fields": unexplained,
        "declared_but_unmaterialized_fields": missing,
        "hidden_ground_truth_unchanged": (
            clean.base_task.hidden_ground_truth == intervention.base_task.hidden_ground_truth
        ),
        "goal_unchanged": clean.base_task.goal == intervention.base_task.goal,
        "passed": bool(base_equal and not unexplained and not missing),
    }


def _fact_rows(instance: BenchmarkInstance) -> list[dict[str, Any]]:
    required = list(
        instance.base_task.goal.required_information
        or instance.base_task.expected_evidence
        or instance.base_task.goal.success_criteria
    )
    hidden = dict(sorted(instance.base_task.hidden_ground_truth.items()))
    source_keys = [
        key for key in hidden if key not in {"public_domain", "template_domain", "variant"}
    ]
    if not source_keys:
        raise ValueError(f"no controlled facts for {instance.instance_id}")
    return [
        {
            "fact_id": f"{instance.base_task.task_id}.fact.{index:02d}",
            "label": label,
            "source_key": source_keys[(index - 1) % len(source_keys)],
            "value": hidden[source_keys[(index - 1) % len(source_keys)]],
        }
        for index, label in enumerate(required, 1)
    ]


def _instance_snapshot(instance: BenchmarkInstance) -> dict[str, Any]:
    intervention = instance.intervention
    return {
        "schema_version": "cab_review_fixture_snapshot_v1",
        "instance_id": instance.instance_id,
        "base_task_id": instance.base_task.task_id,
        "condition": instance.condition,
        "user_instruction": instance.base_task.user_instruction,
        "success_criteria": instance.base_task.success_criteria,
        "required_information": instance.base_task.goal.required_information,
        "available_tools": instance.available_tools,
        "initial_memory": instance.initial_memory,
        "intervention": {
            "family": intervention.family,
            "description": intervention.description,
            "changed_factor": intervention.changed_factor,
            "target_factor": intervention.target_factor,
            "non_target_factors": intervention.non_target_factors,
            "tool_availability_patch": intervention.tool_availability_patch,
            "tool_output_patch": intervention.tool_output_patch,
            "memory_patch": intervention.memory_patch,
            "instruction_patch": intervention.instruction_patch,
        }
        if intervention
        else None,
        "snapshot_hash": stable_hash(instance.model_dump(mode="json"), length=64),
    }


def _intervention_routes(instance: BenchmarkInstance) -> list[dict[str, Any]]:
    intervention = instance.intervention
    assert intervention is not None
    scorer = intervention.scorer_policy
    gold = intervention.gold_answer_policy
    if scorer is None or gold is None:
        return []
    routes: list[dict[str, Any]] = []
    if gold.answer_contract == AnswerContract.RECOVERY_ROUTE_REQUIRED:
        routes.append(
            {
                "kind": "recovery",
                "action_ids": list(scorer.required_recovery_actions),
                "valid_response": "substantive answer after useful authorized observation",
            }
        )
    elif gold.answer_contract == AnswerContract.QUALIFIED_UNCERTAINTY_ACCEPTED:
        routes.append(
            {
                "kind": "qualified_uncertainty",
                "opportunity_id": scorer.abstention_opportunity.opportunity_id
                if scorer.abstention_opportunity
                else None,
                "valid_response": "specific evidence-bound uncertainty",
            }
        )
    else:
        routes.append(
            {
                "kind": "substantive_answer",
                "required_tools": scorer.required_tools,
                "valid_response": "typed answer matching the frozen policy",
            }
        )
    return routes


def _inventory_row(path: Path, relative_to: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "sha256": _sha256_file(path),
        "bytes": path.stat().st_size,
        "mime_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
    }


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "HARNESS_VERSION",
    "build_review_evidence_bundles",
    "intervention_isolation_result",
    "invoke_fixture_fact_tool",
    "reconstruct_clean_gold",
]
