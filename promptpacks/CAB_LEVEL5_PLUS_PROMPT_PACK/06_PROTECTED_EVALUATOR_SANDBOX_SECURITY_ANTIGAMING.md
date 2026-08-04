# Phase 06 — Protected Evaluator, Sandbox, Security and Anti-Gaming

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

Build a fixture-ready protected evaluation service that can later evaluate external submissions without revealing private tasks or answers.

Do not deploy a public production service in this phase.

## 1. Threat model

Cover:

- task exfiltration;
- answer exfiltration;
- environment probing;
- network escape;
- secret access;
- filesystem traversal;
- malicious archives;
- oversized output;
- fork bombs;
- resource exhaustion;
- prompt injection;
- tool-output injection;
- task-ID leakage;
- timing channels;
- score probing;
- memorisation;
- submission collusion;
- result tampering.

## 2. Submission contract

Versioned schema for:

- agent package;
- model declaration;
- policy declaration;
- runtime image;
- resource request;
- network request;
- entry point;
- output protocol;
- licence and authorship;
- attestation.

## 3. Sandbox interface

Implement a container-runtime abstraction with Docker as the fixture implementation.

Requirements:

- ephemeral workspace;
- read-only evaluator code;
- private task mount only at runtime;
- network denied by default;
- CPU, memory, process and wall-clock limits;
- output-size limits;
- non-root user;
- capability drop;
- secret-free environment;
- deterministic seeds;
- audit log;
- cleanup verification.

If Docker is unavailable, tests use a mock runtime and contract checks.

## 4. Protected task broker

The evaluator receives private task IDs and resolves payloads only inside the trusted boundary.

Public result records contain hashes and aggregates only.

## 5. Anti-exfiltration and anti-gaming

Implement fixture checks for:

- encoded answer dumps;
- protected prompt echoes;
- file enumeration;
- suspicious output entropy/volume;
- repeated probing;
- task-specific hardcoding;
- invalid abstention abuse;
- score-oracle queries;
- manipulation of result files.

Clearly document heuristic limitations.

## 6. Signed result receipt

Produce:

- evaluator version;
- task-set hash;
- submission hash;
- model/policy declarations;
- resource use;
- score summary;
- audit status;
- disqualification reasons;
- signature interface.

Use local development signing fixtures, not production secrets.

## 7. Security tests

Use malicious fixture submissions.

No real private tasks.

## CLI

```text
cab evaluator validate-submission
cab evaluator dry-run
cab evaluator run-fixture
cab evaluator audit
cab evaluator receipt
```

## Reports

- `docs/level5/PROTECTED_EVALUATOR_ARCHITECTURE.md`
- `docs/level5/EVALUATOR_THREAT_MODEL.md`
- `docs/level5/ANTI_GAMING_POLICY.md`
- `reports/level5/PHASE06_SECURITY_CAMPAIGN.md`
- `reports/level5/PHASE06_HANDOFF.md`

## Acceptance State

`CAB_PROTECTED_EVALUATOR_FIXTURE_READY`

Run full provider-free tests and security scans.

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
git commit -m "Add CAB protected evaluator foundation"
```
