# No-API Task Review Packet

Status labels:

- `engineering_only`
- `no_provider_evidence`
- `not_scientific_model_performance`

## Purpose

This packet lets humans review task and intervention quality while the live provider pilot is blocked. It requires no model outputs and produces no provider-backed evidence.

Reviewers may assess:

- task clarity,
- intervention isolation,
- gold-answer policy,
- whether abstention is acceptable,
- whether a sample should be excluded.

## Files

- `task_review_template.csv`: task/intervention clarity and isolation review.
- `gold_policy_review_template.csv`: gold-answer and abstention-policy review.

## Evidence Boundary

This packet can improve benchmark-design readiness. It cannot support:

- C1-C8 final claims,
- C3 trajectory claims,
- C10,
- model-performance claims,
- provider-backed evidence,
- human-validation agreement metrics,
- NeurIPS readiness.

C10 must remain pending until completed human review and adjudication artifacts exist.

## Suggested Workflow

1. Select only candidate compact items from reviewed no-run reports.
2. Fill `task_review_template.csv` for task clarity and intervention isolation.
3. Fill `gold_policy_review_template.csv` for expected-answer policy.
4. Exclude rows marked ambiguous, multi-factor, or unresolved.
5. Do not patch frozen data from these templates alone.
6. Do not report annotation counts or agreement metrics from empty templates.

## Reviewer Rules

- Do not infer model behavior.
- Do not fabricate model outputs.
- Do not mark human validation complete.
- Do not mark paper assets eligible.
- Do not promote claims.
