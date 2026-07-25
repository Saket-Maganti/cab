# Prompt 10 — Post-Run Audit, Scorer Sanity, Evidence Classification

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a strict post-run auditor, scorer sanity reviewer, and evidence classifier.

## Task

Audit the completed 3-model Compact-20 live run and determine what evidence it can and cannot support.

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

- live run directory
- config used and config hash
- run metadata
- trajectory outputs
- scorer outputs
- cost/runtime logs
- error/incomplete markers
- claim ledger
- C10 validation status

## Actions

1. Create `reports/COMPACT20_3MODEL_POSTRUN_AUDIT.md`.
2. Create `reports/COMPACT20_3MODEL_TRAJECTORY_REVIEW.csv`.
3. Create `reports/SCORER_SANITY_COMPACT20_3MODEL.md` and `.csv`.
4. Create `reports/COMPACT20_3MODEL_EVIDENCE_CLASSIFICATION.md`.
5. Review every trajectory for scorer/gold/model-output issues.
6. Classify evidence as preliminary/paper-candidate/paper-eligible according to repo policy.
7. Update claim ledger only if evidence gates pass.

## Deliverables

- post-run audit
- trajectory review CSV
- scorer sanity report and CSV
- evidence classification report

## Tests / Checks

- incomplete run cannot support claims
- scorer sanity required
- manual review pending blocks strong claims
- C10 required for isolation claims
- evidence safety passes

## Allowed Commands

['POSTRUN_AUDIT_PASS_PRELIMINARY_EVIDENCE', 'POSTRUN_AUDIT_FAILED_INCOMPLETE_RUN', 'POSTRUN_AUDIT_BLOCKED_SCORER_SANITY', 'POSTRUN_AUDIT_BLOCKED_MANUAL_REVIEW']

## Final Response Format

# Prompt 10 — Post-Run Audit, Scorer Sanity, Evidence Classification Report

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
- `a`
- `l`
- `l`
- `-`
- `n`
- `o`
- `-`
- `r`
- `u`
- `n`
- `-`
- `r`
- `e`
- `p`
- `o`
- `r`
- `t`
- `s`
- ` `
- `-`
- `-`
- `o`
- `u`
- `t`
- `p`
- `u`
- `t`
- `-`
- `d`
- `i`
- `r`
- ` `
- `/`
- `t`
- `m`
- `p`
- `/`
- `c`
- `a`
- `b`
- `_`
- `p`
- `o`
- `s`
- `t`
- `_`
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
