# Compact-20 Reviewer Instructions

Read `docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md` and complete qualification before
assignment.

1. Work independently from the other reviewer.
2. Use only `review_items.jsonl`; do not inspect model outputs, model/provider
   identities, aggregate results, proxy labels, or another reviewer's sheet.
3. Complete your assigned rows in `review_judgments.csv`.
4. Use only the allowed values in the header protocol.
5. Answer all eleven dimensions, record confidence 1–5, add a substantive
   note, and use a timezone-aware ISO-8601 timestamp.
6. Set `review_source=human`, `ai_assistance_used=no`,
   `model_output_visible=no`, and `model_identity_visible=no` only when each
   statement is true.
7. Do not use an AI assistant, proxy, co-reviewer, or study author to create or
   revise a judgment.
8. Report a task-authorship conflict, prior model-output exposure, accidental
   unblinding, or missing evidence to the coordinator. Do not guess.
9. Do not edit candidate content, the deterministic-check report, another
   reviewer slot, or adjudication rows.

A deterministic manipulation check confirms marker presence only. You still
judge manipulation success, isolation, goal/invariance preservation,
solvability, scorer compatibility, realism, and exclusion.

Your row is research input, not proof that C10 or any model-performance claim
is supported. The canonical validator determines eligibility after independent
review and adjudication.
