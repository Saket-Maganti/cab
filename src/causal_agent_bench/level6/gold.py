"""Evidence-only gold reconstruction using a closed, typed derivation DSL."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.hashing import stable_hash

Operation = Literal[
    "arithmetic",
    "boolean_policy",
    "contradiction",
    "currency_normalize",
    "datetime_compare",
    "direct",
    "filter",
    "format",
    "join",
    "literal",
    "normalize",
    "object",
    "percentage",
    "sort",
    "tax",
]


class DerivationExpression(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Operation
    fact: str | None = None
    value: Any = None
    args: list[DerivationExpression] = Field(default_factory=list)
    fields: dict[str, DerivationExpression] = Field(default_factory=dict)
    operator: str | None = None
    template: str | None = None
    key: str | None = None
    reverse: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> DerivationExpression:
        if self.op == "direct" and not self.fact:
            raise ValueError("direct operation requires a declared fact")
        if self.op == "object" and not self.fields:
            raise ValueError("object operation requires fields")
        if self.op == "format" and not self.template:
            raise ValueError("format operation requires a template")
        return self


class DerivationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cab_gold_derivation_dsl_v1"] = "cab_gold_derivation_dsl_v1"
    derivation_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    required_fact_suffixes: list[str] = Field(min_length=1)
    expression: DerivationExpression


def compact_derivation_spec(domain: str) -> DerivationSpec:
    specs: dict[str, dict[str, Any]] = {
        "travel_planning": {
            "required": ["hotel_refundability", "hotel_base_price", "hotel_tax_rate", "hotel_total_price", "selected_hotel"],
            "expression": {"op": "object", "fields": {"option_id": {"op": "direct", "fact": "selected_hotel"}, "total": {"op": "direct", "fact": "hotel_total_price"}}},
        },
        "shopping_comparison": {
            "required": ["bundle_b_base_price", "bundle_tax_rate", "bundle_total_price", "selected_bundle"],
            "expression": {"op": "object", "fields": {"option_id": {"op": "direct", "fact": "selected_bundle"}, "total": {"op": "direct", "fact": "bundle_total_price"}}},
        },
        "file_spreadsheet_qa": {
            "required": ["launch_name", "q2_revenue"],
            "expression": {"op": "object", "fields": {"launch": {"op": "direct", "fact": "launch_name"}, "q2_revenue": {"op": "direct", "fact": "q2_revenue"}}},
        },
        "research_assistant": {
            "required": ["claim_supported", "reported_latency", "claim_threshold"],
            "expression": {"op": "format", "template": "The claim is not supported; the report says {0} ms, not below {1} ms.", "args": [{"op": "direct", "fact": "reported_latency"}, {"op": "direct", "fact": "claim_threshold"}]},
        },
        "coding_debugging": {
            "required": ["bug_type", "bad_expression"],
            "expression": {"op": "format", "template": "The bug is an off-by-one retry loop using {0}.", "args": [{"op": "direct", "fact": "bad_expression"}]},
        },
        "policy_compliance": {
            "required": ["refund_threshold", "refund_amount", "approval_required"],
            "expression": {"op": "format", "template": "Yes. A 700 dollar refund requires manager approval because the threshold is {0} dollars.", "args": [{"op": "direct", "fact": "refund_threshold"}]},
        },
        "calendar_email_workflow": {
            "required": ["meeting_date", "first_open_slot", "recipient_email", "draft_status"],
            "expression": {"op": "object", "fields": {"date": {"op": "direct", "fact": "meeting_date"}, "slot": {"op": "direct", "fact": "first_open_slot"}, "status": {"op": "direct", "fact": "draft_status"}}},
        },
        "operations_planning": {
            "required": ["meeting_time", "vendor_policy", "selected_vendor"],
            "expression": {"op": "object", "fields": {"must_mention": {"op": "direct", "fact": "vendor_policy"}, "time": {"op": "direct", "fact": "meeting_time"}, "vendor": {"op": "direct", "fact": "selected_vendor"}}},
        },
    }
    raw = specs.get(domain)
    if raw is None:
        raise ValueError(f"no closed gold derivation for Compact domain {domain!r}")
    return DerivationSpec(
        derivation_id=f"compact.{domain}.evidence_only.v1",
        domain=domain,
        required_fact_suffixes=raw["required"],
        expression=DerivationExpression.model_validate(raw["expression"]),
    )


def reconstruct_from_visible_evidence(
    controlled_evidence: dict[str, Any],
    spec: DerivationSpec,
) -> dict[str, Any]:
    """Reconstruct an answer from visible facts; hidden gold is not an input."""

    serialized = json.dumps(controlled_evidence, sort_keys=True)
    forbidden = ("hidden_ground_truth", "gold_derivation_inputs", "expected_final_answer")
    present = [name for name in forbidden if name in serialized]
    if present:
        raise ValueError(f"forbidden hidden data present in evidence boundary: {present}")
    facts = controlled_evidence.get("facts")
    if not isinstance(facts, list):
        raise ValueError("visible evidence must contain a fact list")
    by_suffix: dict[str, dict[str, Any]] = {}
    for fact in facts:
        if not isinstance(fact, dict):
            raise ValueError("fact rows must be objects")
        suffix = str(fact.get("fact_id", "")).rsplit(".", 1)[-1]
        if suffix in by_suffix:
            raise ValueError(f"duplicate semantic fact suffix: {suffix}")
        if fact.get("reviewer_visible") is not True:
            raise ValueError(f"derivation fact is not reviewer visible: {suffix}")
        by_suffix[suffix] = fact
    missing = sorted(set(spec.required_fact_suffixes) - set(by_suffix))
    if missing:
        raise ValueError(f"required derivation facts unavailable: {missing}")
    used: list[str] = []
    output = _evaluate(spec.expression, by_suffix, used, stack=[])
    undeclared = sorted(set(used) - set(spec.required_fact_suffixes))
    if undeclared:
        raise ValueError(f"derivation used undeclared facts: {undeclared}")
    graph = _derivation_graph(controlled_evidence, spec, by_suffix, used, output)
    return {
        "schema_version": "cab_evidence_only_gold_result_v1",
        "derivation_id": spec.derivation_id,
        "required_fact_suffixes": spec.required_fact_suffixes,
        "used_fact_suffixes": sorted(set(used)),
        "output": output,
        "derivation_graph": graph,
        "hidden_ground_truth_available": False,
        "arbitrary_code_execution": False,
    }


def reconstruct_in_isolated_directory(
    controlled_evidence: dict[str, Any],
    spec: DerivationSpec,
) -> dict[str, Any]:
    """Exercise reconstruction in a directory containing only visible inputs."""

    with tempfile.TemporaryDirectory(prefix="cab-visible-gold-") as temporary:
        root = Path(temporary)
        evidence_path = root / "reviewer_visible_evidence.json"
        spec_path = root / "derivation_spec.json"
        evidence_path.write_text(json.dumps(controlled_evidence, sort_keys=True), encoding="utf-8")
        spec_path.write_text(spec.model_dump_json(), encoding="utf-8")
        names = {path.name for path in root.iterdir()}
        if names != {"reviewer_visible_evidence.json", "derivation_spec.json"}:
            raise ValueError("isolated reconstruction directory contains undeclared inputs")
        visible = json.loads(evidence_path.read_text(encoding="utf-8"))
        loaded_spec = DerivationSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))
        return reconstruct_from_visible_evidence(visible, loaded_spec)


def _evaluate(
    expression: DerivationExpression,
    facts: dict[str, dict[str, Any]],
    used: list[str],
    stack: list[int],
) -> Any:
    identity = id(expression)
    if identity in stack:
        raise ValueError("circular derivation expression")
    stack = [*stack, identity]
    if expression.op == "literal":
        return expression.value
    if expression.op == "direct":
        assert expression.fact is not None
        if expression.fact not in facts:
            raise ValueError(f"undeclared or unavailable fact: {expression.fact}")
        used.append(expression.fact)
        return facts[expression.fact]["normalized_value"]
    values = [_evaluate(arg, facts, used, stack) for arg in expression.args]
    if expression.op == "object":
        return {
            key: _evaluate(value, facts, used, stack)
            for key, value in expression.fields.items()
        }
    if expression.op == "format":
        assert expression.template is not None
        return expression.template.format(*[_format_scalar(value) for value in values])
    if expression.op == "arithmetic":
        if expression.operator == "add":
            return sum(values)
        if expression.operator == "subtract" and len(values) == 2:
            return values[0] - values[1]
        if expression.operator == "multiply":
            result = 1.0
            for value in values:
                result *= value
            return result
        if expression.operator == "divide" and len(values) == 2 and values[1] != 0:
            return values[0] / values[1]
        raise ValueError("invalid arithmetic operation")
    if expression.op == "percentage":
        if len(values) != 1:
            raise ValueError("percentage expects one argument")
        return float(values[0]) / 100.0
    if expression.op == "tax":
        if len(values) != 2:
            raise ValueError("tax expects base and rate")
        return round(float(values[0]) * (1.0 + float(values[1])), 8)
    if expression.op == "currency_normalize":
        if len(values) != 2:
            raise ValueError("currency normalization expects amount and rate")
        return round(float(values[0]) * float(values[1]), 8)
    if expression.op == "sort":
        if len(values) != 1 or not isinstance(values[0], list):
            raise ValueError("sort expects one list")
        return sorted(
            values[0],
            key=lambda row: str(row.get(expression.key)) if isinstance(row, dict) else str(row),
            reverse=expression.reverse,
        )
    if expression.op == "filter":
        if len(values) != 2 or not isinstance(values[0], list):
            raise ValueError("filter expects a list and comparison value")
        return [row for row in values[0] if isinstance(row, dict) and row.get(expression.key) == values[1]]
    if expression.op == "boolean_policy":
        if len(values) != 2:
            raise ValueError("boolean policy expects observed and threshold")
        operators = {"gte": values[0] >= values[1], "gt": values[0] > values[1], "eq": values[0] == values[1], "lte": values[0] <= values[1], "lt": values[0] < values[1]}
        if expression.operator not in operators:
            raise ValueError("invalid boolean policy operator")
        return operators[expression.operator]
    if expression.op == "datetime_compare":
        if len(values) != 2:
            raise ValueError("datetime comparison expects two values")
        left, right = (datetime.fromisoformat(str(value)) for value in values)
        return left <= right if expression.operator == "lte" else left < right
    if expression.op == "normalize":
        if len(values) != 1:
            raise ValueError("normalize expects one value")
        return " ".join(str(values[0]).casefold().split())
    if expression.op == "join":
        if len(values) != 2 or not all(isinstance(value, list) for value in values):
            raise ValueError("join expects two lists")
        right_by_key = {
            row.get(expression.key): row for row in values[1] if isinstance(row, dict)
        }
        return [
            {**row, **right_by_key[row.get(expression.key)]}
            for row in values[0]
            if isinstance(row, dict) and row.get(expression.key) in right_by_key
        ]
    if expression.op == "contradiction":
        if not values:
            raise ValueError("contradiction requires observations")
        normalized = {json.dumps(value, sort_keys=True) for value in values}
        if len(normalized) > 1:
            raise ValueError("evidence contradiction requires explicit resolution")
        return values[0]
    raise ValueError(f"unsupported derivation operation: {expression.op}")


def _derivation_graph(
    artifact: dict[str, Any],
    spec: DerivationSpec,
    facts: dict[str, dict[str, Any]],
    used: list[str],
    output: Any,
) -> dict[str, Any]:
    artifact_hash = str(artifact.get("artifact_hash") or stable_hash(artifact, length=64))
    nodes: list[dict[str, Any]] = [
        {"node_id": "artifact", "kind": "artifact", "hash": artifact_hash}
    ]
    edges: list[dict[str, Any]] = []
    for suffix in sorted(set(used)):
        fact = facts[suffix]
        nodes.append({"node_id": f"fact:{suffix}", "kind": "semantic_fact", "hash": fact["hash"]})
        edge = {"source": "artifact", "target": f"fact:{suffix}", "kind": "extraction"}
        edge["hash"] = stable_hash(edge, length=64)
        edges.append(edge)
    derivation_hash = stable_hash(spec.model_dump(mode="json"), length=64)
    nodes.append({"node_id": "derivation", "kind": "deterministic_derivation", "hash": derivation_hash})
    for suffix in sorted(set(used)):
        edge = {"source": f"fact:{suffix}", "target": "derivation", "kind": "normalization_and_derivation"}
        edge["hash"] = stable_hash(edge, length=64)
        edges.append(edge)
    output_hash = stable_hash(output, length=64)
    nodes.append({"node_id": "answer", "kind": "final_answer", "hash": output_hash})
    edge = {"source": "derivation", "target": "answer", "kind": "finalization"}
    edge["hash"] = stable_hash(edge, length=64)
    edges.append(edge)
    graph: dict[str, Any] = {"nodes": nodes, "edges": edges}
    graph["graph_hash"] = stable_hash(graph, length=64)
    return graph


def _format_scalar(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


__all__ = [
    "DerivationExpression",
    "DerivationSpec",
    "compact_derivation_spec",
    "reconstruct_from_visible_evidence",
    "reconstruct_in_isolated_directory",
]
