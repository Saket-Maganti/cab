You are working in the Causal Agent Bench repository.

You are Codex acting as a ruthless research advisor, benchmark framing editor, NeurIPS Datasets & Benchmarks reviewer, and evidence-governance enforcer.

Task:
Reframe the project around one sharp, falsifiable thesis without executing any provider/model/benchmark runs.

Current reality:
- The repo has strong infrastructure but no real provider/model experiments.
- Provider-backed evidence is 0.
- Human annotations are 0.
- Paper-eligible assets are 0.
- NeurIPS readiness is false.
- The strongest likely thesis is ranking instability under controlled perturbations, not broad “causal” proof.

Absolute rules:
- Do not call providers.
- Do not run local LLMs.
- Do not run `causal_agent_bench run`.
- Do not run dry-run/plan-run/estimate-run-cost unless explicitly needed for static report refresh and already known safe.
- Do not run main_200/main_500/Compact-20/Compact-50.
- Do not fabricate evidence.
- Do not promote claims.
- Do not mark assets eligible.
- Do not delete files; create an archive plan only.

Inspect:
- README.md
- GOD_TIER_MANIFEST.md
- CLAIM_LEDGER.md or equivalent claim docs
- docs/COMPACT_PAPER_STRATEGY.md
- paper/COMPACT_EMPIRICAL_PAPER_BLUEPRINT.md
- paper/main.tex or paper source
- docs/NEURIPS_SUBMISSION_GATE.md
- docs/NEURIPS_SELF_REVIEW_RUBRIC.md
- any docs mentioning C1-C10
- benchmark spec / intervention taxonomy docs
- metric implementation docs/code, especially ACRS or causal robustness metrics

Tasks:

1. Create a focused project framing memo:
   - docs/FOCUSED_PROJECT_THESIS.md

It must answer:
- What is the project actually about?
- What is the single strongest thesis?
- What claims are allowed before real runs?
- What claims are forbidden before real runs?
- What terms should be avoided or hedged?
- Whether “causal” is justified, and if not, how to reframe as controlled perturbation.
- How this project differs from ordinary agent benchmark work.
- What exact result would make the paper important later.

Recommended thesis:
“Outcome-success leaderboards of tool-using agents may overstate skill; paired controlled perturbations can reveal ranking instability and intervention-specific brittleness.”

2. Create a claim triage table:
   - docs/CLAIM_TRIAGE_NO_RUN.md

For each C1-C10, classify:
- current status
- evidence required
- whether it can be mentioned in the paper now
- whether it must stay planned/unsupported
- minimum experiment/human validation needed later
- safest wording

3. Update compact paper strategy and paper blueprint to reflect the no-run reality:
   - docs/COMPACT_PAPER_STRATEGY.md
   - paper/COMPACT_EMPIRICAL_PAPER_BLUEPRINT.md

Add a section:
“Current evidence boundary”

It must state:
- no provider/model results exist
- no human validation exists
- the paper is currently a methods/benchmark-design scaffold
- empirical claims require future Compact-20/50 provider runs
- NeurIPS D&B is not currently reachable

4. Create a title/framing alternatives file:
   - docs/TITLE_AND_FRAMING_OPTIONS.md

Include:
- 10 title candidates avoiding overclaim
- 5 title candidates using “causal” only if heavily qualified
- 5 rejected titles with reasons

5. Add/update fixture-only tests, if the repo has a suitable test structure:
- no “NeurIPS-ready” phrase in compact paper outputs
- no final empirical claim without provider evidence
- C1-C8/C10 remain unsupported without runs
- “causal” language must be accompanied by a limitation/qualification

Allowed checks:
- targeted fixture tests
- py_compile on changed Python files if any

Final response:

# CAB Focused Reframe Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. New Project Thesis
## 5. Claim Triage Summary
## 6. Causal-Language Decision
## 7. Paper Strategy Update
## 8. Tests Added/Updated
## 9. Commands Run
## 10. Commands Not Run
Confirm no provider calls, no local LLMs, no benchmark runs, no fake evidence.
## 11. Current Evidence State
## 12. Remaining Blockers
## 13. Next Best Action

Final verdict:
NO_RUN_REFRAME_COMPLETE
