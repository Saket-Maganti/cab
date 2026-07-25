from __future__ import annotations

import json
import re
from typing import Any

from causal_agent_bench.schemas import ToolCallParseResult, ToolSpec

CANONICAL_TOOL_ACTION = {
    "action": "tool_call",
    "thought": "why this tool is needed",
    "tool_name": "tool_name",
    "arguments": {},
}

CANONICAL_FINAL_ACTION = {
    "action": "final_answer",
    "thought": "why the answer is supported or impossible",
    "final_answer": "answer text",
    "evidence": ["observation or limitation"],
    "stop": True,
}

CANONICAL_CLARIFICATION_ACTION = {
    "action": "clarification",
    "thought": "why the task is underspecified",
    "clarification": "question or uncertainty statement",
    "stop": True,
}


def parse_tool_action(
    raw_output: str | None,
    *,
    available_tools: list[ToolSpec],
    observation_history: list[dict[str, Any]] | None = None,
    required_information: list[str] | None = None,
) -> ToolCallParseResult:
    """Parse one LLM action according to the canonical tool protocol.

    The parser repairs wrappers such as Markdown code fences, prose around JSON,
    and trailing commas. It does not repair semantic errors such as wrong tool
    names, missing required arguments, or multiple attempted tool calls.
    """

    raw_text = raw_output or ""
    parsed, repair_metadata, parse_error = _parse_jsonish(raw_text)
    if parse_error is not None:
        return ToolCallParseResult(
            raw_output=raw_output,
            action_type="invalid",
            outcome="invalid_json",
            is_valid=False,
            error=parse_error,
            metadata=repair_metadata,
        )

    if isinstance(parsed, list):
        return ToolCallParseResult(
            raw_output=raw_output,
            repaired_json=parsed,
            action_type="invalid",
            outcome="multiple_tool_calls" if len(parsed) != 1 else "missing_action",
            is_valid=False,
            error="Protocol requires exactly one JSON action object, not a list.",
            metadata=repair_metadata,
        )
    if not isinstance(parsed, dict):
        return ToolCallParseResult(
            raw_output=raw_output,
            repaired_json=None,
            action_type="invalid",
            outcome="missing_action",
            is_valid=False,
            error="Parsed payload is not a JSON object.",
            metadata=repair_metadata,
        )

    normalized = _normalize_action(parsed)
    if _contains_multiple_tool_calls(normalized):
        return ToolCallParseResult(
            raw_output=raw_output,
            repaired_json=normalized,
            action_type="invalid",
            outcome="multiple_tool_calls",
            is_valid=False,
            error="Protocol requires exactly one tool call.",
            metadata=repair_metadata,
        )

    action = str(normalized.get("action") or "").strip().lower()
    explanation = _first_string(normalized, "thought", "explanation", "rationale")

    if action == "tool_call" or "tool_call" in normalized or "tool_name" in normalized:
        tool_name, arguments = _extract_tool_call(normalized)
        call_metadata = _metadata_with_call_id(repair_metadata, normalized.get("call_id"))
        if not tool_name:
            return ToolCallParseResult(
                raw_output=raw_output,
                repaired_json=normalized,
                action_type="invalid",
                outcome="missing_action",
                is_valid=False,
                explanation=explanation,
                error="Tool action is missing tool_name.",
                metadata=call_metadata,
            )
        tool_specs = {tool.name: tool for tool in available_tools if tool.is_available}
        if tool_name not in tool_specs:
            return ToolCallParseResult(
                raw_output=raw_output,
                repaired_json=normalized,
                action_type="tool_call",
                outcome="unknown_tool",
                is_valid=False,
                tool_name=tool_name,
                arguments=arguments,
                explanation=explanation,
                error=f"Unknown or unavailable tool: {tool_name}",
                metadata=call_metadata,
            )
        argument_errors = validate_tool_arguments(arguments, tool_specs[tool_name])
        if argument_errors:
            return ToolCallParseResult(
                raw_output=raw_output,
                repaired_json=normalized,
                action_type="tool_call",
                outcome="invalid_argument_schema",
                is_valid=False,
                tool_name=tool_name,
                arguments=arguments,
                explanation=explanation,
                error="; ".join(argument_errors),
                metadata=call_metadata,
            )
        if _repeats_failed_call(tool_name, arguments, observation_history or []):
            return ToolCallParseResult(
                raw_output=raw_output,
                repaired_json=normalized,
                action_type="tool_call",
                outcome="repeated_failed_call",
                is_valid=False,
                tool_name=tool_name,
                arguments=arguments,
                explanation=explanation,
                error="Repeated the immediately previous failed tool call with identical arguments.",
                metadata=call_metadata,
            )
        return ToolCallParseResult(
            raw_output=raw_output,
            repaired_json=normalized,
            action_type="tool_call",
            outcome="valid_tool_call",
            is_valid=True,
            tool_name=tool_name,
            arguments=arguments,
            explanation=explanation,
            metadata=call_metadata,
        )

    if action in {"final_answer", "final"} or "final_answer" in normalized:
        answer = _first_string(normalized, "final_answer", "answer")
        if _final_without_evidence(observation_history or [], required_information or []):
            return ToolCallParseResult(
                raw_output=raw_output,
                repaired_json=normalized,
                action_type="final_answer",
                outcome="final_answer_without_required_evidence",
                is_valid=False,
                final_answer=answer,
                explanation=explanation,
                error="Final answer was produced before required evidence was observed.",
                metadata=repair_metadata,
            )
        return ToolCallParseResult(
            raw_output=raw_output,
            repaired_json=normalized,
            action_type="final_answer",
            outcome="valid_final_answer",
            is_valid=True,
            final_answer=answer,
            explanation=explanation,
            metadata=repair_metadata,
        )

    if action in {"clarification", "clarify", "uncertainty"} or "clarification" in normalized:
        clarification = _first_string(normalized, "clarification", "question", "uncertainty")
        return ToolCallParseResult(
            raw_output=raw_output,
            repaired_json=normalized,
            action_type="clarification",
            outcome="clarification",
            is_valid=True,
            final_answer=clarification,
            explanation=explanation,
            metadata=repair_metadata,
        )

    return ToolCallParseResult(
        raw_output=raw_output,
        repaired_json=normalized,
        action_type="invalid",
        outcome="missing_action",
        is_valid=False,
        explanation=explanation,
        error="No action field, tool_call, tool_name, final_answer, or clarification found.",
        metadata=repair_metadata,
    )


def validate_tool_arguments(arguments: dict[str, Any], tool: ToolSpec) -> list[str]:
    schema = tool.input_schema or {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    errors: list[str] = []
    for field_name in required:
        if field_name not in arguments:
            errors.append(f"missing required argument {field_name!r}")
    for field_name, value in arguments.items():
        field_schema = properties.get(field_name)
        if not isinstance(field_schema, dict):
            continue
        expected = field_schema.get("type")
        if expected and not _matches_json_type(value, expected):
            errors.append(f"argument {field_name!r} expected {expected}, got {type(value).__name__}")
    return errors


def _parse_jsonish(raw_text: str) -> tuple[Any, dict[str, Any], str | None]:
    metadata: dict[str, Any] = {"repair_applied": False, "repair_steps": []}
    candidates = [raw_text.strip()]
    fenced = _extract_fenced_json(raw_text)
    if fenced is not None:
        metadata["repair_applied"] = True
        metadata["repair_steps"].append("markdown_code_fence")
        candidates.insert(0, fenced)
    stripped = raw_text.strip()
    embedded = None if stripped.startswith(("{", "[")) else _extract_balanced_json(raw_text)
    if embedded is not None and embedded not in candidates:
        metadata["repair_applied"] = True
        metadata["repair_steps"].append("prose_wrapped_json")
        candidates.insert(0, embedded)

    last_error = "empty model output"
    for candidate in candidates:
        if not candidate:
            continue
        for repaired, step in ((candidate, None), (_remove_trailing_commas(candidate), "trailing_commas")):
            if step and repaired == candidate:
                continue
            try:
                parsed = json.loads(repaired)
            except json.JSONDecodeError as exc:
                last_error = str(exc)
                continue
            if step:
                metadata["repair_applied"] = True
                metadata["repair_steps"].append(step)
            return parsed, metadata, None
    return None, metadata, last_error


def _extract_fenced_json(text: str) -> str | None:
    match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_balanced_json(text: str) -> str | None:
    start_positions = [index for index, char in enumerate(text) if char in "[{"]
    for start in start_positions:
        opening = text[start]
        closing = "}" if opening == "{" else "]"
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(text)):
            char = text[index]
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == opening:
                depth += 1
            elif char == closing:
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
    return None


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _normalize_action(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    if "tool_call" in normalized and isinstance(normalized["tool_call"], dict):
        call = normalized["tool_call"]
        normalized.setdefault("action", "tool_call")
        normalized.setdefault("tool_name", call.get("tool_name") or call.get("name"))
        normalized.setdefault("arguments", call.get("arguments", {}))
        normalized.setdefault("call_id", call.get("call_id"))
    if "function" in normalized and isinstance(normalized["function"], dict):
        function = normalized["function"]
        normalized.setdefault("action", "tool_call")
        normalized.setdefault("tool_name", function.get("name"))
        normalized.setdefault("arguments", function.get("arguments", {}))
    if "final" in normalized and "final_answer" not in normalized:
        normalized["final_answer"] = normalized["final"]
        normalized.setdefault("action", "final_answer")
    return normalized


def _contains_multiple_tool_calls(payload: dict[str, Any]) -> bool:
    for key in ("tool_calls", "actions"):
        value = payload.get(key)
        if isinstance(value, list) and len(value) != 1:
            return True
    value = payload.get("tool_call")
    return isinstance(value, list) and len(value) != 1


def _extract_tool_call(payload: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    tool_name = payload.get("tool_name") or payload.get("name")
    arguments = payload.get("arguments", {})
    if isinstance(arguments, str):
        try:
            decoded = json.loads(arguments)
        except json.JSONDecodeError:
            decoded = {}
        arguments = decoded if isinstance(decoded, dict) else {}
    return (str(tool_name) if tool_name is not None else None), dict(arguments or {})


def _first_string(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return str(value)
    return None


def _metadata_with_call_id(metadata: dict[str, Any], call_id: Any) -> dict[str, Any]:
    if call_id is None:
        return metadata
    return {**metadata, "call_id": str(call_id)}


def _matches_json_type(value: Any, expected: str | list[str]) -> bool:
    if isinstance(expected, list):
        return any(_matches_json_type(value, item) for item in expected)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _repeats_failed_call(
    tool_name: str,
    arguments: dict[str, Any],
    observation_history: list[dict[str, Any]],
) -> bool:
    if not observation_history:
        return False
    last = observation_history[-1]
    action = last.get("action") if isinstance(last, dict) else None
    observation = last.get("observation") if isinstance(last, dict) else None
    if not isinstance(action, dict) or not isinstance(observation, dict):
        return False
    previous_call = action.get("tool_call")
    if not isinstance(previous_call, dict):
        return False
    return (
        previous_call.get("tool_name") == tool_name
        and previous_call.get("arguments", {}) == arguments
        and observation.get("error") is not None
    )


def _final_without_evidence(
    observation_history: list[dict[str, Any]],
    required_information: list[str],
) -> bool:
    if not required_information:
        return False
    return not any(isinstance(step.get("observation"), dict) for step in observation_history)
