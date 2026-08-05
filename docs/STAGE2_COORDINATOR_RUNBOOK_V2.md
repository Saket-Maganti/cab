# Stage-2 coordinator runbook (V2)

Stage 2 exposes gold, answer contracts, scorer contracts and route policies. It
is the most sensitive material in the project. Treat every step here as
irreversible with respect to blinding: once a reviewer has seen Stage 2, their
Stage-1 judgements can no longer be treated as blind.

```text
No genuine review has occurred.
C10 has not passed.
Model execution is blocked.
```

## Preconditions

Stage 2 cannot be unlocked until all of the following hold, and the command
refuses if any of them does not:

- a valid Stage-1 commitment receipt exists;
- both reviewers hold their own signed declarations;
- both reviewers are qualified against their own private qualification package,
  on the active `cab_qualification_v4` version;
- both Stage-1 submissions are complete and validated;
- no unresolved malformed rows remain;
- the reviewer assignment registry is unchanged since the Stage-1 commitment;
- `$CAB_STAGE2_KEY_PATH` resolves to a readable key outside the repository;
- the packet commitment, the scientific freeze hash and the exact code commit
  all match what the Stage-1 commitment bound.

## Key handling

- The key lives outside the repository, owner-only (`0600`), in an owner-only
  directory (`0700`).
- The key value is never bound into the freeze, never written to a report, and
  never printed.
- The vault refuses to operate if the key path resolves inside the repository.
- Losing the key means the Stage-2 material is unrecoverable. Back it up
  yourself, outside the repository, before you rely on it.

## Generating Stage-2 packages

```bash
python scripts/cab_review_ready_v2.py generate-stage2-packages --output-dir "$HOME/.cab/outbound/stage2"
```

- The output directory must be outside the repository; the command refuses
  otherwise.
- The vault is decrypted into an owner-only scratch directory that is wiped and
  verified empty on exit.
- No Stage-2 plaintext is ever persisted next to the vault; the command reports
  any file it finds there.
- Only hashes and counts are printed.

### Issuance

Generating the archives also seals one **issuance receipt** per reviewer. Each
receipt binds the archive hash to that reviewer's pseudonym hash, canonical
role, opaque-id namespace, declaration hash, qualification receipt hash, the
Stage-1 commitment that authorised the release, the packet commitment, the
scientific freeze hash, the exact commit and the issue time.

Stage-2 ingestion requires the receipt and re-derives every binding from the
workspace, so `ingest-stage2` takes `--package` and hashes the archive it is
given. Each of the following fails closed rather than degrading to a warning: a
modified archive, another reviewer's archive, an issuance receipt copied between
reviewers, an issuance bound to a superseded Stage-1 commitment, a wrong
opaque-id namespace, and a wrong packet, freeze or commit.

The issuance hash is then carried into the Stage-2 submission receipt, the
Stage-2 disagreement queue, both adjudicator packages, the final adjudicated
records, C10, the reviewed-slice lock and the execution authorization, so an
unissued Stage-2 submission cannot reach a pass by any route.

## What Stage 2 actually asks

Each item is judged on nine substantive dimensions, with four allowed values:

| Value | Meaning |
|---|---|
| `YES` | the reviewer accepts this dimension |
| `NO` | a substantive objection; blocks acceptance; requires notes |
| `UNSURE` | unresolved; blocks acceptance exactly as `NO` does; requires notes |
| `NOT_APPLICABLE` | valid only for the three conditional dimensions, and only when the item's frozen `applicability.json` agrees |

The frozen rule lives at
`configs/reviewer_ready_v2/stage2_acceptance_policy_v1.json` and is bound into
the scientific freeze. **A complete Stage-2 form is not an approval.** Form
completion and substantive acceptance are recorded separately, and only the
latter can reach C10.

A reviewer confidence below 3 routes the item to adjudication even when every
value would otherwise accept.

## Adjudication

Stage 1 and Stage 2 have separate disagreement queues, because they dispute
different things: whether the *pair* is a valid controlled comparison, and
whether the *withheld material* is correct. A resolved Stage-1 disagreement can
never stand in for an unexamined Stage-2 objection.

A Stage-2 dimension enters the queue on any of: direct reviewer disagreement,
either reviewer answering `NO`, either reviewer answering `UNSURE`, confidence
below threshold, an unmatched substantive note, a `NOT_APPLICABLE` that
contradicts the applicability map, or an applicability policy mismatch between
the two reviewers.

Adjudicator materials are generated **only after** the relevant queue exists,
and contain only the disputed items. Do not pre-generate a generic adjudicator
package covering all items — that would expose the whole slice to a third person
for no reason.

```bash
python scripts/cab_review_ready_v2.py generate-stage1-adjudicator-package --output-dir "$HOME/.cab/outbound/adjudication"
python scripts/cab_review_ready_v2.py generate-stage2-adjudicator-package --output-dir "$HOME/.cab/outbound/adjudication"
```

A queue records *that* two reviewers disagreed; it does not carry enough of the
item to settle the disagreement. These packages do.

`stage1_adjudicator_package.zip` carries, per disputed item, the clean and
intervention task context, the primitive evidence, the controlled difference
with its intended changed factor, the claimed preserved invariants, the declared
tool capabilities, both reviewers' values, confidence and notes, and a
structured adjudication form. It withholds Stage-2 gold and scorer material
exactly as a Stage-1 reviewer package does, and generation refuses outright if
any Stage-2 key reaches it.

`stage2_adjudicator_package.zip` carries the withheld material that is in
dispute: the gold and policy, the accepted variants, the answer and scorer
contracts, the route requirements, the applicability map, and the recovery,
abstention or clarification policy where the item has one — alongside both
reviewers' judgements and the same structured form. Policies the item genuinely
lacks are named as absent rather than silently omitted.

Each package is sealed to its packet commitment, stage, disagreement-queue hash,
disputed item ids, adjudicator assignment, Stage-2 issuance hashes, freeze hash,
exact commit and its own archive hash. Ingestion takes `--package`, hashes it,
and refuses an adjudication submitted against a stale package — one built before
the queue was rebuilt — or against any other package. Rebuilding a queue
therefore means reissuing its package.

Each decision requires `final_value`, `rationale`, `evidence_reference`,
`confidence` and `exclude_item`, and binds both reviewer values, the
adjudicator's assignment hash and the queue hash. There are exactly two ways to
resolve a disputed dimension: a final value that accepts under the frozen rule,
or `exclude_item=YES`. An adjudicator cannot record a third outcome, so no
unresolved `NO` or `UNSURE` can survive into C10.

The adjudicator must be neither reviewer. The assignment registry refuses the
overlap when the role is created, and ingestion re-checks it against the
registry before it accepts a single decision.

## Final adjudicated records

Before C10 there is one final record per pair, combining Reviewer A and B
Stage-1, the Stage-1 adjudication if there was one, Reviewer A and B Stage-2,
the Stage-2 adjudication if there was one, and the inclusion decision. Every
dimension carries its provenance: `agreed_by_reviewers`,
`resolved_by_adjudicator`, or `excluded`.

C10 reads only these records for eligibility. It never derives an acceptance
from a raw reviewer row.

## C10

C10 runs on genuine validated review data only. It fails closed if any of these
does not hold: two distinct assigned reviewers and a separate adjudicator with
no role overlap; a valid, untampered assignment registry; both signed
declarations; both private qualification passes on the active (non-retired)
qualification version; complete Stage-1 and Stage-2 submissions bound to the
correct package hashes and item namespaces; a sealed Stage-2 issuance receipt
for each reviewer, matching that reviewer's submission and the current Stage-1
commitment, and carried into the queue, the final records and the adjudications;
every adjudicated stage decided against the adjudicator package that was
actually issued for its queue; full pair coverage; every Stage-1 and Stage-2
dimension accepted in the final adjudicated records; every disagreement
resolved; exclusions applied; Stage-1 and Stage-2 raw agreement each at or above
threshold, per dimension and overall; and every authenticity binding present.

Agreement is computed from the two independent pre-adjudication submissions.
Adjudicated values decide eligibility and never enter an agreement statistic —
resolving a dispute must not make two reviewers look as though they had agreed.

Authenticity is not a mode. A production receipt is one sealed under the
coordinator's external acceptance key; a fixture receipt is sealed under a
deliberately public one and fails production verification on origin, on schema
and on message-authentication code. No flag converts one into the other.

Until genuine review happens, C10 is `C10_PENDING_GENUINE_REVIEW`. It is not
`FAIL`, and it is certainly not `PASS`.

## Slice lock and execution

The reviewed slice cannot be locked before C10 passes. The lock binds the packet
commitment, the assignment registry digest, both declaration hashes, both
qualification receipt hashes, both Stage-1 submission hashes, the Stage-1
commitment, both Stage-2 submission hashes, both Stage-2 issuance receipt
hashes, both issued Stage-2 archive hashes, both adjudicator package hashes,
both adjudication hashes, the final adjudicated records, the exclusion register,
the C10 report, the scorer, endpoint, analysis-plan and system-identity hashes,
the exact Git commit and the scientific freeze hash.

Model execution cannot be authorized before the slice is locked, and is refused
on a fixture C10, a manually edited or re-hashed C10, a stale C10, a C10 from
another packet, incomplete Stage 2, an unresolved objection, a mismatched commit
or freeze, or a missing external attestation. Neither gate can be bypassed by
editing a file: every receipt is content-bound and authenticated.
