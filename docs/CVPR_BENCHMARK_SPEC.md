# CAB-Vision Benchmark Specification

**Name:** Causal Vision-Agent Bench (CAB-Vision / CausalVisionBench).
**One-line:** Do multimodal agents make *causally valid* visual decisions — under
interventions, counterfactual scene edits, spurious cues, and action constraints?

**Hard invariant (CVPR CRITICAL):** every task must be **image-central** — *not*
answerable from the question text alone. Enforced empirically by the text-only and
caption-only ablations (`CVPR_EVALUATION_PROTOCOL.md`) and structurally by
`cab_vision/validation/leakage_checks.py`.

Schema reference: `cab_vision/schemas/task_schema.py` (prototyped).
Sample data: `data/cab_vision/examples/sample_tasks.jsonl` (10 toy items, placeholder images).

---

## Common record (all families)

```json
{
  "task_id": "cabv_<domain>_<family>_<n>",
  "family": "visual_intervention | counterfactual_scene | spurious_cue | action_selection | causal_chain | intervention_consistency",
  "split": "train | dev | test | hidden_test",
  "domain": "physical | household | driving | safety | navigation | medical | ...",
  "question": "<text that does NOT contain the answer>",
  "images": [{"asset_id": "...", "path": "...", "role": "primary|before|after|context|video", "is_placeholder": false, "sha256": "..."}],
  "answer_choices": [{"index": 0, "text": "...", "is_spurious_trap": false, "is_valid_action": null}],
  "gold_index": 1,
  "condition": "observational | interventional (paired families)",
  "pair_id": "links paired members",
  "intervention_type": "remove|block|move|replace|occlude|tilt|...",
  "changed_factor": "the single altered factor",
  "expected_answer_change": "yes | no | unclear",
  "gold_causal_chain": ["step1", "step2"],
  "is_synthetic": true, "human_validated": false, "tags": [], "metadata": {}
}
```

**Output format (model):** for MC families, a single chosen `index` (+ optional free-text
rationale). For `causal_chain`, a free-text/selected explanation. For `action_selection`, the
chosen action index. **Ground truth:** `gold_index` (+ `valid_action_indices`, `spurious_index`,
`gold_causal_chain` as applicable).

---

## Task Family 1 — Visual Intervention Reasoning **(v1, CVPR CRITICAL)**
*"If object X is removed/blocked/moved/replaced, what happens to Y?"*

- **Input:** one image + question naming an intervention on a visible object.
- **Output:** MC index (3–4 choices).
- **Ground truth:** `gold_index`; `intervention_type`, `changed_factor`, `expected_answer_change`.
- **Metric:** interventional accuracy; contributes to intervention-sensitivity when paired with
  an un-intervened variant.
- **Required visual assets:** scenes with clear physical/functional dependencies (support, occlusion,
  containment, tool-affordance).
- **Synthetic / real / hybrid:** **hybrid** — synthetic (renderer: blender/CLEVR-style/sim) for
  controlled single-factor edits + real photos for realism.
- **Modality:** image-only (single).
- **Min / ideal examples:** 300 / 1500.
- **Expected failure modes:** model answers from object priors ("a ball usually rolls") ignoring the
  stated intervention; ignores occlusion; defaults to "cannot tell."

Example: `cabv_phys_intv_001`, `cabv_house_intv_001` in the sample file.

## Task Family 2 — Counterfactual Scene Reasoning **(v1, CVPR CRITICAL)**
*Before/after image pair → identify the causal consequence; distinguish a visual difference from a causal effect.*

- **Input:** image **pair** (`role: before` / `after`) + question.
- **Output:** MC index.
- **Ground truth:** `gold_index`; pair members share `pair_id`; `condition` ∈ {observational(before),
  interventional(after)}; `changed_factor`, `expected_answer_change`.
- **Metric:** counterfactual accuracy + **causal consistency** over the pair (answer changes iff the
  causal structure changed) — `cab_vision.eval.metrics.causal_consistency`.
- **Required assets:** matched pairs differing by exactly one edit (object removed, mask inserted,
  lighting/obstruction changed). The *single-factor* property is the validity crux.
- **Synthetic / real / hybrid:** **hybrid**; synthetic gives perfect single-factor control, inpainting
  edits on real images add realism (must be human-validated for artifacts).
- **Modality:** image-pair.
- **Min / ideal:** 200 pairs / 1000 pairs.
- **Failure modes:** flags any pixel difference as causally relevant; misses the causal edit because it
  is subtle; lighting/cosmetic edits wrongly change the decision.

Example: `cabv_house_cf_before_001` / `cabv_house_cf_after_001`.

## Task Family 3 — Spurious Visual Cue Traps **(v1, CVPR CRITICAL)**
*Misleading correlated object present (fire extinguisher / umbrella / smoke-like fog / red object /
imaging artifact). Model must not infer the cause from the cue.*

- **Input:** single image with a salient but causally irrelevant cue + question.
- **Output:** MC index, where one option (`is_spurious_trap: true`) is what the cue suggests.
- **Ground truth:** `gold_index` (correct), `spurious_index` (trap).
- **Metric:** **spurious-cue resistance** = fraction not choosing the trap
  (`cab_vision.eval.metrics.spurious_cue_resistance`); also report accuracy.
- **Required assets:** scenes deliberately pairing a salient cue with the *absence* of its usual cause.
- **Synthetic / real / hybrid:** **hybrid**; compositing/inpainting a cue into a scene gives control,
  real photos give credibility.
- **Modality:** image-only.
- **Min / ideal:** 250 / 1200.
- **Failure modes:** cue capture (extinguisher ⇒ "fire"); over-correction (always rejects the cue);
  saliency bias.

Example: `cabv_safety_spur_001` (fire extinguisher, no fire), `cabv_med_spur_001` (X-ray artifact).

## Task Family 4 — Vision-Agent Action Selection **(v1, CVPR CRITICAL)**
*Choose the next action given causal constraints in the scene (robot/driving/triage/navigation).*

- **Input:** single image (or short context set) + question asking for the **action**.
- **Output:** chosen action index.
- **Ground truth:** `gold_index`; choices flagged `is_valid_action` (set of causally permissible actions).
- **Metric:** **action validity** = chosen ∈ valid set (`cab_vision.eval.metrics.action_validity`);
  plus exact-match accuracy to the single best action.
- **Required assets:** hazard/affordance scenes (oil spill, occluded signal, unstable support, spill).
- **Synthetic / real / hybrid:** **hybrid**; simulators (CARLA-style driving, robotics sims) + curated photos.
- **Modality:** image-only or image+short context; optionally embodied/sim later.
- **Min / ideal:** 250 / 1200.
- **Failure modes:** fluent-but-unsafe action; ignoring occlusion risk; choosing a "describe the scene"
  non-action; over-abstention.

Example: `cabv_nav_action_001` (oil spill → take dry detour).

## Task Family 5 — Visual Causal Chain Explanation *(v1 optional / v2)*
*Produce or select a short causal chain grounded in image evidence; eval checks the chain supports the action.*

- **Input:** single image + "why will Z happen?"
- **Output:** ordered free-text chain **or** MC over candidate chains.
- **Ground truth:** `gold_causal_chain` (ordered steps) + distractor chains.
- **Metric:** explanation faithfulness (MC chain accuracy in v1; rubric/LLM-judge + grounding overlap in v2).
- **Required assets:** scenes with a legible multi-step mechanism (dominoes, pulley, ramp).
- **Synthetic / real / hybrid:** hybrid.
- **Modality:** image-only.
- **Min / ideal:** 150 / 800.
- **Failure modes:** plausible-but-ungrounded story; correct answer with wrong chain; ordering errors.

Example: `cabv_phys_chain_001` (dominoes).

## Task Family 6 — Intervention Consistency Pairs **(v1, the differentiator)**
*Same scene asked observationally and interventionally; the model should change its answer only when the
causal structure changes.*

- **Input:** two questions over related images sharing `pair_id`, with `condition` ∈ {observational,
  interventional}.
- **Output:** an index per member.
- **Ground truth:** per-member `gold_index`; interventional member carries `expected_answer_change`.
- **Metric:** **causal consistency** + **intervention sensitivity** (`cab_vision.eval.metrics`).
- **Required assets:** an observational scene + a minimally-edited interventional counterpart.
- **Synthetic / real / hybrid:** **hybrid** (synthetic preferred for clean single-factor control).
- **Modality:** image (paired queries).
- **Min / ideal:** 200 pairs / 1000 pairs.
- **Failure modes:** prior-locked (never changes), over-reactive (always changes), inconsistent across
  the pair while each answer looks locally plausible.

Example: `cabv_drive_obs_001` / `cabv_drive_intv_001` (signal visible vs occluded).

---

## Coverage matrix (v1 target)

| Family | Modality | Synthetic/Real | Metric anchor | Min | Ideal | In v1 |
|---|---|---|---|--:|--:|:--:|
| 1 Visual Intervention | image | hybrid | interventional acc | 300 | 1500 | ✅ |
| 2 Counterfactual Scene | image-pair | hybrid | counterfactual acc + consistency | 200pr | 1000pr | ✅ |
| 3 Spurious Cue | image | hybrid | cue resistance | 250 | 1200 | ✅ |
| 4 Action Selection | image(+ctx) | hybrid | action validity | 250 | 1200 | ✅ |
| 5 Causal Chain | image | hybrid | faithfulness | 150 | 800 | ➖ optional |
| 6 Intervention Consistency | paired | hybrid (synth pref) | consistency + sensitivity | 200pr | 1000pr | ✅ |

**v1 minimum total ≈ 1,000–1,500 items** (families 1–4 + 6). **Strong CVPR ≈ 5,000–10,000**
(add family 5, more domains, human validation, more pairs). See `CVPR_DATASET_PLAN.md`.

---

## Anti-text-shortcut design rules (enforced)
1. Gold answer text must never appear in `question` (`check_no_answer_in_prompt`).
2. Choices must be plausible without the image (so a blind guesser is at chance).
3. For pairs, the two questions differ only in the intervention clause; the image carries the change.
4. Every family ships with a **text-only control**: if a model answers it without the image above
   chance, the item is flagged and removed (gate in `CVPR_EVALUATION_PROTOCOL.md`).
