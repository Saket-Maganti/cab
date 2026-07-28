# Human Validation Master Protocol

**Version:** 0.1-pre-annotations  
**Status:** Protocol and templates ready · **No completed annotations exist**  
**Claims gated:** C3 (trajectory vs final scoring) · C10 (intervention isolation validity)

The authoritative pre-execution C10 specification is now
`docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md`. This document remains a legacy
overview of both pre-execution validity review and the later trajectory/C3
lane. It does **not** claim annotations, agreement statistics, or expert
validation have been completed.

---

## 1. Annotation goals

| Goal | Supports claim | Current status |
|------|----------------|----------------|
| Task understandability | Benchmark validity | Protocol only |
| Clean/intervention pairing quality | C10 | Blocked |
| Single-factor intervention isolation | C10 | Blocked |
| Gold-answer correctness | Scoring validity | Blocked |
| Trajectory failure-label accuracy | C3 | Blocked |
| Failure taxonomy coverage | C2–C8 diagnostics | Blocked |

---

## 2. Annotator eligibility

- Fluent in English technical instructions
- Familiarity with tool-using agent traces (ReAct-style steps)
- No authorship of benchmark tasks being annotated
- No access to provider API keys or hidden test-split answers beyond packet redaction policy
- Completed calibration set (≥10 items) before main packet
- **Minimum:** 2 independent annotators per item; adjudication for disagreements

---

## 3. Sample selection strategy

**Stratify** across:

- Domain / task family
- Difficulty bucket
- Clean vs intervention
- Intervention type (oversample high-risk families)
- Predicted success vs failure
- Predicted failure category
- Agent family (after provider pilot — not available yet)

**Sources (in order):**

1. **Now:** `human-validation-dry-run-sample` — synthetic fixtures only (workflow rehearsal)
2. **After provider pilot:** stratified export from first complete non-oracle run
3. **Before main benchmark:** additional sample from frozen main split (held-out IDs redacted in packets)

**Exclude:** private data, live credentials, unredacted provider logs, oracle-only trajectories for human validity claims.

---

## 4. Blinded review policy

- Annotators receive **anonymized trajectory packets** (`trajectory_packet_schema.json`)
- Provider model IDs and agent implementation details **redacted**
- No access to aggregate benchmark results or leaderboard during annotation
- Adjudicators see both annotator labels but not each other's identity (hashed `annotator_id_hash`)

---

## 5. Annotation questions (CSV columns)

| Column | Question |
|--------|----------|
| `task_understandable_yes_no` | Is the task understandable without repo context? |
| `intervention_isolation_valid_yes_no` | Does the intervention change exactly one intended causal factor? |
| `gold_answer_correct_yes_no` | Is the reference gold answer plausible and complete? |
| `trajectory_label_valid_yes_no` | Does the predicted failure category match visible trajectory evidence? |
| `annotator_failure_category` | Best failure label or `no_failure_detected` |
| `evidence_span_or_step` | Step range supporting the label |
| `confidence_1_to_5` | 1=very uncertain, 5=highly confident |
| `invalid_sample_flag` | `true` if item should be excluded from metrics |
| `invalid_sample_reason` | Leakage, missing steps, ambiguity, PII, etc. |

---

## 6. Disagreement handling

- Flag `adjudication_required=true` when: label mismatch, confidence ≤2, incompatible evidence spans, or any validity question = `no`
- Adjudicator uses `adjudication_sheet_template.csv`
- Record `adjudicator_label`, `adjudicator_rationale`, `taxonomy_revision_needed`

---

## 7. Agreement metrics (planned — not reported)

| Metric | Use |
|--------|-----|
| Percent agreement | Failure category |
| Cohen's κ | 2 annotators |
| Fleiss' κ | >2 annotators |
| Confusion matrix | Category-level errors |
| Invalid-sample exclusion rate | Quality control |

**Do not fabricate** κ or agreement values. Table 5 remains placeholder until real data.

---

## 8. Data privacy and safety

- Synthetic `example.com` PII only in benchmark data
- No API keys in packets
- Compensation documented before real annotation (paper §11 placeholder)
- Escalation path for harmful or ambiguous content

---

## 9. Expected sample sizes

| Phase | Target items | Annotators | Purpose |
|-------|-------------|------------|---------|
| Dry-run (now) | ~8 synthetic | 0 completed | Workflow rehearsal |
| Pilot HV (post–tiny pilot) | 40–60 | 2 + adjudicator | C3/C10 pilot validity |
| Main benchmark HV | 120–200 | 2 + adjudicator | Paper Table 5 + C10 |

**Current completed annotations:** **0**

---

## 10. C3 / C10 claim gating

| Claim | Required artifacts | Status |
|-------|-------------------|--------|
| **C3** | Completed annotations, agreement on trajectory labels, adjudication records | **blocked** |
| **C10** | Completed annotations on intervention isolation + expert review | **blocked** |

Promotion requires:

1. `data/human_validation/completed_*` export paths
2. `agreement_summary` filled from real data (not template)
3. Claim-evidence matrix update with linked run dirs
4. Post-run safety audit pass

---

## 11. Artifact locations

| Artifact | Path |
|----------|------|
| Annotation CSV template | `data/human_validation/templates/annotation_sheet_template.csv` |
| JSON schema | `data/human_validation/templates/annotation_schema.json` |
| Codebook | `data/human_validation/templates/annotation_codebook.md` |
| Adjudication template | `data/human_validation/templates/adjudication_sheet_template.csv` |
| Agreement template | `data/human_validation/templates/agreement_summary_template.md` |
| Annotator README | `data/human_validation/templates/README_ANNOTATOR.md` |
| Adjudicator README | `data/human_validation/templates/README_ADJUDICATOR.md` |
| Dry-run sample | `human-validation-dry-run-sample` CLI output |

---

## 12. Commands (safe only)

```bash
python3 -m causal_agent_bench human-validation-packet --output-dir reports/human_validation
python3 -m causal_agent_bench human-validation-dry-run-sample --output-dir reports/human_validation_dry_run
```

**Forbidden until provider pilot:** exporting real trajectory samples from live runs without approval.

---

See also: [HUMAN_VALIDATION_PROTOCOL.md](HUMAN_VALIDATION_PROTOCOL.md), [INTERVENTION_VALIDITY_DOSSIER.md](INTERVENTION_VALIDITY_DOSSIER.md).
