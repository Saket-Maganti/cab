# Compact-20 Genuine Human Review Onboarding

This packet is instructions, not evidence. The exact next executable gate is:

```bash
python3 scripts/validate_cab_human_reviews.py
```

Exit code `2` is expected until all genuine human work and prerequisites are
complete.

## Coordinator checklist

1. Read `docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md`.
2. Confirm the canonical packet is still hash-bound and blank. Do not rebuild
   it after genuine data entry begins.
3. Administer qualification independently; require at least 80%.
4. Store real-name mappings and salts outside the repository.
5. Register privacy-safe IDs only after qualification, consent, conflict,
   compensation, and human-only attestations are genuine.
6. Assign exactly two or more independent eligible reviewers per candidate out
   of band. Required C10 rows cannot come from study authors.
7. Keep model-output and model-identity blinding enabled.
8. Lock initial sheets before computing agreement.
9. Assign a separate qualified adjudicator for each observed disagreement.
10. Complete and hash-bind leakage, answer-contract, manipulation, session, and
    slice prerequisites.
11. Run the canonical validator without weakening thresholds.

Each completed judgment must include all 11 dimensions, confidence `1–5`, a
substantive note, a timezone-aware timestamp, human source, and explicit
no-AI/no-proxy attestation. Amendments must supersede an immutable original.

Do not use the bundled local-development review identity adapter as genuine
evidence; repository documentation classifies that adapter as fixture-only.

Expected successful output:

```text
human_review_state=HUMAN_REVIEW_COMPLETE
c10_state=PASS
complete_review_groups=20
```

Only then may CPU-H3 issue a genuine C10 receipt and CPU-H4 begin slice lock.
