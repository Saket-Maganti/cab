# Intervention Taxonomy Upgrade Report

Date: 2026-07-09

## Summary

Created a V2 taxonomy surface that distinguishes current CAB families from candidate future families. The upgrade improves reviewer-facing validity discipline without generating results or modifying human-review rows.

## Added

- `docs/INTERVENTION_TAXONOMY_V2.md`
- `docs/INTERVENTION_FAMILY_VALIDITY_CHECKLIST.md`

## Key Safeguards

- Candidate families are explicitly design inventory, not active evidence.
- Every family has target factor, invariants, valid/invalid examples, scorer risks, human-review questions, and exclusion criteria.
- C10 remains blocked until real human intervention-isolation validation exists.

## Evidence Boundary

No provider calls, local LLM calls, benchmark runs, fake labels, or claim promotion were performed.
