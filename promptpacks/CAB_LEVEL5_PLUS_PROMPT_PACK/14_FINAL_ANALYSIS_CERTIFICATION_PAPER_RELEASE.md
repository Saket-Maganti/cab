# Phase 14 — Final Analysis, Independent Certification, Paper and Level-5 Release

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

- audited controlled and transfer evidence;
- selected RAAC mechanism evidence;
- scorer audits;
- independent reproduction attempts;
- protected evaluator pilot;
- community pilot;
- no unresolved critical red-team issue.

## 1. Frozen final analysis

Execute:

- primary paired endpoints;
- clustered/family-stratified bootstrap;
- exact paired tests;
- equivalence;
- multiplicity;
- rank probabilities;
- pairwise superiority;
- model-family interactions;
- missingness;
- scorer sensitivity;
- exclusion sensitivity;
- RAAC trade-off and frontier;
- naturalistic predictive validity;
- calibration;
- measured resource analysis.

No post-hoc endpoint changes without explicit exploratory labelling.

## 2. Evidence promotion

Promote only claims whose evidence subgraphs satisfy the claim ledger.

Generate final model cards and certificates.

## 3. Independent reproduction

Ingest genuine external reproduction reports.

Resolve discrepancies or document accepted residual differences.

Do not self-certify this gate.

## 4. Protected evaluator and community pilot

Require genuine end-to-end pilot receipts.

## 5. Paper and artifact

Generate:

- paper;
- supplement;
- benchmark card;
- dataset card;
- model cards;
- reproduction report;
- red-team report;
- governance appendix;
- exact commands;
- public-safe evidence bundle.

## 6. Level-5 gate

Run all Level-5 subgates.

Only emit:

`CAB_LEVEL5_COMPLETE`

when every real requirement passes.

Otherwise report the exact blocked state.

## 7. Release

- tag version;
- build packages and images;
- checksums;
- SBOM;
- archive;
- GitHub release instructions;
- stable docs;
- migration notes;
- deprecation policy;
- public evaluation registry.

## Acceptance State

`CAB_LEVEL5_COMPLETE`

This status is forbidden if any required external or empirical gate is simulated.

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
