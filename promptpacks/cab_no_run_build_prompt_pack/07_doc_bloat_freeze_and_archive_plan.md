You are working in the Causal Agent Bench repository.

You are Codex acting as a research-repo maintainer, artifact-release editor, and documentation triage lead.

Task:
Create a documentation freeze and archive plan. Do not delete or move files yet unless explicitly safe and reversible. The goal is to stop doc bloat and make the repo look serious.

Current reality:
- The repo has many Markdown docs and meta-governance reports.
- Reviewers care about evidence, not “god-tier” process docs.
- Deleting now could break references, so make a safe plan first.

Absolute rules:
- Do not run provider/model/benchmark commands.
- Do not delete docs yet.
- Do not move docs yet unless creating a non-destructive index.
- Do not remove evidence-relevant docs.
- Do not hide blockers.
- Do not rewrite history.
- Do not claim cleanup is evidence.

Inspect:
- all top-level Markdown docs
- docs/
- reports/
- paper/
- experiments/
- README.md
- any docs with “god-tier”, “war room”, “readiness”, “attack matrix”, “claim gate”, “approval”, “evidence”
- links/references between docs

Tasks:

1. Create documentation inventory:
   - docs/DOCUMENTATION_INVENTORY.md
   - docs/documentation_inventory.csv

For each doc:
- path
- category
- keep/archive/later-delete recommendation
- reason
- evidence relevance
- paper relevance
- release relevance
- safety/gate relevance
- duplicate/obsolete flag
- references risk

2. Create doc freeze policy:
   - docs/DOCUMENTATION_FREEZE_POLICY.md

It must say:
- no new meta-docs unless tied to evidence, paper, validation, release, or safety
- prefer updating existing docs
- every new doc needs purpose and owner
- no “god-tier” branding in public-facing release docs
- blockers must remain visible

3. Create archive plan:
   - docs/DOC_ARCHIVE_PLAN_NO_DELETE.md

Categories:
- keep public
- keep internal
- archive after results
- archive immediately only if safe
- delete never
- delete later after reference check

4. Create public-facing README outline:
   - docs/PUBLIC_README_OUTLINE.md

Focus:
- what benchmark is
- current evidence state
- how to reproduce once runs exist
- limitations
- no inflated claims

5. Add/update tests or scripts only if simple:
- check no new “GOD_TIER” wording appears in public-facing docs
- check README points to evidence state
- check blockers are not hidden

Allowed commands:
- static inspection
- grep/find
- targeted fixture tests

Final response:

# CAB Documentation Freeze/Archive Plan Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Inventory Summary
## 5. Freeze Policy
## 6. Archive Plan
## 7. Public README Outline
## 8. Tests Added/Updated
## 9. Commands Run
## 10. Commands Not Run
Confirm no provider/model runs and no destructive deletion.
## 11. Risks
## 12. Next Best Action

Final verdict:
DOC_FREEZE_ARCHIVE_PLAN_READY
