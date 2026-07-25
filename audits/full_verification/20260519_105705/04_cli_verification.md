# 04 CLI Verification

| Command | Status | Output summary | Mismatch or fix |
|---|---|---|---|
| `python3 -m causal_agent_bench --help` | pass | Listed expected benchmark, scoring, analysis, provider, validation, and export subcommands. | none |
| `python3 -m causal_agent_bench doctor` | pass | Environment and sample data checks passed; paid-provider keys absent. | none |
| `python3 -m causal_agent_bench list-providers` | pass | `local_stub` configured; `local_openai` configured; OpenAI/Anthropic/Gemini/OpenRouter not configured. | provider runs blocked until configured |
| `python3 -m causal_agent_bench validate data/sample/instances.jsonl --schema instances` | pass | 9 instance records valid, 0 invalid. | none |
| `python3 -m causal_agent_bench validate-config --config configs/smoke.yaml` | pass | Valid local experiment config; includes oracle sanity-check agent. | oracle must not be used for model ranking |
| `python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir audits/full_verification/20260519_105705/dry_runs` | pass | Dry-run planned 360 trajectories with provider validation only; no API keys printed. | provider config not ready |
| `python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml` | pass | Cost upper bound unknown because model IDs/pricing are missing. | paid run blocked |

README commands broadly match the CLI surface, but provider examples must remain marked as setup-dependent until real model IDs, keys, and pricing are present.

