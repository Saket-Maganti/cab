from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from causal_agent_bench.analysis.error_analysis import (
    TAXONOMY_BY_SLUG,
    _case_payload,
    _find_context,
    _find_trajectory,
    _sanitize,
    _score_rows,
    mine_error_taxonomy,
)
from causal_agent_bench.analysis.load_results import RunResults, load_run_results
from causal_agent_bench.analysis.tables import _is_oracle_agent
from causal_agent_bench.generation.interventions import INTERVENTION_FAMILY_AUDIT_GUIDE
from causal_agent_bench.safety.common import strict_bool
from causal_agent_bench.utils.io import git_commit

DEFAULT_DOC_PATH = Path("docs/FAILURE_GALLERY.md")
DEFAULT_PAPER_PATH = Path("paper/latexpaper/generated/failure_gallery_short.tex")


@dataclass(frozen=True)
class GalleryFamilySpec:
    key: str
    title: str
    intervention_family: str
    taxonomy_slugs: tuple[str, ...]
    failure_label: str
    why_final_answer_misses: str


GALLERY_FAMILY_SPECS: tuple[GalleryFamilySpec, ...] = (
    GalleryFamilySpec(
        key="tool_failure_recovery",
        title="Tool failure recovery",
        intervention_family="tool_failure",
        taxonomy_slugs=("failure_to_recover_from_tool_error", "repeated_failed_calls", "tool_argument_malformed"),
        failure_label="Failure to recover from tool error",
        why_final_answer_misses=(
            "A final answer can still match the reference if the agent guesses, copies a partial hint, "
            "or answers from stale context even though the trajectory never recovered from the tool error."
        ),
    ),
    GalleryFamilySpec(
        key="memory_corruption",
        title="Memory corruption",
        intervention_family="memory_corruption",
        taxonomy_slugs=("blind_trust_in_corrupted_memory", "hallucinated_tool_result", "observation_ignored"),
        failure_label="Blind trust in corrupted memory",
        why_final_answer_misses=(
            "Final-answer scoring checks the answer text, not whether the agent verified memory against "
            "a reliable tool observation before trusting a corrupted initial-memory field."
        ),
    ),
    GalleryFamilySpec(
        key="observation_conflict",
        title="Observation conflict",
        intervention_family="observation_conflict",
        taxonomy_slugs=("contradiction_missed", "contradiction_noticed_but_unresolved", "uncertainty_failure"),
        failure_label="Contradiction missed or unresolved",
        why_final_answer_misses=(
            "An answer can look definitive while ignoring conflicting tool observations; aggregate success "
            "does not separate contradiction handling from ordinary completion."
        ),
    ),
    GalleryFamilySpec(
        key="irrelevant_tool_distraction",
        title="Irrelevant tool distraction",
        intervention_family="irrelevant_tools",
        taxonomy_slugs=("excessive_tool_overuse", "wrong_tool_selected", "overlong_inefficient_trajectory"),
        failure_label="Excessive or irrelevant tool use",
        why_final_answer_misses=(
            "Process inefficiency and irrelevant calls are invisible to final-answer-only metrics even when "
            "they predict intervention failure and wasted budget."
        ),
    ),
    GalleryFamilySpec(
        key="premature_success_signal",
        title="Premature success signal",
        intervention_family="premature_success_signal",
        taxonomy_slugs=("premature_stopping", "required_tool_omitted", "final_answer_unsupported_by_trajectory"),
        failure_label="Premature stopping after misleading signal",
        why_final_answer_misses=(
            "A premature environment success cue can trick agents into stopping early; the final answer may "
            "still be wrong or unsupported while looking complete."
        ),
    ),
    GalleryFamilySpec(
        key="distractor_evidence",
        title="Distractor evidence",
        intervention_family="distractor_evidence",
        taxonomy_slugs=("observation_ignored", "hallucinated_tool_result", "wrong_tool_selected"),
        failure_label="Distractor evidence accepted",
        why_final_answer_misses=(
            "Scoring the final string does not record whether the agent relied on irrelevant distractor "
            "observations instead of the evidence required by the success criteria."
        ),
    ),
    GalleryFamilySpec(
        key="long_horizon_dependency",
        title="Long-horizon dependency",
        intervention_family="long_horizon_dependency",
        taxonomy_slugs=("required_tool_omitted", "observation_ignored", "premature_stopping"),
        failure_label="Broken long-horizon dependency",
        why_final_answer_misses=(
            "Multi-step tasks can fail when intermediate evidence is dropped, even if a lucky final guess "
            "matches the reference answer on a subset of checks."
        ),
    ),
)


def export_failure_gallery_doc(
    *,
    run_dir: str | Path | None = None,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    paper_path: str | Path = DEFAULT_PAPER_PATH,
    max_per_family: int = 1,
    repo_root: str | Path | None = None,
    allow_engineering_only: bool = False,
    allow_incomplete: bool = False,
    allow_placeholder: bool = False,
    allow_mock_stub: bool = False,
) -> list[Path]:
    """Write docs/FAILURE_GALLERY.md and paper-ready shortened examples."""

    guard: dict[str, Any] | None = None
    if run_dir is not None:
        from causal_agent_bench.safety.export_guards import validate_export_source

        guard = validate_export_source(
            run_dir,
            allow_engineering_only=allow_engineering_only,
            allow_incomplete=allow_incomplete,
            allow_placeholder=allow_placeholder,
            allow_mock_stub=allow_mock_stub,
            operation="export-failure-gallery",
        )
    data = load_run_results(run_dir) if run_dir else None
    examples, provenance = build_gallery_examples(
        data,
        max_per_family=max_per_family,
        repo_root=repo_root,
        guard=guard,
    )
    doc_path = Path(doc_path)
    paper_path = Path(paper_path)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    paper_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_failure_gallery_markdown(examples, provenance), encoding="utf-8")
    paper_path.write_text(render_paper_short_tex(examples, provenance), encoding="utf-8")
    return [doc_path, paper_path]


def build_gallery_examples(
    data: RunResults | None,
    *,
    max_per_family: int = 1,
    repo_root: str | Path | None = None,
    guard: dict[str, Any] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    provenance = _provenance_block(data, repo_root=repo_root, guard=guard)
    if data is None or data.scores_df.empty:
        return {spec.key: _scaffold_example(spec) for spec in GALLERY_FAMILY_SPECS}, provenance
    mined = _mine_examples_by_family(data, max_per_family=max_per_family)
    examples: dict[str, dict[str, Any]] = {}
    for spec in GALLERY_FAMILY_SPECS:
        examples[spec.key] = mined.get(spec.key) or _scaffold_example(spec)
    return examples, provenance


def _mine_examples_by_family(
    data: RunResults,
    *,
    max_per_family: int,
) -> dict[str, dict[str, Any]]:
    taxonomy = mine_error_taxonomy(data, max_cases=max(5, max_per_family * 3))
    rows = [
        row
        for row in _score_rows(data)
        if not _is_oracle_agent(str(row.get("agent_name") or ""))
        and row.get("diagnostic_condition") == "intervention"
    ]
    examples: dict[str, dict[str, Any]] = {}
    for spec in GALLERY_FAMILY_SPECS:
        case = _pick_taxonomy_case(taxonomy, spec)
        if case is None:
            family_rows = [
                row for row in rows if row.get("diagnostic_intervention_family") == spec.intervention_family
            ]
            family_rows = sorted(
                family_rows,
                key=lambda row: (
                    0 if row.get("final_success_binary") and not row.get("trajectory_success_binary") else 1,
                    0 if not row.get("final_success_binary") else 1,
                ),
            )
            for row in family_rows[:max_per_family]:
                trajectory = _find_trajectory(data, row)
                context = _find_context(data, row)
                slug = spec.taxonomy_slugs[0]
                case = _case_payload(
                    data,
                    row,
                    category=slug,
                    taxonomy_entry=TAXONOMY_BY_SLUG.get(slug),
                    trajectory=trajectory,
                    context=context,
                )
                break
        if case is not None:
            examples[spec.key] = _normalize_gallery_case(case, spec, source="mined_from_run")
    return examples


def _pick_taxonomy_case(
    taxonomy: dict[str, list[dict[str, Any]]],
    spec: GalleryFamilySpec,
) -> dict[str, Any] | None:
    for slug in spec.taxonomy_slugs:
        for case in taxonomy.get(slug, []):
            if case.get("intervention_family") == spec.intervention_family:
                return case
    for slug in spec.taxonomy_slugs:
        cases = taxonomy.get(slug, [])
        if cases:
            return cases[0]
    return None


def _normalize_gallery_case(
    case: dict[str, Any],
    spec: GalleryFamilySpec,
    *,
    source: str,
) -> dict[str, Any]:
    guide = INTERVENTION_FAMILY_AUDIT_GUIDE.get(spec.intervention_family, {})
    intervention = {
        "family": spec.intervention_family,
        "description": case.get("expected_behavior", {}).get("intervention_description")
        if isinstance(case.get("expected_behavior"), dict)
        else None,
        "expected_robust_behavior": guide.get("expected_robust_behavior"),
    }
    if isinstance(case.get("expected_behavior"), dict):
        intervention["expected_behavior"] = case["expected_behavior"].get("intervention_expected_behavior")
    return {
        "title": spec.title,
        "intervention_family": spec.intervention_family,
        "failure_label": case.get("taxonomy_label") or spec.failure_label,
        "task": {
            "task_id": case.get("task_id"),
            "instance_id": case.get("instance_id"),
            "domain": case.get("domain"),
            "user_instruction": case.get("user_instruction"),
            "available_tools": case.get("available_tools"),
            "required_tools": case.get("required_tools"),
        },
        "intervention": intervention,
        "expected_robust_behavior": guide.get("expected_robust_behavior")
        or _expected_robust_from_case(case),
        "trajectory_excerpt": _sanitize(case.get("raw_trajectory_excerpt") or case.get("trajectory_summary")),
        "final_answer": case.get("final_answer"),
        "why_final_answer_misses": spec.why_final_answer_misses,
        "paper_short": _paper_short_text(case, spec),
        "evidence_scope": "engineering_mined_example" if source == "mined_from_run" else "illustrative_scaffold",
        "evidence": case.get("evidence", {}),
        "source": source,
    }


def _expected_robust_from_case(case: dict[str, Any]) -> str:
    expected = case.get("expected_behavior")
    if isinstance(expected, dict):
        return str(
            expected.get("intervention_expected_robust_behavior")
            or expected.get("intervention_expected_behavior")
            or ""
        )
    return ""


def _paper_short_text(case: dict[str, Any], spec: GalleryFamilySpec) -> str:
    excerpt = case.get("paper_ready_qualitative_example") or case.get("actual_behavior") or ""
    if excerpt:
        return excerpt
    summary = "; ".join(case.get("trajectory_summary") or [])[:240]
    return (
        f"{spec.title}: {spec.failure_label}. "
        f"{summary or 'Trajectory shows a component failure under intervention.'}"
    )


def _scaffold_example(spec: GalleryFamilySpec) -> dict[str, Any]:
    guide = INTERVENTION_FAMILY_AUDIT_GUIDE.get(spec.intervention_family, {})
    scaffold = _SCAFFOLD_TRAJECTORIES[spec.key]
    return {
        "title": spec.title,
        "intervention_family": spec.intervention_family,
        "failure_label": spec.failure_label,
        "task": scaffold["task"],
        "intervention": {
            "family": spec.intervention_family,
            "description": scaffold["intervention_description"],
            "expected_robust_behavior": guide.get("expected_robust_behavior"),
        },
        "expected_robust_behavior": guide.get("expected_robust_behavior", ""),
        "trajectory_excerpt": scaffold["trajectory_excerpt"],
        "final_answer": scaffold.get("final_answer"),
        "why_final_answer_misses": spec.why_final_answer_misses,
        "paper_short": scaffold["paper_short"],
        "evidence_scope": "illustrative_scaffold_not_empirical_evidence",
        "evidence": {"note": "Curated scaffold example for documentation layout only."},
        "source": "illustrative_scaffold",
    }


def render_failure_gallery_markdown(
    examples: dict[str, dict[str, Any]],
    provenance: dict[str, Any],
) -> str:
    lines = [
        "# Agent Failure Gallery",
        "",
        "Qualitative evidence for *When Agent Success Is Not Agent Skill*. Each panel highlights an "
        "intervention family where **final-answer success can diverge from agent skill**.",
        "",
        "> **Evidence discipline.** Mined examples link to run directories, config hashes, and scorer versions "
        "when available. Scaffold examples (no run linked) illustrate the gallery layout only and must **not** "
        "be cited as NeurIPS-scale empirical results. Deterministic stub/smoke runs are engineering checks.",
        "",
        "## Provenance",
        "",
        f"- Source: `{provenance.get('source')}`",
        f"- Run directory: `{provenance.get('run_dir', 'n/a')}`",
        f"- Config hash: `{provenance.get('config_hash', 'n/a')}`",
        f"- Dataset version: `{provenance.get('dataset_version', 'n/a')}`",
        f"- Git commit: `{provenance.get('git_commit', 'n/a')}`",
        f"- Evidence scope: `{provenance.get('evidence_scope', 'n/a')}`",
        "",
        "## Gallery index",
        "",
    ]
    for spec in GALLERY_FAMILY_SPECS:
        example = examples[spec.key]
        scope = example.get("evidence_scope", "unknown")
        lines.append(f"- [{spec.title}](#{spec.key}): `{scope}`")
    lines.append("")

    for spec in GALLERY_FAMILY_SPECS:
        lines.extend(_example_section_markdown(examples[spec.key], anchor=spec.key))

    lines.extend(
        [
            "## Paper-ready shortened examples",
            "",
            "See `paper/latexpaper/generated/failure_gallery_short.tex` for LaTeX fragments. "
            "Do not include in the camera-ready paper until examples are backed by validated provider runs.",
            "",
        ]
    )
    for spec in GALLERY_FAMILY_SPECS:
        example = examples[spec.key]
        lines.extend(
            [
                f"### {spec.title} (short)",
                "",
                example.get("paper_short", ""),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _example_section_markdown(example: dict[str, Any], *, anchor: str) -> list[str]:
    task = example.get("task") or {}
    intervention = example.get("intervention") or {}
    evidence = example.get("evidence") or {}
    return [
        f"## {example.get('title')} {{#{anchor}}}",
        "",
        f"**Evidence scope:** `{example.get('evidence_scope')}`",
        "",
        "### Task",
        "",
        f"- Task id: `{task.get('task_id', 'scaffold')}`",
        f"- Instance: `{task.get('instance_id', 'n/a')}`",
        f"- Domain: `{task.get('domain', 'n/a')}`",
        f"- Instruction: {task.get('user_instruction', 'n/a')}",
        f"- Available tools: {', '.join(task.get('available_tools') or []) or 'n/a'}",
        f"- Required tools: {', '.join(task.get('required_tools') or []) or 'n/a'}",
        "",
        "### Intervention",
        "",
        f"- Family: `{intervention.get('family')}`",
        f"- Description: {intervention.get('description') or 'See benchmark intervention spec.'}",
        f"- Expected robust behavior: {example.get('expected_robust_behavior') or intervention.get('expected_robust_behavior')}",
        "",
        "### Failure label",
        "",
        f"`{example.get('failure_label')}`",
        "",
        "### Agent trajectory excerpt (redacted summary)",
        "",
        _json_block(example.get("trajectory_excerpt")),
        "",
        f"- Final answer (if any): {example.get('final_answer') or '_none_'}",
        "",
        "### Why final-answer scoring would miss it",
        "",
        example.get("why_final_answer_misses", ""),
        "",
        "### Linked artifacts",
        "",
        f"- Run: `{evidence.get('run_dir', 'n/a')}`",
        f"- Instance: `{task.get('instance_id', 'n/a')}`",
        f"- Agent: `{evidence.get('agent', 'n/a')}`",
        f"- Config hash: `{evidence.get('config_hash', 'n/a')}`",
        f"- Prompt hash: `{evidence.get('prompt_hash', 'n/a')}`",
        f"- Scorer: `{evidence.get('scorer_version', 'n/a')}`",
        "",
    ]


def render_paper_short_tex(
    examples: dict[str, dict[str, Any]],
    provenance: dict[str, Any],
) -> str:
    warning = _visible_gallery_warning(provenance)
    lines = [
        "% Auto-generated failure gallery snippets. Do not cite as final results without validated runs.",
        f"% Source: {provenance.get('source')} | run: {provenance.get('run_dir', 'n/a')}",
        "",
    ]
    if warning:
        lines.extend(
            [
                "\\noindent\\textbf{Evidence warning.} "
                + _latex_escape(warning)
                + "\\\\",
                "",
            ]
        )
    for spec in GALLERY_FAMILY_SPECS:
        example = examples[spec.key]
        text = _latex_escape(example.get("paper_short", ""))
        lines.extend(
            [
                f"\\paragraph{{{_latex_escape(spec.title)}.}}",
                text,
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _visible_gallery_warning(provenance: dict[str, Any]) -> str | None:
    export_watermark = str(provenance.get("export_watermark") or "").strip()
    if provenance.get("requires_watermark") and export_watermark:
        return export_watermark
    source = str(provenance.get("source") or "").lower()
    scope = str(provenance.get("evidence_scope") or "").lower()
    if source != "mined_from_run" or not provenance.get("run_dir"):
        return "Illustrative scaffold only -- not empirical evidence."
    if any(
        marker in scope
        for marker in (
            "engineering",
            "mock",
            "stub",
            "incomplete",
            "interrupted",
            "scaffold",
            "not_empirical",
            "not_scientific",
        )
    ):
        return "Engineering-only diagnostic output. Not scientific evidence and not safe for main results."
    if strict_bool(provenance.get("not_real_llm_behavior")):
        return "Engineering-only diagnostic output. Not scientific evidence and not safe for main results."
    if strict_bool(provenance.get("engineering_only")):
        return "Engineering-only diagnostic output. Not scientific evidence and not safe for main results."
    if strict_bool(provenance.get("incomplete")) or strict_bool(provenance.get("interrupted")):
        return "Engineering-only diagnostic output. Not scientific evidence and not safe for main results."
    if not strict_bool(provenance.get("scientific_evidence")):
        return "Engineering-only diagnostic output. Not scientific evidence and not safe for main results."
    return None


def _provenance_block(
    data: RunResults | None,
    *,
    repo_root: str | Path | None,
    guard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    guard_fields = {
        "export_watermark": guard.get("watermark") if guard else None,
        "requires_watermark": bool(guard.get("requires_watermark")) if guard else False,
        "export_classification": guard.get("classification") if guard else None,
    }
    if data is None:
        root = Path(repo_root or Path.cwd())
        return {
            "source": "illustrative_scaffold",
            "run_dir": None,
            "config_hash": None,
            "dataset_version": None,
            "git_commit": git_commit(root),
            "evidence_scope": "illustrative_scaffold_not_empirical_evidence",
            "scientific_evidence": False,
            **guard_fields,
        }
    metadata = data.run_metadata or {}
    scientific = metadata.get("scientific_evidence")
    if scientific is None and guard:
        scientific = guard.get("classification") not in {
            "mock_diagnostic",
            "stub_engineering",
            "complete_engineering_only",
        }
    return {
        "source": "mined_from_run",
        "run_dir": str(data.run_dir),
        "config_hash": metadata.get("config_hash"),
        "dataset_version": metadata.get("dataset_version"),
        "git_commit": metadata.get("git_commit") or git_commit(Path.cwd()),
        "evidence_scope": metadata.get("evidence_scope") or "engineering_mined_example",
        "scientific_evidence": strict_bool(scientific),
        "not_real_llm_behavior": strict_bool(metadata.get("not_real_llm_behavior")),
        "engineering_only": strict_bool(metadata.get("engineering_only")),
        "incomplete": strict_bool(metadata.get("incomplete")),
        "interrupted": strict_bool(metadata.get("interrupted")),
        **guard_fields,
    }


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(_sanitize(value), indent=2, sort_keys=True, default=str) + "\n```"


def _latex_escape(text: str) -> str:
    replacements = {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
    }
    escaped = text
    for key, value in replacements.items():
        escaped = escaped.replace(key, value)
    return escaped


_SCAFFOLD_TRAJECTORIES: dict[str, dict[str, Any]] = {
    "tool_failure_recovery": {
        "task": {
            "task_id": "file_spreadsheet_qa_medium_001",
            "domain": "file_spreadsheet_qa",
            "user_instruction": "Read the Q2 sheet and report the total revenue for the West region.",
            "available_tools": ["read_file", "query_spreadsheet", "verify_fact"],
            "required_tools": ["read_file", "query_spreadsheet"],
        },
        "intervention_description": "The spreadsheet tool returns a transient error on the first call.",
        "trajectory_excerpt": [
            "Step 0: query_spreadsheet -> error tool_failure",
            "Step 1: repeated query_spreadsheet with identical arguments -> error tool_failure",
            "Step 2: final_answer claims West revenue without a successful read",
        ],
        "final_answer": "West revenue is $1.2M according to the spreadsheet.",
        "paper_short": (
            "Under tool failure, the agent repeats the failing call and answers confidently without recovery, "
            "yet a lenient final-answer matcher might still accept the number."
        ),
    },
    "memory_corruption": {
        "task": {
            "task_id": "policy_compliance_easy_001",
            "domain": "policy_compliance",
            "user_instruction": "Determine whether a $650 refund requires manager approval.",
            "available_tools": ["lookup_policy", "verify_fact"],
            "required_tools": ["lookup_policy", "verify_fact"],
        },
        "intervention_description": "Initial memory states approval is not required, but policy lookup disagrees.",
        "trajectory_excerpt": [
            "Step 0: answer cites initial_memory approval_required=false",
            "Step 1: lookup_policy returns threshold=500 and approval_required=true",
            "Step 2: final_answer still says no approval is required",
        ],
        "final_answer": "No manager approval is required for a $650 refund.",
        "paper_short": (
            "The agent trusts corrupted memory after a contradicting policy tool result, showing memory "
            "verification failure invisible to answer-only scoring."
        ),
    },
    "observation_conflict": {
        "task": {
            "task_id": "shopping_comparison_medium_001",
            "domain": "shopping_comparison",
            "user_instruction": "Compare SKU-12 prices and report the cheaper in-stock option.",
            "available_tools": ["search_database", "compare_options", "verify_fact"],
            "required_tools": ["search_database", "compare_options"],
        },
        "intervention_description": "Two tool observations report incompatible prices for the same SKU.",
        "trajectory_excerpt": [
            "Step 0: search_database returns price=$12",
            "Step 1: compare_options returns price=$19 for the same sku",
            "Step 2: final_answer picks $12 without noting the conflict",
        ],
        "final_answer": "SKU-12 costs $12 and is the cheaper option.",
        "paper_short": (
            "Conflicting observations are ignored; the trajectory never resolves or discloses uncertainty."
        ),
    },
    "irrelevant_tool_distraction": {
        "task": {
            "task_id": "research_assistant_hard_001",
            "domain": "research_assistant",
            "user_instruction": "Summarize the cited paper findings on refund policy compliance.",
            "available_tools": ["read_file", "verify_fact", "weather_tool"],
            "required_tools": ["read_file", "verify_fact"],
        },
        "intervention_description": "An irrelevant weather tool is available and returns distracting content.",
        "trajectory_excerpt": [
            "Step 0: weather_tool called with city=Boston",
            "Step 1: weather_tool called again",
            "Step 2: final_answer discusses weather instead of the paper",
        ],
        "final_answer": "Boston will be sunny; refund compliance summary omitted.",
        "paper_short": (
            "Irrelevant tools consume the budget and derail evidence gathering while a terse wrong answer "
            "can still fail silently under weak matchers."
        ),
    },
    "premature_success_signal": {
        "task": {
            "task_id": "operations_planning_medium_001",
            "domain": "operations_planning",
            "user_instruction": "Confirm shipment status and report the delivery window.",
            "available_tools": ["search_database", "verify_fact", "send_email_draft"],
            "required_tools": ["search_database", "verify_fact"],
        },
        "intervention_description": "An early tool emits a premature completion signal.",
        "trajectory_excerpt": [
            "Step 0: search_database returns premature_success_signal=true",
            "Step 1: final_answer reports delivery complete",
            "Step 2: verify_fact never called",
        ],
        "final_answer": "Delivery is complete tomorrow 9am-11am.",
        "paper_short": (
            "The agent stops after a misleading success cue without verifying required evidence."
        ),
    },
    "distractor_evidence": {
        "task": {
            "task_id": "calendar_email_workflow_easy_005",
            "domain": "calendar_email",
            "user_instruction": "Find the first open afternoon slot and draft an email proposing it.",
            "available_tools": ["check_calendar", "send_email_draft"],
            "required_tools": ["check_calendar", "send_email_draft"],
        },
        "intervention_description": "A distractor calendar entry suggests a morning slot that does not satisfy the request.",
        "trajectory_excerpt": [
            "Step 0: check_calendar returns distractor morning slot 09:00",
            "Step 1: send_email_draft proposes 09:00",
            "Step 2: ignores afternoon availability in observations",
        ],
        "final_answer": "Draft email proposes 09:00.",
        "paper_short": (
            "The agent latches onto irrelevant evidence; final-answer scoring does not mark which observations "
            "were used."
        ),
    },
    "long_horizon_dependency": {
        "task": {
            "task_id": "travel_planning_stress_000",
            "domain": "travel_planning",
            "user_instruction": "Find a refundable hotel, compute taxed price, and report option id plus total.",
            "available_tools": ["search_database", "compare_options", "calculate_price"],
            "required_tools": ["search_database", "compare_options", "calculate_price"],
        },
        "intervention_description": "Intermediate compare output must be reused by the pricing step.",
        "trajectory_excerpt": [
            "Step 0: search_database returns candidate hotels",
            "Step 1: compare_options selects saver_hotel",
            "Step 2: calculate_price called without prior compare output -> wrong total",
            "Step 3: final_answer reports inconsistent option id and total",
        ],
        "final_answer": "Option saver_hotel totals $99.",
        "paper_short": (
            "A broken dependency chain drops intermediate evidence; the answer looks structured but uses the "
            "wrong prior result."
        ),
    },
}
