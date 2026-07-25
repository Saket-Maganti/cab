# Compact-20 Selection Criteria

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## Goal

Compact-20 is a future manual-review and provider-execution slice. It is not a benchmark result and must not be used as a paper asset until provider outputs, audits, and claim gates exist.

## Required Composition

- 20 paired items if available.
- Each row must reference a clean instance and an intervention instance.
- Cover at least these families: `tool_removal`, `tool_failure`, `memory_corruption`, `observation_conflict`.
- Prefer domain and difficulty diversity.
- Include a controlled number of high-risk or answer-policy-sensitive rows for review.
- Avoid duplicate or near-duplicate tasks.
- Prefer rows with inspectable expected-answer policy.
- Every candidate must be labeled `no_run_manual_review_pending`.

## Exclusion Rules

Exclude rows with unresolved instruction ambiguity, non-isolated interventions, unclear gold policy, or duplicate task structure. Frozen-data concerns are documented, not patched, in this phase.

