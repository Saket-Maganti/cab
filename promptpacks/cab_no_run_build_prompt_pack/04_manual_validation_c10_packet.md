You are working in the Causal Agent Bench repository.

You are Codex acting as a human-validation protocol designer, construct-validity auditor, and benchmark review lead.

Task:
Prepare a C10/intervention-isolation manual validation packet. This is build-only and no-run.

Current reality:
- C10 is planned/unsupported.
- Intervention isolation is the load-bearing validity assumption.
- No human annotations exist.
- The project cannot claim “causal” or “validated perturbation” without completed review.

Absolute rules:
- Do not call providers.
- Do not run local LLMs.
- Do not execute model/benchmark/provider runs.
- Do not fabricate annotations.
- Do not compute agreement without two independent completed reviewers.
- Do not promote C10.
- Do not mark benchmark validated.
- Do not claim causal validity.

Inspect:
- docs/HUMAN_VALIDATION_COMPACT_PROTOCOL.md
- docs/HUMAN_VALIDATION_MASTER_PROTOCOL.md
- data/human_validation/compact_pilot/
- data/human_validation/no_api_task_review/
- docs/GOLD_POLICY_DECISION_MATRIX.md
- intervention taxonomy/spec docs
- C10 claim docs/claim ledger

Tasks:

1. Create C10 validation protocol:
   - docs/C10_INTERVENTION_ISOLATION_VALIDATION_PROTOCOL.md

Include:
- what C10 means
- what human reviewers judge
- isolation criteria
- goal-preservation criteria
- changed-factor criteria
- answer-policy criteria
- exclusion criteria
- agreement metrics to compute later
- pass/fail thresholds
- what claims are allowed at each evidence level

2. Create annotation packet schema:
   - data/human_validation/c10_isolation_review/README.md
   - data/human_validation/c10_isolation_review/c10_isolation_annotation_template.csv
   - data/human_validation/c10_isolation_review/c10_adjudication_template.csv

Reviewer fields blank/TODO.

3. Create reviewer instructions:
   - data/human_validation/c10_isolation_review/C10_REVIEWER_INSTRUCTIONS.md

The instructions must be usable by a human reviewer and include examples of:
- isolated intervention
- non-isolated intervention
- gold should stay same
- gold should change
- abstention acceptable
- exclude item

If examples require actual repo tasks, use placeholders or clearly mark as illustrative only.

4. Create C10 status report:
   - reports/C10_VALIDATION_STATUS_NO_RUN.md

Must state:
- C10 unsupported
- 0 annotations unless user-provided completed files exist
- no agreement metrics
- what is required to promote C10
- why C10 matters for reviewer defense

5. Add/update tests:
- C10 cannot be promoted without completed annotations
- agreement cannot be computed from one reviewer
- C10 review files cannot support model-performance claims
- causal language remains qualified unless C10 is supported

Allowed commands:
- static inspection
- targeted fixture tests
- py_compile if code changed

Final response:

# CAB C10 Manual Validation Packet Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. C10 Protocol
## 5. Annotation Packet
## 6. Reviewer Instructions
## 7. Status and Evidence Boundary
## 8. Tests Added/Updated
## 9. Commands Run
## 10. Commands Not Run
Confirm no provider/model/local LLM/benchmark runs and no fake annotations.
## 11. Evidence State
## 12. Remaining Blockers
## 13. Next Best Action

Final verdict:
C10_NO_RUN_VALIDATION_PACKET_READY
