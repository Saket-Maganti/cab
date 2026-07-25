# Naturalistic Transfer Study V2

Status: future no-provider design.

## Reviewer Attack

“CAB is synthetic and simulated; why should we believe it transfers?”

## Study Idea

Build a small naturalistic local-task mini-study with public, licensed, or author-created artifacts. Each task has clean/intervention pairs mapped to CAB families.

## Candidate Task Types

- local document lookup,
- spreadsheet QA over synthetic-but-realistic sheets,
- config debugging with bundled files,
- calendar/email workflow over generated local JSON,
- policy compliance over bundled policy snippets.

## Rules

- no private data,
- no scraping unless explicitly licensed and documented,
- no provider execution until gates pass,
- clean/intervention pairing preserved,
- compare family-level failure patterns against Compact-20 after both have real runs.

## Transfer Claim Boundary

The mini-study can support external-validity evidence only after real provider runs and human review. Until then it is design scaffolding.
