# Git Repo Hygiene Checkpoint

Generated for: first 3-model Compact-20 no-execution planning pass

## Snapshot

| Field | Value |
|---|---:|
| Current branch | `main` |
| Commit count | `1` |
| Tracked file count | `187` |
| Untracked file count | `910` |
| Dirty porcelain entries | `589` |

## Commit Safety

The repo is **not safe for one broad commit**. The worktree is very dirty, with many pre-existing modified files, deleted old paper files, generated figures/tables, untracked docs, untracked source modules, untracked tests, untracked data, and untracked reports.

It is safe only for a scoped commit after manually staging the exact files intended for that commit.

## Recommended Commit Grouping

1. First 3-model Compact-20 no-execution planning artifacts:
   - `experiments/FIRST_PAPER_ELIGIBLE_3MODEL_COMPACT20_PLAN.md`
   - `experiments/FIRST_3MODEL_PILOT_EXECUTION_CHECKLIST_NO_RUN.md`
   - `configs/compact20_3model_TEMPLATE_NOT_APPROVED.yaml`
   - `configs/compact20_3model_LOCAL_TEMPLATE_NOT_APPROVED.yaml`
   - `paper/FIRST_3MODEL_PILOT_RESULT_TABLE_SCHEMAS.md`
   - `paper/FIRST_MONEY_PLOT_SPEC.md`
   - `docs/LOCAL_MODEL_EVIDENCE_BOUNDARY.md`
   - `tests/test_first_3model_pilot_no_run.py`
2. Repo hygiene checkpoint:
   - `reports/GIT_REPO_HYGIENE_CHECKPOINT.md`
3. Keep unrelated broad build artifacts, old paper deletion/move state, generated figures/tables, and data/results changes out of this commit unless explicitly reviewed.

## Files Or Categories That Should Not Be Committed Without Separate Review

- `.env` or any local secret file.
- API/provider key material in any form.
- `.DS_Store`, cache folders, and local editor state.
- Raw provider responses, raw trajectory dumps, and temporary dry-run outputs unless intentionally included as sanitized artifacts.
- Large generated result folders under `results/`.
- Local/Ollama interrupted run artifacts unless a release policy explicitly includes them with preliminary labels.
- Broad untracked data trees or regenerated paper PDFs without a release decision.

## Warning

This checkout has a very dirty worktree. Do not use `git add .`. Stage only reviewed files by path.
