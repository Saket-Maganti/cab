# LLM Judge Protocol

LLM-as-judge scoring is optional. It is a diagnostic layer for scaling review, not ground truth. Judge labels must not overwrite deterministic scores or human labels unless a future workflow explicitly opts in and documents validation evidence.

## Required Config

Run judge labeling with an explicit YAML config:

```yaml
judge_provider: openai
judge_model: gpt-4.1-mini
prompt_version: judge_v0
temperature: 0.0
max_tokens: 512
retries: 2
sample_size: 100
seed: 0
dimensions:
  - final_answer_correctness
  - intervention_validity
  - trajectory_error_taxonomy
  - contradiction_handling
  - recovery_behavior
allow_label_overwrite: false
```

Required fields are `judge_provider`, `judge_model`, `prompt_version`, `temperature`, `max_tokens`, and `retries`. Provider keys must remain in environment variables. The CLI reports provider names and env var names only; it must not print key values.

## Run Judge Labels

```bash
python -m causal_agent_bench run-llm-judge \
  --run-dir results/<run_dir> \
  --config configs/judge.yaml \
  --output-dir results/<run_dir>/llm_judge
```

Outputs:

- `judge_labels.jsonl`
- `judge_manifest.json`

The manifest records provider, model, prompt version, prompt hashes, config hash, git commit when available, and safety flags showing that deterministic and human labels were not overwritten.

## Prompt Templates

Prompt templates live in `prompts/judges/`:

- `final_answer_correctness.md`
- `intervention_validity.md`
- `trajectory_error_taxonomy.md`
- `contradiction_handling.md`
- `recovery_behavior.md`

Each prompt requires a JSON response with `label`, `rationale`, and `confidence`. Allowed labels are `yes`, `no`, `unclear`, and `not_applicable`.

## Calibration

Compare judge labels to completed human annotations:

```bash
python -m causal_agent_bench calibrate-llm-judge \
  --judge-labels results/<run_dir>/llm_judge/judge_labels.jsonl \
  --human-annotations results/<run_dir>/human_validation/annotation_export.csv \
  --output-dir results/<run_dir>/llm_judge/calibration
```

Outputs:

- `judge_calibration_report.json`
- `judge_calibration_report.md`
- `judge_calibration_table.csv`
- `judge_human_comparisons.jsonl`

The report computes agreement with human labels, bias summaries by agent and judge model, sensitivity to final-answer length, and sensitivity to answer-order bucket.

## Reporting Rule

The paper may describe judge calibration as an analysis tool only after the report is generated and linked in the claim ledger. Judge labels cannot be reported as benchmark ground truth unless human validation demonstrates acceptable agreement and the paper clearly distinguishes judge labels from deterministic and human labels.
