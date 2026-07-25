# No-Run Paper Skeleton

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## Title

Controlled Perturbation Evaluation for Tool-Using Agents

## Abstract Placeholder

Tool-using agents are commonly evaluated by final task success, but final success alone may hide brittleness under tool, memory, and observation perturbations. We introduce a paired controlled-perturbation benchmark design and a conservative evidence-governance protocol for testing ranking instability and intervention-specific brittleness. This draft reports the planned benchmark structure, validation protocol, and future Compact-20/50 empirical path. Empirical results, human-validation claims, and leaderboard claims are not yet reported.

## Introduction

The paper should lead with the ranking-instability hypothesis, not a broad causal proof. The current contribution is a benchmark design and evidence discipline. The future empirical contribution depends on provider-backed runs and human validation.

## Benchmark Design

Describe paired clean/intervention instances, deterministic tool environments, intervention metadata, and the requirement that each intervention names an intended changed factor and expected answer policy.

## Intervention Taxonomy

Summarize `tool_removal`, `tool_failure`, `memory_corruption`, `observation_conflict`, and additional families as planned perturbation types. State that intervention isolation is not yet validated and depends on C10 review.

## Metrics And ACRS Caveats

Report planned final success, paired degradation, trajectory diagnostics, and ACRS. ACRS is a simple summary metric and must not be framed as a deep causal estimator.

## Data Quality And Validation Plan

Gold-output warnings and high-risk intervention families require manual review. The paper should cite the Compact-20 and C10 packets as planned validation scaffolds, not completed evidence.

## Future Compact-20/50 Empirical Plan

Future execution should begin with a reviewed Compact-20 and only then consider Compact-50. Main_200 and main_500 remain out of scope for the no-run phase.

## Human Validation Plan

Human review must cover task clarity, gold policy, intervention isolation, and adjudication. Agreement metrics require two independent completed reviewers.

## Limitations

- No provider-backed results currently exist.
- No completed human annotations currently exist.
- Synthetic/template tasks may limit external validity.
- Gold-output warnings remain unresolved for selected rows.
- Intervention isolation is planned but not validated.
- ACRS is a compact diagnostic, not a proof of causal skill.

## Ethics And Broader Impacts

Discuss cost controls, no API keys in repo files, clear evidence labeling, synthetic data limits, and avoidance of inflated leaderboard claims.

## Reproducibility

List future configs, run IDs, audit scripts, manifest hashes, and reviewer packet hashes only after they exist. Current reproducibility is engineering-only.

## Missing Evidence

Provider outputs, scorer sanity on real trajectories, Compact-20/50 results, C10 validation, human agreement metrics, eligible paper assets, and supported C1-C8/C10 claims are all still missing.

