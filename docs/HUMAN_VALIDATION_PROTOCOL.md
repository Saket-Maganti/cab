# Human Validation Protocol

> The canonical ICLR task/intervention validation protocol is now
> `docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md`. This older trajectory-validation
> protocol remains for the separate postrun C3 lane. It cannot substitute for
> the canonical C10 review sheet or validator.

This protocol prepares the future human-validation lane for Causal Agent Bench. It is workflow scaffolding only until real annotators complete annotation packets, agreement metrics are computed, and adjudication records are stored.

Human validation is meant to verify task understandability, clean/intervention pairing quality, intervention isolation, expected-label validity, trajectory failure-category labels, and whether evidence spans support the assigned labels. It cannot by itself prove model performance, provider behavior, causal robustness, or main benchmark claims without verified provider-backed runs and claim-evidence review.

## Claim Scope

Human validation may eventually support claims about annotation reliability, intervention validity, and failure taxonomy quality. C3 and C10 remain blocked without real annotation artifacts, agreement summaries, and adjudication records. Table 5 placeholders cannot support claims; Table 5 must be generated from completed annotation data only.

## Annotators

Annotators should understand tool-using agent traces, benchmark task specifications, and the failure taxonomy. They should not annotate examples they authored or generated. Each item should receive at least two independent annotations before adjudication; more than two annotators can be used for calibration or contentious categories.

## Annotation Unit

The unit is one clean or intervention trajectory paired with its task metadata, expected answer, intervention type, predicted failure category, and a bounded evidence span or step range. Annotators judge the trajectory and label, not the agent family or provider identity.

## Sample Selection

Use stratified sampling across domain, difficulty, clean/intervention condition, intervention type, success/failure state, agent family, and predicted failure category. Include a small calibration set before the main packet. Do not sample from private data, live credentials, or unredacted provider logs.

## Labels

Required labels include:

- `annotator_failure_category`: the best failure category or `no_failure_detected`.
- `evidence_span_or_step`: the specific step range supporting the label.
- `confidence_1_to_5`: 1 means very uncertain; 5 means highly confident.
- `adjudication_required`: true when the annotator sees ambiguity, missing evidence, or taxonomy mismatch.

Failure categories include `tool_overuse`, `premature_stopper`, `contradiction_blind`, `memory_blind`, `argument_sloppy`, `recovery_weak`, `final_answer_hallucinator`, `retry_loop_agent`, `other`, and `no_failure_detected`.

## Disagreement And Adjudication

Annotators work independently first. Disagreements are flagged by exact label mismatch, low confidence, or incompatible evidence spans. An adjudicator reviews only the packet evidence and records an adjudicated label, rationale, and whether the taxonomy needs revision. Adjudication artifacts become eligible only when they include item ids, annotator-id hashes, timestamps, final labels, and rationale.

## Agreement Metrics

Report percent agreement for all categorical labels. Use Cohen's kappa for two annotators. Use Fleiss' kappa for more than two annotators. Include a confusion matrix over failure categories and a disagreement table with representative anonymized examples.

## Packet Contents

A minimum packet includes the annotation CSV, JSON schema, task metadata, clean/intervention condition, predicted label, trajectory steps, redacted evidence spans, annotator instructions, adjudication sheet, and manifest. The template files live under `data/human_validation/templates/`.

## Privacy, Security, And Ethics

Annotation packets must not include API keys, private user data, proprietary documents, or live credentials. Compensation, consent language, time estimates, and escalation procedures must be documented before real annotation begins.

## Eligibility

Annotation artifacts become eligible only after schema validation, duplicate checks, completed labels, agreement metrics, adjudication for required items, and a no-run safety report. C3/C10 stay blocked until these artifacts exist. Placeholder Table 5 rows are not evidence and cannot support paper claims.

## Dry-Run Sampler

Use `human-validation-dry-run-sample` only for synthetic fixture rehearsal:

```bash
python3 -m causal_agent_bench human-validation-dry-run-sample --output-dir reports/human_validation_dry_run
```

The sampler marks every row `synthetic_fixture=true`, `scientific_evidence=false`, and `paper_eligible=false`. It cannot support C3 or C10.
