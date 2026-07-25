# No-Run Reports Guide

No-run reports inspect static repository files, configs, fixtures, metadata, and paper-governance artifacts. They do not run benchmarks, call providers, call local models, use API keys, promote claims, or make empirical paper assets eligible.

## Reports

- `run-health`: summarizes indexed runs and strict paper eligibility.
- `validate-paper-assets`: checks tables/figures/generated paper artifacts for eligibility metadata.
- `claim-evidence`: summarizes C1-C10 claim support without promotion.
- `paper-todo-inventory`: inventories TODOs, placeholders, and blocked paper language.
- `benchmark-quality`: scores dataset readiness, pairing, splits, metadata, and quality issues.
- `intervention-isolation-audit`: scores static clean/intervention isolation risk.
- `dataset-issue-triage`: groups quality and isolation issues into repair tasks.
- `synthetic-fixture-check`: validates metric-diagnostic synthetic trajectories.
- `human-validation-packet`: writes annotation templates and protocol scaffolding.
- `human-validation-dry-run-sample`: creates a synthetic-only sample annotation packet.
- `estimate-run-cost`: estimates future provider-pilot cost and runtime bounds without APIs.
- `provider-pilot-preflight`: validates an approved provider-pilot config without running it.
- `method-figure-scaffolds`: writes method-only Mermaid diagrams.
- `method-appendix`: writes a method-only appendix scaffold.
- `release-readiness`: summarizes release and empirical-submission blockers.
- `lint-config-metadata`: flags unsafe or ambiguous config metadata.
- `evidence-dashboard`: links and summarizes the governance reports.

## Safe Commands

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_upgrade_reports
python3 -m causal_agent_bench benchmark-quality --output-dir reports/benchmark_quality
python3 -m causal_agent_bench intervention-isolation-audit --output-dir reports/intervention_isolation
python3 -m causal_agent_bench dataset-issue-triage --output-dir reports/dataset_triage
python3 -m causal_agent_bench lint-config-metadata --output-dir reports/config_lint
python3 -m causal_agent_bench evidence-dashboard --output-dir reports/evidence_dashboard
```

## What They Cannot Prove

These reports cannot prove model behavior, provider reliability, causal robustness, human agreement, or empirical benchmark performance. Synthetic fixtures are metric diagnostics only. Method figures and method appendices are paper scaffolds only.

## Provider Pilot Blockers

Provider pilot execution remains blocked until an approved copied config passes preflight, budget caps and stop conditions are documented, dry-run validation is complete, and explicit approval exists. Templates remain blocked for live runs.

## Paper Claim Blockers

C1-C8 and C10 remain planned/unsupported until verified provider-backed runs, eligible paper assets, and required human-validation artifacts exist. C9 may remain engineering-only. No no-run report promotes claims.

## Forbidden Commands

Do not run `python3 -m causal_agent_bench run --config ...`, `make smoke`, `make test`, `run-llm-judge`, provider/full benchmark commands, claim promotion commands, or tests that call experiment/batch/run execution during no-run phases.
## Advanced No-Run Reports

The advanced no-run lane adds publication and advisor-review readiness reports
without running models or providers:

```bash
python3 -m causal_agent_bench repair-plan --input-dir reports --output-dir reports/repair_plan
python3 -m causal_agent_bench benchmark-cards --output-dir reports/benchmark_cards
python3 -m causal_agent_bench validate-gold-outputs --output-dir reports/gold_outputs
python3 -m causal_agent_bench validate-tool-schemas --output-dir reports/tool_schemas
python3 -m causal_agent_bench static-leakage-check --output-dir reports/static_leakage
python3 -m causal_agent_bench benchmark-manifest --output-dir reports/benchmark_manifest
python3 -m causal_agent_bench config-profiles --output-dir reports/config_profiles
python3 -m causal_agent_bench advisor-review-packet --output-dir reports/advisor_review
python3 -m causal_agent_bench paper-readiness-map --output-dir reports/paper_readiness
python3 -m causal_agent_bench evidence-dashboard --reports-dir reports --output-dir reports/evidence_dashboard
```

Or run the static bundle:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_advanced_upgrade_reports
```

Advisory-only reports: benchmark cards, benchmark manifest, config profiles,
advisor packet, and paper readiness map. Blocker reports: repair plan, provider
preflight, intervention isolation, gold-output validation, tool-schema
validation, static leakage, and config lint.

These reports can support method/readiness claims only. They cannot support
empirical performance, robustness, ranking, ablation, or human-validation
claims. Current evidence remains 0 paper-eligible runs, 0 eligible paper assets,
C1-C8/C10 planned / unsupported, and C9 engineering_only.

Forbidden in the no-run lane:

```bash
python3 -m causal_agent_bench run --config ...
make smoke
make test
python3 -m causal_agent_bench run-llm-judge ...
python3 -m causal_agent_bench fill-paper-from-run --promote-to-supported ...
python3 -m causal_agent_bench update-claim-ledger --promote-to-supported ...
```

## How to Use the Repair Plan Without Drowning in Raw Issues

When `repair_plan.json` contains thousands of raw symptoms, start with the
root-cause sections instead of the raw item list:

1. Read `Root Cause Summary`.
2. Fix `Top 10 Provider-Pilot Blockers` first.
3. Use `Top 50 Actionable Repairs` for the next static cleanup batch.
4. Treat `raw_items` and `symptom_items` as traceability evidence, not the
   primary work queue.
5. Rerun:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_triage_calibrated_reports
```

Do not run providers until the provider gate says `ready_for_dry_run` or
`ready_for_live_run` as appropriate, and only after advisor approval. Static
reports remain advisory/no-run aids and cannot support empirical claims.

## Provider Preflight Gate States

- `template_safe_but_not_runnable`: the template has budget/cap/safety fields
  and `allow_paid_calls: false`, but must be copied and approved before use.
- `ready_for_approval_review`: a non-template config has no static blockers but
  still needs advisor/budget approval.
- `ready_for_dry_run`: an approved copy has static budget, cap, provider, and
  dry-run approval markers.
- `ready_for_live_run`: explicit live approval markers and intentional
  `allow_paid_calls: true` exist in an approved copy.
- `blocked`: a required safety/config/preflight condition failed.

Templates must never be live-runnable.

## How to Read Static Leakage Reports

Start with `Root-Cause Summary`, `Top Provider-Pilot Leakage Blockers`, and
`Top Main-Benchmark Leakage Blockers`. Do not inspect a raw 191k-style finding
list manually. Raw findings stay in JSON for traceability; Markdown is capped.

Fix provider-pilot split, answer-leakage, intervention-label, and hidden
metadata exposure clusters first, then rerun:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_provider_static_cleanup_reports
```

Static leakage is heuristic. It can block a run-readiness gate, but it is not
empirical evidence and does not support paper claims.

## How to Interpret Near-Duplicate Leakage

Near-duplicate prompt overlap is not automatically true leakage. The calibrated
report separates raw overlap from boilerplate-adjusted, task-specific overlap.

Use these labels first:

- `true_split_leakage`: treat as a real blocker, especially across provider,
  heldout, train, or main split boundaries.
- `answer_leakage` and `duplicate_id_leakage`: treat as higher priority than
  near-duplicate prompt warnings.
- `clean_intervention_pair_similarity`: expected when the linked clean and
  intervention variants stay inside the same split family.
- `task_family_boilerplate`, `shared_tool_description`, and
  `shared_system_instruction`: usually false-positive candidates caused by
  reusable benchmark scaffolding.
- `split_metadata_issue` and `needs_manual_review`: inspect representative
  examples before deleting or rewriting tasks.

Manual review is required before deleting tasks. Shared instructions, tool
descriptions, and task-family templates can create high raw overlap without
leaking evaluation content. Provider-pilot split leakage remains serious when
task-specific content crosses protected splits.

## Current Safe Next Action

If the config is still template-only, complete advisor review and create an
approved copy later. If leakage blockers remain, fix the top clustered leakage
root causes first. Never run providers until preflight reaches the appropriate
dry-run or live-run ready state.

## Leakage Repair Workflow Before Provider Pilot

Use this workflow before creating any approved provider-pilot config:

1. Run the static bundle:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_leakage_repair_planner_reports
```

2. Inspect `static_leakage/static_leakage_report.md` by cluster, not raw
   finding count.
3. Inspect `leakage_repair_plan/leakage_repair_plan.md`.
4. Review `leakage_repair_plan/proposed_patch_manifest.md`; it proposes
   operations only and does not edit dataset files.
5. Preview proposed deterministic ID renames with
   `apply-leakage-patch` (default mode is preview only). See
   [LEAKAGE_REPAIR_APPLY_GUIDE.md](LEAKAGE_REPAIR_APPLY_GUIDE.md).
6. Apply only reviewed deterministic renames with explicit `--reviewed-ops`,
   `--reviewed-by`, and `--approval-note`. Content edits, split movement, and
   suppression decisions stay preview-only.
7. Document any false-positive clusters in
   `configs/static_leakage_suppressions.yaml` (validated by
   `leakage-suppression-registry`). The registry can never hide
   `answer_leakage` or `duplicate_id_leakage` clusters.
8. Rerun `all-no-run-reports`.
9. Do not create an approved provider config until leakage blockers are
   resolved or explicitly accepted by the advisor.

## Apply-Mode Safety Rules

- Default mode is preview-only and writes a
  `leakage_patch_apply_report.{json,md}` file that lists which operations would
  be applied, which remain preview-only, and which are refused outright.
- Apply mode requires every operation to be both listed via `--selected-op`
  and present in the `--reviewed-ops` file.
- The applier refuses any operation that touches `results/`, the claim ledger,
  paper assets, run metadata, or provider approvals.
- The applier refuses to enable `allow_paid_calls`, `scientific_evidence`,
  `paper_eligible`, or `promote_to_supported`.
- Only deterministic ID renames inside `data/` may be applied. Content edits
  and split movement remain preview-only.

## Readiness War Room

The war-room report is a no-run command-center layer over the static reports:

```bash
python3 -m causal_agent_bench readiness-war-room --reports-dir reports --output-dir reports/readiness_war_room
```

It writes `readiness_war_room.md/json`, `readiness_graph.mmd`,
`reviewer_gauntlet.md`, `what_if_unlock_plan.json`, and
`war_room_manifest.json`.

Use it to inspect mission status, dependency graph, reviewer attack questions,
what-if unlock scenarios, and forbidden-command kill switches. It does not run
models, call providers, apply patches, approve configs, or promote claims.

## Governance OS

For a larger static control plane, generate the Governance OS packet:

```bash
python3 -m causal_agent_bench governance-os --reports-dir reports --output-dir reports/governance_os
```

It writes a multi-artifact packet:

- `governance_os.md/json`
- `critical_path_graph.mmd`
- `go_no_go_matrix.{md,json,csv}`
- `blocker_burndown_plan.{md,json}`
- `sprint_board.{md,json}`
- `reviewer_red_team_dossier.md`
- `command_firewall.{md,json}`
- `claim_safe_wording_bank.{md,json}`
- `decision_log_template.md`
- `artifact_router.{md,json}`
- `control_plane_manifest.json`

Use it as the high-level release/provider/paper command system. It remains
static: no benchmark runs, provider calls, patches, config approval, or claim
promotion.
