from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from causal_agent_bench.analysis.load_results import RunResults
from causal_agent_bench.utils.io import write_json, write_jsonl

UNCERTAINTY_WORDS = {
    "uncertain",
    "unable",
    "cannot",
    "can't",
    "limitation",
    "error",
    "failed",
    "failure",
    "ambiguous",
    "clarify",
    "clarification",
    "not enough",
    "insufficient",
}

CONFLICT_WORDS = {
    "conflict",
    "contradiction",
    "contradict",
    "inconsistent",
    "disagree",
}

SEMANTIC_ARGUMENT_ERRORS = {
    "empty_result",
    "not_found",
    "no_match",
    "semantic_mismatch",
    "wrong_entity",
    "wrong_record",
    "wrong_filter",
    "out_of_scope",
}

PARSER_MALFORMED_STATUSES = {
    "invalid_json",
    "invalid_argument_schema",
    "multiple_tool_calls",
    "missing_action",
}

SECRET_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|password|secret|token)\s*[:=]\s*['\"]?[^'\"\s,}]+"
)
SECRET_VALUE_RE = re.compile(r"\b(sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9_-]{32,}\.[A-Za-z0-9_-]{16,})\b")


@dataclass(frozen=True)
class ErrorTaxonomyEntry:
    slug: str
    label: str
    description: str
    expected_behavior: str
    scoring_notes: str


ERROR_TAXONOMY: tuple[ErrorTaxonomyEntry, ...] = (
    ErrorTaxonomyEntry(
        "wrong_tool_selected",
        "Wrong tool selected",
        "The trajectory calls an unavailable, irrelevant, or non-required tool when the task needed a different tool.",
        "Choose tools that are available and causally relevant to the requested evidence.",
        "Mined from unavailable-tool calls, non-required calls, and tool precision below 1.0.",
    ),
    ErrorTaxonomyEntry(
        "required_tool_omitted",
        "Required tool omitted",
        "The trajectory stops or answers without calling one or more required tools.",
        "Call every required evidence-gathering tool before answering, unless the task explicitly permits abstention.",
        "Mined from missing required-tool counts and required-tool recall.",
    ),
    ErrorTaxonomyEntry(
        "tool_argument_malformed",
        "Tool argument malformed",
        "A tool call has syntactically invalid, schema-invalid, or unparsable arguments.",
        "Construct arguments that satisfy the declared tool-call schema.",
        "Mined from parser outcomes, invalid-argument observations, and argument-error counts.",
    ),
    ErrorTaxonomyEntry(
        "tool_argument_semantically_wrong",
        "Tool argument semantically wrong",
        "A tool call is well formed but points to the wrong entity, filter, query, or task-specific value.",
        "Use arguments that refer to the requested entity and preserve the user's constraints.",
        "Mined from semantic/no-match tool errors, empty results after required calls, and mismatch metadata.",
    ),
    ErrorTaxonomyEntry(
        "observation_ignored",
        "Observation ignored",
        "The trajectory obtains relevant observations but the final answer or later actions do not use them.",
        "Ground the final answer in observations actually returned by tools.",
        "Mined from expected fragments present in observations but absent from the final answer, plus low trajectory faithfulness.",
    ),
    ErrorTaxonomyEntry(
        "contradiction_missed",
        "Contradiction missed",
        "A conflict is present in the task or observations, but the trajectory does not notice it.",
        "Explicitly detect conflicting observations or intervention-induced contradictions.",
        "Mined from contradiction-family rows or conflict text with no contradiction-detection marker.",
    ),
    ErrorTaxonomyEntry(
        "contradiction_noticed_but_unresolved",
        "Contradiction noticed but unresolved",
        "The trajectory acknowledges a conflict but does not resolve, verify, or abstain.",
        "After noticing a contradiction, resolve it with evidence or report calibrated uncertainty.",
        "Mined from contradiction detected=true and contradiction resolved=false.",
    ),
    ErrorTaxonomyEntry(
        "blind_trust_in_corrupted_memory",
        "Blind trust in corrupted memory",
        "The trajectory relies on memory in a memory-corruption setting without verification.",
        "Verify memory against a reliable tool or explicitly discount stale/corrupted memory.",
        "Mined from memory-corruption rows, memory-use markers, and failed memory-verification metrics.",
    ),
    ErrorTaxonomyEntry(
        "failure_to_recover_from_tool_error",
        "Failure to recover from tool error",
        "A tool returns an error, corruption, or partial result and the agent neither retries appropriately nor adapts.",
        "Recover by fixing arguments, choosing another tool, or abstaining with uncertainty.",
        "Mined from tool-error recovery=false after an error/corruption observation.",
    ),
    ErrorTaxonomyEntry(
        "repeated_failed_calls",
        "Repeated failed calls",
        "The same failing call pattern is repeated without a meaningful change.",
        "Change the call, switch tools, or stop with uncertainty after a failed call.",
        "Mined from repeated failed-call counts and repeated failed tool+argument signatures.",
    ),
    ErrorTaxonomyEntry(
        "premature_stopping",
        "Premature stopping",
        "The agent stops before gathering required evidence or before the task can be supported.",
        "Continue until required evidence has been gathered or a principled abstention is warranted.",
        "Mined from premature-stop and final-answer-without-required-evidence indicators.",
    ),
    ErrorTaxonomyEntry(
        "overlong_inefficient_trajectory",
        "Overlong/inefficient trajectory",
        "The trajectory uses too many steps or calls relative to the required evidence.",
        "Use a concise evidence path and avoid redundant calls once enough support is available.",
        "Mined from low efficiency, max-step failures, long trajectories, and high call counts.",
    ),
    ErrorTaxonomyEntry(
        "hallucinated_tool_result",
        "Hallucinated tool result",
        "The final answer attributes facts to tools that were not returned in the observations.",
        "Only report tool results that appear in the trajectory observations.",
        "Mined from tool-result claims without matching observations and from unsupported confident answers.",
    ),
    ErrorTaxonomyEntry(
        "final_answer_unsupported_by_trajectory",
        "Final answer unsupported by trajectory",
        "The final answer is not supported by the evidence actually gathered in the trajectory.",
        "Make final answers traceable to the obtained tool observations.",
        "Mined from trajectory_success=false, low faithfulness, and final answer support checks.",
    ),
    ErrorTaxonomyEntry(
        "correct_final_answer_via_invalid_trajectory",
        "Correct final answer via invalid trajectory",
        "The final answer is correct, but the trajectory used invalid calls, omitted required tools, or otherwise failed process checks.",
        "Treat final-answer correctness as insufficient when the path is invalid or unsupported.",
        "Mined from final_success=true paired with trajectory/process failures.",
    ),
    ErrorTaxonomyEntry(
        "uncertainty_failure",
        "Uncertainty failure",
        "The agent should express uncertainty or limitation but gives an overconfident answer.",
        "Use calibrated uncertainty when evidence is missing, corrupted, contradictory, ambiguous, or errored.",
        "Mined from failure/corruption/ambiguity contexts with confident final answers.",
    ),
    ErrorTaxonomyEntry(
        "clarification_failure",
        "Clarification failure",
        "The task needs clarification, but the agent proceeds or stops without asking for it.",
        "Ask a clarification question when the instruction is ambiguous and cannot be resolved from tools.",
        "Mined from ambiguous-instruction rows without clarification actions and with failed outcomes.",
    ),
    ErrorTaxonomyEntry(
        "excessive_tool_overuse",
        "Excessive tool overuse",
        "The trajectory overuses unnecessary or irrelevant tools beyond a small inefficiency.",
        "Avoid irrelevant tools and stop once the needed evidence has been collected.",
        "Mined from high unnecessary-tool-call rates and repeated non-required calls.",
    ),
)

TAXONOMY_BY_SLUG = {entry.slug: entry for entry in ERROR_TAXONOMY}

LEGACY_CATEGORY_ALIASES = {
    "final_success_trajectory_failure": "correct_final_answer_via_invalid_trajectory",
    "tool_failure_not_recovered": "failure_to_recover_from_tool_error",
    "memory_corruption_blind_trust": "blind_trust_in_corrupted_memory",
    "observation_conflict_missed": "contradiction_missed",
    "premature_success": "premature_stopping",
    "overuse_irrelevant_tools": "excessive_tool_overuse",
    "invalid_tool_arguments": "tool_argument_malformed",
    "max_step_failure": "overlong_inefficient_trajectory",
    "unstated_uncertainty": "uncertainty_failure",
    "tool_corruption_not_detected": "failure_to_recover_from_tool_error",
}

CATEGORY_DESCRIPTIONS = {
    entry.slug: entry.description
    for entry in ERROR_TAXONOMY
} | {
    "clean_succeeds_intervention_fails": "The same agent succeeds on the clean base task but fails on an intervention variant.",
    **{
        alias: f"Backward-compatible alias for `{target}`."
        for alias, target in LEGACY_CATEGORY_ALIASES.items()
    },
}

FILTER_DESCRIPTIONS = {
    "final_success_trajectory_failure": "Final answer succeeded but trajectory/process scoring failed.",
    "clean_succeeds_intervention_fails": "The same agent succeeded on the clean base task but failed on an intervention variant.",
    "model_a_succeeds_model_b_fails": "At least one model/agent succeeded on an instance where another model/agent failed.",
    "high_cost_low_quality": "High-cost or long trajectories with low final/trajectory quality.",
}


def extract_error_cases(data: RunResults, output_dir: str | Path, *, max_cases: int = 5) -> list[Path]:
    """Backward-compatible wrapper that now writes a full failure gallery."""

    return generate_failure_gallery(data, output_dir, max_cases=max_cases, include_legacy_aliases=True)


def generate_failure_gallery(
    data: RunResults,
    output_dir: str | Path,
    *,
    max_cases: int = 5,
    include_filters: bool = True,
    include_legacy_aliases: bool = False,
) -> list[Path]:
    """Write taxonomy-grouped failure examples and paper-ready qualitative snippets."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    taxonomy_cases = mine_error_taxonomy(data, max_cases=max_cases)
    paths: list[Path] = []

    taxonomy_path = out / "taxonomy.json"
    write_json(
        taxonomy_path,
        {
            "taxonomy": [
                {
                    "slug": entry.slug,
                    "label": entry.label,
                    "description": entry.description,
                    "expected_behavior": entry.expected_behavior,
                    "scoring_notes": entry.scoring_notes,
                }
                for entry in ERROR_TAXONOMY
            ],
            "caveat": (
                "These deterministic mined labels are audit aids, not final scientific evidence "
                "until provider-backed runs and human validation are complete."
            ),
        },
    )
    paths.append(taxonomy_path)

    for category, cases in taxonomy_cases.items():
        jsonl_path = out / f"{category}.jsonl"
        md_path = out / f"{category}.md"
        write_jsonl(jsonl_path, cases)
        md_path.write_text(_cases_to_markdown(category, cases), encoding="utf-8")
        paths.extend([jsonl_path, md_path])

    if include_legacy_aliases:
        for alias, target in LEGACY_CATEGORY_ALIASES.items():
            cases = [dict(case, category=alias, taxonomy_error_type=target) for case in taxonomy_cases.get(target, [])]
            jsonl_path = out / f"{alias}.jsonl"
            md_path = out / f"{alias}.md"
            write_jsonl(jsonl_path, cases)
            md_path.write_text(_cases_to_markdown(alias, cases), encoding="utf-8")
            paths.extend([jsonl_path, md_path])

    if include_filters:
        filter_dir = out / "filters"
        filter_dir.mkdir(parents=True, exist_ok=True)
        filtered = mine_filtered_cases(data, max_cases=max_cases)
        for filter_name, cases in filtered.items():
            jsonl_path = filter_dir / f"{filter_name}.jsonl"
            md_path = filter_dir / f"{filter_name}.md"
            write_jsonl(jsonl_path, cases)
            md_path.write_text(_filter_cases_to_markdown(filter_name, cases), encoding="utf-8")
            paths.extend([jsonl_path, md_path])

    qualitative_path = out / "qualitative_examples.md"
    qualitative_path.write_text(_qualitative_examples_markdown(taxonomy_cases), encoding="utf-8")
    paths.append(qualitative_path)

    index_text = _gallery_index_markdown(taxonomy_cases, data, include_filters=include_filters)
    for name in ["README.md", "index.md"]:
        path = out / name
        path.write_text(index_text, encoding="utf-8")
        paths.append(path)

    return paths


def mine_error_cases(data: RunResults, *, max_cases: int = 5) -> dict[str, list[dict[str, Any]]]:
    """Return taxonomy cases plus legacy aliases used by older docs/tests."""

    taxonomy_cases = mine_error_taxonomy(data, max_cases=max_cases)
    cases: dict[str, list[dict[str, Any]]] = dict(taxonomy_cases)
    cases["clean_succeeds_intervention_fails"] = mine_filtered_cases(
        data,
        filters=["clean_succeeds_intervention_fails"],
        max_cases=max_cases,
    )["clean_succeeds_intervention_fails"]
    for alias, target in LEGACY_CATEGORY_ALIASES.items():
        cases[alias] = [
            dict(case, category=alias, taxonomy_error_type=target)
            for case in taxonomy_cases.get(target, [])
        ]
    return cases


def mine_error_taxonomy(data: RunResults, *, max_cases: int = 5) -> dict[str, list[dict[str, Any]]]:
    """Mine the 18-item error taxonomy from trajectory logs and score records."""

    rows = _score_rows(data)
    mined: dict[str, list[dict[str, Any]]] = {entry.slug: [] for entry in ERROR_TAXONOMY}
    if not rows:
        return mined

    for row in rows:
        trajectory = _find_trajectory(data, row)
        context = _find_context(data, row)
        signals = _error_signals(row, trajectory, context)
        for slug, signal in signals.items():
            case = _case_payload(
                data,
                row,
                category=slug,
                taxonomy_entry=TAXONOMY_BY_SLUG[slug],
                signal=signal,
                trajectory=trajectory,
                context=context,
            )
            mined[slug].append(case)

    return {
        slug: _rank_cases(cases)[:max_cases]
        for slug, cases in mined.items()
    }


def mine_filtered_cases(
    data: RunResults,
    *,
    filters: list[str] | None = None,
    max_cases: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    selected = filters or list(FILTER_DESCRIPTIONS)
    rows = _score_rows(data)
    results: dict[str, list[dict[str, Any]]] = {name: [] for name in selected}
    if not rows:
        return results

    for filter_name in selected:
        if filter_name == "final_success_trajectory_failure":
            candidates = [
                row
                for row in rows
                if _truthy(row.get("final_success_binary")) and not _truthy(row.get("trajectory_success_binary"))
            ]
            results[filter_name] = [
                _case_payload(
                    data,
                    row,
                    category=filter_name,
                    signal={"trigger": "final_success=1 and trajectory_success=0"},
                )
                for row in _sort_rows(candidates)
            ][:max_cases]
        elif filter_name == "clean_succeeds_intervention_fails":
            candidates = _clean_succeeds_intervention_fails(rows)
            results[filter_name] = [
                _case_payload(
                    data,
                    row,
                    category=filter_name,
                    signal={"trigger": "clean success paired with intervention failure"},
                )
                for row in _sort_rows(candidates)
            ][:max_cases]
        elif filter_name == "model_a_succeeds_model_b_fails":
            results[filter_name] = _model_contrast_cases(data, rows, max_cases=max_cases)
        elif filter_name == "high_cost_low_quality":
            results[filter_name] = _high_cost_low_quality_cases(data, rows, max_cases=max_cases)
        else:
            results[filter_name] = []

    return results


def _error_signals(row: dict[str, Any], trajectory: Any, context: Any) -> dict[str, dict[str, Any]]:
    required = set(_required_tools(context))
    optional = set(_optional_tools(context))
    available = set(_available_tools(context))
    tool_calls = _tool_calls(trajectory)
    call_names = [str(call.get("tool_name")) for call in tool_calls if call.get("tool_name")]
    call_counter = Counter(call_names)
    non_required_calls = [
        name for name in call_names if name not in required and name not in optional
    ]
    unavailable_calls = [name for name in call_names if available and name not in available]
    observations = _observations(trajectory)
    observation_text = _observations_text(trajectory)
    final_answer = str(_trajectory_final_answer(trajectory) or "")
    final_answer_lc = final_answer.lower()
    expected_fragments = _expected_answer_fragments(context)
    signals: dict[str, dict[str, Any]] = {}

    invalid_tool_count = _number(row.get("invalid_tool_call_count"), 0)
    missing_required_count = _number(row.get("missing_required_tool_count"), 0)
    argument_error_count = _number(row.get("argument_error_count"), 0)
    unnecessary_rate = _number(row.get("unnecessary_tool_call_rate"), 0.0)
    required_recall = _number(row.get("required_tool_recall"), 1.0)
    tool_precision = _number(row.get("tool_precision"), 1.0)
    trajectory_faithfulness = _number(row.get("trajectory_faithfulness"), 1.0)
    trajectory_efficiency = _number(row.get("trajectory_efficiency"), 1.0)

    if unavailable_calls or invalid_tool_count > 0 or (non_required_calls and (missing_required_count > 0 or tool_precision < 1)):
        signals["wrong_tool_selected"] = {
            "unavailable_calls": sorted(set(unavailable_calls)),
            "non_required_calls": sorted(set(non_required_calls)),
            "tool_precision": tool_precision,
        }

    if missing_required_count > 0 or required_recall < 1:
        signals["required_tool_omitted"] = {
            "missing_required_tool_count": missing_required_count,
            "required_tools": sorted(required),
            "called_tools": call_names,
        }

    malformed_steps = _malformed_argument_steps(trajectory)
    if argument_error_count > 0 or malformed_steps:
        signals["tool_argument_malformed"] = {
            "argument_error_count": argument_error_count,
            "steps": malformed_steps,
        }

    semantic_steps = _semantic_argument_steps(trajectory, required)
    if semantic_steps:
        signals["tool_argument_semantically_wrong"] = {
            "steps": semantic_steps,
        }

    expected_in_observation = [
        fragment for fragment in expected_fragments if fragment and fragment.lower() in observation_text
    ]
    expected_missing_from_answer = [
        fragment for fragment in expected_in_observation if fragment.lower() not in final_answer_lc
    ]
    if expected_missing_from_answer or (
        observations
        and not _truthy(row.get("final_success_binary"))
        and trajectory_faithfulness < 0.5
        and not _has_uncertainty(final_answer)
    ):
        signals["observation_ignored"] = {
            "expected_fragments_seen_but_missing": expected_missing_from_answer[:8],
            "trajectory_faithfulness": trajectory_faithfulness,
        }

    family = row.get("diagnostic_intervention_family")
    conflict_present = family == "observation_conflict" or any(word in observation_text for word in CONFLICT_WORDS)
    if conflict_present and not _truthy(row.get("contradiction_detected_binary")):
        signals["contradiction_missed"] = {
            "intervention_family": family,
            "contradiction_detected_binary": row.get("contradiction_detected_binary"),
        }
    if conflict_present and _truthy(row.get("contradiction_detected_binary")) and not _truthy(row.get("contradiction_resolved_binary")):
        signals["contradiction_noticed_but_unresolved"] = {
            "contradiction_detected_binary": row.get("contradiction_detected_binary"),
            "contradiction_resolved_binary": row.get("contradiction_resolved_binary"),
        }

    if (
        _truthy(row.get("memory_blind_trust_failure_binary"))
        or (
            family == "memory_corruption"
            and _truthy(row.get("memory_used_binary"))
            and not _truthy(row.get("memory_verified_binary"))
        )
    ):
        signals["blind_trust_in_corrupted_memory"] = {
            "memory_used_binary": row.get("memory_used_binary"),
            "memory_verified_binary": row.get("memory_verified_binary"),
        }

    has_tool_error = any(_is_error_observation(obs) for obs in observations)
    if has_tool_error and row.get("tool_error_recovery_binary") is False:
        signals["failure_to_recover_from_tool_error"] = {
            "tool_error_recovery_binary": row.get("tool_error_recovery_binary"),
            "failed_steps": _failed_step_summaries(trajectory),
        }

    repeated_failed = _number(row.get("repeated_failed_call_count"), 0)
    repeated_signatures = _repeated_failed_call_signatures(trajectory)
    if repeated_failed > 0 or repeated_signatures:
        signals["repeated_failed_calls"] = {
            "repeated_failed_call_count": repeated_failed,
            "repeated_signatures": repeated_signatures,
        }

    if _truthy(row.get("premature_stop_binary")) or _has_parser_status(trajectory, "final_answer_without_required_evidence"):
        signals["premature_stopping"] = {
            "premature_stop_binary": row.get("premature_stop_binary"),
            "missing_required_tool_count": missing_required_count,
        }

    max_step_failure = _truthy(row.get("max_step_failure_binary"))
    if max_step_failure or trajectory_efficiency <= 0.5 or _is_overlong(trajectory, context):
        signals["overlong_inefficient_trajectory"] = {
            "trajectory_efficiency": trajectory_efficiency,
            "max_step_failure_binary": row.get("max_step_failure_binary"),
            "n_steps": len(_steps(trajectory)),
            "n_tool_calls": len(call_names),
        }

    if final_answer and _hallucinated_tool_result(final_answer, observation_text, observations):
        signals["hallucinated_tool_result"] = {
            "final_answer": _truncate(final_answer, 240),
            "observation_count": len(observations),
        }

    if final_answer and (not _truthy(row.get("trajectory_success_binary")) or trajectory_faithfulness < 1):
        signals["final_answer_unsupported_by_trajectory"] = {
            "trajectory_success_binary": row.get("trajectory_success_binary"),
            "trajectory_faithfulness": trajectory_faithfulness,
        }

    invalid_process = bool(
        signals.keys()
        & {
            "wrong_tool_selected",
            "required_tool_omitted",
            "tool_argument_malformed",
            "tool_argument_semantically_wrong",
            "failure_to_recover_from_tool_error",
            "premature_stopping",
            "hallucinated_tool_result",
            "final_answer_unsupported_by_trajectory",
        }
    )
    if _truthy(row.get("final_success_binary")) and invalid_process:
        signals["correct_final_answer_via_invalid_trajectory"] = {
            "final_success_binary": row.get("final_success_binary"),
            "invalid_process_signals": sorted(signals),
        }

    uncertainty_context = (
        has_tool_error
        or family in {"tool_removal", "tool_failure", "tool_corruption", "observation_conflict", "ambiguous_instruction"}
        or missing_required_count > 0
        or not _truthy(row.get("final_success_binary"))
    )
    if uncertainty_context and final_answer and not _has_uncertainty(final_answer) and not _asked_clarification(trajectory):
        signals["uncertainty_failure"] = {
            "intervention_family": family,
            "has_tool_error": has_tool_error,
            "final_success_binary": row.get("final_success_binary"),
        }

    if (
        family == "ambiguous_instruction"
        and not _asked_clarification(trajectory)
        and not _truthy(row.get("final_success_binary"))
    ):
        signals["clarification_failure"] = {
            "intervention_family": family,
            "clarification_present": False,
        }

    excessive_call_count = sum(count - 1 for name, count in call_counter.items() if name in non_required_calls and count > 1)
    if unnecessary_rate >= 0.5 or excessive_call_count >= 2 or (family == "irrelevant_tools" and unnecessary_rate > 0):
        signals["excessive_tool_overuse"] = {
            "unnecessary_tool_call_rate": unnecessary_rate,
            "repeated_non_required_calls": excessive_call_count,
        }

    return signals


def _case_payload(
    data: RunResults,
    row: dict[str, Any],
    *,
    category: str,
    taxonomy_entry: ErrorTaxonomyEntry | None = None,
    signal: dict[str, Any] | None = None,
    trajectory: Any = None,
    context: Any = None,
) -> dict[str, Any]:
    trajectory = trajectory if trajectory is not None else _find_trajectory(data, row)
    context = context if context is not None else _find_context(data, row)
    instance_id = row.get("instance_id")
    agent = row.get("agent_name")
    taxonomy_entry = taxonomy_entry or TAXONOMY_BY_SLUG.get(category)
    trajectory_summary = _trajectory_summary(trajectory)
    score_details = _score_details(row)
    actual_behavior = _actual_behavior(category, signal or {}, trajectory_summary, score_details)
    payload = {
        "category": category,
        "taxonomy_label": taxonomy_entry.label if taxonomy_entry else category.replace("_", " "),
        "taxonomy_description": taxonomy_entry.description if taxonomy_entry else CATEGORY_DESCRIPTIONS.get(category, ""),
        "task_id": row.get("diagnostic_base_task_id") or _context_base_task_id(context),
        "instance_id": instance_id,
        "run_id": row.get("run_id") or _trajectory_run_id(trajectory),
        "domain": _context_domain(context),
        "agent": agent,
        "model": _model_identifier(row, trajectory),
        "intervention_family": row.get("diagnostic_intervention_family") or _context_intervention_family(context),
        "condition": row.get("diagnostic_condition") or _context_condition(context),
        "available_tools": _available_tools(context),
        "required_tools": _required_tools(context),
        "user_instruction": _user_instruction(context),
        "expected_behavior": _expected_behavior_payload(context, taxonomy_entry),
        "actual_behavior": actual_behavior,
        "scoring_notes": _scoring_notes(context, taxonomy_entry, score_details, signal or {}),
        "trajectory_summary": trajectory_summary,
        "raw_trajectory_excerpt": _raw_trajectory_excerpt(trajectory, signal),
        "tool_calls": _tool_calls(trajectory),
        "observations": _observations(trajectory),
        "final_answer": _trajectory_final_answer(trajectory),
        "score_details": score_details,
        "metric_diagnosis": score_details,
        "signal": signal or {},
        "evidence": _evidence_metadata(data, row, trajectory),
        "paper_ready_qualitative_example": _paper_ready_example(category, actual_behavior, trajectory),
        "why_it_matters": _why_it_matters(category, row),
    }
    payload["_rank_score"] = _rank_score(payload)
    return _sanitize(payload)


def _score_rows(data: RunResults) -> list[dict[str, Any]]:
    if data.scores_df.empty:
        return []
    rows = data.scores_df.to_dict(orient="records")
    return [_normalize_row(row) for row in rows]


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: (None if _is_missing(value) else value) for key, value in row.items()}


def _clean_succeeds_intervention_fails(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean_success = {
        (row.get("agent_name"), row.get("diagnostic_base_task_id"))
        for row in rows
        if row.get("diagnostic_condition") == "clean" and _truthy(row.get("final_success_binary"))
    }
    return [
        row
        for row in rows
        if row.get("diagnostic_condition") == "intervention"
        and not _truthy(row.get("final_success_binary"))
        and (row.get("agent_name"), row.get("diagnostic_base_task_id")) in clean_success
    ]


def _model_contrast_cases(
    data: RunResults,
    rows: list[dict[str, Any]],
    *,
    max_cases: int,
) -> list[dict[str, Any]]:
    by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_instance[str(row.get("instance_id"))].append(row)

    cases = []
    for instance_rows in by_instance.values():
        successes = [row for row in instance_rows if _truthy(row.get("final_success_binary"))]
        failures = [row for row in instance_rows if not _truthy(row.get("final_success_binary"))]
        if not successes or not failures:
            continue
        successful_models = sorted({_model_identifier(row, _find_trajectory(data, row)) for row in successes})
        failed_models = sorted({_model_identifier(row, _find_trajectory(data, row)) for row in failures})
        for row in failures:
            cases.append(
                _case_payload(
                    data,
                    row,
                    category="model_a_succeeds_model_b_fails",
                    signal={
                        "successful_models": successful_models,
                        "failed_models": failed_models,
                    },
                )
            )
    return _rank_cases(cases)[:max_cases]


def _high_cost_low_quality_cases(
    data: RunResults,
    rows: list[dict[str, Any]],
    *,
    max_cases: int,
) -> list[dict[str, Any]]:
    costs = [
        _trajectory_cost(_find_trajectory(data, row))
        for row in rows
        if _trajectory_cost(_find_trajectory(data, row)) is not None
    ]
    positive_costs = [cost for cost in costs if cost is not None and cost > 0]
    cost_threshold = median(positive_costs) if positive_costs else None
    cases = []
    for row in rows:
        trajectory = _find_trajectory(data, row)
        context = _find_context(data, row)
        cost = _trajectory_cost(trajectory)
        low_quality = (
            not _truthy(row.get("final_success_binary"))
            or not _truthy(row.get("trajectory_success_binary"))
            or _number(row.get("trajectory_faithfulness"), 1.0) < 0.5
        )
        high_cost = (
            (cost is not None and cost_threshold is not None and cost >= cost_threshold and cost > 0)
            or _is_overlong(trajectory, context)
            or _number(row.get("trajectory_efficiency"), 1.0) <= 0.25
        )
        if low_quality and high_cost:
            cases.append(
                _case_payload(
                    data,
                    row,
                    category="high_cost_low_quality",
                    signal={
                        "estimated_cost_usd": cost,
                        "cost_threshold_usd": cost_threshold,
                        "trajectory_efficiency": row.get("trajectory_efficiency"),
                    },
                    trajectory=trajectory,
                    context=context,
                )
            )
    return _rank_cases(cases)[:max_cases]


def _find_trajectory(data: RunResults, row: dict[str, Any]) -> Any:
    run_id = row.get("run_id")
    instance_id = row.get("instance_id")
    agent = row.get("agent_name")
    for trajectory in data.trajectories:
        if (
            _trajectory_run_id(trajectory) == run_id
            and getattr(trajectory, "instance_id", None) == instance_id
            and getattr(trajectory, "agent_name", None) == agent
        ):
            return trajectory
    for trajectory in data.trajectories:
        if getattr(trajectory, "instance_id", None) == instance_id and getattr(trajectory, "agent_name", None) == agent:
            return trajectory
    return None


def _find_context(data: RunResults, row: dict[str, Any]) -> Any:
    instance_id = row.get("instance_id")
    for instance in data.instances:
        if instance.instance_id == instance_id:
            return instance
    for task in data.legacy_tasks:
        if task.task_id == instance_id:
            return task
    return None


def _rank_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(cases, key=lambda case: case.get("_rank_score", 0), reverse=True)
    for case in ranked:
        case.pop("_rank_score", None)
    return ranked


def _sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            _number(row.get("final_success_binary"), 0),
            -_number(row.get("trajectory_faithfulness"), 1.0),
            _number(row.get("missing_required_tool_count"), 0),
            _number(row.get("argument_error_count"), 0),
        ),
        reverse=True,
    )


def _rank_score(case: dict[str, Any]) -> float:
    scores = case.get("score_details", {})
    signal = case.get("signal", {})
    cost = case.get("evidence", {}).get("estimated_cost_usd")
    score = 0.0
    score += 4.0 if not _truthy(scores.get("final_success_binary")) else 1.0
    score += 4.0 if not _truthy(scores.get("trajectory_success_binary")) else 0.0
    score += 3.0 * (1 - _number(scores.get("trajectory_faithfulness"), 1.0))
    score += _number(scores.get("missing_required_tool_count"), 0)
    score += _number(scores.get("argument_error_count"), 0)
    score += _number(scores.get("invalid_tool_call_count"), 0)
    score += _number(scores.get("unnecessary_tool_call_rate"), 0.0)
    score += min(float(cost), 10.0) / 10.0 if isinstance(cost, (int, float)) else 0.0
    score += len(signal) * 0.05
    return round(score, 6)


def _tool_calls(trajectory: Any) -> list[dict[str, Any]]:
    if trajectory is None:
        return []
    calls = []
    for step in _steps(trajectory):
        call = _tool_call_from_step(step)
        if call:
            calls.append(call)
    return calls


def _observations(trajectory: Any) -> list[dict[str, Any]]:
    if trajectory is None:
        return []
    observations = []
    for step in _steps(trajectory):
        observation = _observation_from_step(step)
        if observation:
            observations.append(observation)
    return observations


def _trajectory_summary(trajectory: Any) -> list[str]:
    if trajectory is None:
        return []
    summary = []
    for step in _steps(trajectory):
        step_index = _step_index(step)
        call = _tool_call_from_step(step)
        observation = _observation_from_step(step)
        final_answer = _final_answer_from_step(step)
        if call:
            obs_error = observation.get("error") if observation else None
            corrupted = observation.get("is_corrupted") if observation else None
            summary.append(
                f"step {step_index}: call {call.get('tool_name')} error={obs_error} corrupted={corrupted}"
            )
        elif final_answer is not None:
            summary.append(f"step {step_index}: final answer")
    return summary


def _raw_trajectory_excerpt(trajectory: Any, signal: dict[str, Any] | None, *, limit: int = 6) -> list[dict[str, Any]]:
    if trajectory is None:
        return []
    steps = _steps(trajectory)
    signal_steps = set()
    for value in (signal or {}).values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and item.get("step_index") is not None:
                    signal_steps.add(int(item["step_index"]))
    selected: list[Any] = []
    for step in steps:
        if len(selected) >= limit and _step_index(step) not in signal_steps:
            continue
        selected.append(
            {
                "step_index": _step_index(step),
                "raw_model_output": _truncate(_raw_model_output_from_step(step), 800),
                "thought": _truncate(_action_from_step(step).get("thought"), 400),
                "tool_call": _tool_call_from_step(step),
                "observation": _compact(_observation_from_step(step)),
                "final_answer": _truncate(_final_answer_from_step(step), 400),
            }
        )
        if len(selected) >= limit and not signal_steps:
            break
    return selected


def _malformed_argument_steps(trajectory: Any) -> list[dict[str, Any]]:
    steps = []
    for step in _steps(trajectory):
        parser_status = str(_parser_status_from_step(step) or "")
        observation = _observation_from_step(step)
        if parser_status in PARSER_MALFORMED_STATUSES or (observation and observation.get("error") == "invalid_arguments"):
            steps.append(
                {
                    "step_index": _step_index(step),
                    "tool_name": (_tool_call_from_step(step) or {}).get("tool_name"),
                    "parser_status": parser_status,
                    "observation_error": observation.get("error") if observation else None,
                }
            )
    return steps


def _semantic_argument_steps(trajectory: Any, required_tools: set[str]) -> list[dict[str, Any]]:
    steps = []
    for step in _steps(trajectory):
        call = _tool_call_from_step(step)
        observation = _observation_from_step(step)
        if not call or not observation:
            continue
        error = str(observation.get("error") or "")
        metadata = _as_dict(observation.get("metadata"))
        output = observation.get("output")
        output_empty = (
            isinstance(output, dict)
            and any(key in output for key in ["results", "items", "records"])
            and not any(output.get(key) for key in ["results", "items", "records"])
        )
        metadata_signal = str(metadata.get("error_type") or metadata.get("diagnosis") or "")
        if (
            error in SEMANTIC_ARGUMENT_ERRORS
            or metadata_signal in SEMANTIC_ARGUMENT_ERRORS
            or (output_empty and call.get("tool_name") in required_tools)
        ):
            steps.append(
                {
                    "step_index": _step_index(step),
                    "tool_name": call.get("tool_name"),
                    "observation_error": error or None,
                    "metadata_signal": metadata_signal or None,
                }
            )
    return steps


def _failed_step_summaries(trajectory: Any) -> list[dict[str, Any]]:
    summaries = []
    for step in _steps(trajectory):
        observation = _observation_from_step(step)
        if observation and _is_error_observation(observation):
            summaries.append(
                {
                    "step_index": _step_index(step),
                    "tool_name": observation.get("tool_name") or (_tool_call_from_step(step) or {}).get("tool_name"),
                    "error": observation.get("error"),
                    "is_corrupted": observation.get("is_corrupted"),
                }
            )
    return summaries


def _repeated_failed_call_signatures(trajectory: Any) -> list[dict[str, Any]]:
    failed_signatures = []
    for step in _steps(trajectory):
        call = _tool_call_from_step(step)
        observation = _observation_from_step(step)
        if call and observation and _is_error_observation(observation):
            signature = (call.get("tool_name"), json.dumps(_sanitize(call.get("arguments", {})), sort_keys=True))
            failed_signatures.append(signature)
    counts = Counter(failed_signatures)
    return [
        {"tool_name": tool, "arguments": arguments, "count": count}
        for (tool, arguments), count in counts.items()
        if count > 1
    ]


def _has_parser_status(trajectory: Any, status: str) -> bool:
    return any(_parser_status_from_step(step) == status for step in _steps(trajectory))


def _asked_clarification(trajectory: Any) -> bool:
    if trajectory is None:
        return False
    for step in _steps(trajectory):
        parser_status = str(_parser_status_from_step(step) or "")
        action = _action_from_step(step)
        raw = " ".join(
            str(value or "")
            for value in [
                parser_status,
                action.get("thought"),
                action.get("final_answer"),
                _raw_model_output_from_step(step),
            ]
        ).lower()
        if "clarification" in parser_status or "clarify" in raw or "could you" in raw:
            return True
    return False


def _hallucinated_tool_result(final_answer: str, observation_text: str, observations: list[dict[str, Any]]) -> bool:
    answer_lc = final_answer.lower()
    if _has_uncertainty(answer_lc):
        return False
    claims_tool_result = any(
        phrase in answer_lc
        for phrase in [
            "tool returned",
            "tool result",
            "according to the tool",
            "according to the search",
            "database shows",
            "calendar shows",
            "result shows",
        ]
    )
    if claims_tool_result and not observations:
        return True
    if not claims_tool_result:
        return False
    answer_tokens = _salient_tokens(final_answer)
    observed_tokens = _salient_tokens(observation_text)
    unsupported_tokens = answer_tokens - observed_tokens
    return bool(unsupported_tokens and len(unsupported_tokens) >= min(2, len(answer_tokens)))


def _is_overlong(trajectory: Any, context: Any) -> bool:
    if trajectory is None:
        return False
    steps = _steps(trajectory)
    calls = _tool_calls(trajectory)
    max_steps = _context_max_steps(context)
    required_count = max(1, len(_required_tools(context)))
    if max_steps and len(steps) >= max_steps and not _has_final_success_metadata(trajectory):
        return True
    return len(calls) >= max(required_count * 3, required_count + 4)


def _observations_text(trajectory: Any) -> str:
    chunks = []
    for observation in _observations(trajectory):
        chunks.append(json.dumps(_sanitize(observation), sort_keys=True, default=str))
    return " ".join(chunks).lower()


def _expected_answer_fragments(context: Any) -> list[str]:
    values: list[str] = []
    if context is None:
        return values
    if hasattr(context, "base_task"):
        base = context.base_task
        _collect_fragments(getattr(base.goal, "expected_final_answer", None), values)
        _collect_fragments(getattr(base, "hidden_ground_truth", None), values)
    else:
        expected = getattr(context, "expected_behavior", None)
        _collect_fragments(getattr(expected, "acceptable_final_answers", None), values)
        _collect_fragments(getattr(expected, "final_answer_contains", None), values)
        _collect_fragments(getattr(context, "mock_data", None), values)
    return sorted({value.lower() for value in values if len(value) >= 2})


def _collect_fragments(value: Any, out: list[str]) -> None:
    if value is None:
        return
    if isinstance(value, (str, int, float, bool)):
        out.append(str(value))
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_fragments(item, out)
    elif isinstance(value, list):
        for item in value:
            _collect_fragments(item, out)


def _score_details(row: dict[str, Any]) -> dict[str, Any]:
    keys = {
        "final_success_binary",
        "final_success_partial",
        "trajectory_success_binary",
        "trajectory_faithfulness",
        "trajectory_efficiency",
        "required_tool_recall",
        "tool_precision",
        "invalid_tool_call_count",
        "argument_error_count",
        "argument_validity_rate",
        "unnecessary_tool_call_rate",
        "premature_stop_binary",
        "max_step_failure_binary",
        "missing_required_tool_count",
        "tool_error_recovery_binary",
        "steps_to_recovery",
        "repeated_failed_call_count",
        "contradiction_detected_binary",
        "contradiction_resolved_binary",
        "memory_used_binary",
        "memory_verified_binary",
        "memory_blind_trust_failure_binary",
    }
    return {key: row.get(key) for key in sorted(keys) if key in row}


def _expected_behavior_payload(context: Any, taxonomy_entry: ErrorTaxonomyEntry | None) -> dict[str, Any]:
    intervention = _context_intervention(context)
    return {
        "taxonomy_expected_behavior": taxonomy_entry.expected_behavior if taxonomy_entry else None,
        "success_criteria": _success_criteria(context),
        "required_information": _required_information(context),
        "required_tools": _required_tools(context),
        "expected_robust_behavior": getattr(intervention, "expected_robust_behavior", None) if intervention else None,
        "intervention_expected_behavior": getattr(intervention, "expected_behavior", None) if intervention else None,
    }


def _actual_behavior(
    category: str,
    signal: dict[str, Any],
    trajectory_summary: list[str],
    score_details: dict[str, Any],
) -> str:
    pieces = []
    if signal.get("trigger"):
        pieces.append(str(signal["trigger"]))
    if signal.get("invalid_process_signals"):
        pieces.append("Invalid process signals: " + ", ".join(signal["invalid_process_signals"]))
    if signal.get("missing_required_tool_count"):
        pieces.append(f"Missing required tools: {signal['missing_required_tool_count']}")
    if signal.get("failed_steps"):
        pieces.append(f"Failed tool observations: {len(signal['failed_steps'])}")
    if signal.get("unnecessary_tool_call_rate") is not None:
        pieces.append(f"Unnecessary tool-call rate: {signal['unnecessary_tool_call_rate']}")
    if score_details.get("trajectory_faithfulness") is not None:
        pieces.append(f"Trajectory faithfulness: {score_details['trajectory_faithfulness']}")
    if trajectory_summary:
        pieces.append("Trajectory: " + "; ".join(trajectory_summary[:4]))
    return " ".join(pieces) or f"Mined as `{category}` by deterministic trajectory heuristics."


def _scoring_notes(
    context: Any,
    taxonomy_entry: ErrorTaxonomyEntry | None,
    score_details: dict[str, Any],
    signal: dict[str, Any],
) -> dict[str, Any]:
    intervention = _context_intervention(context)
    return {
        "taxonomy_scoring_notes": taxonomy_entry.scoring_notes if taxonomy_entry else None,
        "intervention_scoring_notes": getattr(intervention, "scoring_notes", None) if intervention else None,
        "deterministic_score_details": score_details,
        "mining_signal": signal,
    }


def _evidence_metadata(data: RunResults, row: dict[str, Any], trajectory: Any) -> dict[str, Any]:
    metadata = data.run_metadata or {}
    config_raw = metadata.get("config")
    config = config_raw if isinstance(config_raw, dict) else {}
    provider_metadata = getattr(trajectory, "provider_model_metadata", {}) if trajectory is not None else {}
    token_metadata = getattr(trajectory, "token_cost_metadata", {}) if trajectory is not None else {}
    trajectory_metadata = getattr(trajectory, "metadata", {}) if trajectory is not None else {}
    return {
        "run_dir": str(data.run_dir),
        "run_id": row.get("run_id") or metadata.get("run_id") or _trajectory_run_id(trajectory),
        "config_path": metadata.get("config_path") or metadata.get("benchmark_location") or config.get("benchmark_path") or config.get("tasks_path"),
        "config_hash": metadata.get("config_hash"),
        "dataset_version": metadata.get("dataset_version"),
        "seed": trajectory_metadata.get("seed") or metadata.get("seed"),
        "model_id": _model_identifier(row, trajectory),
        "provider": provider_metadata.get("provider") or trajectory_metadata.get("provider"),
        "prompt_hash": provider_metadata.get("prompt_hash")
        or provider_metadata.get("prompt_version_hash")
        or trajectory_metadata.get("prompt_hash")
        or trajectory_metadata.get("prompt_version_hash"),
        "scorer_version": row.get("metadata_scorer"),
        "git_commit": metadata.get("git_commit"),
        "estimated_cost_usd": _trajectory_cost(trajectory),
        "token_usage": token_metadata.get("token_usage") or trajectory_metadata.get("token_usage"),
    }


def _paper_ready_example(category: str, actual_behavior: str, trajectory: Any) -> str:
    final_answer = _trajectory_final_answer(trajectory)
    excerpt = "; ".join(_trajectory_summary(trajectory)[:3])
    return (
        f"Candidate qualitative example for `{category}`: {actual_behavior} "
        f"Final answer: {final_answer!r}. Excerpt: {excerpt or 'no trajectory excerpt available'}."
    )


def _why_it_matters(category: str, row: dict[str, Any]) -> str:
    if category in {"final_answer_unsupported_by_trajectory", "correct_final_answer_via_invalid_trajectory"}:
        return "Final-answer scoring can hide process failures that matter for causal attribution."
    if category in {"failure_to_recover_from_tool_error", "repeated_failed_calls"}:
        return "Recovery from tool failure is a core robustness skill, not a clean-task success proxy."
    if category == "blind_trust_in_corrupted_memory":
        return "Blindly trusting corrupted memory undermines intervention validity and agent reliability."
    if category.startswith("contradiction"):
        return "Contradiction handling should be separable from ordinary task completion."
    if category in {"wrong_tool_selected", "required_tool_omitted", "tool_argument_malformed", "tool_argument_semantically_wrong"}:
        return "Tool-use component failures explain why success is not always agent skill."
    if category in {"uncertainty_failure", "clarification_failure"}:
        return "Robust agents should expose uncertainty when evidence is insufficient or ambiguous."
    if row.get("max_step_failure_binary"):
        return "Max-step or inefficient failures expose planning and stopping weaknesses."
    return "This case illustrates a component-level failure beyond aggregate success rate."


def _cases_to_markdown(category: str, cases: list[dict[str, Any]]) -> str:
    entry = TAXONOMY_BY_SLUG.get(category)
    title = entry.label if entry else category.replace("_", " ").title()
    description = entry.description if entry else CATEGORY_DESCRIPTIONS.get(category, "")
    lines = [
        f"# {title}",
        "",
        description,
        "",
        "> Deterministic mining labels are audit aids only. They should not be cited as final scientific evidence without human validation and provider-backed runs.",
        "",
    ]
    if not cases:
        lines.append("_No matching cases in this run._")
        return "\n".join(lines) + "\n"

    for case in cases:
        lines.extend(_case_markdown_lines(case))
    return "\n".join(lines).rstrip() + "\n"


def _filter_cases_to_markdown(filter_name: str, cases: list[dict[str, Any]]) -> str:
    lines = [
        f"# {filter_name.replace('_', ' ').title()}",
        "",
        FILTER_DESCRIPTIONS.get(filter_name, ""),
        "",
        "> Filtered examples are candidate audit packets, not final scientific evidence.",
        "",
    ]
    if not cases:
        lines.append("_No matching cases in this run._")
        return "\n".join(lines) + "\n"
    for case in cases:
        lines.extend(_case_markdown_lines(case))
    return "\n".join(lines).rstrip() + "\n"


def _case_markdown_lines(case: dict[str, Any]) -> list[str]:
    evidence = case.get("evidence", {})
    return [
        f"## {case.get('agent')} on {case.get('instance_id')}",
        "",
        f"- Task id: `{case.get('task_id')}`",
        f"- Run: `{evidence.get('run_id')}` in `{evidence.get('run_dir')}`",
        f"- Config/hash: `{evidence.get('config_path')}` / `{evidence.get('config_hash')}`",
        f"- Seed/model/prompt: `{evidence.get('seed')}` / `{evidence.get('model_id')}` / `{evidence.get('prompt_hash')}`",
        f"- Scorer/git: `{evidence.get('scorer_version')}` / `{evidence.get('git_commit')}`",
        f"- Domain: `{case.get('domain')}`",
        f"- Condition/family: `{case.get('condition')}` / `{case.get('intervention_family')}`",
        f"- Available tools: {', '.join(case.get('available_tools') or []) or 'none'}",
        f"- Required tools: {', '.join(case.get('required_tools') or []) or 'none'}",
        f"- User instruction: {case.get('user_instruction')}",
        "",
        "### Expected Behavior",
        "",
        _json_block(case.get("expected_behavior")),
        "",
        "### Actual Behavior",
        "",
        case.get("actual_behavior") or "",
        "",
        "### Raw Trajectory Excerpt",
        "",
        _json_block(case.get("raw_trajectory_excerpt")),
        "",
        "### Scoring Notes",
        "",
        _json_block(case.get("scoring_notes")),
        "",
        f"- Final answer: {case.get('final_answer')}",
        f"- Why it matters: {case.get('why_it_matters')}",
        "",
    ]


def _gallery_index_markdown(
    taxonomy_cases: dict[str, list[dict[str, Any]]],
    data: RunResults,
    *,
    include_filters: bool,
) -> str:
    metadata = data.run_metadata or {}
    lines = [
        "# Failure Gallery",
        "",
        "This gallery is mined from deterministic trajectory logs. It is designed for audit, qualitative case selection, and paper drafting; it is not final scientific evidence until human validation and real LLM-backed runs are complete.",
        "",
        "## Provenance",
        "",
        f"- Run directory: `{data.run_dir}`",
        f"- Run id: `{metadata.get('run_id')}`",
        f"- Config hash: `{metadata.get('config_hash')}`",
        f"- Dataset version: `{metadata.get('dataset_version')}`",
        f"- Git commit: `{metadata.get('git_commit')}`",
        "",
        "## Error Types",
        "",
    ]
    for entry in ERROR_TAXONOMY:
        lines.append(f"- [{entry.label}]({entry.slug}.md): {len(taxonomy_cases.get(entry.slug, []))} cases")
    if include_filters:
        lines.extend(["", "## Filters", ""])
        for name, description in FILTER_DESCRIPTIONS.items():
            lines.append(f"- [`{name}`](filters/{name}.md): {description}")
    return "\n".join(lines) + "\n"


def _qualitative_examples_markdown(taxonomy_cases: dict[str, list[dict[str, Any]]]) -> str:
    lines = [
        "# Paper-Ready Qualitative Example Candidates",
        "",
        "These are candidate qualitative examples selected from mined deterministic labels. Do not present them as final empirical results until the linked run artifacts are real provider-backed runs and the labels have human validation.",
        "",
    ]
    count = 0
    for entry in ERROR_TAXONOMY:
        cases = taxonomy_cases.get(entry.slug, [])
        if not cases:
            continue
        case = cases[0]
        lines.extend(
            [
                f"## {entry.label}",
                "",
                case.get("paper_ready_qualitative_example", ""),
                "",
                f"- Evidence: run `{case.get('evidence', {}).get('run_id')}`, instance `{case.get('instance_id')}`, agent `{case.get('agent')}`, config hash `{case.get('evidence', {}).get('config_hash')}`.",
                f"- Score details: `{case.get('score_details')}`",
                "",
            ]
        )
        count += 1
        if count >= 12:
            break
    if count == 0:
        lines.append("_No qualitative examples were mined from this run._")
    return "\n".join(lines).rstrip() + "\n"


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(_sanitize(value), indent=2, sort_keys=True, default=str) + "\n```"


def _context_intervention(context: Any) -> Any:
    return getattr(context, "intervention", None) if context is not None else None


def _context_intervention_family(context: Any) -> str | None:
    intervention = _context_intervention(context)
    return getattr(intervention, "family", getattr(intervention, "type", None)) if intervention else None


def _context_condition(context: Any) -> str | None:
    if context is None:
        return None
    if hasattr(context, "condition"):
        return context.condition
    return "intervention" if getattr(context, "intervention", None) is not None else "clean"


def _context_base_task_id(context: Any) -> str | None:
    if context is None:
        return None
    if hasattr(context, "base_task"):
        return context.base_task.task_id
    return getattr(context, "clean_task_id", None) or getattr(context, "task_id", None)


def _context_domain(context: Any) -> str | None:
    if context is None:
        return None
    if hasattr(context, "base_task"):
        return context.base_task.domain
    return getattr(context, "domain", None)


def _context_max_steps(context: Any) -> int | None:
    if context is None:
        return None
    if hasattr(context, "base_task"):
        return context.base_task.max_steps
    metadata = getattr(context, "metadata", {})
    return metadata.get("max_steps") if isinstance(metadata, dict) else None


def _required_tools(context: Any) -> list[str]:
    if context is None:
        return []
    if hasattr(context, "base_task"):
        base = context.base_task
        return list(base.gold_tool_sequence or base.required_tools or [])
    expected = getattr(context, "expected_behavior", None)
    return list(getattr(expected, "tool_sequence", None) or getattr(expected, "required_tools", []) or [])


def _optional_tools(context: Any) -> list[str]:
    if context is None:
        return []
    if hasattr(context, "base_task"):
        return list(getattr(context.base_task, "optional_tools", []) or [])
    return []


def _available_tools(context: Any) -> list[str]:
    if context is None:
        return []
    return list(getattr(context, "available_tools", []) or getattr(getattr(context, "base_task", None), "available_tools", []) or [])


def _success_criteria(context: Any) -> list[str]:
    if context is None:
        return []
    if hasattr(context, "base_task"):
        return list(context.base_task.goal.success_criteria)
    expected = getattr(context, "expected_behavior", None)
    fragments = getattr(expected, "final_answer_contains", None) or getattr(expected, "acceptable_final_answers", None) or []
    return [str(item) for item in fragments]


def _required_information(context: Any) -> list[str]:
    if context is None:
        return []
    if hasattr(context, "base_task"):
        return list(context.base_task.goal.required_information)
    return []


def _user_instruction(context: Any) -> str:
    if context is None:
        return ""
    if hasattr(context, "base_task"):
        return context.base_task.goal.user_instruction
    return getattr(context, "user_goal", "")


def _model_identifier(row: dict[str, Any], trajectory: Any) -> str:
    metadata_model = row.get("metadata_model_name")
    if metadata_model:
        return str(metadata_model)
    if trajectory is not None:
        provider = getattr(trajectory, "provider_model_metadata", {}) or {}
        for key in ["model", "model_name"]:
            if provider.get(key):
                return str(provider[key])
        if getattr(trajectory, "model_name", None):
            return str(trajectory.model_name)
    return str(row.get("agent_name") or "unknown")


def _trajectory_cost(trajectory: Any) -> float | None:
    if trajectory is None:
        return None
    for payload in [getattr(trajectory, "token_cost_metadata", {}), getattr(trajectory, "metadata", {})]:
        if not isinstance(payload, dict):
            continue
        value = payload.get("estimated_cost_usd")
        if value is not None:
            return _number(value, None)
    return None


def _trajectory_run_id(trajectory: Any) -> str | None:
    return getattr(trajectory, "run_id", None) if trajectory is not None else None


def _trajectory_final_answer(trajectory: Any) -> str | None:
    return getattr(trajectory, "final_answer", None) if trajectory is not None else None


def _has_final_success_metadata(trajectory: Any) -> bool:
    metadata = getattr(trajectory, "metadata", {}) if trajectory is not None else {}
    return bool(isinstance(metadata, dict) and metadata.get("success") is True)


def _steps(trajectory: Any) -> list[Any]:
    return list(getattr(trajectory, "steps", []) or []) if trajectory is not None else []


def _step_index(step: Any) -> int:
    payload = _as_dict(step)
    return int(payload.get("step_index", payload.get("index", 0)) or 0)


def _action_from_step(step: Any) -> dict[str, Any]:
    payload = _as_dict(step)
    return _as_dict(payload.get("action"))


def _tool_call_from_step(step: Any) -> dict[str, Any] | None:
    payload = _as_dict(step)
    call = payload.get("tool_call")
    if call is None:
        call = _action_from_step(step).get("tool_call")
    return _as_dict(call) if call is not None else None


def _observation_from_step(step: Any) -> dict[str, Any] | None:
    payload = _as_dict(step)
    observation = payload.get("tool_result")
    if observation is None:
        observation = payload.get("observation")
    return _as_dict(observation) if observation is not None else None


def _final_answer_from_step(step: Any) -> str | None:
    payload = _as_dict(step)
    if payload.get("final_answer") is not None:
        return str(payload["final_answer"])
    action = _action_from_step(step)
    return str(action["final_answer"]) if action.get("final_answer") is not None else None


def _raw_model_output_from_step(step: Any) -> str | None:
    payload = _as_dict(step)
    value = payload.get("raw_model_output")
    return str(value) if value is not None else None


def _parser_status_from_step(step: Any) -> str | None:
    payload = _as_dict(step)
    if payload.get("parser_status") is not None:
        return str(payload["parser_status"])
    parsed = _as_dict(payload.get("parsed_action"))
    if parsed.get("outcome") is not None:
        return str(parsed["outcome"])
    action = _action_from_step(step)
    metadata = _as_dict(action.get("metadata"))
    if metadata.get("parser_outcome") is not None:
        return str(metadata["parser_outcome"])
    return None


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    return {}


def _is_error_observation(observation: dict[str, Any]) -> bool:
    return bool(observation.get("error") or observation.get("is_corrupted"))


def _has_uncertainty(text: str | None) -> bool:
    lowered = str(text or "").lower()
    return any(word in lowered for word in UNCERTAINTY_WORDS)


def _salient_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-z0-9_.-]{3,}", text.lower()))
    stop = {
        "the",
        "and",
        "for",
        "that",
        "with",
        "tool",
        "result",
        "returned",
        "according",
        "shows",
        "from",
    }
    return {token for token in tokens if token not in stop}


def _truthy(value: Any) -> bool:
    if _is_missing(value):
        return False
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes"}
    return bool(value)


def _number(value: Any, default: float | int | None = 0) -> Any:
    if _is_missing(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _compact(value: Any, *, depth: int = 0) -> Any:
    if depth > 4:
        return _truncate(value, 200)
    if isinstance(value, dict):
        return {str(key): _compact(val, depth=depth + 1) for key, val in list(value.items())[:12]}
    if isinstance(value, list):
        items = [_compact(item, depth=depth + 1) for item in value[:8]]
        if len(value) > 8:
            items.append(f"... {len(value) - 8} more")
        return items
    return _truncate(value, 500)


def _truncate(value: Any, limit: int = 500) -> Any:
    if value is None:
        return None
    text = str(value)
    text = _redact_secrets(text)
    if len(text) <= limit:
        return text
    return text[: limit - 15].rstrip() + " ...[truncated]"


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_text = str(key)
            if any(secret in key_text.lower() for secret in ["api_key", "apikey", "authorization", "password", "secret", "token"]):
                sanitized[key_text] = "[REDACTED]"
            else:
                sanitized[key_text] = _sanitize(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, str):
        return _redact_secrets(value)
    return value


def _redact_secrets(text: str) -> str:
    text = SECRET_KEY_RE.sub(lambda match: match.group(1) + "=[REDACTED]", text)
    return SECRET_VALUE_RE.sub("[REDACTED]", text)
