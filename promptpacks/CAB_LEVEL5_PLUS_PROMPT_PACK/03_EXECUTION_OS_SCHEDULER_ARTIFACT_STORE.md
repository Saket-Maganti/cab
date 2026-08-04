# Phase 03 — Execution OS, Scheduler, Backends and Artifact Store

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

Build a backend-agnostic, resumable experiment operating system.

Do not run real models in this phase. Use fixture backends.

## 1. Canonical run plan

Create a compiler from study definition to immutable run matrix.

Inputs:

- frozen task/split version;
- model versions;
- policies;
- repeats;
- seed plan;
- budgets;
- scorer version;
- code revision;
- backend constraints.

Outputs:

- run manifest;
- shard plan;
- resource projection;
- dependency graph;
- approval requirements;
- content hashes.

Support dry-run previews and deterministic re-expansion.

## 2. Scheduler

Implement:

- priority queue;
- dependency-aware scheduling;
- concurrency caps;
- per-model limits;
- quota budgets;
- timeout policy;
- retry policy;
- resume policy;
- backoff;
- cancellation;
- checkpoint awareness;
- idempotent submission;
- interrupted-run recovery.

Use a local process scheduler as the first real implementation.

Provide interfaces for:

- local CPU fixture;
- local model backend;
- Kaggle export/backend;
- optional provider API;
- future cloud runner.

### 3. Backend contract

Each backend must expose:

- capability discovery;
- resource limits;
- prepare;
- launch;
- poll;
- checkpoint;
- resume;
- cancel;
- collect;
- cleanup;
- provenance.

No backend may silently substitute a model or policy.

### 4. Content-addressed artifact store

Implement local filesystem CAS with:

- SHA-256 addresses;
- immutable objects;
- metadata sidecars;
- atomic writes;
- partial-upload staging;
- integrity verification;
- deduplication;
- compression;
- raw/derived classes;
- retention policy;
- export/import bundles;
- garbage-collection dry run.

Large artifacts stay outside Git. Git stores public-safe hashes and manifests.

### 5. Registry integration

Every scheduling event and artifact must register transactionally.

### 6. CLI

Target:

```text
cab plan
cab run --dry-run
cab run
cab status
cab cancel
cab resume
cab merge
cab artifacts verify
cab artifacts export
cab artifacts gc --dry-run
```

### 7. Fixture vertical slice

Demonstrate:

- 20 fixture units;
- two workers;
- interruption after partial completion;
- resume;
- duplicate submission rejection;
- deterministic merge;
- artifact verification;
- complete registry lineage.

## Tests

Include:

- matrix determinism;
- shard disjointness;
- duplicate work;
- crash before checkpoint;
- crash after checkpoint;
- partial artifact;
- retry exhaustion;
- cancellation;
- quota limit;
- backend mismatch;
- atomic CAS writes;
- corruption;
- registry/CAS consistency;
- deterministic merge.

## Reports

- `docs/level5/EXECUTION_OS_ARCHITECTURE.md`
- `docs/level5/BACKEND_PLUGIN_CONTRACT.md`
- `docs/level5/ARTIFACT_STORE_SPEC.md`
- `reports/level5/PHASE03_END_TO_END_FIXTURE.md`
- `reports/level5/PHASE03_HANDOFF.md`

## Acceptance State

`CAB_EXECUTION_OS_FOUNDATION_READY`

Run the full provider-free suite.

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
git commit -m "Add CAB execution OS and artifact store"
```
