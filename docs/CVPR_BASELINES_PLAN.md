# CAB-Vision Baselines Plan

Goal: a baseline suite strong enough that no reviewer says "weak/few baselines," and structured so
the **modality ablations carry the scientific argument** (visual centrality + causal failure).

Reuse target: the adapter/config/cost patterns in `src/causal_agent_bench/agents/llm_clients.py`,
`agents/llm_adapters.py`, `runners/costing.py`, `safety/run_cost_estimator.py`,
`configs/model_pricing.yaml`. The key extension: **image input** (multimodal `Message` content).

> Cost discipline (inherited): paid calls disabled by default; estimate cost with the no-run estimator
> before any run; cache every raw output; open-weight models first.

---

## 1. Closed-source / API VLM baselines
*(Use whatever is SOTA at eval time; do not hardcode availability assumptions.)*
- Frontier multimodal models from the major providers (OpenAI GPT-4o/GPT-5-class; Anthropic Claude
  multimodal; Google Gemini multimodal), plus any other strong API VLM available.
- **Adapter:** `cab_vision/providers/openai_vlm.py`, `anthropic_vlm.py`, `gemini_vlm.py` — subclass a
  shared `cab_vision/providers/vlm_adapter.py` that sends `{image, question, choices}` and returns a
  parsed index + rationale + token usage.
- **Reuse:** `Message`/`ModelConfig`/`TokenUsage` from `agents/llm_clients.py` (extend content to image parts).
- **Cost:** the dominant line item; estimate before running; cache outputs; run open models first to debug.

## 2. Open-source VLM baselines
- **Qwen-VL family**, **InternVL family**, **LLaVA family**; **Video-LLaVA / equivalent** if videos are
  included (dream tier).
- **Adapter:** `cab_vision/providers/qwen_vl.py`, `internvl.py`, `llava.py` (HF/transformers; lazy import
  so the no-run path stays light — mirror the lazy pattern in `agents/llm_adapters.py::LocalHFChatAgent`).
- **Cost:** local GPU compute only (free of API spend) → use these for the bulk of dev iteration.

## 3. Ablation / control baselines (these are the experiment, not garnish)
| # | Baseline | Purpose | Adapter / mode |
|---|---|---|---|
| 1 | **Text-only question** | leakage gate; lower bound | drop image from payload |
| 2 | **Caption-only** | is it visual? | run captioner → feed caption text |
| 3 | **Image + question (direct VLM)** | the real condition | standard VLM call |
| 4 | **Image-pair + question** | paired families | send both members |
| 5 | **CoT-disabled / concise** | does reasoning help? | system prompt forbids long CoT |
| 6 | **Tool-free vs tool-using agent** | does agentic scaffolding fix it? | single-shot vs ReAct-style loop (reuse trajectory logging) |
| 7 | **Oracle-caption** | perception vs causal | feed gold/human caption instead of image |
| 8 | **Human baseline** | ceiling | small expert subset via the human-validation harness |
| 9 | **Random** | floor | uniform over choices |
| 10 | **Majority-class** | floor (label bias check) | most-frequent gold per family |

Random + majority-class also **audit dataset balance** (if majority-class is high, choices are imbalanced).

---

## 4. Per-baseline spec (uniform)
For each baseline document: **how it runs** (config in `configs/cabv_*.yaml`), **adapter needed**
(above), **expected cost** (no-run estimate first), **CAB reuse** (`llm_clients`, `costing`,
`run_cost_estimator`, `model_pricing.yaml`), **logs saved** (raw output, parsed index, rationale, token
usage, latency, image hash, seed → trajectory/result records), **leakage avoidance** (never pass
`gold_index`/`spurious_index`/`valid_action_indices` into the prompt; validated by
`cab_vision/validation`), **reproducibility** (pin model version/date, seed, prompt hash; cache raw
outputs; extend `release/repro_bundle.py`), **tables/figures** (feed `cab_vision/eval/metrics.summarize`
→ `reports/` builders adapted from `analysis/tables.py`, `analysis/figures.py`).

---

## 5. Prompting standardization (so comparisons are fair)
- One shared MC prompt template per family; same system message across models; choice order randomized
  by a per-item seed (fixed across models so all see the same permutation).
- Forbid the model from asking for the answer or restating choices as the answer.
- Two prompt variants max (default + CoT) reported; no per-model prompt tuning (disclose if any).

## 6. Minimum vs ideal baseline coverage
- **MVP:** ≥5 models (≥2 closed, ≥3 open) + ablations 1,2,3,7,9,10.
- **Strong:** ≥7 models (≥3 closed, ≥4 open) + all ablations + human baseline on a subset.
- **Dream:** + video VLMs + embodied/sim agent + larger human study.

## 7. Output artifacts
- `results/cabv/<run_id>/raw/*.json` (cached model outputs), `scores.jsonl` (per-item),
  `summary.json` (metric panel + CIs), `reports/cabv/RESULTS.md` (tables), `figures/cabv/*` (money plot,
  decomposition, per-family bars, consistency, spurious-cue, ablation).
