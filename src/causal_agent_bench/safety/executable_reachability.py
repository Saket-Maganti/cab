"""Executable Compact-20 reachability, gold, and intervention-isolation gates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from causal_agent_bench.answer_contracts import AnswerContract, RecoveryActionContract
from causal_agent_bench.environment import BenchmarkEnvironment
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.safety.intervention_reachability import (
    audit_intervention_collection,
)
from causal_agent_bench.safety.review_evidence import (
    intervention_isolation_result,
    invoke_fixture_fact_tool,
    reconstruct_clean_gold,
)
from causal_agent_bench.schemas import AgentAction, BenchmarkInstance, ToolCall
from causal_agent_bench.utils.io import read_jsonl

GateName = Literal[
    "executable_reachability",
    "gold_reconstruction",
    "intervention_isolation",
]


def run_static_reachability_check(
    repo_root: str | Path,
    *,
    instances_path: str | Path = ("data/compact20_reviewed/compact20_v2_instances.jsonl"),
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    instances = read_jsonl(_resolve(root, instances_path), BenchmarkInstance)
    return audit_intervention_collection(
        [row for row in instances if row.condition == "intervention"]
    )


def run_executable_reachability_check(
    repo_root: str | Path,
    *,
    instances_path: str | Path = ("data/compact20_reviewed/compact20_v2_instances.jsonl"),
    evidence_dir: str | Path = ("data/compact20_reviewed/reviewer_evidence"),
) -> dict[str, Any]:
    """Materialize environments and execute every declared Compact-20 route."""

    root = Path(repo_root).resolve()
    instances = read_jsonl(_resolve(root, instances_path), BenchmarkInstance)
    interventions = [row for row in instances if row.condition == "intervention"]
    clean_by_task = {row.base_task.task_id: row for row in instances if row.condition == "clean"}
    index = _read_json(_resolve(root, evidence_dir) / "bundle_index.json")
    candidate_by_intervention = {
        _read_json(root / row["path"])["intervention_instance_id"]: row for row in index["bundles"]
    }
    rows: list[dict[str, Any]] = []
    for instance in interventions:
        candidate = candidate_by_intervention[instance.instance_id]
        candidate_dir = (root / candidate["path"]).parent
        evidence = _read_json(candidate_dir / "controlled_evidence.json")
        bundle = _read_json(candidate_dir / "bundle.json")
        clean = clean_by_task[instance.base_task.task_id]
        fact_transcripts = [
            invoke_fixture_fact_tool(
                evidence,
                candidate_id=bundle["candidate_id"],
                fact_id=fact_id,
            )
            for fact_id in bundle["required_fact_ids"]
        ]
        unsupported = [
            fact_id
            for fact_id, transcript in zip(
                bundle["required_fact_ids"], fact_transcripts, strict=True
            )
            if transcript["observation"].get("fact_id") != fact_id
        ]
        intervention_spec = instance.intervention
        assert intervention_spec is not None
        scorer = intervention_spec.scorer_policy
        gold = intervention_spec.gold_answer_policy
        if scorer is None or gold is None:
            raise ValueError(f"missing policies for {instance.instance_id}")
        route: dict[str, Any]
        if gold.answer_contract == AnswerContract.RECOVERY_ROUTE_REQUIRED:
            route = _execute_recovery_route(instance, scorer.recovery_authorizations)
        elif gold.answer_contract == AnswerContract.QUALIFIED_UNCERTAINTY_ACCEPTED:
            route = _execute_uncertainty_route(instance, fact_transcripts)
        else:
            route = {
                "kind": "substantive_answer",
                "tool_invocations": fact_transcripts,
                "valid_final_response": clean.base_task.goal.expected_final_answer,
                "passed": not unsupported,
            }
        reconstructed = reconstruct_clean_gold(
            clean.base_task.domain,
            evidence["gold_derivation_inputs"],
        )
        isolation = intervention_isolation_result(clean, instance)
        row: dict[str, Any] = {
            "candidate_id": bundle["candidate_id"],
            "instance_id": instance.instance_id,
            "family": intervention_spec.family,
            "environment_hash": stable_hash(BenchmarkEnvironment(instance).state, length=64),
            "fixture_artifact_hash": _sha256_file(candidate_dir / "controlled_evidence.json"),
            "required_fact_count": len(bundle["required_fact_ids"]),
            "unsupported_fact_ids": unsupported,
            "clean_gold_reconstructed": reconstructed,
            "clean_gold_matches": (reconstructed == clean.base_task.goal.expected_final_answer),
            "intervention_isolation_passed": isolation["passed"],
            "route": route,
        }
        row["passed"] = bool(
            not unsupported
            and row["clean_gold_matches"]
            and isolation["passed"]
            and route["passed"]
        )
        row["execution_hash"] = stable_hash(row, length=64)
        rows.append(row)
    payload: dict[str, Any] = {
        "schema_version": "cab_executable_intervention_reachability_v1",
        "gate_kind": "executable_intervention_reachability",
        "status": "CAB_COMPACT_EXECUTABLE_REACHABILITY_READY",
        "instance_count": len(rows),
        "passed_count": sum(row["passed"] for row in rows),
        "failed_count": sum(not row["passed"] for row in rows),
        "clean_gold_passed_count": sum(row["clean_gold_matches"] for row in rows),
        "unsupported_fact_count": sum(len(row["unsupported_fact_ids"]) for row in rows),
        "unexplained_intervention_change_count": sum(
            not row["intervention_isolation_passed"] for row in rows
        ),
        "provider_calls_performed": 0,
        "model_calls_performed": 0,
        "fixture_only": True,
        "rows": rows,
    }
    payload["passed"] = bool(
        payload["instance_count"] == 20
        and payload["passed_count"] == 20
        and payload["clean_gold_passed_count"] == 20
        and payload["unsupported_fact_count"] == 0
        and payload["unexplained_intervention_change_count"] == 0
    )
    payload["report_hash"] = stable_hash(payload, length=64)
    return payload


def run_gold_reconstruction_check(
    repo_root: str | Path,
) -> dict[str, Any]:
    report = run_executable_reachability_check(repo_root)
    rows = [
        {
            "candidate_id": row["candidate_id"],
            "instance_id": row["instance_id"],
            "matches": row["clean_gold_matches"],
            "reconstructed": row["clean_gold_reconstructed"],
        }
        for row in report["rows"]
    ]
    payload: dict[str, Any] = {
        "schema_version": "cab_gold_reconstruction_gate_v1",
        "candidate_count": len(rows),
        "passed_count": sum(row["matches"] for row in rows),
        "failed_count": sum(not row["matches"] for row in rows),
        "rows": rows,
    }
    payload["passed"] = payload["candidate_count"] == payload["passed_count"] == 20
    payload["report_hash"] = stable_hash(payload, length=64)
    return payload


def run_intervention_isolation_check(
    repo_root: str | Path,
) -> dict[str, Any]:
    report = run_executable_reachability_check(repo_root)
    rows = [
        {
            "candidate_id": row["candidate_id"],
            "instance_id": row["instance_id"],
            "passed": row["intervention_isolation_passed"],
        }
        for row in report["rows"]
    ]
    payload: dict[str, Any] = {
        "schema_version": "cab_intervention_isolation_gate_v1",
        "candidate_count": len(rows),
        "passed_count": sum(row["passed"] for row in rows),
        "unexplained_change_count": sum(not row["passed"] for row in rows),
        "rows": rows,
    }
    payload["passed"] = payload["candidate_count"] == payload["passed_count"] == 20
    payload["report_hash"] = stable_hash(payload, length=64)
    return payload


def write_reachability_reports(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/final_pre_review",
) -> dict[str, str]:
    root = Path(repo_root).resolve()
    out = _resolve(root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    reports = {
        "STATIC_REACHABILITY.json": run_static_reachability_check(root),
        "EXECUTABLE_REACHABILITY.json": run_executable_reachability_check(root),
        "GOLD_RECONSTRUCTION.json": run_gold_reconstruction_check(root),
        "INTERVENTION_ISOLATION.json": run_intervention_isolation_check(root),
    }
    for name, payload in reports.items():
        (out / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return {name: str(out / name) for name in reports}


def _execute_recovery_route(
    instance: BenchmarkInstance,
    authorizations: list[RecoveryActionContract],
) -> dict[str, Any]:
    intervention = instance.intervention
    assert intervention is not None
    target = str(intervention.tool_output_patch.get("target_tool") or "")
    if not target or not authorizations:
        return {
            "kind": "recovery",
            "passed": False,
            "reason": "missing target or authorization",
        }
    environment = BenchmarkEnvironment(instance)
    failed_args = _valid_tool_arguments(target, instance)
    failure_step = environment.step(
        AgentAction(tool_call=ToolCall(tool_name=target, arguments=failed_args))
    )
    failure_observation = failure_step.get("observation")
    actual_failure = bool(
        isinstance(failure_observation, dict) and failure_observation.get("error")
    )
    contract = authorizations[0]
    recovery_tool = contract.allowed_tool_names[0]
    recovery_args = _valid_tool_arguments(recovery_tool, instance)
    recovery_step = environment.step(
        AgentAction(
            tool_call=ToolCall(tool_name=recovery_tool, arguments=recovery_args),
            metadata={
                "recovery_action": contract.action_id,
                "recovery_marker": True,
            },
        )
    )
    observation = recovery_step.get("observation")
    useful = bool(
        isinstance(observation, dict)
        and not observation.get("error")
        and observation.get("output") not in (None, {}, [], "")
    )
    return {
        "kind": "recovery",
        "target_tool": target,
        "failure_step": failure_step,
        "actual_failure_observed": actual_failure,
        "authorization_id": contract.action_id,
        "recovery_tool": recovery_tool,
        "recovery_arguments": recovery_args,
        "recovery_step": recovery_step,
        "useful_observation": useful,
        "causal_fact_ids": contract.supported_fact_ids,
        "valid_final_response": (
            instance.base_task.goal.expected_final_answer
            if useful
            else "qualified uncertainty after failed recovery"
        ),
        "passed": bool(actual_failure and useful and contract.supported_fact_ids),
    }


def _execute_uncertainty_route(
    instance: BenchmarkInstance,
    fact_transcripts: list[dict[str, Any]],
) -> dict[str, Any]:
    intervention = instance.intervention
    assert intervention is not None
    scorer = intervention.scorer_policy
    opportunity = scorer.abstention_opportunity if scorer else None
    mutation_materialized = bool(
        intervention.tool_availability_patch or intervention.tool_output_patch
    )
    return {
        "kind": "qualified_uncertainty",
        "mutation_materialized": mutation_materialized,
        "fact_observation_count": len(fact_transcripts),
        "opportunity_id": opportunity.opportunity_id if opportunity else None,
        "valid_final_response": (
            "Cannot safely determine the unchanged clean answer because the "
            "declared evidence route is unavailable or contradictory."
        ),
        "passed": bool(mutation_materialized and opportunity is not None),
    }


def _valid_tool_arguments(
    tool_name: str,
    instance: BenchmarkInstance,
) -> dict[str, Any]:
    hidden = instance.base_task.hidden_ground_truth
    if tool_name == "search_database":
        return {"query": str(hidden.get("best_option_id", "vendor beta"))}
    if tool_name == "lookup_policy":
        return {"policy_name": "vendor", "question": "security addendum policy"}
    if tool_name == "check_calendar":
        return {"date": "2026-06-03", "time_window": "13:00-17:00"}
    if tool_name == "read_file":
        return {"file_id": "retry_helper", "query": "max_retries"}
    if tool_name == "query_spreadsheet":
        return {"sheet_id": "revenue", "query": "Q2"}
    if tool_name == "calculate_price":
        return {
            "items": [{"id": "camera_b", "price": 200, "quantity": 1}],
            "constraints": {"tax_rate": hidden.get("tax_rate", 0.0)},
        }
    if tool_name == "compare_options":
        return {
            "options": [
                {"id": "saver_hotel", "price": 160},
                {"id": "flex_hotel", "price": 210},
            ],
            "criteria": ["price"],
        }
    if tool_name == "send_email_draft":
        return {
            "recipient": str(hidden.get("recipient", "mina@example.com")),
            "subject": "Meeting proposal",
            "body": "Proposed controlled-fixture time.",
        }
    if tool_name == "book_stub":
        return {"item_id": "fixture", "confirmation_required": True}
    if tool_name == "verify_fact":
        evidence_by_domain = {
            "travel_planning": (
                "Saver Hotel Boston is refundable and costs 160 before tax",
                ["travel_saver_hotel"],
            ),
            "calendar_email_workflow": (
                "Mina is free at 15:00 on 2026-06-03",
                ["calendar_1500"],
            ),
            "policy_compliance": (
                "A 700 dollar refund is above the 500 dollar threshold",
                ["refund_threshold"],
            ),
            "research_assistant": (
                "The report says latency dropped to 118 ms",
                ["latency_claim"],
            ),
        }
        claim, evidence_ids = evidence_by_domain.get(
            instance.base_task.domain,
            ("controlled fixture fact", ["calendar_1500"]),
        )
        return {"claim": claim, "evidence_ids": evidence_ids}
    return {}


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "run_executable_reachability_check",
    "run_gold_reconstruction_check",
    "run_intervention_isolation_check",
    "run_static_reachability_check",
    "write_reachability_reports",
]
