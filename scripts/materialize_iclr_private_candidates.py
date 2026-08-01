#!/usr/bin/env python3
"""Materialize private ICLR candidate tasks and a public-safe commitment.

The authoring packet and secret seed must live below an ignored private root.
The generated public manifest contains aggregate counts and cryptographic file
commitments only—never IDs, task text, answers, patches, or evaluator fields.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import secrets
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.analysis.assignment_balance import (
    ASSIGNMENT_DESIGN_VERSION,
    assignment_balance_diagnostics,
    constrained_rotation_assignments,
)
from causal_agent_bench.answer_contracts import AnswerContract
from causal_agent_bench.generation.transfer_artifacts import (
    STUDY_NAME as TRANSFER_STUDY_NAME,
)
from causal_agent_bench.generation.transfer_artifacts import (
    aggregate_artifact_inventory,
    materialize_transfer_bundle,
)
from causal_agent_bench.safety.iclr_dataset_audit import (
    INTERVENTION_FAMILIES,
    diversity_audit,
    naturalistic_safety_audit,
    public_safe_manifest,
    read_jsonl_objects,
)

REVIEW_DIMENSIONS = (
    "task_clarity",
    "clean_gold_correctness",
    "manipulation_success",
    "goal_preservation",
    "invariance_preservation",
    "solvability",
    "answer_contract_correctness",
    "scorer_compatibility",
    "realism",
    "ambiguity",
    "exclusion_recommendation",
)

MANIPULATION_CHECKS = {
    "tool_removal": "required tool is absent from the observable tool registry",
    "tool_failure": "designated tool deterministically returns the injected failure",
    "tool_corruption": "designated output violates its declared content contract",
    "irrelevant_tools": "distractor tools are present and target tools are unchanged",
    "memory_corruption": "seeded memory contradicts a verifiable artifact fact",
    "observation_conflict": "two observable sources make explicitly conflicting claims",
    "ambiguous_instruction": "a material decision is under-specified and clarification is possible",
    "long_horizon_dependency": "a later step depends on evidence from an earlier observable step",
    "premature_success_signal": "an intermediate success marker appears before required evidence",
    "distractor_evidence": "a plausible irrelevant artifact is present beside decisive evidence",
}

PRIOR_PUBLIC_MANIFEST_SHA256 = {
    "scale100_confirmatory_v2": "58419ef66881ffeccbfd15b59961b91dc562d3cdc460f02e3248db2293a95e91",
    "naturalistic_transfer_v2": "09d42c22c516eb7a8fa1ef248f3fa7c072de8589c7847b7181018b956fbfa569",
}


def initialize_private_seed(path: Path) -> Path:
    """Create a private seed once; refuse overwrite."""

    if path.exists():
        raise ValueError(f"refusing to overwrite existing private seed: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(secrets.token_hex(32) + "\n", encoding="utf-8")
    return path


def materialize(
    authoring_path: str | Path,
    seed_path: str | Path,
    output_dir: str | Path,
    public_manifest_path: str | Path,
) -> dict[str, Any]:
    authoring_file = Path(authoring_path).resolve()
    seed_file = Path(seed_path).resolve()
    private_output = Path(output_dir).resolve()
    public_output = Path(public_manifest_path).resolve()
    _require_private_path(authoring_file)
    _require_private_path(seed_file)
    _require_private_path(private_output)
    packet = _read_packet(authoring_file)
    seed = seed_file.read_text(encoding="utf-8").strip()
    if len(seed) < 32:
        raise ValueError("private seed must contain at least 32 characters")
    tasks = packet["tasks"]
    _validate_authoring(packet)
    family_order = list(MANIPULATION_CHECKS)
    assignments = constrained_rotation_assignments(
        tasks,
        family_order,
        block_size=5,
    )
    assignment_balance = assignment_balance_diagnostics(
        tasks,
        assignments,
        families=family_order,
    )
    if not assignment_balance["passed"]:
        failed = sorted(
            key
            for key, value in assignment_balance["checks"].items()
            if not value
        )
        raise ValueError(f"confirmatory assignment balance failed: {failed}")

    private_output.mkdir(parents=True, exist_ok=True)
    materialized: list[dict[str, Any]] = []
    artifact_bundles: list[dict[str, Any]] = []
    for index, (authored, assigned_families) in enumerate(
        zip(tasks, assignments, strict=True)
    ):
        private_id = _private_id(
            seed,
            str(packet["split_role"]),
            index,
            str(authored["scenario_key"]),
        )
        task = _materialized_task(
            authored,
            task_id=private_id,
            split_role=str(packet["split_role"]),
            dataset_id=str(packet["dataset_id"]),
            families=assigned_families,
            block_index=index,
        )
        if str(packet["dataset_id"]) == "naturalistic_transfer_v2":
            bundle_relative = Path("artifacts") / private_id
            bundle = materialize_transfer_bundle(
                task,
                private_output / bundle_relative,
            )
            task["artifact_spec"].update(
                {
                    "artifact_class": "artifact_rich_synthetic",
                    "files": [
                        (bundle_relative / relative).as_posix()
                        for relative in bundle["clean_relative_files"]
                    ],
                    "artifact_manifest": (
                        bundle_relative / "artifact_manifest.json"
                    ).as_posix(),
                    "artifact_manifest_sha256": bundle["manifest_sha256"],
                    "bundle_root_sha256": bundle["bundle_root_sha256"],
                    "gold_derivation_parser": "parse_transfer_bundle",
                }
            )
            task["metadata"].update(
                {
                    "study_name": TRANSFER_STUDY_NAME,
                    "task_style": "artifact_rich_synthetic",
                    "real_world_origin_claimed": False,
                    "human_review_state": (
                        "HUMAN_INPUT_REQUIRED_AFTER_MATERIALIZATION"
                    ),
                }
            )
            artifact_bundles.append(
                {
                    **bundle,
                    "task_id": private_id,
                    "bundle_path": bundle_relative.as_posix(),
                }
            )
        task["metadata"]["content_hash"] = _content_hash(task)
        materialized.append(task)

    candidate_path = private_output / "candidate_tasks.jsonl"
    _write_jsonl(candidate_path, materialized)
    review_items_path = private_output / "human_review_items.jsonl"
    _write_review_items(review_items_path, materialized)
    review_csv_path = private_output / "human_review_judgments.csv"
    _write_blank_review_csv(review_csv_path, materialized)
    assignment_balance_path = private_output / "assignment_balance.json"
    assignment_balance_path.write_text(
        json.dumps(assignment_balance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    artifact_inventory_public = (
        aggregate_artifact_inventory(artifact_bundles)
        if str(packet["dataset_id"]) == "naturalistic_transfer_v2"
        else {
            "schema_version": "cab_transfer_artifact_inventory_v1",
            "study_name": str(packet["dataset_id"]),
            "artifact_class": "not_applicable",
            "bundle_count": 0,
            "artifact_file_count": 0,
            "format_counts": {},
            "all_gold_derivations_match": True,
            "real_world_origin_claimed": False,
            "human_review_state": "HUMAN_INPUT_REQUIRED",
        }
    )
    artifact_inventory = {
        **artifact_inventory_public,
        "applicable": str(packet["dataset_id"]) == "naturalistic_transfer_v2",
        "bundles": [
            {
                "task_id": bundle["task_id"],
                "bundle_path": bundle["bundle_path"],
                "manifest_sha256": bundle["manifest_sha256"],
                "bundle_root_sha256": bundle["bundle_root_sha256"],
                "clean_relative_files": bundle["clean_relative_files"],
            }
            for bundle in artifact_bundles
        ],
    }
    artifact_inventory_path = private_output / "artifact_inventory.json"
    artifact_inventory_path.write_text(
        json.dumps(artifact_inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    diversity = diversity_audit(
        materialized,
        comparison_roles=_public_comparison_roles(),
    )
    safety = naturalistic_safety_audit(materialized)
    if diversity["unique_task_id_count"] != packet["target_count"]:
        raise ValueError("materialized candidate IDs are not unique")
    if diversity["normalized_instruction_pattern_count"] != packet["target_count"]:
        raise ValueError(
            "authoring packet contains normalized instruction reuse; "
            "refusing superficial candidate materialization"
        )
    if diversity["genuinely_distinct_lower_bound"] < int(packet["target_count"] * 0.9):
        raise ValueError("genuinely distinct lower bound is below 90% of target")
    if not safety["static_passed"]:
        raise ValueError(
            "candidate failed static privacy/injection/label safety: "
            f"{safety['blocker_counts']}"
        )

    private_manifest = {
        "schema_version": "cab_private_candidate_manifest_v2",
        "dataset_id": packet["dataset_id"],
        "split_role": packet["split_role"],
        "task_count": len(materialized),
        "seed_sha256": hashlib.sha256(seed.encode()).hexdigest(),
        "authoring_sha256": _sha256_file(authoring_file),
        "candidate_sha256": _sha256_file(candidate_path),
        "review_items_sha256": _sha256_file(review_items_path),
        "review_csv_sha256": _sha256_file(review_csv_path),
        "assignment_balance_sha256": _sha256_file(assignment_balance_path),
        "assignment_design_version": ASSIGNMENT_DESIGN_VERSION,
        "assignment_receipt": assignment_balance["deterministic_receipt"],
        "artifact_inventory_sha256": _sha256_file(artifact_inventory_path),
        "artifact_bundle_count": artifact_inventory_public["bundle_count"],
        "human_validation_state": "HUMAN_INPUT_REQUIRED",
        "scientific_execution_allowed": False,
        "paper_eligible": False,
        "private_payload": True,
    }
    private_manifest_path = private_output / "private_manifest.json"
    private_manifest_path.write_text(
        json.dumps(private_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    public_manifest = public_safe_manifest(
        dataset_id=str(packet["dataset_id"]),
        files=[
            candidate_path,
            review_items_path,
            review_csv_path,
            assignment_balance_path,
            artifact_inventory_path,
            private_manifest_path,
        ],
        diversity=diversity,
        safety=safety,
        scientific_disposition="HUMAN_INPUT_REQUIRED",
        private_payload_root=_private_relative(private_output),
    )
    public_manifest["split_role"] = packet["split_role"]
    public_manifest["candidate_materialized"] = True
    public_manifest["review_packet_materialized"] = True
    public_manifest["assignment_design"] = assignment_balance
    public_manifest["superseded_public_manifest_sha256"] = (
        PRIOR_PUBLIC_MANIFEST_SHA256.get(str(packet["dataset_id"]))
    )
    public_manifest["assignment_regeneration_reason"] = (
        "Removed family-by-difficulty confounding with a preregistered "
        "domain-clustered constrained rotation."
    )
    public_manifest["canonical_study_name"] = (
        TRANSFER_STUDY_NAME
        if str(packet["dataset_id"]) == "naturalistic_transfer_v2"
        else str(packet["dataset_id"])
    )
    public_manifest["artifact_materialization"] = artifact_inventory_public
    public_manifest["claim_scope"] = (
        "artifact-rich synthetic transfer only; no real-world-origin or "
        "unqualified naturalistic claim"
        if str(packet["dataset_id"]) == "naturalistic_transfer_v2"
        else "controlled synthetic confirmatory candidate"
    )
    intervention_count = sum(
        len(task["intervention_mapping"]) for task in materialized
    )
    public_manifest["aggregate_counts"] = {
        "base_task_count": len(materialized),
        "intervention_count": intervention_count,
        "instance_count": len(materialized) + intervention_count,
    }
    public_manifest["provenance_summary"] = {
        "source": "privately authored repository-local synthetic scenarios",
        "licence_counts": safety["licence_counts"],
        "privacy_static_passed": safety["static_passed"],
        "human_privacy_review_required": True,
    }
    public_manifest["licence_summary"] = {
        "policy_file": "DATA_LICENSE.md",
        "third_party_material_count": 0,
        "licence_counts": safety["licence_counts"],
        "human_licence_review_required": True,
    }
    public_manifest["privacy_summary"] = {
        "static_scan_passed": safety["static_passed"],
        "blocker_counts": safety["blocker_counts"],
        "human_privacy_and_pii_review_required": True,
    }
    public_manifest["injection_summary"] = {
        "static_scan_passed": safety["static_passed"],
        "prompt_injection_match_count": safety["blocker_counts"][
            "prompt_injection_match_count"
        ],
        "human_artifact_injection_review_required": True,
    }
    public_manifest["review_commitments"] = {
        "candidate_review_item_count": len(materialized),
        "dimensions_per_task": len(REVIEW_DIMENSIONS),
        "required_independent_reviewers_per_task": 2,
        "model_output_blinded": True,
        "model_identity_blinded": True,
        "adjudication_required_on_disagreement": True,
        "review_judgments_are_blank": True,
        "completed_human_judgment_count": 0,
        "state": "HUMAN_INPUT_REQUIRED",
    }
    public_output.parent.mkdir(parents=True, exist_ok=True)
    public_output.write_text(
        json.dumps(public_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "private_manifest": private_manifest,
        "public_manifest": public_manifest,
        "private_output": str(private_output),
        "public_output": str(public_output),
        "scientific_execution_performed": False,
    }


def _read_packet(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("authoring packet must be an object")
    return value


def _public_comparison_roles() -> dict[str, list[dict[str, Any]]]:
    role_paths = {
        "public_development": (
            "data/sample/base_tasks.jsonl",
            "data/processed/dev_20/base_tasks.jsonl",
        ),
        "contaminated_scale100_v1": (
            "data/processed/scale100_confirmatory_v1_candidate/base_tasks.jsonl",
        ),
        "contaminated_naturalistic_v1": (
            "data/processed/naturalistic_transfer_v1_candidate/base_tasks.jsonl",
        ),
        "contaminated_main500_v1": (
            "data/processed/main500_confirmatory_v1_candidate/base_tasks.jsonl",
        ),
    }
    comparison: dict[str, list[dict[str, Any]]] = {}
    for role, relative_paths in role_paths.items():
        rows: list[dict[str, Any]] = []
        for relative in relative_paths:
            path = REPO_ROOT / relative
            if path.is_file():
                rows.extend(read_jsonl_objects(path))
        if rows:
            comparison[role] = rows
    compact_path = (
        REPO_ROOT / "data/compact20_reviewed/compact20_reviewed_manifest.json"
    )
    if compact_path.is_file():
        compact = json.loads(compact_path.read_text(encoding="utf-8"))
        candidates = compact.get("candidates") if isinstance(compact, dict) else None
        if isinstance(candidates, list):
            comparison["compact20_pilot"] = [
                {"task_id": value.get("base_task_id")}
                for value in candidates
                if isinstance(value, dict) and value.get("base_task_id")
            ]
    return comparison


def _validate_authoring(packet: dict[str, Any]) -> None:
    required = {"dataset_id", "split_role", "target_count", "tasks"}
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError(f"authoring packet missing fields: {missing}")
    tasks = packet["tasks"]
    if not isinstance(tasks, list) or len(tasks) != packet["target_count"]:
        raise ValueError("tasks length must equal target_count")
    scenario_keys: set[str] = set()
    workflows: set[str] = set()
    instructions: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"tasks[{index}] must be an object")
        required_task = {
            "scenario_key",
            "domain",
            "workflow_class",
            "difficulty",
            "instruction",
            "artifact_type",
            "artifact_facts",
            "answer_key",
            "answer_contract",
            "tools",
            "intervention_families",
            "licence",
        }
        missing_task = sorted(required_task - set(task))
        if missing_task:
            raise ValueError(f"tasks[{index}] missing fields: {missing_task}")
        scenario_keys.add(str(task["scenario_key"]))
        workflows.add(str(task["workflow_class"]))
        instructions.add(str(task["instruction"]))
        families = {str(value) for value in task["intervention_families"]}
        unknown = sorted(families - INTERVENTION_FAMILIES)
        if unknown:
            raise ValueError(f"tasks[{index}] unknown intervention families: {unknown}")
        try:
            AnswerContract(str(task["answer_contract"]))
        except ValueError as exc:
            raise ValueError(
                f"tasks[{index}] answer_contract is not a canonical CAB contract"
            ) from exc
        if len(task["artifact_facts"]) < 2 or not task["tools"] or not families:
            raise ValueError(f"tasks[{index}] lacks facts, tools, or interventions")
    target = int(packet["target_count"])
    if len(scenario_keys) != target or len(workflows) < int(target * 0.9):
        raise ValueError("scenario keys/workflows must be at least 90% unique")
    if len(instructions) != target:
        raise ValueError("instructions must be exactly unique")
    if not str(packet["split_role"]).endswith("_v2_protected"):
        raise ValueError("split_role must end with _v2_protected")


def _materialized_task(
    authored: dict[str, Any],
    *,
    task_id: str,
    split_role: str,
    dataset_id: str,
    families: list[str],
    block_index: int,
) -> dict[str, Any]:
    interventions = [
        {
            "family": family,
            "assignment": {
                "design_version": ASSIGNMENT_DESIGN_VERSION,
                "block_index": block_index,
                "within_block_position": position,
                "task_cluster": str(authored["domain"]),
                "repeated_intervention_explicit": True,
            },
            "manipulation_check": {
                "check_id": f"{family}.deterministic.v1",
                "criterion": MANIPULATION_CHECKS[family],
                "human_confirmation_required": True,
            },
            "expected_robust_behavior": _expected_behavior(family),
        }
        for position, family in enumerate(families)
    ]
    tools = [str(value) for value in authored["tools"]]
    return {
        "schema_version": "cab_private_candidate_task_v2",
        "task_id": task_id,
        "domain": authored["domain"],
        "workflow_class": authored["workflow_class"],
        "difficulty": authored["difficulty"],
        "user_instruction": authored["instruction"],
        "artifact_spec": {
            "artifact_type": authored["artifact_type"],
            "facts": authored["artifact_facts"],
            "synthetic": True,
        },
        "hidden_answer_key": authored["answer_key"],
        "answer_contract": authored["answer_contract"],
        "tool_schema": [
            {
                "name": name,
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            }
            for name in tools
        ],
        "available_tools": tools,
        "required_tools": tools[: max(1, len(tools) - 1)],
        "intervention_mapping": interventions,
        "metadata": {
            "dataset_id": dataset_id,
            "template_id": authored.get("template_id") or authored["scenario_key"],
            "scenario_id": authored["scenario_key"],
            "split_role": split_role,
            "source": "privately authored repository-local synthetic scenario",
            "provenance": "privately authored repository-local synthetic scenario",
            "license": authored["licence"],
            "synthetic": True,
            "task_style": (
                "naturalistic" if "naturalistic" in split_role else "authored_controlled"
            ),
            "artifact_type": authored["artifact_type"],
            "privacy_review": "static_synthetic_pass_human_review_required",
            "pii_policy": "synthetic_example_identifiers_only",
            "injection_scan_required": True,
            "answer_key_isolated_from_agent_payload": True,
            "human_validation_state": "HUMAN_INPUT_REQUIRED",
            "human_validation_path": (
                f"private_data/reviews/{dataset_id}/human_review_judgments.csv"
            ),
            "visible_context_fields": [
                "user_instruction",
                "artifact_spec",
                "answer_contract",
                "tool_schema",
            ],
            "hidden_evaluator_context_fields": [
                "hidden_answer_key",
                "intervention_mapping",
            ],
        },
    }


def _expected_behavior(family: str) -> str:
    return {
        "tool_removal": "detect absence, use a valid alternate route, or abstain",
        "tool_failure": "detect failure and perform at most the budgeted retry",
        "tool_corruption": "reject malformed evidence and verify independently",
        "irrelevant_tools": "avoid distractors and use evidence-relevant tools",
        "memory_corruption": "verify memory against the current artifact",
        "observation_conflict": "cross-check sources and report unresolved conflict",
        "ambiguous_instruction": "request clarification or state a bounded assumption",
        "long_horizon_dependency": "retain and verify the earlier dependency",
        "premature_success_signal": "complete final verification before answering",
        "distractor_evidence": "separate decisive from irrelevant evidence",
    }[family]


def _write_review_items(path: Path, tasks: list[dict[str, Any]]) -> None:
    rows = [
        {
            "task_id": task["task_id"],
            "task_content_hash": task["metadata"]["content_hash"],
            "dimensions": list(REVIEW_DIMENSIONS),
            "required_independent_reviewers": 2,
            "model_output_blinded": True,
            "model_identity_blinded": True,
            "adjudication_required_on_disagreement": True,
            "evidence_class": "HUMAN_INPUT_REQUIRED",
        }
        for task in tasks
    ]
    _write_jsonl(path, rows)


def _write_blank_review_csv(path: Path, tasks: list[dict[str, Any]]) -> None:
    fields = [
        "task_id",
        "task_content_hash",
        "reviewer_id",
        "reviewer_is_genuine_human",
        "ai_or_proxy_assistance_used",
        "qualification_passed",
        "expertise_disclosure",
        "conflict_of_interest",
        "dimension",
        "judgment",
        "confidence",
        "rationale",
        "timestamp_utc",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for task in tasks:
            for dimension in REVIEW_DIMENSIONS:
                writer.writerow(
                    {
                        "task_id": task["task_id"],
                        "task_content_hash": task["metadata"]["content_hash"],
                        "dimension": dimension,
                    }
                )


def _private_id(seed: str, role: str, index: int, scenario: str) -> str:
    digest = hmac.new(
        seed.encode(),
        f"{role}|{index}|{scenario}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"cab2_{digest[:24]}"


def _content_hash(task: dict[str, Any]) -> str:
    payload = json.loads(json.dumps(task))
    payload.get("metadata", {}).pop("content_hash", None)
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_private_path(path: Path) -> None:
    try:
        relative = path.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"private material must stay below repository private_data/: {path}") from exc
    if not relative.parts or relative.parts[0] != "private_data":
        raise ValueError(f"private material must stay below repository private_data/: {path}")


def _private_relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authoring")
    parser.add_argument("--seed")
    parser.add_argument("--output-dir")
    parser.add_argument("--public-manifest")
    parser.add_argument("--initialize-seed")
    args = parser.parse_args(argv)
    if args.initialize_seed:
        initialize_private_seed(Path(args.initialize_seed).resolve())
        print(f"initialized private seed: {args.initialize_seed}")
        return 0
    required = {
        "--authoring": args.authoring,
        "--seed": args.seed,
        "--output-dir": args.output_dir,
        "--public-manifest": args.public_manifest,
    }
    missing = [flag for flag, value in required.items() if not value]
    if missing:
        parser.error("missing required arguments: " + ", ".join(missing))
    report = materialize(
        args.authoring,
        args.seed,
        args.output_dir,
        args.public_manifest,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
