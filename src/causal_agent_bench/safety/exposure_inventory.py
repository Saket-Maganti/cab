"""Build a payload-free inventory of protected material exposed in Git history."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.protected_heldout import (
    CONTAMINATION_REGISTRY_PATH,
)

_DISPOSITION_PRIORITY = {
    "PUBLIC_DEVELOPMENT_ONLY": 1,
    "PILOT_ONLY": 2,
    "CONTAMINATED_NOT_CONFIRMATORY": 3,
    "INVALID_FOR_FUTURE_EVALUATION": 4,
}
_ARCHIVE_SUFFIXES = (
    ".zip",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".gz",
    ".7z",
    ".rar",
)
_DIRECT_PROTECTED_NAME = re.compile(
    r"(heldout|held_out|challenge|private_manifest|private_data)",
    re.IGNORECASE,
)


def build_protected_exposure_inventory(
    repo_root: str | Path,
    *,
    contamination_registry_path: str | Path = CONTAMINATION_REGISTRY_PATH,
) -> dict[str, Any]:
    """Inspect every local Git revision without reproducing payload in output."""

    root = Path(repo_root).resolve()
    registry_path = _resolve(root, contamination_registry_path)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise ValueError("contamination registry must be a JSON object")
    records = [record for record in registry.get("records", []) if isinstance(record, dict)]
    commits = _git_lines(root, ["rev-list", "--all", "--reverse"])
    tracked_now = set(_git_lines(root, ["ls-files"]))
    history_paths = {
        path
        for commit in commits
        for path in _git_lines(root, ["ls-tree", "-r", "--name-only", commit])
    }
    path_records: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        exposure_commit = str(record.get("exposure_commit", ""))
        for prefix in record.get("path_prefixes", []):
            if not isinstance(prefix, str):
                continue
            for path in _git_lines(
                root,
                ["ls-tree", "-r", "--name-only", exposure_commit, "--", prefix],
            ):
                _append_record(path_records, path, record)
        for path in record.get("recipe_paths", []):
            if isinstance(path, str) and _git_object_exists(
                root,
                exposure_commit,
                path,
            ):
                _append_record(path_records, path, record)

        source = str(record.get("canonical_source_path", ""))
        source_content = _git_show(root, exposure_commit, source)
        identifiers = _base_task_identifiers(source_content)
        if identifiers:
            for path in _git_grep_paths(
                root,
                exposure_commit,
                identifiers,
            ):
                _append_record(path_records, path, record)

        reference_markers = [
            *[str(prefix) for prefix in record.get("path_prefixes", []) if isinstance(prefix, str)],
            *[str(path) for path in record.get("recipe_paths", []) if isinstance(path, str)],
        ]
        for commit in commits:
            for path in _git_grep_paths(root, commit, reference_markers):
                _append_record(path_records, path, record)

    for path in history_paths:
        lowered = path.lower()
        if _DIRECT_PROTECTED_NAME.search(path) or lowered.endswith(_ARCHIVE_SUFFIXES):
            matched = _records_for_path(path, records)
            for record in matched:
                _append_record(path_records, path, record)
            if not matched and _DIRECT_PROTECTED_NAME.search(path):
                # A named held-out artifact with no registry record is still
                # inventoried and receives the strictest default disposition.
                path_records.setdefault(path, [])

    artifacts: list[dict[str, Any]] = []
    for path in sorted(path_records):
        linked_records = path_records[path]
        first_commit = _first_exposure_commit(
            root,
            commits,
            path,
            linked_records,
        )
        if not first_commit:
            continue
        content = _git_show_bytes(root, first_commit, path)
        disposition = _strictest_disposition(linked_records)
        allowed_use = _allowed_future_use(linked_records, disposition)
        text = content.decode("utf-8", errors="replace")
        task_text_exposed = bool(
            re.search(
                r'"user_instruction"\s*:|goal\.user_instruction|task text',
                text,
                re.IGNORECASE,
            )
        )
        answer_exposed = bool(
            re.search(
                (
                    r'"expected_final_answer"\s*:|'
                    r'"hidden_ground_truth"\s*:|'
                    r'"gold_answer(?:_policy)?"\s*:|'
                    r'"scorer_policy"\s*:'
                ),
                text,
                re.IGNORECASE,
            )
        )
        intervention_exposed = bool(
            re.search(
                (
                    r'"intervention"\s*:|'
                    r'"intervention_id"\s*:|'
                    r'"tool_output_patch"\s*:|'
                    r'"memory_patch"\s*:|'
                    r'"expected_behavior"\s*:'
                ),
                text,
                re.IGNORECASE,
            )
        )
        evaluator_exposed = bool(
            re.search(
                (
                    r'"hidden_evaluator_context_fields"\s*:|'
                    r'"gold_answer_policy"\s*:|'
                    r'"scorer_policy"\s*:|'
                    r'"expected_behavior"\s*:|'
                    r'"success_criteria"\s*:'
                ),
                text,
                re.IGNORECASE,
            )
        )
        recipe_exposed = bool(
            re.search(
                r"(^|/)generate_.*\.(?:ya?ml|json)$",
                path,
                re.IGNORECASE,
            )
            and re.search(r"\bseed\s*:", text)
        )
        archive = path.lower().endswith(_ARCHIVE_SUFFIXES)
        notebook = path.lower().endswith(".ipynb")
        severity = _severity(
            task_text_exposed=task_text_exposed,
            answer_exposed=answer_exposed,
            intervention_exposed=intervention_exposed,
            evaluator_exposed=evaluator_exposed,
            recipe_exposed=recipe_exposed,
            archive=archive,
        )
        artifacts.append(
            {
                "path": path,
                "current_tracking_state": (
                    "TRACKED_PUBLIC"
                    if path in tracked_now
                    else "DELETED_BUT_PRESENT_IN_GIT_HISTORY"
                ),
                "exposure_commit": first_commit,
                "task_text_exposed": task_text_exposed,
                "answer_exposed": answer_exposed,
                "intervention_metadata_exposed": intervention_exposed,
                "evaluator_metadata_exposed": evaluator_exposed,
                "reversible_generation_recipe_exposed": recipe_exposed,
                "compressed_archive": archive,
                "notebook": notebook,
                "generated_bundle_or_audit": any(
                    token in path.lower()
                    for token in (
                        "audit",
                        "bundle",
                        "release",
                        "freeze_manifest",
                        "report",
                    )
                ),
                "severity": severity,
                "scientific_disposition": disposition,
                "allowed_future_use": allowed_use,
                "linked_contamination_records": sorted(
                    {
                        str(record.get("record_id"))
                        for record in linked_records
                        if record.get("record_id")
                    }
                ),
                "artifact_sha256_at_exposure": hashlib.sha256(content).hexdigest(),
            }
        )

    disposition_counts = Counter(str(artifact["scientific_disposition"]) for artifact in artifacts)
    severity_counts = Counter(str(artifact["severity"]) for artifact in artifacts)
    return {
        "schema_version": "cab_protected_heldout_exposure_inventory_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "All local Git revisions and current tracked files; content is "
            "classified in memory and never copied into this report."
        ),
        "evidence_class": "ENGINEERING_ONLY",
        "scientific_rule": (
            "Any payload exposed in public Git remains permanently ineligible "
            "for confirmatory, hidden-challenge, paper-eligible, or "
            "external-validity evidence. Deletion and history rewriting do not "
            "restore scientific secrecy."
        ),
        "repository": {
            "head": _git_scalar(root, ["rev-parse", "HEAD"]),
            "origin_main": _git_scalar(
                root,
                ["rev-parse", "--verify", "refs/remotes/origin/main"],
            ),
            "commit_count_scanned": len(commits),
            "history_rewritten": False,
        },
        "summary": {
            "artifact_count": len(artifacts),
            "tracked_public_artifact_count": sum(
                artifact["current_tracking_state"] == "TRACKED_PUBLIC" for artifact in artifacts
            ),
            "deleted_history_only_artifact_count": sum(
                artifact["current_tracking_state"] == "DELETED_BUT_PRESENT_IN_GIT_HISTORY"
                for artifact in artifacts
            ),
            "task_text_exposure_count": sum(
                bool(artifact["task_text_exposed"]) for artifact in artifacts
            ),
            "answer_exposure_count": sum(
                bool(artifact["answer_exposed"]) for artifact in artifacts
            ),
            "intervention_metadata_exposure_count": sum(
                bool(artifact["intervention_metadata_exposed"]) for artifact in artifacts
            ),
            "evaluator_metadata_exposure_count": sum(
                bool(artifact["evaluator_metadata_exposed"]) for artifact in artifacts
            ),
            "compressed_archive_count": sum(
                bool(artifact["compressed_archive"]) for artifact in artifacts
            ),
            "notebook_count": sum(bool(artifact["notebook"]) for artifact in artifacts),
            "severity_counts": dict(sorted(severity_counts.items())),
            "disposition_counts": dict(sorted(disposition_counts.items())),
        },
        "history_findings": {
            "deleted_protected_matches": [
                artifact["path"]
                for artifact in artifacts
                if artifact["current_tracking_state"] == "DELETED_BUT_PRESENT_IN_GIT_HISTORY"
            ],
            "tracked_compressed_archives_with_protected_references": [
                artifact["path"]
                for artifact in artifacts
                if artifact["compressed_archive"]
                and artifact["current_tracking_state"] == "TRACKED_PUBLIC"
            ],
            "tracked_notebooks_with_protected_references": [
                artifact["path"]
                for artifact in artifacts
                if artifact["notebook"] and artifact["current_tracking_state"] == "TRACKED_PUBLIC"
            ],
        },
        "artifacts": artifacts,
    }


def write_protected_exposure_inventory(
    repo_root: str | Path,
    output_path: str | Path,
) -> tuple[Path, dict[str, Any]]:
    root = Path(repo_root).resolve()
    output = _resolve(root, output_path)
    payload = build_protected_exposure_inventory(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output, payload


def _append_record(
    output: dict[str, list[dict[str, Any]]],
    path: str,
    record: dict[str, Any],
) -> None:
    record_id = record.get("record_id")
    if not any(existing.get("record_id") == record_id for existing in output[path]):
        output[path].append(record)


def _records_for_path(
    path: str,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if any(
            path.startswith(str(prefix))
            for prefix in record.get("path_prefixes", [])
            if isinstance(prefix, str)
        )
        or path
        in {str(value) for value in record.get("recipe_paths", []) if isinstance(value, str)}
    ]


def _base_task_identifiers(content: str) -> list[str]:
    identifiers: set[str] = set()
    for line in content.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, Mapping):
            value = row.get("task_id")
            if isinstance(value, str) and value:
                identifiers.add(value)
    return sorted(identifiers)


def _strictest_disposition(
    records: list[dict[str, Any]],
) -> str:
    if not records:
        return "INVALID_FOR_FUTURE_EVALUATION"
    return max(
        (str(record.get("scientific_disposition")) for record in records),
        key=lambda value: _DISPOSITION_PRIORITY.get(value, 99),
    )


def _allowed_future_use(
    records: list[dict[str, Any]],
    disposition: str,
) -> str:
    uses = sorted(
        {
            str(record.get("allowed_future_use"))
            for record in records
            if record.get("allowed_future_use")
        }
    )
    if uses:
        return " ".join(uses)
    if disposition == "INVALID_FOR_FUTURE_EVALUATION":
        return "Historical audit/provenance only; never future evaluation."
    return "Public development or pilot use under the recorded disposition only."


def _severity(
    *,
    task_text_exposed: bool,
    answer_exposed: bool,
    intervention_exposed: bool,
    evaluator_exposed: bool,
    recipe_exposed: bool,
    archive: bool,
) -> str:
    if archive or (task_text_exposed and answer_exposed):
        return "CRITICAL"
    if any(
        (
            task_text_exposed,
            answer_exposed,
            intervention_exposed,
            evaluator_exposed,
            recipe_exposed,
        )
    ):
        return "HIGH"
    return "MEDIUM"


def _git_grep_paths(
    root: Path,
    commit: str,
    patterns: list[str],
) -> list[str]:
    patterns = [value for value in patterns if value]
    if not patterns:
        return []
    process = subprocess.run(
        ["git", "grep", "-l", "-F", "-f", "-", commit, "--"],
        cwd=root,
        input="\n".join(patterns) + "\n",
        capture_output=True,
        text=True,
        check=False,
    )
    prefix = f"{commit}:"
    return sorted(
        {
            line[len(prefix) :] if line.startswith(prefix) else line
            for line in process.stdout.splitlines()
            if line.strip()
        }
    )


def _first_exposure_commit(
    root: Path,
    commits: list[str],
    path: str,
    records: list[dict[str, Any]],
) -> str | None:
    positions = {commit: index for index, commit in enumerate(commits)}
    recorded = sorted(
        {
            str(record.get("exposure_commit"))
            for record in records
            if str(record.get("exposure_commit")) in positions
            and _git_object_exists(
                root,
                str(record.get("exposure_commit")),
                path,
            )
        },
        key=lambda commit: positions[commit],
    )
    if recorded:
        return recorded[0]
    return next(
        (commit for commit in commits if _git_object_exists(root, commit, path)),
        None,
    )


def _git_object_exists(root: Path, commit: str, path: str) -> bool:
    process = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return process.returncode == 0


def _git_show(root: Path, commit: str, path: str) -> str:
    return _git_show_bytes(root, commit, path).decode(
        "utf-8",
        errors="replace",
    )


def _git_show_bytes(root: Path, commit: str, path: str) -> bytes:
    process = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return process.stdout if process.returncode == 0 else b""


def _git_lines(root: Path, args: list[str]) -> list[str]:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line.strip() for line in process.stdout.splitlines() if line.strip()]


def _git_scalar(root: Path, args: list[str]) -> str | None:
    values = _git_lines(root, args)
    return values[0] if values else None


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


__all__ = [
    "build_protected_exposure_inventory",
    "write_protected_exposure_inventory",
]
