# Notebooks

Notebook work is optional. The canonical analysis path is the deterministic Python package code:

```bash
python -m causal_agent_bench analyze --run-dir results/<run_dir>
python -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

Use notebooks only for exploratory inspection. Any figure or table used in the paper should be promoted into `src/causal_agent_bench/analysis/` or `scripts/make_paper_assets.py` so it can be reproduced without manual notebook state.
