"""Typed semantic facts for the Compact reviewer-evidence boundary."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.schemas import BenchmarkInstance

SemanticType = Literal[
    "boolean",
    "category",
    "currency",
    "datetime",
    "identifier",
    "integer",
    "number",
    "percentage",
    "string",
]
DerivationRole = Literal["input", "constraint", "selection", "derived_input"]


class SemanticFact(BaseModel):
    """One content-bound fact exposed to a reviewer and the gold reconstructor."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(min_length=1)
    canonical_label: str = Field(min_length=1)
    semantic_type: SemanticType
    source_artifact_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    source_field_or_locator: str = Field(min_length=1)
    source_value: Any
    normalized_value: Any
    unit: str = Field(min_length=1)
    derivation_role: DerivationRole
    required_for_clean_answer: bool
    required_for_intervention_answer: bool
    reviewer_visible: bool
    sensitive: bool
    hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_hash_and_type(self) -> SemanticFact:
        expected = semantic_fact_hash(self.model_dump(mode="json", exclude={"hash"}))
        if self.hash != expected:
            raise ValueError("semantic fact hash does not match its content")
        if not _value_matches_type(self.normalized_value, self.semantic_type):
            raise ValueError(
                f"{self.fact_id}: value conflicts with semantic type {self.semantic_type}"
            )
        return self


@dataclass(frozen=True)
class FactTemplate:
    semantic_id: str
    canonical_label: str
    semantic_type: SemanticType
    source_key: str
    unit: str
    role: DerivationRole
    required_clean: bool
    required_intervention: bool
    value: Callable[[dict[str, Any]], Any]


def _hidden(key: str) -> Callable[[dict[str, Any]], Any]:
    def read(values: dict[str, Any]) -> Any:
        if key not in values:
            raise ValueError(f"explicit Compact source key is absent: {key}")
        return values[key]

    return read


def _literal(value: Any) -> Callable[[dict[str, Any]], Any]:
    return lambda _: value


# This registry is intentionally explicit.  Required-information labels are
# never zipped, sorted, cycled, or inferred from hidden-ground-truth ordering.
COMPACT_FACT_TEMPLATES: dict[str, tuple[FactTemplate, ...]] = {
    "travel_planning": (
        FactTemplate("hotel_refundability", "hotel refundability", "boolean", "hotel_refundable", "boolean", "constraint", True, True, _literal(True)),
        FactTemplate("hotel_base_price", "hotel base price", "currency", "hotel_base_price_usd", "USD", "input", True, True, _literal(160.0)),
        FactTemplate("hotel_tax_rate", "hotel tax rate", "percentage", "tax_rate", "ratio", "input", True, True, _hidden("tax_rate")),
        FactTemplate("hotel_total_price", "hotel total price", "currency", "total", "USD", "derived_input", True, True, _hidden("total")),
        FactTemplate("selected_hotel", "selected hotel option", "identifier", "best_option_id", "identifier", "selection", True, True, _hidden("best_option_id")),
    ),
    "shopping_comparison": (
        FactTemplate("bundle_b_base_price", "bundle B base price", "currency", "bundle_b_base_price_usd", "USD", "input", True, True, _literal(200.0)),
        FactTemplate("bundle_tax_rate", "bundle tax rate", "percentage", "tax_rate", "ratio", "input", True, True, _hidden("tax_rate")),
        FactTemplate("bundle_total_price", "selected bundle total price", "currency", "total", "USD", "derived_input", True, True, _hidden("total")),
        FactTemplate("selected_bundle", "selected bundle option", "identifier", "best_option_id", "identifier", "selection", True, True, _hidden("best_option_id")),
    ),
    "file_spreadsheet_qa": (
        FactTemplate("launch_name", "launch note content", "category", "launch", "text", "input", True, True, _hidden("launch")),
        FactTemplate("q2_revenue", "Q2 spreadsheet row", "currency", "q2_revenue", "USD", "input", True, True, _hidden("q2_revenue")),
    ),
    "research_assistant": (
        FactTemplate("claim_supported", "claim verification", "boolean", "claim_supported", "boolean", "derived_input", True, True, _hidden("claim_supported")),
        FactTemplate("reported_latency", "Apex report evidence", "integer", "reported_latency_ms", "ms", "input", True, True, _hidden("reported_latency_ms")),
        FactTemplate("claim_threshold", "claim latency threshold", "integer", "claim_threshold_ms", "ms", "constraint", True, True, _literal(100)),
    ),
    "coding_debugging": (
        FactTemplate("bug_type", "issue note", "category", "bug_type", "text", "input", True, True, _hidden("bug_type")),
        FactTemplate("bad_expression", "retry helper code", "string", "bad_expression", "code", "input", True, True, _hidden("bad_expression")),
    ),
    "policy_compliance": (
        FactTemplate("refund_threshold", "refund threshold", "currency", "threshold", "USD", "constraint", True, True, _hidden("threshold")),
        FactTemplate("refund_amount", "refund amount", "currency", "refund_amount_usd", "USD", "input", True, True, _literal(700)),
        FactTemplate("approval_required", "manager approval requirement", "boolean", "approval_required", "boolean", "derived_input", True, True, _hidden("approval_required")),
    ),
    "calendar_email_workflow": (
        FactTemplate("meeting_date", "calendar date", "datetime", "meeting_date", "ISO-8601 date", "constraint", True, True, _literal("2026-06-03")),
        FactTemplate("first_open_slot", "open afternoon slot", "datetime", "first_open_slot", "HH:MM", "selection", True, True, _hidden("first_open_slot")),
        FactTemplate("recipient_email", "recipient", "string", "recipient", "email", "input", True, True, _hidden("recipient")),
        FactTemplate("draft_status", "email draft status", "category", "draft_status", "text", "derived_input", True, True, _literal("draft_created")),
    ),
    "operations_planning": (
        FactTemplate("meeting_time", "availability", "datetime", "time", "HH:MM", "input", True, True, _hidden("time")),
        FactTemplate("vendor_policy", "vendor policy", "string", "policy", "text", "constraint", True, True, _hidden("policy")),
        FactTemplate("selected_vendor", "vendor score", "identifier", "vendor", "identifier", "selection", True, True, _hidden("vendor")),
        FactTemplate("vendor_email_recipient", "email recipient", "string", "vendor_email_recipient", "email", "input", False, True, _literal("procurement@example.com")),
    ),
}


REQUIRED_LABEL_MAPS: dict[str, dict[str, tuple[str, ...]]] = {
    "travel_planning": {
        "hotel refundability": ("hotel_refundability",),
        "hotel price": ("hotel_base_price", "hotel_total_price", "selected_hotel"),
        "tax rate": ("hotel_tax_rate",),
    },
    "shopping_comparison": {
        "bundle prices": ("bundle_b_base_price", "bundle_total_price", "selected_bundle"),
        "tax rate": ("bundle_tax_rate",),
    },
    "file_spreadsheet_qa": {
        "launch note content": ("launch_name",),
        "Q2 spreadsheet row": ("q2_revenue",),
    },
    "research_assistant": {
        "Apex report evidence": ("reported_latency", "claim_threshold"),
        "claim verification": ("claim_supported",),
    },
    "coding_debugging": {
        "retry helper code": ("bad_expression",),
        "issue note": ("bug_type",),
    },
    "policy_compliance": {
        "refund threshold": ("refund_threshold", "approval_required"),
        "refund amount": ("refund_amount",),
    },
    "calendar_email_workflow": {
        "calendar events": ("meeting_date",),
        "open afternoon slot": ("first_open_slot", "draft_status"),
        "recipient": ("recipient_email",),
    },
    "operations_planning": {
        "availability": ("meeting_time",),
        "vendor policy": ("vendor_policy",),
        "vendor score": ("selected_vendor",),
        "email recipient": ("vendor_email_recipient",),
    },
}


def semantic_fact_hash(payload: dict[str, Any]) -> str:
    return stable_hash(payload, length=64)


def build_compact_semantic_facts(instance: BenchmarkInstance) -> list[SemanticFact]:
    """Build the registered mapping for one Compact task without positional pairing."""

    domain = instance.base_task.domain
    templates = COMPACT_FACT_TEMPLATES.get(domain)
    if templates is None:
        raise ValueError(f"no explicit semantic fact mapping for Compact domain {domain!r}")
    hidden = instance.base_task.hidden_ground_truth
    result: list[SemanticFact] = []
    for template in templates:
        value = template.value(hidden)
        payload: dict[str, Any] = {
            "fact_id": f"{instance.base_task.task_id}.{template.semantic_id}",
            "canonical_label": template.canonical_label,
            "semantic_type": template.semantic_type,
            "source_artifact_id": f"{instance.base_task.task_id}.controlled_evidence",
            "source_path": "controlled_evidence.json",
            "source_field_or_locator": f"source_records.{template.source_key}",
            "source_value": value,
            "normalized_value": _normalize(value, template.semantic_type),
            "unit": template.unit,
            "derivation_role": template.role,
            "required_for_clean_answer": template.required_clean,
            "required_for_intervention_answer": template.required_intervention,
            "reviewer_visible": True,
            "sensitive": False,
        }
        result.append(SemanticFact.model_validate({**payload, "hash": semantic_fact_hash(payload)}))
    validate_compact_semantic_facts(instance, result)
    return result


def validate_compact_semantic_facts(
    instance: BenchmarkInstance,
    facts: list[SemanticFact],
) -> dict[str, Any]:
    domain = instance.base_task.domain
    templates = {row.semantic_id: row for row in COMPACT_FACT_TEMPLATES.get(domain, ())}
    mappings = REQUIRED_LABEL_MAPS.get(domain, {})
    issues: list[str] = []
    by_suffix = {fact.fact_id.rsplit(".", 1)[-1]: fact for fact in facts}
    required_labels = list(instance.base_task.goal.required_information)
    for label in required_labels:
        semantic_ids = mappings.get(label)
        if semantic_ids is None:
            issues.append(f"UNDECLARED_REQUIRED_LABEL:{label}")
            continue
        for semantic_id in semantic_ids:
            fact = by_suffix.get(semantic_id)
            if fact is None:
                issues.append(f"MISSING_MAPPED_FACT:{label}:{semantic_id}")
    for semantic_id, fact in by_suffix.items():
        template = templates.get(semantic_id)
        if template is None:
            issues.append(f"UNREGISTERED_FACT:{semantic_id}")
            continue
        expected_locator = f"source_records.{template.source_key}"
        if fact.canonical_label != template.canonical_label:
            issues.append(f"LABEL_MISMATCH:{semantic_id}")
        if fact.source_field_or_locator != expected_locator:
            issues.append(f"SOURCE_KEY_MISMATCH:{semantic_id}")
        if fact.semantic_type != template.semantic_type:
            issues.append(f"TYPE_MISMATCH:{semantic_id}")
        if fact.unit != template.unit:
            issues.append(f"UNIT_MISMATCH:{semantic_id}")
        if not fact.reviewer_visible:
            issues.append(f"FACT_NOT_REVIEWER_VISIBLE:{semantic_id}")
    locators = [fact.source_field_or_locator for fact in facts]
    duplicate_locators = sorted({value for value in locators if locators.count(value) > 1})
    issues.extend(f"UNDECLARED_DUPLICATE_SOURCE:{value}" for value in duplicate_locators)
    required_clean = {key for key, row in templates.items() if row.required_clean}
    issues.extend(
        f"MISSING_CLEAN_DERIVATION_FACT:{key}" for key in sorted(required_clean - set(by_suffix))
    )
    if issues:
        raise ValueError("; ".join(sorted(set(issues))))
    return {
        "passed": True,
        "fact_count": len(facts),
        "required_label_count": len(required_labels),
        "issues": [],
    }


def build_controlled_evidence_artifact(
    instance: BenchmarkInstance,
    *,
    candidate_id: str,
) -> dict[str, Any]:
    facts = build_compact_semantic_facts(instance)
    records = {
        fact.source_field_or_locator.removeprefix("source_records."): fact.source_value
        for fact in facts
    }
    payload: dict[str, Any] = {
        "schema_version": "cab_controlled_evidence_artifact_v2",
        "candidate_id": candidate_id,
        "base_task_id": instance.base_task.task_id,
        "source_class": "REPOSITORY_AUTHORED_CONTROLLED_SYNTHETIC_FIXTURE",
        "empirical_evidence": False,
        "reviewer_visible": True,
        "source_records": records,
        "facts": [fact.model_dump(mode="json") for fact in facts],
    }
    payload["artifact_hash"] = stable_hash(payload, length=64)
    return payload


def compute_fact_support(
    facts: list[dict[str, Any]],
    transcripts: list[dict[str, Any]],
    *,
    required_fact_ids: list[str],
) -> dict[str, Any]:
    """Compute semantic support from matching, content-bound observations."""

    facts_by_id = {str(row.get("fact_id")): row for row in facts}
    transcript_by_id = {
        str(row.get("observation", {}).get("fact_id")): row
        for row in transcripts
        if isinstance(row.get("observation"), dict)
    }
    fully: list[str] = []
    partially: list[str] = []
    unsupported: list[str] = []
    for fact_id in required_fact_ids:
        fact = facts_by_id.get(fact_id)
        transcript = transcript_by_id.get(fact_id)
        if fact is None:
            unsupported.append(fact_id)
            continue
        if transcript is None:
            partially.append(fact_id)
            continue
        observation = transcript.get("observation", {})
        complete = bool(
            observation.get("fact_hash") == fact.get("hash")
            and observation.get("source_artifact_hash")
            and observation.get("value") == fact.get("normalized_value")
            and observation.get("canonical_label") == fact.get("canonical_label")
        )
        (fully if complete else partially).append(fact_id)
    return {
        "unsupported_fact_count": len(unsupported),
        "unsupported_fact_ids": unsupported,
        "partially_supported_fact_ids": partially,
        "fully_supported_fact_ids": fully,
    }


def _normalize(value: Any, semantic_type: SemanticType) -> Any:
    if semantic_type in {"currency", "number", "percentage"}:
        return float(value)
    if semantic_type == "integer":
        return int(value)
    if semantic_type == "boolean":
        return bool(value)
    return str(value).strip()


def _value_matches_type(value: Any, semantic_type: SemanticType) -> bool:
    if semantic_type == "boolean":
        return isinstance(value, bool)
    if semantic_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if semantic_type in {"currency", "number", "percentage"}:
        return isinstance(value, int | float) and not isinstance(value, bool)
    return isinstance(value, str) and bool(value.strip())


__all__ = [
    "COMPACT_FACT_TEMPLATES",
    "REQUIRED_LABEL_MAPS",
    "SemanticFact",
    "build_compact_semantic_facts",
    "build_controlled_evidence_artifact",
    "compute_fact_support",
    "validate_compact_semantic_facts",
]
