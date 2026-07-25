# Main Benchmark Readiness Plan

**Status:** `main_candidate_not_ready` — pilot infrastructure only  
**Targets:** `main_200` · `main_v0_1_500`  
**Evidence:** 0 paper-eligible runs · 0 human annotations

---

## Why main_200 and main_v0_1_500 are not ready

| Blocker | Detail |
|---------|--------|
| Not frozen | Only generation configs exist (`configs/generate_main_v0_1_500.yaml`, `configs/main_200_*.yaml`) |
| High-risk intervention queue | Manual expert review incomplete for 14 families |
| Gold-output warnings | Manual-review queue not cleared (`gold_output_manual_review_queue.csv`) |
| Human validation | 0 completed annotations; C10 unsupported |
| Provider evidence | No non-oracle pilot on any split |
| Leakage on main scale | Main bundle not statically audited at freeze |
| Split hardening | `test` held-out IDs not release-locked for main |
| Cost/runtime | Main 500 multi-provider not budget-approved |

**Verdict:** Main benchmark is **not ready** for freeze, provider main run, or public leaderboard.

---

## Requirements before main freeze

### Split / held-out

- [ ] Disjoint `dev` / `pilot` / `validation` / `test` / `heldout_templates` per `release_disjoint_v1`
- [ ] `test` instance IDs withheld from generation prompts
- [ ] `freeze_manifest.json` with `dataset_hash` and contamination audit
- [ ] No train-on-test leakage in prompt selection

### Leakage

- [ ] `blocker_cluster_count == 0` on main candidate (static scan)
- [ ] Answer-leakage repair applied with reviewed metadata only
- [ ] No unreviewed suppressions

### High-risk intervention review

- [ ] Clear `high_risk_intervention_queue` for main-scale instances
- [ ] Expert sign-off on: `long_horizon_dependency`, `memory_corruption`, `observation_conflict`, `tool_failure`, `tool_removal`, `premature_success_signal`, `stopping_recovery`
- [ ] No auto-approval

### Gold-output triage

- [ ] Zero pilot blockers in gold validation
- [ ] All `answer_changing_without_gold_change` cases resolved or reclassified
- [ ] Manual review CSV queue empty or waived with documented rationale
- [ ] **Do not auto-fix** ambiguous gold answers

### Human validation

- [ ] Pilot HV sample (40–60) completed with adjudication
- [ ] C10 isolation validity ≥ pre-specified agreement threshold (TBD at protocol lock)
- [ ] Main HV sample plan approved (120–200 items)

---

## Staged path: pilot_20 → main_200 → main_500

```text
Stage 0 (current)
  pilot_v0.1 frozen · pilot_20 instances · 0 provider runs
  └─ validity scorecard + dossier + HV templates

Stage 1 — Provider tiny pilot (≤5 instances)
  Prerequisites: signed approvals · APPROVED config · leakage=0
  Output: first non-oracle trajectories (preliminary, not paper-eligible until audit)
  └─ export HV sample from pilot run

Stage 2 — Pilot human validation (40–60 items)
  Prerequisites: Stage 1 complete trajectories
  Output: agreement stats · C3/C10 pilot support only
  └─ clear high-risk + gold queues on pilot bundle

Stage 3 — main_200 generation + freeze
  Prerequisites: Stage 2 pass · gold triage clear · intervention review
  Output: frozen `main_200` bundle
  └─ static audits on main_200

Stage 4 — main_200 provider run (engineering → scientific after audit)
  Prerequisites: budget approval · frozen main_200
  Output: preliminary main-scale trajectories
  └─ expand HV to main sample

Stage 5 — main_v0_1_500 freeze + multi-provider main
  Prerequisites: main_200 learnings · full HV · claim ledger gates
  Output: headline benchmark results (Tier 4)
  Config: `configs/commercial_api_main_500.yaml`
```

---

## Provider cost / runtime expectations (indicative)

| Stage | Config profile | Instances | Cost cap | Runtime |
|-------|---------------|-----------|----------|---------|
| Tiny pilot | `provider_pilot_tiny_template` | ≤5 | ≤$5 | minutes |
| Pilot 20 | `pilot_20_multi_agent` | ~20×agents | TBD | hours |
| Main 200 | `main_200_run` | 200×agents | TBD | hours–days |
| Main 500 | `commercial_api_main_500` | 500×agents | $$$ | days |

Use `estimate-run-cost` before any approval. **No runs without signed budget.**

---

## Readiness gates (conservative)

| Gate | Command | Pass criterion |
|------|---------|----------------|
| Validity | `validity-scorecard` | overall ≥55; leakage dimension ≥50 |
| Interventions | `high-risk-intervention-queue` | pilot blockers documented |
| Gold | `validate-gold-outputs` | 0 pilot blockers |
| HV | `human-validation-packet` | templates exist; annotations=0 acknowledged |
| Evidence | `check_evidence_safety.py` | exit 0 |

**Main benchmark ready:** only when all Stage 3–5 prerequisites met — **not now**.

---

See: [DATASET_RELEASE_READINESS.md](DATASET_RELEASE_READINESS.md), [VALIDITY_SCORECARD.md](VALIDITY_SCORECARD.md).
