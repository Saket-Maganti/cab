# Figure Specifications

| ID | Title | Type | Data source | Generator | Submission | Claims |
|---|---|---|---|---|---|---|
| Fig 1 | Benchmark overview | Schematic | Design doc | `generate_placeholder_figures.py` | Required (diagram) | — |
| Fig 2 | Intervention pairing | Schematic | Design doc | `generate_placeholder_figures.py` | Required | C10 (design) |
| Fig 3 | ACRS concept | Schematic | METRIC_CARD | `generate_placeholder_figures.py` | Required | — |
| Fig 4 | Run lifecycle | Schematic | State machine | `generate_placeholder_figures.py` | Optional | — |
| Fig 5 | Family degradation | **Empirical** | table3 / scores | `export-paper-assets` | Required | C2 |
| Fig 6 | Failure gallery | **Empirical** | trajectories | `failure-gallery` | Required | C3, C7, C8 |
| Fig 7 | Human validation | **Empirical** | annotations | `summarize-human-validation` | Required | C3, C10 |
| Fig 8 | Cost–robustness | **Empirical** | run metadata | `export-paper-assets` | Optional | C4 |

## Placeholder rules

- Red banner text: `PLACEHOLDER — NOT EMPIRICAL RESULT`
- No bar charts with numeric performance
- No model names ranked by score
- `.meta.json` must include `"placeholder": true`, `"empirical_result": false`

## Empirical figure rules (when runs exist)

- Provenance footer: run dir, config hash, dataset version, scorer version
- Linked in claim ledger before submission wording

See [../FIGURE_TABLE_BLUEPRINT.md](../FIGURE_TABLE_BLUEPRINT.md), [../../docs/FIGURES_AND_TABLES.md](../../docs/FIGURES_AND_TABLES.md).
