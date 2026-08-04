"""The sixteen semantic objectives and the frozen twenty-pair design matrix.

Each objective is a genuinely distinct user task with its own goal, evidence
schema, tool repertoire and derivation.  Objectives carry a hand-specified
expected answer that the executable derivation must reproduce; the two are
written independently so that route validation is a real cross-check rather
than a tautology.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from causal_agent_bench.review_ready_v2.models import (
    Difficulty,
    Domain,
    Family,
    Route,
    ToolContract,
)


@dataclass(frozen=True)
class Nuisance:
    """Controlled, semantics-preserving variation used by true anchors."""

    tag: str
    reverse_records: bool = False

    def label(self, prefix: str) -> str:
        return f"{prefix}-{self.tag}"


def _order(records: list[dict[str, Any]], nuisance: Nuisance) -> list[dict[str, Any]]:
    return list(reversed(records)) if nuisance.reverse_records else list(records)


@dataclass(frozen=True)
class Objective:
    """One semantic objective: goal, environment builder, and derivation."""

    objective_id: str
    archetype: str
    domain: Domain
    goal: str
    prompt: str
    counterparty: str
    counterparty_resolvable_inputs: tuple[str, ...]
    required_input_keys: tuple[str, ...]
    build_environment: Callable[[Nuisance], tuple[dict[str, Any], dict[str, Any], dict[str, int]]]
    tools: Callable[[Nuisance], list[ToolContract]]
    derive: Callable[[dict[str, Any]], str]
    expected_answer: Callable[[Nuisance], str]
    evidence_manifest: dict[str, list[str]] = field(default_factory=dict)


def _tool(
    tool_id: str,
    capability: str,
    scope: str,
    returned_fields: list[str],
    provides: list[str],
    *,
    authorization: str = "standard",
    allowed_arguments: list[str] | None = None,
    failure_modes: list[str] | None = None,
) -> ToolContract:
    return ToolContract(
        tool_id=tool_id,
        declared_capability=capability,  # type: ignore[arg-type]
        scope_source=scope,
        allowed_arguments=allowed_arguments or [],
        returned_fields=returned_fields,
        failure_modes=failure_modes or ["upstream_unavailable", "timeout", "permission_denied"],
        authorization_scope=authorization,  # type: ignore[arg-type]
        provides_inputs=provides,
    )


# ---------------------------------------------------------------------------
# travel
# ---------------------------------------------------------------------------


def _hotel_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    rows = [
        {"code": n.label("CDR"), "nightly_rate": 118, "tax_rate": 0.08, "refundable": True},
        {"code": n.label("HBR"), "nightly_rate": 104, "tax_rate": 0.12, "refundable": False},
        {"code": n.label("LKS"), "nightly_rate": 126, "tax_rate": 0.05, "refundable": True},
    ]
    sources = {
        "hotel_rate_table": _order(rows, n),
        "partner_rate_mirror": _order(rows, n),
        "stay_requirements": {"nights": 2, "budget": 300.0, "refundable_required": True},
    }
    return sources, {}, {"hotel_rate_table": 1, "partner_rate_mirror": 2}


def _hotel_tools(n: Nuisance) -> list[ToolContract]:
    fields = ["code", "nightly_rate", "tax_rate", "refundable"]
    return [
        _tool("hotel_rate_catalog", "collection_read", "hotel_rate_table", fields, ["hotel_rates"]),
        _tool("partner_rate_mirror_feed", "collection_read", "partner_rate_mirror", fields, ["hotel_rates"]),
        _tool(
            "stay_requirements_lookup",
            "record_lookup",
            "stay_requirements",
            ["nights", "budget", "refundable_required"],
            ["stay_requirements"],
        ),
    ]


def _hotel_derive(resolved: dict[str, Any]) -> str:
    rates = resolved["hotel_rates"]
    requirements = resolved["stay_requirements"]
    nights = int(requirements["nights"])
    candidates: list[tuple[float, str]] = []
    for row in rates:
        if requirements["refundable_required"] and not row["refundable"]:
            continue
        total = round(row["nightly_rate"] * nights * (1 + row["tax_rate"]), 2)
        if total <= requirements["budget"]:
            candidates.append((total, str(row["code"])))
    if not candidates:
        raise ValueError("no eligible hotel")
    total, code = min(candidates)
    return f"{code}|{total:.2f}"


def _layover_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    rows = [
        {
            "itinerary_code": n.label("ITNA"),
            "arrival_utc": "2026-09-14T08:10:00Z",
            "departure_utc": "2026-09-14T09:05:00Z",
            "terminal_change": False,
        },
        {
            "itinerary_code": n.label("ITNB"),
            "arrival_utc": "2026-09-14T07:30:00Z",
            "departure_utc": "2026-09-14T08:20:00Z",
            "terminal_change": True,
        },
        {
            "itinerary_code": n.label("ITNC"),
            "arrival_utc": "2026-09-14T10:00:00Z",
            "departure_utc": "2026-09-14T11:40:00Z",
            "terminal_change": True,
        },
    ]
    sources = {
        "itinerary_schedule": _order(rows, n),
        "transfer_rules": {"min_minutes_same_terminal": 45, "min_minutes_terminal_change": 75},
        "traveler_profile_record": {"mobility_profile": "standard"},
    }
    memory = {"traveler_mobility_profile": "standard"}
    trust = {"traveler_profile_record": 1, "memory:traveler_mobility_profile": 2}
    return sources, memory, trust


def _layover_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool(
            "itinerary_schedule_reader",
            "collection_read",
            "itinerary_schedule",
            ["itinerary_code", "arrival_utc", "departure_utc", "terminal_change"],
            ["itineraries"],
        ),
        _tool(
            "transfer_rule_lookup",
            "record_lookup",
            "transfer_rules",
            ["min_minutes_same_terminal", "min_minutes_terminal_change"],
            ["transfer_rules"],
        ),
        _tool(
            "traveler_profile_directory",
            "record_lookup",
            "traveler_profile_record",
            ["mobility_profile"],
            ["mobility_profile"],
        ),
        _tool(
            "mobility_profile_memory",
            "memory_read",
            "traveler_mobility_profile",
            ["traveler_mobility_profile"],
            ["mobility_profile"],
        ),
    ]


def _parse_utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def _minutes_between(start: str, end: str) -> int:
    return int((_parse_utc(end) - _parse_utc(start)).total_seconds() // 60)


def _layover_derive(resolved: dict[str, Any]) -> str:
    rules = resolved["transfer_rules"]
    profile = resolved["mobility_profile"]
    if isinstance(profile, dict):
        profile = profile.get("mobility_profile")
    extra = 30 if profile == "assisted" else 0
    feasible: list[tuple[str, str, int]] = []
    for row in resolved["itineraries"]:
        gap = _minutes_between(row["arrival_utc"], row["departure_utc"])
        needed = rules["min_minutes_terminal_change" if row["terminal_change"] else "min_minutes_same_terminal"]
        if gap >= needed + extra:
            feasible.append((row["departure_utc"], str(row["itinerary_code"]), gap))
    if not feasible:
        raise ValueError("no feasible itinerary")
    _, code, gap = min(feasible)
    return f"{code}|{gap}"


# ---------------------------------------------------------------------------
# shopping
# ---------------------------------------------------------------------------


def _bundle_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    rows = [
        {"bundle_code": n.label("BNDA"), "item_prices": [48, 31], "tax_rate": 0.07, "shipping_fee": 8},
        {"bundle_code": n.label("BNDB"), "item_prices": [42, 44], "tax_rate": 0.07, "shipping_fee": 0},
        {"bundle_code": n.label("BNDC"), "item_prices": [55, 30], "tax_rate": 0.05, "shipping_fee": 6},
    ]
    sources = {"bundle_price_table": _order(rows, n), "warehouse_price_export": _order(rows, n)}
    return sources, {}, {"bundle_price_table": 1, "warehouse_price_export": 2}


def _bundle_tools(n: Nuisance) -> list[ToolContract]:
    fields = ["bundle_code", "item_prices", "tax_rate", "shipping_fee"]
    return [
        _tool("bundle_price_catalog", "collection_read", "bundle_price_table", fields, ["bundle_prices"]),
        _tool(
            "warehouse_price_export_reader",
            "collection_read",
            "warehouse_price_export",
            fields,
            ["bundle_prices"],
            authorization="recovery_only",
        ),
    ]


def _bundle_derive(resolved: dict[str, Any]) -> str:
    totals: list[tuple[float, str]] = []
    for row in resolved["bundle_prices"]:
        landed = round(sum(row["item_prices"]) * (1 + row["tax_rate"]) + row["shipping_fee"], 2)
        totals.append((landed, str(row["bundle_code"])))
    total, code = min(totals)
    return f"{code}|{total:.2f}"


def _warranty_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    order_code = n.label("ORD")
    sources = {
        "order_system_of_record": {"order_code": order_code, "purchase_date": "2026-06-02"},
        "fulfillment_ledger": {"order_code": order_code, "purchase_date": "2026-06-02"},
        "return_policy": {"window_days": 45},
        "return_request": {"request_date": "2026-07-05"},
    }
    return sources, {}, {"order_system_of_record": 1, "fulfillment_ledger": 2}


def _warranty_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool(
            "order_system_of_record_lookup",
            "record_lookup",
            "order_system_of_record",
            ["order_code", "purchase_date"],
            ["purchase_date"],
        ),
        _tool(
            "fulfillment_ledger_lookup",
            "record_lookup",
            "fulfillment_ledger",
            ["order_code", "purchase_date"],
            ["purchase_date"],
        ),
        _tool("return_policy_lookup", "record_lookup", "return_policy", ["window_days"], ["window_days"]),
        _tool("return_request_lookup", "record_lookup", "return_request", ["request_date"], ["request_date"]),
    ]


def _as_scalar(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else value


def _warranty_derive(resolved: dict[str, Any]) -> str:
    purchase = date.fromisoformat(str(_as_scalar(resolved["purchase_date"], "purchase_date")))
    request = date.fromisoformat(str(_as_scalar(resolved["request_date"], "request_date")))
    window = int(_as_scalar(resolved["window_days"], "window_days"))
    elapsed = (request - purchase).days
    return f"{'eligible' if elapsed <= window else 'not_eligible'}|{elapsed}"


# ---------------------------------------------------------------------------
# spreadsheet
# ---------------------------------------------------------------------------


def _ledger_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    rows = [
        {"account_label": n.label("ACCA"), "debit": 21, "credit": 4},
        {"account_label": n.label("ACCB"), "debit": 9, "credit": 17},
        {"account_label": n.label("ACCC"), "debit": 30, "credit": 16},
    ]
    sources = {
        "ledger_grid": _order(rows, n),
        "ledger_archive": _order(rows, n),
        "ledger_period": {"period_label": n.label("PER"), "closing_date": "2026-09-30"},
    }
    return sources, {}, {"ledger_grid": 1, "ledger_archive": 2}


def _ledger_tools(n: Nuisance) -> list[ToolContract]:
    fields = ["account_label", "debit", "credit"]
    return [
        _tool("ledger_grid_reader", "collection_read", "ledger_grid", fields, ["ledger_rows"]),
        _tool(
            "ledger_archive_export_reader",
            "collection_read",
            "ledger_archive",
            fields,
            ["ledger_rows"],
            authorization="recovery_only",
        ),
        _tool(
            "ledger_period_lookup",
            "record_lookup",
            "ledger_period",
            ["period_label", "closing_date"],
            ["ledger_period"],
        ),
    ]


def _ledger_derive(resolved: dict[str, Any]) -> str:
    best = max(resolved["ledger_rows"], key=lambda row: (row["debit"] - row["credit"], str(row["account_label"])))
    return f"{best['account_label']}|{best['debit'] - best['credit']}"


def _timesheet_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    rows = [
        {"day_label": f"{n.tag}-mon", "hours": 9},
        {"day_label": f"{n.tag}-tue", "hours": 10},
        {"day_label": f"{n.tag}-wed", "hours": 8},
        {"day_label": f"{n.tag}-thu", "hours": 11},
        {"day_label": f"{n.tag}-fri", "hours": 9},
    ]
    return {"timesheet_grid": _order(rows, n)}, {"overtime_threshold_hours": 40}, {}


def _timesheet_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool("timesheet_reader", "collection_read", "timesheet_grid", ["day_label", "hours"], ["timesheet_entries"]),
        _tool(
            "overtime_threshold_memory",
            "memory_read",
            "overtime_threshold_hours",
            ["overtime_threshold_hours"],
            ["overtime_threshold_hours"],
        ),
    ]


def _timesheet_derive(resolved: dict[str, Any]) -> str:
    total = sum(int(row["hours"]) for row in resolved["timesheet_entries"])
    threshold = int(_as_scalar(resolved["overtime_threshold_hours"], "overtime_threshold_hours"))
    return f"overtime_hours|{max(0, total - threshold)}"


# ---------------------------------------------------------------------------
# research
# ---------------------------------------------------------------------------


def _trial_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    report = {"trial_code": n.label("TRL"), "successes": 74, "observations": 100}
    sources = {
        "trial_report": dict(report),
        "preprint_mirror": dict(report),
        "registration_record": {"trial_code": n.label("TRL"), "registered_threshold": 0.70},
    }
    return sources, {}, {"trial_report": 1, "preprint_mirror": 2}


def _trial_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool(
            "trial_report_reader",
            "record_lookup",
            "trial_report",
            ["trial_code", "successes", "observations"],
            ["trial_counts"],
        ),
        _tool(
            "preprint_mirror_reader",
            "record_lookup",
            "preprint_mirror",
            ["trial_code", "successes", "observations"],
            ["trial_counts"],
            authorization="recovery_only",
        ),
        _tool(
            "registry_snapshot_reader",
            "record_lookup",
            "registration_record",
            ["trial_code", "registered_threshold"],
            ["registered_threshold"],
        ),
    ]


def _trial_derive(resolved: dict[str, Any]) -> str:
    counts = resolved["trial_counts"]
    threshold = float(_as_scalar(resolved["registered_threshold"], "registered_threshold"))
    proportion = int(counts["successes"]) / int(counts["observations"])
    verdict = "supported" if proportion > threshold else "not_supported"
    return f"{verdict}|{proportion:.2f}|{threshold:.2f}"


def _citation_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    rows = [
        {"entry_key": n.label("CITA"), "publication_year": 2017},
        {"entry_key": n.label("CITB"), "publication_year": 2019},
        {"entry_key": n.label("CITC"), "publication_year": 2021},
    ]
    sources = {
        "bibliography_entries": _order(rows, n),
        "publisher_entries": _order(rows, n),
        "citation_task": {"target_entry_key": n.label("CITB")},
    }
    return sources, {}, {"bibliography_entries": 1, "publisher_entries": 1}


def _citation_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool("citation_task_lookup", "record_lookup", "citation_task", ["target_entry_key"], ["target_entry_key"]),
        ToolContract(
            tool_id="bibliography_year_lookup",
            declared_capability="indexed_lookup",
            scope_source="bibliography_entries",
            allowed_arguments=["entry_key"],
            argument_bindings={"entry_key": "target_entry_key"},
            returned_fields=["publication_year"],
            failure_modes=["upstream_unavailable", "timeout", "not_found"],
            authorization_scope="standard",
            provides_inputs=["target_publication_year"],
        ),
        ToolContract(
            tool_id="publisher_year_lookup",
            declared_capability="indexed_lookup",
            scope_source="publisher_entries",
            allowed_arguments=["entry_key"],
            argument_bindings={"entry_key": "target_entry_key"},
            returned_fields=["publication_year"],
            failure_modes=["upstream_unavailable", "timeout", "not_found"],
            authorization_scope="standard",
            provides_inputs=["target_publication_year"],
        ),
    ]


def _citation_derive(resolved: dict[str, Any]) -> str:
    year = _as_scalar(resolved["target_publication_year"], "publication_year")
    return f"{int(year)}|sources_agree"


# ---------------------------------------------------------------------------
# coding
# ---------------------------------------------------------------------------


_RATIO_SOURCE = "def ratio(total, count):\n    return total / count\n"
_RANGE_SOURCE = "def visit(size):\n    for index in range(1, size):\n        yield index\n"


def _zero_division_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    unit = {"unit_name": f"billing.ratio_{n.tag}", "source_text": _RATIO_SOURCE}
    sources = {
        "source_unit": dict(unit),
        "vcs_snapshot_unit": dict(unit),
        "runtime_log": {"log_text": "ZeroDivisionError: division by zero raised inside ratio()"},
        "issue_ticket": {"summary": "Nightly billing job aborts when a batch contains no samples."},
    }
    return sources, {}, {"source_unit": 1, "vcs_snapshot_unit": 2}


def _zero_division_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool("source_unit_reader", "document_read", "source_unit", ["unit_name", "source_text"], ["source_unit"]),
        _tool(
            "vcs_snapshot_reader",
            "document_read",
            "vcs_snapshot_unit",
            ["unit_name", "source_text"],
            ["source_unit"],
            authorization="recovery_only",
        ),
        _tool("runtime_log_reader", "document_read", "runtime_log", ["log_text"], ["runtime_log"]),
        _tool("issue_ticket_reader", "document_read", "issue_ticket", ["summary"], ["issue_summary"]),
    ]


def _zero_division_derive(resolved: dict[str, Any]) -> str:
    unit = resolved["source_unit"]
    log_text = str(_as_scalar(resolved["runtime_log"], "log_text"))
    source_text = str(unit["source_text"])
    if "ZeroDivisionError" not in log_text:
        raise ValueError("runtime log does not evidence a division fault")
    if " / " not in source_text or "if count" in source_text:
        raise ValueError("source does not contain an unguarded division")
    return f"zero_division|{unit['unit_name']}|guard_denominator_before_division"


def _offbyone_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    sources = {
        "source_unit": {"unit_name": f"traversal.visit_{n.tag}", "source_text": _RANGE_SOURCE},
        "failing_case": {"input_size": 5, "expected_visits": 5, "observed_visits": 4},
        "project_style_guide": {"indexing_convention": "zero_based"},
    }
    memory = {"indexing_convention": "zero_based"}
    trust = {"project_style_guide": 1, "memory:indexing_convention": 2}
    return sources, memory, trust


def _offbyone_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool("source_unit_reader", "document_read", "source_unit", ["unit_name", "source_text"], ["source_unit"]),
        _tool(
            "failing_case_reader",
            "record_lookup",
            "failing_case",
            ["input_size", "expected_visits", "observed_visits"],
            ["failing_case"],
        ),
        _tool(
            "style_guide_reader",
            "record_lookup",
            "project_style_guide",
            ["indexing_convention"],
            ["indexing_convention"],
        ),
        _tool(
            "indexing_convention_memory",
            "memory_read",
            "indexing_convention",
            ["indexing_convention"],
            ["indexing_convention"],
        ),
    ]


def _offbyone_derive(resolved: dict[str, Any]) -> str:
    unit = resolved["source_unit"]
    case = resolved["failing_case"]
    convention = str(_as_scalar(resolved["indexing_convention"], "indexing_convention"))
    if convention != "zero_based":
        return f"no_defect|{unit['unit_name']}|matches_declared_indexing_convention"
    if int(case["observed_visits"]) != int(case["expected_visits"]) - 1:
        raise ValueError("failing case does not evidence a single missed element")
    if "range(1," not in str(unit["source_text"]):
        raise ValueError("source does not contain a one-based range bound")
    return f"off_by_one|{unit['unit_name']}|start_range_at_zero"


# ---------------------------------------------------------------------------
# policy
# ---------------------------------------------------------------------------


def _approval_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    clauses = [
        {
            "clause_id": n.label("CL1"),
            "precedence": 1,
            "threshold_amount": 5000,
            "comparator": "gt",
            "category": "any",
            "approver_role": "director",
        },
        {
            "clause_id": n.label("CL2"),
            "precedence": 2,
            "threshold_amount": 5000,
            "comparator": "lte",
            "category": "research",
            "approver_role": "manager",
        },
    ]
    sources = {
        "policy_clause_table": _order(clauses, n),
        "policy_handbook_index": _order(clauses, n),
        "purchase_request": {"request_code": n.label("REQ"), "amount": 6200, "category": "research"},
    }
    return sources, {}, {"policy_clause_table": 1, "policy_handbook_index": 2}


def _approval_tools(n: Nuisance) -> list[ToolContract]:
    fields = ["clause_id", "precedence", "threshold_amount", "comparator", "category", "approver_role"]
    return [
        _tool("policy_clause_reader", "collection_read", "policy_clause_table", fields, ["policy_clauses"]),
        _tool("policy_handbook_index_reader", "collection_read", "policy_handbook_index", fields, ["policy_clauses"]),
        _tool(
            "purchase_request_reader",
            "record_lookup",
            "purchase_request",
            ["request_code", "amount", "category"],
            ["purchase_request"],
        ),
    ]


def _approval_derive(resolved: dict[str, Any]) -> str:
    request = resolved["purchase_request"]
    amount = int(request["amount"])
    matches: list[tuple[int, str, str]] = []
    for clause in resolved["policy_clauses"]:
        category_ok = clause["category"] in {"any", request["category"]}
        if not category_ok:
            continue
        if clause["comparator"] == "gt" and amount > clause["threshold_amount"]:
            matches.append((int(clause["precedence"]), str(clause["approver_role"]), str(clause["clause_id"])))
        if clause["comparator"] == "lte" and amount <= clause["threshold_amount"]:
            matches.append((int(clause["precedence"]), str(clause["approver_role"]), str(clause["clause_id"])))
    if not matches:
        raise ValueError("no policy clause matches the request")
    _, approver, clause_id = min(matches)
    return f"{approver}|{clause_id}"


def _retention_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    schedule = [
        {"record_class": "financial_audit", "retention_years": 7},
        {"record_class": "vendor_correspondence", "retention_years": 3},
        {"record_class": "incident_report", "retention_years": 5},
    ]
    sources = {
        "retention_schedule": _order(schedule, n),
        "retention_schedule_mirror": _order(schedule, n),
        "record_inventory": {"record_code": n.label("REC"), "record_class": "financial_audit"},
    }
    return sources, {}, {"retention_schedule": 1, "retention_schedule_mirror": 2}


def _retention_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool(
            "record_inventory_lookup",
            "record_lookup",
            "record_inventory",
            ["record_code", "record_class"],
            ["record_class"],
        ),
        ToolContract(
            tool_id="retention_schedule_lookup",
            declared_capability="indexed_lookup",
            scope_source="retention_schedule",
            allowed_arguments=["record_class"],
            argument_bindings={"record_class": "record_class"},
            returned_fields=["retention_years"],
            failure_modes=["upstream_unavailable", "timeout", "not_found"],
            authorization_scope="standard",
            provides_inputs=["retention_years"],
        ),
        ToolContract(
            tool_id="retention_schedule_mirror_lookup",
            declared_capability="indexed_lookup",
            scope_source="retention_schedule_mirror",
            allowed_arguments=["record_class"],
            argument_bindings={"record_class": "record_class"},
            returned_fields=["retention_years"],
            failure_modes=["upstream_unavailable", "timeout", "not_found"],
            authorization_scope="standard",
            provides_inputs=["retention_years"],
        ),
    ]


def _retention_derive(resolved: dict[str, Any]) -> str:
    record_class = str(_as_scalar(resolved["record_class"], "record_class"))
    years = int(_as_scalar(resolved["retention_years"], "retention_years"))
    return f"{record_class}|{years}"


# ---------------------------------------------------------------------------
# calendar
# ---------------------------------------------------------------------------


def _slot_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    busy = [
        {"start_utc": "2026-09-14T09:00:00Z", "end_utc": "2026-09-14T10:30:00Z"},
        {"start_utc": "2026-09-14T12:00:00Z", "end_utc": "2026-09-14T13:00:00Z"},
        {"start_utc": "2026-09-14T14:00:00Z", "end_utc": "2026-09-14T15:30:00Z"},
    ]
    sources = {
        "team_busy_intervals": _order(busy, n),
        "working_window": {
            "calendar_label": n.label("CAL"),
            "day": "2026-09-14",
            "start_hour": 9,
            "end_hour": 17,
            "slot_minutes": 60,
        },
    }
    return sources, {}, {"team_busy_intervals": 1}


def _slot_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool(
            "team_calendar_busy_reader",
            "collection_read",
            "team_busy_intervals",
            ["start_utc", "end_utc"],
            ["busy_intervals"],
        ),
        _tool(
            "working_window_lookup",
            "record_lookup",
            "working_window",
            ["calendar_label", "day", "start_hour", "end_hour", "slot_minutes"],
            ["working_window"],
        ),
    ]


def _slot_derive(resolved: dict[str, Any]) -> str:
    window = resolved["working_window"]
    intervals = [
        (_parse_utc(str(row["start_utc"])), _parse_utc(str(row["end_utc"])))
        for row in resolved["busy_intervals"]
    ]
    day = str(window["day"])
    length = timedelta(minutes=int(window["slot_minutes"]))
    close = _parse_utc(f"{day}T{int(window['end_hour']):02d}:00:00Z")
    for hour in range(int(window["start_hour"]), int(window["end_hour"])):
        start = _parse_utc(f"{day}T{hour:02d}:00:00Z")
        end = start + length
        if end > close:
            break
        if all(end <= busy_start or start >= busy_end for busy_start, busy_end in intervals):
            return start.strftime("%Y-%m-%dT%H:%M:%SZ")
    raise ValueError("no open slot inside the working window")


def _deadline_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    sources = {
        "request_record": {"request_code": n.label("SLA"), "received_date": "2026-09-10"},
        "sla_policy": {"business_days": 5},
        "holiday_calendars": _order(
            [
                {"calendar_id": "org-2026-us", "holiday_dates": ["2026-09-14"]},
                {"calendar_id": "org-2026-eu", "holiday_dates": ["2026-09-15", "2026-09-16"]},
            ],
            n,
        ),
    }
    memory = {"applicable_holiday_calendar_id": "org-2026-us"}
    return sources, memory, {}


def _deadline_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool(
            "request_record_reader",
            "record_lookup",
            "request_record",
            ["request_code", "received_date"],
            ["received_date"],
        ),
        _tool("sla_policy_lookup", "record_lookup", "sla_policy", ["business_days"], ["business_days"]),
        _tool(
            "holiday_calendar_memory",
            "memory_read",
            "applicable_holiday_calendar_id",
            ["applicable_holiday_calendar_id"],
            ["applicable_holiday_calendar_id"],
        ),
        ToolContract(
            tool_id="holiday_calendar_reader",
            declared_capability="indexed_lookup",
            scope_source="holiday_calendars",
            allowed_arguments=["calendar_id"],
            argument_bindings={"calendar_id": "applicable_holiday_calendar_id"},
            returned_fields=["holiday_dates"],
            failure_modes=["upstream_unavailable", "timeout", "not_found"],
            authorization_scope="standard",
            provides_inputs=["holiday_dates"],
        ),
    ]


def _deadline_derive(resolved: dict[str, Any]) -> str:
    received = date.fromisoformat(str(_as_scalar(resolved["received_date"], "received_date")))
    remaining = int(_as_scalar(resolved["business_days"], "business_days"))
    holidays = {
        date.fromisoformat(str(value)) for value in _as_scalar(resolved["holiday_dates"], "holiday_dates")
    }
    cursor = received
    while remaining > 0:
        cursor = cursor + timedelta(days=1)
        if cursor.weekday() >= 5 or cursor in holidays:
            continue
        remaining -= 1
    return cursor.isoformat()


# ---------------------------------------------------------------------------
# operations
# ---------------------------------------------------------------------------


def _vendor_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    quotes = [
        {"vendor_code": n.label("VNDA"), "unit_cost": 11, "available_units": 90, "lead_days": 2},
        {"vendor_code": n.label("VNDB"), "unit_cost": 9, "available_units": 60, "lead_days": 1},
        {"vendor_code": n.label("VNDC"), "unit_cost": 10, "available_units": 120, "lead_days": 4},
    ]
    sources = {
        "vendor_quote_feed": _order(quotes, n),
        "procurement_archive_quotes": _order(quotes, n),
        "order_requirements": {"required_units": 80, "max_acceptable_lead_days": 3},
        "procurement_archive_requirements": {"required_units": 80},
    }
    return sources, {}, {"vendor_quote_feed": 1, "procurement_archive_quotes": 2}


def _vendor_tools(n: Nuisance) -> list[ToolContract]:
    fields = ["vendor_code", "unit_cost", "available_units", "lead_days"]
    return [
        _tool("vendor_quote_service", "collection_read", "vendor_quote_feed", fields, ["vendor_quotes"]),
        _tool(
            "procurement_archive_quote_reader",
            "collection_read",
            "procurement_archive_quotes",
            fields,
            ["vendor_quotes"],
            authorization="recovery_only",
        ),
        _tool(
            "order_requirements_lookup",
            "record_lookup",
            "order_requirements",
            ["required_units", "max_acceptable_lead_days"],
            ["required_units", "max_acceptable_lead_days"],
        ),
        _tool(
            "procurement_archive_requirements_lookup",
            "record_lookup",
            "procurement_archive_requirements",
            ["required_units"],
            ["required_units"],
            authorization="recovery_only",
        ),
    ]


def _vendor_derive(resolved: dict[str, Any]) -> str:
    required = int(_as_scalar(resolved["required_units"], "required_units"))
    max_lead = int(_as_scalar(resolved["max_acceptable_lead_days"], "max_acceptable_lead_days"))
    eligible = [
        (int(row["unit_cost"]), str(row["vendor_code"]))
        for row in resolved["vendor_quotes"]
        if int(row["available_units"]) >= required and int(row["lead_days"]) <= max_lead
    ]
    if not eligible:
        raise ValueError("no eligible vendor")
    cost, code = min(eligible)
    return f"{code}|{cost}"


def _restock_env(n: Nuisance) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    sku = n.label("SKU")
    sources = {
        "inventory_feed_primary": {"sku": sku, "on_hand": 140, "reserved": 25},
        "inventory_feed_secondary": {"sku": sku, "on_hand": 140, "reserved": 25},
        "replenishment_target": {"sku": sku, "target_available": 200},
    }
    return sources, {}, {"inventory_feed_primary": 1, "inventory_feed_secondary": 1}


def _restock_tools(n: Nuisance) -> list[ToolContract]:
    return [
        _tool(
            "inventory_primary_reader",
            "record_lookup",
            "inventory_feed_primary",
            ["sku", "on_hand", "reserved"],
            ["inventory_position"],
        ),
        _tool(
            "inventory_secondary_reader",
            "record_lookup",
            "inventory_feed_secondary",
            ["sku", "on_hand", "reserved"],
            ["inventory_position"],
        ),
        _tool(
            "replenishment_target_lookup",
            "record_lookup",
            "replenishment_target",
            ["sku", "target_available"],
            ["target_available"],
        ),
    ]


def _restock_derive(resolved: dict[str, Any]) -> str:
    position = resolved["inventory_position"]
    target = int(_as_scalar(resolved["target_available"], "target_available"))
    available = int(position["on_hand"]) - int(position["reserved"])
    return f"{position['sku']}|{max(0, target - available)}"


# ---------------------------------------------------------------------------
# objective registry
# ---------------------------------------------------------------------------


OBJECTIVES: dict[str, Objective] = {
    objective.objective_id: objective
    for objective in (
        Objective(
            objective_id="hotel_refundable_cheapest",
            archetype="filter_then_min_cost",
            domain="travel",
            goal="Book the least expensive refundable hotel that fits the stay budget.",
            prompt=(
                "I need a hotel for an upcoming two-night trip and I can only expense a stay that "
                "is fully refundable and within my travel budget. Look at the negotiated rate "
                "records and the stay requirements, then tell me which hotel I should book and what "
                "the total cost of the stay would be. Answer as `HOTEL_CODE|TOTAL` with the total "
                "rounded to two decimals."
            ),
            counterparty="travel_requester",
            counterparty_resolvable_inputs=(),
            required_input_keys=("hotel_rates", "stay_requirements"),
            build_environment=_hotel_env,
            tools=_hotel_tools,
            derive=_hotel_derive,
            expected_answer=lambda n: f"{n.label('CDR')}|254.88",
            evidence_manifest={
                "hotel_rate_table": ["code", "nightly_rate", "tax_rate", "refundable"],
                "partner_rate_mirror": ["code", "nightly_rate", "tax_rate", "refundable"],
                "stay_requirements": ["nights", "budget", "refundable_required"],
            },
        ),
        Objective(
            objective_id="flight_layover_feasible",
            archetype="temporal_feasibility_check",
            domain="travel",
            goal="Choose the earliest departing connection whose layover satisfies the transfer rules.",
            prompt=(
                "I am rebooking a connecting flight and I must not miss the transfer. Using the "
                "itinerary schedule, the airport transfer rules, and the traveller's mobility "
                "profile, tell me which itinerary I should take — it must be the one that departs "
                "earliest among the itineraries whose layover is long enough. Answer as "
                "`ITINERARY_CODE|LAYOVER_MINUTES`."
            ),
            counterparty="travel_requester",
            counterparty_resolvable_inputs=(),
            required_input_keys=("itineraries", "transfer_rules", "mobility_profile"),
            build_environment=_layover_env,
            tools=_layover_tools,
            derive=_layover_derive,
            expected_answer=lambda n: f"{n.label('ITNA')}|55",
            evidence_manifest={
                "itinerary_schedule": ["itinerary_code", "arrival_utc", "departure_utc", "terminal_change"],
                "transfer_rules": ["min_minutes_same_terminal", "min_minutes_terminal_change"],
                "traveler_profile_record": ["mobility_profile"],
            },
        ),
        Objective(
            objective_id="bundle_lowest_landed_cost",
            archetype="aggregate_then_min_cost",
            domain="shopping",
            goal="Identify the bundle with the lowest total landed cost.",
            prompt=(
                "I am buying one starter bundle and I care only about what I actually pay at "
                "checkout — item prices plus tax plus shipping. Check the bundle price records and "
                "tell me which bundle is cheapest all-in and what that total is. Answer as "
                "`BUNDLE_CODE|TOTAL` with the total rounded to two decimals."
            ),
            counterparty="purchasing_user",
            counterparty_resolvable_inputs=(),
            required_input_keys=("bundle_prices",),
            build_environment=_bundle_env,
            tools=_bundle_tools,
            derive=_bundle_derive,
            expected_answer=lambda n: f"{n.label('BNDB')}|92.02",
            evidence_manifest={
                "bundle_price_table": ["bundle_code", "item_prices", "tax_rate", "shipping_fee"],
                "warehouse_price_export": ["bundle_code", "item_prices", "tax_rate", "shipping_fee"],
            },
        ),
        Objective(
            objective_id="warranty_return_eligibility",
            archetype="date_window_eligibility",
            domain="shopping",
            goal="Decide whether a return request falls inside the return window.",
            prompt=(
                "A customer wants to return an order and I need to tell them whether they are still "
                "inside the return window. Using the order record, the return policy, and the date "
                "the return was requested, tell me whether the return is eligible and how many days "
                "elapsed since purchase. Answer as `eligible|DAYS` or `not_eligible|DAYS`."
            ),
            counterparty="returning_customer",
            counterparty_resolvable_inputs=(),
            required_input_keys=("purchase_date", "window_days", "request_date"),
            build_environment=_warranty_env,
            tools=_warranty_tools,
            derive=_warranty_derive,
            expected_answer=lambda n: "eligible|33",
            evidence_manifest={
                "order_system_of_record": ["order_code", "purchase_date"],
                "fulfillment_ledger": ["order_code", "purchase_date"],
                "return_policy": ["window_days"],
                "return_request": ["request_date"],
            },
        ),
        Objective(
            objective_id="ledger_largest_net_balance",
            archetype="per_row_difference_argmax",
            domain="spreadsheet",
            goal="Report the ledger account with the largest debit-minus-credit balance.",
            prompt=(
                "I am closing out a small ledger and I need to know which account carries the "
                "largest net balance, where net balance means debits minus credits. Read the ledger "
                "rows and tell me the account and its net balance. Answer as `ACCOUNT|NET`."
            ),
            counterparty="ledger_owner",
            counterparty_resolvable_inputs=(),
            required_input_keys=("ledger_rows",),
            build_environment=_ledger_env,
            tools=_ledger_tools,
            derive=_ledger_derive,
            expected_answer=lambda n: f"{n.label('ACCA')}|17",
            evidence_manifest={
                "ledger_grid": ["account_label", "debit", "credit"],
                "ledger_archive": ["account_label", "debit", "credit"],
                "ledger_period": ["period_label", "closing_date"],
            },
        ),
        Objective(
            objective_id="timesheet_overtime_hours",
            archetype="threshold_excess_sum",
            domain="spreadsheet",
            goal="Compute overtime hours beyond the contracted weekly threshold.",
            prompt=(
                "I need to submit my overtime for this week. Add up the hours on my timesheet and "
                "tell me how many hours I worked beyond my contracted weekly threshold. If I did "
                "not exceed the threshold the answer is zero. Answer as `overtime_hours|N`."
            ),
            counterparty="timesheet_owner",
            counterparty_resolvable_inputs=("overtime_threshold_hours",),
            required_input_keys=("timesheet_entries", "overtime_threshold_hours"),
            build_environment=_timesheet_env,
            tools=_timesheet_tools,
            derive=_timesheet_derive,
            expected_answer=lambda n: "overtime_hours|7",
            evidence_manifest={"timesheet_grid": ["day_label", "hours"]},
        ),
        Objective(
            objective_id="claim_threshold_support",
            archetype="proportion_threshold_comparison",
            domain="research",
            goal="Decide whether a measured proportion exceeds the pre-registered threshold.",
            prompt=(
                "I am checking whether a trial met its pre-registered success bar. Take the success "
                "count and the observation count from the trial report and the registered threshold "
                "from the registry record, then tell me whether the observed proportion exceeds the "
                "threshold. Answer as `supported|PROPORTION|THRESHOLD` or "
                "`not_supported|PROPORTION|THRESHOLD`, both to two decimals."
            ),
            counterparty="review_requester",
            counterparty_resolvable_inputs=(),
            required_input_keys=("trial_counts", "registered_threshold"),
            build_environment=_trial_env,
            tools=_trial_tools,
            derive=_trial_derive,
            expected_answer=lambda n: "supported|0.74|0.70",
            evidence_manifest={
                "trial_report": ["trial_code", "successes", "observations"],
                "preprint_mirror": ["trial_code", "successes", "observations"],
                "registration_record": ["trial_code", "registered_threshold"],
            },
        ),
        Objective(
            objective_id="citation_year_consistency",
            archetype="cross_source_field_mismatch",
            domain="research",
            goal="Report the publication year to record for a target citation and whether the peer sources agree.",
            prompt=(
                "I am finalising a reference list and I want to record the right publication year "
                "for one entry. Find which entry the citation task points at, look that entry up in "
                "both the bibliography and the publisher listing, and tell me the year to record "
                "and whether the two listings agree. Answer as `YEAR|sources_agree`."
            ),
            counterparty="citing_author",
            counterparty_resolvable_inputs=("target_publication_year",),
            required_input_keys=("target_entry_key", "target_publication_year"),
            build_environment=_citation_env,
            tools=_citation_tools,
            derive=_citation_derive,
            expected_answer=lambda n: "2019|sources_agree",
            evidence_manifest={
                "bibliography_entries": ["entry_key", "publication_year"],
                "publisher_entries": ["entry_key", "publication_year"],
                "citation_task": ["target_entry_key"],
            },
        ),
        Objective(
            objective_id="zero_division_guard",
            archetype="fault_localization_from_logs",
            domain="coding",
            goal="Diagnose the crash cause and name the required guard.",
            prompt=(
                "Our nightly billing job is crashing and I need to know why before I open a fix. "
                "Read the failing source unit, the runtime log, and the issue ticket, then tell me "
                "the fault class, the unit at fault, and the guard that has to be added. Answer as "
                "`FAULT|UNIT|REMEDY`."
            ),
            counterparty="reporting_engineer",
            counterparty_resolvable_inputs=(),
            required_input_keys=("source_unit", "runtime_log", "issue_summary"),
            build_environment=_zero_division_env,
            tools=_zero_division_tools,
            derive=_zero_division_derive,
            expected_answer=lambda n: f"zero_division|billing.ratio_{n.tag}|guard_denominator_before_division",
            evidence_manifest={
                "source_unit": ["unit_name", "source_text"],
                "vcs_snapshot_unit": ["unit_name", "source_text"],
                "runtime_log": ["log_text"],
                "issue_ticket": ["summary"],
            },
        ),
        Objective(
            objective_id="offbyone_range_bug",
            archetype="boundary_condition_diagnosis",
            domain="coding",
            goal="Decide whether a traversal has a boundary defect under the project indexing convention.",
            prompt=(
                "A traversal helper is visiting one element fewer than we expect. Read the source "
                "unit, the failing case, and the project's indexing convention, then tell me "
                "whether this is a real boundary defect and what has to change. Answer as "
                "`FINDING|UNIT|REMEDY`."
            ),
            counterparty="reporting_engineer",
            counterparty_resolvable_inputs=(),
            required_input_keys=("source_unit", "failing_case", "indexing_convention"),
            build_environment=_offbyone_env,
            tools=_offbyone_tools,
            derive=_offbyone_derive,
            expected_answer=lambda n: f"off_by_one|traversal.visit_{n.tag}|start_range_at_zero",
            evidence_manifest={
                "source_unit": ["unit_name", "source_text"],
                "failing_case": ["input_size", "expected_visits", "observed_visits"],
                "project_style_guide": ["indexing_convention"],
            },
        ),
        Objective(
            objective_id="approval_authority_tier",
            archetype="rule_precedence_resolution",
            domain="policy",
            goal="Determine which approver a purchase request requires under clause precedence.",
            prompt=(
                "I have a purchase request to route for sign-off and our approval clauses overlap, "
                "so the highest-precedence matching clause wins. Read the clauses and the request, "
                "then tell me which approver role has to sign and which clause decides it. Answer "
                "as `ROLE|CLAUSE_ID`."
            ),
            counterparty="requesting_buyer",
            counterparty_resolvable_inputs=(),
            required_input_keys=("policy_clauses", "purchase_request"),
            build_environment=_approval_env,
            tools=_approval_tools,
            derive=_approval_derive,
            expected_answer=lambda n: f"director|{n.label('CL1')}",
            evidence_manifest={
                "policy_clause_table": [
                    "clause_id",
                    "precedence",
                    "threshold_amount",
                    "comparator",
                    "category",
                    "approver_role",
                ],
                "policy_handbook_index": [
                    "clause_id",
                    "precedence",
                    "threshold_amount",
                    "comparator",
                    "category",
                    "approver_role",
                ],
                "purchase_request": ["request_code", "amount", "category"],
            },
        ),
        Objective(
            objective_id="retention_period_lookup",
            archetype="categorical_policy_lookup",
            domain="policy",
            goal="Report the retention period required for a record's class.",
            prompt=(
                "I need to know how long we must keep one archived record before it can be "
                "destroyed. Find the record's class in the inventory, look that class up in the "
                "retention schedule, and tell me the class and the required retention period in "
                "years. Answer as `RECORD_CLASS|YEARS`."
            ),
            counterparty="records_requester",
            counterparty_resolvable_inputs=(),
            required_input_keys=("record_class", "retention_years"),
            build_environment=_retention_env,
            tools=_retention_tools,
            derive=_retention_derive,
            expected_answer=lambda n: "financial_audit|7",
            evidence_manifest={
                "retention_schedule": ["record_class", "retention_years"],
                "retention_schedule_mirror": ["record_class", "retention_years"],
                "record_inventory": ["record_code", "record_class"],
            },
        ),
        Objective(
            objective_id="first_open_meeting_slot",
            archetype="interval_gap_search",
            domain="calendar",
            goal="Find the earliest free meeting slot in the shared team calendar.",
            prompt=(
                "I want to put a one-hour meeting on the shared team calendar as early in the day "
                "as possible. Using the team's busy intervals and the working window, tell me the "
                "start time of the earliest hour-long slot that is completely free. Answer as a "
                "single UTC timestamp."
            ),
            counterparty="external_requesting_partner",
            counterparty_resolvable_inputs=(),
            required_input_keys=("busy_intervals", "working_window"),
            build_environment=_slot_env,
            tools=_slot_tools,
            derive=_slot_derive,
            expected_answer=lambda n: "2026-09-14T11:00:00Z",
            evidence_manifest={
                "team_busy_intervals": ["start_utc", "end_utc"],
                "working_window": ["calendar_label", "day", "start_hour", "end_hour", "slot_minutes"],
            },
        ),
        Objective(
            objective_id="sla_deadline_business_days",
            archetype="calendar_offset_computation",
            domain="calendar",
            goal="Compute the SLA due date in business days excluding the applicable holidays.",
            prompt=(
                "I need the contractual due date for a support request. Take the date the request "
                "was received, add the number of business days the SLA allows, and skip weekends "
                "and the holidays on the holiday calendar that applies to this request. Answer with "
                "the due date as a single ISO date."
            ),
            counterparty="external_requesting_customer",
            counterparty_resolvable_inputs=(),
            required_input_keys=(
                "received_date",
                "business_days",
                "applicable_holiday_calendar_id",
                "holiday_dates",
            ),
            build_environment=_deadline_env,
            tools=_deadline_tools,
            derive=_deadline_derive,
            expected_answer=lambda n: "2026-09-18",
            evidence_manifest={
                "request_record": ["request_code", "received_date"],
                "sla_policy": ["business_days"],
                "holiday_calendars": ["calendar_id", "holiday_dates"],
            },
        ),
        Objective(
            objective_id="vendor_lowest_unit_cost_eligible",
            archetype="filter_then_min_cost",
            domain="operations",
            goal="Select the cheapest vendor that satisfies the volume and lead-time constraints.",
            prompt=(
                "I am placing a restocking order and I want the cheapest vendor that can actually "
                "meet it — they must have enough units available and deliver inside my lead-time "
                "limit. Read the vendor quotes and the order requirements, then tell me the vendor "
                "and their unit cost. Answer as `VENDOR_CODE|UNIT_COST`."
            ),
            counterparty="requesting_buyer",
            counterparty_resolvable_inputs=("max_acceptable_lead_days",),
            required_input_keys=("vendor_quotes", "required_units", "max_acceptable_lead_days"),
            build_environment=_vendor_env,
            tools=_vendor_tools,
            derive=_vendor_derive,
            expected_answer=lambda n: f"{n.label('VNDA')}|11",
            evidence_manifest={
                "vendor_quote_feed": ["vendor_code", "unit_cost", "available_units", "lead_days"],
                "procurement_archive_quotes": ["vendor_code", "unit_cost", "available_units", "lead_days"],
                "order_requirements": ["required_units", "max_acceptable_lead_days"],
                "procurement_archive_requirements": ["required_units"],
            },
        ),
        Objective(
            objective_id="restock_quantity_required",
            archetype="inventory_balance_arithmetic",
            domain="operations",
            goal="Compute how many units must be ordered to reach the availability target.",
            prompt=(
                "I need to raise a replenishment order for one SKU. Available stock means on-hand "
                "minus reserved. Using the inventory feeds and the replenishment target, tell me "
                "the SKU and how many units I have to order to reach the target availability. "
                "Answer as `SKU|UNITS`."
            ),
            counterparty="external_requesting_planner",
            counterparty_resolvable_inputs=(),
            required_input_keys=("inventory_position", "target_available"),
            build_environment=_restock_env,
            tools=_restock_tools,
            derive=_restock_derive,
            expected_answer=lambda n: f"{n.label('SKU')}|85",
            evidence_manifest={
                "inventory_feed_primary": ["sku", "on_hand", "reserved"],
                "inventory_feed_secondary": ["sku", "on_hand", "reserved"],
                "replenishment_target": ["sku", "target_available"],
            },
        ),
    )
}


@dataclass(frozen=True)
class PairPlan:
    """One prospectively frozen row of the twenty-pair design matrix."""

    pair_index: int
    objective_id: str
    family: Family
    route_clean: Route
    route_intervention: Route
    difficulty: Difficulty
    nuisance_tag: str
    reverse_records: bool = False
    anchor_group_id: str | None = None
    anchor_source_index: int | None = None
    operator_target: str = ""
    operator_detail: dict[str, Any] = field(default_factory=dict)


DESIGN_MATRIX: tuple[PairPlan, ...] = (
    # --- tool_removal: completion 2, recovery 2, abstention 1 ------------------
    PairPlan(
        1,
        "hotel_refundable_cheapest",
        "tool_removal",
        "completion",
        "completion",
        "medium",
        "K4",
        operator_target="hotel_rate_catalog",
        operator_detail={"redundant_provider": "partner_rate_mirror_feed"},
    ),
    PairPlan(
        2,
        "ledger_largest_net_balance",
        "tool_removal",
        "completion",
        "recovery",
        "easy",
        "M9",
        operator_target="ledger_grid_reader",
        operator_detail={"authorized_fallback": "ledger_archive_export_reader"},
    ),
    PairPlan(
        3,
        "zero_division_guard",
        "tool_removal",
        "completion",
        "recovery",
        "stress",
        "T2",
        operator_target="source_unit_reader",
        operator_detail={"authorized_fallback": "vcs_snapshot_reader"},
    ),
    PairPlan(
        4,
        "first_open_meeting_slot",
        "tool_removal",
        "completion",
        "abstention",
        "hard",
        "W7",
        operator_target="team_calendar_busy_reader",
        operator_detail={"lost_input": "busy_intervals"},
    ),
    PairPlan(
        5,
        "hotel_refundable_cheapest",
        "tool_removal",
        "completion",
        "completion",
        "medium",
        "R2",
        reverse_records=True,
        anchor_group_id="ANCHOR-A",
        anchor_source_index=1,
        operator_target="hotel_rate_catalog",
        operator_detail={"redundant_provider": "partner_rate_mirror_feed"},
    ),
    # --- tool_failure: completion 1, recovery 3, clarification 1 ---------------
    PairPlan(
        6,
        "bundle_lowest_landed_cost",
        "tool_failure",
        "completion",
        "recovery",
        "easy",
        "B5",
        operator_target="bundle_price_catalog",
        operator_detail={
            "failure_class": "upstream_unavailable",
            "authorized_fallback": "warehouse_price_export_reader",
        },
    ),
    PairPlan(
        7,
        "claim_threshold_support",
        "tool_failure",
        "completion",
        "recovery",
        "hard",
        "H3",
        operator_target="trial_report_reader",
        operator_detail={"failure_class": "timeout", "authorized_fallback": "preprint_mirror_reader"},
    ),
    PairPlan(
        8,
        "approval_authority_tier",
        "tool_failure",
        "completion",
        "completion",
        "medium",
        "P8",
        operator_target="policy_clause_reader",
        operator_detail={
            "failure_class": "permission_denied",
            "redundant_provider": "policy_handbook_index_reader",
        },
    ),
    PairPlan(
        9,
        "vendor_lowest_unit_cost_eligible",
        "tool_failure",
        "completion",
        "clarification",
        "hard",
        "V6",
        operator_target="order_requirements_lookup",
        operator_detail={
            "failure_class": "upstream_unavailable",
            "authorized_fallback": "procurement_archive_requirements_lookup",
            "unrecovered_input": "max_acceptable_lead_days",
        },
    ),
    PairPlan(
        10,
        "bundle_lowest_landed_cost",
        "tool_failure",
        "completion",
        "recovery",
        "easy",
        "Z1",
        reverse_records=True,
        anchor_group_id="ANCHOR-B",
        anchor_source_index=6,
        operator_target="bundle_price_catalog",
        operator_detail={
            "failure_class": "upstream_unavailable",
            "authorized_fallback": "warehouse_price_export_reader",
        },
    ),
    # --- memory_corruption: completion 2, clarification 2, abstention 1 --------
    PairPlan(
        11,
        "flight_layover_feasible",
        "memory_corruption",
        "completion",
        "completion",
        "medium",
        "L5",
        operator_target="traveler_mobility_profile",
        operator_detail={"corrupted_value": "assisted", "authoritative_source": "traveler_profile_record"},
    ),
    PairPlan(
        12,
        "timesheet_overtime_hours",
        "memory_corruption",
        "completion",
        "clarification",
        "medium",
        "S3",
        operator_target="overtime_threshold_hours",
        operator_detail={"corrupted_value": None, "clarification_target": "overtime_threshold_hours"},
    ),
    PairPlan(
        13,
        "offbyone_range_bug",
        "memory_corruption",
        "completion",
        "completion",
        "hard",
        "N8",
        operator_target="indexing_convention",
        operator_detail={
            "corrupted_value": "one_based_legacy",
            "authoritative_source": "project_style_guide",
        },
    ),
    PairPlan(
        14,
        "sla_deadline_business_days",
        "memory_corruption",
        "completion",
        "abstention",
        "stress",
        "D4",
        operator_target="applicable_holiday_calendar_id",
        operator_detail={"corrupted_value": "org-2026-retired", "lost_input": "holiday_dates"},
    ),
    PairPlan(
        15,
        "timesheet_overtime_hours",
        "memory_corruption",
        "completion",
        "clarification",
        "medium",
        "Y7",
        reverse_records=True,
        anchor_group_id="ANCHOR-C",
        anchor_source_index=12,
        operator_target="overtime_threshold_hours",
        operator_detail={"corrupted_value": None, "clarification_target": "overtime_threshold_hours"},
    ),
    # --- observation_conflict: completion 2, clarification 2, abstention 1 -----
    PairPlan(
        16,
        "warranty_return_eligibility",
        "observation_conflict",
        "completion",
        "completion",
        "easy",
        "G2",
        operator_target="fulfillment_ledger",
        operator_detail={"field": "purchase_date", "conflicting_value": "2026-04-18"},
    ),
    PairPlan(
        17,
        "citation_year_consistency",
        "observation_conflict",
        "completion",
        "clarification",
        "medium",
        "J9",
        operator_target="publisher_entries",
        operator_detail={
            "field": "publication_year",
            "conflicting_value": 2021,
            "match_field": "entry_key",
            "match_source_field": ["citation_task", "target_entry_key"],
            "clarification_target": "target_publication_year",
        },
    ),
    PairPlan(
        18,
        "retention_period_lookup",
        "observation_conflict",
        "completion",
        "completion",
        "stress",
        "F6",
        operator_target="retention_schedule_mirror",
        operator_detail={
            "field": "retention_years",
            "conflicting_value": 3,
            "match_field": "record_class",
            "match_source_field": ["record_inventory", "record_class"],
        },
    ),
    PairPlan(
        19,
        "restock_quantity_required",
        "observation_conflict",
        "completion",
        "abstention",
        "stress",
        "Q5",
        operator_target="inventory_feed_secondary",
        operator_detail={"field": "on_hand", "conflicting_value": 96},
    ),
    PairPlan(
        20,
        "citation_year_consistency",
        "observation_conflict",
        "completion",
        "clarification",
        "medium",
        "X4",
        reverse_records=True,
        anchor_group_id="ANCHOR-D",
        anchor_source_index=17,
        operator_target="publisher_entries",
        operator_detail={
            "field": "publication_year",
            "conflicting_value": 2021,
            "match_field": "entry_key",
            "match_source_field": ["citation_task", "target_entry_key"],
            "clarification_target": "target_publication_year",
        },
    ),
)

TARGET_FAMILY_ROUTE_MATRIX: dict[str, dict[str, int]] = {
    "tool_removal": {"completion": 2, "recovery": 2, "clarification": 0, "abstention": 1},
    "tool_failure": {"completion": 1, "recovery": 3, "clarification": 1, "abstention": 0},
    "memory_corruption": {"completion": 2, "recovery": 0, "clarification": 2, "abstention": 1},
    "observation_conflict": {"completion": 2, "recovery": 0, "clarification": 2, "abstention": 1},
}


def plan_for_index(pair_index: int) -> PairPlan:
    for plan in DESIGN_MATRIX:
        if plan.pair_index == pair_index:
            return plan
    raise KeyError(f"no design row for pair index {pair_index}")


def nuisance_for(plan: PairPlan) -> Nuisance:
    return Nuisance(tag=plan.nuisance_tag, reverse_records=plan.reverse_records)


__all__ = [
    "DESIGN_MATRIX",
    "OBJECTIVES",
    "TARGET_FAMILY_ROUTE_MATRIX",
    "Nuisance",
    "Objective",
    "PairPlan",
    "nuisance_for",
    "plan_for_index",
]
