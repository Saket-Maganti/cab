# CAB Dataset Diversity and Split Audit

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

Counts treat parameter variants as variants, not independent conceptual diversity. Unique templates/patterns/domains are reported separately from raw instances.

| Role | Raw instances | Unique bases | Templates | Instruction patterns | Domains | Tool combinations | Answer types | Families | Naturalistic share |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| `dev_fixture` | 9 | 3 | 3 | 3 | 3 | 3 | object:2, string:1 | 6 | 0.0 |
| `compact20_pilot` | 30 | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| `scale100_confirmatory` | 600 | 100 | 12 | 44 | 12 | 27 | object:76, string:24 | 10 | 0.0 |
| `naturalistic_transfer` | 432 | 72 | 8 | 47 | 8 | 17 | object:54, string:18 | 10 | 1.0 |
| `main500_confirmatory` | 3000 | 500 | 12 | 48 | 12 | 27 | object:374, string:126 | 10 | 0.0 |
| `heldout_challenge` | 300 | 50 | 12 | 39 | 12 | 23 | object:38, string:12 | 10 | 0.0 |

## Role policy

- `dev_fixture`: code mechanics only.
- `compact20_pilot`: feasibility, scorer sanity, cost, and pipeline pilot; insufficient alone for top-tier empirical claims.
- `scale100_confirmatory`: preregistered family-balanced confirmatory candidate.
- `naturalistic_transfer`: mock-realistic artifacts with provenance, license, privacy, injection, answer-isolation, and human-review requirements.
- `main500_confirmatory`: 500 pilot bases plus a separately held-out 50-base challenge role; execution requires earlier evidence.
- `heldout_challenge`: delayed/post-study release; never a development target.

## Split integrity

- Cross-role overlap count: 0
- Recorded/live hash issues: 0
- Registry hashes exact instances, base memberships, and source files.
- Any incompatible overlap is a blocker.

## Diversity gates before freeze

- Unique base tasks and normalized instruction patterns, not raw rows.
- Maximum variants per template and family/domain balance.
- Difficulty, tool, scorer-policy, and answer-policy diversity.
- Naturalistic share and source/license coverage.
- No development/confirmatory/challenge overlap.
- Human clarity, gold, isolation, ambiguity, realism, and exclusion review.

## Current status

All non-fixture roles are candidate material labeled `HUMAN_INPUT_REQUIRED`. No pack is paper eligible or authorized for scientific execution.
