"""Fail-closed validation for the real Compact-20 human-review packet.

This module deliberately ignores every file whose name or contents indicate
proxy, synthetic, fixture, template, or AI review.  It is a workflow gate, not
an annotation generator, and it never fills review rows.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_REVIEW_DIR = Path("data/human_validation/compact20_real_review")
DEFAULT_CANDIDATE_MANIFEST = Path("data/compact20_reviewed/compact20_reviewed_manifest.json")

REVIEW_FILES: dict[str, tuple[str, ...]] = {
    "task_clarity_review.csv": (
        "candidate_id",
        "clear_task",
        "notes",
        "reviewer_id",
        "timestamp",
    ),
    "gold_policy_review.csv": (
        "candidate_id",
        "gold_policy_valid",
        "notes",
        "reviewer_id",
        "timestamp",
    ),
    "intervention_isolation_review.csv": (
        "candidate_id",
        "isolation_valid",
        "goal_preserved",
        "notes",
        "reviewer_id",
        "timestamp",
    ),
}
ADJUDICATION_FILE = "adjudication_template.csv"
ADJUDICATION_COLUMNS = (
    "candidate_id",
    "final_decision",
    "adjudicator_id",
    "notes",
    "timestamp",
)
PLACEHOLDER_TOKENS = {
    "",
    "tbd",
    "todo",
    "unknown",
    "placeholder",
    "reviewer",
    "reviewer_id",
    "annotator",
    "anonymous",
    "ai",
    "proxy",
    "synthetic",
    "fixture",
}
POSITIVE_VALUES = {"yes", "true", "pass", "valid", "include", "1"}
NEGATIVE_VALUES = {"no", "false", "fail", "invalid", "exclude", "0"}


@dataclass(frozen=True)
class HumanReviewPolicy:
    """Preregistered engineering policy for the future Compact-20 review."""

    min_independent_reviewers: int = 2
    min_raw_agreement: float = 0.80
    require_all_final_valid: bool = True


def validate_compact20_human_reviews(
    repo_root: str | Path,
    *,
    review_dir: str | Path = DEFAULT_REVIEW_DIR,
    candidate_manifest: str | Path = DEFAULT_CANDIDATE_MANIFEST,
    policy: HumanReviewPolicy | None = None,
) -> dict[str, Any]:
    """Validate genuine rows and derive human/C10 state without inference."""

    root = Path(repo_root).resolve()
    review_root = _resolve(root, review_dir)
    manifest_path = _resolve(root, candidate_manifest)
    policy = policy or HumanReviewPolicy()
    candidate_ids = _candidate_ids(manifest_path)
    issues: list[dict[str, str]] = []
    rows_by_file: dict[str, list[dict[str, str]]] = {}

    for filename, required_columns in REVIEW_FILES.items():
        path = review_root / filename
        rows_by_file[filename] = _read_real_rows(
            path,
            required_columns=required_columns,
            issues=issues,
        )

    adjudication_rows = _read_real_rows(
        review_root / ADJUDICATION_FILE,
        required_columns=ADJUDICATION_COLUMNS,
        issues=issues,
        allow_empty=True,
    )
    adjudication_by_candidate = {
        row["candidate_id"]: row
        for row in adjudication_rows
        if row.get("candidate_id") and _valid_identity(row.get("adjudicator_id", ""))
    }

    coverage: dict[str, dict[str, Any]] = {}
    unresolved_disagreements: list[dict[str, str]] = []
    total_review_groups = 0
    agreeing_review_groups = 0
    final_validity: dict[str, bool | None] = {}

    for candidate_id in candidate_ids:
        candidate_summary: dict[str, Any] = {}
        candidate_final: list[bool] = []
        for filename, decision_columns in _decision_columns().items():
            matching = [
                row for row in rows_by_file[filename] if row.get("candidate_id") == candidate_id
            ]
            real_reviewers = {
                row["reviewer_id"].strip()
                for row in matching
                if _valid_identity(row.get("reviewer_id", ""))
            }
            decisions: list[bool] = []
            for row in matching:
                if not _valid_identity(row.get("reviewer_id", "")):
                    continue
                decision = _row_decision(row, decision_columns)
                if decision is not None:
                    decisions.append(decision)
            complete = (
                len(real_reviewers) >= policy.min_independent_reviewers
                and len(decisions) >= policy.min_independent_reviewers
            )
            agrees = complete and len(set(decisions)) == 1
            if complete:
                total_review_groups += 1
                if agrees:
                    agreeing_review_groups += 1
            adjudicated = candidate_id in adjudication_by_candidate
            if complete and not agrees and not adjudicated:
                unresolved_disagreements.append(
                    {
                        "candidate_id": candidate_id,
                        "review_file": filename,
                        "reason": "independent reviewers disagree and no adjudication exists",
                    }
                )
            final_decision = _final_decision(
                decisions=decisions,
                adjudication=adjudication_by_candidate.get(candidate_id),
            )
            if final_decision is not None:
                candidate_final.append(final_decision)
            candidate_summary[filename] = {
                "row_count": len(matching),
                "independent_reviewer_count": len(real_reviewers),
                "complete": complete,
                "agreement": agrees if complete else None,
                "adjudicated": adjudicated,
                "final_valid": final_decision,
            }
        coverage[candidate_id] = candidate_summary
        final_validity[candidate_id] = (
            all(candidate_final) if len(candidate_final) == len(REVIEW_FILES) else None
        )

    expected_groups = len(candidate_ids) * len(REVIEW_FILES)
    complete_groups = sum(
        int(summary["complete"])
        for candidate in coverage.values()
        for summary in candidate.values()
    )
    raw_agreement = (
        agreeing_review_groups / total_review_groups if total_review_groups else None
    )
    all_covered = expected_groups > 0 and complete_groups == expected_groups
    adjudication_complete = not unresolved_disagreements
    threshold_met = raw_agreement is not None and raw_agreement >= policy.min_raw_agreement
    all_final_valid = (
        bool(final_validity)
        and all(value is True for value in final_validity.values())
    )

    if not candidate_ids:
        human_state = "HUMAN_REVIEW_INCOMPLETE"
        c10_state = "C10_PENDING"
        issues.append(
            _issue("candidate_manifest", str(manifest_path), "candidate manifest is empty or missing")
        )
    elif not all_covered:
        human_state = "HUMAN_REVIEW_INCOMPLETE"
        c10_state = "C10_PENDING"
    elif not adjudication_complete:
        human_state = "ADJUDICATION_PENDING"
        c10_state = "C10_PENDING"
    elif not threshold_met or (policy.require_all_final_valid and not all_final_valid):
        human_state = "HUMAN_REVIEW_COMPLETE"
        c10_state = "C10_FAILED"
    else:
        human_state = "HUMAN_REVIEW_COMPLETE"
        c10_state = "PASS"

    genuine_rows = sum(len(rows) for rows in rows_by_file.values()) + len(adjudication_rows)
    return {
        "schema_version": "cab_human_review_gate_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "evidence_class": "HUMAN_INPUT_REQUIRED" if c10_state != "PASS" else "AUDITED_REAL_EVIDENCE",
        "review_dir": _relative(review_root, root),
        "candidate_manifest": _relative(manifest_path, root),
        "policy": {
            "min_independent_reviewers": policy.min_independent_reviewers,
            "min_raw_agreement": policy.min_raw_agreement,
            "require_all_final_valid": policy.require_all_final_valid,
            "policy_status": "DESIGN_ONLY_PREREGISTERED_BEFORE_REVIEW",
        },
        "candidate_count": len(candidate_ids),
        "expected_review_groups": expected_groups,
        "complete_review_groups": complete_groups,
        "genuine_human_row_count": genuine_rows,
        "proxy_rows_counted": 0,
        "raw_agreement": raw_agreement,
        "unresolved_disagreements": unresolved_disagreements,
        "coverage": coverage,
        "final_validity": final_validity,
        "issues": issues,
        "human_review_state": human_state,
        "c10_state": c10_state,
        "slice_lock_allowed": c10_state == "PASS",
        "paper_eligibility_allowed": False,
        "scientific_execution_allowed": False,
    }


def write_human_review_gate_report(
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _candidate_ids(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
    return sorted(
        {
            str(row.get("candidate_id", "")).strip()
            for row in candidates
            if isinstance(row, dict) and str(row.get("candidate_id", "")).strip()
        }
    )


def _read_real_rows(
    path: Path,
    *,
    required_columns: Iterable[str],
    issues: list[dict[str, str]],
    allow_empty: bool = False,
) -> list[dict[str, str]]:
    if not path.exists():
        issues.append(_issue("missing_file", str(path), "required review file is missing"))
        return []
    lowered_path = path.as_posix().lower()
    if any(token in lowered_path for token in ("proxy", "synthetic", "fixture", "ai_review")):
        issues.append(_issue("proxy_file_rejected", str(path), "proxy/synthetic review file rejected"))
        return []
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])
            missing = sorted(set(required_columns) - fieldnames)
            if missing:
                issues.append(
                    _issue("missing_columns", str(path), f"missing columns: {', '.join(missing)}")
                )
                return []
            rows = [
                {str(key): str(value or "").strip() for key, value in row.items()}
                for row in reader
            ]
    except (OSError, csv.Error) as exc:
        issues.append(_issue("unreadable_csv", str(path), type(exc).__name__))
        return []
    real_rows = [row for row in rows if _row_is_genuine(row)]
    if not real_rows and not allow_empty:
        issues.append(_issue("header_only", str(path), "no genuine completed human rows"))
    return real_rows


def _row_is_genuine(row: dict[str, str]) -> bool:
    joined = " ".join(row.values()).lower()
    if any(token in joined for token in ("ai_proxy", "not_human", "synthetic_review", "fixture_only")):
        return False
    identity = row.get("reviewer_id") or row.get("adjudicator_id") or ""
    if not _valid_identity(identity):
        return False
    if not row.get("candidate_id", "").strip():
        return False
    if not row.get("notes", "").strip():
        return False
    return bool(row.get("timestamp", "").strip())


def _valid_identity(value: str) -> bool:
    normalized = value.strip().lower()
    return bool(normalized) and normalized not in PLACEHOLDER_TOKENS and not any(
        token in normalized for token in ("proxy", "synthetic", "fixture", "placeholder")
    )


def _decision_columns() -> dict[str, tuple[str, ...]]:
    return {
        "task_clarity_review.csv": ("clear_task",),
        "gold_policy_review.csv": ("gold_policy_valid",),
        "intervention_isolation_review.csv": ("isolation_valid", "goal_preserved"),
    }


def _row_decision(row: dict[str, str], columns: tuple[str, ...]) -> bool | None:
    values: list[bool] = []
    for column in columns:
        normalized = row.get(column, "").strip().lower()
        if normalized in POSITIVE_VALUES:
            values.append(True)
        elif normalized in NEGATIVE_VALUES:
            values.append(False)
        else:
            return None
    return all(values)


def _final_decision(
    *,
    decisions: list[bool],
    adjudication: dict[str, str] | None,
) -> bool | None:
    if adjudication is not None:
        normalized = adjudication.get("final_decision", "").strip().lower()
        if normalized in POSITIVE_VALUES:
            return True
        if normalized in NEGATIVE_VALUES:
            return False
        return None
    if decisions and len(set(decisions)) == 1:
        return decisions[0]
    return None


def _issue(kind: str, path: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "path": path, "detail": detail}


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
