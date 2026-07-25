# CAB-Vision Claim Ledger (Target)

Claims the paper may make **only if** the linked evidence exists. Mirrors the discipline of
`src/causal_agent_bench/claim_ledger.py` + `docs/claim_ledger.json`; re-point the claim IDs to the
visual claims below. Status vocab (reuse): `planned · engineering_only · supported · weakened · rejected`.
**All claims start `planned`** (no runs yet).

For each claim: required experiment · metric · table/figure · minimum-evidence threshold · confounders ·
reviewer attack · defense · safe wording · too-strong wording.

---

### V1 — Interventional/counterfactual << observational
- **Experiment:** all VLMs on paired observational vs interventional/counterfactual items.
- **Metric:** `Acc_obs`, `Acc_int`, gap `Δ` (`cab_vision.eval.metrics`).
- **Figure/Table:** money plot (obs vs int per model) + table with CIs.
- **Threshold:** `Δ` ≥ ~15 pts, 95% CI excludes 0, holds for ≥3 models & ≥2 domains.
- **Confounders:** interventional items just harder/noisier; different base rates.
- **Attack:** "you made the int items harder, not more causal."
- **Defense:** matched pairs (same scene, single-factor edit), human-validated single-factor, recognition
  controlled (V4).
- **Safe:** "VLMs show a substantial, significant drop from observational to interventional accuracy."
- **Too strong:** "VLMs cannot do causal reasoning."

### V2 — Caption-then-reason loses visual causal information
- **Experiment:** caption-only & oracle-caption vs image+Q.
- **Metric:** accuracy under each condition (gate table).
- **Figure/Table:** modality-ablation table.
- **Threshold:** caption-only materially < image+Q; if oracle-caption < image+Q the info is genuinely visual.
- **Confounders:** weak captioner (use a strong one + oracle caption).
- **Attack:** "your captioner is bad."
- **Defense:** oracle/human caption arm.
- **Safe:** "caption-mediated pipelines lose causally relevant visual information."
- **Too strong:** "captioning is useless."

### V3 — Strong VLMs rely on spurious visual priors under cue conflict
- **Experiment:** family-3 with matched no-cue controls.
- **Metric:** `SCR` (spurious-cue resistance), trap-choice rate.
- **Figure:** spurious-cue failure figure (cue present vs absent).
- **Threshold:** trap-rate significantly above the no-cue control for ≥3 models.
- **Confounders:** option imbalance (majority-class baseline rules out).
- **Attack:** "trap option is just more salient/likely text."
- **Defense:** text-only ≈ chance on these items; matched controls.
- **Safe:** "VLMs are systematically biased toward salient but causally irrelevant cues."
- **Too strong:** "VLMs always hallucinate causes."

### V4 — Causal consistency collapses even when recognition is intact **(the headline)**
- **Experiment:** pairs + recognition probe / oracle-caption decomposition.
- **Metric:** `CC`, `IS`, plus % interventional errors that are causal (recognition-correct).
- **Figure:** perception-vs-causality decomposition.
- **Threshold:** CC near chance while recognition ≥ ~90% on the same items, ≥3 models.
- **Confounders:** recognition probe imperfect.
- **Attack:** "they just didn't see the change."
- **Defense:** oracle-caption + recognition probe show they did.
- **Safe:** "models recognize the scene yet fail to update decisions causally."
- **Too strong:** "models have no causal model of vision."

### V5 — Agentic/tool-use prompting does not reliably fix visual causal failure
- **Experiment:** tool-free vs tool-using/ReAct agent (reuse trajectory logging).
- **Metric:** per-family deltas of agentic vs single-shot.
- **Table:** ablation table.
- **Threshold:** no consistent significant improvement across families.
- **Attack:** "your agent scaffold is weak."
- **Defense:** standard ReAct + report the scaffold; frame as "off-the-shelf agentic prompting."
- **Safe:** "common agentic prompting does not close the causal gap."
- **Too strong:** "agents can't help."

### V6 — Models explain fluently while choosing causally invalid actions
- **Experiment:** action family + explanation family.
- **Metric:** `AV` vs explanation faithfulness; cases of fluent chain + invalid action.
- **Figure:** failure-gallery panel.
- **Threshold:** sizable fraction of invalid actions accompanied by confident fluent rationales.
- **Attack:** "explanation scoring subjective."
- **Defense:** MC-chain (objective) + human-audited judge.
- **Safe:** "fluent visual explanations do not guarantee causally valid decisions."
- **Too strong:** "explanations are always wrong."

### V7 — Human performance remains substantially higher
- **Experiment:** expert human baseline on a validated subset.
- **Metric:** human vs best-model on the same items.
- **Table:** human row in the results table.
- **Threshold:** human >> best model, CI-separated, on the validated subset.
- **Attack:** "humans only beat models on your subset."
- **Defense:** subset is representative/stratified; report subset stats.
- **Safe:** "a substantial human–model gap remains on validated items."
- **Too strong:** "humans are perfect."

### V8 — The benchmark exposes failures invisible to standard VQA/grounding accuracy
- **Experiment:** correlate standard VQA/grounding accuracy with CAB-Vision causal metrics.
- **Metric:** rank correlation between standard accuracy and `CC`/`Acc_int`.
- **Figure:** ranking-instability plot (adapt the existing ranking-instability figure machinery).
- **Threshold:** low/weak correlation → standard metrics don't predict causal competence.
- **Attack:** "just a harder VQA set."
- **Defense:** decorrelation + decomposition show a distinct axis.
- **Safe:** "causal-decision competence is weakly predicted by standard visual accuracy."
- **Too strong:** "VQA benchmarks are meaningless."

---

## Ledger hygiene (carry over from CAB)
- No claim text in the paper without a `supported` row + linked figure/table/run.
- Keep a machine-readable `docs/cabv_claim_ledger.json`; validate in CI (adapt
  `tests/test_claim_ledger.py` → `tests/test_cabv_claim_ledger.py`).
- Pre-register V1/V4 as the primary claims; everything else is secondary/exploratory.
