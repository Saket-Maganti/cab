from __future__ import annotations

import hashlib
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from causal_agent_bench.schemas import BenchmarkTask, ToolObservation

ALL_TOOL_NAMES = [
    "search_database",
    "lookup_policy",
    "check_calendar",
    "read_file",
    "query_spreadsheet",
    "calculate_price",
    "compare_options",
    "send_email_draft",
    "book_stub",
    "verify_fact",
]


class ToolRegistry:
    """Deterministic simulated tools backed by each task's mock_data."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[[dict[str, Any], BenchmarkTask], dict[str, Any]]] = {
            "search_database": search_database,
            "lookup_policy": lookup_policy,
            "check_calendar": check_calendar,
            "read_file": read_file,
            "query_spreadsheet": query_spreadsheet,
            "calculate_price": calculate_price,
            "compare_options": compare_options,
            "send_email_draft": send_email_draft,
            "book_stub": book_stub,
            "verify_fact": verify_fact,
        }

    @property
    def names(self) -> list[str]:
        return list(self._tools)

    def call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        task: BenchmarkTask,
        call_id: str | None = None,
    ) -> ToolObservation:
        if tool_name not in self._tools:
            return ToolObservation(
                tool_name=tool_name,
                call_id=call_id,
                error="unknown_tool",
            )
        if tool_name not in task.available_tools:
            return ToolObservation(
                tool_name=tool_name,
                call_id=call_id,
                error="tool_unavailable",
            )
        failure = _forced_failure(tool_name, task)
        if failure is not None:
            return ToolObservation(
                tool_name=tool_name,
                call_id=call_id,
                output=failure.get("output", {}),
                error=failure.get("error", "tool_failure"),
            )
        try:
            output = self._tools[tool_name](arguments, task)
        except KeyError as exc:
            return ToolObservation(
                tool_name=tool_name,
                call_id=call_id,
                error="invalid_arguments",
                output={"missing": str(exc)},
            )
        except ValueError as exc:
            return ToolObservation(
                tool_name=tool_name,
                call_id=call_id,
                error="invalid_arguments",
                output={"message": str(exc)},
            )
        output, is_corrupted = _maybe_corrupt(tool_name, output, task)
        return ToolObservation(
            tool_name=tool_name,
            call_id=call_id,
            output=output,
            is_corrupted=is_corrupted,
        )


def _forced_failure(tool_name: str, task: BenchmarkTask) -> dict[str, Any] | None:
    intervention = task.intervention
    if intervention is None or intervention.type != "tool_failure":
        return None
    target = intervention.params.get("target_tool")
    if target != tool_name:
        return None
    return {
        "error": intervention.params.get("error", "tool_failure"),
        "output": intervention.params.get("partial_output", {}),
    }


def _maybe_corrupt(
    tool_name: str, output: dict[str, Any], task: BenchmarkTask
) -> tuple[dict[str, Any], bool]:
    intervention = task.intervention
    if intervention is None or intervention.family != "tool_corruption":
        return output, False
    if intervention.tool_output_patch.get("target_tool") != tool_name:
        return output, False
    corrupted = deepcopy(output)
    for dotted_key, value in intervention.tool_output_patch.get("overrides", {}).items():
        _set_dotted(corrupted, dotted_key, value)
    corrupted["corrupted"] = True
    return corrupted, True


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


def _records(task: BenchmarkTask, key: str) -> list[dict[str, Any]]:
    records = task.mock_data.get(key, [])
    if not isinstance(records, list):
        raise ValueError(f"mock_data.{key} must be a list")
    return records


def _contains(haystack: Any, needle: str) -> bool:
    return needle.lower() in str(haystack).lower()


def search_database(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    query = str(arguments.get("query", "")).strip().lower()
    if not query:
        raise ValueError("query is required")
    limit = int(arguments.get("limit", 5))
    matches = []
    for record in _records(task, "database"):
        searchable = " ".join(str(v) for v in record.values()).lower()
        if all(token in searchable for token in query.split()):
            matches.append(record)
    if not matches:
        for record in _records(task, "database"):
            searchable = " ".join(str(v) for v in record.values()).lower()
            if any(token in searchable for token in query.split()):
                matches.append(record)
    return {"query": query, "results": matches[:limit], "count": len(matches)}


def lookup_policy(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    topic = str(arguments.get("topic", arguments.get("policy_id", ""))).strip()
    if not topic:
        raise ValueError("topic or policy_id is required")
    policies = task.mock_data.get("policies", {})
    if not isinstance(policies, dict):
        raise ValueError("mock_data.policies must be an object")
    for policy_id, policy in policies.items():
        if _contains(policy_id, topic) or _contains(policy, topic):
            return {"policy_id": policy_id, "policy": policy}
    return {"policy_id": None, "policy": None}


def check_calendar(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    date = str(arguments.get("date", "")).strip()
    participant = str(arguments.get("participant", arguments.get("owner", ""))).strip().lower()
    if not date:
        raise ValueError("date is required")
    events = []
    for event in _records(task, "calendar"):
        event_participants = [str(p).lower() for p in event.get("participants", [])]
        participant_match = not participant or participant in event_participants
        if event.get("date") == date and participant_match:
            events.append(event)
    busy = [{"start": e.get("start"), "end": e.get("end"), "title": e.get("title")} for e in events]
    return {"date": date, "participant": participant or None, "busy": busy, "free": len(busy) == 0}


def read_file(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    path = str(arguments.get("path", "")).strip()
    if not path:
        raise ValueError("path is required")
    files = task.mock_data.get("files", {})
    if not isinstance(files, dict):
        raise ValueError("mock_data.files must be an object")
    if path not in files:
        raise ValueError(f"file not found: {path}")
    return {"path": path, "content": files[path]}


def query_spreadsheet(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    sheet = str(arguments.get("sheet", "")).strip()
    operation = str(arguments.get("operation", "lookup")).strip()
    column = str(arguments.get("column", "")).strip()
    match_column = str(arguments.get("match_column", "")).strip()
    match_value = arguments.get("match_value")
    if not sheet:
        raise ValueError("sheet is required")
    sheets = task.mock_data.get("spreadsheets", {})
    if sheet not in sheets:
        raise ValueError(f"sheet not found: {sheet}")
    rows = sheets[sheet]
    if not isinstance(rows, list):
        raise ValueError("spreadsheet sheet must contain rows")
    filtered = rows
    if match_column:
        filtered = [row for row in rows if row.get(match_column) == match_value]
    if operation == "sum":
        return {"sheet": sheet, "operation": operation, "value": sum(float(r.get(column, 0)) for r in filtered)}
    if operation == "max":
        best = max(filtered, key=lambda r: float(r.get(column, 0)), default=None)
        return {"sheet": sheet, "operation": operation, "row": best}
    if operation == "min":
        best = min(filtered, key=lambda r: float(r.get(column, 0)), default=None)
        return {"sheet": sheet, "operation": operation, "row": best}
    return {"sheet": sheet, "operation": "lookup", "rows": filtered}


def calculate_price(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    item_ids = arguments.get("item_ids", [])
    if isinstance(item_ids, str):
        item_ids = [item_ids]
    catalog = {item["id"]: item for item in _records(task, "catalog")}
    subtotal = 0.0
    items = []
    for item_id in item_ids:
        if item_id not in catalog:
            raise ValueError(f"unknown item_id: {item_id}")
        item = catalog[item_id]
        price = float(item.get("price", 0))
        subtotal += price
        items.append({"id": item_id, "price": price})
    discount = float(arguments.get("discount", task.mock_data.get("discount", 0.0)))
    tax_rate = float(arguments.get("tax_rate", task.mock_data.get("tax_rate", 0.0)))
    discounted = subtotal * (1 - discount)
    total = round(discounted * (1 + tax_rate), 2)
    return {
        "items": items,
        "subtotal": round(subtotal, 2),
        "discount": discount,
        "tax_rate": tax_rate,
        "total": total,
    }


def compare_options(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    option_ids = arguments.get("option_ids", [])
    criterion = str(arguments.get("criterion", "score")).strip()
    direction = str(arguments.get("direction", "max")).strip()
    options = _records(task, "options")
    if option_ids:
        option_set = set(option_ids)
        options = [option for option in options if option.get("id") in option_set]
    if not options:
        raise ValueError("no options to compare")
    reverse = direction != "min"
    best = sorted(options, key=lambda o: float(o.get(criterion, 0)), reverse=reverse)[0]
    return {"criterion": criterion, "direction": direction, "best": best, "options": options}


def send_email_draft(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    to = str(arguments.get("to", "")).strip()
    subject = str(arguments.get("subject", "")).strip()
    body = str(arguments.get("body", "")).strip()
    if not to or not subject or not body:
        raise ValueError("to, subject, and body are required")
    digest = hashlib.sha256(f"{task.task_id}|{to}|{subject}|{body}".encode()).hexdigest()
    draft_id = f"draft-{int(digest[:8], 16) % 100000:05d}"
    return {"draft_id": draft_id, "to": to, "subject": subject, "body": body, "sent": False}


def book_stub(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    option_id = str(arguments.get("option_id", "")).strip()
    if not option_id:
        raise ValueError("option_id is required")
    if not task.expected_behavior.allow_booking:
        return {"booked": False, "reason": "booking_not_allowed_for_task", "option_id": option_id}
    return {"booked": True, "reference": f"BOOK-{task.task_id.upper()}-{option_id.upper()}", "option_id": option_id}


def verify_fact(arguments: dict[str, Any], task: BenchmarkTask) -> dict[str, Any]:
    statement = str(arguments.get("statement", "")).strip()
    if not statement:
        raise ValueError("statement is required")
    facts = task.mock_data.get("facts", {})
    if not isinstance(facts, dict):
        raise ValueError("mock_data.facts must be an object")
    normalized = statement.lower()
    for known_statement, truth in facts.items():
        if known_statement.lower() == normalized or normalized in known_statement.lower():
            return {"statement": statement, "supported": bool(truth), "source": "mock_facts"}
    return {"statement": statement, "supported": False, "source": "mock_facts", "unknown": True}
