# Prompt 16 — Naturalistic Transfer Mini-Study

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a benchmark validity researcher.

## Task

Design a small naturalistic transfer mini-study to test whether CAB intervention findings transfer beyond template/simulated tasks.

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

- existing task families
- license/source policies
- current benchmark schema
- related work risks
- Compact-20 findings if present

## Actions

1. Create `experiments/NATURALISTIC_TRANSFER_MINISTUDY_DESIGN.md`.
2. Create `data/naturalistic_ministudy/README.md`, `task_template.json`, and `license_and_source_log.md`.
3. Create `configs/naturalistic_ministudy_TEMPLATE_NOT_APPROVED.yaml`.
4. Create `reports/NATURALISTIC_MINISTUDY_READINESS.md`.
5. Design 10-30 realistic tasks mapped to CAB intervention families.
6. Do not scrape, copy private data, or fabricate tasks beyond clearly authored toy scenarios.

## Deliverables

- design doc
- data scaffold
- source/license log
- non-runnable config template
- readiness report

## Tests / Checks

- source/license log required
- no private data
- no fake model outputs
- template non-runnable
- claims false

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 16 — Naturalistic Transfer Mini-Study Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `NATURALISTIC_MINISTUDY_DESIGNED_NO_EXECUTION`
- `NATURALISTIC_MINISTUDY_BLOCKED_SOURCE_POLICY`
