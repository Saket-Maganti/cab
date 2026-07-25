# NeurIPS Reviewer Quickstart

**Benchmark:** Causal Agent Bench  
**Artifact type:** Infrastructure / benchmark-design candidate (empirical evidence blocked)  
**Time budgets:** 5 min · 15 min · 30 min · optional provider path (not runnable without keys)

---

## What you are reviewing

CAB is an **interventional benchmark scaffold** for tool-using agents: paired clean/intervention tasks, ACRS metrics, trajectory diagnostics, and evidence governance. The repository is strong on **design and reproducibility infrastructure**; it has **0 paper-eligible provider runs** and **0 eligible empirical assets** as of 2026-06-10.

**Do not infer:** model rankings, degradation percentages, human agreement, or public-release readiness from stub/mock runs or placeholder tables.

---

## 5-minute static review path

**Goal:** Verify scope, honesty, and evidence boundaries without executing code.

1. Read [NEURIPS_CONTRIBUTION_MAP.md](NEURIPS_CONTRIBUTION_MAP.md) — separates ready vs blocked contributions.
2. Skim [reports/claim_evidence_matrix.md](../reports/claim_evidence_matrix.md) — confirm 0 eligible runs, C1–C8/C10 planned.
3. Read [DO_NOT_OVERCLAIM.md](DO_NOT_OVERCLAIM.md) — forbidden phrases and safer alternatives.
4. Check abstract guard in `paper/latexpaper/generated/00_abstract.tex` — must state results not yet reported.

**Verify:**

- [ ] No section claims completed provider experiments
- [ ] C9 is engineering-only, not empirical benchmark evidence
- [ ] Placeholder tables/figures are labeled or blocked

**Do not infer:** Any number in bracket placeholders `[N]`, `[X]`, `[rho]` is real data.

---

## 15-minute no-run report reproduction path

**Goal:** Regenerate static governance reports (no model execution, no API calls).

```bash
cd <repo_root>
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_neurips_reviewer
```

**Expected outputs:**

| Output | Location | What to check |
|--------|----------|---------------|
| Evidence safety | stdout exit 0 | No paper-eligible runs misclassified |
| Claim–evidence matrix | `/tmp/cab_neurips_reviewer/claim_evidence_matrix.md` | `Eligible scientific runs: 0` |
| Paper asset eligibility | `paper_asset_eligibility.md` | `eligible_count` near 0 for empirical claims |
| God-tier / provider gate | `god_tier_status/` if present | `template_safe_but_not_runnable` |
| Static leakage | `static_leakage_report.md` | `blocker_cluster_count: 0` |

**Verify:**

- [ ] `check_evidence_safety.py` exits 0
- [ ] No claim status is `supported` for C1–C8 or C10
- [ ] Provider gate does not show `ready_for_live_provider_run: true` without APPROVED config

**Runtime:** ~1–3 minutes CPU, ~0 cost.

---

## 30-minute artifact inspection path

**Goal:** Validate benchmark design, dataset freeze, and config safety.

```bash
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_template.yaml
python3 -m causal_agent_bench estimate-run-cost \
  --config configs/provider_pilot_tiny_template.yaml \
  --output-dir /tmp/cab_neurips_reviewer/cost_estimate
python3 -m causal_agent_bench benchmark-manifest --output-dir /tmp/cab_neurips_reviewer/manifest
```

**Read (no commands):**

- [BENCHMARK_CARD.md](BENCHMARK_CARD.md) — task scope and limitations
- [DATASET_CARD.md](DATASET_CARD.md) — construction and splits
- [SPLIT_PROTOCOL.md](SPLIT_PROTOCOL.md) — dev/pilot/test policy
- [INTERVENTION_TAXONOMY.md](INTERVENTION_TAXONOMY.md) — perturbation families
- [METRIC_CARD_ACRS.md](METRIC_CARD_ACRS.md) — scoring definitions
- `data/frozen/pilot_v0.1/freeze_manifest.json` — frozen pilot hashes

**Verify:**

- [ ] `provider_pilot_tiny_template.yaml` header says TEMPLATE ONLY / `allow_paid_calls: false`
- [ ] No `configs/*_APPROVED.yaml` in repo without signed `docs/approvals/` forms
- [ ] Frozen vs processed distinction documented in [DATASET_RELEASE_READINESS.md](DATASET_RELEASE_READINESS.md)
- [ ] `release/benchmark_artifact_manifest.json` reports `paper_eligible_runs: 0`

**Runtime:** ~3–8 minutes CPU, ~0 cost.

---

## Provider-required optional path (NOT runnable without keys/approval)

**Status:** Explicitly **blocked** in the public artifact. Documented for completeness only.

**Prerequisites (all required before any `run`):**

1. Signed `docs/approvals/ADVISOR_APPROVAL_FORM.md`
2. Signed `docs/approvals/BUDGET_APPROVAL_FORM.md`
3. Completed `docs/approvals/PROVIDER_MODEL_SELECTION_FORM.md`
4. Copy `configs/provider_pilot_tiny_template.yaml` → `configs/provider_pilot_tiny_APPROVED.yaml`
5. Set `allow_paid_calls: true` only after budget sign-off
6. Export API keys via environment (never commit)

**Would-be commands (do not run during standard review):**

```bash
# BLOCKED — requires approval + keys:
# python3 -m causal_agent_bench dry-run --config configs/provider_pilot_tiny_APPROVED.yaml
# python3 -m causal_agent_bench run --config configs/provider_pilot_tiny_APPROVED.yaml
```

**Current gate:** `template_safe_but_not_runnable` — template validates but live execution is not cleared.

**Do not infer:** `validate-config` or `plan-run` on the template implies a completed pilot.

---

## What reviewers should verify

| Check | Pass criterion |
|-------|----------------|
| Evidence honesty | 0 paper-eligible runs acknowledged in checklist + matrix |
| Claim firewall | C1–C8/C10 not `supported`; results section blocked |
| Provider safety | No APPROVED config without signed docs; `allow_paid_calls: false` in template |
| Dataset integrity | Frozen pilot manifest + split policy documented |
| Reproducibility | No-run bundle regenerates; deterministic artifact script documented |
| Ethics | Synthetic data, no live PII, cost caps documented |

## What reviewers should NOT infer

- Smoke/stub/mock runs demonstrate LLM behavior
- Placeholder tables (`table2_*`, `figure2_*`) contain real results
- Engineering-only C9 validates benchmark conclusions
- `estimate-run-cost` output implies experiments were run
- Leakage cluster count 0 alone means paper-ready (provider + HV still blocked)
- Infrastructure strength equals NeurIPS empirical acceptance

---

## Related artifacts

- [NEURIPS_ARTIFACT_READINESS_CHECKLIST.md](NEURIPS_ARTIFACT_READINESS_CHECKLIST.md)
- [REPRODUCIBILITY_TIERS.md](REPRODUCIBILITY_TIERS.md)
- [reviews/reviewer_attack_response_matrix.md](../reviews/reviewer_attack_response_matrix.md)
- [GOD_TIER_MANIFEST.md](../GOD_TIER_MANIFEST.md)
