# CAB Level-5+ Ultimate One-Shot Foundation Build

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


## Mission

In one aggressive Codex run, build the maximum scientifically legal Level-5+ CAB platform foundation.

This prompt covers the buildable-now substance of phases 01–10. It does not authorise genuine human or model evidence.

## Target Architecture

Build and integrate:

1. Level-5 architecture and ADRs;
2. SQLite-default experiment registry with migrations;
3. immutable provenance primitive;
4. hermetic environment and SBOM;
5. benchmark-authoring DSL;
6. intervention compiler;
7. diversity and contamination engine;
8. backend-agnostic run planner;
9. scheduler and fixture backends;
10. content-addressed artifact store;
11. observability and local dashboard;
12. deterministic fault-injection laboratory;
13. human-review operating system;
14. protected evaluator fixture;
15. public SDK, CLI and plugin system;
16. evidence graph and certificates;
17. model-card and result-registry framework;
18. clean-room reproduction harness;
19. red-team programme;
20. governance and release system;
21. honest Level-5 maturity gate.

## Execution Method

### Step 1 — Audit and plan

Create:

- `reports/level5/CAB_LEVEL5_BUILD_STATE.json`;
- `reports/level5/CAB_LEVEL5_MASTER_LEDGER.md`;
- capability gap matrix;
- dependency graph;
- file ownership map.

Do not restart systems that already exist.

### Step 2 — Build vertical slices first

For each subsystem, implement one complete fixture vertical slice before adding breadth.

### Step 3 — Canonical integration

Use one:

- state model;
- registry interface;
- hash utility;
- artifact interface;
- CLI root;
- plugin registry;
- evidence graph;
- release gate.

### Step 4 — Testing cadence

- focused tests after each subsystem;
- integration tests after each pair of subsystems;
- full suite after execution OS, evaluator and final gate;
- packaging and clean-install tests at the end.

### Step 5 — Checkpointing

After every major subsystem:

- update ledger;
- update build state;
- write handoff;
- make a coherent local commit.

Push to main at stable milestones after security review.

## Mandatory Subsystem Contracts

### Registry
Transactional, migrated, immutable after freeze, idempotent, public-safe export.

### Benchmark factory
Typed DSL, deterministic compiler, invariance and manipulation checks, lifecycle and retirement.

### Execution OS
Deterministic plans, backends, scheduler, retry/resume, no silent substitution.

### Artifact store
Content addressed, atomic, immutable, compressed, verified, public/private separated.

### Reliability
Fault injection, no silent loss, deterministic recovery, privacy-safe observability.

### Human review
Blind assignments, genuine-only evidence paths, amendments, adjudication, C10 integration.

### Evaluator
Sandbox contract, network deny default, resource limits, protected broker, anti-exfiltration fixtures.

### Public interface
Stable SDK/CLI, plugins, dry run, JSON output, clean packaging and docs.

### Evidence system
Lineage graph, certificates, claim compiler, model cards, corrected/withdrawn result support.

### Reproduction and red team
Clean-room package, discrepancy tracking, attack fixtures, issue register.

### Governance and release
Contribution, versioning, contamination, correction, appeals, security, release gate.

## Required Commands

Target CLI surface:

```text
cab doctor
cab validate
cab benchmark init
cab benchmark compile
cab benchmark validate
cab review serve
cab review status
cab registry init
cab registry doctor
cab plan
cab run --dry-run
cab run
cab resume
cab merge
cab audit
cab analyse
cab evidence trace
cab certify
cab model-card
cab reproduce
cab evaluator dry-run
cab reliability campaign
cab level5 check
cab release-check
```

## Required Final Validation

- focused subsystem tests;
- full provider-free suite;
- static checks;
- structured-data validation;
- security and leakage scans;
- migration tests;
- package build and clean install;
- docs build;
- fixture run with crash/resume;
- chaos campaign;
- evaluator malicious fixtures;
- evidence graph verification;
- reproduction fixture;
- release check;
- Level-5 gate.

## Required Reports

- `CAB_LEVEL5_FOUNDATION_BUILD_REPORT.md`
- `cab_level5_handoff.md`
- `docs/level5/CAB_RESEARCH_OS_ARCHITECTURE.md`
- `docs/level5/CAB_LEVEL5_CAPABILITY_MATRIX.md`
- subsystem specifications;
- phase validation reports;
- `reports/level5/CAB_LEVEL5_BUILD_STATE.json`
- `reports/level5/CAB_LEVEL5_VALIDATION_LEDGER.md`
- `reports/level5/CAB_LEVEL5_GITHUB_PUBLISH.md`

## Correct Final State

```text
CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
```

Do not claim `CAB_LEVEL5_COMPLETE`.

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


Preferred milestone commits:

```text
Add CAB Level-5 registry and benchmark factory
Add CAB execution OS reliability and evaluator
Add CAB public SDK evidence certification and governance
Complete CAB Level-5 platform foundation
```

## Final Response

Report:

- architecture;
- subsystems;
- tests;
- performance;
- fixture demonstrations;
- security;
- packaging;
- blocked real-world gates;
- commits;
- remote verification;
- CI;
- exact next action.
