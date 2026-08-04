# CAB Current Project State

**Authority:** this is the sole current top-level state and next-action guide.
**State:** `CAB_REVIEWER_READY_V2_REPAIR_COMPLETE`
**Review packet:** `compact20-review-ready-v2` (all earlier packets are retired)
**External gates:** `HUMAN_VALIDATION_REQUIRED`, `LIVE_EVIDENCE_REQUIRED`
**Scientific execution during this pass:** none
**Final pre-review baseline SHA:** `715d981cf68eb2741dd6e05b097b08445f87accf`
**Publication SHA:** recorded after the direct-main push in
`reports/pre_run_hardening/CAB_PRE_RUN_GITHUB_PUBLISH.md` and in the release
handoff; a commit cannot truthfully contain its own future hash.

## Canonical review path (reviewer-ready V2)

The repository is engineering-ready for genuine Stage-1 review.
No genuine review has occurred.
Stage 2 remains locked.
C10 has not passed.
Model execution is prohibited.

The active packet is `compact20-review-ready-v2`. Every earlier Compact packet —
including `compact20-final-private-v1` — is retired and rejected **in code** at
ingestion, C10, slice lock and execution authorization, by public-commitment and
package-hash identity rather than by name. Resolve every path from
`reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json`.

```bash
export CAB_STAGE2_KEY_PATH="$HOME/.cab/keys/stage2_review_ready_v2.key"
python3 scripts/cab_review_ready_v2.py validate-private-packet
python3 scripts/cab_review_ready_v2.py validate-stage1-packages
python3 scripts/cab_review_ready_v2.py fixture-e2e
python3 scripts/cab_review_ready_v2.py verify-freeze
```

Canonical documents:
[runbook](docs/HUMAN_REVIEW_READY_V2_RUNBOOK.md) ·
[scientific design](docs/COMPACT20_V2_SCIENTIFIC_DESIGN.md) ·
[reviewer instructions](docs/STAGE1_REVIEWER_INSTRUCTIONS_V2.md) ·
[coordinator runbook](docs/STAGE2_COORDINATOR_RUNBOOK_V2.md) ·
[security policy](docs/PRIVATE_PACKET_SECURITY_POLICY.md).

The V2 kernel is paired: each unit is a clean instance plus an intervention
instance produced by applying exactly one executable operator to it. Intervention
family is no longer confounded with the required response type, anchors are
controlled repetitions rather than flags, abstention requires proved route
exhaustion, and there is no general-purpose artifact reader in the scientific
route.

Compact-20 is a **pilot**: feasibility, protocol validation, scorer-audit basis,
runtime calibration and effect-direction exploration. It is not confirmatory and
is not adequately powered for broad claims. Inference applies to the fixed
evaluated model panel unless a model-superpopulation design is separately
preregistered. Prospective calibration shows the model x family interaction is
underpowered across the whole SESOI grid and is designated
secondary/exploratory, and that the raw rank-reversal probability is dominated
by its own noise floor and is therefore not a usable estimand.

Sections below this point describe earlier passes and are retained as history.

## Platform state

The provider-free benchmark, validation, two-stage review packet, deterministic planning,
Kaggle fixture, packaging, and release surfaces are implemented. Scientific
scoring is frozen at `cab_typed_final_answer` version `3.0.0`. Completion, safe
response, compliance, typed abstention, clarification, refusal, disclosure,
and the four recovery states are separate. Final pre-review gates are:

```bash
cab benchmark static-reachability-check
cab benchmark executable-reachability-check
cab benchmark gold-reconstruction-check
cab benchmark intervention-isolation-check
cab approval verify --fixture
cab power validate
cab final-pre-review check
```

This state is readiness to begin genuine review, not empirical completion.

## Scientific state

- Endpoints are frozen in `configs/pre_run/frozen_endpoints.json`.
- Compact-20 is a regenerated v2 pre-review packet with 20 items, four current
  families × five items, 16 unique base tasks, and four deliberate anchors.
- All 20 Compact interventions have inspectable controlled evidence bundles and
  pass both static policy reachability and executable environment reachability;
  gold reconstructs 20/20 with zero unsupported facts or unexplained changes.
- Human review is immutable and two-stage. Stage 1 excludes gold, intended
  routes, and scorers; Stage 2 remains locked until a completed Stage-1 CSV hash
  is frozen. The canonical packet contains zero human judgments.
- Recovery authorization v4 binds exact post-failure actions, argument schemas,
  success predicates, causal facts, attempt budgets, and costs.
- Scale-100 v2 and transfer v2 use deterministic constrained family rotation;
  all family × difficulty cells are populated and both documented association
  thresholds pass.
- V2 is the sole future scientific execution path. Private candidate → genuine
  two-stage review → adjudication → C10 → content-bound cryptographic receipt →
  bound execution manifest → run → import → audit is mandatory. An
  approved-looking directory or Boolean never authorizes execution.
- Power assumptions are prospective and frozen before outcomes. Models are
  hierarchical factors, not independent task replicates. Compact-20 is a
  validation/pilot tier; Scale-100 is confirmatory only after human gates.
- GPU/resource projections remain `ASSUMPTION_BASED_PRE_SMOKE_PROJECTION`.
  RAAC is staged through Waves A–D; the full 81,000-trajectory design is not the
  immediate default.
- Every scientific run must bind the full evaluated system identity, including
  both model and adapter hashes. Native tool calling is a secondary ablation.
- Transfer is named `artifact_rich_synthetic_transfer`. Its heterogeneous files
  are deterministic synthetic artifacts with parser-derived gold; it makes no
  real-world-origin claim.

## Genuine evidence counters

| Counter | Value |
|---|---:|
| `genuine_human_judgments` | 0 |
| `genuine_adjudications` | 0 |
| `real_model_trajectories` | 0 |
| `audited_real_runs` | 0 |
| `paper_eligible_empirical_assets` | 0 |
| `supported_empirical_claims` | 0 |
| `external_reproductions` | 0 |
| `protected_evaluator_pilots` | 0 |
| `community_pilots` | 0 |

## Canonical study paths

| Surface | Canonical path | Current state |
|---|---|---|
| Compact instances | `data/compact20_reviewed/compact20_v2_instances.jsonl` | public pre-review |
| Compact review evidence | `data/compact20_reviewed/reviewer_evidence/` | 20 inspectable controlled bundles |
| Compact two-stage packet | `data/human_validation/compact20_two_stage_review/` | blank; Stage 2 locked; human input required |
| Compact public commitment | `data/manifests/compact20_two_stage_review_commitment.json` | immutable two-stage hashes |
| Scale design commitment | `data/manifests/scale100_confirmatory_v2_public_manifest.json` | protected candidate; execution forbidden |
| Scale execution template | `configs/iclr/scale100_v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml` | template only |
| Transfer design commitment | `data/manifests/naturalistic_transfer_v2_public_manifest.json` | artifact-rich synthetic; execution forbidden |
| Transfer execution template | `configs/iclr/artifact_rich_transfer_v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml` | template only |
| Resource manifests | `configs/pre_run/study_execution_manifests.json` | frozen design input |
| Power assumptions | `configs/pre_run/power_assumptions.json` | frozen design input |
| System contract | `configs/pre_run/evaluated_system_manifest.json` | model binding pending preflight |

Public Scale and transfer manifests contain commitments and aggregate metadata,
not protected task bodies, gold answers, or intervention payloads.

## Prohibited obsolete commands and paths

Do not execute scientific runs from any v1 Scale, Main-500,
`naturalistic_ministudy`, or unapproved public candidate path. In particular,
the following are historical/fixture-only and fail closed:

- `configs/generate_scale100_confirmatory_v1.yaml`
- `configs/generate_naturalistic_transfer_v1.yaml`
- `configs/generate_main500_confirmatory_v1.yaml`
- `configs/generate_main_v0_1_500.yaml`
- `configs/main_500_multi_provider_TEMPLATE_NOT_APPROVED.yaml`
- `configs/naturalistic_ministudy_TEMPLATE_NOT_APPROVED.yaml`
- `notebooks/kaggle/CAB_T4X2_04_MAIN500_OPEN_MODEL_RUNNER.ipynb`

Do not run models, call providers, approve v2 templates, populate human rows,
or promote claims merely because the static hardening gate passes.

## Superseded guidance

`MASTER_STATUS.md`, `PROJECT_STATUS.md`, and `NEXT_STEPS.md` are retained as
historical generated snapshots and explicitly point here. Older prompt packs,
status reports, Main-500 plans, and v1 execution documents remain historical;
they are not current authorization.

## Exact next action

> Recruit and onboard two genuine qualified independent Compact-20 reviewers
> using the regenerated packet, plus a separate adjudicator.

After independent Stage-1 review, freeze the completed CSV hash and run the
unchanged unlock validator. Then complete Stage 2 and separate adjudication and
run the unchanged C10 validator. Only an authentic passing result plus a trusted
scientific-scope cryptographic receipt permits model execution.

`CAB_LEVEL5_COMPLETE=false`.
