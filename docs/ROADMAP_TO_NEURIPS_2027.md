# Roadmap to NeurIPS 2027

## Current status (May 2026)

- Benchmark generation pipeline operational (pilot + main slices)
- Deterministic scoring, analysis, paper-asset export scaffolding
- Zero-cost / micro / stub configs and run-management CLI
- Claim ledger: C1–C8/C10 **planned**; no final scientific claims supported
- No completed provider-backed non-oracle pilot at publication scale
- Human validation infrastructure only (no completed annotation study)

## Next 30 days (build-only + micro validation)

- Keep using stub/mock micro runs for CI and tooling (`pilot_stub_micro_3.yaml`)
- Complete run-report / compare-runs / failure-gallery workflows on stub fixtures
- Dataset audits on frozen pilot_v0.1 and main_v0_1_500
- Submission readiness checker green on engineering scaffold (expected: fail submission)
- Reviewer attack matrix kept current with code guards

## Next 90 days (bounded pilots)

- Complete 20-task local Ollama pilot (preliminary only)
- Small paid provider pilot with explicit budget approval
- Human validation sample (≥20 cases) with dual annotation
- Ablation matrix on stub then provider cells
- Re-run post-run verification audit after first real provider pilot

## Pilot phase

| Milestone | Config | Evidence |
|-----------|--------|----------|
| Micro stub | `pilot_stub_micro_3.yaml` | engineering |
| Micro local | `pilot_free_local_micro_3.yaml` | preliminary |
| 20-task local | `pilot_free_local_fast_10.yaml` | preliminary |
| 20-task provider | `pilot_multi_provider_20.yaml` | pilot candidate |

## Human validation phase

- Export samples from completed pilots
- Annotate task quality + trajectory diagnostics
- Agreement report before claim updates

## Main experiment phase

- Freeze eval split (`main_v0_1_500`)
- Multi-provider 500-task run with budget + monitoring
- Statistical analysis on held-out templates

## Paper phase

- Fill placeholders only from verified runs (`fill-paper-from-run`)
- Submission mode checks: placeholders, evidence mapping, claim ledger
- No Prompt 67 / NeurIPS-scale wording until checklist green

## Release phase

- Artifact bundle + reproducibility scripts
- Public dataset card + contamination audit
- Leaderboard export (oracle excluded)
