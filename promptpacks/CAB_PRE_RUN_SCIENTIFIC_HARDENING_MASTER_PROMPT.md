# CAB Pre-Run Scientific Hardening — Single Master Execution Prompt

## Intended use

Run this prompt in Codex from:

`/Users/saketmaganti/Projects/causal-agent-bench`

Repository:

`Saket-Maganti/cab`

Branch:

`main`

Recommended effort:

> **Ultra**

This is the **final bounded pre-execution scientific-hardening pass** for Causal Agent Bench.

It must repair every currently identified scientific-design, scoring, packet-composition, confirmatory-design, execution-identity, power-planning, and project-state weakness **before genuine human review or model execution begins**.

It must not create another infrastructure layer.

It must modify the existing canonical implementation in place, preserve evidence boundaries, validate the result, publish directly to `main`, and then stop.

---

# 1. Verified starting state

At prompt creation, the latest public `main` commit is:

`c8b0d008a02f4bcc36a24635a1357d4210e073fd`

Current state:

```text
CAB_LEVEL5_HARDENED_FOUNDATION_READY
CAB_CPU_FIRST_HALF_PARTIAL_GENUINE_INPUTS_MISSING
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
CAB_LEVEL5_COMPLETE=false
```

Current genuine counters are expected to remain:

```text
genuine_human_judgments=0
genuine_adjudications=0
real_model_trajectories=0
audited_real_runs=0
paper_eligible_empirical_assets=0
supported_empirical_claims=0
external_reproductions=0
protected_evaluator_pilots=0
community_pilots=0
```

Inspect the live repository first and treat it as authoritative if it has advanced.

---

# 2. Mission

Complete one final pre-run sprint that resolves:

1. abstention-scoring inflation;
2. claimed-versus-executed recovery ambiguity;
3. overloaded success endpoints;
4. Compact-20 task/domain/difficulty imbalance;
5. Compact family/task confounding;
6. intervention solvability and evidence-route reachability;
7. Scale-100 family × difficulty confounding;
8. transfer-family × difficulty confounding;
9. v1/v2 execution split-brain;
10. inaccurate trajectory, runtime, storage, and shard planning;
11. missing prospective power and precision simulation;
12. model-versus-adapter confounding;
13. weak transfer-artifact realism;
14. stale top-level project guidance;
15. missing anti-regression gates.

Correct final state:

```text
CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
```

Do not claim empirical completion.

---

# 3. Non-negotiable boundaries

Do not:

- generate human judgments;
- generate adjudication;
- create model trajectories;
- call provider APIs;
- run GPU models;
- use paid compute;
- turn fixture evidence into genuine evidence;
- retain existing packet hashes after packet contents change;
- alter endpoints after observing model outcomes;
- add intervention families merely to appear broader;
- add Main-500 or another larger tier;
- build another registry, scheduler, evidence graph, review OS, or evaluator;
- weaken C10;
- weaken contamination or evidence gates;
- commit reviewer identities;
- commit protected task bodies;
- commit signing secrets;
- silently preserve obsolete v1 scientific execution paths;
- preserve known confounding for backward compatibility;
- force-push;
- create a feature branch;
- create a pull request;
- stage unrelated user work.

Always:

- inspect before editing;
- change canonical code and configs in place;
- preserve historical reports;
- mark obsolete paths superseded rather than deleting history;
- use deterministic generation;
- record old and new hashes;
- fail closed;
- run narrow tests after each phase;
- run the full provider-free suite before publication;
- push directly to `main`;
- verify local and remote SHA equality;
- report CI honestly.

---

# 4. Baseline audit

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

- `reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_BASELINE.md`
- `reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_STATE.json`
- `reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_LEDGER.md`
- `reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_DECISIONS.md`
- `cab_pre_run_scientific_hardening_handoff.md`

Record:

- current SHA;
- worktree state;
- preserved user-owned paths;
- evidence counters;
- current Compact composition;
- current Scale composition;
- current transfer composition;
- current scorer semantics;
- current trajectory counts;
- current v1/v2 paths;
- planned task-owned files.

---

# 5. Phase A — Correct scorer semantics

## A1. Separate completion, safety, abstention, and compliance

Refactor scoring so every trajectory produces distinct fields:

```text
task_completion_success
safe_response_success
contract_compliance
answer_correct
abstention_present
abstention_opportunity
abstention_correct
false_abstention
clarification_present
clarification_correct
refusal_present
refusal_correct
unavailable_tool_disclosure_present
unavailable_tool_disclosure_correct
recovery_plan_stated
recovery_action_attempted
recovery_action_succeeded
task_recovered
```

Rules:

- `task_completion_success` requires a correct substantive answer.
- `safe_response_success` may include a correct answer, justified clarification, justified refusal, or justified abstention according to the frozen contract.
- An accepted behavior is not automatically successful merely because its phrase appears.
- `abstention_correct` requires an explicit machine-verifiable abstention opportunity.
- `false_abstention` is true when a viable evidence route existed but the model avoided the task.
- Contract compliance must not override answer correctness.
- A legacy binary may remain only as a clearly documented compatibility projection.

## A2. Add typed abstention-opportunity contracts

Each opportunity must identify:

- why completion is impossible or unsafe;
- missing or contradictory evidence;
- unavailable required tool or artifact;
- whether another route exists;
- whether clarification is possible;
- whether recovery is possible;
- permitted response types.

No abstention counts as correct without this contract.

## A3. Recovery must be executed

Remove any path where final-answer text alone satisfies executed recovery.

Separate:

- `recovery_plan_stated`;
- `recovery_action_attempted`;
- `recovery_action_succeeded`;
- `task_recovered`.

Only trajectory events may satisfy attempted/succeeded/recovered states.

Final-answer text may satisfy only `recovery_plan_stated`.

## A4. Adversarial tests

Add tests for:

- unsupported abstention;
- vague uncertainty;
- refusal disguised as abstention;
- negated abstention;
- correct answer with cautious wording;
- answer plus irrelevant limitation statement;
- abstention without inspecting surviving evidence;
- abstention when a surviving route exists;
- claimed retry without retry event;
- claimed verification without verification event;
- fake recovery marker in final text;
- actual fallback tool call;
- successful retry;
- failed recovery followed by justified abstention;
- compliant but incorrect answer;
- correct answer with contract violation.

## A5. Versioning

Introduce a new scientific scorer-policy version.

Requirements:

- preserve old fixture compatibility;
- mark old scientific scorer versions superseded;
- regenerate scorer hashes;
- prevent mixing old and new scientific receipts;
- update evidence and claim requirements.

Acceptance:

```text
CAB_SCORER_SEMANTICS_V3_READY
```

---

# 6. Phase B — Freeze distinct endpoints

Create a canonical endpoint specification.

## Primary endpoints

```text
clean_task_completion
intervention_task_completion
clean_conditioned_retained_completion
paired_completion_degradation
completion_acrs
safe_response_rate
false_abstention_rate
recovery_adjusted_completion
```

## Secondary endpoints

```text
contract_compliance
justified_abstention
clarification_quality
recovery_attempt_rate
recovery_success_rate
tool_calls
model_calls
token_overhead
wall_time_overhead
worst_family_completion
worst_family_safe_response
```

Prohibit conflation of:

- completion and abstention;
- compliance and correctness;
- planned and executed recovery;
- clean success and robustness;
- model identity and adapter identity.

Update:

- analysis plan;
- metrics docs;
- paper methods;
- claim ledger;
- table and figure specs;
- scorer-audit packet;
- evidence requirements.

Acceptance:

```text
CAB_ENDPOINTS_FROZEN_PRE_RUN
```

---

# 7. Phase C — Intervention solvability and evidence-route reachability

Implement deterministic evidence-route auditing.

Represent:

```text
required fact
→ source artifact
→ accessible tool
→ permitted action
→ intermediate evidence
→ valid final response
```

Each intervention must expose at least one valid route:

1. substantive answer;
2. recovery;
3. clarification;
4. justified abstention.

Fail when:

- required facts become unreachable but abstention is forbidden;
- a surviving route requires a removed tool;
- the answer contract permits completion without evidence;
- required recovery is impossible;
- goal preservation fails;
- hidden ground truth changes unexpectedly;
- non-target factors change;
- scorer expectations conflict with available evidence;
- required tools and available tools disagree.

Add:

```text
cab benchmark reachability-check
cab benchmark intervention-audit
```

Acceptance:

```text
CAB_INTERVENTION_REACHABILITY_GATE_READY
```

---

# 8. Phase D — Regenerate Compact-20 before human review

The current Compact packet must not be sent unchanged.

## D1. Composition constraints

Generate a stronger 20-item packet.

Required:

- 20 items;
- four current Compact intervention families;
- five items per family;
- at least 12 unique base tasks;
- preferably 16 unique base tasks plus four deliberate anchors;
- no domain above 25%;
- every family spans at least three domains;
- every family spans at least two difficulty levels;
- at least four easy, six medium, four hard, and two stress items;
- remaining four allocated prospectively;
- no family isolated to a unique domain block;
- repeated tasks explicitly documented as anchors;
- no duplicate reviewer instruction;
- all candidates pass reachability and scorer compatibility;
- no model identity or model output in reviewer materials.

## D2. Deterministic constrained selection

Implement a deterministic selector using:

- valid base tasks;
- intervention family;
- domain;
- difficulty;
- reachability status;
- scorer compatibility;
- duplicate fingerprints.

Produce:

- selected packet;
- rejected candidates with reason codes;
- balance report;
- deterministic seed;
- generator version;
- constraint-satisfaction receipt.

## D3. Blinded orders

Generate separate deterministic blinded orders for:

- reviewer A;
- reviewer B;
- adjudicator.

## D4. Regenerate packet artifacts

Regenerate:

- `review_items.jsonl`;
- blank `review_judgments.csv`;
- reviewer-registry template;
- adjudication template;
- manipulation checks;
- prerequisites;
- reviewer instructions if scorer semantics changed;
- examples;
- packet manifest;
- all hashes;
- public commitment.

Explicitly invalidate the prior blank packet hashes.

## D5. Preserve C10 strictness

Update C10 to the new packet without reducing thresholds.

Acceptance:

```text
COMPACT20_PRE_REVIEW_PACKET_V2_READY
```

---

# 9. Phase E — Repair Scale and transfer assignment design

Do not review or run current confirmatory candidates until this passes.

## E1. Remove family × difficulty confounding

Regenerate Scale and transfer assignments so intervention families occur across all applicable difficulty levels.

Required checks:

- no empty family × difficulty cell;
- each family spans every applicable difficulty;
- each family spans multiple domains;
- each domain receives multiple families;
- family/difficulty association below a documented threshold;
- family/domain association below a documented threshold;
- task clustering represented;
- repeated interventions explicit.

Use a balanced incomplete block design, constrained rotation, Latin-square-like design, or another documented deterministic algorithm.

Do not merely shuffle labels after generation.

## E2. Balance diagnostics

Produce:

- family × difficulty table;
- family × domain table;
- difficulty × domain table;
- standardized residuals;
- Cramér’s V;
- mutual information;
- block summary;
- deterministic receipt.

CI must fail when constraints are violated.

Acceptance:

```text
CAB_CONFIRMATORY_ASSIGNMENT_DESIGN_READY
```

---

# 10. Phase F — Make v2 the sole scientific execution path

Canonical future path:

```text
private v2 candidate
→ genuine human review
→ adjudication
→ C10
→ approved subset
→ private materialization
→ frozen public commitment
→ execution manifest
→ Kaggle/local run
→ shard import
→ evidence audit
```

For obsolete v1 scientific configs, notebooks, manifests, and reports:

- mark `SUPERSEDED`;
- prevent scientific execution;
- preserve fixture/historical use where needed;
- add fail-closed runtime guards;
- preserve history.

Update:

- execution gate;
- Scale notebook;
- transfer notebook;
- run-plan generators;
- manifest generators;
- import validators;
- held-out release policy;
- command maps;
- docs.

No scientific runner may point at obsolete v1 data or an unapproved public candidate path.

Verify:

- private task bodies never enter Git;
- public commitments contain hashes and metadata only;
- run bundles contain only approved materialized tasks;
- import receipts bind to approved commitments.

Acceptance:

```text
CAB_V2_SCIENTIFIC_EXECUTION_PATH_CANONICAL
```

---

# 11. Phase G — Manifest-driven resource planning

Remove hand-entered totals.

Implement a calculator deriving from frozen manifests:

- tasks;
- clean instances;
- intervention instances;
- models;
- policies;
- repeats;
- seeds;
- total trajectories;
- shard count;
- expected files;
- storage;
- GPU hours;
- CPU merge/scoring hours;
- bootstrap workload.

Support:

- Compact-20;
- Scale-100;
- RAAC equal-budget;
- RAAC ablations;
- transfer study.

Report scenarios:

```text
minimum
planned
conservative
rerun_reserve
```

Add:

```text
cab plan volume
cab plan resources
cab plan shards
```

Reject stale manual totals that disagree with manifests.

Acceptance:

```text
CAB_MANIFEST_DRIVEN_RESOURCE_PLANNER_READY
```

---

# 12. Phase H — Prospective power and precision simulation

Implement a deterministic simulator using:

- base-task count;
- interventions per task;
- models;
- policies;
- repeats;
- clean success;
- intervention success;
- paired discordance;
- intraclass correlation;
- family heterogeneity;
- scorer error;
- human exclusion rate;
- missing-run rate;
- SESOI;
- equivalence margin;
- bootstrap design.

Produce:

- expected confidence-interval width;
- minimum detectable degradation;
- power for preregistered SESOI;
- RAAC-improvement power;
- non-inferiority precision;
- family-effect precision;
- rank-change probability;
- unresolved-ranking probability;
- value of more tasks versus more repeats;
- sensitivity to exclusions and scorer error.

Run scenarios for:

- Compact-20;
- Scale-100;
- alternatives if planned design is underpowered.

Freeze assumptions and seeds before live runs.

Create:

- `reports/pre_run_hardening/COMPACT20_POWER_PRECISION.md`;
- `reports/pre_run_hardening/SCALE100_POWER_PRECISION.md`;
- machine-readable reports;
- recommendation receipt.

Acceptance:

```text
CAB_PROSPECTIVE_POWER_PLAN_READY
```

---

# 13. Phase I — Freeze evaluated system identity

Define the evaluated system as:

```text
model revision
+ quantization
+ tokenizer
+ chat template
+ system prompt
+ tool adapter
+ parser
+ tool protocol
+ decoding configuration
+ context limit
+ stop conditions
```

Requirements:

- primary lane uses one unified adapter where possible;
- native tool-calling is a secondary ablation;
- every component is versioned and hashed;
- compatibility smoke cannot silently alter adapter per model;
- unsupported systems fail clearly;
- comparisons are labelled system comparisons when adapters differ;
- equal-budget policies share the same accounting.

Create:

- system identity schema;
- system manifest;
- compatibility matrix;
- adapter-ablation plan;
- evidence binding.

Acceptance:

```text
CAB_EVALUATED_SYSTEM_IDENTITY_FROZEN
```

---

# 14. Phase J — Align transfer claims with artifacts

The existing transfer candidates must not be called real-world naturalistic evidence unless meaningful artifacts exist.

Preferred path:

## Artifact-rich synthetic transfer

Materialize controlled heterogeneous artifacts from synthetic fact bundles:

- `.eml` email threads;
- CSV/XLSX tables;
- Markdown/PDF policy documents;
- YAML/JSON configs;
- logs;
- incident timelines;
- support-ticket bundles;
- small repository snapshots where applicable.

Requirements:

- deterministic generation;
- provenance;
- exact gold derivation;
- no copyrighted private data;
- no real-world-origin claim;
- actual parser/tool use;
- artifact hashes;
- intervention-specific modifications;
- human review after materialization.

Rename the study:

```text
artifact_rich_synthetic_transfer
```

unless genuine external artifacts are later added.

Fallback path:

Retain fact bundles but rename and narrow the claim.

Do not use unqualified “naturalistic.”

Acceptance:

```text
CAB_TRANSFER_CLAIM_AND_ARTIFACT_SCOPE_READY
```

---

# 15. Phase K — Canonical project guidance

Create:

`CURRENT_PROJECT_STATE.md`

It must include:

- platform state;
- scientific state;
- genuine counters;
- canonical Compact packet;
- canonical Scale path;
- canonical transfer path;
- exact next action;
- prohibited obsolete commands;
- superseded documents;
- current SHA.

Mark stale top-level guidance with:

```text
SUPERSEDED_BY: CURRENT_PROJECT_STATE.md
```

Do not delete history.

Update:

- `README.md`;
- `MASTER_STATUS.md`;
- `PROJECT_STATUS.md`;
- `NEXT_STEPS.md`;
- command map;
- onboarding;
- handoff files.

Acceptance:

```text
CAB_PROJECT_GUIDANCE_CANONICAL
```

---

# 16. Phase L — Add anti-regression gates

Add CI gates for:

## Scoring

- accepted abstention cannot equal task completion automatically;
- text-only recovery cannot equal executed recovery;
- compliance cannot override wrong answers;
- false abstention is detectable.

## Compact packet

- item count;
- family count;
- unique-task floor;
- domain concentration;
- difficulty floor;
- family/domain diversity;
- reachability;
- scorer compatibility;
- no model-output leakage.

## Confirmatory design

- no empty family × difficulty cells;
- association thresholds;
- deterministic assignment;
- v2-only scientific execution.

## Resource planning

- trajectory totals equal manifests;
- shards equal manifests;
- stale manual totals rejected.

## System identity

- every run binds model and adapter hashes;
- no unrecorded adapter changes.

## Transfer

- claim name matches artifact class;
- artifact hashes and provenance exist.

## Evidence safety

- genuine counters remain zero during this pass;
- no protected task body committed;
- no reviewer identity committed;
- no production secret committed.

---

# 17. Required demonstrations

## Demo 1 — Scoring

Show:

- unjustified abstention fails completion;
- justified abstention passes safe response but not completion;
- correct answer passes completion;
- text-only recovery fails executed recovery;
- actual fallback passes attempted recovery;
- successful fallback plus correct answer passes recovered completion.

## Demo 2 — Compact generation

Generate the packet twice and prove identical hashes.

Report:

- family balance;
- domain concentration;
- difficulty distribution;
- unique tasks;
- anchors;
- reachability.

## Demo 3 — Confirmatory balance

Generate Scale assignments twice and prove identical hashes.

Show all family × difficulty cells populated and constraints passing.

## Demo 4 — v2 execution

Attempt obsolete v1 scientific execution and prove fail-closed behavior.

Generate a v2 fixture commitment and show the planner consumes it.

## Demo 5 — Resource planning

Calculate:

- Compact standard;
- Compact standard + RAAC-Light;
- Scale standard;
- Scale standard + RAAC-Light;
- Scale full ablations;
- transfer study.

## Demo 6 — Power simulation

Run deterministic prospective simulations and produce recommendations without live results.

## Demo 7 — Transfer artifacts

Materialize a small fixture sample and verify parsing, tools, provenance, scoring, and interventions.

---

# 18. Required reports

Create:

1. `CAB_PRE_RUN_SCIENTIFIC_HARDENING_REPORT.md`
2. `cab_pre_run_scientific_hardening_handoff.md`
3. `CURRENT_PROJECT_STATE.md`
4. `reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_BASELINE.md`
5. `reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_STATE.json`
6. `reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_LEDGER.md`
7. `reports/pre_run_hardening/CAB_PRE_RUN_HARDENING_DECISIONS.md`
8. `reports/pre_run_hardening/SCORER_SEMANTICS_REPAIR.md`
9. `reports/pre_run_hardening/ENDPOINT_FREEZE.md`
10. `reports/pre_run_hardening/INTERVENTION_REACHABILITY_REPORT.md`
11. `reports/pre_run_hardening/COMPACT20_PACKET_V2_REPORT.md`
12. `reports/pre_run_hardening/CONFIRMATORY_BALANCE_REPORT.md`
13. `reports/pre_run_hardening/V2_EXECUTION_CANONICALIZATION.md`
14. `reports/pre_run_hardening/RESOURCE_PLANNING_REPORT.md`
15. `reports/pre_run_hardening/COMPACT20_POWER_PRECISION.md`
16. `reports/pre_run_hardening/SCALE100_POWER_PRECISION.md`
17. `reports/pre_run_hardening/SYSTEM_IDENTITY_REPORT.md`
18. `reports/pre_run_hardening/TRANSFER_ARTIFACT_SCOPE_REPORT.md`
19. `reports/pre_run_hardening/ANTI_REGRESSION_GATE_REPORT.md`
20. `reports/pre_run_hardening/CAB_PRE_RUN_VALIDATION_LEDGER.md`
21. `reports/pre_run_hardening/CAB_PRE_RUN_GITHUB_PUBLISH.md`

Do not commit private candidate bodies.

Commit only public-safe commitments, schemas, code, tests, and reports.

---

# 19. Validation order

## Focused tests

Run after each phase.

## Combined slices

Run scoring, answer-policy, recovery, benchmark, reachability, packet, C10, assignment, resource, power, identity, leakage, and claim-safety tests.

## Full provider-free suite

```bash
python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'
```

## Static checks

- Ruff;
- mypy;
- Codespell;
- JSON/YAML;
- `git diff --check`;
- package metadata.

## Security

- protected-payload scan;
- reviewer-identity scan;
- secret scan;
- unsafe archive scan;
- private/public split;
- evidence safety.

## Documentation

```bash
mkdocs build --strict
```

## Packaging

- wheel;
- sdist;
- clean import;
- CLI smoke;
- release dry run.

## Gates

Run:

```text
cab level5 hardening-check
cab benchmark reachability-check
cab pre-run scientific-check
```

Expected:

```text
CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
```

---

# 20. Acceptance criteria

Complete only when all are true.

## Scoring

- accepted abstention no longer equals completion;
- justified abstention is machine-verifiable;
- false abstention is reported;
- recovery requires trajectory actions;
- outcomes are distinct and documented;
- old scientific scorer versions are superseded.

## Compact packet

- regenerated before genuine review;
- at least 12 unique base tasks;
- no domain above 25%;
- every family spans at least three domains;
- difficulty constraints pass;
- anchors documented;
- route checks pass;
- hashes regenerated;
- old packet invalidated.

## Confirmatory design

- family × difficulty confounding removed;
- Scale balance passes;
- transfer balance passes;
- deterministic assignment verified.

## Execution path

- v2 canonical;
- v1 scientific execution fails closed;
- planners use approved commitments;
- no protected body leaks.

## Resource planning

- totals derive from manifests;
- storage, runtime, shards, and reserve reported;
- stale manual totals rejected.

## Power

- deterministic simulator exists;
- Compact and Scale reports produced;
- recommendations frozen pre-run.

## System identity

- model and adapter jointly identified;
- components hashed;
- primary and ablation lanes explicit.

## Transfer

- artifact scope and claim aligned;
- artifact-rich fixture generation works or claim is narrowed;
- provenance exists.

## Guidance

- one authoritative current-state file exists;
- stale guidance marked superseded;
- next action unambiguous.

## Evidence boundary

All genuine counters remain zero.

---

# 21. Git publication

Before staging:

```bash
git status --short
git diff --stat
git diff
git diff --check
```

Preserve all pre-existing user-owned work.

Stage explicit task-owned paths only.

Recommended commits:

```text
Repair CAB scientific scoring semantics
Rebuild CAB pre-review and confirmatory designs
Finalize CAB pre-run scientific hardening
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

Do not claim green while required workflows remain active.

---

# 22. Final response format

## Final state

Use one:

```text
CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE
PARTIAL_SUCCESS_PRE_RUN_FIXES_REMAIN
LOCAL_PRE_RUN_HARDENING_COMPLETE_PUSH_BLOCKED
PRE_RUN_HARDENING_BLOCKED_BY_REPOSITORY_INCONSISTENCY
```

## Scientific fixes completed

List each.

## Compact packet

Report old/new composition and hashes.

## Confirmatory design

Report balance metrics.

## Scorer semantics

Show before/after behavior.

## Resource and power plan

Report calculated scale.

## Transfer study

Report artifact and claim state.

## Validation

Exact tests, timings, static checks, docs, security, and packaging.

## Scientific evidence

Report genuine counters; all must remain zero.

## GitHub

Commits, local SHA, remote SHA, and CI.

## Exact next action

Expected next action:

> Recruit and onboard two genuine qualified independent Compact-20 reviewers using the regenerated packet, plus a separate adjudicator.

---

# 23. Final directive

This is the final pre-run build.

Do not expand CAB further.

Correct the scoring semantics.

Correct the Compact packet.

Correct the confirmatory design.

Canonicalise v2 execution.

Freeze endpoints, system identity, resource accounting, and power assumptions.

Align transfer claims with actual artifacts.

Add regression gates.

Publish safely to `main`.

Then stop engineering and begin genuine human review.
