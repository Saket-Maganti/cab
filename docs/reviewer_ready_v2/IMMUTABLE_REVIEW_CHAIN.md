# The immutable review chain

This document is the reference for how CAB's two-stage human review binds what it
commits, and why a coordinator who holds the sealing key still cannot rewrite the
scientific record after the fact.

Status of the review itself, stated once so nothing here reads as a claim about
results:

```text
CAB_READY_FOR_GENUINE_REVIEWER_DISTRIBUTION
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
```

## 1. The defect this design exists to close

The retired `cab_stage1_commitment_v2` shape recorded, per reviewer, exactly one
thing:

```text
submission_hashes[role] = stage1_submission_receipt["submission_sha256"]
```

That is the hash of the CSV bytes the reviewer uploaded. It is not the hash of
the scientific record. The record downstream is the *parsed* judgement content
inside the sealed submission receipt, together with the role, package,
declaration and qualification bindings that receipt asserts.

So a coordinator could:

1. read the sealed Stage-1 submission receipt after commitment;
2. edit a parsed judgement inside it;
3. leave the `submission_sha256` field exactly as it was;
4. re-seal the receipt with the coordinator key, producing a valid MAC;
5. leave the Stage-1 commitment untouched.

Every downstream consumer read the current receipt file, so the altered content
flowed into pairing, the disagreement queues, agreement, the adjudicator
packages, the final adjudicated records, C10, the exclusion register, the slice
lock and the execution authorization. The chain still reached
`C10_MECHANICS_PASS`.

The MAC was never the weak link. The MAC proves the receipt was sealed by the
authority; it says nothing about whether the authority sealed it *before or after*
the commitment. The weak link was that nothing recorded what "before" looked
like.

## 2. Three digests, never interchangeable

| digest | covers | answers |
| --- | --- | --- |
| `payload_sha256` | the bytes the reviewer uploaded | was the form edited in transit? |
| `sealed_receipt_file_sha256` | the exact receipt file on disk, envelope and all | was this file replaced or re-sealed? |
| `canonical_scientific_content_sha256` | every parsed cell and every provenance binding | did the *content* change? |

Each answers a different question and none substitutes for another:

- Re-sealing an unchanged receipt changes the **file** hash (sealing stamps a
  fresh `recorded_at`) but not the **content** hash. That is why a re-seal alone
  is distinguishable from an edit.
- Editing a judgement while retaining `submission_sha256` leaves the **payload**
  hash unchanged but changes the **content** hash. That is precisely the
  confirmed exploit, and it is why the payload hash is itself *inside* the
  canonical content digest.
- Reordering the JSON keys changes the **file** hash but not the **content**
  hash, because canonicalisation sorts mappings. Key order is serialisation, not
  science.

The canonical content digest excludes only `receipt_sha256` and `receipt_mac`
(a digest cannot cover itself, and the MAC is computed over the digest) plus
`recorded_at` (a sealing stamp, not content). **Notes are inside it.** Notes gate
nothing, but they are committed evidence, so changing one is detected.

Implementation: [`commitment_integrity.py`](../../src/causal_agent_bench/review_ready_v2/commitment_integrity.py).

## 3. The committed snapshot

At `commit_stage1()` the verified receipt bytes are copied into a write-once
directory under the private root:

```text
<private_root>/<authority_namespace>/committed_stage1/
    REVIEWER_A.stage1_submission.json
    REVIEWER_B.stage1_submission.json
    manifest.json
```

Canonical role names only — never `reviewer-a`, never `stage1_reviewer_a`. Two
spellings would be two committed identities for one person.

Creation is atomic. The whole snapshot is built in a temporary sibling directory,
fsynced, and renamed into place, so an interrupted commitment leaves no partially
populated snapshot that could verify as valid. Directories are `0700`, files are
`0600`, and an existing snapshot is never overwritten.

The sealed manifest binds, per reviewer: canonical role, reviewer pseudonym hash,
Stage-1 package hash, CSV payload SHA-256, sealed receipt file SHA-256, canonical
judgements SHA-256, declaration receipt SHA-256, qualification receipt SHA-256,
item count and item-id digest. It also binds the manifest schema version, the
ordered reviewer-role set, the expected item count, the reviewer item-id
namespace digest, the assignment registry digest, the creation timestamp, the
artifact origin, the authority namespace, the packet version, the private packet
commitment, the scientific freeze and the frozen source commit.

Stage 2 gets the same treatment, created automatically the moment the second
Stage-2 submission is accepted and before any queue can be generated. Its
manifest additionally binds the Stage-1 commitment hash, the Stage-1 snapshot
manifest hash, both reviewers' canonical Stage-1 judgement digests, and both
Stage-2 issuance receipts.

## 4. One verifier, and nothing reimplements it

```python
verify_committed_stage1_snapshot(workspace, *, expected_packet_commitment=None,
                                 expected_scientific_freeze_sha256=None,
                                 expected_frozen_source_commit=None)
verify_committed_stage2_snapshot(workspace, ...)
review_input_graph(workspace, ...)
```

The verifier reads **only** snapshot files. It rejects the retired commitment
schemas outright — there is no silent migration of scientific review evidence —
then re-derives every file hash, content hash, canonical judgement digest, payload
hash, declaration binding, qualification binding, package hash, registry digest,
pseudonym binding, item coverage, packet commitment, freeze, source commit and
artifact origin, and confirms exactly two distinct reviewer roles.

It also reads the *live* `stage1_submission_<role>.json` — not to use it, but to
refuse when it differs from the snapshot. Nothing downstream would consume that
file any more, so silently ignoring a conflicting replacement would hide
tampering rather than resist it.

`review_input_graph()` extends this over the whole chain: both snapshots, both
disagreement queues, both adjudications and the final records, each re-derived
from disk and compared against what the artifact consuming it bound.

## 5. What each gate now verifies

| gate | reads | refuses when |
| --- | --- | --- |
| Stage-2 unlock | committed Stage-1 snapshot | snapshot absent, manifest absent, any hash changed, registry/declaration/qualification/package changed, packet/freeze/commit changed, live receipt conflicts |
| Stage-2 issuance | committed Stage-1 snapshot | the same, and binds the snapshot manifest plus that reviewer's frozen judgement digest into the issuance receipt |
| Stage-2 ingestion | committed Stage-1 snapshot | issuance does not bind the same immutable Stage-1 evidence, or role/pseudonym/namespace/qualification/declaration/package/packet/freeze/commit disagree |
| pairing (`_paired`) | committed snapshots only | never reads a mutable submission path after commitment |
| disagreement queues | committed snapshots | regenerated after adjudication; binds both snapshot manifests, both judgement digests and its own content digest |
| agreement | committed judgements only | computed from anything else; binds its complete input graph |
| adjudicator packages | committed judgements | binding does not match the queue it answers |
| adjudication | sealed queue and package | queue content digest changed, already sealed, or the final records already exist |
| final records | validated input graph | the graph is inconsistent; binds both snapshots, both queues, both adjudications |
| C10 | validated input graph | any binding differs — and it **recomputes** agreement and the final records from committed judgements and refuses to score a report that does not reproduce |
| exclusion register | validated input graph | derived from different final records |
| slice lock | revalidated whole graph | anything upstream changed; binds every immutable digest, not just payload hashes |
| execution authorization | revalidated whole graph | any upstream artifact changed after the lock, **including reviewer notes that gate nothing** |

`locked: true` is a claim, not a proof. `authorize_model_execution()` re-derives
the entire chain from disk and compares it to what the lock bound.

## 6. C10 under a mutated chain

C10 verifies the complete input graph *before* computing any check. If any
committed receipt, snapshot, queue, adjudication or final record differs from
what the consuming artifact bound:

```text
status           = C10_PENDING_GENUINE_REVIEW
mechanics_status = C10_MECHANICS_FAIL
```

It reports rather than raises, deliberately: a mutated chain must leave a
recorded, visible failure that no caller can catch and treat as "not applicable".

## 7. One-way state transitions

```text
assignment → declarations → qualification → Stage-1 submissions
  → Stage-1 immutable commitment → Stage-2 unlock → Stage-2 issuance
  → Stage-2 submissions → Stage-2 immutable commitment → queues
  → adjudications → final records → C10 → exclusion register
  → slice lock → execution authorization
```

Every sealed receipt is write-once. Stage 1 cannot be committed twice or
resubmitted after commitment; Stage 2 cannot accept a third submission after its
snapshot exists; a queue cannot be regenerated after adjudication; an
adjudication cannot be replaced, nor accepted after the final records are built;
and C10 cannot be rewritten once a slice lock binds it.

There is no correction path. See
[`RECOVERY_AND_CORRECTION_POLICY.md`](RECOVERY_AND_CORRECTION_POLICY.md).

## 8. Filesystem defences

Critical artifacts are written by writing a temporary file in the same directory,
flushing, fsyncing, setting mode, renaming atomically, and fsyncing the
directory. Immutable artifacts are never replaced at all.

Before any critical private artifact is read or written: symbolic links are
refused, paths that resolve outside the private root are refused, and in a
production workspace group- or world-accessible files and world-writable parent
directories are refused. POSIX mode checks are skipped on platforms without
them; the containment and symlink checks are portable.

## 9. Schemas

| schema | active | retired (refused, never migrated) |
| --- | --- | --- |
| two-stage workflow | `cab_review_ready_v2_two_stage_workflow_v3` | `…_v1`, `…_v2` |
| Stage-1 commitment | `cab_stage1_commitment_v3` | absent field, `…_v1`, `…_v2` |
| committed Stage-1 snapshot | `cab_committed_stage1_snapshot_v1` | — |
| committed Stage-2 snapshot | `cab_committed_stage2_snapshot_v1` | — |
| review input graph | `cab_review_input_graph_v1` | — |

Review evidence recorded under a retired workflow schema is **development-only**.
It cannot be migrated and the active gates refuse it. Genuine review starts under
`v3` or it does not start.

Changing these receipt schemas does not invalidate the scientific task packet:
the twenty pairs, their content hashes, the reviewer packages, the qualification
material and the Stage-2 vault are unchanged.

## 10. Verifying it yourself

```bash
python scripts/audit_final_review_integrity.py
```

Builds isolated synthetic workspaces, runs the legitimate workflow, executes the
full hostile mutation matrix, and exits nonzero on any false acceptance. Results
land in `reports/final_integrity_closure/HOSTILE_INTEGRITY_AUDIT.{json,md}`.

```bash
python -m causal_agent_bench.review_ready_v2.cli verify-committed-evidence
```

Re-derives the committed evidence in a real workspace and reports every binding.
Run it first whenever a workspace has been moved, restored from backup, or
touched by anything other than this CLI.
