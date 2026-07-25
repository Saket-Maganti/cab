# Prompt 03 — C10 Validation and Slice Lock

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a construct-validity auditor for intervention isolation.

## Task

Validate C10 for the locked Compact-20 slice using real human reviews. Then lock the slice for the first provider pilot.

## Absolute rules

- Do not fabricate validation.
- Do not treat proxy review as human.
- Do not call providers.
- Do not run local LLMs.
- Do not run benchmark execution.
- Do not promote C10 beyond `preliminary_supported_compact20_only`.
- Do not promote C1-C8.

## Preconditions

Proceed only if:

- `data/compact20_locked/compact20_locked_manifest.json` exists,
- the locked slice contains human-reviewed tasks,
- human review rows are real.

## Analysis

Compute:

- task clarity pass rate,
- gold correctness pass rate,
- goal preservation pass rate,
- intervention isolation pass rate,
- per-family pass rates,
- reviewer disagreement rate,
- adjudication status,
- excluded-task count.

## Thresholds

Suggested minimum:

- task clarity pass rate >= 0.80,
- gold correctness pass rate >= 0.80,
- goal preservation pass rate >= 0.80,
- intervention isolation pass rate >= 0.80,
- no unresolved severe blockers.

## Create/update

- `reports/C10_INTERVENTION_ISOLATION_VALIDATION.md`
- `reports/C10_INTERVENTION_ISOLATION_VALIDATION.csv`
- `data/compact20_locked/compact20_c10_validated_manifest.json`
- `reports/COMPACT20_SLICE_LOCK_REPORT.md`

## Claim impact

Allowed:

- C10 may become `preliminary_supported_compact20_only` if thresholds pass.

Forbidden:

- full C10 support,
- C1-C8 support,
- model-performance claims,
- NeurIPS-readiness claims.

## Tests/checks

- evidence safety passes,
- C10 cannot pass with proxy rows,
- C10 cannot pass without threshold,
- C1-C8 remain unsupported.

## Final response format

# C10 Validation and Slice Lock Report

## 1. Executive Summary
## 2. Locked Slice Identity
## 3. Human Review Coverage
## 4. C10 Metrics
## 5. Per-Family Validity
## 6. Exclusions/Repairs
## 7. Claim Ledger Impact
## 8. Tests Run
## 9. Commands Not Run
## 10. Next Best Action

Final verdict:

- `C10_PRELIMINARY_SUPPORTED_COMPACT20_ONLY`
- `C10_BLOCKED_MISSING_LOCKED_SLICE`
- `C10_FAILED_THRESHOLD`
- `C10_NEEDS_ADJUDICATION`
