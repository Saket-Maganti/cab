# Reports Index — Causal Agent Bench

Reports are **generated locally** by zero-provider CLI tools. They do not call model APIs or start benchmark runs.

## Policy

| Location | Meaning |
|----------|---------|
| Committed `reports/` | **Snapshot** — may be stale; safe to share as examples |
| `/tmp/cab_*` from `all-no-run-reports` | **Fresh bundle** — regenerate before advisor meetings |

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_god_tier
python3 scripts/god_tier_status.py
```

---

## Quick commands

| Command | Output |
|---------|--------|
| `all-safety-reports` | Core 5 safety reports → `reports/` |
| `all-no-run-reports` | Full governance bundle (40+ reports) |
| `god-tier-status` / `scripts/god_tier_status.py` | One-screen status banner |
| `scripts/check_evidence_safety.py` | Repo-wide evidence guard |
| `scripts/check_run_index.py` | RUN_INDEX freshness |

---

## NeurIPS artifact reports (static)

| Doc | Purpose |
|-----|---------|
| [NEURIPS_ARTIFACT_READINESS_CHECKLIST.md](NEURIPS_ARTIFACT_READINESS_CHECKLIST.md) | Snapshot checklist (canonical: `docs/`) |
| `docs/NEURIPS_CONTRIBUTION_MAP.md` | Ready vs blocked contributions |
| `docs/BENCHMARK_ARTIFACT_MANIFEST.md` | Safe/forbidden commands, evidence state |
| `docs/REVIEWER_QUICKSTART_NEURIPS.md` | 5/15/30-min reviewer paths |
| `docs/REPRODUCIBILITY_TIERS.md` | Tier 0–5 ladder |
| `docs/DATASET_RELEASE_READINESS.md` | Frozen vs processed, release blockers |
| `docs/NEURIPS_SELF_REVIEW_RUBRIC.md` | Conservative self-audit |

---

## Core safety reports (`all-safety-reports`)

| Report | Files | Purpose |
|--------|-------|---------|
| Run health | `run_health_report.*` | Classify runs; flag stale index / ineligible |
| Paper asset eligibility | `paper_asset_eligibility.*` | Scan tables/figures/TeX sidecars |
| Claim–evidence matrix | `claim_evidence_matrix.*` | C1–C10 vs evidence (conservative) |
| Paper TODO inventory | `paper_todo_inventory.*` | TODOs, placeholders, blocked language |
| Reproducibility / environment | `reproducibility_environment_report.*` | Python, imports, lockfiles |

---

## Full no-run bundle (`all-no-run-reports`)

### Evidence & governance

| Key | Purpose |
|-----|---------|
| `evidence_dashboard` | Traffic-light overview + next action |
| `governance_os` | Reviewer red-team + decision templates |
| `readiness_war_room` | War-room readiness summary |
| `next_action_plan` | Ranked next actions |
| `report_quality_check` | Bundle parseability + overclaim scan |
| `god_tier_status` | Legendary status banner (also via script) |

### Provider pilot

| Key | Purpose |
|-----|---------|
| `provider_pilot_preflight` | Gate: template_safe / dry-run / live / blocked |
| `provider_pilot_config_hardening` | Template field audit |
| `run_cost_estimate` | Static cost bounds |

### Dataset & leakage

| Key | Purpose |
|-----|---------|
| `benchmark_quality` | Per-dataset quality + main vs pilot gates |
| `static_leakage` | Leakage clusters (root-cause first) |
| `answer_leakage_repair` | Manual repair worksheets |
| `leakage_repair_plan` | Clustered repair plan |
| `split_metadata_repair` | Split metadata preview |
| `dataset_issue_triage` | Dataset issue queue |
| `intervention_isolation` | Intervention isolation heuristics |
| `gold_output_validation` | Gold-output warnings |
| `tool_schema_validation` | Tool schema checks |

### Paper & advisor

| Key | Purpose |
|-----|---------|
| `advisor_review_packet` | Advisor packet + checklist + one-pager |
| `paper_readiness_map` | Section readiness + wording examples |
| `publication_readiness` | Venue-tier honesty (arXiv/workshop/main) |
| `benchmark_cards` | Benchmark/dataset/intervention cards |
| `human_validation_packet` | Human-val protocol (C3/C10 blocked) |

### Release

| Key | Purpose |
|-----|---------|
| `release_readiness` | Public release blockers |
| `release_blocker_report` | Release blocker analyzer |
| `reproducibility_manifest` | Repro manifest |
| `repair_plan` | Cross-cutting repair plan |

---

## Evidence levels

- **Scientific evidence:** verified provider/main run + post-run audit — required for C1–C8/C10.
- **Engineering-only:** smoke/stub/mock — pipeline validation only (C9).
- **No-run reports:** governance only — **never** empirical results.

See: [docs/EVIDENCE_LEVEL_POLICY.md](../docs/EVIDENCE_LEVEL_POLICY.md), [docs/DO_NOT_OVERCLAIM.md](../docs/DO_NOT_OVERCLAIM.md), [GOD_TIER_MANIFEST.md](../GOD_TIER_MANIFEST.md).
