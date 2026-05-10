from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

from causal_agent_bench.schemas import ToolObservation, ToolSpec


class BaseTool(ABC):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

    def run(self, arguments: dict[str, Any], state: dict[str, Any]) -> ToolObservation:
        """Validate arguments, execute deterministically, then apply intervention effects."""

        call_id = state.get("current_call_id")
        missing = self._missing_required(arguments)
        if missing:
            return ToolObservation(
                tool_name=self.name,
                call_id=call_id,
                output={"missing": missing},
                error="invalid_arguments",
                metadata={"message": f"missing required arguments: {', '.join(missing)}"},
            )
        if self.name not in state.get("available_tools", []):
            return ToolObservation(
                tool_name=self.name,
                call_id=call_id,
                output=None,
                error="tool_unavailable",
                metadata={"available_tools": state.get("available_tools", [])},
            )

        forced = self._forced_output_patch(state)
        if forced is not None:
            return forced

        try:
            output = self._run(arguments, state)
        except ValueError as exc:
            return ToolObservation(
                tool_name=self.name,
                call_id=call_id,
                output={"message": str(exc)},
                error="invalid_arguments",
                metadata={"arguments": arguments},
            )

        output, corrupted = self._apply_corruption(output, state)
        metadata = {
            "arguments": deepcopy(arguments),
            "step": state.get("step_index"),
            "deterministic": True,
        }
        if self.name in state.get("conflicting_observation_tools", []):
            metadata["conflict_inserted"] = True
            output = deepcopy(output)
            output["conflicting_observation"] = state.get(
                "conflicting_observation",
                {"source_a": "approved", "source_b": "denied"},
            )
        if state.get("premature_success_signal") and state.get("step_index") == 0:
            metadata["premature_success_signal"] = state["premature_success_signal"]
        return ToolObservation(
            tool_name=self.name,
            call_id=call_id,
            output=output,
            error=None,
            is_corrupted=corrupted,
            metadata=metadata,
        )

    def spec(self, is_available: bool = True) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            failure_modes=["invalid_arguments", "tool_unavailable", "tool_failure"],
            is_available=is_available,
        )

    def _missing_required(self, arguments: dict[str, Any]) -> list[str]:
        required = self.input_schema.get("required", [])
        return [field for field in required if field not in arguments or arguments[field] is None]

    def _forced_output_patch(self, state: dict[str, Any]) -> ToolObservation | None:
        patch = state.get("tool_output_patch", {})
        target = patch.get("target_tool")
        if target not in {self.name, None}:
            return None
        if patch.get("error"):
            return ToolObservation(
                tool_name=self.name,
                call_id=state.get("current_call_id"),
                output=patch.get("partial_output"),
                error=patch["error"],
                metadata={
                    "intervention": "tool_failure",
                    "patch": deepcopy(patch),
                    "step": state.get("step_index"),
                },
            )
        if patch.get("partial_output") and patch.get("mode") == "partial":
            return ToolObservation(
                tool_name=self.name,
                call_id=state.get("current_call_id"),
                output=patch["partial_output"],
                error=None,
                metadata={
                    "intervention": "partial_output",
                    "patch": deepcopy(patch),
                    "step": state.get("step_index"),
                },
            )
        return None

    def _apply_corruption(
        self, output: dict[str, Any], state: dict[str, Any]
    ) -> tuple[dict[str, Any], bool]:
        patch = state.get("tool_output_patch", {})
        target = patch.get("target_tool")
        if target not in {self.name, None}:
            return output, False
        overrides = patch.get("overrides") or patch.get("corruptions")
        if not overrides:
            return output, False
        corrupted = deepcopy(output)
        for dotted_key, value in overrides.items():
            _set_dotted(corrupted, dotted_key, value)
        corrupted["corrupted"] = True
        return corrupted, True

    @abstractmethod
    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


def _set_dotted(payload: dict[str, Any], dotted_key: str, value: Any) -> None:
    cursor = payload
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        next_cursor = cursor.get(part)
        if not isinstance(next_cursor, dict):
            next_cursor = {}
            cursor[part] = next_cursor
        cursor = next_cursor
    cursor[parts[-1]] = value
