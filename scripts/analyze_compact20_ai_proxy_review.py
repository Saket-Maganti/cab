#!/usr/bin/env python3
"""Create and summarize Compact-20 AI proxy review fixtures.

This script is intentionally limited to synthetic/proxy labels for downstream
pipeline testing. It does not read model outputs, call providers, run local
models, or modify the original manual-review CSVs.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

REVIEW_DATE = "2026-06-21"
PROXY_STATUS = "ai_proxy_test_only"
PROXY_REVIEW_TYPE = "ai_proxy_review"
PROXY_LABELS = "ai_proxy_review;synthetic_review_for_pipeline_testing;not_human_annotation"
PROXY_REVIEWER = "AI_PROXY_TEST_ONLY"
PROXY_NOTE_PREFIX = "AI_PROXY_TEST_ONLY: not human validation."

INPUT_DIR = Path("data/human_validation/no_api_task_review")
TASK_REVIEW_CSV = INPUT_DIR / "compact20_task_review.csv"
GOLD_REVIEW_CSV = INPUT_DIR / "compact20_gold_policy_review.csv"
MANIFEST_JSON = INPUT_DIR / "compact20_candidate_manifest.json"

TASK_PROXY_CSV = INPUT_DIR / "compact20_task_review_AI_PROXY_TEST_ONLY.csv"
GOLD_PROXY_CSV = INPUT_DIR / "compact20_gold_policy_review_AI_PROXY_TEST_ONLY.csv"
PROXY_SUBSET_JSON = INPUT_DIR / "compact20_ai_proxy_clean_candidate_subset.json"
PROXY_SUBSET_MD = INPUT_DIR / "compact20_ai_proxy_clean_candidate_subset.md"

STATUS_REPORT = Path("reports/COMPACT20_AI_PROXY_REVIEW_TEST_STATUS.md")
COMPLETION_REPORT = Path("reports/COMPACT20_AI_PROXY_REVIEW_COMPLETION_STATUS.md")
ACTION_LOG_CSV = Path("reports/COMPACT20_AI_PROXY_REVIEW_ACTION_LOG.csv")
ACTION_LOG_MD = Path("reports/COMPACT20_AI_PROXY_REVIEW_ACTION_LOG.md")
GOLD_REVISION_PLAN = Path("reports/COMPACT20_AI_PROXY_GOLD_POLICY_REVISION_PLAN.md")
C10_STATUS_REPORT = Path("reports/C10_STATUS_AFTER_AI_PROXY_REVIEW_TEST.md")
EVIDENCE_BOUNDARY_REPORT = Path("reports/AI_PROXY_REVIEW_EVIDENCE_BOUNDARY.md")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _load_manifest(path: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["candidate_id"]: row for row in payload["candidates"]}


def _task_proxy_decision(candidate: dict[str, str]) -> dict[str, str]:
    family = candidate["family"]
    expected_change = candidate["expected_final_answer_change"]
    risk = candidate["intervention_validity_risk"]

    if family == "memory_corruption" and expected_change == "no":
        return {
            "task_clear": "yes_proxy",
            "intervention_isolated": "yes_proxy_pending_human_review",
            "gold_policy_clear": "yes_proxy_pending_human_review",
            "include_in_compact20": "include_proxy_pipeline_test_only",
            "issue_category": "proxy_clean_candidate",
            "issue_severity": "low_proxy_only",
            "reason": "Metadata says expected answer stays unchanged; still requires real human review.",
        }
    if family == "tool_removal" and expected_change == "yes":
        return {
            "task_clear": "yes_proxy",
            "intervention_isolated": "manual_review_needed",
            "gold_policy_clear": "manual_review_needed",
            "include_in_compact20": "review_before_include",
            "issue_category": "answer_changing_policy",
            "issue_severity": "medium",
            "reason": "Tool removal can legitimately change the answer, so a human must verify the policy.",
        }
    if family == "observation_conflict" or risk == "high":
        return {
            "task_clear": "yes_proxy",
            "intervention_isolated": "unclear_manual_review_needed",
            "gold_policy_clear": "unclear_manual_review_needed",
            "include_in_compact20": "review_before_include",
            "issue_category": "high_risk_conflict_policy",
            "issue_severity": "high",
            "reason": "Observation conflicts are high-risk and need human policy resolution.",
        }
    return {
        "task_clear": "yes_proxy",
        "intervention_isolated": "unclear_manual_review_needed",
        "gold_policy_clear": "unclear_manual_review_needed",
        "include_in_compact20": "review_before_include",
        "issue_category": "unclear_gold_policy",
        "issue_severity": "medium",
        "reason": "Metadata leaves the final-answer policy unclear, so manual review is needed.",
    }


def _gold_proxy_decision(candidate: dict[str, str]) -> dict[str, str]:
    expected_change = candidate["expected_final_answer_change"]
    policy = candidate["ground_truth_policy"]
    family = candidate["family"]

    if expected_change == "no" and policy == "unchanged":
        return {
            "should_answer_change": "no_proxy_pending_human_review",
            "abstention_acceptable": "manual_review_needed",
            "cannot_determine_acceptable": "manual_review_needed",
            "human_review_required": "yes",
            "auto_fix_allowed": "no",
            "review_decision": "proxy_policy_consistent_pending_human_review",
            "issue_category": "proxy_policy_consistent",
            "reason": "Manifest policy says unchanged; human review remains mandatory before paper use.",
        }
    if expected_change == "yes" and policy == "behavioral_override_required":
        return {
            "should_answer_change": "yes_proxy_but_requires_human_review",
            "abstention_acceptable": "manual_review_needed",
            "cannot_determine_acceptable": "manual_review_needed",
            "human_review_required": "yes",
            "auto_fix_allowed": "no",
            "review_decision": "proxy_answer_change_requires_human_review",
            "issue_category": "answer_changing_policy",
            "reason": "Answer-changing tool-removal cases require human verification of the override.",
        }
    return {
        "should_answer_change": "unclear_manual_review_needed",
        "abstention_acceptable": "manual_review_needed",
        "cannot_determine_acceptable": "manual_review_needed",
        "human_review_required": "yes",
        "auto_fix_allowed": "no",
        "review_decision": "proxy_unclear_manual_review_needed",
        "issue_category": f"{family}_policy_unclear",
        "reason": "Metadata does not settle whether the final answer should change.",
    }


def _proxy_common(candidate: dict[str, str], decision: dict[str, str]) -> dict[str, str]:
    return {
        "status": PROXY_STATUS,
        "review_type": PROXY_REVIEW_TYPE,
        "review_labels": PROXY_LABELS,
        "reviewer_confidence_1_to_5": "3",
        "reviewer_notes": (
            f"{PROXY_NOTE_PREFIX} {decision['reason']} "
            "Synthetic review for pipeline testing only; not C10 evidence and not paper-eligible."
        ),
        "source_manifest_status": candidate["status"],
    }


def _build_task_proxy_rows(
    task_rows: list[dict[str, str]], manifest: dict[str, dict[str, str]]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    proxy_rows: list[dict[str, str]] = []
    actions: list[dict[str, str]] = []
    for row in task_rows:
        candidate = manifest[row["candidate_id"]]
        decision = _task_proxy_decision(candidate)
        proxy = dict(row)
        proxy.update(
            {
                "task_clear": decision["task_clear"],
                "intervention_isolated": decision["intervention_isolated"],
                "gold_policy_clear": decision["gold_policy_clear"],
                "include_in_compact20": decision["include_in_compact20"],
                "reviewer_id": PROXY_REVIEWER,
                "review_date": REVIEW_DATE,
                "notes": "synthetic_review_for_pipeline_testing; not_human_annotation",
            }
        )
        proxy.update(_proxy_common(candidate, decision))
        proxy_rows.append(proxy)

        actions.append(
            {
                "candidate_id": row["candidate_id"],
                "base_task_id": row["base_task_id"],
                "family": row["family"],
                "domain": row["domain"],
                "action_type": (
                    "candidate_for_pipeline_testing_only"
                    if decision["issue_category"] == "proxy_clean_candidate"
                    else "human_review_required"
                ),
                "issue_category": decision["issue_category"],
                "issue_severity": decision["issue_severity"],
                "reason": decision["reason"],
                "proxy_only": "true",
                "blocks_c10": "true",
                "blocks_paper_use": "true",
            }
        )
    return proxy_rows, actions


def _build_gold_proxy_rows(
    gold_rows: list[dict[str, str]], manifest: dict[str, dict[str, str]]
) -> list[dict[str, str]]:
    proxy_rows: list[dict[str, str]] = []
    for row in gold_rows:
        candidate = manifest[row["candidate_id"]]
        decision = _gold_proxy_decision(candidate)
        proxy = dict(row)
        proxy.update(
            {
                "should_answer_change": decision["should_answer_change"],
                "abstention_acceptable": decision["abstention_acceptable"],
                "cannot_determine_acceptable": decision["cannot_determine_acceptable"],
                "human_review_required": decision["human_review_required"],
                "auto_fix_allowed": decision["auto_fix_allowed"],
                "review_decision": decision["review_decision"],
                "reviewer_id": PROXY_REVIEWER,
                "review_date": REVIEW_DATE,
                "notes": "synthetic_review_for_pipeline_testing; not_human_annotation",
            }
        )
        proxy.update(_proxy_common(candidate, decision))
        proxy_rows.append(proxy)
    return proxy_rows


def _clean_subset(task_rows: list[dict[str, str]], gold_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    gold_by_id = {row["candidate_id"]: row for row in gold_rows}
    subset: list[dict[str, str]] = []
    for row in task_rows:
        gold = gold_by_id[row["candidate_id"]]
        if (
            row["include_in_compact20"] == "include_proxy_pipeline_test_only"
            and gold["review_decision"] == "proxy_policy_consistent_pending_human_review"
        ):
            subset.append(
                {
                    "candidate_id": row["candidate_id"],
                    "base_task_id": row["base_task_id"],
                    "clean_instance_id": row["clean_instance_id"],
                    "intervention_instance_id": row["intervention_instance_id"],
                    "family": row["family"],
                    "domain": row["domain"],
                    "difficulty": row["difficulty"],
                    "proxy_status": PROXY_STATUS,
                    "review_labels": PROXY_LABELS,
                    "paper_eligible": False,
                    "c10_evidence": False,
                    "human_annotation": False,
                    "use_limit": "pipeline_testing_only_not_human_validation",
                }
            )
    return subset


def _candidate_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row["family"] for row in rows)


def _write_subset_outputs(repo: Path, subset: list[dict[str, str]]) -> None:
    payload = {
        "schema_version": 1,
        "status": PROXY_STATUS,
        "labels": ["ai_proxy_review", "synthetic_review_for_pipeline_testing", "not_human_annotation"],
        "candidate_count": len(subset),
        "paper_asset_eligibility": False,
        "c10_support": False,
        "human_annotation_count": 0,
        "provider_backed_evidence_count": 0,
        "use_limit": "For downstream analysis pipeline testing only.",
        "candidates": subset,
    }
    subset_json = repo / PROXY_SUBSET_JSON
    subset_md = repo / PROXY_SUBSET_MD
    subset_json.parent.mkdir(parents=True, exist_ok=True)
    subset_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Compact-20 AI Proxy Clean Candidate Subset",
        "",
        "Status: `ai_proxy_test_only`",
        "",
        "These rows are synthetic/proxy labels for pipeline testing only. They are not human annotations, not C10 evidence, not provider evidence, and not paper-eligible.",
        "",
        f"Proxy clean candidate count: `{len(subset)}`",
        "",
        "| candidate_id | family | domain | use limit |",
        "|---|---|---|---|",
    ]
    for row in subset:
        lines.append(
            f"| `{row['candidate_id']}` | `{row['family']}` | `{row['domain']}` | `pipeline_testing_only_not_human_validation` |"
        )
    _write_text(subset_md, "\n".join(lines))


def _write_action_logs(repo: Path, actions: list[dict[str, str]]) -> None:
    _write_csv(
        repo / ACTION_LOG_CSV,
        actions,
        [
            "candidate_id",
            "base_task_id",
            "family",
            "domain",
            "action_type",
            "issue_category",
            "issue_severity",
            "reason",
            "proxy_only",
            "blocks_c10",
            "blocks_paper_use",
        ],
    )
    lines = [
        "# Compact-20 AI Proxy Review Action Log",
        "",
        "Status: `ai_proxy_test_only`",
        "",
        "Every action below is synthetic/proxy pipeline-testing metadata. It is not human validation and cannot promote C10 or paper assets.",
        "",
        "| candidate_id | family | action | issue | blocks paper use |",
        "|---|---|---|---|---|",
    ]
    for action in actions:
        lines.append(
            f"| `{action['candidate_id']}` | `{action['family']}` | `{action['action_type']}` | `{action['issue_category']}` | `{action['blocks_paper_use']}` |"
        )
    _write_text(repo / ACTION_LOG_MD, "\n".join(lines))


def _write_reports(
    repo: Path,
    task_rows: list[dict[str, str]],
    gold_rows: list[dict[str, str]],
    actions: list[dict[str, str]],
    subset: list[dict[str, str]],
) -> None:
    task_counts = _candidate_counts(task_rows)
    action_counts = Counter(action["action_type"] for action in actions)
    family_issue_counts = Counter(action["family"] for action in actions if action["action_type"] == "human_review_required")

    _write_text(
        repo / STATUS_REPORT,
        """# Compact-20 AI Proxy Review Test Status

Status: `ai_proxy_test_only`

Labels: `ai_proxy_review`, `synthetic_review_for_pipeline_testing`, `not_human_annotation`.

## Boundary

These files contain AI/proxy test labels. They are not human annotations, cannot support C10, cannot support model-performance claims, cannot support paper assets, and are only for testing downstream analysis scripts.

The original human-review CSVs were not modified:

- `data/human_validation/no_api_task_review/compact20_task_review.csv`
- `data/human_validation/no_api_task_review/compact20_gold_policy_review.csv`

## Generated Proxy Files

- `data/human_validation/no_api_task_review/compact20_task_review_AI_PROXY_TEST_ONLY.csv`
- `data/human_validation/no_api_task_review/compact20_gold_policy_review_AI_PROXY_TEST_ONLY.csv`

## Evidence State

- Provider-backed evidence remains `0`.
- Real human annotations remain `0`.
- Eligible paper assets remain `0`.
- C1-C8/C10 remain unsupported.
""",
    )

    _write_text(
        repo / COMPLETION_REPORT,
        f"""# Compact-20 AI Proxy Review Completion Status

Status: `ai_proxy_test_only`

## Completion

- Task proxy rows filled: `{len(task_rows)}`
- Gold-policy proxy rows filled: `{len(gold_rows)}`
- Proxy clean candidate subset rows: `{len(subset)}`
- Human annotations produced: `0`
- C10 evidence produced: `0`
- Provider-backed evidence produced: `0`
- Eligible paper assets produced: `0`

## Family Counts

| family | proxy rows |
|---|---:|
{chr(10).join(f"| `{family}` | `{count}` |" for family, count in sorted(task_counts.items()))}

## Action Counts

| action | count |
|---|---:|
{chr(10).join(f"| `{action}` | `{count}` |" for action, count in sorted(action_counts.items()))}

## Boundary

This completion report proves only that the downstream review-analysis plumbing can parse clearly labeled proxy files. It does not prove human validation quality, intervention isolation, C10, model performance, or paper readiness.
""",
    )

    _write_text(
        repo / GOLD_REVISION_PLAN,
        f"""# Compact-20 AI Proxy Gold-Policy Revision Plan

Status: `ai_proxy_test_only`

This plan is synthetic/proxy guidance for testing downstream review handling. It is not a human decision log and must not be used to patch frozen data.

## Proxy Family Assessment

| family | proxy assessment | required real action before paper use |
|---|---|---|
| `memory_corruption` | Expected answer marked unchanged in the manifest; `{task_counts.get('memory_corruption', 0)}` rows are proxy-clean for pipeline testing only. | Human reviewer must confirm goal preservation, evidence path, and answer policy. |
| `tool_removal` | Answer-changing behavioral override; `{task_counts.get('tool_removal', 0)}` rows require policy verification. | Human reviewer must decide whether answer change, abstention, or exclusion is appropriate. |
| `tool_failure` | Current policy is unclear between unchanged and behavioral override; `{task_counts.get('tool_failure', 0)}` rows require review. | Human reviewer must verify whether a recovery path exists and whether abstention/cannot-determine is acceptable. |
| `observation_conflict` | High-risk conflict policy; `{task_counts.get('observation_conflict', 0)}` rows require review. | Human reviewer must resolve conflict rules or exclude rows with multiple plausible answers. |

## Proxy Issues Requiring Manual Review

| family | rows needing real review |
|---|---:|
{chr(10).join(f"| `{family}` | `{count}` |" for family, count in sorted(family_issue_counts.items()))}

## Hard Limits

- No auto-fix is authorized.
- No frozen data may be edited from this proxy review.
- No C10, C1-C8, model-performance, or paper-asset claim is promoted.
""",
    )

    _write_text(
        repo / C10_STATUS_REPORT,
        """# C10 Status After AI Proxy Review Test

Status: `C10_UNSUPPORTED_AFTER_AI_PROXY_REVIEW_TEST`

The AI proxy review test does not create C10 evidence. C10 still requires completed human intervention-isolation review, at least two independent reviewers where agreement is claimed, adjudication for disagreements, and an evidence-safety pass.

## Counts

- AI/proxy rows: `20`
- Real human annotations: `0`
- Inter-annotator agreement computations: `0`
- C10-supporting artifacts: `0`
- Eligible paper assets: `0`

## Boundary

These proxy files are useful only for testing review-analysis plumbing. They are not human validation, not C10 evidence, not provider evidence, and not paper-eligible.
""",
    )

    _write_text(
        repo / EVIDENCE_BOUNDARY_REPORT,
        """# AI Proxy Review Evidence Boundary

Status: `ai_proxy_test_only`

## Current Evidence Classification

- Provider-backed evidence remains `0`.
- Real human annotations remain `0`.
- Eligible paper assets remain `0`.
- C1-C8/C10 remain unsupported.

## What The Proxy Review Is

The AI proxy review is a synthetic review fixture for downstream analysis pipeline testing. It is labeled `ai_proxy_review`, `synthetic_review_for_pipeline_testing`, and `not_human_annotation`.

## What The Proxy Review Is Not

It is not human validation, not C10 evidence, not model-performance evidence, not provider evidence, and not paper-eligible.

## Required Before Paper Use

Before any paper use, a real human must fill the original CSVs:

- `data/human_validation/no_api_task_review/compact20_task_review.csv`
- `data/human_validation/no_api_task_review/compact20_gold_policy_review.csv`

The proxy copies must not be counted as annotations, agreement inputs, C10 support, provider evidence, or eligible paper assets.
""",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--proxy-test-mode",
        action="store_true",
        help="Required. Confirms outputs are synthetic proxy fixtures only.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.proxy_test_mode:
        parser.error("--proxy-test-mode is required; this script may only generate proxy-test outputs.")

    repo = Path(args.repo_root).resolve()
    task_rows = _read_csv(repo / TASK_REVIEW_CSV)
    gold_rows = _read_csv(repo / GOLD_REVIEW_CSV)
    manifest = _load_manifest(repo / MANIFEST_JSON)

    task_proxy_rows, actions = _build_task_proxy_rows(task_rows, manifest)
    gold_proxy_rows = _build_gold_proxy_rows(gold_rows, manifest)
    subset = _clean_subset(task_proxy_rows, gold_proxy_rows)

    task_fields = [
        *task_rows[0].keys(),
        "status",
        "review_type",
        "review_labels",
        "reviewer_confidence_1_to_5",
        "reviewer_notes",
        "source_manifest_status",
    ]
    gold_fields = [
        *gold_rows[0].keys(),
        "status",
        "review_type",
        "review_labels",
        "reviewer_confidence_1_to_5",
        "reviewer_notes",
        "source_manifest_status",
    ]

    _write_csv(repo / TASK_PROXY_CSV, task_proxy_rows, task_fields)
    _write_csv(repo / GOLD_PROXY_CSV, gold_proxy_rows, gold_fields)
    _write_action_logs(repo, actions)
    _write_subset_outputs(repo, subset)
    _write_reports(repo, task_proxy_rows, gold_proxy_rows, actions, subset)

    print(
        "wrote Compact-20 AI proxy review fixtures: "
        f"task_rows={len(task_proxy_rows)} gold_rows={len(gold_proxy_rows)} clean_subset={len(subset)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
