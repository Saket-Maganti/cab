# CAB-Vision Repo Changeset

Exact structure changes. The new `cab_vision/` package lives at the repo root, **isolated** from
`src/causal_agent_bench/` so the text benchmark keeps working. ✅ = created in this prototype.

```
cab_vision/
  __init__.py                         ✅
  schemas/
    __init__.py                       ✅
    task_schema.py                    ✅ VisualCausalTask / VisualAsset / AnswerChoice
    visual_intervention_schema.py     ⬜ family-1 helpers (intervention_type enums, builders)
    counterfactual_schema.py          ⬜ before/after pair builders + validators
    action_schema.py                  ⬜ action-set / validity helpers
  tasks/                              ⬜ per-family generators/curation
    visual_intervention/ counterfactual_scene/ spurious_cue/ action_selection/
  data/                              ⬜ pipeline code (not the bytes)
    synth/ real/ edit/  (render / ingest / inpaint)
  eval/
    __init__.py                       ✅
    metrics.py                        ✅ accuracy, causal_consistency, intervention_sensitivity,
                                         spurious_cue_resistance, action_validity, summarize
    causal_consistency.py             ⬜ (optional split-out; currently in metrics.py)
    intervention_sensitivity.py       ⬜ (optional split-out)
    spurious_cue_resistance.py        ⬜ (optional split-out)
    action_validity.py                ⬜ (optional split-out)
    run_eval.py                       ⬜ driver: dataset × model × ablation → summary.json
  providers/                         ⬜
    vlm_adapter.py openai_vlm.py anthropic_vlm.py gemini_vlm.py qwen_vl.py internvl.py llava.py
    mock_vlm.py                       ⬜ deterministic, no-network (for smoke/tests)
  validation/
    __init__.py                       ✅
    leakage_checks.py                 ✅ no-answer-in-prompt, image-present, family/split, pair leakage
    schema_checks.py                  ⬜ thin wrapper around pydantic for batch reports
    visual_asset_checks.py            ⬜ pHash dedup, size/format, sha256 verify
    label_visibility_checks.py        ⬜ stricter label-in-prompt + choice-balance audit
  reports/                           ⬜
    build_tables.py build_failure_gallery.py build_scorecards.py
  agents/                            ⬜ (only if agentic action tasks) mock_vlm + ReAct loop

data/cab_vision/
  examples/sample_tasks.jsonl         ✅ 10 toy items (placeholder images)
  images/                             ⬜ the actual assets (placeholders referenced now)
  raw/ processed/ splits/             ⬜
  DATA_CARD.md ETHICS.md              ⬜

tests/
  test_cab_vision_schema.py           ✅
  test_cab_vision_metrics.py          ✅
  test_visual_label_leakage.py        ⬜
  test_pair_consistency_metrics.py    ⬜ (subset already covered by test_cab_vision_metrics)
  test_spurious_cue_metrics.py        ⬜ (subset covered)
  test_action_validity_metrics.py     ⬜ (subset covered)
  test_dataset_split_integrity.py     ⬜
  test_no_groundtruth_in_prompt.py    ⬜ (prompt builder; needs providers)

docs/  CVPR_*.md                       ✅ (this set)
paper/cabv/                            ⬜ new tex (replaces deleted paper/main.tex)
figures/cabv/                          ⬜ generated
configs/  cabv_*.yaml                  ⬜ smoke / pilot / full / ablation
```

**Edited existing files (minimal):**
- `pyproject.toml` — pytest `pythonpath = ["src", "."]` (✅, only existing-file change so far).
- Later (non-blocking): `Makefile` (+`cabv-*` targets), `README.md` (link the CVPR direction),
  `mkdocs.yml` (nav), deprecate `safety/neurips_submission_gate.py` / NeurIPS blueprints.

---

## Per-file purpose · dependencies · minimal impl · tests · CVPR support

### `cab_vision/schemas/task_schema.py` ✅
- **Purpose:** the strict visual-causal task contract.
- **Deps:** pydantic v2 (already a dep). No vision deps.
- **Minimal impl:** done — `VisualCausalTask` + helpers + `load_tasks_jsonl`.
- **Tests:** `tests/test_cab_vision_schema.py` (12 tests).
- **CVPR:** schema = the dataset definition reviewers scrutinize; enforces single-factor/pair fields.

### `cab_vision/eval/metrics.py` ✅
- **Purpose:** causal metric panel beyond accuracy.
- **Deps:** stdlib only (`statistics`, `collections`).
- **Minimal impl:** done. **Next:** wire bootstrap CIs (reuse `metrics/statistics.py`).
- **Tests:** `tests/test_cab_vision_metrics.py` (18 tests).
- **CVPR:** these metrics are the contribution's measuring instrument (V1/V3/V4 claims).

### `cab_vision/validation/leakage_checks.py` ✅
- **Purpose:** anti-text-shortcut + integrity guards.
- **Deps:** schema only.
- **Minimal impl:** done. **Next:** pHash dedup (`visual_asset_checks.py`).
- **Tests:** in `tests/test_cab_vision_schema.py`.
- **CVPR:** directly answers the two biggest reject reasons (text shortcut, leakage).

### `cab_vision/providers/vlm_adapter.py` ⬜
- **Purpose:** uniform `predict(image, question, choices) -> (index, rationale, usage)`.
- **Deps:** reuse `agents/llm_clients.py` (`Message`/`ModelConfig`/`TokenUsage`); per-provider SDKs lazy-imported.
- **Minimal impl:** abstract base + `mock_vlm.py` first (deterministic).
- **Tests:** `tests/test_no_groundtruth_in_prompt.py` + mock adapter unit test.
- **CVPR:** baseline strength + reproducibility.

### `cab_vision/eval/run_eval.py` ⬜
- **Purpose:** orchestrate dataset × model × ablation; emit `results/cabv/<run>/summary.json`.
- **Deps:** schema, metrics, providers, validation, cost estimator.
- **Minimal impl:** loop + cache + `summarize`.
- **Tests:** mock end-to-end (`tests/test_cabv_smoke.py`).
- **CVPR:** produces every results table/figure.

### `cab_vision/validation/visual_asset_checks.py` ⬜
- **Purpose:** pHash near-dup across splits, sha256 verify, size/format.
- **Deps:** `imagehash`/`Pillow` (new, gated import). **Tests:** dedup on toy images.
- **CVPR:** contamination/leakage defense (V8 credibility).

### `cab_vision/reports/build_*.py` ⬜
- **Purpose:** tables, visual failure gallery, scorecards.
- **Deps:** adapt `analysis/tables.py`, `analysis/figures.py`, `analysis/failure_gallery_doc.py`.
- **CVPR:** Sec 8–9 assets.

---

## Isolation guarantees
- No import from `cab_vision` into `causal_agent_bench` or vice-versa (keeps both runnable).
- New deps (`Pillow`, `imagehash`, `torch`/`transformers` for open VLMs) go in a **new optional extra**
  `pyproject.toml [project.optional-dependencies] vision = [...]` so the text benchmark's light install
  is unchanged.
- All new tests are additive; existing 120 test files untouched.
