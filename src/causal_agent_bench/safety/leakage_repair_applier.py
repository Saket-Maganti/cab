"""Safe leakage-patch applier with mandatory preview + reviewed-apply gates.

The applier supports two phases:

1. **Preview (default).** Loads a proposed patch manifest, the user's selected
   ``operation_id`` set, and produces a deterministic patch preview JSON/MD
   plus a no-op audit log. No file is written or modified. Manifest blocker
   conditions (touches results/, mutates claim ledger, promotes
   ``scientific_evidence``, etc.) refuse the preview.
2. **Apply.** Requires ``--apply``, a ``--reviewed-ops`` file listing the
   exact ``operation_id`` values approved by a human, ``--reviewed-by`` and
   ``--approval-note`` arguments. The applier still refuses any operation that
   is not a deterministic ID rename and any operation flagged
   ``requires_manual_review`` or with content/split impact.

Hard refusal rules:

* Never apply ``remove_prompt_answer_leakage`` (content edits).
* Never apply ``update_split_assignment`` or ``correct_split_metadata`` (split
  movement). Those remain preview-only.
* Never apply ``mark_false_positive`` (suppression must go through the YAML
  suppression registry).
* Never apply when the manifest validator marked the manifest invalid.
* Never touch ``results/``, ``claim_ledger``, ``paper`` paths, run metadata,
  or provider approvals.
* Never set ``scientific_evidence=true``, ``paper_eligible=true``,
  ``allow_paid_calls=true``.
* Never apply all operations by default; the operator must list IDs.

Apply-mode actions are limited to deterministic ``rename_instance_id``
operations on JSONL dataset files inside ``data/`` whose ``new_id`` does not
collide with any existing identifier. Every applied change is recorded with
SHA-1 hashes of the pre- and post-patch file contents.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

APPLIABLE_OP_TYPES = frozenset({"rename_instance_id"})
PREVIEW_ONLY_OP_TYPES = frozenset(
    {
        "remove_prompt_answer_leakage",
        "update_split_assignment",
        "correct_split_metadata",
        "mark_false_positive",
        "manual_review_required",
    }
)
FORBIDDEN_PATH_PARTS = ("results/", "claim_ledger", "claim_evidence", "paper/", "release/")
FORBIDDEN_KEYS = frozenset({"scientific_evidence", "allow_paid_calls", "paper_eligible", "promote_to_supported"})
ID_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+")


def build_leakage_patch_preview(
    repo_root: str | Path,
    *,
    manifest_path: str | Path,
    selected_ops: list[str] | None = None,
    output_dir: str | Path = "reports/leakage_repair_apply",
) -> dict[str, Any]:
    """Run preview mode for the requested operations. No files are modified."""

    return _run(
        repo_root,
        manifest_path=manifest_path,
        selected_ops=selected_ops or [],
        apply=False,
        reviewed_ops_path=None,
        reviewed_by=None,
        approval_note=None,
        output_dir=output_dir,
    )


def build_reviewed_ops_template(
    repo_root: str | Path,
    *,
    manifest_path: str | Path,
    output_dir: str | Path = "reports/leakage_repair_apply",
    include_only: str = "safe_to_auto_patch",
) -> dict[str, Any]:
    """Emit a reviewed-ops review template (Markdown + JSON) for advisor sign-off.

    The template lists each candidate-auto-patch operation with the metadata
    a human reviewer needs (old/new IDs, affected files, classification,
    rationale) so they can decide which operation_ids to approve. It writes a
    *blank* reviewed-ops file (no IDs preselected) — the reviewer adds IDs
    manually after inspection.

    ``include_only`` selects which operations are listed:
      - ``safe_to_auto_patch`` (default): only deterministic ID renames marked
        ``safe_to_auto_patch=true`` in the manifest.
      - ``all``: every operation, useful for full-context audits (still no IDs
        preselected).

    The template does not approve anything by itself. It is a worksheet.
    """

    root = Path(repo_root).resolve()
    manifest = Path(manifest_path)
    if not manifest.is_absolute():
        manifest = root / manifest
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    payload = _read_json(manifest) or {}
    operations = payload.get("operations") if isinstance(payload.get("operations"), list) else []
    if include_only not in {"safe_to_auto_patch", "all"}:
        raise ValueError("include_only must be 'safe_to_auto_patch' or 'all'.")
    if include_only == "safe_to_auto_patch":
        candidates = [op for op in operations if isinstance(op, dict) and op.get("safe_to_auto_patch")]
    else:
        candidates = [op for op in operations if isinstance(op, dict)]

    rows: list[dict[str, Any]] = []
    for op in candidates:
        details = op.get("details") if isinstance(op.get("details"), dict) else {}
        rows.append(
            {
                "operation_id": str(op.get("operation_id") or ""),
                "type": str(op.get("type") or ""),
                "classification": str(op.get("classification") or ""),
                "reason": str(op.get("reason") or ""),
                "requires_manual_review": bool(op.get("requires_manual_review", True)),
                "safe_to_auto_patch": bool(op.get("safe_to_auto_patch", False)),
                "candidate_auto_patch": bool(op.get("candidate_auto_patch", False)),
                "details": details,
                "affected_files": list(op.get("affected_files") or []),
            }
        )

    json_path = out / "reviewed_ops_template.json"
    md_path = out / "reviewed_ops_template.md"
    blank_path = out / "reviewed_ops_blank.txt"

    template_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Advisor-facing review worksheet. This file does not approve any operation. "
            "Add operation_ids to reviewed_ops_blank.txt only after inspecting each row."
        ),
        "manifest_path": str(manifest),
        "include_only": include_only,
        "candidate_count": len(rows),
        "rows": rows,
        "blank_reviewed_ops_path": str(blank_path),
        "summary": {
            "candidate_count": len(rows),
            "include_only": include_only,
            "blank_reviewed_ops_path": str(blank_path),
            "ids_preselected": False,
        },
        "verdicts": {
            "ids_preselected": False,
            "approvals_recorded": False,
            "worksheet_only": True,
        },
        "instructions": [
            "1. Review each candidate row below.",
            "2. Confirm the operation type is `rename_instance_id` and `safe_to_auto_patch=true`.",
            "3. Confirm the affected_files all live inside `data/` and never touch `results/`, claim_ledger, paper, or release/.",
            "4. Append only the approved operation_ids (one per line) to reviewed_ops_blank.txt.",
            "5. Run `apply-leakage-patch --manifest <manifest> --selected-op <id> ... --reviewed-ops reviewed_ops_blank.txt --reviewed-by <you> --approval-note '<why>' --apply`.",
            "6. Re-run `all-no-run-reports` to confirm the leakage repair clusters disappear.",
        ],
    }

    json_path.write_text(json.dumps(template_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_reviewed_ops_template_markdown(template_payload), encoding="utf-8")
    if not blank_path.exists():
        blank_path.write_text(
            "# Add the approved operation_ids one per line.\n"
            "# Lines starting with '#' are ignored.\n",
            encoding="utf-8",
        )

    template_payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path), "blank": str(blank_path)}
    return template_payload


def _reviewed_ops_template_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Reviewed-Ops Template",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        f"Manifest: `{payload['manifest_path']}`",
        f"Candidate count ({payload['include_only']}): {payload['candidate_count']}",
        f"Blank reviewed-ops file: `{payload['blank_reviewed_ops_path']}`",
        "",
        "## Instructions",
        "",
    ]
    for step in payload["instructions"]:
        lines.append(f"- {step}")
    lines.extend(["", "## Candidates (no rows are pre-approved)", ""])
    if not payload["rows"]:
        lines.append("- (none — no candidate-auto-patch operations in this manifest)")
    for row in payload["rows"][:200]:
        details = row.get("details") or {}
        files = ", ".join(row.get("affected_files") or [])[:160] or "(none)"
        lines.append(
            f"- `{row['operation_id']}` `{row['type']}` class=`{row['classification']}` "
            f"safe_to_auto_patch=`{row['safe_to_auto_patch']}` -> {row['reason']}"
        )
        if row["type"] == "rename_instance_id":
            lines.append(f"  - Rename `{details.get('old_id')}` -> `{details.get('new_id')}`")
        lines.append(f"  - Affected files: {files}")
    if len(payload["rows"]) > 200:
        lines.append(f"- ... {len(payload['rows']) - 200} more rows in JSON.")
    lines.append("")
    return "\n".join(lines)


def apply_leakage_patch(
    repo_root: str | Path,
    *,
    manifest_path: str | Path,
    selected_ops: list[str],
    reviewed_ops_path: str | Path,
    reviewed_by: str,
    approval_note: str,
    output_dir: str | Path = "reports/leakage_repair_apply",
) -> dict[str, Any]:
    """Apply only the approved deterministic ID renames.

    All other operation types remain preview-only and are recorded in the
    refusal log without modifying files.
    """

    if not selected_ops:
        raise ValueError("apply_leakage_patch requires explicit selected_ops; refusing to apply all operations.")
    if not reviewed_by:
        raise ValueError("apply_leakage_patch requires reviewed_by.")
    if not approval_note:
        raise ValueError("apply_leakage_patch requires approval_note.")
    if not reviewed_ops_path:
        raise ValueError("apply_leakage_patch requires reviewed_ops_path.")
    return _run(
        repo_root,
        manifest_path=manifest_path,
        selected_ops=selected_ops,
        apply=True,
        reviewed_ops_path=reviewed_ops_path,
        reviewed_by=reviewed_by,
        approval_note=approval_note,
        output_dir=output_dir,
    )


def _run(
    repo_root: str | Path,
    *,
    manifest_path: str | Path,
    selected_ops: list[str],
    apply: bool,
    reviewed_ops_path: str | Path | None,
    reviewed_by: str | None,
    approval_note: str | None,
    output_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    manifest = Path(manifest_path)
    if not manifest.is_absolute():
        manifest = root / manifest
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)

    manifest_payload = _read_json(manifest) or {}
    operations = manifest_payload.get("operations") if isinstance(manifest_payload.get("operations"), list) else []
    selected_set = list(dict.fromkeys(selected_ops))
    reviewed_set: list[str] = []
    if reviewed_ops_path is not None:
        reviewed_set = _read_reviewed_ops(reviewed_ops_path, root)

    actions: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    refusals: list[dict[str, Any]] = []

    if not selected_set:
        refusals.append(
            {
                "severity": "blocker",
                "id": "no_selected_operations",
                "operation_id": None,
                "message": (
                    "No --selected-ops were provided. The applier refuses to apply all operations by "
                    "default; the operator must list each operation_id explicitly."
                ),
            }
        )

    manifest_validation = _validate_manifest_safety(manifest_payload)
    refusals.extend(manifest_validation)

    if apply and not reviewed_set:
        refusals.append(
            {
                "severity": "blocker",
                "id": "reviewed_ops_required_for_apply",
                "operation_id": None,
                "message": "Apply mode requires --reviewed-ops file listing approved operation_id values.",
            }
        )

    if apply and refusals:
        # Hard-refuse apply mode if anything looks unsafe at the manifest level.
        return _final_payload(
            root=root,
            manifest=manifest,
            mode="apply_refused",
            apply=apply,
            reviewed_by=reviewed_by,
            approval_note=approval_note,
            selected_set=selected_set,
            reviewed_set=reviewed_set,
            actions=actions,
            applied=applied,
            refusals=refusals,
            output_dir=out,
        )

    operation_by_id = {str(op.get("operation_id")): op for op in operations if isinstance(op, dict)}
    for op_id in selected_set:
        op = operation_by_id.get(op_id)
        if op is None:
            refusals.append(
                {
                    "severity": "blocker",
                    "id": "operation_not_found",
                    "operation_id": op_id,
                    "message": f"Operation `{op_id}` is not in the manifest.",
                }
            )
            continue
        decision = _classify_operation(op, apply=apply, reviewed_set=reviewed_set)
        if decision["category"] == "applied":
            try:
                applied.append(_apply_id_rename(root, op))
                actions.append(
                    {
                        "operation_id": op_id,
                        "type": op.get("type"),
                        "category": "applied",
                        "reason": decision["reason"],
                    }
                )
            except _ApplierError as exc:
                refusals.append(
                    {
                        "severity": "blocker",
                        "id": exc.refusal_id,
                        "operation_id": op_id,
                        "message": exc.message,
                    }
                )
        else:
            actions.append(
                {
                    "operation_id": op_id,
                    "type": op.get("type"),
                    "category": decision["category"],
                    "reason": decision["reason"],
                }
            )
            if decision["category"] == "refused":
                refusals.append(
                    {
                        "severity": "blocker",
                        "id": decision["refusal_id"],
                        "operation_id": op_id,
                        "message": decision["reason"],
                    }
                )

    mode = (
        "apply_refused"
        if apply and refusals
        else "apply"
        if apply
        else "preview"
    )
    return _final_payload(
        root=root,
        manifest=manifest,
        mode=mode,
        apply=apply,
        reviewed_by=reviewed_by,
        approval_note=approval_note,
        selected_set=selected_set,
        reviewed_set=reviewed_set,
        actions=actions,
        applied=applied,
        refusals=refusals,
        output_dir=out,
    )


def _final_payload(
    *,
    root: Path,
    manifest: Path,
    mode: str,
    apply: bool,
    reviewed_by: str | None,
    approval_note: str | None,
    selected_set: list[str],
    reviewed_set: list[str],
    actions: list[dict[str, Any]],
    applied: list[dict[str, Any]],
    refusals: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Leakage-patch preview/apply only. Apply mode is restricted to deterministic "
            "rename_instance_id operations that have been explicitly approved. Content edits, "
            "split moves, and suppressions remain preview-only."
        ),
        "mode": mode,
        "apply_requested": apply,
        "apply_succeeded": mode == "apply" and not refusals,
        "manifest_path": str(manifest),
        "reviewed_by": reviewed_by,
        "approval_note": approval_note,
        "selected_operation_ids": selected_set,
        "reviewed_operation_ids": reviewed_set,
        "actions": actions,
        "applied_changes": applied,
        "refusals": refusals,
        "summary": {
            "selected_count": len(selected_set),
            "applied_count": len(applied),
            "previewed_count": sum(1 for action in actions if action["category"] in {"preview", "preview_only"}),
            "refused_count": sum(1 for action in actions if action["category"] == "refused"),
            "manifest_refusal_count": sum(1 for refusal in refusals if refusal.get("operation_id") is None),
        },
        "verdicts": {
            "patches_applied": mode == "apply" and bool(applied) and not refusals,
            "manifest_blocked": any(
                refusal.get("source") == "manifest_validation" or refusal.get("operation_id") is None
                for refusal in refusals
            ),
        },
        "audit_log": {
            "reviewed_by": reviewed_by,
            "approval_note": approval_note,
            "reviewed_operation_ids": reviewed_set,
            "applied_changes": applied,
        },
    }
    md = leakage_patch_apply_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="leakage_patch_apply_report",
        payload=payload,
        markdown=md,
        output_dir=output_dir,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return payload


def leakage_patch_apply_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Leakage Patch Apply Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Mode: `{payload['mode']}`",
                f"- Apply requested: `{payload['apply_requested']}`",
                f"- Apply succeeded: `{payload['apply_succeeded']}`",
                f"- Selected operations: {summary['selected_count']}",
                f"- Applied operations: {summary['applied_count']}",
                f"- Preview-only operations: {summary['previewed_count']}",
                f"- Refused operations: {summary['refused_count']}",
                f"- Manifest-level refusals: {summary['manifest_refusal_count']}",
                f"- Reviewed by: `{payload['reviewed_by'] or '(not provided)'}`",
                f"- Approval note: {payload['approval_note'] or '(not provided)'}",
            ],
        ),
        "## Actions",
        "",
    ]
    if not payload["actions"]:
        lines.append("- (none)")
    for action in payload["actions"]:
        lines.append(
            f"- `{action['operation_id']}` `{action.get('type', 'unknown')}` -> `{action['category']}`: {action['reason']}"
        )
    lines.extend(["", "## Applied Changes", ""])
    if not payload["applied_changes"]:
        lines.append("- (none)")
    for change in payload["applied_changes"]:
        lines.append(
            f"- `{change['operation_id']}` rename `{change['old_id']}` -> `{change['new_id']}` "
            f"(files updated: {len(change['files'])})"
        )
        for entry in change["files"]:
            lines.append(
                f"  - `{entry['path']}` pre_hash={entry['pre_hash']} post_hash={entry['post_hash']} "
                f"matches={entry['matches_replaced']}"
            )
    lines.extend(["", "## Refusals", ""])
    if not payload["refusals"]:
        lines.append("- (none)")
    for refusal in payload["refusals"]:
        lines.append(
            f"- `{refusal['severity']}` `{refusal['id']}` `{refusal.get('operation_id', '-')}`: {refusal['message']}"
        )
    lines.append("")
    return "\n".join(lines)


def _validate_manifest_safety(manifest_payload: dict[str, Any]) -> list[dict[str, Any]]:
    refusals: list[dict[str, Any]] = []
    if not manifest_payload:
        refusals.append(
            {
                "severity": "blocker",
                "id": "manifest_not_parseable",
                "operation_id": None,
                "source": "manifest_validation",
                "message": "Patch manifest is missing or not parseable.",
            }
        )
        return refusals
    operations = manifest_payload.get("operations") if isinstance(manifest_payload.get("operations"), list) else []
    for op in operations:
        if not isinstance(op, dict):
            continue
        op_id = str(op.get("operation_id") or op.get("type") or "operation")
        for affected in op.get("affected_files") or []:
            text = str(affected).replace("\\", "/").lower()
            if any(forbidden in text for forbidden in FORBIDDEN_PATH_PARTS):
                refusals.append(
                    {
                        "severity": "blocker",
                        "id": "manifest_touches_forbidden_path",
                        "operation_id": op_id,
                        "source": "manifest_validation",
                        "message": f"Operation `{op_id}` affects forbidden path `{affected}`.",
                    }
                )
        if _contains_true_marker(op):
            refusals.append(
                {
                    "severity": "blocker",
                    "id": "manifest_promotes_evidence",
                    "operation_id": op_id,
                    "source": "manifest_validation",
                    "message": f"Operation `{op_id}` would set a forbidden evidence/paid-call marker.",
                }
            )
    return refusals


def _classify_operation(
    op: dict[str, Any],
    *,
    apply: bool,
    reviewed_set: list[str],
) -> dict[str, Any]:
    op_id = str(op.get("operation_id") or "")
    op_type = str(op.get("type") or "")
    if not op_type:
        return {
            "category": "refused",
            "refusal_id": "operation_missing_type",
            "reason": f"Operation `{op_id}` is missing a type.",
        }
    if op_type in PREVIEW_ONLY_OP_TYPES:
        return {
            "category": "preview_only",
            "reason": f"`{op_type}` is preview-only and requires manual dataset edits.",
        }
    if op_type not in APPLIABLE_OP_TYPES:
        return {
            "category": "refused",
            "refusal_id": "unsupported_operation_type",
            "reason": f"Operation type `{op_type}` is not supported by the applier.",
        }
    if op.get("requires_manual_review") and not op.get("safe_to_auto_patch"):
        return {
            "category": "refused",
            "refusal_id": "requires_manual_review",
            "reason": f"Operation `{op_id}` is marked manual-review only.",
        }
    if not apply:
        return {"category": "preview", "reason": "Preview mode: no files were modified."}
    if op_id not in reviewed_set:
        return {
            "category": "refused",
            "refusal_id": "operation_not_reviewed",
            "reason": f"Operation `{op_id}` is not listed in the reviewed-ops file.",
        }
    if not op.get("safe_to_auto_patch"):
        return {
            "category": "refused",
            "refusal_id": "operation_not_marked_safe_to_auto_patch",
            "reason": f"Operation `{op_id}` is not marked safe_to_auto_patch=true in the manifest.",
        }
    return {"category": "applied", "reason": "Deterministic ID rename approved and applied."}


class _ApplierError(Exception):
    def __init__(self, refusal_id: str, message: str) -> None:
        super().__init__(message)
        self.refusal_id = refusal_id
        self.message = message


def _apply_id_rename(root: Path, op: dict[str, Any]) -> dict[str, Any]:
    details = op.get("details") if isinstance(op.get("details"), dict) else {}
    old_id = str(details.get("old_id") or "")
    new_id = str(details.get("new_id") or "")
    if not old_id or not new_id:
        raise _ApplierError("id_rename_missing_ids", "Operation is missing old_id or new_id in details.")
    if old_id == new_id:
        raise _ApplierError("id_rename_noop", "old_id and new_id are identical.")
    if not _id_safe(old_id) or not _id_safe(new_id):
        raise _ApplierError("id_rename_unsafe_characters", "IDs contain unsafe characters.")
    affected = [str(item) for item in (op.get("affected_files") or [])]
    if not affected:
        raise _ApplierError("id_rename_no_affected_files", "Operation has no affected_files to update.")
    # Global pre-flight: refuse if the new_id already appears anywhere under data/.
    if _new_id_appears_globally(root, new_id):
        raise _ApplierError(
            "id_rename_new_id_collision_global",
            f"new_id `{new_id}` already appears somewhere under data/; choose a different new_id.",
        )
    file_entries: list[dict[str, Any]] = []
    for relative in affected:
        path = Path(relative)
        if not path.is_absolute():
            path = root / path
        normalized = str(path).replace("\\", "/").lower()
        if any(forbidden in normalized for forbidden in FORBIDDEN_PATH_PARTS):
            raise _ApplierError("id_rename_forbidden_path", f"Refusing to edit forbidden path `{relative}`.")
        data_root = (root / "data").resolve()
        try:
            resolved = path.resolve()
        except OSError as exc:
            raise _ApplierError("id_rename_path_unresolvable", f"Cannot resolve path `{relative}`: {exc}") from exc
        if not _is_within(resolved, data_root):
            raise _ApplierError("id_rename_path_outside_data", f"Refusing to edit path outside data/: `{relative}`.")
        if not path.exists():
            raise _ApplierError("id_rename_file_missing", f"Target file `{relative}` does not exist.")
        if "/frozen/" in str(resolved).replace("\\", "/"):
            raise _ApplierError(
                "id_rename_path_in_frozen",
                f"Refusing to edit frozen dataset file `{relative}`. Frozen content has external hashes.",
            )
        text = path.read_text(encoding="utf-8")
        if new_id in text:
            raise _ApplierError("id_rename_new_id_collision", f"new_id `{new_id}` already present in `{relative}`.")
        matches = _count_token_matches(text, old_id)
        if matches == 0:
            raise _ApplierError("id_rename_old_id_not_found", f"old_id `{old_id}` not found in `{relative}`.")
        new_text = _replace_token(text, old_id, new_id)
        pre_hash = hashlib.sha1(text.encode("utf-8")).hexdigest()
        post_hash = hashlib.sha1(new_text.encode("utf-8")).hexdigest()
        path.write_text(new_text, encoding="utf-8")
        file_entries.append(
            {
                "path": str(path),
                "matches_replaced": matches,
                "pre_hash": pre_hash,
                "post_hash": post_hash,
            }
        )
    return {
        "operation_id": str(op.get("operation_id")),
        "old_id": old_id,
        "new_id": new_id,
        "files": file_entries,
    }


def _new_id_appears_globally(root: Path, new_id: str) -> bool:
    data_root = root / "data"
    if not data_root.exists():
        return False
    for path in sorted(data_root.glob("**/*.jsonl")):
        if "/frozen/" in str(path).replace("\\", "/"):
            continue
        try:
            if new_id in path.read_text(encoding="utf-8"):
                return True
        except (OSError, UnicodeDecodeError):
            continue
    for path in sorted(data_root.glob("**/*.json")):
        if "/frozen/" in str(path).replace("\\", "/"):
            continue
        try:
            if new_id in path.read_text(encoding="utf-8"):
                return True
        except (OSError, UnicodeDecodeError):
            continue
    return False


def _id_safe(value: str) -> bool:
    if not value:
        return False
    return bool(ID_TOKEN_RE.fullmatch(value))


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _count_token_matches(text: str, token: str) -> int:
    pattern = re.compile(rf"(?<![A-Za-z0-9_./:-]){re.escape(token)}(?![A-Za-z0-9_./:-])")
    return len(pattern.findall(text))


def _replace_token(text: str, old: str, new: str) -> str:
    pattern = re.compile(rf"(?<![A-Za-z0-9_./:-]){re.escape(old)}(?![A-Za-z0-9_./:-])")
    return pattern.sub(new, text)


def _read_reviewed_ops(path: str | Path, root: Path) -> list[str]:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = root / file_path
    if not file_path.exists():
        return []
    if file_path.suffix.lower() in {".json"}:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if isinstance(payload, list):
            return [str(value) for value in payload]
        if isinstance(payload, dict):
            ops = payload.get("reviewed_operation_ids") or payload.get("operations") or payload.get("operation_ids") or []
            if isinstance(ops, list):
                return [str(value) for value in ops]
    lines = file_path.read_text(encoding="utf-8").splitlines()
    cleaned = []
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        cleaned.append(text)
    return cleaned


def _contains_true_marker(value: Any) -> bool:
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if str(current_key) in FORBIDDEN_KEYS and current_value is True:
                return True
            if _contains_true_marker(current_value):
                return True
    if isinstance(value, list):
        return any(_contains_true_marker(item) for item in value)
    return False


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
