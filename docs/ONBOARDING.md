# Onboarding Guide

For new contributors, co-authors, and advisors reviewing the repository.

Start with [CURRENT_PROJECT_STATE.md](https://github.com/Saket-Maganti/cab/blob/main/CURRENT_PROJECT_STATE.md). It
supersedes historical generated status and next-step documents.

## 1. Setup

```bash
git clone <repo>
cd causal-agent-bench
pip install -e ".[dev]"
# or: export PYTHONPATH=src
cp .env.example .env   # never commit .env
```

Requires **Python 3.11+**.

## 2. Fast checks

```bash
make fast-check          # ~40s, no model runs
make precommit           # claim ledger, evidence safety, paper lint
cab pre-run scientific-check  # frozen pre-run design gate
```

## 3. Safe commands (no experiments)

```bash
python3 -m causal_agent_bench --help
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
python3 scripts/check_submission_readiness.py
python3 scripts/lint_paper_claims.py --mode draft
```

## 4. What NOT to run (without approval)

- `run --config` with Ollama/local/paid providers
- `allow_paid_calls: true`
- Scoring/exporting **interrupted** runs as scientific evidence
- Filling paper placeholders [N], [M], [K], [X], [rho]
- Any v1 Scale, Main-500, `naturalistic_ministudy`, or unapproved v2 scientific path
- Populating review rows with proxy, synthetic, or AI judgments

## 5. Evidence levels

Read [EVIDENCE_LEVEL_POLICY.md](EVIDENCE_LEVEL_POLICY.md). Summary:

| Level | Paper claims? |
|---|---|
| stub / mock / dry-run | No |
| local preliminary | Limitations only |
| provider pilot | Pilot wording only |
| main + human validated | Per claim ledger |

## 6. Inspect a run

```bash
python3 -m causal_agent_bench run-status --run-dir results/<dir>
python3 scripts/check_experiment_state.py --run-dir results/<dir>
python3 -m causal_agent_bench generate-report --run-dir results/<dir>
```

Check `evidence_scope` in `run_metadata.json`.

## 7. Inspect claims

```bash
python3 scripts/check_claim_ledger.py --mode draft
```

See [paper/EVIDENCE_GAP_MAP.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/paper/EVIDENCE_GAP_MAP.md).

## 8. Add a task template

1. Edit [benchmark_specs/task_template_registry.json](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/benchmark_specs/task_template_registry.json)
2. Update [benchmark_specs/TASK_TEMPLATE_REGISTRY.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/benchmark_specs/TASK_TEMPLATE_REGISTRY.md)
3. Regenerate dataset if needed (generation config)

## 9. Add an intervention

1. Follow family guide in [INTERVENTIONS.md](INTERVENTIONS.md)
2. Run `audit-interventions` + `audit_intervention_isolation.py`
3. Document in [BENCHMARK_TAXONOMY.md](BENCHMARK_TAXONOMY.md) if new family

## 10. Add a metric

1. Implement in `src/causal_agent_bench/metrics/`
2. Wire in `scoring.py`
3. Document in [METRICS.md](METRICS.md)
4. Add mock diagnostic expectation test if applicable

## 11. Add documentation

1. Place in `docs/` and link from [docs/index.md](index.md)
2. For paper-facing docs, update [paper/PAPER_TASK_BOARD.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/paper/PAPER_TASK_BOARD.md)

## 12. Avoid overclaiming

- Update claim ledger status only with linked run dirs + artifacts
- Run `lint_paper_claims.py` before PR
- Mock/stub = **engineering_only / not_real_llm_behavior**

## Next steps

The only current scientific next action is to recruit and onboard two genuine
qualified independent Compact-20 reviewers using the regenerated v2 packet,
plus a separate adjudicator. Do not start model execution first.

- [REPO_MAP.md](REPO_MAP.md)
- [GLOSSARY.md](GLOSSARY.md)
- [handoff/ADVISOR_DEMO_SCRIPT.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/handoff/ADVISOR_DEMO_SCRIPT.md)
- [CONTRIBUTING.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/CONTRIBUTING.md)
