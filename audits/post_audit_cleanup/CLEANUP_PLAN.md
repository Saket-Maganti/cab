# Post-Audit Worktree Cleanup Plan

Generated: 2026-05-19 (Prompt 61)

## Repository snapshot

| Field | Value |
|---|---|
| **Current branch** | `main` |
| **HEAD** | `dea8e25` — Initialize CausalAgentBench research benchmark scaffold |
| **Dirty files** | 292 total (99 modified tracked, 193 untracked) |
| **Tracked diff** | 99 files, +8436 / −720 lines |
| **Audit verdict** | Deterministic prototype working; **not** provider-pilot ready; **not** submission ready |
| **Tests (2026-05-19)** | `244 passed, 1 skipped` in 71s |

## Worktree status summary

The worktree contains a large post-scaffold expansion: Phase-2 CLI, provider adapters, dataset generation/freeze, claim ledger, paper tooling, CI workflows, and a full verification audit. Almost all meaningful work is **uncommitted** on `main` atop a single initial scaffold commit.

Local run artifacts (`results/`, 149M, 18 run dirs) are correctly excluded by `.gitignore`. Benchmark data (`data/frozen/` 15M, `data/processed/` 69M) and audit reproduction copies (`audits/.../generation_repro/` 18M) are untracked and need explicit commit/ignore decisions.

---

## Dirty files grouped by type

### 1. Tracked code changes (modified `M`, 99 files)

**Core package (`src/causal_agent_bench/`, 31 modified + 30 untracked new modules)**

| Area | Modified | New (untracked) |
|---|---|---|
| Agents | `base.py`, `llm_adapters.py`, `llm_interfaces.py`, `registry.py`, `greedy_tool_agent.py`, `scripted_oracle_agent.py`, `__init__.py` | `llm_agents.py`, `llm_clients.py`, `tool_protocol.py` |
| Runners | `config.py`, `execution.py`, `experiment.py`, `metadata.py`, `resume.py`, `errors.py` | `batch.py`, `commercial.py`, `costing.py`, `evidence_scope.py`, `redaction.py` |
| Generation | `base_tasks.py`, `instances.py`, `interventions.py`, `quality_checks.py`, `templates.py` | `naturalistic.py`, `naturalistic_templates.py`, `web_shadow*.py` (4 files) |
| Analysis | `error_analysis.py`, `figures.py`, `load_results.py`, `report.py`, `tables.py` | `failure_gallery_doc.py`, `human_validation.py`, `leaderboard.py`, `llm_judge.py`, `mini_study.py`, `paper_assets.py`, `paper_fill.py`, `statistics.py`, `web_shadow_study.py` |
| Other | `cli.py`, `environment.py`, `schemas.py`, `scoring.py`, `validation.py`, `tools/simulated.py`, `metrics/recovery.py`, `metrics/statistics.py` | `ablation_matrix.py`, `claim_ledger.py`, `contamination/`, `doctor.py`, `metrics/v2.py`, `phase2.py`, `trajectory.py`, `tools/web_snapshot.py` |

**Tests (`tests/`, 6 modified + 26 new)**

Modified: `test_agents.py`, `test_analysis_assets.py`, `test_cli.py`, `test_experiment_runner.py`, `test_generation.py`, `test_scoring_metrics.py`

New: `test_ablation_matrix.py`, `test_batch_runner.py`, `test_bibliography.py`, `test_camera_ready_precheck.py`, `test_claim_ledger.py`, `test_commercial_api_runs.py`, `test_contamination.py`, `test_error_analysis.py`, `test_failure_gallery_doc.py`, `test_leaderboard.py`, `test_llm_agents.py`, `test_main500_generation.py`, `test_mini_study.py`, `test_open_weight_local.py`, `test_paper_assets.py`, `test_paper_fill.py`, `test_pilot_generation.py`, `test_release_check.py`, `test_release_hardening.py`, `test_reproduce_artifact.py`, `test_reviewer_proofing.py`, `test_security_check.py`, `test_statistical_reporting.py`, `test_tool_protocol.py`, `test_trajectory_v2.py`, `test_web_shadow.py`

**Build / repo hygiene**

- `.gitignore` (+7 lines: env example exception, results/cache, key files, raw provider responses)
- `Makefile` (+67 lines)
- `CHANGELOG.md` (+42 lines)

### 2. Generated artifacts

**Figures (`figures/`, 11 modified + 9 untracked)**

Modified: `figure1_benchmark_schematic.md`, figures 2–6 (pdf/png pairs)

Untracked: `figure3_intervention_family_degradation.*`, `figure5_cost_vs_robustness.*`, `figure6_error_case_taxonomy.*`, `figure6_trajectory_failure_taxonomy.*`, `figures/legacy/`

**Tables (`tables/`, 18 modified + 15 untracked)**

Modified: `paired_clean_vs_intervention.*`, `table1`–`table5` (csv/md/tex triplets)

Untracked: `table*_*.meta.json`, `table2_oracle_sanity_check.*`, `table4_ablation_placeholder_or_results.*`, `table_ranking_instability.*`

**Paper generated (`paper/generated/`, untracked, 28K)**

Placeholder snippets with explicit “no final scientific results” language. Safe to track as draft scaffolding; do **not** treat as evidence.

**Release (`release/`, untracked)**

- `release_manifest.json` — bundle hash; may drift when code changes

### 3. Paper / doc changes

**Paper (`paper/`, 17 modified + 2 untracked section files)**

Modified: `main.tex`, `main.pdf`, `references.bib`, `README.md`, sections `00`–`11`, `checklist.tex`

Untracked: `sections/06_experiments.tex`, `paper/generated/`

**Status:** Draft with bracket placeholders (`[N]`, `[M]`, `[K]`, `[X]`, `[rho]`, `[main finding placeholder]`). Audit classifies paper as **not submission ready**. Commit as draft only; never mark claims supported.

**Docs (`docs/`, 12 modified + 35 untracked)**

Modified guides: `ANALYSIS_GUIDE.md`, `BASELINE_AGENTS.md`, `BENCHMARK_CARD.md`, `CLAIM_LEDGER.md`, `DATASET_CARD.md`, `ERROR_ANALYSIS_GUIDE.md`, `ETHICS_AND_LIMITATIONS.md`, `FIGURES_AND_TABLES.md`, `METRICS.md`, `RELATED_WORK_TRACKER.md`, `REPRODUCIBILITY.md`, `RUNNING_EXPERIMENTS.md`

New: `QUICKSTART.md`, `COMMERCIAL_API_RUNS.md`, `BATCH_RUNS.md`, `COST_LATENCY.md`, `DATASET_FREEZE.md`, human-validation docs (5), intervention/contamination docs, `PAPER_EVIDENCE_MAPPING.json`, `claim_ledger.json`, `claim_ledger_schema.json`, `leaderboard_schema_v1.json`, `submission_checklist.md`, and 15+ protocol/guide files

**Top-level status docs (untracked)**

- `PROJECT_STATUS.md`, `NEXT_STEPS.md`, `MILESTONES.md`, `DATA_LICENSE.md`, `CITATION.cff`

### 4. Result directories (gitignored, not in status)

| Path | Size | Status |
|---|---|---|
| `results/` | 149M | 18 local smoke/stub run dirs; correctly ignored via `results/*/` |
| `results/dry_runs/` | (empty or ephemeral) | Now explicitly ignored |
| `results/cache/` | — | Ignored |

No provider-backed run artifacts exist. All results are engineering-only smoke/stub/oracle runs.

### 5. Config changes (30 untracked YAML files)

**Generation configs:** `generate_pilot_v0_1.yaml`, `generate_main_v0_1_500.yaml`, `generate_mini_study_*.yaml`, `generate_web_shadow_25.yaml`, `validate_pilot_v0_1.yaml`

**Pilot / main run configs:** `pilot_*_20.yaml` (multi-provider, per-provider, local stub), `pilot_100/200_multi_agent.yaml`, `pilot_budget_limited.yaml`, `main_500_multi_provider.yaml`, `main_local_openai_compatible_100.yaml`

**Commercial API configs:** `commercial_api_pilot_small_20.yaml`, `commercial_api_pilot_medium_100.yaml`, `commercial_api_ablation_20.yaml`, `commercial_api_main_500.yaml`

**Ablation / stub configs:** `configs/ablations/` (10 files), `ablation_matrix_local_stub.yaml`, `baseline_suite_local_stub.yaml`, `mini_study_*_stub.yaml`, `web_shadow_*_stub.yaml`, `judge_fake_smoke.yaml`

**Audit-added:** `configs/web_shadow_api_stub.yaml`, `configs/web_shadow_web_stub.yaml`

### 6. Audit and verification reports (untracked)

**Full verification audit:** `audits/full_verification/20260519_105705/`

- 23 numbered audit reports (`00`–`22`) + `FINAL_AUDIT_SUMMARY.md`
- `dry_runs/20260519T053218Z_pilot_multi_provider_20/` (safe dry-run evidence, no API keys)
- `generation_repro/pilot_v0_1_rerun/` (18M — full dataset reproduction copy for audit)
- `frozen_contamination_audit/`, `pilot_intervention_audit/`

**Review artifacts:** `reviews/phase2_audit.md`, `reviews/repo_audit_upgrade_map.{json,md}`, `reviews/reviewer_attack_response_matrix.md`

### 7. Data directories (untracked, 84M total)

| Path | Size | Recommendation |
|---|---|---|
| `data/frozen/pilot_v0.1/` | 15M | **Commit** — frozen benchmark snapshot with manifest |
| `data/processed/pilot_v0_1/` | — | Commit or document as regeneratable |
| `data/processed/main_v0_1_500/` | — | **Manual review** — 500-task processed set; large |
| `data/processed/web_shadow_25/` | — | Commit if web-shadow study is in scope |
| `data/web_shadow/` | — | Manual review |

### 8. Scripts (26 untracked)

Check/validation: `check_paper_*.py`, `check_claim_ledger.py`, `check_bibliography.py`, `check_repo_packaging.py`, `security_check.py`, `camera_ready_precheck.py`, etc.

Export/release: `export_paper_assets.py`, `export_leaderboard.py`, `fill_paper_from_run.py`, `release_check.py`, `release_dry_run.py`, `reproduce_artifact.py`

Ops: `run_batch_local.sh`, `slurm_batch_template.sh`, `audit_contamination.py`, `human_validation.py`

### 9. CI / artifact / prompts

- `.github/workflows/ci.yml`, `.github/workflows/batch_smoke.yml` — **commit**
- `artifact/` (repro scripts + README) — **commit**
- `.env.example` — **commit** (template only; real `.env` ignored)
- `prompts/agents/`, `prompts/judges/` — **manual review** (112K; may be intentional benchmark prompts)

---

## `.gitignore` protection review

### Already protected (before + during audit)

| Pattern | Protects |
|---|---|
| `.env`, `.env.*` with `!.env.example` | Secrets; allows template |
| `*.pem`, `*.key`, `credentials.json`, `secrets.json` | API keys / credentials |
| `**/raw_provider_responses/` | Sensitive provider payloads |
| `results/*/` (keep `results/.gitkeep`) | Large local run dirs (149M) |
| `results/cache/` | Cached run state |
| `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.ruff_cache/` | Python caches |
| `data/raw/private/` | Private raw data |
| `*.log`, `paper/*.aux|bbl|blg|log|out|toc` | Build/log noise |

### Added in this cleanup (Prompt 61)

| Pattern | Protects |
|---|---|
| `results/dry_runs/` | Ephemeral dry-run CLI output (default `--output-dir`) |
| `**/provider_logs/`, `**/provider_telemetry/` | Local provider telemetry that may contain request metadata |
| `.coverage`, `htmlcov/`, `.mypy_cache/` | Test/coverage artifacts |

### Intentionally **not** ignored (commit decision required)

- `audits/full_verification/.../dry_runs/` — audit evidence (small, redacted); commit in Audit commit
- `audits/.../generation_repro/` — large (18M) but audit evidence; commit or trim after review
- `data/frozen/`, `data/processed/` — benchmark artifacts; commit frozen, review processed size

---

## Files that should probably be ignored

- `results/**` (all run output) — already ignored
- Any future `.env` with real API keys — already ignored
- `results/dry_runs/**` — now explicitly ignored
- Regeneratable `data/processed/main_v0_1_500/` if size is a concern (69M total processed) — **optional**; prefer documenting regeneration command over ignoring if reproducibility matters
- Personal scratch outside repo — N/A

## Files that should probably be committed

1. **Audit trail:** `audits/full_verification/20260519_105705/` (reports + dry-run evidence)
2. **Source + tests:** all `src/`, `tests/`, `scripts/`
3. **Configs:** all `configs/` YAML files
4. **CI + artifact:** `.github/workflows/`, `artifact/`, `.env.example`
5. **Docs:** `docs/`, `README.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`, `NEXT_STEPS.md`, `MILESTONES.md`, `DATA_LICENSE.md`, `CITATION.cff`
6. **Frozen data:** `data/frozen/pilot_v0.1/`
7. **Reviews:** `reviews/`
8. **Build:** `Makefile`, `.gitignore`

## Files requiring manual review before commit

| Item | Concern | Action |
|---|---|---|
| `paper/main.pdf` | Binary; may embed stale placeholder narrative | Commit only if draft PDF is intentional; prefer source `.tex` as canonical |
| `paper/generated/*.tex` | Auto-filled snippets | OK as placeholders; verify no false “supported” language |
| `tables/*.csv`, `figures/*.png` | Generated from stub/smoke runs | Commit as **engineering placeholders** only; label in commit message |
| `data/processed/main_v0_1_500/` | 69M processed data | Decide: commit for reproducibility vs. regenerate-from-config |
| `audits/.../generation_repro/` | 18M duplicate of pilot data | Keep for audit reproducibility or replace with checksum references |
| `release/release_manifest.json` | Hash drift | Regenerate via `release_check.py` immediately before commit |
| `prompts/` | Agent/judge prompt templates | Confirm these are project prompts, not personal notes |
| `configs/commercial_api_*.yaml` | Reference paid API configs | Ensure no embedded secrets; use env vars only |

---

## Suggested commit grouping

> **No commits were made.** Execute manually when ready. Order preserves audit evidence before code changes.

### Commit 1: Audit and verification reports

```bash
git add audits/full_verification/20260519_105705/ \
  reviews/phase2_audit.md reviews/repo_audit_upgrade_map.json \
  reviews/repo_audit_upgrade_map.md reviews/reviewer_attack_response_matrix.md \
  audits/post_audit_cleanup/CLEANUP_PLAN.md
```

**Suggested message:**

```
audit: add full verification report and post-audit cleanup plan

Records 2026-05-19 end-to-end audit (244 tests pass, deterministic
prototype working). Classifies repo as not provider-pilot or submission
ready. Includes dry-run evidence and dataset reproduction artifacts.
```

**Files:** ~48 audit paths + 4 review files + this plan

---

### Commit 2: Provider-readiness code, configs, and tests

```bash
git add src/ tests/ scripts/ configs/ .github/ artifact/ \
  Makefile .gitignore .env.example release/ prompts/ \
  data/frozen/ data/processed/ data/web_shadow/
```

**Suggested message:**

```
feat: phase-2 pipeline, provider adapters, datasets, and validation tooling

Adds CLI (dry-run, validate-config, estimate-cost, freeze-dataset),
LLM agent/client layer, commercial runner, claim ledger, contamination
audits, frozen pilot_v0.1 data, configs for pilot/main runs, CI workflows,
and expanded test suite (244 pass). No paid provider runs included.
```

**Note:** Split `data/processed/main_v0_1_500/` into a separate commit if size is problematic.

---

### Commit 3: Docs and README updates

```bash
git add README.md CHANGELOG.md docs/ PROJECT_STATUS.md NEXT_STEPS.md \
  MILESTONES.md DATA_LICENSE.md CITATION.cff
```

**Suggested message:**

```
docs: expand reproducibility, provider-run, and claim-ledger documentation

Documents engineering-only status, pilot/main experiment protocols,
human-validation placeholders, and explicit unsupported-claims policy.
```

---

### Commit 4: Generated paper assets (draft placeholders only)

```bash
git add paper/ figures/ tables/
```

**Suggested message:**

```
paper: draft scaffold with placeholder figures and tables

Tracks LaTeX draft, bibliography, and stub-generated assets. All
empirical values remain placeholders; no scientific claims supported.
```

**Warning:** Do not run `fill-paper-from-run` or mark claim-ledger rows supported until real provider artifacts exist.

---

## Pre-provider-readiness checklist

| Gate | Status |
|---|---|
| Tests pass | ✅ `244 passed, 1 skipped` |
| Worktree categorized | ✅ This document |
| Secrets gitignored | ✅ `.env`, keys, raw provider responses |
| Run dirs gitignored | ✅ `results/*/` (149M local only) |
| Dry-run output gitignored | ✅ `results/dry_runs/` |
| Audit verdict recorded | ✅ Not provider-pilot ready |
| Commits created | ❌ Pending manual execution |
| Provider keys configured | ❌ Blocker for paid pilot |
| Model IDs / pricing complete | ❌ Blocker (Prompt 62) |
| Oracle excluded from provider configs | ⚠️ Verify in Prompt 62 |

## Safe to proceed to provider readiness?

**Yes, for engineering work (Prompt 62)** — tests pass, worktree is mapped, secrets and run artifacts are protected, and no commits are required before starting provider-readiness fixes.

**No, for paid provider pilot** — external providers unconfigured, model IDs/pricing missing, no non-oracle provider-backed artifacts, paper claims remain planned.

---

## Exact next step

Run **Prompt 62 — Provider Readiness and Config Gate** (`62_PROVIDER_READINESS_AND_CONFIG_GATE.md`).

First commands to execute inside that prompt:

```bash
python3 -m causal_agent_bench list-providers
python3 -m causal_agent_bench validate-config --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir results/dry_runs
python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
```

Do **not** run `python3 -m causal_agent_bench run` with paid providers until Prompt 62 reports `paid_pilot_ready` and cost is explicitly approved.
