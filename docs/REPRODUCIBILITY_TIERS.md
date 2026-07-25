# Reproducibility Tiers

CAB defines six reproducibility tiers (0–5). Higher tiers require more compute, approvals, and evidence; only Tier 4+ can support headline empirical paper claims (and Tier 5 for C3/C10).

**Current ceiling for artifact review:** **Tier 1** (no-run reports). Tiers 3–5 are blocked.

---

## Tier 0: Static docs / report inspection

| Field | Value |
|-------|-------|
| **Commands** | Read `docs/REVIEWER_QUICKSTART_NEURIPS.md`, `reports/claim_evidence_matrix.md`, `docs/NEURIPS_CONTRIBUTION_MAP.md` |
| **Expected runtime** | 5–15 minutes (human reading) |
| **Compute** | None |
| **API / cost** | $0 |
| **Evidence value** | Design intent, claim boundaries, blocked-state honesty |
| **Supports paper claims?** | **Method/design only** — not empirical results |

---

## Tier 1: No-run reports

| Field | Value |
|-------|-------|
| **Commands** | `python3 scripts/check_evidence_safety.py` · `python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_tier1` |
| **Expected runtime** | 1–5 minutes CPU |
| **Compute** | Laptop CPU; no GPU |
| **API / cost** | $0 |
| **Evidence value** | Regenerated governance bundle: claim matrix, asset eligibility, leakage, provider gate |
| **Supports paper claims?** | **No** — confirms what is *not* yet evidenced |

**Example:**

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_tier1
```

---

## Tier 2: Stub / mock engineering smoke

| Field | Value |
|-------|-------|
| **Commands** | `python3 -m causal_agent_bench run --config configs/pilot_mock_diagnostic_micro.yaml` (engineering) · `artifact/scripts/reproduce_deterministic.sh` |
| **Expected runtime** | 2–15 minutes |
| **Compute** | Laptop CPU |
| **API / cost** | $0 (mock/stub agents) |
| **Evidence value** | Pipeline E2E, detector wiring, C9 engineering_only |
| **Supports paper claims?** | **C9 only** (reproducibility scaffolding) — **not** C1–C8 or C10 |

**Artifact review default:** Tier 2 commands are **not** required and **must not** be interpreted as LLM benchmark results.

---

## Tier 3: Approved provider pilot

| Field | Value |
|-------|-------|
| **Commands** | `validate-config` → `dry-run` → `run` on `configs/provider_pilot_tiny_APPROVED.yaml` |
| **Expected runtime** | 10–60 minutes (pilot scale) |
| **Compute** | Network + API latency |
| **API / cost** | Template cap ≤ $5; requires `allow_paid_calls: true` + signed budget |
| **Evidence value** | First non-oracle LLM trajectories; preliminary only until post-run audit |
| **Supports paper claims?** | **Pending audit** — not automatic; `scientific_evidence` starts false |

**Approval required:** Yes — advisor forms, model selection, risk acknowledgement, copied APPROVED config.

**Current status:** **Blocked** — `template_safe_but_not_runnable`; no `*_APPROVED.yaml` without signed docs.

**Planning commands (safe, no run):**

```bash
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_template.yaml
python3 -m causal_agent_bench estimate-run-cost \
  --config configs/provider_pilot_tiny_template.yaml \
  --output-dir /tmp/cab_tier3_cost
```

---

## Tier 4: Full multi-provider benchmark

| Field | Value |
|-------|-------|
| **Commands** | `run` on `configs/commercial_api_main_500.yaml` or `configs/main_500_multi_provider.yaml` |
| **Expected runtime** | Hours to days |
| **Compute** | Multi-provider API + storage |
| **API / cost** | Substantial ($$$); explicit budget approval |
| **Evidence value** | Headline benchmark results, rankings, ablations |
| **Supports paper claims?** | **Yes** — if runs complete, pass post-run audit, and claims promoted in ledger |

**Current status:** **Blocked** — no provider pilot, main dataset not release-frozen.

---

## Tier 5: Human validation and final paper assets

| Field | Value |
|-------|-------|
| **Commands** | `sample-human-validation` → annotation export → `analyze-human-validation` → `fill-paper-from-run` (after Tier 4 evidence) |
| **Expected runtime** | Days (annotator time) + analysis |
| **Compute** | Human labor + CPU analysis |
| **API / cost** | Annotator compensation (planned) |
| **Evidence value** | C3 trajectory disagreement validation; C10 intervention isolation validity |
| **Supports paper claims?** | **C3, C10** — plus Tier 4 for joint empirical narrative |

**Current status:** **Blocked** — no completed annotations; Table 5 placeholder.

---

## Tier selection guide

| Reviewer goal | Recommended tier |
|---------------|------------------|
| Verify honest blocked state | Tier 0–1 |
| Verify engineering pipeline | Tier 2 (optional, not default) |
| Reproduce empirical paper numbers | Tier 4 + 5 (**not available**) |
| Reproduce provider pilot only | Tier 3 (**blocked**) |

## Tier vs claim support matrix

| Claim | Tier 0–1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |
|-------|----------|--------|--------|--------|--------|
| C1–C8 | No | No | Audit only | Yes* | Partial† |
| C9 | No | Engineering | No | No | No |
| C10 | No | No | No | Partial* | Yes* |

\*After post-run audit and claim-ledger promotion.  
†C3 requires Tier 5; other claims require Tier 4.

---

See [REVIEWER_QUICKSTART_NEURIPS.md](REVIEWER_QUICKSTART_NEURIPS.md) and [BENCHMARK_ARTIFACT_MANIFEST.md](BENCHMARK_ARTIFACT_MANIFEST.md).
