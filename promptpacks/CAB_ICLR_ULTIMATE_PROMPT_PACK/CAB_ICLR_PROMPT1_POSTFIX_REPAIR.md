# CAB ICLR Prompt 1 Post-Fix Repair

## Purpose

Use this prompt immediately after completing:

`01_ICLR_CONTRIBUTION_AND_THEORY_BUILD.md`

and before starting:

`02_RECOVERY_AWARE_CONTROLLER_BUILD.md`

Repository:

`/Users/saketmaganti/Projects/causal-agent-bench`

GitHub repository:

`Saket-Maganti/cab`

Current Prompt 1 commit:

`d3469045a78de3a20b37783b29167805e7417e04`

The Prompt 1 implementation is scientifically strong and must be preserved. This repair pass addresses only two remaining full-suite failures:

1. protected held-out payloads are tracked in Git and therefore cannot be treated as uncontaminated hidden evaluation data;
2. one test contains a stale hard-coded workflow-state set that does not recognise the canonical `METHODOLOGY_READY` state.

Do not redesign Prompt 1. Do not begin Prompt 2. Do not execute scientific model runs.

---

# 1. Role

Act as:

- a benchmark-leakage auditor;
- a research software engineer;
- a Git and release-integrity specialist;
- an ICLR reproducibility reviewer;
- and a scientific-evidence governance reviewer.

Repair the two failures without weakening scientific gates or silently deleting user work.

---

# 2. Hard Boundaries

Do not:

- run external model inference;
- run provider APIs;
- launch Kaggle;
- fabricate replacement results;
- fabricate human review;
- promote scientific claims;
- silently delete tracked files;
- force-push;
- rewrite public Git history automatically;
- remove benchmark gates merely to make tests pass;
- downgrade held-out leakage from an error to a warning;
- change Prompt 1 estimands, theory, hypotheses, or null-result policy;
- commit or push unless explicitly authorised.

You may:

- inspect Git history;
- identify tracked protected payloads;
- classify leakage severity;
- invalidate contaminated held-out material;
- generate replacement candidate payloads locally using deterministic CPU-only generation;
- move protected material to a private/local-only path;
- update `.gitignore`, release policies, manifests, hashes, tests, and documentation;
- repair the stale state-contract test;
- run all provider-free validation.

All replacement material remains `DESIGN_ONLY`, `ENGINEERING_ONLY`, or `HUMAN_INPUT_REQUIRED` until genuine review and execution occur.

---

# 3. Phase A — Reproduce and Isolate Both Failures

Run the exact provider-free suite that produced:

- 1,012 passed;
- 1 skipped;
- 2 failures.

Capture:

- exact failing test names;
- full tracebacks;
- exact files involved;
- current branch;
- current commit;
- current Git status;
- whether both failures reproduce on the live checkout.

Create:

`reports/ICLR_PROMPT1_POSTFIX_BASELINE.md`

Include:

- commands;
- exit codes;
- failing assertions;
- whether each failure predates Prompt 1;
- and the minimal repair plan.

Do not modify files before reproducing both failures.

---

# 4. Phase B — Protected Held-Out Payload Audit

## 4.1 Identify all exposed protected material

Search the complete repository and Git history for:

- held-out task payloads;
- challenge-set task text;
- hidden answers;
- hidden intervention metadata;
- evaluator-only metadata;
- scorer gold policies;
- answer keys;
- private split payloads;
- challenge split instances;
- compressed archives or notebooks containing protected fields.

Inspect:

- current tracked files;
- deleted files still present in history;
- generated reports;
- notebooks;
- release bundles;
- archived outputs;
- Git LFS references;
- JSON, JSONL, CSV, YAML, pickle, and notebook files.

Create:

`reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json`

For every item record:

- path;
- current tracking state;
- first known public commit;
- last known public commit;
- content type;
- whether task text is exposed;
- whether answers are exposed;
- whether intervention labels are exposed;
- whether evaluator-only metadata is exposed;
- severity;
- scientific disposition;
- required repair.

## 4.2 Scientific contamination rule

Treat every protected payload ever pushed to the public repository as permanently compromised for future hidden or confirmatory evaluation.

Even after deletion, it may remain in:

- Git history;
- forks;
- clones;
- caches;
- search indexes;
- downloaded archives.

Therefore:

- do not continue calling exposed material “held out”;
- do not restore it as a hidden split;
- do not rely on history rewriting as proof of secrecy;
- do not use exposed tasks for confirmatory claims.

Classify exposed material as one of:

- `PUBLIC_DEVELOPMENT_ONLY`;
- `PILOT_ONLY`;
- `CONTAMINATED_NOT_CONFIRMATORY`;
- `INVALID_FOR_FUTURE_EVALUATION`.

## 4.3 Invalidate contaminated artifacts

Update canonical split and evidence registries so exposed material:

- cannot pass a confirmatory run gate;
- cannot enter Scale-100 confirmatory;
- cannot enter Main confirmatory;
- cannot enter a hidden challenge set;
- cannot produce paper-eligible claims;
- may remain only for public fixtures, development, or historical reproducibility.

Add explicit metadata:

- contamination state;
- public exposure commit/date;
- invalidation reason;
- replacement required;
- allowed future use.

## 4.4 Generate replacement protected candidates

If deterministic task-generation infrastructure exists, generate replacement candidate payloads with new:

- namespaces;
- task IDs;
- seeds;
- hashes;
- task content.

Requirements:

- no reuse of exposed IDs;
- no reuse of exposed text;
- no trivial parameter substitutions;
- no answer overlap where avoidable;
- no template-role conflict;
- no source-lineage overlap with public held-out content;
- no model-output-driven selection;
- no real model execution;
- no fabricated human validation.

Store full replacement protected payloads outside the public tracked tree, for example:

`private_data/heldout_challenge_v2/`

Add the private path to `.gitignore`.

The public repository may contain only:

- schemas;
- generators;
- safe aggregate metadata;
- non-reversible hashes;
- counts;
- provenance summaries;
- authorised local-generation instructions.

Do not commit replacement task text or answers.

## 4.5 Public-safe manifest

Create a public-safe manifest, for example:

`data/manifests/heldout_challenge_v2_public_manifest.json`

Include:

- split version;
- generator version;
- item count;
- domain distribution;
- intervention-family distribution;
- template distribution;
- source/licence summary;
- cryptographic content hashes;
- creation timestamp;
- contamination status;
- human-validation state.

Exclude:

- task text;
- answer keys;
- answer-bearing metadata;
- intervention payloads;
- any reversible protected fields.

Add a test proving the public manifest cannot expose or reconstruct protected content.

## 4.6 Strengthen release and leakage gates

Add or update tests that fail when:

- protected payload text is tracked;
- answer-bearing held-out files are tracked;
- protected payloads appear in release manifests;
- contaminated splits receive confirmatory roles;
- a public-safe manifest contains forbidden fields;
- protected paths are not ignored;
- replacement splits reuse exposed IDs;
- exact or near-duplicate public/private tasks overlap;
- notebooks or archives embed protected content.

Do not weaken the existing test just to make the suite green.

## 4.7 Git-history policy

Do not rewrite history automatically.

Create:

`docs/PUBLIC_HELDOUT_CONTAMINATION_AND_HISTORY_POLICY.md`

Explain:

- what was exposed;
- why the material is scientifically invalidated;
- why deleting it from the latest branch is insufficient;
- optional history-rewrite steps for repository hygiene;
- why history rewriting does not restore scientific secrecy;
- replacement-split policy;
- future protected-data handling.

If a history rewrite is recommended, provide exact commands under:

`OPTIONAL_DESTRUCTIVE_OPERATION_REQUIRES_EXPLICIT_AUTHORISATION`

Do not execute them.

---

# 5. Phase C — Repair the Stale `METHODOLOGY_READY` Test

Locate the test that recognises only the older workflow-state set.

Determine the canonical source of allowed states.

Prefer:

1. importing the allowed-state enumeration from the canonical state engine;
2. testing semantic invariants rather than copying the complete state list;
3. centralising state definitions in one typed enum or immutable constant.

Avoid:

- adding `METHODOLOGY_READY` to another independent hard-coded list;
- weakening the assertion to accept arbitrary strings;
- changing the canonical gate to return an older state;
- suppressing the test.

Add tests proving:

- `METHODOLOGY_READY` is recognised;
- unknown states are rejected;
- scientific execution remains blocked in `METHODOLOGY_READY`;
- it does not imply human review, C10, real runs, or paper eligibility;
- transitions remain fail-closed.

---

# 6. Phase D — Canonical State Repair

Regenerate or update:

- verified project state;
- evidence state;
- split registry;
- execution-entry gate;
- release inventory;
- current handoff;
- run-handbook references where needed.

The resulting state must report honestly:

- Prompt 1 theory build complete;
- held-out v1 exposed and invalidated;
- replacement protected candidate generated privately or pending;
- human review incomplete;
- C10 pending;
- scientific execution blocked;
- real model evidence zero;
- paper-eligible assets zero.

Do not mark the project ICLR-ready.

---

# 7. Phase E — Validation

Run at minimum:

## Focused tests

- protected-heldout release-policy tests;
- split-registry tests;
- contamination tests;
- state-engine tests;
- Prompt 1 paired-metric tests;
- intervention-validity profile tests.

## Static checks

- Ruff;
- mypy;
- JSON/YAML validation;
- `git diff --check`;
- secret scan;
- release validation.

## Full suite

Run the complete provider-free suite.

Acceptance target:

- zero unexpected failures;
- expected human/C10 fail-closed gates may return documented blocking exit codes;
- no provider, model, or Kaggle execution;
- no contaminated split eligible for confirmation.

Record:

- command;
- exit code;
- elapsed time;
- pass/skip/deselect counts;
- expected blocks;
- remaining blockers.

Create:

`reports/ICLR_PROMPT1_POSTFIX_VERIFICATION.md`

---

# 8. Required Outputs

Create or update:

1. `reports/ICLR_PROMPT1_POSTFIX_BASELINE.md`
2. `reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json`
3. `reports/ICLR_HELDOUT_CONTAMINATION_REPAIR.md`
4. `docs/PUBLIC_HELDOUT_CONTAMINATION_AND_HISTORY_POLICY.md`
5. public-safe replacement split manifest
6. updated split registry
7. updated release and leakage gates
8. repaired canonical state test
9. contamination and state-transition tests
10. `reports/ICLR_PROMPT1_POSTFIX_VERIFICATION.md`
11. updated canonical project handoff
12. logical commit plan

---

# 9. Acceptance Criteria

Complete only when:

- both original failures are reproduced and documented;
- all publicly exposed protected material is inventoried;
- exposed held-out content is scientifically invalidated;
- contaminated tasks cannot enter confirmatory or paper-eligible analysis;
- replacement candidates use new IDs, content, seeds, and hashes;
- full replacement payloads are not publicly tracked;
- a public-safe non-reversible manifest exists;
- leakage/release tests remain strict;
- `METHODOLOGY_READY` is canonically defined;
- the stale test no longer duplicates an outdated list;
- `METHODOLOGY_READY` remains non-executable and non-empirical;
- the full provider-free suite has zero unexpected failures;
- Prompt 1 theory and metrics remain intact;
- no scientific run, human review, commit, push, or history rewrite occurs without authorisation.

---

# 10. Final Response Format

## Final Status

Use one exact state:

- `ICLR_PROMPT1_POSTFIX_COMPLETE`
- `PARTIAL_SUCCESS_PROTECTED_DATA_REPLACEMENT_PENDING`
- `BLOCKED_BY_UNRESOLVED_PUBLIC_CONTAMINATION`

## Original Failures

State both tests and root causes.

## Held-Out Contamination Decision

List:

- exposed artifacts;
- invalidation decision;
- replacement status;
- public-safe manifest;
- private storage path;
- remaining risks.

## State-Contract Repair

Explain how duplicate hard-coded state definitions were removed.

## Validation

Provide exact commands, exit codes, and counts.

## Evidence State

Confirm:

- genuine human rows;
- real trajectories;
- audited runs;
- paper-eligible assets;
- empirical claims.

## Remaining Blockers

Separate:

- human validation;
- C10;
- replacement protected review;
- execution approval;
- optional Git-history hygiene.

## Exact Next Action

If all tests pass and replacement architecture is safe:

> Proceed to `02_RECOVERY_AWARE_CONTROLLER_BUILD.md` at Ultra effort.

Otherwise identify the single next repair.

## Files Changed

List all paths.

---

# 11. Final Directive

Fix the repository, not merely the test symptoms.

The protected-heldout failure is a scientific contamination problem, not only a CI inconvenience.

Preserve Prompt 1’s methodology.

Permanently invalidate exposed held-out content for confirmatory use.

Create a safe replacement architecture.

Restore a zero-failure provider-free suite.

Only then advance to Prompt 2.
