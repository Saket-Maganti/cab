# CAB Final Pre-Review Remaining-Fixes Master Prompt

## Purpose

Run this prompt in Codex from:

`/Users/saketmaganti/Projects/causal-agent-bench`

Repository:

`Saket-Maganti/cab`

Branch:

`main`

Recommended effort:

> **Ultra**

This is the final bounded repair pass after the CAB pre-run scientific-hardening build.

The previous pass successfully repaired the majority of the project, including scorer-v3 outcome separation, Compact-20 redesign, confirmatory balancing, v2 execution-path canonicalisation, manifest-derived resource planning, system identity, artifact-rich synthetic transfer, documentation, tests, and publication.

However, independent audit found additional scientific weaknesses that must be resolved before genuine human reviewers or model executions begin.

This prompt must repair **all remaining known pre-review and pre-execution weaknesses**, not merely the three headline findings.

It must not expand CAB with new benchmark tiers, new generic infrastructure, or new speculative intervention families.

---

# 1. Verified Starting State

At prompt creation, public `main` is expected to be:

`715d981cf68eb2741dd6e05b097b08445f87accf`

Published commits from the prior pass:

```text
3c883cb0206be03dbee35556adad3ab62ebca075 — Repair CAB scientific scoring semantics
3a3a2758c70b58ac169b321ac3983d3d1e018e2c — Rebuild CAB pre-review and confirmatory designs
9f773f36639fa0d584362a63be4a6e116cbef2b0 — Finalize CAB pre-run scientific hardening
715d981cf68eb2741dd6e05b097b08445f87accf — Refresh CAB release bundle and publication record
```

Expected current scientific state:

```text
CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
CAB_LEVEL5_COMPLETE=false
```

Expected genuine evidence counters:

```text
genuine_human_judgments=0
genuine_adjudications=0
real_model_trajectories=0
audited_real_runs=0
paper_eligible_empirical_assets=0
supported_empirical_claims=0
independent_external_reproductions=0
protected_evaluator_pilots=0
community_pilots=0
```

Inspect the live repository first. If it has advanced, treat the live state as authoritative and record the difference.

---

# 2. Final Mission

Complete every remaining scientific and operational repair required before CAB can truthfully begin genuine Compact-20 review.

The pass must address:

1. reviewer access to inspectable source evidence;
2. two-stage blinded human validation;
3. exact authorized recovery-action matching;
4. recovery success causally linked to the authorized action;
5. hierarchical and clustered prospective power simulation;
6. correct experimental-unit treatment;
7. per-model, pooled, family, interaction, RAAC, and ranking power outputs;
8. cryptographic approval receipts instead of path-name approval;
9. executable evidence-route reachability;
10. executable gold reconstruction;
11. artifact/tool-route parity under interventions;
12. measured smoke-based runtime and storage calibration hooks;
13. staged, prospective RAAC ablation planning;
14. clean-checkout release reproducibility;
15. accurate terminology and claims for all static versus executable gates;
16. final reviewer packet regeneration and invalidation of superseded packets;
17. adversarial tests that independently challenge the new rules;
18. one final fail-closed pre-review gate;
19. complete public-safe documentation and publication.

Correct terminal state:

```text
CAB_FINAL_PRE_REVIEW_HARDENING_COMPLETE
COMPACT20_REVIEW_PACKET_EVIDENCE_VERIFIABLE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
CAB_LEVEL5_COMPLETE=false
```

---

# 3. Non-Negotiable Boundaries

Do not:

- create human judgments;
- create adjudication;
- run real models;
- call providers;
- run paid compute;
- run GPU inference;
- fabricate tool outputs;
- fabricate artifacts;
- fabricate smoke throughput;
- convert fixture evidence into genuine evidence;
- claim empirical validation;
- create new benchmark scales;
- add Main-500;
- add new generic platform layers;
- rewrite the scheduler, registry, evidence graph, evaluator, or review OS;
- weaken C10;
- weaken scorer-v3 endpoint separation;
- restore text-only recovery credit;
- expose reviewer identities;
- expose protected held-out task bodies;
- commit private candidate bodies;
- commit signing secrets;
- trust an “approved” directory name as scientific approval;
- treat models as independent task replications without an explicit covariance model;
- claim measured runtime from assumptions;
- force-push;
- create a branch or pull request;
- stage unrelated existing user work.

Always:

- inspect before modifying;
- preserve all valid prior hardening work;
- preserve historical reports;
- version all changed scientific contracts;
- record old and new hashes;
- fail closed;
- use deterministic generation;
- distinguish static validation from executable validation;
- distinguish planning assumptions from measurements;
- update paper, claims, configs, tests, reports, and gates together;
- run full provider-free validation before publication;
- push only task-owned public-safe files directly to `main`;
- verify local and remote SHA equality;
- report CI truthfully.

---

# 4. Baseline Audit and Task-Owned Ledger

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
```

Create:

- `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_BASELINE.md`
- `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_STATE.json`
- `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_LEDGER.md`
- `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_DECISIONS.md`
- `cab_final_pre_review_handoff.md`

Record:

- starting SHA;
- current branch and divergence;
- all existing modified/untracked user-owned paths;
- exact task-owned paths;
- current Compact packet hashes;
- current scorer version;
- current endpoint version;
- current power assumptions;
- current approval mechanism;
- current reachability classification;
- current release-manifest state;
- current evidence counters.

Do not modify or stage pre-existing user-owned paths unless they are explicitly part of this task and the baseline report records that decision.

---

# 5. Phase A — Reviewer-Verifiable Evidence Bundles

## A1. Problem

Human reviewers currently receive task descriptions, declared required information, gold answers, scorer policy, intervention descriptions, and intended evidence routes.

That is insufficient for independent validation of:

- clean-gold correctness;
- intervention solvability;
- scorer compatibility;
- abstention opportunity;
- recovery feasibility;
- manipulation validity.

Reviewers must inspect the actual controlled evidence rather than trust designer-authored summaries.

## A2. Evidence-bundle contract

Create a typed reviewer evidence-bundle schema.

For every Compact item, the bundle must contain or safely reference:

```text
candidate_id
base_task_id
clean_instance_id
intervention_instance_id
schema_version
artifact_inventory
artifact_hashes
artifact_mime_types
tool_contracts
clean_tool_availability
intervention_tool_availability
clean_tool_fixture_snapshots
intervention_tool_fixture_snapshots
required_fact_ids
fact_to_artifact_mapping
fact_to_tool_mapping
fact_to_output_mapping
clean_gold_derivation
intervention_valid_response_routes
abstention_opportunity
clarification_opportunity
recovery_routes
manipulation_check
non_target_invariants
reviewer_safe_redactions
bundle_hash
```

The bundle must be sufficient for a qualified reviewer to independently answer:

1. Is the clean gold answer supported?
2. Can the required facts be recovered through the declared clean tools?
3. After intervention, is a substantive answer still possible?
4. If not, is clarification, recovery, or abstention justified?
5. Does the scorer accept exactly the defensible response types?
6. Did the intervention alter only the intended factor?

## A3. Inspectable artifacts

For each Compact item, provide inspectable controlled artifacts such as:

- CSV/XLSX fixture tables;
- Markdown/PDF fixture documents;
- email fixtures;
- JSON/YAML configs;
- database snapshots;
- log excerpts;
- policy text;
- deterministic tool-response transcripts;
- repository fixtures;
- task-specific source records.

Use existing controlled fixtures when available.

When artifacts are generated, generation must be deterministic and source-controlled if public-safe.

Protected/private content must remain outside Git, with only public commitments and schemas tracked.

## A4. Tool fixture snapshots

For each declared route, produce reviewer-safe fixture transcripts:

```text
input tool call
normalized arguments
tool availability
returned observation
observation hash
source artifact hash
fact IDs supported
```

Do not include model outputs.

These are environment fixtures, not empirical trajectories.

## A5. Gold derivation

Create a deterministic gold-derivation receipt per item.

It must show:

```text
source facts
normalization rules
calculation steps
answer-contract transformation
final gold answer
derivation hash
```

Gold must be machine-reconstructable from the evidence bundle.

## A6. Public/private split

Track publicly:

- schemas;
- generators;
- validators;
- aggregate reports;
- public fixture artifacts when safe;
- commitments and hashes.

Keep private:

- protected held-out task bodies;
- private reviewer assignments;
- reviewer identities;
- private candidate source records;
- hidden future evaluation data.

Acceptance state:

```text
CAB_COMPACT_REVIEW_EVIDENCE_BUNDLES_READY
```

---

# 6. Phase B — Two-Stage Blinded Human Validation

## B1. Motivation

Reviewers should not see the designer’s gold answer and intended response route before independently judging task validity and evidence sufficiency.

Create a two-stage workflow.

## B2. Stage 1 — Evidence and intervention validity

Reviewer sees:

- task instruction;
- clean artifacts;
- intervention artifacts;
- clean/intervention tool contracts;
- deterministic fixture outputs;
- manipulation description;
- non-target invariants;
- required information categories;
- no model identity;
- no model output;
- no gold answer;
- no intended abstention/recovery verdict;
- no scorer acceptance decision.

Stage-1 judgments:

```text
task_clarity
artifact_integrity
clean_solvability
intervention_manipulation_success
goal_preservation
invariance_preservation
intervention_substantive_solvability
clarification_opportunity_exists
abstention_opportunity_exists
recovery_route_exists
realism
ambiguity
exclusion_recommendation
confidence
substantive_note
```

## B3. Stage 2 — Gold and scorer audit

After Stage 1 is immutably submitted, reviewer sees:

- gold derivation;
- final clean gold;
- intervention answer contract;
- scorer policy;
- allowed response types;
- proposed recovery action set.

Stage-2 judgments:

```text
clean_gold_correctness
intervention_gold_or_safe_response_correctness
answer_contract_correctness
scorer_compatibility
abstention_policy_correctness
recovery_policy_correctness
false_abstention_risk
scorer_false_positive_risk
scorer_false_negative_risk
exclusion_recommendation
confidence
substantive_note
```

## B4. Blinding and immutability

Enforce:

- Stage 1 must be final before Stage 2 unlocks;
- no Stage-2 content leaks into Stage-1 packet;
- Stage-1 hashes bind the evidence bundle;
- reviewer orders remain independently randomized;
- adjudicator receives both stages plus disagreement context;
- amendments preserve immutable history;
- public exports remain identity-safe.

## B5. Qualification update

Qualification must test ability to:

- inspect artifacts;
- trace facts to evidence;
- identify unsupported gold;
- distinguish solvability from safe abstention;
- detect scorer over-credit;
- detect recovery-route mismatch.

Regenerate qualification examples and expected rationales.

## B6. Packet regeneration

Regenerate:

- Stage-1 review items;
- Stage-1 judgment sheet/schema;
- Stage-2 scorer items;
- Stage-2 judgment sheet/schema;
- reviewer instructions;
- evidence-bundle guide;
- adjudication schema;
- qualification packet;
- packet manifest;
- commitments;
- hashes.

Explicitly invalidate every superseded blank Compact packet and prior hash.

Acceptance state:

```text
CAB_TWO_STAGE_HUMAN_REVIEW_READY
```

---

# 7. Phase C — Exact Authorized Recovery Semantics

## C1. Required behavior

A recovery outcome may receive credit only when all of the following hold:

```text
a genuine failure occurred
AND
the recovery action occurred after that failure
AND
the executed action matches an allowed preregistered recovery action
AND
the action’s arguments satisfy its contract
AND
the action produced an acceptable observation
AND
the observation causally supports the recovered answer
AND
the final substantive answer is correct
```

## C2. Typed recovery action contract

Create a schema containing:

```text
action_id
action_type
allowed_tool_names
allowed_argument_schema
required_preconditions
failure_types_addressed
success_observation_predicate
supported_fact_ids
maximum_attempts
budget_cost
terminal_or_nonterminal
```

## C3. Exact matching

Do not accept:

- any truthy `recovery_action` metadata;
- arbitrary alternate tools;
- action-name substring matching;
- final-answer claims;
- unrelated successful observations;
- fabricated recovery markers;
- a correct final answer unsupported by the recovery observation.

Require exact canonical action ID or an explicitly declared equivalent action class.

## C4. Causal evidence binding

When `task_recovered=true`, record:

```text
failure_event_id
recovery_action_event_id
recovery_observation_event_id
supported_fact_ids
final_answer_event_id
causal_binding_hash
```

## C5. Multiple attempts

Handle:

- several permitted attempts;
- failed first recovery followed by successful second recovery;
- unauthorized attempt followed by authorized attempt;
- authorized attempt exceeding budget;
- recovery after terminal failure;
- recovery before failure;
- unrelated tool calls after failure.

## C6. Required tests

Add adversarial tests for:

- wrong recovery action ID;
- unauthorized alternate tool;
- valid metadata without actual action;
- actual action with invalid arguments;
- actual action before failure;
- actual action after failure but no useful observation;
- unrelated successful observation;
- authorized action with supported evidence;
- authorized action followed by wrong final answer;
- authorized action followed by correct final answer;
- correct answer that did not use recovery evidence;
- several recovery attempts;
- budget violation;
- substring collision between action names.

Acceptance state:

```text
CAB_RECOVERY_AUTHORIZATION_V4_READY
```

---

# 8. Phase D — Executable Evidence-Route Reachability

## D1. Rename existing gate accurately

If the current gate only validates declarative consistency, rename it:

```text
static_intervention_policy_reachability
```

Do not describe it as executable route validation.

## D2. Executable route harness

Create an executable fixture harness that, for every Compact item:

1. materializes the clean environment;
2. verifies artifact hashes;
3. invokes the declared clean route;
4. retrieves required facts;
5. reconstructs the clean gold;
6. applies the intervention;
7. verifies non-target invariant hashes;
8. invokes each declared surviving route;
9. determines whether substantive completion is possible;
10. determines whether recovery is possible;
11. determines whether clarification is necessary;
12. determines whether abstention is justified;
13. verifies the scorer contract matches the executable result.

## D3. Route outcomes

Each item must receive one or more executable outcomes:

```text
substantive_answer_route_verified
recovery_route_verified
clarification_route_verified
justified_abstention_route_verified
no_valid_route
```

## D4. Fact coverage

Every required fact must be linked to:

- source artifact;
- tool invocation;
- observation;
- normalization step;
- gold derivation.

No “route exists” assertion may rely only on a tool name remaining in a list.

## D5. Intervention isolation

Verify:

- target factor changes;
- non-target artifacts remain hash-identical unless explicitly permitted;
- hidden ground truth remains stable unless the intervention contract says otherwise;
- answer-contract changes are justified by executable evidence availability.

## D6. Commands

Provide:

```bash
cab benchmark static-reachability-check
cab benchmark executable-reachability-check
cab benchmark gold-reconstruction-check
cab benchmark intervention-isolation-check
```

Acceptance requires:

```text
20/20 Compact executable routes classified
20/20 clean gold reconstructions pass
0 unsupported facts
0 unexplained non-target changes
```

Acceptance state:

```text
CAB_COMPACT_EXECUTABLE_REACHABILITY_READY
```

---

# 9. Phase E — Cryptographic Scientific Approval Receipts

## E1. Eliminate path-name approval

No scientific runner, notebook, importer, planner, or evidence promotion path may trust directory names such as:

```text
approved/
approved_bundle/
private_data/approved/
```

A path may be storage metadata only.

## E2. Approval receipt schema

Create a signed or hash-bound receipt containing:

```text
receipt_version
study_id
packet_version
packet_manifest_hash
evidence_bundle_manifest_hash
stage1_review_export_hash
stage2_review_export_hash
reviewer_qualification_aggregate_hash
adjudication_export_hash
c10_certificate_hash
approved_item_hashes
excluded_item_hashes
exclusion_reason_hash
scorer_version
endpoint_version
reachability_report_hash
gold_reconstruction_report_hash
intervention_isolation_report_hash
system_identity_manifest_hash
analysis_plan_hash
power_plan_hash
resource_plan_hash
slice_lock_timestamp
issuer
signature_or_transparency_log_reference
```

## E3. Validation

Scientific execution must fail unless:

- receipt schema is valid;
- all referenced hashes resolve;
- C10 status is genuine PASS;
- packet and evidence-bundle hashes match;
- current scorer and endpoint versions match;
- all approved items passed executable reachability;
- no excluded item appears in execution manifest;
- receipt is not revoked;
- receipt was issued after all required evidence.

## E4. Replay and substitution protection

Reject:

- receipt from another packet;
- stale scorer version;
- stale endpoint version;
- substituted system identity;
- altered task body;
- altered tool fixture;
- revoked receipt;
- path rename masquerading as approval.

## E5. Fixture demonstration

Use fixture-only synthetic receipts to demonstrate:

- valid receipt accepted in non-scientific fixture mode;
- missing C10 rejected;
- wrong packet hash rejected;
- wrong scorer rejected;
- wrong system identity rejected;
- revoked receipt rejected;
- approved-looking path without receipt rejected.

Acceptance state:

```text
CAB_CRYPTOGRAPHIC_APPROVAL_GATE_READY
```

---

# 10. Phase F — Hierarchical and Clustered Prospective Power

## F1. Correct experimental units

The simulator must not automatically multiply effective sample size by model count.

Support explicitly distinct estimands.

## F2. Required estimands

Produce separate prospective precision and power for:

### Per-model paired degradation

```text
clean versus intervention within the same base tasks for one model/policy
```

### Pooled hierarchical degradation

```text
population-average degradation across systems with base-task clustering
```

### Model × intervention-family interaction

```text
whether systems differ in family-specific robustness
```

### Family-level degradation

```text
paired effect within each intervention family
```

### RAAC within-model improvement

```text
standard versus RAAC under equal budget on the same base tasks
```

### RAAC non-inferiority on clean tasks

```text
clean completion loss relative to the frozen margin
```

### Ranking instability

```text
probability of rank reversal or unresolved ordering
```

### Safe-response and false-abstention outcomes

```text
precision for justified safety and unnecessary avoidance
```

## F3. Hierarchical simulation model

Implement simulation with configurable:

```text
base-task random effect
model effect
policy effect
intervention-family effect
difficulty effect
domain effect
model × family interaction
model × difficulty interaction
repeat noise
paired discordance structure
scorer error
human exclusion
missing trajectories
systematic missingness
```

## F4. Binary paired outcome generation

Model the four paired cells explicitly:

```text
clean=1, intervention=1
clean=1, intervention=0
clean=0, intervention=1
clean=0, intervention=0
```

Power for paired degradation must derive from discordant probabilities and clustering, not an unsupported generic variance shortcut.

## F5. Analysis-model parity

The prospective simulator must match the frozen confirmatory analysis as closely as practical.

If confirmatory inference uses:

- clustered bootstrap;
- mixed-effects logistic regression;
- permutation;
- paired exact tests;
- Bayesian hierarchical analysis;

then power should be estimated for the intended decision rule.

## F6. Required scenarios

Run and report:

- Compact-20 pilot;
- Scale-100 current plan;
- Scale-100 one model;
- Scale-100 five models analysed separately;
- pooled hierarchical Scale-100;
- increased task count;
- increased repeats;
- reduced model panel;
- scorer error sensitivity;
- 10%, 20%, and 30% human exclusion;
- 5%, 10%, and 20% missingness;
- family-level effects;
- RAAC equal-budget improvement;
- clean non-inferiority;
- ranking instability.

## F7. Replace unsupported claims

Remove or revise any report that states:

```text
Scale power = 0.999295
```

unless the corrected simulator reproduces that value under a clearly named estimand and justified covariance model.

Every power value must state:

- estimand;
- experimental unit;
- assumptions;
- analysis method;
- number of simulations;
- Monte Carlo error;
- seed;
- exclusion/missingness assumptions.

## F8. Decision report

Create a recommendation answering:

- Is Scale-100 sufficient for the primary per-model effect?
- Is it sufficient for family effects?
- Is it sufficient for model × family interactions?
- Is it sufficient for RAAC claims?
- Are more tasks or more repeats more valuable?
- Should the model panel be reduced or stratified?

Acceptance state:

```text
CAB_HIERARCHICAL_POWER_PLAN_READY
```

---

# 11. Phase G — Runtime Calibration and Resource Uncertainty

## G1. Separate assumed from measured

Resource reports must distinguish:

```text
manifest_exact_counts
planning_assumptions
fixture_measurements
live_smoke_measurements
projected_intervals
observed_full_run_measurements
```

No assumption may be labelled as measured.

## G2. Calibration hooks

Prepare but do not execute real-model smoke runs.

Create a smoke-result ingestion schema containing:

```text
system_identity_hash
model_revision
quantization
adapter_hash
prompt_hash
task_id
policy
model_calls
tool_calls
input_tokens
output_tokens
wall_time
peak_vram
peak_ram
artifact_bytes
retry_count
failure_reason
```

## G3. Projection update

After future smoke ingestion, resource planner must estimate:

- median runtime;
- p90 runtime;
- confidence interval;
- per-system throughput;
- shard duration;
- storage interval;
- expected failure reserve;
- Kaggle-session count;
- CPU merge and scorer time.

## G4. Current reports

Until smoke exists, label all GPU runtime numbers:

```text
ASSUMPTION_BASED_PRE_SMOKE_PROJECTION
```

## G5. RAAC 81,000-trajectory risk

The current full ablation plan is too large to treat as the default immediate run.

Create a prospectively staged design.

### Wave A — Compact feasibility

- all planned systems;
- Standard;
- RAAC-Light;
- selected small mechanism subset;
- pilot-only inference.

### Wave B — Mechanism ablation

- two preregistered representative systems;
- full component ablations;
- all Compact items;
- explicit selection rationale fixed before outcomes.

### Wave C — Scale confirmation

- all systems;
- Standard;
- only preregistered winning/retained RAAC variants;
- equal-budget primary comparison.

### Wave D — Optional robustness expansion

Run only when prospectively triggered by predefined Compact/Scale criteria.

## G6. Stop and continuation rules

Freeze rules for:

- dropping a mechanically broken variant;
- retaining a variant;
- expanding to all models;
- reporting an informative null;
- terminating excessive-overhead variants;
- prohibiting outcome-driven cherry-picking.

Acceptance state:

```text
CAB_SMOKE_CALIBRATION_AND_STAGED_RAAC_PLAN_READY
```

---

# 12. Phase H — Clean-Checkout Release Reproducibility

## H1. Problem

The current development release manifest was generated from a dirty checkout because pre-existing user-owned files were present.

That is acceptable for development but not the final scientific release.

## H2. Clean release mode

Implement a clean release path that:

1. creates a Git archive or clean temporary clone at a specific commit;
2. verifies zero uncommitted files inside the clean environment;
3. builds wheel and sdist;
4. regenerates release inventory;
5. regenerates bundle hash;
6. runs clean import;
7. runs release dry run;
8. verifies deterministic public-safe inventory;
9. records source commit and tree hash;
10. emits a clean-release receipt.

## H3. Development mode

Development manifests may still record a dirty checkout, but must be labelled:

```text
DEVELOPMENT_SNAPSHOT_NOT_FINAL_RELEASE
```

## H4. Final pre-review demonstration

Run clean-checkout fixture reproduction for the current code and public packet commitments.

This does not create scientific evidence.

Acceptance state:

```text
CAB_CLEAN_RELEASE_PATH_READY
```

---

# 13. Phase I — Terminology, Claims, and Documentation Corrections

Audit the entire repository for overstatements.

Correct language including:

- “reachability passed” when only static policy consistency passed;
- “naturalistic” when the study is artifact-rich synthetic;
- “measured runtime” when projected;
- “power” without estimand/experimental-unit definition;
- “recovery succeeded” without authorized causal execution;
- “review packet ready” without inspectable evidence;
- “approval” based on path names;
- “pre-run complete” before final reviewer evidence verification.

Update:

- `CURRENT_PROJECT_STATE.md`;
- `README.md`;
- methods docs;
- human-validation protocol;
- scorer docs;
- recovery docs;
- power reports;
- resource reports;
- transfer docs;
- paper methods;
- claim ledger;
- execution gate docs;
- handoffs;
- status generators.

Correct state before completion:

```text
CAB_PRE_RUN_SCIENTIFIC_HARDENING_SUBSTANTIALLY_COMPLETE
FINAL_PRE_REVIEW_FIXES_IN_PROGRESS
```

Correct state after all acceptance criteria pass:

```text
CAB_FINAL_PRE_REVIEW_HARDENING_COMPLETE
COMPACT20_REVIEW_PACKET_EVIDENCE_VERIFIABLE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
```

---

# 14. Phase J — Independent Adversarial Audit

Do not rely only on unit tests written alongside the implementation.

Create an independent adversarial audit module that attempts to break the final contracts.

## J1. Reviewer bundle attacks

Test:

- gold answer unsupported by artifacts;
- altered artifact with stale hash;
- missing fact mapping;
- tool fixture contradicting source artifact;
- Stage-2 gold leaked into Stage 1;
- review packet points to wrong bundle;
- protected content leaks publicly.

## J2. Recovery attacks

Test:

- wrong action ID;
- action substring collision;
- fake metadata;
- unrelated success;
- recovery before failure;
- unsupported final answer;
- stale action contract;
- budget overflow.

## J3. Approval attacks

Test:

- approved-looking path without receipt;
- substituted packet;
- substituted scorer;
- substituted system identity;
- revoked receipt;
- receipt replay;
- missing C10;
- excluded item inserted.

## J4. Reachability attacks

Test:

- declared tool with missing artifact;
- declared route returning wrong fact;
- hidden dependence on removed tool;
- non-target artifact mutation;
- gold reconstruction mismatch;
- unjustified abstention contract.

## J5. Power attacks

Test:

- model-count pseudo-replication;
- repeated tasks treated as independent;
- wrong paired-cell probabilities;
- zero interaction variance;
- missingness ignored;
- exclusion ignored;
- Monte Carlo instability;
- contradictory estimand labels.

## J6. Resource attacks

Test:

- assumed runtime marked measured;
- manifest counts disagree with report;
- missing retry reserve;
- impossible shard duration;
- full ablation enabled without trigger.

Produce:

- attack inventory;
- prevented/detected/contained/manual-review/unmitigated status;
- exact residual risk;
- zero silent critical failures.

Acceptance state:

```text
CAB_FINAL_PRE_REVIEW_ADVERSARIAL_AUDIT_PASSED
```

---

# 15. Phase K — Final Packet and Approval Dry Run

Using fixture-only non-scientific data:

1. generate Stage-1 packets;
2. validate evidence bundles;
3. submit fixture Stage-1 judgments;
4. unlock Stage 2;
5. submit fixture Stage-2 judgments;
6. create fixture disagreement;
7. adjudicate fixture disagreement;
8. run fixture C10;
9. issue fixture approval receipt;
10. attempt scientific run without receipt and verify rejection;
11. attempt fixture-mode run with valid fixture receipt and verify acceptance;
12. verify no genuine evidence counters increment;
13. regenerate the real blank Compact packet;
14. verify real packet remains `HUMAN_INPUT_REQUIRED`.

Do not use fixture judgments as genuine evidence.

Acceptance state:

```text
CAB_FINAL_REVIEW_AND_APPROVAL_DRY_RUN_READY
```

---

# 16. Anti-Regression Gates

Add one final workflow:

`.github/workflows/final-pre-review-hardening.yml`

It must check:

## Reviewer evidence

- every Compact item has an evidence bundle;
- bundle hashes resolve;
- gold reconstructs;
- Stage-1 packet excludes gold/scorer verdicts;
- Stage-2 binds to immutable Stage-1 submission;
- public/private split is clean.

## Recovery

- exact action authorization;
- post-failure ordering;
- observation support;
- correct final answer;
- no metadata-only success;
- no unrelated-tool success.

## Reachability

- static checks pass;
- executable route harness passes;
- gold reconstruction passes;
- intervention isolation passes.

## Approval

- path name alone is insufficient;
- receipt hashes bind all required artifacts;
- revoked/stale/substituted receipts fail.

## Power

- no pseudo-replication by model count;
- estimand and experimental unit present;
- simulation deterministic under fixed seed;
- Monte Carlo error reported;
- analysis-model parity recorded.

## Resource planning

- assumptions and measurements separated;
- smoke schema valid;
- RAAC staged plan present;
- full ablation requires trigger.

## Release

- clean-checkout release path works;
- development snapshots labelled correctly.

## Evidence safety

All genuine evidence counters remain zero.

Expected final gate:

```text
CAB_FINAL_PRE_REVIEW_HARDENING_COMPLETE
COMPACT20_REVIEW_PACKET_EVIDENCE_VERIFIABLE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
```

---

# 17. Required Demonstrations

## Demo 1 — Reviewer evidence verification

For at least four representative Compact items spanning all four intervention families:

- open source artifact;
- invoke fixture tool;
- retrieve fact;
- reconstruct clean gold;
- apply intervention;
- classify valid response route;
- prove packet hashes.

## Demo 2 — Two-stage blinding

Show Stage 1 contains no gold/scorer verdict.

Show Stage 2 remains locked before Stage-1 final submission.

Show Stage 2 unlocks afterward.

## Demo 3 — Recovery authorization

Show:

- wrong action rejected;
- unrelated successful tool rejected;
- correct authorized fallback attempted;
- correct fallback observation accepted;
- correct final answer required for task recovery.

## Demo 4 — Cryptographic approval

Show:

- approved-looking directory rejected;
- valid fixture receipt accepted only in fixture mode;
- substituted task rejected;
- stale scorer rejected;
- revoked receipt rejected.

## Demo 5 — Executable reachability

Show 20/20 Compact items receive executable classifications and clean-gold reconstruction.

## Demo 6 — Corrected power

Show distinct results for:

- per-model effect;
- pooled hierarchical effect;
- family effect;
- model × family interaction;
- RAAC effect;
- ranking instability.

Explain why model count does or does not add independent information for each estimand.

## Demo 7 — Resource calibration readiness

Ingest fixture smoke receipts and update projection intervals.

No real model run.

## Demo 8 — Clean release

Build from a clean archive/clone and produce deterministic release receipt.

---

# 18. Required Reports

Create:

1. `CAB_FINAL_PRE_REVIEW_HARDENING_REPORT.md`
2. `cab_final_pre_review_handoff.md`
3. `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_BASELINE.md`
4. `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_STATE.json`
5. `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_LEDGER.md`
6. `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_DECISIONS.md`
7. `reports/final_pre_review/REVIEWER_EVIDENCE_BUNDLE_REPORT.md`
8. `reports/final_pre_review/TWO_STAGE_REVIEW_REPORT.md`
9. `reports/final_pre_review/RECOVERY_AUTHORIZATION_REPORT.md`
10. `reports/final_pre_review/EXECUTABLE_REACHABILITY_REPORT.md`
11. `reports/final_pre_review/GOLD_RECONSTRUCTION_REPORT.md`
12. `reports/final_pre_review/INTERVENTION_ISOLATION_REPORT.md`
13. `reports/final_pre_review/CRYPTOGRAPHIC_APPROVAL_REPORT.md`
14. `reports/final_pre_review/HIERARCHICAL_POWER_REPORT.md`
15. `reports/final_pre_review/POWER_DESIGN_RECOMMENDATION.md`
16. `reports/final_pre_review/SMOKE_CALIBRATION_READINESS.md`
17. `reports/final_pre_review/STAGED_RAAC_PLAN.md`
18. `reports/final_pre_review/CLEAN_RELEASE_REPORT.md`
19. `reports/final_pre_review/TERMINOLOGY_AND_CLAIM_AUDIT.md`
20. `reports/final_pre_review/ADVERSARIAL_AUDIT.md`
21. `reports/final_pre_review/FINAL_PACKET_DRY_RUN.md`
22. `reports/final_pre_review/FINAL_VALIDATION_LEDGER.md`
23. `reports/final_pre_review/CAB_FINAL_PRE_REVIEW_GITHUB_PUBLISH.md`

Update:

- `CURRENT_PROJECT_STATE.md`;
- reviewer onboarding;
- human-validation protocol;
- scorer docs;
- recovery docs;
- analysis plan;
- resource plan;
- paper methods;
- claim ledger;
- command map;
- release guidance.

---

# 19. Validation Order

## Focused suites

Run after each phase.

Required slices:

- reviewer evidence bundles;
- artifact integrity;
- gold reconstruction;
- two-stage review;
- recovery authorization;
- executable reachability;
- intervention isolation;
- approval receipts;
- power simulation;
- resource calibration;
- RAAC stage gates;
- clean release;
- evidence safety;
- claim safety.

## Full provider-free suite

```bash
python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'
```

## Static checks

- Ruff;
- mypy;
- Codespell;
- JSON/YAML validation;
- schema validation;
- `git diff --check`;
- package metadata.

## Security and privacy

- protected-payload scan;
- reviewer-identity scan;
- secret scan;
- public/private split;
- archive safety;
- receipt replay tests;
- path-name approval bypass tests.

## Documentation

```bash
mkdocs build --strict
```

## Packaging and release

- wheel;
- sdist;
- Twine;
- clean import;
- CLI smoke;
- clean-checkout release build;
- release dry run;
- release inventory verification.

## Final commands

Provide and run:

```bash
cab benchmark static-reachability-check
cab benchmark executable-reachability-check
cab benchmark gold-reconstruction-check
cab benchmark intervention-isolation-check
cab approval verify --fixture
cab power validate
cab final-pre-review check
```

Expected:

```text
CAB_FINAL_PRE_REVIEW_HARDENING_COMPLETE
COMPACT20_REVIEW_PACKET_EVIDENCE_VERIFIABLE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
```

---

# 20. Acceptance Criteria

The task is complete only when all conditions below hold.

## Reviewer evidence

- every Compact item has inspectable source evidence;
- every required fact maps to artifacts, tools, and observations;
- clean gold reconstructs deterministically;
- reviewer can independently verify solvability;
- Stage 1 is free of gold/scorer anchoring;
- Stage 2 is immutable and correctly bound;
- old packets are invalidated.

## Recovery

- exact authorized action required;
- action must occur after failure;
- action arguments must validate;
- observation must support required facts;
- correct final answer required;
- unrelated actions cannot receive recovery credit;
- text and metadata cannot fake execution.

## Reachability

- static and executable checks are distinct;
- 20/20 clean gold reconstructions pass;
- every intervention has a verified response route or is excluded;
- no required fact is unsupported;
- no unexplained non-target mutation exists.

## Approval

- path-name approval removed;
- cryptographic receipt binds all required evidence;
- stale, substituted, revoked, or replayed receipts fail;
- no scientific run can start before genuine C10 and valid receipt.

## Power

- experimental unit is explicit;
- model pseudo-replication removed;
- paired cells modelled correctly;
- hierarchical dependence represented;
- per-model, pooled, family, interaction, RAAC, and ranking outputs exist;
- Monte Carlo error reported;
- unsupported 0.999295 claim removed or justified.

## Resources

- counts remain manifest-exact;
- assumed and measured values separated;
- smoke ingestion ready;
- staged RAAC plan frozen;
- full ablation cannot launch without trigger.

## Release

- clean-checkout release path works;
- development snapshot is clearly labelled;
- release receipt binds clean source commit.

## Evidence boundary

All genuine evidence counters remain zero.

---

# 21. Publication

Before staging:

```bash
git status --short
git diff --stat
git diff
git diff --check
```

Stage only task-owned public-safe files.

Never stage:

- reviewer identities;
- completed genuine judgments;
- protected candidate bodies;
- raw private evidence;
- signing secrets;
- unrelated user work;
- local caches;
- build output;
- private smoke data.

Recommended commits:

```text
Make CAB human validation evidence-verifiable
Harden CAB recovery, reachability, and approval semantics
Correct CAB power and execution planning
Finalize CAB reviewer-ready scientific gate
```

Use fewer commits when coherent.

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

Observe required CI with a bounded wait.

Do not claim total green while workflows remain active.

Pages enablement remains an external repository setting and must not block this scientific gate if strict documentation builds pass.

---

# 22. Final Response Format

## Final state

Use exactly one:

```text
CAB_FINAL_PRE_REVIEW_HARDENING_COMPLETE
PARTIAL_SUCCESS_FINAL_FIXES_REMAIN
LOCAL_FINAL_PRE_REVIEW_COMPLETE_PUSH_BLOCKED
FINAL_PRE_REVIEW_BLOCKED_BY_REPOSITORY_INCONSISTENCY
```

## Reviewer evidence

Report bundle coverage, artifact counts, gold reconstruction, blinding, and packet hashes.

## Recovery

Report exact authorization behavior and adversarial cases.

## Reachability

Report static versus executable results.

## Approval

Report receipt binding and bypass tests.

## Power

Report each estimand, experimental unit, assumptions, results, and design recommendation.

## Resources

Report exact counts, assumption labels, calibration readiness, and staged RAAC plan.

## Release

Report clean-checkout build and bundle hash.

## Validation

Report exact tests, static checks, security, docs, packaging, and gates.

## Scientific evidence

Report all genuine counters; they must remain zero.

## GitHub

Report commits, local SHA, remote SHA, and honest CI state.

## Exact next action

After genuine success, the exact next action is:

> Recruit and onboard two genuine qualified independent Compact-20 reviewers using the new Stage-1 evidence-verification packet and Stage-2 scorer packet, plus a separate adjudicator.

---

# 23. Final Directive

This is the last pre-review engineering pass.

Do not make CAB larger.

Make the existing science independently verifiable.

Give reviewers the evidence required to check the gold, routes, interventions, and scorer.

Require exact authorized recovery.

Require executable reachability.

Replace path-name approval with cryptographic evidence binding.

Correct the power model to respect task clustering and model dependence.

Separate assumptions from measurements.

Stage RAAC prospectively.

Make release reproduction clean-checkout based.

Add independent adversarial gates.

Publish safely to `main`.

Then stop engineering and begin genuine human review.
