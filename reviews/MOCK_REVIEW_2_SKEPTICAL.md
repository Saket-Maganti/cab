# Mock Review 2 — Skeptical (Harsh)

**Venue:** NeurIPS Main (simulated)  
**Recommendation:** Reject  
**Confidence:** [4/5 placeholder]

## Summary

This submission describes an interventional benchmark for tool-using agents with synthetic tools and heuristic trajectory metrics. The repository is polished, but **the paper presents no completed experiments on real LLM agents** and therefore reads as an ambitious proposal document with LaTeX wrappers—not a scientific result.

## Strengths

1. Problem statement (success ≠ skill) is widely believed and well articulated.
2. Intervention audit tooling shows awareness of validity risks.
3. Claim ledger / evidence policy is more disciplined than many benchmark papers.

## Weaknesses (major)

1. **No frontier or even mid-tier model results.** Mock agents are not evidence.
2. **Synthetic environment** — tasks are templated; tools do not reflect real API friction, latency, or schema diversity.
3. **"Causal" framing is marketing.** Paired perturbations in a simulator are robustness testing, not causal inference; the paper occasionally drifts toward stronger language in the abstract placeholders.
4. **ACRS is an unvalidated composite** — weighting appears arbitrary; no ablation on the metric itself.
5. **No human validation** — trajectory diagnostics are heuristic regex/feature checks, not validated against annotators.
6. **Novelty vs AgentBench / WebArena / GAIA / τ-bench / AgentBoard** — incremental combination of existing ideas (interventions + tool benchmarks).
7. **Benchmark gaming** — synthetic splits and known templates invite overfitting; leaderboard policy not operational.
8. **Scoring heuristics** — premature-stop and contradiction detectors can be gamed by phrase patterns.
9. **Intervention isolation** — automated audit passing ≠ expert agreement; memory-corruption tasks may not reflect real memory interfaces.
10. **Engineering-heavy** — large fraction of repo is CI, release manifests, run management; scientific contribution unclear without data.

## Questions

1. Why should the community adopt another synthetic benchmark when web-agent benchmarks exist?
2. What happens when GPT-4-class models saturate clean tasks—does intervention signal remain?
3. Show one human-validated example where your diagnostic catches a failure a human also flags.

## Reproducibility concerns

Cannot reproduce **results** because there are none. Reproducing **code smoke tests** is not sufficient for NeurIPS main.

## Ethical concerns

Low direct risk (synthetic). Concern: presenting engineering scaffold as near-submission work could mislead readers.

## Required fixes (likely insufficient for this venue without restructure)

1. Target D&B track with empirical pilot as minimum bar.
2. Complete multi-model study + human validation before resubmission.
3. Sharpen related-work contrast; cut causal rhetoric or formalize identifiability assumptions.
4. Validate ACRS against human rankings on a subset.

## Score placeholder

**3/10**
