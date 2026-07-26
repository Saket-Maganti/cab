from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from statistics import mean
from typing import Any

NEAR_ZERO_CLEAN_THRESHOLD = 0.05
MATCHED_UNIT_FIELDS = (
    "agent_name",
    "model_name",
    "base_task_id",
    "intervention_id_or_family",
    "repeat_id",
)
EVIDENCE_CLASSES = {
    "DESIGN_ONLY",
    "ENGINEERING_ONLY",
    "FIXTURE_ONLY",
    "HUMAN_INPUT_REQUIRED",
    "EXECUTION_PENDING",
    "PRELIMINARY_REAL_EVIDENCE",
    "AUDITED_REAL_EVIDENCE",
    "PAPER_ELIGIBLE_EVIDENCE",
}


def success_rate(rows: list[dict[str, Any]]) -> float | None:
    values = [
        value
        for row in rows
        if (value := _success_value(row)) is not None
    ]
    return round(mean(values), 6) if values else None


def acrs(
    intervention_success_rate: float | None,
    clean_success_rate: float | None,
) -> float | None:
    """Return the raw ACRS ratio.

    This low-level helper retains its historical behaviour for callers that
    intentionally want a ratio. The production aggregate uses
    :func:`denominator_policy` and suppresses zero or near-zero denominators.
    """

    if (
        clean_success_rate is None
        or clean_success_rate == 0.0
        or intervention_success_rate is None
    ):
        return None
    return round(intervention_success_rate / clean_success_rate, 6)


def denominator_policy(
    clean_success_rate: float | None,
    *,
    n_pairs: int,
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, Any]:
    """Describe whether a clean-success denominator supports a stable ratio."""

    if near_zero_threshold < 0.0 or near_zero_threshold >= 1.0:
        raise ValueError("near_zero_threshold must be in [0, 1)")
    if n_pairs == 0 or clean_success_rate is None:
        state = "missing_clean_condition"
    elif clean_success_rate == 0.0:
        state = "zero_clean_success"
    elif clean_success_rate <= near_zero_threshold:
        state = "near_zero_clean_success"
    else:
        state = "stable"
    return {
        "state": state,
        "ratio_reportable": state == "stable",
        "near_zero_threshold": near_zero_threshold,
        "n_pairs": n_pairs,
    }


def degradation(
    clean_success_rate: float | None,
    intervention_success_rate: float | None,
) -> dict[str, float | None]:
    score = acrs(intervention_success_rate, clean_success_rate)
    absolute = (
        round(clean_success_rate - intervention_success_rate, 6)
        if clean_success_rate is not None and intervention_success_rate is not None
        else None
    )
    relative = round(1 - score, 6) if score is not None else None
    return {
        "absolute_degradation": absolute,
        "relative_degradation": relative,
    }


def matched_pair_outcomes(
    rows: list[dict[str, Any]],
    *,
    evidence_class: str = "FIXTURE_ONLY",
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, dict[str, Any]]:
    """Construct an explicit, auditable clean/intervention pair ledger.

    A clean observation is indexed by ``(agent/model, base_task_id, repeat_id)``.
    Every intervention adds ``intervention_id`` (or family when no ID exists).
    A clean row may therefore be the comparator for multiple intervention
    variants, but duplicate rows for the *same* unit are never averaged.

    Missing, duplicate, or malformed units remain in ``invalid_pairs`` with a
    reason. Only ``complete_pairs`` may enter downstream metrics or inference.
    """

    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError(
            f"unknown evidence_class {evidence_class!r}; "
            f"expected one of {sorted(EVIDENCE_CLASSES)}"
        )
    # Validate the threshold even when rows is empty.
    denominator_policy(
        None,
        n_pairs=0,
        near_zero_threshold=near_zero_threshold,
    )

    normalized = [_normalize_row(row, index=index) for index, row in enumerate(rows)]
    by_subject: dict[tuple[str, str | None], list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        by_subject[(row["agent_name"], row["model_name"])].append(row)

    subjects_per_agent: dict[str, int] = Counter(
        agent for agent, _model in by_subject
    )
    output: dict[str, dict[str, Any]] = {}
    for (agent, model), subject_rows in sorted(
        by_subject.items(),
        key=lambda item: (item[0][0], item[0][1] or ""),
    ):
        label = (
            agent
            if subjects_per_agent[agent] == 1
            else f"{agent}::{model or 'model_unspecified'}"
        )
        complete, invalid = _match_subject_rows(
            subject_rows,
            evidence_class=evidence_class,
        )
        output[label] = {
            "agent_name": agent,
            "model_name": model,
            "matched_unit_fields": list(MATCHED_UNIT_FIELDS),
            "repeat_policy": (
                "Use explicit repeat_id/repeat/seed when present; otherwise use "
                "implicit repeat 0. Multiple observations at an implicit or explicit "
                "repeat are invalid duplicates, never averaged."
            ),
            "complete_pairs": complete,
            "invalid_pairs": invalid,
            "pairing_summary": _pairing_summary(
                subject_rows,
                complete,
                invalid,
            ),
            "evidence_class": evidence_class,
            "fixture_only_not_evidence": evidence_class == "FIXTURE_ONLY",
            "scientific_evidence": evidence_class
            in {
                "PRELIMINARY_REAL_EVIDENCE",
                "AUDITED_REAL_EVIDENCE",
                "PAPER_ELIGIBLE_EVIDENCE",
            },
        }
    return output


def agent_robustness(
    rows: list[dict[str, Any]],
    *,
    evidence_class: str = "FIXTURE_ONLY",
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, dict[str, Any]]:
    """Aggregate robustness exclusively from valid, explicitly matched pairs."""

    ledgers = matched_pair_outcomes(
        rows,
        evidence_class=evidence_class,
        near_zero_threshold=near_zero_threshold,
    )
    output: dict[str, dict[str, Any]] = {}
    for label, ledger in ledgers.items():
        complete = ledger["complete_pairs"]
        summary = summarize_complete_pairs(
            complete,
            near_zero_threshold=near_zero_threshold,
        )
        raw_subject_rows = [
            row
            for row in rows
            if str(row.get("agent_name") or row.get("agent_id") or "unknown")
            == ledger["agent_name"]
            and _model_name(row) == ledger["model_name"]
        ]
        raw_clean = [
            row for row in raw_subject_rows if _condition(row) == "clean"
        ]
        raw_intervention = [
            row for row in raw_subject_rows if _condition(row) == "intervention"
        ]
        output[label] = {
            **summary,
            "agent_name": ledger["agent_name"],
            "model_name": ledger["model_name"],
            "n_trajectories": len(raw_subject_rows),
            "raw_unpaired_clean_success_rate": success_rate(raw_clean),
            "raw_unpaired_intervention_success_rate": success_rate(
                raw_intervention
            ),
            "pair_outcomes": complete,
            "invalid_pairs": ledger["invalid_pairs"],
            "pairing_summary": ledger["pairing_summary"],
            "matched_unit_fields": ledger["matched_unit_fields"],
            "repeat_policy": ledger["repeat_policy"],
            "evidence_class": ledger["evidence_class"],
            "fixture_only_not_evidence": ledger[
                "fixture_only_not_evidence"
            ],
            "scientific_evidence": ledger["scientific_evidence"],
        }
    return output


def paired_metrics_fixture_self_check() -> dict[str, Any]:
    """Run a tiny no-I/O fixture proving matched family denominators.

    The fixture is intentionally asymmetric: the agent-global clean rate is
    2/3, while the ``tool_failure`` family corresponds only to two base tasks
    whose clean rate is 1/2. A pooled-denominator regression therefore cannot
    pass this check accidentally.
    """

    def fixture_row(
        base_task_id: str,
        condition: str,
        success: int,
        family: str | None = None,
    ) -> dict[str, Any]:
        return {
            "instance_id": (
                f"{base_task_id}.clean"
                if condition == "clean"
                else f"{base_task_id}.{family}"
            ),
            "agent_name": "fixture_agent",
            "metrics": {"final_success_binary": success},
            "diagnostics": {
                "condition": condition,
                "base_task_id": base_task_id,
                "intervention_family": family,
                "repeat_id": 0,
            },
            "metadata": {
                "synthetic_fixture": True,
                "scientific_evidence": False,
            },
        }

    rows = [
        fixture_row("t1", "clean", 1),
        fixture_row("t2", "clean", 0),
        fixture_row("t3", "clean", 1),
        fixture_row("t1", "intervention", 0, "tool_failure"),
        fixture_row("t2", "intervention", 0, "tool_failure"),
        fixture_row("t3", "intervention", 1, "memory_corruption"),
    ]
    result = agent_robustness(
        rows,
        evidence_class="FIXTURE_ONLY",
    )["fixture_agent"]
    tool_family = result["families"]["tool_failure"]
    checks = {
        "three_complete_pairs": result["n_pairs"] == 3,
        "no_invalid_pairs": (
            result["pairing_summary"]["invalid_pair_count"] == 0
        ),
        "global_clean_rate_is_two_thirds": (
            result["clean_success_rate"] == 0.666667
        ),
        "tool_family_clean_rate_is_exact_half": (
            tool_family["clean_success_rate"] == 0.5
        ),
        "tool_family_not_using_global_clean_rate": (
            tool_family["clean_success_rate"]
            != result["clean_success_rate"]
        ),
        "fixture_only_label_preserved": (
            result["evidence_class"] == "FIXTURE_ONLY"
            and result["scientific_evidence"] is False
        ),
    }
    return {
        "check_id": "phase5_matched_family_denominator_fixture_v1",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "global_clean_success_rate": result[
                "clean_success_rate"
            ],
            "tool_family_clean_success_rate": tool_family[
                "clean_success_rate"
            ],
            "tool_family_intervention_success_rate": tool_family[
                "intervention_success_rate"
            ],
        },
        "evidence_class": "FIXTURE_ONLY",
        "scientific_evidence": False,
    }


def summarize_complete_pairs(
    pairs: list[dict[str, Any]],
    *,
    near_zero_threshold: float = NEAR_ZERO_CLEAN_THRESHOLD,
) -> dict[str, Any]:
    """Summarize a list of validated pair records."""

    clean_values = [float(pair["clean_success"]) for pair in pairs]
    intervention_values = [
        float(pair["intervention_success"]) for pair in pairs
    ]
    clean_rate_raw = mean(clean_values) if clean_values else None
    intervention_rate_raw = (
        mean(intervention_values) if intervention_values else None
    )
    clean_rate = (
        round(clean_rate_raw, 6) if clean_rate_raw is not None else None
    )
    intervention_rate = (
        round(intervention_rate_raw, 6)
        if intervention_rate_raw is not None
        else None
    )
    denominator = denominator_policy(
        clean_rate,
        n_pairs=len(pairs),
        near_zero_threshold=near_zero_threshold,
    )
    score = (
        acrs(intervention_rate, clean_rate)
        if denominator["ratio_reportable"]
        else None
    )
    absolute = (
        round(clean_rate_raw - intervention_rate_raw, 6)
        if clean_rate_raw is not None
        and intervention_rate_raw is not None
        else None
    )
    relative = round(1.0 - score, 6) if score is not None else None

    clean_success_pairs = [
        pair for pair in pairs if pair["clean_success"] == 1
    ]
    conditional = _mean_or_none(
        [
            float(pair["intervention_success"])
            for pair in clean_success_pairs
        ]
    )
    transitions = Counter(pair["transition"] for pair in pairs)
    transition_profile = {
        name: {
            "count": transitions.get(name, 0),
            "rate": (
                round(transitions.get(name, 0) / len(pairs), 6)
                if pairs
                else None
            ),
        }
        for name in (
            "success_to_success",
            "success_to_failure",
            "failure_to_success",
            "failure_to_failure",
        )
    }

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        by_family[pair["intervention_family"]].append(pair)
    families: dict[str, dict[str, Any]] = {}
    for family, family_pairs in sorted(by_family.items()):
        family_summary = summarize_complete_pairs(
            family_pairs,
            near_zero_threshold=near_zero_threshold,
        ) if len(by_family) > 1 else _summarize_family_without_recursion(
            family_pairs,
            near_zero_threshold=near_zero_threshold,
        )
        families[family] = {
            "n": len(family_pairs),
            "unique_base_task_count": len(
                {pair["base_task_id"] for pair in family_pairs}
            ),
            "clean_success_rate": family_summary["clean_success_rate"],
            "success_rate": family_summary[
                "intervention_success_rate"
            ],
            "intervention_success_rate": family_summary[
                "intervention_success_rate"
            ],
            "acrs_family": family_summary["acrs"],
            "absolute_degradation": family_summary[
                "absolute_degradation"
            ],
            "relative_degradation": family_summary[
                "relative_degradation"
            ],
            "conditional_robustness_among_clean_successes": family_summary[
                "conditional_robustness_among_clean_successes"
            ],
            "transition_profile": family_summary["transition_profile"],
            "denominator_policy": family_summary["denominator_policy"],
        }

    family_ratios = [
        family["acrs_family"]
        for family in families.values()
        if family["acrs_family"] is not None
    ]
    family_clean_conditioned = [
        family["conditional_robustness_among_clean_successes"]
        for family in families.values()
        if family["conditional_robustness_among_clean_successes"]
        is not None
    ]
    recovery_values = [
        float(pair["recovery_success"])
        for pair in pairs
        if pair["recovery_success"] is not None
    ]
    correct_abstention_values = [
        float(pair["correct_abstention"])
        for pair in pairs
        if pair["correct_abstention"] is not None
    ]
    false_abstention_values = [
        float(pair["false_abstention"])
        for pair in pairs
        if pair["false_abstention"] is not None
    ]
    return {
        "clean_success_rate": clean_rate,
        "intervention_success_rate": intervention_rate,
        "acrs": score,
        "micro_acrs": score,
        "macro_acrs": _mean_or_none(family_ratios),
        "macro_acrs_reportable_family_count": len(family_ratios),
        "macro_acrs_excluded_family_count": len(families)
        - len(family_ratios),
        "family_macro_clean_conditioned_robustness": _mean_or_none(
            family_clean_conditioned
        ),
        "family_macro_clean_conditioned_reportable_family_count": len(
            family_clean_conditioned
        ),
        "family_macro_clean_conditioned_excluded_family_count": (
            len(families) - len(family_clean_conditioned)
        ),
        "absolute_degradation": absolute,
        "paired_absolute_degradation": absolute,
        "relative_degradation": relative,
        "conditional_robustness_among_clean_successes": conditional,
        "conditional_degradation_among_clean_successes": (
            round(1.0 - conditional, 6)
            if conditional is not None
            else None
        ),
        "conditional_clean_success_denominator": len(
            clean_success_pairs
        ),
        "worst_family_robustness": (
            min(family_ratios) if family_ratios else None
        ),
        "worst_family_acrs": (
            min(family_ratios) if family_ratios else None
        ),
        "worst_family_clean_conditioned_robustness": (
            min(family_clean_conditioned)
            if family_clean_conditioned
            else None
        ),
        "families": families,
        "transition_profile": transition_profile,
        "recovery_success_rate": _mean_or_none(recovery_values),
        "recovery_observed_pair_count": len(recovery_values),
        "correct_abstention_rate": _mean_or_none(
            correct_abstention_values
        ),
        "correct_abstention_observed_pair_count": len(
            correct_abstention_values
        ),
        "false_abstention_rate": _mean_or_none(
            false_abstention_values
        ),
        "false_abstention_observed_pair_count": len(
            false_abstention_values
        ),
        "n_pairs": len(pairs),
        "unique_base_task_count": len(
            {pair["base_task_id"] for pair in pairs}
        ),
        "template_count": len(
            {
                pair["template_id"]
                for pair in pairs
                if pair["template_id"] is not None
            }
        ),
        "domain_count": len(
            {
                pair["domain"]
                for pair in pairs
                if pair["domain"] is not None
            }
        ),
        "family_count": len(families),
        "clustering_unit": "base_task_id",
        "denominator_policy": denominator,
    }


def _summarize_family_without_recursion(
    pairs: list[dict[str, Any]],
    *,
    near_zero_threshold: float,
) -> dict[str, Any]:
    clean_rate = _mean_or_none(
        [float(pair["clean_success"]) for pair in pairs]
    )
    intervention_rate = _mean_or_none(
        [float(pair["intervention_success"]) for pair in pairs]
    )
    denominator = denominator_policy(
        clean_rate,
        n_pairs=len(pairs),
        near_zero_threshold=near_zero_threshold,
    )
    score = (
        acrs(intervention_rate, clean_rate)
        if denominator["ratio_reportable"]
        else None
    )
    conditional_pairs = [
        pair for pair in pairs if pair["clean_success"] == 1
    ]
    conditional = _mean_or_none(
        [
            float(pair["intervention_success"])
            for pair in conditional_pairs
        ]
    )
    transitions = Counter(pair["transition"] for pair in pairs)
    return {
        "clean_success_rate": clean_rate,
        "intervention_success_rate": intervention_rate,
        "acrs": score,
        "absolute_degradation": (
            round(clean_rate - intervention_rate, 6)
            if clean_rate is not None and intervention_rate is not None
            else None
        ),
        "relative_degradation": (
            round(1.0 - score, 6) if score is not None else None
        ),
        "conditional_robustness_among_clean_successes": conditional,
        "transition_profile": {
            name: {
                "count": transitions.get(name, 0),
                "rate": (
                    round(transitions.get(name, 0) / len(pairs), 6)
                    if pairs
                    else None
                ),
            }
            for name in (
                "success_to_success",
                "success_to_failure",
                "failure_to_success",
                "failure_to_failure",
            )
        },
        "denominator_policy": denominator,
    }


def _match_subject_rows(
    rows: list[dict[str, Any]],
    *,
    evidence_class: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    clean: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    interventions: dict[
        tuple[str, str, str],
        list[dict[str, Any]],
    ] = defaultdict(list)
    invalid: list[dict[str, Any]] = []

    for row in rows:
        row_reasons = list(row["normalization_errors"])
        condition = row["condition"]
        if condition not in {"clean", "intervention"}:
            row_reasons.append("unknown_condition")
        if row["base_task_id"] is None:
            row_reasons.append("missing_base_task_id")
        if row["success"] is None:
            row_reasons.append("missing_or_nonbinary_success")
        if condition == "intervention" and row["intervention_scope"] is None:
            row_reasons.append("missing_intervention_id_or_family")
        if row_reasons:
            invalid.append(_invalid_record(row, row_reasons))
            continue
        base_repeat = (row["base_task_id"], row["repeat_id"])
        if condition == "clean":
            clean[base_repeat].append(row)
        else:
            interventions[
                (
                    row["base_task_id"],
                    row["repeat_id"],
                    row["intervention_scope"],
                )
            ].append(row)

    complete: list[dict[str, Any]] = []
    matched_clean_keys: set[tuple[str, str]] = set()
    for intervention_key, intervention_rows in sorted(
        interventions.items()
    ):
        base_task_id, repeat_id, _scope = intervention_key
        clean_key = (base_task_id, repeat_id)
        clean_rows = clean.get(clean_key, [])
        reasons = []
        if len(intervention_rows) > 1:
            reasons.append("duplicate_intervention_run")
        if not clean_rows:
            reasons.append("missing_clean_condition")
        elif len(clean_rows) > 1:
            reasons.append("duplicate_clean_run")
        if reasons:
            invalid.append(
                _invalid_group_record(
                    intervention_rows,
                    clean_rows,
                    reasons,
                )
            )
            continue
        clean_row = clean_rows[0]
        intervention_row = intervention_rows[0]
        matched_clean_keys.add(clean_key)
        complete.append(
            _complete_pair_record(
                clean_row,
                intervention_row,
                evidence_class=evidence_class,
            )
        )

    for clean_key, clean_rows in sorted(clean.items()):
        if clean_key in matched_clean_keys:
            continue
        has_intervention = any(
            key[:2] == clean_key for key in interventions
        )
        if has_intervention:
            # A duplicate-clean problem was already recorded against each
            # affected intervention unit.
            continue
        reasons = (
            ["duplicate_clean_run", "missing_intervention_condition"]
            if len(clean_rows) > 1
            else ["missing_intervention_condition"]
        )
        invalid.append(
            _invalid_group_record(
                [],
                clean_rows,
                reasons,
            )
        )

    complete.sort(
        key=lambda pair: (
            pair["base_task_id"],
            pair["repeat_id"],
            pair["intervention_id_or_family"],
        )
    )
    invalid.sort(
        key=lambda pair: (
            str(pair.get("base_task_id") or ""),
            str(pair.get("repeat_id") or ""),
            str(pair.get("intervention_id_or_family") or ""),
            ",".join(pair["invalid_pair_reasons"]),
        )
    )
    return complete, invalid


def _complete_pair_record(
    clean: dict[str, Any],
    intervention: dict[str, Any],
    *,
    evidence_class: str,
) -> dict[str, Any]:
    clean_success = int(clean["success"])
    intervention_success = int(intervention["success"])
    transition = {
        (1, 1): "success_to_success",
        (1, 0): "success_to_failure",
        (0, 1): "failure_to_success",
        (0, 0): "failure_to_failure",
    }[(clean_success, intervention_success)]
    recovery = intervention["recovery_success"]
    correct_abstention = intervention["correct_abstention"]
    false_abstention = intervention["false_abstention"]
    return {
        "pair_id": "|".join(
            (
                clean["agent_name"],
                clean["model_name"] or "model_unspecified",
                clean["base_task_id"],
                intervention["intervention_scope"],
                clean["repeat_id"],
            )
        ),
        "agent_name": clean["agent_name"],
        "model_name": clean["model_name"],
        "base_task_id": clean["base_task_id"],
        "intervention_id": intervention["intervention_id"],
        "intervention_id_or_family": intervention[
            "intervention_scope"
        ],
        "intervention_family": intervention[
            "intervention_family"
        ],
        "repeat_id": clean["repeat_id"],
        "repeat_id_source": clean["repeat_id_source"],
        "clean_success": clean_success,
        "intervention_success": intervention_success,
        "success_to_success": transition == "success_to_success",
        "success_to_failure": transition == "success_to_failure",
        "failure_to_success": transition == "failure_to_success",
        "failure_to_failure": transition == "failure_to_failure",
        "transition": transition,
        "absolute_degradation": clean_success - intervention_success,
        "relative_degradation": (
            clean_success - intervention_success
            if clean_success == 1
            else None
        ),
        "conditional_degradation": (
            1 - intervention_success if clean_success == 1 else None
        ),
        "recovery_success": recovery,
        "correct_abstention": correct_abstention,
        "false_abstention": false_abstention,
        "completeness_state": "complete",
        "invalid_pair_reason": None,
        "invalid_pair_reasons": [],
        "clean_source_row_index": clean["source_row_index"],
        "intervention_source_row_index": intervention[
            "source_row_index"
        ],
        "template_id": intervention["template_id"]
        or clean["template_id"],
        "domain": intervention["domain"] or clean["domain"],
        "evidence_class": evidence_class,
        "fixture_only_not_evidence": evidence_class == "FIXTURE_ONLY",
    }


def _invalid_record(
    row: dict[str, Any],
    reasons: Iterable[str],
) -> dict[str, Any]:
    unique_reasons = sorted(set(reasons))
    return {
        "pair_id": None,
        "agent_name": row["agent_name"],
        "model_name": row["model_name"],
        "base_task_id": row["base_task_id"],
        "intervention_id": row["intervention_id"],
        "intervention_id_or_family": row["intervention_scope"],
        "intervention_family": row["intervention_family"],
        "repeat_id": row["repeat_id"],
        "completeness_state": "invalid",
        "invalid_pair_reason": unique_reasons[0],
        "invalid_pair_reasons": unique_reasons,
        "source_row_indices": [row["source_row_index"]],
    }


def _invalid_group_record(
    intervention_rows: list[dict[str, Any]],
    clean_rows: list[dict[str, Any]],
    reasons: Iterable[str],
) -> dict[str, Any]:
    rows = intervention_rows or clean_rows
    representative = rows[0]
    unique_reasons = sorted(set(reasons))
    return {
        "pair_id": None,
        "agent_name": representative["agent_name"],
        "model_name": representative["model_name"],
        "base_task_id": representative["base_task_id"],
        "intervention_id": (
            intervention_rows[0]["intervention_id"]
            if intervention_rows
            else None
        ),
        "intervention_id_or_family": (
            intervention_rows[0]["intervention_scope"]
            if intervention_rows
            else None
        ),
        "intervention_family": (
            intervention_rows[0]["intervention_family"]
            if intervention_rows
            else None
        ),
        "repeat_id": representative["repeat_id"],
        "completeness_state": "invalid",
        "invalid_pair_reason": unique_reasons[0],
        "invalid_pair_reasons": unique_reasons,
        "source_row_indices": sorted(
            row["source_row_index"]
            for row in clean_rows + intervention_rows
        ),
    }


def _pairing_summary(
    input_rows: list[dict[str, Any]],
    complete: list[dict[str, Any]],
    invalid: list[dict[str, Any]],
) -> dict[str, Any]:
    reason_counts = Counter(
        reason
        for pair in invalid
        for reason in pair["invalid_pair_reasons"]
    )
    implicit_repeat_rows = sum(
        row["repeat_id_source"] == "implicit_single_repeat"
        for row in input_rows
    )
    return {
        "input_row_count": len(input_rows),
        "complete_pair_count": len(complete),
        "invalid_pair_count": len(invalid),
        "invalid_pair_reason_counts": dict(sorted(reason_counts.items())),
        "pairing_complete": bool(complete) and not invalid,
        "unique_base_task_count": len(
            {pair["base_task_id"] for pair in complete}
        ),
        "intervention_pair_count": len(complete),
        "template_count": len(
            {
                pair["template_id"]
                for pair in complete
                if pair["template_id"] is not None
            }
        ),
        "domain_count": len(
            {
                pair["domain"]
                for pair in complete
                if pair["domain"] is not None
            }
        ),
        "family_count": len(
            {pair["intervention_family"] for pair in complete}
        ),
        "clustering_unit": "base_task_id",
        "implicit_repeat_row_count": implicit_repeat_rows,
    }


def _normalize_row(row: dict[str, Any], *, index: int) -> dict[str, Any]:
    agent = str(
        _first_present(
            row,
            ("agent_name", "agent_id", "model_name"),
        )
        or "unknown"
    )
    model = _model_name(row)
    condition = _condition(row)
    base_task = _first_present(
        row,
        ("base_task_id", "diagnostic_base_task_id"),
        nested=(("diagnostics", "base_task_id"), ("metadata", "base_task_id")),
    )
    repeat, repeat_source = _repeat_id(row)
    intervention_id = _first_present(
        row,
        ("intervention_id", "diagnostic_intervention_id"),
        nested=(
            ("diagnostics", "intervention_id"),
            ("metadata", "intervention_id"),
        ),
    )
    family = _first_present(
        row,
        (
            "intervention_family",
            "diagnostic_intervention_family",
        ),
        nested=(
            ("diagnostics", "intervention_family"),
            ("metadata", "intervention_family"),
        ),
    )
    instance_id = _first_present(row, ("instance_id",))
    if condition == "intervention" and intervention_id is None:
        # Score records have historically omitted intervention_id from
        # diagnostics while retaining an explicit intervention instance_id.
        intervention_id = instance_id
    scope = intervention_id or family
    normalized_family = (
        str(family)
        if family is not None
        else (
            f"intervention:{intervention_id}"
            if intervention_id is not None
            else None
        )
    )
    return {
        "source_row_index": index,
        "agent_name": agent,
        "model_name": model,
        "condition": str(condition) if condition is not None else None,
        "base_task_id": str(base_task) if base_task is not None else None,
        "repeat_id": repeat,
        "repeat_id_source": repeat_source,
        "intervention_id": (
            str(intervention_id)
            if intervention_id is not None
            else None
        ),
        "intervention_scope": (
            str(scope) if scope is not None else None
        ),
        "intervention_family": normalized_family,
        "success": _success_value(row),
        "recovery_success": _optional_binary(
            row,
            (
                "recovery_success",
                "recovery_success_binary",
                "tool_error_recovery_binary",
            ),
        ),
        "correct_abstention": _correct_abstention(row),
        "false_abstention": _false_abstention(row),
        "template_id": _optional_text(
            row,
            ("template_id", "diagnostic_template_id"),
            nested=(
                ("diagnostics", "template_id"),
                ("metadata", "template_id"),
            ),
        ),
        "domain": _optional_text(
            row,
            ("domain", "diagnostic_domain"),
            nested=(
                ("diagnostics", "domain"),
                ("metadata", "domain"),
            ),
        ),
        "normalization_errors": [],
    }


def _success_value(row: dict[str, Any]) -> float | None:
    value = _first_present(
        row,
        ("final_success_binary", "success"),
        nested=(("metrics", "final_success_binary"),),
    )
    return _binary(value)


def _binary(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)) and value in (0, 1):
        return float(value)
    return None


def _optional_binary(
    row: dict[str, Any],
    keys: tuple[str, ...],
) -> bool | None:
    nested = tuple(("metrics", key) for key in keys)
    value = _first_present(row, keys, nested=nested)
    binary = _binary(value)
    return bool(binary) if binary is not None else None


def _correct_abstention(row: dict[str, Any]) -> bool | None:
    explicit = _optional_binary(
        row,
        (
            "correct_abstention_binary",
            "correct_abstention_uncertainty_binary",
        ),
    )
    if explicit is not None:
        return explicit
    required = _first_present(
        row,
        ("abstention_required",),
        nested=(("diagnostics", "abstention_required"),),
    )
    abstained = _first_present(
        row,
        ("abstained", "abstention_binary"),
        nested=(
            ("metrics", "abstention_binary"),
            ("diagnostics", "abstained"),
        ),
    )
    if required is True and _binary(abstained) is not None:
        return bool(_binary(abstained))
    return None


def _false_abstention(row: dict[str, Any]) -> bool | None:
    explicit = _optional_binary(
        row,
        ("false_abstention_binary",),
    )
    if explicit is not None:
        return explicit
    required = _first_present(
        row,
        ("abstention_required",),
        nested=(("diagnostics", "abstention_required"),),
    )
    abstained = _first_present(
        row,
        ("abstained", "abstention_binary"),
        nested=(
            ("metrics", "abstention_binary"),
            ("diagnostics", "abstained"),
        ),
    )
    if required is False and _binary(abstained) is not None:
        return bool(_binary(abstained))
    return None


def _repeat_id(row: dict[str, Any]) -> tuple[str, str]:
    candidates = (
        ("repeat_id", "explicit_repeat_id"),
        ("diagnostic_repeat_id", "explicit_repeat_id"),
        ("repeat", "explicit_repeat"),
        ("metadata_repeat_id", "metadata_repeat_id"),
        ("metadata_repeat", "metadata_repeat"),
        ("seed", "seed"),
        ("metadata_seed", "metadata_seed"),
    )
    for key, source in candidates:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return str(value), source
    for container, key, source in (
        ("diagnostics", "repeat_id", "diagnostic_repeat_id"),
        ("diagnostics", "repeat", "diagnostic_repeat"),
        ("metadata", "repeat_id", "metadata_repeat_id"),
        ("metadata", "repeat", "metadata_repeat"),
        ("metadata", "seed", "metadata_seed"),
    ):
        payload = row.get(container)
        if isinstance(payload, dict):
            value = payload.get(key)
            if value is not None and str(value).strip() != "":
                return str(value), source
    return "0", "implicit_single_repeat"


def _model_name(row: dict[str, Any]) -> str | None:
    value = _first_present(
        row,
        ("model_name", "metadata_model_name", "metadata_model"),
        nested=(
            ("metadata", "model_name"),
            ("metadata", "model"),
            ("provider_model_metadata", "model_name"),
            ("provider_model_metadata", "model"),
        ),
    )
    if value is None or str(value).strip() == "":
        return None
    return str(value)


def _condition(row: dict[str, Any]) -> str | None:
    value = _first_present(
        row,
        ("condition", "diagnostic_condition"),
        nested=(("diagnostics", "condition"),),
    )
    return str(value) if value is not None else None


def _optional_text(
    row: dict[str, Any],
    keys: tuple[str, ...],
    *,
    nested: tuple[tuple[str, str], ...] = (),
) -> str | None:
    value = _first_present(row, keys, nested=nested)
    if value is None or str(value).strip() == "":
        return None
    return str(value)


def _first_present(
    row: dict[str, Any],
    keys: tuple[str, ...],
    *,
    nested: tuple[tuple[str, str], ...] = (),
) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    for container, key in nested:
        payload = row.get(container)
        if isinstance(payload, dict):
            value = payload.get(key)
            if value is not None:
                return value
    return None


def _mean_or_none(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None
