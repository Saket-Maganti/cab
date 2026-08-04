# CAB Final Hostile Pre-Run Repair, Verification, Freeze, and Run-Readiness Master Prompt

## Purpose

Run this prompt in Codex from:

`/Users/saketmaganti/Projects/causal-agent-bench`

Repository:

`Saket-Maganti/cab`

Branch:

`main`

Recommended effort:

> **Ultra**

This is the final engineering prompt for Causal Agent Bench before genuine human review and authorized benchmark execution.

It is intentionally narrow.

It must not add another maturity level, another generic subsystem, another benchmark tier, another governance framework, another dashboard, or another large infrastructure layer.

It must repair the remaining scientific invariants that prior builder-authored gates failed to prove.

The only acceptable success state is:

```text
CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_PASSED
CAB_NEW_COMPACT20_STAGE1_PACKET_READY
CAB_STAGE2_PRIVATE_AND_UNEXPOSED
CAB_CAUSAL_TOOL_ROUTE_VALIDATED
CAB_POWER_PLAN_CALIBRATED
CAB_REPOSITORY_FROZEN_FOR_HUMAN_REVIEW
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
CAB_LEVEL5_COMPLETE=false
CAB_LEVEL6_COMPLETE=false
```

After successful completion, engineering stops.

The exact next action is genuine Stage-1 human review, followed by Stage-2 review, adjudication, C10, slice lock, and then authorized runs.

---

# 1. Starting State

At prompt creation, the latest known public `main` commit is:

`a3cbfc0016438714ba286c5bbacd33845a201a77`

The repository already contains:

- a large Level-5/Level-6 engineering foundation;
- semantic fact schemas;
- two-stage review infrastructure;
- recovery authorization;
- power tooling;
- governance and release infrastructure;
- extensive provider-free tests;
- CI and reproducible builds.

However, the following unresolved problems remain:

1. current Compact candidate IDs and Stage-2 contents have already been exposed publicly;
2. reviewer evidence still contains derived answer-bearing facts in some domains;
3. evidence-only reconstruction can remain circular because artifacts may embed answer outputs;
4. executable reachability can use fixture fact readers instead of actual benchmark tools;
5. recovery routes may receive expected fact IDs from the validator rather than deriving them from returned content;
6. abstention routes may pass without truly exhausting all permitted routes;
7. hierarchical power simulation may use data-generating processes or detection rules that do not match the intended estimator;
8. Level-6/final gates may check file/report existence instead of directly attacking the scientific invariant;
9. exact-tip release state may be stale after subsequent commits;
10. the project lacks a final immutable freeze receipt that prevents further silent endpoint/task/scorer changes after review begins.

Inspect the live repository first. If `main` has advanced, document the exact current state and adapt without weakening this prompt.

---

# 2. Mission

Complete one final hostile repair and freeze pass that:

1. retires the exposed Compact-20 candidates from genuine review use;
2. creates a completely new unseen Compact-20 packet;
3. uses only primitive raw evidence in Stage 1;
4. derives every answer from raw artifacts through actual benchmark tools;
5. proves completion, recovery, clarification, and abstention routes causally;
6. removes all expected-fact injection from observations;
7. validates recovery per attempt;
8. calibrates power using the exact intended estimator/test in each simulated dataset;
9. replaces self-certifying gates with adversarial black-box checks;
10. binds release and freeze receipts to the exact final commit;
11. generates the final human-review and run-readiness handoff;
12. freezes all scientific surfaces.

Do not perform genuine human review or model execution in this prompt.

---

# 3. Non-Negotiable Boundaries

Do not:

- create new benchmark maturity levels;
- add Level 7;
- add Main-500;
- add new intervention families;
- add generic governance subsystems;
- add new dashboards;
- add cloud deployment;
- add a SaaS evaluator;
- redesign the entire repository;
- generate reviewer judgments;
- generate adjudication;
- impersonate humans;
- run providers;
- run models;
- run GPUs;
- create live trajectories;
- create paper results;
- fabricate empirical evidence;
- fabricate external validation;
- promote fixture outputs to genuine evidence;
- reuse any previously exposed Compact candidate for genuine review;
- commit unlocked Stage-2 materials;
- commit reviewer package decryption keys;
- commit reviewer identities;
- commit private protected task bodies;
- use final answers as primitive source facts;
- inject expected fact IDs into tool output;
- claim route exhaustion without executing or formally eliminating each route;
- mark nonempty output as causal evidence;
- label heuristic detection as statistical power;
- claim exact-tip release when receipt SHA differs from HEAD;
- weaken existing safety gates;
- stage unrelated user-owned files;
- force-push;
- create a feature branch;
- create a pull request.

Always:

- inspect first;
- preserve existing history;
- work directly on `main`;
- fail closed;
- distinguish fixture, review, live, audited, and paper-eligible evidence;
- use deterministic generation;
- record seeds and hashes;
- treat every existing PASS report as untrusted until independently rechecked;
- use black-box exported artifacts where possible;
- run narrow tests after each repair;
- run the full provider-free suite;
- push only task-owned changes;
- verify local and remote SHA equality;
- observe CI honestly.

---

# 4. Baseline Audit and Protected Worktree

Run:

```bash
cd /Users/saketmaganti/Projects/causal-agent-bench

git status --short
git status --branch --short
git branch --show-current
git rev-parse HEAD
git remote -v
git fetch origin main
git rev-list --left-right --count origin/main...main
git log -8 --oneline --decorate
```

Create:

- `reports/final_hostile_pre_run/BASELINE.md`
- `reports/final_hostile_pre_run/STATE.json`
- `reports/final_hostile_pre_run/DECISIONS.md`
- `reports/final_hostile_pre_run/TASK_OWNED_PATHS.txt`
- `cab_final_hostile_pre_run_handoff.md`

Record:

- current SHA;
- worktree state;
- all unrelated modified/untracked files;
- exact paths to preserve;
- current exposed Compact candidate IDs;
- public Stage-2 paths;
- current scientific endpoint versions;
- current scorer versions;
- current review packet hashes;
- current power report hashes;
- current release receipt SHA;
- current genuine evidence counters.

---

# 5. Phase A — Retire the Exposed Compact Slice

## A1. Mark all exposed Compact candidates as development-only

Every candidate whose candidate ID, task content, Stage-2 gold, scorer policy, answer contract, recovery route, or abstention opportunity has appeared in public Git history must be marked:

```text
EXPOSED_DEVELOPMENT_FIXTURE_NOT_ELIGIBLE_FOR_GENUINE_REVIEW
```

They must never count toward C10, human validation, Compact pilot results, model runs, or paper claims.

## A2. Exposure ledger

Create a machine-readable exposure ledger containing:

```text
candidate_id
task_id
first_public_commit
exposed_fields
exposure_type
retirement_status
replacement_required
```

## A3. Fail-closed enforcement

Any attempt to include exposed candidate IDs in a genuine packet, approve them for scientific execution, count judgments on them toward C10, or include their trajectories in paper analysis must fail.

## A4. Historical preservation

Do not rewrite public Git history.

Preserve old candidates as development fixtures, clearly labelled.

Acceptance state:

```text
CAB_EXPOSED_COMPACT_SLICE_RETIRED
```

---

# 6. Phase B — Generate a Completely New Unseen Compact-20

## B1. New candidate universe

Create a new Compact-20 slice using candidate/task variants that have never appeared in:

- public Git history;
- prior reports;
- prior reviewer files;
- prior fixture packages;
- public tests;
- release bundles.

Use new IDs and new content hashes.

## B2. Packet composition

Required:

- 20 items;
- four Compact intervention families;
- five items per family;
- at least 16 unique base tasks;
- no domain above 20%;
- every family spans at least three domains;
- every family spans at least three difficulty levels where feasible;
- at least four easy;
- at least six medium;
- at least four hard;
- at least two stress;
- explicit deliberate anchors only;
- no accidental duplicates;
- deterministic seed;
- selection receipt;
- exposure scan PASS.

## B3. Private generation

Generate real candidate bodies only under ignored private paths.

Public repository may contain schemas, commitments, aggregate composition, hashes, generator version, and deterministic seed commitment.

It must not contain raw candidate bodies, golds, Stage-2 contents, hidden facts, or unlock keys.

## B4. Public commitment

Create a public commitment containing:

```text
packet_id
candidate_count
family_counts
domain_counts
difficulty_counts
candidate_content_hashes
stage1_package_hashes
generator_version
seed_commitment
exposure_scan_result
```

Acceptance state:

```text
CAB_NEW_COMPACT20_PRIVATE_SLICE_READY
```

---

# 7. Phase C — Primitive Raw Evidence Only

## C1. Primitive evidence rule

Stage-1 evidence may contain only primitive source records.

It must not contain any derived answer-bearing field such as:

- selected option;
- best option;
- final total;
- final decision;
- claim supported;
- approval required;
- first open slot;
- selected vendor;
- bug diagnosis;
- final category;
- final answer text.

## C2. Domain-specific primitive artifacts

Create raw artifacts such as:

### Travel planning

- all hotel records;
- prices;
- refundability;
- taxes;
- constraints;
- no selected hotel;
- no final total.

### Shopping comparison

- all bundles;
- item prices;
- taxes;
- shipping;
- constraints;
- no selected bundle;
- no final total.

### Spreadsheet/file QA

- actual spreadsheet rows;
- actual note/document;
- no extracted final answer.

### Research assistant

- raw report text;
- claim text;
- threshold;
- no `claim_supported` field.

### Coding/debugging

- raw source code;
- logs;
- issue description;
- no `bug_type` answer field.

### Policy compliance

- raw policy clauses;
- transaction amount;
- approval hierarchy;
- no `approval_required` field.

### Calendar/email

- raw events;
- working hours;
- recipient directory;
- no `first_open_slot` or `draft_status`.

### Operations planning

- raw vendor table;
- policies;
- schedules;
- no selected vendor.

## C3. Derived-field blacklist

Add a validator with a domain-specific blacklist of answer-bearing fields.

Stage-1 generation fails if any blacklisted field is present.

## C4. Semantic fact derivation

Semantic facts must be extracted from primitive artifacts—not copied from hidden gold.

Derived semantic facts may exist internally after tool execution, but not as primitive Stage-1 source records.

Acceptance state:

```text
CAB_PRIMITIVE_EVIDENCE_ONLY_READY
```

---

# 8. Phase D — Actual Benchmark-Tool Gold Reconstruction

## D1. No fixture fact reader for scientific validation

The final validation path must not use `cab_fixture_read_fact` or an equivalent direct fact-access helper for scientific route certification.

Fixture readers may remain for unit tests only.

## D2. Actual tool execution

For each candidate, use the actual declared benchmark tools, including domain-appropriate tools such as:

- `search_database`;
- `compare_options`;
- `calculate_price`;
- `read_file`;
- `query_spreadsheet`;
- `verify_fact`;
- `lookup_policy`;
- calendar/email tools;
- code/file tools;
- recovery tools.

## D3. Tool-output extraction

Every tool output must be parsed into semantic facts through an extraction layer.

The extractor must derive:

```text
fact_id
source_artifact_hash
source_locator
observed_value
normalized_value
extraction_rule
confidence_or_deterministic_status
```

## D4. No expected-fact injection

Search for and remove any code that writes:

```text
returned_fact_ids = contract.supported_fact_ids
```

or equivalent expected values into observations.

Returned fact IDs must be computed from actual output content.

## D5. Gold reconstruction

Gold must be reconstructed only from facts obtained through actual tool calls.

The checker must run in an isolated environment without hidden gold, expected final answer, Stage-2 scorer policy, or answer contract.

It may compare the derived output to the frozen commitment only after reconstruction is complete.

## D6. Negative controls

Add corrupted and incomplete artifacts proving that:

- reconstruction fails when a primitive fact is missing;
- wrong prices produce a different total;
- wrong policy clauses change the decision;
- missing calendar events prevent slot selection;
- unrelated tool output cannot satisfy the derivation.

Acceptance state:

```text
CAB_ACTUAL_TOOL_GOLD_RECONSTRUCTION_READY
```

---

# 9. Phase E — Hostile Stage-1 Leakage Audit

## E1. Black-box archive inspection

Inspect only the exported Stage-1 archives as an external reviewer would.

Do not consult source generators while evaluating leakage.

## E2. Leakage categories

Search for:

- exact final answers;
- selected options;
- final totals;
- derived decision labels;
- scorer policy IDs;
- answer contracts;
- recovery action IDs;
- abstention opportunities;
- Stage-2 file names;
- hidden fact labels;
- gold derivation outputs;
- hashes that trivially map to public gold files;
- candidate IDs from exposed packets.

## E3. Inferability attack

Build a fixture attacker that attempts to infer the final answer directly from filenames, metadata, ordering, IDs, precomputed derived fields, README wording, and manifests.

The attacker must not be able to recover answer-bearing fields without executing the intended task logic.

## E4. Physically isolated packages

Generate:

```text
stage1_reviewer_a.zip
stage1_reviewer_b.zip
stage1_adjudicator.zip
```

under ignored private storage.

Stage-2 material must not be committed.

## E5. Stage-2 access

Stage 2 must require finalized Stage-1 judgments, a Stage-1 receipt, coordinator unlock, and separate package generation or decryption.

Acceptance state:

```text
CAB_STAGE1_BLACK_BOX_LEAKAGE_AUDIT_PASSED
```

---

# 10. Phase F — Causal Route Validation

## F1. Completion route

For every completion route:

```text
raw artifact
→ actual tool call
→ actual observation
→ semantic extraction
→ derivation
→ final answer
```

Every edge must be recorded.

## F2. Recovery route

For every recovery route:

1. actual target failure occurs;
2. failure class is verified;
3. exact authorized recovery action is executed;
4. output is parsed;
5. causal facts are extracted;
6. final answer is derived;
7. answer correctness is verified.

## F3. Clarification route

A clarification route passes only if all artifacts and tools are exhausted, one exact user-provided variable remains unknown, the clarification question targets that variable, and the task cannot be solved without it.

## F4. Abstention route

An abstention route passes only if every permitted route is executed and failed, or formally eliminated with a machine-checkable reason.

Required proof:

```text
route inventory
attempt/elimination status
missing fact IDs
unavailable tools/artifacts
recovery impossibility
terminal response contract
```

## F5. Irrelevant-output attack

Inject nonempty but irrelevant output, output from the wrong artifact, stale output, output from another candidate, and output with expected IDs but wrong values.

All must fail.

Acceptance state:

```text
CAB_CAUSAL_ROUTE_AUDIT_PASSED
```

---

# 11. Phase G — Recovery Per-Attempt Final Repair

## G1. Per-attempt state

Each attempt must be isolated by:

```text
attempt_id
failure_event_id
action_id
tool_name
arguments
observation
fact_ids
success_predicate
budget
temporal order
```

## G2. No state carryover

No Boolean or mutable authorization state may survive into a later unrelated step.

## G3. Success binding

A recovery attempt succeeds only when its own output satisfies its own schema, contains its own required facts, and passes its own success predicate.

## G4. Task recovery

`task_recovered` requires a successful authorized attempt, correct final answer, and causal dependency on recovered evidence.

## G5. Hostile trajectories

Test:

- authorized attempt fails, later unrelated tool succeeds;
- correct action ID with wrong tool;
- correct tool with wrong arguments;
- replayed observation;
- cross-candidate observation;
- stale failure event;
- budget exhausted;
- forged metadata;
- successful authorized recovery.

Acceptance state:

```text
CAB_RECOVERY_FINAL_AUDIT_PASSED
```

---

# 12. Phase H — Statistical Power Calibration Against the Actual Analysis

## H1. Freeze the actual estimators

Before simulation, define the exact planned estimator/test for:

- per-model paired degradation;
- fixed-panel pooled degradation;
- family effects;
- model × family interaction;
- RAAC improvement;
- clean non-inferiority;
- rank instability;
- unresolved ranking.

## H2. Valid paired data generation

Replace weighted-uniform threshold constructions.

Use a valid method such as:

- Gaussian copula for correlated Bernoulli outcomes;
- conditional transition probabilities;
- beta-binomial paired hierarchy;
- another documented method with correct marginals.

Verify simulated marginals empirically.

## H3. Apply the actual test in every replicate

Do not use heuristic thresholds such as:

```text
observed SD > assumed SD / 3
```

For each replicate, fit or compute the actual planned estimator/test.

## H4. Non-inferiority

Use the correct confidence-bound rule:

```text
upper confidence bound on clean loss < margin
```

or the exact frozen alternative.

## H5. Per-model reporting

Report:

- power for each model separately;
- minimum model power;
- median model power;
- probability all models pass as a separate familywise metric.

Do not label `all models pass` as per-model power.

## H6. Fixed panel versus superpopulation

Treat the named five-model panel as fixed unless the scientific claim explicitly targets a model population.

For model-superpopulation inference, use a calibrated hierarchical estimator and appropriate small-sample uncertainty.

## H7. Simulation resume

Implement persisted shards:

```text
simulation_shard_id
seed
replicate_start
replicate_end
status
hash
```

Support deterministic resume and merge.

## H8. Calibration checks

Under the null, verify empirical Type-I error.

Under known alternatives, verify expected monotonicity.

Generate:

- Type-I error;
- power;
- CI coverage;
- bias;
- RMSE;
- Monte Carlo SE.

Acceptance state:

```text
CAB_POWER_AND_INFERENCE_CALIBRATED
```

---

# 13. Phase I — Replace Self-Certifying Gates

## I1. No existence-only checks

The final gate must not pass because files such as `blinding.py`, `recovery.py`, or `executable_reachability.py` exist.

## I2. Required direct checks

The final gate must directly run:

- exposure retirement check;
- new-slice novelty check;
- primitive-evidence blacklist check;
- black-box Stage-1 leakage attack;
- actual-tool reconstruction;
- expected-fact injection scan;
- causal completion route;
- causal recovery route;
- clarification proof;
- abstention route exhaustion;
- recovery cross-step attack;
- power Type-I calibration;
- CI coverage calibration;
- exact-HEAD release check;
- authoritative Level-5/Level-6 state ingestion.

## I3. Independent fixture attacker

Create a separate hostile-audit module that does not import internal builder helpers where feasible.

It must consume exported packages and public interfaces only.

## I4. Fail-closed terminal state

Any failed hostile invariant yields:

```text
CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_FAILED
```

Acceptance state:

```text
CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_PASSED
```

---

# 14. Phase J — Exact Final-Commit Release and Scientific Freeze

## J1. Commit-first sealing

1. finish source changes;
2. commit;
3. build from the exact commit in detached clean trees;
4. compare artifacts;
5. generate an external receipt bound to that commit;
6. push;
7. verify remote SHA;
8. record final receipt outside the source tree or in a follow-up attestation that does not falsely claim self-inclusion.

## J2. Exact-HEAD enforcement

The validator must fail when:

```text
receipt.source_commit != git rev-parse HEAD
```

unless the receipt explicitly uses a documented external attestation model referencing the final immutable tag.

## J3. Scientific freeze manifest

Create a freeze manifest binding:

```text
new Compact public commitment
Stage-1 package hashes
Stage-2 encrypted commitment
scorer version
endpoint version
analysis-plan hash
power-plan hash
system-identity schema
review protocol hash
C10 contract hash
generator commit
```

## J4. Freeze enforcement

After the freeze:

- scientific task changes require a new benchmark version;
- scorer changes require a new version;
- endpoint changes require a new version;
- packet regeneration invalidates prior review;
- model runs must reject mismatched hashes.

## J5. Final status

Required:

```text
CAB_REPOSITORY_FROZEN_FOR_HUMAN_REVIEW
```

---

# 15. Phase K — Final Review and Run-Readiness Handoff

## K1. Human review package

Generate coordinator-only instructions for:

- reviewer recruitment;
- qualification;
- Stage-1 distribution;
- Stage-1 commitment;
- Stage-2 unlock;
- Stage-2 distribution;
- adjudication;
- C10 execution;
- slice lock.

## K2. Run gate

Create a final run gate requiring:

```text
C10_PASS
slice_lock_receipt
approved_packet_hash
scorer_hash
endpoint_hash
analysis_plan_hash
system_identity_hash
approval_receipt
```

## K3. Runbook

Prepare the exact authorized execution order:

```text
1. Compact offline fixture rehearsal
2. one-task live smoke
3. Compact-20 standard policy
4. Compact-20 RAAC-Light
5. scorer audit
6. decision gate
7. Scale-100 standard
8. Scale-100 RAAC-Light
9. staged RAAC ablations
10. transfer study
11. final analysis
```

## K4. No execution in this prompt

Do not perform real model/provider/GPU execution.

A fixture-only rehearsal is allowed.

Acceptance state:

```text
CAB_FINAL_RUN_READINESS_PACKAGE_READY
```

---

# 16. Required Adversarial Demonstrations

## Demo 1 — Exposed candidates rejected

Attempt to include one old candidate in a genuine packet. It must fail.

## Demo 2 — Primitive evidence only

Insert a derived field such as `selected_hotel` into Stage 1. It must fail.

## Demo 3 — Hidden-gold denial

Remove hidden gold entirely and still reconstruct the new packet through actual tools.

## Demo 4 — Expected-fact injection blocked

Attempt to write expected fact IDs into a tool observation. It must fail.

## Demo 5 — Irrelevant nonempty output

Return nonempty irrelevant output. Route must fail.

## Demo 6 — Abstention exhaustion

Show every allowed route attempted or formally eliminated.

## Demo 7 — Recovery isolation

Show later unrelated success cannot inherit earlier authorization.

## Demo 8 — Stage-1 attacker

Attempt answer inference from exported Stage-1 archives. No direct leakage allowed.

## Demo 9 — Power null calibration

Empirical Type-I error must be within a preregistered tolerance.

## Demo 10 — Exact-HEAD release

Create a stale receipt and prove the validator fails.

## Demo 11 — Freeze mismatch

Alter one scorer or packet hash and prove the run gate refuses execution.

---

# 17. Required Reports

Create:

1. `CAB_FINAL_HOSTILE_PRE_RUN_REPORT.md`
2. `cab_final_hostile_pre_run_handoff.md`
3. `reports/final_hostile_pre_run/BASELINE.md`
4. `reports/final_hostile_pre_run/STATE.json`
5. `reports/final_hostile_pre_run/DECISIONS.md`
6. `reports/final_hostile_pre_run/EXPOSED_CANDIDATE_LEDGER.json`
7. `reports/final_hostile_pre_run/NEW_COMPACT_SELECTION_REPORT.md`
8. `reports/final_hostile_pre_run/PRIMITIVE_EVIDENCE_AUDIT.md`
9. `reports/final_hostile_pre_run/ACTUAL_TOOL_GOLD_REPORT.md`
10. `reports/final_hostile_pre_run/STAGE1_BLACK_BOX_LEAKAGE_REPORT.md`
11. `reports/final_hostile_pre_run/CAUSAL_ROUTE_AUDIT.md`
12. `reports/final_hostile_pre_run/RECOVERY_FINAL_AUDIT.md`
13. `reports/final_hostile_pre_run/POWER_CALIBRATION_REPORT.md`
14. `reports/final_hostile_pre_run/HOSTILE_GATE_REPORT.md`
15. `reports/final_hostile_pre_run/SCIENTIFIC_FREEZE_MANIFEST.json`
16. `reports/final_hostile_pre_run/RELEASE_ATTESTATION.json`
17. `reports/final_hostile_pre_run/HUMAN_REVIEW_HANDOFF.md`
18. `reports/final_hostile_pre_run/RUN_READINESS_HANDOFF.md`
19. `reports/final_hostile_pre_run/VALIDATION_LEDGER.md`
20. `reports/final_hostile_pre_run/GITHUB_PUBLICATION.md`

Do not commit private candidate bodies, real Stage-2 contents, packages, keys, or reviewer information.

---

# 18. Required CLI Gates

Add and run:

```bash
cab final exposed-candidate-check
cab final new-compact-novelty-check
cab final primitive-evidence-check
cab final stage1-black-box-check
cab final actual-tool-gold-check
cab final expected-fact-injection-check
cab final causal-route-check
cab final recovery-isolation-check
cab final power-calibration-check
cab final exact-head-release-check
cab final scientific-freeze-check
cab final hostile-pre-run-check
```

Expected:

```text
CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_PASSED
CAB_NEW_COMPACT20_STAGE1_PACKET_READY
CAB_STAGE2_PRIVATE_AND_UNEXPOSED
CAB_CAUSAL_TOOL_ROUTE_VALIDATED
CAB_POWER_PLAN_CALIBRATED
CAB_REPOSITORY_FROZEN_FOR_HUMAN_REVIEW
```

---

# 19. Validation

## Focused tests

Run after each phase.

## Full provider-free suite

```bash
python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'
```

## Static

- Ruff lint;
- mypy;
- Codespell;
- JSON/YAML/schema validation;
- `git diff --check`.

Do not mass-format unrelated files.

## Security and privacy

- Stage-1 leakage scan;
- Stage-2 public-history exposure scan;
- private candidate scan;
- reviewer identity scan;
- secret/key scan;
- archive traversal scan;
- protected payload scan.

## Documentation

```bash
mkdocs build --strict
```

## Packaging

- wheel;
- sdist;
- Twine;
- clean import;
- CLI smoke;
- release dry run;
- two detached reproducible builds.

## Final fixture rehearsal

Run the complete fixture-only lifecycle:

```text
new private packet
→ Stage-1 export
→ fake fixture commitment
→ Stage-2 unlock fixture
→ fixture adjudication
→ fixture C10
→ fixture freeze
→ fixture run-gate approval
```

Clearly label it fixture-only.

All genuine evidence counters must remain zero.

---

# 20. Acceptance Criteria

The task is complete only when:

## Candidate novelty

- no genuine candidate has appeared in public history;
- old candidates are retired;
- new slice passes exposure scan.

## Primitive evidence

- no answer-bearing source fields;
- no selected option;
- no final total;
- no derived decision label;
- no final answer embedded.

## Gold reconstruction

- actual tools only;
- hidden gold unavailable;
- expected final answer unavailable during derivation;
- final comparison happens only afterward;
- negative controls fail.

## Stage-1 blinding

- exported archives contain no Stage-2 data;
- answer-inference attacker finds no direct leakage;
- Stage 2 remains private/encrypted.

## Causal routes

- completion uses actual tools;
- recovery uses actual failure and fallback;
- facts come from observations;
- abstention proves route exhaustion;
- irrelevant output fails.

## Recovery

- per-attempt isolation;
- no carryover;
- exact action/tool/arguments/order/budget;
- task recovery requires correct final answer.

## Power

- valid paired generator;
- actual estimator/test per replicate;
- Type-I error calibration;
- CI coverage calibration;
- no heuristic detection metrics presented as power;
- persisted shards and resume.

## Final gate

- direct hostile checks;
- no file-existence-only closure;
- authoritative Level-5/Level-6 state ingestion.

## Release

- receipt bound to exact final commit/tag;
- reproducible wheel and sdist;
- hashes verified.

## Freeze

- all scientific surfaces hash-bound;
- mismatches block review/run;
- repository state clearly frozen.

## Evidence

All genuine evidence counters remain zero.

---

# 21. Git Publication

Before staging:

```bash
git status --short
git diff --stat
git diff
git diff --check
```

Stage task-owned paths only.

Recommended commits:

```text
Retire exposed CAB review slice and rebuild primitive evidence
Validate CAB causal routes and calibrated inference
Freeze CAB for genuine human review and authorized runs
```

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

Observe CI with a bounded wait.

Do not claim green while required checks are active.

---

# 22. Final Response Format

## Final State

Use one:

```text
CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_PASSED
PARTIAL_SUCCESS_FINAL_REPAIRS_REMAIN
LOCAL_FINAL_REPAIR_COMPLETE_PUSH_BLOCKED
FINAL_REPAIR_BLOCKED_BY_REPOSITORY_INCONSISTENCY
```

## Exposed Slice

Report retired candidate count and enforcement.

## New Compact

Report aggregate composition and public commitment hash only.

Do not reveal private candidate bodies.

## Primitive Evidence

Report blacklist and negative-control results.

## Actual Tools

Report tool-route validation counts.

## Stage-1 Blinding

Report package hashes and leakage results.

## Recovery

Report hostile trajectory results.

## Power

Report Type-I error, coverage, bias, RMSE, power, and MCSE.

## Freeze

Report scientific freeze manifest hash.

## Release

Report exact commit/tag and reproducible artifact hashes.

## Validation

Report exact tests, lint, typing, docs, security, packaging, and CI.

## Evidence

Report genuine evidence counters; all must remain zero.

## Exact Next Action

Use exactly:

> Recruit and onboard two genuine qualified independent reviewers with the new physically isolated Stage-1 packages, keep Stage 2 inaccessible until Stage-1 commitment, complete adjudication and C10, lock the slice, and then begin the authorized Compact run sequence.

---

# 23. Final Directive

Do not expand CAB again.

Do not add Level 7.

Do not add another general framework.

Do not create more self-certifying reports.

Retire the exposed slice.

Generate a genuinely unseen slice.

Use raw primitive evidence.

Use actual benchmark tools.

Derive facts from output.

Prove every route.

Calibrate the real analysis.

Attack the exported packages as an outsider.

Bind the release to the exact final commit.

Freeze the scientific surfaces.

Finish at:

```text
CAB_FINAL_HOSTILE_PRE_RUN_AUDIT_PASSED
CAB_NEW_COMPACT20_STAGE1_PACKET_READY
CAB_STAGE2_PRIVATE_AND_UNEXPOSED
CAB_CAUSAL_TOOL_ROUTE_VALIDATED
CAB_POWER_PLAN_CALIBRATED
CAB_REPOSITORY_FROZEN_FOR_HUMAN_REVIEW
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
CAB_LEVEL5_COMPLETE=false
CAB_LEVEL6_COMPLETE=false
```

Then stop engineering.

Begin genuine human review.

After C10 and slice lock, begin the runs.
