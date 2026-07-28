# Reviewer Qualification Examples

Status: `DESIGN_ONLY`. These are worked examples, not reviewer identities,
responses, human rows, or C10 evidence.

Reviewers must complete an independently administered calibration derived from
these patterns and achieve at least 80%. The coordinator records only the
privacy-safe reviewer ID and aggregate score in `reviewer_registry.csv`.

## Example 1 — valid tool removal

A required search tool appears in the clean condition and is absent in the
intervention condition. The user goal and gold policy are unchanged, while an
alternate route remains available.

- manipulation success: `yes`
- goal preservation: `yes`
- invariance preservation: `yes`
- exclusion recommendation: `include`

## Example 2 — multi-factor confound

The intervention removes a tool and also rewrites the user's requested output
format.

- manipulation success: `yes`
- goal preservation: `no`
- invariance preservation: `no`
- exclusion recommendation: `exclude`

## Example 3 — deterministic failure but no recovery route

The intended failure is present, but the item requires evidence obtainable
only through the failed tool and the answer contract forbids abstention.

- manipulation success: `yes`
- solvability: `no`
- answer-contract correctness: `no`
- exclusion recommendation: `revise`

## Example 4 — managed ambiguity

Two interpretations are plausible, and the task explicitly permits a
clarification question or a stated assumption.

- task clarity: `yes`
- ambiguity: `acceptable`
- answer-contract correctness: `yes`

## Example 5 — scorer mismatch

The reference permits a calibrated abstention, while the scorer accepts only
the unchanged clean answer.

- clean gold correctness: `yes`
- answer-contract correctness: `yes`
- scorer compatibility: `no`
- exclusion recommendation: `revise`

Do not copy these labels into candidate review rows. Candidate judgments must
be made independently from the blinded packet.
