# Recovery and correction policy

Read this before starting genuine review, not after something goes wrong.

## The policy, in one line

**There is no correction path for committed review evidence. A mistake means a
fresh workspace under a new packet version.**

## Why not an amendment mechanism

A correction mechanism would have to let a coordinator rewrite a sealed artifact
and re-derive everything downstream. That is exactly the capability the
integrity closure removed — the confirmed defect was a coordinator who could
re-seal a committed Stage-1 receipt and have every downstream gate accept it.
Adding a blessed version of the same capability would reopen it, and the
difference between a legitimate correction and the attack would come down to
intent, which no gate can check.

Before genuine review has produced anything, that trade is easy: a fresh
workspace costs a re-run of a workflow that takes minutes, and the review packet
itself is unchanged. The alternative costs the property that makes the record
worth anything.

So: committed review evidence is immutable, full stop.

## What is immutable, and from when

| artifact | immutable from |
| --- | --- |
| reviewer assignment | the moment it is created (write-once registry) |
| reviewer declaration, qualification receipt | the moment it is sealed |
| Stage-1 submission receipts | `commit-stage1` |
| Stage-1 commitment and snapshot | `commit-stage1` |
| Stage-2 issuance receipts | issuance |
| Stage-2 submission receipts | the second submission (snapshot is created then) |
| disagreement queues | adjudication of that stage |
| adjudicator packages, adjudications | the moment they are sealed |
| final adjudicated records | the moment they are built |
| agreement report | the moment it is computed |
| C10 report | the reviewed-slice lock |
| exclusion register, slice lock, execution authorization | the moment they are sealed |

## What to do instead

### Before `commit-stage1`

Nothing is frozen yet except assignments, declarations and qualification
receipts. A malformed Stage-1 submission can simply be re-ingested — Stage-1
submissions become immutable only at commitment.

If an **assignment** is wrong, that is not recoverable in place: assignments are
write-once by design, because a reassignable role is a reviewer swap waiting to
happen. Start a fresh private root.

### After `commit-stage1`

Start a fresh workspace:

1. Choose a new packet version. Do **not** reuse the existing private root.
2. Regenerate the private packet, the Stage-1 packages and the qualification
   packages under that version.
3. Re-run the whole coordinator sequence from
   [`COORDINATOR_RUNBOOK.md`](COORDINATOR_RUNBOOK.md).
4. Retire the abandoned packet version in
   `reports/reviewer_ready_v2/RETIRED_PACKET_REGISTRY.json` so the active gates
   refuse it.
5. Record why, in the commit message and in the retirement entry. An abandoned
   review that leaves no trace is worse than one that leaves an explanation.

Reviewers do **not** need to redo work they already did correctly, but their
submissions must be re-ingested under the new packet version and re-committed.
Their earlier receipts are not evidence for the new packet, and copying one
across is refused on the packet binding.

### If the private root was moved, restored, or touched by another tool

Run this first, before any other command:

```bash
python -m causal_agent_bench.review_ready_v2.cli verify-committed-evidence
```

If it passes, the chain is intact and you can continue. If it fails, **stop**.
Do not attempt a repair. Read the failed checks, work out what touched the
workspace, and treat the workspace as compromised unless you can account for the
change from a backup that verifies.

### If the coordinator key is lost

There is no recovery. The committed production receipts can no longer be
verified, and no replacement key can re-seal them without producing exactly the
artifact this design refuses. Back the key up separately from the private root,
before you begin.

## Backups

Back up, to encrypted storage outside the repository:

- the whole private root, including `committed_stage1/` and `committed_stage2/`;
- the four external keys, stored separately from the private root.

Restore is the one moment a snapshot can be silently damaged — a partial copy, a
permissions change, a symlink introduced by an archiver. All three are refused by
the verifier rather than silently accepted, which is why the verify step after a
restore is mandatory rather than advisory.

## What a hostile audit will and will not tell you

```bash
python scripts/audit_final_review_integrity.py
```

This proves the *gates* refuse a mutated chain. It runs entirely on synthetic
fixtures and says nothing about whether your particular workspace is intact —
use `verify-committed-evidence` for that.

Neither command, and nothing in this repository, can tell you whether a human
reviewer actually did the work they signed for. Receipts are tamper-evident and
content-bound; they are not proof of identity, and the project makes no such
claim.
