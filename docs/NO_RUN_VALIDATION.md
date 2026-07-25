# Strict no-run validation lane

Use this lane before merge or before any paid provider / full benchmark run. It verifies evidence governance, claim safety, and CLI wiring **without** starting local experiments or calling external APIs.

## Safe commands

```bash
# Core pytest lane (no local experiment startup)
python3 -m pytest tests/test_safety_reports.py tests/test_cli.py tests/test_claim_ledger.py tests/test_provider_pilot_readiness.py -q

# Evidence governance scripts / CLI (read-only on repo artifacts)
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench run-health --output-dir /tmp/cab_reports
python3 -m causal_agent_bench validate-paper-assets --output-dir /tmp/cab_reports
python3 -m causal_agent_bench claim-evidence --no-tex --output-dir /tmp/cab_reports
python3 -m causal_agent_bench paper-todo-inventory --output-dir /tmp/cab_reports

# Compile changed modules after edits
python3 -m py_compile src/causal_agent_bench/claim_ledger.py src/causal_agent_bench/cli.py
```

## Marker lane warning

The broad marker expression is **not currently sufficient** for strict no-run validation. Do **not** treat either of these as approved no-run commands:

```bash
python3 -m pytest tests/ -m "not integration and not local_run" -q
python3 -m pytest --collect-only -m "not integration and not local_run"
```

Those commands still select tests that can start local experiments. The broad marker lane may become safe later only after every run-starting test is marked and audited. Until then, only the explicit named-file pytest command above is approved for strict no-run validation.

## Unsafe for this lane (do not run in CI pre-merge checks)

| Command / test | Why |
|----------------|-----|
| `python3 -m causal_agent_bench run --config ...` | Starts a benchmark run |
| `make smoke` / `make test` | May invoke full or run-starting tests |
| `run-llm-judge` | Provider / model calls |
| `tests/test_paper_assets.py` | Calls `run_experiment(...)` (marked `integration`, `local_run`) |
| `tests/test_paper_fill.py` | Calls `run_experiment(...)` (marked `integration`, `local_run`) |
| Any provider / commercial API pilot | Paid or external inference |
| Long local model jobs | Non-deterministic, costly |

## Known unsafe or unmarked run-starting tests

Do not include these in strict no-run validation until they are marked/refactored and audited:

- `tests/test_paper_assets.py`
- `tests/test_paper_fill.py`
- `tests/test_experiment_runner.py`
- `tests/test_analysis_assets.py`
- `tests/test_build_phase2.py`
- `tests/test_build_phase3.py`
- `tests/test_batch_runner.py`
- `tests/test_run_management.py`
- `tests/test_leaderboard.py`
- `tests/test_trajectory_v2.py`
- `tests/test_io_repro_cli.py`
- `tests/test_reproduce_artifact.py`

## Claim ledger safety

- **Verified promotion:** `update-claim-ledger --run-dir … --promote-to-supported` uses strict run classification and per-claim artifact eligibility.
- **Manual supported:** `--status supported` requires the same eligibility unless `--force-manual-supported` is passed (adds a visible ledger warning; not for paper claims).

## Test markers

- `@pytest.mark.integration` — may exercise multi-step local flows.
- `@pytest.mark.local_run` — calls `run_experiment` and writes trajectories under a temp directory.

Run integration tests only when you intend to start local experiments:

```bash
python3 -m pytest tests/test_paper_assets.py tests/test_paper_fill.py -m integration -q
```

## Before provider pilot

Use this lane until advisor approval in `docs/PROVIDER_PILOT_READINESS_PACKET.md`.

### Safe (preparation only)

```bash
python3 -m pytest tests/test_safety_reports.py tests/test_cli.py tests/test_claim_ledger.py tests/test_provider_pilot_readiness.py -q
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench dry-run --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench estimate-cost --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench run-health --output-dir /tmp/cab_reports
```

Read (no commands):

- `docs/PROVIDER_PILOT_READINESS_PACKET.md`
- `docs/PROVIDER_PILOT_METADATA_REQUIREMENTS.md`
- `docs/POST_PROVIDER_PILOT_CHECKLIST.md`
- `configs/provider_pilot_tiny_template.yaml` (template only — copy before editing)

### Forbidden before approval

| Command / action | Why |
|------------------|-----|
| `python3 -m causal_agent_bench run --config configs/provider_pilot_tiny_template.yaml` | Template is not approved |
| `python3 -m causal_agent_bench run --config …` (any live provider config) | Starts paid/local inference |
| `update-claim-ledger --promote-to-supported` | No verified evidence yet |
| `fill-paper-from-run --promote-to-supported` | Paper overclaim |
| `make smoke` / `make test` | May start runs |
| `run-llm-judge` | API calls |
| `tests/test_paper_assets.py` / `tests/test_paper_fill.py` | `run_experiment(...)` |

After approval, follow `docs/POST_PROVIDER_PILOT_CHECKLIST.md` — still no claim promotion until metadata and artifacts pass.

## Benchmark-strengthening reports

The next no-run lane adds static reports that strengthen benchmark governance without executing agents:

```bash
python3 -m causal_agent_bench benchmark-quality --output-dir /tmp/cab_no_run_build_reports
python3 -m causal_agent_bench intervention-isolation-audit --output-dir /tmp/cab_no_run_build_reports
python3 -m causal_agent_bench synthetic-fixture-check --output-dir /tmp/cab_no_run_build_reports
python3 -m causal_agent_bench human-validation-packet --output-dir /tmp/cab_no_run_build_reports
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_template.yaml --output-dir /tmp/cab_no_run_build_reports
python3 -m causal_agent_bench method-figure-scaffolds --output-dir figures/method
python3 -m causal_agent_bench release-readiness --output-dir /tmp/cab_no_run_build_reports
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_run_build_reports
```

These commands inspect static files, templates, fixtures, and metadata only. They do not promote claims, create eligible paper assets, call providers, or run local models.

## Extended no-run upgrade reports

```bash
python3 -m causal_agent_bench dataset-issue-triage --output-dir /tmp/cab_upgrade_reports
python3 -m causal_agent_bench provider-pilot-preflight --config configs/provider_pilot_tiny_template.yaml --output-dir /tmp/cab_upgrade_reports
python3 -m causal_agent_bench human-validation-dry-run-sample --output-dir /tmp/cab_upgrade_reports/human_validation_dry_run
python3 -m causal_agent_bench method-appendix --output-dir /tmp/cab_upgrade_reports/method_appendix
python3 -m causal_agent_bench evidence-dashboard --reports-dir /tmp/cab_upgrade_reports --output-dir /tmp/cab_upgrade_reports/evidence_dashboard
python3 -m causal_agent_bench lint-config-metadata --output-dir /tmp/cab_upgrade_reports
```

See `docs/NO_RUN_REPORTS_GUIDE.md` for what each report can and cannot prove.
