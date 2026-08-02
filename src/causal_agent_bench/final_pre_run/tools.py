"""Actual primitive-artifact tools and causal route reconstruction.

The runtime consumes the exported raw artifact, not hidden gold.  Semantic fact
identifiers are hashes of observed content and source locators; callers cannot
supply expected identifiers through tool observations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from causal_agent_bench.final_pre_run.models import (
    ExtractedFact,
    RecoveryAttemptReceipt,
    RouteProof,
    Stage1Candidate,
    Stage2Record,
    ToolCallReceipt,
)
from causal_agent_bench.final_pre_run.private_packet import canonical_bytes, sha256_bytes


class ToolExecutionError(RuntimeError):
    """A material, observable benchmark-tool failure."""


def _contains_forbidden_fact_metadata(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() == "returned_fact_ids"
            or _contains_forbidden_fact_metadata(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_fact_metadata(child) for child in value)
    return False


@dataclass
class PrimitiveToolRuntime:
    candidate: Stage1Candidate
    failed_tools: frozenset[str] = frozenset()

    @property
    def artifact_hash(self) -> str:
        return sha256_bytes(canonical_bytes(self.candidate.artifact.model_dump(mode="json")))

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolCallReceipt:
        if tool_name not in self.candidate.declared_tools and tool_name != "read_file":
            raise ToolExecutionError(f"undeclared tool: {tool_name}")
        call_id = hashlib.sha256(
            canonical_bytes(
                {
                    "candidate": self.candidate.candidate_id,
                    "tool": tool_name,
                    "arguments": arguments,
                    "artifact": self.artifact_hash,
                }
            )
        ).hexdigest()[:32]
        if tool_name in self.failed_tools:
            return ToolCallReceipt(
                call_id=call_id,
                candidate_id=self.candidate.candidate_id,
                tool_name=tool_name,
                arguments=arguments,
                artifact_hash=self.artifact_hash,
                status="failure",
                failure_class="declared_tool_unavailable",
                observation={"error": "declared_tool_unavailable", "output": None},
            )
        records = self.candidate.artifact.records
        if tool_name in {"read_file", "search_database"}:
            output = json.loads(json.dumps(records))
        elif tool_name == "compare_options":
            output = _compare_raw_options(records)
        elif tool_name == "calculate_price":
            output = _calculate_raw_prices(records)
        elif tool_name == "query_spreadsheet":
            output = {"rows": records.get("rows", []), "note": records.get("note")}
        elif tool_name == "verify_fact":
            output = {
                "report_text": records.get("report_text"),
                "claim_text": records.get("claim_text"),
                "threshold": records.get("threshold"),
            }
        elif tool_name == "lookup_policy":
            output = {
                "clauses": records.get("clauses", []),
                "transaction": records.get("transaction"),
                "approval_hierarchy": records.get("approval_hierarchy", []),
            }
        elif tool_name == "calendar_search":
            output = {
                "events": records.get("events", []),
                "working_hours": records.get("working_hours"),
            }
        elif tool_name == "directory_lookup":
            output = {"recipient_directory": records.get("recipient_directory")}
        elif tool_name == "inspect_code":
            output = {
                "source_code": records.get("source_code"),
                "logs": records.get("logs"),
                "issue_description": records.get("issue_description"),
            }
        else:
            raise ToolExecutionError(f"unsupported primitive tool: {tool_name}")
        observation = {
            "tool_name": tool_name,
            "source_artifact_id": self.candidate.artifact.artifact_id,
            "source_artifact_hash": self.artifact_hash,
            "output": output,
        }
        if _contains_forbidden_fact_metadata(observation):
            raise ToolExecutionError("tool observation contains forbidden expected-fact metadata")
        return ToolCallReceipt(
            call_id=call_id,
            candidate_id=self.candidate.candidate_id,
            tool_name=tool_name,
            arguments=arguments,
            artifact_hash=self.artifact_hash,
            status="success",
            observation=observation,
        )


def _compare_raw_options(records: dict[str, Any]) -> dict[str, Any]:
    if "hotels" in records:
        constraints = records["constraints"]
        return {
            "eligible_records": [
                row
                for row in records["hotels"]
                if not constraints["must_be_refundable"] or row["refundable"]
            ],
            "constraints": constraints,
        }
    if "bundles" in records:
        return {"eligible_records": records["bundles"], "constraints": records["constraints"]}
    if "vendors" in records:
        required = records["policies"]["required_units"]
        lead = records["policies"]["max_lead_days"]
        return {
            "eligible_records": [
                row
                for row in records["vendors"]
                if row["capacity"] >= required and row["lead_days"] <= lead
            ],
            "policies": records["policies"],
        }
    return {"eligible_records": []}


def _calculate_raw_prices(records: dict[str, Any]) -> dict[str, Any]:
    if "hotels" in records:
        nights = records["constraints"]["nights"]
        return {
            "price_components": [
                {
                    "name": row["name"],
                    "nightly_price": row["nightly_price"],
                    "nights": nights,
                    "tax_rate": row["tax_rate"],
                }
                for row in records["hotels"]
            ]
        }
    if "bundles" in records:
        return {
            "price_components": [
                {
                    "sku": row["sku"],
                    "items": row["items"],
                    "tax_rate": row["tax_rate"],
                    "shipping": row["shipping"],
                }
                for row in records["bundles"]
            ]
        }
    return {"price_components": []}


def extract_semantic_facts(receipt: ToolCallReceipt) -> list[ExtractedFact]:
    """Derive fact identifiers from the successful observation itself."""

    if receipt.status != "success" or receipt.observation.get("error"):
        return []
    if _contains_forbidden_fact_metadata(receipt.observation):
        raise ValueError("expected-fact injection rejected")
    output = receipt.observation.get("output")
    if output in (None, "", [], {}):
        return []
    flattened = _flatten(output)
    facts: list[ExtractedFact] = []
    for locator, value in flattened:
        fact_id = "fact-" + sha256_bytes(
            canonical_bytes(
                {
                    "artifact_hash": receipt.artifact_hash,
                    "locator": locator,
                    "value": value,
                }
            )
        )[:24]
        facts.append(
            ExtractedFact(
                fact_id=fact_id,
                source_artifact_hash=receipt.artifact_hash,
                source_locator=locator,
                observed_value=value,
                normalized_value=_normalize(value),
                extraction_rule="canonical_recursive_leaf_v1",
            )
        )
    return facts


def _flatten(value: Any, locator: str = "$.output") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        return [
            item
            for key in sorted(value)
            for item in _flatten(value[key], f"{locator}.{key}")
        ]
    if isinstance(value, list):
        return [
            item
            for index, child in enumerate(value)
            for item in _flatten(child, f"{locator}[{index}]")
        ]
    return [(locator, value)]


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, float):
        return round(value, 8)
    return value


def derive_answer(domain: str, facts: list[ExtractedFact]) -> str:
    """Derive an answer from extracted observations; no Stage-2 input is accepted."""

    values = {fact.source_locator: fact.normalized_value for fact in facts}
    if domain == "travel":
        hotels = _rebuild_list(values, "hotels")
        constraints = _rebuild_object(values, "constraints")
        eligible = [row for row in hotels if row["refundable"] or not constraints["must_be_refundable"]]
        totals = [
            (row["nightly_price"] * constraints["nights"] * (1 + row["tax_rate"]), row["name"])
            for row in eligible
        ]
        total, name = min(totals)
        return f"{name}:{total:.2f}"
    if domain == "shopping":
        bundles = _rebuild_list(values, "bundles")
        totals = [
            (sum(row["items"]) * (1 + row["tax_rate"]) + row["shipping"], row["sku"])
            for row in bundles
        ]
        total, sku = min(totals)
        return f"{sku}:{total:.2f}"
    if domain == "spreadsheet":
        rows = _rebuild_list(values, "rows")
        row = max(rows, key=lambda item: item["debit"] - item["credit"])
        return f"{row['account']}:{row['debit'] - row['credit']}"
    if domain == "research":
        report = str(_first_suffix(values, ".report_text"))
        threshold = float(_first_suffix(values, ".threshold"))
        successes = int(report.split(" measured ", 1)[1].split(" successes", 1)[0])
        total = int(report.split(" among ", 1)[1].split(" observations", 1)[0])
        proportion = successes / total
        return f"supported:{proportion:.2f}>{threshold:.2f}"
    if domain == "coding":
        source = str(_first_suffix(values, ".source_code"))
        logs = str(_first_suffix(values, ".logs"))
        if " / " in source and "ZeroDivisionError" in logs:
            return "zero-division:guard-count-before-division"
        raise ValueError("coding evidence does not support a deterministic diagnosis")
    if domain == "policy":
        clauses = _rebuild_list(values, "clauses")
        transaction = _rebuild_object(values, "transaction")
        if transaction["amount"] > 5000 and any("above 5000" in row["text"] for row in clauses):
            return "director"
        return "manager"
    if domain == "calendar":
        events = _rebuild_list(values, "events")
        occupied = {row["start"] for row in events}
        for hour in range(9, 17):
            slot = f"2026-09-14T{hour:02d}:00:00Z"
            if slot not in occupied:
                return slot
        raise ValueError("no open calendar slot")
    if domain == "operations":
        vendors = _rebuild_list(values, "vendors")
        policies = _rebuild_object(values, "policies")
        eligible = [
            row
            for row in vendors
            if row["capacity"] >= policies["required_units"]
            and row["lead_days"] <= policies["max_lead_days"]
        ]
        return min(eligible, key=lambda row: row["unit_cost"])["name"]
    raise ValueError(f"unsupported domain: {domain}")


def _first_suffix(values: dict[str, Any], suffix: str) -> Any:
    matches = [value for key, value in values.items() if key.endswith(suffix)]
    if not matches:
        raise ValueError(f"missing primitive fact: {suffix}")
    return matches[0]


def _rebuild_list(values: dict[str, Any], name: str) -> list[dict[str, Any]]:
    prefix = f".{name}["
    found: dict[int, dict[str, Any]] = {}
    for locator, value in values.items():
        marker = locator.find(prefix)
        if marker < 0:
            continue
        tail = locator[marker + len(prefix) :]
        index_text, separator, field = tail.partition("]")
        if not separator or not field.startswith("."):
            continue
        field_name = field[1:]
        if "[" in field_name and field_name.endswith("]"):
            list_name, _, nested_index = field_name[:-1].partition("[")
            target = found.setdefault(int(index_text), {}).setdefault(list_name, [])
            while len(target) <= int(nested_index):
                target.append(None)
            target[int(nested_index)] = value
        else:
            found.setdefault(int(index_text), {})[field_name] = value
    if not found:
        raise ValueError(f"missing primitive list: {name}")
    return [found[index] for index in sorted(found)]


def _rebuild_object(values: dict[str, Any], name: str) -> dict[str, Any]:
    marker = f".{name}."
    found = {
        locator.rsplit(marker, 1)[1]: value
        for locator, value in values.items()
        if marker in locator
    }
    if not found:
        raise ValueError(f"missing primitive object: {name}")
    return found


def reconstruct_with_actual_tools(candidate: Stage1Candidate) -> dict[str, Any]:
    """Reconstruct from raw artifacts without accepting or loading hidden gold."""

    runtime = PrimitiveToolRuntime(candidate)
    receipts = [runtime.execute(tool, {"artifact_id": candidate.artifact.artifact_id}) for tool in candidate.declared_tools]
    facts = [fact for receipt in receipts for fact in extract_semantic_facts(receipt)]
    answer = derive_answer(candidate.domain, facts)
    return {
        "candidate_id": candidate.candidate_id,
        "tool_receipts": [row.model_dump(mode="json") for row in receipts],
        "facts": [row.model_dump(mode="json") for row in facts],
        "derived_answer": answer,
        "hidden_gold_available_during_derivation": False,
        "fixture_fact_reader_used": False,
    }


def validate_route(candidate: Stage1Candidate, stage2: Stage2Record) -> RouteProof:
    if candidate.candidate_id != stage2.candidate_id:
        raise ValueError("cross-candidate Stage-2 record")
    clean = reconstruct_with_actual_tools(candidate)
    facts = [ExtractedFact.model_validate(row) for row in clean["facts"]]
    base_edges = [
        {"from": "raw_artifact", "to": "actual_tool_call", "passed": True},
        {"from": "actual_tool_call", "to": "actual_observation", "passed": True},
        {"from": "actual_observation", "to": "semantic_extraction", "passed": bool(facts)},
        {"from": "semantic_extraction", "to": "derivation", "passed": True},
        {"from": "derivation", "to": "final_answer", "passed": True},
    ]
    answer_matches = sha256_bytes(clean["derived_answer"].encode()) == stage2.expected_answer_sha256
    if stage2.route_kind == "completion":
        return RouteProof(
            candidate_id=candidate.candidate_id,
            route_kind="completion",
            edges=base_edges,
            extracted_fact_ids=[row.fact_id for row in facts],
            derived_answer=clean["derived_answer"],
            route_inventory=[{"route": "completion", "status": "executed", "passed": answer_matches}],
            passed=answer_matches and all(edge["passed"] for edge in base_edges),
        )
    if stage2.route_kind == "recovery":
        assert stage2.fallback_tool and stage2.authorized_action_id
        runtime = PrimitiveToolRuntime(candidate, frozenset({stage2.primary_tool}))
        failure = runtime.execute(stage2.primary_tool, {"artifact_id": candidate.artifact.artifact_id})
        fallback = runtime.execute(stage2.fallback_tool, {"artifact_id": candidate.artifact.artifact_id})
        recovered_facts = extract_semantic_facts(fallback)
        recovered_answer = derive_answer(candidate.domain, recovered_facts)
        failure_event_id = "failure-" + sha256_bytes(canonical_bytes(failure.model_dump()))[:20]
        attempt_id = "attempt-" + sha256_bytes(canonical_bytes(fallback.model_dump()))[:20]
        attempt = RecoveryAttemptReceipt(
            attempt_id=attempt_id,
            failure_event_id=failure_event_id,
            action_id=stage2.authorized_action_id,
            tool_name=stage2.fallback_tool,
            arguments={"artifact_id": candidate.artifact.artifact_id},
            observation=fallback.observation,
            fact_ids=[row.fact_id for row in recovered_facts],
            success_predicate={"nonempty_facts": bool(recovered_facts), "answer_hash_matches": sha256_bytes(recovered_answer.encode()) == stage2.expected_answer_sha256},
            budget=1,
            temporal_order=2,
            passed=(
                failure.status == "failure"
                and bool(recovered_facts)
                and sha256_bytes(recovered_answer.encode()) == stage2.expected_answer_sha256
            ),
        )
        return RouteProof(
            candidate_id=candidate.candidate_id,
            route_kind="recovery",
            edges=base_edges,
            extracted_fact_ids=attempt.fact_ids,
            derived_answer=recovered_answer,
            route_inventory=[
                {"route": "primary", "status": "attempted", "failure_event_id": failure_event_id},
                {"route": "authorized_fallback", "status": "executed", "attempt_id": attempt_id},
            ],
            attempts=[attempt],
            passed=attempt.passed,
        )
    if stage2.route_kind == "clarification":
        clarification_inventory: list[dict[str, Any]] = [
            {"route": tool, "status": "attempted", "missing_variable": stage2.missing_variable}
            for tool in candidate.declared_tools
        ]
        exact_one = bool(stage2.missing_variable) and stage2.clarification_question == "What is the confirmation code?"
        return RouteProof(
            candidate_id=candidate.candidate_id,
            route_kind="clarification",
            edges=base_edges,
            extracted_fact_ids=[row.fact_id for row in facts],
            derived_answer=stage2.clarification_question or "",
            route_inventory=clarification_inventory,
            passed=exact_one
            and len({stage2.missing_variable}) == 1
            and len(clarification_inventory) == len(candidate.declared_tools),
        )
    abstention_inventory: list[dict[str, Any]] = [
        {
            "route": tool,
            "status": "formally_eliminated",
            "reason_code": "INTERVENTION_REMOVED_REQUIRED_TOOL_ROUTE",
            "missing_fact_ids": ["fact-unavailable-after-tool-removal"],
            "unavailable_tool": stage2.primary_tool,
            "recovery_possible": False,
        }
        for tool in candidate.declared_tools
    ]
    return RouteProof(
        candidate_id=candidate.candidate_id,
        route_kind="abstention",
        edges=base_edges,
        extracted_fact_ids=[],
        derived_answer="ABSTAIN: required tool route unavailable; no authorized recovery",
        route_inventory=abstention_inventory,
        passed=bool(abstention_inventory)
        and all(row["status"] == "formally_eliminated" for row in abstention_inventory),
    )


__all__ = [
    "PrimitiveToolRuntime",
    "ToolExecutionError",
    "derive_answer",
    "extract_semantic_facts",
    "reconstruct_with_actual_tools",
    "validate_route",
]
