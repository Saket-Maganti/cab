# Related Work Gap Map

This map uses existing repo references and positioning notes only. Missing citations are marked TODO rather than invented.

## Tool-Agent Reliability Benchmarks

- Covers: end-task success, tool/API use, multi-step agent performance.
- CAB overlaps: tool-using synthetic tasks and success scoring.
- CAB may add later: paired clean/intervention robustness analysis.
- CAB does not add now: empirical model-performance evidence.
- Reviewer attack: "This is another tool benchmark."
- Citation status: partially present in `docs/RELATED_WORK_MATRIX.md`; verify bibliography before paper use.

## Agent Robustness And Adversarial Benchmarks

- Covers: stress tests, adversarial scenarios, reliability failures.
- CAB overlaps: perturbation families and brittleness framing.
- CAB may add later: intervention-specific paired deltas.
- CAB does not add now: real robustness findings.
- Reviewer attack: "Perturbations are synthetic and unvalidated."
- Citation status: TODO for missing robustness benchmark citations.

## Process Vs Outcome Evaluation

- Covers: trajectories, intermediate steps, final answer limitations.
- CAB overlaps: trajectory metrics and ACRS design.
- CAB may add later: cases where trajectory metrics detect failures missed by final success.
- CAB does not add now: human-validated trajectory evidence.
- Reviewer attack: "Trajectory metrics are heuristic."
- Citation status: TODO where bib entries are missing.

## Synthetic/Template Benchmark Validity

- Covers: validity risks from template tasks and artificial distributions.
- CAB overlaps: synthetic data generation.
- CAB may add later: clear disclosure plus manual validation.
- CAB does not add now: naturalistic transfer evidence.
- Reviewer attack: "The benchmark may reward template quirks."
- Citation status: TODO for benchmark-validity references.

## Human Validation Of Benchmark Interventions

- Covers: expert review, annotation agreement, adjudication.
- CAB overlaps: C10 packet and planned human review.
- CAB may add later: intervention-isolation agreement.
- CAB does not add now: completed agreement metrics.
- Reviewer attack: "Isolation is asserted, not validated."
- Citation status: TODO for human validation and annotation agreement references.

## Causal/Controlled Perturbation Language

- Covers: causal inference and controlled-factor language.
- CAB overlaps: paired intervention design.
- CAB may add later: better-validated intervention-isolation evidence.
- CAB does not add now: causal identification proof.
- Reviewer attack: "Causal language is too strong."
- Citation status: present only at broad foundation level; qualify heavily.

