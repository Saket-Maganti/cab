# Stage-1 reviewer instructions (V2)

This is the tracked copy of the instructions shipped inside each Stage-1
package as `REVIEWER_INSTRUCTIONS.md`. Reviewers should work from the copy in
their own package.

```text
No genuine review has occurred.
C10 has not passed.
Model execution is blocked.
```

## What you are judging

Each item shows the same user goal twice: a *clean* instance and an
*intervention* instance produced by changing exactly one declared factor. You
are judging whether that is a scientifically valid controlled comparison.

You are **not** judging whether a model would answer correctly, and you are not
asked what the right answer is. You will not be shown the expected result, the
expected response type, the grading rules, or any material held back for the
second review stage.

## Dimensions

One row per item, one value per column:

| Column | Values |
|---|---|
| `task_clarity` | 1-5 |
| `clean_goal_clear` | yes / no |
| `clean_evidence_sufficient` | yes / no |
| `clean_solvable` | yes / no |
| `intervention_understandable` | yes / no |
| `intended_factor_identifiable` | yes / no |
| `goal_preserved` | yes / no |
| `single_factor_isolation` | yes / no |
| `preserved_invariants_hold` | yes / no / partial |
| `primitive_evidence_adequate` | yes / no |
| `declared_tools_adequate` | yes / no |
| `intervention_realistic` | 1-5 |
| `ambiguity_present` | none / minor / material |
| `response_space_structurally_valid` | yes / no / unsure |
| `exclude_item` | yes / no |
| `reviewer_confidence` | 1-5 |
| `notes` | free text |

`notes` is required whenever `exclude_item=yes`,
`ambiguity_present=material`, or `response_space_structurally_valid=unsure`.

Filling every cell does not approve anything. Any gating dimension that does not
land on an accepting value — and any `unsure`, `material` ambiguity, or
confidence below 3 — sends that item to an independent adjudicator. That is the
correct outcome, and it does not count against you.

## Rules

- Work alone. Do not discuss any item with the other reviewer or anyone else.
- Do not use any AI assistant or language model for any part of this review.
- Complete `reviewer_declaration.json` and return it with your qualification
  answers. Every `*_confirmed` field must be a literal `true` written by you;
  the coordinator cannot fill in any of it on your behalf, and a missing
  confirmation stops the process rather than defaulting to anything.
- Declare any conflict of interest before you begin. Disclosing one does not
  automatically disqualify you; it routes the decision to the coordinator.
  Concealing one invalidates the review.
- Do not copy, publish, post, or upload any part of the package.
- Expect roughly 8-12 minutes per item.
- To correct a submitted row, send a complete corrected form and say it
  supersedes the previous one. The coordinator records only the latest validated
  submission, and every submission is hash-bound.
- If a file is missing, an item will not open, or an item makes no sense, stop
  and contact the coordinator with the `reviewer_item_id`. A malformed package
  is our defect, not your judgement call.

## Access tiers

Some declared tools are marked `restricted`. That means the capability is not
part of the default repertoire and requires an explicit grant. It does not tell
you anything about the expected response, and you should not infer one.

## Qualification

Before you are assigned a review package you complete a short calibration set.
It is generated specifically for you: your items are not the other reviewer's
items, and neither set exists anywhere in the public repository. Qualification
uses separate tasks, records, identifiers and item content from the final review
set.

Complete every requested field. Qualification scoring uses hidden predefined
criteria and may weigh selected dimensions; you are not told which ones, so
answer every column on its own merits rather than guessing at what is graded. A
row that leaves a requested field blank is rejected before it is scored. The
threshold is 80%.

## A second stage exists

If your Stage-1 submission is accepted you may later be asked to review the
withheld material — expected results, accepted variants, answer contracts,
scorer contracts and route policies. That stage uses `YES` / `NO` / `UNSURE` /
`NOT_APPLICABLE`, and `NO` and `UNSURE` are substantive answers that require a
note. Nothing about Stage 2 is visible to you now, and seeing it would end the
blindness of your Stage-1 judgements.
