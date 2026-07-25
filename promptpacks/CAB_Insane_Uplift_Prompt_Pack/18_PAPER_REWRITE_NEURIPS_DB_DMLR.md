# Prompt 18 — Paper Rewrite for NeurIPS D&B / DMLR

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a senior ML paper writer and ruthless reviewer.

## Task

Rewrite the paper around the actual evidence state. If only Compact-20 exists, write a pilot-paper draft. If larger study exists, write the benchmark paper. Do not invent results.

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

- paper skeleton/source
- real result tables/figures
- claim ledger
- evidence safety reports
- related work
- limitations
- release docs

## Actions

1. Create `paper/PAPER_NARRATIVE_PLAN.md`.
2. Update paper sections: intro, benchmark, experiments, results, limitations, ethics, reproducibility.
3. Create `paper/PAPER_CLAIM_TO_EVIDENCE_MAP.md`.
4. Frame as controlled perturbation / paired intervention evaluation, not strong causal inference unless validated.
5. Use real results only.
6. Use pilot-only language if only Compact-20 exists.
7. Ensure abstract and results are empty/blocked if no real evidence exists.

## Deliverables

- rewritten paper sections
- narrative plan
- claim-to-evidence map

## Tests / Checks

- paper section contract passes
- no stub results
- no unsupported causal overclaim
- all result sentences map to artifacts

## Allowed Commands

['PAPER_DRAFT_READY_WITH_REAL_EVIDENCE', 'PAPER_DRAFT_BLOCKED_NO_REAL_RESULTS', 'PAPER_DRAFT_PILOT_ONLY']

## Final Response Format

# Prompt 18 — Paper Rewrite for NeurIPS D&B / DMLR Report

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
- `d`
- `f`
- `l`
- `a`
- `t`
- `e`
- `x`
- ` `
- `o`
- `n`
- `l`
- `y`
- ` `
- `i`
- `f`
- ` `
- `r`
- `e`
- `p`
- `o`
- ` `
- `a`
- `l`
- `r`
- `e`
- `a`
- `d`
- `y`
- ` `
- `s`
- `u`
- `p`
- `p`
- `o`
- `r`
- `t`
- `s`
- ` `
- `s`
- `a`
- `f`
- `e`
- ` `
- `p`
- `a`
- `p`
- `e`
- `r`
- ` `
- `c`
- `o`
- `m`
- `p`
- `i`
- `l`
- `a`
- `t`
- `i`
- `o`
- `n`
