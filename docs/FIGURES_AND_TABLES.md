# Figures And Tables

## Figures

- Figure 1: benchmark schematic, generated as Mermaid Markdown.
- Figure 2: clean success vs intervention success.
- Figure 3: intervention family success breakdown.
- Figure 4: clean ranking vs ACRS ranking.
- Figure 5: failure mode distribution.
- Figure 6: final-answer success vs trajectory failure disagreement.

Figures are generated with matplotlib, except Figure 1 which is a Mermaid template until the paper design is finalized.

## Tables

- Table 1: benchmark statistics.
- Table 2: main agent performance.
- Table 3: intervention family performance.
- Table 4: ablation results placeholder.
- Table 5: human validation agreement placeholder.

Tables are exported as `.csv`, `.md`, and `.tex`. Placeholder tables explicitly say `not yet run`; they do not contain fabricated results.

## Reproducibility

All paper assets should be generated from a run directory:

```bash
python -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

Do not manually edit generated tables or figures for claimed results. If a presentation-only edit is needed later, keep the raw generated asset and document the edit.
