# Prompt 09 — Scorer Sanity and Gold Policy Repair

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a scorer auditor and gold-policy repair engineer.

## Task

Use completed manual trajectory review to audit scorer reliability and repair scorer/gold issues without rerunning models.

## Absolute rules

- Do not fabricate manual judgments.
- Do not rerun providers/local LLMs.
- Do not change raw model outputs.
- Do not quietly change gold answers without report.
- Do not promote claims if scorer sanity fails.

## Preconditions

Proceed only if manual trajectory review is complete.

## Actions

1. Compare deterministic scorer result with manual judgment.
2. Compute scorer agreement, false positives, false negatives, issue rates by model/task/family, and severe gold-policy issue count.
3. If gold/scorer repairs are needed, patch scorer/gold policy if safe and re-score existing outputs only if repo supports offline re-score with no model/provider calls.
4. Create:

- `reports/SCORER_SANITY_COMPACT20_3MODEL.md`
- `reports/SCORER_SANITY_COMPACT20_3MODEL.csv`
- `reports/GOLD_POLICY_REPAIR_AFTER_LIVE_RUN.md`
- `analysis/compact20_3model/rescored_outputs.csv` if offline re-score is run.

## Tests/checks

- offline scorer tests,
- no provider calls,
- no raw output mutation,
- evidence safety pass.

## Final response format

# Scorer Sanity and Gold Policy Repair Report

## 1. Executive Summary
## 2. Manual Review Coverage
## 3. Scorer Agreement
## 4. False Positives/Negatives
## 5. Gold Policy Issues
## 6. Repairs Made
## 7. Offline Re-Score
## 8. Claim Impact
## 9. Tests Run
## 10. Next Best Action

Final verdict:

- `SCORER_SANITY_PASS_READY_FOR_ANALYSIS`
- `SCORER_SANITY_REPAIRED_READY_FOR_ANALYSIS`
- `SCORER_SANITY_FAILED_BLOCK_CLAIMS`
- `SCORER_SANITY_BLOCKED_NO_MANUAL_REVIEW`
