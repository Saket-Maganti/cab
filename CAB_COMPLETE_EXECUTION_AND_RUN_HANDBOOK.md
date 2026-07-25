# CAB Complete Execution and Run Handbook

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

This is the only canonical post-build runbook. Follow it top to bottom. Live/model/provider commands remain forbidden until their listed gates pass.

Every runtime and monetary figure below is a planning range or formula labeled `ESTIMATE_NOT_MEASURED`; no T4, model, API, or human duration was measured by this build.

## Mandatory order

A (CPU) → B (human review/C10/slice lock) → C (engineering smoke) → explicit approval → D (Compact-20) → audit/scorer sanity → E (Scale-100 decision/run) → F/G as preregistered → H only if justified → I.

## Runtime methodology

`runtime = load_time + trajectories × (prompt_tokens + output_tokens) / effective_tokens_per_second + tool_latency + checkpoint_overhead + retries`.

Use low/base/high inputs for model size, quantization, prompt/output length, tool calls, tasks, repetitions, two-worker sharding, load time, checkpoint frequency, and retry rate. Replace estimates only with immutable manifest-linked measurements.

## Compute labels

`CPU_ONLY`, `GPU_SINGLE`, `GPU_T4X2_DATA_PARALLEL`, `GPU_T4X2_OPTIONAL_TENSOR_PARALLEL`, `PROVIDER_API`, `HUMAN_ONLY`, `HYBRID`.

## Category A — CPU pre-execution validation

### A1_FAST_STATIC

- **Run ID:** A1_FAST_STATIC
- **Study stage:** pre-execution
- **Purpose:** Imports, schema/scorer/metric/leakage/claim/config fast checks.
- **Evidence role:** engineering gate
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** repository checkout; dev dependencies
- **Task pack:** all static code/configs; no scientific pack execution
- **Models or category:** none
- **Repetitions:** 1
- **Clean/intervention counts:** 0 / 0
- **Expected trajectories:** 0
- **Compute class:** CPU_ONLY
- **CPU/GPU/API:** CPU
- **Kaggle suitability:** no
- **T4×2 compatibility:** not applicable
- **Expected VRAM:** not applicable
- **Expected disk:** <1 GiB generated output
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: 1–10 minutes
- **Estimation assumptions:** serial Python; no network/model
- **Expected monetary cost:** USD 0; ESTIMATE_NOT_MEASURED
- **Command or notebook:** PYTHONPATH=src:. python3 scripts/run_cab_max_ceiling_validation.py --lane fast
- **Outputs:** reports/CAB_VALIDATION_LEDGER.json
- **Completion validator:** ledger required build failures empty
- **Failure recovery:** fix first failing check; rerun serially
- **Paper eligibility:** no; engineering only

### A2_FULL_SAFE_AUDIT

- **Run ID:** A2_FULL_SAFE_AUDIT
- **Study stage:** pre-execution
- **Purpose:** Full provider-free tests, task lint, scorer/metric properties, release and paper checks.
- **Evidence role:** engineering gate
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** A1 passes
- **Task pack:** all repository-controlled fixtures
- **Models or category:** none
- **Repetitions:** 1
- **Clean/intervention counts:** 0 / 0
- **Expected trajectories:** 0
- **Compute class:** CPU_ONLY
- **CPU/GPU/API:** CPU
- **Kaggle suitability:** no
- **T4×2 compatibility:** not applicable
- **Expected VRAM:** not applicable
- **Expected disk:** <5 GiB including test caches
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: 10–60 minutes
- **Estimation assumptions:** suite size, CPU, filesystem, LaTeX availability
- **Expected monetary cost:** USD 0; ESTIMATE_NOT_MEASURED
- **Command or notebook:** PYTHONPATH=src:. python3 scripts/run_cab_max_ceiling_validation.py --lane all
- **Outputs:** validation ledger, audit reports, paper draft PDF if TeX exists
- **Completion validator:** build_validation_passed=true
- **Failure recovery:** preserve logs; rerun failing ID with --only
- **Paper eligibility:** no; engineering only

### A3_HUMAN_C10_SLICE_GATE

- **Run ID:** A3_HUMAN_C10_SLICE_GATE
- **Study stage:** pre-execution
- **Purpose:** Validate review rows, agreement, adjudication, C10, split hash, and slice lock.
- **Evidence role:** execution prerequisite
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** human Category B completed
- **Task pack:** Compact-20 candidate manifest and review CSVs
- **Models or category:** none
- **Repetitions:** 1
- **Clean/intervention counts:** 0 / 0
- **Expected trajectories:** 0
- **Compute class:** CPU_ONLY
- **CPU/GPU/API:** CPU
- **Kaggle suitability:** no
- **T4×2 compatibility:** not applicable
- **Expected VRAM:** not applicable
- **Expected disk:** <1 GiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: under 5 minutes
- **Estimation assumptions:** 20 candidates × 3 review files
- **Expected monetary cost:** USD 0; ESTIMATE_NOT_MEASURED
- **Command or notebook:** python3 scripts/validate_cab_human_reviews.py --review-dir data/human_validation/compact20_real_review
- **Outputs:** reports/CAB_HUMAN_REVIEW_AND_C10_GATE.json
- **Completion validator:** human complete; C10 PASS; slice_lock_allowed=true
- **Failure recovery:** return disagreements to independent adjudicator; never synthesize rows
- **Paper eligibility:** human-validity evidence only; not model evidence


## Category B — Human validation

### B1_DUAL_VALIDITY_REVIEW

- **Run ID:** B1_DUAL_VALIDITY_REVIEW
- **Study stage:** human validation
- **Purpose:** Two blind independent reviews of task clarity, gold correctness, goal preservation, isolation, solvability, ambiguity, and realism.
- **Evidence role:** human validity
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** A1/A2 pass; reviewer independence arranged
- **Task pack:** 20 Compact-20 candidates
- **Models or category:** two human reviewers; no model outputs
- **Repetitions:** 1 review per reviewer per required form
- **Clean/intervention counts:** 20 task/gold groups / 20 intervention groups
- **Expected trajectories:** 120 required reviewer-form rows
- **Compute class:** HUMAN_ONLY
- **CPU/GPU/API:** human
- **Kaggle suitability:** no
- **T4×2 compatibility:** not applicable
- **Expected VRAM:** not applicable
- **Expected disk:** <100 MiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: 4–12 human-hours total
- **Estimation assumptions:** 40–120 seconds per judgment plus notes
- **Expected monetary cost:** human time only; ESTIMATE_NOT_MEASURED
- **Command or notebook:** Complete CSVs under data/human_validation/compact20_real_review/ according to reviewer_instructions.md
- **Outputs:** three completed review CSVs
- **Completion validator:** A3 validator reports complete coverage and two reviewers
- **Failure recovery:** pause on ambiguity; do not reveal model identity/results
- **Paper eligibility:** supports validity/C10 only after audit

### B2_ADJUDICATION_C10_LOCK

- **Run ID:** B2_ADJUDICATION_C10_LOCK
- **Study stage:** human validation
- **Purpose:** Adjudicate disagreements, compute preregistered agreement/C10, and lock passing slice.
- **Evidence role:** human audit
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** B1 complete; independent adjudicator
- **Task pack:** review packets and candidate manifest
- **Models or category:** human adjudicator
- **Repetitions:** 1
- **Clean/intervention counts:** 0 / up to 20 disputed interventions
- **Expected trajectories:** one adjudication per disagreement
- **Compute class:** HUMAN_ONLY
- **CPU/GPU/API:** human
- **Kaggle suitability:** no
- **T4×2 compatibility:** not applicable
- **Expected VRAM:** not applicable
- **Expected disk:** <100 MiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: 1–6 human-hours
- **Estimation assumptions:** depends on disagreement count
- **Expected monetary cost:** human time only; ESTIMATE_NOT_MEASURED
- **Command or notebook:** Complete adjudication_template.csv, then run python3 scripts/validate_cab_human_reviews.py
- **Outputs:** adjudication CSV, C10 report, frozen slice/hash
- **Completion validator:** C10 PASS and slice_lock_allowed=true
- **Failure recovery:** if C10 fails, revise before outcomes and version the pack; never lower threshold post hoc
- **Paper eligibility:** validity evidence; model paper eligibility still no

### B3_SCORER_TRAJECTORY_REVIEW

- **Run ID:** B3_SCORER_TRAJECTORY_REVIEW
- **Study stage:** postrun human validation
- **Purpose:** Blinded scorer sanity and trajectory error review by model/family/condition/auto-score.
- **Evidence role:** scorer audit
- **Mandatory or optional:** mandatory after D; repeat after E/H
- **Prerequisite gates:** auditable real trajectories exist; sample frozen before review
- **Task pack:** stratified immutable trajectory sample
- **Models or category:** two reviewers plus adjudicator
- **Repetitions:** 1 sample round per study
- **Clean/intervention counts:** preregistered sample / same
- **Expected trajectories:** sample size fixed in study manifest
- **Compute class:** HUMAN_ONLY
- **CPU/GPU/API:** human
- **Kaggle suitability:** no
- **T4×2 compatibility:** not applicable
- **Expected VRAM:** not applicable
- **Expected disk:** <1 GiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: sample_size × 3–10 minutes
- **Estimation assumptions:** trajectory length and disagreement rate
- **Expected monetary cost:** human time only; ESTIMATE_NOT_MEASURED
- **Command or notebook:** Use scorer-sanity packet generated only from the audited run manifest
- **Outputs:** human correctness, FP/FN, disagreement, adjudication tables
- **Completion validator:** thresholds pass and audit signs eligibility
- **Failure recovery:** freeze auto-scores/raw trajectories; rescore without editing originals
- **Paper eligibility:** yes only after audited threshold pass


## Category C — Engineering smoke

### C1_FAKE_ADAPTER_SMOKE

- **Run ID:** C1_FAKE_ADAPTER_SMOKE
- **Study stage:** engineering smoke
- **Purpose:** Exercise agent/tool/output/error wiring without provider or model behavior.
- **Evidence role:** fixture mechanics
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** A passes
- **Task pack:** dev_fixture
- **Models or category:** fake/stub adapter
- **Repetitions:** 1
- **Clean/intervention counts:** fixture-defined
- **Expected trajectories:** fixture-defined only
- **Compute class:** CPU_ONLY
- **CPU/GPU/API:** CPU
- **Kaggle suitability:** yes, but unnecessary
- **T4×2 compatibility:** compatible
- **Expected VRAM:** not applicable
- **Expected disk:** <1 GiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: under 10 minutes
- **Estimation assumptions:** fixture task count
- **Expected monetary cost:** USD 0; ESTIMATE_NOT_MEASURED
- **Command or notebook:** python3 -m pytest -q -n0 tests/test_experiment_runner.py tests/test_batch_runner.py
- **Outputs:** temporary fixture artifacts only
- **Completion validator:** pytest passes; no result-shaped scientific artifact
- **Failure recovery:** delete only temporary test output; preserve failure log
- **Paper eligibility:** no; FIXTURE_ONLY

### C2_T4X2_SHARD_RESUME_MERGE

- **Run ID:** C2_T4X2_SHARD_RESUME_MERGE
- **Study stage:** engineering smoke
- **Purpose:** Prove two-worker sharding, checkpoint/resume, merge, corruption detection, and notebook safety.
- **Evidence role:** fixture mechanics
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** A passes; Kaggle environment for optional hardware smoke
- **Task pack:** 8 fixture work items per notebook
- **Models or category:** no model
- **Repetitions:** 1
- **Clean/intervention counts:** 0 / 0
- **Expected trajectories:** 72 receipts across 9 notebooks
- **Compute class:** GPU_T4X2_DATA_PARALLEL
- **CPU/GPU/API:** CPU fixture; optional T4×2 environment detection
- **Kaggle suitability:** yes
- **T4×2 compatibility:** compatible; no model loaded
- **Expected VRAM:** 0 GiB model VRAM in fixture mode
- **Expected disk:** <2 GiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: 2–15 minutes
- **Estimation assumptions:** 9 notebooks × 8 receipts; two shards
- **Expected monetary cost:** USD 0; ESTIMATE_NOT_MEASURED
- **Command or notebook:** python3 scripts/validate_kaggle_notebooks.py --execute-offline
- **Outputs:** temporary shard/checkpoint/merge/integrity receipts
- **Completion validator:** 9/9 notebooks; 72 receipts; scientific_execution_performed=false
- **Failure recovery:** resume from per-worker ledger; corruption must fail merge
- **Paper eligibility:** no; FIXTURE_ONLY


## Category D — Compact-20 pilot

### D1_COMPACT20_OPEN_MODEL

- **Run ID:** D1_COMPACT20_OPEN_MODEL
- **Study stage:** pilot
- **Purpose:** Open-model feasibility, scorer sanity, cost/runtime pilot, paired preliminary analysis.
- **Evidence role:** preliminary real evidence
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** A–C pass; C10/slice lock; explicit live approval; pinned model snapshot
- **Task pack:** compact20_pilot
- **Models or category:** preregistered open-model panel
- **Repetitions:** preregistered, recommended ≥3
- **Clean/intervention counts:** 10 unique clean / 20 intervention
- **Expected trajectories:** 30 × models × repeats
- **Compute class:** GPU_T4X2_DATA_PARALLEL
- **CPU/GPU/API:** two T4s; independent model workers
- **Kaggle suitability:** yes
- **T4×2 compatibility:** compatible subject to preflight
- **Expected VRAM:** ESTIMATE_NOT_MEASURED: model-dependent; target ≤14 GiB/GPU fp16 or 4-bit
- **Expected disk:** ESTIMATE_NOT_MEASURED: 10–30 GiB model/cache/output
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: formula; low/base/high required in approved manifest
- **Estimation assumptions:** model size, tokens, tools, repeats, two shards, retry rate
- **Expected monetary cost:** USD 0 Kaggle compute assumption; ESTIMATE_NOT_MEASURED
- **Command or notebook:** notebooks/kaggle/CAB_T4X2_02_COMPACT20_OPEN_MODEL_RUNNER.ipynb
- **Outputs:** manifest, shard ledgers, raw trajectories, scores, audit bundle
- **Completion validator:** merge complete; hashes match; postrun audit; B3 scorer sanity
- **Failure recovery:** resume deterministic shards; classify OOM/timeout as infrastructure
- **Paper eligibility:** preliminary only until audit; not automatically paper eligible

### D2_COMPACT20_PROVIDER

- **Run ID:** D2_COMPACT20_PROVIDER
- **Study stage:** pilot
- **Purpose:** Equivalent provider lane for the frozen Compact-20 design.
- **Evidence role:** preliminary real evidence
- **Mandatory or optional:** optional model-panel component
- **Prerequisite gates:** D1 gates plus separate provider/budget approval and credential preflight
- **Task pack:** compact20_pilot
- **Models or category:** preregistered provider models
- **Repetitions:** same repeat policy as D1
- **Clean/intervention counts:** 10 unique clean / 20 intervention
- **Expected trajectories:** 30 × provider models × repeats
- **Compute class:** PROVIDER_API
- **CPU/GPU/API:** API
- **Kaggle suitability:** no
- **T4×2 compatibility:** not applicable
- **Expected VRAM:** not applicable
- **Expected disk:** <5 GiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: requests × latency with retry cap
- **Estimation assumptions:** tokens, price snapshot, tool calls, timeout/retry
- **Expected monetary cost:** ESTIMATE_NOT_MEASURED: input_tokens×price + output_tokens×price; hard cap required
- **Command or notebook:** Use only an approved manifest/config listed by the entry gate; no command is authorized yet
- **Outputs:** same canonical manifest/trajectory/score/audit contract
- **Completion validator:** budget, completeness, merge, scorer sanity, postrun audit
- **Failure recovery:** checkpoint; stop at cap; never asymmetric retry
- **Paper eligibility:** preliminary until audit


## Category E — Scale-100 confirmatory study

### E1_SCALE100_CONFIRMATORY

- **Run ID:** E1_SCALE100_CONFIRMATORY
- **Study stage:** confirmatory
- **Purpose:** Multi-model paired confirmatory study with rank uncertainty and trajectory sampling.
- **Evidence role:** candidate paper evidence
- **Mandatory or optional:** mandatory for primary empirical thesis
- **Prerequisite gates:** audited D; preregistered go decision; Scale-specific review/freeze/approval
- **Task pack:** scale100_confirmatory
- **Models or category:** fixed open + provider panel
- **Repetitions:** preregistered ≥3
- **Clean/intervention counts:** 100 clean / 500 intervention
- **Expected trajectories:** 600 × models × repeats
- **Compute class:** HYBRID
- **CPU/GPU/API:** T4×2 open-model shards plus separately approved APIs
- **Kaggle suitability:** yes for open models
- **T4×2 compatibility:** compatible via notebook 03
- **Expected VRAM:** ESTIMATE_NOT_MEASURED: per approved model/preflight
- **Expected disk:** ESTIMATE_NOT_MEASURED: 20–100 GiB across sessions
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: trajectory formula with low/base/high scenarios
- **Estimation assumptions:** 600 conditions, model panel, repeats, tool/token budgets
- **Expected monetary cost:** ESTIMATE_NOT_MEASURED: Kaggle $0 assumption + provider pricing/cap
- **Command or notebook:** notebooks/kaggle/CAB_T4X2_03_SCALE100_OPEN_MODEL_RUNNER.ipynb plus approved provider manifests
- **Outputs:** immutable manifests, raw runs, merge, paired statistics, rank probability, human sample
- **Completion validator:** exact completeness; clustered inference; B3; claim-gate audit
- **Failure recovery:** resume by task/repeat; quarantine conflicts; never post-hoc select
- **Paper eligibility:** only after audited eligibility and claim-ledger promotion


## Category F — Baselines and ablations

### F1_BASELINES_ABLATIONS

- **Run ID:** F1_BASELINES_ABLATIONS
- **Study stage:** confirmatory secondary
- **Purpose:** Policy baselines; scorer/metric/intervention/template/domain/repeat sensitivity.
- **Evidence role:** secondary and exploratory evidence
- **Mandatory or optional:** mandatory subset; optional extensions preregistered
- **Prerequisite gates:** E design frozen before outcome inspection
- **Task pack:** same frozen Scale-100 or declared heldout slices
- **Models or category:** policy baselines and fixed ablation variants
- **Repetitions:** same repeats as corresponding primary comparison
- **Clean/intervention counts:** matched to frozen slice
- **Expected trajectories:** conditions × baselines/ablations × repeats
- **Compute class:** GPU_T4X2_DATA_PARALLEL
- **CPU/GPU/API:** T4×2 for open paths; CPU for rescoring
- **Kaggle suitability:** yes
- **T4×2 compatibility:** compatible via notebook 05
- **Expected VRAM:** ESTIMATE_NOT_MEASURED: model-dependent
- **Expected disk:** ESTIMATE_NOT_MEASURED: 10–100 GiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: matrix cells × primary-study runtime
- **Estimation assumptions:** number of fixed cells, models, repeats
- **Expected monetary cost:** ESTIMATE_NOT_MEASURED; provider cells require separate cap
- **Command or notebook:** notebooks/kaggle/CAB_T4X2_05_BASELINES_AND_ABLATIONS.ipynb
- **Outputs:** cell manifests, trajectories, paired ablation tables, sensitivity assets
- **Completion validator:** all preregistered cells complete; multiplicity and exploratory labels applied
- **Failure recovery:** resume per cell; do not drop unfavorable cells
- **Paper eligibility:** yes only for preregistered audited cells


## Category G — Naturalistic transfer

### G1_NATURALISTIC_TRANSFER

- **Run ID:** G1_NATURALISTIC_TRANSFER
- **Study stage:** transfer
- **Purpose:** Test whether controlled robustness patterns transfer to mock-realistic artifacts.
- **Evidence role:** transfer evidence
- **Mandatory or optional:** mandatory for stronger ceiling
- **Prerequisite gates:** artifact provenance/license/privacy/injection/human review; D audited
- **Task pack:** naturalistic_transfer
- **Models or category:** same fixed panel where technically possible
- **Repetitions:** preregistered
- **Clean/intervention counts:** 72 pilot clean / 360 pilot intervention
- **Expected trajectories:** 432 × models × repeats
- **Compute class:** HYBRID
- **CPU/GPU/API:** T4×2 open + separately approved providers
- **Kaggle suitability:** yes
- **T4×2 compatibility:** compatible via notebook 08
- **Expected VRAM:** ESTIMATE_NOT_MEASURED: model-dependent
- **Expected disk:** ESTIMATE_NOT_MEASURED: 10–60 GiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: artifact-token/tool-call formula
- **Estimation assumptions:** 432 pilot instances, longer context/tool use, retries
- **Expected monetary cost:** ESTIMATE_NOT_MEASURED; cap per provider manifest
- **Command or notebook:** notebooks/kaggle/CAB_T4X2_08_NATURALISTIC_TRANSFER_RUNNER.ipynb
- **Outputs:** provenance-linked trajectories, transfer tables/plots, audit
- **Completion validator:** privacy/license/PII and injection checks; exact merge; human audit
- **Failure recovery:** quarantine artifact failures; removal procedure; preserve raw errors
- **Paper eligibility:** only after audited eligibility


## Category H — Main-500

### H1_MAIN500

- **Run ID:** H1_MAIN500
- **Study stage:** main confirmatory
- **Purpose:** High-coverage final study, multi-session shards, final scorer sanity and reproducibility reruns.
- **Evidence role:** primary paper evidence candidate
- **Mandatory or optional:** conditional mandatory
- **Prerequisite gates:** E/G justify scale; Main-specific review/freeze/power/cost/approval; challenge remains hidden
- **Task pack:** main500_confirmatory (heldout challenge excluded until final protocol)
- **Models or category:** fixed justified panel
- **Repetitions:** preregistered
- **Clean/intervention counts:** 500 pilot clean / 2500 pilot intervention
- **Expected trajectories:** 3000 × models × repeats
- **Compute class:** HYBRID
- **CPU/GPU/API:** multi-session T4×2 open plus approved provider plan
- **Kaggle suitability:** yes
- **T4×2 compatibility:** compatible via notebook 04
- **Expected VRAM:** ESTIMATE_NOT_MEASURED: per model; 4-bit/fallback rules
- **Expected disk:** ESTIMATE_NOT_MEASURED: 50–500 GiB across checkpoints/exports
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: 3000 conditions × models × repeats / two workers
- **Estimation assumptions:** multi-session overhead, tokens, tools, retry, reproducibility subset
- **Expected monetary cost:** ESTIMATE_NOT_MEASURED: explicit provider price/cap scenarios
- **Command or notebook:** notebooks/kaggle/CAB_T4X2_04_MAIN500_OPEN_MODEL_RUNNER.ipynb
- **Outputs:** chunk manifests, append ledgers, merged raw/scores, audits, statistics, reruns
- **Completion validator:** all chunks/keys/hashes; B3; reproducibility; claim and release gates
- **Failure recovery:** resume chunks; failure-recovery notebook 07; merge notebook 06
- **Paper eligibility:** only audited eligible runs/assets


## Category I — Paper asset build

### I1_PAPER_RELEASE_BUILD

- **Run ID:** I1_PAPER_RELEASE_BUILD
- **Study stage:** paper and release
- **Purpose:** Generate final tables/figures/failure gallery/claims, compile paper/supplement, package release.
- **Evidence role:** paper/release
- **Mandatory or optional:** mandatory
- **Prerequisite gates:** eligible audited manifests; human/scorer audits; claims explicitly promoted
- **Task pack:** eligible run directories only
- **Models or category:** none
- **Repetitions:** 1 deterministic build plus reproducibility check
- **Clean/intervention counts:** n/a
- **Expected trajectories:** 0 trajectories; consumes immutable eligible evidence
- **Compute class:** CPU_ONLY
- **CPU/GPU/API:** CPU
- **Kaggle suitability:** no
- **T4×2 compatibility:** not applicable
- **Expected VRAM:** not applicable
- **Expected disk:** ESTIMATE_NOT_MEASURED: 5–20 GiB
- **Expected runtime range:** ESTIMATE_NOT_MEASURED: 10–90 minutes
- **Estimation assumptions:** eligible runs, plot count, LaTeX passes
- **Expected monetary cost:** USD 0; ESTIMATE_NOT_MEASURED
- **Command or notebook:** make paper-draft && python3 scripts/release_check.py
- **Outputs:** tables, figures, failure gallery, PDF/supplement, release manifest/package
- **Completion validator:** paper submission checks; asset eligibility; claims; release; reproduction
- **Failure recovery:** refuse ineligible input; rebuild from raw immutable runs
- **Paper eligibility:** yes only after all gates pass


## Global failure rules

- Infrastructure failures are not model failures.
- Preserve partial trajectories/checkpoints and failure metadata.
- Never silently retry one model more favorably than another.
- Refuse merge on missing/duplicate task-repeat keys or hash/version mismatch.
- Do not change prompts, tasks, interventions, exclusions, scorer tolerances, or analysis endpoints after observing confirmatory outcomes.
- Null or contrary results remain reportable outcomes.
