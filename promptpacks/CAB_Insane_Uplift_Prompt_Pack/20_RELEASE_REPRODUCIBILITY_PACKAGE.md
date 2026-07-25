# Prompt 20 — Release and Reproducibility Package

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as an artifact evaluation engineer and reproducibility lead.

## Task

Prepare the release package needed for NeurIPS D&B / DMLR style review.

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

- install docs
- configs
- run scripts
- result artifacts
- data provenance
- license files
- secret-risk files
- tests

## Actions

1. Create/update `REPRODUCIBILITY.md`, `ARTIFACT_EVALUATION_CHECKLIST.md`, `DATA_CARD_CAB.md`, `MODEL_CARD_EVALUATION_SUBJECTS.md`.
2. Create/update `docs/INSTALL_AND_RUN.md`, `docs/REPRODUCE_COMPACT20_RESULTS.md`, `docs/REPRODUCE_MAIN_RESULTS.md`.
3. Create `release/MANIFEST.json`, `release/README.md`, `release/EXCLUDED_FILES.md`.
4. Create `reports/RELEASE_READINESS_AUDIT.md`.
5. Include dependency setup, no-provider smoke tests, config validation, table reproduction from existing outputs, provider-run safety, hashes, licenses, limitations.

## Deliverables

- reproducibility docs
- data/model cards
- release manifest
- release readiness audit

## Tests / Checks

- no secrets in release
- release manifest paths exist
- reproduction avoids live providers by default
- no stub tables claimed as final results

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 20 — Release and Reproducibility Package Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `RELEASE_PACKAGE_READY_PRELIMINARY`
- `RELEASE_BLOCKED_NO_REAL_RESULTS`
- `RELEASE_BLOCKED_SECRET_OR_LICENSE_RISK`
