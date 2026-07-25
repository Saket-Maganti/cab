# Figure and Table Blueprint

Planned paper assets. **No fake results.** Placeholders allowed in draft only where noted.

## Tables

| ID | Purpose | Required input | Generator | Status | Draft placeholder? | Submission | Claims |
|---|---|---|---|---|---|---|---|
| **Table 1** | Benchmark statistics (domains, families, counts) | Frozen dataset manifest | `export-paper-assets` / generation report | Partial (stats from frozen pilot) | Yes | Required | C10 (design) |
| **Table 2** | Main agent performance (clean, intervention, ACRS) | Complete provider/main run | `export-paper-assets` | **Placeholder** | Yes | Required | C1, C4, C5, C7 |
| **Table 3** | Intervention-family performance | Scored trajectories by family | `export-paper-assets` | **Placeholder** | Yes | Required | C2, C10 |
| **Table 4** | Ablations (scaffolds, prompts) | Ablation run dirs | `export-ablation-table` | **Placeholder** | Yes | Required | C5, C6 |
| **Table 5** | Human validation agreement | Annotation CSV + summary | `summarize-human-validation` | **Placeholder** | Yes | Required | C3, C10 |
| **Table 6** | Cost / latency vs performance | Run metadata + scores | `export-paper-assets` | **Placeholder** | Yes | Recommended | — |
| **Appendix A1** | Config / model metadata | `run_metadata.json` | Manual + export sidecars | Partial | Yes | Required | — |

## Figures

| ID | Purpose | Required input | Generator | Status | Draft placeholder? | Submission | Claims |
|---|---|---|---|---|---|---|---|
| **Figure 1** | Benchmark overview | Design spec | Mermaid / `figures/figure1_*` | Scaffold exists | Yes | Required | — |
| **Figure 2** | Paired intervention design | Diagram spec | `figures/figure1_benchmark_schematic` / design | Scaffold | Yes | Required | C10 (design) |
| **Figure 3** | Intervention-family degradation | table3 / scores by family | `export-paper-assets` | **Placeholder** | Yes | Required | C2 |
| **Figure 4** | Ranking instability (clean vs ACRS) | table2 rankings | `export-paper-assets` | **Placeholder** | Yes | Required | C4 |
| **Figure 5** | Trajectory diagnostic breakdown | Scores + failure gallery | `failure-gallery`, export | **Placeholder** | Yes | Required | C3, C7, C8 |
| **Figure 6** | Failure gallery (examples) | Run trajectories | `failure-gallery` CLI | Engineering examples only | Yes | Required | C3, C7, C8 |
| **Figure 7** | Human validation agreement | table5 | `summarize-human-validation` | **Placeholder** | Yes | Required | C3, C10 |
| **Figure 8** | Cost–robustness frontier | table6 + ACRS | `export-paper-assets` | **Placeholder** | Yes | Optional | C4, C5 |

## Generation workflow (when runs exist)

```bash
python3 -m causal_agent_bench score --run-dir results/<complete_run>
python3 -m causal_agent_bench analyze --run-dir results/<complete_run>
python3 -m causal_agent_bench export-paper-assets --run-dir results/<complete_run>
# NOT on incomplete/interrupted runs without explicit preliminary labeling
```

## Status legend

- **Scaffold** — structure exists, no empirical data
- **Partial** — deterministic/generation stats only
- **Placeholder** — "not yet run" in CSV/TeX
- **Ready** — linked in claim ledger with run dir

See also [docs/FIGURES_AND_TABLES.md](../docs/FIGURES_AND_TABLES.md), [PAPER_SYNC_MAP.md](PAPER_SYNC_MAP.md).
