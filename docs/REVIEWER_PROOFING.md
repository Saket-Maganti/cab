# NeurIPS ED Track Reviewer Proofing

This document indexes reviewer-facing materials for *When Agent Success Is Not Agent Skill*. It does **not** replace the claim ledger or paper text.

## Primary artifact

- **[Reviewer attack response matrix](../reviews/reviewer_attack_response_matrix.md)** — 20 likely reviewer attacks with status, required fixes, paper sections, evidence needs, and submission blocking flags.
- **Prioritized fix list** — embedded at the top of the matrix (P0–P3).

## Related governance

| Resource | Purpose |
| --- | --- |
| `docs/claim_ledger.json` | Which claims are planned vs supported |
| `docs/PAPER_EVIDENCE_MAPPING.json` | Map paper fragments to run artifacts |
| `docs/ETHICS_AND_LIMITATIONS.md` | Release-scope limits |
| `reviews/rebuttal_plan_round_1.md` | Earlier round-1 response sketches |
| `reviews/internal_review_round_1.md` | Internal review notes |

## Author workflow

1. Read the matrix before filling results or tightening claims.
2. Run `python scripts/check_reviewer_proofing.py` (included in `make paper-check`).
3. After a verified non-oracle run: `make paper-fill RUN_DIR=results/<dir>` and update matrix **Current status** for attacks 5, 11, 12, 14, 16, 18.
4. Never cite stub/smoke runs as scientific evidence (`release/release_manifest.json`).

## Submission gate (empirical paper)

Minimum before claiming NeurIPS-ready empirical results:

- P0 fixes in matrix (LLM runs, human validation pilot, intervention audit, oracle excluded from rankings).
- All blocking **Yes** rows addressed or claims downgraded to `planned` / `engineering_only` in the claim ledger.
- `make paper-submission-check` passes with filled `paper/generated/` and no submission-blocking placeholders.
