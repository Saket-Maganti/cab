# Intervention Taxonomy

This document describes the machine-readable intervention taxonomy in
`configs/intervention_taxonomy.yaml`.

The taxonomy is a no-run validation asset. It supports static isolation audits,
gold-answer policy checks, and advisor review. It does not support empirical
performance claims and must not be used to mark C1-C8 or C10 as supported.

## Fields

Each intervention type defines:

- `intervention_type`: stable intervention family name.
- `description`: short method description.
- `intended_causal_factor`: the single factor the intervention is meant to vary.
- `allowed_changed_fields`: fields that may differ from the clean instance.
- `expected_unchanged_fields`: fields expected to remain invariant.
- `answer_preservation`: `answer_preserving`, `answer_changing`, or `depends`.
- `requires_human_review`: whether static review is insufficient on its own.
- `examples`: non-binding examples for reviewers.
- `risks`: known isolation and leakage risks.
- `severity_if_violated`: default severity when invariants are violated.

## Current Policy

The current taxonomy is pre-provider-pilot. Unknown intervention types are
`needs_review`. Expected-unchanged field changes are warnings or blockers. An
answer-preserving intervention must not change the gold answer unless the
taxonomy is updated and a rationale is documented.

## Use In The Audit

Run:

```bash
python3 -m causal_agent_bench intervention-isolation-audit --taxonomy configs/intervention_taxonomy.yaml --output-dir reports/intervention_isolation
```

If the taxonomy is missing, the audit falls back to built-in conservative
defaults and records that fallback in the report.

## Evidence Boundary

This taxonomy can support method claims about how interventions are specified
and statically checked. It cannot support empirical claims, provider results,
human-validation claims, or leaderboard claims.
