# Causal Agent Bench — NeurIPS Readiness Prompt Pack

This prompt pack is designed to move Causal Agent Bench from **NeurIPS-grade infrastructure scaffold** to a **credible NeurIPS Evaluations/Datasets-style benchmark paper candidate**.

## Current starting point assumed

- Leakage blocker clusters: 0
- Provider gate: `template_safe_but_not_runnable`
- Paper-eligible runs: 0
- Eligible empirical assets: 0
- Provider-backed scientific evidence: 0
- Human annotations: 0
- C1–C8: planned / unsupported
- C9: engineering_only
- C10: planned / unsupported
- Main benchmark not ready
- main_200 and main_v0_1_500 not main-candidate ready
- High-risk intervention queue and gold-output warnings remain
- No claims promoted
- No `*_APPROVED.yaml` unless signed approval exists

## Important truth

These prompts cannot magically make the project NeurIPS-ready by documentation alone. They are written so that, **if executed successfully with real provider runs, human validation, cleaned gold outputs, main benchmark freeze, statistical analysis, release packaging, and paper completion**, the project should become a serious NeurIPS candidate.

If any critical empirical gate fails, Composer must stop and report `NOT_READY`, not fake readiness.

## Execution order

Run the prompts in this exact order:

1. `01_provider_approval_dryrun_prompt.md`
2. `02_tiny_provider_pilot_postrun_audit_prompt.md`
3. `03_scorer_calibration_gold_policy_prompt.md`
4. `04_human_validation_pilot_prompt.md`
5. `05_main200_readiness_and_benchmark_prompt.md`
6. `06_main500_multi_provider_benchmark_prompt.md`
7. `07_neurips_paper_release_submission_gate_prompt.md`

## Expected outcome by the end

The final target state is:

- Provider-backed runs exist and pass post-run audit
- Scorer is calibrated against human judgment
- Gold-output warnings are triaged and resolved
- High-risk intervention review queue is cleared or bounded
- main_200 is validated
- main_v0_1_500 / main_500 is frozen and benchmarked
- ≥5 models / ≥3 provider categories are evaluated, if budget allows
- Human validation for C3/C10 exists with agreement statistics
- Claims C1–C8/C10 are promoted only if supported by linked evidence
- Paper tables/figures are generated only from eligible assets
- Public artifact/release bundle is packaged
- NeurIPS submission gate returns `READY` or an explicit `NOT_READY` with exact blockers

## Non-negotiable rules

- Never fabricate numbers.
- Never fabricate human annotations.
- Never promote claims without linked evidence.
- Never treat mock/stub/oracle/local interrupted runs as scientific evidence.
- Never mark paper assets eligible manually.
- Never hide failed gates.
- If evidence is insufficient, the final output must say `NOT_READY`.

## Budget/computation note

Prompts 2, 5, and 6 may require paid provider calls. Prompt 4 requires human annotation labor. If budget, API keys, or annotators are unavailable, Composer must stop and create a blocking report rather than pretending completion.
