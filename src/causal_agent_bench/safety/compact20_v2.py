"""Deterministic constrained selector for the Compact-20 pre-review packet."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Final

from causal_agent_bench.generation.answer_policies import (
    POLICY_VERSION,
    attach_base_task_policies,
    attach_intervention_policies,
)
from causal_agent_bench.generation.interventions import make_intervention
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.safety.intervention_reachability import (
    audit_intervention_reachability,
)
from causal_agent_bench.schemas import BaseTask, BenchmarkInstance

COMPACT20_SEED: Final[int] = 20260801
GENERATOR_VERSION: Final[str] = "cab_compact20_selector_v2.0.0"
OLD_MANIFEST_SHA256: Final[str] = (
    "683c9c873594c83b6a45179cc25ab4fa7a5ca14f875635e2aee22ae8fd030224"
)
OLD_PACKET_MANIFEST_SHA256: Final[str] = (
    "0c02bfe5083c9fc34be59826c8c01896c105da5e6c86752faa35b21db8062bce"
)
OLD_REVIEW_ITEMS_SHA256: Final[str] = (
    "8c7ae2b0987e8eff9b6e827b188b3acbacd7ee2a3b92e2189c662f888e52cfd8"
)

# Four IDs are deliberate cross-family anchors.  Every other cell consumes a
# different base task, yielding exactly 16 unique bases across 20 candidates.
TARGET_CELLS: Final[tuple[tuple[str, str, str, str | None], ...]] = (
    ("tool_removal", "travel_planning", "medium", "anchor_a"),
    ("tool_removal", "file_spreadsheet_qa", "hard", "anchor_b"),
    ("tool_removal", "research_assistant", "easy", "anchor_c"),
    ("tool_removal", "coding_debugging", "stress", None),
    ("tool_removal", "policy_compliance", "medium", None),
    ("tool_failure", "travel_planning", "medium", "anchor_a"),
    ("tool_failure", "calendar_email_workflow", "hard", None),
    ("tool_failure", "shopping_comparison", "easy", None),
    ("tool_failure", "operations_planning", "stress", None),
    ("tool_failure", "file_spreadsheet_qa", "medium", None),
    ("memory_corruption", "research_assistant", "easy", "anchor_c"),
    ("memory_corruption", "coding_debugging", "stress", "anchor_d"),
    ("memory_corruption", "calendar_email_workflow", "medium", None),
    ("memory_corruption", "policy_compliance", "hard", None),
    ("memory_corruption", "operations_planning", "medium", None),
    ("observation_conflict", "file_spreadsheet_qa", "hard", "anchor_b"),
    ("observation_conflict", "coding_debugging", "stress", "anchor_d"),
    ("observation_conflict", "shopping_comparison", "medium", None),
    ("observation_conflict", "travel_planning", "easy", None),
    ("observation_conflict", "research_assistant", "hard", None),
)


def build_compact20_v2(
    repo_root: str | Path,
    *,
    source_instances: str | Path = "data/processed/pilot_v0_1/instances.jsonl",
    output_dir: str | Path = "data/compact20_reviewed",
) -> dict[str, Any]:
    """Build the public pre-review slice and its deterministic receipts."""

    root = Path(repo_root).resolve()
    source_path = _resolve(root, source_instances)
    out = _resolve(root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_rows = _read_jsonl(source_path)
    raw_tasks = {
        str(row["base_task"]["task_id"]): row["base_task"]
        for row in raw_rows
        if isinstance(row.get("base_task"), dict)
    }
    tasks = {
        task_id: attach_base_task_policies(
            BaseTask.model_validate(payload),
            benchmark_version="compact20_v2",
            split_role="compact20_public_pre_review_v2",
        )
        for task_id, payload in raw_tasks.items()
    }
    selected_task_ids, anchor_ids = _select_task_ids(tasks)

    selected_instances: list[BenchmarkInstance] = []
    selected_interventions: list[BenchmarkInstance] = []
    candidates: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str]] = set()
    clean_by_task: dict[str, BenchmarkInstance] = {}

    for index, ((family, domain, difficulty, anchor), task_id) in enumerate(
        zip(TARGET_CELLS, selected_task_ids, strict=True),
        1,
    ):
        base = tasks[task_id]
        raw_intervention = make_intervention(base, family)  # type: ignore[arg-type]
        intervention = attach_intervention_policies(
            base,
            raw_intervention,
            benchmark_version="compact20_v2",
        )
        instance = BenchmarkInstance(
            instance_id=f"{base.task_id}.{family}",
            base_task=base,
            condition="intervention",
            intervention=intervention,
            available_tools=_patched_tools(base.available_tools, intervention),
            initial_memory=dict(intervention.memory_patch),
            environment_seed=_seed_for(base.task_id, family),
            metadata={
                "synthetic": True,
                "selector_version": GENERATOR_VERSION,
                "selector_seed": COMPACT20_SEED,
                "anchor_id": anchor,
            },
        )
        audit = audit_intervention_reachability(instance)
        if not audit.passed:
            raise ValueError(
                f"selected candidate failed reachability: {instance.instance_id}: "
                f"{audit.failure_codes}"
            )
        if not _scorer_compatible(instance):
            raise ValueError(f"selected candidate has incompatible scorer: {instance.instance_id}")
        scorer_policy = intervention.scorer_policy
        if scorer_policy is None:
            raise ValueError(f"selected candidate lacks scorer policy: {instance.instance_id}")
        clean_by_task.setdefault(
            base.task_id,
            BenchmarkInstance(
                instance_id=f"{base.task_id}.clean",
                base_task=base,
                condition="clean",
                available_tools=list(base.available_tools),
                environment_seed=_seed_for(base.task_id, "clean"),
                metadata={
                    "synthetic": True,
                    "selector_version": GENERATOR_VERSION,
                },
            ),
        )
        selected_interventions.append(instance)
        selected_keys.add((base.task_id, family))
        candidates.append(
            {
                "candidate_id": f"compact20_v2_cand_{index:02d}",
                "base_task_id": base.task_id,
                "clean_instance_id": f"{base.task_id}.clean",
                "intervention_instance_id": instance.instance_id,
                "family": family,
                "domain": domain,
                "difficulty": difficulty,
                "anchor_id": anchor,
                "deliberate_anchor": anchor is not None,
                "data_source": "data/compact20_reviewed/compact20_v2_instances.jsonl",
                "status": "no_run_genuine_human_review_pending",
                "scorer_policy_version": POLICY_VERSION,
                "scorer_policy_hash": stable_hash(
                    scorer_policy.model_dump(mode="json"),
                    length=64,
                ),
                "reachability_status": "PASS",
                "reachability_hash": audit.audit_hash,
                "reviewer_instruction_fingerprint": stable_hash(
                    {
                        "task": base.user_instruction,
                        "intervention": intervention.description,
                    },
                    length=64,
                ),
                "expected_final_answer_change": intervention.expected_final_answer_change,
                "ground_truth_policy": intervention.metadata.get("ground_truth_policy"),
                "intervention_validity_risk": intervention.intervention_validity_risk,
            }
        )

    selected_instances.extend(
        clean_by_task[task_id] for task_id in sorted(clean_by_task)
    )
    selected_instances.extend(selected_interventions)
    instances_path = out / "compact20_v2_instances.jsonl"
    _write_jsonl(instances_path, selected_instances)

    balance = _balance_report(candidates, anchor_ids)
    constraints = _constraint_checks(candidates)
    if not all(constraints.values()):
        failed = sorted(key for key, value in constraints.items() if not value)
        raise ValueError(f"Compact-20 constraints failed: {failed}")
    rejections = _rejection_rows(tasks, selected_keys)

    manifest: dict[str, Any] = {
        "schema_version": "cab_compact20_reviewed_manifest_v2",
        "generator_version": GENERATOR_VERSION,
        "deterministic_seed": COMPACT20_SEED,
        "candidate_count": len(candidates),
        "unique_base_task_count": len({row["base_task_id"] for row in candidates}),
        "candidates": candidates,
        "anchors": [
            {
                "anchor_id": anchor,
                "base_task_id": task_id,
                "candidate_ids": [
                    row["candidate_id"] for row in candidates if row["anchor_id"] == anchor
                ],
                "purpose": "cross-family paired design anchor",
            }
            for anchor, task_id in sorted(anchor_ids.items())
        ],
        "constraint_satisfaction": constraints,
        "prior_packet_invalidation": {
            "status": "INVALIDATED_BY_COMPACT20_V2_REGENERATION",
            "prior_candidate_manifest_sha256": OLD_MANIFEST_SHA256,
            "prior_packet_manifest_sha256": OLD_PACKET_MANIFEST_SHA256,
            "prior_review_items_sha256": OLD_REVIEW_ITEMS_SHA256,
            "reason": "Scorer semantics and packet composition changed before human review.",
        },
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "scientific_evidence": False,
        "genuine_human_review_rows": 0,
    }
    manifest["constraint_satisfaction_receipt"] = stable_hash(
        {
            "generator_version": GENERATOR_VERSION,
            "seed": COMPACT20_SEED,
            "candidate_keys": [
                [row["base_task_id"], row["family"]] for row in candidates
            ],
            "constraints": constraints,
        },
        length=64,
    )
    manifest_path = out / "compact20_reviewed_manifest.json"
    _write_json(manifest_path, manifest)
    balance_path = out / "compact20_v2_balance_report.json"
    _write_json(balance_path, balance)
    rejected_path = out / "compact20_v2_rejected_candidates.jsonl"
    _write_jsonl_dicts(rejected_path, rejections)

    public_manifest = {
        "schema_version": "cab_compact20_v2_public_commitment_v1",
        "study_id": "compact20_v2",
        "generator_version": GENERATOR_VERSION,
        "deterministic_seed": COMPACT20_SEED,
        "candidate_count": 20,
        "unique_base_task_count": 16,
        "candidate_manifest_sha256": _sha256_file(manifest_path),
        "instances_sha256": _sha256_file(instances_path),
        "balance_report_sha256": _sha256_file(balance_path),
        "rejected_candidates_sha256": _sha256_file(rejected_path),
        "constraint_satisfaction_receipt": manifest[
            "constraint_satisfaction_receipt"
        ],
        "prior_commitments_invalidated": [
            OLD_MANIFEST_SHA256,
            OLD_PACKET_MANIFEST_SHA256,
            OLD_REVIEW_ITEMS_SHA256,
        ],
        "human_validation_state": "HUMAN_INPUT_REQUIRED",
        "scientific_evidence": False,
    }
    public_path = root / "data/manifests/compact20_v2_public_manifest.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(public_path, public_manifest)
    return {
        "manifest": str(manifest_path),
        "instances": str(instances_path),
        "balance_report": str(balance_path),
        "rejected_candidates": str(rejected_path),
        "public_manifest": str(public_path),
        "constraints": constraints,
        "candidate_count": len(candidates),
        "unique_base_task_count": len(clean_by_task),
    }


def _select_task_ids(
    tasks: dict[str, BaseTask],
) -> tuple[list[str], dict[str, str]]:
    by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
    for task in tasks.values():
        by_cell[(task.domain, task.difficulty)].append(task.task_id)
    for key in by_cell:
        by_cell[key].sort(
            key=lambda task_id: stable_hash(
                {"seed": COMPACT20_SEED, "task_id": task_id}, length=64
            )
        )
    used: set[str] = set()
    anchors: dict[str, str] = {}
    selected: list[str] = []
    for family, domain, difficulty, anchor in TARGET_CELLS:
        del family
        if anchor is not None and anchor in anchors:
            selected.append(anchors[anchor])
            continue
        choices = [
            task_id for task_id in by_cell[(domain, difficulty)] if task_id not in used
        ]
        if not choices:
            raise ValueError(f"no unused task for target cell {domain}/{difficulty}")
        chosen = choices[0]
        used.add(chosen)
        if anchor is not None:
            anchors[anchor] = chosen
        selected.append(chosen)
    return selected, anchors


def _balance_report(
    candidates: list[dict[str, Any]],
    anchors: dict[str, str],
) -> dict[str, Any]:
    family_domain: dict[str, Counter[str]] = defaultdict(Counter)
    family_difficulty: dict[str, Counter[str]] = defaultdict(Counter)
    for row in candidates:
        family_domain[row["family"]][row["domain"]] += 1
        family_difficulty[row["family"]][row["difficulty"]] += 1
    return {
        "schema_version": "cab_compact20_balance_v2",
        "generator_version": GENERATOR_VERSION,
        "deterministic_seed": COMPACT20_SEED,
        "family_counts": dict(sorted(Counter(row["family"] for row in candidates).items())),
        "domain_counts": dict(sorted(Counter(row["domain"] for row in candidates).items())),
        "difficulty_counts": dict(
            sorted(Counter(row["difficulty"] for row in candidates).items())
        ),
        "family_by_domain": {
            family: dict(sorted(counts.items()))
            for family, counts in sorted(family_domain.items())
        },
        "family_by_difficulty": {
            family: dict(sorted(counts.items()))
            for family, counts in sorted(family_difficulty.items())
        },
        "unique_base_task_count": len({row["base_task_id"] for row in candidates}),
        "anchor_count": len(anchors),
        "anchors": dict(sorted(anchors.items())),
        "max_domain_share": max(Counter(row["domain"] for row in candidates).values())
        / len(candidates),
    }


def _constraint_checks(candidates: list[dict[str, Any]]) -> dict[str, bool]:
    families = Counter(row["family"] for row in candidates)
    domains = Counter(row["domain"] for row in candidates)
    difficulties = Counter(row["difficulty"] for row in candidates)
    by_family_domains: dict[str, set[str]] = defaultdict(set)
    by_family_difficulties: dict[str, set[str]] = defaultdict(set)
    for row in candidates:
        by_family_domains[row["family"]].add(row["domain"])
        by_family_difficulties[row["family"]].add(row["difficulty"])
    fingerprints = [row["reviewer_instruction_fingerprint"] for row in candidates]
    return {
        "exactly_20_items": len(candidates) == 20,
        "exactly_four_current_families": len(families) == 4,
        "five_items_per_family": set(families.values()) == {5},
        "at_least_12_unique_bases": len({row["base_task_id"] for row in candidates}) >= 12,
        "preferred_16_unique_plus_4_anchors": (
            len({row["base_task_id"] for row in candidates}) == 16
            and len({row["anchor_id"] for row in candidates if row["anchor_id"]}) == 4
        ),
        "domain_share_at_most_25_percent": max(domains.values()) <= 5,
        "each_family_at_least_3_domains": all(
            len(values) >= 3 for values in by_family_domains.values()
        ),
        "each_family_at_least_2_difficulties": all(
            len(values) >= 2 for values in by_family_difficulties.values()
        ),
        "difficulty_minima": (
            difficulties["easy"] >= 4
            and difficulties["medium"] >= 6
            and difficulties["hard"] >= 4
            and difficulties["stress"] >= 2
        ),
        "no_duplicate_reviewer_instruction": len(fingerprints) == len(set(fingerprints)),
        "all_reachability_pass": all(row["reachability_status"] == "PASS" for row in candidates),
        "all_scorers_v3": all(
            row["scorer_policy_version"] == "cab_answer_policy_v3"
            for row in candidates
        ),
        "model_output_and_identity_absent_by_construction": True,
    }


def _rejection_rows(
    tasks: dict[str, BaseTask],
    selected_keys: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    families = sorted({cell[0] for cell in TARGET_CELLS})
    target_cells = {(cell[0], cell[1], cell[2]) for cell in TARGET_CELLS}
    for task_id, task in sorted(tasks.items()):
        for family in families:
            if (task_id, family) in selected_keys:
                continue
            reason = (
                "TARGET_CELL_NOT_PREREGISTERED"
                if (family, task.domain, task.difficulty) not in target_cells
                else "LOWER_DETERMINISTIC_PRIORITY_OR_DUPLICATE_BASE"
            )
            rows.append(
                {
                    "base_task_id": task_id,
                    "family": family,
                    "domain": task.domain,
                    "difficulty": task.difficulty,
                    "reason_codes": [reason],
                    "selector_version": GENERATOR_VERSION,
                    "selector_seed": COMPACT20_SEED,
                }
            )
    return rows


def _scorer_compatible(instance: BenchmarkInstance) -> bool:
    assert instance.intervention is not None
    scorer = instance.intervention.scorer_policy
    gold = instance.intervention.gold_answer_policy
    return bool(
        scorer
        and gold
        and scorer.metadata.get("policy_version") == "cab_answer_policy_v3"
        and scorer.fallback_mode.value == "disabled"
        and (
            scorer.abstention.value == "forbidden"
            or scorer.abstention_opportunity is not None
        )
    )


def _patched_tools(base_tools: list[str], intervention: Any) -> list[str]:
    tools = list(base_tools)
    removed = set(intervention.tool_availability_patch.get("removed_tools", []))
    tools = [tool for tool in tools if tool not in removed]
    for tool in intervention.tool_availability_patch.get("added_tools", []):
        if tool not in tools:
            tools.append(tool)
    return tools


def _seed_for(task_id: str, family: str) -> int:
    return int(stable_hash({"seed": COMPACT20_SEED, "task": task_id, "family": family}, length=8), 16)


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[BenchmarkInstance]) -> None:
    _write_jsonl_dicts(path, [row.model_dump(mode="json") for row in rows])


def _write_jsonl_dicts(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = ["COMPACT20_SEED", "GENERATOR_VERSION", "build_compact20_v2"]
