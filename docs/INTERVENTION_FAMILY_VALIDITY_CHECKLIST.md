# Intervention Family Validity Checklist

Use this checklist before adding a task pair to Compact-20, Compact-100, or Main-500. Do not mark any row human-reviewed unless a real human completed the review.

## Required Checks

- Family is documented in `docs/INTERVENTION_TAXONOMY_V2.md`.
- Intended factor changed is a single factor.
- User goal is preserved.
- Hidden ground truth is unchanged unless the family explicitly allows answer change.
- Gold policy states whether final answer should change.
- Required evidence remains available or abstention is explicitly valid.
- Success criteria are machine-checkable or marked for human scoring.
- Scorer risk is identified.
- C10 reviewer questions are defined.
- Exclusion criteria are applied before execution.

## Review Outcomes

- `valid_for_execution`: static checks pass; still not evidence.
- `needs_human_review`: unclear but possibly usable.
- `exclude_before_run`: confounded or scorer-fragile.
- `replacement_candidate`: candidate may be swapped into a future sample after review.

## Hard Exclusions

- Multiple target factors change.
- User goal changes.
- Proxy review is copied into human-review fields.
- Gold answer changes without policy.
- Scorer can pass by substring artifact alone.
- Task requires private data, scraping, or external state not bundled in the artifact.
