# First Paper-Eligible 3-Model Compact-20 Pilot Plan

Status: `NO_EXECUTION_PLAN_ONLY`

Labels: `planned_paper_eligible_pilot`, `manual_review_required`, `no_provider_evidence`, `no_claim_promotion`.

## Purpose

The purpose of the first 3-model Compact-20 pilot is to obtain the smallest provider-backed, auditable evidence surface that can test whether clean-task success and intervention-robustness metrics tell different stories for tool-using agents.

This is not a main benchmark. It is the first possible paper-eligible pilot only after all prerequisites, approvals, execution, post-run audits, scorer sanity checks, and paper-asset eligibility gates pass.

## Why Compact-20 Is Enough For First Evidence

Compact-20 is enough for the first evidence pass because it is small enough to review manually before execution and still covers the core paired-intervention design:

- 20 clean/intervention pairs.
- 4 intervention families.
- 5 candidate pairs per family: `tool_removal`, `tool_failure`, `memory_corruption`, `observation_conflict`.
- Multiple domains and difficulties represented in the current candidate manifest.
- One clean and one intervention condition per pair, enabling paired deltas rather than unpaired leaderboard noise.

Compact-20 can support only compact-sample, pilot-level observations after audit. It is not enough for broad leaderboard, NeurIPS-scale, or general agent-capability claims.

## Why Main-200 And Main-500 Are Deferred

`main_200` and `main_500` are explicitly deferred because the current blockers are evidence quality and review completion, not task volume.

- Provider-backed evidence is still `0`.
- Human annotations are still `0`.
- Eligible paper assets are still `0`.
- Compact-20 task review fields are blank.
- Compact-20 gold-policy review fields are blank.
- C10 intervention-isolation review has not produced two-reviewer agreement or adjudication.
- Large runs would multiply cost and audit burden before the scoring, metadata, and manual-review chain has been proven on a compact slice.

The first scientific target is therefore a reviewed 3-model Compact-20 pilot, not scale.

## Model Categories

Use placeholders until a live-run approval exists.

| Category | Placeholder | Role | Minimum rationale |
|---|---|---|---|
| Frontier/API model | `PLACEHOLDER_FRONTIER_API_MODEL` | High-capability reference | Tests whether a frontier model remains robust under controlled perturbations. |
| Strong open/local model | `PLACEHOLDER_STRONG_OPEN_OR_LOCAL_MODEL` | Reproducible/open comparison | Tests whether a strong open model shows the same rank/robustness pattern. |
| Smaller/cheaper baseline | `PLACEHOLDER_SMALLER_OR_CHEAPER_MODEL` | Cost-sensitive baseline | Tests whether a cheaper/smaller model changes rank under ACRS. |

No model ID is final until approval. No model/provider credential belongs in YAML.

## Minimum Acceptable Model Metadata

Every model row must include:

- provider/deployment category,
- exact model ID and provider-facing model string,
- model release, snapshot, version, or served artifact ID when available,
- endpoint class without secrets,
- temperature, max tokens, retry policy, timeout, and step budget,
- prompt file names, prompt versions, and prompt hashes,
- config hash and git commit,
- pricing registry entry or zero-cost/local caveat,
- run ID and run directory,
- provider response metadata available from the runner,
- token/call/cost metadata,
- evidence scope and scientific-evidence flags,
- completion state and interrupted marker absence.

For local/open models, also require server stack, quantization or model artifact identifier, hardware summary, base URL class, and reproducibility limitations.

## Exact Trajectory Count

The planned pilot has exactly:

- 20 reviewed pairs.
- 2 conditions per pair: clean and intervention.
- 3 model categories.
- 1 trajectory per model per condition.

Exact planned trajectories: `20 * 2 * 3 * 1 = 120`.

Retries, provider failures, malformed responses, or resumed attempts must be logged separately and must not be silently counted as successful trajectories.

## Expected Clean/Intervention Pairs

The run should produce:

- 20 unique clean/intervention pairs.
- 40 unique task-condition instances.
- 60 model-pair records, one per model per pair.
- Family coverage: 5 `tool_removal`, 5 `tool_failure`, 5 `memory_corruption`, 5 `observation_conflict`.

The selected slice must come from a reviewed Compact-20 artifact, not directly from the pending candidate manifest.

## Required Scorer Outputs

Required scorer outputs:

- final answer success for each trajectory,
- clean success and intervention success by model and pair,
- paired clean-to-intervention delta,
- ACRS or the repo's current causal robustness score,
- trajectory-level diagnostics,
- tool-call count and invalid-tool flags,
- recovery behavior,
- contradiction handling where applicable,
- early stopping/premature success flags where applicable,
- per-family degradation,
- rank by clean success,
- rank by ACRS,
- rank-change table,
- scorer issue flags and malformed-output flags.

## Required Audit Outputs

Required post-run audit outputs:

- run metadata completeness audit,
- evidence safety check,
- run health report,
- provider/model metadata audit,
- cost and call audit,
- scorer sanity report,
- malformed trajectory report,
- clean/intervention pair-link audit,
- per-family sample audit,
- paper asset eligibility report,
- claim-evidence matrix,
- no secret/key leakage scan over configs and metadata,
- run index refresh or freshness check.

## Required Human-Review Linkage

Before execution:

- Compact-20 task review must be complete.
- Compact-20 gold-policy review must be complete.
- Any excluded candidate must have a replacement reviewed before the slice is approved.

Before C10 support:

- C10 intervention-isolation review must include at least two independent reviewers where required.
- Disagreements must be adjudicated.
- Agreement metrics must be computed.
- The C10 sheet must link each reviewed row back to `candidate_id`, clean instance ID, intervention instance ID, family, and gold-policy status.

Provider outputs may become pilot evidence only after the review linkage is present and audited.

## Claims Allowed After This Pilot

Only if the pilot is actually executed, complete, provider-backed, audited, and paper-asset gates pass, the paper may say:

- "In a 3-model Compact-20 pilot, we observed TODO_REAL_RESULT."
- "In this compact reviewed slice, clean-success rank and ACRS rank were TODO_REAL_RESULT."
- "These pilot observations motivate or fail to motivate larger main-scale evaluation."
- "The result is preliminary compact-sample evidence, not a full benchmark conclusion."

If local/open-model results are included, they must be separately labeled and not pooled with commercial provider results unless the post-run audit explicitly allows that scope.

## Claims Still Forbidden After This Pilot

Even after a successful 3-model Compact-20 pilot, still forbidden unless separate gates pass:

- main-benchmark or leaderboard claims,
- NeurIPS-ready or benchmark-validated claims,
- broad claims that clean success generally overestimates robustness,
- broad claims that ACRS generally changes rankings,
- C10 support without completed human review and adjudication,
- C3 human-diagnostic claims without trajectory review evidence,
- self-checking or ablation claims not run in this pilot,
- any claim over `main_200`, `main_500`, or heldout tasks.

## Current Evidence State

- Provider-backed evidence: `0`
- Human annotations: `0`
- Eligible paper assets: `0`
- C1-C8/C10: planned/unsupported.
- This plan promotes no claims.

## No-Execution Boundary

This file is a plan. It authorizes no provider calls, no local LLM calls, no benchmark execution, no Compact-20 execution, and no claim promotion.
