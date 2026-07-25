# Prompt 09 — Execute 3-Model Compact-20 Provider Pilot, Gated

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a live provider execution lead and evidence-governance enforcer.

## Task

Execute exactly one approved 3-model Compact-20 pilot only if every gate passes. This is the first real evidence run. Do not broaden scope.

## Global Evidence Rules

- Do not fabricate results, human annotations, provider outputs, costs, or reviewer labels.
- Do not promote C1-C8/C10 unless the required real evidence exists and the evidence-safety checks pass.
- C9 may remain `engineering_only`; stub/mock/dry-run outputs can only support pipeline wiring.
- Do not mark paper assets eligible manually.
- Do not store API keys, tokens, or secrets in YAML, Markdown, JSON, logs, CSVs, or repo files.
- Provider credentials must be checked only through environment presence checks without printing values.
- Do not leave `allow_paid_calls=true` after any live run.
- Do not run providers, local LLMs, `causal_agent_bench run`, `main_200`, `main_500`, Compact-50, or broad sweeps unless the prompt explicitly allows it and every gate passes.
- Always distinguish `engineering_only`, `zero_cost_local_preliminary`, `provider_pilot_preliminary`, `paper_candidate_pending_audit`, and `paper_eligible`.



## Inspect

- `reports/COMPACT20_3MODEL_PRELIVE_PREFLIGHT.md`
- `configs/compact20_3model_APPROVED.yaml`
- approval docs
- environment credential presence
- cost estimate
- reviewed Compact-20 slice

## Actions

1. Proceed only if prelive report says `PRELIVE_READY_FOR_SINGLE_EXECUTION`.
2. Re-run evidence safety and config validation.
3. Edit only the approved config: set `allow_paid_calls=true` and `approved_for_live_run=true`.
4. Run exactly one command: `PYTHONPATH=src python3 -m causal_agent_bench run --config configs/compact20_3model_APPROVED.yaml`.
5. Immediately after success or failure, set `allow_paid_calls=false` and lock config if schema supports.
6. Identify run directory.
7. Create `reports/COMPACT20_3MODEL_LIVE_RUN_EXECUTION_REPORT.md` or a blocked/failed report.

## Deliverables

- live execution report or blocked/failed report
- run directory identification
- locked config confirmation

## Tests / Checks

- no extra provider commands
- no main_200/main_500/Compact-50
- trajectory count <= approval
- budget <= approval
- config locked after run

## Allowed Commands

['COMPACT20_3MODEL_RUN_COMPLETE_PENDING_AUDIT', 'COMPACT20_3MODEL_RUN_FAILED_LOCKED', 'COMPACT20_3MODEL_RUN_BLOCKED_NO_EXECUTION']

## Final Response Format

# Prompt 09 — Execute 3-Model Compact-20 Provider Pilot, Gated Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `p`
- `y`
- `t`
- `h`
- `o`
- `n`
- `3`
- ` `
- `s`
- `c`
- `r`
- `i`
- `p`
- `t`
- `s`
- `/`
- `c`
- `h`
- `e`
- `c`
- `k`
- `_`
- `e`
- `v`
- `i`
- `d`
- `e`
- `n`
- `c`
- `e`
- `_`
- `s`
- `a`
- `f`
- `e`
- `t`
- `y`
- `.`
- `p`
- `y`
- `
`
- `P`
- `Y`
- `T`
- `H`
- `O`
- `N`
- `P`
- `A`
- `T`
- `H`
- `=`
- `s`
- `r`
- `c`
- ` `
- `p`
- `y`
- `t`
- `h`
- `o`
- `n`
- `3`
- ` `
- `-`
- `m`
- ` `
- `c`
- `a`
- `u`
- `s`
- `a`
- `l`
- `_`
- `a`
- `g`
- `e`
- `n`
- `t`
- `_`
- `b`
- `e`
- `n`
- `c`
- `h`
- ` `
- `v`
- `a`
- `l`
- `i`
- `d`
- `a`
- `t`
- `e`
- `-`
- `c`
- `o`
- `n`
- `f`
- `i`
- `g`
- ` `
- `-`
- `-`
- `c`
- `o`
- `n`
- `f`
- `i`
- `g`
- ` `
- `c`
- `o`
- `n`
- `f`
- `i`
- `g`
- `s`
- `/`
- `c`
- `o`
- `m`
- `p`
- `a`
- `c`
- `t`
- `2`
- `0`
- `_`
- `3`
- `m`
- `o`
- `d`
- `e`
- `l`
- `_`
- `A`
- `P`
- `P`
- `R`
- `O`
- `V`
- `E`
- `D`
- `.`
- `y`
- `a`
- `m`
- `l`
- `
`
- `P`
- `Y`
- `T`
- `H`
- `O`
- `N`
- `P`
- `A`
- `T`
- `H`
- `=`
- `s`
- `r`
- `c`
- ` `
- `p`
- `y`
- `t`
- `h`
- `o`
- `n`
- `3`
- ` `
- `-`
- `m`
- ` `
- `c`
- `a`
- `u`
- `s`
- `a`
- `l`
- `_`
- `a`
- `g`
- `e`
- `n`
- `t`
- `_`
- `b`
- `e`
- `n`
- `c`
- `h`
- ` `
- `r`
- `u`
- `n`
- ` `
- `-`
- `-`
- `c`
- `o`
- `n`
- `f`
- `i`
- `g`
- ` `
- `c`
- `o`
- `n`
- `f`
- `i`
- `g`
- `s`
- `/`
- `c`
- `o`
- `m`
- `p`
- `a`
- `c`
- `t`
- `2`
- `0`
- `_`
- `3`
- `m`
- `o`
- `d`
- `e`
- `l`
- `_`
- `A`
- `P`
- `P`
- `R`
- `O`
- `V`
- `E`
- `D`
- `.`
- `y`
- `a`
- `m`
- `l`
