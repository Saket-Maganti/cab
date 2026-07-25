# Experiment Command Plans

Generated command blocks only — **never auto-executed**.

# Command plan: micro_stub

**Micro stub (engineering)**
- Config: `configs/pilot_stub_micro_3.yaml`
- Evidence level: `stub_engineering`
- Expected runtime: ~15s
- Expected cost: $0
- Approval needed: False

## preflight
```bash
make fast-check
python3 scripts/check_submission_readiness.py
python3 -m causal_agent_bench validate-config --config configs/pilot_stub_micro_3.yaml
python3 scripts/check_zero_cost_readiness.py --config configs/pilot_stub_micro_3.yaml --require zero_cost_ready
```

## plan_run
```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
```

## readiness
```bash
python3 scripts/check_submission_readiness.py
python3 scripts/check_claim_ledger.py --mode draft
```

## dry_run
```bash
python3 -m causal_agent_bench dry-run --config configs/pilot_stub_micro_3.yaml --output-dir results/dry_runs
```

## run
```bash
python3 -m causal_agent_bench run --config configs/pilot_stub_micro_3.yaml
```

## post_run
```bash
python3 -m causal_agent_bench run-status --latest
python3 -m causal_agent_bench generate-report --latest
python3 -m causal_agent_bench score --run-dir results/<run_dir>
python3 -m causal_agent_bench analyze --run-dir results/<run_dir>
python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

## audit
```bash
python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/pilot_v0.1
python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
```

## claim_ledger
```bash
python3 scripts/check_claim_ledger.py --mode draft
python3 scripts/check_evidence_safety.py
```

---

# Command plan: micro_local

**Micro local open-weight (preliminary)**
- Config: `configs/pilot_free_local_micro_3.yaml`
- Evidence level: `local_model_preliminary`
- Expected runtime: ~600s
- Expected cost: $0
- Approval needed: True

> **DO NOT RUN NOW without explicit approval — Ollama/local model calls.**

## preflight
```bash
make fast-check
python3 scripts/check_submission_readiness.py
python3 -m causal_agent_bench validate-config --config configs/pilot_free_local_micro_3.yaml
python3 scripts/check_zero_cost_readiness.py --config configs/pilot_free_local_micro_3.yaml --require zero_cost_ready
```

## plan_run
```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_free_local_micro_3.yaml
```

## readiness
```bash
python3 scripts/check_submission_readiness.py
python3 scripts/check_claim_ledger.py --mode draft
```

## dry_run
```bash
python3 -m causal_agent_bench dry-run --config configs/pilot_free_local_micro_3.yaml --output-dir results/dry_runs
```

## run
```bash
python3 -m causal_agent_bench run --config configs/pilot_free_local_micro_3.yaml
```

## post_run
```bash
python3 -m causal_agent_bench run-status --latest
python3 -m causal_agent_bench generate-report --latest
python3 -m causal_agent_bench score --run-dir results/<run_dir>
python3 -m causal_agent_bench analyze --run-dir results/<run_dir>
python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

## audit
```bash
python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/pilot_v0.1
python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
```

## claim_ledger
```bash
python3 scripts/check_claim_ledger.py --mode draft
python3 scripts/check_evidence_safety.py
```

---

# Command plan: provider_pilot

**Provider pilot (20 tasks)**
- Config: `configs/pilot_multi_provider_20.yaml`
- Evidence level: `provider_pilot`
- Expected runtime: ~3600s
- Expected cost: $25
- Approval needed: True

> **DO NOT RUN NOW — paid API calls require budget approval.**

## preflight
```bash
make fast-check
python3 scripts/check_submission_readiness.py
python3 -m causal_agent_bench validate-config --config configs/pilot_multi_provider_20.yaml
python3 scripts/check_zero_cost_readiness.py --config configs/pilot_multi_provider_20.yaml --require zero_cost_ready
```

## plan_run
```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_multi_provider_20.yaml
```

## readiness
```bash
python3 scripts/check_submission_readiness.py
python3 scripts/check_claim_ledger.py --mode draft
```

## dry_run
```bash
python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir results/dry_runs
```

## run
```bash
python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
```

## post_run
```bash
python3 -m causal_agent_bench run-status --latest
python3 -m causal_agent_bench generate-report --latest
python3 -m causal_agent_bench score --run-dir results/<run_dir>
python3 -m causal_agent_bench analyze --run-dir results/<run_dir>
python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

## audit
```bash
python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/pilot_v0.1
python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
```

## claim_ledger
```bash
python3 scripts/check_claim_ledger.py --mode draft
python3 scripts/check_evidence_safety.py
```

---

# Command plan: main_500

**Main 500-task experiment**
- Config: `configs/main_500_multi_provider.yaml`
- Evidence level: `main_experiment`
- Expected runtime: ~86400s
- Expected cost: $500
- Approval needed: True

> **DO NOT RUN NOW — main experiment gate must pass first.**

## preflight
```bash
make fast-check
python3 scripts/check_submission_readiness.py
python3 -m causal_agent_bench validate-config --config configs/main_500_multi_provider.yaml
python3 scripts/check_zero_cost_readiness.py --config configs/main_500_multi_provider.yaml --require zero_cost_ready
```

## plan_run
```bash
python3 -m causal_agent_bench plan-run --config configs/main_500_multi_provider.yaml
```

## readiness
```bash
python3 scripts/check_submission_readiness.py
python3 scripts/check_claim_ledger.py --mode draft
```

## dry_run
```bash
python3 -m causal_agent_bench dry-run --config configs/main_500_multi_provider.yaml --output-dir results/dry_runs
```

## run
```bash
python3 -m causal_agent_bench run --config configs/main_500_multi_provider.yaml
```

## post_run
```bash
python3 -m causal_agent_bench run-status --latest
python3 -m causal_agent_bench generate-report --latest
python3 -m causal_agent_bench score --run-dir results/<run_dir>
python3 -m causal_agent_bench analyze --run-dir results/<run_dir>
python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

## audit
```bash
python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/pilot_v0.1
python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
```

## claim_ledger
```bash
python3 scripts/check_claim_ledger.py --mode draft
python3 scripts/check_evidence_safety.py
```

---
