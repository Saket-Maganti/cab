# Compact-20 Canonical Human Review Packet

Status: `HUMAN_INPUT_REQUIRED`. Genuine human review rows: **0**.

This directory is the only canonical Compact-20 C10 input packet. Read
`docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md` before using it.

| File | Purpose | Current human evidence |
|---|---|---:|
| `review_items.jsonl` | Hash-bound, model-blinded candidate pairs | 0 |
| `review_judgments.csv` | 40 assignment rows (20 candidates × 2 blank reviewer slots) | 0 |
| `reviewer_registry.csv` | Header-only qualified reviewer/adjudicator registry | 0 |
| `adjudication.csv` | Blank candidate placeholders for later disagreements | 0 |
| `review_session.json` | Pending session, blinding, and provenance state | 0 |
| `manipulation_checks.json` | Deterministic marker/linkage checks | engineering only |
| `c10_prerequisites.json` | Hashes/status for leakage, answer, checks, and freeze | input pending |
| `packet_manifest.json` | Packet hashes and zero-count boundary | 0 |
| `REVIEWER_QUALIFICATION_EXAMPLES.md` | Worked training patterns | design only |

The assignment rows contain candidate IDs and slot numbers only. Blank slots
are not human rows. Never invent identities or judgments to fill them.

Build safely:

```bash
python3 scripts/build_c10_review_packet.py
```

Validate fail-closed:

```bash
python3 scripts/validate_cab_human_reviews.py
```

Exit code 2 is expected until genuine review and every prerequisite are
complete. Legacy split CSVs remain for historical compatibility and are
ignored by the canonical validator.
