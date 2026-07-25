# Causal Agent Bench — Maximum-Ceiling Forensic Audit, Codebase Repair, Leakage Hardening, Pre-Execution Build, and Runbook Master Prompt

## Intended Use

Give this prompt to Codex with full access to:

`/Users/saketmaganti/Projects/causal-agent-bench`

This prompt supersedes the earlier standalone forensic audit. It combines:

- repository-first forensic verification;
- all earlier audit and repair requirements;
- production scorer and paired-metric repairs;
- leakage, contamination, and prompt-injection defenses;
- intervention-validity hardening;
- Compact-20, Scale-100, naturalistic-transfer, and Main-500 preparation;
- provider and open-model execution architecture;
- Kaggle dual-T4 notebook construction;
- statistical-analysis and evidence-gating infrastructure;
- paper-asset generation plumbing without fabricated results;
- release, CI, provenance, security, and reproducibility hardening;
- and one final execution handbook describing every future run, dependencies, compute class, commands, expected runtime, and evidence role.

The objective is to build CAB as far as it can honestly go **before any scientific benchmark runs are executed**.

---

# 1. Role and Research Ambition

Act simultaneously as:

- a senior benchmark researcher;
- an LLM-agent evaluation specialist;
- a NeurIPS Datasets & Benchmarks reviewer;
- a DMLR reproducibility reviewer;
- a statistical-methodology reviewer;
- a research software architect;
- a secure evaluation-infrastructure engineer;
- a benchmark-leakage and contamination auditor;
- a multi-GPU inference engineer;
- a Kaggle notebook reliability engineer;
- and a publication-readiness lead.

Transform Causal Agent Bench into the strongest possible pre-execution benchmark repository.

The primary realistic publication ceiling is:

> **NeurIPS Datasets & Benchmarks**

The release-oriented alternative is:

> **DMLR**

A NeurIPS or ICLR general main-track submission is only a stretch ceiling if the repository develops and later empirically supports a contribution beyond a benchmark release, such as:

- a generally useful intervention-validity methodology;
- a reliability-aware robustness estimator;
- a principled benchmark-construction algorithm;
- a robustness-improving agent method;
- a formal result with real scope and a completed proof;
- or evidence that CAB predicts meaningful deployment failures.

Do not claim venue readiness merely because the code or paper scaffold is extensive.

---

# 2. Repository and Historical Context

Repository root:

`/Users/saketmaganti/Projects/causal-agent-bench`

A historical handoff such as `cabv1.md` may be present.

Treat historical reports as context only. They may contain:

- stale counts;
- planned work adjacent to completed work;
- inconsistent evidence classifications;
- duplicated status files;
- old venue directions;
- partially implemented V3 or V4 designs;
- and claims inherited from earlier prompt-pack outputs.

The repository is the source of truth.

The prior inspection identified likely high-priority risks that must be verified directly:

1. Most evolved work may be uncommitted on top of a single initial commit.
2. The V4 code-heavy layer may not yet be implemented.
3. The production final-answer scorer may still rely heavily on substring matching.
4. The canonical ACRS implementation may pool clean and intervention outcomes instead of using properly matched paired units.
5. Intervention-specific answer policies may not be integrated into production scoring.
6. Compact-20 may contain only 10 unique base tasks despite 20 intervention candidates.
7. The larger synthetic dataset may contain far fewer unique instruction templates than raw task counts suggest.
8. Multiple project status files may disagree about run and evidence state.
9. Default pytest configuration may depend on optional packages such as `pytest-xdist` and `hypothesis`.
10. The repository may contain excessive report, venue, prompt-pack, and direction sprawl.
11. The active paper may still use stronger causal language than the validated methodology supports.
12. Existing mock, stub, interrupted, or fallback runs may be inconsistently classified.

Verify every point. Do not assume it is still true.

---

# 3. Non-Negotiable Execution Boundary

This is a **maximum pre-execution build**.

Do not execute scientific benchmark runs.

## 3.1 Prohibited actions

Do not:

- call paid APIs;
- call external model providers;
- execute real provider inference;
- execute local or Hugging Face model inference on benchmark tasks;
- run the Compact-20 experiment;
- run the Scale-100 study;
- run Main-500;
- run naturalistic-transfer experiments;
- launch Kaggle jobs;
- launch Colab jobs;
- start cloud or remote GPU jobs;
- download large model weights;
- fabricate model trajectories;
- generate synthetic model outputs and present them as evidence;
- fill human-review rows;
- invent reviewer identities;
- invent adjudication;
- fabricate ACRS values;
- fabricate confidence intervals;
- fabricate costs or measured runtimes;
- fabricate model rankings;
- fabricate paper tables, plots, findings, or failure cases;
- tune tasks or scorers to produce a desired rank reversal;
- promote unsupported claims;
- mark any result paper-eligible without satisfying real evidence gates;
- push, publish, or release externally;
- destroy or reset unrelated user work;
- use secrets found in the environment;
- print or store secret values.

## 3.2 Permitted actions

You may:

- inspect the complete repository;
- read all code, configs, data schemas, task manifests, tests, notebooks, reports, and paper files;
- repair source code;
- add missing validators;
- add safe deterministic fixtures;
- add unit, property, integration, and notebook tests;
- run CPU-only fixture tests;
- run static analysis;
- run schema validation;
- run type checking;
- run linting;
- run secret scanning;
- run configuration validation;
- compile paper scaffolds;
- validate notebooks in offline fixture mode;
- execute tiny deterministic smoke fixtures that cannot call a model;
- build cost and runtime estimators using explicit assumptions;
- create execution scripts and notebooks;
- create frozen manifests;
- create paper table and figure generators that remain empty until real results exist;
- and create complete runbooks for the user to execute later.

Every output must preserve these evidence classes:

- `DESIGN_ONLY`
- `ENGINEERING_ONLY`
- `FIXTURE_ONLY`
- `HUMAN_INPUT_REQUIRED`
- `EXECUTION_PENDING`
- `PRELIMINARY_REAL_EVIDENCE`
- `AUDITED_REAL_EVIDENCE`
- `PAPER_ELIGIBLE_EVIDENCE`

---

# 4. Fundamental Operating Rules

## 4.1 Build, do not merely recommend

When a problem is locally repairable, repair it.

Do not finish with a long recommendation list while leaving obvious implementation work undone.

## 4.2 Consolidate rather than multiply

Prefer:

- one canonical scorer;
- one canonical metric library;
- one canonical evidence-state engine;
- one canonical run registry;
- one canonical benchmark manifest;
- one canonical claim ledger;
- one canonical project status;
- and one canonical execution handbook.

Do not create another generation of near-duplicate reports unless the artifact has a clear canonical purpose.

## 4.3 Protect scientific neutrality

Code changes may improve:

- correctness;
- determinism;
- efficiency;
- failure handling;
- scoring validity;
- statistical validity;
- fairness;
- and reproducibility.

Code changes must not optimize the benchmark toward a desired conclusion.

Do not:

- select tasks because they create larger model gaps;
- modify gold answers after observing model behaviour;
- modify scoring to produce rank reversals;
- remove difficult cases merely because models fail;
- or create asymmetric tool conditions that favour a model family.

Any change that could affect future scientific results must be:

- documented;
- versioned;
- tested;
- reflected in a new benchmark hash;
- and frozen before real execution.

## 4.4 Preserve reversible history

Before major modifications:

- inspect Git state;
- identify or create a checkpoint branch;
- avoid destructive cleanup;
- preserve original artifacts;
- record all modifications;
- and produce a logical commit plan.

Do not commit unless authorized. Otherwise, provide exact commit groups and commands.

---

# 5. Phase 0 — Repository Checkpoint and Forensic Discovery

## 5.1 Establish repository state

Record:

- current branch;
- current commit;
- Git status;
- tracked modifications;
- untracked files;
- ignored but scientifically relevant files;
- large files;
- result directories;
- generated artifacts;
- paper outputs;
- notebooks;
- local virtual environments;
- caches;
- and external-data placeholders.

Measure and report:

- source files;
- source lines;
- test files;
- tests collected;
- docs and reports;
- task counts;
- intervention counts;
- unique base tasks;
- unique templates;
- intervention-family counts;
- current runs by evidence class;
- and paper-eligible assets.

## 5.2 Inventory all status sources

Find every file that claims to describe project state, including:

- `MASTER_STATUS.json`;
- `PROJECT_STATUS.json`;
- `PROJECT_STATUS.md`;
- final reports;
- V1/V2/V3/V4 reports;
- claim ledgers;
- evidence registries;
- run indexes;
- provider-approval files;
- human-review status;
- C10 status;
- release readiness;
- paper readiness;
- prompt-pack ledgers;
- audit reports;
- and handoff files.

Create a contradiction matrix containing:

- artifact A;
- artifact B;
- conflicting field;
- actual repository-derived truth;
- resolution;
- canonical replacement;
- and deprecation action.

## 5.3 Verify the historical handoff

For each major statement in `cabv1.md`, classify it:

- `VERIFIED_CURRENT`
- `VERIFIED_BUT_STALE`
- `PARTIALLY_VERIFIED`
- `PLANNED_ONLY`
- `NOT_FOUND`
- `CONTRADICTED`
- `OBSOLETE`
- `UNVERIFIABLE`

Include:

- V3 implementation;
- V4 implementation;
- test counts;
- provider evidence counts;
- human-review counts;
- C1-C10 states;
- Compact-20 status;
- paper state;
- release state;
- and publication-ceiling assumptions.

## 5.4 Canonical verified state

Implement a derived machine-readable project state.

Required outputs:

- `reports/CAB_CURRENT_STATE_VERIFIED.json`
- `reports/CAB_CURRENT_STATE_VERIFIED.md`

The state must be derived from actual artifacts and validators, not manually asserted.

---

# 6. Phase 1 — Thesis, Contribution, and Venue-Ceiling Audit

## 6.1 Define the strongest honest thesis

Reconstruct the strongest defensible one-sentence thesis.

Likely direction:

> Success-only evaluation can misrepresent the competence of tool-using agents; paired, goal-preserving controlled interventions expose family-specific brittleness, recovery behaviour, abstention quality, and ranking uncertainty that clean-task success alone does not reveal.

Do not retain stronger language without support.

## 6.2 Clarify “causal”

Audit all uses of:

- causal;
- causal robustness;
- causal benchmark;
- causal effect;
- intervention effect;
- identification;
- counterfactual;
- and do-operator language.

Distinguish:

- designed interventions;
- paired controlled perturbations;
- causal motivation;
- and formal causal identification.

The brand may remain, but the paper and README must state clearly that CAB does not currently establish formal causal identification unless that is genuinely supported.

## 6.3 Canonical contribution hierarchy

Separate:

### Primary contribution candidates

- paired controlled-intervention benchmark design;
- intervention-family taxonomy;
- intervention-validity protocol;
- leakage-resistant task construction;
- paired robustness and rank-uncertainty analysis;
- naturalistic-transfer methodology;
- reproducible agent-evaluation release.

### Secondary contribution candidates

- ACRS and companion metrics;
- scorer-conformance framework;
- evidence-state and paper-eligibility governance;
- run-provenance architecture.

### Non-contributions

Do not present ordinary infrastructure, test quantity, prompt packs, or configuration management as headline research contributions.

## 6.4 Main-track stretch analysis

Evaluate—but do not force—possible methodological additions:

- intervention validity certificates;
- reliability-adjusted robustness aggregation;
- uncertainty-aware ranking distributions;
- paired transition profiles;
- formal estimator properties;
- intervention-generation validation;
- task-family generalization;
- or deployment-failure prediction.

Implement only components that are mathematically valid, useful, and honestly novel.

Do not invent a theorem or named metric for appearance.

---

# 7. Phase 2 — Leakage, Contamination, and Benchmark Integrity

Build a comprehensive threat model and repair all mechanically detectable leakage.

## 7.1 Leakage taxonomy

Audit at minimum:

### A. Gold-answer leakage

- answers in prompts;
- answer values in filenames;
- answer fragments in IDs;
- gold fields visible to agents;
- answer-bearing debug logs;
- answer-bearing tool descriptions;
- and accidental gold fields in serialized payloads.

### B. Intervention-label leakage

- family names visible to agents;
- task IDs revealing perturbation;
- prompts explicitly revealing corruption when inference is intended;
- ordering patterns revealing intervention class;
- and benchmark instructions revealing expected recovery behaviour.

### C. Cross-condition leakage

- conversations reused across clean and intervention;
- cache reuse;
- memory reuse;
- tool-state reuse;
- temporary workspace reuse;
- response reuse;
- and order effects.

Each condition must be independently initialized unless carryover is the explicit research object.

### D. Split and selection leakage

- Compact-20 reused for development and confirmation;
- Scale-100 tuned after seeing results;
- Main-500 selected after pilot performance;
- family thresholds changed post hoc;
- and post-hoc exclusions.

Create immutable roles:

- development;
- pilot;
- validation;
- confirmatory;
- naturalistic transfer;
- held-out challenge.

### E. Scorer leakage

- gold access inside agent code;
- model-specific scoring rules;
- scoring changed after viewing outputs;
- unsafe substring matching;
- and hidden manual overrides.

### F. Tool and environment leakage

- tools exposing hidden task state;
- debug endpoints available to agents;
- error strings encoding correct responses;
- environment metadata exposing intervention;
- and paths containing labels.

### G. Prompt-injection leakage

Audit task artifacts, retrieved content, tool outputs, and notebooks for:

- instructions to reveal secrets;
- instructions to ignore evaluator rules;
- instructions to modify scoring;
- notebook-code injection;
- CSV formula injection;
- HTML or Markdown injection;
- shell injection;
- path traversal;
- and serialization injection.

Add sanitization and sandbox boundaries.

### H. Provider and adapter leakage

- provider-specific system prompts;
- asymmetric retries;
- unequal tools;
- unequal context;
- hidden reasoning access for one model;
- provider-side memory;
- cached conversations;
- and inconsistent safety filtering.

### I. Human-review leakage

Separate:

- task validation;
- intervention validation;
- scorer sanity;
- trajectory error review;
- and claim adjudication.

Task validators should not see model identity or performance.

### J. Public-release contamination

Prevent held-out tasks and answer keys from becoming public before confirmatory evaluation.

Create release tiers:

- development release;
- harness-only release;
- hidden or delayed test pack;
- post-study full release.

### K. Pretraining contamination

Mitigate—not overclaim elimination—through:

- fresh parameterization;
- private held-out variants;
- timestamped task creation;
- naturalistic artifacts;
- contamination probes;
- and explicit limitations.

## 7.2 Leakage scanners

Create or repair scanners for:

- answer overlap;
- answer fragments in visible fields;
- task/intervention label exposure;
- duplicate and near-duplicate text;
- template overlap;
- split overlap;
- path leakage;
- secret leakage;
- prompt-injection strings;
- suspicious tool output;
- and notebook variable exposure.

Each finding must record:

- file;
- task ID;
- field;
- severity;
- leakage class;
- suggested repair;
- automatic repair status;
- and unresolved human-review state.

## 7.3 Split and freeze architecture

Create canonical split manifests with immutable hashes:

- `dev_fixture`;
- `compact20_pilot`;
- `scale100_confirmatory`;
- `naturalistic_transfer`;
- `main500_confirmatory`;
- `heldout_challenge`.

No task may occupy incompatible roles.

Use:

- exact IDs;
- normalized text;
- template IDs;
- token similarity;
- answer overlap;
- and source lineage.

## 7.4 Leakage gate

Add one command that blocks run eligibility when high-severity leakage remains unresolved.

---

# 8. Phase 3 — Canonical Task, Intervention, and Gold Policy

## 8.1 Base-task schema

Include:

- task ID;
- version;
- source;
- license;
- domain;
- difficulty;
- instruction;
- visible context;
- hidden evaluator context;
- tools;
- expected output schema;
- gold-answer policy;
- scorer policy;
- ambiguity policy;
- abstention policy;
- provenance;
- template ID;
- split role;
- and content hash.

## 8.2 Intervention schema

Every intervention must include:

- intervention ID;
- base-task ID;
- intervention family;
- intended manipulated factor;
- manipulation strength;
- goal-preservation statement;
- required invariances;
- changed fields;
- unchanged fields;
- environment mutation;
- tool mutation;
- observation mutation;
- memory mutation;
- expected behavioural adaptation;
- answer-policy change;
- scorer-policy change;
- valid recovery routes;
- acceptable abstention conditions;
- manipulation check;
- human-validation state;
- and content hash.

## 8.3 Explicit answer contracts

Implement machine-readable policies:

- `ORIGINAL_ANSWER_REQUIRED`
- `ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED`
- `RECOVERY_ROUTE_REQUIRED`
- `QUALIFIED_UNCERTAINTY_ACCEPTED`
- `CLARIFICATION_REQUIRED`
- `ABSTENTION_REQUIRED`
- `MULTIPLE_VALID_OUTCOMES`
- `HUMAN_REVIEW_REQUIRED`

The production scorer must use the intervention policy.

## 8.4 Task/intervention linter

Validate:

- fields;
- IDs;
- linkage;
- family values;
- policy compatibility;
- no visible gold;
- no illegal hidden fields;
- invariances;
- source and license;
- split role;
- tool availability;
- and hashes.

## 8.5 Human validity packets

Generate blank, complete review packets for:

- task clarity;
- gold correctness;
- goal preservation;
- intended-factor presence;
- intervention isolation;
- manipulation success;
- solvability;
- ambiguity;
- realism;
- and exclusion recommendation.

Do not fill judgments.

---

# 9. Phase 4 — Production Scorer Repair

## 9.1 Audit all scorer paths

Find and reconcile:

- trajectory scorer;
- fixture scorer;
- result exporter;
- offline rescoring;
- paper table scoring;
- manual-review integration;
- and alternate implementations.

## 9.2 Replace unsafe substring scoring

Substring scoring may remain only as a clearly limited fallback.

Implement typed scoring for:

- normalized strings;
- categorical answers;
- numbers with absolute and relative tolerances;
- percentages;
- units;
- currencies;
- dates;
- datetimes and time zones;
- booleans;
- ordered lists;
- unordered sets;
- key-value objects;
- structured JSON;
- ranges;
- multiple accepted answers;
- preregistered partial credit;
- abstention;
- clarification;
- refusal;
- recovery actions;
- and tool-use requirements.

## 9.3 False-positive protection

Do not award credit because expected fragments occur in:

- negations;
- rejected alternatives;
- quoted task text;
- tool logs;
- intermediate text;
- or irrelevant explanations.

Score only the canonical final-answer field unless a preregistered trajectory criterion applies.

## 9.4 Scorer versioning

Every result must record:

- scorer name;
- scorer version;
- scorer config;
- scorer-policy ID;
- scorer-policy hash;
- gold-policy ID;
- and code revision.

Raw trajectories must remain immutable and offline-rescorable.

## 9.5 Adversarial conformance tests

Add tests for:

- expected answer in the wrong context;
- negated answer;
- multiple numbers and incorrect final selection;
- currency formatting;
- tolerance boundaries;
- date variants;
- duplicate list items;
- unordered sets;
- invalid JSON containing expected fragments;
- refusal when an answer is required;
- confident answer when abstention is required;
- valid clarification;
- unavailable-tool disclosure;
- injection strings;
- and Unicode edge cases.

## 9.6 Future scorer-sanity workflow

Build a workflow that:

- samples by model, family, condition, and auto-score;
- blinds model identity where practical;
- records human correctness;
- estimates false-positive and false-negative rates;
- classifies scorer disagreements;
- supports adjudication;
- and blocks paper eligibility when disagreement exceeds thresholds.

Do not populate real results.

---

# 10. Phase 5 — Paired Metrics and Statistical Repair

## 10.1 Define the matched unit

Use an explicit unit such as:

`(model, base_task_id, intervention_id or family, repeat_id)`

Clean and intervention outcomes must be matched by base task and repeat policy.

## 10.2 Pair-level outcomes

Derive:

- clean success;
- intervention success;
- success-to-success;
- success-to-failure;
- failure-to-success;
- failure-to-failure;
- absolute degradation;
- conditional degradation among clean successes;
- recovery success;
- abstention correctness;
- invalid-pair reason;
- and completeness state.

## 10.3 Metric suite

Implement:

- clean success;
- intervention success;
- paired absolute degradation;
- paired relative degradation;
- ACRS ratio;
- conditional robustness among clean successes;
- macro ACRS;
- micro ACRS;
- family robustness;
- worst-family robustness;
- transition profiles;
- recovery score;
- correct abstention;
- false abstention;
- rank shift;
- Spearman correlation;
- Kendall correlation;
- rank uncertainty;
- and scorer-adjusted sensitivity analysis.

## 10.4 Denominator policy

Define behaviour for:

- zero clean success;
- near-zero clean success;
- missing clean condition;
- incomplete pair;
- repeated clean runs;
- and heterogeneous task sets.

Do not silently divide by unstable denominators.

## 10.5 Matching family denominators

Family-level robustness must use clean results from the exact corresponding base-task subset.

Do not use one global clean denominator for all families.

## 10.6 Inference utilities

Implement:

- paired bootstrap;
- cluster bootstrap by base task;
- stratified bootstrap by family;
- paired binary tests;
- confidence intervals;
- rank bootstrap;
- rank-probability matrices;
- multiple-comparison correction;
- effect sizes;
- and scorer-error sensitivity.

## 10.7 Pseudoreplication

Report:

- intervention-pair count;
- unique base-task count;
- template count;
- domain count;
- family count;
- and clustering unit.

Confidence intervals must account for correlated variants.

## 10.8 Frozen analysis plan

Define:

### Primary endpoints

- paired degradation;
- conditional robustness among clean successes;
- family macro robustness;
- rank uncertainty or rank change.

### Secondary endpoints

- recovery;
- abstention;
- tool-family profiles;
- error taxonomy;
- scorer-adjusted analysis.

### Exploratory endpoints

Explicitly label all post-hoc analyses.

---

# 11. Phase 6 — Dataset Diversity and Benchmark Construction

## 11.1 Measure actual diversity

For each task pack report:

- raw task count;
- unique base tasks;
- unique templates;
- normalized instruction patterns;
- domains;
- tool combinations;
- answer-policy types;
- intervention families;
- source types;
- and split roles.

Do not treat simple parameter variants as independent diversity.

## 11.2 Compact-20

Treat Compact-20 as:

- a pipeline pilot;
- scorer-sanity pilot;
- cost pilot;
- and feasibility study.

Do not make it the sole basis for top-tier claims.

Repair balance and uniqueness before human review, without using model performance.

## 11.3 Scale-100

Build and freeze a stronger confirmatory set with:

- substantially more unique base tasks;
- broad family coverage;
- diverse templates;
- domain balance;
- difficulty balance;
- scorer-policy diversity;
- answer-policy diversity;
- no development overlap;
- and power-aware allocation.

## 11.4 Naturalistic transfer

Build complete infrastructure for realistic tasks in domains such as:

- document retrieval;
- policy interpretation;
- spreadsheet analysis;
- calendar scheduling;
- travel planning;
- data cleaning;
- code debugging;
- configuration diagnosis;
- multi-step file operations;
- and tool-failure recovery.

Every artifact must include:

- provenance;
- license;
- privacy check;
- injection scan;
- answer-key isolation;
- and human validation.

## 11.5 Main-500

Main-500 must not merely scale templates.

Define gates for:

- unique base tasks;
- maximum variants per template;
- domain balance;
- naturalistic-task share;
- family balance;
- difficulty spread;
- scorer-policy diversity;
- and no confirmatory overlap.

## 11.6 Held-out challenge set

Prepare a hidden challenge-set architecture.

Do not expose answer keys or complete held-out payloads before final evaluation.

---

# 12. Phase 7 — Agent and Model Fairness

## 12.1 Canonical agent contract

Define:

- system prompt;
- task prompt;
- context;
- tool schemas;
- tool protocol;
- tool-call budget;
- token budget;
- wall-clock timeout;
- retry policy;
- sampling parameters;
- stopping criteria;
- output schema;
- and error handling.

## 12.2 Provider adapters

Audit for:

- equivalent prompts;
- equivalent tools;
- equivalent retries;
- equivalent max-token logic;
- equivalent timeouts;
- metadata capture;
- and unavoidable provider differences.

## 12.3 Open-model adapters

Prepare a robust open-model lane supporting:

- chat templates;
- function-calling emulation;
- JSON repair;
- quantized loading;
- fp16 on T4;
- safe single-GPU operation;
- optional two-GPU placement;
- stop tokens;
- context truncation;
- and output validation.

Do not download or execute model weights.

## 12.4 State isolation

Each run must initialize:

- fresh conversation;
- fresh tools;
- fresh memory;
- fresh workspace;
- independent cache namespace;
- and controlled random seed.

## 12.5 Failure taxonomy

Standardize:

- provider error;
- rate limit;
- timeout;
- parser failure;
- invalid tool call;
- tool failure;
- OOM;
- notebook interruption;
- partial output;
- scorer failure;
- and benchmark invalidity.

Infrastructure failures must not silently count as model failures.

---

# 13. Phase 8 — Run Architecture and Provenance

## 13.1 Canonical run manifest

Record:

- study ID;
- run ID;
- benchmark version;
- split role;
- task-pack hash;
- intervention-pack hash;
- scorer version;
- scorer-policy hash;
- code revision;
- environment hash;
- model ID;
- model revision;
- provider;
- adapter version;
- quantization;
- device;
- GPU count;
- seed;
- repeat;
- prompt version;
- tool budget;
- token budget;
- timeout;
- retry policy;
- start/end time;
- status;
- cost;
- trajectory path;
- score path;
- audit state;
- and evidence class.

## 13.2 Append-only run ledger

Support:

- resume;
- deduplication;
- conflict detection;
- incomplete-run detection;
- completion checks;
- artifact hashing;
- and merge safety.

## 13.3 Checkpoint/resume

Runners must:

- checkpoint per task or small batch;
- preserve completed trajectories;
- detect corrupted partial output;
- resume deterministically;
- and preserve failure metadata.

## 13.4 Merge validator

Verify:

- expected task IDs;
- expected repeats;
- no duplicates;
- no missing pairs;
- matching config hashes;
- matching scorer versions;
- matching model revision;
- matching benchmark version;
- and valid evidence class.

## 13.5 Cost/runtime estimator

Create estimators using explicit assumptions:

- tasks;
- conditions;
- repeats;
- tokens;
- tool calls;
- tokens per second;
- API pricing;
- load time;
- and retry rate.

All estimates must be labelled:

`ESTIMATE_NOT_MEASURED`

---

# 14. Phase 9 — Kaggle T4×2 Notebook Build

Create production-grade `.ipynb` runbooks for Kaggle with two NVIDIA T4 GPUs.

## 14.1 Environment assumptions

Detect at runtime:

- GPU count;
- VRAM;
- CUDA;
- system RAM;
- disk;
- package availability;
- repository paths;
- and internet status.

Prefer fp16. Do not assume bfloat16.

## 14.2 Parallel strategy

Default to independent data-parallel sharding:

- worker 0 on GPU 0;
- worker 1 on GPU 1;
- deterministic non-overlapping shards;
- independent model processes where memory permits;
- separate output directories;
- append-safe ledgers;
- deterministic merge.

Allow optional tensor parallelism only when genuinely supported.

For models that do not fit one T4:

- provide a 4-bit route;
- optional two-GPU placement;
- smaller alternatives;
- and an actionable preflight failure.

## 14.3 Required notebooks

Create at least:

1. `notebooks/kaggle/CAB_T4X2_00_ENVIRONMENT_PREFLIGHT.ipynb`

2. `notebooks/kaggle/CAB_T4X2_01_OFFLINE_FIXTURE_SMOKE.ipynb`

3. `notebooks/kaggle/CAB_T4X2_02_COMPACT20_OPEN_MODEL_RUNNER.ipynb`

4. `notebooks/kaggle/CAB_T4X2_03_SCALE100_OPEN_MODEL_RUNNER.ipynb`

5. `notebooks/kaggle/CAB_T4X2_04_MAIN500_OPEN_MODEL_RUNNER.ipynb`

6. `notebooks/kaggle/CAB_T4X2_05_BASELINES_AND_ABLATIONS.ipynb`

7. `notebooks/kaggle/CAB_T4X2_06_MERGE_AUDIT_AND_RESCORE.ipynb`

8. `notebooks/kaggle/CAB_T4X2_07_FAILURE_RECOVERY.ipynb`

9. `notebooks/kaggle/CAB_T4X2_08_NATURALISTIC_TRANSFER_RUNNER.ipynb`

## 14.4 Notebook safety structure

Every notebook must include:

- purpose;
- evidence-boundary warning;
- exact inputs;
- exact outputs;
- configuration cell;
- no secrets;
- no hard-coded user path;
- idempotent setup;
- explicit preflight;
- `RUN_LIVE = False` or equivalent by default;
- deterministic seeds;
- checkpointing;
- export instructions;
- and final integrity verification.

No notebook may automatically execute live inference when opened or run-all is pressed without explicit user activation.

## 14.5 Offline notebook validation

Validate using:

- notebook JSON validation;
- extracted Python syntax;
- `nbclient` or equivalent fixture execution;
- cell-order checks;
- import checks;
- secret checks;
- live-default checks;
- and output-path tests.

Claim “errorless” only for the tested fixture path and repository-controlled logic. Do not guarantee third-party model availability forever.

---

# 15. Phase 10 — Execution Lanes

Build separate lanes.

## 15.1 CPU-only

For:

- validation;
- generation;
- leakage scans;
- scorer tests;
- human-review validation;
- C10;
- statistics;
- tables;
- paper compilation;
- and release packaging.

## 15.2 Kaggle T4×2

For:

- approved open-model inference;
- Compact-20;
- Scale-100;
- selected Main-500 chunks;
- and open-model ablations.

## 15.3 Local GPU

Provide equivalent CLI commands.

## 15.4 Provider API

Build:

- approval gates;
- environment-only credential checks;
- cost caps;
- adapters;
- retry limits;
- rate-limit handling;
- and cost estimates.

Provider credentials must not be embedded in Kaggle notebooks.

## 15.5 Human review

Provide packets and validators for:

- task validity;
- intervention isolation;
- adjudication;
- scorer sanity;
- and trajectory error taxonomy.

## 15.6 Postrun analysis

No raw result may enter a paper table until:

- merge passes;
- completeness passes;
- scorer sanity passes;
- human requirements pass;
- evidence is promoted;
- and claim-ledger permission exists.

---

# 16. Phase 11 — Baselines, Ablations, and Profiles

## 16.1 Model panel

Design capability-diverse categories:

- strong proprietary model;
- second independent proprietary family;
- strong open instruct model;
- smaller open model;
- cost-efficient baseline.

Keep exact current models configurable and record snapshots at run time.

## 16.2 Agent-policy baselines

Prepare:

- direct answer;
- standard tool use;
- ReAct-style;
- self-check;
- recovery-aware;
- abstention-aware;
- and oracle engineering controls.

## 16.3 Metric ablations

Compare:

- pooled ACRS;
- paired ACRS;
- conditional robustness;
- absolute degradation;
- family macro;
- worst-family;
- rank uncertainty;
- and scorer-adjusted results.

## 16.4 Scorer ablations

Prepare:

- legacy scorer;
- canonical repaired scorer;
- strict structured scorer;
- human-reviewed subset.

Legacy results must not silently enter canonical tables.

## 16.5 Intervention ablations

Prepare:

- intervention strength;
- goal-preservation sensitivity;
- family removal;
- template-held-out;
- domain-held-out;
- and naturalistic-only.

## 16.6 Order and repeat analysis

Prepare:

- randomized condition order;
- order-effect checks;
- repeated-run variance;
- temperature sensitivity;
- and retry-policy sensitivity.

---

# 17. Phase 12 — Human Validation and C10

## 17.1 Human-review validator

Check:

- files exist;
- columns exist;
- rows are not header-only;
- reviewer IDs exist and are not placeholders;
- values are valid;
- rationales are present;
- all tasks are covered;
- duplicates are detected;
- proxy labels are rejected;
- disagreement is identified;
- and adjudication is enforced.

## 17.2 Reviewer independence

Where possible:

- require two independent reviewers for intervention isolation;
- hide model identity and outputs;
- record conflicts;
- separate author review from external review.

## 17.3 C10 engine

Resolve the canonical definition of C10.

Calculate it only from genuine qualifying rows.

Output:

- `PASS`
- `FAIL`
- or a precise blocked state.

Never pass empty review files.

## 17.4 Slice locking

A slice may be locked only after:

- task review;
- gold review;
- intervention-isolation review;
- leakage check;
- adjudication;
- C10;
- and manifest hashing.

---

# 18. Phase 13 — Evidence State and Run Gates

Implement one canonical evidence-state engine with states such as:

- `SCAFFOLD_ONLY`
- `METHODOLOGY_READY`
- `LEAKAGE_REPAIR_PENDING`
- `SCORER_REPAIR_PENDING`
- `METRIC_REPAIR_PENDING`
- `HUMAN_REVIEW_PENDING`
- `HUMAN_REVIEW_INCOMPLETE`
- `ADJUDICATION_PENDING`
- `C10_PENDING`
- `C10_FAILED`
- `SLICE_LOCK_PENDING`
- `PROVIDER_APPROVAL_PENDING`
- `CREDENTIAL_PREFLIGHT_PENDING`
- `COMPACT20_READY`
- `COMPACT20_RUN_UNAUDITED`
- `COMPACT20_AUDIT_PENDING`
- `PRELIMINARY_EVIDENCE_READY`
- `SCALE100_READY`
- `NATURALISTIC_TRANSFER_READY`
- `MAIN500_READY`
- `PAPER_CANDIDATE_READY`
- `RELEASE_CANDIDATE_READY`

The state must be validator-derived.

## 18.1 Unified no-execution gate

One command must check:

- repository consistency;
- leakage;
- schemas;
- scorer;
- metrics;
- human review;
- C10;
- slice integrity;
- configs;
- secrets;
- provider approval;
- notebooks;
- provenance;
- paper claims;
- and release status.

It must print:

- current state;
- exact blockers;
- exact next allowed command;
- and forbidden commands.

## 18.2 Study-specific gates

Create gates for:

- Compact-20;
- Scale-100;
- naturalistic transfer;
- Main-500;
- and paper assets.

---

# 19. Phase 14 — Tests, CI, and Reproducibility

## 19.1 Test lanes

### Fast

- imports;
- schemas;
- scorer tests;
- metric tests;
- leakage;
- claims;
- configuration.

### Medium

- integration;
- fixture runner;
- merge/resume;
- notebook offline execution;
- paper compilation;
- release checks.

### Full

- property tests;
- all integrations;
- all notebook checks;
- complete local-safe audit.

## 19.2 Dependencies

Ensure dev dependencies are correct.

If `pytest-xdist` or `hypothesis` are required:

- include them in the dev group;
- document installation;
- and provide a serial fallback.

## 19.3 Lint/type checks

Run and repair where configured:

- Ruff;
- formatter;
- mypy or pyright;
- notebook lint;
- Markdown links;
- JSON/YAML schemas;
- and shell checks.

Avoid huge cosmetic rewrites that obscure scientific changes.

## 19.4 CI

CI must never call providers.

Add:

- fast tests;
- medium tests where practical;
- notebook fixture validation;
- leakage gate;
- secret scan;
- claim ledger;
- paper placeholder checks;
- and release validation.

## 19.5 Environment reproducibility

Produce:

- dependency specification;
- lock where practical;
- Python version;
- CUDA guidance;
- Kaggle setup;
- local GPU setup;
- and provider setup.

---

# 20. Phase 15 — Paper and Result Plumbing

The paper will be completed after real runs.

## 20.1 Paper scaffold

Prepare:

- title options;
- stage-safe abstracts;
- introduction;
- benchmark design;
- intervention validity;
- leakage controls;
- metrics;
- statistical plan;
- protocol;
- results placeholders;
- limitations;
- ethics;
- release;
- and governance.

## 20.2 Asset generators

Build scripts for:

- main performance;
- family robustness;
- rank comparison;
- rank uncertainty;
- transition profiles;
- scorer sanity;
- intervention validity;
- naturalistic transfer;
- ablations;
- failure gallery;
- and cost/runtime appendix.

These scripts must refuse noneligible evidence.

## 20.3 Money plots

Prepare:

- clean-success rank versus robustness rank;
- rank probability;
- family robustness heatmap;
- transition matrix;
- model robustness profile;
- and scorer sensitivity.

Do not place fabricated plots in the paper.

## 20.4 Claim ledger

Each claim must map to:

- claim ID;
- required study;
- required evidence;
- validation threshold;
- current state;
- allowed wording;
- forbidden wording;
- and paper location.

---

# 21. Phase 16 — Release, Security, Privacy, and Governance

## 21.1 Public surface

Create a clean active surface:

- README;
- installation;
- quickstart;
- benchmark card;
- data card;
- evaluation card;
- schemas;
- scorer docs;
- metric docs;
- release manifest;
- license inventory;
- security policy;
- and citation placeholder.

## 21.2 Repository sprawl

Identify obsolete or noncanonical:

- prompt packs;
- venue experiments;
- old reports;
- duplicate papers;
- CVPR branches;
- AAAI artifacts;
- `cab_vision`;
- and generated status files.

Do not blindly delete.

Create:

- active-surface index;
- archive index;
- deprecation notices;
- and relocation plan.

## 21.3 Secrets

Scan:

- code;
- notebooks;
- configs;
- logs;
- reports;
- Git history where safe;
- and outputs.

Repair unsafe defaults.

## 21.4 Privacy and licensing

Naturalistic artifacts need:

- provenance;
- license;
- privacy review;
- PII policy;
- and removal procedure.

## 21.5 Governance

Document:

- versioning;
- task additions;
- retirement;
- bug fixes;
- scorer changes;
- leakage discoveries;
- challenge-set policy;
- model snapshots;
- result updates;
- and maintenance ownership.

---

# 22. Phase 17 — Performance and Reliability Optimization

Repair for better future execution only in scientifically neutral ways.

Allowed:

- batching;
- deterministic sharding;
- memory optimization;
- robust JSON parsing;
- checkpoint frequency;
- retry handling;
- timeout handling;
- GPU use;
- quantization;
- token-budget enforcement;
- tool-call validation;
- cache isolation;
- and merge efficiency.

Forbidden:

- prompt tuning after confirmatory outcomes;
- selecting favourable tasks;
- model-specific retry advantages;
- model-specific scorer tolerance;
- hiding failures;
- and changing intervention strength to force findings.

---

# 23. Required Final Execution Handbook

Create exactly one canonical file:

`CAB_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md`

It must describe every run the user must perform after the build.

## 23.1 Required fields for each run

Include:

- run ID;
- study stage;
- purpose;
- evidence role;
- mandatory or optional;
- prerequisite gates;
- task pack;
- models or category;
- repetitions;
- clean/intervention counts;
- expected trajectories;
- compute class;
- CPU/GPU/API;
- Kaggle suitability;
- T4×2 compatibility;
- expected VRAM;
- expected disk;
- expected runtime range;
- estimation assumptions;
- expected monetary cost;
- command or notebook;
- outputs;
- completion validator;
- failure recovery;
- and paper eligibility.

Every unmeasured runtime must say:

`ESTIMATE_NOT_MEASURED`

## 23.2 Required run categories

### Category A — CPU pre-execution validation

- fast tests;
- full safe audit;
- leakage scan;
- task lint;
- scorer conformance;
- metric tests;
- notebook validation;
- human-review validation;
- C10;
- slice lock;
- release checks.

### Category B — Human validation

- task clarity;
- gold correctness;
- intervention isolation;
- adjudication;
- scorer sanity;
- trajectory review.

List human time separately.

### Category C — Engineering smoke

- fake-adapter run;
- T4×2 sharding smoke;
- checkpoint/resume smoke;
- merge smoke;
- no-provider notebook smoke.

### Category D — Compact-20 pilot

- open-model T4×2 lane;
- provider lane;
- repeats;
- scorer sanity;
- postrun audit;
- preliminary analysis.

### Category E — Scale-100 confirmatory study

- model panel;
- repeats;
- open-model shards;
- provider lanes;
- merge;
- paired statistics;
- rank uncertainty;
- human trajectory sample.

### Category F — Baselines and ablations

- policy baselines;
- scorer ablations;
- metric ablations;
- intervention-strength;
- template-held-out;
- domain-held-out;
- repeat sensitivity.

### Category G — Naturalistic transfer

- validation;
- open-model runs;
- provider runs;
- audit;
- transfer analysis.

### Category H — Main-500

- chunk plan;
- multi-session Kaggle plan;
- provider cost plan;
- open-model plan;
- merge audit;
- final scorer sanity;
- statistics;
- reproducibility reruns.

### Category I — Paper asset build

- final analysis;
- tables;
- figures;
- failure gallery;
- claim promotion;
- paper compile;
- supplement;
- release package.

## 23.3 Runtime methodology

Use conservative ranges derived from:

- model size;
- quantization;
- prompt length;
- output length;
- tool calls;
- task count;
- repeats;
- two-GPU sharding;
- load time;
- checkpoint overhead;
- and retry rate.

Where data is missing, give formulas and low/base/high scenarios.

## 23.4 Compute labels

Every run must be one of:

- `CPU_ONLY`
- `GPU_SINGLE`
- `GPU_T4X2_DATA_PARALLEL`
- `GPU_T4X2_OPTIONAL_TENSOR_PARALLEL`
- `PROVIDER_API`
- `HUMAN_ONLY`
- `HYBRID`

## 23.5 Mandatory order

Provide a dependency-ordered sequence that can be followed from top to bottom.

---

# 24. Required Output Artifacts

Create or update:

1. `reports/CAB_MAX_CEILING_FORENSIC_AUDIT.md`
2. `reports/CAB_CURRENT_STATE_VERIFIED.json`
3. `reports/CAB_CURRENT_STATE_VERIFIED.md`
4. `reports/CAB_REPOSITORY_CONTRADICTION_MATRIX.md`
5. `reports/CAB_REPAIR_AND_UPGRADE_LEDGER.md`
6. `reports/CAB_LEAKAGE_AND_CONTAMINATION_AUDIT.md`
7. `reports/CAB_SCORER_VALIDITY_AUDIT.md`
8. `reports/CAB_PAIRED_METRIC_AND_STATISTICAL_AUDIT.md`
9. `reports/CAB_DATASET_DIVERSITY_AND_SPLIT_AUDIT.md`
10. `reports/CAB_KAGGLE_T4X2_NOTEBOOK_READINESS.md`
11. `reports/CAB_EXECUTION_ENTRY_GATE.md`
12. `reports/CAB_HIGHEST_CEILING_ROADMAP.md`
13. `reports/CAB_VERIFICATION_COMMANDS.md`
14. `CAB_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md`
15. `cabv2.md`

Reuse existing canonical artifacts when appropriate rather than duplicating them.

---

# 25. `cabv2.md` Requirements

Create an authoritative handoff:

`cabv2.md`

Include:

- project purpose;
- strongest thesis;
- publication ceiling;
- project evolution;
- verified repository state;
- contradictions;
- files repaired;
- systems implemented;
- leakage fixes;
- scorer changes;
- metric changes;
- task/intervention changes;
- tests and CI;
- notebook state;
- evidence state;
- claim state;
- human-review state;
- C10 state;
- Compact-20 state;
- Scale-100 state;
- naturalistic-transfer state;
- Main-500 state;
- paper state;
- release state;
- blockers;
- exact next steps;
- exact commands;
- and the path to the execution handbook.

Explicitly list which `cabv1.md` claims were:

- confirmed;
- corrected;
- superseded;
- or invalidated.

---

# 26. Verification Requirements

Attempt all safe relevant validation:

- package imports;
- fast tests;
- medium safe tests;
- full test collection;
- scorer conformance;
- metric property tests;
- leakage tests;
- split overlap;
- task/intervention lint;
- claim ledger;
- evidence state;
- secret scan;
- config audit;
- notebook JSON;
- notebook offline execution;
- run-manifest tests;
- merge/resume;
- paper placeholders;
- paper compilation;
- release validation;
- and unified no-execution gate.

Record:

- command;
- working directory;
- exit code;
- elapsed time;
- outcome;
- and evidence class.

A passing test is engineering evidence, not benchmark evidence.

---

# 27. Acceptance Criteria

The build is complete only when:

## Truth

- repository truth is derived;
- V4 status is resolved;
- contradictions are reconciled;
- canonical project and evidence state exist;
- unsupported claims are downgraded;
- paper eligibility is mechanically gated.

## Leakage

- threat model exists;
- high-severity leakage is repaired;
- splits are checked;
- agent payloads exclude gold;
- condition state is isolated;
- prompt-injection surfaces are scanned;
- held-out release policy exists.

## Scoring

- unsafe production substring scoring is repaired;
- intervention-specific answer contracts exist;
- policies are typed and versioned;
- adversarial tests pass;
- offline rescoring works.

## Metrics

- primary metrics are paired;
- family denominators are matched;
- denominator edge cases are defined;
- dependence is handled;
- rank uncertainty exists;
- analysis plan is executable.

## Dataset

- diversity is measured honestly;
- Compact-20 is a pilot;
- Scale-100 is a confirmatory design;
- naturalistic-transfer infrastructure exists;
- Main-500 diversity gates exist;
- split overlap is blocked.

## Execution

- canonical manifests exist;
- checkpoint/resume works in fixtures;
- T4×2 sharding works in fixtures;
- merge validation works;
- failure recovery is documented;
- provider gates exist.

## Notebooks

- all required notebooks exist;
- fixture mode executes;
- live inference is off by default;
- dual-GPU sharding exists;
- single-GPU fallback exists;
- outputs are resumable;
- validation passes.

## Testing

- test lanes are clear;
- dev dependencies are correct;
- serial fallback works;
- CI is provider-free;
- setup is reproducible.

## Handbook

- every run is classified;
- compute class is explicit;
- T4×2 compatibility is explicit;
- runtime ranges are present and labelled;
- commands are exact;
- order is dependency-complete.

## Handoff

- `cabv2.md` is accurate;
- diminishing-return no-execution work is identified;
- the transition to human validation and scientific execution is explicit.

---

# 28. Final Response Format

Conclude with:

## Final Status

Use a precise status, for example:

- `CAB_MAX_CEILING_PREEXECUTION_BUILD_COMPLETE`
- `PARTIAL_SUCCESS_LOCAL_BLOCKERS_REMAIN`
- `BLOCKED_BY_REPOSITORY_INCONSISTENCY`

## Verified Current State

State what CAB actually is after the build.

## Highest-Impact Findings

Cover scientific, leakage, scorer, metric, dataset, and engineering findings.

## Repairs Completed

List actual modifications.

## New Systems Implemented

List canonical components.

## Kaggle T4×2 Readiness

State:

- notebook paths;
- fixture status;
- parallel strategy;
- remaining external risks;
- first notebook to run later.

## Evidence State

Report:

- genuine human rows;
- real provider trajectories;
- real open-model trajectories;
- audited runs;
- paper-eligible assets;
- supported claims.

## Validation Results

Provide commands, exit codes, and elapsed times.

## Remaining Blockers

Separate:

- human input;
- external resources;
- execution;
- empirical evidence;
- optional stretch work.

## Current Rating

Score:

- thesis;
- novelty;
- methodology;
- intervention validity;
- leakage resistance;
- scorer validity;
- statistical validity;
- dataset diversity;
- engineering;
- execution readiness;
- evidence;
- paper readiness;
- release readiness;
- and overall state.

## Highest Realistic Ceiling

Explain what requires:

- Compact-20;
- Scale-100;
- naturalistic transfer;
- Main-500;
- and an additional main-track contribution.

## Exact Next Action

Give only the first permitted action and point to the handbook.

## Files Created or Modified

List canonical paths.

## Handoff

Confirm:

- `cabv2.md`;
- `CAB_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md`;
- and the authoritative project state.

---

# 29. Stop Rule

Once the repository satisfies the acceptance criteria, stop adding scaffold.

Do not create V5, V6, or another prompt-pack cycle simply because no real evidence exists.

At that point, the next phase is:

1. genuine human review;
2. adjudication;
3. C10;
4. slice locking;
5. CPU preflight;
6. Kaggle fixture smoke;
7. approved Compact-20 execution;
8. postrun audit;
9. scorer sanity;
10. Scale-100 decision;
11. naturalistic transfer;
12. Main-500 if justified;
13. paper construction from audited evidence.

Explicitly state when the no-execution ceiling has been reached.

---

# 30. Final Directive

Go all the way on the build.

Repair the codebase, scorer, metrics, task contracts, leakage boundaries, statistics, execution infrastructure, notebooks, CI, release surface, and paper plumbing as far as possible without running scientific experiments.

Be ambitious about engineering and methodology.

Be strict about evidence.

Do not manufacture stronger results.

Do not hide possible null results.

Do not tune the benchmark to force rank instability.

The final repository should be:

> a coherent, leakage-resistant, statistically defensible, scorer-valid, reproducible, dual-T4 execution-ready controlled-intervention benchmark that is as close as honestly possible to NeurIPS Datasets & Benchmarks or DMLR readiness before genuine human validation and model execution begin.
