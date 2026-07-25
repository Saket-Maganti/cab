from __future__ import annotations

import random
import re
from abc import ABC, abstractmethod
from typing import Any

from causal_agent_bench.schemas import (
    AgentAction,
    BenchmarkInstance,
    BenchmarkTask,
    ToolCall,
    ToolSpec,
)


class BaseAgent(ABC):
    """Base interface for deterministic and future LLM-backed agents."""

    name = "base_agent"
    uses_hidden_information = False

    def __init__(self, seed: int = 0, **_: Any) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.instance: BenchmarkInstance | None = None
        self.legacy_task: BenchmarkTask | None = None

    def reset(self, instance: BenchmarkInstance | BenchmarkTask, seed: int | None = None) -> None:
        if seed is not None:
            self.seed = seed
        self.rng = random.Random(self.seed)
        if isinstance(instance, BenchmarkTask):
            self.legacy_task = instance
            self.instance = None
        else:
            self.instance = instance
            self.legacy_task = None

    @abstractmethod
    def act(
        self,
        observation_history: list[dict[str, Any]],
        available_tools: list[ToolSpec],
    ) -> AgentAction:
        raise NotImplementedError

    def user_instruction(self) -> str:
        if self.instance is not None:
            return self.instance.base_task.goal.user_instruction
        if self.legacy_task is not None:
            return self.legacy_task.user_goal
        return ""

    def domain(self) -> str:
        if self.instance is not None:
            return self.instance.base_task.domain
        if self.legacy_task is not None:
            return self.legacy_task.domain
        return ""

    def gold_tool_sequence(self) -> list[str]:
        if self.instance is not None:
            return list(self.instance.base_task.gold_tool_sequence or [])
        if self.legacy_task is not None:
            return list(
                self.legacy_task.expected_behavior.tool_sequence
                or self.legacy_task.expected_behavior.required_tools
            )
        return []

    def expected_answer(self) -> str:
        if self.instance is not None:
            expected = self.instance.base_task.goal.expected_final_answer
            if isinstance(expected, dict):
                return ", ".join(f"{key}: {value}" for key, value in sorted(expected.items()))
            return str(expected or "Done.")
        if self.legacy_task is not None:
            answers = self.legacy_task.expected_behavior.acceptable_final_answers
            answer = answers[0] if answers else "Done."
            if (
                self.legacy_task.expected_behavior.must_detect_contradiction
                and "conflict" not in answer.lower()
            ):
                answer += " I detected conflicting evidence and treated it as requiring verification."
            if self.legacy_task.expected_behavior.must_verify_memory and "verified" not in answer.lower():
                answer += " I verified the memory against the available facts."
            return answer
        return "Done."

    def tool_arguments(
        self,
        tool_name: str,
        tool_spec: ToolSpec | None = None,
        observation_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if self.legacy_task is not None:
            args = self.legacy_task.expected_behavior.tool_arguments.get(tool_name)
            if args is not None:
                return dict(args)
        if self.instance is not None:
            hidden = self.instance.base_task.hidden_ground_truth
            call_plan = hidden.get("oracle_tool_calls")
            if isinstance(call_plan, list) and call_plan:
                index = len(self.called_tools(observation_history or []))
                if index < len(call_plan):
                    step = call_plan[index]
                    if isinstance(step, dict):
                        if step.get("tool") == tool_name:
                            return dict(step.get("arguments", {}))
                        if tool_name in step:
                            return dict(step[tool_name])
            per_tool = hidden.get("oracle_tool_args", {}).get(tool_name)
            if isinstance(per_tool, dict):
                return dict(per_tool)
        return default_tool_arguments(tool_name, self.user_instruction(), self.domain(), oracle=self)

    def called_tools(self, observation_history: list[dict[str, Any]]) -> list[str]:
        calls = []
        for step in observation_history:
            step_dict = _as_dict(step)
            action = _as_dict(step_dict.get("action", {}))
            tool_call = action.get("tool_call") if isinstance(action, dict) else None
            if tool_call:
                calls.append(_as_dict(tool_call)["tool_name"])
        return calls

    def has_error(self, observation_history: list[dict[str, Any]]) -> bool:
        for step in observation_history:
            obs = _as_dict(_as_dict(step).get("observation"))
            if obs.get("error"):
                return True
        return False

    def tool_by_name(self, available_tools: list[ToolSpec], tool_name: str) -> ToolSpec | None:
        return next((tool for tool in available_tools if tool.name == tool_name and tool.is_available), None)


def tool_action(tool_name: str, arguments: dict[str, Any], thought: str | None = None) -> AgentAction:
    return AgentAction(tool_call=ToolCall(tool_name=tool_name, arguments=arguments), thought=thought)


def final_action(answer: str, thought: str | None = None) -> AgentAction:
    return AgentAction(final_answer=answer, stop=True, thought=thought)


def default_tool_arguments(
    tool_name: str,
    user_instruction: str,
    domain: str,
    oracle: BaseAgent | None = None,
) -> dict[str, Any]:
    instruction = user_instruction.lower()
    date = _extract_date(user_instruction) or "2026-06-03"
    if tool_name == "search_database":
        return {"query": _compact_query(user_instruction), "domain": _domain_alias(domain)}
    if tool_name == "lookup_policy":
        policy = "refunds" if "refund" in instruction else "vendor" if "vendor" in instruction else "general"
        return {"policy_name": policy, "question": user_instruction}
    if tool_name == "check_calendar":
        window = "12:00-17:00" if "afternoon" in instruction else None
        return {"date": date, "time_window": window}
    if tool_name == "read_file":
        file_id = "retry_helper" if "retry" in instruction else "launch_note"
        query = "bug" if "bug" in instruction else "revenue" if "revenue" in instruction else None
        return {"file_id": file_id, "query": query}
    if tool_name == "query_spreadsheet":
        sheet = "vendor_scores" if "vendor" in instruction else "revenue"
        return {"sheet_id": sheet, "query": user_instruction}
    if tool_name == "calculate_price":
        return {"items": _price_items(oracle), "constraints": {"tax_rate": 0.1, "currency": "USD"}}
    if tool_name == "compare_options":
        return {"options": _options(oracle), "criteria": ["price" if "cheap" in instruction or "cost" in instruction else "score"]}
    if tool_name == "send_email_draft":
        return {
            "recipient": "mina@example.com",
            "subject": "Proposed meeting time",
            "body": f"Can we meet at 15:00 on {date}?",
        }
    if tool_name == "book_stub":
        return {"item_id": "saver_hotel", "confirmation_required": True}
    if tool_name == "verify_fact":
        return {"claim": user_instruction, "evidence_ids": ["refund_threshold", "calendar_1500", "travel_saver_hotel"]}
    if tool_name == "web_open_page":
        start = "/"
        if oracle is not None and oracle.instance is not None:
            start = oracle.instance.base_task.hidden_ground_truth.get("navigation", {}).get("start_url", "/")
        return {"url": start}
    if tool_name == "web_follow_link":
        nav = {}
        if oracle is not None and oracle.instance is not None:
            nav = oracle.instance.base_task.hidden_ground_truth.get("navigation", {})
        href = nav.get("follow_href")
        if href:
            return {"href": href}
        return {"link_text": "documentation"}
    if tool_name == "web_search_snapshot":
        query = "task"
        if oracle is not None and oracle.instance is not None:
            query = oracle.instance.base_task.hidden_ground_truth.get("navigation", {}).get("search_query", query)
        return {"query": query}
    if tool_name == "web_extract_section":
        section_id = "sku"
        if oracle is not None and oracle.instance is not None:
            section_id = oracle.instance.base_task.hidden_ground_truth.get("navigation", {}).get("section_id", section_id)
        return {"section_id": section_id}
    return {}


def _extract_date(text: str) -> str | None:
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    return match.group(0) if match else None


def _compact_query(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text)
    useful = [word for word in words if len(word) > 3][:8]
    return " ".join(useful) or "task"


def _domain_alias(domain: str) -> str | None:
    if "travel" in domain:
        return "travel"
    if "shopping" in domain:
        return "shopping"
    return None


def _price_items(agent: BaseAgent | None) -> list[dict[str, Any]]:
    if agent is not None and agent.instance is not None:
        truth = agent.instance.base_task.hidden_ground_truth
        if truth.get("best_option_id") == "saver_hotel":
            return [{"id": "saver_hotel", "price": 160, "quantity": 1}]
    return [{"id": "saver_hotel", "price": 160, "quantity": 1}]


def _options(agent: BaseAgent | None) -> list[dict[str, Any]]:
    if agent is not None and agent.instance is not None and "calendar" in agent.domain():
        return [{"id": "15:00", "score": 1.0}]
    return [{"id": "saver_hotel", "price": 160, "score": 0.8}, {"id": "flex_hotel", "price": 210, "score": 0.9}]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    return {}
