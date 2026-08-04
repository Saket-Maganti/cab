# CAB ICLR Ultimate One-Shot Build Completion Prompt

## Intended Use

Run this prompt in Codex at:

> **Effort: Ultra**

Repository:

`/Users/saketmaganti/Projects/causal-agent-bench`

GitHub repository:

`Saket-Maganti/cab`

Current verified Prompt 1 commit:

`d3469045a78de3a20b37783b29167805e7417e04`

This prompt supersedes:

- `CAB_ICLR_ONE_HOUR_CODEX_SPRINT.md`;
- the standalone Prompt 1 post-fix repair;
- separate build prompts 02–05 where their work can be completed in this pass.

The goal is to use the available Ultra budget aggressively and complete as much of the remaining **ICLR pre-execution build** as possible in one continuous run.

After this prompt, the repository should ideally require only:

1. genuine human review;
2. adjudication and C10;
3. slice locking;
4. real model execution;
5. postrun analysis;
6. final paper writing from audited evidence.

Do not execute scientific model runs in this prompt.

---

# 1. Role

Act simultaneously as:

- an ICLR area-chair-level research reviewer;
- a tool-using-agent evaluation researcher;
- a causal and controlled-intervention methodology reviewer;
- a statistical-methodology reviewer;
- a benchmark-leakage and contamination auditor;
- an agent-systems architect;
- a recovery and abstention method designer;
- a human-evaluation protocol designer;
- a dataset and benchmark-construction lead;
- a Kaggle dual-T4 inference engineer;
- a Mac resource-optimisation engineer;
- a reproducibility and release engineer;
- and a research-paper infrastructure lead.

Your mission is to turn the current CAB repository into the strongest possible **ICLR-ready pre-execution research system** within the user’s real resource envelope.

---

# 2. Actual Resource Envelope

Assume the user has only:

- MacBook Air M4;
- 16 GB unified memory;
- 512 GB storage;
- free Kaggle notebooks with two NVIDIA T4 GPUs when available;
- no A100 or H100 cluster;
- no guaranteed paid API budget;
- no remote background compute;
- limited Kaggle session duration;
- limited local storage.

Every design must be feasible under these constraints.

Prefer:

- streaming;
- compression;
- deterministic sharding;
- quantisation;
- resumability;
- checkpointing;
- bounded concurrency;
- low-memory analysis;
- compact artifacts;
- incremental exports;
- optional provider lanes rather than required provider dependence.

Do not solve problems by assuming more compute.

---

# 3. Scientific Identity

The target ICLR paper identity is:

> **Success Is Not Skill: Intervention-Validated Robustness Evaluation and Recovery for Tool-Using Agents**

CAB must become:

> a general methodology for constructing valid controlled interventions, measuring robustness with paired inference, improving robustness with a recovery-aware controller, and testing whether controlled robustness predicts failures in naturalistic workflows.

The benchmark is the empirical vehicle.

It is not the sole contribution.

The intended contribution stack is:

1. intervention-validity methodology;
2. paired robustness inference;
3. Recovery-Aware Agent Control;
4. naturalistic predictive validity;
5. a leakage-resistant and reproducible benchmark release.

---

# 4. Non-Negotiable Boundaries

Do not:

- call external model APIs;
- launch provider inference;
- launch Kaggle jobs;
- run real Hugging Face or local model inference;
- download large model weights;
- execute Compact-20;
- execute Scale-100;
- execute naturalistic transfer;
- execute Main-500;
- fabricate human review;
- generate fake reviewer identities;
- fabricate trajectories;
- fabricate scores;
- fabricate confidence intervals;
- fabricate paper tables or plots;
- claim model rankings;
- claim RAAC improvements;
- select benchmark tasks based on model performance;
- expose gold answers to agent-facing code;
- expose intervention labels to RAAC;
- weaken leakage gates to pass tests;
- mark fixture outputs as evidence;
- commit, push, tag, or rewrite history unless explicitly authorised;
- destroy unrelated user work;
- silently remove files;
- print or store secrets.

Allowed:

- source-code repair;
- deterministic fixture execution;
- CPU-only tests;
- static analysis;
- schema validation;
- task generation without model inference;
- leakage analysis;
- notebook fixture execution;
- paper compilation with placeholders;
- safe result-pipeline tests;
- cost and runtime estimation labelled as estimates;
- human-review packet generation without filling rows.

All work must preserve evidence classes:

- `DESIGN_ONLY`
- `ENGINEERING_ONLY`
- `FIXTURE_ONLY`
- `HUMAN_INPUT_REQUIRED`
- `EXECUTION_PENDING`
- `PRELIMINARY_REAL_EVIDENCE`
- `AUDITED_REAL_EVIDENCE`
- `PAPER_ELIGIBLE_EVIDENCE`

---

# 5. Working Strategy

## 5.1 Do not restart from zero

Prompt 1 is already implemented.

Preserve:

- the formal problem setup;
- intervention-validity framing;
- paired robustness inference;
- frozen research questions;
- null-result policy;
- reviewer attack matrix;
- paired-metric repairs;
- intervention-validity implementation;
- Prompt 1 tests.

Do not rewrite these merely for stylistic preference.

Extend them canonically.

## 5.2 Build before writing reports

Priority order:

1. fix scientific blockers;
2. implement RAAC;
3. complete human-validation machinery;
4. strengthen Scale-100 and naturalistic datasets;
5. finish M4 and T4×2 execution infrastructure;
6. integrate analysis and paper gates;
7. validate;
8. generate handoff and reports.

Do not spend most of the run generating prose before code works.

## 5.3 Consolidate

Prefer:

- one state engine;
- one split registry;
- one contamination registry;
- one RAAC implementation;
- one run manifest;
- one notebook framework;
- one human-review validator;
- one execution handbook;
- one ICLR handoff.

Do not create duplicate parallel systems.

## 5.4 Keep a live ledger

Create immediately:

`reports/ICLR_ULTIMATE_ONESHOT_LEDGER.md`

Update it after every major phase with:

- files inspected;
- files modified;
- commands;
- exit codes;
- elapsed time;
- blockers;
- decisions;
- next phase.

This is the recovery checkpoint if Codex stops unexpectedly.

---

# 6. Phase 0 — Rapid Current-State Verification

Inspect only what is needed to establish the live state.

Record:

- branch;
- commit;
- Git status;
- uncommitted Prompt 1 work if any;
- latest canonical status;
- evidence counts;
- human-review state;
- C10;
- split registry;
- protected held-out paths;
- current failing tests;
- current agent abstractions;
- current runner and manifest schemas;
- current Kaggle notebooks;
- current Scale-100 and naturalistic candidates;
- current paper scaffold.

Run focused Prompt 1 tests first.

Create:

- `reports/ICLR_ONESHOT_CURRENT_STATE.json`
- `reports/ICLR_ONESHOT_CURRENT_STATE.md`

Do not run the full suite yet.

---

# 7. Phase 1 — Fix Prompt 1 Integration Blockers

## 7.1 Reproduce both known failures

Reproduce:

1. protected held-out payloads tracked in Git;
2. stale test rejecting `METHODOLOGY_READY`.

Capture exact test names and traces.

Do not assume the failures remain unchanged.

## 7.2 Public held-out contamination audit

Identify every publicly exposed protected artifact, including:

- held-out task text;
- challenge tasks;
- hidden answers;
- intervention payloads;
- evaluator-only fields;
- private manifests;
- compressed archives;
- notebooks;
- generated bundles;
- deleted files still in Git history.

Create:

`reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json`

For each artifact record:

- path;
- current tracking state;
- exposure commit;
- task text exposed;
- answer exposed;
- intervention metadata exposed;
- evaluator metadata exposed;
- severity;
- scientific disposition;
- allowed future use.

## 7.3 Permanent scientific invalidation

Any protected payload ever publicly pushed must be treated as permanently contaminated.

Classify it as:

- `PUBLIC_DEVELOPMENT_ONLY`;
- `PILOT_ONLY`;
- `CONTAMINATED_NOT_CONFIRMATORY`;
- or `INVALID_FOR_FUTURE_EVALUATION`.

It must never enter:

- confirmatory Scale-100;
- confirmatory Main set;
- hidden challenge evaluation;
- paper-eligible evidence;
- external-validity claims.

Deleting it from the current branch does not restore secrecy.

## 7.4 Replacement protected architecture

Create a new protected split architecture.

Requirements:

- new split version;
- new IDs;
- new seeds;
- new hashes;
- no reuse of public task text;
- no trivial parameter replacement;
- no answer overlap where avoidable;
- no model-output-based selection;
- no committed private payloads.

Store complete private payloads under an ignored path such as:

`private_data/heldout_challenge_v2/`

or the repository’s canonical private location.

Public Git may contain only:

- schemas;
- deterministic generators;
- non-reversible hashes;
- aggregate counts;
- distribution summaries;
- provenance and licence summaries;
- generation instructions.

Create:

`data/manifests/heldout_challenge_v2_public_manifest.json`

The manifest must not expose:

- task text;
- answers;
- intervention payloads;
- evaluator-only fields;
- reversible encodings.

## 7.5 Contamination tests

Add tests that fail if:

- protected payload text is tracked;
- answer-bearing held-out content is tracked;
- contaminated tasks receive confirmatory roles;
- private payload paths are not ignored;
- public manifests contain forbidden fields;
- exposed IDs are reused;
- public/private exact or near-duplicate overlap exists;
- notebooks or archives embed protected content;
- release bundles contain protected payloads.

Do not weaken existing release tests.

## 7.6 History policy

Create:

`docs/PUBLIC_HELDOUT_CONTAMINATION_AND_HISTORY_POLICY.md`

Explain:

- exposure;
- invalidation;
- why deletion is insufficient;
- safe replacement policy;
- optional Git-history rewrite for hygiene;
- why rewriting does not restore scientific secrecy.

Do not execute destructive history rewriting.

## 7.7 Canonical state repair

Repair `METHODOLOGY_READY` state handling by:

- centralising state values;
- importing canonical enums/constants;
- or testing semantic invariants.

Do not add another duplicated hard-coded list.

Add tests proving:

- `METHODOLOGY_READY` is valid;
- unknown states are rejected;
- live execution is blocked;
- human review remains incomplete;
- C10 remains pending;
- paper eligibility remains false.

Run focused blocker tests.

Do not continue until they pass.

---

# 8. Phase 2 — Complete Recovery-Aware Agent Control

Implement the complete pre-execution RAAC method.

Working name:

> Recovery-Aware Agent Control (RAAC)

Rename only if a clearly better, non-inflated name exists.

## 8.1 Method principles

RAAC must:

- be model agnostic;
- receive no intervention labels;
- receive no gold;
- use only observable interaction signals;
- remain compatible with provider and open-model agents;
- have explicit compute bounds;
- expose auditable traces;
- support recovery, verification, clarification, and abstention;
- avoid unnecessary intervention on clean successful trajectories;
- prevent infinite loops.

## 8.2 Canonical state machine

Implement typed states:

- `PLAN`
- `ACT`
- `VALIDATE_OBSERVATION`
- `DETECT_ANOMALY`
- `RETRY`
- `ALTERNATE_ROUTE`
- `CROSS_CHECK`
- `CLARIFY`
- `ABSTAIN`
- `FINAL_VERIFY`
- `ANSWER`
- `TERMINATE`

Define legal transitions.

Invalid transitions must fail closed.

## 8.3 Observable anomaly signals

Implement typed signals for:

- tool error;
- timeout;
- malformed output;
- missing required field;
- schema mismatch;
- contradictory observation;
- stale timestamp;
- inconsistent repeated result;
- partial output;
- impossible value;
- insufficient evidence;
- unverifiable success signal;
- exhausted token budget;
- exhausted tool budget;
- exhausted retry budget;
- infrastructure failure.

Do not inspect:

- intervention family;
- intervention ID;
- condition label;
- hidden expected behaviour;
- answer key;
- evaluator metadata.

Add explicit tests proving hidden metadata is inaccessible or ignored.

## 8.4 Decision policy

Implement typed decisions:

- continue;
- retry same tool;
- use alternate tool;
- cross-check source;
- verify current evidence;
- request clarification;
- qualified answer;
- abstain;
- final verification;
- answer;
- terminate infrastructure failure.

Each decision must include:

- reason code;
- current state;
- trigger signal;
- remaining budgets;
- action;
- trace index;
- evidence class.

## 8.5 RAAC variants

Implement:

### `RAAC_LIGHT`

Designed for limited Kaggle compute.

- one bounded verification;
- one bounded retry;
- optional one alternate route;
- low token overhead.

### `RAAC_FULL`

- multiple bounded checks;
- contradiction resolution;
- alternate route;
- clarification;
- abstention;
- final verification.

### Ablation policies

- `VERIFY_ONLY`
- `RETRY_ONLY`
- `ABSTAIN_ONLY`
- `NO_CROSS_CHECK`
- `NO_ALTERNATE_ROUTE`
- `NO_FINAL_VERIFY`

### Baseline wrappers

- direct answer;
- standard tool use;
- ReAct-style;
- self-check;
- oracle engineering-only control.

## 8.6 Compute contracts

Each policy declares:

- max extra model calls;
- max extra tool calls;
- max retries;
- max alternate routes;
- max verification steps;
- max clarification steps;
- token budget;
- wall-clock budget;
- termination rule.

Provide:

- equal-budget comparison mode;
- practical-budget comparison mode;
- overhead accounting.

## 8.7 Integration

Integrate RAAC into:

- canonical agent interface;
- runner configuration;
- manifest schema;
- result metadata;
- trajectory schema;
- failure taxonomy;
- scorer opportunity flags;
- analysis configuration;
- Kaggle notebook configs;
- provider adapter extension points;
- open-model adapter extension points.

Do not require real model execution.

## 8.8 Deterministic fixture environment

Create fixture tools and observations for:

- clean success;
- transient tool failure;
- persistent failure;
- conflicting observations;
- stale memory;
- malformed output;
- partial output;
- premature success signal;
- insufficient evidence;
- clarification;
- correct abstention;
- false abstention;
- alternate-route recovery.

## 8.9 RAAC tests

Add comprehensive tests for:

- no unnecessary clean intervention;
- bounded retry;
- alternate route after failure;
- contradiction cross-check;
- stale evidence verification;
- malformed-output handling;
- clarification;
- correct abstention;
- false abstention;
- premature success verification;
- exhausted budgets;
- deterministic traces;
- invalid transition rejection;
- hidden label blindness;
- clean budget parity;
- equal-budget mode;
- practical-budget mode;
- light versus full overhead;
- checkpoint and resume;
- no infinite loops;
- evidence-class preservation.

## 8.10 RAAC documentation

Create or update:

- `docs/RAAC_METHOD.md`
- `docs/RAAC_FAIRNESS_AND_BUDGET_POLICY.md`
- `experiments/RAAC_ABLATION_PLAN.md`
- `configs/raac/` canonical policy configs

Add paper-ready pseudocode, but no result claims.

---

# 9. Phase 3 — Complete Human-Validation and C10 Infrastructure

Do not perform human review.

## 9.1 Review protocol

Build complete packets for:

- task clarity;
- clean gold correctness;
- manipulation success;
- goal preservation;
- invariance preservation;
- solvability;
- answer-contract correctness;
- scorer compatibility;
- realism;
- ambiguity;
- exclusion recommendation.

## 9.2 Reviewer design

Support:

- two independent reviewers for Compact-20;
- two or three for Scale-100 where feasible;
- separate adjudicator;
- model-output blinding;
- model-identity blinding;
- reviewer qualification examples;
- expertise disclosure;
- conflict-of-interest disclosure;
- privacy-safe reviewer IDs;
- timestamped judgments.

## 9.3 Agreement analysis

Implement:

- raw agreement;
- Cohen’s kappa where appropriate;
- Krippendorff’s alpha where appropriate;
- prevalence diagnostics;
- confidence intervals;
- adjudication rate;
- exclusion rate;
- family-specific validity;
- reviewer-confidence summaries.

Return blocked states for insufficient samples.

## 9.4 Manipulation checks

Implement deterministic manipulation checks where possible:

- tool absent;
- tool failure injected;
- stale timestamp threshold;
- conflicting observations;
- premature success signal;
- missing evidence;
- distractor presence;
- memory corruption.

Link each intervention to its manipulation check.

## 9.5 C10

Define one canonical C10 contract.

It must require:

- genuine human rows;
- at least two independent reviewers where required;
- no proxy or AI review;
- full candidate coverage;
- threshold satisfaction;
- adjudication complete;
- leakage gate pass;
- answer-contract validity;
- slice hash freeze.

Empty or header-only files must never pass.

## 9.6 Human-resource plan

Create:

`docs/HUMAN_REVIEW_RESOURCE_PLAN.md`

Include:

- Compact-20 reviewer time;
- Scale-100 staged review plan;
- estimated minutes per item;
- adjudication reserve;
- reviewer training;
- quality controls;
- evidence boundaries.

All estimates must be labelled `ESTIMATE_NOT_MEASURED`.

## 9.7 Ethics

Create or update:

- consent language;
- reviewer data handling;
- compensation disclosure;
- expertise disclosure;
- limitations;
- authors-as-reviewers policy.

## 9.8 Tests

Add tests for:

- empty packets;
- header-only files;
- fake IDs;
- duplicated reviewers;
- missing coverage;
- invalid values;
- low agreement;
- unresolved adjudication;
- proxy/AI review rejection;
- genuine pass fixtures clearly labelled fixture-only;
- C10 fail-closed behaviour.

---

# 10. Phase 4 — Strengthen Scale-100

The goal is approximately 100 genuinely distinct base tasks, not 100 superficial variants.

## 10.1 Diversity audit

Measure:

- raw tasks;
- unique base tasks;
- template IDs;
- normalised instruction patterns;
- domains;
- tool combinations;
- answer contracts;
- difficulty;
- intervention families;
- source types;
- exact duplication;
- lexical duplication;
- structural duplication;
- answer overlap;
- role overlap.

Create:

`reports/ICLR_SCALE100_DIVERSITY_AUDIT.md`

## 10.2 Scale-100 requirements

Build or repair a frozen candidate with:

- approximately 100 unique base tasks;
- 8–10 domains where justified;
- multiple tool combinations;
- multiple answer-contract types;
- difficulty balance;
- intervention-family balance;
- low template duplication;
- no Compact-20 overlap;
- no development overlap;
- no contaminated held-out overlap;
- deterministic hashes;
- source and licence metadata;
- manipulation checks;
- human-review packet generation.

Prefer 80 excellent tasks over 100 weak template variants.

## 10.3 Power and allocation

Create a resource-aware prospective design.

Estimate:

- detectable paired degradation;
- cluster count;
- family allocation;
- repeat needs;
- uncertainty width;
- model-panel trajectories.

Do not fabricate measured variance.

Use planning scenarios labelled `ESTIMATE_NOT_MEASURED`.

## 10.4 Freeze protocol

Prepare:

- candidate manifest;
- role registry;
- split hash;
- analysis-plan hash;
- exclusion rules;
- future lock command.

Do not mark the set human-validated or confirmatory-ready.

---

# 11. Phase 5 — Build Naturalistic Transfer Set

Construct a high-quality, resource-feasible naturalistic candidate set.

Target:

- 50–100 tasks;
- quality over size;
- open or locally authorable artifacts;
- realistic tool workflows.

Potential domains:

- document retrieval;
- policy interpretation;
- spreadsheets;
- scheduling;
- file operations;
- data cleaning;
- code debugging;
- configuration diagnosis;
- travel planning;
- conflicting source reconciliation;
- stale records;
- tool outages;
- partial observability.

## 11.1 Every task requires

- provenance;
- licence;
- privacy check;
- PII check;
- prompt-injection scan;
- hidden answer key;
- answer contract;
- tool schema;
- intervention mapping;
- manipulation check;
- human-validation path;
- split role;
- content hash.

## 11.2 Predictive-validity plan

Prepare analysis testing whether naturalistic outcomes are predicted by:

- clean success;
- ACRS;
- clean-conditioned robustness;
- recovery score;
- abstention score;
- worst-family robustness;
- full robustness profile.

Prepare:

- correlation with uncertainty;
- regression;
- calibration;
- leave-one-family-out;
- leave-one-model-out only if model count permits;
- limitations on small model panels.

Do not claim predictive validity before execution.

## 11.3 Leakage and injection

Add checks for:

- hidden answer leakage;
- source overlap;
- prompt injection;
- path leakage;
- task IDs revealing labels;
- private/public role overlap.

## 11.4 Output

Create:

- naturalistic candidate pack;
- public-safe manifest;
- provenance registry;
- licence registry;
- privacy report;
- injection report;
- review packet;
- predictive-validity plan.

---

# 12. Phase 6 — Decide Main-Set Scope

Do not automatically force Main-500.

Create a decision framework comparing:

- Scale-100 only;
- Scale-100 + naturalistic 50–100;
- 150–250 diverse main set;
- Main-500.

Proceed to larger scale only if:

- Scale-100 reveals stable signal;
- naturalistic transfer is meaningful;
- additional statistical power is needed;
- task diversity remains high;
- T4×2 runtime is feasible;
- storage is feasible;
- human validation is feasible.

Create:

`docs/MAIN_SET_RESOURCE_AWARE_DECISION_POLICY.md`

The ICLR paper should prefer scientific diversity over raw count.

---

# 13. Phase 7 — M4 Mac Infrastructure

Optimise all CPU work for the user’s M4 Mac.

## 13.1 Worker limits

Provide safe modes:

- serial;
- low-memory;
- four-worker;
- adaptive.

Avoid unbounded `-n auto`.

## 13.2 Streaming analysis

Use:

- JSONL streaming;
- chunked scoring;
- chunked bootstrap inputs;
- compact intermediate formats;
- compressed archives;
- lazy loading;
- bounded temporary directories.

## 13.3 Disk management

Create tooling for:

- repository disk report;
- model-cache report;
- trajectory-size estimate;
- safe cache cleanup;
- duplicate artifact detection;
- intermediate regeneration policy;
- raw evidence retention;
- compressed shard export.

Never remove raw evidence automatically.

## 13.4 Bootstrap modes

Support:

- 1,000-replicate pilot mode;
- 10,000-replicate final mode;
- deterministic seeds;
- base-task clustering;
- family stratification;
- resumable bootstrap batches;
- mergeable bootstrap shards.

## 13.5 Commands and docs

Create:

- `docs/M4_LOW_MEMORY_WORKFLOW.md`
- low-memory CLI flags;
- safe Make targets;
- CPU runtime estimator;
- disk estimator.

---

# 14. Phase 8 — Kaggle T4×2 Infrastructure Completion

Audit and harden all nine notebooks.

Required notebooks:

1. environment preflight;
2. offline fixture smoke;
3. Compact-20 runner;
4. Scale-100 runner;
5. Main-set runner;
6. RAAC baselines and ablations;
7. merge/audit/rescore;
8. failure recovery;
9. naturalistic transfer.

## 14.1 Default dual-GPU strategy

Use independent data parallelism:

- GPU 0 worker;
- GPU 1 worker;
- deterministic disjoint shards;
- one model instance per GPU when feasible;
- separate ledgers;
- separate checkpoints;
- deterministic merge.

## 14.2 Model compatibility registry

Create configurable metadata:

- model ID;
- revision;
- licence;
- parameter count;
- chat template;
- context;
- tool support;
- recommended quantisation;
- expected VRAM range;
- T4 single-GPU feasibility;
- optional two-GPU placement;
- fallback model.

Do not claim unmeasured VRAM as fact.

Label estimates.

## 14.3 Quantisation

Support:

- fp16;
- 8-bit where appropriate;
- 4-bit;
- optional CPU offload;
- single-GPU fallback;
- actionable OOM recovery.

## 14.4 Session safety

Every notebook must:

- default live execution to false;
- require explicit approval flag;
- validate task hashes;
- validate scorer version;
- checkpoint per task or small batch;
- export each chunk;
- detect completed chunks;
- prevent duplicates;
- resume safely;
- create session manifests;
- compress outputs;
- produce integrity summaries.

## 14.5 RAAC integration

The RAAC notebook must support:

- standard baseline;
- RAAC_LIGHT;
- RAAC_FULL;
- selected ablations;
- budget matching;
- overhead reporting;
- trace export.

## 14.6 Notebook validation

Run:

- JSON validation;
- Python extraction;
- offline fixture execution;
- import checks;
- live-default checks;
- path checks;
- no-secret checks;
- checkpoint/resume;
- merge;
- corruption detection.

Do not guarantee live third-party downloads.

---

# 15. Phase 9 — Model Panel and Resource-Aware Experiment Plan

Create a configurable model panel by category.

Target categories:

- strong open instruct model fitting T4 with quantisation;
- second independent open family;
- smaller efficient open model;
- optional reasoning-oriented open model if feasible;
- optional strong proprietary model;
- optional second provider family.

The paper must remain viable with an open-model core.

## 15.1 Panel constraints

For each model record:

- role;
- capability category;
- exact version at run time;
- estimated VRAM;
- expected Kaggle feasibility;
- tool-calling method;
- licence;
- expected runtime formula;
- fallback.

## 15.2 Experiment tiers

Define:

### Tier 0

One-task live smoke.

### Tier 1

Compact-20:

- 3–4 models;
- standard + RAAC_LIGHT;
- optional RAAC_FULL subset;
- limited repeats.

### Tier 2

Scale-100:

- 5–7 models if resources permit;
- standard + RAAC;
- power-aware repeats;
- open-model core;
- optional provider subset.

### Tier 3

Naturalistic transfer:

- most informative model subset;
- standard + RAAC;
- predictive-validity analysis.

### Tier 4

Main expansion only if justified.

## 15.3 Cost and runtime

Create formulas and low/base/high scenarios.

All values must say:

`ESTIMATE_NOT_MEASURED`

No false precision.

---

# 16. Phase 10 — Statistical and Analysis Infrastructure

Complete code for:

- paired bootstrap;
- cluster bootstrap;
- family-stratified bootstrap;
- exact paired tests;
- rank probability;
- pairwise superiority probability;
- mixed-effects model where justified;
- model × family interaction;
- multiple-comparison correction;
- effect sizes;
- equivalence tests where preregistered;
- scorer-error sensitivity;
- missingness diagnostics;
- opportunity-denominator checks;
- naturalistic predictive validity;
- RAAC clean-performance trade-off;
- cost-normalised efficiency frontier.

## 16.1 Property and edge tests

Add tests for:

- no pairs;
- zero clean success;
- near-zero clean success;
- one cluster;
- ties;
- identical models;
- all-discordant pairs;
- repeated base tasks;
- missing opportunities;
- scorer flips;
- rank instability;
- undefined mixed-effects cases;
- bootstrap resumability.

## 16.2 Analysis plan

Create:

`docs/ICLR_CONFIRMATORY_ANALYSIS_PLAN.md`

Freeze:

- primary endpoints;
- secondary endpoints;
- exploratory endpoints;
- multiplicity;
- SESOI;
- equivalence region;
- exclusion rules;
- missingness policy;
- rank-claim policy;
- null-result policy.

---

# 17. Phase 11 — Claim and Paper Asset Gates

## 17.1 Claim ledger

Create:

`CAB_ICLR_PAPER_CLAIM_LEDGER.md`

For every intended claim record:

- claim ID;
- RQ;
- hypothesis;
- required study;
- required sample;
- required validation;
- required effect;
- robustness checks;
- current evidence state;
- allowed wording;
- forbidden wording;
- paper location.

## 17.2 Paper asset generation

Prepare scripts for:

- clean-versus-robust rank plot;
- rank probability matrix;
- transition profiles;
- family heatmap;
- RAAC effect and overhead;
- naturalistic transfer;
- scorer sanity;
- intervention validity;
- failure gallery;
- cost/runtime appendix.

Every asset must embed:

- study ID;
- data hash;
- scorer version;
- code revision;
- generation command;
- evidence class.

Scripts must refuse noneligible evidence.

## 17.3 Paper scaffold

Update the ICLR paper scaffold with:

- method-first introduction;
- formal setup;
- intervention validity;
- paired inference;
- RAAC;
- benchmark construction;
- experimental protocol;
- results placeholders;
- naturalistic transfer;
- limitations;
- ethics;
- reproducibility.

Do not fill result placeholders.

Maintain stage-safe abstracts:

- no evidence;
- pilot;
- confirmatory;
- final.

---

# 18. Phase 12 — Reviewer Gauntlet

Create a pre-execution reviewer audit from six perspectives:

1. sceptical ICLR generalist;
2. agent-systems reviewer;
3. causal-methodology reviewer;
4. statistics reviewer;
5. benchmark/dataset reviewer;
6. reproducibility reviewer.

For each provide:

- likely score before experiments;
- confidence;
- fatal concerns;
- required evidence;
- possible rejection reason;
- mitigation status;
- remaining work.

Create:

`reviews/ICLR_PREEXECUTION_REVIEWER_GAUNTLET.md`

Do not fabricate acceptance likelihood as certainty.

---

# 19. Phase 13 — Unified ICLR Pre-Execution Gate

Create:

```bash
python3 scripts/check_iclr_preexecution_readiness.py
```

The gate must check:

- Prompt 1 integrity;
- contamination repair;
- canonical states;
- RAAC code and tests;
- hidden-label blindness;
- compute bounds;
- human-review packet readiness;
- C10 state;
- Scale-100 diversity;
- naturalistic provenance;
- split overlap;
- leakage;
- scorer;
- paired metrics;
- analysis plan;
- Kaggle notebooks;
- M4 workflow;
- run manifests;
- paper asset refusal;
- release safety;
- evidence counts.

Possible states:

- `ICLR_BUILD_INCOMPLETE`
- `METHODOLOGY_READY`
- `HUMAN_VALIDATION_REQUIRED`
- `C10_PENDING`
- `COMPACT20_READY`
- `COMPACT20_AUDIT_REQUIRED`
- `SCALE100_READY`
- `NATURALISTIC_TRANSFER_READY`
- `ICLR_EMPIRICAL_PACKAGE_READY`
- `ICLR_SUBMISSION_CANDIDATE`

After this prompt, expected state:

> `HUMAN_VALIDATION_REQUIRED`

unless genuine human rows already exist.

The gate must print:

- current state;
- blockers;
- exact next allowed action;
- forbidden actions;
- evidence counts.

---

# 20. Phase 14 — Complete Execution Handbook

Create one canonical file:

`CAB_ICLR_COMPLETE_EXECUTION_AND_EXPERIMENT_HANDBOOK.md`

It must list every future run in strict order.

For each run include:

- run ID;
- study stage;
- purpose;
- evidence role;
- mandatory/optional;
- prerequisites;
- task pack;
- model category;
- policy;
- repeats;
- clean/intervention counts;
- trajectories;
- compute class;
- CPU/GPU/API/HUMAN;
- Kaggle suitability;
- T4×2 compatibility;
- estimated VRAM;
- estimated disk;
- estimated runtime;
- assumptions;
- estimated cost;
- command/notebook;
- outputs;
- completion validator;
- failure recovery;
- paper eligibility.

Compute classes:

- `CPU_ONLY`
- `GPU_SINGLE`
- `GPU_T4X2_DATA_PARALLEL`
- `GPU_T4X2_OPTIONAL_MODEL_PARALLEL`
- `PROVIDER_API`
- `HUMAN_ONLY`
- `HYBRID`

Every unmeasured runtime:

`ESTIMATE_NOT_MEASURED`

Required categories:

- CPU validation;
- human review;
- adjudication/C10;
- engineering smoke;
- Compact-20;
- scorer sanity;
- Scale-100;
- RAAC ablations;
- naturalistic transfer;
- optional providers;
- optional main expansion;
- final analysis;
- paper assets;
- release.

---

# 21. Phase 15 — Validation

Run focused tests after each phase.

At the end run:

## Static

- Ruff;
- formatting checks;
- mypy;
- JSON/YAML validation;
- notebook lint;
- secret scan;
- Git diff check.

## Focused

- contamination tests;
- state tests;
- Prompt 1 tests;
- RAAC tests;
- human/C10 tests;
- dataset diversity tests;
- naturalistic provenance tests;
- notebook fixture tests;
- analysis property tests;
- paper asset gate tests.

## Full

Run the complete provider-free suite.

Target:

- zero unexpected failures;
- documented expected nonzero gate codes only for human/C10 blocks;
- no scientific execution;
- no fabricated evidence.

Record:

- exact command;
- working directory;
- exit code;
- elapsed time;
- pass/skip/deselect counts;
- expected blockers;
- unexpected blockers.

If the full suite is too long:

- complete the highest-value focused tests;
- preserve logs;
- provide exact continuation command;
- do not claim full pass.

---

# 22. Required Final Artifacts

Create or update:

1. `reports/ICLR_ULTIMATE_ONESHOT_LEDGER.md`
2. `reports/ICLR_ONESHOT_CURRENT_STATE.json`
3. `reports/ICLR_ONESHOT_CURRENT_STATE.md`
4. `reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json`
5. `docs/PUBLIC_HELDOUT_CONTAMINATION_AND_HISTORY_POLICY.md`
6. `docs/RAAC_METHOD.md`
7. `docs/RAAC_FAIRNESS_AND_BUDGET_POLICY.md`
8. `experiments/RAAC_ABLATION_PLAN.md`
9. `docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md`
10. `docs/HUMAN_REVIEW_RESOURCE_PLAN.md`
11. `reports/ICLR_SCALE100_DIVERSITY_AUDIT.md`
12. naturalistic candidate and provenance artifacts
13. `docs/MAIN_SET_RESOURCE_AWARE_DECISION_POLICY.md`
14. `docs/M4_LOW_MEMORY_WORKFLOW.md`
15. `docs/KAGGLE_T4X2_OPERATIONS.md`
16. `docs/ICLR_CONFIRMATORY_ANALYSIS_PLAN.md`
17. `CAB_ICLR_PAPER_CLAIM_LEDGER.md`
18. `reviews/ICLR_PREEXECUTION_REVIEWER_GAUNTLET.md`
19. `CAB_ICLR_COMPLETE_EXECUTION_AND_EXPERIMENT_HANDBOOK.md`
20. `CAB_ICLR_ULTIMATE_ONESHOT_BUILD_REPORT.md`
21. `cab_iclr_handoff.md`

Reuse and update existing canonical artifacts where appropriate.

Do not duplicate files unnecessarily.

---

# 23. Acceptance Criteria

This one-shot build is successful when:

## Prompt 1 integration

- both known failures are fixed;
- public held-out contamination is handled scientifically;
- contaminated tasks are ineligible;
- canonical states are centralised;
- Prompt 1 focused tests remain green.

## RAAC

- real implementation exists;
- state machine is typed;
- legal transitions are enforced;
- hidden labels are inaccessible;
- budgets are bounded;
- trace is auditable;
- variants and ablations exist;
- fixture tests pass;
- run and notebook integration exists.

## Human validation

- complete blank packets exist;
- agreement analysis exists;
- C10 is canonical;
- empty/proxy/AI review fails;
- adjudication is required;
- human-resource plan exists.

## Dataset

- Scale-100 diversity is honest;
- overlap is blocked;
- naturalistic candidate exists;
- provenance/licence/privacy/injection checks exist;
- Main expansion is conditional.

## Resource fit

- Mac low-memory lane exists;
- T4×2 notebooks are fixture-valid;
- 4-bit and fp16 paths exist;
- single-GPU fallback exists;
- checkpoint/resume/merge work;
- storage/runtime estimators exist.

## Analysis

- paired inference is complete;
- RAAC treatment analysis exists;
- rank uncertainty exists;
- naturalistic predictive-validity analysis exists;
- edge/property tests pass;
- confirmatory plan is frozen.

## Paper and release

- claim ledger exists;
- asset scripts fail closed;
- paper scaffold is method first;
- reviewer gauntlet exists;
- execution handbook is complete;
- no fabricated result appears.

## Evidence

Expected final evidence remains:

- human rows: 0 unless genuinely supplied;
- real trajectories: 0;
- audited runs: 0;
- paper-eligible assets: 0;
- supported empirical claims: 0.

That is correct for pre-execution completion.

---

# 24. Stop Rule

Do not start another generic build cycle after this prompt.

Once the pre-execution gate reaches:

`HUMAN_VALIDATION_REQUIRED`

stop adding infrastructure.

The next valid sequence is:

1. human review;
2. adjudication;
3. C10;
4. slice lock;
5. CPU preflight;
6. Kaggle fixture smoke;
7. Compact-20 real pilot;
8. scorer sanity;
9. Scale-100;
10. naturalistic transfer;
11. selected ablations;
12. paper from audited evidence.

---

# 25. Final Response Format

## Final Status

Use one:

- `CAB_ICLR_ULTIMATE_PREEXECUTION_BUILD_COMPLETE`
- `PARTIAL_SUCCESS_HIGH_VALUE_CORE_COMPLETE`
- `PARTIAL_SUCCESS_VALIDATION_REMAINS`
- `BLOCKED_BY_REPOSITORY_INCONSISTENCY`

## Verified State

State exactly what the project is.

## Prompt 1 Blockers

Explain contamination and state repairs.

## RAAC

List implementation, policies, tests, and integration.

## Human Validation

State packet, C10, and agreement readiness.

## Scale-100

State diversity and freeze readiness.

## Naturalistic Transfer

State task, provenance, and review readiness.

## Resource Readiness

State M4 and T4×2 readiness.

## Analysis Readiness

State metrics, uncertainty, RAAC analysis, transfer analysis.

## Paper Readiness

State claim ledger, assets, scaffold, and remaining empirical blockers.

## Validation

List commands, exit codes, elapsed time, and test counts.

## Evidence Counts

Report genuine counts.

## Remaining Blockers

Separate:

- human;
- execution;
- empirical;
- optional provider;
- optional scale expansion.

## Exact Next Action

Give only the first allowed action.

## Files Changed

List paths.

## Handoff

Point to:

- `cab_iclr_handoff.md`;
- `CAB_ICLR_COMPLETE_EXECUTION_AND_EXPERIMENT_HANDBOOK.md`;
- and the unified pre-execution gate.

---

# 26. Final Directive

Use the Ultra budget aggressively.

Do not waste it repeating audits already completed.

Close the known blockers.

Complete the RAAC method.

Finish human-validation machinery.

Strengthen the confirmatory and naturalistic datasets.

Finish Mac and Kaggle execution infrastructure.

Complete analysis, claim, paper, and release gates.

Validate as much as possible.

Leave the repository at the true no-execution ceiling for a strong ICLR submission.

After this run, the project should be ready to move from building to genuine human and model evidence.

---

# 27. Mandatory Direct-to-Main GitHub Publish

Publishing is part of this task.

After implementation and validation, commit the intended changes directly to:

`Saket-Maganti/cab`

Branch:

`main`

Do not create a feature branch.

Do not create a pull request.

Do not force-push.

## 27.1 Capture the Git baseline before editing

At the beginning of the run, execute:

```bash
cd /Users/saketmaganti/Projects/causal-agent-bench
git status --short
git status --branch --short
git branch --show-current
git rev-parse HEAD
git remote -v
```

Record the output in:

`reports/ICLR_ULTIMATE_ONESHOT_GIT_BASELINE.md`

The baseline must distinguish:

- changes already present before this prompt;
- files created or modified by this prompt;
- unrelated user-owned edits;
- generated temporary files;
- private or protected files that must never be committed.

Preserve all unrelated work.

## 27.2 Confirm the target repository and branch

Run:

```bash
git remote get-url origin
git branch --show-current
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || true
```

The remote must resolve to the user’s CAB repository:

```text
Saket-Maganti/cab
```

The working branch must be:

```text
main
```

If the checkout is not on `main`, switch to it only when doing so is safe:

```bash
git switch main
```

Do not discard changes to switch branches.

If switching would overwrite or hide work, stop the publish phase, preserve all completed implementation, and report the exact blocker.

## 27.3 Synchronise safely before the final commit

Before staging the completed work, fetch the remote:

```bash
git fetch origin main
```

Inspect divergence:

```bash
git rev-list --left-right --count origin/main...main
git log --oneline --decorate --max-count=10 --all
```

Rules:

- If local `main` is only ahead of `origin/main`, continue.
- If local `main` is behind and the worktree is clean enough to integrate safely, use:

```bash
git pull --rebase --autostash origin main
```

- If local and remote have diverged, do not force-push.
- Resolve only straightforward conflicts caused by this task.
- Never overwrite remote work.
- If safe reconciliation is not possible, stop publishing and report the exact conflict state and continuation commands.

After synchronisation, rerun the highest-value focused checks affected by any rebased changes.

## 27.4 Pre-commit security and release sanitation

Before staging, verify that the commit contains none of the following:

- `.env` files;
- API keys;
- authentication tokens;
- private held-out task payloads;
- hidden answer keys;
- evaluator-only protected metadata;
- private reviewer identities;
- model weights;
- Hugging Face caches;
- Kaggle caches;
- raw temporary notebook output;
- large generated caches;
- OS metadata;
- editor temporary files;
- unapproved real trajectories;
- result artifacts not eligible for public release.

Run the repository’s available:

- secret scan;
- protected-payload scan;
- release validation;
- large-file inspection;
- `git diff --check`.

Also inspect:

```bash
git status --short
git diff --stat
git diff
git ls-files
```

Private replacement held-out material must remain under an ignored local path and must not be committed.

## 27.5 Stage only intended task-owned changes

Do not blindly run `git add -A` on a mixed worktree.

Build an explicit list of files that belong to:

- the Prompt 1 blocker repair;
- RAAC;
- human-validation infrastructure;
- Scale-100 and naturalistic candidate improvements;
- M4 and Kaggle infrastructure;
- statistical analysis;
- ICLR gates;
- reports and handoff generated by this prompt.

Stage those explicit paths.

Example pattern:

```bash
git add \
  src/causal_agent_bench/... \
  tests/... \
  docs/... \
  configs/... \
  experiments/... \
  scripts/... \
  reports/... \
  reviews/... \
  CAB_ICLR_ULTIMATE_ONESHOT_BUILD_REPORT.md \
  CAB_ICLR_COMPLETE_EXECUTION_AND_EXPERIMENT_HANDBOOK.md \
  CAB_ICLR_PAPER_CLAIM_LEDGER.md \
  cab_iclr_handoff.md
```

Adapt the list to the files actually changed.

After staging, inspect:

```bash
git status --short
git diff --cached --stat
git diff --cached
```

Unstage anything unrelated:

```bash
git restore --staged <path>
```

Do not commit empty generated directories or temporary logs unless they are intentional research artifacts.

## 27.6 Final validation before commit

Run the strongest validation possible before committing:

1. Prompt 1 blocker tests;
2. contamination and release tests;
3. canonical state tests;
4. RAAC tests;
5. human/C10 tests;
6. Scale-100 and naturalistic validation tests;
7. notebook fixture tests;
8. analysis property tests;
9. Ruff;
10. mypy;
11. `git diff --check`;
12. complete provider-free suite when feasible.

The commit may proceed when:

- all relevant focused tests pass;
- static checks pass;
- no unexpected security or release failure remains;
- any uncompleted full-suite validation is documented honestly in the handoff.

Do not push code known to contain an unexpected failing focused test.

Expected human-review and C10 fail-closed states are not implementation failures.

## 27.7 Commit directly on main

Create one intentional commit for the complete one-shot build.

Preferred commit message:

```bash
git commit -m "Complete CAB ICLR pre-execution build"
```

If the change is too large for one coherent commit and multiple commits materially improve auditability, use a small logical sequence such as:

```bash
git commit -m "Repair CAB heldout and readiness gates"
git commit -m "Add recovery-aware agent control"
git commit -m "Complete CAB ICLR pre-execution infrastructure"
```

Do not create many trivial commits.

After committing, capture:

```bash
git status --branch --short
git log -1 --oneline
git show --stat --oneline HEAD
```

The working tree should be clean except for:

- intentionally preserved unrelated user edits;
- ignored private data;
- documented local-only artifacts.

## 27.8 Push directly to GitHub main

Push the current `main` branch directly:

```bash
git push origin main
```

Do not use:

```bash
git push --force
git push --force-with-lease
```

If GitHub rejects the push because remote `main` changed:

1. do not force-push;
2. run:

```bash
git fetch origin main
git pull --rebase --autostash origin main
```

3. resolve only safe conflicts;
4. rerun affected tests;
5. retry:

```bash
git push origin main
```

If authentication fails:

- do not expose credentials;
- run `gh auth status` if `gh` is installed;
- preserve the local commit;
- report the exact remaining command;
- do not claim the push succeeded.

## 27.9 Verify the remote push

After a successful push, run:

```bash
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
printf 'local=%s\nremote=%s\n' "$LOCAL_HEAD" "$REMOTE_HEAD"
test "$LOCAL_HEAD" = "$REMOTE_HEAD"
```

Also run:

```bash
git status --branch --short
git log -1 --oneline origin/main
```

The publish phase is complete only when:

- `origin/main` exists;
- local HEAD equals remote main HEAD;
- the pushed commit contains the intended ICLR work;
- no force push occurred;
- no protected/private payload was included.

## 27.10 GitHub Actions and remote checks

After the push, inspect available commit checks using either repository tooling or GitHub CLI:

```bash
gh run list --branch main --limit 10
gh api repos/Saket-Maganti/cab/commits/"$(git rev-parse HEAD)"/status
```

If workflows start, report their state.

Do not wait indefinitely for remote CI.

Do not claim CI passed unless it actually completed successfully.

If there are no configured checks, state:

```text
No remote commit-status checks were attached at verification time.
```

## 27.11 Publish report

Create or update:

`reports/ICLR_ULTIMATE_ONESHOT_GITHUB_PUBLISH.md`

It must include:

- repository;
- branch;
- pre-run commit;
- final commit;
- commit message;
- files committed;
- validation completed before commit;
- local HEAD;
- remote main HEAD;
- push command;
- push result;
- remote CI state;
- preserved unrelated edits;
- excluded private/protected files;
- any remaining publish or validation blocker.

---

# 28. Updated Final Response Requirements

In addition to the earlier final-response sections, include:

## Git Publication

Report:

- repository: `Saket-Maganti/cab`;
- branch: `main`;
- commit SHA;
- commit message;
- push result;
- verification that local HEAD equals `origin/main`;
- whether remote CI exists and its observed state;
- confirmation that no force-push was used;
- confirmation that private/protected held-out payloads were excluded.

Use one exact publication state:

- `PUSHED_TO_GITHUB_MAIN`
- `LOCAL_COMMIT_COMPLETE_PUSH_BLOCKED`
- `PUSH_BLOCKED_BY_REMOTE_DIVERGENCE`
- `PUSH_BLOCKED_BY_AUTHENTICATION`
- `PUSH_SKIPPED_DUE_TO_VALIDATION_FAILURE`

Do not claim successful publication without remote SHA verification.

---

# 29. Final Directive Including Publication

Complete the maximum possible ICLR pre-execution build.

Validate it.

Commit only the intended task-owned changes.

Push directly to:

```text
origin/main
```

Do not create a branch.

Do not create a pull request.

Do not force-push.

Do not include protected or private payloads.

Verify that the local commit and GitHub `main` commit are identical before declaring success.

