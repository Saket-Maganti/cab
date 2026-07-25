# Figures And Tables

## Figures

- Figure 1: benchmark overview schematic (Mermaid Markdown).
- Figure 2: clean success vs intervention success. Planned claim links: C1.
- Figure 3: intervention-family degradation heatmap. Planned claim links: C2, C10.
- Figure 4: clean ranking vs ACRS ranking. Planned claim links: C4.
- Figure 5: cost vs robustness (ACRS scatter). Planned claim links: C5, C7.
- Figure 6: trajectory failure taxonomy (mined audit aid). Planned claim links: C7, C8.
- Figure 7: human validation / LLM-judge agreement (only when annotation or calibration artifacts exist).

Legacy supplementary figures (`failure mode distribution`, `final-answer vs trajectory disagreement`) are written under `paper_assets/figures/legacy/` for backward compatibility.

Figures are generated with matplotlib, except Figure 1 which is a Mermaid template until the paper design is finalized.
Each figure exports **PNG**, **PDF**, and a **`.meta.json` sidecar** with caption text and provenance placeholders.
Generated figures include a small metadata footer with run directory, config hash, dataset version, model IDs, and timestamp.

## Tables

- Table 1: benchmark statistics. Planned claim links: C10.
- Table 2: main agent performance, excluding oracle sanity-check agents by default. Planned claim links: C1, C4, C5, C7.
- Table 2 oracle sanity check: oracle upper-bound rows, reported separately and not as realistic-agent leaderboard evidence.
- Table 3: intervention family performance. Planned claim links: C2, C10.
- Table 4: prompt/scaffold ablation results when ablation metadata is present; otherwise a placeholder. Planned claim links: C5, C6.
- Table 5: human validation agreement placeholder. Planned claim links: C3, C10.
- Table 6: performance vs cost and latency, excluding oracle sanity-check agents by default.
- Table 7: robustness vs cost and latency, excluding oracle sanity-check agents by default.

Tables are exported as `.csv`, `.md`, `.tex`, and **`.meta.json` sidecars** with captions and eligibility flags. Placeholder tables explicitly say `not yet run`; they do not contain fabricated results.
Generated tables include metadata columns for run directory, config hash, seed, dataset version, model IDs, scorer versions, git commit, and timestamp when available. Table 4 also includes prompt version hashes and prompt file references for ablation rows.
Table 5 loads human-validation agreement from `human_validation/summary/` when `summarize-human-validation` has been run.
Cost tables use estimated provider costs from token usage and configured pricing; local-stub zero-cost rows are engineering checks only.

## Reproducibility

All paper assets should be generated from a run directory:

```bash
python -m causal_agent_bench export-paper-assets --run-dir results/<run_dir> --allow-engineering-only
```

Exports are blocked for oracle-only runs. Stub/smoke/local-stub runs require `--allow-engineering-only` and are marked `engineering_only_scaffold` in `paper_assets_manifest.json`.

To export only the ablation table:

```bash
python -m causal_agent_bench export-ablation-table --run-dir results/<run_dir>
```

Run-local exports also write `results/<run_dir>/paper_assets/asset_metadata.json`.

Do not manually edit generated tables or figures for claimed results. If a presentation-only edit is needed later, keep the raw generated asset and document the edit.
