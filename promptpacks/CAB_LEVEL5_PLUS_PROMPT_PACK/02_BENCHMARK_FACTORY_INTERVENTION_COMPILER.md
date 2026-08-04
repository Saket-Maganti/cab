# Phase 02 — Benchmark Factory and Intervention Compiler

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

Turn CAB from a fixed benchmark repository into a governed benchmark-authoring system.

Build a benchmark factory that can author, compile, validate, review, version and retire intervention-based evaluations.

## Core Components

### 1. Authoring DSL

Define typed specifications for:

- base task;
- tool environment;
- answer contract;
- gold source;
- intervention;
- invariance contract;
- manipulation check;
- solvability contract;
- expected opportunity;
- scorer binding;
- provenance;
- licence;
- privacy class;
- split role.

Support JSON/YAML authoring and Python builders.

### 2. Intervention compiler

Compile a base task and intervention specification into candidate instances.

Requirements:

- deterministic IDs and hashes;
- canonical family taxonomy;
- legal family parameters;
- invariance validation;
- manipulation-check generation;
- answer-contract compatibility;
- hidden-field separation;
- public/private output separation;
- compilation receipt;
- reversible build metadata without revealing protected content.

The compiler must reject:

- intervention changing the target answer without contract;
- multiple uncontrolled mechanisms;
- missing manipulation check;
- invalid tool schema;
- public answer leakage;
- role collision;
- contaminated source reuse.

### 3. Quality and diversity engine

Implement:

- exact duplicate checks;
- normalised duplicate checks;
- structural fingerprints;
- lexical similarity;
- optional offline semantic plugin;
- answer overlap;
- template concentration;
- domain balance;
- tool-combination balance;
- answer-contract balance;
- difficulty balance;
- intervention-family balance;
- source concentration;
- author concentration.

Do not depend on paid embeddings.

### 4. Data-governance lifecycle

States:

```text
DRAFT
→ STATIC_VALIDATED
→ HUMAN_REVIEW_REQUIRED
→ ADJUDICATION_REQUIRED
→ C10_ELIGIBLE
→ FROZEN
→ ACTIVE
→ DEPRECATED
→ RETIRED
→ CONTAMINATED
```

Create versioned task retirement and contamination rules.

### 5. Human packet integration

Generate:

- blinded review packets;
- manipulation-check views;
- adjudication packets;
- public-safe manifests;
- reviewer workload estimates;
- exact coverage matrices.

No synthetic judgments.

### 6. Factory CLI

Target:

```text
cab benchmark init
cab benchmark compile
cab benchmark validate
cab benchmark diversity
cab benchmark review-packet
cab benchmark freeze
cab benchmark retire
cab benchmark contamination-audit
```

### 7. Public sample benchmark

Create a small fully public fixture benchmark that demonstrates the full authoring workflow without using protected CAB tasks.

## Tests

Include:

- deterministic compilation;
- invalid invariance;
- answer-change rejection;
- hidden-field leakage;
- role collision;
- duplicate detection;
- semantic plugin absence;
- retirement;
- contamination propagation;
- review packet generation;
- public/private split;
- malicious input;
- schema migration.

## Reports

- `docs/level5/BENCHMARK_FACTORY_SPEC.md`
- `docs/level5/INTERVENTION_COMPILER_SPEC.md`
- `docs/level5/TASK_LIFECYCLE_AND_RETIREMENT.md`
- `reports/level5/PHASE02_FACTORY_VALIDATION.md`
- `reports/level5/PHASE02_HANDOFF.md`

## Acceptance State

`CAB_BENCHMARK_FACTORY_READY`

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
git commit -m "Build CAB benchmark factory and intervention compiler"
```
