# CAB CPU First-Half Deferred Stages

Deferral is caused by missing genuine inputs, not by an engineering failure.
Commands below are prospective and must not be run out of order.

| Stage | Missing input | Responsible party | Required contract | Exact command when legal | Expected output | Next gate |
|---|---|---|---|---|---|---|
| H3 | Two genuine qualified independent reviews for all 20 items and separate adjudication of every disagreement | Human-review coordinator and independent adjudicator | `configs/human_validation/c10_contract_v1.json` | `python3 scripts/validate_cab_human_reviews.py` | exit 0, `c10_state=PASS`, 20/20 groups | `COMPACT20_C10_PASSED` |
| H4 | Genuine C10 PASS and frozen candidate decisions | Benchmark coordinator | hash-bound included/excluded items, task/split/answer/scorer/analysis/manipulation/code versions | `python3 scripts/check_iclr_preexecution_readiness.py --json` | readiness state allowing slice lock | `COMPACT20_SLICE_LOCKED` |
| H5 | Locked manifest plus genuine GPU shard exports | GPU run operator and evidence custodian | immutable manifest/task/model/policy/scorer/code hashes and non-overlapping unit IDs | `python3 -m causal_agent_bench index-runs --results-root results --verify` | read-only inventory with expected locked run present | `COMPACT20_RAW_EVIDENCE_IMPORTED` |
| H6 | Complete valid imported raw evidence | Analysis operator | strict batch manifest and shard layout | `python3 -m causal_agent_bench batch-merge --batch-dir <approved_batch_dir> --output-dir <derived_output_dir>` | deterministic complete merged run; no missing/duplicate units | `COMPACT20_MERGED_AND_RESCORED` |
| H7 | Valid merged/rescored trajectories | Scorer-audit coordinator | blinded stratified audit packet; no invented human rows | `python3 -m causal_agent_bench failure-report --run-dir <merged_run_dir>` | automatic findings and manual-review queue | `COMPACT20_AUDIT_REQUIRED` or audit complete |
| H8 | Valid common-support evidence and permitted audit state | Statistical analyst | frozen Compact analysis plan | `python3 -m causal_agent_bench analyze --run-dir <merged_run_dir>` | preliminary real-evidence report, never fixture evidence | decision inputs complete |
| H9 | Completed Compact analysis and audit | Prospective decision owner | unchanged registered decision rule | No command is authorized before H8; record one allowed decision in a signed receipt | exactly one allowed decision | Scale permitted or stopped |
| H10 | `PROCEED_TO_SCALE` or another rule-permitted progression decision | Scale coordinator | frozen models/policies/repeats/budgets/seeds/estimands plus human C10 | `python3 scripts/check_iclr_preexecution_readiness.py --json` | Scale readiness without model execution | `SCALE100_CPU_AND_MANIFEST_READINESS_COMPLETE` |

Angle-bracket paths are deliberately unresolved because no approved locked
manifest or genuine shard export exists yet. Substituting fixture paths would
violate the evidence contract.

## Exact immediate action

```bash
python3 scripts/validate_cab_human_reviews.py
```

Do not advance until it returns a genuine `PASS`.
