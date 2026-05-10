from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from causal_agent_bench.schemas import BenchmarkTask, ToolObservation
from causal_agent_bench.tools.base import BaseTool
from causal_agent_bench.tools.simulated import build_simulated_tools

DEFAULT_KNOWLEDGE_BASE = Path(__file__).resolve().parents[3] / "data" / "sample" / "mock_knowledge_base.json"


class ToolRegistry:
    """Registry for deterministic local simulated tools."""

    def __init__(
        self,
        tools: list[BaseTool] | None = None,
        knowledge_base_path: str | Path | None = None,
    ) -> None:
        self._tools = {tool.name: tool for tool in (tools or build_simulated_tools())}
        self.knowledge_base = load_knowledge_base(knowledge_base_path or DEFAULT_KNOWLEDGE_BASE)

    @property
    def names(self) -> list[str]:
        return list(self._tools)

    def get(self, name: str) -> BaseTool:
        return self._tools[name]

    def specs(self, available_tools: list[str] | None = None):
        available = set(available_tools or self.names)
        return [tool.spec(is_available=tool.name in available) for tool in self._tools.values()]

    def call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        state_or_task: dict[str, Any] | BenchmarkTask | None = None,
        call_id: str | None = None,
    ) -> ToolObservation:
        state, converted_arguments = self._normalize_call_state(tool_name, arguments, state_or_task)
        state["current_call_id"] = call_id or state.get("current_call_id")
        if tool_name not in self._tools:
            return ToolObservation(
                tool_name=tool_name,
                call_id=state.get("current_call_id"),
                output=None,
                error="unknown_tool",
                metadata={"available_tools": self.names},
            )
        return self._tools[tool_name].run(converted_arguments, state)

    def _normalize_call_state(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        state_or_task: dict[str, Any] | BenchmarkTask | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if isinstance(state_or_task, BenchmarkTask):
            return _state_from_legacy_task(state_or_task, self.knowledge_base), _legacy_arguments(
                tool_name, arguments, state_or_task
            )
        state = deepcopy(state_or_task or {})
        state.setdefault("knowledge_base", deepcopy(self.knowledge_base))
        state.setdefault("available_tools", self.names)
        state.setdefault("tool_output_patch", {})
        state.setdefault("step_index", 0)
        return state, arguments


def load_knowledge_base(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _state_from_legacy_task(task: BenchmarkTask, default_kb: dict[str, Any]) -> dict[str, Any]:
    kb = deepcopy(default_kb)
    kb["records"] = task.mock_data.get("database", kb.get("records", []))
    kb["policies"] = _legacy_policies(task)
    kb["calendar_events"] = task.mock_data.get("calendar", kb.get("calendar_events", []))
    kb["files"] = task.mock_data.get("files", kb.get("files", {}))
    kb["spreadsheets"] = task.mock_data.get("spreadsheets", kb.get("spreadsheets", {}))
    kb["default_tax_rate"] = task.mock_data.get("tax_rate", kb.get("default_tax_rate", 0.0))
    kb["evidence"] = _legacy_evidence(task)
    state = {
        "knowledge_base": kb,
        "available_tools": list(task.available_tools),
        "initial_memory": task.mock_data.get("memory", {}),
        "tool_output_patch": {},
        "step_index": 0,
    }
    if task.intervention is not None:
        state["tool_output_patch"] = dict(task.intervention.tool_output_patch)
        if task.intervention.family == "premature_success_signal":
            state["premature_success_signal"] = task.intervention.metadata.get(
                "signal", "premature completion signal"
            )
        if task.intervention.family == "observation_conflict":
            state["conflicting_observation_tools"] = list(task.expected_behavior.required_tools[:1])
            state["conflicting_observation"] = task.mock_data.get("conflicting_observation")
    return state


def _legacy_policies(task: BenchmarkTask) -> dict[str, Any]:
    policies = {}
    for name, text in task.mock_data.get("policies", {}).items():
        policies[name] = {"text": text, "clauses": [{"id": f"{name}-1", "text": text}]}
    return policies


def _legacy_evidence(task: BenchmarkTask) -> dict[str, Any]:
    evidence = {}
    for index, (claim, truth) in enumerate(task.mock_data.get("facts", {}).items(), start=1):
        evidence[f"fact-{index}"] = {"text": claim, "supports": bool(truth)}
    return evidence


def _legacy_arguments(
    tool_name: str, arguments: dict[str, Any], task: BenchmarkTask
) -> dict[str, Any]:
    if tool_name == "calculate_price":
        item_ids = arguments.get("item_ids", [])
        if isinstance(item_ids, str):
            item_ids = [item_ids]
        catalog = {item["id"]: item for item in task.mock_data.get("catalog", [])}
        items = [
            {"id": item_id, "price": catalog[item_id]["price"], "quantity": 1}
            for item_id in item_ids
            if item_id in catalog
        ]
        return {"items": items, "constraints": {"tax_rate": arguments.get("tax_rate", task.mock_data.get("tax_rate", 0.0))}}
    if tool_name == "compare_options":
        option_ids = arguments.get("option_ids", [])
        options = task.mock_data.get("options", [])
        if option_ids:
            options = [option for option in options if option.get("id") in set(option_ids)]
        return {"options": options, "criteria": [arguments.get("criterion", "score")]}
    if tool_name == "lookup_policy":
        topic = arguments.get("topic") or arguments.get("policy_id") or arguments.get("policy_name")
        return {"policy_name": topic, "question": arguments.get("question", str(topic))}
    if tool_name == "check_calendar":
        return {"date": arguments.get("date"), "time_window": arguments.get("time_window")}
    if tool_name == "read_file":
        return {"file_id": arguments.get("file_id") or arguments.get("path"), "query": arguments.get("query")}
    if tool_name == "query_spreadsheet":
        query = " ".join(str(v) for v in arguments.values() if v is not None)
        return {"sheet_id": arguments.get("sheet_id") or arguments.get("sheet"), "query": query}
    if tool_name == "send_email_draft":
        return {
            "recipient": arguments.get("recipient") or arguments.get("to"),
            "subject": arguments.get("subject"),
            "body": arguments.get("body"),
        }
    if tool_name == "book_stub":
        return {
            "item_id": arguments.get("item_id") or arguments.get("option_id"),
            "confirmation_required": arguments.get("confirmation_required", True),
        }
    if tool_name == "verify_fact":
        claim = arguments.get("claim") or arguments.get("statement")
        evidence_ids = arguments.get("evidence_ids") or list(_legacy_evidence(task))
        return {"claim": claim, "evidence_ids": evidence_ids}
    return arguments


ALL_TOOL_NAMES = [tool.name for tool in build_simulated_tools()]
