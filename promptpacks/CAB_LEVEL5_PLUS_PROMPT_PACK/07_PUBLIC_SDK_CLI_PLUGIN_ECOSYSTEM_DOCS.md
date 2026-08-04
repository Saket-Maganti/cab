# Phase 07 — Public SDK, CLI, Plugin Ecosystem and Documentation

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

Turn internal modules into a stable public developer experience.

## 1. Public API design

Define supported interfaces for:

- benchmark loading and authoring;
- intervention compilation;
- agent adapters;
- tool adapters;
- model backends;
- policies;
- RAAC;
- scorers;
- registries;
- artifacts;
- audits;
- analyses;
- evaluator submissions.

Separate public API from internal modules.

Use semantic versioning and deprecation warnings.

## 2. Plugin system

Plugin types:

- agent;
- tool;
- backend;
- scorer;
- intervention family;
- analysis;
- exporter;
- evaluator runtime.

Requirements:

- typed metadata;
- version constraints;
- capability discovery;
- isolated loading failures;
- safe entry points;
- plugin compatibility checks;
- no arbitrary silent override of canonical safety gates.

Create example plugins.

## 3. CLI

Consolidate commands under one `cab` entry point:

```text
cab doctor
cab validate
cab benchmark ...
cab review ...
cab registry ...
cab plan
cab run
cab resume
cab merge
cab audit
cab analyse
cab reproduce
cab evaluator ...
cab release-check
```

Requirements:

- `--json`;
- `--dry-run`;
- stable exit codes;
- actionable errors;
- no secrets in output;
- shell completion if low cost.

## 4. Documentation

Create a structured documentation site or source tree:

- quickstart;
- architecture;
- authoring;
- execution;
- review;
- evaluation;
- analysis;
- security;
- governance;
- plugin development;
- API reference;
- troubleshooting;
- tutorials.

Add a public-safe end-to-end tutorial using fixture data.

## 5. Packaging

Validate:

- source distribution;
- wheel;
- clean install;
- optional extras;
- minimal install;
- development install;
- CLI entry point;
- licence and metadata.

## 6. Compatibility contract

Create an API stability policy and compatibility test matrix.

## Tests

- public import surface;
- plugin discovery;
- broken plugin isolation;
- command snapshots;
- clean install;
- minimal dependencies;
- docs links;
- example execution;
- deprecation warnings.

## Reports

- `docs/level5/PUBLIC_API_POLICY.md`
- `docs/level5/PLUGIN_SYSTEM.md`
- `docs/level5/CLI_REFERENCE.md`
- `reports/level5/PHASE07_PUBLIC_API_AUDIT.md`
- `reports/level5/PHASE07_HANDOFF.md`

## Acceptance State

`CAB_PUBLIC_INTERFACE_BETA_READY`

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
git commit -m "Publish CAB SDK CLI and plugin interfaces"
```
