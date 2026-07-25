from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PolicyModel(BaseModel):
    """Strict, hash-stable base model for preregistered answer policies."""

    model_config = ConfigDict(extra="forbid")


class AnswerContract(StrEnum):
    """Canonical intervention-aware answer contracts required by CAB."""

    ORIGINAL_ANSWER_REQUIRED = "ORIGINAL_ANSWER_REQUIRED"
    ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED = (
        "ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED"
    )
    RECOVERY_ROUTE_REQUIRED = "RECOVERY_ROUTE_REQUIRED"
    QUALIFIED_UNCERTAINTY_ACCEPTED = "QUALIFIED_UNCERTAINTY_ACCEPTED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    ABSTENTION_REQUIRED = "ABSTENTION_REQUIRED"
    MULTIPLE_VALID_OUTCOMES = "MULTIPLE_VALID_OUTCOMES"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


class AnswerValueType(StrEnum):
    NORMALIZED_STRING = "normalized_string"
    CATEGORY = "category"
    NUMBER = "number"
    PERCENTAGE = "percentage"
    UNIT = "unit"
    CURRENCY = "currency"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    ORDERED_COLLECTION = "ordered_collection"
    UNORDERED_COLLECTION = "unordered_collection"
    KEY_VALUE = "key_value"
    JSON = "json"
    RANGE = "range"
    MULTIPLE = "multiple"


class FallbackMode(StrEnum):
    DISABLED = "disabled"
    SAFE_TOKEN_CONTAINS = "safe_token_contains"


class BehaviorRequirement(StrEnum):
    FORBIDDEN = "forbidden"
    ACCEPTED = "accepted"
    REQUIRED = "required"


class NumericTolerance(PolicyModel):
    absolute: float = Field(default=0.0, ge=0.0)
    relative: float = Field(default=0.0, ge=0.0)
    inclusive: bool = True


class PercentagePolicy(PolicyModel):
    expected_scale: Literal["fraction", "percent"] = "percent"
    allow_bare_number: bool = True


class UnitPolicy(PolicyModel):
    canonical_unit: str = Field(min_length=1)
    aliases: dict[str, str] = Field(default_factory=dict)
    conversion_factors: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_factors(self) -> UnitPolicy:
        if any(factor <= 0 for factor in self.conversion_factors.values()):
            raise ValueError("unit conversion factors must be positive")
        return self


class CurrencyPolicy(PolicyModel):
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    accepted_symbols: list[str] = Field(default_factory=list)
    allow_currency_code: bool = True
    allow_symbol: bool = True


class DateTimePolicy(PolicyModel):
    accepted_formats: list[str] = Field(default_factory=list)
    default_timezone: str | None = None
    require_timezone: bool = False
    timezone_aliases: dict[str, str] = Field(default_factory=dict)


class CollectionPolicy(PolicyModel):
    allow_delimited_text: bool = True
    delimiter: str = ","
    allow_duplicates: bool = False


class PartialCreditRule(PolicyModel):
    rule_id: str = Field(min_length=1)
    expected: Any
    answer_type: AnswerValueType = AnswerValueType.NORMALIZED_STRING
    weight: float = Field(gt=0.0)
    path: list[str | int] = Field(default_factory=list)


class GoldAnswerPolicy(PolicyModel):
    """Gold values and CAB answer semantics, independent of model output."""

    policy_id: str = Field(min_length=1)
    answer_contract: AnswerContract = AnswerContract.ORIGINAL_ANSWER_REQUIRED
    answer_type: AnswerValueType | None = None
    expected: Any = None
    accepted_answers: list[Any] = Field(default_factory=list)
    partial_credit_rules: list[PartialCreditRule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract_payload(self) -> GoldAnswerPolicy:
        if (
            self.answer_contract == AnswerContract.MULTIPLE_VALID_OUTCOMES
            and self.expected is None
            and not self.accepted_answers
        ):
            raise ValueError(
                "MULTIPLE_VALID_OUTCOMES requires expected or accepted_answers"
            )
        rule_ids = [rule.rule_id for rule in self.partial_credit_rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("partial-credit rule IDs must be unique")
        return self


class ScorerPolicy(PolicyModel):
    """Typed comparison and trajectory requirements fixed before execution."""

    policy_id: str = Field(min_length=1)
    answer_type: AnswerValueType = AnswerValueType.NORMALIZED_STRING
    case_sensitive: bool = False
    unicode_normalization: Literal["NFC", "NFKC", "NFD", "NFKD"] = "NFKC"
    strip_terminal_punctuation: bool = True
    category_aliases: dict[str, list[str]] = Field(default_factory=dict)
    numeric_tolerance: NumericTolerance = Field(default_factory=NumericTolerance)
    percentage: PercentagePolicy = Field(default_factory=PercentagePolicy)
    unit: UnitPolicy | None = None
    currency: CurrencyPolicy | None = None
    datetime: DateTimePolicy = Field(default_factory=DateTimePolicy)
    collection: CollectionPolicy = Field(default_factory=CollectionPolicy)
    range_bounds: Literal["closed", "open", "left_closed", "right_closed"] = "closed"
    multiple_answer_type: AnswerValueType = AnswerValueType.NORMALIZED_STRING
    fallback_mode: FallbackMode = FallbackMode.DISABLED
    abstention: BehaviorRequirement = BehaviorRequirement.FORBIDDEN
    clarification: BehaviorRequirement = BehaviorRequirement.FORBIDDEN
    refusal: BehaviorRequirement = BehaviorRequirement.FORBIDDEN
    required_tools: list[str] = Field(default_factory=list)
    required_recovery_actions: list[str] = Field(default_factory=list)
    unavailable_tool_disclosure: BehaviorRequirement = BehaviorRequirement.FORBIDDEN
    unavailable_tools: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_typed_configuration(self) -> ScorerPolicy:
        if self.answer_type == AnswerValueType.UNIT and self.unit is None:
            raise ValueError("unit answer type requires a unit policy")
        if self.answer_type == AnswerValueType.CURRENCY and self.currency is None:
            raise ValueError("currency answer type requires a currency policy")
        for field_name in (
            "required_tools",
            "required_recovery_actions",
            "unavailable_tools",
        ):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
        return self


def policy_hash(policy: BaseModel | dict[str, Any]) -> str:
    """Return a deterministic SHA-256 hash for a policy or scorer config."""

    payload = (
        policy.model_dump(mode="json", exclude_none=False)
        if isinstance(policy, BaseModel)
        else policy
    )
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "AnswerContract",
    "AnswerValueType",
    "BehaviorRequirement",
    "CollectionPolicy",
    "CurrencyPolicy",
    "DateTimePolicy",
    "FallbackMode",
    "GoldAnswerPolicy",
    "NumericTolerance",
    "PartialCreditRule",
    "PercentagePolicy",
    "ScorerPolicy",
    "UnitPolicy",
    "policy_hash",
]
