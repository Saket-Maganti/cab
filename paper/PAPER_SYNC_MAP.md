# Paper Synchronization Map

Maps paper sections to required evidence. **Results, Human Validation, and Ablations remain blocked** until real provider/main evidence exists.

Machine-readable guard: `paper/paper_section_contract.json`. Run
`python3 scripts/check_paper_section_contract.py --mode draft` before paper
edits and `--mode submission` before any submission claim.

| Paper Section | Required Evidence | Current Status | Artifact Path | Claim IDs | Safe? |
|---|---|---|---|---|---|
| Abstract | None (no numbers) | Draft — placeholders preserved | `paper/latexpaper/generated/00_abstract.tex` | — | Yes |
| Introduction | Motivation + framework | Updated 2026-05-20 | `paper/latexpaper/sections/01_introduction.tex` | — | Yes |
| Related Work | Bibliography | Draft | `paper/latexpaper/references.bib` | — | Yes |
| Benchmark Design | Taxonomy, templates, freeze, audits | Updated | `docs/BENCHMARK_TAXONOMY.md`, `benchmark_specs/`, `data/frozen/pilot_v0.1/` | — | Yes |
| Interventional Framework | Intervention + isolation audit | Updated | `scripts/audit_intervention_isolation.py`, `audits/` | C10 (method) | Yes |
| Metrics | Metric definitions + guards | Updated | `docs/METRICS.md`, `docs/METRIC_CARD_ACRS.md` | — | Yes |
| Experimental Setup | Run pipeline, configs, evidence policy | Updated | `docs/CLI_REFERENCE.md`, `experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md` | — | Yes |
| Results RQ1–RQ5 | Complete provider/main runs + CIs | **Blocked** | `paper/latexpaper/generated/07_results.tex` | C1–C8 | No |
| Human Validation | Annotations + agreement | **Blocked** — scaffold only | `docs/HUMAN_VALIDATION_*.md` | C3, C10 | No |
| Ablations | Ablation matrix runs | **Blocked** — planned | `configs/ablations/`, `paper/latexpaper/sections/09_ablations.tex` | C5, C6 | No |
| Limitations | Honest scope | Updated | `docs/DO_NOT_OVERCLAIM.md` | — | Yes |
| Ethics/Repro | Safety, release, evidence levels | Updated | `release/`, `docs/EVIDENCE_LEVEL_POLICY.md` | C9 | Yes (engineering) |
| Checklist | NeurIPS items | Updated honest statuses | `docs/NEURIPS_ARTIFACT_CHECKLIST.md` | — | Yes |
| Conclusion | None (no results) | Updated | `paper/latexpaper/sections/12_conclusion.tex` | — | Yes |
| Engineering demo (not a paper section) | Mock micro E2E | Complete — **not empirical** | `demo/ENGINEERING_DEMO_BUNDLE.md` | — | Appendix only |

## Rules

1. Do not fill numeric placeholders (N, M, K, X, rho) without linked run artifacts.
2. Mock/stub runs may appear only in methods/appendix as **detector validation**, not results.
3. Phase 9 mock demo (`results/20260520T072032Z_pilot_mock_diagnostic_micro`) — engineering only.
4. Update this map when claim ledger statuses change.

## Sync commands

```bash
python3 scripts/check_paper_placeholders.py --mode draft
python3 scripts/check_paper_section_contract.py --mode draft
python3 scripts/check_claim_ledger.py --mode draft
python3 scripts/validate_paper_assets.py --mode draft
python3 scripts/lint_paper_claims.py --mode draft
```

See [PAPER_STATUS.md](PAPER_STATUS.md).
