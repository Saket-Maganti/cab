# Artifact Evaluation Package

Reviewer-oriented reproduction paths for **CausalAgentBench**. This package documents how to verify the benchmark pipeline without requiring paid API access for the default path.

**Important:** Stub and smoke runs are **engineering-only**. They validate schemas, scoring, tables, and figures. They are **not** final scientific evidence for the paper (`evidence_scope: pilot_stub_engineering_only`).

## Quickstart (5 commands)

From the repository root:

```bash
# 1. Install
python3 -m pip install -e ".[dev]"

# 2. Smoke run (sample instances, deterministic agents)
python3 scripts/reproduce_artifact.py --step smoke

# 3. Small pilot (20 tasks, local_stub LLM — no API keys)
python3 scripts/reproduce_artifact.py --step pilot-stub

# 4. Reproduce Table 2 (uses latest pilot-stub run dir)
python3 scripts/reproduce_artifact.py --step table2

# 5. Reproduce Figure 2
python3 scripts/reproduce_artifact.py --step figure2
```

Or run the full deterministic path:

```bash
python3 scripts/reproduce_artifact.py --all-deterministic
```

Preflight only:

```bash
python3 scripts/reproduce_artifact.py --check
python3 scripts/reproduce_artifact.py --list-steps
```

## Expected runtime

| Step | Approx. time | API keys |
|------|----------------|----------|
| `install` | 1–3 min | No |
| `smoke` | < 1 min | No |
| `pilot-stub` | 1–5 min | No |
| `table2` / `figure2` | < 1 min each | No |
| `api-preflight` | < 1 min | Optional (estimate only) |
| `api-pilot` | 10–60+ min | **Yes** (paid) |

Times vary by CPU and disk; first matplotlib import may add ~10–30s.

## Hardware requirements

- **CPU:** 2+ cores recommended; runs are single-machine and mostly CPU-bound.
- **RAM:** 4 GB minimum; 8 GB comfortable for pilot-stub + figure export.
- **Disk:** ~500 MB for install + generated `results/` artifacts.
- **GPU:** Not required (default agents are deterministic or `local_stub`).
- **Network:** Not required for the deterministic path; required for optional API pilots.

## Path A — API-free (deterministic / stub)

**Goal:** Reproduce pipeline mechanics end-to-end without paid providers.

| Step | Config | Output |
|------|--------|--------|
| Smoke | `configs/smoke.yaml` | `results/<timestamp>_smoke/` |
| Pilot stub | `configs/pilot_20_multi_agent.yaml` | `results/<timestamp>_pilot_20_multi_agent_stub/` |
| Table 2 | export from run dir | `tables/table2_main_agent_performance.csv` |
| Figure 2 | export from run dir | `figures/figure2_clean_vs_intervention_success.png` |

Each run directory should contain:

- `run_metadata.json` — config hash, seed, git commit, evidence scope, scorer version
- `trajectories.jsonl`, `scores.jsonl`, `aggregate_scores.json`
- `artifact_manifest.json` (after `pilot-stub` via reproduce script)

**Oracle agents** (`scripted_oracle_agent`) are sanity-check upper bounds and are excluded from main leaderboard tables.

## Path B — API-backed (optional)

Only after Path A succeeds. Keys are read from the environment only (never written to disk).

```bash
export OPENAI_API_KEY=...          # example
export OPENAI_MODEL_ID=gpt-4o-mini # example

python3 scripts/reproduce_artifact.py --step api-preflight
python3 scripts/reproduce_artifact.py --step api-pilot
```

Commercial runs may require `allow_paid_calls: true` in config — see [docs/COMMERCIAL_API_RUNS.md](../docs/COMMERCIAL_API_RUNS.md).

Always run cost estimation before a paid pilot:

```bash
python3 -m causal_agent_bench estimate-cost --config configs/pilot_openai_20.yaml
```

## Exact commands (copy-paste)

See [scripts/reproduce_deterministic.sh](scripts/reproduce_deterministic.sh) and [scripts/reproduce_api_optional.sh](scripts/reproduce_api_optional.sh), or use:

```bash
make artifact-check          # prerequisites only
make artifact-smoke          # install + smoke
make artifact-deterministic  # full API-free path
```

## Linking results to the paper

After a **verified non-stub** run exists:

```bash
python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
python3 scripts/fill_paper_from_run.py --run-dir results/<run_dir>
python3 -m causal_agent_bench update-claim-ledger --run-dir results/<run_dir>
```

See [docs/PAPER_RESULTS_FILL.md](../docs/PAPER_RESULTS_FILL.md) and [docs/claim_ledger.json](../docs/claim_ledger.json).

## Related docs

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [docs/QUICKSTART.md](../docs/QUICKSTART.md)
- [docs/REPRODUCIBILITY.md](../docs/REPRODUCIBILITY.md)
- [docs/submission_checklist.md](../docs/submission_checklist.md)
