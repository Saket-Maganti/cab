# Web shadow study (static snapshot, no live browsing)

Optional external-validity probe that compares **simulated API tools** against **static web snapshot tools** on the same underlying facts. The environment never opens a live network connection during benchmark execution.

## What is included

- Frozen site bundle: `data/web_shadow/acme_site.json` (also built from `web_shadow_site.py`)
- Web snapshot tools: `web_open_page`, `web_follow_link`, `web_search_snapshot`, `web_extract_section`
- 25 navigation scenarios × 2 interfaces = 50 base tasks (`task_style: web_shadow`)
- Web-specific interventions (one patch group each):
  - `web_broken_link`
  - `web_stale_page`
  - `web_conflicting_page`
  - `web_irrelevant_search_result`
  - `web_hidden_evidence`
- API-interface tasks use mirrored standard interventions (`tool_failure`, `tool_corruption`, etc.)

## Generate dataset

```bash
python -m causal_agent_bench.cli generate --config configs/generate_web_shadow_25.yaml
```

## Stub smoke runs (engineering only)

```bash
python -m causal_agent_bench.cli run --config configs/web_shadow_api_stub.yaml
python -m causal_agent_bench.cli run --config configs/web_shadow_web_stub.yaml
```

## Compare interfaces

```bash
python -m causal_agent_bench.cli compare-web-shadow \
  --api-run-dir runs/web_shadow_api_stub \
  --web-run-dir runs/web_shadow_web_stub \
  --output-dir analysis/web_shadow_comparison
```

Outputs `web_shadow_comparison.json` and `web_shadow_comparison.md`.

## Limits (read before citing)

- **No live web**: All pages and search results are static; there is no HTML/JS rendering, authentication, CAPTCHA, or network drift.
- **Synthetic site**: The Acme snapshot is fictional; patterns may not transfer to real product, legal, or support sites.
- **Stub runs are not science**: Deterministic stub/smoke trajectories are scaffolding only until validated model runs and human review exist.
- **Interventions are analogous, not identical**: API tasks use standard tool interventions; web tasks use navigation-specific families. Compare degradation patterns, not byte-for-byte parity.
- **No private data**: Do not point this machinery at private or authenticated pages.

## Scoring

Uses the standard deterministic scorer (`deterministic_heuristic_v1`) on trajectories. Recovery and contradiction metrics apply when interventions surface tool errors or conflicting page payloads.

## Reproducibility fields

Each task records `web_site_id`, `web_site_frozen_at`, `tool_interface`, `scenario_key`, and generator seed in `metadata`. Tie run directories to `configs/*.yaml`, git commit, and `run_metadata.json`.
