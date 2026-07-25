# Human Validation Pilot Plan

This plan describes a small validation pilot before any paper claims rely on human labels. It is a protocol placeholder until completed annotations, adjudication, and agreement reports exist.

## Goals

The pilot should test whether annotators can apply the guidelines consistently and whether the annotation form exposes enough evidence to judge:

- task clarity,
- intervention validity,
- final-answer label correctness,
- trajectory faithfulness and tool use,
- recovery, contradiction handling, memory verification, and premature stopping,
- automated error-taxonomy labels.

## Inputs

Use one scored run directory with `instances.jsonl`, `trajectories.jsonl`, `scores.jsonl`, and `aggregate_scores.json`. The run should record config hash, dataset version or frozen dataset hash, seed, agent names, model ids when available, prompt hashes when available, scorer version, timestamp, and git commit when available.

Do not use a run containing private data, credentials, live actions, or undisclosed oracle-only results as realistic-agent evidence.

## Sampling

Create the pilot export with:

```bash
python -m causal_agent_bench export-human-validation \
  --run-dir results/<run_dir> \
  --output-dir results/<run_dir>/human_validation_pilot \
  --sample-size 30 \
  --seed 0 \
  --annotators-per-item 2
```

The sample should include, where available:

- at least three domains,
- at least two difficulty levels,
- clean and intervention instances,
- multiple intervention families,
- at least two agents,
- successful trajectories and failed trajectories,
- at least a few mined error-taxonomy categories.

If the run is too small to satisfy these targets, document the missing strata in the pilot report.

## Annotator Setup

Before annotation:

- give annotators `docs/HUMAN_VALIDATION_GUIDELINES.md`,
- give annotators `docs/HUMAN_VALIDATION_FORM_SCHEMA.md`,
- explain that synthetic data should not be connected to real people or accounts,
- explain that oracle agents are sanity-check upper bounds, not realistic agents,
- state expected time per item and compensation,
- provide a contact/escalation path for unclear or uncomfortable examples.

Annotators should work independently for first-pass labels.

## Pilot Procedure

1. Export the sample and archive `annotation_manifest.json`.
2. Assign two annotators per item where possible.
3. Annotators fill all applicable labels and notes.
4. Run agreement summary:

```bash
python -m causal_agent_bench summarize-human-validation \
  --annotations results/<run_dir>/human_validation_pilot/annotation_export.csv \
  --output-dir results/<run_dir>/human_validation_pilot/summary
```

5. Review `disagreement_examples.jsonl`.
6. Adjudicate disagreements for dimensions relevant to claims.
7. Update the validation report with adjudication notes and known limitations.

## Acceptance Criteria

The pilot is ready to scale only if:

- annotators report that the form exposes enough evidence for most items,
- task and intervention labels have acceptable agreement for the intended claim,
- systematic disagreements have documented decision-rule updates,
- any scoring bugs found during annotation are fixed or excluded,
- no private data, credentials, or live-action requests appear in annotation packets,
- compensation and consent documentation are complete.

The project should not move claim-ledger rows about label quality, intervention validity, or trajectory diagnostics to `supported` based on an incomplete pilot.

## Expected Outputs

The pilot directory should contain:

- `annotation_export.csv`
- `annotation_export.jsonl`
- `annotation_interface.html`
- `annotation_manifest.json`
- completed annotation files,
- `validation_agreement.json`
- `validation_report.md`
- `table5_human_validation_agreement.csv`
- `table5_human_validation_agreement.md`
- `table5_human_validation_agreement.tex`
- `disagreement_examples.jsonl`

## Risks To Track

- Annotators may disagree because the packet omits tool outputs or hidden ground-truth details.
- Some interventions may remain valid technically but feel too artificial.
- Deterministic stub trajectories may be easier to judge than realistic LLM trajectories.
- Error-taxonomy labels may be too coarse for ambiguous failures.
- High agreement on synthetic items may not imply external validity.

Record these risks in the validation report and claim ledger before citing validation results.
