# Phase 01 — Architecture, Experiment Registry and Hermetic Environments

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

Create the canonical foundation for CAB Research OS:

- architecture and subsystem boundaries;
- Level-5 capability model;
- transactional experiment registry;
- immutable provenance;
- hermetic environments;
- migrations and compatibility contracts.

## Required Work

### 1. Architecture audit and ADRs

Inspect the current repository and create:

- `docs/level5/CAB_RESEARCH_OS_ARCHITECTURE.md`
- `docs/level5/CAB_LEVEL5_CAPABILITY_MATRIX.md`
- `docs/architecture/adr/`

Define bounded contexts:

- scientific kernel;
- benchmark factory;
- human validation;
- experiment registry;
- orchestrator;
- backends;
- artifact store;
- evidence graph;
- evaluator;
- certification;
- public SDK;
- governance.

Document what already exists and what will be extended. Do not duplicate canonical state, scoring, RAAC or safety systems.

### 2. Experiment registry

Implement a storage interface with SQLite as the default.

Canonical entities:

- projects;
- studies;
- preregistrations;
- datasets;
- task versions;
- split versions;
- model versions;
- policy versions;
- scorer versions;
- code revisions;
- run manifests;
- runs;
- shards;
- attempts;
- checkpoints;
- artifacts;
- evidence records;
- audits;
- claims;
- certifications;
- review sessions.

Requirements:

- typed IDs;
- UTC timestamps;
- schema migrations;
- foreign keys;
- immutable fields after freeze;
- idempotent registration;
- transaction safety;
- content hashes;
- append-only event history;
- export to public-safe JSON;
- import and integrity verification;
- no private payload storage inside registry rows.

Build:

- repository interface;
- SQLite implementation;
- in-memory fixture implementation;
- migration CLI;
- query APIs;
- registry doctor command;
- registry backup and restore;
- corruption detection;
- tests for transaction rollback and concurrent access.

### 3. Evidence provenance primitive

Every artifact edge must record:

- parent hashes;
- transformation command;
- code revision;
- environment ID;
- actor class;
- evidence class;
- timestamp;
- output hash.

Do not build the full certification layer yet; establish the primitive.

### 4. Hermetic environments

Add or improve:

- deterministic dependency lock;
- Dockerfile;
- optional Apptainer definition;
- Mac setup;
- Linux setup;
- Kaggle environment export;
- software bill of materials;
- dependency licence report;
- reproducibility metadata.

Use optional extras for heavyweight services.

### 5. CI

Add contract checks for:

- migrations;
- fresh registry creation;
- backup/restore;
- Python version matrix;
- macOS/Linux compatibility where available;
- lockfile consistency;
- SBOM generation;
- no protected payload in images or build context.

## CLI Vertical Slice

Provide:

```text
cab registry init
cab registry doctor
cab registry export
cab registry verify
cab env doctor
```

If the existing CLI architecture differs, integrate rather than replace it.

## Tests

At minimum:

- migration upgrade/downgrade safety;
- immutable freeze;
- idempotency;
- hash mismatch;
- rollback;
- concurrent writer handling;
- public-safe export;
- private-field rejection;
- backup/restore equivalence;
- CLI smoke;
- clean environment metadata.

## Reports

Create:

- `reports/level5/PHASE01_ARCHITECTURE_AUDIT.md`
- `reports/level5/PHASE01_REGISTRY_VALIDATION.json`
- `reports/level5/PHASE01_HERMETIC_ENVIRONMENT_REPORT.md`
- `reports/level5/PHASE01_HANDOFF.md`

## Acceptance State

`CAB_LEVEL5_CORE_REGISTRY_READY`

Do not claim operational live execution.

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
git commit -m "Add CAB Level-5 registry and environment foundation"
```
