# Human Review Sheet Guide

Status: instructions only; no judgments are embedded here.

Open `review_items.jsonl` with a local text/JSON viewer and
`review_judgments.csv` with a CSV editor that preserves UTF-8 and the header.
Filter to the reviewer slot assigned by the coordinator.

Do not sort only one column, rename columns, add formulas, or export in a locale
that rewrites timestamps. Save a CSV copy, reopen it, and confirm the candidate
IDs and row count are unchanged before returning it.

Allowed review values:

- dimensions 1–9: `yes`, `no`, `unclear`;
- ambiguity: `acceptable`, `problematic`, `unclear`;
- exclusion: `include`, `revise`, `exclude`;
- confidence: integer 1–5.

Leave no assigned human field blank. Never fill an unassigned slot. Never
paste AI/proxy labels or ask an AI to draft notes. Report accidental model or
peer-label exposure to the coordinator; the affected row is ineligible until
the blinding deviation is resolved.
