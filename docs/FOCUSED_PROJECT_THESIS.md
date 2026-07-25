# Focused Project Thesis

## Current Evidence Boundary

Causal Agent Bench currently has strong benchmark infrastructure and no provider-backed empirical evidence. Provider-backed evidence is `0`, completed human annotations are `0`, paper-eligible empirical assets are `0`, and the NeurIPS submission gate remains `NOT_READY`.

This memo is a no-run framing artifact. It is `engineering_only`, `manual_review_pending`, and `no_provider_evidence`.

## What The Project Is Actually About

The project is about evaluating tool-using agents with paired clean and perturbed tasks. The useful object of study is not a broad proof of agent "causality"; it is whether ordinary outcome-success leaderboards hide brittleness that appears when one controlled factor changes.

## Single Strongest Thesis

Outcome-success leaderboards of tool-using agents may overstate skill; paired controlled perturbations can reveal ranking instability and intervention-specific brittleness.

This is falsifiable. A future provider-backed study could weaken the thesis if clean-success rankings and ACRS rankings remain stable across intervention families, or if observed differences vanish under uncertainty.

## Claims Allowed Before Real Runs

- CAB defines a benchmark design for paired clean/intervention evaluation.
- CAB documents a taxonomy of intended intervention factors.
- CAB includes static governance for claim discipline, provider budgets, and no-API fallback review.
- CAB has engineering-only reproducibility checks and no-run validation scaffolds.
- CAB has planned protocols for Compact-20/50 provider runs and human validation.

## Claims Forbidden Before Real Runs

- Any claim that a model or provider performs better or worse under CAB.
- Any claim that clean success overestimates robustness in observed model behavior.
- Any claim that ACRS changes real model rankings.
- Any claim that trajectory metrics detect real hidden failures.
- Any claim that C10 intervention isolation is validated.
- Any claim that the benchmark is NeurIPS-ready, empirically validated, or leaderboard-ready.

## Terms To Avoid Or Hedge

Avoid as factual claims before evidence:

- "validated benchmark"
- "causal proof"
- "model rankings"
- "agents fail under intervention"
- "we demonstrate"
- "NeurIPS ready"

Safer wording:

- "controlled perturbation"
- "paired intervention design"
- "planned empirical test"
- "ranking-instability hypothesis"
- "intervention-isolation claim remains pending"

## Is "Causal" Justified?

Only in a limited design sense. The repo can say the benchmark uses controlled perturbations intended to vary one factor at a time. It cannot yet say the interventions empirically isolate causal skill components. That stronger wording requires C10 human/expert validation and provider-backed trajectories.

Until then, public-facing language should prefer "controlled perturbation benchmark" or "paired intervention evaluation." Use "causal" only with explicit qualification that causal validity is a hypothesis under review.

## Difference From Ordinary Agent Benchmarks

Ordinary tool-agent benchmarks often score whether the final outcome is correct. CAB's intended distinction is the paired design: compare clean and intervention variants, inspect family-specific brittleness, and ask whether a final-success leaderboard changes when robustness and recovery are measured.

This is a design contribution until real provider outputs and human validation exist.

## Result That Would Make The Paper Important Later

The paper becomes important if a real Compact-20/50 or larger provider-backed study shows:

- clean-success rank and ACRS rank diverge with uncertainty reported,
- degradation differs meaningfully by intervention family,
- trajectory audits identify failures not visible in final-answer success,
- C10 reviewers agree that selected interventions preserve the user goal while varying the intended factor,
- gold-policy review clears or excludes ambiguous answer-changing cases.

