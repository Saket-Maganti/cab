# Benchmark Artifact Manifest

**Benchmark ID:** `causal-agent-bench`  
**Version:** `0.1.0-dev`  
**Status:** `research_scaffold` / `infrastructure_artifact_candidate`  
**Machine-readable:** [release/benchmark_artifact_manifest.json](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/release/benchmark_artifact_manifest.json)

---

## Versioning

| Component | Version / ID |
|-----------|--------------|
| Package | `0.1.0` (`pyproject.toml`) |
| Release ID | `causal-agent-bench-0.1.0` |
| Default frozen dataset | `pilot_v0.1` → `data/frozen/pilot_v0.1` |
| Split policy | `release_disjoint_v1` |
| Claim ledger schema | v2 |
| Scorer (declared) | `deterministic_heuristic_v1` |

## Dataset versions

| Bundle | Path | Status |
|--------|------|--------|
| `pilot_v0.1` (frozen) | `data/frozen/pilot_v0.1/` | **Release-ready (pilot scale)** |
| `pilot_v0_1` (processed) | `data/processed/pilot_v0_1/` | Regenerable; not release authority |
| `main_200` | configs only | **Blocked** — not frozen |
| `main_v0.1_500` | configs only | **Blocked** — not frozen |

## Config profiles

| Profile | Config | Runnable without approval? | Paper-eligible? |
|---------|--------|---------------------------|-----------------|
| Smoke / stub | `configs/smoke.yaml`, `configs/pilot_stub_*.yaml` | Engineering only — **not for artifact review default** | No |
| Mock diagnostic | `configs/pilot_mock_diagnostic_micro.yaml` | Engineering only | No |
| Provider tiny template | `configs/provider_pilot_tiny_template.yaml` | **No** — template only | No (until post-run audit) |
| Provider APPROVED | `configs/provider_pilot_tiny_APPROVED.yaml` | **No** — must not exist without signed forms | Pending post-run |
| Main 500 | `configs/commercial_api_main_500.yaml` | **No** — paid, blocked | No |

## Evidence state (2026-06-10)

```text
paper_eligible_runs:          0
eligible_empirical_assets:    0
provider_gate:                template_safe_but_not_runnable
leakage_blocker_clusters:     0
approved_provider_config:     false (must remain false without signed docs)
claims C1-C8, C10:            planned / unsupported
claim C9:                     engineering_only
public_release:               blocked
run_index:                    may be stale (refresh: index-runs)
```

## Expected reproduction modes

### Static-only reproduction (Tier 0–1)

Inspect docs, claim ledger, no-run reports. **No Python execution required** beyond optional report regeneration.

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_static
python3 scripts/check_evidence_safety.py
```

**Evidence value:** Infrastructure, governance, dataset design. **Cannot support paper empirical claims.**

### Stub / mock engineering reproduction (Tier 2)

Deterministic smoke and mock diagnostic paths validate pipeline wiring only.

**Not listed as default artifact-review commands.** If run, outputs are `engineering_only` / `mock_diagnostic_only`.

**Evidence value:** C9 (reproducibility scaffolding). **Cannot support C1–C8 or C10.**

### Provider-required reproduction (Tier 3–4)

Requires API keys, signed approval forms, copy of template → `*_APPROVED.yaml`, `allow_paid_calls: true` after budget sign-off.

```bash
# NOT RUNNABLE in current repo state without approval:
# python3 -m causal_agent_bench run --config configs/provider_pilot_tiny_APPROVED.yaml
```

**Evidence value:** Required for C1–C8 empirical claims. **Currently blocked.**

### Human-validation required assets (Tier 5)

| Asset | Status |
|-------|--------|
| `configs/human_validation_sample.yaml` | Template ready |
| `data/human_validation/completed_*` | **Missing** |
| `tables/table5_human_validation_agreement.csv` | Placeholder |
| C3, C10 claim promotion | **Blocked** |

## Blocked assets

- All `tables/table2_*` performance tables (engineering_only / placeholder)
- All results figures with `placeholder: true`
- `paper/latexpaper/generated/07_results.tex` empirical insertions
- Leaderboard exports from non-eligible runs
- `configs/*_APPROVED.yaml` (must not be auto-created)
- Public Zenodo/HF dataset bundle

## Safe commands (artifact review)

```bash
python3 scripts/check_evidence_safety.py
python3 scripts/check_run_index.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_reports
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_template.yaml
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_template.yaml --output-dir /tmp/cab_cost
python3 -m causal_agent_bench benchmark-manifest --output-dir reports/benchmark_manifest
python3 scripts/check_claim_ledger.py --mode draft
python3 -m py_compile <changed_python_files>
```

Targeted fixture-only pytest (examples):

```bash
python3 -m pytest tests/test_neurips_artifact_upgrade.py -q
python3 -m pytest tests/test_safety_reports.py -q -k "claim_evidence"
```

## Forbidden commands (without explicit approval)

```bash
python3 -m causal_agent_bench run --config configs/pilot_openai_20.yaml
python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench run --config configs/commercial_api_main_500.yaml
python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml
python3 -m causal_agent_bench fill-paper-from-run   # without verified pilot
make smoke
make test   # broad lane — may trigger runs
```

Also forbidden:

- Setting `allow_paid_calls: true` without signed budget approval
- Auto-creating `*_APPROVED.yaml`
- Mutating `results/` metadata to mark eligibility
- Promoting claim ledger rows without post-run audit
- Editing frozen data without documented repair workflow

---

See also: [GOD_TIER_MANIFEST.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/GOD_TIER_MANIFEST.md), [docs/REPRODUCIBILITY_TIERS.md](REPRODUCIBILITY_TIERS.md), [docs/REVIEWER_QUICKSTART_NEURIPS.md](REVIEWER_QUICKSTART_NEURIPS.md).
