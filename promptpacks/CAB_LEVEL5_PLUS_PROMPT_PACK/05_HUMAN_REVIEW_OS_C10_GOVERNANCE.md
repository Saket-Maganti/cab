# Phase 05 — Human Review OS, C10 Operations and Governance

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

Build a real human-review operating system while preserving the rule that only genuine humans create evidence.

## 1. Review service architecture

Implement a local-first review application with secure defaults.

Capabilities:

- reviewer qualification;
- role-based access;
- privacy-safe reviewer IDs;
- blind assignment;
- randomised item order;
- model identity blinding;
- output blinding where required;
- autosave;
- immutable submitted judgments;
- amendment workflow;
- time-on-item;
- confidence;
- conflict and expertise disclosure;
- consent;
- compensation disclosure;
- adjudication queue;
- audit log;
- export/import.

Choose a lightweight implementation compatible with the repository. Heavy UI dependencies must be optional.

## 2. Assignment engine

Support:

- two independent reviewers;
- separate adjudicator;
- balanced workload;
- no self-review when conflicts are declared;
- deterministic assignment receipts;
- replacement only through logged policy;
- coverage verification.

## 3. Review schemas

Version:

- qualification;
- reviewer registry;
- assignment;
- judgment;
- amendment;
- disagreement;
- adjudication;
- exclusion;
- C10 decision;
- slice-lock receipt.

## 4. Agreement and monitoring

Provide:

- raw agreement;
- Wilson intervals;
- Cohen's kappa;
- Krippendorff's alpha;
- prevalence diagnostics;
- reviewer drift;
- time anomalies;
- straight-line detection;
- disagreement clusters;
- item-level uncertainty;
- family-level validity.

Do not auto-reject a reviewer solely from one metric.

## 5. C10 integration

The service exports into the existing canonical C10 validator.

No UI action may bypass C10.

## 6. Governance and ethics

Create:

- reviewer code of conduct;
- authors-as-reviewers policy;
- conflict policy;
- privacy and retention;
- compensation reporting;
- amendment policy;
- reviewer appeal;
- audit access.

## 7. Fixture demonstration

Use clearly fake fixture identities and judgments isolated from genuine evidence paths.

## CLI

```text
cab review serve
cab review qualify
cab review assign
cab review status
cab review export
cab review adjudicate
cab review validate
```

## Tests

Include:

- duplicate identity;
- proxy/AI attestation rejection;
- incomplete coverage;
- self-conflict;
- immutable submission;
- logged amendment;
- assignment balance;
- missing consent;
- low agreement;
- unresolved adjudication;
- fixture/genuine path isolation;
- C10 fail-closed.

## Reports

- `docs/level5/HUMAN_REVIEW_OS.md`
- `docs/level5/HUMAN_REVIEW_GOVERNANCE.md`
- `reports/level5/PHASE05_REVIEW_FIXTURE_DEMO.md`
- `reports/level5/PHASE05_HANDOFF.md`

## Acceptance State

`CAB_HUMAN_REVIEW_OS_READY`

The unified scientific state must remain `HUMAN_VALIDATION_REQUIRED`.

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
git commit -m "Build CAB human review operating system"
```
