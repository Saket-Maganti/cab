# CAB Reviewer-Ready V2 — Final Focused Scientific-Kernel Repair Master Prompt

## Role

You are an expert operating directly inside the existing **Causal Agent Bench (CAB)** repository.

Repository:

```text
/Users/saketmaganti/Projects/causal-agent-bench
```

The latest known Git commit from the independent audit is:

```text
267491d96a4d9746c35b404272cb021e2dca83ad
```

Do not assume the worktree is clean, the documentation is current, or the latest generated reports are correct. Inspect and verify everything before modifying anything.

Use the highest available reasoning/effort setting.

---

# 1. Mission

Perform **one final, narrow, evidence-safe repair pass** that fixes every known blocker preventing CAB from being sent to genuine human reviewers.

The goal is not another maturity layer, another broad framework, or another collection of planning documents.

The goal is:

> Replace the flawed current private Compact-20 scientific kernel with a genuinely paired, semantically diverse, intervention-valid, privacy-safe reviewer-ready packet; connect the complete two-stage human-review workflow end to end; update canonical paths and documentation; verify release provenance; and freeze the repository in a clean state ready for two independent human reviewers.

Do not execute models.

Do not perform genuine human review.

Do not fabricate annotations, agreement, adjudication, C10, evidence, trajectories, results, or claims.

At completion, CAB must be ready for the **first genuine Stage-1 human review**, but it must still honestly report:

```text
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
GENUINE_HUMAN_JUDGMENTS=0
GENUINE_MODEL_TRAJECTORIES=0
PAPER_ELIGIBLE_EMPIRICAL_ASSETS=0
SUPPORTED_EMPIRICAL_CLAIMS=0
CAB_LEVEL5_COMPLETE=false
CAB_LEVEL6_COMPLETE=false
```

---

# 2. Why This Repair Is Required

The independent audit found that the surrounding infrastructure is strong, but the currently frozen private Compact-20 and reviewer workflow are not yet scientifically or operationally sufficient.

Known problems that must all be corrected:

1. The current final-private Compact-20 is not represented as explicit clean/intervention pairs.
2. “Twenty unique tasks” mostly means unique IDs and artifacts, not twenty semantically distinct objectives.
3. The four claimed anchors are flags on unique rows, not true controlled repeated anchors.
4. Intervention family is perfectly confounded with required response type:
   - tool removal → abstention;
   - tool failure → recovery;
   - memory corruption → clarification;
   - observation conflict → completion.
5. Several interventions are declarations or proof-route constructions rather than actual environment transformations.
6. Observation conflict does not always inject a genuine executable conflict.
7. Memory corruption does not always corrupt a previously valid, task-critical memory field.
8. Tool removal can incorrectly force abstention even when arithmetic, visible evidence, or another legitimate route remains.
9. Tool failure recovery relies too heavily on a general `read_file`-style oracle fallback.
10. Abstention opportunities are not always proven by complete route exhaustion.
11. Stage-1 reviewer packages do not expose enough clean/intervention structure to assess intervention isolation, goal preservation, or C10 dimensions.
12. Stage-1 packages do not contain a complete structured review form.
13. The final-private two-stage workflow is not fully connected from reviewer ingestion through C10 and slice lock.
14. Existing commands and canonical docs still default to retired exposed review paths.
15. Stage-2 plaintext and its encryption key coexist in the same archive.
16. The uploaded repository worktree was not clean even though the scientific freeze files remained hash-consistent.
17. The external exact-commit release attestation was absent.
18. Distribution hashes in the uploaded archive did not substantiate the hashes quoted in the latest handoff.
19. Compact-20 is not powered for confirmatory claims and must be labeled as a pilot/feasibility study.
20. The central rank-instability claim lacks prospective power/sensitivity calibration.
21. Fixed-panel inference must not be generalized to all LLM agents.
22. Interaction power was below conventional confirmatory adequacy.
23. Builder-authored reports have repeatedly claimed completion before deeper invariants were satisfied.

This prompt exists to fix these issues once, narrowly, and then stop engineering.

---

# 3. Non-Negotiable Boundaries

## 3.1 No execution

Do not perform:

- provider calls;
- paid API calls;
- local LLM inference;
- GPU benchmark runs;
- live agent execution;
- genuine human review;
- genuine reviewer qualification;
- genuine adjudication;
- empirical result generation.

Provider-free deterministic tests and fixture-only workflow tests are allowed.

## 3.2 No fabrication

Never create or imply:

- genuine reviewer identities;
- genuine reviewer scores;
- genuine annotations;
- agreement values from fake reviewers;
- C10 PASS;
- a reviewed slice;
- paper-eligible evidence;
- model trajectories;
- ACRS results;
- rank reversals;
- supported C1–C10 claims.

Fixture reviewers may be used only under test-only temporary directories and must be visibly labeled:

```text
SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE
```

Fixture judgments must never enter:

- `private_data/` final review paths;
- production review receipts;
- C10 reports;
- claim ledgers;
- paper assets;
- run authorization.

## 3.3 No new maturity level

Do not add:

- Level 7;
- a new benchmark constitution;
- a new governance framework;
- a new broad dashboard suite;
- another generic “ultimate” architecture;
- unrelated refactors.

Use the existing architecture wherever sound.

## 3.4 Preserve history, retire flawed packets

Do not rewrite Git history.

Do not delete historical development artifacts without a backup.

Permanently retire every exposed or scientifically invalid packet from genuine use.

## 3.5 Private data must never be committed

Never stage or commit:

- candidate bodies;
- private manifests;
- Stage-2 golds;
- Stage-2 accepted variants;
- answer contracts;
- recovery authorizations;
- abstention labels;
- private reviewer mappings;
- encryption keys;
- decrypted Stage-2 files;
- reviewer submissions.

The tracked repository may contain only:

- schemas;
- generators;
- validators;
- public commitments;
- hashes;
- path conventions;
- empty templates;
- non-sensitive readiness reports;
- fixture-only tests.

## 3.6 Do not leak the new packet in output

Terminal output, logs, reports, commit messages, test names, and final summaries must not print:

- private prompts;
- private artifacts;
- expected answers;
- route labels;
- accepted variants;
- private IDs;
- Stage-2 contents.

Output only aggregate counts, hashes, statuses, and safe paths.

---

# 4. Required Final State

The final tracked repository and private reviewer packet must satisfy all of the following:

```text
CAB_REVIEWER_READY_V2_REPAIR_COMPLETE
CAB_NEW_PRIVATE_COMPACT20_V2_READY
CAB_CLEAN_INTERVENTION_PAIRING_VALIDATED
CAB_SEMANTIC_DIVERSITY_VALIDATED
CAB_TRUE_ANCHORS_VALIDATED
CAB_INTERVENTION_OPERATORS_EXECUTABLE
CAB_ROUTE_RESPONSE_CONFOUND_REDUCED
CAB_STAGE1_PACKAGES_READY
CAB_STAGE1_LEAKAGE_AUDIT_PASSED
CAB_STAGE2_ENCRYPTED_AND_KEY_EXTERNAL
CAB_TWO_STAGE_WORKFLOW_E2E_FIXTURE_VALIDATED
CAB_CANONICAL_PATHS_UPDATED
CAB_RETIRED_PACKETS_BLOCKED
CAB_SCIENTIFIC_FREEZE_V2_VALID
CAB_REPOSITORY_CLEAN
CAB_EXACT_COMMIT_ATTESTATION_CREATED
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
CAB_LEVEL5_COMPLETE=false
CAB_LEVEL6_COMPLETE=false
```

Do not print these statuses unless every corresponding hard gate passes.

---

# 5. Phase 0 — Baseline, Safety, and Worktree Reconciliation

Before changing code:

1. Record:
   - current branch;
   - current HEAD;
   - remotes;
   - `git status --short`;
   - tracked modifications;
   - untracked files;
   - ignored private paths;
   - current private packet locations;
   - existing Stage-2 plaintext/key locations;
   - existing distribution artifacts;
   - existing exact-commit attestations.

2. Create a local, private, non-Git backup of:
   - the current `private_data/` tree;
   - current reviewer ZIPs;
   - Stage-2 plaintext;
   - Stage-2 key;
   - scientific freeze manifests;
   - external attestation if found.

3. Store the backup outside the repository root under a timestamped owner-only directory, for example:

```text
~/.cab/private_backups/<timestamp>/
```

Use permissions equivalent to:

```text
0700 directories
0600 files
```

4. Compute a backup inventory with SHA-256 hashes.

5. Do not print private filenames containing answer/gold content beyond safe relative directory names.

6. Reconcile the dirty worktree:
   - inspect every tracked diff;
   - restore timestamp-only or stale regenerated changes that are not scientifically meaningful;
   - intentionally preserve meaningful changes by incorporating them into this repair;
   - move valuable untracked prompt packs or local notes to an ignored local archive rather than deleting them;
   - do not commit giant prompt archives unless they are already part of the repository’s intended tracked surface.

7. Create a short internal baseline report containing only:
   - HEAD;
   - dirty-file counts;
   - private-backup path;
   - backup inventory hash;
   - known blockers;
   - no private content.

Suggested tracked report:

```text
reports/reviewer_ready_v2/BASELINE_AUDIT.json
```

---

# 6. Phase 1 — Retire All Prior Review Packets

Create or update a single machine-readable retired-packet registry.

Suggested path:

```text
reports/reviewer_ready_v2/RETIRED_PACKET_REGISTRY.json
```

It must include every known previous review packet, including:

- public Compact development packets;
- `compact20_real_review`;
- older V1/V2 review packages;
- `compact20-final-private-v1`;
- any packet whose design, answers, routes, or identifiers were exposed during development or audit.

Each entry must include:

```text
packet_version
status
retirement_reason
eligible_for_genuine_review=false
eligible_for_c10=false
eligible_for_model_execution=false
eligible_for_paper_claims=false
public_commitment_or_hash_if_safe
replacement_version
```

Required status:

```text
EXPOSED_OR_INVALID_DEVELOPMENT_FIXTURE_NOT_ELIGIBLE_FOR_GENUINE_REVIEW
```

Update all validators and execution gates so that any retired packet is rejected automatically.

Do not merely document retirement. Enforce it in code.

Add hostile tests proving that:

- a retired packet cannot be ingested as genuine review;
- a retired packet cannot produce C10;
- a retired packet cannot be slice-locked;
- a retired packet cannot authorize execution;
- a renamed copy with the same packet commitment is still rejected.

---

# 7. Phase 2 — Design the New Private Compact-20 V2

Create a new, unseen packet version.

Suggested version:

```text
compact20-review-ready-v2
```

Suggested private root:

```text
private_data/human_review/compact20-review-ready-v2/
```

This directory must remain ignored by Git.

## 7.1 Unit of evaluation

The scientific unit must be an explicit pair:

```text
base task
clean instance
intervention instance
paired comparison
```

Every pair must include a private machine-readable specification containing:

```text
pair_id
base_task_id
semantic_objective_id
domain
difficulty
intervention_family
route_requirement_clean
route_requirement_intervention
anchor_group_id_or_null
clean_instance_id
intervention_instance_id
shared_goal
clean_prompt
intervention_prompt
clean_environment
intervention_environment
primitive_evidence_manifest
declared_tool_contracts
intervention_operator
intended_changed_factor
preserved_invariants
clean_gold_private
intervention_gold_or_policy_private
clean_answer_contract_private
intervention_answer_contract_private
clean_scorer_contract_private
intervention_scorer_contract_private
recovery_authorization_private_or_null
abstention_opportunity_private_or_null
clarification_requirement_private_or_null
```

Private fields must never enter Stage 1.

## 7.2 Composition

Generate exactly 20 paired evaluation units:

- four intervention families;
- five pairs per family;
- eight or more domains;
- no domain above three pairs;
- four easy;
- eight medium;
- four hard;
- four stress;
- at least 16 genuinely distinct semantic task objectives;
- four true repeated anchors.

## 7.3 True anchors

The four anchors must be controlled repetitions derived from four of the 16 distinct base objectives.

Each anchor must preserve:

- semantic objective;
- underlying answer logic;
- difficulty;
- intervention family;
- intended route requirement.

It may vary only controlled nuisance properties such as:

- record order;
- irrelevant identifier names;
- formatting;
- harmless distractor order;
- tool-output ordering where semantics remain unchanged.

Every anchor must have:

```text
anchor_group_id
anchor_source_pair_id
allowed_nuisance_differences
forbidden_semantic_differences
```

Add validators proving that anchors are actual semantic repetitions rather than unrelated items with a boolean flag.

## 7.4 Prompt quality

Prompts must directly state the user’s objective.

Do not use generic wording such as:

```text
Resolve request 1837 using the declared records.
```

Use natural, task-specific objectives.

Every prompt must make clear:

- what outcome the user wants;
- relevant constraints;
- what information is available;
- what action or answer is expected.

## 7.5 Semantic diversity

Do not equate unique IDs with unique tasks.

Create deterministic semantic-diversity checks using non-model methods such as:

- normalized objective signatures;
- task-archetype labels;
- token n-gram similarity;
- MinHash or equivalent;
- structural schema signatures;
- required-operation signatures;
- gold-derivation graph signatures.

Requirements:

- at least 16 distinct objective signatures;
- no more than two non-anchor pairs sharing the same task archetype;
- anchors excluded from uniqueness counts but validated separately;
- no prompt-template cluster may dominate the packet;
- no domain may map to only one operation type;
- no intervention family may use only one task archetype.

Fail generation if diversity requirements are not met.

---

# 8. Phase 3 — Remove Family/Response-Type Confounding

The current one-family/one-response mapping must be eliminated.

Use the following target matrix unless a stronger scientifically justified matrix is derived and documented:

| Intervention family | Completion | Recovery | Clarification | Abstention | Total |
|---|---:|---:|---:|---:|---:|
| Tool removal | 2 | 2 | 0 | 1 | 5 |
| Tool failure | 1 | 3 | 1 | 0 | 5 |
| Memory corruption | 2 | 0 | 2 | 1 | 5 |
| Observation conflict | 2 | 0 | 2 | 1 | 5 |
| **Total** | **7** | **5** | **5** | **3** | **20** |

Small adjustments are allowed only when:

- the route is scientifically implausible for a specific family;
- no family maps exclusively to one response type;
- no response type is confined to one family;
- the final matrix is frozen prospectively;
- the reason is documented before review.

Do not optimize the matrix after observing human or model outcomes.

Add a confounding audit that reports:

- family × route matrix;
- domain × family matrix;
- difficulty × family matrix;
- archetype × family matrix;
- route × difficulty matrix.

Fail if any major factor is deterministically confounded.

---

# 9. Phase 4 — Implement Real Intervention Operators

Every intervention must be an executable environment transformation applied to a clean instance.

Do not generate an intervention instance merely by selecting a different expected route.

Implement or repair actual operators for:

```text
remove_tool
inject_tool_failure
corrupt_memory_field
inject_conflicting_observation
```

Each operator must produce:

```text
clean_state
intervention_patch
intervention_state
structural_diff
intended_changed_factor
preserved_invariants
```

## 9.1 Tool removal

Tool removal must:

- remove or revoke one specific capability;
- preserve unrelated tools;
- preserve the task goal;
- preserve unaffected evidence;
- record exact capability loss;
- test whether another legitimate route remains.

Do not label abstention correct merely because the preferred tool is absent.

## 9.2 Tool failure

Tool failure must:

- make a declared tool call fail through the actual tool runtime;
- define the failure type;
- preserve unrelated tools and evidence;
- permit only explicitly declared fallback routes;
- prevent a later unrelated success from inheriting recovery credit.

## 9.3 Memory corruption

Memory corruption must:

- start from a valid clean memory field;
- corrupt, stale, delete, or conflict a task-critical field;
- identify the exact field and clean value privately;
- preserve unrelated memory fields;
- demonstrate why completion, verification, clarification, or abstention is required.

Do not manufacture a clarification request for a field that was never part of the clean task.

## 9.4 Observation conflict

Observation conflict must:

- inject at least two genuinely inconsistent observations;
- define source provenance and trust hierarchy;
- preserve the underlying task goal;
- preserve non-conflicting evidence;
- ensure the conflict is visible through actual tool observations;
- specify whether resolution, clarification, or abstention is justified.

Do not validate conflict merely by declaring that a conflict exists.

## 9.5 Isolation audit

For every pair, automatically verify:

```text
exact intended mutation count
allowed incidental metadata differences
forbidden semantic differences
goal preservation
primitive evidence preservation where required
tool-contract preservation where required
no hidden answer-bearing field introduced
```

The isolation validator must fail closed.

---

# 10. Phase 5 — Primitive Evidence and Tool Contracts

## 10.1 Primitive-only evidence

Artifacts may contain primitive facts only.

Forbidden answer-bearing fields include, but are not limited to:

```text
selected_option
selected_vendor
final_total
final_answer
final_decision
claim_supported
approval_required
first_open_slot
recommended_choice
best_option
computed_refund
resolved_status
```

Create a stronger negative-control scanner that detects:

- forbidden field names;
- synonyms;
- direct answer duplication;
- derived totals;
- pre-ranked options;
- boolean conclusions;
- source fields equal to private gold;
- answer-bearing filenames;
- answer-bearing metadata.

## 10.2 No universal oracle reader

Remove the general artifact-reader fallback from the scientific route unless it is capability-bounded.

A tool must not return the entire underlying artifact merely because a preferred tool failed.

Every tool must have:

```text
tool_id
declared_capability
allowed_arguments
returned_fields
failure_modes
authorization_scope
```

If a generic file reader remains for engineering reasons:

- it must not be declared to scientific agents by default;
- it must not appear in valid route proofs unless the task explicitly grants it;
- it must support locator-scoped reads rather than full-file dumping;
- it must be rejected as an undeclared oracle in hostile tests.

## 10.3 Ordinary reasoning remains allowed

Route-exhaustion logic must account for what an agent can derive from already visible facts using ordinary reasoning.

At minimum, closure must include:

- arithmetic;
- comparison;
- sorting;
- set membership;
- filtering;
- date/time comparison;
- conjunction of visible conditions;
- direct lookup from visible primitive observations.

Do not mark abstention correct if the answer remains derivable without the removed tool.

---

# 11. Phase 6 — Executable Causal Route Validation

Build route validation around the actual clean/intervention environments and actual tool registry.

The validation path must be:

```text
private pair specification
→ instantiate clean environment
→ apply intervention operator
→ expose declared tools
→ execute authorized actions
→ collect real tool observations
→ derive facts from observations
→ derive candidate outcome without hidden gold
→ compare candidate outcome with private gold/policy only at the final validation boundary
```

Hidden gold, expected fact IDs, route labels, or answer contracts must not be accessible to:

- tool execution;
- observation creation;
- fact extraction;
- route search;
- recovery authorization matching.

## 11.1 Completion proof

Completion requires:

- sufficient observed facts;
- valid derivation;
- correct final answer;
- contract compliance.

## 11.2 Recovery proof

Recovery requires all of:

```text
primary failure occurred
authorized fallback action matched exactly
fallback followed the failure
tool ID matched
arguments matched
budget remained
fallback observation came from that action
fallback observation contained sufficient primitive facts
final answer was correct
```

No recovery state may leak across unrelated later actions.

## 11.3 Clarification proof

Clarification requires:

- a task-critical missing, corrupted, or unresolved field;
- no valid completion route without that field;
- a specific clarification question that would resolve the uncertainty;
- no generic “please clarify” credit;
- no clarification credit when enough evidence remains.

## 11.4 Abstention proof

Abstention requires:

- all declared tool routes exhausted or invalid;
- all visible-evidence reasoning routes exhausted;
- no allowed recovery route;
- no targeted clarification capable of resolving the issue;
- a safe and specific abstention explanation.

A mere `abstention_opportunity` object is not sufficient.

## 11.5 Hostile tests

Add hostile cases for:

- wrong tool;
- correct tool, wrong arguments;
- wrong order;
- recovery before failure;
- unrelated success after failure;
- stale authorization;
- authorization inherited across steps;
- undeclared fallback;
- full-artifact oracle access;
- hidden-gold access;
- expected-fact injection;
- answer-bearing source field;
- false abstention despite arithmetic solvability;
- generic clarification despite available evidence;
- conflict declaration without conflicting observations;
- memory corruption without a clean predecessor field;
- tool removal that removes more than one capability;
- intervention patch that changes the goal;
- intervention patch that changes unrelated evidence.

---

# 12. Phase 7 — Build Reviewer-Ready Stage-1 Packages

Generate two reviewer-specific Stage-1 packages:

```text
stage1_reviewer_a.zip
stage1_reviewer_b.zip
```

Use independent randomized item order and reviewer-specific opaque IDs.

Do not expose stable private candidate IDs.

Maintain the reviewer-ID mapping only in the private coordinator area.

## 12.1 What Stage 1 must show

For each item, Stage 1 must include:

- natural-language task objective;
- clean task context;
- intervention task context or a clear controlled diff;
- primitive artifacts necessary for assessment;
- declared tool capabilities;
- intended intervention family;
- intended changed factor;
- claimed preserved invariants;
- difficulty and domain only if they do not leak the answer;
- structured review form.

Reviewers must be able to assess the intervention itself.

## 12.2 What Stage 1 must hide

Stage 1 must not reveal:

- clean gold;
- intervention gold;
- accepted variants;
- scorer internals;
- route labels;
- expected response type;
- preferred fallback;
- recovery authorization;
- abstention correctness;
- clarification requirement;
- answer-bearing fact IDs;
- private manifest paths;
- source-code paths that allow trivial lookup;
- Stage-2 filenames or hashes that expose content.

## 12.3 Stage-1 review form

Provide a machine-readable and human-friendly form with one row per item.

Required dimensions:

```text
reviewer_item_id
task_clarity
clean_goal_clear
clean_evidence_sufficient
clean_solvable
intervention_understandable
intended_factor_identifiable
goal_preserved
single_factor_isolation
preserved_invariants_hold
primitive_evidence_adequate
declared_tools_adequate
intervention_realistic
ambiguity_present
response_space_structurally_valid
exclude_item
reviewer_confidence
notes
```

Use constrained enums and validation rules.

Do not prefill judgments.

## 12.4 Reviewer instructions

Include:

- independence requirement;
- conflict-of-interest declaration;
- no author/coauthor reviewers;
- no AI assistance;
- separate work;
- confidentiality;
- no sharing between Reviewer A and B;
- exact submission format;
- correction policy;
- expected time per item;
- escalation path for malformed packages.

## 12.5 Qualification

Create a qualification packet separate from the final 20.

Requirements:

- qualification items must not reuse final tasks;
- qualification answer key remains private;
- pass threshold remains at least 0.80 unless the existing frozen C10 contract requires stricter behavior;
- qualification completion cannot be fabricated;
- production workflow remains blocked until both genuine reviewers pass.

---

# 13. Phase 8 — Stage-1 Leakage Audit

Create a fail-closed leakage scanner over:

- extracted ZIP contents;
- filenames;
- archive metadata;
- READMEs;
- manifests;
- review forms;
- artifacts;
- tool descriptions;
- intervention diffs.

The scanner must compare Stage-1 content against private Stage-2 material and reject leakage of:

- exact answers;
- accepted variants;
- normalized answers;
- scorer expressions;
- route labels;
- recovery action IDs;
- abstention labels;
- clarification target values;
- private IDs;
- answer-bearing fact IDs;
- obvious paraphrases encoded as structured fields.

Add structural denylist checks and value-level checks.

The final report may state only aggregate pass/fail counts and package hashes.

Do not print leaked values during tests.

---

# 14. Phase 9 — Secure Stage-2 Vault

The final reviewer-ready state must not contain Stage-2 plaintext next to its key.

## 14.1 Key location

Require an external key path through an environment variable:

```text
CAB_STAGE2_KEY_PATH
```

The key must live outside the repository root.

If the variable is unset, generation must fail closed with a clear instruction.

Do not silently create the key inside the repository.

Use owner-only permissions.

## 14.2 Vault behavior

Store only encrypted Stage-2 material in the private project area.

Do not persist decrypted Stage-2 plaintext.

When Stage 2 is later unlocked:

- decrypt into memory or an owner-only temporary directory;
- generate reviewer-specific Stage-2 packages;
- delete temporary plaintext immediately;
- verify no plaintext remains;
- log only hashes and counts.

## 14.3 Stage-2 contents

Stage 2 may include:

- clean gold;
- intervention gold or valid policy;
- accepted variants;
- answer contracts;
- scorer contracts;
- recovery authorization;
- abstention opportunity;
- clarification requirement;
- source-to-gold rationale.

It must still exclude model outputs because task validity review occurs before model evaluation.

---

# 15. Phase 10 — Implement the Complete Two-Stage Workflow

Provide one canonical CLI workflow integrated with the current CAB CLI architecture.

Use existing naming conventions where practical.

Required production commands or equivalent subcommands:

```text
generate-private-packet
validate-private-packet
generate-stage1-packages
validate-stage1-packages
ingest-reviewer-qualification
ingest-stage1
validate-stage1-submissions
commit-stage1
unlock-stage2
generate-stage2-packages
ingest-stage2
validate-stage2-submissions
build-disagreement-queue
ingest-adjudication
compute-agreement
run-c10
build-exclusion-register
lock-reviewed-slice
authorize-model-execution
```

## 15.1 Stage-1 commitment

Stage-1 commitment must bind:

- private packet commitment;
- Reviewer A package hash;
- Reviewer B package hash;
- qualification receipt hashes;
- Reviewer A submission hash;
- Reviewer B submission hash;
- reviewer pseudonymous IDs;
- review schema version;
- scientific freeze hash;
- exact Git commit.

Stage 2 must remain inaccessible until this receipt validates.

## 15.2 Stage-2 unlock

The unlock command must require:

- valid Stage-1 commitment;
- both qualified reviewers;
- complete Stage-1 submissions;
- no unresolved malformed rows;
- external key availability;
- matching packet commitment;
- matching freeze hash;
- matching code commit or explicitly versioned migration.

## 15.3 Adjudication

Adjudicator materials must be generated only after the disagreement queue exists.

Do not pre-generate a generic adjudicator package for all items.

Adjudication must bind each decision to:

- disputed item;
- reviewer judgments;
- adjudicator pseudonymous ID;
- rationale;
- final decision;
- timestamp;
- submission hash.

## 15.4 C10

C10 must use genuine validated review data only.

It must fail if:

- reviewer identities are missing;
- reviewers are unqualified;
- reviews are synthetic fixtures;
- coverage is incomplete;
- agreement is below threshold;
- adjudication is unresolved;
- intervention isolation fails;
- goal preservation fails;
- gold/scorer review is incomplete;
- packet or freeze bindings mismatch.

The repository must finish this repair with:

```text
C10_PENDING_GENUINE_REVIEW
```

not PASS.

## 15.5 Slice lock

Slice lock must be impossible before C10 PASS.

The reviewed slice must bind:

- included pairs;
- excluded pairs and reasons;
- review receipts;
- adjudication receipt;
- C10 report;
- scorer;
- endpoints;
- analysis plan;
- system-identity schema;
- exact commit;
- private packet commitment.

## 15.6 Execution authorization

Model execution must remain blocked until a valid slice-lock receipt exists.

Add hostile tests proving that no manual file edit or boolean override can bypass the gate.

---

# 16. Phase 11 — Fixture-Only End-to-End Workflow Test

Create a completely separate test fixture packet under a temporary test path.

It must not reuse final-private candidate bodies, IDs, answers, or keys.

Exercise the entire workflow:

```text
fixture packet generation
→ Stage-1 package generation
→ qualification fixture
→ Stage-1 fixture ingestion
→ Stage-1 commitment
→ Stage-2 fixture unlock
→ Stage-2 fixture ingestion
→ disagreement queue
→ fixture adjudication
→ C10 fixture evaluation
→ fixture slice lock
→ fixture execution authorization
```

Mark every fixture artifact:

```text
SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE
```

Production reports must reject fixture receipts.

The test proves workflow mechanics only.

It must not change genuine evidence counters.

---

# 17. Phase 12 — Compact and Power-Plan Corrections

## 17.1 Compact status

Update all tracked plans and paper language so Compact-20 is described as:

- pilot;
- feasibility study;
- protocol validation;
- scorer audit basis;
- runtime and resource calibration;
- effect-direction exploration.

Do not call Compact-20 confirmatory or adequately powered for broad scientific claims.

## 17.2 Scale-100 status

Retain Scale-100 as the primary confirmatory design if its assumptions remain valid.

State explicitly:

```text
Inference applies to the fixed evaluated model panel unless a model-superpopulation design is separately preregistered.
```

## 17.3 Rank-instability calibration

Add prospective simulation for the central rank-instability claim.

Simulate:

- plausible clean-success distributions;
- clean/intervention correlations;
- family-specific degradation;
- tied ranks;
- missing trajectories;
- scorer noise;
- five-model fixed panels;
- multiple effect-size grids;
- probabilities of at least one meaningful rank reversal;
- Spearman and Kendall uncertainty;
- top-model identity change;
- rank-shift magnitude.

Report sensitivity across small, medium, and large degradation regimes.

Do not use these simulations as empirical findings.

## 17.4 Interaction claim

Because prior model × family interaction power was below 0.80:

- either revise the confirmatory design prospectively to reach adequate power;
- or designate model × family interaction as secondary/exploratory.

Do not claim confirmatory adequacy merely because power is above null.

## 17.5 SESOI sensitivity

Include smaller degradation assumptions, not only large alternatives.

At minimum examine mean degradation regimes near:

```text
0.03
0.05
0.08
0.10
0.15
```

Clearly separate:

- planning assumptions;
- powered estimands;
- exploratory estimands;
- unsupported generalizations.

---

# 18. Phase 13 — Canonical Documentation and Path Repair

Create one authoritative machine-readable path registry.

Suggested path:

```text
reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json
```

It must identify:

```text
active_private_packet_version
active_private_root
active_stage1_package_paths
active_stage2_vault_path
external_key_environment_variable
active_review_schema
active_c10_contract
active_scientific_freeze
active_public_commitment
retired_packet_registry
canonical_review_runbook
canonical_cli_commands
```

Update:

- `README.md`;
- `CURRENT_PROJECT_STATE.md`;
- `PROJECT_STATUS.md` if still canonical;
- human-review runbooks;
- C10 runbooks;
- execution runbooks;
- default CLI paths;
- configuration defaults;
- package references.

Remove or fail closed on defaults pointing to retired paths.

Historical reports may remain, but must be visibly marked as superseded where necessary.

The canonical documentation must say:

```text
The repository is engineering-ready for genuine Stage-1 review.
No genuine review has occurred.
Stage 2 remains locked.
C10 has not passed.
Model execution is prohibited.
```

---

# 19. Phase 14 — Reviewer Package Usability Checks

No genuine human review may occur in this prompt.

Perform only automated usability checks:

- every referenced file exists;
- every item opens from the ZIP;
- no broken relative paths;
- review forms contain exactly one row per item;
- opaque IDs are consistent within each reviewer package;
- Reviewer A and B order differs;
- package instructions are complete;
- qualification package is separate;
- Stage-1 content supports every requested Stage-1 judgment;
- no Stage-2 leakage;
- ZIPs extract safely;
- no path traversal;
- no hidden files;
- no source-code lookup path;
- no private manifest;
- package size is reasonable;
- package hashes are stable.

Also create a disposable 3–5-item **usability-pilot generator** for later use with a human, but do not expose or replace the final packet and do not fabricate pilot feedback.

The usability pilot must use separate non-final items.

---

# 20. Phase 15 — Scientific Freeze V2

Create a new scientific freeze covering the repaired reviewer-ready design.

The freeze must bind:

- packet generator source hash;
- generator commit provenance;
- private packet public commitment;
- pair schema;
- intervention operators;
- tool contracts;
- primitive-evidence rules;
- route validator;
- Stage-1 schema;
- Stage-1 package hashes;
- Stage-2 encrypted vault hash;
- Stage-2 schema;
- C10 contract;
- scorer;
- endpoints;
- analysis plan;
- power plan;
- system-identity schema;
- retired-packet registry;
- active-path registry;
- two-stage workflow version.

Do not bind the external key value.

Do not expose private content.

Generate a public freeze manifest containing safe hashes only.

Verify every frozen file directly from disk.

Add a provenance check proving that the committed generator source at the recorded commit matches the source used to generate the private packet.

---

# 21. Phase 16 — Clean Repository and Exact Release Attestation

## 21.1 Final tracked state

Before the final commit:

- all intended tracked changes must be staged;
- no private material may be staged;
- no stale generated reports may remain modified;
- no old distribution artifacts may be treated as current;
- untracked local prompt archives must be moved to ignored local storage or intentionally excluded.

Create logical commits, preferably:

1. scientific-kernel redesign;
2. two-stage reviewer workflow and security;
3. canonical docs, gates, tests, and freeze.

Do not commit after creating the exact final release attestation.

## 21.2 Clean build

After the final tracked commit:

1. create a clean temporary clone or worktree at the exact final commit;
2. install/use the declared reproducible build environment;
3. build wheel and sdist twice;
4. normalize only using the repository’s documented deterministic procedure;
5. verify the two builds match;
6. compute exact hashes;
7. run the focused reviewer-ready suite;
8. run the full provider-free suite;
9. run lint, type, spelling, docs, security, package and secret checks.

## 21.3 External attestation

Create an exact-commit attestation outside the repository.

Use an environment variable if already defined, otherwise use a stable owner-only location such as:

```text
~/.cab/attestations/cab-review-ready-v2-<commit>.json
```

The attestation must contain:

```text
exact_commit
branch
scientific_freeze_hash
public_packet_commitment
stage1_reviewer_a_hash
stage1_reviewer_b_hash
encrypted_stage2_vault_hash
wheel_hash
normalized_sdist_hash
test_summary
build_environment
timestamp
```

Set owner-only permissions.

Store only a safe pointer and required-attestation policy in the repository before the final commit.

Do not modify tracked files after generating the attestation.

Verify:

```text
git status --porcelain
```

is empty.

If the repository cannot be made clean, do not claim completion.

---

# 22. Phase 17 — Required Tests and Gates

Add focused tests covering every known issue.

At minimum:

## Scientific design

- explicit clean/intervention pair schema;
- 20 pairs;
- four families × five;
- eight or more domains;
- difficulty distribution;
- 16 semantic objectives;
- four true anchors;
- family/route deconfounding;
- family/domain balance;
- family/difficulty balance;
- no generic prompt IDs as task objectives.

## Intervention operators

- actual tool removal;
- actual tool failure;
- actual memory corruption;
- actual observation conflict;
- exact structural diffs;
- goal preservation;
- invariance preservation;
- no unintended mutations.

## Evidence and routes

- primitive-only evidence;
- no answer-bearing fields;
- no universal reader oracle;
- manual-reasoning closure;
- completion proof;
- recovery proof;
- clarification proof;
- abstention proof;
- hidden-gold isolation;
- expected-fact injection rejection.

## Reviewer packages

- Stage-1 completeness;
- Stage-1 review form;
- independent order;
- opaque IDs;
- no Stage-2 leakage;
- package path safety;
- correct package hashes;
- retired packets rejected.

## Security

- Stage-2 plaintext absent;
- key outside repository;
- owner-only permissions where testable;
- unlock fails without key;
- private files ignored;
- sanitized source archive excludes private data;
- secret scanner passes.

## Workflow

- qualification gate;
- Stage-1 ingestion;
- Stage-1 commitment;
- Stage-2 lock;
- Stage-2 unlock;
- disagreement queue;
- adjudication;
- C10 fail-closed behavior;
- slice-lock gate;
- execution-authorization gate;
- fixture receipts rejected as genuine.

## Power and claims

- Compact labeled pilot;
- fixed-panel wording;
- rank-instability simulation deterministic;
- small-effect sensitivity;
- interaction designation consistent with power.

## Provenance

- freeze hashes;
- generator commit provenance;
- clean build reproducibility;
- exact external attestation required;
- stale dist artifacts rejected.

---

# 23. Final Validation Sequence

Run the strongest available provider-free validation.

Required sequence:

```text
focused reviewer-ready tests
full provider-free pytest suite
ruff
mypy
codespell
strict documentation checks
schema validation
security scan
secret scan
private-path scan
Stage-1 leakage scan
retired-packet rejection audit
intervention-isolation audit
semantic-diversity audit
route hostile audit
two-stage fixture E2E test
power-plan calibration tests
package build
double-build reproducibility
scientific-freeze verification
exact-attestation verification
Git cleanliness check
```

If the full suite cannot run because declared dependencies are unavailable:

- make a best effort to restore the declared environment;
- do not silently skip;
- report the exact blocker;
- do not claim full completion.

Do not use a timeout-truncated partial suite as proof of full validation.

---

# 24. Required Deliverables

## Tracked code and configuration

Create or adapt:

```text
src/causal_agent_bench/review_ready_v2/
src/causal_agent_bench/interventions/
src/causal_agent_bench/review_workflow/
src/causal_agent_bench/security/
configs/human_review/compact20_review_ready_v2.yaml
scripts/cab_review_ready_v2.py
```

Use the existing architecture instead of duplicating modules when equivalent locations already exist.

## Tracked documentation and safe reports

Required safe artifacts or equivalents:

```text
docs/HUMAN_REVIEW_READY_V2_RUNBOOK.md
docs/STAGE1_REVIEWER_INSTRUCTIONS_V2.md
docs/STAGE2_COORDINATOR_RUNBOOK_V2.md
docs/COMPACT20_V2_SCIENTIFIC_DESIGN.md
docs/PRIVATE_PACKET_SECURITY_POLICY.md
reports/reviewer_ready_v2/BASELINE_AUDIT.json
reports/reviewer_ready_v2/RETIRED_PACKET_REGISTRY.json
reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json
reports/reviewer_ready_v2/PUBLIC_PACKET_COMMITMENT.json
reports/reviewer_ready_v2/STAGE1_PACKAGE_RECEIPT.json
reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json
reports/reviewer_ready_v2/REVIEWER_READINESS_REPORT.json
reports/reviewer_ready_v2/REVIEWER_READINESS_REPORT.md
```

These files must not contain private candidate content.

## Private, ignored artifacts

Expected private artifacts or equivalents:

```text
private_data/human_review/compact20-review-ready-v2/
  coordinator/
  stage1/
    stage1_reviewer_a.zip
    stage1_reviewer_b.zip
  qualification/
  stage2/
    stage2_vault.enc
  mappings/
```

No Stage-2 plaintext may remain after generation.

The key must be outside the repository.

## External artifacts

```text
~/.cab/private_backups/<timestamp>/
~/.cab/attestations/cab-review-ready-v2-<commit>.json
```

---

# 25. Final Reviewer-Ready Report

Write one final concise but complete report.

It must include:

- exact final commit;
- branch;
- clean worktree status;
- private packet version;
- public commitment;
- Stage-1 Reviewer A package path and SHA-256;
- Stage-1 Reviewer B package path and SHA-256;
- qualification package path and hash;
- encrypted Stage-2 vault path and hash;
- confirmation that the key is outside the repository;
- scientific freeze hash;
- semantic diversity counts;
- anchor validation summary;
- family × route matrix;
- domain and difficulty balance;
- intervention-operator validation counts;
- hostile route-test counts;
- Stage-1 leakage audit counts;
- workflow fixture E2E status;
- full provider-free test count;
- lint/type/docs/security/build status;
- exact external attestation path;
- wheel and normalized sdist hashes;
- genuine evidence counters, all zero;
- exact next human action.

Do not include:

- private prompts;
- private answers;
- Stage-2 values;
- private IDs;
- fake reviewer results;
- C10 PASS;
- model-run approval.

The exact next action must be:

```text
Recruit two independent qualified reviewers, give each only their assigned frozen Stage-1 package and qualification materials, keep Stage 2 inaccessible until both qualified Stage-1 submissions are validated and committed, then continue through the canonical two-stage workflow.
```

---

# 26. Final Hard Acceptance Criteria

The task is complete only if all of the following are true.

## Scientific kernel

- [ ] Twenty explicit clean/intervention pairs exist.
- [ ] At least sixteen semantically distinct objectives exist.
- [ ] Four true controlled repeated anchors exist.
- [ ] Family and response type are not deterministically confounded.
- [ ] Every intervention is an actual executable environment mutation.
- [ ] Primitive evidence contains no answer-bearing fields.
- [ ] No undeclared universal artifact oracle is used.
- [ ] Abstention requires genuine route exhaustion.
- [ ] Clarification requires genuine unresolved information.
- [ ] Recovery is temporally and causally bound to the exact authorized action.

## Human-review readiness

- [ ] Reviewer A and B Stage-1 ZIPs are complete and independently randomized.
- [ ] Stage 1 exposes enough information to judge intervention validity.
- [ ] Stage 1 hides all gold, scorer, route and policy information.
- [ ] Structured review forms cover the required C10 Stage-1 dimensions.
- [ ] Qualification materials are separate.
- [ ] Stage-1 leakage audit passes.
- [ ] Stage-2 plaintext is absent.
- [ ] Stage-2 key is external.
- [ ] The full two-stage workflow passes fixture-only E2E validation.
- [ ] C10 remains blocked pending genuine review.
- [ ] Execution remains blocked pending C10 and slice lock.

## Operational integrity

- [ ] All previous packets are retired and rejected by code.
- [ ] Canonical docs and CLI paths point only to V2.
- [ ] Compact is labeled pilot/feasibility, not confirmatory.
- [ ] Rank-instability planning is calibrated.
- [ ] Fixed-panel inference is explicit.
- [ ] Interaction claims match actual power.
- [ ] Scientific freeze V2 validates.
- [ ] Exact external attestation exists.
- [ ] Clean builds are reproducible.
- [ ] The final Git worktree is clean.
- [ ] No private data is committed.
- [ ] No genuine evidence is fabricated.

If any checkbox fails, report:

```text
CAB_REVIEWER_READY_V2_BLOCKED
```

with exact blockers.

Do not claim partial work as full completion.

---

# 27. Stop Condition

After satisfying the acceptance criteria:

1. commit the tracked repairs logically;
2. push to the existing remote branch only if:
   - the branch is correct;
   - the push is fast-forward;
   - authentication is already available;
   - no private files are included;
3. create the external exact-commit attestation;
4. verify the final worktree is clean;
5. print the safe final report;
6. stop.

Do not:

- begin human review;
- unlock Stage 2;
- run C10 with fixtures as genuine data;
- authorize model execution;
- run agents;
- add another maturity level;
- propose another broad engineering pass.

The repository must end at the honest boundary:

```text
CAB_REVIEWER_READY_V2_REPAIR_COMPLETE
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
```
