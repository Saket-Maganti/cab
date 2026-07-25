# Scorer Risk Inventory

Date: 2026-07-09

## High-Risk Scoring Cases

| risk | example | mitigation |
|---|---|---|
| false positive substring | expected `cat`, output `concatenate` | safe word-boundary contains match |
| false negative paraphrase | expected `insufficient info`, output `cannot verify` | abstention synonym list plus human review |
| numeric tolerance | expected `10`, output `10.001` | documented tolerance by field |
| unordered lists | expected `[A,B]`, output `[B,A]` | set matching when order irrelevant |
| date ambiguity | `07/09/2026` | prefer ISO dates in gold policy |
| scorer disagreement | deterministic pass conflicts with reviewer | scorer-adjusted success only after manual review |

## Evidence Boundary

The new scorer fixtures test code behavior only. They do not grade real CAB trajectories or promote paper claims.
