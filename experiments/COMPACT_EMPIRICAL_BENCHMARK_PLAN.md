# Compact Empirical Benchmark Plan

## Purpose

Move from infrastructure-only CAB to a compact empirical study without running
`main_200` or `main_500`.

## Scope

Two allowed compact scales:

| Scale | Paired intervention items | Clean matches | Total instances per model | Family balance |
| --- | ---: | ---: | ---: | --- |
| Compact-20 | 20 | 20 | 40 | 5 per family |
| Compact-50 | 50 | 50 | 100 | 12 or 13 per family |

Intervention families:

- `tool_removal`
- `tool_failure`
- `memory_corruption`
- `observation_conflict`

## Selection Rule

Use only reviewed items from `data/processed/pilot_v0_1` or a later approved
compact slice. Select for:

- no unresolved leakage blocker,
- completed compact gold-output triage,
- no unresolved high-risk isolation ambiguity,
- domain diversity across calendar/email, travel, research, files/spreadsheets, and coding/debugging,
- difficulty diversity where feasible,
- no duplicate base task in the compact set unless explicitly paired for clean/intervention comparison.

## Provider/Model Plan

Preferred compact comparison:

| Category | Count | Notes |
| --- | ---: | --- |
| frontier provider | 1 | e.g. OpenAI/Anthropic/Gemini family, chosen by approved config |
| budget provider | 1 | cheaper production API category |
| open or local compatible provider | 1 | only if no local LLM run is required in this task |

If budget is limited, run one provider for Compact-20 first and use it only for
pipeline/scorer/human-validation calibration.

## Expected Trajectories

| Scale | 1 model | 3 models |
| --- | ---: | ---: |
| Compact-20 | 40 | 120 |
| Compact-50 | 100 | 300 |

## Runtime And Cost Planning

Approximate runtime:

- Compact-20: 1 to 3 hours depending on provider latency and retries.
- Compact-50: 4 to 8 hours depending on provider latency and retries.

Approximate budget caps:

- Tiny pilot: <= 5 trajectories, <= approved budget.
- Compact-20: proposed cap <= 25 USD after approval.
- Compact-50: proposed cap <= 100 USD after approval.

Exact costs must be estimated with `estimate-run-cost` on the approved compact
config before any live call. Unknown pricing is not zero cost.

## Required Gates

Before Compact-20:

1. Tiny provider pilot complete or explicitly waived by approval.
2. `SCORER_SANITY_TINY_PROVIDER_PILOT.md` exists from real provider outputs.
3. Compact gold triage complete for selected items.
4. Human validation compact protocol locked.
5. Approved config exists with budget cap and trajectory cap.
6. `allow_paid_calls=true` only in approved live config.
7. Evidence safety passes.

Before Compact-50:

1. Compact-20 post-run audit passes.
2. Human validation sample is ready.
3. Cost estimate stays within approved budget.
4. No unresolved high-risk selected-item blockers.

## Post-Run Audit

Every compact run must produce:

- run directory and metadata audit,
- provider classification audit,
- trajectory count and cost audit,
- incomplete marker check,
- manual review of selected trajectories,
- evidence safety rerun,
- no-run reports rerun,
- scorer sanity refresh,
- human-validation packet export.

## Statistical Analysis

- Report success/degradation with bootstrap confidence intervals.
- Use paired clean/intervention analysis within task pairs.
- Avoid definitive rankings unless 3 models complete and intervals are interpretable.
- Compact-20 supports debugging/preliminary observations only.
- Compact-50 can support modest workshop/COLM-style claims if audits and human validation pass.

## Claims Allowed

Only after real provider runs and audits:

- pipeline works on provider-backed trajectories,
- scorer sanity observations,
- preliminary intervention-family degradation patterns for the compact slice,
- qualitative failure modes with reviewed examples.

## Claims Forbidden

- universal benchmark claim,
- definitive model ranking without enough models and confidence intervals,
- causal proof,
- general real-world robustness,
- NeurIPS readiness,
- validated benchmark without human validation,
- any C1-C8/C10 promotion without claim-gate evidence.

## Explicit Non-Goals

- Do not run `main_200`.
- Do not run `main_500`.
- Do not run broad sweeps.
- Do not use mock/stub/oracle outputs as scientific evidence.
