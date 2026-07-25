# Compact Empirical Paper Blueprint

## Working Position

Controlled intervention evaluation for tool-using agents: a compact empirical study.

## Current Evidence Boundary

This blueprint is currently a no-run paper scaffold. Provider/model results are
`0`, completed human validation annotations are `0`, paper-eligible empirical
assets are `0`, and supported C1-C8/C10 claims are `0`.

The current paper should be written as a methods/benchmark-design scaffold.
Empirical claims require future Compact-20/50 provider runs, post-run audit,
scorer sanity, and human validation. The current NeurIPS D&B status is not
reachable.

Canonical companion files:

- `docs/FOCUSED_PROJECT_THESIS.md`
- `docs/CLAIM_TRIAGE_NO_RUN.md`
- `paper/NO_RUN_PAPER_SKELETON.md`
- `paper/FIGURE_TABLE_SPEC_NO_RUN.md`
- `paper/PAPER_WORDING_GUARDRAILS.md`
- `docs/SUBMISSION_LADDER.md`

## Title Candidates

1. Controlled Intervention Evaluation for Tool-Using Agents: A Compact Empirical Study
2. Beyond Final Answers: Compact Interventional Evaluation of Tool-Using Agents
3. Causal Agent Bench Lite: A Compact Study of Tool, Memory, and Observation Perturbations

## Abstract Skeleton

Tool-using language agents are often evaluated by final task success, which can
hide brittle tool use, memory handling, observation interpretation, and recovery.
We introduce a controlled intervention protocol pairing clean tasks with targeted
perturbations over tool removal, tool failure, memory corruption, and observation
conflict. This compact paper reports the benchmark design, scorer calibration
protocol, and human-validation plan. Empirical result placeholders remain blocked
until real provider-backed compact runs and human validation exist.

## Contributions

- A compact controlled-intervention slice for tool-using agents.
- A scorer sanity protocol comparing deterministic scores to manual review.
- A gold-output triage policy for answer-changing interventions.
- A small human-validation protocol for trajectory and intervention review.
- A conservative evidence policy that prevents claim promotion from mock/stub/oracle outputs.

## Method

Describe clean/intervention pairs, deterministic tools, intervention-family
selection, capped provider execution, and post-run audit.

## Compact Dataset

Plan:

- Compact-20: 20 paired intervention items plus clean matches.
- Compact-50: 50 paired intervention items plus clean matches.
- Four families: `tool_removal`, `tool_failure`, `memory_corruption`, `observation_conflict`.

## Metrics

- final-answer success,
- paired clean/intervention degradation,
- ACRS where justified,
- recovery and trajectory diagnostics,
- scorer/manual agreement for calibration sample.

## Tiny Pilot Section

Placeholder. Fill only if a real approved provider pilot exists. Tiny pilot
results support pipeline and scorer sanity only.

## Blocked Provider Pilot / No-API Fallback

Current status: the live provider pilot is blocked because `OPENAI_API_KEY` is
not available, and provider-backed evidence remains `0`.

With no provider evidence, this paper can be framed only as a methodology,
benchmark-design, or workshop proposal. Dry-run outputs are not empirical
model-performance results. Stub/mock outputs are engineering diagnostics only.

No-API manual task review can strengthen benchmark-design validity by checking
task clarity, intervention isolation, gold-answer policy, abstention policy, and
sample exclusion decisions. It cannot support model claims, C3 trajectory
claims, C10, model rankings, or NeurIPS readiness.

Required labels for any no-API fallback artifacts:

- `engineering_only`
- `no_provider_evidence`
- `not_scientific_model_performance`

A future provider pilot can unlock preliminary empirical evidence only after the
approved live gates pass, the single tiny run completes, the config is locked
back to `allow_paid_calls: false`, and the post-run audit plus scorer sanity
review are complete.

## Compact Benchmark Results

Placeholder. Fill only after an approved compact run, post-run audit, and
evidence safety pass.

## Scorer Calibration

Report deterministic scorer result, manual judgment, agreement, mismatch
category, and fix-needed status for each sampled provider trajectory.

## Human Validation

Report only real annotations. Until then, state that human validation is planned
and blocked by absence of provider outputs.

## Limitations

- compact sample size,
- synthetic task distribution,
- heuristic deterministic scorer,
- provider/model selection limited by budget,
- no universal benchmark claim,
- no definitive model ranking without sufficient models and intervals.

## Ethics

Discuss synthetic data, API cost controls, no API keys in configs, annotator
privacy, and no overclaiming.

## Reproducibility

List exact configs, run IDs, cost estimates, post-run audits, scorer sanity CSV,
and human validation packet hashes when available.

## Future Scaling

Future NeurIPS E&D path requires larger provider-backed runs, human validation,
eligible paper assets, and passing submission gate.

## Forbidden Phrases Until Supported

- "we demonstrate"
- "validated benchmark"
- "model rankings"
- "causal proof"
- "general real-world robustness"
- "NeurIPS ready"

See `paper/PAPER_WORDING_GUARDRAILS.md` for stage-specific allowed and
forbidden wording.
