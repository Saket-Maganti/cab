# C10 Intervention-Isolation Validation Protocol

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## What C10 Means

C10 is the claim that controlled interventions isolate intended skill components. It is currently planned/unsupported. Static taxonomy checks help prepare the claim, but they do not validate it.

## Reviewer Judgments

Human reviewers judge whether each intervention:

- preserves the user's goal,
- changes the intended target factor,
- leaves non-target factors unchanged,
- has a clear expected-answer policy,
- should be included, revised, or excluded.

## Isolation Criteria

An intervention passes isolation review only when the target factor is identifiable, the clean and intervention task remain paired, and no unplanned change alters the success criterion.

## Goal-Preservation Criteria

The user goal should remain recognizable across clean and intervention variants. If the intervention changes the user's requested outcome, it must be documented as answer-changing or excluded.

## Changed-Factor Criteria

The changed factor must match the family definition, such as tool availability for `tool_removal`, tool reliability for `tool_failure`, memory correctness for `memory_corruption`, or conflicting evidence for `observation_conflict`.

## Answer-Policy Criteria

Reviewers must record whether the gold answer should stay the same, change, become an abstention, allow multiple answers, or be marked cannot-determine.

## Exclusion Criteria

Exclude a row when the intervention changes multiple factors, makes the task unverifiable, lacks a clear gold policy, duplicates another row, or cannot be reviewed from available metadata.

## Agreement Metrics To Compute Later

Compute agreement only after at least two independent completed reviewers exist. Planned metrics include raw agreement, Cohen kappa where labels permit, family-level disagreement rate, and adjudicated pass/fail rate.

## Pass/Fail Thresholds

For a compact pilot, require high raw agreement on include/exclude and no unresolved high-severity disagreements in selected rows. Exact thresholds must be preregistered before claiming C10 support.

## Evidence Levels

| Evidence level | Allowed claim |
|---|---|
| Static taxonomy only | Interventions are specified by intended factor. |
| One reviewer | Review is in progress; no agreement claim. |
| Two reviewers plus adjudication | Compact-slice intervention isolation may be described if thresholds pass. |
| Larger validated sample | C10 may be considered for claim-ledger promotion after evidence safety checks. |

