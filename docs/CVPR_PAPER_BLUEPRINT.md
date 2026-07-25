# CAB-Vision CVPR Paper Blueprint

CVPR-style (8 pages + refs, double-blind, supplementary allowed). Write it as a **computer-vision**
paper whose contribution is a *finding about visual causal reasoning*, instrumented by a dataset —
**not** an "LLM eval" paper. Replaces the deleted `paper/main.tex` and the NeurIPS blueprints
(`paper/NEURIPS_PAPER_BLUEPRINT.md` → deprecate).

**Title (lead):** *When Seeing Is Not Reasoning: A Benchmark for Causal Decision-Making in
Vision-Language Agents.* (Alt: *Causal Vision-Agent Bench: Do Multimodal Agents Make Causally Valid
Visual Decisions?*)

**Abstract (message):** VLMs describe scenes well but choose causally invalid answers/actions when
visual evidence conflicts with priors, spurious cues, interventions, or counterfactual edits. CAB-Vision
pairs observational with interventional visual decisions across N domains; SOTA VLMs drop Δ pts from
observational to interventional, the gap is **not** closed by oracle captions (so it is visual-causal,
not linguistic), causal-consistency is near chance even at ≥90% recognition, and agentic prompting
doesn't fix it. We release data, a hidden test, and a leaderboard.

---

## Section-by-section

### 1. Introduction
- **Message:** recognition ≠ causal decision; existing VLM benchmarks test recognition/caption/grounding/
  instruction-following/embodied-success, not *causal validity of decisions*.
- **Evidence:** teaser money figure + one striking gallery example.
- **Figures/tables:** Fig 1 (teaser/overview).
- **Reviewer objection:** "isn't this VQA?" → answer in the first column with the modality ablation preview.
- **CV framing:** open with a *pixel-level* example (occlusion/support), not a chat transcript.

### 2. Related Work
- **Message:** map the gap. Buckets: visual QA/recognition; visual grounding/referring; intuitive
  physics/CLEVRER-style; causal/counterfactual VQA; robustness/spurious-correlation (e.g., VQA-CP);
  embodied/decision benchmarks; VLM agents.
- **Evidence:** comparison table with columns {visual?, interventional?, counterfactual pairs?, decision/
  action?, paired-consistency metric?, spurious-cue control?}; CAB-Vision uniquely fills the last cells.
- **Figures/tables:** Tab 1 (related-work matrix; adapt `docs/RELATED_WORK_MATRIX.md`).
- **Objection:** "causal VQA exists." → emphasize *paired consistency + decision/action + cue-conflict*.
- **CV framing:** cite CV venues, not just NLP.

### 3. Benchmark Design
- **Message:** the causal-decision construct; observational↔interventional pairing; anti-text-shortcut rules.
- **Evidence:** schema (`cab_vision/schemas/task_schema.py`), the single-factor intervention principle.
- **Figures/tables:** Fig 2 (benchmark overview / pipeline).
- **Objection:** "answerable from text." → §6 ablation forward-ref + design rules.

### 4. Task Families
- **Message:** the 4–6 families and what each isolates.
- **Evidence:** one visual example per family (image + question + choices + gold).
- **Figures/tables:** Fig 3 (example task figure, one panel per family).
- **Objection:** "toy." → show real-image examples.

### 5. Dataset Construction
- **Message:** sources (real+synthetic), single-factor edits, splits incl. hidden test, leakage &
  contamination control, human validation.
- **Evidence:** dataset-statistics table; IAA (κ); pHash dedup; contamination audit.
- **Figures/tables:** Tab 2 (dataset statistics: family×domain×split, real/synthetic, n, κ).
- **Objection:** "leakage/contamination/ambiguity." → `cab_vision/validation` + human validation + audit.

### 6. Evaluation Protocol
- **Message:** metric panel beyond accuracy; the modality ablations as the visual-centrality proof.
- **Evidence:** metric formulas (`CVPR_EVALUATION_PROTOCOL.md`); statistical plan (bootstrap/paired).
- **Figures/tables:** Tab 3 (modality ablation: text-only/caption-only/image+Q/oracle-caption).
- **Objection:** "no CIs / shortcuts." → CIs everywhere + ablation gate.

### 7. Models and Baselines
- **Message:** strong closed + open VLMs + controls + human.
- **Evidence:** model list, prompting standardization, cost/repro notes.
- **Figures/tables:** part of Tab 4.
- **Objection:** "weak baselines." → ≥6 models incl. frontier + human.

### 8. Results
- **Message:** obs vs int gap; cue capture; consistency collapse; agentic doesn't fix it; per-domain.
- **Evidence:** main results table with CIs; money figure; per-family bars.
- **Figures/tables:** Fig 4 (money plot), Tab 4 (main results), Fig 5 (per-family/consistency).
- **Objection:** "unsurprising / cherry-picked." → pre-registered claims + significance + multiple models.

### 9. Failure Analysis
- **Message:** *why* models fail — perception vs causal decomposition + taxonomy.
- **Evidence:** decomposition (recognition correct, decision wrong); tagged failure rates.
- **Figures/tables:** Fig 6 (perception-vs-causality decomposition), Fig 7 (visual failure gallery),
  Fig 8 (spurious-cue failure).
- **Objection:** "shows that, not why." → this section is the answer; reuse `analysis/failure_gallery_doc.py`.
- **CV framing:** this section is what makes it a CV paper, not a leaderboard.

### 10. Limitations
- Synthetic share; domain coverage; "causal" is operationalized via controlled single-factor edits, not a
  full SCM; medical = triage research not diagnosis; API model drift. (Adapt `docs/ETHICS_AND_LIMITATIONS.md`.)

### 11. Ethics
- De-identification; licensing; dual-use; no deployment-safety claims; medical disclaimer.

### 12. Conclusion
- Seeing ≠ reasoning; release data + hidden test + leaderboard; call to build causally robust VLMs.

---

## Figure / table inventory (build via `reports/` + `figures/`)
| ID | Asset | Source builder (adapt) |
|---|---|---|
| Fig 1 | Teaser / money plot | `analysis/figures.py` |
| Fig 2 | Benchmark overview / pipeline | new schematic (cf. `figures/figure1_benchmark_schematic.md`) |
| Fig 3 | Example task per family | new (image panels) |
| Fig 4 | Obs vs Int money plot | `analysis/figures.py` (cf. existing `figure2_clean_vs_intervention_success`) |
| Fig 5 | Per-family / consistency | `analysis/figures.py` (cf. `figure3_intervention_family_breakdown`) |
| Fig 6 | Perception-vs-causality decomposition | new |
| Fig 7 | Visual failure gallery | `analysis/failure_gallery_doc.py` |
| Fig 8 | Spurious-cue failure | new |
| Tab 1 | Related-work matrix | `docs/RELATED_WORK_MATRIX.md` |
| Tab 2 | Dataset statistics | `analysis/tables.py` |
| Tab 3 | Modality ablation | `analysis/tables.py` |
| Tab 4 | Main results (+ CIs, human) | `analysis/tables.py` |

The existing `figures/figure4_ranking_instability.*` repurposes directly into the V8 "standard accuracy
doesn't predict causal competence" plot.

## How to keep it a CV paper (checklist)
- Lead and close with pixels, not transcripts.
- Every claim tied to a visual figure.
- Cite CV venues; position vs CV benchmarks.
- Failure analysis (Sec 9) ≥ 1.5 pages with visual evidence.
- Supplementary: full per-domain tables, more gallery, prompts, repro.
