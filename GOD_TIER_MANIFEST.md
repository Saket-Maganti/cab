# God-Tier Manifest — Causal Agent Bench

**What “god tier” means here:** world-class **benchmark infrastructure + evidence governance**, not fabricated empirical results.

## Legendary strengths (built)

| Layer | Status |
|-------|--------|
| Paired clean/intervention benchmark design | Strong |
| 80+ CLI subcommands | Strong |
| Claim ledger + export guards | Strong |
| No-run report bundle (`all-no-run-reports`) | Strong |
| Provider-pilot safety template + preflight gates | Strong |
| Advisor / paper / release readiness packets | Strong |
| Answer-leakage calibration + repair tooling | Strong |
| Fixture-only test lanes for governance | Strong |

## Honest limits (by design)

| Layer | Status |
|-------|--------|
| Paper-eligible provider runs | **0** |
| Eligible empirical paper assets | **0** |
| C1–C8 / C10 empirical claims | **Unsupported** |
| Live provider pilot | **Blocked until advisor + APPROVED config** |
| Public v1.0 release | **Blocked** |

## One-command status

```bash
python3 scripts/god_tier_status.py
python3 scripts/god_tier_status.py --json
make god-tier-status
```

## Full governance bundle

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_god_tier
python3 scripts/check_evidence_safety.py
python3 scripts/check_run_index.py
```

## NeurIPS artifact bundle (2026-06-10)

| Doc | Purpose |
|-----|---------|
| [docs/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md](docs/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md) | Full artifact checklist |
| [docs/NEURIPS_CONTRIBUTION_MAP.md](docs/NEURIPS_CONTRIBUTION_MAP.md) | Ready vs blocked contributions |
| [docs/BENCHMARK_ARTIFACT_MANIFEST.md](docs/BENCHMARK_ARTIFACT_MANIFEST.md) | Versions, modes, safe/forbidden commands |
| [release/benchmark_artifact_manifest.json](release/benchmark_artifact_manifest.json) | Machine-readable manifest |
| [docs/REVIEWER_QUICKSTART_NEURIPS.md](docs/REVIEWER_QUICKSTART_NEURIPS.md) | 5/15/30-min reviewer paths |
| [docs/REPRODUCIBILITY_TIERS.md](docs/REPRODUCIBILITY_TIERS.md) | Tier 0–5 reproduction ladder |
| [docs/DATASET_RELEASE_READINESS.md](docs/DATASET_RELEASE_READINESS.md) | Frozen vs processed, release blockers |
| [docs/NEURIPS_SELF_REVIEW_RUBRIC.md](docs/NEURIPS_SELF_REVIEW_RUBRIC.md) | Conservative self-audit scores |

**Classification:** `infrastructure_artifact_candidate` — not empirical-results-ready.

## Key documents

| Doc | Purpose |
|-----|---------|
| [PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md](PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md) | Full audit dossier |
| [PROVIDER_PILOT_PREPARATION_STATUS.md](PROVIDER_PILOT_PREPARATION_STATUS.md) | Provider prep state |
| [docs/COMMAND_AND_RUNTIME_GUIDE.md](docs/COMMAND_AND_RUNTIME_GUIDE.md) | Safe vs unsafe commands |
| [docs/NO_RUN_REPORTS_GUIDE.md](docs/NO_RUN_REPORTS_GUIDE.md) | Report bundle guide |
| [reports/INDEX.md](reports/INDEX.md) | Report catalog |
| [handoff/ADVISOR_REVIEW_BUNDLE_INDEX.md](handoff/ADVISOR_REVIEW_BUNDLE_INDEX.md) | Advisor share pack |

## Path to legendary *empirical* benchmark (not done yet)

1. Advisor approval + `provider_pilot_tiny_APPROVED.yaml`
2. Dry-run → tiny live pilot → post-run audit
3. Human validation for C3/C10
4. Main-benchmark split hardening (main_200 / main_v0_1_500)
5. Claim promotion only per claim-evidence matrix

**Never skip evidence gates.**
