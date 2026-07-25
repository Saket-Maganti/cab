# AI Proxy Review Evidence Boundary

Status: `ai_proxy_test_only`

## Current Evidence Classification

- Provider-backed evidence remains `0`.
- Real human annotations remain `0`.
- Eligible paper assets remain `0`.
- C1-C8/C10 remain unsupported.

## What The Proxy Review Is

The AI proxy review is a synthetic review fixture for downstream analysis pipeline testing. It is labeled `ai_proxy_review`, `synthetic_review_for_pipeline_testing`, and `not_human_annotation`.

## What The Proxy Review Is Not

It is not human validation, not C10 evidence, not model-performance evidence, not provider evidence, and not paper-eligible.

## Required Before Paper Use

Before any paper use, a real human must fill the original CSVs:

- `data/human_validation/no_api_task_review/compact20_task_review.csv`
- `data/human_validation/no_api_task_review/compact20_gold_policy_review.csv`

The proxy copies must not be counted as annotations, agreement inputs, C10 support, provider evidence, or eligible paper assets.
