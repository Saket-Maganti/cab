# Human Review UI Guide

Status: instructions only. Do not fill rows from this document.

## Reviewer Task

For each Compact-20 candidate, inspect the clean/intervention pair and answer the review fields in the CSVs. Use your own judgment; do not copy AI-proxy labels.

## Review Choices

- `yes`: criterion clearly passes.
- `no`: criterion clearly fails.
- `unclear`: criterion cannot be resolved from the packet.
- `exclude`: task should not be run until repaired or replaced.

## Required Metadata

Every completed row needs `reviewer_id`, `timestamp`, and notes for any `no`, `unclear`, or `exclude`.

## Do Not

- Do not infer missing information.
- Do not change task content.
- Do not paste proxy labels into human fields.
- Do not mark C10 complete.
