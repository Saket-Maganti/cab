# Post-provider-pilot checklist

Run these steps **after** a provider pilot completes and **before** changing the claim ledger or paper. All commands are read-only or report-generating except where noted.

Replace `RUN_DIR` with the new results path (e.g. `results/20260520T120000_provider_pilot_tiny_APPROVED`).

---

## 0. Immediate run-folder checks (before reports)

In `RUN_DIR`:

- [ ] **`INCOMPLETE_RUN.json` absent** (or run marked interrupted — do not promote)
- [ ] **`run_metadata.json`** present: `scientific_evidence` still false until human review; `evidence_scope` not engineering-only
- [ ] **Provider classification**: real API provider in metadata (not mock/local/oracle-only)
- [ ] **Trajectories**: non-oracle agent steps present for cited evidence
- [ ] **Scores / metrics**: auto-score outputs inspected; no placeholder tables copied to paper
- [ ] **Cost actual**: compare `cost_summary` / billing logs to pre-run `estimate-run-cost` cap
- [ ] **No claim promotion yet** — C1–C8/C10 stay blocked until sections below pass

---

## 1. Safe inspection commands (run in order)

```bash
# 1) Run health / classification
python3 -m causal_agent_bench run-health --output-dir reports/provider_pilot_review

# 2) Paper asset sidecars and eligibility
python3 -m causal_agent_bench validate-paper-assets --output-dir reports/provider_pilot_review

# 3) Claim–evidence matrix (conservative statuses)
python3 -m causal_agent_bench claim-evidence --no-tex --output-dir reports/provider_pilot_review

# 4) Paper TODO / placeholder scan
python3 -m causal_agent_bench paper-todo-inventory --output-dir reports/provider_pilot_review

# 5) Repo-wide evidence safety
python3 scripts/check_evidence_safety.py
```

Optional (still no claim promotion):

```bash
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench summarize-run --run-dir RUN_DIR
```

---

## 2. Inspect paper-eligibility

Open `reports/provider_pilot_review/run_health_report.json` and find your `run_id`.

| Check | Pass criterion |
|-------|----------------|
| `classification` | `provider_backed_pilot` (or `main_benchmark` for larger runs) |
| `paper_eligible` | `true` |
| `scientific_evidence` | `true` in metadata (after review) |
| `missing_metadata` | `[]` |
| `completion_state` | `complete` |
| `provider_type` | Real API provider |

If any fail → **do not promote claims**; see `docs/PROVIDER_PILOT_READINESS_PACKET.md` remediation sections.

---

## 3. When **not** to promote claims

Do **not** run `update-claim-ledger --promote-to-supported` when:

- `paper_eligible` is false
- `scientific_evidence` is false or string `"false"`
- `INCOMPLETE_RUN.json` exists
- Artifact sidecars missing or `eligible_for_paper_claims: false`
- Table 5 contains “not yet run” or placeholder text (blocks C3, C10)
- Only oracle agent has model trajectories
- Run was exported with `--allow-engineering-only` / `--allow-mock-stub` without verified metadata fix

Keep C1–C8 and C10 as `planned` or `partially_supported` in the matrix until per-claim artifacts pass.

---

## 4. Pre-promotion agent and classification checks

Before `update-claim-ledger --promote-to-supported`:

- [ ] **Agent check:** `run_metadata.json` / trajectories use a **non-oracle** agent for the evidence you cite (not `scripted_oracle_agent`, `mock_behavior_agent`, stub agents)
- [ ] **Provider check:** `provider_type` and `providers` list a **real** API provider (`openai`, `anthropic`, `gemini`, `openrouter`, etc.) — not `local`, `mock`, `stub`, `oracle`
- [ ] **Classifier check:** `run-health` row shows `classification: provider_backed_pilot` (or `main_benchmark`) and `paper_eligible: true`
- [ ] **Scope check:** `evidence_scope` is not `oracle_sanity_only`, `mock_diagnostic_only`, or other engineering-only scope
- [ ] **Scientific flag:** `scientific_evidence` is boolean `true` after human review, not `"false"` or omitted
- [ ] Reject mixed configs: provider pilot APPROVED yaml must not include oracle agents (see `validate_provider_pilot_evidence_config` in `safety/provider_pilot_config.py`)

If the run is oracle-only or oracle-mixed → stop; do not promote.

---

## 5. When `--promote-to-supported` may be used

Only when **all** of the following hold for the specific claim:

1. Post-run checklist above passed for that run.
2. `claim-evidence` shows eligible artifacts for that `claim_id`.
3. For C3/C10: human-validation files exist and pass `artifact_claim_eligibility`.
4. Human reviewer signed off on metadata `scientific_evidence: true`.

Example (single claim, after review):

```bash
python3 -m causal_agent_bench update-claim-ledger \
  --ledger docs/claim_ledger.json \
  --repo-root . \
  --run-dir RUN_DIR \
  --claim-id C1 \
  --promote-to-supported
```

Expect only matching claims to promote; others remain unchanged.

**Forbidden:** `--force-manual-supported` for paper claims.

---

## 6. Why C3 and C10 still need human validation

| Claim | Extra requirement |
|-------|-------------------|
| **C3** | Trajectory vs final-answer disagreement must be backed by annotation agreement, not pilot scores alone |
| **C10** | Intervention isolation + human agreement; frozen audit JSON where configured |

Table 5 CSV text alone never supports these claims. Pilot run links are necessary but not sufficient.

---

## 7. Before `fill-paper-from-run`

- [ ] Run export guards pass without override flags, **or** use overrides only for draft previews with visible watermarks
- [ ] `verify_run_for_paper_fill` would pass with `allow_engineering_only=false`
- [ ] Do **not** pass `--promote-to-supported` on first pilot
- [ ] Generated fragments must not appear in camera-ready until watermarks removed legitimately

```bash
# Draft only — engineering preview example (NOT for submission):
# python3 -m causal_agent_bench fill-paper-from-run RUN_DIR --allow-engineering-only --no-ledger
```

---

## 8. Before exporting final paper assets

```bash
python3 -m causal_agent_bench export-paper-assets --run-dir RUN_DIR
```

- [ ] No `--allow-mock-stub` / `--allow-engineering-only` unless explicitly drafting
- [ ] Confirm `paper_assets_manifest.json` assessment flags
- [ ] Regenerate `validate-paper-assets` and `claim-evidence` after export
- [ ] Failure gallery: check `failure_gallery_short.tex` for visible warnings if evidence not final

---

## 9. Claim ledger discipline

After inspection, ledger should still show:

- **C1–C8, C10:** `planned` or `partially_supported` until per-claim promotion
- **C9:** `engineering_only` unless reproducibility separately verified

```bash
python3 scripts/check_paper_claims.py --mode submission  # when preparing submission
```

---

## 10. If anything fails

| Symptom | Action |
|---------|--------|
| Interrupted run | Do not promote; document; re-run with stricter limits |
| Wrong provider (mock/local) | Discard for scientific claims; fix config |
| Missing sidecars | Re-run `export-paper-assets`; re-validate |
| Matrix still `blocked` | Expected until artifacts + metadata complete |

See `docs/PROVIDER_PILOT_READINESS_PACKET.md` for full escalation paths.

---

## 11. Re-run no-run governance after any provider pilot

After a real approved provider pilot completes, regenerate the static reports before touching paper claims:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir reports/no_run_post_provider
```

Then inspect `run-health`, `validate-paper-assets`, `claim-evidence`, `benchmark-quality`, `intervention-isolation`, and `release-readiness`. Claim promotion remains forbidden unless the strict claim-evidence matrix and human-validation requirements support the specific claim.

Also inspect `evidence-dashboard`, `dataset-issue-triage`, and `config-metadata-lint` outputs. Treat dashboard badges as navigation aids, not evidence.
## Precondition From Advanced No-Run Reports

Do not use this post-provider checklist until the pre-provider static review has
been completed:

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_pre_provider_review
python3 scripts/check_evidence_safety.py
```

The advanced reports identify what must be repaired before a pilot and what must
be reviewed after a pilot. They do not make the pilot paper-eligible. After a
future provider run, keep claims blocked until run metadata, eligibility,
claim-evidence matrix, human-validation state, and paper assets have all been
reviewed.

Never use post-provider review to retroactively bless a template, mock, oracle,
local, or incomplete run as empirical evidence.

## Provider Gate Reminder

Only a copied approved config can reach `ready_for_dry_run` or
`ready_for_live_run`. A template may report `template_safe_but_not_runnable`;
that is a good static-review state, not permission to execute.

Before any future provider command, static leakage clusters must be reviewed.
Use the root-cause summary and top provider-pilot leakage blockers first. Raw
findings in JSON are for traceability and should not be manually triaged as the
primary queue.
