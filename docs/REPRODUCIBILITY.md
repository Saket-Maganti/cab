# Reproducibility (low-compute)

## Safe setup

Prefer **`python3`** for all commands (local `python` may be broken under pyenv).

```bash
python3 -m pip install -e ".[dev]"
python3 -m causal_agent_bench doctor
python3 -m causal_agent_bench reproducibility-report
```

The environment report is written to `reports/reproducibility_environment_report.md` (no package installs, no API calls).

## Safe validation

```bash
python3 -m pytest tests/test_safety_reports.py -q
python3 -m causal_agent_bench all-safety-reports
```

## Artifact reproduction

Engineering smoke paths are documented in `artifact/scripts/reproduce_deterministic.sh`. Full provider reproduction requires API keys and is **not** implied by local stub/mock outputs.

## Lockfiles

If no lockfile is present, pin dependencies in your environment before large runs. See `reports/reproducibility_environment_report.json` for detected lockfiles and README `python` vs `python3` usage.

## Static no-run bundle

For reproducibility review without model execution, use:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_run_build_reports
```

This bundle is reproducible as static file inspection. It does not reproduce provider behavior, human annotations, or empirical paper results.
## Advanced No-Run Provenance

The benchmark manifest records static provenance before provider spend:

```bash
python3 -m causal_agent_bench benchmark-manifest --output-dir reports/benchmark_manifest
```

It captures git branch/commit when available, dirty-tree count, data/config
paths, dataset versions, frozen split manifests, run index summary, evidence
state, claim state, provider-preflight status, no-run report timestamps, Python
version, package version, lockfile status, and license/doc presence.

Release hygiene:

- Dirty tree is a release blocker or must be explicitly documented.
- Missing commit hash is a warning.
- Missing lockfile is a warning.
- No provider evidence blocks empirical paper readiness.

For a full static refresh:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_advanced_upgrade_reports
```

This command remains no-run only. It must not run benchmarks, call providers,
call local LLMs, use API keys, promote claims, or mutate run outputs.
