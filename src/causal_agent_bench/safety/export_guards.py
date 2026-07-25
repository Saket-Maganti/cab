from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from causal_agent_bench.runners.run_completion import infer_completion_state, load_run_metadata
from causal_agent_bench.safety.common import (
    WATERMARK_ENGINEERING_ONLY,
    WATERMARK_INCOMPLETE,
    WATERMARK_MOCK_STUB,
    WATERMARK_PLACEHOLDER,
    classify_run_entry,
    strict_bool,
)

EXPORT_OVERRIDE_FLAGS = (
    "allow_engineering_only",
    "allow_incomplete",
    "allow_placeholder",
    "allow_mock_stub",
)

ENGINEERING_ONLY_LEVELS = frozenset(
    {
        "deterministic_baseline_engineering",
        "engineering_only",
        "engineering_only_local_stub",
        "local_model_preliminary",
        "local_open_weight_unvalidated",
        "mock_diagnostic_only",
        "pilot_stub_engineering_only",
        "preliminary_or_engineering",
        "stub_engineering",
    }
)


@dataclass(frozen=True)
class SafetyIssue:
    kind: str
    message: str
    required_override: str | None
    watermark: str


def validate_export_source(
    run_dir: str | Path,
    *,
    allow_engineering_only: bool = False,
    allow_incomplete: bool = False,
    allow_placeholder: bool = False,
    allow_mock_stub: bool = False,
    operation: str = "paper-export",
) -> dict[str, Any]:
    """Conservative gate for paper asset export/fill. Raises ValueError when blocked."""

    run_path = Path(run_dir)
    metadata = load_run_metadata(run_path)
    state = infer_completion_state(run_path)
    entry = {
        "path": str(run_path),
        "run_id": run_path.name,
        "status": state["run_status"],
        "completion_state": state["completion_state"],
        "scientific_evidence": state["scientific_evidence"],
        "evidence_level": state["evidence_level"],
        "agents": metadata.get("agents") or [],
        "run_name": metadata.get("run_name"),
    }
    classified = classify_run_entry(entry, run_path.parent.parent)

    issues = _collect_safety_issues(
        run_path=run_path,
        metadata=metadata,
        state=state,
        classified=classified,
    )
    overrides = {
        "allow_engineering_only": allow_engineering_only,
        "allow_incomplete": allow_incomplete,
        "allow_placeholder": allow_placeholder,
        "allow_mock_stub": allow_mock_stub,
    }
    unresolved = [
        issue
        for issue in issues
        if issue.required_override is None or not overrides.get(issue.required_override, False)
    ]

    if unresolved:
        details = "; ".join(
            issue.message
            if issue.required_override is None
            else f"{issue.message} (requires --{issue.required_override.replace('_', '-')})"
            for issue in unresolved
        )
        raise ValueError(f"refusing {operation} on {run_path.name}: {details}")

    classification = classified["classification"]
    watermark = _combined_watermark(issues) or _default_watermark(classification, allow_engineering_only)

    return {
        "allowed": True,
        "watermark": watermark or _default_watermark(classification, allow_engineering_only),
        "classification": classification,
        "issues": [issue.message for issue in issues],
        "issue_details": [
            {
                "kind": issue.kind,
                "message": issue.message,
                "required_override": issue.required_override,
                "watermark": issue.watermark,
            }
            for issue in issues
        ],
        "requires_watermark": bool(issues) or not classified["paper_eligible"],
    }


def apply_export_watermark(text: str, watermark: str | None) -> str:
    if not watermark:
        return text
    stripped = text.lstrip()
    if stripped.startswith(("%", "\\")):
        visible = "\\noindent\\textbf{Evidence warning.} " + _latex_escape(watermark) + "\n\n"
        return f"% {watermark}\n{visible}{text}"
    return f"**Evidence warning:** {watermark}\n\n{text}"


def _collect_safety_issues(
    *,
    run_path: Path,
    metadata: dict[str, Any],
    state: dict[str, Any],
    classified: dict[str, Any],
) -> list[SafetyIssue]:
    issues: list[SafetyIssue] = []
    classification = classified["classification"]
    scope = str(metadata.get("evidence_scope") or state.get("evidence_level") or "").lower()
    evidence_level = str(state.get("evidence_level") or classified.get("evidence_level") or "").lower()
    provider_type = str(metadata.get("provider_type") or classified.get("provider_type") or "").lower()

    if state["completion_state"] != "complete":
        issues.append(
            SafetyIssue(
                kind="incomplete",
                message=f"run incomplete ({state['completed_trajectories']}/{state['expected_trajectories']})",
                required_override="allow_incomplete",
                watermark=WATERMARK_INCOMPLETE,
            )
        )
    if state.get("run_status") == "interrupted" or (run_path / "INCOMPLETE_RUN.json").exists():
        issues.append(
            SafetyIssue(
                kind="interrupted",
                message="run interrupted or INCOMPLETE_RUN.json present",
                required_override="allow_incomplete",
                watermark=WATERMARK_INCOMPLETE,
            )
        )
    if not metadata:
        issues.append(
            SafetyIssue(
                kind="missing_metadata",
                message="missing run metadata",
                required_override=None,
                watermark="MISSING METADATA -- NOT SCIENTIFIC EVIDENCE -- NOT SAFE FOR MAIN RESULTS",
            )
        )
        return _dedupe_issues(issues)

    if strict_bool(metadata.get("placeholder")):
        issues.append(
            SafetyIssue(
                kind="placeholder",
                message="run metadata marked placeholder",
                required_override="allow_placeholder",
                watermark=WATERMARK_PLACEHOLDER,
            )
        )

    if (
        classification in {"mock_diagnostic", "stub_engineering"}
        or "mock" in scope
        or "stub" in scope
        or "oracle" in scope
        or "synthetic" in scope
        or provider_type in {"mock", "stub", "oracle", "synthetic", "fake"}
        or strict_bool(metadata.get("not_real_llm_behavior"))
        or str(metadata.get("deployment_class") or "").lower() == "mock_diagnostic_only"
        or _oracle_only(metadata)
    ):
        issues.append(
            SafetyIssue(
                kind="mock_stub_or_oracle",
                message=f"mock/stub/oracle/synthetic evidence source (classification={classification}, scope={scope or 'unknown'})",
                required_override="allow_mock_stub",
                watermark=WATERMARK_MOCK_STUB,
            )
        )

    if (
        not strict_bool(metadata.get("scientific_evidence", state.get("scientific_evidence")))
        or strict_bool(metadata.get("engineering_only"))
        or classified.get("scientific_evidence") is False
        or classification in {"complete_engineering_only", "local_preliminary"}
        or scope in ENGINEERING_ONLY_LEVELS
        or evidence_level in ENGINEERING_ONLY_LEVELS
        or "engineering" in scope
        or "engineering" in evidence_level
    ):
        issues.append(
            SafetyIssue(
                kind="engineering_only",
                message="scientific_evidence=false or source is engineering-only",
                required_override="allow_engineering_only",
                watermark=WATERMARK_ENGINEERING_ONLY,
            )
        )

    return _dedupe_issues(issues)


def _oracle_only(metadata: dict[str, Any]) -> bool:
    agents = [str(agent).lower() for agent in metadata.get("agents") or []]
    if agents and all("oracle" in agent for agent in agents):
        return True
    agent_runs = metadata.get("agent_runs") or []
    run_agents = [
        str(run.get("agent") or run.get("name") or "").lower()
        for run in agent_runs
        if isinstance(run, dict)
    ]
    return bool(run_agents) and all("oracle" in agent for agent in run_agents)


def _dedupe_issues(issues: list[SafetyIssue]) -> list[SafetyIssue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[SafetyIssue] = []
    for issue in issues:
        key = (issue.kind, issue.required_override or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped


def _combined_watermark(issues: list[SafetyIssue]) -> str | None:
    if not issues:
        return None
    labels = list(dict.fromkeys(issue.watermark for issue in issues))
    if any(issue.required_override is not None for issue in issues):
        labels.append("NOT SCIENTIFIC EVIDENCE -- NOT SAFE FOR MAIN RESULTS")
    return " | ".join(labels)


def _default_watermark(classification: str, allow_engineering_only: bool) -> str | None:
    if classification in {"mock_diagnostic", "stub_engineering"}:
        return WATERMARK_MOCK_STUB
    if allow_engineering_only or classification == "complete_engineering_only":
        return WATERMARK_ENGINEERING_ONLY
    return None


def _latex_escape(text: str) -> str:
    escaped = str(text)
    for key, value in {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
    }.items():
        escaped = escaped.replace(key, value)
    return escaped
