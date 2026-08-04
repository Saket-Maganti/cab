# Phase 13 — Scale-100, RAAC Mechanism Study and Naturalistic Transfer

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

- audited Compact evidence;
- Scale and naturalistic genuine human review;
- C10 and frozen manifests;
- frozen power/allocation plan;
- measured resource model;
- explicit live approval.

## Study 1 — Scale-100 controlled evaluation

Target:

- strongest 80–100 valid base tasks;
- 5-model open core where feasible;
- at least three model families;
- standard and locked RAAC policy;
- fixed repeats;
- equal-budget primary comparison;
- practical-budget secondary comparison.

Monitor:

- common support;
- missingness;
- family balance;
- clean-success denominators;
- checkpoint integrity;
- overhead.

## Study 2 — RAAC mechanism

Use a prospectively selected model/task subset.

Policies:

- RAAC_LIGHT;
- RAAC_FULL;
- VERIFY_ONLY;
- RETRY_ONLY;
- ABSTAIN_ONLY;
- NO_CROSS_CHECK;
- NO_ALTERNATE_ROUTE;
- NO_FINAL_VERIFY.

Measure:

- recovery;
- clean-path parity;
- false abstention;
- extra model/tool calls;
- tokens;
- wall time;
- cost-normalised efficiency.

## Study 3 — Naturalistic transfer

Use 50–100 reviewed workflows and a representative model subset.

Test whether naturalistic failure is predicted by:

- clean success;
- ACRS;
- clean-conditioned robustness;
- recovery;
- abstention;
- worst-family robustness;
- full profile.

Run uncertainty, calibration, regression and leave-family-out analyses.

## Audit

- immutable raw evidence;
- deterministic merge;
- scorer audit;
- sensitivity to exclusion;
- alternative scoring;
- missingness;
- rank probabilities;
- no task replacement based on outcomes.

## Outputs

- controlled confirmatory bundle;
- RAAC mechanism bundle;
- transfer bundle;
- model robustness cards;
- evidence graph;
- claim eligibility report;
- Main-expansion decision.

## Acceptance State

`CAB_LEVEL4_AUDITED_CONFIRMATORY_EVIDENCE_READY`

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
git commit -m "Record CAB confirmatory and transfer evidence"
```
