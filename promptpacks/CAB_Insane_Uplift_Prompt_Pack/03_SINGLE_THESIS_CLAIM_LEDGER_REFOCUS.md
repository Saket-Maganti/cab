# Prompt 03 — Single-Thesis Claim Ledger Refocus

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a NeurIPS D&B area-chair-minded claim-governance auditor.

## Task

Refocus CAB around one falsifiable thesis and rebuild the claim architecture so the project stops looking like ten unsupported papers at once.

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

- claim ledger files
- `docs/CLAIM_TRIAGE_NO_RUN.md`
- `MASTER_STATUS.json`
- `PROJECT_STATUS.md`
- paper skeleton and generated tables
- `scripts/check_evidence_safety.py`
- claim-status tests

## Actions

1. Create `docs/CLAIM_ARCHITECTURE.md`.
2. Define primary thesis: success-only rankings can misrepresent agent capability because controlled perturbations reveal brittleness and ranking instability.
3. Map C1-C8/C10 to evidence requirements and keep them unsupported until real evidence exists.
4. Keep C9 as `engineering_only` if supported by tests.
5. Create `reports/CLAIM_LEDGER_REFOCUS_REPORT.md`.
6. Add/update tests that reject claim support from stub/mock/dry-run evidence.

## Deliverables

- `docs/CLAIM_ARCHITECTURE.md`
- `reports/CLAIM_LEDGER_REFOCUS_REPORT.md`
- targeted claim/evidence tests

## Tests / Checks

- C1-C8/C10 remain unsupported.
- C9 remains engineering-only.
- No paper section says results are proven.
- Evidence safety passes.

## Allowed Commands

['CLAIM_ARCHITECTURE_READY', 'CLAIM_ARCHITECTURE_BLOCKED']

## Final Response Format

# Prompt 03 — Single-Thesis Claim Ledger Refocus Report

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
- `c`
- `l`
- `a`
- `i`
- `m`
- `*`
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
- `s`
- `a`
- `f`
- `e`
- `t`
- `y`
- `*`
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
