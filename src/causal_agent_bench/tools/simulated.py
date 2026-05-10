from __future__ import annotations

import hashlib
from typing import Any

from causal_agent_bench.tools.base import BaseTool


class SearchDatabaseTool(BaseTool):
    name = "search_database"
    description = "Search local synthetic records by query and optional domain."
    input_schema = {"type": "object", "required": ["query"], "properties": {"query": {"type": "string"}, "domain": {"type": ["string", "null"]}}}
    output_schema = {"type": "object", "required": ["results"], "properties": {"results": {"type": "array"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments["query"]).lower().strip()
        domain = arguments.get("domain")
        records = state["knowledge_base"].get("records", [])
        tokens = [token for token in query.split() if token]
        results = []
        for record in records:
            if domain and record.get("domain") != domain:
                continue
            haystack = " ".join(str(value) for value in record.values()).lower()
            if all(token in haystack for token in tokens) or any(token in haystack for token in tokens):
                results.append(record)
        return {"results": results[:10]}


class LookupPolicyTool(BaseTool):
    name = "lookup_policy"
    description = "Lookup a synthetic policy document and return relevant clause ids."
    input_schema = {"type": "object", "required": ["policy_name", "question"], "properties": {"policy_name": {"type": "string"}, "question": {"type": "string"}}}
    output_schema = {"type": "object", "required": ["policy_text", "relevant_clause_ids"], "properties": {"policy_text": {"type": "string"}, "relevant_clause_ids": {"type": "array"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        policy_name = str(arguments["policy_name"]).lower()
        question = str(arguments["question"]).lower()
        policies = state["knowledge_base"].get("policies", {})
        for key, policy in policies.items():
            if key.lower() == policy_name or policy_name in key.lower():
                clauses = policy.get("clauses", [])
                relevant = []
                for clause in clauses:
                    text = clause.get("text", "").lower()
                    if any(token in text for token in question.split()):
                        relevant.append(clause.get("id"))
                return {
                    "policy_text": policy.get("text", ""),
                    "relevant_clause_ids": [clause_id for clause_id in relevant if clause_id],
                }
        return {"policy_text": "", "relevant_clause_ids": []}


class CheckCalendarTool(BaseTool):
    name = "check_calendar"
    description = "Read synthetic calendar events for a date and optional time window."
    input_schema = {"type": "object", "required": ["date"], "properties": {"date": {"type": "string"}, "time_window": {"type": ["string", "null"]}}}
    output_schema = {"type": "object", "required": ["events", "is_free"], "properties": {"events": {"type": "array"}, "is_free": {"type": "boolean"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        date = str(arguments["date"])
        time_window = arguments.get("time_window")
        events = [
            event
            for event in state["knowledge_base"].get("calendar_events", [])
            if event.get("date") == date
        ]
        if time_window:
            events = [event for event in events if _overlaps_window(event, str(time_window))]
        return {"events": events, "is_free": len(events) == 0}


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read a synthetic local file by id and optionally return matched sections."
    input_schema = {"type": "object", "required": ["file_id"], "properties": {"file_id": {"type": "string"}, "query": {"type": ["string", "null"]}}}
    output_schema = {"type": "object", "required": ["content", "matched_sections"], "properties": {"content": {"type": "string"}, "matched_sections": {"type": "array"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        file_id = str(arguments["file_id"])
        files = state["knowledge_base"].get("files", {})
        if file_id not in files:
            raise ValueError(f"unknown file_id: {file_id}")
        content = files[file_id]
        query = str(arguments.get("query") or "").lower()
        sections = [part.strip() for part in content.split("\n\n") if part.strip()]
        matched = [section for section in sections if query and query in section.lower()]
        return {"content": content, "matched_sections": matched}


class QuerySpreadsheetTool(BaseTool):
    name = "query_spreadsheet"
    description = "Query synthetic spreadsheet rows with a simple text query."
    input_schema = {"type": "object", "required": ["sheet_id", "query"], "properties": {"sheet_id": {"type": "string"}, "query": {"type": "string"}}}
    output_schema = {"type": "object", "required": ["rows", "summary"], "properties": {"rows": {"type": "array"}, "summary": {"type": "string"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        sheet_id = str(arguments["sheet_id"])
        query = str(arguments["query"]).lower()
        sheets = state["knowledge_base"].get("spreadsheets", {})
        if sheet_id not in sheets:
            raise ValueError(f"unknown sheet_id: {sheet_id}")
        rows = sheets[sheet_id]
        tokens = [token for token in query.split() if token]
        matched = [
            row
            for row in rows
            if not tokens or any(token in " ".join(str(value).lower() for value in row.values()) for token in tokens)
        ]
        return {"rows": matched, "summary": f"{len(matched)} rows matched query '{query}'."}


class CalculatePriceTool(BaseTool):
    name = "calculate_price"
    description = "Calculate deterministic totals for item dictionaries."
    input_schema = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array"}, "constraints": {"type": "object"}}}
    output_schema = {"type": "object", "required": ["total", "currency", "breakdown"], "properties": {"total": {"type": "number"}, "currency": {"type": "string"}, "breakdown": {"type": "array"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        items = arguments["items"]
        if not isinstance(items, list):
            raise ValueError("items must be a list")
        constraints = arguments.get("constraints") or {}
        tax_rate = float(constraints.get("tax_rate", state["knowledge_base"].get("default_tax_rate", 0.0)))
        currency = str(constraints.get("currency", "USD"))
        breakdown = []
        subtotal = 0.0
        for item in items:
            price = float(item.get("price", 0))
            quantity = int(item.get("quantity", 1))
            line_total = price * quantity
            subtotal += line_total
            breakdown.append({"item_id": item.get("id"), "quantity": quantity, "line_total": round(line_total, 2)})
        total = round(subtotal * (1 + tax_rate), 2)
        return {"total": total, "currency": currency, "breakdown": breakdown}


class CompareOptionsTool(BaseTool):
    name = "compare_options"
    description = "Rank option dictionaries according to deterministic criteria."
    input_schema = {"type": "object", "required": ["options", "criteria"], "properties": {"options": {"type": "array"}, "criteria": {"type": "array"}}}
    output_schema = {"type": "object", "required": ["ranking", "best_option_id"], "properties": {"ranking": {"type": "array"}, "best_option_id": {"type": "string"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        options = arguments["options"]
        criteria = arguments["criteria"]
        if not isinstance(options, list) or not options:
            raise ValueError("options must be a non-empty list")
        if not isinstance(criteria, list) or not criteria:
            raise ValueError("criteria must be a non-empty list")
        criterion = str(criteria[0])
        reverse = criterion not in {"price", "cost", "risk"}
        ranking = sorted(options, key=lambda option: float(option.get(criterion, 0)), reverse=reverse)
        return {"ranking": ranking, "best_option_id": str(ranking[0].get("id"))}


class SendEmailDraftTool(BaseTool):
    name = "send_email_draft"
    description = "Create a simulated email draft. This never sends real email."
    input_schema = {"type": "object", "required": ["recipient", "subject", "body"], "properties": {"recipient": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}}
    output_schema = {"type": "object", "required": ["draft_id", "status"], "properties": {"draft_id": {"type": "string"}, "status": {"type": "string"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        seed = f"{arguments['recipient']}|{arguments['subject']}|{arguments['body']}"
        digest = hashlib.sha256(seed.encode()).hexdigest()[:10]
        return {"draft_id": f"draft_{digest}", "status": "draft_created"}


class BookStubTool(BaseTool):
    name = "book_stub"
    description = "Simulate a booking flow. This never makes real bookings."
    input_schema = {"type": "object", "required": ["item_id", "confirmation_required"], "properties": {"item_id": {"type": "string"}, "confirmation_required": {"type": "boolean"}}}
    output_schema = {"type": "object", "required": ["booking_status", "confirmation_id"], "properties": {"booking_status": {"type": "string"}, "confirmation_id": {"type": ["string", "null"]}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        if arguments["confirmation_required"]:
            return {"booking_status": "confirmation_required", "confirmation_id": None}
        digest = hashlib.sha256(str(arguments["item_id"]).encode()).hexdigest()[:8]
        return {"booking_status": "stub_confirmed", "confirmation_id": f"STUB-{digest}"}


class VerifyFactTool(BaseTool):
    name = "verify_fact"
    description = "Verify a synthetic claim against local evidence ids."
    input_schema = {"type": "object", "required": ["claim", "evidence_ids"], "properties": {"claim": {"type": "string"}, "evidence_ids": {"type": "array"}}}
    output_schema = {"type": "object", "required": ["verdict", "supporting_evidence"], "properties": {"verdict": {"type": "string"}, "supporting_evidence": {"type": "array"}}}

    def _run(self, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        claim = str(arguments["claim"]).lower()
        evidence_ids = arguments["evidence_ids"]
        evidence = state["knowledge_base"].get("evidence", {})
        supporting = []
        contradicting = []
        for evidence_id in evidence_ids:
            item = evidence.get(evidence_id)
            if not item:
                continue
            text = str(item.get("text", "")).lower()
            if any(token in text for token in claim.split()):
                if item.get("supports", True):
                    supporting.append(evidence_id)
                else:
                    contradicting.append(evidence_id)
        verdict = "supported" if supporting and not contradicting else "contradicted" if contradicting else "unknown"
        return {"verdict": verdict, "supporting_evidence": supporting}


def build_simulated_tools() -> list[BaseTool]:
    return [
        SearchDatabaseTool(),
        LookupPolicyTool(),
        CheckCalendarTool(),
        ReadFileTool(),
        QuerySpreadsheetTool(),
        CalculatePriceTool(),
        CompareOptionsTool(),
        SendEmailDraftTool(),
        BookStubTool(),
        VerifyFactTool(),
    ]


def _overlaps_window(event: dict[str, Any], window: str) -> bool:
    if "-" not in window:
        return True
    start, end = window.split("-", 1)
    event_start = str(event.get("start", ""))
    event_end = str(event.get("end", ""))
    return not (event_end <= start or event_start >= end)
