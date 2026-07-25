# Prompt 14 — Baseline Agent and Ablation Upgrades

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as an ML systems engineer and experimental-design lead.

## Task

Upgrade baseline agent templates and ablation hooks so CAB can test whether simple scaffolds improve robustness. Do not execute models.

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

- existing agent interfaces
- mock/stub agents
- config schema
- runner metadata
- analysis grouping code

## Actions

1. Add config templates for direct-answer, ReAct tool, function-calling, self-check, recovery-aware, abstention-aware, and oracle/stub engineering baseline.
2. Create `experiments/ABLATION_DESIGN_FOR_CAB.md`.
3. Create `reports/BASELINE_AGENT_UPGRADE_REPORT.md`.
4. Ensure templates are non-runnable without approval, no secrets, claims false, paper eligibility false.
5. Ensure ablation labels propagate to future run metadata and analysis grouping.

## Deliverables

- agent template configs
- ablation design doc
- baseline upgrade report
- fixture tests

## Tests / Checks

- templates load
- no secrets
- mock/stub engineering-only
- ablation labels preserved
- no run execution

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 14 — Baseline Agent and Ablation Upgrades Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `ABLATION_INFRA_READY_NO_EXECUTION`
- `ABLATION_INFRA_BLOCKED`
