# Model / Provider Selection Rationale

**Status:** Planning document only — **no final model list committed**  
**Rule:** Model IDs come from env vars (`OPENAI_MODEL_ID`, etc.) — use **categories** until Stage C locks choices.

---

## Why multiple models are required

A single model result is **insufficient** for NeurIPS-level claims because:

- C1/C2 require cross-model degradation patterns, not one-off behavior
- C4 requires ranking comparison across ≥5 agents
- Provider diversity controls API-specific artifacts
- Budget vs frontier gap tests whether robustness conclusions generalize

**Minimum for headline claims (Stage F):** ≥5 model families across ≥3 provider categories.

---

## Model categories (placeholders)

| Category | Role | Example slot (env-driven) |
|----------|------|---------------------------|
| **Frontier proprietary** | Strongest API models | `OPENAI_MODEL_ID`, `ANTHROPIC_MODEL_ID` |
| **Mid-tier proprietary** | Cost-performance tradeoff | Second env slot per provider |
| **Budget / small API** | Robustness at lower cost | OpenRouter budget route |
| **Open-weight local** | Repro without paid API | `OPENAI_COMPATIBLE_*` + Ollama |
| **Deterministic baselines** | Sanity bounds | scripted oracle (excluded from rankings) |

**Do not** name specific version strings (e.g. gpt-4.x) as final until configs + env are locked pre-Stage C.

---

## Provider diversity

| Provider type | Purpose | Risk |
|---------------|---------|------|
| Direct API (category A) | Primary frontier | Version drift |
| Direct API (category B) | Second frontier family | Rate limits |
| Aggregator (OpenRouter) | Budget + diversity | Routing opacity |
| OpenAI-compatible local | Free reproduction path | Hardware variance |

Configs: `configs/providers.yaml`, `configs/pilot_multi_provider_20.yaml`

---

## Cost control

- Stage B cap: ≤$5 (`provider_pilot_tiny_template`)
- `estimate-run-cost` before every approval
- `allow_paid_calls: false` default
- `model_pricing.yaml` for upper-bound estimates
- Interrupt/resume for long runs

---

## Risk factors

| Risk | Mitigation |
|------|------------|
| Rate limits | Stagger providers · retry policy in runner |
| API versioning | Pin model IDs + timestamp in `run_metadata.json` |
| Reproducibility | Log temperature, seed, config_hash, scorer version |
| Cost overrun | Budget approval form · trajectory caps |
| Contamination | Hidden test split · no tuning on test |

---

## NeurIPS minimum model set (planned)

| Stage | Min models | Min providers |
|-------|-----------|---------------|
| B (tiny) | 1 | 1 |
| C (pilot 20) | 2–3 | 2 |
| D (100) | 3 | 2 |
| F (main 500) | **≥5** | **≥3** |

---

## Excluded from scientific rankings

- `scripted_oracle_agent` — upper bound sanity only
- Mock/stub agents — engineering only
- Interrupted/incomplete runs

See `docs/LEADERBOARD_PROTOCOL.md`, `experiments/NEURIPS_EXPERIMENT_MATRIX.md`.
