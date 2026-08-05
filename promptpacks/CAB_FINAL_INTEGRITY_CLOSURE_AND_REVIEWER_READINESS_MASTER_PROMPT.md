# CAB Final Integrity Closure and Genuine Reviewer-Readiness Master Prompt

## Repository

```text
/Users/saketmaganti/Projects/causal-agent-bench
```

## Expected starting point

The last independently audited repository state was:

```text
branch: main
HEAD: 131cd10abe519a7174171bb47e90347326862ca4
commit message: Make qualification unreconstructible, and bind what reviewers receive
remote: origin/main
```

The repository may have advanced since this prompt was written. Before modifying anything:

1. inspect the real current branch, commit, status, remote, and recent history;
2. confirm whether `131cd10abe519a7174171bb47e90347326862ca4` is the current commit or an ancestor;
3. adapt this repair to the current code without reverting legitimate later work;
4. refuse to proceed from an unrelated branch, detached accidental worktree, or repository that does not contain the CAB reviewer-ready V2 workflow.

Use the highest available reasoning and implementation effort.

---

# 1. Mission

Perform **one final, targeted integrity-closure pass** over CAB’s human-review and execution-authorization workflow.

This is not another maturity-level expansion.

Do not create Level 7.

Do not redesign CAB.

Do not regenerate the scientific task packet unless an actual cryptographic or scientific defect makes that unavoidable.

Do not run models.

Do not perform genuine human review.

Do not fabricate reviewer declarations, qualification attempts, human judgments, adjudications, C10 evidence, slice locks, trajectories, empirical results, paper assets, or supported claims.

The mission is to:

1. close the confirmed Stage-1 post-commit mutability defect;
2. detect and close every adjacent defect of the same class across the complete reviewer workflow;
3. make committed review evidence immutable or cryptographically revalidated before every downstream use;
4. ensure no stale, replaced, swapped, replayed, copied, or coordinator-resealed receipt can silently alter the scientific record after commitment;
5. make every downstream gate fail closed under hostile mutation;
6. preserve the frozen scientific kernel and private-review design;
7. update all schemas, tests, status documents, freeze artifacts, release artifacts, and external provenance;
8. leave the repository clean, committed, pushed, reproducible, and genuinely safe for distribution of the active role-specific qualification and Stage-1 packages.

The final honest achievement is:

> CAB is engineering-complete and integrity-closed for genuine reviewer onboarding and Stage-1 package distribution.

It is **not**:

- empirically complete;
- C10-complete;
- model-execution ready before genuine C10 and slice lock;
- submission-ready;
- paper-ready;
- Level-5 scientifically complete;
- Level-6 scientifically complete.

---

# 2. Confirmed Current Defect

The following defect was independently reproduced against commit `131cd10`.

## 2.1 Stage-1 commitment binds only the CSV payload hash

Current `ReviewWorkspace.commit_stage1()` records, for each reviewer:

```text
submission_hashes[role] = stage1_submission_receipt["submission_sha256"]
```

This binds the original CSV payload bytes, but it does not bind:

```text
the complete sealed Stage-1 submission receipt
the canonical parsed judgment content
an immutable committed snapshot of the Stage-1 receipt
```

The Stage-1 submission receipt contains more than the CSV hash, including:

- parsed judgments;
- validation results;
- role;
- package hash;
- qualification receipt hash;
- declaration hash;
- row count;
- artifact origin;
- receipt schema;
- timestamp or issuance metadata;
- receipt hash;
- receipt authentication tag.

## 2.2 Downstream consumers read mutable current receipts

Downstream operations read the current receipt files from the workspace, including paths used by:

- Stage-2 unlock;
- Stage-2 issuance;
- `_paired()`;
- disagreement queue generation;
- raw agreement calculation;
- adjudicator-package generation;
- adjudication validation;
- final adjudicated record construction;
- C10;
- exclusion-register construction;
- reviewed-slice lock;
- model-execution authorization.

The workflow does not uniformly verify that the currently read Stage-1 receipt is byte-for-byte and semantically identical to the receipt frozen at Stage-1 commitment.

## 2.3 Reproduced hostile exploit

A fixture workflow was completed through Stage-1 commitment.

After commitment:

1. the Stage-1 submission receipts were read;
2. parsed reviewer content was altered;
3. the original `submission_sha256` field was retained;
4. the altered receipts were resealed with the fixture authority;
5. the original Stage-1 commitment was left unchanged;
6. downstream code consumed the altered content;
7. the workflow still reached:

```text
C10_MECHANICS_PASS
```

Observed invariant failure:

```text
Stage-1 commitment unchanged: true
committed payload hashes unchanged: true
current Stage-1 receipt hashes changed: true
altered parsed content visible downstream: true
non-fixture mechanics checks still passing: true
```

This must be impossible after this repair.

---

# 3. Required Final State

Emit the following labels only if every hard acceptance gate in this prompt passes:

```text
CAB_FINAL_INTEGRITY_CLOSURE_COMPLETE
CAB_STAGE1_IMMUTABLE_SNAPSHOT_VALID
CAB_STAGE1_POST_COMMIT_MUTATION_EXPLOIT_CLOSED
CAB_ALL_REVIEW_RECEIPT_CHAINS_REVALIDATED
CAB_STAGE2_UNLOCK_BOUND_TO_COMMITTED_STAGE1_BYTES
CAB_STAGE2_ISSUANCE_BOUND_TO_IMMUTABLE_STAGE1
CAB_ADJUDICATION_INPUTS_IMMUTABLE_AND_BOUND
CAB_C10_INPUT_GRAPH_IMMUTABLE_AND_COMPLETE
CAB_SLICE_LOCK_INPUT_GRAPH_IMMUTABLE_AND_COMPLETE
CAB_EXECUTION_AUTHORIZATION_FAILS_CLOSED
CAB_SCIENTIFIC_KERNEL_V2_PRESERVED
CAB_PRIVATE_QUALIFICATION_V4_PRESERVED
CAB_STAGE2_PRIVATE_AND_UNEXPOSED
CAB_FREEZE_AND_RELEASE_PROVENANCE_REFRESHED
CAB_REPOSITORY_CLEAN
CAB_PUSHED_TO_ORIGIN_MAIN
CAB_READY_FOR_GENUINE_REVIEWER_DISTRIBUTION
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
GENUINE_HUMAN_JUDGMENTS=0
GENUINE_ADJUDICATIONS=0
GENUINE_MODEL_TRAJECTORIES=0
PAPER_ELIGIBLE_EMPIRICAL_ASSETS=0
SUPPORTED_EMPIRICAL_CLAIMS=0
CAB_LEVEL5_COMPLETE=false
CAB_LEVEL6_COMPLETE=false
```

Do not emit `CAB_READY_FOR_GENUINE_REVIEWER_DISTRIBUTION` merely because tests written during this pass are green. It requires the hostile tests, fresh-clone verification, private-material scan, and independent invariant report defined below.

---

# 4. Non-Negotiable Preservation Rules

## 4.1 Preserve the scientific kernel

Unless a confirmed defect requires a versioned rebuild, preserve:

- all 20 active pair-content hashes;
- active Stage-1 reviewer package contents;
- active Stage-1 reviewer package hashes;
- private packet commitment;
- intervention-family composition;
- domain and difficulty composition;
- primitive evidence;
- actual-tool reconstruction;
- endpoint semantics;
- scorer semantics;
- route requirements;
- power-analysis estimands;
- statistical-analysis plan;
- private qualification V4 design;
- Stage-2 vault plaintext content;
- Stage-2 reviewer-visible scientific content;
- reviewer role definitions;
- active reviewer namespaces.

Before editing, compute and save a preservation baseline for:

```text
active pair-content digest
all individual pair-content hashes
Stage-1 Reviewer A archive hash
Stage-1 Reviewer B archive hash
qualification package hashes
qualification commitment
encrypted qualification vault hash
Stage-2 encrypted vault hash
public packet commitment
current scientific-freeze hash
```

After repair, compare every preserved value.

If any scientific-kernel value changes, stop and explain exactly why. Do not silently accept drift.

## 4.2 Preserve privacy

Never print, commit, upload, or expose:

- private candidate bodies;
- Stage-2 plaintext;
- Stage-2 decryption key;
- private qualification answer key;
- private qualification source content;
- reviewer pseudonyms;
- reviewer identities;
- reviewer declarations;
- reviewer submissions;
- coordinator acceptance key;
- production receipt-authentication key;
- private item mappings.

Use hashes and synthetic fixtures in reports.

## 4.3 Preserve evidence boundaries

No fixture artifact may count as genuine evidence.

No command-line flag, mode field, environment variable, copied receipt, or edited JSON may promote fixture artifacts to production evidence.

No generated report may claim:

```text
C10_PASS
reviewed slice approved
model execution authorized
paper eligible
empirical claim supported
```

without genuine production-origin human evidence satisfying every frozen gate.

## 4.4 No broad infrastructure expansion

Do not add:

- new maturity levels;
- new benchmark families;
- new model policies;
- new paper sections unrelated to this repair;
- new synthetic result tables;
- new execution plans unrelated to the integrity closure;
- duplicate status systems;
- another parallel reviewer workflow.

Repair and consolidate the active `review_ready_v2` path.

---

# 5. Phase 0 — Establish the Authoritative Baseline

Before changing code, produce:

```text
reports/final_integrity_closure/BASELINE_REPOSITORY_STATE.md
reports/final_integrity_closure/BASELINE_REPOSITORY_STATE.json
reports/final_integrity_closure/SCIENTIFIC_KERNEL_PRESERVATION_BASELINE.json
```

Record:

- repository root;
- branch;
- HEAD;
- origin URL;
- origin/main;
- ahead/behind state;
- dirty files;
- untracked files;
- submodules, if any;
- Python version;
- dependency environment;
- current active packet version;
- workflow schema versions;
- qualification schema version;
- receipt schema versions;
- current freeze hash;
- current package and vault hashes;
- active status-document paths;
- exact list of active scientific and private-package surfaces.

## 5.1 Handle the stale untracked prompt

The independently inspected ZIP contained:

```text
promptpacks/CAB_FINAL_REVIEW_WORKFLOW_INTEGRITY_REPAIR_PROMPT.md
```

as an untracked file.

It targets an older commit and is superseded.

If present and untracked:

- delete it, or
- move it to a clearly marked non-operational archive outside the active prompt path.

Do not execute it.

Do not leave the repository dirty.

Record the action in the final report.

## 5.2 Confirm historical commit relation

Verify:

```text
131cd10abe519a7174171bb47e90347326862ca4
```

is the starting commit or an ancestor.

If it is not in history, stop and report repository mismatch.

---

# 6. Phase 1 — Define Canonical Digests

Create a small, central, fully tested digest module, preferably:

```text
src/causal_agent_bench/review_ready_v2/commitment_integrity.py
```

Do not scatter different canonicalization rules across the workflow.

Implement deterministic functions for:

```python
canonical_stage1_judgements_digest(receipt) -> str
canonical_stage2_judgements_digest(receipt) -> str
canonical_declaration_digest(receipt) -> str
canonical_qualification_digest(receipt) -> str
canonical_adjudication_digest(receipt) -> str
canonical_queue_digest(receipt) -> str
canonical_assignment_registry_digest(registry) -> str
receipt_file_sha256(path) -> str
receipt_content_sha256(receipt) -> str
```

## 6.1 Canonicalization requirements

Canonical content digests must:

- use deterministic JSON serialization;
- sort mappings by key;
- preserve list order only where order is scientifically meaningful;
- normalize reviewer roles through the canonical role system;
- include all scientific and provenance fields that downstream logic trusts;
- exclude only self-referential envelope fields such as the receipt’s own hash or MAC;
- never exclude notes merely because notes are not a gating value;
- never trust a stored digest field without recomputing it;
- reject unknown schema versions;
- reject duplicate item IDs;
- reject missing expected fields;
- reject noncanonical role aliases;
- reject NaN, Infinity, or non-JSON values;
- document exactly which fields are included.

## 6.2 Receipt-file versus semantic-content digests

Maintain separate concepts:

```text
payload_sha256
sealed_receipt_file_sha256
canonical_scientific_content_sha256
```

They are not interchangeable.

The Stage-1 commitment must bind all three where applicable.

---

# 7. Phase 2 — Create an Immutable Stage-1 Snapshot

Implement a true committed snapshot instead of relying on mutable current receipt paths.

Recommended private layout:

```text
<private_root>/<authority_namespace>/committed_stage1/
    reviewer_a.stage1_submission.json
    reviewer_b.stage1_submission.json
    manifest.json
```

Use canonical role names rather than ambiguous aliases.

## 7.1 Snapshot creation

During `commit_stage1()`:

1. read and verify the current Stage-1 submission receipts;
2. verify the assignment registry;
3. verify reviewer declarations;
4. verify qualification receipts;
5. verify Stage-1 package bindings;
6. verify expected item coverage;
7. verify each receipt’s current authentication;
8. compute:
   - original CSV payload hash;
   - sealed receipt file hash;
   - canonical parsed-judgment hash;
9. copy the exact verified receipt bytes into a new temporary snapshot directory;
10. write a deterministic snapshot manifest;
11. fsync files and directory where supported;
12. atomically rename the completed temporary directory into the final committed snapshot path;
13. set private permissions:
   - directories: `0700`;
   - files: `0600`;
14. refuse overwrite if a committed Stage-1 snapshot already exists;
15. seal the Stage-1 commitment only after the snapshot and manifest verify.

Do not permit `commit_stage1()` to be called twice for the same packet/workspace.

## 7.2 Snapshot manifest

The manifest must bind, per reviewer:

```text
canonical role
reviewer pseudonym hash
Stage-1 package hash
CSV payload SHA-256
sealed receipt file SHA-256
canonical judgments SHA-256
declaration receipt SHA-256
qualification receipt SHA-256
assignment registry SHA-256
review schema version
packet version
private packet commitment
scientific freeze SHA-256
frozen-source commit
```

The manifest must also bind:

```text
manifest schema version
ordered reviewer-role set
expected item count
expected reviewer item-ID namespace digest
snapshot creation timestamp
artifact origin
authority namespace
```

Seal or authenticate the manifest under the active workspace authority.

## 7.3 Stage-1 commitment fields

Version the Stage-1 commitment schema.

The commitment must include:

```text
stage1_snapshot_manifest_sha256
stage1_snapshot_receipt_file_hashes
stage1_submission_payload_hashes
stage1_submission_receipt_hashes
stage1_canonical_judgement_hashes
stage1_package_hashes
declaration_receipt_hashes
qualification_receipt_hashes
assignment_registry_sha256
review_schema_version
packet_version
private_packet_commitment
scientific_freeze_sha256
frozen_source_commit
stage1_final = true
```

Deprecate ambiguous `submission_hashes` or retain it only as a clearly named compatibility alias that cannot be used by the active workflow.

Old Stage-1 commitment schemas must be rejected by the active workflow, not silently upgraded.

---

# 8. Phase 3 — Central Stage-1 Commitment Verification

Implement one fail-closed function, preferably:

```python
verify_committed_stage1_snapshot(
    workspace: ReviewWorkspace,
    *,
    expected_packet_commitment: str | None = None,
    expected_scientific_freeze_sha256: str | None = None,
    expected_frozen_source_commit: str | None = None,
) -> dict[str, Any]
```

This function must:

1. read and authenticate the Stage-1 commitment;
2. reject retired commitment schema versions;
3. read and authenticate the immutable snapshot manifest;
4. read only snapshot receipt files, not mutable live submission paths;
5. verify exact file hashes;
6. verify canonical judgment hashes;
7. verify CSV payload hashes;
8. verify declaration bindings;
9. verify qualification bindings;
10. verify Stage-1 package hashes;
11. verify assignment registry digest;
12. verify reviewer role and pseudonym bindings;
13. verify expected item coverage;
14. verify packet commitment;
15. verify freeze;
16. verify source commit;
17. verify artifact origin;
18. verify no duplicate reviewer;
19. verify exactly two reviewer roles;
20. return the committed snapshot receipts only after every check passes.

No downstream function may independently reimplement a subset of this logic.

---

# 9. Phase 4 — Make Every Downstream Stage Use the Immutable Snapshot

Replace mutable Stage-1 reads in all downstream scientific paths.

The following must call `verify_committed_stage1_snapshot()` and use only its returned committed receipts.

## 9.1 Stage-2 unlock

`unlock_stage2()` must fail if:

- a current live Stage-1 receipt differs from the committed snapshot;
- the snapshot is absent;
- the manifest is absent;
- the snapshot receipt hash differs;
- the judgment digest differs;
- the CSV payload digest differs;
- the assignment registry changed;
- declarations changed;
- qualification receipts changed;
- package hashes changed;
- packet commitment changed;
- freeze changed;
- source commit changed.

Even if downstream logic no longer needs the mutable live receipt, detect and reject a conflicting replacement rather than silently ignoring it. This makes tampering visible.

## 9.2 Stage-2 issuance

Every Stage-2 issuance receipt must bind:

```text
stage1_commitment_sha256
stage1_snapshot_manifest_sha256
reviewer-specific Stage-1 snapshot receipt SHA-256
reviewer-specific canonical Stage-1 judgment SHA-256
```

Stage-2 issuance verification must rederive them.

## 9.3 Stage-2 ingestion

Before accepting a Stage-2 submission:

- verify the committed Stage-1 snapshot;
- verify that the reviewer’s Stage-2 issuance binds the same immutable Stage-1 evidence;
- verify role, pseudonym, namespace, qualification, declaration, package, packet, freeze, and commit.

## 9.4 Pairing and disagreement queues

`_paired()` must accept committed receipts or call the centralized verifier.

It must never read mutable `stage1_submission_<role>.json` paths after Stage-1 commitment.

Stage-1 disagreement queues must bind:

```text
stage1_snapshot_manifest_sha256
Stage-1 commitment SHA-256
both committed Stage-1 receipt hashes
both canonical Stage-1 judgment hashes
queue content digest
```

## 9.5 Raw agreement

Raw agreement must be computed only from the immutable committed Stage-1 judgments and immutable committed Stage-2 judgments.

The agreement report must bind its complete input graph.

## 9.6 Adjudicator packages

Stage-1 adjudicator packages must use only immutable committed Stage-1 judgments.

Their bindings must include the immutable snapshot manifest and receipt hashes.

Stage-2 adjudicator packages must use verified immutable Stage-2 submissions and issuance receipts.

## 9.7 Final adjudicated records

Final records must bind:

```text
Stage-1 immutable snapshot manifest
Stage-1 commitment
Stage-1 queue
Stage-1 adjudication
Stage-2 issuance receipts
Stage-2 immutable submission snapshot or equivalent receipt bindings
Stage-2 queue
Stage-2 adjudication
assignment registry
qualification receipts
declaration receipts
packet commitment
scientific freeze
source commit
```

## 9.8 C10

C10 must verify the complete input graph before calculating any check.

If any upstream receipt or snapshot differs from what was committed:

```text
status = C10_PENDING_GENUINE_REVIEW
mechanics_status = C10_MECHANICS_FAIL
```

Do not allow a mutated fixture chain to retain `C10_MECHANICS_PASS`.

Add explicit checks such as:

```text
stage1_snapshot_manifest_valid
stage1_receipt_hashes_match_commitment
stage1_judgement_hashes_match_commitment
stage1_payload_hashes_match_commitment
stage1_live_receipts_not_conflicting
stage2_issuance_bound_to_stage1_snapshot
stage2_submission_receipts_immutable
adjudication_inputs_match_queues
final_records_match_adjudications
complete_input_graph_valid
```

## 9.9 Slice lock

The reviewed-slice lock must bind all immutable receipt and content hashes, not only payload hashes.

It must refuse:

- stale C10;
- changed final records;
- changed exclusion register;
- changed Stage-1 snapshot;
- changed Stage-2 submissions;
- changed adjudications;
- changed assignments;
- changed declarations;
- changed qualification receipts;
- changed package hashes;
- changed freeze or source commit.

## 9.10 Execution authorization

Before authorization, reverify the entire immutable chain.

Execution authorization must fail if any upstream artifact has changed after lock, including non-gating reviewer notes if those notes were part of the committed receipt.

No shortcut may trust only the slice-lock’s `locked: true` field.

---

# 10. Phase 5 — Apply the Same Immutability Invariant to Every Receipt Chain

Do not stop after fixing Stage 1.

Perform a systematic time-of-check/time-of-use and replacement audit over:

```text
assignment registry
reviewer declaration receipts
qualification receipts
Stage-1 submissions
Stage-1 commitment
Stage-2 unlock
Stage-2 issuance
Stage-2 submissions
Stage-1 disagreement queue
Stage-2 disagreement queue
Stage-1 adjudicator package
Stage-2 adjudicator package
Stage-1 adjudication
Stage-2 adjudication
final adjudicated records
agreement report
C10 report
exclusion register
reviewed-slice lock
execution authorization
external attestation
scientific freeze
```

For every artifact, answer and enforce:

1. What exact bytes or canonical semantic content are frozen?
2. Which upstream hashes does it bind?
3. Which downstream artifacts consume it?
4. Does each downstream consumer reverify those hashes?
5. Can a coordinator replace and reseal it after commitment?
6. Can a valid receipt from another reviewer, stage, packet, namespace, or workspace be replayed?
7. Can an old receipt from the same reviewer be replayed?
8. Can a fixture receipt be copied into a production workspace?
9. Can a production receipt be used under a different packet?
10. Can content change while a stored payload-hash field stays unchanged?
11. Can notes, confidence, applicability, exclusions, or N/A values change without detection?
12. Can the assignment registry change after reviewers are committed?
13. Can adjudication be changed after final-record construction?
14. Can final records change after C10?
15. Can C10 change after slice lock?
16. Can a slice lock be copied to another workspace?
17. Can execution authorization be copied or replayed?
18. Can symlink or path-replacement behavior redirect a read?
19. Can partial writes or crash interruption produce an apparently valid state?
20. Are all state transitions one-way and idempotent?

Repair every confirmed issue in this class.

---

# 11. Phase 6 — Add Immutable Stage-2 and Adjudication Snapshots Where Needed

If Stage-2 submissions, queues, or adjudications are currently read from mutable current paths after their own commitment point, apply the same snapshot architecture.

At minimum:

## 11.1 Stage-2 committed submissions

Once both Stage-2 submissions are accepted and before disagreement generation:

- create an immutable Stage-2 submission snapshot;
- bind payload, sealed receipt, and canonical judgment hashes;
- bind both Stage-2 issuance receipts;
- refuse overwrite;
- make downstream Stage-2 agreement and adjudication read only the snapshot.

## 11.2 Disagreement queues

Once generated:

- make each queue content-addressed;
- bind the exact immutable reviewer inputs;
- refuse adjudication against a different queue;
- refuse queue regeneration after adjudication without a new version.

## 11.3 Adjudications

Once accepted:

- bind exact queue hash;
- bind exact adjudicator package hash;
- bind role assignment and declaration;
- bind every disputed item and final value;
- bind rationale and evidence reference;
- refuse post-finalization replacement;
- make final records read immutable adjudication snapshots.

## 11.4 Final records

Once built:

- content-address and freeze;
- refuse silent regeneration from changed inputs;
- require a new explicit workflow version if scientific inputs change.

Use the minimum new mechanism necessary. Prefer one reusable snapshot helper over multiple bespoke implementations.

---

# 12. Phase 7 — Receipt and Filesystem Hardening

## 12.1 Atomic writes

Update receipt writing so that critical files are written by:

1. writing a temporary file in the same directory;
2. flushing;
3. fsyncing where supported;
4. setting permissions;
5. atomic replacement only when replacement is explicitly allowed;
6. directory fsync where supported.

For immutable artifacts, replacement is never allowed.

## 12.2 Symlink and path defense

Before reading or writing critical private artifacts:

- reject symbolic links;
- reject paths escaping the private root;
- reject unexpected hard-link counts where practical;
- use resolved paths and confirm containment;
- reject world-readable or group-readable production private files;
- reject world-writable parent directories.

Do not make the code unportable; use capability-aware checks and document platform limitations.

## 12.3 One-way state transitions

Enforce:

```text
assignment
→ declarations
→ qualification
→ Stage-1 submissions
→ Stage-1 immutable commitment
→ Stage-2 unlock
→ Stage-2 issuance
→ Stage-2 submissions
→ Stage-2 immutable commitment
→ queues
→ adjudications
→ final records
→ C10
→ exclusion register
→ slice lock
→ execution authorization
```

A completed state must not be overwritten in place.

Corrections require:

- explicit correction receipt;
- superseding workflow version;
- preserved prior record;
- reason;
- coordinator signature;
- re-execution of every affected downstream gate.

For pre-review readiness, it is acceptable to reject corrections entirely and require a fresh workspace.

---

# 13. Phase 8 — Schema and Compatibility Policy

Increment the active workflow and receipt schemas.

Suggested examples:

```text
cab_review_ready_v2_two_stage_workflow_v3
cab_stage1_commitment_v3
cab_committed_stage1_snapshot_v1
cab_committed_stage2_snapshot_v1
cab_review_input_graph_v1
```

Use names consistent with the repository’s existing conventions.

Requirements:

- old commitment schemas are rejected by active workflow gates;
- no silent in-place migration of scientific review evidence;
- fixture builders are updated to the active schema;
- retired schema versions are listed and tested;
- documentation clearly states that prior fixture receipts are development-only;
- genuine review must start only under the new schema.

Do not invalidate the scientific task packet merely because workflow receipt schemas change.

---

# 14. Phase 9 — Mandatory Hostile Regression Suite

Create a dedicated test file, preferably:

```text
tests/test_final_integrity_closure.py
```

Also update relevant existing tests.

The hostile suite must exercise the actual public APIs and workflow, not private implementation shortcuts.

## 14.1 Stage-1 post-commit replacement attacks

After Stage-1 commitment, attempt each attack independently:

1. modify reviewer notes and reseal;
2. modify reviewer confidence and reseal;
3. modify a non-gating judgment and reseal;
4. modify a gating judgment and reseal;
5. add a row;
6. remove a row;
7. reorder rows where order should not matter;
8. duplicate an item ID;
9. change reviewer role;
10. change pseudonym binding;
11. change Stage-1 package hash;
12. change declaration hash;
13. change qualification hash;
14. change validation results;
15. change row count;
16. preserve old `submission_sha256` while changing parsed content;
17. preserve old parsed content while changing receipt envelope;
18. replace Reviewer A receipt with Reviewer B receipt;
19. replay an older valid receipt;
20. copy a valid receipt from another workspace;
21. copy a fixture receipt into production verification;
22. replace the immutable snapshot file;
23. replace the snapshot manifest;
24. delete a snapshot file;
25. create a conflicting live receipt after commitment.

For every attack, assert failure at all applicable gates:

```text
Stage-2 unlock
Stage-2 issuance
Stage-2 ingestion
pairing
Stage-1 queue generation
agreement
adjudicator package generation
final records
C10
exclusion register
slice lock
execution authorization
```

## 14.2 Stage-2 attacks

Attempt:

- issuance swap;
- archive swap;
- namespace swap;
- reviewer swap;
- stale Stage-1 commitment;
- changed Stage-1 snapshot;
- altered Stage-2 judgment;
- altered applicability;
- altered N/A value;
- altered package hash;
- replayed issuance;
- copied issuance receipt;
- altered Stage-2 receipt with retained payload hash;
- Stage-2 submission replacement after queue generation.

Every affected downstream gate must fail.

## 14.3 Adjudication attacks

Attempt:

- adjudication against wrong queue;
- changed disputed-item set;
- omitted disputed item;
- extra item;
- changed final value;
- changed exclusion decision;
- changed rationale;
- changed evidence reference;
- wrong adjudicator;
- reviewer acting as adjudicator;
- copied adjudication from another workspace;
- post-final-record adjudication replacement.

Every affected downstream gate must fail.

## 14.4 Final-record, C10, and lock attacks

Attempt:

- final-record replacement;
- stale agreement report;
- changed included-pair list;
- changed excluded-pair reason;
- C10 report copied from another workspace;
- C10 report changed after lock;
- exclusion-register replacement;
- slice-lock replacement;
- source-commit mismatch;
- freeze mismatch;
- packet mismatch;
- execution authorization replay.

Every attack must fail closed.

## 14.5 Positive tests

Also prove:

- a normal fixture workflow still reaches `C10_MECHANICS_PASS`;
- a fixture never reaches genuine `C10_PASS`;
- production-origin requirements remain enforced;
- the committed snapshot can be reverified from a fresh process;
- deterministic inputs produce deterministic manifests and digests;
- scientific-kernel hashes remain unchanged;
- active private material remains untracked;
- Reviewer A and Reviewer B packages remain role-isolated.

---

# 15. Phase 10 — Independent Hostile Audit Script

Add a standalone provider-free audit script, preferably:

```text
scripts/audit_final_review_integrity.py
```

It must:

- create isolated temporary fixture workspaces;
- run the legitimate workflow;
- execute the hostile mutation matrix;
- print only non-sensitive identifiers and hashes;
- produce machine-readable and human-readable reports;
- exit nonzero on any false acceptance;
- avoid importing test-only monkeypatches;
- use the same public workflow APIs a real coordinator uses.

Outputs:

```text
reports/final_integrity_closure/HOSTILE_INTEGRITY_AUDIT.json
reports/final_integrity_closure/HOSTILE_INTEGRITY_AUDIT.md
```

The report must distinguish:

```text
attack attempted
expected rejection stage
actual rejection stage
pass/fail
affected receipt chain
fixture-only or production-invariant
```

A final “PASS” requires every attack to be rejected no later than the first gate that consumes the changed artifact.

---

# 16. Phase 11 — Status, Documentation, and Operational Runbooks

Update the canonical active status documents.

Find the repository’s authoritative current-state document and ensure there is only one active source of truth.

It must state:

```text
CAB_READY_FOR_GENUINE_REVIEWER_DISTRIBUTION
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
```

It must not state:

```text
submission ready
paper ready
empirical evidence complete
C10 passed
model execution approved
Level 5 complete
Level 6 complete
```

## 16.1 Required documentation updates

Update or create:

```text
docs/reviewer_ready_v2/IMMUTABLE_REVIEW_CHAIN.md
docs/reviewer_ready_v2/COORDINATOR_RUNBOOK.md
docs/reviewer_ready_v2/RECOVERY_AND_CORRECTION_POLICY.md
reports/final_integrity_closure/FINAL_INTEGRITY_CLOSURE_REPORT.md
reports/final_integrity_closure/FINAL_INTEGRITY_CLOSURE_REPORT.json
```

Document:

- the difference between payload, sealed-receipt, and canonical-content hashes;
- snapshot creation;
- snapshot verification;
- immutable state transitions;
- correction policy;
- Stage-2 unlock requirements;
- adjudication binding;
- C10 input graph;
- slice-lock input graph;
- exact next commands for genuine onboarding;
- prohibited actions;
- private-material handling;
- backup requirements.

## 16.2 Reviewer distribution instructions

The final runbook must name the exact active role-specific files to send.

It must explicitly prohibit sending:

- full repository;
- full ZIP;
- `private_data`;
- qualification source;
- qualification answer vault;
- Stage-2 plaintext;
- Stage-2 key;
- private mappings;
- retired packages;
- old qualification versions;
- source code containing private material.

It must require independent hash verification before distribution.

---

# 17. Phase 12 — Scientific Freeze and Provenance Refresh

Do not attempt an impossible self-referential Git commit hash.

Use a two-step provenance design consistent with CAB’s existing freeze architecture.

## 17.1 Repair source commit

After code, tests, and documentation are complete:

1. commit the repair source and tests as commit A;
2. record commit A as the frozen source commit;
3. ensure commit A is reachable from the final publication commit.

## 17.2 Generated freeze and release commit

Generate:

- refreshed scientific freeze;
- refreshed public packet commitment if workflow metadata requires it;
- refreshed release inventory;
- refreshed reproducibility reports;
- refreshed status reports.

Scientific task-content hashes must remain unchanged.

Commit generated tracked artifacts as commit B.

## 17.3 External exact-tip attestation

After final commit B:

- create an external attestation outside Git;
- bind:
  - final exact commit B;
  - frozen source commit A;
  - scientific-freeze hash;
  - package hashes;
  - vault hashes;
  - wheel hash;
  - normalized sdist hash;
  - hostile-audit report hash;
  - full validation report hash;
- store it under the existing protected attestation convention, such as:

```text
~/.cab/attestations/
```

Do not place private keys in the repository.

Verify from a fresh clone that:

- commit A is reachable from commit B;
- frozen source files at A match the freeze;
- generated artifacts at B match their recorded hashes;
- the external attestation verifies B.

---

# 18. Phase 13 — Full Validation

Run all relevant checks.

## 18.1 Focused tests

Run at least:

```text
tests/test_final_integrity_closure.py
tests/test_reviewer_distribution_patch.py
tests/test_review_workflow_integrity.py
tests/test_review_ready_v2.py
tests/test_review_ready_v2_freeze.py
tests/test_review_ready_v2_fixture_e2e.py
```

Include any renamed or successor files.

If `pytest-xdist` is unavailable and `pyproject.toml` contains `-n auto`, either install the locked development dependency or run with a documented local override such as:

```bash
pytest -o addopts='' ...
```

Do not misreport a missing optional local plugin as a test failure.

## 18.2 Full provider-free suite

Run the complete provider-free test suite.

Provider tests must remain skipped or mocked unless a real key is explicitly and safely provided. Do not make a provider call as part of this repair.

## 18.3 Static and policy checks

Run:

- Ruff;
- mypy;
- Codespell;
- strict docs checks;
- security checks;
- private-material tracking scan;
- secret scan;
- structured-data validation;
- active-path registry validation;
- retired-version validation;
- evidence-safety validation;
- claim-ledger validation.

## 18.4 Packaging and reproducibility

Run:

- wheel build;
- sdist build;
- second clean build;
- deterministic hash comparison or normalized-sdist comparison;
- `twine check`;
- SBOM/provenance generation if already part of CAB;
- release inventory validation.

## 18.5 Fresh-clone verification

Clone the final branch into a fresh path.

Without copying untracked repository files:

- install;
- run focused tests;
- verify the freeze;
- verify release hashes;
- verify no private data are tracked;
- verify old commitment schemas are rejected;
- verify the hostile audit;
- verify status documents;
- verify exact-tip external attestation.

Private-package verification may use hashes and externally supplied protected paths, not Git-tracked private bodies.

---

# 19. Phase 14 — Clean Git Publication

Before finalizing:

```bash
git status --short --branch
git diff --check
git ls-files private_data
git ls-files | grep -Ei '(key|secret|answer.*vault|stage2.*plain|reviewer.*identity)'
```

The expected private-data tracking result is empty.

Commit logically, for example:

```text
repair: freeze immutable Stage-1 review evidence
test: close post-commit receipt replacement attacks
release: refresh CAB reviewer-readiness provenance
```

A different clean commit structure is acceptable.

Push to:

```text
origin/main
```

Then verify:

```text
HEAD == origin/main
worktree clean
no untracked operational prompt
all required reports present
external attestation backed up
```

Do not stop after editing files.

Do not leave commits unpushed.

---

# 20. Final Deliverables

Produce:

```text
reports/final_integrity_closure/BASELINE_REPOSITORY_STATE.md
reports/final_integrity_closure/BASELINE_REPOSITORY_STATE.json
reports/final_integrity_closure/SCIENTIFIC_KERNEL_PRESERVATION_BASELINE.json
reports/final_integrity_closure/HOSTILE_INTEGRITY_AUDIT.md
reports/final_integrity_closure/HOSTILE_INTEGRITY_AUDIT.json
reports/final_integrity_closure/SCIENTIFIC_KERNEL_PRESERVATION_FINAL.json
reports/final_integrity_closure/FULL_VALIDATION_REPORT.md
reports/final_integrity_closure/FULL_VALIDATION_REPORT.json
reports/final_integrity_closure/FRESH_CLONE_VERIFICATION.md
reports/final_integrity_closure/FRESH_CLONE_VERIFICATION.json
reports/final_integrity_closure/FINAL_INTEGRITY_CLOSURE_REPORT.md
reports/final_integrity_closure/FINAL_INTEGRITY_CLOSURE_REPORT.json
docs/reviewer_ready_v2/IMMUTABLE_REVIEW_CHAIN.md
docs/reviewer_ready_v2/COORDINATOR_RUNBOOK.md
docs/reviewer_ready_v2/RECOVERY_AND_CORRECTION_POLICY.md
```

Also produce or refresh:

- active scientific freeze;
- public packet commitment;
- release inventory;
- reproducible package hashes;
- external exact-tip attestation;
- canonical current-project status;
- exact reviewer-onboarding command sequence.

---

# 21. Hard Acceptance Criteria

The pass is successful only if all of the following are true.

## 21.1 Known exploit closure

- The exact independently reproduced post-commit mutation attack fails.
- A changed Stage-1 receipt cannot be consumed after commitment.
- Retaining the old CSV `submission_sha256` cannot hide changed parsed content.
- A resealed replacement receipt cannot preserve downstream mechanics success.
- C10 mechanics fail under any committed-input mutation.

## 21.2 Complete chain binding

- Stage-1 commitment binds payload, sealed receipt, and canonical judgments.
- Stage-2 unlock verifies the immutable Stage-1 snapshot.
- Stage-2 issuance binds the immutable Stage-1 snapshot.
- Stage-2 submissions are immutable before adjudication.
- Queues bind exact immutable reviewer inputs.
- Adjudications bind exact queues and packages.
- Final records bind exact adjudications and immutable submissions.
- C10 binds and verifies the complete input graph.
- Slice lock binds and verifies the complete C10 input graph.
- Execution authorization revalidates the locked chain.

## 21.3 Hostile tests

- Every required hostile attack is implemented.
- Every attack is rejected.
- No test merely checks that a field exists.
- Tests mutate actual sealed artifacts and exercise real downstream APIs.
- Positive fixture E2E still works.
- Fixture artifacts never become genuine evidence.

## 21.4 Preservation

- All active pair-content hashes are unchanged.
- Stage-1 reviewer package hashes are unchanged unless an unavoidable defect is documented.
- Qualification privacy remains intact.
- Stage-2 remains private.
- No private material is tracked.
- No genuine evidence is fabricated.

## 21.5 Repository and release

- Full provider-free suite passes.
- Static, security, docs, structured-data, and claim checks pass.
- Reproducible build passes.
- Fresh-clone verification passes.
- Worktree is clean.
- HEAD equals origin/main.
- External exact-tip attestation exists and is backed up.

## 21.6 Honest state

- C10 remains pending because genuine review has not occurred.
- Model execution remains blocked.
- Genuine evidence counters remain zero.
- No paper-readiness or submission-readiness claim is emitted.

---

# 22. Required Final Report Structure

The final response and tracked final report must contain:

## 22.1 Executive result

One of:

```text
CAB_FINAL_INTEGRITY_CLOSURE_COMPLETE
```

or:

```text
CAB_FINAL_INTEGRITY_CLOSURE_BLOCKED
```

If blocked, name every blocker. Do not soften the status.

## 22.2 Repository identity

- starting commit;
- repair source commit;
- final publication commit;
- branch;
- remote;
- push state;
- worktree state.

## 22.3 Files changed

Group by:

- integrity primitives;
- workflow integration;
- hostile tests;
- documentation;
- freeze and release;
- status cleanup.

## 22.4 Confirmed exploit result

Show:

```text
before repair
after repair
first gate rejecting the attack
all downstream gates protected
```

Do not include private content.

## 22.5 Adjacent-chain audit

For each receipt chain:

```text
artifact
commitment point
immutable digest
downstream verifier
hostile attacks
result
```

## 22.6 Preservation report

Show old and new hashes for all preserved scientific surfaces.

## 22.7 Validation

Include exact:

- test counts;
- skips and reasons;
- lint result;
- type-check result;
- docs result;
- security result;
- package hashes;
- fresh-clone result;
- hostile-audit count.

## 22.8 Current scientific state

Explicitly report:

```text
genuine human judgments: 0
genuine adjudications: 0
genuine model trajectories: 0
paper-eligible empirical assets: 0
supported empirical claims: 0
C10: pending genuine review
model execution: blocked
```

## 22.9 Exact next action

End with:

> Recruit two independent reviewers and one separate adjudicator; create production assignments and declarations; run private qualification V4; distribute only the role-specific frozen Stage-1 packages; commit immutable Stage-1 evidence; unlock Stage 2; adjudicate; run C10; lock the reviewed slice; and only then begin the one-task live smoke.

---

# 23. Final Stop Rule

After this integrity-closure pass:

- do not create another broad engineering prompt;
- do not add another maturity level;
- do not redesign the benchmark;
- do not regenerate the active packet casually;
- do not begin model runs before genuine C10 and slice lock.

If every gate passes, freeze the engineering workflow and move to genuine human evidence creation.

The next scientific value must come from:

```text
real reviewer judgments
real adjudication
genuine C10
real model trajectories
human scorer audit
confirmatory analysis
external reproduction
```

Not from another scaffold expansion.
