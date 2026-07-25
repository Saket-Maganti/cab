You are working in the Causal Agent Bench repository.

You are Codex acting as a ruthless NeurIPS/COLM/TMLR reviewer simulator, publication strategist, and paper defense editor.

Task:
Create a reviewer-defense and submission strategy pack grounded in the no-run reality. Do not claim the project is ready.

Absolute rules:
- Do not run provider/model/benchmark commands.
- Do not fabricate results.
- Do not fabricate reviewer scores as facts; label them simulations.
- Do not claim NeurIPS readiness.
- Do not hide blockers.
- Do not overstate novelty.

Inspect:
- docs/FOCUSED_PROJECT_THESIS.md
- docs/CLAIM_TRIAGE_NO_RUN.md
- docs/NOVELTY_BOUNDARY_MEMO.md
- paper/NO_RUN_PAPER_SKELETON.md
- paper/FIGURE_TABLE_SPEC_NO_RUN.md
- docs/RELATED_WORK_GAP_MAP.md
- docs/NEURIPS_SUBMISSION_GATE.md
- docs/COMPACT_PAPER_STRATEGY.md

Tasks:

1. Create reviewer simulation:
   - docs/REVIEWER_SIMULATION_NO_RUN.md

Reviewers:
- supportive but critical
- skeptical benchmark reviewer
- agent-evaluation domain expert
- reproducibility/artifact reviewer

For each:
- likely praise
- likely rejection reasons
- exact questions they ask
- what artifact/result would answer them
- current score simulation
- score after future Compact-20
- score after future 3-model + C10 validation

2. Create rebuttal-preparation matrix:
   - docs/REVIEWER_ATTACK_DEFENSE_MATRIX.md

Rows:
- no real results
- synthetic/template tasks
- causal overclaim
- ACRS too simple
- crowded related work
- intervention isolation unvalidated
- gold-output warnings
- doc bloat/process theater
- no human validation
- no naturalistic transfer

Columns:
- current defense
- honest weakness
- required fix
- evidence needed
- owner/timing

3. Create submission ladder:
   - docs/SUBMISSION_LADDER.md

Categories:
- current no-run state
- after manual Compact-20 review
- after tiny provider pilot
- after 3-model Compact-20
- after 5-model Compact-50/200 + C10
- after naturalistic slice

For each:
- best venue type
- what to submit
- what not to claim
- difficulty

4. Update compact paper strategy with this ladder.

5. Add/update tests:
- submission docs do not claim current NeurIPS readiness
- no-run state mapped only to proposal/workshop/methodology
- top-tier path requires real results and human validation

Allowed commands:
- static inspection
- targeted fixture tests

Final response:

# CAB Reviewer Defense/Submission Strategy Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Reviewer Simulation
## 5. Attack/Defense Matrix
## 6. Submission Ladder
## 7. Tests Added/Updated
## 8. Commands Run
## 9. Commands Not Run
Confirm no provider/model runs and no fake results.
## 10. Current Submission Reality
## 11. Remaining Blockers
## 12. Next Best Action

Final verdict:
REVIEWER_DEFENSE_STRATEGY_READY
