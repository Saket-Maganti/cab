# CAB ICLR Complete Execution and Experiment Handbook

Status: canonical future-run order. Nothing in this file authorises a run.

All runtime, memory, disk, and cost values below are
`ESTIMATE_NOT_MEASURED` until an approved run records measurement. Replace
formulas only with audited measurements. Provider stages are optional; the
paper must remain viable with an open-model core.

## Global stop rules

- Do not cross HUMAN-01 until the unified pre-execution gate reports
  `HUMAN_VALIDATION_REQUIRED`.
- Do not execute a model before human review, adjudication, C10, slice lock,
  CPU preflight, Kaggle offline fixture smoke, and explicit live approval.
- Do not expose or commit private task text, answers, intervention payloads, or
  evaluator metadata.
- Do not use fixture, interrupted, corrupt, or unaudited output for a paper
  claim.
- Stop after each stage if its validator fails. Resume from its checkpoint; do
  not skip forward.

## Run 00 — CPU-PREEXEC-VALIDATE

- Study stage: pre-execution build closeout.
- Purpose: prove code, contamination, state, human, RAAC, notebook, analysis,
  paper, and release gates work without models.
- Evidence role: `ENGINEERING_ONLY`; mandatory.
- Prerequisites: repository checkout at intended commit.
- Task pack: public fixtures and public-safe manifests only.
- Model category / policy / repeats: none / none / 1 validation pass.
- Clean / intervention / trajectories: 0 / 0 / 0.
- Compute class: `CPU_ONLY`; Kaggle suitability: unnecessary; T4×2: unnecessary.
- Estimated VRAM: 0; disk: test caches only; runtime:
  `ESTIMATE_NOT_MEASURED` from the local suite.
- Assumptions / cost: dependencies installed; $0.
- Command: `python3 scripts/check_iclr_preexecution_readiness.py`.
- Outputs: structured readiness JSON/text and validation logs.
- Completion validator: expected state `HUMAN_VALIDATION_REQUIRED`, with no
  unexpected build blocker.
- Failure recovery: run the named failing focused check; preserve logs; repair
  before repeating.
- Paper eligibility: none.

## Run 01 — HUMAN-REVIEW-QUALIFY-AND-DOUBLE-CODE

- Study stage: Compact-20 validation.
- Purpose: qualify reviewers and independently review clarity, clean gold,
  manipulation success, goal/invariance preservation, solvability, answer
  contract, scorer compatibility, realism, ambiguity, and exclusion.
- Evidence role: `HUMAN_INPUT_REQUIRED`; mandatory.
- Prerequisites: Run 00; packet hash frozen; reviewers trained; conflict,
  expertise, consent, privacy, and compensation disclosures complete.
- Task pack: Compact-20 locked candidate packet.
- Model category / policy: no model; two independent genuine human reviewers.
- Repeats: one judgment per reviewer per required dimension.
- Clean / intervention counts: from packet manifest; trajectories: 0.
- Compute class: `HUMAN_ONLY`; Kaggle/T4×2: no.
- Estimated VRAM / disk: 0 / small CSV+audit log.
- Estimated runtime: minutes per item plus training and adjudication reserve,
  all `ESTIMATE_NOT_MEASURED`; estimated cost: compensation plan,
  `ESTIMATE_NOT_MEASURED`.
- Command: follow `docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md`; then
  `python3 scripts/validate_cab_human_reviews.py --review-dir data/human_validation/compact20_real_review`.
- Outputs: genuine signed/attested rows, qualification records, disagreement
  queue; never public reviewer identities.
- Completion validator: full coverage, two distinct reviewer IDs, valid values,
  no proxy/AI attestation, agreement diagnostics available.
- Failure recovery: correct malformed rows through a logged amendment; never
  infer or auto-fill a judgment.
- Paper eligibility: not yet; adjudication/C10 required.

## Run 02 — HUMAN-ADJUDICATION-C10

- Study stage: intervention validity and slice lock preparation.
- Purpose: independently adjudicate disagreements and decide exclusions under
  the canonical C10 contract.
- Evidence role: `HUMAN_INPUT_REQUIRED`; mandatory.
- Prerequisites: Run 01 complete; separate adjudicator assigned.
- Task pack: exact Run 01 packet and disagreement queue.
- Model / policy / repeats: none / adjudication / one final disposition each.
- Clean / intervention counts: unchanged; trajectories: 0.
- Compute class: `HUMAN_ONLY`; Kaggle/T4×2: no.
- Estimated VRAM/disk: 0 / small; runtime and cost:
  `ESTIMATE_NOT_MEASURED`.
- Command: validator command above, followed by the canonical C10/slice-lock
  command printed by the unified gate.
- Outputs: adjudication log, agreement/CI report, exclusion register, C10 state,
  slice hash.
- Completion validator: genuine rows, coverage, threshold, manipulation,
  leakage, answer-contract, adjudication, and slice-hash prerequisites all pass.
- Failure recovery: return only unresolved items to the adjudicator; if C10
  fails, repair/re-review as a new version rather than weakening thresholds.
- Paper eligibility: human-validity evidence only after audit.

## Run 03 — CPU-SLICE-LOCK-AND-PREFLIGHT

- Study stage: pre-pilot freeze.
- Purpose: freeze task, split, scorer, analysis, exclusion, controller, code,
  and environment hashes.
- Evidence role: `ENGINEERING_ONLY`; mandatory.
- Prerequisites: Run 02 C10 pass.
- Task pack: adjudicated Compact-20 slice; no contaminated IDs.
- Model / policy / repeats: none.
- Clean / intervention / trajectories: manifest counts / 0 trajectories.
- Compute class: `CPU_ONLY`; Kaggle/T4×2: compatible but unnecessary.
- Estimated VRAM: 0; disk/runtime: `ESTIMATE_NOT_MEASURED`; cost: $0.
- Command: use the exact future lock command emitted by the C10 gate, then Run
  00 and `PYTHONPATH=src python3 scripts/cab_resource_preflight.py`.
- Outputs: immutable split/run manifests, hash receipt, disk/runtime plan.
- Completion validator: hashes recompute exactly; live execution remains false.
- Failure recovery: do not edit the locked slice in place; create a new version.
- Paper eligibility: none.

## Run 04 — KAGGLE-OFFLINE-FIXTURE

- Study stage: engineering smoke.
- Purpose: validate environment, dual-worker sharding, checkpoint/resume, merge,
  archive, and corruption detection without loading a model.
- Evidence role: `FIXTURE_ONLY`; mandatory.
- Prerequisites: Run 03; notebook sources match generator.
- Task pack: deterministic fixture receipts only.
- Model category / policy / repeats: no model / fixture / one full resume cycle.
- Clean / intervention / trajectories: 0 scientific; fixture receipts only.
- Compute class: `CPU_ONLY` or Kaggle CPU; Kaggle suitable: yes; T4×2: detected
  but unused.
- Estimated VRAM: 0; disk/runtime: `ESTIMATE_NOT_MEASURED`; cost: $0.
- Notebook/command:
  `CAB_T4X2_00_ENVIRONMENT_PREFLIGHT.ipynb`,
  `CAB_T4X2_01_OFFLINE_FIXTURE_SMOKE.ipynb`, and
  `python3 scripts/validate_kaggle_notebooks.py --execute-offline`.
- Outputs: fixture ledgers/checkpoints/merge/integrity receipts.
- Completion validator: nine notebooks validate; receipts are disjoint,
  complete, resumable, and `FIXTURE_ONLY`.
- Failure recovery: export current fixture workspace; repair generator/source;
  restart only corrupt shard.
- Paper eligibility: none.

## Run 05 — TIER0-ONE-TASK-LIVE-SMOKE

- Study stage: approved live preflight.
- Purpose: measure one pinned open model’s adapter, memory, latency, output,
  scorer, and export path.
- Evidence role: `PRELIMINARY_REAL_EVIDENCE`; mandatory before Compact-20.
- Prerequisites: Runs 00–04, explicit human live approval, model licence and
  revision verified.
- Task pack: one locked non-sensitive smoke task selected before output.
- Model category / policy: smaller efficient open / standard tool use.
- Repeats: 1.
- Clean / intervention: one preregistered smoke unit; trajectories: formula from
  locked manifest.
- Compute class: `GPU_SINGLE`; Kaggle suitable: yes; T4×2 compatible: run only
  one worker.
- Estimated VRAM/disk/runtime/cost: `ESTIMATE_NOT_MEASURED`; provider cost: $0.
- Notebook: environment preflight then the Compact-20 runner with a one-item
  manifest and explicit approval.
- Outputs: one preliminary trajectory, measured preflight, integrity receipt.
- Completion validator: pinned hashes, no duplicate, valid scorer, checkpoint,
  and archive.
- Failure recovery: use OOM order in `docs/KAGGLE_T4X2_OPERATIONS.md`; a changed
  model/quantisation creates a new manifest.
- Paper eligibility: no; smoke only.

## Run 06 — TIER1-COMPACT20

- Study stage: audited pilot.
- Purpose: test feasibility, scorer sanity, initial paired signal, and
  `RAAC_LIGHT` mechanics.
- Evidence role: `PRELIMINARY_REAL_EVIDENCE`; mandatory.
- Prerequisites: Run 05 pass and measured resource plan.
- Task pack: locked Compact-20.
- Model category: 3–4 models, open-model core; policies: standard +
  `RAAC_LIGHT`, optional preregistered `RAAC_FULL` subset.
- Repeats: limited and fixed before execution.
- Clean/intervention counts: locked manifest; trajectories:
  `(clean + intervention) × models × policies × repeats`.
- Compute class: `GPU_T4X2_DATA_PARALLEL`; Kaggle suitable: yes; T4×2: two
  deterministic independent shards.
- Estimated VRAM/disk/runtime/cost: `ESTIMATE_NOT_MEASURED`, with measured Tier
  0 assumptions; provider cost $0 for core.
- Notebook: `CAB_T4X2_02_COMPACT20_OPEN_MODEL_RUNNER.ipynb`.
- Outputs: per-GPU ledgers/checkpoints, chunks, merged trajectories, scores,
  overhead traces, session/integrity manifests.
- Completion validator: complete/disjoint merge, hashes and scorer pinned, all
  policies within budgets, evidence remains preliminary until audit.
- Failure recovery: resume completed IDs; rerun only failed/corrupt shards; no
  silent model substitution.
- Paper eligibility: not until Run 07 audit; pilot wording only.

## Run 07 — SCORER-SANITY-AND-TRAJECTORY-AUDIT

- Study stage: Compact-20 postrun audit.
- Purpose: blind-check scorer error, trace integrity, hidden-label blindness,
  false abstention, and run completeness.
- Evidence role: `HYBRID` human + CPU; mandatory.
- Prerequisites: Run 06 complete.
- Task pack/model/policy/repeats: exact Run 06 frozen support.
- Clean/intervention/trajectories: audit sample and full integrity inventory
  defined before viewing model identity.
- Compute class: `HYBRID`; Kaggle/T4×2: no.
- Estimated VRAM: 0; disk/runtime/cost: `ESTIMATE_NOT_MEASURED`.
- Command: scorer-sanity and run-audit commands from the unified gate; human
  reviewers remain model/blinded where specified.
- Outputs: scorer FP/FN estimates, audit decisions, eligible/excluded trajectory
  register, preliminary paired report.
- Completion validator: scorer thresholds, no hidden metadata access, complete
  audit and immutable evidence hashes.
- Failure recovery: repair scorer only through a versioned rescoring plan;
  preserve raw trajectories; rerun affected analyses.
- Paper eligibility: Compact-20 evidence may become audited preliminary, not
  automatically confirmatory.

## Run 08 — TIER2-SCALE100

- Study stage: confirmatory controlled evaluation.
- Purpose: estimate primary paired endpoints and RAAC effect with adequate
  diversity/uncertainty.
- Evidence role: `AUDITED_REAL_EVIDENCE` after audit; mandatory only if the
  prospective design passes.
- Prerequisites: Run 07; Scale-100 v2 genuine review/C10/slice lock; power and
  allocation frozen.
- Task pack: approximately 100 genuinely distinct private protected base tasks;
  exact counts from locked manifest.
- Model category: 5–7 if feasible, open-model core; policies: standard + locked
  RAAC policy; repeats: power-aware and fixed.
- Clean/intervention counts: locked allocation; trajectories: product formula.
- Compute class: `GPU_T4X2_DATA_PARALLEL`; Kaggle suitable: yes.
- Estimated VRAM/disk/runtime/cost: `ESTIMATE_NOT_MEASURED`, updated from Runs
  05–06 measurements.
- Notebook: `CAB_T4X2_03_SCALE100_OPEN_MODEL_RUNNER.ipynb`.
- Outputs: resumable shards, manifests, raw trajectories, scores, audit pack.
- Completion validator: task/scorer/code/model/policy hashes, complete common
  support, integrity, missingness, and audit gates.
- Failure recovery: resume by deterministic shard; never replace failed tasks
  based on model output.
- Paper eligibility: only after postrun audit and claim promotion.

## Run 09 — RAAC-ABLATIONS

- Study stage: mechanism analysis.
- Purpose: compare `RAAC_FULL`, `VERIFY_ONLY`, `RETRY_ONLY`, `ABSTAIN_ONLY`,
  `NO_CROSS_CHECK`, `NO_ALTERNATE_ROUTE`, and `NO_FINAL_VERIFY`.
- Evidence role: `AUDITED_REAL_EVIDENCE`; selected ablations mandatory for the
  RAAC mechanism claim, remainder optional.
- Prerequisites: Run 08 integrity; ablations and family/model subset frozen
  before outcomes.
- Task pack: exact common locked Scale-100 subset.
- Model category: informative open-model subset; policies above; repeats:
  power-aware.
- Clean/intervention counts: locked subset; trajectories: product formula.
- Compute class: `GPU_T4X2_DATA_PARALLEL`; Kaggle suitable/T4×2: yes.
- Estimated VRAM/disk/runtime/cost: `ESTIMATE_NOT_MEASURED`.
- Notebook: `CAB_T4X2_05_BASELINES_AND_ABLATIONS.ipynb`.
- Outputs: policy traces, budget-parity report, effect/overhead table, audit
  bundle.
- Completion validator: common support, equal-budget primary comparison,
  practical-budget separation, multiplicity plan, no hidden labels.
- Failure recovery: resume by policy/shard; do not drop a weak policy arm.
- Paper eligibility: after audit and evidence promotion.

## Run 10 — TIER3-NATURALISTIC-TRANSFER

- Study stage: external/predictive validity.
- Purpose: test whether controlled robustness predicts failures on realistic
  local workflows beyond clean success.
- Evidence role: `AUDITED_REAL_EVIDENCE`; mandatory for the transfer claim.
- Prerequisites: reviewed/C10-locked transfer set; provenance, licence, privacy,
  PII, injection, leakage, and answer-contract gates; Run 08.
- Task pack: 50–100 high-quality naturalistic private tasks; exact locked count.
- Model category: most informative open-model subset; policies: standard +
  selected RAAC; repeats: fixed prospectively.
- Clean/intervention counts and trajectories: locked manifest/product formula.
- Compute class: `GPU_T4X2_DATA_PARALLEL`; Kaggle suitable/T4×2: yes.
- Estimated VRAM/disk/runtime/cost: `ESTIMATE_NOT_MEASURED`.
- Notebook: `CAB_T4X2_08_NATURALISTIC_TRANSFER_RUNNER.ipynb`.
- Outputs: audited outcomes, transfer correlations/regression/calibration,
  leave-family-out report, privacy-safe failure examples.
- Completion validator: integrity plus naturalistic registry gates and
  confirmatory analysis plan.
- Failure recovery: preserve artifacts; fix source/privacy issues through a new
  task version, not post-outcome replacement.
- Paper eligibility: after audit and claim promotion.

## Run 11 — OPTIONAL-PROVIDER-PANEL

- Study stage: optional model-family triangulation.
- Purpose: test whether open-core conclusions generalise to one or two
  proprietary categories.
- Evidence role: optional `PRELIMINARY_REAL_EVIDENCE` then audited.
- Prerequisites: explicit paid/API authority and budget, frozen support, open
  core complete.
- Task pack: preregistered Compact/Scale/transfer subset.
- Model category: optional strong proprietary and optional second provider;
  policy/repeats fixed before calls.
- Clean/intervention/trajectories: locked formula.
- Compute class: `PROVIDER_API`; Kaggle/T4×2: unnecessary.
- Estimated VRAM: provider-managed; disk/runtime/cost:
  `ESTIMATE_NOT_MEASURED`, hard capped before approval.
- Command: approved provider config only; default remains paid calls false.
- Outputs: pinned provider/model records, metering, trajectories, audit bundle.
- Completion validator: cost/call caps, version identity, common support,
  evidence audit.
- Failure recovery: bounded retry; never silently fall back to another model.
- Paper eligibility: optional after audit; paper cannot depend on it.

## Run 12 — MAIN-SCOPE-DECISION

- Study stage: conditional expansion decision.
- Purpose: choose Scale-only, Scale+transfer, 150–250, or Main-500.
- Evidence role: `HYBRID` design/human; mandatory decision, expansion optional.
- Prerequisites: Runs 08 and 10 audited.
- Task/model/policy/repeats/counts: none; review audited evidence and prospective
  power only.
- Compute class: `CPU_ONLY` + human decision; Kaggle/T4×2: no.
- Estimated VRAM/cost: 0; disk/runtime: `ESTIMATE_NOT_MEASURED`.
- Command: apply `docs/MAIN_SET_RESOURCE_AWARE_DECISION_POLICY.md`.
- Outputs: signed decision record with diversity, power, human, measured runtime
  and storage assumptions.
- Completion validator: every expansion prerequisite explicitly passed.
- Failure recovery: default to the smaller scope.
- Paper eligibility: decision/protocol only.

## Run 13 — OPTIONAL-MAIN-EXPANSION

- Study stage: Tier 4, only if Run 12 justifies it.
- Purpose: reduce uncertainty or expand diversity for a named unresolved RQ.
- Evidence role: optional audited evidence.
- Prerequisites: Run 12 expansion pass; new tasks independently reviewed,
  adjudicated, C10-passed, locked, and non-contaminated.
- Task pack: chosen 150–250 or Main-500 version; exact locked counts.
- Model/policy/repeats: preregistered informative subset.
- Clean/intervention/trajectories: locked manifest/product formula.
- Compute class: `GPU_T4X2_DATA_PARALLEL` or
  `GPU_T4X2_OPTIONAL_MODEL_PARALLEL` after measured preflight.
- Kaggle suitable: only if session/export plan passes; T4×2: required.
- Estimated VRAM/disk/runtime/cost: `ESTIMATE_NOT_MEASURED`.
- Notebook: `CAB_T4X2_04_MAIN500_OPEN_MODEL_RUNNER.ipynb` with scope-specific
  manifest.
- Outputs/validator/recovery: same integrity, resume, audit, and no-replacement
  rules as Scale-100.
- Paper eligibility: after audit; never implied merely by size.

## Run 14 — FINAL-ANALYSIS

- Study stage: postrun inference.
- Purpose: execute the frozen confirmatory, secondary, exploratory, RAAC,
  scorer, missingness, and transfer analyses.
- Evidence role: `AUDITED_REAL_EVIDENCE`; mandatory.
- Prerequisites: every included study audited and immutable.
- Task/model/policy/repeats/counts: inherit included manifests; no new runs.
- Compute class: `CPU_ONLY`, low-memory streaming; Kaggle/T4×2: no.
- Estimated VRAM: 0; disk/runtime: `ESTIMATE_NOT_MEASURED`; cost: $0.
- Command: merge/audit/rescore notebook for integrity, then the frozen analysis
  commands and 10,000-replicate resumable bootstrap.
- Outputs: statistics, CIs, rank matrix, RAAC trade-off, transfer, sensitivity,
  provenance receipts.
- Completion validator: no missing shards, undefined cases labelled, hashes and
  code revision embedded.
- Failure recovery: resume bootstrap shards; rerun analysis from raw immutable
  evidence; never alter raw data.
- Paper eligibility: analysis outputs remain ineligible until Run 15 gate.

## Run 15 — PAPER-ASSETS-AND-CLAIM-PROMOTION

- Study stage: evidence-to-paper transfer.
- Purpose: generate tables, figures, failure gallery, and safe claim wording.
- Evidence role: `PAPER_ELIGIBLE_EVIDENCE`; mandatory.
- Prerequisites: Run 14 plus claim-specific thresholds and robustness checks.
- Counts/compute: no trajectories; `CPU_ONLY`; low-memory; $0.
- Estimated disk/runtime: `ESTIMATE_NOT_MEASURED`.
- Command: strict Phase-15 paper asset exporter and claim-ledger validator.
- Outputs: clean-vs-robust ranks, rank probabilities, transitions, family
  heatmap, RAAC effect/overhead, transfer, scorer sanity, validity, failure
  gallery, measured cost/runtime, metadata sidecars.
- Completion validator: every asset embeds study ID, data hash, scorer version,
  code revision, command, and `PAPER_ELIGIBLE_EVIDENCE`; placeholders remain
  for unsupported claims.
- Failure recovery: repair evidence linkage or wording; never bypass the gate.
- Paper eligibility: yes only for assets that pass individually.

## Run 16 — RELEASE

- Study stage: reproducibility/release.
- Purpose: publish the leakage-safe code, public metadata, manifests, paper, and
  eligible evidence without private payloads or secrets.
- Evidence role: engineering/release; mandatory.
- Prerequisites: paper and release checks, independent inventory review.
- Counts/compute: no trajectories; `CPU_ONLY`; $0.
- Estimated disk/runtime: `ESTIMATE_NOT_MEASURED`.
- Command: security scan, protected-payload scan, release validation,
  large-file inspection, `git diff --check`, provider-free suite, then the
  intentional Git publication workflow.
- Outputs: public bundle, hashes, reproduction commands, release report.
- Completion validator: no secrets/private answers/reviewer identities/caches,
  bundle hash matches, clean-environment reproduction, remote commit verified.
- Failure recovery: remove only unintended release entries while preserving raw
  private evidence outside Git; rebuild and revalidate.
- Paper eligibility: release does not create evidence; it preserves audited
  provenance.

## Immediate next action

Run 01 only: have two independent genuine human reviewers complete the locked
Compact-20 packets. Do not execute a model.
