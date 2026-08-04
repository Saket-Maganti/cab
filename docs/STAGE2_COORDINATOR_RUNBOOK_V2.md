# Stage-2 coordinator runbook (V2)

Stage 2 exposes gold, answer contracts, scorer contracts and route policies. It
is the most sensitive material in the project. Treat every step here as
irreversible with respect to blinding: once a reviewer has seen Stage 2, their
Stage-1 judgements can no longer be treated as blind.

## Preconditions

Stage 2 cannot be unlocked until all of the following hold, and the command
refuses if any of them does not:

- a valid Stage-1 commitment receipt exists;
- both reviewers are qualified;
- both Stage-1 submissions are complete and validated;
- no unresolved malformed rows remain;
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

## Adjudication

Adjudicator materials are generated **only after** the disagreement queue
exists. Do not pre-generate a generic adjudicator package covering all items —
that would expose the whole slice to a third person for no reason.

Each decision binds the disputed item, both reviewer judgements, the
adjudicator's pseudonymous id, a rationale, the final decision, a timestamp and
the submission hash. The adjudicator must not be either reviewer.

## C10

C10 runs on genuine validated review data only. It fails closed if reviewer
identities are missing, reviewers are unqualified, any receipt is a synthetic
fixture, coverage is incomplete, agreement is below threshold on any gating
dimension, adjudication is unresolved, intervention isolation or goal
preservation is not confirmed, the Stage-2 gold and scorer review is incomplete,
or any packet or freeze binding mismatches.

Until genuine review happens, C10 is `C10_PENDING_GENUINE_REVIEW`. It is not
`FAIL`, and it is certainly not `PASS`.

## Slice lock and execution

The reviewed slice cannot be locked before C10 passes. Model execution cannot be
authorized before the slice is locked. Neither gate can be bypassed by editing a
file: the receipts are hash-bound, and fixture receipts are refused outright.
