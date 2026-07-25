# 16 Paper-Code Consistency Audit

## Files inspected

`paper/`, `figures/`, `tables/`, `docs/CLAIM_LEDGER.md`, `docs/claim_ledger.json`, `docs/REPRODUCIBILITY.md`, `docs/METRICS.md`, `docs/INTERVENTIONS.md`, `docs/BENCHMARK_CARD.md`, `docs/DATASET_CARD.md`, `docs/ETHICS_AND_LIMITATIONS.md`, and `README.md`.

## Consistency findings

- Title/theme are consistent with CausalAgentBench as a causal benchmark for tool-using agents.
- ACRS formula in code and docs is consistent: intervention success divided by clean success, undefined when clean success is zero.
- Intervention families in generated pilot data and docs align at the high level.
- Agent names in configs match registry names after validation.
- Dataset counts in generated pilot output are reproducible: 250 base tasks, 1250 interventions, 1500 instances.
- Exported paper assets exist but are explicitly engineering-only when produced from local-stub runs.

## Risks

- Paper generated snippets still contain placeholders.
- Global `figures/` and `tables/` are easy to mistake for scientific assets; use run-local manifests and claim ledger before citing.
- Some docs describe planned studies and must not be read as completed evidence.

## Fixes

No paper wording was changed by this audit beyond generated asset refreshes required to make existing release/camera-ready checks pass.

