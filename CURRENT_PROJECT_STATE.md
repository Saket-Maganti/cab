# CAB Current Project State

**Authority:** this is the sole current top-level state and next-action guide.
**State:** `CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE`
**External gates:** `HUMAN_VALIDATION_REQUIRED`, `LIVE_EVIDENCE_REQUIRED`
**Scientific execution during this pass:** none
**Hardening baseline SHA:** `c8b0d008a02f4bcc36a24635a1357d4210e073fd`
**Publication SHA:** recorded after the direct-main push in
`reports/pre_run_hardening/CAB_PRE_RUN_GITHUB_PUBLISH.md` and in the release
handoff; a commit cannot truthfully contain its own future hash.

## Platform state

The provider-free benchmark, validation, review-packet, deterministic planning,
Kaggle fixture, packaging, and release surfaces are implemented. Scientific
scoring is frozen at `cab_typed_final_answer` version `3.0.0`. Completion, safe
response, compliance, typed abstention, clarification, refusal, disclosure,
and the four recovery states are separate. The one-command static gate is:

```bash
cab pre-run scientific-check
```

This state is readiness to begin genuine review, not empirical completion.

## Scientific state

- Endpoints are frozen in `configs/pre_run/frozen_endpoints.json`.
- Compact-20 is a regenerated v2 pre-review packet with 20 items, four current
  families × five items, 16 unique base tasks, and four deliberate anchors.
- All 20 Compact interventions pass deterministic evidence-route reachability.
- Scale-100 v2 and transfer v2 use deterministic constrained family rotation;
  all family × difficulty cells are populated and both documented association
  thresholds pass.
- V2 is the sole future scientific execution path. Private candidate → genuine
  review → adjudication → C10 → approved materialization → public commitment →
  bound execution manifest → run → import → audit is mandatory.
- Power assumptions are prospective and frozen before outcomes. Compact-20 is
  a validation/pilot tier; Scale-100 is the confirmatory tier after human gates.
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
| Compact review packet | `data/human_validation/compact20_real_review/` | blank; human input required |
| Compact public commitment | `data/manifests/compact20_review_packet_v2_public_commitment.json` | frozen v2 hashes |
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

After independent review and adjudication, run the unchanged C10 validator.
Only an authentic passing result permits creation of an approved v2
materialization; model execution remains a later, separately authorized step.
