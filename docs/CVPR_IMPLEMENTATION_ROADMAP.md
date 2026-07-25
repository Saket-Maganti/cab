# CAB-Vision Implementation Roadmap

Phased, concrete. For each phase: goals · files to create · files to edit · tests · acceptance ·
risks · complexity (S/M/L/XL) · **mandatory for CVPR?**

Status legend: ✅ done in this prototype · ⬜ to do.

---

## Phase 0 — Repo audit & cleanup ✅ (mostly done)
- **Goals:** understand reuse surface; isolate new work from text benchmark.
- **Created:** `docs/CVPR_CONVERSION_AUDIT.md`, this roadmap, the `CVPR_*` doc set.
- **Edit:** none destructive. (Later: deprecate NeurIPS-only docs — non-blocking.)
- **Tests:** n/a. **Acceptance:** audit + plan exist. **Risk:** low. **Complexity:** S. **Mandatory:** yes.

## Phase 1 — Reframe CAB → CAB-Vision without breaking old code ✅ (prototype done)
- **Goals:** new isolated `cab_vision/` package; existing `causal_agent_bench` untouched.
- **Created:** `cab_vision/__init__.py`, subpackages `schemas/`, `eval/`, `validation/`.
- **Edited:** `pyproject.toml` pytest `pythonpath = ["src", "."]` (only change to an existing file).
- **Tests:** existing suite still green; new tests green.
- **Acceptance:** `import cab_vision` works; old tests pass. **Risk:** low. **Complexity:** S. **Mandatory:** yes.

## Phase 2 — Define schemas ✅ (prototype done)
- **Goals:** strict visual-causal task schema.
- **Created:** `cab_vision/schemas/task_schema.py` (`VisualCausalTask`, `VisualAsset`, `AnswerChoice`).
- **Tests:** `tests/test_cab_vision_schema.py`.
- **Acceptance:** schema validates sample + rejects malformed. **Risk:** schema churn. **Complexity:** M. **Mandatory:** yes.
- **Next (⬜):** add optional `causal_graph`, `region_annotation` (bbox/mask) for grounding score; video asset role.

## Phase 3 — Build synthetic visual prototype ⬜
- **Goals:** first *real images* via a renderer (controlled single-factor edits) for families 1 & 6.
- **Create:** `cab_vision/data/synth/render_physical.py` (Blender/PyBullet/CLEVR-style), writer to
  `data/cab_vision/processed/synth_v0/*.jsonl` + `data/cab_vision/images/*`.
- **Edit:** `cab_vision/validation/visual_asset_checks.py` (ADD: pHash, size, format).
- **Tests:** `tests/test_dataset_split_integrity.py`, `tests/test_visual_label_leakage.py`.
- **Acceptance:** ≥200 synth items pass all validators; pairs single-factor. **Risk:** renderer setup. **Complexity:** L. **Mandatory:** yes (synthetic-controlled arm).

## Phase 4 — Add real-image tasks ⬜
- **Goals:** real photos/sim frames for families 3 & 4 (driving/household/safety).
- **Create:** `cab_vision/data/real/ingest.py` (license tracking, sha256), curation notebooks.
- **Edit:** `data/cab_vision/DATA_CARD.md`.
- **Tests:** asset-existence + license-field checks.
- **Acceptance:** ≥300 real items pass validators with license metadata. **Risk:** licensing. **Complexity:** L. **Mandatory:** yes.

## Phase 5 — Paired intervention/counterfactual examples ⬜
- **Goals:** complete obs↔int pairs (family 6) + before/after (family 2) with single-factor edits.
- **Create:** `cab_vision/data/edit/inpaint_intervene.py` (compositing/inpainting), pair linker.
- **Edit:** `cab_vision/validation/leakage_checks.py` (already has cross-split pair check ✅).
- **Tests:** `tests/test_pair_consistency_metrics.py` (metrics) + pair-integrity.
- **Acceptance:** ≥200 valid pairs; cross-split leakage = 0. **Risk:** edit artifacts → human validation needed. **Complexity:** L. **Mandatory:** yes (the differentiator).

## Phase 6 — Baseline adapters ⬜
- **Goals:** VLM adapters (closed + open) + ablation modes.
- **Create:** `cab_vision/providers/vlm_adapter.py` + `openai_vlm.py`/`anthropic_vlm.py`/`gemini_vlm.py`/
  `qwen_vl.py`/`internvl.py`/`llava.py`; ablation harness `cab_vision/eval/run_eval.py`.
- **Edit:** reuse `agents/llm_clients.py` patterns; `configs/cabv_*.yaml`; `configs/model_pricing.yaml`.
- **Tests:** `tests/test_no_groundtruth_in_prompt.py` (prompt builder never leaks labels); adapter unit
  tests with a **mock** client (no network).
- **Acceptance:** mock end-to-end run produces a metric panel; cost estimator returns a number. **Risk:**
  multimodal payload differences per provider. **Complexity:** L. **Mandatory:** yes.

## Phase 7 — Smoke tests ⬜
- **Goals:** zero-cost deterministic end-to-end on the 10 sample items with a mock VLM.
- **Create:** `cab_vision/agents/mock_vlm.py` (deterministic), `configs/cabv_smoke.yaml`.
- **Tests:** `tests/test_cabv_smoke.py`.
- **Acceptance:** `make cabv-smoke` green, no network. **Risk:** low. **Complexity:** M. **Mandatory:** yes.

## Phase 8 — Pilot evaluation ⬜
- **Goals:** small real run (open models + 1 closed) on a ~200-item pilot; first numbers.
- **Edit:** configs, cost guardrails (reuse `safety/run_cost_estimator.py`).
- **Tests:** result-schema + report-builder tests.
- **Acceptance:** pilot summary.json with CIs; money plot renders; obs>int direction visible. **Risk:**
  signal too weak → revise items. **Complexity:** M. **Mandatory:** yes.

## Phase 9 — Human validation ⬜
- **Goals:** ≥300-item validated subset; IAA; drop ambiguous.
- **Create:** `docs/CABV_ANNOTATION_GUIDE.md`; reuse `safety/human_validation_*`, `analysis/human_validation.py`.
- **Acceptance:** κ ≥ target; validated subset frozen. **Risk:** annotator cost/time. **Complexity:** L. **Mandatory:** yes.

## Phase 10 — Full run ⬜
- **Goals:** all models × full dataset; cache raw outputs; full metric panel + decomposition.
- **Edit:** `release/repro_bundle.py` (capture VLM versions/prompts/seeds).
- **Acceptance:** all `CVPR_CLAIM_LEDGER_TARGET.md` primary claims `supported` or `weakened` with
  evidence. **Risk:** cost; API drift. **Complexity:** XL. **Mandatory:** yes.

## Phase 11 — Paper writing ⬜
- **Goals:** write per `CVPR_PAPER_BLUEPRINT.md`; figures/tables from `reports/`.
- **Create:** `paper/cabv/` (new `.tex`), figures in `figures/cabv/`.
- **Acceptance:** all claims linked to figures/tables; CIs present. **Risk:** overclaiming. **Complexity:** L. **Mandatory:** yes.

## Phase 12 — CVPR submission package ⬜
- **Goals:** anonymized repo, supplementary, data card, ethics, repro bundle, hidden-test leaderboard.
- **Edit:** adapt `release/*`, `docs/REPRODUCIBILITY.md`, `docs/leaderboard_schema_v1.json`.
- **Acceptance:** double-blind compliant; one-command re-score from cache. **Risk:** anonymization slips. **Complexity:** M. **Mandatory:** yes.

---

## Critical path (shortest route to a defensible submission)
P1✅ → P2✅ → P3 (synth) → P5 (pairs) → P6 (adapters) → P7 (smoke) → P8 (pilot) → P9 (human, partial) →
P10 (full) → P11 → P12. Phase 4 (real images) runs parallel to P3 and is required for the
"not toy" verdict. Family 5 (causal chain) is the first thing to cut under time pressure.

## Suggested Makefile targets (ADD)
`make cabv-validate` (run `cab_vision.validation` over a dataset) · `make cabv-smoke` (mock e2e) ·
`make cabv-cost` (no-run cost estimate) · `make cabv-report` (build tables/figures).
