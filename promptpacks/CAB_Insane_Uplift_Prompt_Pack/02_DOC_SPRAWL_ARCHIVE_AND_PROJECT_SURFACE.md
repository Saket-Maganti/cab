# Prompt 02 — Doc Sprawl Archive and Focused Project Surface

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a ruthless paper strategist and documentation curator.

## Task

Archive redundant no-run/governance documents and create a focused CAB project surface that reads like a serious benchmark project rather than process theater.

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

- all `.md` files under root, `docs/`, `reports/`, `paper/`
- `README.md`
- `PROJECT_STATUS.md`
- `MASTER_STATUS.json`
- claim ledger files
- approval docs
- no-run reports

## Actions

1. Create `docs/CAB_FOCUSED_PROJECT_SURFACE.md` with: thesis, built components, missing evidence, current claim state, next scientific gate, forbidden claims, and safe commands.
2. Create `docs/archive/no_run_scaffold/ARCHIVE_INDEX.md`.
3. Move redundant/self-congratulatory/obsolete docs to `docs/archive/no_run_scaffold/` without breaking tests.
4. Keep active: approvals, claim ledger, C10/human validation protocols, current execution plans, evidence safety docs.
5. Update `README.md` to point to the focused surface and current next action.
6. Create `reports/DOC_SPRAWL_REDUCTION_REPORT.md` with before/after doc counts.

## Deliverables

- `docs/CAB_FOCUSED_PROJECT_SURFACE.md`
- `docs/archive/no_run_scaffold/ARCHIVE_INDEX.md`
- `reports/DOC_SPRAWL_REDUCTION_REPORT.md`
- updated `README.md`

## Tests / Checks

- Paper section contract passes.
- Evidence safety passes.
- Active docs referenced by tests still exist or references are updated.
- No evidence state changes.

## Allowed Commands

['PROJECT_SURFACE_FOCUSED', 'ARCHIVE_BLOCKED_BY_TEST_REFERENCES', 'DOC_SPRAWL_REDUCTION_BLOCKED']

## Final Response Format

# Prompt 02 — Doc Sprawl Archive and Focused Project Surface Report

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
- `p`
- `a`
- `p`
- `e`
- `r`
- `_`
- `s`
- `e`
- `c`
- `t`
- `i`
- `o`
- `n`
- `_`
- `c`
- `o`
- `n`
- `t`
- `r`
- `a`
- `c`
- `t`
- `.`
- `p`
- `y`
- ` `
- `-`
- `-`
- `m`
- `o`
- `d`
- `e`
- ` `
- `d`
- `r`
- `a`
- `f`
- `t`
- `
`
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
- `p`
- `y`
- `t`
- `e`
- `s`
- `t`
- ` `
- `-`
- `q`
- ` `
- `t`
- `e`
- `s`
- `t`
- `s`
- `/`
- `t`
- `e`
- `s`
- `t`
- `_`
- `n`
- `o`
- `_`
- `r`
- `u`
- `n`
- `_`
- `b`
- `u`
- `i`
- `l`
- `d`
- `_`
- `p`
- `a`
- `c`
- `k`
- `.`
- `p`
- `y`
- ` `
- `t`
- `e`
- `s`
- `t`
- `s`
- `/`
- `t`
- `e`
- `s`
- `t`
- `_`
- `p`
- `a`
- `p`
- `e`
- `r`
- `_`
- `s`
- `e`
- `c`
- `t`
- `i`
- `o`
- `n`
- `_`
- `c`
- `o`
- `n`
- `t`
- `r`
- `a`
- `c`
- `t`
- `.`
- `p`
- `y`
