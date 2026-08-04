# Phase 08 — Evidence Graph, Certification, Model Cards and Evaluation Registry

Recommended effort: **Ultra**

## Verified Starting State

Repository: `Saket-Maganti/cab`  
Local path: `/Users/saketmaganti/Projects/causal-agent-bench`  
Branch: `main`  
Verified starting commit at prompt-pack creation: `bcd8bc49074c67ff1a9858d87143170e3428e228`

The repository currently reports:

- `CAB_ICLR_ULTIMATE_PREEXECUTION_BUILD_COMPLETE`;
- `CAB_CPU_EXECUTION_COMPLETE_WITH_EXPECTED_HUMAN_BLOCK`;
- unified state `HUMAN_VALIDATION_REQUIRED`;
- `build_complete=true`;
- genuine human rows: 0;
- real model trajectories: 0;
- audited real runs: 0;
- paper-eligible empirical assets: 0;
- supported empirical claims: 0;
- provider-free suite: 1,091 passed, 1 skipped;
- all currently legal CPU-only lanes completed;
- nine Kaggle notebooks validated offline;
- direct-to-main publication already established.

Treat the live repository as authoritative if it has advanced beyond this commit.


## Objective

Make every CAB result auditable from raw artifact to public claim.

## 1. Evidence graph

Build on the Phase-01 provenance primitive.

Nodes:

- task version;
- review;
- C10 decision;
- split lock;
- model version;
- policy version;
- run;
- shard;
- raw trajectory;
- score;
- audit;
- analysis;
- figure;
- table;
- claim;
- release.

Edges:

- generated-from;
- scored-by;
- reviewed-by;
- audited-by;
- analysed-by;
- supports;
- invalidates;
- supersedes;
- reproduced-by.

Requirements:

- immutable hashes;
- cycle detection;
- missing-parent rejection;
- public-safe graph export;
- private-node redaction;
- lineage query;
- evidence-class transition validation.

## 2. Certification framework

Define certificates:

- task validity;
- split integrity;
- run integrity;
- scorer audit;
- analysis reproducibility;
- model robustness profile;
- paper-asset eligibility;
- release reproducibility.

Certificates must be machine-readable and human-readable.

A certificate is not a scientific claim by itself.

## 3. Model robustness cards

Template fields:

- model and revision;
- tool adapter;
- policy;
- task versions;
- clean success;
- paired robustness;
- recovery;
- abstention;
- false abstention;
- worst family;
- uncertainty;
- overhead;
- missingness;
- scorer audit;
- limitations;
- evidence status.

Keep result fields blocked until real evidence exists.

## 4. Evaluation registry

Create a local/public-safe registry for evaluated submissions.

Support:

- audited status;
- versioned corrections;
- withdrawals;
- superseding runs;
- comparable-support sets;
- no point leaderboard without uncertainty;
- rank probability;
- family profiles;
- reproducibility status.

## 5. Claim compiler

A claim can be promoted only when its evidence subgraph satisfies the claim ledger.

Add exact diagnostics for missing evidence.

## CLI

```text
cab evidence trace
cab evidence verify
cab certify
cab model-card
cab registry results
cab claims validate
```

## Tests

- invalid transition;
- missing parent;
- redaction;
- superseded score;
- correction;
- withdrawn run;
- claim without support;
- incompatible support;
- tampered certificate;
- deterministic graph export.

## Reports

- `docs/level5/EVIDENCE_GRAPH_SPEC.md`
- `docs/level5/CERTIFICATION_FRAMEWORK.md`
- `docs/level5/EVALUATION_REGISTRY_POLICY.md`
- `reports/level5/PHASE08_FIXTURE_CERTIFICATION.md`
- `reports/level5/PHASE08_HANDOFF.md`

## Acceptance State

`CAB_EVIDENCE_CERTIFICATION_FOUNDATION_READY`

## Global Non-Negotiable Rules

Do not:

- fabricate human judgments, adjudication, trajectories, scores, timings, model results, external replications or user feedback;
- pass C10 using fixtures, AI review, blank rows or proxy review;
- enable real model execution unless the phase explicitly authorises it and every prerequisite passes;
- expose or commit private task text, answers, intervention payloads, reviewer identities or evaluator-only metadata;
- add a parallel replacement for a canonical system that already exists;
- weaken tests or gates merely to make the build pass;
- use benchmark outputs to redesign confirmatory tasks after outcomes are known;
- run Main-scale experiments before Scale and transfer evidence justify expansion;
- use paid APIs unless explicitly authorised;
- force-push, rewrite Git history, create a branch or open a pull request;
- stage unrelated user-owned work;
- claim Level 5 merely because code exists.

Always:

- inspect before building;
- extend canonical modules;
- use typed schemas and explicit states;
- fail closed;
- preserve raw evidence outside Git;
- use content hashes and immutable provenance;
- separate `DESIGN_ONLY`, `ENGINEERING_ONLY`, `FIXTURE_ONLY`, `HUMAN_INPUT_REQUIRED`, `PRELIMINARY_REAL_EVIDENCE`, `AUDITED_REAL_EVIDENCE` and `PAPER_ELIGIBLE_EVIDENCE`;
- add focused tests before broad validation;
- keep a live ledger and resumable handoff;
- measure actual runtime when executing and label projections honestly;
- push only public-safe, intentional changes.

## Git Publication Contract

At the beginning:

```bash
cd /Users/saketmaganti/Projects/causal-agent-bench
git status --short
git status --branch --short
git branch --show-current
git rev-parse HEAD
git remote -v
git fetch origin main
git rev-list --left-right --count origin/main...main
```

Remain on `main`. Preserve every pre-existing user-owned tracked or untracked path.

Before commit:

```bash
git diff --check
git status --short
git diff --stat
git diff
```

Stage explicit task-owned paths only. Never blindly stage a mixed worktree.

Push:

```bash
git push origin main
```

Never force-push.

Verify:

```bash
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
test "$LOCAL_HEAD" = "$REMOTE_HEAD"
```

Observe remote CI with a bounded wait. Fix deterministic repository defects, but do not change external repository settings without authorisation.


Preferred commit:

```bash
git commit -m "Add CAB evidence graph and certification framework"
```
