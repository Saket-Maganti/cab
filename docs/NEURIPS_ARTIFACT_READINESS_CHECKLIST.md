# NeurIPS Artifact Readiness Checklist

**Benchmark:** Causal Agent Bench (CAB)  
**Version:** `0.1.0-dev`  
**Classification:** `research_scaffold` — infrastructure-ready, empirical evidence blocked  
**Last updated:** 2026-06-10 (static, no-run)

This checklist maps NeurIPS Datasets/Evaluations-track artifact expectations to CAB's current state. It is conservative: passing a row does **not** promote claims or mark runs paper-eligible.

---

## 1. Benchmark motivation

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Problem statement (final success conflates skills) | **Ready (method)** | `paper/latexpaper/sections/01_introduction.tex`, `docs/RESEARCH_SPEC.md` |
| Skill decomposition rationale | **Ready (method)** | `docs/BENCHMARK_TAXONOMY.md`, `docs/INTERVENTION_TAXONOMY.md` |
| Empirical motivation claims (degradation, rankings) | **Blocked** | C1–C8 planned; 0 paper-eligible runs |

## 2. Dataset construction

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Generation pipeline documented | **Ready** | `docs/DATASET_CARD.md`, `benchmark_specs/generation_rules.md` |
| Template registry | **Ready** | `benchmark_specs/task_template_registry.json` |
| Naturalistic / mini-study variants | **Partial** | Configs exist; not frozen for main release |
| Frozen pilot bundle (`pilot_v0.1`) | **Ready (pilot scale)** | `data/frozen/pilot_v0.1/freeze_manifest.json` |
| Main 200 / main_v0.1_500 frozen release | **Blocked** | Generation configs exist; freeze + human audit pending |

## 3. Intervention taxonomy

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Family definitions | **Ready** | `docs/INTERVENTION_TAXONOMY.md`, `configs/intervention_taxonomy.yaml` |
| Pairing protocol (clean ↔ intervention) | **Ready** | `docs/INTERVENTIONS.md`, `benchmark_specs/intervention_families.yaml` |
| Isolation audit tooling | **Ready (static)** | `audit-intervention-isolation`, reports in no-run bundle |
| Expert validity of isolation (C10) | **Blocked** | Human validation annotations missing |

## 4. Data leakage controls

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Static leakage scan | **Ready** | `static-leakage-report` in no-run bundle |
| True leakage blocker clusters | **0** (current) | `PROVIDER_PILOT_PREPARATION_STATUS.md`; re-verify via `all-no-run-reports` |
| Answer-leakage repair workflow | **Ready** | `docs/LEAKAGE_REPAIR_APPLY_GUIDE.md` |
| Contamination audit on freeze | **Ready (pilot)** | `freeze_manifest.json` → `contamination_audit_summary` |
| Held-out template policy | **Ready** | `docs/PUBLIC_VS_HIDDEN_SPLITS.md` |

## 5. Train / dev / test / frozen split policy

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Split protocol documented | **Ready** | `docs/SPLIT_PROTOCOL.md` |
| Disjoint base-task splits | **Ready (pilot)** | `data/frozen/pilot_v0.1/splits.json` |
| Hidden `test` split policy | **Ready** | IDs withheld until release policy met |
| Leaderboard split rules | **Ready** | `docs/LEADERBOARD_PROTOCOL.md` |
| Main-scale split hardening | **Blocked** | `main_200`, `main_v0.1_500` not release-frozen |

## 6. Tool environment documentation

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Simulated tools spec | **Ready** | `docs/TOOL_CALL_PROTOCOL.md`, `src/causal_agent_bench/environment.py` |
| Deterministic execution | **Ready** | `artifact/scripts/reproduce_deterministic.sh` |
| No live email/booking / PII policy | **Ready** | `docs/ETHICS_AND_LIMITATIONS.md` |
| Provider tool adapters | **Template only** | Documented; not validated with live runs |

## 7. Metric definitions

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Clean / intervention success | **Ready (definition)** | `docs/METRICS.md` |
| ACRS | **Ready (definition)** | `docs/METRIC_CARD_ACRS.md` |
| Trajectory diagnostics | **Ready (definition)** | `docs/TRAJECTORY_SCHEMA_V2.md` |
| Statistical reporting policy | **Ready** | `docs/ANALYSIS_GUIDE.md` |
| Empirical metric values | **Blocked** | No provider-backed runs |

## 8. Scoring reproducibility

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Deterministic scorer version pinned | **Ready** | `docs/PAPER_EVIDENCE_MAPPING.json` → `scorer` |
| Config hash per run | **Ready** | Runner writes `config_hash.txt` |
| Export guards (no ineligible → paper) | **Ready** | `fill-paper-from-run` refuses ineligible sources |
| Scoring on provider trajectories | **Blocked** | 0 complete provider runs |

## 9. Claim–evidence mapping

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Claim ledger (C1–C10) | **Ready** | `docs/claim_ledger.json` |
| Claim–evidence matrix | **Ready (static)** | `reports/claim_evidence_matrix.md` |
| Paper readiness map | **Ready (static)** | `reports/paper_readiness/` |
| Supported empirical claims | **0** | C1–C8/C10 planned; C9 engineering_only |

## 10. Human validation requirements

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Protocol + forms | **Ready** | `docs/HUMAN_VALIDATION_PROTOCOL.md` |
| Sampling config | **Ready** | `configs/human_validation_sample.yaml` |
| Completed annotations | **Missing** | Blocks C3, C10 |
| Agreement statistics | **Missing** | `tables/table5_human_validation_agreement.csv` placeholder |

## 11. Provider-run requirements

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Provider pilot template | **Ready (template)** | `configs/provider_pilot_tiny_template.yaml` |
| Preflight gate | **template_safe_but_not_runnable** | `reports/god_tier_status/god_tier_status.json` |
| APPROVED config in repo | **Must not exist** without signed forms | `docs/approvals/` |
| `allow_paid_calls: true` | **Forbidden** without budget approval | Template has `false` |
| Post-run audit checklist | **Ready** | `docs/POST_PROVIDER_PILOT_CHECKLIST.md` |

## 12. Artifact package contents

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Source package | **Ready** | `src/causal_agent_bench/` |
| Configs (all experiment profiles) | **Ready** | `configs/` |
| Frozen pilot data | **Ready** | `data/frozen/pilot_v0.1/` |
| Paper LaTeX (placeholder-safe) | **Ready** | `paper/latexpaper/` |
| Release manifest | **Ready (dev)** | `release/release_manifest.json` |
| Benchmark artifact manifest | **Ready** | `docs/BENCHMARK_ARTIFACT_MANIFEST.md`, `release/benchmark_artifact_manifest.json` |
| Results bundled in release | **None by default** | Policy: cite `run_metadata.json` paths |

## 13. Reproducibility commands

| Tier | Command | Runnable now? |
|------|---------|---------------|
| Static inspection | Read `docs/REVIEWER_QUICKSTART_NEURIPS.md` | Yes |
| No-run reports | `python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_reports` | Yes |
| Config validation | `python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml` | Yes |
| Run planning | `python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_template.yaml` | Yes |
| Cost estimate | `python3 -m causal_agent_bench estimate-run-cost --config ...` | Yes |
| Stub/mock smoke | `make smoke` / `causal_agent_bench run` | **Forbidden in artifact review** unless explicitly scoped |
| Provider pilot | `run` with APPROVED config | **Blocked** — keys + signed approval required |

See `docs/REPRODUCIBILITY_TIERS.md` for full tier definitions.

## 14. Limitations

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Synthetic task limitations | **Ready** | `docs/ETHICS_AND_LIMITATIONS.md` |
| Heuristic scorer limits | **Ready** | `docs/LLM_JUDGE_RISKS.md` |
| No empirical results disclaimer | **Ready** | `docs/DO_NOT_OVERCLAIM.md` |
| Self-review rubric | **Ready** | `docs/NEURIPS_SELF_REVIEW_RUBRIC.md` |

## 15. Ethics / safety

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Ethics section in paper | **Ready** | `paper/latexpaper/sections/11_ethics_reproducibility.tex` |
| Security / privacy | **Ready** | `docs/SECURITY_AND_PRIVACY.md`, `SECURITY.md` |
| API cost safeguards | **Ready** | Budget caps, `allow_paid_calls` default false |
| Human annotator compensation placeholder | **Needs fill before HV** | Paper §11 placeholder flagged |

## 16. Release license / data license

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| Code license (MIT) | **Ready** | `LICENSE` |
| Data license | **Ready** | `DATA_LICENSE.md` |
| Citation file | **Ready** | `CITATION.cff` |
| Public v1.0 release | **Blocked** | `release/release_manifest.json` → `benchmark_status: research_scaffold` |

## 17. Compute / cost requirements

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| No-run review compute | **~0** | Static files only |
| Stub/mock engineering | **Low (CPU)** | Minutes on laptop |
| Tiny provider pilot (template) | **≤ $5 cap** | `estimate-run-cost` on template |
| Main 500 multi-provider | **High ($$$)** | `configs/commercial_api_main_500.yaml` — not runnable without approval |

## 18. Reviewer instructions

| Item | Status | Evidence / pointer |
|------|--------|-------------------|
| 5 / 15 / 30-minute review paths | **Ready** | `docs/REVIEWER_QUICKSTART_NEURIPS.md` |
| Attack response matrix | **Ready** | `reviews/reviewer_attack_response_matrix.md` |
| What **not** to infer | **Ready** | Quickstart + `docs/DO_NOT_OVERCLAIM.md` |

---

## What is currently ready

- Benchmark **design** and intervention framework (method-only)
- Frozen **pilot_v0.1** dataset with split policy and leakage tooling
- **80+** CLI subcommands, run management, claim ledger, export guards
- **No-run report bundle** for static reproducibility review
- Provider pilot **template** + preflight gates (not runnable without approval)
- Paper draft with **placeholder protection** and evidence firewall
- Engineering E2E validation via mock diagnostic micro run (C9 only)

## What is currently blocked

| Blocker | Impact |
|---------|--------|
| 0 paper-eligible provider runs | C1–C8 empirical claims unsupported |
| 0 eligible empirical paper assets | Results tables/figures blocked |
| No human-validation annotations | C3, C10 blocked |
| No `*_APPROVED.yaml` without signed docs | Provider pilot execution blocked |
| `template_safe_but_not_runnable` gate | Live provider path not cleared |
| Main 200 / main_v0.1_500 not frozen | Full benchmark release blocked |
| Public v1.0 release | Zenodo/HF packaging blocked |
| RUN_INDEX may be stale | Refresh with `index-runs`; does not change eligibility |

---

## Pre-submission verification (safe only)

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_neurips_check
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml
python3 scripts/check_claim_ledger.py --mode draft
```

**Do not run** `make smoke`, `causal_agent_bench run`, or broad pytest during artifact review unless explicitly scoped.

**Current NeurIPS artifact classification:** `infrastructure_artifact_candidate` — suitable for **method/benchmark design review**, not empirical results review.
