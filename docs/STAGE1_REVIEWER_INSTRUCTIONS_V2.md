# Stage-1 reviewer instructions (V2)

This is the tracked copy of the instructions shipped inside each Stage-1
package as `REVIEWER_INSTRUCTIONS.md`. Reviewers should work from the copy in
their own package.

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

`notes` is required whenever `exclude_item=yes` or
`ambiguity_present=material`.

## Rules

- Work alone. Do not discuss any item with the other reviewer or anyone else.
- Do not use any AI assistant or language model for any part of this review.
- Declare any conflict of interest before you begin; authors and co-authors
  cannot review.
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
