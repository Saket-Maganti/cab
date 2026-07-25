# Paper Wording Guardrails

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## Before Provider Results

Allowed:

- "we introduce"
- "we design"
- "we plan to test"
- "controlled perturbation"
- "ranking-instability hypothesis"

Forbidden:

- "we demonstrate"
- "we find"
- "validated benchmark"
- "model rankings"
- "causal proof"
- "NeurIPS ready"

## After Tiny Provider Pilot

Allowed only if the run exists and post-run audit passes:

- "provider integration sanity"
- "scorer debugging evidence"
- "preliminary pipeline check"

Still forbidden:

- C1-C8/C10 support
- final leaderboard claims
- paper-eligible assets

## After Compact-20/50

Allowed only with audits and intervals:

- "preliminary compact evidence"
- "in this compact sample"
- "observed rank instability under these conditions"

## After Human Validation

Allowed only after two-reviewer completion and adjudication:

- "reviewers agreed on selected intervention-isolation cases"
- "C10 is supported for the reviewed slice"

## After Full Submission Gate

Only after all gates pass may the paper use submission-strength empirical language. Until then, gate status must remain visible.

