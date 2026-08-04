# Phase 09 — Independent Reproduction, Red Team and External Pilot Harness

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

Build the infrastructure and protocols for independent reproduction and adversarial validation.

Do not claim an external person completed these tasks unless they genuinely did.

## 1. One-command reproduction

Create a public-safe command that:

- verifies environment;
- validates manifests;
- executes fixture pipeline;
- verifies artifacts;
- regenerates selected non-empirical reports;
- builds the paper with placeholders;
- emits a reproduction receipt.

Later it must support audited public evidence.

## 2. Clean-room package

Create:

- independent reproducer instructions;
- expected hashes;
- environment options;
- troubleshooting;
- discrepancy form;
- signed attestation template;
- artifact retrieval protocol;
- table-regeneration protocol.

## 3. Reproduction coordinator

Track:

- reproducer identity privately;
- environment;
- attempts;
- discrepancies;
- resolutions;
- matched hashes;
- acceptable numerical tolerance;
- sign-off.

No self-attestation as independent reproduction.

## 4. Red-team harness

Attack classes:

- benchmark leakage;
- task memorisation;
- scorer exploitation;
- answer-format gaming;
- abstention gaming;
- retry amplification;
- budget loopholes;
- RAAC over-triggering;
- hidden-label access;
- prompt/tool injection;
- task-ID leakage;
- artifact tampering;
- evaluator escape;
- collusive submissions;
- suspicious performance jump.

Provide fixture attack submissions and expected detections.

## 5. External pilot kit

Create a package for an external researcher to:

- install CAB;
- run public fixtures;
- author one sample task;
- validate a plugin;
- submit a fixture agent;
- report usability issues.

Do not fabricate external feedback.

## 6. Issue register

Versioned red-team and reproduction findings:

- severity;
- reproducibility;
- owner;
- mitigation;
- accepted risk;
- release blocker.

## Reports

- `docs/level5/INDEPENDENT_REPRODUCTION_PROTOCOL.md`
- `docs/level5/RED_TEAM_PROGRAMME.md`
- `docs/level5/EXTERNAL_PILOT_GUIDE.md`
- `reports/level5/PHASE09_INTERNAL_REPRODUCTION_FIXTURE.md`
- `reports/level5/PHASE09_REDTEAM_FIXTURE_CAMPAIGN.md`
- `reports/level5/PHASE09_HANDOFF.md`

## Acceptance State

`CAB_REPRODUCTION_AND_REDTEAM_HARNESS_READY`

Not `INDEPENDENTLY_REPRODUCED`.

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
git commit -m "Add CAB reproduction and red-team harness"
```
