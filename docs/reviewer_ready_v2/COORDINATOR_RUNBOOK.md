# Coordinator runbook — genuine reviewer onboarding

The operational sequence for running CAB's two-stage human review with real
reviewers. Every command below is provider-free and performs no model execution.

Current state, stated up front so nothing here reads as a result:

```text
CAB_READY_FOR_GENUINE_REVIEWER_DISTRIBUTION
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
genuine human judgments: 0
genuine adjudications: 0
genuine model trajectories: 0
```

For *why* the chain is built the way it is, read
[`IMMUTABLE_REVIEW_CHAIN.md`](IMMUTABLE_REVIEW_CHAIN.md) first. For what happens
when something goes wrong, read
[`RECOVERY_AND_CORRECTION_POLICY.md`](RECOVERY_AND_CORRECTION_POLICY.md) *before*
you start, not after.

## 0. Before anything

Four external keys live outside the repository and are never committed:

| variable | holds |
| --- | --- |
| `CAB_PACKET_SEED_PATH` | private packet generation seed |
| `CAB_STAGE2_KEY_PATH` | Stage-2 vault key |
| `CAB_QUALIFICATION_KEY_PATH` | qualification answer key |
| `CAB_COORDINATOR_KEY_PATH` | coordinator acceptance key that seals production receipts |

Without `CAB_COORDINATOR_KEY_PATH` no production receipt can be sealed at all, so
a synthetic run cannot mint one. That is the authenticity boundary; there is no
flag anywhere that substitutes for it.

Print the machine-readable version of this runbook at any time:

```bash
python -m causal_agent_bench.review_ready_v2.cli coordinator-checklist
```

## 1. People

Recruit **two independent reviewers and one separate adjudicator**. The
adjudicator must be neither reviewer; the registry refuses the overlap rather
than warning about it.

```bash
python -m causal_agent_bench.review_ready_v2.cli create-reviewer-assignment --role REVIEWER_A --pseudonym <pseudonym>
```

Repeat for `REVIEWER_B` and `ADJUDICATOR`. Assignments are write-once. Reusing a
pseudonym across roles, re-registering a role, or presenting a package whose hash
does not match the recorded binding is refused.

## 2. Declarations and qualification

Each reviewer returns a signed declaration and their qualification answers.

```bash
python -m causal_agent_bench.review_ready_v2.cli ingest-reviewer-declaration --role REVIEWER_A --declaration <file>
python -m causal_agent_bench.review_ready_v2.cli score-private-qualification --role REVIEWER_A --submission <file>
```

Every `*_confirmed` field must be a literal `true` in the reviewer's own file.
Ingestion never supplies, defaults or infers a value. A disclosed conflict of
interest does not silently pass — record an explicit decision:

```bash
python -m causal_agent_bench.review_ready_v2.cli accept-reviewer-declaration --role <role> --decision ACCEPTED --rationale <text>
```

The qualification answer key is never logged, and the receipt binds the reviewer
by pseudonym *hash* so it can be shown without naming anyone.

## 3. Stage 1

```bash
python -m causal_agent_bench.review_ready_v2.cli ingest-stage1 --role REVIEWER_A --submission <file>
python -m causal_agent_bench.review_ready_v2.cli ingest-stage1 --role REVIEWER_B --submission <file>
python -m causal_agent_bench.review_ready_v2.cli commit-stage1
python -m causal_agent_bench.review_ready_v2.cli verify-committed-evidence
```

**`commit-stage1` is irreversible.** It verifies both submissions against the
registry, the declarations, the qualification receipts, the package hashes and
the expected item coverage, then copies the verified receipt bytes into a
write-once snapshot and seals a commitment that binds the payload hash, the
sealed receipt file hash and the canonical judgement digest for each reviewer.

From that moment nothing reads a live submission file again, and a live file that
no longer matches the snapshot is treated as tampering.

## 4. Stage 2

Never send Stage-2 material before `commit-stage1` and `unlock-stage2` both
succeed.

```bash
python -m causal_agent_bench.review_ready_v2.cli unlock-stage2
python -m causal_agent_bench.review_ready_v2.cli generate-stage2-packages --output-dir <outside-repo>
python -m causal_agent_bench.review_ready_v2.cli ingest-stage2 --role <role> --submission <file> --package <issued-stage2-zip>
```

Each Stage-2 submission must be ingested against the exact archive issued to that
reviewer. A modified or swapped archive is refused on the issuance binding. The
Stage-2 snapshot is created automatically when the second submission lands; after
that no further Stage-2 submission is accepted.

A complete Stage-2 form is not an approval. Adjudicate every `NO` and every
`UNSURE`.

## 5. Adjudication

```bash
python -m causal_agent_bench.review_ready_v2.cli build-stage1-disagreements
python -m causal_agent_bench.review_ready_v2.cli generate-stage1-adjudicator-package --output-dir <outside-repo>
python -m causal_agent_bench.review_ready_v2.cli build-stage2-disagreements
python -m causal_agent_bench.review_ready_v2.cli generate-stage2-adjudicator-package --output-dir <outside-repo>
python -m causal_agent_bench.review_ready_v2.cli ingest-stage1-adjudication --pseudonym <pseudonym> --decisions <file> --package <zip>
python -m causal_agent_bench.review_ready_v2.cli ingest-stage2-adjudication --pseudonym <pseudonym> --decisions <file> --package <zip>
```

Adjudicator packages carry disputed items only, with the evidence to decide them
and nothing else. Stage-1 packages withhold all Stage-2 gold, contracts and
scorer material exactly as a Stage-1 reviewer's package does.

An adjudication binds the exact queue *and* the exact package. If a queue is
rebuilt the package must be reissued; an adjudication against the stale package
is refused. Once an adjudication is sealed it cannot be replaced, and it cannot
be accepted at all after the final records exist.

## 6. Settle, evaluate, lock

```bash
python -m causal_agent_bench.review_ready_v2.cli build-final-adjudicated-records
python -m causal_agent_bench.review_ready_v2.cli compute-agreement
python -m causal_agent_bench.review_ready_v2.cli run-c10
python -m causal_agent_bench.review_ready_v2.cli build-exclusion-register
python -m causal_agent_bench.review_ready_v2.cli lock-reviewed-slice
python -m causal_agent_bench.review_ready_v2.cli authorize-model-execution
```

Agreement is computed from the raw independent judgements and never improves when
an adjudicator resolves a dispute. C10 recomputes both the agreement tables and
the final records from the committed judgements and refuses to score a sealed
report that does not reproduce.

`authorize-model-execution` re-derives the entire chain and compares it to what
the lock bound. Any change to any upstream artifact after the lock — including a
reviewer note that gates nothing — refuses execution.

## 7. Distribution: exactly what to send

Send each reviewer **only** their own role-specific frozen package, out of band,
and verify the hash independently before sending:

| recipient | file |
| --- | --- |
| Reviewer A | `private_data/human_review/compact20-review-ready-v2/stage1/stage1_reviewer_a.zip` |
| Reviewer A | `private_data/human_review/compact20-review-ready-v2/qualification_v4/qualification_reviewer_a.zip` |
| Reviewer B | `private_data/human_review/compact20-review-ready-v2/stage1/stage1_reviewer_b.zip` |
| Reviewer B | `private_data/human_review/compact20-review-ready-v2/qualification_v4/qualification_reviewer_b.zip` |
| Adjudicator | the Stage-1/Stage-2 adjudicator package generated at step 5, outside the repo |

Verify against `reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json`
(`stage1_package_hashes`) and `PUBLIC_PACKET_COMMITMENT.json`
(`qualification_package_hashes`) before each send:

```bash
shasum -a 256 private_data/human_review/compact20-review-ready-v2/stage1/stage1_reviewer_a.zip
```

**Never send, for any reason:**

- the full repository, or a full ZIP of it;
- any part of `private_data/` other than the one role-specific package above;
- the qualification source (`qualification_v4/qualification_source.json`);
- the qualification answer vault (`qualification_v4/qualification_key.enc`);
- Stage-2 plaintext, or the Stage-2 vault (`stage2/stage2_vault.enc`);
- the Stage-2 decryption key, or any other external key;
- the private item mappings (`mappings/`);
- retired packages or old qualification versions
  (`qualification_retired_v3/` is retired and refused by the active gates);
- source code containing private material;
- the other reviewer's package — role isolation is the design, not a formality.

Reviewer A and Reviewer B receive independently ordered packages with disjoint
opaque item namespaces (`RA-…` and `RB-…`). A submission carrying the other
reviewer's prefix is a package swap and is refused.

## 8. Backups

Back up the private root — including `committed_stage1/` and
`committed_stage2/` — to encrypted storage outside the repository. Restore is the
one moment the snapshot can be silently damaged, so after any restore run:

```bash
python -m causal_agent_bench.review_ready_v2.cli verify-committed-evidence
```

Back up the four external keys separately from the private root. Losing
`CAB_COORDINATOR_KEY_PATH` after commitment means the committed receipts can no
longer be verified, and there is no recovery from that.

## 9. Prohibited

- Editing any receipt, registry, queue, snapshot or manifest by hand.
- Copying a receipt between workspaces, reviewers, packets or stages.
- Re-running `commit-stage1` — it refuses, and attempting it is a sign something
  has already gone wrong.
- Presenting fixture artifacts as evidence. Fixture receipts are sealed by a
  deliberately public authority and stamped
  `SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE`; no flag converts one.
- Beginning any model run before genuine C10 and the reviewed-slice lock.
- Publishing a reviewer pseudonym, identity, declaration text or submission.

## 10. The next action

> Recruit two independent reviewers and one separate adjudicator; create
> production assignments and declarations; run private qualification V4;
> distribute only the role-specific frozen Stage-1 packages; commit immutable
> Stage-1 evidence; unlock Stage 2; adjudicate; run C10; lock the reviewed slice;
> and only then begin the one-task live smoke.
