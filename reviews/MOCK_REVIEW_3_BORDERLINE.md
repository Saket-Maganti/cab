# Mock Review 3 — Borderline (D&B Track)

**Venue:** NeurIPS Datasets & Benchmarks (simulated)  
**Recommendation:** Borderline / Weak Reject until pilot complete  
**Confidence:** [3/5 placeholder]

## Summary

CausalAgentBench offers paired clean/intervention instances, ten intervention families, and a reproducible evaluation harness. The benchmark **design and documentation exceed many submissions**, but the paper lacks the empirical demonstration and human audit normally expected even for D&B at NeurIPS.

## Strengths

1. Well-documented intervention families and failure taxonomy.
2. Frozen pilot dataset with audit reports.
3. Transparent claim ledger — authors state what is not yet supported.
4. Trajectory + final-success dual reporting is timely.

## Weaknesses

1. Empirical section is placeholder-only ([N], [M], [K], [X], [rho]).
2. Only engineering/mock trajectories exist in the repo index.
3. ACRS may be redundant with reporting family-level metrics separately.
4. Related work coverage is broad but contrast bullets could be sharper.
5. Human validation protocol not executed.

## Questions

1. Dataset size for v1.0 release vs pilot — which is the canonical benchmark?
2. Will you provide baseline numbers for at least two API models?
3. How do you prevent template memorization across train/dev/test?

## Reproducibility

Good infrastructure; missing result artifacts.

## Ethics

Acceptable for synthetic benchmark; complete human-subjects protocol before collecting labels.

## Required fixes

1. At minimum: one complete provider pilot run + published baseline table.
2. Human audit sample with agreement stats for intervention validity.
3. Clarify track positioning (D&B vs methods).

## Score placeholder

**5/10**
