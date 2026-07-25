# Security and Privacy

**Release:** `0.1.0-rc1`  
**Preflight:** `python3 scripts/security_check.py` · `make security-check`

## Intended use

This document describes how CausalAgentBench avoids leaking secrets, using private data, and performing unsafe real-world actions in the default configuration.

## API keys and secrets

- Provider keys are read from **environment variables only** (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.).
- Copy `.env.example` to `.env` locally; **never commit** `.env`.
- YAML configs must not contain inline API keys; `validate-config` flags secret-like keys.
- Run metadata and trajectories are passed through redaction helpers (`src/causal_agent_bench/runners/redaction.py`) before persistence.
- The runner logs whether keys are configured; it does **not** print or save key values.

```bash
cp .env.example .env   # edit locally; .env is gitignored
python3 scripts/security_check.py
```

## Simulated tools (default environment)

| Tool | Behavior | Real-world effect |
|------|----------|-------------------|
| `send_email_draft` | Creates a deterministic draft id | **No email sent** (`sent: false`) |
| `book_stub` | Returns a synthetic booking reference | **No reservation made** |
| `search_database`, `read_file`, etc. | Reads mock in-memory / JSON data | No external services |
| `web_*` (optional web shadow) | Reads frozen static snapshot JSON | **No live HTTP** in default benchmark run |

Implementation reference: `src/causal_agent_bench/tools/mock_tools.py`, `src/causal_agent_bench/tools/web_snapshot.py`.

## No live web by default

- Standard configs do not enable live browsing.
- Optional web-shadow study uses `data/web_shadow/acme_site.json` only.
- Do not wire real browser automation into the default scorer without a separate safety review.

## Synthetic data policy

- Tasks use fictional `@example.com` addresses and mock artifacts.
- Do not add customer records, private email, or proprietary documents to public dataset splits.
- Human-validation exports require protocol compliance (`docs/HUMAN_VALIDATION_PROTOCOL.md`).

## What to gitignore

See `.gitignore`. In particular:

- `.env` and local secrets
- `results/` run outputs (may contain raw model text — treat as sensitive if real APIs were used)
- `results/cache/` LLM response caches
- Private drops under `data/raw/private/`

## Provider-backed runs

Commercial API configs require explicit opt-in (`allow_paid_calls: true`). Estimate cost before running:

```bash
python3 -m causal_agent_bench estimate-cost --config configs/pilot_openai_20.yaml
```

See `docs/COMMERCIAL_API_RUNS.md` and `docs/COST_LATENCY.md`.

## Reporting vulnerabilities

If you discover a secret committed to the repository or a path that sends real email/bookings, open a private security report to the maintainers and rotate any exposed credentials immediately.

## License

- **Code:** MIT (`LICENSE`)
- **Synthetic data:** MIT (`DATA_LICENSE.md`)
- **Citation:** `CITATION.cff`
