# CAB-Vision Prototype Status

**Date:** 2026-06-21. **Scope:** safe, isolated, zero-cost prototype. No paid APIs, no large
datasets, no heavy vision deps. The existing `causal_agent_bench` package and its 120 test files are
untouched.

---

## What was implemented

| Artifact | Path | Status |
|---|---|---|
| Package root | `cab_vision/__init__.py` | ✅ |
| Visual-causal task schema | `cab_vision/schemas/task_schema.py` | ✅ |
| Causal metrics | `cab_vision/eval/metrics.py` | ✅ |
| Leakage / validation guards | `cab_vision/validation/leakage_checks.py` | ✅ |
| Sample tasks (10, placeholder images) | `data/cab_vision/examples/sample_tasks.jsonl` | ✅ |
| Schema/validation tests | `tests/test_cab_vision_schema.py` (16) | ✅ |
| Metrics tests | `tests/test_cab_vision_metrics.py` (14) | ✅ |
| pytest path for root package | `pyproject.toml` (`pythonpath = ["src", "."]`) | ✅ edited |

### Schema (`VisualCausalTask`)
Strict pydantic v2 (`extra="forbid"`), mirroring `causal_agent_bench.schemas`. Fields: `task_id`,
`family` (6 families), `split` (train/dev/test/hidden_test), `domain`, `question`, `images`
(`VisualAsset` with `is_placeholder`), `answer_choices` (`AnswerChoice` with `is_spurious_trap` /
`is_valid_action`), `gold_index`, paired fields (`condition`, `pair_id`), intervention fields
(`intervention_type`, `changed_factor`, `expected_answer_change`), `gold_causal_chain`. Constructor-level
validators enforce contiguous unique choices, gold-in-range, pair/condition for paired families, and a
valid action for action tasks.

### Metrics (`cab_vision.eval.metrics`)
`accuracy`, `accuracy_by_condition`, `causal_consistency` (answer changes iff structure changes),
`intervention_sensitivity` (changes when it should), `spurious_cue_resistance` (avoids the trap),
`action_validity` (chosen action permissible), `summarize` (full panel). Empty populations return
`None` (distinguishes "0.0" from "not measured").

### Validation / leakage (`cab_vision.validation.leakage_checks`)
Per-task: no gold-answer/spoiler text in prompt; image exists or is an explicit placeholder; valid
family; valid split; well-formed choices; intervention/pair fields present. Dataset-level: duplicate
`task_id` detection + **cross-split pair leakage** (same `pair_id` in >1 split).

---

## Verified results (this session)

```
$ pytest tests/test_cab_vision_schema.py tests/test_cab_vision_metrics.py -n0 -q
..............................                                            [100%]
30 passed in ~0.1s

$ pytest tests/test_import.py tests/test_schemas.py -n0 -q   # existing suite unaffected
3 passed

sample dataset: tasks=10 | errors=0 | ok=True
families covered: action_selection, causal_chain, counterfactual_scene,
                  intervention_consistency, spurious_cue, visual_intervention   (all 6)
domains covered:  driving, household, medical, navigation, physical, safety     (6)
```

The prototype demonstrates the **whole evaluation loop in miniature**: load JSONL → schema-validate →
leakage-check → score with causal metrics — entirely offline and deterministic.

---

## Requirements checklist (Part 11)
- [x] Draft visual task schema.
- [x] 5–10 toy examples with placeholder image paths.
- [x] Validator: no ground-truth in prompt; image path exists or explicit placeholder; valid family;
      intervention fields exist; valid answer choices; valid split.
- [x] Metrics: accuracy, causal consistency (paired), intervention sensitivity, spurious-cue resistance
      (+ action validity, by-condition accuracy).
- [x] Unit tests for schema, validation, and metrics (30 total).
- [x] Tests run and pass; existing suite not broken.

---

## What is intentionally NOT done (and why)
- **No real images** — placeholders only (`is_placeholder: true`). Real assets = Phases 3–5.
- **No VLM provider adapters** — Phase 6; needs multimodal `Message` + SDKs.
- **No bootstrap CIs in the metric panel yet** — wire `metrics/statistics.py` in Phase 8.
- **No network / no paid calls** — by design.

---

## Immediate next steps
1. `cab_vision/providers/mock_vlm.py` + `cab_vision/eval/run_eval.py` → first offline end-to-end run.
2. `cab_vision/validation/visual_asset_checks.py` (pHash dedup) for when real images arrive.
3. `make cabv-validate` / `make cabv-smoke` targets.
4. Phase 3 synthetic renderer for the first real images.

See `CVPR_IMPLEMENTATION_ROADMAP.md` for the full plan and `CVPR_REPO_CHANGESET.md` for the file map.
