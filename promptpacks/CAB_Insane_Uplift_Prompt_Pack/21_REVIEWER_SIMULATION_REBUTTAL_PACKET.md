# Prompt 21 — Reviewer Simulation and Rebuttal Packet

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as three NeurIPS/DMLR reviewers and a rebuttal strategist.

## Task

Simulate reviews based only on actual repo/paper/evidence state, then create a rebuttal/preemption packet.

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

- paper draft
- result tables
- figures
- claim/evidence map
- related work matrix
- C10 validation
- scorer sanity
- release package
- limitations

## Actions

1. Create `reviews/SIMULATED_REVIEW_R1_SUPPORTIVE.md`.
2. Create `reviews/SIMULATED_REVIEW_R2_SKEPTICAL.md`.
3. Create `reviews/SIMULATED_REVIEW_R3_DOMAIN_EXPERT.md`.
4. Create `reviews/REBUTTAL_PREEMPTION_MATRIX.md`.
5. Create `reports/REVIEWER_SIMULATION_SUMMARY.md`.
6. Review risks: no/weak evidence, synthetic validity, causal overclaim, ACRS triviality, overlap, scorer validity, human validation, reproducibility, provider bias, repo overbuild.

## Deliverables

- 3 simulated reviews
- rebuttal preemption matrix
- reviewer simulation summary

## Tests / Checks

- no flattery
- no fabricated strengths
- scores realistic
- limitations not hidden

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 21 — Reviewer Simulation and Rebuttal Packet Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `REVIEW_RISK_ACCEPTABLE_FOR_SUBMISSION`
- `REVIEW_RISK_TOO_HIGH_NEEDS_MORE_EVIDENCE`
- `REVIEW_RISK_BLOCKED_NO_REAL_RESULTS`
