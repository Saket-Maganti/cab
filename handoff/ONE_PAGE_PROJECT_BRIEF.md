# CausalAgentBench — One-Page Project Brief

**Title:** *When Agent Success Is Not Agent Skill: A Causal Benchmark for Tool-Using LLM Agents*

**Problem:** Tool-using LLM agents are scored mainly on final task success, which hides failures in planning, tool use, memory verification, contradiction handling, recovery, and stopping.

**Core idea:** Pair each clean task with **controlled interventions** that change one designed factor (tool availability, memory, observations, etc.) while holding the user goal stable, then measure robustness with **ACRS** and trajectory diagnostics.

**Benchmark design:** Synthetic but deterministic tool environments (8 domains, 10 intervention families); frozen pilot v0.1 (500 base / 2500 intervention instances candidate); automated intervention + isolation audits.

**Metric:** Agent Causal Robustness Score (ACRS) combines clean and intervention performance with trajectory-level signals (tool efficiency, recovery, contradiction handling, etc.).

**Expected contribution (when evidenced):** (1) interventional evaluation protocol, (2) reproducible benchmark + package, (3) empirical show that clean success overestimates robustness and changes rankings, (4) human-validated intervention/diagnostic quality.

**Current status:** `local_preliminary` / deterministic prototype — infrastructure complete; **empirical claims planned, not supported**.

**Missing evidence:** Provider-backed multi-agent runs, human validation annotations, main-scale results, ablation runs. See [EVIDENCE_GAP_MAP.md](../paper/EVIDENCE_GAP_MAP.md).

**NeurIPS ED-track relevance (hypothesis, not promise):** Strong fit for **datasets & benchmarks** and **evaluation methodology** if intervention validity + reproducibility package are demonstrated; empirical novelty requires real agent study. **Acceptance is not guaranteed.**

**Immediate next steps:** Advisor review of handoff packet → bounded provider pilot (with budget approval) → human validation sample → revise paper from [MOCK_REVIEW_SUMMARY.md](../reviews/MOCK_REVIEW_SUMMARY.md).

**Do not cite stub/mock/local interrupted runs as scientific results.**
