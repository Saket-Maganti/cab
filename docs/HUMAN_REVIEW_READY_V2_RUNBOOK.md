# Human review runbook (reviewer-ready V2)

Canonical operating procedure for `compact20-review-ready-v2`.

```text
The repository is engineering-ready for genuine Stage-1 review.
No genuine review has occurred.
Stage 2 remains locked.
C10 has not passed.
Model execution is prohibited.
```

## Canonical paths

Everything below is resolved from
`reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json`. Do not use any path from
a retired packet; the gates reject them by identity, not by name.

| What | Where |
|---|---|
| Private packet root | `private_data/human_review/compact20-review-ready-v2/` (Git-ignored) |
| Reviewer A package | `<root>/stage1/stage1_reviewer_a.zip` |
| Reviewer B package | `<root>/stage1/stage1_reviewer_b.zip` |
| Qualification packet | `<root>/qualification/qualification_packet.zip` |
| Encrypted Stage 2 | `<root>/stage2/stage2_vault.enc` |
| Stage-2 key | outside the repository, at `$CAB_STAGE2_KEY_PATH` |
| Public commitment | `reports/reviewer_ready_v2/PUBLIC_PACKET_COMMITMENT.json` |
| Scientific freeze | `reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json` |

## Before you start

```bash
export CAB_STAGE2_KEY_PATH="$HOME/.cab/keys/stage2_review_ready_v2.key"
```

The key must live outside the repository. If the variable is unset, every vault
operation fails closed with an instruction rather than creating a key in the
working tree.

## The sequence

Each step is a gate. A later step cannot run until the earlier receipt exists
and validates.

1. **Recruit two independent reviewers.** Neither may be an author or
   co-author. Record only pseudonymous ids.
2. **Qualify them.** Send each the qualification packet. Ingest each result:
   ```bash
   python scripts/cab_review_ready_v2.py ingest-reviewer-qualification --reviewer-id <id> --submission <file>
   ```
   The threshold is 0.80 on the decisive dimensions. An unqualified reviewer
   cannot be assigned a package.
3. **Send Stage-1 packages.** Reviewer A gets only `stage1_reviewer_a.zip`;
   Reviewer B gets only `stage1_reviewer_b.zip`. Item order and opaque ids
   differ between them. Never send both packages to one person.
4. **Ingest Stage-1 submissions.**
   ```bash
   python scripts/cab_review_ready_v2.py ingest-stage1 --reviewer-id <id> --package-role stage1_reviewer_a --submission <file>
   ```
5. **Commit Stage 1.** This binds the packet commitment, both package hashes,
   both qualification receipts, both submission hashes, the review schema, the
   freeze hash and the exact commit. Stage 2 is unreachable until it validates.
6. **Unlock Stage 2.** Requires the valid Stage-1 commitment, both qualified
   reviewers, complete submissions, no unresolved malformed rows, the external
   key, and matching packet / freeze / commit bindings.
7. **Generate Stage-2 packages** into an owner-only directory outside the
   repository. Plaintext is never persisted; the scratch area is wiped and
   verified empty.
8. **Ingest Stage-2 submissions** — gold, answer contract, scorer compatibility
   and route-policy defensibility.
9. **Build the disagreement queue**, then and only then generate adjudicator
   materials for the disputed pairs.
10. **Ingest adjudication.** The adjudicator must be independent of both
    reviewers, and every decision needs a rationale.
11. **Compute agreement**, then **run C10**.
12. **Build the exclusion register**, **lock the reviewed slice**, and only then
    **authorize model execution**.

## What is currently true

- Genuine human judgements: 0
- Genuine model trajectories: 0
- C10: `C10_PENDING_GENUINE_REVIEW`
- Model execution: `MODEL_EXECUTION_BLOCKED`

## Fixture mode

`--fixture` runs the same workflow in a separate namespace stamped
`SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE`. Fixture receipts are refused by
every production gate. Use it to rehearse the mechanics; it can never produce
genuine evidence, a C10 pass, or a real run authorization.

## The exact next human action

> Recruit two independent qualified reviewers, give each only their assigned
> frozen Stage-1 package and qualification materials, keep Stage 2 inaccessible
> until both qualified Stage-1 submissions are validated and committed, then
> continue through the canonical two-stage workflow.
