# CAB Final Reviewer-Distribution Patch — Claude New Session

Repository:

```text
/Users/saketmaganti/Projects/causal-agent-bench
```

Expected current branch/commit:

```text
main
ab16089848c9dc30bbe597704cfe79e164cdb0b2
```

Treat the repository and this prompt as the only sources of truth. Do not rely on earlier completion reports.

## Mission

Perform one final surgical patch so CAB is genuinely safe to distribute to real human reviewers.

Preserve the existing `compact20-review-ready-v2` scientific kernel and Stage-1 packages unless a confirmed defect requires regeneration.

Do not:

- redesign the 20 scientific pairs;
- run models;
- perform or fabricate human review;
- generate C10 PASS;
- authorize model execution;
- add new maturity layers;
- make broad unrelated refactors.

Final honest state must be:

```text
CAB_FINAL_REVIEWER_DISTRIBUTION_PATCH_COMPLETE
CAB_SCIENTIFIC_KERNEL_V2_PRESERVED
CAB_QUALIFICATION_V4_PRIVATE
CAB_STAGE1_ADJUDICATION_PACKAGE_VALID
CAB_STAGE2_ADJUDICATION_PACKAGE_VALID
CAB_STAGE2_ISSUANCE_BOUND
CAB_FREEZE_AND_ATTESTATION_REFRESHED
CAB_REPOSITORY_CLEAN
CAB_READY_FOR_GENUINE_REVIEWER_ONBOARDING
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
```

Only print these if every gate passes.

---

# Confirmed Remaining Defects

## 1. Active qualification is reconstructible

Tracked source still reveals the private qualification design indirectly through:

- defect templates;
- how each defect modifies an item;
- the decisive dimension;
- expected value mapping.

A reviewer can classify the generated qualification item and reconstruct its answer using public source.

### Fix

Retire `cab_qualification_v3`.

Create `cab_qualification_v4` where tracked code contains only:

- schemas;
- generic private-item loading;
- generic package generation;
- generic encryption/decryption;
- generic scoring against private answer material.

Move all of the following outside Git:

- qualification item bodies;
- defect templates;
- generation parameters;
- decisive dimensions;
- expected answers;
- explanations;
- answer mappings.

Use ignored private storage, for example:

```text
private_data/human_review/compact20-review-ready-v2/qualification_v4/
```

Use existing external key infrastructure or:

```text
CAB_QUALIFICATION_KEY_PATH
```

Generate reviewer-specific packages and an encrypted private answer vault.

Tracked reports may contain only safe hashes, versions, schemas, and retirement state.

Add hostile tests proving that the active V4 qualification answers cannot be reconstructed from:

```text
tracked repository
+ reviewer qualification ZIP
```

At minimum, ensure no tracked source contains private item-generation templates or defect-to-answer mappings.

The 20 scientific pairs and Stage-1 packages must remain unchanged.

---

## 2. Adjudicator packages lack scientific evidence

Current adjudication data contains disputes but not enough evidence to decide them.

### Fix

Generate two disputed-items-only packages:

```text
stage1_adjudicator_package.zip
stage2_adjudicator_package.zip
```

### Stage-1 adjudicator package must include, only for disputed items:

- clean and intervention task context;
- primitive evidence;
- controlled intervention diff;
- intended changed factor;
- preserved invariants;
- declared tool capabilities;
- both reviewers’ values, confidence, and notes;
- structured adjudication form.

It must hide Stage-2 gold/scorer material.

### Stage-2 adjudicator package must include, only for disputed items:

- relevant private gold/policy;
- accepted variants;
- answer/scorer contracts;
- applicability map;
- recovery/abstention/clarification policy where applicable;
- both reviewers’ values, confidence, and notes;
- structured adjudication form.

It must not expose unrelated non-disputed items.

Bind each adjudicator package to:

```text
packet commitment
review stage
disagreement queue hash
included disputed item IDs
adjudicator assignment
freeze hash
exact commit
package hash
```

Add tests proving:

- only disputed items are included;
- Stage 1 contains no Stage-2 leakage;
- Stage 2 contains required private evidence;
- adjudication cannot be ingested from a stale or different package;
- adjudicator role cannot overlap with Reviewer A or B.

---

## 3. Stage-2 package issuance is not permanently bound

Stage-2 ZIP hashes are generated but not bound through the workflow.

### Fix

When Stage-2 packages are generated, create a coordinator-sealed issuance receipt for each reviewer containing:

```text
reviewer pseudonym hash
canonical reviewer role
Stage-1 commitment hash
Stage-2 package hash
opaque-ID namespace
packet commitment
qualification receipt hash
reviewer declaration hash
scientific freeze hash
exact Git commit
issued_at
```

Stage-2 ingestion must require and validate the exact issuance receipt and package hash.

Bind Stage-2 issuance receipts into:

- Stage-2 submission receipts;
- disagreement queues;
- adjudication packages;
- final adjudicated records;
- C10;
- slice lock;
- execution authorization.

Add hostile tests for:

- modified Stage-2 ZIP;
- package swap;
- stale issuance receipt;
- copied receipt;
- wrong reviewer;
- wrong namespace;
- wrong Stage-1 commitment;
- wrong freeze or commit.

All must fail closed.

---

# Documentation Corrections

Update qualification instructions so they accurately describe scoring.

Do not say:

```text
Every dimension is scored.
```

unless every dimension truly is scored.

Use accurate language such as:

```text
Complete every requested field. Qualification scoring uses hidden predefined criteria and may weigh selected dimensions.
```

Do not claim qualification domains are entirely disjoint from the benchmark unless verified.

Prefer:

```text
Qualification uses separate tasks, records, identifiers, and item content from the final review set.
```

Update only the canonical files:

```text
README.md
CURRENT_PROJECT_STATE.md
docs/HUMAN_REVIEW_READY_V2_RUNBOOK.md
docs/STAGE1_REVIEWER_INSTRUCTIONS_V2.md
docs/STAGE2_COORDINATOR_RUNBOOK_V2.md
```

---

# Hash and Attestation Reconciliation

Do not trust prior textual summaries.

Derive all final values from the actual repository and private artifacts.

Verify and report:

```text
public packet commitment
Stage-1 Reviewer A hash
Stage-1 Reviewer B hash
qualification V4 package hashes
Stage-2 vault hash
Stage-2 issuance receipt hashes
Stage-1 adjudicator package hash if generated
Stage-2 adjudicator package hash if generated
scientific freeze hash
wheel hash
normalized sdist hash
```

Refresh the scientific freeze to bind:

- qualification V4 version and commitments;
- adjudication package schemas;
- Stage-2 issuance schema;
- active path registry;
- exact reachable commit;
- preserved scientific packet commitment.

Create a new external exact-commit attestation and verify it using the canonical CLI.

Ensure generator provenance still verifies from a branch-only fresh clone after unreachable objects are pruned.

---

# Required Regression Tests

Add focused tests for:

1. V3 qualification is retired and rejected.
2. V4 answers cannot be recovered from tracked source.
3. Qualification packages contain no answer key.
4. Stage-1 adjudicator package includes only disputed items.
5. Stage-1 adjudicator package has no Stage-2 leakage.
6. Stage-2 adjudicator package includes required private evidence.
7. Stale adjudicator package is rejected.
8. Modified Stage-2 package is rejected.
9. Reviewer package swap is rejected.
10. Missing or stale Stage-2 issuance receipt is rejected.
11. Stage-2 issuance is bound into C10 and slice lock.
12. Existing false-C10 exploit remains closed.
13. Scientific pair hashes and Stage-1 package hashes remain unchanged.
14. Freeze verifies in a single-branch fresh clone.
15. No private qualification or reviewer material is tracked.

---

# Validation

Run:

```text
focused new regression tests
existing workflow-integrity tests
full provider-free pytest suite
ruff
mypy
codespell
docs-strict
security-check
secret scan
structured-data checks
release-check
wheel/sdist double-build reproducibility
twine check
branch-only fresh-clone freeze verification
external attestation verification
git status --porcelain
```

Do not claim completion if any required validation is skipped, truncated, or unavailable.

---

# Commit and Push

Create logical commits, preferably:

1. private qualification V4;
2. adjudicator packages and Stage-2 issuance binding;
3. docs, freeze, tests, release.

Then:

- verify no private files are tracked;
- verify worktree is clean;
- verify push is fast-forward;
- push to `origin/main`;
- do not force-push.

Stop if the remote diverged.

---

# Final Report

Report only safe metadata:

```text
final commit
push status
clean worktree
scientific pair preservation result
public packet commitment
Stage-1 A/B hashes
qualification V4 hashes
retired qualification versions
Stage-2 vault hash
Stage-2 issuance receipt schema/version
adjudicator package hashes or generation-ready status
scientific freeze hash
fresh-clone provenance result
external attestation path
wheel/sdist hashes
test counts
quality-gate results
genuine evidence counters
exact next human action
```

Never print qualification answers, private candidate content, reviewer identities, keys, or Stage-2 golds.

Exact next action:

```text
Recruit two independent qualified reviewers and one separate adjudicator, create their private assignments and declarations, distribute only their assigned qualification and Stage-1 packages, score qualification privately, and keep Stage 2 locked until both valid Stage-1 submissions are committed.
```

If any required condition fails, report:

```text
CAB_FINAL_REVIEWER_DISTRIBUTION_PATCH_BLOCKED
```

with exact blockers. Do not call partial completion reviewer-ready.
