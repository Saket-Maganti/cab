"""Static leakage and prompt-injection checks over real agent-visible surfaces."""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from causal_agent_bench.agent_payload import (
    FORBIDDEN_AGENT_TASK_CONTEXT_FIELDS,
    build_agent_task_context,
    validate_agent_task_context,
)
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.tools.registry import ToolRegistry

PROMPT_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "instruction_override",
        re.compile(
            r"\b(?:ignore|disregard|override|forget)\s+(?:all\s+|any\s+|the\s+)?"
            r"(?:previous|prior|above|earlier)\s+(?:instructions?|messages?|rules?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "role_impersonation",
        re.compile(
            r"(?:<\|(?:system|assistant|developer)\|>|\[(?:INST|/INST)\]|"
            r"^\s*#{0,3}\s*(?:system|developer)\s*:)",
            re.IGNORECASE | re.MULTILINE,
        ),
    ),
    (
        "hidden_prompt_exfiltration",
        re.compile(
            r"\b(?:reveal|print|show|repeat|return|expose)\s+(?:the\s+|your\s+)?"
            r"(?:hidden|secret|system|developer)\s+(?:prompt|instructions?|message|context)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "secret_exfiltration",
        re.compile(
            r"\b(?:reveal|print|show|return|expose|send)\s+(?:the\s+|your\s+|all\s+)?"
            r"(?:api[_ -]?keys?|tokens?|passwords?|credentials?|secrets?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "identity_override",
        re.compile(
            r"\b(?:you are now|act as|pretend to be)\s+(?:an?\s+)?"
            r"(?:unrestricted|unfiltered|developer|system|administrator|root)\b",
            re.IGNORECASE,
        ),
    ),
)

_ANSWER_SPOILER_RE = re.compile(
    r"\b(?:final|expected|gold|correct)\s+answer\b|\banswer\s+is\b|"
    r"\brespond\s+with\b|\boutput\s+must\s+be\b",
    re.IGNORECASE,
)


def scan_agent_visible_dataset(
    instances_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    selected_instance_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Scan serialized instances and intervention mutation surfaces."""

    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    path = Path(instances_path)
    if not path.is_absolute():
        path = root / path
    selected = set(selected_instance_ids or [])
    findings: list[dict[str, Any]] = []
    checked = 0
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                findings.append(
                    _finding(
                        path,
                        root,
                        task_id=None,
                        instance_id=None,
                        field="json",
                        severity="blocker",
                        leakage_class="invalid_payload",
                        detail=str(exc),
                        suggested_repair="Repair the malformed JSONL row.",
                        line=line_no,
                    )
                )
                continue
            instance_id = (
                str(row.get("instance_id", ""))
                if isinstance(row, dict)
                else ""
            )
            if selected and instance_id not in selected:
                continue
            try:
                instance = BenchmarkInstance.model_validate(row)
            except ValidationError as exc:
                findings.append(
                    _finding(
                        path,
                        root,
                        task_id=_raw_base_task_id(row),
                        instance_id=instance_id or None,
                        field="schema",
                        severity="blocker",
                        leakage_class="invalid_payload",
                        detail=str(exc),
                        suggested_repair="Repair the instance schema before leakage review.",
                        line=line_no,
                    )
                )
                continue
            checked += 1
            findings.extend(
                scan_agent_visible_instance(
                    instance,
                    source_path=path,
                    repo_root=root,
                    line=line_no,
                )
            )
    findings.extend(_scan_registered_tool_surfaces(path, root))

    severity_counts = Counter(row["severity"] for row in findings)
    class_counts = Counter(row["leakage_class"] for row in findings)
    blockers = [
        row for row in findings if row["severity"] in {"blocker", "error"}
    ]
    return {
        "scope": (
            "Static scan of the runtime task allowlist plus instruction, memory, "
            "and tool-output mutation surfaces. No model or provider is invoked."
        ),
        "evidence_class": "ENGINEERING_ONLY",
        "instances_path": _relative(path, root),
        "instances_checked": checked,
        "selected_instance_count": len(selected),
        "finding_count": len(findings),
        "blocker_count": len(blockers),
        "by_severity": dict(sorted(severity_counts.items())),
        "by_leakage_class": dict(sorted(class_counts.items())),
        "passed": not blockers,
        "findings": findings,
    }


def scan_agent_visible_instance(
    instance: BenchmarkInstance,
    *,
    source_path: str | Path,
    repo_root: str | Path | None = None,
    line: int | None = None,
) -> list[dict[str, Any]]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    path = Path(source_path)
    payload = build_agent_task_context(instance)
    findings: list[dict[str, Any]] = []
    task_id = instance.base_task.task_id
    instance_id = instance.instance_id

    for detail in validate_agent_task_context(payload):
        findings.append(
            _finding(
                path,
                root,
                task_id=task_id,
                instance_id=instance_id,
                field="agent_task_context",
                severity="blocker",
                leakage_class="evaluator_field_exposure",
                detail=detail,
                suggested_repair="Use the canonical agent-task-context allowlist.",
                line=line,
            )
        )

    serialized = json.dumps(payload, sort_keys=True, default=str).casefold()
    forbidden_key_tokens = [
        field
        for field in FORBIDDEN_AGENT_TASK_CONTEXT_FIELDS
        if f'"{field.casefold()}"' in serialized
    ]
    if forbidden_key_tokens:
        findings.append(
            _finding(
                path,
                root,
                task_id=task_id,
                instance_id=instance_id,
                field="agent_task_context",
                severity="blocker",
                leakage_class="evaluator_field_exposure",
                detail=f"forbidden keys serialized: {sorted(forbidden_key_tokens)}",
                suggested_repair="Remove evaluator-only keys before prompt assembly.",
                line=line,
            )
        )

    intervention = instance.intervention
    if intervention is not None:
        family = intervention.family.casefold()
        expected_behavior = intervention.expected_behavior.strip().casefold()
        if family in serialized:
            findings.append(
                _finding(
                    path,
                    root,
                    task_id=task_id,
                    instance_id=instance_id,
                    field="agent_task_context",
                    severity="blocker",
                    leakage_class="intervention_label_exposure",
                    detail=f"intervention family `{intervention.family}` is visible",
                    suggested_repair="Remove condition and intervention labels from prompts.",
                    line=line,
                )
            )
        if len(expected_behavior) >= 12 and expected_behavior in serialized:
            findings.append(
                _finding(
                    path,
                    root,
                    task_id=task_id,
                    instance_id=instance_id,
                    field="agent_task_context",
                    severity="blocker",
                    leakage_class="intervention_policy_exposure",
                    detail="expected intervention behavior is visible to the evaluated agent",
                    suggested_repair="Keep evaluator adaptation policy outside the model prompt.",
                    line=line,
                )
            )

    visible_surfaces = _flatten_named_strings(payload)
    mutation_surfaces = _mutation_surfaces(instance)
    for field, text in [*visible_surfaces, *mutation_surfaces]:
        for pattern_name, pattern in PROMPT_INJECTION_PATTERNS:
            match = pattern.search(text)
            if match is None:
                continue
            findings.append(
                _finding(
                    path,
                    root,
                    task_id=task_id,
                    instance_id=instance_id,
                    field=field,
                    severity="blocker",
                    leakage_class="prompt_injection",
                    detail=(
                        f"{pattern_name}: matched `{_snippet(match.group(0))}`"
                    ),
                    suggested_repair=(
                        "Remove the injection string or explicitly isolate and "
                        "preregister it as a dedicated injection challenge."
                    ),
                    line=line,
                    unresolved_human_review_state=True,
                )
            )

    expected = instance.base_task.goal.expected_final_answer
    answer_leaves = _answer_leaves(expected)
    complete_expected = _complete_expected_text(expected)
    for field, text in visible_surfaces:
        lowered = text.casefold()
        spoiler_framed = _ANSWER_SPOILER_RE.search(text) is not None
        complete_answer_visible = (
            bool(complete_expected)
            and len(complete_expected) >= 12
            and complete_expected in lowered
            and not field.startswith("user_instruction")
        )
        for leaf in answer_leaves:
            leaf_lower = leaf.casefold()
            if len(leaf_lower) < 4 or leaf_lower not in lowered:
                continue
            # Success criteria, input entities, constraints, and source
            # evidence legitimately overlap individual answer leaves.  Treat
            # overlap as a blocker only when it is explicitly spoiler-framed,
            # or when the complete expected answer is copied into a
            # non-instruction surface.  The broader calibrated overlap scanner
            # remains responsible for corpus-level review.
            if not spoiler_framed and not complete_answer_visible:
                continue
            findings.append(
                _finding(
                    path,
                    root,
                    task_id=task_id,
                    instance_id=instance_id,
                    field=field,
                    severity="blocker",
                    leakage_class="gold_answer_exposure",
                    detail=f"gold fragment `{_snippet(leaf)}` appears in an agent-visible field",
                    suggested_repair=(
                        "Move evaluator answers out of the agent payload or rewrite "
                        "the visible field without the answer."
                    ),
                    line=line,
                )
            )
            break
    return _dedupe_findings(findings)


def _mutation_surfaces(
    instance: BenchmarkInstance,
) -> list[tuple[str, str]]:
    intervention = instance.intervention
    if intervention is None:
        intervention_surfaces: list[tuple[str, str]] = []
    else:
        intervention_surfaces = [
            *_flatten_named_strings(
                {"memory_patch": intervention.memory_patch},
                prefix="runtime_mutation",
            ),
            *_flatten_named_strings(
                {"tool_output_patch": intervention.tool_output_patch},
                prefix="runtime_mutation",
            ),
            *_flatten_named_strings(
                {"instruction_patch": intervention.instruction_patch},
                prefix="runtime_mutation",
            ),
        ]
    runtime_evidence = {
        key: instance.base_task.hidden_ground_truth.get(key)
        for key in ("web_site", "api_mock")
        if instance.base_task.hidden_ground_truth.get(key) is not None
    }
    return [
        *intervention_surfaces,
        *_flatten_named_strings(
            runtime_evidence,
            prefix="runtime_tool_evidence",
        ),
    ]


def _scan_registered_tool_surfaces(
    source_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    registry = ToolRegistry()
    surfaces = {
        "registered_tool_catalog": [
            spec.model_dump(mode="json") for spec in registry.specs()
        ],
        "registered_tool_knowledge_base": registry.knowledge_base,
    }
    findings: list[dict[str, Any]] = []
    for field, text in _flatten_named_strings(surfaces):
        for pattern_name, pattern in PROMPT_INJECTION_PATTERNS:
            match = pattern.search(text)
            if match is None:
                continue
            findings.append(
                _finding(
                    source_path,
                    root,
                    task_id=None,
                    instance_id=None,
                    field=field,
                    severity="blocker",
                    leakage_class="prompt_injection",
                    detail=(
                        f"{pattern_name}: matched `{_snippet(match.group(0))}`"
                    ),
                    suggested_repair=(
                        "Remove prompt-like instructions from shared tool "
                        "descriptions or deterministic tool evidence."
                    ),
                    unresolved_human_review_state=True,
                )
            )
    return _dedupe_findings(findings)


def _flatten_named_strings(
    value: Any,
    *,
    prefix: str = "",
) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []

    def visit(current: Any, path: str) -> None:
        if isinstance(current, dict):
            for key, item in current.items():
                child = f"{path}.{key}" if path else str(key)
                visit(item, child)
        elif isinstance(current, list):
            for index, item in enumerate(current):
                child = f"{path}[{index}]"
                visit(item, child)
        elif isinstance(current, str) and current.strip():
            output.append((path or "value", current))

    visit(value, prefix)
    return output


def _answer_leaves(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [
            leaf for item in value.values() for leaf in _answer_leaves(item)
        ]
    if isinstance(value, list):
        return [leaf for item in value for leaf in _answer_leaves(item)]
    if value is None:
        return []
    return [str(value).strip()]


def _complete_expected_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip().casefold()
    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).casefold()
    return str(value).strip().casefold() if value is not None else ""


def _finding(
    path: Path,
    root: Path,
    *,
    task_id: str | None,
    instance_id: str | None,
    field: str,
    severity: str,
    leakage_class: str,
    detail: str,
    suggested_repair: str,
    line: int | None = None,
    unresolved_human_review_state: bool = False,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "file": _relative(path, root),
        "task_id": task_id,
        "instance_id": instance_id,
        "field": field,
        "severity": severity,
        "leakage_class": leakage_class,
        "detail": detail,
        "suggested_repair": suggested_repair,
        "automatic_repair_status": "not_attempted",
        "unresolved_human_review_state": unresolved_human_review_state,
    }
    if line is not None:
        value["line"] = line
    return value


def _dedupe_findings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        key = (
            row.get("file"),
            row.get("instance_id"),
            row.get("field"),
            row.get("leakage_class"),
            row.get("detail"),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def _raw_base_task_id(row: Any) -> str | None:
    if not isinstance(row, dict):
        return None
    base = row.get("base_task")
    if isinstance(base, dict) and base.get("task_id"):
        return str(base["task_id"])
    return None


def _snippet(value: str, limit: int = 120) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized if len(normalized) <= limit else normalized[: limit - 1] + "…"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "PROMPT_INJECTION_PATTERNS",
    "scan_agent_visible_dataset",
    "scan_agent_visible_instance",
]
