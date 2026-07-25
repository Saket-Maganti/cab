# Prompt 7 — NeurIPS Paper Finalization, Release Package, and Submission Gate

You are working in the Causal Agent Bench repository.

You are Cursor Composer acting as a NeurIPS paper lead, artifact evaluation chair, release manager, and claim-evidence auditor.

## Mission

Turn completed evidence into a final NeurIPS-ready paper and artifact package.

This prompt should be run only after:

- main_500 or equivalent benchmark evidence exists
- human validation exists
- paper assets are eligible
- claim ledger has supported claims
- release artifact can be packaged

If those are missing, the correct final output is `NOT_READY`.

## Starting assumptions

- main benchmark may or may not be complete.
- This prompt must check, not assume.
- No fake results.
- No unsupported claims.
- No paper readiness if gates fail.

## Absolute rules

Do not:

- write fake results
- invent numbers
- fabricate human validation
- promote unsupported claims
- hide limitations
- mark paper as ready if submission gate fails
- create release artifacts with placeholder results
- call provider APIs unless explicitly part of missing approved runs
- manually override eligibility scanner

Allowed:

- fill paper from eligible assets
- generate tables/figures from eligible runs
- package release bundle
- run submission gate
- run reproducibility checks
- update claim ledger through approved mechanism
- polish paper text
- create final blocking report if not ready

## Tasks

### 1. NeurIPS readiness audit

Run and inspect:

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_final_neurips_readiness
python3 -m causal_agent_bench neurips-submission-gate --output-dir /tmp/cab_final_neurips_readiness/neurips_submission_gate
python3 -m causal_agent_bench validity-scorecard --output-dir /tmp/cab_final_neurips_readiness/validity_scorecard
```

Inspect:

- claim ledger
- paper asset eligibility
- human validation reports
- main benchmark reports
- release readiness
- submission gate
- paper source

If gate says `NOT_READY`, stop after creating `reports/FINAL_NEURIPS_BLOCKERS.md`.

### 2. Fill paper only from eligible evidence

If ready:

Update paper sections:

- abstract
- introduction
- benchmark design
- dataset
- intervention taxonomy
- metrics
- experiments
- results
- human validation
- ablations
- limitations
- ethics
- reproducibility
- conclusion

Rules:

- Every empirical claim must cite eligible table/figure/run artifact.
- No "we show" unless claim ledger supports it.
- No C3/C10 unless human validation supports them.
- No public-release claim unless bundle exists.
- Include template-inflation limitations.
- Include scorer-calibration limitations.
- Include synthetic/simulated environment limitations.

### 3. Generate final tables and figures

Only from eligible assets:

- dataset statistics
- main results
- intervention breakdown
- ACRS
- model ranking stability
- failure taxonomy
- human agreement
- ablations
- cost/runtime
- robustness heatmap
- clean/intervention deltas
- evidence lifecycle

Run eligibility scanner again.

### 4. Release package

Create:

- release tarball/zip
- dataset manifests
- hashes
- license
- data license
- citation file
- model/provider metadata
- reproducibility commands
- reviewer quickstart
- artifact evaluation checklist
- known limitations
- leaderboard protocol if applicable

Do not publish externally unless user explicitly asks. Prepare local release artifact.

### 5. Final checks

Run:

- evidence safety
- paper asset eligibility
- claim-evidence matrix
- NeurIPS submission gate
- no-overclaim scanner
- tests
- build paper PDF if LaTeX environment exists

### 6. Submission packet

Create:

- `SUBMISSION_PACKET_NEURIPS/README.md`
- `SUBMISSION_PACKET_NEURIPS/paper_checklist.md`
- `SUBMISSION_PACKET_NEURIPS/artifact_checklist.md`
- `SUBMISSION_PACKET_NEURIPS/reproducibility_checklist.md`
- `SUBMISSION_PACKET_NEURIPS/limitations_and_ethics.md`
- `SUBMISSION_PACKET_NEURIPS/known_blockers.md`

### 7. Final verdict

If all gates pass:

- write `NEURIPS_READY.md`
- state exact supported claims
- state exact artifact version
- state exact remaining limitations

If any gate fails:

- write `NOT_NEURIPS_READY.md`
- list blockers in priority order
- do not claim readiness

## Tests

Add/update tests for:

- every empirical claim maps to eligible evidence
- paper has no placeholder TODO results
- C3/C10 require human validation
- release bundle contains required files
- submission gate blocks missing artifacts
- no-overclaim scanner catches unsupported language
- final paper cannot be marked ready with 0 eligible assets

## Final response format

# Final NeurIPS Paper and Release Readiness Report

## 1. Executive Summary
## 2. Submission Gate Result
## 3. Supported Claims
## 4. Paper Sections Updated
## 5. Tables/Figures Generated
## 6. Human Validation Evidence
## 7. Release Package
## 8. Reproducibility Checks
## 9. Tests Added/Updated
## 10. Commands Run
## 11. Commands Not Run
## 12. Final Evidence State
## 13. Remaining Blockers
## 14. Final Verdict

Must be either:

- `NEURIPS_READY`
- `NOT_READY`

Success condition:

- If evidence is complete, project becomes NeurIPS-ready.
- If evidence is incomplete, project honestly reports not ready with exact remaining blockers.
