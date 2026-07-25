# Pre-Provider Freeze Checklist

Use this checklist before creating any approved provider-pilot config or spending
provider budget.

## Freeze Inputs

- [ ] Repair plan reviewed and top provider-pilot blockers resolved or deferred by advisor.
- [ ] Dataset splits reviewed for duplicate IDs, leakage, and clean/intervention overlap.
- [ ] Intervention taxonomy reviewed and committed.
- [ ] Gold-output validation has no blockers.
- [ ] Tool-schema validation has no blockers.
- [ ] Static leakage report has no blockers.
- [ ] Config profiles reviewed; templates keep `allow_paid_calls: false`.
- [ ] Provider preflight report reviewed.
- [ ] Advisor review packet signed or otherwise approved.

## Git and Provenance

- [ ] Benchmark manifest generated.
- [ ] Current commit hash recorded.
- [ ] Dirty tree either resolved or explicitly documented.
- [ ] Dataset version/freeze manifest recorded where applicable.
- [ ] Lockfile status reviewed.

## Evidence Boundary

Freezing the repo does not change claim status:

- paper-eligible runs: 0
- eligible paper assets: 0
- C1-C8: planned / unsupported
- C9: engineering_only
- C10: planned / unsupported

## Safe Freeze Commands

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_pre_provider_freeze_reports
python3 scripts/check_evidence_safety.py
```

## Forbidden During Freeze

```bash
python3 -m causal_agent_bench run --config ...
make smoke
make test
python3 -m causal_agent_bench run-llm-judge ...
python3 -m causal_agent_bench fill-paper-from-run --promote-to-supported ...
python3 -m causal_agent_bench update-claim-ledger --promote-to-supported ...
```

## Dataset Fix Decision

Request dataset fixes before provider spend if any of these are true:

- repair plan has `must_fix_before_provider_pilot` items
- gold-output validation has blockers
- tool-schema validation has blockers
- static leakage has blockers
- provider preflight is blocked
- advisor cannot identify the exact cost cap, stop cap, and post-run review path

## How to Use the Repair Plan Without Drowning in Raw Issues

Do not freeze against thousands of individual symptoms. Freeze decisions should
use the clustered repair plan:

1. Review `Root Cause Summary`.
2. Resolve or advisor-defer `Top 10 Provider-Pilot Blockers`.
3. Check `Suppressed / Deduplicated Symptoms` only to understand blast radius.
4. Rerun:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_triage_calibrated_reports
```

If the provider gate remains `blocked`, do not create a runnable approved config
and do not run providers. These static reports can justify method-readiness
work, not empirical claims.

## Provider Preflight Gate States

- `template_safe_but_not_runnable`: acceptable for freeze review, never runnable.
- `ready_for_approval_review`: ready for advisor review, not provider execution.
- `ready_for_dry_run`: approved copy can proceed to dry-run validation.
- `ready_for_live_run`: explicit live-run approval and paid-call intent exist.
- `blocked`: freeze is not ready for provider spend.

## How to Read Static Leakage Reports

Review leakage clusters, not raw findings. The freeze decision should focus on:

- top provider-pilot leakage blockers
- answer text visible in prompts/context
- intervention labels visible to users
- hidden metadata exposed in observations
- protected split overlap

Raw findings are retained in JSON for auditability. They are not the work queue.

## How to Interpret Near-Duplicate Leakage

Before freeze, near-duplicate prompt clusters should be interpreted through the
classification fields, not raw overlap alone:

- `true_split_leakage`, `answer_leakage`, and `duplicate_id_leakage` block the
  provider-pilot freeze unless explicitly repaired or advisor-deferred.
- `clean_intervention_pair_similarity` is expected if the linked variants are
  not split across protected boundaries.
- `task_family_boilerplate`, `shared_tool_description`, and
  `shared_system_instruction` are false-positive candidates; review examples,
  but do not treat raw counts as the fix list.
- `split_metadata_issue` means split metadata must be clarified before provider
  approval.

Do not delete or rewrite tasks solely because raw near-duplicate counts are
large. Confirm task-specific overlap and split risk first.

## Current Safe Next Action

If still on the template, get advisor approval before creating an approved copy.
If leakage blockers remain, fix the top clustered leakage root causes and rerun
the no-run bundle. Provider commands remain forbidden until the preflight gate
allows the specific dry-run or live-run step.

## Leakage Repair Workflow Before Provider Pilot

Freeze review should include the leakage repair planner:

1. Run `all-no-run-reports`.
2. Inspect static leakage clusters.
3. Inspect `leakage_repair_plan.md`.
4. Review `proposed_patch_manifest.md` and confirm it does not touch `results/`,
   claim ledgers, provider configs, or scientific-evidence fields.
5. Apply only reviewed dataset fixes manually, or wait for a separate explicit
   patch command.
6. Rerun `all-no-run-reports`.
7. Do not create an approved provider config until leakage blockers are resolved
   or explicitly accepted in advisor review.

## Readiness War Room

Before freeze, generate the war-room packet:

```bash
python3 -m causal_agent_bench readiness-war-room --reports-dir /tmp/cab_pre_provider_freeze_reports --output-dir /tmp/cab_pre_provider_freeze_reports/readiness_war_room
```

Review `readiness_war_room.md`, `readiness_graph.mmd`, and
`reviewer_gauntlet.md` before requesting provider approval. The packet is a
static review aid only; it does not authorize provider execution or empirical
claims.
