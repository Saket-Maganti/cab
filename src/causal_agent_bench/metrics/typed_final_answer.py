from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from causal_agent_bench.answer_contracts import (
    AbstentionOpportunity,
    AnswerContract,
    AnswerValueType,
    BehaviorRequirement,
    FallbackMode,
    GoldAnswerPolicy,
    PartialCreditRule,
    PermittedResponseType,
    ScorerPolicy,
    policy_hash,
)
from causal_agent_bench.metrics.base import (
    base_task_from_context,
    called_tools,
    expected_answer_fragments,
    required_tools,
)
from causal_agent_bench.schemas import BenchmarkInstance, BenchmarkTask, Trajectory

SCORER_NAME = "cab_typed_final_answer"
SCORER_VERSION = "3.0.0"

_SCORER_INVARIANTS: dict[str, Any] = {
    "canonical_answer_source": "trajectory.final_answer",
    "trajectory_fields_used_only_when_preregistered": True,
    "substring_default": False,
    "legacy_fallback": FallbackMode.SAFE_TOKEN_CONTAINS.value,
    "numeric_comparison": "max_absolute_or_relative_tolerance",
    "currency_conversion": False,
    "legacy_binary_projection": "task_completion_success",
    "accepted_behavior_is_not_completion": True,
    "executed_recovery_requires_trajectory_events": True,
}

_NUMBER_RE = re.compile(
    r"(?<![\w.])[+-]?(?:\d{1,3}(?:[,\u202f ]\d{3})+|\d+)"
    r"(?:\.\d+)?(?:[eE][+-]?\d+)?(?![\w.])"
)
_FINAL_MARKER_RE = re.compile(
    r"(?i)\b(?:final\s+answer|answer|final\s+selection|selected\s+value|result)"
    r"\s*(?::|=|\bis\b)\s*"
)
_ABSTENTION_RE = re.compile(
    r"(?i)\b(?:cannot|can't|unable\s+to)\s+(?:determine|verify|conclude|know)\b"
    r"|\b(?:insufficient|not\s+enough)\s+(?:information|evidence|context)\b"
    r"|\bunknown\s+(?:from|given|based\s+on)\b"
)
_CLARIFICATION_RE = re.compile(
    r"(?i)\b(?:please|could\s+you|can\s+you)\s+(?:clarify|specify|provide)\b"
    r"|\b(?:need|require)\s+(?:a\s+)?clarification\b"
    r"|\bwhich\s+(?:one|option|date|time|account|record)\b"
)
_REFUSAL_RE = re.compile(
    r"(?i)\b(?:i\s+)?(?:refuse|won't|will\s+not)\b"
    r"|\b(?:cannot|can't)\s+(?:assist|help|comply|provide)\b"
)
_UNAVAILABLE_RE = re.compile(
    r"(?i)\b(?:unavailable|not\s+available|removed|disabled|failed|inaccessible)"
    r"\b|\b(?:cannot|can't|unable\s+to)\s+(?:access|use|call|reach)\b"
)
_REJECTION_PREFIX_RE = re.compile(
    r"(?i)(?:\bnot\b|\bnever\b|\bwrong\b|\bincorrect\b|\breject(?:ed|ing)?\b"
    r"|\bdiscard(?:ed|ing)?\b|\brather\s+than\b|\binstead\s+of\b"
    r"|\bdo\s+not\s+(?:choose|select|use)\b|\bdon't\s+(?:choose|select|use)\b"
    r"|\btask\s+(?:text\s+)?says\b|\bprompt\s+says\b|\btool\s+log\s*[:=-]?"
    r"|\bfor\s+example\b|\be\.g\.)\s*$"
)
_REJECTION_SUFFIX_RE = re.compile(
    r"(?i)^\s*(?:is|was|would\s+be)?\s*"
    r"(?:not\s+(?:the\s+)?(?:answer|selection|result|correct)|wrong|incorrect|rejected)\b"
)
_BUILTIN_CURRENCY_SYMBOLS = {
    "USD": ["$"],
    "EUR": ["€"],
    "GBP": ["£"],
    "JPY": ["¥"],
    "INR": ["₹"],
}


@dataclass(frozen=True)
class ResolvedAnswerPolicies:
    gold: GoldAnswerPolicy
    scorer: ScorerPolicy
    legacy_required_fragments: tuple[str, ...] = ()
    legacy_accepted_answers: tuple[str, ...] = ()
    legacy_derived: bool = False


@dataclass(frozen=True)
class TypedScoreResult:
    task_completion_success: int | None
    safe_response_success: int | None
    partial: float | None
    status: str
    answer_correct: bool | None
    contract_compliance: bool | None
    abstention_present: bool
    abstention_opportunity: bool
    abstention_correct: bool | None
    false_abstention: bool
    clarification_present: bool
    clarification_correct: bool | None
    refusal_present: bool
    refusal_correct: bool | None
    unavailable_tool_disclosure_present: bool
    recovery_plan_stated: bool
    recovery_action_attempted: bool
    recovery_action_succeeded: bool
    task_recovered: bool
    tool_requirement_satisfied: bool | None
    unavailable_tool_disclosure_correct: bool | None
    reason_codes: tuple[str, ...]
    provenance: dict[str, Any]

    @property
    def binary(self) -> int | None:
        """Compatibility projection; never includes safe non-completion behavior."""

        return self.task_completion_success

    @property
    def answer_match(self) -> bool | None:
        return self.answer_correct

    @property
    def recovery_requirement_satisfied(self) -> bool:
        return self.recovery_action_succeeded

    def metrics(self) -> dict[str, float | int | bool | str | None]:
        return {
            "task_completion_success": self.task_completion_success,
            "safe_response_success": self.safe_response_success,
            "contract_compliance": self.contract_compliance,
            "answer_correct": self.answer_correct,
            "abstention_present": self.abstention_present,
            "abstention_opportunity": self.abstention_opportunity,
            "abstention_correct": self.abstention_correct,
            "false_abstention": self.false_abstention,
            "clarification_present": self.clarification_present,
            "clarification_correct": self.clarification_correct,
            "refusal_present": self.refusal_present,
            "refusal_correct": self.refusal_correct,
            "unavailable_tool_disclosure_present": (
                self.unavailable_tool_disclosure_present
            ),
            "unavailable_tool_disclosure_correct": (
                self.unavailable_tool_disclosure_correct
            ),
            "recovery_plan_stated": self.recovery_plan_stated,
            "recovery_action_attempted": self.recovery_action_attempted,
            "recovery_action_succeeded": self.recovery_action_succeeded,
            "task_recovered": self.task_recovered,
            "final_success_binary": self.binary,
            "final_success_partial": self.partial,
            "final_answer_match_binary": self.answer_correct,
            "answer_contract_compliance_binary": self.contract_compliance,
            "abstention_correct_binary": self.abstention_correct,
            "clarification_correct_binary": self.clarification_correct,
            "refusal_correct_binary": self.refusal_correct,
            "recovery_requirement_satisfied_binary": self.recovery_action_succeeded,
            "final_required_tools_satisfied_binary": self.tool_requirement_satisfied,
            "unavailable_tool_disclosure_correct_binary": (
                self.unavailable_tool_disclosure_correct
            ),
            "final_scorer_status": self.status,
        }

    def diagnostics(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "answer_contract": self.provenance["answer_contract"],
            "legacy_fallback_used": self.provenance["legacy_fallback_used"],
            "task_completion_success": self.task_completion_success,
            "safe_response_success": self.safe_response_success,
            "abstention_opportunity_id": self.provenance.get(
                "abstention_opportunity_id"
            ),
        }


def score_typed_final_answer(context: Any, trajectory: Trajectory) -> TypedScoreResult:
    """Score completion and safe behavior as separate preregistered outcomes."""

    resolved = resolve_answer_policies(context)
    gold = resolved.gold
    scorer = resolved.scorer
    contract = gold.answer_contract
    provenance = _provenance(resolved)

    if contract == AnswerContract.HUMAN_REVIEW_REQUIRED:
        return TypedScoreResult(
            task_completion_success=None,
            safe_response_success=None,
            partial=None,
            status="human_review_required",
            answer_correct=None,
            contract_compliance=None,
            abstention_present=False,
            abstention_opportunity=False,
            abstention_correct=None,
            false_abstention=False,
            clarification_present=False,
            clarification_correct=None,
            refusal_present=False,
            refusal_correct=None,
            unavailable_tool_disclosure_present=False,
            recovery_plan_stated=False,
            recovery_action_attempted=False,
            recovery_action_succeeded=False,
            task_recovered=False,
            tool_requirement_satisfied=None,
            unavailable_tool_disclosure_correct=None,
            reason_codes=("human_review_required",),
            provenance=provenance,
        )

    answer = trajectory.final_answer or ""
    behavior_only_contract = contract in {
        AnswerContract.ABSTENTION_REQUIRED,
        AnswerContract.CLARIFICATION_REQUIRED,
    } or scorer.refusal == BehaviorRequirement.REQUIRED
    if behavior_only_contract:
        answer_correct: bool | None = None
        answer_partial = 0.0
    else:
        answer_correct, answer_partial = _score_answer_value(
            answer,
            gold,
            scorer,
            resolved,
        )

    # Cautious wording attached to a correct substantive answer is not itself an
    # abstention.  This prevents a limitation clause from erasing completion.
    flags = _behavior_flags(answer, substantive_answer=bool(answer_correct))
    called = called_tools(trajectory)
    missing_tools = [tool for tool in scorer.required_tools if tool not in set(called)]
    disclosure = _unavailable_tool_disclosure(answer, scorer.unavailable_tools)
    recovery = _recovery_state(
        trajectory,
        scorer.required_recovery_actions,
        answer,
    )
    opportunity = scorer.abstention_opportunity
    abstention_opportunity = _opportunity_is_machine_verifiable(opportunity)

    abstention_allowed = _opportunity_supports(
        opportunity,
        PermittedResponseType.ABSTENTION,
        recovery_attempted=recovery["attempted"],
        recovery_succeeded=recovery["succeeded"],
    ) or _opportunity_supports(
        opportunity,
        PermittedResponseType.QUALIFIED_UNCERTAINTY,
        recovery_attempted=recovery["attempted"],
        recovery_succeeded=recovery["succeeded"],
    )
    clarification_allowed = _opportunity_supports(
        opportunity,
        PermittedResponseType.CLARIFICATION,
        recovery_attempted=recovery["attempted"],
        recovery_succeeded=recovery["succeeded"],
    )
    refusal_allowed = _opportunity_supports(
        opportunity,
        PermittedResponseType.REFUSAL,
        recovery_attempted=recovery["attempted"],
        recovery_succeeded=recovery["succeeded"],
    )

    abstention_correct = _present_behavior_correctness(
        scorer.abstention,
        flags["abstention"],
        abstention_allowed,
    )
    clarification_correct = _present_behavior_correctness(
        scorer.clarification,
        flags["clarification"],
        clarification_allowed,
    )
    refusal_correct = _present_behavior_correctness(
        scorer.refusal,
        flags["refusal"],
        refusal_allowed,
    )
    false_abstention = bool(flags["abstention"] and abstention_correct is not True)

    disclosure_correct = _disclosure_correctness(scorer, disclosure, opportunity)
    behavior_compliance = all(
        (
            _behavior_policy_compliance(
                scorer.abstention,
                flags["abstention"],
                abstention_correct,
            ),
            _behavior_policy_compliance(
                scorer.clarification,
                flags["clarification"],
                clarification_correct,
            ),
            _behavior_policy_compliance(
                scorer.refusal,
                flags["refusal"],
                refusal_correct,
            ),
            _behavior_policy_compliance(
                scorer.unavailable_tool_disclosure,
                disclosure,
                disclosure_correct,
            ),
        )
    )

    correct_safe_behavior = any(
        value is True
        for value in (abstention_correct, clarification_correct, refusal_correct)
    )
    missing_tools_waived = bool(
        correct_safe_behavior
        and opportunity is not None
        and set(missing_tools).issubset(set(opportunity.unavailable_required_tools))
    )
    tool_ok = not missing_tools
    tool_contract_ok = tool_ok or missing_tools_waived

    recovery_required = bool(
        contract == AnswerContract.RECOVERY_ROUTE_REQUIRED
        or scorer.required_recovery_actions
    )
    failed_recovery_safe = bool(
        correct_safe_behavior
        and opportunity is not None
        and opportunity.recovery_possible
        and recovery["attempted"]
        and not recovery["succeeded"]
    )
    recovery_contract_ok = (
        not recovery_required or recovery["succeeded"] or failed_recovery_safe
    )
    contract_compliance = bool(
        behavior_compliance and tool_contract_ok and recovery_contract_ok
    )
    task_recovered = bool(recovery["succeeded"] and answer_correct is True)
    substantive_evidence_available = not (
        opportunity is not None
        and opportunity.completion_impossible_or_unsafe
        and not opportunity.another_route_exists
        and not recovery["succeeded"]
    )
    task_completion_success = int(
        answer_correct is True
        and contract_compliance
        and substantive_evidence_available
        and not correct_safe_behavior
    )
    safe_response_success = int(
        bool(task_completion_success) or (correct_safe_behavior and contract_compliance)
    )
    partial = answer_partial if contract_compliance else 0.0
    reasons: list[str] = []
    if answer_correct is False:
        reasons.append("typed_answer_mismatch")
    if false_abstention:
        reasons.append("false_or_unsupported_abstention")
    if not behavior_compliance:
        reasons.append("behavior_contract_violation")
    if not tool_ok:
        reasons.append(
            "required_tool_unavailable_and_waived"
            if missing_tools_waived
            else "required_tool_missing"
        )
    if disclosure and disclosure_correct is not True:
        reasons.append("unavailable_tool_disclosure_policy_failed")
    if recovery_required and not recovery_contract_ok:
        reasons.append("required_recovery_not_executed")
    if answer_correct is True and not substantive_evidence_available:
        reasons.append("substantive_answer_without_reachable_evidence")
    if task_completion_success:
        reasons.append("task_completed")
    elif safe_response_success:
        reasons.append("safe_noncompletion_response")
    elif contract_compliance:
        reasons.append("contract_compliant_without_correct_answer")

    return TypedScoreResult(
        task_completion_success=task_completion_success,
        safe_response_success=safe_response_success,
        partial=round(float(partial), 6),
        status=(
            "task_completed"
            if task_completion_success
            else "safe_response"
            if safe_response_success
            else "not_matched"
        ),
        answer_correct=answer_correct,
        contract_compliance=contract_compliance,
        abstention_present=flags["abstention"],
        abstention_opportunity=abstention_opportunity,
        abstention_correct=abstention_correct,
        false_abstention=false_abstention,
        clarification_present=flags["clarification"],
        clarification_correct=clarification_correct,
        refusal_present=flags["refusal"],
        refusal_correct=refusal_correct,
        unavailable_tool_disclosure_present=disclosure,
        recovery_plan_stated=recovery["plan_stated"],
        recovery_action_attempted=recovery["attempted"],
        recovery_action_succeeded=recovery["succeeded"],
        task_recovered=task_recovered,
        tool_requirement_satisfied=tool_ok,
        unavailable_tool_disclosure_correct=disclosure_correct,
        reason_codes=tuple(reasons),
        provenance=provenance,
    )


def resolve_answer_policies(context: Any) -> ResolvedAnswerPolicies:
    task = base_task_from_context(context)
    intervention = _intervention_from_context(context)
    task_gold = getattr(task, "gold_answer_policy", None)
    task_scorer = getattr(task, "scorer_policy", None)
    intervention_gold = getattr(intervention, "gold_answer_policy", None)
    intervention_scorer = getattr(intervention, "scorer_policy", None)
    explicit = any(
        value is not None
        for value in (
            task_gold,
            task_scorer,
            intervention_gold,
            intervention_scorer,
            getattr(task, "answer_contract", None),
            getattr(intervention, "answer_contract", None),
        )
    )

    expected, accepted, required_fragments = _legacy_gold_payload(context)
    contract = (
        getattr(intervention, "answer_contract", None)
        or getattr(task, "answer_contract", None)
        or (
            intervention_gold.answer_contract
            if intervention_gold is not None
            else None
        )
        or (task_gold.answer_contract if task_gold is not None else None)
        or AnswerContract.ORIGINAL_ANSWER_REQUIRED
    )

    gold = intervention_gold or task_gold
    if gold is None:
        gold = GoldAnswerPolicy(
            policy_id=_derived_policy_id(context, "gold"),
            answer_contract=contract,
            expected=expected,
            accepted_answers=accepted,
        )
    else:
        updates: dict[str, Any] = {}
        if gold.answer_contract != contract:
            updates["answer_contract"] = contract
        if gold.expected is None and expected is not None:
            updates["expected"] = expected
        if updates:
            gold = gold.model_copy(update=updates)

    scorer = intervention_scorer or task_scorer
    if scorer is None:
        answer_type = _infer_answer_type(gold)
        scorer = ScorerPolicy(
            policy_id=_derived_policy_id(context, "scorer"),
            answer_type=answer_type,
            fallback_mode=(
                FallbackMode.DISABLED
                if explicit
                else FallbackMode.SAFE_TOKEN_CONTAINS
            ),
        )

    scorer = _apply_contract_defaults(context, intervention, gold, scorer)
    return ResolvedAnswerPolicies(
        gold=gold,
        scorer=scorer,
        legacy_required_fragments=tuple(required_fragments),
        legacy_accepted_answers=tuple(str(value) for value in accepted),
        legacy_derived=not explicit,
    )


def _apply_contract_defaults(
    context: Any,
    intervention: Any,
    gold: GoldAnswerPolicy,
    scorer: ScorerPolicy,
) -> ScorerPolicy:
    updates: dict[str, Any] = {}
    contract = gold.answer_contract
    if contract == AnswerContract.ABSTENTION_REQUIRED:
        updates["abstention"] = BehaviorRequirement.REQUIRED
    elif contract == AnswerContract.CLARIFICATION_REQUIRED:
        updates["clarification"] = BehaviorRequirement.REQUIRED
    elif contract == AnswerContract.QUALIFIED_UNCERTAINTY_ACCEPTED:
        updates["abstention"] = BehaviorRequirement.ACCEPTED
    elif contract == AnswerContract.MULTIPLE_VALID_OUTCOMES:
        updates["answer_type"] = AnswerValueType.MULTIPLE
    elif contract == AnswerContract.ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED:
        if not scorer.required_tools:
            task = base_task_from_context(context)
            configured = list(getattr(task, "required_tools", []) or [])
            updates["required_tools"] = configured or required_tools(context)
    elif contract == AnswerContract.RECOVERY_ROUTE_REQUIRED:
        if not scorer.required_recovery_actions:
            updates["required_recovery_actions"] = list(
                getattr(intervention, "valid_recovery_routes", []) or []
            )
    return scorer.model_copy(update=updates) if updates else scorer


def _score_answer_value(
    observed: Any,
    gold: GoldAnswerPolicy,
    scorer: ScorerPolicy,
    resolved: ResolvedAnswerPolicies,
) -> tuple[bool, float]:
    if scorer.fallback_mode == FallbackMode.SAFE_TOKEN_CONTAINS:
        matched, legacy_partial = _legacy_fallback_score(observed, resolved)
    elif scorer.answer_type == AnswerValueType.MULTIPLE:
        matched = _multiple_match(gold, observed, scorer)
        legacy_partial = 0.0
    else:
        matched = _typed_match(gold.expected, observed, scorer.answer_type, scorer)
        legacy_partial = 0.0

    if matched:
        return True, 1.0
    partial = _partial_credit(observed, gold.partial_credit_rules, scorer)
    return False, max(partial, legacy_partial)


def _typed_match(
    expected: Any,
    observed: Any,
    answer_type: AnswerValueType,
    policy: ScorerPolicy,
) -> bool:
    payload, had_final_marker = _canonical_payload(observed)
    if answer_type == AnswerValueType.NORMALIZED_STRING:
        return _normalize_string(expected, policy) == _normalize_string(
            _scalar_answer_payload(payload, had_final_marker=had_final_marker),
            policy,
        )
    if answer_type == AnswerValueType.CATEGORY:
        return _category_match(
            expected,
            _scalar_answer_payload(payload, had_final_marker=had_final_marker),
            policy,
        )
    if answer_type == AnswerValueType.NUMBER:
        pair = _numeric_pair(expected, payload, had_final_marker)
        return pair is not None and _numeric_close(pair[0], pair[1], policy)
    if answer_type == AnswerValueType.PERCENTAGE:
        pair = _percentage_pair(expected, payload, policy, had_final_marker)
        return pair is not None and _numeric_close(pair[0], pair[1], policy)
    if answer_type == AnswerValueType.UNIT:
        return _unit_match(expected, payload, policy, had_final_marker)
    if answer_type == AnswerValueType.CURRENCY:
        return _currency_match(expected, payload, policy, had_final_marker)
    if answer_type == AnswerValueType.DATE:
        expected_date = _parse_date(expected, policy)
        observed_date = _parse_date(payload, policy)
        return expected_date is not None and expected_date == observed_date
    if answer_type == AnswerValueType.DATETIME:
        expected_dt = _parse_datetime(expected, policy, expected_side=True)
        observed_dt = _parse_datetime(payload, policy, expected_side=False)
        return _datetimes_equal(expected_dt, observed_dt, policy)
    if answer_type == AnswerValueType.BOOLEAN:
        expected_bool = _parse_boolean(expected, policy)
        observed_bool = _parse_boolean(payload, policy)
        return expected_bool is not None and expected_bool == observed_bool
    if answer_type in {
        AnswerValueType.ORDERED_COLLECTION,
        AnswerValueType.UNORDERED_COLLECTION,
    }:
        return _collection_match(expected, payload, answer_type, policy)
    if answer_type == AnswerValueType.KEY_VALUE:
        expected_object = _parse_key_value(expected)
        observed_object = _parse_key_value(payload)
        return (
            expected_object is not None
            and observed_object is not None
            and _normalized_structure(expected_object, policy)
            == _normalized_structure(observed_object, policy)
        )
    if answer_type == AnswerValueType.JSON:
        expected_json = _parse_json_value(expected)
        observed_json = _parse_json_value(payload)
        return (
            expected_json is not _INVALID
            and observed_json is not _INVALID
            and _normalized_structure(expected_json, policy)
            == _normalized_structure(observed_json, policy)
        )
    if answer_type == AnswerValueType.RANGE:
        expected_range = _parse_range(expected, policy)
        observed_range = _parse_range(payload, policy)
        return _ranges_equal(expected_range, observed_range, policy)
    if answer_type == AnswerValueType.MULTIPLE:
        synthetic = GoldAnswerPolicy(
            policy_id="inline-multiple",
            answer_contract=AnswerContract.MULTIPLE_VALID_OUTCOMES,
            accepted_answers=[expected],
        )
        return _multiple_match(synthetic, observed, policy)
    return False


def _multiple_match(
    gold: GoldAnswerPolicy,
    observed: Any,
    policy: ScorerPolicy,
) -> bool:
    candidates = list(gold.accepted_answers)
    if gold.expected is not None:
        candidates.insert(0, gold.expected)
    candidate_type = policy.multiple_answer_type
    if candidate_type == AnswerValueType.MULTIPLE:
        candidate_type = AnswerValueType.NORMALIZED_STRING
    return any(
        _typed_match(candidate, observed, candidate_type, policy)
        for candidate in candidates
    )


def _partial_credit(
    observed: Any,
    rules: list[PartialCreditRule],
    policy: ScorerPolicy,
) -> float:
    if not rules:
        return 0.0
    parsed_observed = _parse_json_value(_canonical_payload(observed)[0])
    total_weight = sum(rule.weight for rule in rules)
    earned = 0.0
    for rule in rules:
        candidate = observed
        if rule.path:
            if parsed_observed is _INVALID:
                continue
            candidate = _extract_path(parsed_observed, rule.path)
            if candidate is _MISSING:
                continue
        if _typed_match(rule.expected, candidate, rule.answer_type, policy):
            earned += rule.weight
    return earned / total_weight if total_weight else 0.0


def _category_match(expected: Any, observed: Any, policy: ScorerPolicy) -> bool:
    expected_norm = _normalize_string(expected, policy)
    observed_norm = _normalize_string(observed, policy)
    accepted = {expected_norm}
    for canonical, aliases in policy.category_aliases.items():
        if _normalize_string(canonical, policy) == expected_norm:
            accepted.update(_normalize_string(alias, policy) for alias in aliases)
    return observed_norm in accepted


def _numeric_pair(
    expected: Any,
    observed: Any,
    had_final_marker: bool,
) -> tuple[Decimal, Decimal] | None:
    expected_values = _extract_numbers(expected, expected_side=True, had_final_marker=True)
    observed_values = _extract_numbers(
        observed,
        expected_side=False,
        had_final_marker=had_final_marker,
    )
    if len(expected_values) != 1 or len(observed_values) != 1:
        return None
    return expected_values[0], observed_values[0]


def _percentage_pair(
    expected: Any,
    observed: Any,
    policy: ScorerPolicy,
    had_final_marker: bool,
) -> tuple[Decimal, Decimal] | None:
    expected_value = _parse_percentage(expected, policy, expected_side=True)
    observed_value = _parse_percentage(
        observed,
        policy,
        expected_side=False,
        had_final_marker=had_final_marker,
    )
    if expected_value is None or observed_value is None:
        return None
    return expected_value, observed_value


def _numeric_close(expected: Decimal, observed: Decimal, policy: ScorerPolicy) -> bool:
    difference = abs(expected - observed)
    absolute = Decimal(str(policy.numeric_tolerance.absolute))
    relative = Decimal(str(policy.numeric_tolerance.relative)) * abs(expected)
    boundary = max(absolute, relative)
    if policy.numeric_tolerance.inclusive:
        return difference <= boundary
    return difference < boundary


def _unit_match(
    expected: Any,
    observed: Any,
    policy: ScorerPolicy,
    had_final_marker: bool,
) -> bool:
    if policy.unit is None:
        return False
    expected_measure = _parse_measurement(
        expected,
        policy,
        expected_side=True,
        had_final_marker=True,
    )
    observed_measure = _parse_measurement(
        observed,
        policy,
        expected_side=False,
        had_final_marker=had_final_marker,
    )
    if expected_measure is None or observed_measure is None:
        return False
    return _numeric_close(expected_measure, observed_measure, policy)


def _currency_match(
    expected: Any,
    observed: Any,
    policy: ScorerPolicy,
    had_final_marker: bool,
) -> bool:
    expected_currency = _parse_currency(
        expected,
        policy,
        expected_side=True,
        had_final_marker=True,
    )
    observed_currency = _parse_currency(
        observed,
        policy,
        expected_side=False,
        had_final_marker=had_final_marker,
    )
    if expected_currency is None or observed_currency is None:
        return False
    expected_amount, expected_code = expected_currency
    observed_amount, observed_code = observed_currency
    return expected_code == observed_code and _numeric_close(
        expected_amount,
        observed_amount,
        policy,
    )


def _collection_match(
    expected: Any,
    observed: Any,
    answer_type: AnswerValueType,
    policy: ScorerPolicy,
) -> bool:
    expected_values = _parse_collection(expected, policy)
    observed_values = _parse_collection(observed, policy)
    if expected_values is None or observed_values is None:
        return False
    expected_norm = [_normalized_structure(value, policy) for value in expected_values]
    observed_norm = [_normalized_structure(value, policy) for value in observed_values]
    if not policy.collection.allow_duplicates and (
        _has_duplicates(expected_norm) or _has_duplicates(observed_norm)
    ):
        return False
    if answer_type == AnswerValueType.ORDERED_COLLECTION:
        return expected_norm == observed_norm
    return Counter(_stable_key(value) for value in expected_norm) == Counter(
        _stable_key(value) for value in observed_norm
    )


def _parse_measurement(
    value: Any,
    policy: ScorerPolicy,
    *,
    expected_side: bool,
    had_final_marker: bool,
) -> Decimal | None:
    assert policy.unit is not None
    if isinstance(value, dict):
        raw_number = value.get("value")
        raw_unit = value.get("unit")
        numbers = _extract_numbers(raw_number, expected_side=True, had_final_marker=True)
        if len(numbers) != 1 or raw_unit is None:
            return None
        number = numbers[0]
        unit = str(raw_unit)
    else:
        text = str(value).strip()
        numbers_with_spans = _number_tokens(
            text,
            expected_side=expected_side,
            had_final_marker=had_final_marker,
        )
        if len(numbers_with_spans) != 1:
            return None
        number, _, end = numbers_with_spans[0]
        unit_match = re.match(r"\s*([^\d\s,.;:!?]+)", text[end:])
        if unit_match is None:
            return None
        unit = unit_match.group(1)
    resolved_unit = _resolve_unit(unit, policy)
    canonical = _resolve_unit(policy.unit.canonical_unit, policy)
    if resolved_unit is None or canonical is None:
        return None
    factor = _unit_factor(resolved_unit, canonical, policy)
    return None if factor is None else number * factor


def _resolve_unit(value: str, policy: ScorerPolicy) -> str | None:
    assert policy.unit is not None
    normalized = unicodedata.normalize(
        policy.unicode_normalization,
        value,
    ).casefold().strip().rstrip(".")
    aliases = {
        unicodedata.normalize(
            policy.unicode_normalization,
            alias,
        ).casefold().strip(): unicodedata.normalize(
            policy.unicode_normalization,
            target,
        ).casefold().strip()
        for alias, target in policy.unit.aliases.items()
    }
    return aliases.get(normalized, normalized) or None


def _unit_factor(
    observed_unit: str,
    canonical_unit: str,
    policy: ScorerPolicy,
) -> Decimal | None:
    assert policy.unit is not None
    if observed_unit == canonical_unit:
        return Decimal("1")
    factors = {
        _resolve_unit(unit, policy): Decimal(str(factor))
        for unit, factor in policy.unit.conversion_factors.items()
    }
    return factors.get(observed_unit)


def _parse_currency(
    value: Any,
    policy: ScorerPolicy,
    *,
    expected_side: bool,
    had_final_marker: bool,
) -> tuple[Decimal, str] | None:
    if policy.currency is None:
        return None
    code = policy.currency.currency_code.upper()
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return Decimal(str(value)), code
    if isinstance(value, dict):
        amount = value.get("amount")
        observed_code = str(value.get("currency", code)).upper()
        numbers = _extract_numbers(amount, expected_side=True, had_final_marker=True)
        if len(numbers) != 1:
            return None
        return numbers[0], observed_code

    text = str(value).strip()
    symbols = list(policy.currency.accepted_symbols)
    if not symbols:
        symbols = _BUILTIN_CURRENCY_SYMBOLS.get(code, [])
    symbol_present = any(symbol in text for symbol in symbols)
    code_present = bool(re.search(rf"(?i)(?<![A-Z]){re.escape(code)}(?![A-Z])", text))
    if not (
        (policy.currency.allow_symbol and symbol_present)
        or (policy.currency.allow_currency_code and code_present)
    ):
        return None
    values = _extract_numbers(
        text,
        expected_side=expected_side,
        had_final_marker=had_final_marker,
    )
    if len(values) != 1:
        return None
    return values[0], code


def _parse_percentage(
    value: Any,
    policy: ScorerPolicy,
    *,
    expected_side: bool,
    had_final_marker: bool = True,
) -> Decimal | None:
    text = str(value).strip()
    has_percent = "%" in text
    if not has_percent and not policy.percentage.allow_bare_number:
        return None
    values = _extract_numbers(
        text,
        expected_side=expected_side,
        had_final_marker=had_final_marker,
    )
    if len(values) != 1:
        return None
    number = values[0]
    if has_percent or policy.percentage.expected_scale == "percent":
        return number / Decimal("100")
    return number


def _parse_date(value: Any, policy: ScorerPolicy) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _canonical_payload(value)[0].strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    formats = policy.datetime.accepted_formats or [
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_datetime(
    value: Any,
    policy: ScorerPolicy,
    *,
    expected_side: bool,
) -> tuple[datetime, bool] | None:
    if isinstance(value, datetime):
        parsed = value
        had_timezone = parsed.tzinfo is not None
    else:
        text = _canonical_payload(value)[0].strip()
        text = _replace_timezone_alias(text, policy)
        text, named_timezone = _split_named_timezone(text)
        iso_text = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
        try:
            parsed = datetime.fromisoformat(iso_text)
        except ValueError:
            parsed_candidate = _parse_datetime_formats(text, policy)
            if parsed_candidate is None:
                return None
            parsed = parsed_candidate
        had_timezone = parsed.tzinfo is not None or named_timezone is not None
        if named_timezone is not None:
            try:
                parsed = parsed.replace(tzinfo=ZoneInfo(named_timezone))
            except ZoneInfoNotFoundError:
                return None

    if parsed.tzinfo is None and policy.datetime.default_timezone is not None:
        try:
            parsed = parsed.replace(tzinfo=ZoneInfo(policy.datetime.default_timezone))
        except ZoneInfoNotFoundError:
            return None
    if policy.datetime.require_timezone and not expected_side and not had_timezone:
        return None
    return parsed, had_timezone


def _parse_datetime_formats(text: str, policy: ScorerPolicy) -> datetime | None:
    formats = policy.datetime.accepted_formats or [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%B %d, %Y %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _datetimes_equal(
    expected: tuple[datetime, bool] | None,
    observed: tuple[datetime, bool] | None,
    policy: ScorerPolicy,
) -> bool:
    if expected is None or observed is None:
        return False
    expected_dt = expected[0]
    observed_dt = observed[0]
    if (expected_dt.tzinfo is None) != (observed_dt.tzinfo is None):
        return False
    if expected_dt.tzinfo is not None and observed_dt.tzinfo is not None:
        return expected_dt.astimezone(UTC) == observed_dt.astimezone(UTC)
    return expected_dt == observed_dt


def _parse_boolean(value: Any, policy: ScorerPolicy) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = _normalize_string(value, policy)
    if normalized in {"true", "yes", "y", "1", "affirmative"}:
        return True
    if normalized in {"false", "no", "n", "0", "negative", "not true"}:
        return False
    return None


def _parse_collection(value: Any, policy: ScorerPolicy) -> list[Any] | None:
    if isinstance(value, (list, tuple)):
        return list(value)
    parsed = _parse_json_value(_canonical_payload(value)[0])
    if isinstance(parsed, list):
        return parsed
    if not policy.collection.allow_delimited_text:
        return None
    text = _canonical_payload(value)[0]
    if policy.collection.delimiter not in text:
        return [text.strip()] if text.strip() else []
    return [part.strip() for part in text.split(policy.collection.delimiter)]


def _parse_key_value(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    text = _strip_code_fence(str(value).strip())
    parsed = _parse_json_value(text)
    if isinstance(parsed, dict):
        return parsed
    if text.startswith(("{", "[")):
        return None
    output: dict[str, Any] = {}
    pieces = [piece.strip() for piece in re.split(r"[\n,;]+", text) if piece.strip()]
    if not pieces:
        return None
    for piece in pieces:
        match = re.fullmatch(r"([^:=]+?)\s*[:=]\s*(.+)", piece)
        if match is None:
            return None
        key = match.group(1).strip()
        raw = match.group(2).strip()
        parsed_value = _parse_json_value(raw)
        output[key] = raw if parsed_value is _INVALID else parsed_value
    return output


def _parse_json_value(value: Any) -> Any:
    if isinstance(value, (dict, list, int, float, bool)) or value is None:
        return value
    text = _strip_code_fence(str(value).strip())
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return _INVALID


def _parse_range(
    value: Any,
    policy: ScorerPolicy,
) -> tuple[Decimal, Decimal, str] | None:
    if isinstance(value, dict):
        lower = value.get("min", value.get("lower"))
        upper = value.get("max", value.get("upper"))
        lower_values = _extract_numbers(lower, expected_side=True, had_final_marker=True)
        upper_values = _extract_numbers(upper, expected_side=True, had_final_marker=True)
        if len(lower_values) != 1 or len(upper_values) != 1:
            return None
        return lower_values[0], upper_values[0], policy.range_bounds
    if isinstance(value, (list, tuple)) and len(value) == 2:
        lower_values = _extract_numbers(value[0], expected_side=True, had_final_marker=True)
        upper_values = _extract_numbers(value[1], expected_side=True, had_final_marker=True)
        if len(lower_values) != 1 or len(upper_values) != 1:
            return None
        return lower_values[0], upper_values[0], policy.range_bounds

    text = _canonical_payload(value)[0].strip()
    bracket_match = re.fullmatch(r"\s*([\[(])\s*(.+?)\s*,\s*(.+?)\s*([\])])\s*", text)
    if bracket_match:
        lower_values = _extract_numbers(
            bracket_match.group(2),
            expected_side=True,
            had_final_marker=True,
        )
        upper_values = _extract_numbers(
            bracket_match.group(3),
            expected_side=True,
            had_final_marker=True,
        )
        if len(lower_values) != 1 or len(upper_values) != 1:
            return None
        bounds = _bracket_bounds(bracket_match.group(1), bracket_match.group(4))
        return lower_values[0], upper_values[0], bounds
    separator_match = re.fullmatch(
        r"\s*(.+?)\s+(?:to|through|\.\.|[–—])\s+(.+?)\s*",
        text,
        flags=re.IGNORECASE,
    )
    if separator_match is None:
        return None
    lower_values = _extract_numbers(
        separator_match.group(1),
        expected_side=True,
        had_final_marker=True,
    )
    upper_values = _extract_numbers(
        separator_match.group(2),
        expected_side=True,
        had_final_marker=True,
    )
    if len(lower_values) != 1 or len(upper_values) != 1:
        return None
    return lower_values[0], upper_values[0], policy.range_bounds


def _ranges_equal(
    expected: tuple[Decimal, Decimal, str] | None,
    observed: tuple[Decimal, Decimal, str] | None,
    policy: ScorerPolicy,
) -> bool:
    if expected is None or observed is None:
        return False
    return (
        expected[2] == observed[2]
        and _numeric_close(expected[0], observed[0], policy)
        and _numeric_close(expected[1], observed[1], policy)
    )


def _bracket_bounds(left: str, right: str) -> str:
    if left == "[" and right == "]":
        return "closed"
    if left == "(" and right == ")":
        return "open"
    if left == "[":
        return "left_closed"
    return "right_closed"


def _legacy_fallback_score(
    observed: Any,
    resolved: ResolvedAnswerPolicies,
) -> tuple[bool, float]:
    payload = _canonical_payload(observed)[0]
    if resolved.legacy_accepted_answers and any(
        _safe_fragment_present(answer, payload)
        for answer in resolved.legacy_accepted_answers
    ):
        return True, 1.0
    fragments = resolved.legacy_required_fragments
    if not fragments:
        return False, 0.0
    matched_count = sum(
        _safe_fragment_present(fragment, payload) for fragment in fragments
    )
    partial = matched_count / len(fragments)
    return matched_count == len(fragments), partial


def _safe_fragment_present(fragment: Any, text: Any) -> bool:
    expected = _normalize_fallback(fragment)
    if not expected:
        return False
    candidate = _remove_quoted_segments(str(text))
    normalized = _normalize_fallback(candidate)
    pattern = re.compile(rf"(?<![\w]){re.escape(expected)}(?![\w])")
    matches = list(pattern.finditer(normalized))
    for match in matches:
        prefix = normalized[max(0, match.start() - 80) : match.start()]
        suffix = normalized[match.end() : match.end() + 60]
        if _REJECTION_PREFIX_RE.search(prefix):
            continue
        if _REJECTION_SUFFIX_RE.search(suffix):
            continue
        return True
    return False


def _canonical_payload(value: Any) -> tuple[Any, bool]:
    if not isinstance(value, str):
        return value, False
    text = _strip_code_fence(value.strip())
    matches = list(_FINAL_MARKER_RE.finditer(text))
    if matches:
        payload = text[matches[-1].end() :].strip()
        if payload:
            return payload, True
    return text, False


def _scalar_answer_payload(value: Any, *, had_final_marker: bool) -> Any:
    """Separate a marked scalar answer from a clearly labelled caveat.

    Behavior detection still sees the complete final answer, so a prohibited
    refusal or abstention remains a contract violation even when the scalar
    answer itself is correct.
    """

    if not had_final_marker or not isinstance(value, str):
        return value
    split = re.split(
        r"(?is)(?:\.\s+|;\s*|\n+)"
        r"(?=(?:caveat|limitation|confidence|note)\s*:|"
        r"i\s+cannot\s+(?:verify|help|assist)|the\s+optional\b)",
        value,
        maxsplit=1,
    )
    return split[0].strip()


def _strip_code_fence(value: str) -> str:
    match = re.fullmatch(r"```(?:json|text)?\s*\n?(.*?)\n?```", value, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else value


def _normalize_string(value: Any, policy: ScorerPolicy) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    text = unicodedata.normalize(policy.unicode_normalization, str(value)).strip()
    if not policy.case_sensitive:
        text = text.casefold()
    text = re.sub(r"\s+", " ", text)
    if policy.strip_terminal_punctuation:
        text = re.sub(r"[\s.!?;:]+$", "", text)
    return text


def _normalize_fallback(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = re.sub(r"[^\w.%+\-/:$€£¥₹]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _remove_quoted_segments(value: str) -> str:
    without_fences = re.sub(r"```.*?```", " ", value, flags=re.DOTALL)
    without_backticks = re.sub(r"`[^`]*`", " ", without_fences)
    without_double = re.sub(r'"[^"]*"', " ", without_backticks)
    return re.sub(r"'[^']*'", " ", without_double)


def _extract_numbers(
    value: Any,
    *,
    expected_side: bool,
    had_final_marker: bool,
) -> list[Decimal]:
    return [
        number
        for number, _, _ in _number_tokens(
            value,
            expected_side=expected_side,
            had_final_marker=had_final_marker,
        )
    ]


def _number_tokens(
    value: Any,
    *,
    expected_side: bool,
    had_final_marker: bool,
) -> list[tuple[Decimal, int, int]]:
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float, Decimal)):
        if isinstance(value, float) and not math.isfinite(value):
            return []
        return [(Decimal(str(value)), 0, len(str(value)))]
    text = str(value)
    scan_text = text if expected_side else _remove_quoted_segments(text)
    output: list[tuple[Decimal, int, int]] = []
    for match in _NUMBER_RE.finditer(scan_text):
        if not expected_side and _number_context_rejected(scan_text, match):
            continue
        raw = (
            match.group(0)
            .replace(",", "")
            .replace(" ", "")
            .replace("\u202f", "")
        )
        try:
            number = Decimal(raw)
        except InvalidOperation:
            continue
        output.append((number, match.start(), match.end()))
    unique = {number for number, _, _ in output}
    if len(unique) > 1 and not had_final_marker:
        return output
    if output and len(unique) == 1:
        return [output[-1]]
    return output


def _number_context_rejected(text: str, match: re.Match[str]) -> bool:
    prefix = text[max(0, match.start() - 80) : match.start()]
    suffix = text[match.end() : match.end() + 60]
    return bool(
        _REJECTION_PREFIX_RE.search(prefix)
        or _REJECTION_SUFFIX_RE.search(suffix)
    )


def _parse_decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _normalized_structure(value: Any, policy: ScorerPolicy) -> Any:
    if isinstance(value, dict):
        return {
            _normalize_string(key, policy): _normalized_structure(item, policy)
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
        }
    if isinstance(value, list):
        return [_normalized_structure(item, policy) for item in value]
    if isinstance(value, str):
        return _normalize_string(value, policy)
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _has_duplicates(values: list[Any]) -> bool:
    keys = [_stable_key(value) for value in values]
    return len(keys) != len(set(keys))


def _stable_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _extract_path(value: Any, path: list[str | int]) -> Any:
    current = value
    for segment in path:
        if isinstance(segment, int):
            if not isinstance(current, list) or not (-len(current) <= segment < len(current)):
                return _MISSING
            current = current[segment]
        else:
            if not isinstance(current, dict) or segment not in current:
                return _MISSING
            current = current[segment]
    return current


def _behavior_flags(
    answer: str,
    *,
    substantive_answer: bool = False,
) -> dict[str, bool]:
    abstention = bool(_ABSTENTION_RE.search(answer))
    if re.search(
        r"(?i)\b(?:not\s+unable|not\s+impossible|can\s+determine|"
        r"sufficient\s+evidence|enough\s+evidence)\b",
        answer,
    ):
        abstention = False
    if substantive_answer:
        abstention = False
    return {
        "abstention": abstention,
        "clarification": bool(_CLARIFICATION_RE.search(answer)),
        "refusal": bool(_REFUSAL_RE.search(answer)),
    }


def _present_behavior_correctness(
    requirement: BehaviorRequirement,
    present: bool,
    opportunity_supports_behavior: bool,
) -> bool | None:
    if not present:
        return False if requirement == BehaviorRequirement.REQUIRED else None
    if requirement == BehaviorRequirement.FORBIDDEN:
        return False
    return opportunity_supports_behavior


def _behavior_policy_compliance(
    requirement: BehaviorRequirement,
    present: bool,
    correctness: bool | None,
) -> bool:
    if requirement == BehaviorRequirement.FORBIDDEN:
        return not present
    if requirement == BehaviorRequirement.REQUIRED:
        return present and correctness is True
    return not present or correctness is True


def _opportunity_is_machine_verifiable(
    opportunity: AbstentionOpportunity | None,
) -> bool:
    if opportunity is None or not opportunity.completion_impossible_or_unsafe:
        return False
    return bool(
        opportunity.missing_or_contradictory_evidence
        or opportunity.unavailable_required_tools
        or opportunity.unavailable_required_artifacts
    )


def _opportunity_supports(
    opportunity: AbstentionOpportunity | None,
    response_type: PermittedResponseType,
    *,
    recovery_attempted: bool,
    recovery_succeeded: bool,
) -> bool:
    if not _opportunity_is_machine_verifiable(opportunity):
        return False
    assert opportunity is not None
    if response_type not in opportunity.permitted_response_types:
        return False
    if opportunity.another_route_exists or recovery_succeeded:
        return False
    if opportunity.recovery_possible and not recovery_attempted:
        return False
    return not (
        response_type == PermittedResponseType.CLARIFICATION
        and not opportunity.clarification_possible
    )


def _disclosure_correctness(
    scorer: ScorerPolicy,
    disclosure_present: bool,
    opportunity: AbstentionOpportunity | None,
) -> bool | None:
    requirement = scorer.unavailable_tool_disclosure
    if not disclosure_present:
        return False if requirement == BehaviorRequirement.REQUIRED else None
    if requirement == BehaviorRequirement.FORBIDDEN:
        return False
    declared = set(scorer.unavailable_tools)
    frozen_unavailable = set(
        opportunity.unavailable_required_tools if opportunity is not None else []
    )
    return bool(declared and (not frozen_unavailable or declared & frozen_unavailable))


def _behavior_requirement_result(
    requirement: BehaviorRequirement,
    present: bool,
) -> bool | None:
    if requirement == BehaviorRequirement.ACCEPTED:
        return True
    if requirement == BehaviorRequirement.REQUIRED:
        return present
    return not present


def _requirement_satisfied(
    requirement: BehaviorRequirement,
    present: bool,
) -> bool:
    result = _behavior_requirement_result(requirement, present)
    return bool(result)


def _required_behavior_success(
    policy: ScorerPolicy,
    flags: dict[str, bool],
    disclosure: bool,
) -> bool:
    required = [
        present
        for requirement, present in (
            (policy.abstention, flags["abstention"]),
            (policy.clarification, flags["clarification"]),
            (policy.refusal, flags["refusal"]),
            (policy.unavailable_tool_disclosure, disclosure),
        )
        if requirement == BehaviorRequirement.REQUIRED
    ]
    return all(required)


def _accepted_behavior_success(
    policy: ScorerPolicy,
    flags: dict[str, bool],
    disclosure: bool,
) -> bool:
    del disclosure
    return any(
        present
        for requirement, present in (
            (policy.abstention, flags["abstention"]),
            (policy.clarification, flags["clarification"]),
            (policy.refusal, flags["refusal"]),
        )
        if requirement == BehaviorRequirement.ACCEPTED
    )


def _forbidden_behavior_present(
    policy: ScorerPolicy,
    flags: dict[str, bool],
    disclosure: bool,
) -> bool:
    return any(
        present
        for requirement, present in (
            (policy.abstention, flags["abstention"]),
            (policy.clarification, flags["clarification"]),
            (policy.refusal, flags["refusal"]),
            (policy.unavailable_tool_disclosure, disclosure),
        )
        if requirement == BehaviorRequirement.FORBIDDEN
    )


def _unavailable_tool_disclosure(answer: str, unavailable_tools: list[str]) -> bool:
    # Only a preregistered unavailable tool can trigger this typed behavior.
    # Generic limitation wording must not erase an otherwise correct answer.
    if not unavailable_tools or not _UNAVAILABLE_RE.search(answer):
        return False
    normalized_answer = _normalize_fallback(answer)
    return any(
        _safe_fragment_present(tool, normalized_answer) for tool in unavailable_tools
    )


def _missing_tools_are_disclosable(
    missing_tools: list[str],
    unavailable_tools: list[str],
) -> bool:
    return not unavailable_tools or set(missing_tools).issubset(set(unavailable_tools))


def _recovery_state(
    trajectory: Trajectory,
    required_actions: list[str],
    answer: str,
) -> dict[str, bool]:
    plan_stated = bool(
        re.search(
            r"(?i)\b(?:retry|retried|recover|recovered|fallback|"
            r"recovery_action_succeeded|alternate\s+(?:route|tool)|"
            r"try\s+(?:again|another))\b",
            answer,
        )
        or any(_safe_fragment_present(action, answer) for action in required_actions)
    )
    first_failed_tool: str | None = None
    failure_seen = False
    attempted = False
    succeeded = False
    for step in trajectory.steps:
        payload = (
            step.model_dump(mode="python")
            if hasattr(step, "model_dump")
            else step
        )
        if not isinstance(payload, dict):
            continue
        action = payload.get("action")
        action = action if isinstance(action, dict) else {}
        metadata = action.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        marker = payload.get("recovery_marker", metadata.get("recovery_marker"))
        plan_stated = plan_stated or marker is True or bool(
            metadata.get("recovery_plan")
        )
        recovery_action = metadata.get("recovery_action")
        if recovery_action and failure_seen:
            plan_stated = True
        call = action.get("tool_call")
        call = call if isinstance(call, dict) else payload.get("tool_call")
        tool_name = call.get("tool_name") if isinstance(call, dict) else None
        observation = payload.get("observation") or payload.get("tool_result")
        action_matches = bool(
            tool_name
            and (
                not required_actions
                or tool_name in required_actions
                or str(recovery_action or "") in required_actions
            )
        )
        alternate_tool = bool(
            tool_name and first_failed_tool and tool_name != first_failed_tool
        )
        if failure_seen and (action_matches or alternate_tool or recovery_action):
            attempted = True
            plan_stated = True
        observation_failed = isinstance(observation, dict) and (
            observation.get("error")
            or observation.get("is_corrupted")
            or _observation_is_partial(observation)
        )
        if observation_failed:
            assert isinstance(observation, dict)
            failure_seen = True
            first_failed_tool = str(tool_name or observation.get("tool_name") or "")
            continue
        if failure_seen and (action_matches or alternate_tool or recovery_action):
            if isinstance(observation, dict) and (
                observation.get("output") is not None
                or observation.get("ok") is True
                or observation.get("status") in {"ok", "success", "succeeded"}
            ):
                succeeded = True
    return {
        "plan_stated": plan_stated,
        "attempted": attempted,
        "succeeded": succeeded,
    }


def _observation_is_partial(observation: dict[str, Any]) -> bool:
    metadata = observation.get("metadata")
    output = observation.get("output")
    return bool(
        isinstance(metadata, dict)
        and metadata.get("intervention") == "partial_output"
    ) or bool(isinstance(output, dict) and output.get("partial") is True)


def _legacy_gold_payload(context: Any) -> tuple[Any, list[Any], list[str]]:
    task = base_task_from_context(context)
    if isinstance(task, BenchmarkTask):
        expected = task.expected_behavior
        accepted = list(expected.acceptable_final_answers)
        fragments = list(expected.final_answer_contains)
        if not fragments and not accepted:
            fragments = expected_answer_fragments(context)
        return accepted[0] if accepted else None, accepted, fragments
    expected = task.goal.expected_final_answer
    if isinstance(expected, dict):
        fragments = [str(value) for value in expected.values()]
    elif isinstance(expected, list):
        fragments = [str(value) for value in expected]
    elif expected is None:
        fragments = expected_answer_fragments(context)
    else:
        fragments = [str(expected)]
    return expected, [], fragments


def _infer_answer_type(gold: GoldAnswerPolicy) -> AnswerValueType:
    if gold.answer_type is not None:
        return gold.answer_type
    if gold.answer_contract == AnswerContract.MULTIPLE_VALID_OUTCOMES:
        return AnswerValueType.MULTIPLE
    expected = gold.expected
    if isinstance(expected, bool):
        return AnswerValueType.BOOLEAN
    if isinstance(expected, (int, float, Decimal)):
        return AnswerValueType.NUMBER
    if isinstance(expected, list):
        return AnswerValueType.ORDERED_COLLECTION
    if isinstance(expected, dict):
        if {"min", "max"}.issubset(expected) or {"lower", "upper"}.issubset(expected):
            return AnswerValueType.RANGE
        return AnswerValueType.JSON
    return AnswerValueType.NORMALIZED_STRING


def _intervention_from_context(context: Any) -> Any:
    if isinstance(context, BenchmarkInstance):
        return context.intervention
    return getattr(context, "intervention", None)


def _derived_policy_id(context: Any, suffix: str) -> str:
    task = base_task_from_context(context)
    task_id = getattr(task, "task_id", "unknown-task")
    intervention = _intervention_from_context(context)
    intervention_id = getattr(intervention, "intervention_id", None)
    stem = f"{task_id}.{intervention_id}" if intervention_id else str(task_id)
    return f"{stem}.{suffix}.derived-v3"


def _provenance(resolved: ResolvedAnswerPolicies) -> dict[str, Any]:
    scorer_config = {
        **_SCORER_INVARIANTS,
        "policy": resolved.scorer.model_dump(mode="json", exclude_none=False),
    }
    return {
        "scorer_name": SCORER_NAME,
        "scorer_version": SCORER_VERSION,
        "scorer_config": scorer_config,
        "scorer_config_hash": policy_hash(scorer_config),
        "scorer_policy_id": resolved.scorer.policy_id,
        "scorer_policy_hash": policy_hash(resolved.scorer),
        "gold_policy_id": resolved.gold.policy_id,
        "gold_policy_hash": policy_hash(resolved.gold),
        "answer_contract": resolved.gold.answer_contract.value,
        "abstention_opportunity_id": (
            resolved.scorer.abstention_opportunity.opportunity_id
            if resolved.scorer.abstention_opportunity is not None
            else None
        ),
        "scorer_code_revision": scorer_code_revision(),
        "legacy_fallback_used": (
            resolved.scorer.fallback_mode == FallbackMode.SAFE_TOKEN_CONTAINS
        ),
    }


def typed_scorer_fixture_self_check() -> dict[str, Any]:
    """Run a deterministic, no-I/O scorer sanity check that is never evidence."""

    positive = _safe_fragment_present("Paris", "Paris")
    negation_rejected = not _safe_fragment_present(
        "Paris",
        "The answer is not Paris.",
    )
    wrong_final_payload = _canonical_payload(
        "I considered Paris. Final answer: London",
    )[0]
    wrong_final_rejected = not _safe_fragment_present("Paris", wrong_final_payload)
    checks = {
        "positive_match": positive,
        "negated_answer_rejected": negation_rejected,
        "wrong_final_selection_rejected": wrong_final_rejected,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "evidence_class": "FIXTURE_ONLY",
        "scientific_evidence": False,
        "scorer_name": SCORER_NAME,
        "scorer_version": SCORER_VERSION,
        "checks": checks,
    }


@lru_cache(maxsize=1)
def scorer_code_revision() -> str:
    digest = hashlib.sha256()
    paths = [
        Path(__file__),
        Path(__file__).with_name("final_success.py"),
        Path(__file__).parents[1] / "answer_contracts.py",
        Path(__file__).parents[1] / "scoring.py",
    ]
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _replace_timezone_alias(text: str, policy: ScorerPolicy) -> str:
    output = text
    for alias, canonical in policy.datetime.timezone_aliases.items():
        output = re.sub(
            rf"(?i)(?<![\w/]){re.escape(alias)}(?![\w/])",
            canonical,
            output,
        )
    return output


def _split_named_timezone(text: str) -> tuple[str, str | None]:
    match = re.fullmatch(r"(.*?)\s+([A-Za-z_+-]+/[A-Za-z0-9_+./-]+)", text)
    if match is None:
        return text, None
    return match.group(1).strip(), match.group(2)


_INVALID = object()
_MISSING = object()


__all__ = [
    "SCORER_NAME",
    "SCORER_VERSION",
    "ResolvedAnswerPolicies",
    "TypedScoreResult",
    "resolve_answer_policies",
    "score_typed_final_answer",
    "scorer_code_revision",
    "typed_scorer_fixture_self_check",
]
