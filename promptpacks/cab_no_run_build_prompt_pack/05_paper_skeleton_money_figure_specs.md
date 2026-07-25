You are working in the Causal Agent Bench repository.

You are Codex acting as a senior ML paper editor, NeurIPS D&B strategist, and figure/table planner.

Task:
Rewrite the compact paper skeleton around the honest no-run reality and specify future result tables/figures without fabricating results.

Current reality:
- Paper has no real empirical results yet.
- Provider evidence is 0.
- Human validation is 0.
- The project needs a sharp story and future figure/table specs.

Absolute rules:
- Do not fabricate numbers.
- Do not create fake result tables.
- Do not run provider/model/benchmark commands.
- Do not promote claims.
- Do not mark paper assets eligible.
- Placeholder tables must be clearly marked “future required result.”
- Do not write “we demonstrate” unless a real result exists.
- Do not claim NeurIPS readiness.

Inspect:
- paper/COMPACT_EMPIRICAL_PAPER_BLUEPRINT.md
- paper/main.tex
- paper sections
- docs/COMPACT_PAPER_STRATEGY.md
- docs/FOCUSED_PROJECT_THESIS.md
- docs/CLAIM_TRIAGE_NO_RUN.md
- related work docs
- existing generated tables/figures

Tasks:

1. Create or update:
   - paper/NO_RUN_PAPER_SKELETON.md

Sections:
- Title
- Abstract placeholder with no empirical claims
- Introduction
- Benchmark design
- Intervention taxonomy
- Metrics and ACRS caveats
- Data quality and validation plan
- Future Compact-20/50 empirical plan
- Human validation plan
- Limitations
- Ethics/broader impacts
- Reproducibility
- What evidence is still missing

2. Create money-figure specification:
   - paper/FIGURE_TABLE_SPEC_NO_RUN.md

Future required figures/tables:
- Table 1: intervention taxonomy and examples
- Table 2: future clean vs intervention success by model
- Figure 1: paired perturbation design
- Figure 2: future success-rank vs ACRS-rank crossing plot
- Figure 3: future per-family degradation
- Table 3: future C10 human validation agreement
- Table 4: future self-check/scaffold ablation
- Figure 4: future failure gallery

For each:
- what data it needs
- why it matters
- what claim it supports
- what claim it cannot support
- minimum evidence threshold
- current status

3. Create paper wording guardrails:
   - paper/PAPER_WORDING_GUARDRAILS.md

Include allowed and forbidden phrases:
- before provider results
- after tiny provider pilot
- after Compact-20/50
- after human validation
- after full NeurIPS gate

4. Update compact paper blueprint to align with these guardrails.

5. Add/update tests:
- paper skeleton does not contain fake result numbers
- future figures are clearly marked future required
- no “we demonstrate” without evidence
- no “validated benchmark” without C10
- no “NeurIPS ready” before gate

Allowed commands:
- static inspection
- targeted fixture tests
- py_compile if code changed

Final response:

# CAB No-Run Paper Skeleton Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Paper Thesis
## 5. Figure/Table Specs
## 6. Wording Guardrails
## 7. Tests Added/Updated
## 8. Commands Run
## 9. Commands Not Run
Confirm no fake results and no provider/model runs.
## 10. Current Paper Evidence State
## 11. Remaining Blockers
## 12. Next Best Action

Final verdict:
NO_RUN_PAPER_SKELETON_READY
