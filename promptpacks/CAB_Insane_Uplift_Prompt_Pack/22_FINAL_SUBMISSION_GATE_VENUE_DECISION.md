# Prompt 22 — Final Submission Gate and Venue Decision

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a final submission gatekeeper, area-chair simulator, and venue strategist.

## Task

Decide whether CAB is ready for submission, and to which venue tier, based only on real artifacts.

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

- `MASTER_STATUS.json`
- `PROJECT_STATUS.md`
- claim ledger
- paper PDF/source
- result tables/figures
- post-run audits
- scorer sanity
- C10 validation
- release package
- related work matrix
- simulated reviews
- test status
- git hygiene report

## Actions

1. Create `reports/FINAL_SUBMISSION_GATE.md`.
2. Create `reports/VENUE_DECISION_MATRIX.md`.
3. Create `paper/SUBMISSION_READINESS_CHECKLIST.md`.
4. Evaluate evidence, paper, artifact, claim support, reviewer risk, and venue fit.
5. Classify as NeurIPS D&B ready, DMLR ready, workshop only, or not submittable.
6. Give submit/do-not-submit recommendation.

## Deliverables

- final submission gate
- venue decision matrix
- submission readiness checklist

## Tests / Checks

- provider-backed runs exist if any scientific claim is made
- paper has real results
- release has no secrets
- claims supported
- no unsupported causal overclaim

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 22 — Final Submission Gate and Venue Decision Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `SUBMIT_NEURIPS_DB`
- `SUBMIT_DMLR`
- `SUBMIT_WORKSHOP_ONLY`
- `DO_NOT_SUBMIT_NEEDS_MORE_EVIDENCE`
- `DO_NOT_SUBMIT_SCAFFOLD_ONLY`
