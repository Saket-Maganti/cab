"""Primitive-evidence scanning: no artifact may carry a conclusion.

The scanner rejects answer-bearing field names, their common synonyms, pre-ranked
orderings, boolean conclusions, and any record that reproduces a private gold
string verbatim.  Identifier echoes — the answer naming a primitive identifier
that the agent must *select* from evidence — are reported rather than failed,
because selecting the right identifier is the task itself.
"""

from __future__ import annotations

from typing import Any

from causal_agent_bench.review_ready_v2.common import flatten

FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "answer_contract",
        "approval_required",
        "best_option",
        "claim_supported",
        "computed_refund",
        "first_open_slot",
        "final_answer",
        "final_decision",
        "final_total",
        "gold_answer",
        "recommended_choice",
        "recovery_action_id",
        "resolved_status",
        "route_kind",
        "scorer_policy",
        "selected_bundle",
        "selected_hotel",
        "selected_option",
        "selected_vendor",
    }
)

FORBIDDEN_FIELD_SUBSTRINGS = (
    "answer",
    "best_",
    "chosen",
    "conclusion",
    "final_",
    "gold",
    "is_correct",
    "optimal",
    "preferred_",
    "ranked",
    "ranking",
    "rank_order",
    "recommend",
    "route_kind",
    "scorer",
    "selected_",
    "verdict",
    "winner",
)

ANSWER_BEARING_TOKENS = tuple(sorted(FORBIDDEN_FIELD_NAMES | set(FORBIDDEN_FIELD_SUBSTRINGS)))

ANSWER_PHRASES = (
    "final answer",
    "best option",
    "selected option",
    "the correct answer",
    "you should choose",
    "recommended choice",
)


def _keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key).casefold())
            found |= _keys(child)
    elif isinstance(value, list):
        for child in value:
            found |= _keys(child)
    return found


def scan_answer_bearing(value: Any) -> set[str]:
    """Return every offending field name found anywhere inside ``value``."""

    offenders: set[str] = set()
    for key in _keys(value):
        if key in FORBIDDEN_FIELD_NAMES:
            offenders.add(key)
            continue
        if any(marker in key for marker in FORBIDDEN_FIELD_SUBSTRINGS):
            offenders.add(key)
    return offenders


def scan_answer_phrases(value: Any) -> set[str]:
    found: set[str] = set()
    for _, leaf in flatten(value):
        if not isinstance(leaf, str):
            continue
        lowered = leaf.casefold()
        found |= {phrase for phrase in ANSWER_PHRASES if phrase in lowered}
    return found


def gold_echoes(sources: Any, gold: str) -> list[dict[str, Any]]:
    """Locate gold *components* that appear as primitive leaves."""

    components = [part for part in gold.split("|") if part]
    echoes: list[dict[str, Any]] = []
    for locator, leaf in flatten(sources):
        text = str(leaf)
        for component in components:
            if text == component:
                echoes.append({"component": component, "locator": locator})
    return echoes


def verbatim_gold_present(sources: Any, gold: str) -> list[str]:
    """Hard failure: a record leaf reproduces the complete gold string."""

    return [locator for locator, leaf in flatten(sources) if str(leaf) == gold]


def primitive_evidence_report(
    sources: dict[str, Any], *, gold: str, manifest: dict[str, list[str]]
) -> dict[str, Any]:
    offending_fields = sorted(scan_answer_bearing(sources))
    phrases = sorted(scan_answer_phrases(sources))
    verbatim = verbatim_gold_present(sources, gold)
    undeclared_fields = sorted(
        f"{name}.{field}"
        for name, declared in manifest.items()
        if name in sources
        for field in _record_fields(sources[name]) - set(declared)
    )
    checks = {
        "no_answer_bearing_field_names": not offending_fields,
        "no_answer_phrases": not phrases,
        "no_verbatim_gold_in_evidence": not verbatim,
        "fields_match_declared_manifest": not undeclared_fields,
    }
    return {
        "offending_fields": offending_fields,
        "answer_phrases": phrases,
        "verbatim_gold_locators": verbatim,
        "undeclared_fields": undeclared_fields,
        "identifier_echoes": gold_echoes(sources, gold),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _record_fields(source: Any) -> set[str]:
    if isinstance(source, list):
        return {str(key) for row in source if isinstance(row, dict) for key in row}
    if isinstance(source, dict):
        return {str(key) for key in source}
    return set()


__all__ = [
    "ANSWER_BEARING_TOKENS",
    "ANSWER_PHRASES",
    "FORBIDDEN_FIELD_NAMES",
    "FORBIDDEN_FIELD_SUBSTRINGS",
    "gold_echoes",
    "primitive_evidence_report",
    "scan_answer_bearing",
    "scan_answer_phrases",
    "verbatim_gold_present",
]
