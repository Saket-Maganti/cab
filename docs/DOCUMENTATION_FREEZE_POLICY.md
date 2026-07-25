# Documentation Freeze Policy

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## Policy

- Do not create new meta-docs unless they directly support evidence, paper authoring, validation, release, or safety.
- Prefer updating canonical docs over adding parallel documents.
- Every new doc needs a purpose, owner, and evidence boundary.
- Public-facing release docs should avoid "god-tier" or war-room branding.
- Blockers must remain visible.
- Cleanup is not evidence and must not be described as claim support.

## Canonical Surfaces

- Claims: `docs/CLAIM_LEDGER.md`, `docs/claim_ledger.json`, `docs/CLAIM_TRIAGE_NO_RUN.md`
- No-overclaim: `docs/DO_NOT_OVERCLAIM.md`, `paper/PAPER_WORDING_GUARDRAILS.md`
- Compact review: `docs/COMPACT20_SELECTION_CRITERIA.md`, `data/human_validation/no_api_task_review/`
- C10 validation: `docs/C10_INTERVENTION_ISOLATION_VALIDATION_PROTOCOL.md`
- Submission state: `docs/NEURIPS_SUBMISSION_GATE.md`, `reports/FINAL_NO_RUN_BUILD_GATE.md`

