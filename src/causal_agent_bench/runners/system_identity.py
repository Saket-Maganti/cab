"""Strict evaluated-system identity binding and compatibility contracts."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PRIMARY_ADAPTER_LANE: Final = "cab_json_tool_protocol_v3"
NATIVE_ADAPTER_LANE: Final = "native_tool_calling_secondary_ablation_v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PLACEHOLDER = re.compile(
    r"(?:PIN_|REPLACE|RUN_TIME|VERIFY_|TBD|UNKNOWN)", re.IGNORECASE
)


class DecodingConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(ge=0)
    top_p: float = Field(gt=0, le=1)
    do_sample: bool
    max_new_tokens: int = Field(ge=1)
    seed: int


class EvaluatedSystemIdentity(BaseModel):
    """Fully bound system identity; placeholders are never valid here."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["cab_evaluated_system_identity_v1"] = (
        "cab_evaluated_system_identity_v1"
    )
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    quantization: str = Field(min_length=1)
    tokenizer_id: str = Field(min_length=1)
    tokenizer_revision: str = Field(min_length=1)
    tokenizer_hash: str
    chat_template_id: str = Field(min_length=1)
    chat_template_hash: str
    system_prompt_id: str = Field(min_length=1)
    system_prompt_hash: str
    tool_adapter_id: str = Field(min_length=1)
    tool_adapter_version: str = Field(min_length=1)
    tool_adapter_hash: str
    parser_id: str = Field(min_length=1)
    parser_version: str = Field(min_length=1)
    parser_hash: str
    tool_protocol_id: str = Field(min_length=1)
    tool_protocol_hash: str
    decoding: DecodingConfiguration
    context_limit: int = Field(ge=1)
    stop_conditions: list[str] = Field(min_length=1)
    adapter_lane: Literal[
        "cab_json_tool_protocol_v3",
        "native_tool_calling_secondary_ablation_v1",
    ]
    system_identity_hash: str | None = None

    @model_validator(mode="after")
    def validate_and_hash(self) -> EvaluatedSystemIdentity:
        values = self.model_dump(mode="json", exclude={"system_identity_hash"})
        for field in (
            "model_id",
            "model_revision",
            "quantization",
            "tokenizer_id",
            "tokenizer_revision",
            "chat_template_id",
            "system_prompt_id",
            "tool_adapter_id",
            "tool_adapter_version",
            "parser_id",
            "parser_version",
            "tool_protocol_id",
        ):
            if _PLACEHOLDER.search(str(values[field])):
                raise ValueError(f"{field} contains an unresolved placeholder")
        for field in (
            "tokenizer_hash",
            "chat_template_hash",
            "system_prompt_hash",
            "tool_adapter_hash",
            "parser_hash",
            "tool_protocol_hash",
        ):
            if not _SHA256.fullmatch(str(values[field])):
                raise ValueError(f"{field} must be a lowercase SHA-256 digest")
        expected = system_identity_hash(values)
        if self.system_identity_hash is not None and self.system_identity_hash != expected:
            raise ValueError("system_identity_hash does not match bound components")
        self.system_identity_hash = expected
        return self


class CompatibilityRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_category: str = Field(min_length=1)
    primary_lane_supported: bool
    native_ablation_supported: bool
    primary_adapter: Literal["cab_json_tool_protocol_v3"] = "cab_json_tool_protocol_v3"
    unsupported_behavior: Literal["fail_closed"] = "fail_closed"
    notes: str = Field(min_length=1)


def system_identity_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def content_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def assert_compatible_lane(
    rows: list[CompatibilityRow],
    *,
    model_category: str,
    adapter_lane: str,
) -> CompatibilityRow:
    matches = [row for row in rows if row.model_category == model_category]
    if len(matches) != 1:
        raise ValueError(
            f"UNSUPPORTED_SYSTEM: no unique compatibility row for {model_category!r}"
        )
    row = matches[0]
    if adapter_lane == PRIMARY_ADAPTER_LANE and not row.primary_lane_supported:
        raise ValueError(
            f"UNSUPPORTED_SYSTEM: {model_category!r} cannot use the frozen primary adapter"
        )
    if adapter_lane == NATIVE_ADAPTER_LANE and not row.native_ablation_supported:
        raise ValueError(
            f"UNSUPPORTED_SYSTEM: {model_category!r} lacks the native secondary ablation"
        )
    if adapter_lane not in {PRIMARY_ADAPTER_LANE, NATIVE_ADAPTER_LANE}:
        raise ValueError(f"UNSUPPORTED_SYSTEM: unknown adapter lane {adapter_lane!r}")
    return row


def comparison_label(
    left: EvaluatedSystemIdentity,
    right: EvaluatedSystemIdentity,
) -> Literal["model_comparison", "system_comparison"]:
    adapter_fields = (
        "tool_adapter_hash",
        "parser_hash",
        "tool_protocol_hash",
        "chat_template_hash",
        "system_prompt_hash",
        "decoding",
        "context_limit",
        "stop_conditions",
    )
    return (
        "model_comparison"
        if all(getattr(left, field) == getattr(right, field) for field in adapter_fields)
        else "system_comparison"
    )


__all__ = [
    "NATIVE_ADAPTER_LANE",
    "PRIMARY_ADAPTER_LANE",
    "CompatibilityRow",
    "DecodingConfiguration",
    "EvaluatedSystemIdentity",
    "assert_compatible_lane",
    "comparison_label",
    "content_sha256",
    "system_identity_hash",
]
