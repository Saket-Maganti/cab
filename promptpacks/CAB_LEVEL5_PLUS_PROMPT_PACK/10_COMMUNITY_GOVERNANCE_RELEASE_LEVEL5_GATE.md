# Phase 10 — Community Governance, Release Engineering and Level-5 Gate

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

Complete the buildable-now Level-5 platform foundation and create an honest maturity gate.

## 1. Governance charter

Create policies for:

- project roles;
- task contribution;
- review and acceptance;
- benchmark versioning;
- schema compatibility;
- task deprecation and retirement;
- contamination response;
- result correction;
- leaderboard correction;
- appeals;
- conflicts of interest;
- contributor attribution;
- security disclosure;
- privacy;
- release cadence;
- supported versions;
- end-of-life.

## 2. Community contribution flow

Provide templates and validation for:

- new benchmark pack;
- intervention family;
- scorer;
- backend;
- model adapter;
- analysis;
- documentation;
- security report.

No contribution may bypass safety or evidence gates.

## 3. Release engineering

Build:

- release candidate workflow;
- changelog generation;
- schema migration notes;
- SBOM;
- licence bundle;
- reproducibility receipt;
- benchmark card;
- dataset card;
- model-card templates;
- security report;
- red-team report template;
- signed checksum manifest;
- clean-install verification.

## 4. Level-5 gate

Implement:

```bash
cab level5 check
```

Subgates:

- scientific validity;
- empirical evidence;
- evidence lineage;
- operational reliability;
- protected evaluator;
- independent reproduction;
- community usability;
- governance;
- security;
- release.

Possible states:

```text
LEVEL5_FOUNDATION_INCOMPLETE
LEVEL5_PLATFORM_FOUNDATION_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
LEVEL5_RELEASE_CANDIDATE
CAB_LEVEL5_COMPLETE
```

`CAB_LEVEL5_COMPLETE` must require real evidence, external reproduction and protected/community pilots.

## 5. Final build-now validation

Run:

- focused subsystem tests;
- full provider-free suite;
- static checks;
- packaging;
- clean install;
- fixture reproduction;
- chaos campaign;
- evaluator security fixtures;
- docs build;
- release check;
- Level-5 gate.

## 6. Foundation report

Create:

- `CAB_LEVEL5_FOUNDATION_BUILD_REPORT.md`
- `cab_level5_handoff.md`
- `reports/level5/CAB_LEVEL5_BUILD_STATE.json`
- `reports/level5/CAB_LEVEL5_VALIDATION_LEDGER.md`
- `reports/level5/CAB_LEVEL5_GITHUB_PUBLISH.md`

## Expected State

```text
CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
```

## Acceptance State

`CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE`

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
git commit -m "Complete CAB Level-5 platform foundation"
```
