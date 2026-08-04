# Phase 12 — Live Calibration and Compact-20 Execution

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


## Prerequisites

- genuine Compact C10 pass;
- frozen slice;
- explicit live approval;
- pinned model licences and revisions;
- Kaggle fixture smoke;
- artifact store and registry healthy.

If any prerequisite fails, stop.

## Stage A — One-task calibration

For each candidate model class:

- pin revision;
- verify licence;
- select quantisation;
- measure load time;
- measure peak VRAM;
- measure tokens and latency;
- validate tool adapter;
- validate scorer;
- validate checkpoint/export;
- register measured resource profile.

Do not silently substitute models.

## Stage B — Freeze Compact matrix

Use measured calibration to select:

- 3–4 open models;
- at least two model families;
- standard and RAAC_LIGHT;
- optional RAAC_FULL subset;
- fixed repeats;
- budgets;
- seeds;
- shard plan.

## Stage C — Execute

Use T4×2 deterministic data parallelism.

Requirements:

- registry before launch;
- per-unit checkpoints;
- resumability;
- no duplicate work;
- raw immutable trajectories;
- content-addressed export;
- integrity receipts;
- live logs;
- bounded retries.

## Stage D — CPU audit

- merge;
- integrity verification;
- score;
- blind scorer audit;
- hidden-label audit;
- paired analysis;
- RAAC overhead;
- failure taxonomy;
- missingness;
- preliminary claim ledger.

## Decision Gate

Decide prospectively whether to:

- proceed to Scale;
- repair and rerun a new version;
- reduce panel;
- report informative null;
- stop the thesis.

## Outputs

- measured runtime report;
- audited Compact evidence bundle;
- scorer audit;
- preliminary analysis;
- Scale readiness decision;
- registry and evidence graph updates.

## Acceptance State

`COMPACT20_AUDITED_REAL_EVIDENCE_READY`

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


Preferred public-safe commit:

```bash
git commit -m "Record audited CAB Compact-20 pilot"
```

Never commit protected raw trajectories or private task payloads.
