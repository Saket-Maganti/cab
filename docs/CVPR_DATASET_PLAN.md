# CAB-Vision Dataset Construction Plan

Three target tiers (MVP → strong → dream), domain analysis, schema, splits, leakage
prevention, human validation, QC, data card, ethics. Builds on the existing data discipline
(`data/frozen/`, `safety/static_leakage.py`, `safety/human_validation_*`, `contamination/audit.py`).

---

## 1. Minimum viable dataset (MVP — submit-able)
- **Size:** 1,000–3,000 items.
- **Families:** 1, 2, 3, 4, (+6 pairs). (Family 5 optional.)
- **Images:** image-based (single + before/after pairs). Mostly **hybrid**: synthetic for
  single-factor control + curated real photos.
- **Models:** ≥5 VLMs (≥2 closed, ≥3 open). See `CVPR_BASELINES_PLAN.md`.
- **Human validation:** ≥300-item validated subset with IAA.
- **Why this is the floor:** below this, reviewers call it a pilot/workshop artifact.

## 2. Strong CVPR dataset
- **Size:** 5,000–10,000 items.
- **Families:** 1–6.
- **Domains:** ≥4 visual domains.
- **Human validation:** larger validated subset; ambiguity adjudication; paired observational/
  interventional throughout family 6 + counterfactual family 2.
- **Baselines:** robust (≥3 frontier closed + ≥4 open + all ablations).

## 3. Highest-ceiling ("dream") dataset
- **Size:** 10,000+ items.
- **Modalities:** images **+ short videos + embodied/sim** action tasks.
- **Composition:** real + synthetic hybrid.
- **Annotations:** causal-graph annotations, intervention annotations, action-validity annotations,
  expert validation (e.g., clinician for medical, driving-safety expert for driving).
- **Release:** public leaderboard + hidden test (adapt `docs/leaderboard_schema_v1.json`,
  `docs/LEADERBOARD_PROTOCOL.md`).

---

## 4. Domain analysis

For each: CVPR relevance · causal value · data sources · annotation needs · risks · in v1?

### Physical reasoning scenes — **v1 ✅**
- **CVPR relevance:** intuitive physics is a live CV topic (stability, support, collision).
- **Causal value:** clean do-interventions (remove support → fall); single-factor edits trivial in a renderer.
- **Sources:** Blender/PyBullet/ThreeDWorld renders; CLEVRER-style; own captures.
- **Annotation:** programmatic gold from the simulator state (cheap, exact).
- **Risks:** "too synthetic/toy" → pair with real photos of real support/stacking.
- **Verdict:** include; anchor family 1 & 6.

### Household / robotics / manipulation — **v1 ✅**
- **CVPR relevance:** embodied AI, affordances, manipulation.
- **Causal value:** tool-moved → task feasible? object removed → consequence?
- **Sources:** AI2-THOR/Habitat/robotics sims; Ego4D-style real (license-permitting); own.
- **Annotation:** sim ground truth + human for real.
- **Risks:** licensing of real egocentric data.
- **Verdict:** include; anchor family 4.

### Autonomous-driving-style scenes — **v1 ✅**
- **CVPR relevance:** core CV community; safety-critical decisions.
- **Causal value:** occluded signal → safe action; spurious red object ≠ traffic light.
- **Sources:** CARLA/sim; permissively-licensed dashcam; nuScenes/BDD-style (check license/redistribution).
- **Annotation:** sim ground truth; human safety-action labels for real.
- **Risks:** redistribution license; safety claims must be careful.
- **Verdict:** include; anchor families 3 & 4.

### Medical / diagnostic visual triage — **v2 / stretch**
- **CVPR relevance:** medical imaging is huge at CVPR; triage decisions are causal.
- **Causal value:** artifact vs lesion (spurious cue); accept/defer/request-expert (abstention).
- **Sources:** open de-identified sets (e.g., chest X-ray public sets) **with artifact annotations**;
  synthetic artifacts overlaid on normal scans.
- **Annotation:** **expert** (radiologist) — expensive; required for credibility.
- **Risks:** ethics, label noise, over-claiming clinical utility. Keep as "triage decision under
  visual ambiguity," not diagnosis.
- **Verdict:** stretch; high payoff for the abstention/defer metric but gated on expert time.

### Safety / risk scenes — **v1 ✅**
- **CVPR relevance:** scene-understanding for safety.
- **Causal value:** is there an actual hazard vs a hazard *symbol*?
- **Sources:** curated photos, compositing.
- **Risks:** subjectivity → strong rubric.
- **Verdict:** include; anchor family 3.

### Object affordance scenes — **v1/v2**
- **CVPR relevance:** affordance learning.
- **Causal value:** can the action be completed if the tool is moved/blocked?
- **Sources:** sim + real.
- **Verdict:** fold into household/action family.

### Document / chart visual reasoning — **CUT for v1**
- **Why cut:** weak causal/intervention story; risks "this is OCR/text, not visual causality."
- **Verdict:** exclude (re-evaluate later only if a causal angle emerges).

### Synthetic CLEVR-like scenes — **v1 ✅ (only as controlled complement)**
- **CVPR relevance:** acceptable *if* combined with realistic images; alone reads as toy.
- **Causal value:** perfect single-factor intervention control + free programmatic labels → ideal for
  family 6 validity and the intervention-isolation proof.
- **Verdict:** include as the *controlled* arm; never the whole benchmark.

---

## 5. Dataset schema, IDs, splits

- **Schema:** `cab_vision/schemas/task_schema.py` (`VisualCausalTask`). JSONL on disk.
- **Example IDs:** `cabv_<domain>_<family>_<nnn>`; paired members share `pair_id`
  (`pair_<concept>_<nnn>`) and use suffixes (`..._obs` / `..._int`, or `_before`/`_after`).
- **Splits:** `train`, `dev`, `test`, **`hidden_test`** (labels withheld; served via leaderboard).
  - Split by **scene/source**, not by item, so a pair never straddles splits (enforced by
    `validate_dataset` cross-split-pair-leakage check in `cab_vision/validation/leakage_checks.py`).
  - Suggested ratio v1: train 50% / dev 10% / test 25% / hidden_test 15%.

## 6. Leakage & contamination prevention (a current strength — extend it)
- **Label-in-prompt:** `check_no_answer_in_prompt` (done).
- **Cross-split pair leakage:** `validate_dataset` (done).
- **Image dedup:** sha256 exact + **perceptual hash (pHash) near-dup** across splits (ADD:
  `cab_vision/validation/visual_asset_checks.py`).
- **Pretraining contamination:** reverse-image / pHash against known public sets; prefer **synthetic or
  own-captured** images for the hidden test (extend `contamination/audit.py`).
- **Text-shortcut:** the text-only & caption-only ablations are a *release gate* (see eval protocol).

## 7. Human validation protocol (reuse `safety/human_validation_*`, rewrite rubric)
- **Sample:** stratified by family × domain; ≥300 (MVP), scale up for strong tier.
- **Each item, 3 annotators rate:** (a) is the question answerable **only with the image**? (b) is the
  gold answer correct? (c) for interventions: does the edit change **only** the stated factor
  (single-factor validity)? (d) is the item unambiguous?
- **Keep** items with ≥2/3 agreement on (a)–(d); **adjudicate** ties; **drop** ambiguous.
- **Report:** Cohen's/Fleiss' κ (machinery in `analysis/human_validation.py`).

## 8. Ambiguity handling
- Allow a "cannot be determined" option where genuinely under-determined, but never as the gold for a
  determinable item. Items where annotators split on the gold are dropped or sent to expert adjudication.

## 9. Annotation guidelines (new doc: `docs/CABV_ANNOTATION_GUIDE.md`)
- Define each family, the single-factor rule, trap-cue rule, action-validity rule, and worked
  positive/negative examples. Mirror the rigor of `docs/HUMAN_VALIDATION_ANNOTATION_GUIDE.md`.

## 10. Quality-control checks (gate before freeze)
- All `cab_vision/validation` checks pass (0 errors).
- pHash near-dup rate below threshold across splits.
- Text-only ablation ≤ chance + ε on the test split.
- Per-family/per-domain counts meet minimums.
- Human-validated subset κ ≥ target.

## 11. Data card (new: `data/cab_vision/DATA_CARD.md`)
Adapt `docs/DATASET_CARD.md` + `data/frozen/pilot_v0.1/dataset_card.md`: sources, licenses per source,
synthetic-vs-real counts, splits, known limitations, intended use, contamination audit summary.

## 12. Ethics statement (new: `data/cab_vision/ETHICS.md`)
Adapt `docs/ETHICS_AND_LIMITATIONS.md`: medical items are **triage-decision research, not diagnosis**;
driving items are **not** a deployment safety certification; de-identification for any real imagery;
license compliance; dual-use note. Required for CVPR.
