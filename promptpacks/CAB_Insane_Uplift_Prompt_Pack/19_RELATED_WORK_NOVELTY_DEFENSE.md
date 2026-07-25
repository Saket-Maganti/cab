# Prompt 19 — Related Work and Novelty Defense

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as an ML literature strategist and skeptical reviewer.

## Task

Strengthen CAB’s related work and novelty positioning against existing agent benchmarks and robustness benchmarks.

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

- existing related work
- paper sections
- novelty docs
- benchmark comparison notes
- citation TODOs

## Actions

1. Search/inspect primary sources if web access is available: tau-bench, AgentDojo, AgentBench, AgentBoard, ToolBench, WebArena, OSWorld, SWE-bench, HELM-style evaluation, robustness benchmarks.
2. Create `paper/RELATED_WORK_MATRIX.md`.
3. Update related work section.
4. Create `docs/NOVELTY_BOUNDARY_AND_REVIEWER_DEFENSE.md`.
5. Create `reports/RELATED_WORK_AUDIT.md`.
6. Keep novelty modest: paired clean/intervention design + intervention taxonomy + ACRS + intervention-isolation validation for tool-using agents.

## Deliverables

- related work matrix
- novelty defense doc
- related work audit
- updated paper section

## Tests / Checks

- no fabricated citations
- no “first benchmark” overclaim
- all citations backed by sources
- overlap risks clearly stated

## Allowed Commands

['RELATED_WORK_DEFENSE_READY', 'RELATED_WORK_BLOCKED_MISSING_SOURCES']

## Final Response Format

# Prompt 19 — Related Work and Novelty Defense Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `U`
- `s`
- `e`
- ` `
- `w`
- `e`
- `b`
- `/`
- `l`
- `i`
- `t`
- `e`
- `r`
- `a`
- `t`
- `u`
- `r`
- `e`
- ` `
- `s`
- `e`
- `a`
- `r`
- `c`
- `h`
- ` `
- `o`
- `n`
- `l`
- `y`
- ` `
- `i`
- `f`
- ` `
- `a`
- `v`
- `a`
- `i`
- `l`
- `a`
- `b`
- `l`
- `e`
- `.`
- ` `
- `P`
- `r`
- `e`
- `f`
- `e`
- `r`
- ` `
- `p`
- `r`
- `i`
- `m`
- `a`
- `r`
- `y`
- ` `
- `s`
- `o`
- `u`
- `r`
- `c`
- `e`
- `s`
- `.`
- ` `
- `D`
- `o`
- ` `
- `n`
- `o`
- `t`
- ` `
- `r`
- `u`
- `n`
- ` `
- `e`
- `x`
- `p`
- `e`
- `r`
- `i`
- `m`
- `e`
- `n`
- `t`
- `s`
- `.`
