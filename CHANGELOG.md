# Changelog

## Unreleased - Phase-2 pilot readiness

- Hardened config validation with provider readiness checks, safe missing-key reporting, and dry-run report generation.
- Added provider specs, OpenAI-compatible/local OpenAI-compatible adapters, response caching, and structured LLM call hashes.
- Added canonical LLM tool-call protocol parsing with raw/parsed trajectory logging.
- Added Trajectory Schema v2 validation, compatibility migration, and markdown transcript helpers.
- Expanded synthetic generation to a 500-base-task candidate config across 12 domains with balanced interventions.
- Added Gemini and larger multi-provider pilot config templates.
- Added Phase-2 CLI commands for config validation, dry-run planning, intervention audits, dataset freezing, run summaries, and claim-ledger updates.
- Expanded intervention audits with family-level validity guides, patch-isolation checks, and per-instance pass/warning/fail validity scores.
- Hardened dataset freezing with schema validation, quality-audit gating, release splits, leakage checks, dataset hashes, manifests, and benchmark-card snapshots.
- Added human-validation sampling, annotation export, static HTML aid, agreement/adjudication reports, and protocol documentation.
- Added human-validation annotation guidelines, form schema, and pilot plan documentation.
- Added optional LLM judge interface, prompt templates, fake-judge tests, and calibration reports guarded by human-validation requirements.
- Added the named LLM baseline suite, versioned prompt templates, agent cards, and oracle-separated leaderboard export.
- Added prompt/scaffold ablation configs, single-factor prompt variants, prompt hash logging controls, and a Table 4 ablation exporter.
- Added first-class cost/latency tracking, provider/model cost-model config, budget caps, and cost-normalized paper tables.
- Added Metrics v2 exports with expanded component metrics, confidence intervals, metric cards, and undefined-ACRS handling.
- Added statistical reporting exports with base-task-paired tests, bootstraps, rank correlations, effect sizes, and reviewer-facing warnings.
- Added open-weight/local OpenAI-compatible pilot configs, evidence-scope labeling, and `docs/OPEN_WEIGHT_LOCAL_MODELS.md`.
- Added commercial API run configs with `allow_paid_calls` gating, budget preflight enforcement, metadata/redaction, and `docs/COMMERCIAL_API_RUNS.md`.
- Added synthetic-to-realistic mini-study generation (40 naturalistic mock-artifact tasks), comparison analysis, configs, and paper table scaffolding.
- Added optional web shadow study: frozen static HTML snapshot tools, 25 navigation scenarios (API + web interfaces), web-specific interventions, comparison CLI, and `docs/WEB_SHADOW_STUDY.md`.
- Added release package `0.1.0-rc1`: benchmark/dataset/metric/intervention cards, `release/release_manifest.json`, `make release-check`, and expanded reproducibility/ethics documentation.
- Added safe paper fill workflow (`fill-paper-from-run`, `paper/generated/` fragments, `docs/PAPER_EVIDENCE_MAPPING.json`, claim-ledger updates) without fabricating scientific results from stub runs.
- Added run and paper-asset metadata stamping for config hash, dataset version, model IDs, timestamp, and run directory.
- Added the 18-way trajectory error-taxonomy miner, failure-gallery exports, qualitative example packets, and cross-case filters.
- Added project status, milestones, and Phase-2 audit documentation.
- Added tests for the new CLI commands and asset metadata.
- Expanded related work (agent, tool-use, web, SWE, trajectory, robustness, causal, judge sections), added `docs/RELATED_WORK_MATRIX.md`, seven new verified citations (AgentBoard, WebShop, VisualWebArena, OSWorld, StableToolBench, $\tau$-bench, DecodingTrust), and `scripts/check_bibliography.py` wired into `make paper-check`.
- Added NeurIPS ED reviewer-proofing matrix (`reviews/reviewer_attack_response_matrix.md`), prioritized P0–P3 fix list, `docs/REVIEWER_PROOFING.md`, paper/checklist scope updates, and `scripts/check_reviewer_proofing.py` in `make paper-check`.
- Added camera-ready packaging: `docs/submission_checklist.md`, check scripts (citations, TODOs, paper assets, package import, repo packaging), `scripts/camera_ready_precheck.py`, `make submission-precheck` / `submission-check`, `make release-dry-run`, and GitHub Actions CI workflow.
- Added claim ledger schema v2 (`src/causal_agent_bench/claim_ledger.py`), paper claim cross-check (`scripts/check_paper_claims.py`), enhanced `scripts/check_claim_ledger.py`, and `update-claim-ledger --run-dir` CLI integration.
- Added artifact evaluation package (`artifact/`), `docs/QUICKSTART.md`, `scripts/reproduce_artifact.py`, Makefile `artifact-*` targets, and troubleshooting for reviewer reproduction paths.
- Added security/privacy/license hardening: `scripts/security_check.py`, `.env.example`, `DATA_LICENSE.md`, `CITATION.cff`, `docs/SECURITY_AND_PRIVACY.md`, and expanded `.gitignore` for secrets/caches.
- Added leaderboard and held-out split protocol: `docs/LEADERBOARD_PROTOCOL.md`, `docs/SPLIT_PROTOCOL.md`, `docs/leaderboard_schema_v1.json`, `src/causal_agent_bench/analysis/leaderboard.py`, `export-leaderboard` CLI, `scripts/export_leaderboard.py`, and tests with oracle exclusion and contamination warnings.
- Added model contamination and memorization audits: template fingerprinting, hidden-split canaries, near-duplicate detection, prompt-leakage checks, `audit-contamination` CLI, freeze-time canary injection, and `docs/MODEL_CONTAMINATION.md` / `docs/PUBLIC_VS_HIDDEN_SPLITS.md`.
- Added agent failure gallery for paper/website: `docs/FAILURE_GALLERY.md`, `paper/generated/failure_gallery_short.tex`, `export-failure-gallery` CLI, and seven intervention-family qualitative panels with trajectory excerpts and final-answer scoring blind-spot notes.
- Upgraded paper asset generator: canonical Tables 1–5 and Figures 1–7 with PNG/PDF/CSV/TeX exports, per-asset `.meta.json` sidecars, `paper_assets_manifest.json`, engineering-only/stub run guards, and new figures for family degradation, cost vs robustness, failure taxonomy, and human/judge agreement.
- Added ablation matrix runner: factorial matrix YAML (`configs/ablation_matrix_local_stub.yaml`), per-cell config generation, plan/execute CLI (`ablation-matrix`), aggregated table/heatmap exports, cost safeguards, and tests with `local_stub`.
- Added batch/shard runner prep: instance/agent/intervention-family sharding (`batch-plan`), resumable runs with `--retry-failed` and `checkpoint.json`, shard merge with duplicate/missing checks (`batch-merge`), failure reports, local/SLURM scripts, and CI batch smoke workflow.

## 0.1.0 - Initial research scaffold

- Added benchmark schemas and JSONL validation.
- Added synthetic task and intervention generation.
- Added deterministic simulated tool environment.
- Added baseline agents and LLM adapter interfaces.
- Added metrics, scoring, experiment runner, resume checks, and analysis assets.
- Added documentation, benchmark/data cards, claim ledger, review artifacts, and paper scaffold.
