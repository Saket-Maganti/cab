# Phase 04 — Reliability Lab, Observability and Fault Injection

Recommended effort: **XHigh**

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

Prove that CAB recovers from failures without silent data loss or evidence corruption.

## 1. Observability

Implement structured events for:

- planner;
- scheduler;
- backend;
- model adapter;
- RAAC;
- checkpoint;
- artifact store;
- scorer;
- audit;
- analysis;
- evaluator.

Provide:

- JSON logs;
- correlation IDs;
- run/shard/attempt IDs;
- monotonic sequence numbers;
- metrics interface;
- trace export;
- local static run dashboard;
- health and diagnostic summaries;
- privacy redaction.

Do not introduce mandatory external telemetry services.

## 2. Reliability SLOs

Define design SLOs for:

- no silent data loss;
- duplicate prevention;
- checkpoint recovery;
- artifact integrity;
- deterministic merge;
- stale-run detection;
- provenance completeness;
- bounded retry;
- fail-closed security.

Mark SLOs as unmeasured until real execution.

## 3. Fault-injection framework

Create deterministic injections for:

- worker process kill;
- timeout;
- disk-full simulation;
- permission failure;
- corrupt checkpoint;
- corrupt artifact;
- duplicate shard;
- partial upload;
- network disconnect fixture;
- malformed model output;
- invalid schema;
- scorer crash;
- registry lock/contention;
- stale heartbeat;
- model OOM signal;
- quota exhaustion;
- clock skew fixture;
- unexpected reboot marker.

## 4. Recovery invariants

Verify:

- no completed unit reruns without explicit reason;
- no missing unit silently disappears;
- corrupted artifacts never become evidence;
- resumes use identical manifests;
- retry attempts remain linked;
- changed model/config creates a new run identity;
- raw outputs remain immutable;
- derived outputs are reproducible.

## 5. Chaos campaign

Run a fixture campaign across a matrix of injected failures.

Produce a machine-readable reliability scorecard, but do not call it empirical model evidence.

## 6. CLI

```text
cab reliability inject
cab reliability campaign
cab reliability report
cab doctor
cab diagnose <run-id>
```

## Tests

Property and state-machine tests plus deterministic chaos integration tests.

## Reports

- `docs/level5/RELIABILITY_MODEL.md`
- `docs/level5/OBSERVABILITY_AND_REDACTION.md`
- `reports/level5/PHASE04_CHAOS_CAMPAIGN.json`
- `reports/level5/PHASE04_CHAOS_CAMPAIGN.md`
- `reports/level5/PHASE04_HANDOFF.md`

## Acceptance State

`CAB_RELIABILITY_LAB_READY`

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
git commit -m "Add CAB reliability lab and observability"
```
