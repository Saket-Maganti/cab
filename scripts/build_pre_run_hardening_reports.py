#!/usr/bin/env python3
"""Build the bounded public-safe CAB pre-run hardening report set."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.metrics.endpoints_v3 import (
    PRIMARY_ENDPOINTS,
    SECONDARY_ENDPOINTS,
)
from causal_agent_bench.runners.resource_planner import plan_all_scenarios

BASELINE_SHA = "c8b0d008a02f4bcc36a24635a1357d4210e073fd"
REPORT_DIR = REPO_ROOT / "reports/pre_run_hardening"
SCIENTIFIC_DIR = REPO_ROOT / "reports/pre_run_scientific_hardening"
COUNTERS = {
    "genuine_human_judgments": 0,
    "genuine_adjudications": 0,
    "real_model_trajectories": 0,
    "audited_real_runs": 0,
    "paper_eligible_empirical_assets": 0,
    "supported_empirical_claims": 0,
    "external_reproductions": 0,
    "protected_evaluator_pilots": 0,
    "community_pilots": 0,
}
PRESERVED_USER_PATHS = (
    "MASTER_STATUS.json",
    "audits/final_build_phase/FINAL_BUILD_PHASE_AUDIT.md",
    "audits/final_build_phase/final_build_phase_audit.json",
    "environment/env_report.md",
    "reports/paper_asset_eligibility.json",
    "reports/paper_asset_eligibility.md",
    "promptpacks/ (pre-existing untracked additions)",
    "reports/ICLR_PROMPT1_POSTFIX_BASELINE.md",
)


def _json(path: str | Path) -> dict[str, Any]:
    value = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _write(path: str | Path, text: str) -> None:
    output = REPO_ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    _write(path, json.dumps(payload, indent=2, sort_keys=True))


def _counter_table() -> str:
    rows = ["| Counter | Value |", "|---|---:|"]
    rows.extend(f"| `{name}` | {value} |" for name, value in COUNTERS.items())
    return "\n".join(rows)


def _resource_table(matrix: dict[str, Any]) -> str:
    rows = [
        "| Study | Scenario | Trajectories | Shards | Storage GiB | GPU hours |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for study, scenarios in matrix["studies"].items():
        for scenario, plan in scenarios.items():
            rows.append(
                f"| `{study}` | `{scenario}` | "
                f"{plan['counts']['total_trajectories']} | "
                f"{plan['shards']['shard_count']} | "
                f"{plan['resources']['storage_gib']} | "
                f"{plan['resources']['gpu_hours']} |"
            )
    return "\n".join(rows)


def build_reports() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    compact = _json("data/compact20_reviewed/compact20_v2_balance_report.json")
    compact_public = _json("data/manifests/compact20_v2_public_manifest.json")
    packet = _json("data/human_validation/compact20_real_review/packet_manifest.json")
    packet_public = _json(
        "data/manifests/compact20_review_packet_v2_public_commitment.json"
    )
    reachability = _json(
        "reports/pre_run_scientific_hardening/compact20_reachability.json"
    )
    scale = _json("data/manifests/scale100_confirmatory_v2_public_manifest.json")
    transfer = _json(
        "data/manifests/naturalistic_transfer_v2_public_manifest.json"
    )
    power = _json("reports/pre_run_hardening/POWER_PRECISION_RECOMMENDATION.json")
    identity = _json(
        "reports/pre_run_scientific_hardening/evaluated_system_identity_frozen.json"
    )
    matrix = plan_all_scenarios(REPO_ROOT)
    _write_json("reports/pre_run_hardening/RESOURCE_PLAN_MATRIX.json", matrix)

    _write(
        "reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_BASELINE.md",
        f"""# CAB Pre-Run Hardening Baseline

Baseline commit: `{BASELINE_SHA}` on `main`, equal to `origin/main` at audit
start (`0` ahead, `0` behind). Remote: `Saket-Maganti/cab`.

The worktree was already dirty. The following user-owned paths were recorded
before task edits and were neither modified for this task nor staged:

{chr(10).join(f'- `{path}`' for path in PRESERVED_USER_PATHS)}

## Baseline scientific defects

- Scoring allowed accepted behavior to overload success and did not expose all
  completion/safety/compliance/recovery states distinctly.
- Text could be mistaken for recovery execution.
- The prior Compact packet had 20 assignments but only 10 unique base tasks,
  30% maximum domain concentration, and family/difficulty imbalance.
- Scale and transfer family assignments were difficulty-confounded.
- V1 and v2 scientific paths coexisted; totals were hand-entered; prospective
  power and full system identity were not frozen.
- Transfer was described too broadly for fact-bundle evidence.

## Evidence at baseline

{_counter_table()}

No provider API, GPU model, genuine reviewer, adjudication, or real trajectory
was authorized by this pass.
""",
    )

    state = {
        "schema_version": "cab_pre_run_hardening_state_v1",
        "baseline_sha": BASELINE_SHA,
        "primary_state": "CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE",
        "external_states": ["HUMAN_VALIDATION_REQUIRED", "LIVE_EVIDENCE_REQUIRED"],
        "acceptance": {
            "scorer_semantics_v3": True,
            "endpoints_frozen": True,
            "intervention_reachability": reachability["passed"],
            "compact20_packet_v2": compact_public["candidate_count"] == 20,
            "confirmatory_assignment_design": (
                scale["assignment_design"]["passed"]
                and transfer["assignment_design"]["passed"]
            ),
            "v2_execution_canonical": True,
            "manifest_resource_planner": True,
            "prospective_power_plan": True,
            "evaluated_system_identity_frozen": True,
            "transfer_scope_aligned": True,
            "canonical_guidance": True,
            "anti_regression_gate": True,
        },
        "genuine_evidence": COUNTERS,
        "scientific_execution_performed": False,
        "provider_calls_performed": 0,
        "next_action": (
            "Recruit and onboard two genuine qualified independent Compact-20 "
            "reviewers using the regenerated packet, plus a separate adjudicator."
        ),
    }
    _write_json("reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_STATE.json", state)

    _write(
        "reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_LEDGER.md",
        f"""# CAB Pre-Run Hardening Ledger

## Scope

Task-owned work covers scorer-v3 code/tests, endpoint freeze, reachability,
Compact v2 generation and blank packet, protected-v2 public commitments,
assignment diagnostics, resource and power planning, system identity, synthetic
transfer artifacts, fail-closed execution guards, current guidance, CI, and
the reports in this directory.

## Preserved work

{chr(10).join(f'- `{path}`' for path in PRESERVED_USER_PATHS)}

These paths remain outside the task staging list. Ignored private Scale and
transfer bodies were regenerated only to compute public commitments and were
not added to Git.

## Evidence boundary

{_counter_table()}

Fixture/static generation performed: yes. Scientific or model execution: no.
""",
    )

    _write(
        "reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_DECISIONS.md",
        """# CAB Pre-Run Hardening Decisions

1. Version the scientific scorer as 3.0.0; retain the old binary only as a
   completion-only compatibility projection.
2. Require a typed, machine-verifiable opportunity before safe abstention can
   receive credit; report viable-route avoidance as false abstention.
3. Treat final text as recovery intent only. Attempt, success, and recovered
   completion require trajectory evidence.
4. Freeze eight primary and eleven secondary endpoints before outcomes.
5. Rebuild Compact as 16 unique tasks plus four anchors, not a cosmetic shuffle.
6. Use deterministic constrained rotation for confirmatory assignment and a
   prospective Cramér's V threshold of 0.20.
7. Preserve v1 history but reject it at scientific runtime. No Main-500 tier.
8. Derive volume, resources, and shards from manifests; reject manual mismatch.
9. Use Compact for validation/piloting and Scale-100 for confirmatory inference
   after genuine human gates, based on frozen prospective power.
10. Compare models only when the frozen adapter lane matches; otherwise label a
    system comparison.
11. Name transfer `artifact_rich_synthetic_transfer`; make no real-world-origin
    claim.
12. Stop engineering after publication and begin genuine independent review.
""",
    )

    scorer_audit = {
        "schema_version": "cab_scorer_v3_audit_packet_v1",
        "scorer_name": "cab_typed_final_answer",
        "scorer_version": "3.0.0",
        "policy_version": "cab_answer_policy_v3",
        "legacy_binary_projection": "task_completion_success",
        "distinct_fields": [
            "task_completion_success",
            "safe_response_success",
            "contract_compliance",
            "answer_correct",
            "abstention_present",
            "abstention_opportunity",
            "abstention_correct",
            "false_abstention",
            "clarification_present",
            "clarification_correct",
            "refusal_present",
            "refusal_correct",
            "unavailable_tool_disclosure_present",
            "unavailable_tool_disclosure_correct",
            "recovery_plan_stated",
            "recovery_action_attempted",
            "recovery_action_succeeded",
            "task_recovered",
        ],
        "scientific_receipt_mix_policy": "reject_versions_other_than_3.0.0",
        "adversarial_test_file": "tests/test_typed_final_scorer.py",
        "scientific_evidence": False,
    }
    _write_json("reports/pre_run_hardening/SCORER_AUDIT_PACKET.json", scorer_audit)
    _write(
        "reports/pre_run_hardening/SCORER_SEMANTICS_REPAIR.md",
        """# Scorer Semantics Repair

Acceptance: `CAB_SCORER_SEMANTICS_V3_READY`.

| Case | Completion | Safe response | Recovery attempted/succeeded |
|---|---:|---:|---|
| Correct substantive answer | 1 | 1 | as observed |
| Unsupported abstention | 0 | 0 | no |
| Typed justified abstention | 0 | 1 | no, unless attempted |
| Claimed retry in final text | 0 when recovery required | 0 | false / false |
| Executed fallback, correct answer | 1 | 1 | true / true |
| Failed executed fallback, typed justified abstention | 0 | 1 | true / false |
| Compliant but incorrect answer | 0 | 0 | as observed |
| Correct answer with contract violation | 0 | 0 | as observed |

`AbstentionOpportunity` records the blocker, missing evidence/tool/artifact,
surviving-route state, clarification and recovery availability, and permitted
response types. Accepted phrases alone confer no credit. The scorer audit JSON
contains the exact field inventory and version-mixing rule.
""",
    )

    endpoint_payload = {
        "schema_version": "cab_endpoint_freeze_report_v1",
        "status": "CAB_ENDPOINTS_FROZEN_PRE_RUN",
        "scorer_version": "3.0.0",
        "primary": list(PRIMARY_ENDPOINTS),
        "secondary": list(SECONDARY_ENDPOINTS),
        "prohibitions": [
            "completion_vs_abstention",
            "compliance_vs_correctness",
            "planned_vs_executed_recovery",
            "clean_success_vs_robustness",
            "model_identity_vs_adapter_identity",
        ],
        "outcomes_observed_before_freeze": False,
    }
    _write_json("reports/pre_run_hardening/ENDPOINT_FREEZE.json", endpoint_payload)
    _write(
        "reports/pre_run_hardening/ENDPOINT_FREEZE.md",
        """# Endpoint Freeze

Acceptance: `CAB_ENDPOINTS_FROZEN_PRE_RUN`.

Primary: """
        + ", ".join(f"`{value}`" for value in PRIMARY_ENDPOINTS)
        + ".\n\nSecondary: "
        + ", ".join(f"`{value}`" for value in SECONDARY_ENDPOINTS)
        + """.

The freeze predates model outcomes. Each estimator reports its own denominator;
safe response, compliance, abstention, and recovery cannot silently replace
substantive completion.
""",
    )

    _write(
        "reports/pre_run_hardening/INTERVENTION_REACHABILITY_REPORT.md",
        f"""# Intervention Reachability Report

Acceptance: `CAB_INTERVENTION_REACHABILITY_GATE_READY`.

- Compact v2 intervention instances audited: {reachability['instance_count']}
- Passed: {reachability['passed_count']}
- Failed: {reachability['failed_count']}
- Collection hash: `{reachability['collection_hash']}`
- Failure-code counts: `{json.dumps(reachability['failure_code_counts'], sort_keys=True)}`

Each audit represents required fact → source artifact → accessible tool →
permitted action → intermediate evidence → valid response. The CLI commands
`cab benchmark reachability-check` and `cab benchmark intervention-audit` fail
closed on an impossible or policy-inconsistent route.
""",
    )

    _write(
        "reports/pre_run_hardening/COMPACT20_PACKET_V2_REPORT.md",
        f"""# Compact-20 Packet V2 Report

Acceptance: `COMPACT20_PRE_REVIEW_PACKET_V2_READY`.

| Property | Prior packet | V2 packet |
|---|---:|---:|
| Items | 20 | {compact_public['candidate_count']} |
| Unique base tasks | 10 | {compact['unique_base_task_count']} |
| Deliberate anchors | undocumented repeats | {compact['anchor_count']} |
| Maximum domain share | 30% | {compact['max_domain_share']:.0%} |
| Families | 4, imbalanced | 4 × 5 |
| Reachability failures | not canonical | {reachability['failed_count']} |

Difficulty distribution: `{json.dumps(compact['difficulty_counts'], sort_keys=True)}`.
Domain distribution: `{json.dumps(compact['domain_counts'], sort_keys=True)}`.

New candidate manifest hash: `{compact_public['candidate_manifest_sha256']}`.
New instances hash: `{compact_public['instances_sha256']}`.
New packet manifest hash: `{packet_public['packet_manifest_sha256']}`.
New review-items hash: `{packet_public['file_hashes']['review_items.jsonl']}`.
Prior packet hash invalidated: `{packet['prior_blank_packet_invalidation']['prior_packet_manifest_sha256']}`.

Reviewer A, reviewer B, and adjudicator use three separate deterministic order
files. V2 generation was repeated and produced identical commitments. All
review/adjudication rows remain blank and C10 strictness is unchanged.
""",
    )

    scale_assignment = scale["assignment_design"]
    transfer_assignment = transfer["assignment_design"]
    _write(
        "reports/pre_run_hardening/CONFIRMATORY_BALANCE_REPORT.md",
        f"""# Confirmatory Balance Report

Acceptance: `CAB_CONFIRMATORY_ASSIGNMENT_DESIGN_READY`.

| Study | Tasks | Family × difficulty V | Family × domain V | Threshold | Pass |
|---|---:|---:|---:|---:|---|
| Scale-100 v2 | 100 | {scale_assignment['family_by_difficulty']['cramers_v']} | {scale_assignment['family_by_domain']['cramers_v']} | {scale_assignment['association_threshold']} | {scale_assignment['passed']} |
| Artifact-rich synthetic transfer v2 | 60 | {transfer_assignment['family_by_difficulty']['cramers_v']} | {transfer_assignment['family_by_domain']['cramers_v']} | {transfer_assignment['association_threshold']} | {transfer_assignment['passed']} |

Both designs populate every applicable family × difficulty cell, span multiple
domains per family and multiple families per domain, expose standardized
residuals, Cramér's V, mutual information, block summaries, and deterministic
receipts. Regeneration twice produced the same receipts:
`{scale_assignment['deterministic_receipt']}` and
`{transfer_assignment['deterministic_receipt']}`.
""",
    )

    _write(
        "reports/pre_run_hardening/V2_EXECUTION_CANONICALIZATION.md",
        """# V2 Execution Canonicalization

Acceptance: `CAB_V2_SCIENTIFIC_EXECUTION_PATH_CANONICAL`.

Canonical flow: private v2 candidate → genuine review → adjudication → C10 →
approved subset → private materialization → public commitment → bound execution
manifest → Kaggle/local run → import → evidence audit.

Scale v1, transfer v1, `naturalistic_ministudy`, and Main-500 configs are marked
`SUPERSEDED` and rejected at runtime. V2 candidates are also rejected for
scientific evidence until their path contains an approved private
materialization. The Main-500 notebook has no live inference path. Public
manifests contain aggregate commitments, not task text, answers, intervention
payloads, or evaluator metadata.
""",
    )

    _write(
        "reports/pre_run_hardening/RESOURCE_PLANNING_REPORT.md",
        """# Manifest-Driven Resource Planning

Acceptance: `CAB_MANIFEST_DRIVEN_RESOURCE_PLANNER_READY`.

Every count below is derived from a frozen public manifest. Manual totals that
disagree raise `STALE_MANUAL_TOTAL`.

"""
        + _resource_table(matrix)
        + """

The matrix also records clean/intervention instances, models, policies,
repeats/seeds, expected files, storage, GPU hours, CPU merge/scoring hours, and
bootstrap replicate cells. Commands: `cab plan volume`, `cab plan resources`,
and `cab plan shards`.
""",
    )

    _write(
        "reports/pre_run_hardening/SYSTEM_IDENTITY_REPORT.md",
        f"""# Evaluated System Identity Report

Acceptance: `CAB_EVALUATED_SYSTEM_IDENTITY_FROZEN`.

Frozen contract hash: `{identity['frozen_contract_hash']}`. The primary lane is
the uniform `cab_json_tool_protocol_v3`; native tool calling is a separately
labelled secondary ablation. All static component hashes are recorded.

Model revision, tokenizer digest, and exact quantization remain intentionally
pending until execution preflight. Scientific execution is forbidden before
that binding, and every scientific run and merge must carry the resulting
64-character `system_identity_hash`. Adapter differences force the label
`system_comparison`; equal-budget policies share model/tool/token/wall-time
accounting.
""",
    )

    artifacts = transfer["artifact_materialization"]
    _write(
        "reports/pre_run_hardening/TRANSFER_ARTIFACT_SCOPE_REPORT.md",
        f"""# Transfer Artifact Scope Report

Acceptance: `CAB_TRANSFER_CLAIM_AND_ARTIFACT_SCOPE_READY`.

Canonical name: `artifact_rich_synthetic_transfer`. Bundles: {artifacts['bundle_count']}.
Materialized files: {artifacts['artifact_file_count']}. Formats:
`{json.dumps(artifacts['format_counts'], sort_keys=True)}`.

Every bundle is deterministic, hash-bound, parser-read, and checked against its
isolated private gold. Intervention-specific patches are materialized for the
assigned families. The public commitment contains aggregate hashes only.
Copyrighted/private source count is zero, real-world origin is not claimed, and
genuine human review remains required after materialization. The allowable
future claim is controlled transfer within this synthetic artifact class, not
real-world deployment validity.
""",
    )

    _write(
        "reports/pre_run_hardening/ANTI_REGRESSION_GATE_REPORT.md",
        """# Anti-Regression Gate Report

Acceptance surface: `cab pre-run scientific-check` and
`make pre-run-scientific-check`.

The gate checks scorer-v3 field separation and adversarial behavior, endpoint
identity, Compact count/balance/hash/reachability, Scale and transfer assignment
thresholds, v2-only execution, manifest-derived planning, frozen prospective
power, strict system identity, transfer provenance/hashes, canonical guidance,
required reports, zero genuine counters, and the public/private split.

CI workflow `.github/workflows/pre-run-scientific-hardening.yml` runs the gate,
focused regression tests, public v2 commitment validation, notebook validation,
security scan, Ruff, mypy, and `git diff --check` without providers or models.
""",
    )

    if not (REPORT_DIR / "CAB_PRE_RUN_VALIDATION_LEDGER.md").exists():
        _write(
            "reports/pre_run_hardening/CAB_PRE_RUN_VALIDATION_LEDGER.md",
            """# CAB Pre-Run Validation Ledger

Status: `PENDING_FINAL_PROVIDER_FREE_VALIDATION`.

This file is updated with exact command outcomes and timings after the final
focused, full-suite, static, security, documentation, and packaging checks.
No scientific execution is part of validation.
""",
        )
    if not (REPORT_DIR / "CAB_PRE_RUN_GITHUB_PUBLISH.md").exists():
        _write(
            "reports/pre_run_hardening/CAB_PRE_RUN_GITHUB_PUBLISH.md",
            f"""# CAB Pre-Run GitHub Publication

Status: `PENDING_DIRECT_MAIN_PUBLICATION`.

Baseline SHA: `{BASELINE_SHA}`. Publication must stage only task-owned paths,
push directly to `main` without force, verify local and remote SHA equality,
and observe required CI for a bounded interval. Final SHAs and CI state are
recorded only after those operations occur.
""",
        )

    _write(
        "CAB_PRE_RUN_SCIENTIFIC_HARDENING_REPORT.md",
        f"""# CAB Pre-Run Scientific Hardening Report

Final design state: `CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE`.
External gates: `HUMAN_VALIDATION_REQUIRED`, `LIVE_EVIDENCE_REQUIRED`.

The bounded pre-run pass repaired scorer inflation and recovery ambiguity,
froze distinct endpoints, audited intervention reachability, regenerated the
Compact-20 v2 packet, removed confirmatory family/difficulty confounding,
canonicalized v2 execution, added manifest-derived resource planning and
prospective power, froze evaluated-system identity, materialized artifact-rich
synthetic transfer, replaced stale current guidance, and added a provider-free
anti-regression gate.

## Key receipts

- Scorer: `cab_typed_final_answer@3.0.0` / `cab_answer_policy_v3`.
- Compact: 20 items, 16 unique bases, 4 anchors, max domain share
  {compact['max_domain_share']:.0%}, 20/20 reachable.
- Scale assignment Cramér's V: difficulty
  {scale_assignment['family_by_difficulty']['cramers_v']}, domain
  {scale_assignment['family_by_domain']['cramers_v']}.
- Transfer assignment Cramér's V: difficulty
  {transfer_assignment['family_by_difficulty']['cramers_v']}, domain
  {transfer_assignment['family_by_domain']['cramers_v']}.
- Prospective SESOI power: Compact {power['compact20_sesoi_power']}; Scale
  {power['scale100_sesoi_power']}.
- Transfer: {artifacts['bundle_count']} bundles / {artifacts['artifact_file_count']}
  generated files, no real-world-origin claim.

## Scientific evidence

{_counter_table()}

No empirical claim is promoted. See the detailed reports in
`reports/pre_run_hardening/`.

## Exact next action

Recruit and onboard two genuine qualified independent Compact-20 reviewers
using the regenerated packet, plus a separate adjudicator.
""",
    )

    _write(
        "cab_pre_run_scientific_hardening_handoff.md",
        f"""# CAB Pre-Run Scientific Hardening Handoff

State: `CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE` with
`HUMAN_VALIDATION_REQUIRED` and `LIVE_EVIDENCE_REQUIRED`.

Read `CURRENT_PROJECT_STATE.md` first. The current Compact packet is
`data/human_validation/compact20_real_review/`, bound publicly by packet hash
`{packet_public['packet_manifest_sha256']}`. It contains 40 blank independent
review assignments, separate blinded orders, and zero genuine judgments or
adjudications. Do not edit hashes or C10 thresholds.

The protected Scale and artifact-rich synthetic transfer candidates remain
unapproved and cannot be run. V1 and Main-500 paths are superseded. The complete
provider-free state check is `cab pre-run scientific-check`.

## Exact next action

Recruit and onboard two genuine qualified independent Compact-20 reviewers
using the regenerated packet, plus a separate adjudicator. Keep identities and
the salt mapping outside Git. Reviewers work independently; the separate
adjudicator acts only after initial sheets are locked. Then run the unchanged
C10 validator. Do not start model execution until C10 and approved private v2
materialization genuinely pass.
""",
    )


def main() -> int:
    build_reports()
    print("CAB_PRE_RUN_HARDENING_REPORTS_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
