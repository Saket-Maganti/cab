# Provider Pilot Readiness Packet

**Status:** preparation only — no verified paper-eligible provider pilot exists in this repository yet.  
**Do not run** `causal_agent_bench run` on a provider config until the advisor approval checklist at the end of this document is signed off.

---

## 1. Purpose

Run a **tiny, budget-capped, metadata-complete** provider-backed pilot to obtain the first trajectories scored with a **real commercial API** (not mock/stub/local). The pilot is a **verification gate**, not the main benchmark.

Success means: complete run directory, honest metadata, exportable paper assets with sidecars, and claim-evidence reports that classify the run as `provider_backed_pilot` with `paper_eligible=true` after human review — **without** prematurely promoting paper claims.

---

## 2. Why this pilot is needed

| Current state | Gap |
|---------------|-----|
| Engineering / mock / stub / local / interrupted runs exist | None are paper-eligible scientific evidence |
| Claim ledger C1–C8, C10 are `planned` | No verified provider run links |
| C9 is engineering-only | Reproducibility smoke, not empirical competence |
| Guardrails and export watermarks are merge-ready | Need one **verified** provider artifact chain |

The pilot de-risks paid spend, metadata discipline, and post-run governance before any larger commercial run.

---

## 3. Claims this pilot **may** support later (not at launch)

Only **after** post-run checks, eligible artifacts, and explicit human review:

| Claim | Condition |
|-------|-----------|
| **C1** | Non-oracle agents, complete trajectories, eligible Table 2 + Figure 2 sidecars |
| **C2** | Family breakdown artifacts exported with eligible metadata |
| **C4** | Ranking instability figure/table with eligible metadata |
| **C5–C7** | Matching ablation/performance artifacts present and eligible |
| **C9** | Engineering/reproducibility wording only unless reproducibility evidence is separately verified |

Promotion uses `update-claim-ledger --run-dir … --promote-to-supported` per claim, not blanket promotion.

---

## 4. Provider pilot vs oracle sanity check

| | Provider pilot (`provider_pilot_tiny_template.yaml`) | Oracle sanity (`provider_pilot_oracle_sanity_check_template.yaml`) |
|---|------------------------------------------------------|---------------------------------------------------------------------|
| **Purpose** | First **real provider-backed LLM** trajectories for evidence review | **Pipeline plumbing** only (runner, scoring, export paths) |
| **Agents** | `direct_tool_agent` + commercial provider placeholder | `scripted_oracle_agent` only |
| **Paper-eligible** | Maybe, **after** post-run checks + `scientific_evidence: true` | **Never** |
| **Claims** | May support C1/C2/C4/etc. later per claim | **Cannot** support C1–C8 or C10 |
| **Promotion** | Per-claim `--promote-to-supported` after review | **Must not** use `--promote-to-supported` |

**Rules:**

- Oracle sanity checks verify that the benchmark **runs and scores**; they do not measure LLM competence under intervention.
- Provider pilot evidence must come from **real provider-backed LLM agents** (non-oracle, non-mock, non-stub).
- Oracle outputs cannot support C1–C8 or C10 and cannot be promoted to `supported` in the claim ledger.
- Do **not** mix oracle and provider agents in the same APPROVED provider-pilot config.

---

## 5. Claims this pilot **cannot** support alone

| Claim | Why |
|-------|-----|
| **C3** | Requires human-validation agreement artifacts (Table 5 + annotations), not pilot trajectories alone |
| **C10** | Requires intervention audit + human validation; Table 5 placeholder is insufficient |
| **Main-scale / NeurIPS-final wording** | One tiny pilot ≠ full benchmark |
| **All agents / all families** | Tiny cap by design |
| **Causal deployment claims** | Pilot is `commercial_api_pilot_unvalidated` until externally validated |

**Never** use `fill-paper-from-run --promote-to-supported` or `--force-manual-supported` for paper claims on the first pilot.

---

## 6. Pre-run safety checklist

- [ ] Read `docs/NO_RUN_VALIDATION.md` and `docs/PROVIDER_PILOT_METADATA_REQUIREMENTS.md`
- [ ] Run `all-no-run-reports` and review clustered static leakage output
- [ ] Review `leakage_repair_plan.md` and `proposed_patch_manifest.md`
- [ ] Resolve or advisor-accept leakage blockers before creating an APPROVED config
- [ ] Copy `configs/provider_pilot_tiny_template.yaml` → `configs/provider_pilot_tiny_APPROVED.yaml` (do not edit template in place)
- [ ] Advisor written approval for budget ceiling and provider choice
- [ ] API keys in environment only (never in YAML/git)
- [ ] `allow_paid_calls: false` in template; set `true` only in **APPROVED** copy after approval
- [ ] Model IDs set via env (e.g. `OPENAI_MODEL_ID`)
- [ ] Benchmark path frozen and committed (`data/processed/pilot_v0.1/…`)
- [ ] Provider pilot config has **no** oracle/mock/stub agents (oracle sanity is a **separate** optional config)
- [ ] Optional: run oracle sanity template first for plumbing only — do not use its results for claims
- [ ] Limits: `stop_after_trajectories` and `max_total_usd` set conservatively
- [ ] Claim ledger unchanged (`planned` / `engineering_only` for C1–C10)
- [ ] Run `validate-config` and `dry-run` on APPROVED config (no API in dry-run)

### Leakage repair workflow before provider pilot

1. Run:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_leakage_repair_planner_reports
```

2. Inspect `static_leakage/static_leakage_report.md`.
3. Inspect `leakage_repair_plan/leakage_repair_plan.md`.
4. Review `leakage_repair_plan/proposed_patch_manifest.md`.
5. Apply only reviewed dataset fixes manually, or with a separate explicit patch
   command later.
6. Rerun `all-no-run-reports`.
7. Do not create an APPROVED provider config until leakage blockers are resolved
   or explicitly accepted by the advisor.

The leakage repair planner and patch manifest do not apply patches and do not
create empirical evidence.

---

## 7. Required metadata fields (at run start)

Written automatically to `run_metadata.json` / `metadata.json`:

- `config_hash`, `run_name`, `git_commit`, `timestamp`
- `providers`, `provider_type`, `model_ids`, `agent_runs`
- `evidence_scope` (expect `commercial_api_pilot_unvalidated` when `pilot` in run name + commercial provider)
- `scientific_evidence`: **false** at start (default)
- `allow_paid_calls`, `budget`, `cost_estimate_preflight`
- `benchmark_instances_path`, `dataset_version` (if available)
- `not_real_llm_behavior`: must be **absent or false** for real provider runs

See `docs/PROVIDER_PILOT_METADATA_REQUIREMENTS.md` for paper-eligibility after completion.

---

## 8. Required artifact sidecars

After `export-paper-assets` (post-run, with guards):

- `paper_assets/tables/*.meta.json` with `scientific_evidence: true` and `eligibility.eligible_for_paper_claims: true` only when run verified
- `paper_assets/figures/*.meta.json` same
- `paper_assets/paper_assets_manifest.json` with assessment flags
- Global `tables/*.meta.json` / `figures/*.meta.json` if `write_global=true`

Placeholder tables (Table 5 “not yet run”) must **not** support human-validation claims.

---

## 9. Required budget cap

| Field | Template default | Notes |
|-------|------------------|-------|
| `budget.max_total_usd` | 5.0 | Hard ceiling |
| `budget_cap_usd` | 5.0 | Align with budget block |
| `task_budget_cap_usd` | 0.75 | Per-task guard |
| Per-agent `budget_cap_usd` | 3.0 | Split across agents |
| `budget.max_calls` | 40 | Call count stop |
| `allow_paid_calls` | **false** in template | Enable only in APPROVED copy |

Stop the run if preflight estimate exceeds cap (`validate-config` / cost estimate).

---

## 10. Required stop conditions

Configured in `limits` (template):

- `stop_after_trajectories: 5`
- `max_trajectories: 5`
- `max_runtime_minutes: 30`
- `fail_fast: true` (stop on repeated errors)
- Budget / call caps from `budget` block
- Runner may write `INCOMPLETE_RUN.json` if interrupted — treat as **non-eligible**

---

## 11. Required run completion checks

After the run finishes (before any claim promotion):

- [ ] No `INCOMPLETE_RUN.json` (unless intentionally marked interrupted)
- [ ] `checkpoint.json` shows `completed == total`
- [ ] `run-health` → `classification: provider_backed_pilot`, `paper_eligible: true`
- [ ] `trajectories.jsonl` non-empty for non-oracle agents
- [ ] `scores.jsonl` or `aggregate_scores.json` present if `auto_score: true`
- [ ] `scientific_evidence` reviewed — set `true` in metadata **only** if all eligibility rules pass
- [ ] Trajectory counts match `expected_trajectories` in run index
- [ ] No mock/stub/local-only providers in `providers` list

---

## 12. Required claim-evidence checks after run

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench claim-evidence --no-tex --output-dir reports/provider_pilot_review
```

- [ ] C1–C8, C10 status in matrix remains `blocked` or `partially_supported` until artifacts + runs eligible
- [ ] No claim `supported` in `docs/claim_ledger.json` without promotion workflow
- [ ] `section_allowed` for abstract/conclusion is false for `partially_supported` claims

---

## 13. Required human-validation checks after run

- [ ] Table 5 still placeholder → **do not** promote C3 or C10
- [ ] If annotation batch exists, verify files in `linked_validation_files` before any human-validation claim
- [ ] Failure gallery examples mined from run must show export watermark if `scientific_evidence` was false during export

---

## 14. Commands allowed **before** the run

| Command | Purpose |
|---------|---------|
| `python3 -m pytest tests/test_safety_reports.py tests/test_cli.py tests/test_claim_ledger.py -q` | Guardrail regression |
| `python3 scripts/check_evidence_safety.py` | Static evidence scan |
| `python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml` | Schema/budget validation |
| `python3 -m causal_agent_bench dry-run --config configs/provider_pilot_tiny_APPROVED.yaml` | Plan trajectories/cost (no API) |
| `python3 -m causal_agent_bench estimate-cost --config …` | Cost upper bound |
| `python3 -m causal_agent_bench list-providers` | Provider registry inspect |
| `python3 -m causal_agent_bench run-health --output-dir /tmp/cab_reports` | Index existing runs only |

---

## 15. Commands **forbidden** before advisor approval

| Command | Reason |
|---------|--------|
| `python3 -m causal_agent_bench run --config …` | Starts benchmark |
| `make smoke` / `make test` | May start runs |
| `run-llm-judge` | Provider calls |
| `fill-paper-from-run` on real dirs | Paper overclaim risk |
| `update-claim-ledger --promote-to-supported` | No verified evidence yet |
| `export-paper-assets` without guards on unverified run | Overclaim |
| Any command requiring API keys in CI | Paid / live inference |

---

## 16. If the run is interrupted

1. Do **not** promote claims or fill paper sections.
2. Confirm `INCOMPLETE_RUN.json` and `RUN_STATUS.md` exist.
3. Re-run `run-health`; expect `interrupted` / not `paper_eligible`.
4. Document reason in run notes; fix config limits; start a **new** run directory (do not patch old results to look complete).

---

## 17. If metadata is missing

1. Do not set `scientific_evidence: true`.
2. Inspect `run_metadata.json` for required fields (see metadata requirements doc).
3. If unrecoverable, mark run engineering-only and exclude from paper exports.
4. Do not use scope/name heuristics alone to infer provider-pilot complete.

---

## 18. If output is mock/stub/local by mistake

1. Check `providers`, `provider_type`, `deployment_class`, `not_real_llm_behavior`.
2. If mock/stub/local: do not export for main results; do not promote claims.
3. Abort paid spend if wrong provider was selected.
4. Re-run with APPROVED config after fixing `agent_runs[].provider` and model env.

---

## 19. Advisor approval checklist

| # | Item | Approver | Date |
|---|------|----------|------|
| 1 | Template copied to `*_APPROVED.yaml` | | |
| 2 | Budget cap and `allow_paid_calls` documented | | |
| 3 | Frozen benchmark path named | | |
| 4 | Non-oracle agent(s) listed | | |
| 5 | Pre-run validate-config + dry-run logs attached | | |
| 6 | Claim ledger still conservative (no supported C1–C10) | | |
| 7 | Post-run owner assigned for `POST_PROVIDER_PILOT_CHECKLIST.md` | | |

**Approved to run provider pilot:** ☐ Yes ☐ No  
**Signature / issue link:** ___________________________

---

## Related documents

- `docs/PROVIDER_PILOT_METADATA_REQUIREMENTS.md` — field-level eligibility
- `docs/POST_PROVIDER_PILOT_CHECKLIST.md` — safe post-run commands
- `docs/NO_RUN_VALIDATION.md` — CI / pre-merge lane
- `configs/provider_pilot_tiny_template.yaml` — provider evidence template (not runnable as-is)
- `configs/provider_pilot_oracle_sanity_check_template.yaml` — oracle plumbing only (never for claims)

---

## 20. Added no-run quality gates

Before copying the template to an approved config, review the static reports from:

```bash
python3 -m causal_agent_bench benchmark-quality --output-dir reports/benchmark_quality
python3 -m causal_agent_bench intervention-isolation-audit --output-dir reports/intervention_isolation
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_template.yaml --output-dir reports/cost_estimates
python3 -m causal_agent_bench release-readiness --output-dir reports/release_readiness
```

These reports are preparation gates only. A clean report does not authorize paid execution, does not make the provider pilot runnable by default, and does not support C1-C8 or C10.

Run the stricter static preflight on an approved copied config before any dry-run or live-run decision:

```bash
python3 -m causal_agent_bench provider-pilot-preflight --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir reports/provider_pilot_preflight
```

The template config should remain blocked. A copied approved config can become dry-run-ready before it is live-run-ready.
## Advanced Static Review Before Provider Pilot

Before any provider spend, review:

- `reports/repair_plan/repair_plan.md`
- `reports/gold_outputs/gold_output_validation.md`
- `reports/tool_schemas/tool_schema_validation.md`
- `reports/static_leakage/static_leakage_report.md`
- `reports/config_profiles/config_profiles.md`
- `reports/advisor_review/advisor_review_packet.md`
- `reports/paper_readiness/paper_readiness_map.md`

Provider-pilot readiness requires that provider templates still have
`allow_paid_calls: false`, that any approved copy has explicit approval markers,
and that blockers in repair/preflight/gold/tool/leakage reports are resolved or
explicitly deferred by the advisor.

These reports do not approve a live provider pilot. They only prepare the review
packet. Current claim status remains unchanged: C1-C8 and C10 planned /
unsupported, C9 engineering_only, and no paper-eligible runs.

## How to Use the Repair Plan Without Drowning in Raw Issues

If the repair plan reports thousands of static items, do not turn that raw list
into the provider-pilot checklist. Use the clustered view:

1. Start with `Root Cause Summary`.
2. Review `Top 10 Provider-Pilot Blockers` with the advisor.
3. Fix root causes that affect many tasks once, then rerun reports.
4. Use raw symptoms only to inspect representative examples or verify that a
   root fix worked.

Safe rerun:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_triage_calibrated_reports
```

Do not run a dry-run or live provider pilot until the provider gate reports the
appropriate ready state and the approved copied config has explicit approval
markers. A static gate report is not empirical evidence.

## Provider Preflight Gate States

- `template_safe_but_not_runnable`: the template includes safe caps and
  conservative defaults, but is not an execution config.
- `ready_for_approval_review`: static config fields look complete enough for
  advisor/budget review.
- `ready_for_dry_run`: an approved copy has dry-run approval markers and static
  safety caps.
- `ready_for_live_run`: live approval markers and intentional paid-call settings
  are present in an approved copy.
- `blocked`: one or more required preflight checks failed.

## How to Read Static Leakage Reports

Use leakage root-cause clusters first. Do not ask reviewers to inspect raw
191k-style findings manually. Provider-pilot leakage blockers should be fixed
or explicitly deferred before budget approval. Main-benchmark leakage warnings
can be queued after dry-run readiness is settled.

Static leakage remains a heuristic, no-run review aid. It cannot support
empirical claims.

## Current Safe Next Action

If the provider config is still a template, complete advisor approval before
creating an approved copy. If leakage blockers exist, fix the top clustered
leakage root causes first. Never run provider commands until preflight permits
the exact next dry-run or live-run state.
