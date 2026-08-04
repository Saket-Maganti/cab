# Human review runbook (reviewer-ready V2)

Canonical operating procedure for `compact20-review-ready-v2`.

```text
No genuine review has occurred.
C10 has not passed.
Model execution is blocked.
Stage 2 remains locked.
Genuine human judgements: 0
Genuine model trajectories: 0
```

The repository is engineering-ready for genuine Stage-1 review. Nothing below
has been executed against a real reviewer.

## Canonical roles

There is one role enum and no synonyms:

```text
REVIEWER_A
REVIEWER_B
ADJUDICATOR
```

Every CLI flag, package name, receipt field and registry entry normalizes to it.
`reviewer-a`, `stage1_reviewer_a` and `Reviewer A` all resolve to `REVIEWER_A`;
an unrecognised spelling is a hard error, never a new role.

## Canonical paths

Everything below is resolved from
`reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json`. Do not use any path from
a retired packet; the gates reject them by identity, not by name.

| What | Where |
|---|---|
| Private packet root | `private_data/human_review/compact20-review-ready-v2/` (Git-ignored) |
| Reviewer A Stage-1 package | `<root>/stage1/stage1_reviewer_a.zip` |
| Reviewer B Stage-1 package | `<root>/stage1/stage1_reviewer_b.zip` |
| Reviewer A qualification | `<root>/qualification/qualification_reviewer_a.zip` |
| Reviewer B qualification | `<root>/qualification/qualification_reviewer_b.zip` |
| Encrypted qualification key | `<root>/qualification/qualification_key.enc` |
| Reviewer assignment registry | `<root>/coordinator/reviewer_assignments.json` |
| Encrypted Stage 2 | `<root>/stage2/stage2_vault.enc` |
| Public commitment | `reports/reviewer_ready_v2/PUBLIC_PACKET_COMMITMENT.json` |
| Scientific freeze | `reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json` |
| Stage-2 acceptance policy | `configs/reviewer_ready_v2/stage2_acceptance_policy_v1.json` |

## External keys

Four secrets live outside the repository, named only by environment variable.
No key value is ever committed, logged, hashed into a report, or bound into the
freeze.

```bash
export CAB_PACKET_SEED_PATH="$HOME/.cab/seeds/review_ready_v2.seed"
export CAB_STAGE2_KEY_PATH="$HOME/.cab/keys/stage2_review_ready_v2.key"
export CAB_QUALIFICATION_KEY_PATH="$HOME/.cab/keys/qualification_review_ready_v2.key"
export CAB_COORDINATOR_KEY_PATH="$HOME/.cab/keys/coordinator_review_ready_v2.key"
```

`CAB_COORDINATOR_KEY_PATH` is the coordinator's acceptance key. Every production
receipt is sealed with it, and every production gate verifies that seal. Without
it the workflow cannot record production evidence at all — which is what stops a
synthetic run from being stamped as genuine. It is tamper-evidence and
coordinator authority; it is **not** a proof of any reviewer's identity, and
nothing in this project claims otherwise.

## The sequence

Each step is a gate. A later step cannot run until the earlier receipt exists
and validates. `python3 scripts/cab_review_ready_v2.py coordinator-checklist`
prints this list with the exact flags.

### Prepare the packages

```bash
python3 scripts/cab_review_ready_v2.py generate-private-packet
python3 scripts/cab_review_ready_v2.py validate-private-packet
python3 scripts/cab_review_ready_v2.py validate-stage1-packages
```

`generate-private-packet` also writes both private qualification packages and
the encrypted answer key. To rebuild only the qualification material, use
`generate-private-qualification-packages`.

### Bind each reviewer to exactly one package

```bash
python3 scripts/cab_review_ready_v2.py create-reviewer-assignment --role REVIEWER_A --pseudonym <pseudonym>
```

Repeat for `REVIEWER_B` and `ADJUDICATOR`. Assignments are write-once. They bind
pseudonym → role → Stage-1 package hash → qualification package hash → opaque id
namespace. A package swap, a reused pseudonym, a reviewer acting as adjudicator,
or a hand-edited registry is refused, not silently accepted.

### Take each reviewer's own declaration

Send each reviewer their qualification package. It contains
`reviewer_declaration.json` and `DECLARATION_INSTRUCTIONS.md`. They fill it in;
you never fill in any field on their behalf.

```bash
python3 scripts/cab_review_ready_v2.py ingest-reviewer-declaration --role REVIEWER_A --declaration <file>
```

A missing confirmation is a refusal, not a `false`. If a reviewer discloses a
conflict of interest, ingestion succeeds but qualification stays blocked until
you record an explicit decision:

```bash
python3 scripts/cab_review_ready_v2.py accept-reviewer-declaration --role REVIEWER_A --decision ACCEPTED --rationale "<text>"
```

### Score qualification privately

```bash
python3 scripts/cab_review_ready_v2.py score-private-qualification --role REVIEWER_A --submission <file>
```

The answer key is decrypted in coordinator mode only, from
`$CAB_QUALIFICATION_KEY_PATH`. The threshold is 0.80. The receipt records the
rate and per-item correctness; it never records a decisive dimension, an
expected value, or an explanation.

The earlier qualification version, `cab_stage1_qualification_v2`, shipped its
items and its answer key in tracked source. It is retired and rejected in code
under any name.

### Stage 1

```bash
python3 scripts/cab_review_ready_v2.py ingest-stage1 --role REVIEWER_A --submission <file>
python3 scripts/cab_review_ready_v2.py commit-stage1
```

Ingestion verifies the assignment, the declaration, the qualification receipt,
the package hash and the reviewer's own item namespace. `commit-stage1` binds
the packet commitment, both package hashes, both declaration hashes, both
qualification receipts, both submission hashes, the assignment registry digest,
the review schema, the freeze hash and the exact commit.

### Stage 2

```bash
python3 scripts/cab_review_ready_v2.py unlock-stage2
python3 scripts/cab_review_ready_v2.py generate-stage2-packages --output-dir <outside-repo>
python3 scripts/cab_review_ready_v2.py ingest-stage2 --role REVIEWER_A --submission <file>
```

Stage 2 asks for substantive acceptance of gold, accepted variants, answer
contracts, scorer compatibility, intervention policy, route defensibility, and
the recovery / abstention / clarification policies. `YES` and a
map-corroborated `NOT_APPLICABLE` accept; `NO` and `UNSURE` both block and both
require notes. **A complete Stage-2 form is not an approval.**

### Disagreement and adjudication

```bash
python3 scripts/cab_review_ready_v2.py build-stage1-disagreements --output-dir <outside-repo>
python3 scripts/cab_review_ready_v2.py build-stage2-disagreements --output-dir <outside-repo>
python3 scripts/cab_review_ready_v2.py ingest-stage1-adjudication --pseudonym <pseudonym> --decisions <file>
python3 scripts/cab_review_ready_v2.py ingest-stage2-adjudication --pseudonym <pseudonym> --decisions <file>
```

The two stages have separate queues because they dispute different things. Each
adjudicator decision needs `final_value`, `rationale`, `evidence_reference`,
`confidence` and `exclude_item`. There are exactly two ways to resolve a
disputed dimension: give a value that accepts under the frozen rule, or exclude
the item. An unresolved objection cannot proceed.

### Final records, C10, lock

```bash
python3 scripts/cab_review_ready_v2.py build-final-adjudicated-records
python3 scripts/cab_review_ready_v2.py compute-agreement
python3 scripts/cab_review_ready_v2.py run-c10
python3 scripts/cab_review_ready_v2.py build-exclusion-register
python3 scripts/cab_review_ready_v2.py lock-reviewed-slice
python3 scripts/cab_review_ready_v2.py authorize-model-execution
```

Agreement is computed from the two independent pre-adjudication submissions and
is reported separately for Stage 1 and Stage 2; both must meet the threshold.
Adjudicated values never enter an agreement statistic — resolving a dispute must
not make two reviewers look as though they had agreed.

C10 reads **only** the final adjudicated records for eligibility. It fails
closed unless every reviewer prerequisite, every Stage-1 and Stage-2 acceptance,
every resolved disagreement, both agreement thresholds and every authenticity
binding hold.

## Status

```bash
python3 scripts/cab_review_ready_v2.py status
```

Reports stage completion, which external keys are configured, and the C10 and
execution status. It reveals no private content and no reviewer identity.

## Fixture mode

`--fixture` runs the same workflow in a separate namespace stamped
`SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE`. Fixture receipts are sealed by a
deliberately public authority and fail production verification on origin, on
schema, and on message-authentication code. Use it to rehearse the mechanics; no
flag, mode, or edit converts a fixture artifact into genuine evidence.

## What is currently true

- Genuine human judgements: 0
- Genuine model trajectories: 0
- C10: `C10_PENDING_GENUINE_REVIEW`
- Model execution: `MODEL_EXECUTION_BLOCKED`

## The exact next human action

> Recruit two independent qualified reviewers, create and accept their reviewer
> assignments and signed declarations, give each only the assigned private
> qualification package and frozen Stage-1 package, score qualification
> privately, ingest genuine Stage-1 submissions, commit Stage 1, and keep Stage
> 2 inaccessible until every Stage-1 prerequisite passes.
