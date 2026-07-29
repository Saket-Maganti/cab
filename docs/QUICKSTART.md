# Quickstart

Minimal reviewer path for CausalAgentBench. Full detail: [artifact/README.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/artifact/README.md).

## 1. Install

```bash
python3 -m pip install -e ".[dev]"
python3 scripts/reproduce_artifact.py --check
```

Requires **Python 3.11+**.

## 2. Smoke run

```bash
python3 scripts/reproduce_artifact.py --step smoke
# or: make smoke
```

Uses `configs/smoke.yaml` and `data/sample/instances.jsonl` (no API keys).

## 3. Reproduce small pilot

```bash
python3 scripts/reproduce_artifact.py --step pilot-stub
```

Uses `configs/pilot_20_multi_agent.yaml` with `provider: local_stub` on 20 pilot instances.

## 4. Reproduce one table

```bash
python3 scripts/reproduce_artifact.py --step table2
# writes tables/table2_main_agent_performance.csv
```

## 5. Reproduce one figure

```bash
python3 scripts/reproduce_artifact.py --step figure2
# writes figures/figure2_clean_vs_intervention_success.png
```

## All-in-one (API-free)

```bash
python3 scripts/reproduce_artifact.py --all-deterministic
# or: bash artifact/scripts/reproduce_deterministic.sh
```

## Optional: API-backed pilot

```bash
export OPENAI_API_KEY=...
export OPENAI_MODEL_ID=...
python3 scripts/reproduce_artifact.py --step api-preflight
# optional paid run:
RUN_API_PILOT=1 bash artifact/scripts/reproduce_api_optional.sh
```

## Troubleshooting

See [artifact/TROUBLESHOOTING.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/artifact/TROUBLESHOOTING.md).

## What this does *not* prove

Smoke and stub pilots are **engineering checks** only. Paper claims require verified non-oracle LLM runs, human validation, and claim-ledger updates — see [docs/claim_ledger.json](claim_ledger.json).
