"""Unified provider-free Phase 2/3 leakage and contract eligibility gate."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.agent_payload_leakage import (
    scan_agent_visible_dataset,
)
from causal_agent_bench.safety.heldout_release import (
    validate_heldout_release_policy,
)
from causal_agent_bench.safety.pair_link_validator import (
    validate_dataset_pair_links,
)
from causal_agent_bench.safety.split_registry import (
    CANONICAL_SPLIT_REGISTRY_PATH,
    validate_canonical_split_registry,
)
from causal_agent_bench.safety.static_leakage import (
    check_static_leakage_for_dataset,
)
from causal_agent_bench.safety.task_intervention_lint import (
    lint_task_intervention_dataset,
)


def run_cab_leakage_gate(
    repo_root: str | Path,
    *,
    registry_path: str | Path = CANONICAL_SPLIT_REGISTRY_PATH,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run all deterministic Phase 2/3 gates and optionally persist JSON."""

    root = Path(repo_root).resolve()
    registry_file = _resolve(root, registry_path)
    registry_issues = validate_canonical_split_registry(
        root,
        registry_path=registry_file,
    )
    registry = _read_json(registry_file)
    role_reports: list[dict[str, Any]] = []

    for role_row in registry.get("roles", []):
        if not isinstance(role_row, dict):
            continue
        role = str(role_row.get("role", ""))
        source = _resolve(root, str(role_row.get("source", "")))
        if role == "dev_fixture":
            payload_scan = scan_agent_visible_dataset(source, repo_root=root)
            role_reports.append(
                {
                    "role": role,
                    "source": _relative(source, root),
                    "contract_lint": {
                        "passed": True,
                        "scope": "Fixture role uses schema/runtime fixture tests.",
                        "counts": {"blockers": 0, "warnings": 0},
                    },
                    "pair_link": {
                        "passed": True,
                        "scope": "Fixture role excluded from scientific pair eligibility.",
                        "blockers": 0,
                    },
                    "static_leakage": {
                        "passed": True,
                        "blocker_cluster_count": 0,
                        "scope": "Fixture role excluded from scientific split eligibility.",
                    },
                    "agent_payload": payload_scan,
                    "passed": payload_scan["passed"],
                }
            )
            continue

        dataset_dir, selected_ids, instances_source = _role_materialization(
            role,
            source,
        )
        contract = lint_task_intervention_dataset(
            dataset_dir,
            repo_root=root,
            role=role,
            selected_instance_ids=selected_ids,
            strict_explicit_policies=True,
        )
        payload_scan = scan_agent_visible_dataset(
            instances_source,
            repo_root=root,
            selected_instance_ids=selected_ids if source.suffix == ".json" else None,
        )
        static = check_static_leakage_for_dataset(
            dataset_dir,
            repo_root=root,
        )
        pair = validate_dataset_pair_links(dataset_dir, repo_root=root)
        pair_blockers = sum(
            1
            for issue in pair.get("issues", [])
            if issue.get("severity") in {"blocker", "error"}
        )
        static_passed = int(static.get("blocker_cluster_count", 0)) == 0
        pair_summary = {
            "passed": pair_blockers == 0,
            "blockers": pair_blockers,
            "warnings": sum(
                1
                for issue in pair.get("issues", [])
                if issue.get("severity") == "warning"
            ),
            "issue_count": int(pair.get("issue_count", 0)),
            "issues": pair.get("issues", []),
        }
        static_summary = {
            "passed": static_passed,
            "blocker_cluster_count": int(
                static.get("blocker_cluster_count", 0)
            ),
            "needs_review_count": int(static.get("needs_review_count", 0)),
            "warning_cluster_count": int(
                static.get("warning_cluster_count", 0)
            ),
            "classification_counts": static.get("classification_counts", {}),
            "top_true_leakage_clusters": static.get(
                "top_true_leakage_clusters",
                [],
            ),
        }
        role_passed = all(
            (
                contract["passed"],
                payload_scan["passed"],
                static_passed,
                pair_blockers == 0,
            )
        )
        role_reports.append(
            {
                "role": role,
                "source": _relative(source, root),
                "dataset_dir": _relative(dataset_dir, root),
                "selected_instance_count": (
                    len(selected_ids) if selected_ids is not None else None
                ),
                "contract_lint": contract,
                "pair_link": pair_summary,
                "static_leakage": static_summary,
                "agent_payload": payload_scan,
                "passed": role_passed,
            }
        )

    release = validate_heldout_release_policy(root)
    internal_blockers: list[dict[str, Any]] = []
    for detail in registry_issues:
        internal_blockers.append(
            {
                "gate": "canonical_split_registry",
                "role": None,
                "detail": detail,
            }
        )
    for report in role_reports:
        role = report["role"]
        if not report["contract_lint"]["passed"]:
            internal_blockers.append(
                {
                    "gate": "task_intervention_lint",
                    "role": role,
                    "detail": (
                        f"{report['contract_lint']['counts']['blockers']} "
                        "contract blocker(s)"
                    ),
                }
            )
        if not report["pair_link"]["passed"]:
            internal_blockers.append(
                {
                    "gate": "pair_link",
                    "role": role,
                    "detail": f"{report['pair_link']['blockers']} blocker(s)",
                }
            )
        if not report["static_leakage"]["passed"]:
            internal_blockers.append(
                {
                    "gate": "static_leakage",
                    "role": role,
                    "detail": (
                        f"{report['static_leakage']['blocker_cluster_count']} "
                        "blocker cluster(s)"
                    ),
                }
            )
        if not report["agent_payload"]["passed"]:
            internal_blockers.append(
                {
                    "gate": "agent_payload",
                    "role": role,
                    "detail": (
                        f"{report['agent_payload']['blocker_count']} blocker(s)"
                    ),
                }
            )
    if not release["passed"]:
        internal_blockers.append(
            {
                "gate": "heldout_release_policy",
                "role": "heldout_challenge",
                "detail": f"{len(release['issues'])} policy issue(s)",
            }
        )

    passed = not internal_blockers
    payload = {
        "schema_version": "cab_phase2_phase3_leakage_gate_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Provider-free static eligibility gate. No models, providers, "
            "benchmark execution, scientific results, or paper evidence."
        ),
        "evidence_class": "ENGINEERING_ONLY",
        "status": "LEAKAGE_GATE_PASS" if passed else "LEAKAGE_GATE_BLOCKED",
        "run_eligible_under_phase2_phase3": passed,
        "paper_eligible": False,
        "registry": {
            "path": _relative(registry_file, root),
            "passed": not registry_issues,
            "issues": registry_issues,
        },
        "roles": role_reports,
        "heldout_release_policy": release,
        "internal_blocker_count": len(internal_blockers),
        "internal_blockers": internal_blockers,
        "next_allowed_action": (
            "Proceed to independent human validity review; provider execution remains separately gated."
            if passed
            else "Repair the first reported internal blocker, regenerate affected hashes, and rerun this command."
        ),
        "exact_command": "PYTHONPATH=src python3 scripts/cab_leakage_gate.py",
        "forbidden_actions": [
            "Do not run provider/model inference while this gate is blocked.",
            "Do not publish protected held-out payloads before post-study release approval.",
            "Do not convert this engineering pass into empirical or paper evidence.",
        ],
    }
    if output_path is not None:
        output = _resolve(root, output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        payload["output_path"] = _relative(output, root)
    return payload


def _role_materialization(
    role: str,
    source: Path,
) -> tuple[Path, set[str] | None, Path]:
    if source.suffix == ".jsonl":
        return source.parent, _jsonl_instance_ids(source), source
    if role == "compact20_pilot":
        manifest = _read_json(source)
        candidates = [
            row
            for row in manifest.get("candidates", [])
            if isinstance(row, dict)
        ]
        selected: set[str] = set()
        data_sources: set[Path] = set()
        for row in candidates:
            for field in ("clean_instance_id", "intervention_instance_id"):
                value = str(row.get(field, "")).strip()
                if value:
                    selected.add(value)
            value = str(row.get("data_source", "")).strip()
            if value:
                candidate_path = Path(value)
                data_sources.add(
                    candidate_path
                    if candidate_path.is_absolute()
                    else source.parents[2] / candidate_path
                )
        if len(data_sources) != 1:
            raise ValueError(
                "Compact20 manifest must reference exactly one instance source"
            )
        instances = next(iter(data_sources)).resolve()
        return instances.parent, selected, instances
    raise ValueError(f"unsupported canonical role source: {role} -> {source}")


def _jsonl_instance_ids(path: Path) -> set[str]:
    values: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict) and row.get("instance_id"):
                values.add(str(row["instance_id"]))
    return values


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


__all__ = ["run_cab_leakage_gate"]
