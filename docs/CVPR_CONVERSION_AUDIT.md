# CVPR Conversion Audit — CausalAgentBench → Causal Vision-Agent Bench

**Auditor role:** CVPR senior AC / benchmark author / VLM + causality researcher.
**Date:** 2026-06-21. **Audited commit context:** `main` (working tree, paper `.tex` deleted, no provider runs).
**Verdict scale:** `NOT_CVPR_RELEVANT` · `WEAK_CVPR_WORKSHOP_ONLY` · `POSSIBLE_CVPR_WORKSHOP` · `POSSIBLE_CVPR_MAIN_WITH_MAJOR_CONVERSION` · `CVPR_MAIN_COMPETITIVE` · `CVPR_MAIN_SAFE`

---

## 0. TL;DR

The repository is a **mature, text/tool-only LLM-agent benchmark** with **world-class
research-engineering discipline** and **zero computer-vision content** (0 image/vision
references in `src/`; deps are `numpy/pandas/scipy` only — no `torch`/`Pillow`/`transformers`).
As-is, it is **`NOT_CVPR_RELEVANT`**: CVPR will reject anything where the central object of
study is text-tool agents.

However, the *infrastructure* (paired clean/intervention design, the ACRS metric pattern,
provider abstraction, leakage guards, claim ledger, no-run validation, reproducibility
bundles, human-validation protocols) is **directly transferable** to a vision benchmark and
would take a typical CVPR benchmark team months to rebuild. With a genuine visual-causal
dataset + VLM baselines layered on top, the ceiling becomes
**`POSSIBLE_CVPR_MAIN_WITH_MAJOR_CONVERSION` → `CVPR_MAIN_COMPETITIVE`**.

| | Verdict |
|---|---|
| **Current ceiling (no conversion)** | `NOT_CVPR_RELEVANT` (text agents) |
| **Ceiling after light visual tasks bolted on** | `WEAK_CVPR_WORKSHOP_ONLY` |
| **Ceiling after full conversion (1–3k real visual-causal items + 5–8 VLMs)** | `POSSIBLE_CVPR_MAIN_WITH_MAJOR_CONVERSION` |
| **Ceiling at the dream version (5–10k, real+synthetic, human validation, leaderboard)** | `CVPR_MAIN_COMPETITIVE` (not "safe" — benchmark papers rarely are) |

---

## 1. What the project currently is

A Python research package (`src/causal_agent_bench/`, pkg `causal-agent-bench` v0.1.0,
Python 3.11+) that evaluates **tool-using language agents** under **controlled
perturbations ("interventions")** using a **paired clean/intervention design**.

- **Object of study:** text agents that emit JSON tool calls in simulated environments
  (travel, shopping, calendar, a "web-shadow" fake site). See `data/sample/instances.jsonl`.
- **Core scientific construct:** ACRS = `intervention_success / clean_success`
  (`src/causal_agent_bench/metrics/causal_robustness.py:13`). Hypothesis: outcome-success
  leaderboards overstate skill; paired perturbations reveal ranking instability.
- **15 intervention families**, *all textual/tool/web* (`schemas.py:8`): `tool_removal`,
  `tool_failure`, `tool_corruption`, `memory_corruption`, `observation_conflict`,
  `web_broken_link`, `web_stale_page`, … **None are visual.**
- **Maturity:** 120 test files (`tests/`), ~80 governance modules (`src/causal_agent_bench/safety/`),
  135 docs, frozen datasets (`data/frozen/pilot_v0.1/`), CI workflows, claim ledger, evidence dashboard.
- **Empirical status:** **0 provider-backed runs.** `docs/FOCUSED_PROJECT_THESIS.md` and
  `MASTER_STATUS.*` confirm: "provider-backed evidence is 0", NeurIPS gate `NOT_READY`.
  Everything to date is "engineering-only / no-run".
- **Target venue today:** NeurIPS/ICLR-style (`docs/ROADMAP_TO_NEURIPS_2027.md`,
  `paper/NEURIPS_PAPER_BLUEPRINT.md`). Paper `.tex` sources were deleted (git status shows `D paper/main.tex`).

---

## 2. Asset-by-asset reuse verdict

Legend: **KEEP** (reuse ~as-is) · **MODIFY** (reuse with vision changes) · **CUT** (not for CVPR v1) · **ADD** (must build).

### 2A. Directly reusable (the crown jewels) — **KEEP / MODIFY**

| Asset | File(s) | Verdict | Why it transfers |
|---|---|---|---|
| Paired clean/intervention design | `schemas.py` `BenchmarkInstance.condition`, `metrics/causal_robustness.py` | **MODIFY** | The single most valuable idea. Becomes observational/interventional **visual** pairs. The ACRS ratio + per-family degradation logic ports almost verbatim (`agent_robustness()`). |
| Provider abstraction | `agents/llm_clients.py` (`Message`, `ModelConfig`, `TokenUsage`), `agents/llm_adapters.py` (OpenAI/Anthropic/Gemini/OpenRouter/local) | **MODIFY** | Adapter pattern + cost/usage logging reusable. **Must extend `Message.content` from `str` to support image parts** (multimodal payloads). This is the highest-leverage code change. |
| Leakage / static-leakage guards | `safety/static_leakage.py`, `safety/answer_leakage_repair.py`, `safety/leakage_repair_planner.py` | **MODIFY** | Concept ports: add **label-visibility-in-prompt** and **cross-split pair leakage** for images. Prototyped in `cab_vision/validation/leakage_checks.py`. |
| Claim ledger | `claim_ledger.py`, `docs/claim_ledger.json`, `safety/claim_evidence_matrix.py` | **KEEP (reframe)** | The discipline of "no claim without linked evidence" is exactly what saves benchmark papers. Re-point claim IDs to visual claims (see `CVPR_CLAIM_LEDGER_TARGET.md`). |
| No-run validation / governance | `safety/*`, `runners/plan_run.py`, `runners/audit_dataset.py`, `Makefile` | **KEEP** | Lets you validate the visual dataset + estimate cost **before** spending on VLM APIs. Rare and valuable. |
| Reproducibility bundle | `release/repro_bundle.py`, `safety/reproducibility_manifest.py`, `scripts/reproduce_artifact.py` | **KEEP** | CVPR cares about artifacts; this is ahead of most submissions. |
| Human-validation protocol | `safety/human_validation_*`, `docs/HUMAN_VALIDATION_*.md`, `analysis/human_validation.py` | **MODIFY** | Reuse sampling + agreement machinery; rewrite the **rubric** for visual causal judgments. |
| Statistics / bootstrap | `metrics/statistics.py`, `analysis/statistics.py` | **KEEP** | CIs / bootstrap / paired tests are venue-agnostic. CVPR reviewers want CIs on benchmark numbers. |
| Failure gallery / reports | `analysis/failure_gallery_doc.py`, `runners/failure_gallery_report.py`, `analysis/figures.py` | **MODIFY** | Becomes a **visual** failure gallery (image + model answer + gold + cue). High reviewer impact. |
| Trajectory logging | `schemas.py` `TrajectoryV2`, `trajectory.py` | **MODIFY** | Keep for agentic/action tasks; add image-reference + per-step visual-evidence fields. CUT for single-shot VQA-style families. |
| Contamination audit | `contamination/audit.py` | **MODIFY** | Vision contamination is real (web images in pretraining). Add perceptual-hash / reverse-image-search checks. |

### 2B. Not reusable for CVPR — **CUT (from v1) / DEPRECATE**

| Asset | File(s) | Verdict | Why |
|---|---|---|---|
| Text/tool intervention families | `schemas.py:8-24`, `generation/interventions.py`, `generation/web_shadow*.py` | **CUT (v1)** | `tool_removal`, `memory_corruption`, `web_broken_link`, etc. are not visual and not CVPR-relevant. Keep the *taxonomy idea*, discard the textual instances. |
| Simulated text tools | `tools/mock_tools.py`, `tools/simulated.py`, `tools/web_snapshot.py` | **CUT (v1)** | No visual grounding. (Optional later: simulator-rendered scenes for embodied tasks.) |
| Tool-call parser / protocol | `schemas.py` `ToolCallParseResult`, `docs/TOOL_CALL_PROTOCOL.md` | **CUT (v1)** | Only needed if v1 includes agentic action tasks; defer. |
| Travel/shopping/calendar task content | `data/sample/*`, `data/frozen/pilot_v0.1/*`, `data/processed/*` | **CUT** | Pure text. Not transferable. |
| NeurIPS-specific gates/blueprints | `safety/neurips_submission_gate.py`, `paper/NEURIPS_*`, `docs/ROADMAP_TO_NEURIPS_2027.md` | **DEPRECATE/RENAME** | Re-target to CVPR (formatting, page limits, supplementary, reviewer norms differ). |
| Greedy/random/react/planner text agents | `agents/greedy_tool_agent.py`, `agents/react_stub_agent.py`, etc. | **CUT (v1)** | Replaced by VLM adapters + ablation baselines. |

### 2C. Must add — **ADD (CVPR CRITICAL)**

| New asset | Where | Why |
|---|---|---|
| Visual task schema | `cab_vision/schemas/task_schema.py` (✅ prototyped) | Image-grounded causal tasks. |
| VLM provider adapters (image input) | `cab_vision/providers/*` | OpenAI/Anthropic/Gemini + Qwen-VL/InternVL/LLaVA. |
| Visual-causal metrics | `cab_vision/eval/metrics.py` (✅ prototyped) | causal consistency, intervention sensitivity, spurious-cue resistance, action validity. |
| Visual asset pipeline | `cab_vision/data/*` | raw → processed → splits, sha256, perceptual-hash dedup. |
| The actual images | `data/cab_vision/images/*` | The dataset. Currently placeholders only. |
| Modality ablations | `cab_vision/eval/` + configs | text-only / caption-only / image+Q to prove visual centrality. |

---

## 3. Claims that CVPR reviewers would reject today

| Current claim / framing | Source | Reviewer reaction |
|---|---|---|
| "Causal benchmark for tool-using LLM agents" | `README.md:3` | "Not computer vision. Wrong venue." → desk-reject risk. |
| "ACRS changes model rankings" (C4) | `claim_ledger.py` | Unsupported (0 runs) **and** about text agents. |
| Anything implying empirical results | various blueprints | There are none. CVPR reviewers check for real numbers + CIs. |
| "Controlled interventions isolate causal skill" | C10, `docs/INTERVENTION_VALIDITY_DOSSIER.md` | For *text*; for vision must be re-proven with visual human validation. |
| "Benchmark is reproducible" (C9) | C9 | True for *engineering smoke*, but reviewers will read it as "results reproducible" — there are no results. |

**The honest current state CVPR would see:** a beautifully engineered harness with no
vision and no experiments. That is a `NOT_CVPR_RELEVANT` desk reject.

---

## 4. Genuinely strong assets (do not throw away)

1. **Paired causal design + ratio metric** — the conceptual spine; differentiates from VQA.
2. **No-run validation + cost governance** — lets you de-risk an expensive VLM study before paying.
3. **Leakage discipline** (`safety/static_leakage.py`) — vision benchmarks routinely die on
   leakage; you already think this way.
4. **Claim ledger** — forces 1:1 claim↔evidence; the antidote to "overclaiming benchmark paper".
5. **Human-validation + statistics machinery** — CVPR reviewers demand IAA + CIs; you have the scaffolding.
6. **Reproducibility bundles** — artifact-ready muscle memory.

These are exactly the things weak CVPR benchmark submissions lack. They are your moat.

---

## 5. Ceiling analysis

**Without conversion:** `NOT_CVPR_RELEVANT`. Best alternative home unchanged: NeurIPS/ICLR
D&B, but even there it needs real runs.

**With full conversion** (real visual-causal data, VLM baselines, modality ablations proving
text-alone fails, human validation, visual failure gallery, CIs):
- Realistic ceiling: **`CVPR_MAIN_COMPETITIVE`** — *if* the headline result is strong (e.g.
  large interventional-vs-observational gap that survives the caption-only ablation, plus a
  causal-consistency collapse uncorrelated with recognition accuracy).
- "`CVPR_MAIN_SAFE`" is not a realistic target for any benchmark paper; do not claim it.

**The result that unlocks the ceiling:** *"State-of-the-art VLMs recognize the scene
correctly yet choose causally invalid answers/actions — interventional accuracy drops X%
vs observational, the gap is NOT closed by oracle captions (so it is a visual-causal failure,
not a language failure), and causal-consistency is near chance even when object recognition is
≥90%."* That is a CVPR-grade finding.

---

## 6. Conversion risk register (top items)

| Risk | Severity | Mitigation |
|---|---|---|
| "Just another VQA/benchmark" dismissal | High | Lead with the *causal pairing + modality ablation*, not accuracy tables. |
| "Not CV enough" (looks like an LLM eval) | High | Center image-only-answerable tasks, visual failure gallery, perception-vs-causality decomposition. |
| Synthetic-only data looks toy | High | Real images (driving/medical/household) in v1, synthetic only as a *controlled* complement. |
| Label leakage / text shortcuts | High | Already your strength — enforce `cab_vision/validation` + caption-only ablation as a gate. |
| Cost of VLM eval | Medium | No-run cost estimator (`safety/run_cost_estimator.py` pattern) + open-weight VLMs first. |
| Data licensing for real images | Medium | Use permissively-licensed/own-captured/simulator images; document in data card. |

See `CVPR_FIT_SCORECARD.md` for quantified scores and `CVPR_IMPLEMENTATION_ROADMAP.md` for the build order.
