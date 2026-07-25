# Prompt 4 — Human Validation Pilot for C3/C10

You are working in the Causal Agent Bench repository.

You are Cursor Composer acting as a human-validation coordinator, benchmark validity auditor, and claim-evidence governance lead.

## Mission

Create and execute the first real human-validation pilot, if annotators and provider trajectory samples exist.

This is required to support:

- C3: trajectory-level diagnostics correspond to human-recognized failures
- C10: intervention pairs are truly isolated / valid

## Starting assumptions

- Tiny provider pilot exists, or if not, human validation must be limited to task/intervention validity review.
- Human annotators are available or the prompt must stop and create a recruitment packet.
- No human annotations currently exist.
- C3/C10 are blocked.
- No claims should be promoted until agreement metrics exist and pass thresholds.

## Absolute rules

Do not:

- fabricate annotations
- fabricate annotator IDs
- fabricate agreement metrics
- use model outputs as human labels
- promote C3/C10 without real annotation artifacts
- run providers unless separately approved
- expose private provider/API data unnecessarily
- deanonymize provider outputs if blinded protocol requires redaction

Allowed:

- export annotation packets
- create anonymized samples
- create CSV/JSON schemas
- run agreement scripts on real completed annotation CSVs
- create adjudication packets
- update claim ledger only if evidence thresholds pass
- run no-run reports and fixture tests

## Tasks

### 1. Check human validation prerequisites

Inspect:

- `docs/HUMAN_VALIDATION_MASTER_PROTOCOL.md`
- `data/human_validation/templates/`
- `reports/TINY_PROVIDER_PILOT_POSTRUN_AUDIT.md`
- provider run outputs, if available
- annotation scripts/exporters

If no real provider outputs exist, create `reports/HUMAN_VALIDATION_BLOCKED_NO_PROVIDER_OUTPUTS.md`.

If no annotators exist, create:

- `docs/HUMAN_VALIDATION_RECRUITMENT_PACKET.md`
- `reports/HUMAN_VALIDATION_BLOCKED_NO_ANNOTATORS.md`

and stop before claiming evidence.

### 2. Export pilot validation packet

Create a stratified pilot sample:

- 40–60 items minimum if available
- include clean/intervention pairs
- include high-risk intervention families
- include tool_removal / tool_failure / memory_corruption / observation_conflict
- include final answer and trajectory diagnostics
- redact provider/model identity
- include gold answer and task context as allowed by protocol

Create:

- `data/human_validation/pilot_v0_1/sample_manifest.json`
- `data/human_validation/pilot_v0_1/annotation_sheet_annotator_A.csv`
- `data/human_validation/pilot_v0_1/annotation_sheet_annotator_B.csv`
- `data/human_validation/pilot_v0_1/README.md`
- `data/human_validation/pilot_v0_1/adjudication_sheet.csv`

### 3. Annotation instructions

Ensure annotator packet asks:

- Is the task understandable?
- Is the expected answer valid?
- Is the intervention isolated?
- Did the intervention change the correct behavior?
- Is the model answer correct?
- Is the trajectory failure label correct?
- Is the sample invalid?
- Confidence score
- Free-text rationale

### 4. Agreement analysis

If completed annotation CSVs exist:

Compute:

- raw agreement
- Cohen’s kappa or Krippendorff alpha where appropriate
- confidence intervals if implemented
- disagreement counts by category
- invalid sample rate
- adjudicated agreement if adjudication complete

Create:

- `reports/HUMAN_VALIDATION_PILOT_AGREEMENT.md`
- `reports/HUMAN_VALIDATION_PILOT_AGREEMENT.json`

If annotations are incomplete, create blocked status only.

### 5. Claim gate

Only if real annotations exist and thresholds pass:

- mark C3/C10 as candidate_supported or supported according to repo policy
- link exact annotation artifacts
- do not promote other claims

If thresholds fail:

- keep C3/C10 blocked
- create repair plan

### 6. Tests

Add/update tests for:

- annotation export requires real provider outputs for trajectory claims
- no fake annotations
- agreement script refuses incomplete files
- C3/C10 cannot promote without completed agreement report
- invalid sample rates block claims if too high

### 7. Validation

Run:

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_human_validation_pilot
```

Run targeted tests.

## Final response format

# Human Validation Pilot Report

## 1. Executive Summary
## 2. Prerequisites
## 3. Annotation Packet
## 4. Annotator Status
## 5. Agreement Metrics
## 6. C3/C10 Claim Gate
## 7. Invalid Samples
## 8. Disagreements and Adjudication
## 9. Tests Added/Updated
## 10. Commands Run
## 11. Commands Not Run
## 12. Evidence State
## 13. Remaining Human Validation Blockers
## 14. Next Step

Success condition:

- real annotation packet exists
- completed annotations are analyzed if available
- C3/C10 remain blocked unless real evidence supports them
