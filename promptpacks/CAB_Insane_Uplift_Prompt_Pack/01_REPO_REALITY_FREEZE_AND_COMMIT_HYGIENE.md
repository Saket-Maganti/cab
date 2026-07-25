# Prompt 01 — Repo Reality Freeze and Commit Hygiene

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a senior research engineer, repo hygienist, and evidence-safety auditor.

## Task

Freeze the current repo reality, identify commit groups, clean obvious transient clutter, and make the repository safe for serious experiment work. Do not commit automatically.

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

- `git status --short --branch`
- `git log --oneline --decorate -n 10`
- `git diff --stat`
- `MASTER_STATUS.json`
- `PROJECT_STATUS.md`
- `results/`, `runs/`, `tables/`
- `.gitignore`
- evidence-safety scripts

## Actions

1. Create `reports/REPO_REALITY_FREEZE.md` with branch, commit count, dirty file counts, untracked count, generated/stub artifact summary, and evidence state.
2. Create `reports/COMMIT_GROUPING_PLAN.md` with staged commit groups: source, configs, tests, evidence governance, paper/docs, data review packets, generated reports.
3. Update `.gitignore` only for obvious transient files such as `.DS_Store`, `__pycache__/`, `.pytest_cache/`, `.env`, temp runs, local secret files.
4. Identify files that should not be committed.
5. Confirm no secrets and no `allow_paid_calls=true` are present in intended commit files.

## Deliverables

- `reports/REPO_REALITY_FREEZE.md`
- `reports/COMMIT_GROUPING_PLAN.md`
- optional `.gitignore` cleanup

## Tests / Checks

- Evidence safety still blocks C1-C8/C10.
- No API keys in changed files.
- No stub table is paper-eligible.
- Worktree is summarized honestly.

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 01 — Repo Reality Freeze and Commit Hygiene Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `REPO_FREEZE_READY`
- `REPO_FREEZE_BLOCKED`
- `DIRTY_TREE_NEEDS_MANUAL_TRIAGE`
