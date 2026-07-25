# Next No-Run Build Plan

This phase adds static benchmark-strengthening infrastructure: benchmark quality audit, intervention isolation audit, synthetic trajectory diagnostics, human-validation templates, cost estimation, method figure scaffolds, release readiness checks, and CLI entry points.

None of these artifacts are empirical evidence. They do not run agents, call providers, call local models, promote claims, mark runs paper-eligible, or fill paper results.

## Safe Commands

```bash
python -m causal_agent_bench benchmark-quality --output-dir reports/benchmark_quality
python -m causal_agent_bench intervention-isolation-audit --output-dir reports/intervention_isolation
python -m causal_agent_bench synthetic-fixture-check --output-dir reports/synthetic_fixtures
python -m causal_agent_bench human-validation-packet --output-dir reports/human_validation
python -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_template.yaml --output-dir reports/cost_estimates
python -m causal_agent_bench method-figure-scaffolds --output-dir figures/method
python -m causal_agent_bench release-readiness --output-dir reports/release_readiness
python -m causal_agent_bench all-no-run-reports --output-dir reports/no_run
```

## Do Not Run During This Phase

Do not run benchmark execution commands, provider commands, paid API calls, local LLM jobs, claim promotion, paper filling with promotion flags, broad test lanes, or result export overrides against real paper assets.

## Next Milestone

Before provider execution, complete manual review of the provider pilot template, cost estimate, benchmark quality report, intervention isolation report, and provider-pilot readiness packet. Keep `allow_paid_calls=false` until explicit budget and execution approval exists.

## Paper Support

These reports support the eventual paper by making quality gates, intervention validity checks, annotation readiness, and release blockers explicit. They do not support C1-C8 or C10 without real eligible provider runs and real human-validation artifacts.

## Upgrade Additions

The next no-run upgrade adds scored benchmark quality, scored intervention isolation, dataset issue triage, provider-pilot preflight validation, synthetic human-validation dry-run sampling, method-only appendix generation, evidence dashboard indexing, and config/metadata linting.

These additions remain static governance tools. They do not authorize provider execution, promote claims, or convert synthetic fixtures into evidence.
## Advanced No-Run Improvement Phase

Next static build priority:

1. Use `repair-plan` to rank dataset/config/paper blockers.
2. Generate benchmark/dataset/intervention/limitations cards.
3. Keep `configs/intervention_taxonomy.yaml` as the machine-readable field-change policy.
4. Run gold-output, tool-schema, and static leakage validators.
5. Generate benchmark manifest and config profiles before advisor review.
6. Generate advisor packet and paper readiness map before provider spend.
7. Regenerate the evidence dashboard so “Next 10 Actions” reflects the repair plan.

Safe command:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_advanced_upgrade_reports
```

This phase remains advisory/static. It does not run models, call providers,
promote claims, approve provider configs, or fill empirical paper results.

## How to Use the Repair Plan Without Drowning in Raw Issues

The next cleanup phase is not more infrastructure. It is triage calibration:
collapse repeated symptoms into root causes, fix the provider-pilot blockers,
and rerun the no-run bundle.

Use this order:

1. Open the repair plan `Root Cause Summary`.
2. Work only from `Top 10 Provider-Pilot Blockers` until that list is empty or
   advisor-deferred.
3. Then use `Top 50 Actionable Repairs`.
4. Ignore the raw 10k-style symptom list initially; it exists for traceability.
5. Rerun:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_triage_calibrated_reports
```

Provider execution remains blocked until provider preflight and advisor approval
make the exact next action explicit. No no-run report supports C1-C8 or C10.

## Provider Preflight Gate States

- `template_safe_but_not_runnable`: safe static template, not a runnable config.
- `ready_for_approval_review`: non-template config needs advisor/budget review.
- `ready_for_dry_run`: approved copy can proceed to dry-run validation only.
- `ready_for_live_run`: live approval and paid-call intent are explicit.
- `blocked`: fix static blockers before any provider action.

## How to Read Static Leakage Reports

Use clustered leakage root causes first. Ignore the raw findings initially,
especially when the raw count is very large. Fix provider-pilot leakage blockers
before main-benchmark warnings, then rerun:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_provider_static_cleanup_reports
```

Static leakage reports are deterministic heuristics. They improve readiness and
reviewability; they do not become empirical evidence.

## How to Interpret Near-Duplicate Leakage

The next cleanup phase should treat near-duplicate prompts as a triage signal,
not a deletion queue. Raw token overlap can be caused by shared system
instructions, repeated tool descriptions, and normal task-family boilerplate.

Priority order:

1. Fix `answer_leakage`, `duplicate_id_leakage`, and confirmed
   `true_split_leakage`.
2. Review `split_metadata_issue` and `needs_manual_review` clusters with
   representative examples.
3. Treat `clean_intervention_pair_similarity` as expected when both variants
   remain in the same split family.
4. Treat `task_family_boilerplate`, `shared_tool_description`, and
   `shared_system_instruction` as false-positive candidates unless
   task-specific overlap remains high across protected splits.

Provider-pilot split leakage is serious; boilerplate reuse is not empirical
evidence and does not support claims.

## Current Safe Next Action

For a template-only provider config: complete advisor approval and create an
approved copy later. For leakage blockers: fix the top clustered root causes
first. Do not run providers until preflight explicitly allows the next dry-run
or live-run step.

## Leakage Repair Workflow Before Provider Pilot

The next no-run step is leakage repair planning, not provider execution:

1. Run `all-no-run-reports`.
2. Inspect clustered static leakage output.
3. Run or inspect `leakage-repair-plan`.
4. Review `proposed_patch_manifest.md`; it is advisory and applies nothing.
5. Make only reviewed dataset fixes manually or with a later explicit patch
   command.
6. Rerun `all-no-run-reports`.
7. Keep provider configs as templates until leakage blockers are resolved or
   explicitly advisor-accepted.

Safe command:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_leakage_repair_planner_reports
```

## Readiness War Room Upgrade

The war-room layer turns the no-run reports into a compact strategy packet:
mission status, risk radar, unlock ladder, reviewer gauntlet, what-if scenarios,
and a Mermaid readiness graph.

```bash
python3 -m causal_agent_bench readiness-war-room --reports-dir reports --output-dir reports/readiness_war_room
```

This remains no-run infrastructure. It is useful for advisor/reviewer prep, but
it does not approve provider spend or support empirical claims.

## Governance OS Upgrade

The bigger command-center layer is `governance-os`. It compiles no-run reports
into a release/provider/paper control plane:

- go/no-go matrix
- critical-path graph
- blocker burn-down plan
- sprint board
- reviewer red-team dossier
- command firewall
- claim-safe wording bank
- decision log template
- artifact routing manifest

```bash
python3 -m causal_agent_bench governance-os --reports-dir reports --output-dir reports/governance_os
```

This should be reviewed before advisor approval, provider dry-run planning, or
public release packaging.
