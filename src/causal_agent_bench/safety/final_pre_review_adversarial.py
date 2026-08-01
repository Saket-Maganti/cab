"""Independent malicious-fixture audit for final pre-review gates."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

from causal_agent_bench.analysis.hierarchical_power import (
    validate_hierarchical_power_design,
)
from causal_agent_bench.answer_contracts import RecoveryActionContract
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.metrics.typed_final_answer import score_typed_final_answer
from causal_agent_bench.runners.smoke_calibration import SmokeMeasurement
from causal_agent_bench.safety.approval_receipt import verify_approval_receipt
from causal_agent_bench.safety.intervention_reachability import (
    audit_intervention_reachability,
)
from causal_agent_bench.schemas import BenchmarkInstance, Trajectory
from causal_agent_bench.utils.io import read_jsonl


def run_final_pre_review_adversarial_audit(
    repo_root: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    instances = read_jsonl(
        root / "data/compact20_reviewed/compact20_v2_instances.jsonl",
        BenchmarkInstance,
    )
    recovery_instance = next(
        row
        for row in instances
        if row.intervention is not None
        and row.intervention.scorer_policy is not None
        and row.intervention.scorer_policy.recovery_authorizations
    )
    cases: list[dict[str, Any]] = []
    recovery_attacks: dict[str, Callable[[list[dict[str, Any]], RecoveryActionContract], None]] = {
        "wrong_action_id": lambda steps, contract: steps[1]["action"]["metadata"].update(
            {"recovery_action": contract.action_id + ".wrong"}
        ),
        "wrong_tool": lambda steps, contract: steps[1]["action"]["tool_call"].update(
            {"tool_name": "unrelated_tool"}
        ),
        "wrong_arguments": lambda steps, contract: steps[1]["action"]["tool_call"].update(
            {"arguments": {}}
        ),
        "missing_observation": lambda steps, contract: steps[1].update({"observation": None}),
        "unrelated_observation": lambda steps, contract: steps[1].update(
            {
                "observation": {
                    "tool_name": contract.allowed_tool_names[0],
                    "output": {"unrelated": True},
                }
            }
        ),
        "recovery_before_failure": lambda steps, contract: steps.reverse(),
        "text_only_substring": lambda steps, contract: steps.clear(),
        "attempt_budget_exceeded": _append_excess_attempt,
        "stale_failure_id": lambda steps, contract: steps[1]["action"]["metadata"].update(
            {"failure_event_id": "stale-failure-event"}
        ),
        "replayed_attempt": lambda steps, contract: steps.append(deepcopy(steps[1])),
    }
    valid_steps, contract = _valid_recovery_steps(recovery_instance)
    valid_result = _score_recovery(recovery_instance, valid_steps)
    cases.append(
        {
            "surface": "recovery",
            "attack": "valid_control",
            "expected": "accept",
            "observed": "accept" if valid_result.recovery_action_succeeded else "reject",
            "passed": valid_result.recovery_action_succeeded,
        }
    )
    for name, mutate in recovery_attacks.items():
        steps = deepcopy(valid_steps)
        mutate(steps, contract)
        result = _score_recovery(recovery_instance, steps)
        cases.append(
            {
                "surface": "recovery",
                "attack": name,
                "expected": "reject",
                "observed": "accept" if result.recovery_action_succeeded else "reject",
                "passed": not result.recovery_action_succeeded,
            }
        )

    static_payload = recovery_instance.model_dump(mode="json")
    static_payload["intervention"]["scorer_policy"]["required_recovery_actions"] = []
    static_payload["intervention"]["scorer_policy"]["recovery_authorizations"] = []
    broken_instance = BenchmarkInstance.model_validate(static_payload)
    static_result = audit_intervention_reachability(broken_instance)
    cases.append(
        {
            "surface": "reachability",
            "attack": "recovery_contract_removed",
            "expected": "reject",
            "observed": "accept" if static_result.passed else "reject",
            "passed": not static_result.passed,
        }
    )

    fixture_receipt = root / "tests/fixtures/approval/fixture_approval_receipt.json"
    if fixture_receipt.is_file():
        approval_control = verify_approval_receipt(
            fixture_receipt,
            repo_root=root,
            allowed_scope="fixture",
        )
        cases.append(
            {
                "surface": "approval",
                "attack": "valid_fixture_control",
                "expected": "accept",
                "observed": "accept" if approval_control["passed"] else "reject",
                "passed": approval_control["passed"],
            }
        )
        receipt_payload = json.loads(fixture_receipt.read_text(encoding="utf-8"))
        for name, mutation, scope in (
            (
                "candidate_hash_substitution",
                lambda row: row.update({"candidate_manifest_sha256": "0" * 64}),
                "fixture",
            ),
            (
                "signature_replay_as_scientific",
                lambda row: None,
                "scientific",
            ),
            (
                "path_only_approval",
                lambda row: row["artifact_bindings"]["candidate_manifest"].update(
                    {"sha256": "f" * 64}
                ),
                "fixture",
            ),
        ):
            mutated = deepcopy(receipt_payload)
            mutation(mutated)
            with tempfile.TemporaryDirectory(prefix="cab-approval-attack-") as temp:
                path = Path(temp) / "receipt.json"
                path.write_text(
                    json.dumps(mutated, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                result = verify_approval_receipt(
                    path,
                    repo_root=root,
                    allowed_scope=scope,  # type: ignore[arg-type]
                )
            cases.append(
                {
                    "surface": "approval",
                    "attack": name,
                    "expected": "reject",
                    "observed": "accept" if result["passed"] else "reject",
                    "passed": not result["passed"],
                }
            )

    design_path = root / "reports/final_pre_review/HIERARCHICAL_POWER_DESIGN.json"
    if design_path.is_file():
        design = json.loads(design_path.read_text(encoding="utf-8"))
        design["automatic_model_count_ess_multiplier"] = True
        design["design_hash"] = stable_hash(
            {key: value for key, value in design.items() if key != "design_hash"},
            length=64,
        )
        with tempfile.TemporaryDirectory(prefix="cab-power-attack-") as temp:
            path = Path(temp) / "power.json"
            path.write_text(
                json.dumps(design, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result = validate_hierarchical_power_design(root, design_path=path)
        cases.append(
            {
                "surface": "power",
                "attack": "model_count_pseudoreplication",
                "expected": "reject",
                "observed": "accept" if result["passed"] else "reject",
                "passed": not result["passed"],
            }
        )

    try:
        SmokeMeasurement.model_validate(
            {
                "schema_version": "cab_smoke_measurement_v1",
                "smoke_run_id": "attack",
                "system_identity_hash": "a" * 64,
                "code_revision": "b" * 40,
                "task_pack_sha256": "c" * 64,
                "trajectory_count": 2,
                "completed_count": 2,
                "failed_count": 1,
                "latency_seconds": [1.0],
                "throughput_trajectories_per_hour": 1.0,
                "shard_count": 1,
                "storage_bytes": 1,
                "failure_counts": {},
                "cpu_merge_scoring_seconds": 0,
                "measured_at": "2026-08-01T00:00:00Z",
                "evidence_class": "LIVE_SMOKE_MEASUREMENT",
            }
        )
        smoke_rejected = False
    except Exception:
        smoke_rejected = True
    cases.append(
        {
            "surface": "resource",
            "attack": "inconsistent_fake_smoke_counts",
            "expected": "reject",
            "observed": "reject" if smoke_rejected else "accept",
            "passed": smoke_rejected,
        }
    )

    critical_failures = [
        row
        for row in cases
        if not row["passed"] and row["surface"] in {"approval", "recovery", "reachability"}
    ]
    payload: dict[str, Any] = {
        "schema_version": "cab_final_pre_review_adversarial_audit_v1",
        "status": (
            "CAB_FINAL_PRE_REVIEW_ADVERSARIAL_AUDIT_PASSED"
            if all(row["passed"] for row in cases)
            else "CAB_FINAL_PRE_REVIEW_ADVERSARIAL_AUDIT_FAILED"
        ),
        "case_count": len(cases),
        "passed_count": sum(row["passed"] for row in cases),
        "failed_count": sum(not row["passed"] for row in cases),
        "silent_critical_failure_count": len(critical_failures),
        "cases": cases,
    }
    payload["passed"] = bool(
        payload["failed_count"] == 0 and payload["silent_critical_failure_count"] == 0
    )
    payload["audit_hash"] = stable_hash(payload, length=64)
    return payload


def _valid_recovery_steps(
    instance: BenchmarkInstance,
) -> tuple[list[dict[str, Any]], RecoveryActionContract]:
    assert instance.intervention is not None
    scorer = instance.intervention.scorer_policy
    assert scorer is not None
    contract = scorer.recovery_authorizations[0]
    required_properties = contract.argument_schema.get("properties", {})
    arguments = {
        key: _example_value(schema)
        for key, schema in required_properties.items()
        if key in contract.argument_schema.get("required", [])
    }
    required_output = contract.success_predicate.get("required_output_keys", [])
    output = dict.fromkeys(required_output, "fixture-value")
    target = instance.intervention.tool_output_patch.get("target_tool")
    steps = [
        {
            "action": {"tool_call": {"tool_name": target, "arguments": {}}},
            "observation": {
                "tool_name": target,
                "error": "simulated_tool_failure",
                "failure_event_id": "failure-fixture-01",
            },
        },
        {
            "action": {
                "tool_call": {
                    "tool_name": contract.allowed_tool_names[0],
                    "arguments": arguments,
                },
                "metadata": {
                    "recovery_action": contract.action_id,
                    "recovery_marker": True,
                    "attempt_id": "attempt-fixture-01",
                    "failure_event_id": "failure-fixture-01",
                },
            },
            "observation": {
                "tool_name": contract.allowed_tool_names[0],
                "output": output,
                "error": None,
                "attempt_id": "attempt-fixture-01",
                "returned_fact_ids": contract.supported_fact_ids,
            },
        },
    ]
    return steps, contract


def _append_excess_attempt(
    steps: list[dict[str, Any]],
    contract: RecoveryActionContract,
) -> None:
    steps.append(deepcopy(steps[1]))


def _score_recovery(
    instance: BenchmarkInstance,
    steps: list[dict[str, Any]],
):
    expected = instance.base_task.goal.expected_final_answer
    final_answer = (
        json.dumps(expected, sort_keys=True) if isinstance(expected, dict | list) else str(expected)
    )
    trajectory = Trajectory(
        run_id="adversarial-fixture",
        instance_id=instance.instance_id,
        agent_name="fixture",
        steps=steps,
        final_answer=final_answer,
        terminated_reason="final_answer",
    )
    return score_typed_final_answer(instance, trajectory)


def _example_value(schema: dict[str, Any]) -> Any:
    expected = schema.get("type")
    if isinstance(expected, list):
        expected = next((value for value in expected if value != "null"), "string")
    expected_type = str(expected) if expected is not None else "string"
    return {
        "string": "fixture",
        "array": [],
        "object": {},
        "boolean": False,
        "integer": 1,
        "number": 1.0,
    }.get(expected_type, "fixture")


__all__ = ["run_final_pre_review_adversarial_audit"]
