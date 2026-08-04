# CAB ICLR Ultimate Prompt Pack

This pack redirects Causal Agent Bench toward the strongest realistic ICLR submission achievable under the user's limited hardware.

It does **not** guarantee acceptance. Its purpose is to maximise scientific novelty, methodological quality, empirical credibility, reproducibility, and paper clarity while remaining honest about the available compute.

## Intended Paper Identity

> **Success Is Not Skill: Intervention-Validated Robustness Evaluation and Recovery for Tool-Using Agents**

CAB should become a methodology-and-findings paper with four connected contributions:

1. an intervention-validity framework;
2. paired robustness inference;
3. a resource-efficient recovery-aware agent controller;
4. naturalistic transfer showing whether CAB robustness predicts realistic failures.

The benchmark supports these contributions; it is not the sole contribution.

## Execution Order

### Build-only phase

1. `00_ICLR_ULTIMATE_MASTER_ORCHESTRATOR.md`
2. `01_ICLR_CONTRIBUTION_AND_THEORY_BUILD.md`
3. `02_RECOVERY_AWARE_CONTROLLER_BUILD.md`
4. `03_INTERVENTION_VALIDITY_AND_HUMAN_STUDY_BUILD.md`
5. `04_SCALE100_AND_NATURALISTIC_DATASET_BUILD.md`
6. `05_RESOURCE_AWARE_M4_KAGGLE_T4X2_INFRA.md`

The master orchestrator may execute Prompts 1–5 internally. Use the separate prompts when work must be split across Codex sessions.

### Evidence phase

7. `06_COMPACT20_PILOT_EXECUTION.md`
8. `07_SCALE100_CONFIRMATORY_EXECUTION.md`
9. `08_NATURALISTIC_TRANSFER_AND_ABLATIONS.md`
10. `09_STATISTICAL_ANALYSIS_CLAIM_AND_PAPER_GATE.md`
11. `10_ICLR_PAPER_RELEASE_AND_REVIEWER_GAUNTLET.md`

Do not run evidence prompts before the build gate and genuine human-validation gate allow them.

## Compute Strategy

### MacBook Air

Use it for code development, tests, task generation, leakage checks, human-review validation, analysis, paper compilation, plotting, result merging, and release packaging.

Do not plan large-model inference on the Mac.

### Kaggle T4×2

Use it for quantised open-model inference, deterministic two-worker data parallelism, Compact-20, Scale-100 shards, naturalistic-transfer shards, selected ablations, and optional Main-set expansion only if justified.

### Optional provider lane

Keep provider support optional and strictly budget-gated. The paper must remain viable with an open-model core panel, though a small independent provider panel would strengthen external validity if affordable later.

## Stop Rule

Do not create another generic scaffold cycle after the build prompts pass. Move to genuine human review and then real execution.
