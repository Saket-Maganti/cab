# NeurIPS ED Track — Reviewer Attack Response Matrix

**Paper:** *When Agent Success Is Not Agent Skill: A Causal Benchmark for Tool-Using LLM Agents*  
**Repo status (2026-05):** Deterministic scaffold; paper placeholders; no publication-grade LLM or human-validation evidence in-tree.  
**Legend — blocking for submission:**  
- **Yes** = must be resolved (or claims downgraded to planned/engineering-only) before NeurIPS ED submission with empirical results.  
- **Partial** = honest limitation + partial mitigation acceptable if scope is narrowed.  
- **No (draft)** = acknowledged in paper/docs; does not block a transparent scaffold draft.  

**Claim ledger:** `docs/claim_ledger.json` · **Evidence mapping:** `docs/PAPER_EVIDENCE_MAPPING.json`

---

## Prioritized fix list (submission path)

| Priority | Attack # | Fix | Owner artifact | Blocking |
| --- | --- | --- | --- | --- |
| P0 | 12, 11 | Run frozen benchmark with ≥2 non-oracle LLM agents; complete human-validation pilot on intervention validity + label quality | `results/<run>/`, `tables/table5_*`, C1–C4 | Yes |
| P0 | 11, 2, 3 | Expert/human audit of interventions (C10); soften causal wording everywhere it implies identification | `docs/INTERVENTION_AUDIT.md`, §4, §10 | Yes |
| P0 | 17 | Exclude oracle from all ranking/ACRS tables; separate sanity-check appendix | Table 2 export, §6 | Yes |
| P1 | 5, 4, 18 | Fill results: clean vs intervention, ACRS, ranking ρ, trajectory–final disagreement figures from verified runs | `fill-paper-from-run`, figures 2–4, 6 | Yes |
| P1 | 14 | Report cost/latency per agent from run metadata | `docs/COST_LATENCY.md`, §6, cost columns in tables | Yes |
| P1 | 16 | Run prompt/scaffold ablations (Table 4) for C6 | `tables/table4_ablation_results.csv` | Yes (if ablation claims kept) |
| P2 | 13 | At least one open-weight/local run with `local_open_weight_unvalidated` label | `docs/OPEN_WEIGHT_LOCAL_MODELS.md`, configs | Partial |
| P2 | 15 | Export synthetic-to-realistic mini-study + optional web-shadow comparison (no stub-as-evidence) | §3 mini-study table, `docs/WEB_SHADOW_STUDY.md` | Partial |
| P2 | 6, 7 | Human agreement on trajectory diagnostics; document judge risks if LLM judge enabled | §8, `docs/LLM_JUDGE_RISKS.md` | Partial |
| P3 | 8, 9, 10 | Held-out templates, difficulty reporting, anti-gaming release policy | dataset freeze, §10–11 | Partial |
| P3 | 19, 20 | Sharpen scientific framing + 2–3 diagnostic use-case vignettes in paper | §1, §12, failure gallery | No (draft) |

---

## Attack matrix

### 1. “This is just a synthetic benchmark.”

| Field | Content |
| --- | --- |
| **Why it matters** | ED reviewers expect external validity or a clear reason controlled simulation is the right first step. |
| **Current status** | Default environment is synthetic and deterministic; paper §3 argues this tradeoff explicitly; synthetic-to-realistic mini-study and web-shadow study exist as engineering probes only. |
| **Required fix** | Keep narrow claims; report mini-study and/or web-shadow only from validated runs; position synthetic bench as **diagnostic**, not deployment predictor. |
| **Paper section** | §3 (design), §10 (limitations), §12 (conclusion) |
| **Evidence needed** | Frozen dataset card; optional mini-study table with paired non-stub runs; web-shadow comparison exports. |
| **Blocking** | **Partial** — blocks transfer/deployment claims, not benchmark release as controlled diagnostic. |

---

### 2. “The interventions are artificial.”

| Field | Content |
| --- | --- |
| **Why it matters** | Paired causal claims require that perturbations resemble real failure modes and isolate one factor. |
| **Current status** | Ten intervention families with metadata and automated audit; `docs/INTERVENTION_AUDIT.md`; human audit **not complete** (C10 planned). |
| **Required fix** | Complete expert/human audit sample; map each family to real-world analogues in paper; report audit pass/warn/fail rates. |
| **Paper section** | §4, §8, §10 |
| **Evidence needed** | `intervention_audit_report.json`, `tables/table5_human_validation_agreement.csv`, audited examples. |
| **Blocking** | **Yes** for strong intervention/causal skill claims (C2, C10). |

---

### 3. “The causal language is too strong.”

| Field | Content |
| --- | --- |
| **Why it matters** | “Causal” implies identification; reviewers will reject overclaiming from controlled pairs alone. |
| **Current status** | §4 cites Pearl/Holland and states **not** observational identification; estimand is behavior change under named simulator perturbation. |
| **Required fix** | Audit all “causal” instances; prefer “interventional,” “paired perturbation,” “controlled benchmark design”; tie claims to C10 validity. |
| **Paper section** | §1, §4, §5 (ACRS name), abstract |
| **Evidence needed** | Consistent terminology pass; claim-ledger wording aligned with §4 estimand. |
| **Blocking** | **Partial** — wording fix is low-risk now; validity evidence still required for empirical claims. |

---

### 4. “ACRS is too simple.”

| Field | Content |
| --- | --- |
| **Why it matters** | A single ratio can mis-rank agents with low clean success or uniform failure. |
| **Current status** | §5 defines ACRS with undefined-at-zero-clean rule; requires reporting clean, intervention, n, uncertainty, components. |
| **Required fix** | All tables include clean + intervention + CIs; per-family ACRS; sensitivity note for low clean-success agents. |
| **Paper section** | §5, §7 (results tables) |
| **Evidence needed** | Filled Table 2/3 from verified runs; bootstrap CIs in statistical report. |
| **Blocking** | **Yes** if paper leads with ACRS without component context (C4). |

---

### 5. “Final success already measures what matters.”

| Field | Content |
| --- | --- |
| **Why it matters** | Core motivation must be demonstrated, not asserted. |
| **Current status** | Claim C1/C3 planned; trajectory–final disagreement figure scaffold exists; **no validated LLM evidence in repo**. |
| **Required fix** | Show cases where clean success is high but intervention success or trajectory diagnostics fail; quantify gap (C1). |
| **Paper section** | §1, §7, Figure 2 & 6 |
| **Evidence needed** | Non-oracle run dir linked via `fill-paper-from-run`; error-case gallery. |
| **Blocking** | **Yes** for main empirical contribution. |

---

### 6. “Trajectory metrics are heuristic.”

| Field | Content |
| --- | --- |
| **Why it matters** | Component metrics need reliability evidence or must stay diagnostic hypotheses. |
| **Current status** | Deterministic trajectory scorer documented; Metrics v2 export; human validation of diagnostics **incomplete**. |
| **Required fix** | Human agreement study on subset of trajectory labels; report κ/F1; document known failure modes. |
| **Paper section** | §5, §8, §10 |
| **Evidence needed** | `tables/table5_*`, annotated disagreement packet, `docs/ERROR_TAXONOMY.md` examples. |
| **Blocking** | **Yes** for C3; **Partial** if framed as exploratory diagnostics with agreement bounds. |

---

### 7. “LLM-as-judge is unreliable.”

| Field | Content |
| --- | --- |
| **Why it matters** | Judge bias and circular evaluation undermine ED benchmarks. |
| **Current status** | Default path is deterministic scoring; judge protocol docs exist; judge **optional** and not default for smoke. |
| **Required fix** | If judge used: report model, prompt hash, agreement vs humans, failure modes; never replace human audit for intervention validity. |
| **Paper section** | §5, §8, §10, checklist |
| **Evidence needed** | `docs/LLM_JUDGE_PROTOCOL.md`, calibration run (if enabled). |
| **Blocking** | **No** if judge disabled; **Yes** if judge scores appear in main tables without calibration. |

---

### 8. “The benchmark can be gamed.”

| Field | Content |
| --- | --- |
| **Why it matters** | Public tasks, tool schemas, and heuristics invite overfitting and oracle-like shortcuts. |
| **Current status** | Held-out template split in freeze manifest; ethics § warns against static leaderboard gaming; PlannerExecutor leak fixed (round 1). |
| **Required fix** | Versioned releases, held-out evaluation policy, contamination reporting, baseline audit for hidden metadata. |
| **Paper section** | §10–11, §6 |
| **Evidence needed** | `splits.json` held-out policy, baseline audit checklist, release manifest. |
| **Blocking** | **Partial** — required for long-term community benchmark; soften if single-shot paper with frozen split. |

---

### 9. “The tasks are too easy.”

| Field | Content |
| --- | --- |
| **Why it matters** | Ceiling effects destroy discrimination among modern LLMs. |
| **Current status** | Difficulty tags in schema; oracle/stub can score highly; **no published LLM difficulty curve**. |
| **Required fix** | Report per-difficulty breakdown; show non-oracle failure rates; avoid citing stub/oracle as difficulty evidence. |
| **Paper section** | §3, §7, Table 1 stats |
| **Evidence needed** | Main run with difficulty-stratified tables; optional harder held-out slice. |
| **Blocking** | **Yes** if all agents saturate; **Partial** if failures appear under interventions even when clean is easy. |

---

### 10. “The tasks are too template-like.”

| Field | Content |
| --- | --- |
| **Why it matters** | Template artifacts can inflate scores and misalign with naturalistic agent settings. |
| **Current status** | Generator uses templates; 40-task naturalistic mini-study cohort exists; comparison table is placeholder. |
| **Required fix** | Populate mini-study comparison from validated runs; report template vs naturalistic degradation correlation. |
| **Paper section** | §3 (mini-study), §10 |
| **Evidence needed** | `compare-mini-study` exports, Table mini-study in §3. |
| **Blocking** | **Partial** — blocks claims about natural language robustness, not controlled intervention design. |

---

### 11. “No human validation.”

| Field | Content |
| --- | --- |
| **Why it matters** | Intervention validity and heuristic labels need human/expert ground truth for ED trust. |
| **Current status** | Export workflow + protocol docs; §8 uses generated placeholder; **no completed annotation study in repo**. |
| **Required fix** | Run pilot per `docs/HUMAN_VALIDATION_PILOT_PLAN.md`; fill Table 5; link to C10. |
| **Paper section** | §8, checklist item 5 |
| **Evidence needed** | `tables/table5_human_validation_agreement.csv`, adjudication log. |
| **Blocking** | **Yes** for label-quality and intervention-validity claims. |

---

### 12. “No real LLM agents.”

| Field | Content |
| --- | --- |
| **Why it matters** | A tool-agent benchmark paper without LLM trajectories will be desk-rejected. |
| **Current status** | LLM adapters, prompts, multi-provider configs exist; main results are placeholders; stubs for engineering only. |
| **Required fix** | Frozen pilot/main run with ≥2 non-oracle LLM configs; `fill-paper-from-run`; update claim ledger paths. |
| **Paper section** | §6–7, abstract, generated snippets |
| **Evidence needed** | `results/<timestamp>_*` with model IDs, prompt hashes, config hash, git commit in metadata. |
| **Blocking** | **Yes** for any empirical NeurIPS submission. |

---

### 13. “No open-weight models.”

| Field | Content |
| --- | --- |
| **Why it matters** | Reproducibility and access equity; reviewers expect at least one non-proprietary datapoint. |
| **Current status** | `local_openai` provider + `docs/OPEN_WEIGHT_LOCAL_MODELS.md`; runs labeled `local_open_weight_unvalidated`; **no validated open-weight results in paper**. |
| **Required fix** | One documented local/open-weight pilot run; separate from commercial leaderboard; report hardware context. |
| **Paper section** | §6, appendix or Table 2 footnote |
| **Evidence needed** | Config under `configs/pilot_*_local*` or similar; run metadata with base URL and model id. |
| **Blocking** | **Partial** — increasingly expected; not always strict if API models + full reproducibility package. |

---

### 14. “No cost analysis.”

| Field | Content |
| --- | --- |
| **Why it matters** | Agent benchmarks vary widely in cost; ED reviewers ask about feasibility. |
| **Current status** | Cost/latency tracking in runner + `docs/COST_LATENCY.md`; not in filled paper tables yet. |
| **Required fix** | Export per-agent token/cost/latency from main runs; optional cost-normalized ranking appendix. |
| **Paper section** | §6, results tables |
| **Evidence needed** | `run_summary.json` cost fields, Table 2 cost column. |
| **Blocking** | **Yes** for multi-LLM main experiments; **No** for pure scaffold. |

---

### 15. “No external validity.”

| Field | Content |
| --- | --- |
| **Why it matters** | Synthetic simulator may not predict WebArena/SWE-bench-style performance. |
| **Current status** | Related work positions WebArena/SWE-bench/OSWorld as comparators; web-shadow + mini-study are optional modules; **no cross-benchmark correlation reported**. |
| **Required fix** | Honest limitation + one external-validity probe (mini-study and/or web-shadow) with non-stub runs; future work for live environments. |
| **Paper section** | §3, §10, §2 |
| **Evidence needed** | Mini-study table; optional web-shadow `compare-web-shadow` report. |
| **Blocking** | **Partial** — blocks external-transfer claims; does not block controlled-benchmark contribution if scoped. |

---

### 16. “Not enough ablations.”

| Field | Content |
| --- | --- |
| **Why it matters** | Prompt/scaffold changes may explain gains rather than benchmark insight. |
| **Current status** | Ablation configs + Table 4 scaffold; C6 planned; generated §09 placeholders. |
| **Required fix** | Run single-factor prompt ablations (ReAct, self-check, memory verify, etc.) on fixed tasks/agents. |
| **Paper section** | §7 / generated 09_ablations |
| **Evidence needed** | `tables/table4_ablation_results.csv` from ablation config runs. |
| **Blocking** | **Yes** if paper claims scaffold improvements (C6); **No** if ablations framed as future work. |

---

### 17. “The oracle baseline contaminates claims.”

| Field | Content |
| --- | --- |
| **Why it matters** | Hidden-metadata oracle inflates scores and confuses readers if mixed with LLM agents. |
| **Current status** | §6 labels oracle as sanity-check only; export paths should exclude oracle from rankings. |
| **Required fix** | Enforce oracle exclusion in table exporters; separate row or appendix; never use oracle in ACRS ranking figure. |
| **Paper section** | §6, §7, Table 2 caption |
| **Evidence needed** | Table export script filter; caption text “oracle excluded.” |
| **Blocking** | **Yes** if oracle appears in main leaderboard; **No** if clearly separated. |

---

### 18. “Ranking instability is obvious.”

| Field | Content |
| --- | --- |
| **Why it matters** | Reviewers may view low clean–ACRS correlation as tautological or uninteresting. |
| **Current status** | §5 defines Spearman analysis for C4; figure scaffold exists; **no filled correlation from LLM runs**. |
| **Required fix** | Report ρ with CI and n agents; show non-trivial rank changes with examples; avoid overclaiming surprise. |
| **Paper section** | §5, §7, Figure 4 |
| **Evidence needed** | Statistical report from verified main run. |
| **Blocking** | **Yes** for C4 headline; **Partial** if framed as “may differ” with measured ρ. |

---

### 19. “The contribution is engineering, not scientific.”

| Field | Content |
| --- | --- |
| **Why it matters** | ED track still requires a clear scientific question and falsifiable tests. |
| **Current status** | Claims C1–C8 are explicit; package is engineering-heavy; empirical tests unfilled. |
| **Required fix** | Lead with estimand and planned tests (C1–C4); separate “benchmark artifact” from “findings”; fill at least primary tests. |
| **Paper section** | §1 contributions, §7, claim ledger |
| **Evidence needed** | Linked artifacts per claim; no stub-as-evidence. |
| **Blocking** | **Yes** for results-forward submission; **No** for transparent benchmark+dataset paper with planned study. |

---

### 20. “The benchmark is not useful.”

| Field | Content |
| --- | --- |
| **Why it matters** | Community adoption requires clear developer/researcher workflows. |
| **Current status** | CLI, configs, cards, failure gallery miner, reproducibility docs; no adoption case studies. |
| **Required fix** | Add 2–3 concrete use cases (diagnose tool failure vs memory vs stopping); link to error taxonomy gallery; release-check gate. |
| **Paper section** | §1, §12, optional appendix vignettes |
| **Evidence needed** | `results/<run>/error_cases/`, README quickstart, benchmark card. |
| **Blocking** | **Partial** — mitigated by documentation and diagnostic examples; full utility proven by adoption over time. |

---

## Low-risk fixes applied in-repo (Prompt 47)

- This matrix and prioritized list (`reviews/reviewer_attack_response_matrix.md`).
- `docs/REVIEWER_PROOFING.md` index for authors.
- Paper §6–§10 and checklist strengthened (scope, oracle exclusion, cost/open-weight status) without fabricating results.
- `scripts/check_reviewer_proofing.py` + test ensuring matrix completeness.

## Maintenance

After each pilot or main run:

1. Update **Current status** rows for attacks 5, 11, 12, 14, 16, 18.
2. Link evidence paths in `docs/claim_ledger.json`.
3. Re-run `make paper-check` and `python scripts/check_reviewer_proofing.py`.
